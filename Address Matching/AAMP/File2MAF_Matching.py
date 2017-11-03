import Tkinter as tk
import os
import tkMessageBox
import cx_Oracle as Oracle
import pip
import sys
import logging
from Data_Standardization.LocalFileExtraction import LocalExtraction
from MAF_Extraction.MAF_DataExtraction import MAFextract
from Matching_Algorithms.Matching import Match

pip.main(['install', '--upgrade', 'pygubu'])
import pygubu

# Setup Logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
file_handler = logging.FileHandler('AAMP.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# noinspection PyGlobalUndefined
class File2MAF_Application(pygubu.TkApplication):
    def _create_ui(self):
        # 1: Create a builder
        self.builder2 = builder2 = pygubu.Builder()

        # 2: Load an ui file
        # directory = os.path.abspath(os.chdir('..'))                        # Before zipping comment this line
        builder2.add_from_file(os.getcwd() + r'\GUI\Interface_File2MAF.ui')  # and change 'directory' to 'os.getcwd()'

        # 3: Create the widget using self.master as parent
        self.mainwindow = builder2.get_object('File2MAF', self.master)

        # 4: Set default choices to GUI
        self.builder2.tkvariables['env'].set("PRODTRAN")
        self.builder2.tkvariables['blockingType'].set("ZIP")  # set default blocking type to 'ZIP'
        self.builder2.tkvariables['detail'].set("BEST")  # set default output detail type to 'BEST'
        self.builder2.tkvariables['jwThreshold'].set(1.00)

        # Configure callbacks
        builder2.connect_callbacks(self)

    ####################################################################################################################
    # Button Functions in GUI
    ####################################################################################################################
    def get_project_name(self):
        """
        Local method that returns project name for matching from GUI
        :return project_name: String variable of project name
        """
        project_name = self.builder2.tkvariables['projectName'].get()
        return project_name

    def get_jbid(self):
        """
        Local Method that returns JBID from GUI
        :return username: the JBID entered in the GUI as a String variable
        """
        username = self.builder2.tkvariables['username_entry'].get()
        return username

    def get_password(self):
        """
        Local Method that returns user password for db from GUI
        :return password: the password entered in GUI as a String variable
        """
        password = self.builder2.tkvariables['password_entry'].get()
        return password

    def get_env(self):
        """
        Local Method that returns user password for db from GUI
        :return password: the password entered in GUI as a String variable
        """
        env = self.builder2.tkvariables['env'].get()
        return env

    def get_file_parameter(self):
        """
        Local Method that returns string path of file to standardize/match with from GUI
        :return fileParam: string variable to local path file
        """
        fileParam = self.builder2.tkvariables['fileParameter'].get()
        return fileParam

    def get_block_type(self):
        """
        Local Method that returns blocking type used for matching from GUI
        :return blkType: string variable for match() class object
        """
        blkType = self.builder2.tkvariables['blockingType'].get()
        return blkType

    def get_m_level(self):
        """
        Local Method that returns mlevel type used for matching from GUI
        :return mlevel: string variable used for match() class object
        """
        mlevel = self.builder2.tkvariables['mLevel'].get()
        return mlevel

    def get_jw_threshold(self):
        """
        Local Method that returns jaro wrinkler threshold value for matching from GUI
        :return jwThreshold: double variable used for match() class object
        """
        jwThreshold = self.builder2.tkvariables['jwThreshold'].get()
        return jwThreshold

    def get_lvl(self):
        """
        Local Method that returns level of matching exactness for matching from GUI
        :return password: string variable used for match() class object
        """
        lvl = self.builder2.tkvariables['lvl'].get()
        return lvl

    def get_detail_output(self):
        """
        Local Method that returns level of detail for output file of results from matching from GUI
        :return detail: string variable used for match() class object
        """
        detail = self.builder2.tkvariables['detail'].get()
        return detail

    def get_output_path(self):
        """
        Local method that returns output directory of results for matching
        :return output_path: string variable of a path directory
        """
        output_path = self.builder2.tkvariables['outputPath'].get()
        return output_path

    def update_progress(self, value):
        """
        Local method for execute() method to call to update progress on GUI of matching
        :param value:
        :return updated progress in GUI:
        """
        self.builder2.tkvariables['progress'].set(value)

    def test_connection(self):

        username = self.get_jbid()
        password = self.get_password()

        try:
            host = 'PRODTRAN'
            Oracle.connect(username, password, host)
            logger.info('Database Connection Test Successful from GUI')
        except Oracle.DatabaseError as e:
            error, = e.args
            if error.code == 1017:
                tkMessageBox.showerror('Oracle Connection Error', 'Please check your credentials.')
            else:
                tkMessageBox.showerror('Oracle Connection Error', 'Database connection error: %s'.format(e))
            # Very important part!
            raise
        except TypeError:
            tkMessageBox.showerror('Oracle Connection Error', 'Please check your credentials.')
            # Very important part!
            raise
        return tkMessageBox.showinfo('Oracle Connection', 'A connection was successfully made.')

    ####################################################################################################################
    # Main Button for Matching Execution
    ####################################################################################################################
    def execute(self):
        local_input = self.get_file_parameter()
        jbid = self.get_jbid()
        password = self.get_password()
        env = self.get_env()

        # Standardize Data
        self.update_progress(10)  # 10
        local_extraction_file, blocks_4_maf, oracle_user = LocalExtraction().run(local_input, jbid, password, env)
        self.update_progress(20)  # 30

        # Get MAF Data to Compare with
        foreign_file = MAFextract().run(blocks_4_maf, oracle_user, self.get_output_path())
        self.update_progress(20)  # 50

        # Read in matching parameters
        project_name = self.get_project_name()
        block_type = self.get_block_type()
        m_level = self.get_m_level()
        jw_threshold = self.get_jw_threshold()
        level = self.get_lvl()
        detail = self.get_detail_output()

        out_file = r'\AAMP_' + project_name + '_' + block_type + '_' + m_level + '_' + str(
            jw_threshold) + '_' + level + '_' + detail + '.txt'
        output_file = self.get_output_path() + out_file

        # Execute Matching
        new_match = Match(blocks_4_maf, local_extraction_file, foreign_file, output_file, block_type, m_level,
                          jw_threshold, level, detail)
        new_match.run(blocks_4_maf, local_extraction_file, foreign_file, output_file, block_type, m_level,
                      jw_threshold, level, detail)

        self.update_progress(50)  # 100

        # Remove intermediary files if desired to check
        os.remove('localExtractionFile.csv')
        os.remove('blockingList.txt')
        os.remove(foreign_file)

        tkMessageBox.showinfo("Matching Complete",
                              "AAMP has finished matching. Please review your results located at: " +
                              "\n" + self.get_output_path())
        sys.exit()

########################################################################################################################
if __name__ == '__main__':
    root1 = tk.Tk()
    app1 = File2MAF_Application(root1)
    app1.run()
