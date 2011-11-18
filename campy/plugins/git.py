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
import shlex
import subprocess
from campy import log
from campy.plugins import CampyPlugin

class GitPlugin(CampyPlugin):
    shortname  = 'git'
    commandRE  = re.compile(r'git\s+(.+)\s*$', re.I)

    def __init__(self, campy, **kwargs):
        self.campy = campy
        # The path where we store everything
        self.path = kwargs.get('path', os.path.abspath(os.path.expanduser('~/')))
    
    def handle_message(self, campfire, room, message, speaker):
        body = message['body']
        match = self.commandRE.match(body)
        if match:
            cwd = os.getcwd()
            os.chdir(self.campy.home)
            command = ['git']
            command.extend(shlex.split(match.group(1).strip().encode('utf-8')))
            room.paste('Running %s' % ' '.join(command))
            try:
                room.paste(match.group(1) + ' => ' + subprocess.check_output(command))
                self.campy.updatePath()
            except subprocess.CalledProcessError as e:
                room.paste(match.group(1) + ' => ERROR %s' % e.output)
            finally:
                os.chdir(cwd)
            return
        else:
            self.send_help(campfire, room, message, speaker)
    
    def send_message(self, campfire, room, message, speaker):
        raise NotImplementedError

    def send_help(self, campfire, room, message, speaker):
        room.paste('''This plugin lets you checkout git repos to __campy__'s path:
# clone a repository
campy git clone git@github.com:someuser/someproject
# Pull updates into a repo
campy git update someproject
''')