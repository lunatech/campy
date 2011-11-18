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
import simplejson as json
from campy.plugins import CampyPlugin

class ConfigPlugin(CampyPlugin):
    shortname = 'config'
    reloadRE  = re.compile(r'config\s*reload\s*$', re.I)
    statusRE  = re.compile(r'config\s*$')
    saveRE    = re.compile(r'config\s*save\s$')
    setRE     = re.compile(r'config\s*set\s+(.+)$')
    
    def __init__(self, campy, **kwargs):
        self.campy = campy
    
    def handle_message(self, campfire, room, message, speaker):
        body = message['body']
        if self.statusRE.match(body):
            room.paste('Current configuration: %s' % repr(self.campy.data))
            return
        
        if self.reloadRE.match(body):
            room.speak('Reloading confguration...')
            self.campy.read()
            room.speak('Reloaded configuration')
            return
        
        if self.saveRE.match(body):
            room.speak('Saving configuration')
            self.campy.save()
            return
        
        match = self.setRE.match(body)
        if match:
            obj = json.loads(match.group(1))
            room.speak('Setting %s' % repr(obj))
            self.campy.read(obj)

    def send_message(self, campfire, room, message, speaker):
        raise NotImplementedError

    def send_help(self, campfire, room, message, speaker):
        room.paste('''This plugin lets you change campy's configuration:
# Get the current configuration
campy config
# Reload the configuration files
campy config reload
# Set a configuration option (in JSON)
campy config set {"module": {"option1" : "value1"}}
# Save the configuration to the campy configs
campy config save
''')