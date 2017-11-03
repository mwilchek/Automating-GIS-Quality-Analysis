import pip
import Tkinter as tk
import tkMessageBox
import logging
import os
from subprocess import call

###############################################################################
# Setup Application Logging
logger = logging.getLogger("AAMP")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
file_handler = logging.FileHandler('AAMP.log', mode='w')  # should create new log to overwrite existing log file
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)  # records logging statements to a log file
logger.addHandler(stream_handler)  # prints log statements to the console
###############################################################################

pip.main(['install', '--upgrade', 'pygubu'])
import pygubu


class AAMP_Application(pygubu.TkApplication):

    def _create_ui(self):
        #1: Create a builder
        self.builder = builder = pygubu.Builder()

        #2: Load an ui file
        directory = os.path.abspath(os.chdir(".."))
        builder.add_from_file(directory + r'\GUI\Interface_Main.ui')

        #3: Create the widget using self.master as parent
        self.mainwindow = builder.get_object('mainwindow', self.master)

        #4. Set main menu
        self.mainmenu = menu = builder.get_object('mainmenu', self.master)
        self.set_menu(menu)

        #5. Configure callbacks / call GUI to come up
        builder.connect_callbacks(self)

    ####################################################################################################################
    # Button Functions in GUI
    ####################################################################################################################
    def selectFiletoFile(self):
        """
        Local Method that returns JBID
        :return username: the JBID entered in the GUI as a String variable
        """
        logger.info('New AAMP File to File Session Initiated')
        file_2_file = os.getcwd() + r'\AAMP\File2File_Matching.py'
        call(["python", file_2_file])

    def selectFiletoMAF(self):
        """
        Local Method that returns user password for db
        :return password: the password entered in GUI as a String variable
        """
        logger.info('New AAMP File to MAF Session Initiated')
        file_2_maf = os.getcwd() + r'\AAMP\File2MAF_Matching.py'
        call(["python", file_2_maf])

    def selectMAFtoMAF(self):
        """
        Local Method that returns user password for db
        :return password: the password entered in GUI as a String variable
        """
        tkMessageBox.showinfo('Matching MAF to MAF', 'This is a placeholder to execute MAF to MAF Matching')

    ####################################################################################################################
    # Button Functions in GUI for Help at Top Level
    ####################################################################################################################
    def _create_about_dialog(self):
        builder3 = pygubu.Builder()
        builder3.add_from_file(os.getcwd() + r'\AAMP\GUI\Interface_Main.ui')

        dialog = builder3.get_object(
            'aboutdialog', self.master.winfo_toplevel())
        entry = builder3.get_object('version')
        txt = entry.cget('text')
        txt = txt.replace('%version%', str(1.0))  # Manually Change per new versions of AAMP
        entry.configure(text=txt)

        def on_ok_execute():
            dialog.close()

        builder3.connect_callbacks({'on_ok_execute': on_ok_execute})

        return dialog

    def show_about_dialog(self):
        self.about_dialog = self._create_about_dialog()
        self.about_dialog.run()

########################################################################################################################
if __name__ == '__main__':
        root = tk.Tk()
        app = AAMP_Application(root)
        app.run()
