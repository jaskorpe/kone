#!/usr/bin/env python

# Copyright (c) 2006 Øyvind Skaar, Jon Anders Skorpen

# GUI module, responsible for creating and updating the GUI and retrive info from it.

import pygtk
pygtk.require("2.0")
import gtk, gobject

class GUI:
	"""
	Gui class to make the gui.
	"""

	def delete_event(self, widget, event, data=None):
		"""
		Called when the window manager sends exit
		"""
		self.destroy()
	
	def destroy(self, a1=None):
		"""
		Self-destroy aka quit
		"""

		if self.debug:
			print a1 
		gtk.main_quit()

	def __init__(self, parrent):
		"""
		Constructor
		"""

		# Set some variables
		self.debug = parrent.debug 	# Needed elsewhere, dont want to have to pass parrent arround all the time
		self.store = None		# initialize for the show_cd_info() function
	
		# Main window
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window .set_title( parrent.client+ "v " + str(parrent.version) )
		self.window.connect("delete_event", self.delete_event )
		self.window.set_border_width(10)

		# Main box
		self.box_main = gtk.HBox(False, 0)
		self.window.add(self.box_main)
		self.box_main.show()

		# A frame for buttons and ..?
		self.frame_left = gtk.Frame()
		self.box_main.pack_start(self.frame_left)

		# button row
		self.bbox = gtk.VButtonBox()
		self.frame_left.add(self.bbox)
		self.bbox.show()

		# buttons
		self.button = gtk.Button("Read cd")
		self.button.connect("clicked", parrent.read_cd, self)
		self.button.show()
		self.bbox.add(self.button)
		self.button = gtk.Button("Quit")
		self.button.connect("clicked", self.destroy)
		self.bbox.add(self.button)
		self.bbox.set_child_secondary(self.button, True)
		self.button.show()
		# Create the rip -button
		self.button_rip = gtk.Button("Extract songs")
		self.button_rip.connect("clicked", parrent.rip, self)
		self.bbox.add(self.button_rip)
		
		# Show the frames
		self.frame_left.show()


	def show_cd_info(self, artist, album, year, genre, titles):
		"""
		Creates and shows a ListStore, TreeView etc for displaying the cd info.
		"""

		# Does the objects exist already? if so, update them and return
		if self.store:
			# Remove everything from the ListStore
			self.store.clear()
			# Add data to the ListStore
			for i in range(len(titles)):
				self.store.append( [True, i+1, titles[i] ] )

			self.artist.set_text(artist)
			self.album.set_text(album)
			self.year.set_text(str(year))
			self.genre.set_text(genre)

			return

		# A box for holding the info
		box = gtk.VBox()
		
		
		# Store and show artist, album, year & genre
		# needs to ba acsessable from other funcs
		self.artist	= gtk.Entry(max=100) # Text entry, max 100 chars
		self.artist.set_text(artist)
		self.album	= gtk.Entry(max=100) # Text entry, max 100 chars
		self.album.set_text(album)
		self.year	= gtk.Entry(max=100) # Text entry, max 100 chars
		self.year.set_text(str(year))
		self.genre	= gtk.Entry(max=100) # Text entry, max 100 chars
		self.genre.set_text(genre)

		# A ListStore to store the tracks
		self.store = gtk.ListStore(gobject.TYPE_BOOLEAN,	 int, 		str)
		#			rip-this-song toggle -	tracknr -    song name

		# TreeView
		treeview = gtk.TreeView(self.store)
		treeview.set_rules_hint(True) # Se those uber cool colorized rows

		# Add data to the ListStore
		for i in range(len(titles)):
			self.store.append( [True, i+1, titles[i] ] )	

		# editable cells
		cell_renderer0 = gtk.CellRendererToggle()	# Col. 0
		cell_renderer0.set_property("activatable", True)
		cell_renderer1 = gtk.CellRendererText()		# Col. 1
		cell_renderer1.set_property("editable", True)
		cell_renderer2 = gtk.CellRendererText()		# Col. 2
		cell_renderer2.set_property("editable", True)


		# handle changed cells
		def col0_changed(cell, path):
			""" Column 0 changed, update store with new info """
			self.store[path][0] = not self.store[path][0]
		def col1_changed(cell, path, new_text):
			""" Column 1 changed, update store with new info """
			self.store[path][1] = int(new_text)
		def col2_changed(cell, path, new_text):
			""" Column 2 changed, update store with new info """
			self.store[path][2] = new_text

		cell_renderer0.connect('toggled',col0_changed)	
		cell_renderer1.connect('edited', col1_changed)	
		cell_renderer2.connect('edited', col2_changed)	

		# make columns
		column0 = gtk.TreeViewColumn("Extract", cell_renderer0)
		column1 = gtk.TreeViewColumn("Track number", cell_renderer1)
		column2 = gtk.TreeViewColumn("Song title", cell_renderer2)
		
		# insert the data from the store
		column0.set_attributes(cell_renderer0, active=0) # what cell - column in store to read the info from
		column1.set_attributes(cell_renderer1, text=1)
		column2.set_attributes(cell_renderer2, text=2)

		treeview.append_column( column0 )
		treeview.append_column( column1 )
		treeview.append_column( column2 )
		
		# Let the user select what format to use
		self.dropdown = gtk.combo_box_new_text() # dropdown is read from other functions
		self.dropdown.append_text("Mp3 (using lame)")
		self.dropdown.append_text("Ogg (using OggEnc)")
		self.dropdown.set_active(0) # Set default value
	
		# pack
		box.pack_start(treeview)
		box.pack_start(self.artist)
		box.pack_start(self.album)
		box.pack_start(self.year)
		box.pack_start(self.genre)
		box.pack_start(gtk.Label("Select encoding format") )
		box.pack_end(self.dropdown)
		self.box_main.pack_end(box)

		# show 
		box.show_all()
		self.bbox.show_all() # Show all the buttons (e.g the "extract button" since the other one is already shown)
	

	def get_cd_info(self):
		"""
		Returns cd info and a, possibly modyfied list, of songs needs to be extracted
		on the format: 
		[[1, 4], ['song nr 1', 'song nr 4']]
		"""

		# make a list
		songs = [ [],[] ]
		for i in range(len(self.store)):
			if self.store[i][0]:
				# It is selected, add it to the list
				songs[0].append( self.store[i][1] )
				songs[1].append( self.store[i][2] )
		
		# the format (eg. MP3) 
		#		format = self.dropdown.get_active_text()
		# Workarround for pygtk 2.4 and older
		model = self.dropdown.get_model()
		active = self.dropdown.get_active()
		format = model[active][0]

		return( format, self.artist.get_text(), self.album.get_text(), self.year.get_text(), self.genre.get_text(), songs )


	def show_string(self, s):
		# Text label
		self.label = gtk.Label(s)
		self.label.set_justify(gtk.JUSTIFY_CENTER)
		self.label.set_line_wrap(True)
		self.box_main.pack_end(self.label)
		self.label.show()

	def popup(self, text, buttons):
		"""
		Creates and shows a opoup window
		Returns what button (if any) the user pressed
		"""
		self.button_clicked = None

		def button_clicked(s, button_nr):
			"""
			Helper method for popup()
			"""
			self.button_clicked = button_nr
			dialog.destroy()

		dialog = gtk.Dialog(flags=gtk.DIALOG_DESTROY_WITH_PARENT)

		for x in range(len(buttons)):
			button = gtk.Button(buttons[x])
  			dialog.action_area.pack_start(button, True, True, 0)
			button.connect("clicked", button_clicked, x)
  			button.show()
  		
		label = gtk.Label(text)
 		dialog.vbox.pack_start(label, True, True, 0)
  		label.show()
		dialog.show()

		return self.button_clicked	

	def rip_started(self, nr_of_tracks):
		"""
		Metthod called when the extracting is started
		Hides the cdinfo and shows a progress bar instead
		"""
		
		text = "Starting extractig"	

		self.box_progress = gtk.VBox()

		self.progressbar = gtk.ProgressBar();
		self.progressbar.set_pulse_step(1.0/nr_of_tracks)
		self.progressbar.set_text(text)
		self.box_main.hide_all();

		# A label above the bar
		self.progressbar_label = gtk.Label(text)

		self.box_progress.pack_end(self.progressbar)
		self.box_progress.pack_start(self.progressbar_label)
		self.box_main.pack_start(self.box_progress)

		self.box_progress.show_all()
		self.box_main.show()

	
	def rip_update(self, text):
		"""
		Updates the progressbar with \"text\"
		and pulse()'s the bar to show some progress
		Called after each track is extracted/rip'ed
		"""
		
		self.progressbar_label.set_text(text)
		self.progressbar.set_text(text)
		self.progressbar.pulse()


	def rip_finished(self):
		"""
	       Hides progressbar and shows main cdinfo
		"""
		self.box_progress.hide_all()
		self.box_main.show_all()


	def run(self):
		gtk.gdk.threads_init()
		if self.debug:
			print "run"
		self.window.show()
		gtk.main()


if __name__ == "__main__":
	
	# fake a parrent
	import kone
	parrent = kone.Kone("kone", "0.1", "/dev/acd0", 1, "os", "gunda.odots.org")

	gui = GUI(parrent)
	
	# test show_cd_info()
	gui.show_cd_info("Petter Pettersen", "Petter synger julen inn", 2007, "Metal", ["eg og gitaren min", "lalalala", "petter synger weee", "petter imploderer" ] )
	gui.show_cd_info("-", "-", 2000, "-", ["-", "-", "-", "-" ] )

	print gui.popup("dette er en test", ["close","cancel" ,"ok", "make snow"] )

	gui.run()

	print " back from gui.run()"
	print gui.button_clicked





# test freedb: REMOVE ME
#l = ["150", "20825", "47257", "68720", "93935", "113557", "133887", "153737", "163640", "181920", "197050" ]
#id = "8e0b6f0b"
#cds = freedb.query(id, 11, l, 2929)
#cds = freedb.read(cds[0][0], cds[0][1] )


