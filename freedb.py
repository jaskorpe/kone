#!/usr/local/env python

# Copyright (c) 2006 Øyvind Skaar, Jon Anders Skorpen

import telnetlib
import re



# Kone 
#	Module for communicating with freedb serverse
#	CDDB should work equally well, if the server adr. is
#	hardwired, but is complitly untested

class Freedb:

	def __init__(self, parrent, client, version, username, hostname):
		self.connection = None # Telnet objekt
		self.preferred_server = "freedb.freedb.org" # Fallback, should be set to another string by find_best_server()
		self.username = username
		self.hostname = hostname
		self.client = client
		self.version = version
		self.debug = parrent.debug

	
	def find_best_server(self):
		"""
		NOT WORKING, TODO
		Tries to select the best freedb server by getting a list from the 
		official freedb.freedb.org and "pinging" them one by one
		This feature of the freedb server seems to be broke atm, makes this func useless
		(see http://www.freedb.org/en/forum/read.php?1,16 )
		"""
	
		sites = []

		# Connect
		status = self.connect("freedb.freedb.org") # hard-wired official server 
		if status:
			# Something went wrong .. this is bad
			print("Could not connect: %s" % status)
			return None
	
		# get the sites list
		self.connection.write("sites\n")
		for l in self.connection.read_until("\n.", 20).split("\n"): # A dot markes the end of output from the server
			# We only want the servers (and lines) that supports the cddb protocol
			print l
			if "CDDBP" in l:
				sites.append(l)
		self.disconnect()

		# find the "best" one


		# return answer, or None for error


	def discid(self, nr_of_tracks, tableofcontents):
		"""
		Compute the discid from the TOC (availible through the tableofcontents dict.
		"""
		def freedb_sum(n):
			ret = 0
			while (n > 0):
				ret = ret + (n % 10)
				n = n / 10
			return ret
		i = 0
		t = 0
		n = 0

		while (i < nr_of_tracks):
			tmp = tableofcontents[i]['addr']
			n = n + freedb_sum((tmp['min']*60)+tmp['sec'])
			i = i+1;

		tmp1 = tableofcontents[nr_of_tracks]['addr']
		tmp2 = tableofcontents[0]['addr']
		t = ((tmp1['min']*60)+tmp1['sec']) - ((tmp2['min']*60)+tmp2['sec'])

		return "%08x" % ((n % 0xff) << 24 | t << 8 | nr_of_tracks )
	

	def discid_remote(self, nr_of_tracks, offset_list, total_len):
		"""
		Asks the server to compute the discid (instead of doing this ourself)
		returns this id as a string
		"""

		status = self.connect()
		if status:
			print ("could not connect to remote server: %s" % status )
			return None
	
		offsets = ""
		for o in offset_list: offsets += str(o) + " ";
		q = "discid %d %s %d\n" % (nr_of_tracks, offsets, total_len) 
		self.connection.write(q) 
		self.connection.write("help help\n") # to get a reply thats acutally parsable
		if self.debug: print " discid_remote() sendt:\n\"%s\"" % q
		a = self.connection.read_until("\n.", 5)
		match = re.search(r"200\s*Disc\s*ID\s*is\s*(\w+)", a)
		if not match:
			print "Could not get DiscID in discid(), server returned:\n\t %s" % a
			return None
		discid = match.group(1)	
		return discid


	def query(self, discid, nr_of_tracks, offset_list, total_len):	
		"""
		Ask the server for matches,
		can be zero, one or more
		this function _must_ be called before the other cddb function read()
		"""

		status = self.connect()
		if status:
			print ("could not connect to remote server: %s" % status )
			return None
	
		# Get a list of matches
		# the first line is either:
		#	200 categ discid dtitle
		# or:	211 close matches found
		# or:	210 Found exact matches, list follows (until terminating marker)
		# or:	Another code
		#
		# If code is 210 or 211 the next lines (until .) are the matches, on the form:
		#	categ discid dtitle
		# Codes:
		#	200	Found exact match
		#	210 	Found exact matches, list follows (until terminating marker)
		#	211	Found inexact matches, list follows (until terminating marker)
		#	202	No match found
		#	403	Database entry is corrupt
		#	409	No handshake

		offsets = ""
		for o in offset_list: offsets += str(o) + " "; # Make a string of the list of frame offsets

		# expected answers (index used to understand the response)
		expected = [
		"200.*$",	# exact match
		"202", 		# no match
		"403", 		# db entry corrupt
		"409", 		# no handshake (HELLO)
		"\n\." ]	# 210 & 211. They require more output

		q = "CDDB QUERY %s %d %s%d\n" % (discid, nr_of_tracks, offsets, total_len)
		self.connection.write(q)
		(index, match, text) = self.connection.expect(expected, 10)
	
		# DEBUG INFO	
#		print "match: " 
#		print text
#		print index
#		print expected

		if not match:
			# No reg. exp. match, this is an error and does not mean 
			# 	the cd was not found
			print "Did not understand CDDB QUERY response, got %s" % text
			print "\n and sendt: %s" % q
			return None
	
		# Parse reply
		text = text.strip()
		cds = []
		#      code    cat      discid       disctile (eg Artist / Album)	
		r = r"(\d*)\s*(\w+)\s*([a-z0-9]+)\s*(.*)"
		if   index is 0:
			m = re.search(r, text)
			cds.append( m.group(2,3,4) )
		elif index is 1:
			# Do _something_ indecating that the cd was not found in the db
			pass
		elif index is 2:
			print "Server said the db entry is corrupt (403):\n\t%s" % text
			return None
		elif index is 3:
			print "Server said \"No handshake\" (409):\n\t%s" % text
			return None
		elif index is 4:
			for line in text.split("\n")[1:-1]: # dont need the 1st or the last line
			
				m = None
				m = re.search(r, line)
				if not m:
					print " Error parsing in query(), got:"
					print "\"%s\"" % line
				cds.append( m.group(2,3,4) )
	
		return cds	

	
	def read(self, cat, discid):
		"""
		Get the cd-data from the db
		query() _must_ be called befor this function, 
		even if we already have the needed info: cat & discid
		(this is required by the server, failing to do so may result in wrong data !!)
		"""

		self.connection.write("CDDB READ %s %s\n" % (cat, discid) )
		# expected answers (index used to understand the response)
		expected = [
		"\n401",	# Specified CDDB entry not found.
		"\n402",	# Server error.
		"\n403",	# Database entry is corrupt.
		"\n409",	# No handshake.
		"\n\."	# (210) OK, CDDB database entry follows (until terminating marker)
		]
		(index, match, text) = self.connection.expect(expected, 10)

		if   index is 0:
			# Do _something_ indecating that the cd was not found in the db
			print "CD was not found in the db"
			if self.debug: print text
			return None
		elif index is 1:
			print "FreeDB server error (402) in read()"
			return None
		elif index is 2:
			print "Server said the db entry is corrupt (403):\n\t%s" % text
			return None
		elif index is 3:
			print "Server said \"No handshake\" (409):\n\t%s" % text
			return None
		elif index is 4:
			# Ok, output follows
	
			# make a list
			list = text.split("\n")
			list = [ x for x in list if x and x[0] is not "#" ]

			dtitle	= [ x[7:] for x in list if "DTITLE" in x ][0]
			(artist, album) = re.search(r"(.*)\s/\s(.*)", dtitle).group(1,2)
			(artist, album) = (artist.strip(), album.strip() ) # Strip newline (if any)
			year	= [ x[6:].strip() for x in list if "DYEAR" in x ][0]
			genre	= [ x[7:].strip() for x in list if "DGENRE" in x ][0]
			titles	= [ re.search(r"(\w+\d+=)(.*)", x).group(2).strip() for x in list if "TTITLE" in x ]
		
			return (artist, album, year, genre, titles)

	
	def connect(self, adr=None):
		"""
		(Re)Connect to a freedb server, return an message on error (or _at least_ != 0)
		"""
		port = 8880

		if not adr:
			adr = self.preferred_server

		if self.connection:
			# already connected, disconnect() (could be wrong server, or dead connection)
			# TODO: Implement a check to stop reconnecting if not necessary
			self.disconnect()

		self.connection = telnetlib.Telnet(adr, port)

		# test connection
		self.connection.write("\n")
		self.connection.write("proto 6\n") # set protocol level 6
		a = self.connection.read_until("now: 6", 10)
		if not "OK" in a:
			return "Connection not working properly in connect()"

		# say hi
		self.connection.write("CDDB HELLO %s %s %s %s\n" % (self.username, self.hostname, self.client, self.version) )
		a = self.connection.read_until(self.version + ".", 5)
		if not a:
			print "server did not respond to our polite hello.. "
			return None
	

	def disconnect(self):
		"""
		Disconnect from whatever server we are connected to and remove the pointer Telnet obj.
		"""

		if self.connection:
			self.connection.close()
		self.connection = None	


if __name__ == "__main__":
	# run some tests
	
	# fake a parrent
	import kone
	parrent = kone.Kone("kone", "0.1", "/dev/acd0", 1, "os", "gunda.odots.org")


	l = ["150", "20825", "47257", "68720", "93935", "113557", "133887", "153737", "163640", "181920", "197050" ] 
	id = "8e0b6f0b"
	nr = 11
	len = 2929

	l = ['150', '26282', '51500', '76850', '101592', '121407', '143785', '154072', '178470', '209117', '237547', '237968', '257870', '275813']
	nr = 14
	len = 3834


	id = parrent.fdb.discid_remote(nr, l, len)
	print id
	print "d40ef80e"
	print parrent.debug

	cds = parrent.fdb.query(id, nr, l, len )
	(artist, album, year, genre, titles) = parrent.fdb.read(cds[0][0], cds[0][1]) 

	print artist
	print album
	print year
	print genre
	print titles


