#
# Copyright (c) 2011 Ben Belchak <ben@belchak.com>
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
import re
import sys
import yaml
import inspect
import logging
# Import ALL the plugins!
from plugins import *
from pinder.campfire import Campfire
from twisted.internet import reactor

log = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s => %(levelname)s %(message)s', level=logging.DEBUG)

class Room(object):
    def __init__(self, name, client):
        self.name   = name
        self.client = client
    
    def callback(self, line):
        self.client.callback(self, line)

class Campy(object):
    def __init__(self, **kwargs):
        # This is the directory we were launched in, before we move to the 
        # Campy home directory
        self.launchdir = os.getcwd()
        # In some cases, it might be useful to provide the subdomain and
        # an API key in the initializer (perhaps passed in as a command-
        # line argument?)
        self.subdomain = kwargs.get('subdomain', None)
        self.apiKey    = kwargs.get('api_key', None)
        # When we get a message from Campfire, we're supplied with the room_id
        # as one of the parameters of the message. As such, we'll have a room
        # dictionary so we can quickly look up the appropriate room object
        self.rooms = {}
        # This is a list of all our plugins, where each is an instance of the 
        # type campy.CampyPlugin, and the keys are the regular expressions they
        # are meant to match.
        from campy.plugins import say, config, alias
        self.plugins = {
            'say'   : say.SayPlugin(self),
            'config': config.ConfigPlugin(self),
            'alias' : alias.AliasPlugin(self)
        }
        # This is the name that the campy bot will respond to. It can be 
        # provided in the constructor, or it can be provided in the settings.
        # The value provided in the constructor overrides what's specified in
        # the settings, and it defaults to 'campy'
        self.name = kwargs.get('name', None)
        # This is the regular expression that matches our bot's name, and the
        # corresponding message to parse
        self.nameRE = None
        
        # This is our actual campfire client. It will be made when we read in
        # our settings. However, for now, it is None. That value is used as
        # a semaphore indicating whether or not this is the first read-in or
        # not.
        self.client = None
        
        self.goodbye     = 'Goodbye!'
        self.leaveOnExit = True
        
        # Try to set up our home directory
        self.home   = kwargs.get('home', os.path.expanduser('~/.campy'))
        if not os.path.exists(self.home):
            try:
                os.mkdir(self.home)
            except Exception as e:
                log.exception('Cannot make directory %s' % self.home)
        
        # Set the configuration files
        self.configs = [
            os.path.join(self.home, 'campy.conf'),
            os.path.join(self.launchdir, 'campy.conf')
        ]
        self.read()

    def findPlugin(self, n):
        '''Try to locate the module with this particular name'''
        try:
            log.debug('Trying to import %s' % n)
            plugins = []
            # If we've already loaded this particular module...
            try:
                import campy
                m = __import__('campy.plugins.%s' % n)
                m = getattr(campy, 'plugins')
                m = getattr(m, n)
            except ImportError:
                m = __import__(n)
            for name, klass in inspect.getmembers(m):
                try:
                    if issubclass(klass, CampyPlugin):
                        plugins.append(klass)
                except:
                    continue
            return plugins
        except:
            log.exception('Could not find plugin %s' % n)
            return []
    
    def reloadPlugin(self, n):
        '''Try to reload a given module'''
        try:
            reload(n)
        except Exception:
            log.exception('Could not reload %s' % n)
    
    def reload(self, **kwargs):
        '''Given a new set of configurations, make sure we're up to date'''
        if self.client:
            pass
        else:
            log.info(repr(kwargs))
            subdomain = kwargs.get('subdomain', self.subdomain)
            apiKey    = kwargs.get('api_key', self.apiKey)
            if not subdomain and not apiKey:
                log.critical('Need a subdomain and API key')
                exit(1)
            self.client = Campfire(subdomain, apiKey)
            
            # Now register the bot's name
            self.name   = kwargs.get('name', self.name) or 'campy'
            self.nameRE = re.compile(r'\s*%s\s+(.+)\s*$' % re.escape(self.name), re.I)
            
            # Now join all the appropriate rooms
            for room in kwargs.get('rooms', []):
                if not self.joinRoom(room):
                    log.warn('Could not find room %s' % room)
                else:
                    log.debug('Joined %s' % room)
    
    def read(self, overrides={}):
        '''Re-read the settings, and do all the appropriate imports'''
        # We're going to build up a single dictionary, making sure to merge
        # and override all options in subsequent config files. Then, and
        # only then will we start to go through it.
        log.debug('Reading configuration files...')
        self.data = {}
        for fname in self.configs:
            try:
                with file(fname) as f:
                    self.data.update(yaml.safe_load(f))
            except Exception as e:
                log.error('Could not read %s => %s' % (fname, repr(e)))
        self.data.update(overrides)
        # There has to at least be a campy section
        if 'campy' not in self.data:
            log.critical('No campy configuration found in config files!')
            exit(1)
        # Now go through the remaining sections
        for section, values in self.data.items():
            if section == 'campy':
                if not values:
                    values = {}
                self.reload(**values)
                continue
            if section == 'logger':
                import logging.config
                logging.config.dictConfig(values)
                continue
            # If it wasn't the campy section, then we should try to
            # import the module named in that section, and then to
            # instantiate each of the plugins that inherit from 
            # plugins.CampyPlugin
            try:
                for m in self.findPlugin(section):
                    # Alright! We found a plugin. Now, let's see
                    # if the plugin has been instantiated, or if
                    # it hasn't yet been encountered
                    plugin = self.plugins.get(m.shortname)
                    if plugin:
                        if not values:
                            values = {}
                        plugin.reload(**values)
                    else:
                        log.debug('Storing plugin at %s' % m.shortname)
                        self.plugins[m.shortname] = m(self, **values)
            except ImportError:
                log.exception('Unable to import module %s' % section)
        log.debug('Read configuration files...')
    
    def save(self, filename=None):
        # Try to save the current configuration to a file.
        try:
            # To be safe when writing, the best thing to do is to first
            # save a temporary copy, and then if successful, replace the
            # original with the temporary
            path = filename or os.path.join(self.home, 'campy.conf')
            with file(path + '.bak', 'w+') as f:
                f.write(yaml.dump(self.data))
            
            # And now move the new file to replace the old file
            os.rename(path + '.bak', path)
            log.debug('Wrote to %s' % path)
            return 'Wrote configuration to %s' % path
        except Exception as e:
            log.exception('Campy save exception')
            return 'Campy save exception => %s' % repr(e)
    
    def callback(self, obj):
        '''Go through all the plugins and give it the appropriate message'''
        # The object provided looks something like this:
        #   'body'       : Text we heard
        #   'user_id'    : Who said it
        #   'created_at' : When it happened
        #   'room_id'    : The room where it was said
        #   'starred'    : A string representation ('true' or 'false')
        #   'type'       : Message type (e.g. 'TextMessage')
        #   'id'         : Message ID
        
        match = self.nameRE.match(obj.get('body', ''))
        if match:
            message = match.group(1)
            obj['body'] = message
        else:
            log.debug('Message "%s" did not match "%s "' % (obj.get('body', ''), self.name))
            return
        
        # The room that received the message:
        room = self.rooms.get(obj.get('room_id', ''), None)
        if room:
            log.info('I just heard : %s' % repr(obj))
        else:
            log.warn('I do not know about room %s' % obj.get('room_id', ''))
            return
        
        user = self.client.user(obj['user_id'])
        self.handle_message(self.client, room, obj, user)
    
    def handle_message(self, campfire, room, message, speaker):
        # Handle the join room command
        match = re.match(r'\s*join\s+(.+)\s*$', message['body'])
        if match:
            room.speak(self.joinRoom(match.group(1).strip()))
            return
        
        # Handle the leave room command
        match = re.match(r'\s*leave\s+(.+)\s*$', message['body'])
        if match:
            room.speak(self.leaveRoom(match.group(1).strip()))
            return
        
        # See if it's a built-in command
        if re.match(r'\s*help\s*', message['body']):
            self.handle_help(campfire, room, message, speaker)
        
        # Handle all help requests...
        match = re.match(r'\s*help\s*(.+?)\s*$', message['body'])
        if match:
            name = match.group(1)
            plugin = self.plugins.get(name, None)
            if plugin:
                plugin.send_help(self.client, room, message, speaker)
                return
            # Alright, if we've made it here, nothing had help for this command
            room.speak('No help available for %s' % match.group(1))
        
        # Otherwise, try to find the plugin that they were trying to talk to
        match = re.match(r'\s*(\S+)(\s*.*$|$)', message['body'])
        if match:
            name = match.group(1)
            plugin = self.plugins.get(name, None)
            if plugin:
                try:
                    plugin.handle_message(self.client, room, message, speaker)
                    return
                except Exception as e:
                    room.paste('Expection in %s => %s' % (name, repr(e)))
                    log.exception('Exception in %s' % name)
            else:
                room.speak('No plugin responds to %s' % message['body'])
        else:
            log.warn('No match.')
    
    def handle_help(self, campfire, room, message, speaker):
        room.paste('''Give this campfire bot commands by saying "campy <command>".
To find out more about a command, type "campy help <command>". The currently-loaded
plugins are: %s''' % ', '.join(self.plugins.keys()))
    
    def errback(self, failure):
        try:
            failure.raiseException()
        except:
            log.exception('Errback')
    
    def joinRoom(self, name):
        room = self.client.find_room_by_name(name)
        if room:
            if room.id in self.rooms:
                log.debug('Already in room %s' % name)
                return 'Already in room %s' % name
            else:
                self.rooms[room.id] = room
                room.join()
                room.listen(self.callback, self.errback, start_reactor=False)
                log.debug('Joined room %s' % name)
                return 'Joined room %s' % name
        else:
            log.debug('Could not find room %s' % name)
            return 'Couldn\'t find room %s' % name
    
    def leaveRoom(self, name):
        room = self.client.find_room_by_name(name)
        if room:
            if len(self.rooms) > 1:
                if room.id in self.rooms:
                    del self.rooms[room.id]
                    return 'Left room %s' % name
                else:
                    return 'I\'m not in room %s' % name
            else:
                return '%s is the last room I\'m in, and I\'m not leaving!' % name
        else:
            return 'Couldn\'t find room %s' % name
    
    def start(self):
        log.info('Starting campy...')
        reactor.run()
    
    def stop(self):
        for room in self.rooms.values():
            room.speak(self.goodbye)
            if self.leaveOnExit:
                room.leave()
