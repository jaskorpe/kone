# Copyright (c) 2006 Øyvind Skaar, Jon Anders Skorpen

import threading
import os

class Rip (threading.Thread):

    def __init__(self, gui, debug):
        self.gui = gui
        self.debug = debug

        threading.Thread.__init__ ( self )

    def run (self):
        """
        This function gets calles when we press "Extract songs".
        It will run cdparanoia and oggenc or lame to perform the
        main function of the program, namely to rip music.
        """

        format, artist, album, year, genre, songs = self.gui.get_cd_info()

        os.mkdir(('%s - %s' % (artist, album)))
        os.chdir(('%s - %s' % (artist, album)))

        self.gui.rip_started(len(songs[1]))
        # - Does not work, nothing happens before controll is returned to the gtk.main()
	# Need sepperate threads - TODO 
	# "Ill fix this on 17.11 and not use the whole day to talk about stargate" -jascorpe
	# :)
        # a couple of years later, and it works!

        for i in range(len(songs[0])):
            # filename without three letter extension
            filename = ('%s-%s-%s' % (songs[0][i], songs[1][i], artist))
            tmp = "cdparanoia -q %s - |" % songs[0][i]
            if ("Mp3" in format):
                tmp = ('%s lame -V 2 --quiet --tt "%s" --ta "%s" --tl "%s" --ty "%s" --tn "%s" --tg "%s" - "%s.mp3"' % (tmp, songs[1][i], artist, album, year, songs[0][i], genre, filename))
            elif ("Ogg" in format):
                tmp = '%s oggenc -a "%s" -G "%s" -N "%s" -t "%s" -l "%s" -o "%s.ogg" -' % (tmp, artist, genre, songs[0][i], songs[1][i], album, filename)
            self.gui.rip_update(songs[1][i]) #threads TODO
            if self.debug: print tmp
            os.system(tmp)

        os.chdir('../')

        self.gui.popup("Ferdig :D", ["Jiipii"])
        self.gui.rip_finished()
