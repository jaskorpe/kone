#!/usr/bin/env python


if __name__ == "__main__":
	import sys, os, socket
	import freedb, gui, cdrom
	
	
	# Configuration
	client		= "Kone"
	version		= "0.3"
	
	# Get the hostname & username from the os,
	# used in communication with the freedb server
	username	= os.getlogin()
	hostname	= socket.gethostname()
	
	# Debug, print extra information
	debug = 0

	# Check line arguments 
	if len(sys.argv)>1:
		if "help" in sys.argv[1]:
			# Print out a simple usage message to stdout
			print "Usage:\n\t%s [cdrom device]" % sys.argv[0]
			sys.exit(0)
		else:	
			# does the device exist?
			if os.path.isfile(sys.argv[1]) or os.path.islink(sys.argv[1]):
				cd_device = sys.argv[1]
			else:
				print "%s is not a valid cdrom device, run %s -help for help" % (sys.argv[1], sys.argv[0])
				sys.exit(1)
	else: cd_device = "/dev/cdrom"



class Kone:
	"""
	The main class of the program. IT ties the other modules toghether.
	"""

	def __init__(self, client, version, debug, username, hostname, cd):
		"""
		This takes name and version of the program, debug, and username and hostname
		for freedb interaction. The last argument is the CD object.
		"""

		# Set some variables
		self.client		= client
		self.version		= version
		self.cd			= cd
		self.debug		= debug


		# Create a freedb object
		self.fdb = freedb.Freedb(self, client, version, username, hostname)


	def rip(self, source_button, gui):
		"""
		This function gets calles when we press "Extract songs".
		It will run cdparanoia and oggenc or lame to perform the
		main function of the program, namely to rip music.
		"""

		format, artist, album, year, genre, songs = gui.get_cd_info()
		#gui.rip_started(len(songs[1])) - Does not work, nothing happens before controll is returned to the gtk.main()
		#					Need sepperate threads - TODO 
		#					"Ill fix this on 17.11 and not use the whole day to talk about stargate" -jascorpe
		#						:)

		for i in range(len(songs[0])):
			# filename without three letter extension
			filename = ('%s-%s-%s' % (songs[0][i], songs[1][i], artist))
			tmp = "cdparanoia -q %s - |" % songs[0][i]
			if ("Mp3" in format):
				tmp = ('%s lame -V 2 --quiet --tt "%s" --ta "%s" --tl "%s" --ty "%s" --tn "%s" --tg "%s" - "%s.mp3"' % (tmp, songs[1][i], artist, album, year, songs[0][i], genre, filename))
			elif ("Ogg" in format):
				tmp = '%s oggenc -a "%s" -G "%s" -N "%s" -t "%s" -l "%s" -o "%s.ogg" -' % (tmp, artist, genre, songs[0][i], songs[1][i], album, filename)
		#	gui.rip_update(songs[1][i]) threads TODO
			if self.debug: print tmp
			os.system(tmp)

		gui.popup("Ferdig :D", ["Jiipii"])


	def read_cd(self, source_button, gui):
		"""
		This will call on the function in the cd object to extract the
		table of contents from the cd. Then it will obtain info from freedb
		"""

		nrtracks = self.cd.readtoc()
		if debug: print nrtracks
		if nrtracks < 0:
			# Not good ..
			gui.popup("Could not read the cd", ["Close"] )	
			return None
		id = self.fdb.discid(nrtracks, self.cd.tableofcontents)
		cds = self.fdb.query(id, nrtracks, self.cd.return_offset_list(), self.cd.return_len())
		if not cds:
			gui.popup("Could not get the album information from freedb", ["Ok"])
		cdinfo = self.fdb.read(cds[0][0], cds[0][1])
		if not cdinfo:
			gui.popup("Could not get the album information from freedb", ["Ok"])
			"fdb.read() failed in read_cd in kone.py got:"
			cdinfo
			return None
		artist, album, year, genre, tracks = cdinfo
		gui.show_cd_info(artist, album, year, genre, tracks)

		# Show the rip -button
		gui.button_rip.show()


if __name__ == "__main__":
	
	# Create cdrom
	if debug: print "device in kone.py: %s" % cd_device 
	cd = cdrom.CD(cd_device)
	
	# Create self
	kone = Kone(client, version, debug, username, hostname, cd)
	
	# Create the gui
	gui = gui.GUI(kone)


	# Run the gui
	gui.run()
