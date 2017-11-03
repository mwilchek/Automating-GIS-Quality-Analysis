# Load required modules################################################################################################
from abc import ABCMeta
import sys
import tkMessageBox
from OracleStandardizer import OracleStandardizer
import cx_Oracle as Oracle
import pandas as pd
import os
import pip

pip.main(['install', 'openpyxl'])  # for parsing .xlsx including ones with multiple sheets
import openpyxl
from openpyxl import load_workbook


########################################################################################################################
# Class file to handle input for ANY file type entered in
class dataFile(object):
    __metaclass__ = ABCMeta

    def __init__(self, filename):
        self.filename = filename

    def classify(self, dataFile):
        file_in = dataFile.get_name()

        if file_in[-4:] == ".csv":
            return csv(file_in)
        elif file_in[-4:] == ".txt":
            return txt(file_in)
        elif file_in[-5:] == ".xlsx":
            return xlsx(file_in)
        else:
            return json(file_in)

    def get_name(self):
        return os.path.abspath(self.filename)


########################################################################################################################
# Subclasses ###########################################################################################################
########################################################################################################################

# Handeling csv files as user input
class csv(dataFile):
    def print_name(self):
        name = super(csv, self).get_name()
        return "%s - %s" % ("The csv file is located at: ", name)

    def read_file(self):
        try:
            dataFile.df = pd.read_csv(self.get_name())  # refers to super().get_name
        except ValueError:
            value = sys.exc_info()
            tkMessageBox.showerror("Error",
                                   "The chosen .csv file could not be parsed correctly. Below are the error details: \n"
                                   + value.strerror)
            sys.exit()
        return dataFile.df

    def standardize(self, jbid, password, env):
        # Instantiate login info
        x = OracleStandardizer(jbid, password, env)

        readDataIn = self.read_file()

        # Connect to DEVTRAN database
        # db = Oracle.connect(x.userName, x.passWord, devtran)
        # cur = db.cursor()

        # Connect to PRODTRAN database
        try:
            dbProd = Oracle.connect(x.userName, x.passWord, env)
            curProd = dbProd.cursor()
        except Oracle.DatabaseError:
            dbProd = Oracle.connect(x.userName, x.passWord, env)
            curProd = dbProd.cursor()

        outputData = x.useCSVBind(readDataIn, dbProd, curProd)  # change if different db
        # outputData = x.getBCU(outputData, dbProd, curProd)  # change if different db

        outputData = x.writeToCSV(outputData)
        blockingList = x.getBlockingInfo(outputData)

        return outputData, blockingList, x


# Handeling text files as user input (CURRENT USED FOR TESTING)
class txt(dataFile):
    def print_name(self):
        name = super(txt, self).get_name()
        return "%s - %s" % ("The text file is located at: ", name)

    # Assumes text file is '|' delimited
    def read_file(self):
        try:
            dataFile.df = pd.read_csv(self.get_name())  # refers to super().get_name
        except ValueError:
            value = sys.exc_info()
            tkMessageBox.showerror("Error",
                                   "The chosen .txt file could not be parsed correctly. Below are the error details: \n"
                                   + value.strerror)
            sys.exit()
        return dataFile.df

    def standardize(self, jbid, password, env):
        # Instantiate login info
        x = OracleStandardizer(jbid, password, env)

        readDataIn = self.read_file()

        # Connect to DEVTRAN database
        # db = Oracle.connect(x.userName, x.passWord, devtran)
        # cur = db.cursor()

        # Connect to PRODTRAN database
        try:
            dbProd = Oracle.connect(x.userName, x.passWord, env)
            curProd = dbProd.cursor()
        except Oracle.DatabaseError:
            dbProd = Oracle.connect(x.userName, x.passWord, env)
            curProd = dbProd.cursor()

        outputData = x.useCSVBind(readDataIn, dbProd, curProd)  # change if different db
        # outputData = x.getBCU(outputData, dbProd, curProd)  # change if different db

        outputData = x.writeToCSV(outputData)
        blockingList = x.getBlockingInfo(outputData)

        return outputData, blockingList, x


# Handeling xlsx files as user input with single or multiple worksheets
class xlsx(dataFile):
    def print_name(self):
        name = super(xlsx, self).get_name()
        return "%s - %s" % ("The xlsx file is located at: ", name)

    def read_file(self):
        name = self.get_name()
        wb = load_workbook(str(name), read_only=True)

        # Check if more than 1 sheet of data exists in workbook
        multiple_sheets = False
        if len(wb.get_sheet_names()) > 1:
            multiple_sheets = True

        if multiple_sheets:
            master_df = pd.DataFrame()
            xls = pd.ExcelFile(name)

            for x in range(0, len(xls.sheet_names)):
                a = xls.parse(x, header=4, parse_cols='A:G')
                master_df = master_df.append(a)

            master_df.columns = ['INPUTID', 'ADDRESS', 'ZIP', 'MTFCC', 'GQ_NAME', 'LATITUDE', 'LONGITUDE']

            return master_df  # combines all sheets into one giant dataframe

        if not multiple_sheets:
            dataFile.df = pd.read_excel(name)
            return dataFile.df

    def standardize(self, jbid, password, env):
        # Instantiate login info
        x = OracleStandardizer(jbid, password, env)

        readDataIn = self.read_file()

        # Connect to DEVTRAN database
        # db = Oracle.connect(x.userName, x.passWord, devtran)
        # cur = db.cursor()

        # Connect to PRODTRAN database
        try:
            dbProd = Oracle.connect(x.userName, x.passWord, env)
            curProd = dbProd.cursor()
        except Oracle.DatabaseError:
            dbProd = Oracle.connect(x.userName, x.passWord, env)
            curProd = dbProd.cursor()

        outputData = x.useCSVBind(readDataIn, dbProd, curProd)  # change if different db
        # outputData = x.getBCU(outputData, dbProd, curProd)  # change if different db

        outputData = x.writeToCSV(outputData)
        blockingList = x.getBlockingInfo(outputData)

        return outputData, blockingList, x


# Handeling json files as user input
class json(dataFile):
    def print_name(self):
        name = super(json, self).get_name()
        return "%s - %s" % ("The json file is located at: ", name)

    def read_file(self):
        try:
            dataFile.df = pd.read_json(self.get_name())  # refers to super().get_name
        except ValueError:
            value = sys.exc_info()
            tkMessageBox.showerror("Error",
                                   "The chosen .json file could not be parsed correctly. Below are the error details: \n"
                                   + value.strerror)
            sys.exit()
        return dataFile.df

    def standardize(self, jbid, password, env):
        # Instantiate login info
        x = OracleStandardizer(jbid, password, env)

        readDataIn = self.read_file()

        # Connect to DEVTRAN database
        # db = Oracle.connect(x.userName, x.passWord, devtran)
        # cur = db.cursor()

        # Connect to PRODTRAN database
        try:
            dbProd = Oracle.connect(x.userName, x.passWord, env)
            curProd = dbProd.cursor()
        except Oracle.DatabaseError:
            dbProd = Oracle.connect(x.userName, x.passWord, env)
            curProd = dbProd.cursor()

        outputData = x.useCSVBind(readDataIn, dbProd, curProd)  # change if different db
        outputData = x.getBCU(outputData, dbProd, curProd)  # change if different db

        outputData = x.writeToCSV(outputData)
        blockingList = x.getBlockingInfo(outputData)

        return outputData, blockingList, x
