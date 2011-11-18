Introduction
==================

Campy is designed to be a self-contained, self-sufficient bot for Campfire.
It is designed to be highly extensible through a very simple plugin interface.

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

Developing plugins
==================

Developing plugins is fun and easy. Check out the plugins directory for a couple
of examples. I am sure there are improvements that can be made, but it's a start.

TODO
===================

* Plugin discovery
	* So that you don't have to necessarily add your plugin to the campy plugin
	directory, but instead, you could install your plugin somewhere, and then
	campy could discover it as needed.
* Built-in commands for dealing with the campy bot
	* 'Stats' => how're things going on campy?
* Message regex registration mechanism
	* The idea is that plugins would register for the kinds of messages they get,
	so that campy can more easily determine if it knows how to handle a given type
	of message.
* Develop some other plugins
	* 'seen' plugin
	* 'reminders' plugin
* Further flesh out the plugins system.
