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
import os
import subprocess
from campy import log
from campy.plugins import CampyPlugin

class PipPlugin(CampyPlugin):
    shortname  = 'pip'
    installRE  = re.compile(r'pip\s+install\s+(\S+?)\s*$', re.I)
    
    def handle_message(self, campfire, room, message, speaker):
        body = message['body']
        match = self.installRE.match(body)
        if match:
            repo = match.group(1)
            try:
                results = subprocess.check_output(['pip', 'install', repo], stderr=subprocess.STDOUT)
            except Exception as e:
                log.exception('Failed to git action')
            finally:
				room.paste('Pip: %s' % results)
            return

    def send_message(self, campfire, room, message, speaker):
        raise NotImplementedError

    def send_help(self, campfire, room, message, speaker):
        room.paste('''This plugin lets you install packages with pip:
campy pip install pyyaml
''')