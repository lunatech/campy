#! /usr/bin/env python

dependencies = ['twisted', 'simplejson', 'BeautifulSoup', 'httplib2', 'pyopenssl', 'feedparser', 'pinder', 'pyyaml', 'argparse']

try:
    from setuptools import setup
    from setuptools.extension import Extension
    extra = {
        'install_requires' : dependencies
    }
except ImportError:
    from distutils.core import setup
    from distutils.extension import Extension
    extra = {
        'dependencies' : dependencies
    }

setup(name           = 'campy',
    version          = '0.1.0',
    description      = 'A Campfire Bot for Python',
    long_description = 'Based on pinder, campy makes it easy to write plugins for your favorite group chat.',
    url              = 'https://github.com/bbelchak/campy',
    author           = 'Ben Belchak',
    author_email     = 'ben@needle.com',
    keywords         = 'campfire, pinder, campy, bot',
    packages         = ['campy', 'campy.plugins'],
    scripts          = ['bin/campy', 'bin/campy-daemon'],
    classifiers      = [
        'Topic :: Internet :: WWW/HTTP',
        'Programming Language :: Python',
        'topic :: Communications :: Chat',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
    ],
    **extra
)