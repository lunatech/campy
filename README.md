Introduction
==================

Campy is designed to be a self-contained, self-sufficient bot for Campfire.
It is designed to be highly extensible through a very simple plugin interface.

Campy keeps a home directory (which defaults to `~/.campy`), that it uses as
its base of operations. This includes files it stores, repositories it checks
out, etc. It stores its configuration file in `~/.campy/campy.conf`, but it
will also look in the current directory for a file called `campy.conf` for 
additional configuration. But once you get started with campy, it's less 
and less important. __Campy is meant to be administrable from Campfire.__

Setup
==================

Campy is easily set up. Just clone the repository, configure the settings to be
appropriate for your environment, and run!

	# Check out the repo
	git clone https://github.com/bbelchak/campy
	# Install
	sudo python setup.py install
	# You can run the campy in a non-detaching fashion, for example
	# if you want to do some debugging:
	#		campy-daemon
	# Otherwise, you'll probably want to start campy as a demon:
	campy start
	# When you're done, which will probably be never...
	campy stop

Campy Built-ins
===============

Campy has a number of built-in commands that you might enjoy:

Configuration
-------------

Campy allows you to update its configuration mid-flight. When changes take place,
campy reconfigures its plugins with the update.

	# List the current configuration
	campy config
	# Set some configuration (in JSON)
	campy config set {"my-plugin":{"option":"value"}}
	# Now the configuration as a whole is re-interpreted
	# You can even now __save__ this configuration back to the conf file!
	campy config save

Alias
-----

Long verbose commands are nobody's friend. Thus, alias!

	# List the currently-defined aliases
	campy alias list
	# Now set an alias
	campy alias set hi = say hello, everyone!
	# And execute your alias
	campy alias hi

Shell
-----

While it's not full shell access, you can ask campy to execute certain commands on
its behalf. For this reason, we don't recommend running campy as root.

	# Ask campy to do something
	campy sh echo "hello, everyone"

PIP
---

Campy can even install packages for you as you need them!

	# Install a package
	campy pip install twisted

Git
---

Believe it or not, campy will even checkout / update git projects for you. It saves
them in its home directory

	# Ask campy to clone a repo
	campy git clone git@github.com:you/yourproject.git

Developing plugins
==================

Developing plugins is fun and easy. Check out the plugins directory for a couple
of examples. Here, we'll describe the interface a little bit.

Every plugin must inherit from `campy.plugins.CampyPlugin`. Python modules loaded
into campy are searched for classes that inherit from this class, and then stored.

Every plugin is initialized with a reference to the campy object, and a dictionary
of all the configuration applied to the plugin. It must also implement a `reload`
method that takes the same dictionary of configuration, but this may be done many
times over the lifetime of campy running, where plugin instantiation happens only
once. It's a good practice to implement idempotent reload, and implement `__init__`
in terms of reload:

	from campy import log
	from campy.plugins import CampyPlugin
	
	class MyAwesomePlugin(CampyPlugin):
		shortname = 'awesome'
	
		def __init__(self, campy, **kwargs):
			# You may want to save this for later reference
			self.campy = campy
			# Now use the idempotent reload
			self.reload(**kwargs)
		
		def reload(self, **kwargs)
			# Now, we might set some configurations.
			self.option = kwargs.get('option', 'some default value')

When a plugin, you must also define a shortname, which is the name that identifies
the command to campy. As in, your plugin will only see messages that begin
'`campy <shortname>`'. Your plugin should define two additional methods, `send_help`
and `handle_message`. Both of these take as arguments the campfire client, the room
in which the communication took place, the method object, and the speaker. __All
of these are the analogous pinder objects.__

	...
	def handle_message(self, campfire, room, message, speaker):
		room.speak('Hey everyone, I just heard: "%s"' % message['body'])
	
	def send_help(self, campfire, room, message, speaker):
		room.paste('This is a short explanation of how the command works!')

By the time the message gets to your plugin, the campy bot's name has been stripped
off, __but not your plugin's shortname__. The reason the `send_help` is implemented
as a method and not just a string is that it allows your plugin to handle help for
specific in-plugin commands if it wants.

TODO
===================

* Plugin discovery
	* So that you don't have to necessarily add your plugin to the campy plugin
	directory, but instead, you could install your plugin somewhere, and then
	campy could discover it as needed.
* Built-in commands for dealing with the campy bot
	* 'Stats' => how're things going on campy?
* Develop some other plugins
	* 'seen' plugin
	* 'reminders' plugin
* Further flesh out the plugins system.
	* Basically, I want to have git checkouts stored in ``~/.campy``, and then it
	can add those directories to the path.
	* Also, we need the ability to reload modules if they change.
