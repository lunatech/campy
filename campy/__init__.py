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
import inspect
import logging
import settings
import ConfigParser
from plugins import CampyPlugin
from pinder.campfire import Campfire
from twisted.internet import reactor

log = logging.getLogger(__name__)

class Room(object):
    def __init__(self, name, client):
        self.name   = name
        self.client = client
    
    def callback(self, line):
        self.client.callback(self, line)

class Campy(object):
    def __init__(self, **kwargs):
        # In some cases, it might be useful to provide the subdomain and
        # an API key in the initializer (perhaps passed in as a command-
        # line argument?)
        self.subdomain = kwargs.get('subdomain', None)
        self.apiKey    = kwargs.get('api_key', None)
        # This is a list of all the config files we should use. By default,
        # we should check '/etc/campy.conf', '~/campy.conf' (of the running
        # user), and any config file provided
        self.configs = ['/etc/campy.conf', os.path.abspath('~/campy.conf'), os.path.abspath('./campy.conf')]
        if kwargs.get('config', None):
            self.configs.append(kwargs['config'])
        # When we get a message from Campfire, we're supplied with the room_id
        # as one of the parameters of the message. As such, we'll have a room
        # dictionary so we can quickly look up the appropriate room object
        self.rooms = {}
        # This is a list of all our plugins, where each is an instance of the 
        # type campy.CampyPlugin, and the keys are the regular expressions they
        # are meant to match.
        self.plugins = {}
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
        self.reload(**kwargs)
    
    def reload(self, **kwargs):
        '''Given a new set of configurations, make sure we're up to date'''
        if self.client:
            pass
        else:
            subdomain = kwargs.get('subdomain', self.subdomain)
            apiKey    = kwargs.get('api_key', self.apiKey)
            if not subdomain and not apiKey:
                log.critical('Need a subdomain and API key')
                exit(1)
            self.client = Campfire(subdomain, apiKey)
            self.name   = kwargs.get('name', self.name) or 'campy'
            self.nameRE = re.compile(r'\s*%s\s+(.+)\s*$' % re.escape(self.name), re.I)
            for room in kwargs.get('rooms', '').split(','):
                room = self.client.find_room_by_name(room)
                if room:
                    log.debug("Joining %s" % room)
                    self.rooms[room.id] = room
                    room.join()
                else:
                    log.warn('Room %s not found' % room)
    
    def read(self):
        '''Re-read the settings, and do all the appropriate imports'''
        # We're going to build up a single dictionary, making sure to merge
        # and override all options in subsequent config files. Then, and
        # only then will we start to go through it.
        parser = ConfigParser.SafeConfigParser()
        # This reads through all the listed configuration files, adn then
        # tells you which files it was able to read
        readfiles = parser.read(self.configs)
        if len(readfiles) < len(self.configs):
            for f in self.configs:
                if f not in readfiles:
                    log.warn('Could not read %s' % f)
        # Now go through all the sections and set options accordingly
        if not parser.has_section('campy'):
            log.critial('No campy configuration found in config files!')
            exit(1)
        for section in parser.sections():
            if section == 'campy':
                self.reload(**dict(parser.items('campy')))
                continue
            # If it wasn't the campy section, then we should try to
            # import the module named in that section, and then to
            # instantiate each of the plugins that inherit from 
            # plugins.CampyPlugin
            try:
                m = __import__(section)
                for name, klass in inspect.getmembers(m):
                    if issubclass(klass, CampyPlugin):
                        # Alright! We found a plugin. Now, let's see
                        # if the plugin has been instantiated, or if
                        # it hasn't yet been encountered
                        plugin = self.plugins.get('%s.%s' % (section, name))
                        if plugin:
                            t = getattr(section, name)
                            args = dict(parser.items(section))
                            self.plugins['%s.%s' % (section, name)] = t(**args)
                        else:
                            plug.reload(**args)
            except ImportError:
                log.exception('Unable to import module %s' % section)
        
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
        # Handle all help requests...
        match = re.match(r'\s*help\s*(.+?)\s*', message)
        if match:
            name = match.group(1)
            for key, plugin in self.plugins.items():
                if plugin.shortname == name:
                    plugin.send_help(self.client, room, message['body', obj, user])
                    return
            # Alright, if we've made it here, nothing had help for this command
            room.speak('No help available for %s' % match.group(1))
        
        # Otherwise, try to find the plugin that they were trying to talk to
        for key, plugin in self.plugins.items():
            try:
                if re.match('\s*%s\s*', plugin.shortname):
                    plugin.handle_message(message)
            except Exception as e:
                room.paste('Exception in %s => %s' % (key, repr(e)))
                
        # Now, we should handle the message appropriately
        room.paste('Hey everybody! I just heard "%s"' % repr(obj))
    
    def errback(self, failure):
        log.warn(failure.getErrorMessage())
    
    def start(self):
        log.info('Starting campy...')
        self.listen()
        reactor.run()
    
    def stop(self):
        for room in self.rooms.values():
            room.speak(self.goodbye)
            if self.leaveOnExit:
                room.leave()

    def listen(self):
        log.info('Listening...')
        for room in self.rooms.values():
            room.listen(self.callback, self.errback, start_reactor=False)
