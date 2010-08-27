#!/usr/bin/env python

# Copyright (c) 2006 Øyvind Skaar, Jon Anders Skorpen

import os, fcntl, struct, sys


class CD:
	"""
	When making a new instance of this class you must supply
	the device name of the cdrom you want to read. 
	At this point it only supports linux.
	"""

	def __init__(self, dev):
		"""
		This constructor takes device name as argument.
		"""

		self.dev = dev


		# These are linux specific
		# Maybe add for bsd too?
		if sys.platform == "linux2":
			# Operations for ioctl
			self.CDROMREADTOCHDR = 0x5305
			self.CDROMREADTOCENTRY = 0x5306
			self.CDROMEJECT = 0x5309
			self.CDROMCLOSETRAY = 0x5319
			self.CDROM_LOCKDOOR = 0x5329
		elif sys.platform == "freebsd6":
			self.CDROMREADTOCHDR = 0x40046304
			self.CDROMREADTOCENTRY = -1072930042
			self.CDROMEJECT = 0x20006318
			self.CDROMCLOSETRAY = 0x2000631c

		
		# Lead out track
		self.CDROM_LEADOUT = 0xAA

		# Addressing mode
		self.CDROM_LBA = 0x01
		self.CDROM_MSF = 0x02


		self.debug = 0
		self.numberoftracks = 0

		print dev


	def opencdrom(self, name):
		"""
		Function to open the cdrom device
		Takes name of device as argument
		"""
		# According to <linux/cdrom.h> we need to open
		# the device without blocking
		return os.open(name, os.O_RDONLY)

	def readtoc(self):
		"""
		Reads the table of contents of the cd.
		Everything is put in the object variable
		tableofcontents. It returns the number of
		tracks found on the disk, excluding lead out.
		"""

		self.tableofcontents = []

		fd = self.opencdrom(self.dev)

		# The toc header is a struct with to members
		# of type __u8, wich is a typedef for unsigned char
		if sys.platform == "linux2":
			tocfmt = 'BB'	
			entryfmt = '3BiB'
			unionfmt = '3Bx'
		elif sys.platform == "freebsd6":
			tocfmt = 'xBB'
			entryfmt = '2Bxxx2Bxi'
			unionfmt = 'x3B'

		toc = struct.pack(tocfmt, 0, 0)

		try:
			toc = fcntl.ioctl(fd, self.CDROMREADTOCHDR, toc)
		except IOError:
			os.close(fd)

			if self.debug: print "Could not open cdrom"

			return -1

		start, end = struct.unpack(tocfmt,toc)

		self.numberoftracks = end

		if self.debug:
			print "Start: ", start, ", End: ", end


		# the struct cdrom_tocentry contains first
		# one unsigned char, then two bitfields, with
		# a width of four, and then another unsigned char.
		# Cant seem to find anything about bit fields in
		# python, but it seems that it works. Although
		# bitfields can be dodgy in c also. This adds
		# up to 3 unsigned chars. There is also a union
		# with the size of an integer, and at last
		# one more unsigned char.
		#fmt = '3BiB'


		oldmin = 0
		oldsec = 0
		for tracknr in range(start, end + 1) + [self.CDROM_LEADOUT]:
			# We want address in MSF format.
			if sys.platform == "linux2":
				te = struct.pack(entryfmt, tracknr, 0, self.CDROM_MSF, 0, 0)
			elif sys.platform == "freebsd6":
				te = struct.pack(entryfmt, self.CDROM_MSF, tracknr, 0, 0, 0)

			try:
				te = fcntl.ioctl(fd, self.CDROMREADTOCENTRY, te)
			except IOError:
				print "IOError"
				os.close(fd)

				if self.debug: print "Could not read cdrom"

				return -1

			if sys.platform == "linux2":	
				track, adrctrl, format, addr, mode = struct.unpack(entryfmt, te)
			elif sys.platform == "freebsd6":
				format, tmp, adrctrl, track, addr = struct.unpack(entryfmt, te)
				mode = 0
			
			# The union contains a struct of type cdrom_msf, and this
			# contains three unsigned characters. Because it is the size
			# of an integer we must pad with a byte.
			min, sec, frame = struct.unpack(unionfmt, struct.pack('i', addr))
			adr = adrctrl & 0xf
			ctrl = adrctrl >> 4

			# We are not interested in the last track since it is
			# just lead out
			#if track != CDROM_LEADOUT:
			self.tableofcontents.append({"track":track, "adr":adr, "ctrl":ctrl,
						"format":format, "addr":{"min":min,
						"sec":sec, "frame":frame},
						"mode":mode, "time":0})
			# The only thing we need the lead out is to know the
			# length of the last track
			if track != start:
				if track != self.CDROM_LEADOUT:
					dic = self.tableofcontents[track-2]
				else:
					dic = self.tableofcontents[end-1]
				dic['time'] = ((min*60)+sec) - ((dic['addr']['min']*60)+dic['addr']['sec'])

			if self.debug:			
				print "Track: ", track, " adr: ", adr, " ctrl: ", ctrl
				print "format: ", format, " mode: ", mode
				print "start: ", min, "m,", sec, "s\n"

		os.close(fd)
		return self.numberoftracks

	
	def cd_eject(self, file):
		"""
		This takes the devicename as argument and tries
		to eject the cd.
		"""
		fd = opencdrom(file)
		fcntl.ioctl(fd, self.CDROMEJECT)
		os.close(fd)

	def return_offset_list(self):
		"""
		Returns a list with offset (address) of each track,
		including lead out. 
		"""
		offset_list = []
		for i in self.tableofcontents:
			if (i['track'] != self.CDROM_LEADOUT):
				j = i['addr']
				offset_list.append((j['min']*60*75)+(j['sec']*75))
		return offset_list

	def return_len(self):
		"""
		Returns length of the cd in seconds.
		"""
		tmp = self.tableofcontents[-1]['addr']
		last = (tmp['min']*60)+tmp['sec']
		tmp = self.tableofcontents[0]['addr']
		first = (tmp['min']*60)+tmp['sec']
		return last - first

if __name__=="__main__":
	dev = sys.argv[1]
	c = CD(dev)
	tracks = c.readtoc()
	if (tracks == -1):
		print "Error"
		sys.exit()
	print "Number of tracks: ", tracks

	for i in c.tableofcontents:
		time = i['time']
		sec = time%60
		min = (time-sec)/60
		print "Track: %i - Time: %imin %isec" % (i['track'], min, sec)

	#print freedb.discid(tracks, cdrom.tableofcontents)
	print c.return_len()
	print c.return_offset_list()
	#c.cd_eject(dev)
