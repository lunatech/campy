#! /usr/bin/env python

import httplib2
import urllib
import feedparser
# It's important to use the same reactor as campy
from campy import reactor

from plugins import CampyPlugin

class RSSReader(CampyPlugin):
    shortname = 'rss'
    
    def __init__(self, **kwargs):
        self.reload(**kwargs)
        self._known_entries = set()
        self._known_rooms = {}
        self.get_feed(True)

    def reload(self, **kwargs):
        self.urls    = kwargs.get('urls', [])
        # Get the refresh time in minutes
        self.refresh = kwargs.get('refresh', 5) * 60
        # Get the prefix
        self.prefix  = kwargs.get('prefix', '')

    def get_feed(self, first_run):
        for url in self.urls:           
            d = feedparser.parse(url)
            for entry in d.entries:
                if first_run or entry.guid in self._known_entries:
                    self._known_entries.add(entry.guid)
                    continue

                request_info = "%s %s\n\n%s" % (
                    self.prefix,
                    entry.title,
                    entry.link)

                for room in self._known_rooms.itervalues():
                    room.speak(request_info)
                    self._known_entries.add(entry.guid)

        reactor.callLater(self.refresh, self.get_feed, False)

    def handle_message(self, campfire, room, message, speaker):
        if room.id not in self._known_rooms:
            self._known_rooms[room.id] = room
        
