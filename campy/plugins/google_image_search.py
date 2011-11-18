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
#

import traceback
import re
import simplejson
import httplib2
import urllib

from campy.plugins import CampyPlugin

class GoogleImage(CampyPlugin):
    shortname = 'gis'
    base = 'https://ajax.googleapis.com/ajax/services/search/images?safe=%s&v=1.0&q=%s'
    
    def __init__(self, campy, **kwargs):
        self.campy = campy
        self.safe = kwargs.get('safe', '0')
    
    def reload(self, **kwargs):
        self.safe = kwargs.get('safe', '0')

    def send_help(self, campfire, room, message, speaker):
        help_text = """%s: Here is your help for the Google Image Search plugin:
        gis searchstring -- Search for an image. Will return the top result. (e.g. gis cuddly bunny)
        """ % speaker['user']['name']
        room.paste(help_text)
    
    def handle_message(self, campfire, room, message, speaker):
        body = message['body']
        if not body:
            return

        m = re.match('gis (?P<search_string>.*)$', body)
        if m:
            try:
                headers, content = httplib2.Http().request(
                    self.base % (self.safe, urllib.quote(m.group('search_string'))))
                json = simplejson.loads(content)
                self.speak_image_url(room, json['responseData']['results'][0]['unescapedUrl'])
            except (KeyError,):
                room.speak(traceback.format_exc())


    def speak_image_url(self, room, url):
        room.speak(unicode(url))
