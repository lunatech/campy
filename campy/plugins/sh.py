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
import shlex
import subprocess
from campy import log
from campy.plugins import CampyPlugin

class ShPlugin(CampyPlugin):
    shortname  = 'sh'
    execRE     = re.compile(r'sh\s+(.+)\s*$', re.I)

    def handle_message(self, campfire, room, message, speaker):
        body = message['body']
        match = self.execRE.match(body)
        if match:
            room.speak('Running command "%s". One moment...' % match.group(1).strip())
            command = shlex.split(match.group(1).strip().encode('utf-8'))
            # Append the command name
            try:
                room.paste(match.group(1) + ' => ' + subprocess.check_output(command))
            except subprocess.CalledProcessError as e:
                room.paste(match.group(1) + ' => ERROR %i %s' % (e.returncode, e.output))
    
    def send_message(self, campfire, room, message, speaker):
        raise NotImplementedError

    def send_help(self, campfire, room, message, speaker):
        room.paste('''This plugin lets you execute a program on the remote system:
# Note, that this does not provide true shell access
campy sh echo "howdy"
''')