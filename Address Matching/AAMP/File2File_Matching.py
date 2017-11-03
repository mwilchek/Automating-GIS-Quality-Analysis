# coding=utf-8
import Tkinter as tk
import os
import tkMessageBox
import cx_Oracle as Oracle
import pip
import sys
import logging
import shutil
from Data_Standardization.LocalFileExtraction import LocalExtraction
from Matching_Algorithms.Matching_KH import Match

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
class File2File_Application(pygubu.TkApplication):
    def _create_ui(self):
        # 1: Create a builder
        self.builder4 = builder4 = pygubu.Builder()

        # 2: Load an ui file
        builder4.add_from_file(os.getcwd() + r'\GUI\Interface_File2File.ui')

        # 3: Create the widget using self.master as parent
        self.mainwindow = builder4.get_object('File2File', self.master)

        # 4: Set default choices to GUI
        self.builder4.tkvariables['env'].set("PRODTRAN")
        self.builder4.tkvariables['blockingType'].set("ZIP")  # set default blocking type to 'ZIP'
        self.builder4.tkvariables['detail'].set("BEST")  # set default output detail type to 'BEST'
        self.builder4.tkvariables['jwThreshold'].set(1.00)

        # Configure callbacks
        builder4.connect_callbacks(self)

    ####################################################################################################################
    # Button Functions in GUI
    ####################################################################################################################
    def get_project_name(self):
        """
        Local method that returns project name for matching from GUI
        :return project_name: String variable of project name
        """
        project_name = self.builder4.tkvariables['projectName'].get()
        return project_name

    def get_jbid(self):
        """
        Local Method that returns JBID from GUI
        :return username: the JBID entered in the GUI as a String variable
        """
        username = self.builder4.tkvariables['username_entry'].get()
        return username

    def get_password(self):
        """
        Local Method that returns user password for db from GUI
        :return password: the password entered in GUI as a String variable
        """
        password = self.builder4.tkvariables['password_entry'].get()
        return password

    def get_env(self):
        """
        Local Method that returns user password for db from GUI
        :return password: the password entered in GUI as a String variable
        """
        env = self.builder4.tkvariables['env'].get()
        return env

    def get_file_parameter1(self):
        """
        Local Method that returns string path of file to standardize/match with from GUI
        :return fileParam: string variable to local path file
        """
        fileParam1 = self.builder4.tkvariables['fileParameter1'].get()
        return fileParam1

    def get_file_parameter2(self):
        """
        Local Method that returns string path of file to standardize/match with from GUI
        :return fileParam: string variable to local path file
        """
        fileParam2 = self.builder4.tkvariables['fileParameter2'].get()
        return fileParam2

    def get_block_type(self):
        """
        Local Method that returns blocking type used for matching from GUI
        :return blkType: string variable for match() class object
        """
        blkType = self.builder4.tkvariables['blockingType'].get()
        return blkType

    def get_m_level(self):
        """
        Local Method that returns mlevel type used for matching from GUI
        :return mlevel: string variable used for match() class object
        """
        mlevel = self.builder4.tkvariables['mLevel'].get()
        return mlevel

    def get_jw_threshold(self):
        """
        Local Method that returns jaro wrinkler threshold value for matching from GUI
        :return jwThreshold: double variable used for match() class object
        """
        jwThreshold = self.builder4.tkvariables['jwThreshold'].get()
        return jwThreshold

    def get_lvl(self):
        """
        Local Method that returns level of matching exactness for matching from GUI
        :return password: string variable used for match() class object
        """
        lvl = self.builder4.tkvariables['lvl'].get()
        return lvl

    def get_detail_output(self):
        """
        Local Method that returns level of detail for output file of results from matching from GUI
        :return detail: string variable used for match() class object
        """
        detail = self.builder4.tkvariables['detail'].get()
        return detail

    def get_output_path(self):
        """
        Local method that returns output directory of results for matching
        :return output_path: string variable of a path directory
        """
        output_path = self.builder4.tkvariables['outputPath'].get()
        return output_path

    def update_progress(self, value):
        """
        Local method for execute() method to call to update progress on GUI of matching
        :param value:
        :return updated progress in GUI:
        """
        self.builder4.tkvariables['progress'].set(value)

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
        file_input_one = self.get_file_parameter1()
        file_input_two = self.get_file_parameter2()
        jbid = self.get_jbid()
        password = self.get_password()
        env = self.get_env()

        # Standardize Data
        self.update_progress(10)
        local_extraction_file1, blocks_4_maf1, oracle_user = LocalExtraction().run(file_input_one, jbid, password, env)
        self.update_progress(30)
        os.rename('localExtractionFile.csv', 'file1.csv')
        os.rename('blockingList.txt', 'block_list1.txt')
        local_extraction_file1 = os.path.abspath('file1.csv')

        local_extraction_file2, blocks_4_maf2, oracle_user = LocalExtraction().run(file_input_two, jbid, password, env)
        self.update_progress(50)
        os.rename('localExtractionFile.csv', 'file2.csv')
        os.rename('blockingList.txt', 'block_list2.txt')
        local_extraction_file2 = os.path.abspath('file2.csv')

        # join the outputs and remove the split results
        with open('blockingList.txt', 'wb') as wfd:
            for f in ['block_list1.txt', 'block_list2.txt']:
                with open(f, 'rb') as fd:
                    shutil.copyfileobj(fd, wfd, 1024 * 1024 * 10)

        blocks_4_maf = os.path.join('blockingList.txt')
        os.remove('block_list1.txt')
        os.remove('block_list2.txt')

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
        new_match = Match(blocks_4_maf, local_extraction_file1, local_extraction_file2, output_file, block_type,
                          m_level,
                          jw_threshold, level, detail)
        new_match.run(blocks_4_maf, local_extraction_file1, local_extraction_file2, output_file, block_type, m_level,
                      jw_threshold, level, detail)

        self.update_progress(100)

        # Remove intermediary files if desired to check
        os.remove('file1.csv')
        os.remove('file2.csv')
        os.remove('blockingList.txt')

        tkMessageBox.showinfo("Matching Complete",
                              "AAMP has finished matching. Please review your results located at: " +
                              "\n" + self.get_output_path())
        sys.exit()


########################################################################################################################
if __name__ == '__main__':
    root1 = tk.Tk()
    app1 = File2File_Application(root1)
    app1.run()
