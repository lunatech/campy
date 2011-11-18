#
# Copyright (c) 2011 SEOmoz
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

import re
from campy import log
from campy.plugins import CampyPlugin

class AliasPlugin(CampyPlugin):
    shortname  = 'alias'
    listRE     = re.compile(r'alias\s+list\s*$', re.I)
    execRE     = re.compile(r'alias\s+(.+)\s*$', re.I)
    setRE      = re.compile(r'alias\s+set\s+([^\=]+)\s*\=\s*(.+)\s*$', re.I)
    
    def __init__(self, campy, **kwargs):
        self.campy   = campy
        self.aliases = kwargs
    
    def reload(self, **kwargs):
        self.aliases = kwargs

    def handle_message(self, campfire, room, message, speaker):
        body = message['body']
        match = self.listRE.match(body)
        if match:
            aliases = [' => '.join(pair) for pair in self.aliases.items()]
            room.paste('\n'.join(aliases) or 'No aliases registered')
            return
        
        match = self.setRE.match(body)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()
            self.aliases[key] = value
            # Now save it to campy's configuration
            self.campy.data.setdefault('alias', {})
            self.campy.data['alias'][key] = value
            self.campy.save()
            room.speak('Alias %s saved' % key)
            return
        
        match =  self.execRE.match(body)
        if match:
            command = self.aliases.get(match.group(1).strip(), None)
            if command:
                message['body'] = command
                self.campy.handle_message(campfire, room, message, speaker)
            else:
                room.speak('Unknown alias "%s"' % match.group(1))
        else:
            room.paste('Alias did not understand the command "%s"' % body)
    
    def send_message(self, campfire, room, message, speaker):
        raise NotImplementedError

    def send_help(self, campfire, room, message, speaker):
        room.paste('''This plugin lets you create aliases for other commands:
# Create a short alias
campy alias hello = say howdy, everyone!
# Now execute the alias accoringly
campy alias hello
''')