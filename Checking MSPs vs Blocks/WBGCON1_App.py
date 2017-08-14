import arcpy
import os
import pandas as pd
import numpy as np
import subprocess
import csv
import datetime
import pip
import time
import Tkinter as tk
import tkMessageBox

pip.main(['install', 'pygubu'])
import pygubu  # required to load GUI

MINUTE = 60
HOUR = 60 * MINUTE


class Application:
    """
        Queries data from a SQL Database Table for Quality Check defined in GUI
        Loads data into FME Workspaces to get related GIS data
        Loads GIS data into a geo-database and performs quality check analysis
        Outputs a final report of results
        :param User Name: User Name for Oracle Database with data to quality check
        :param Password: Password for Oracle Database with data to quality check
        :param Record Count: Number or percentage of how many records to check
        :param State County: User defined state county ID to query data to quality check
        :param Empty Geodatabase: Full UNC path to an empty geo-database to put FME data in
        :param Geographic Vintage: User defined selection of geographic version data to quality check with
        :return: File object with results.
    """
    def __init__(self, master):
        self.done_time = datetime.datetime.now() + datetime.timedelta(seconds=HOUR / 2)  # half hour
        self.master = master
        self.builder = builder = pygubu.Builder()
        builder.add_from_file('GUI\wbgcon1_gui.ui')  # Load GUI ui file
        self.mainwindow = builder.get_object('mainwindow', master)  # Create the widget using a master as parent
        builder.connect_callbacks(self)

    ####################################################################################################################
    # Get variables from GUI
    ####################################################################################################################
    def getJBID(self):  # testing how to retrieve data
        userName = self.builder.tkvariables['username_entry'].get()
        return userName

    def getPassword(self):
        password = self.builder.tkvariables['password_entry'].get()
        return password

    def getFileParameter(self):
        fileParam = self.builder.tkvariables['fileParameter'].get()
        return fileParam

    def getSTCOU(self):
        stcou = self.builder.tkvariables['stcouChoice'].get()
        return stcou

    def getRecords(self):
        records = self.builder.tkvariables['recordCount'].get()
        return records

    def getMSP(self):
        mspName = self.builder.tkvariables['mspLayerName'].get()
        return mspName

    def getGDB(self):
        gdbPath = self.builder.tkvariables['gdbPath'].get()
        return gdbPath

    def getCheckbox1(self):
        checkValue = self.builder.tkvariables['checkValue1'].get()
        if checkValue == 1:
            return "True"
        else:
            return "False"

    def getCheckbox2(self):
        checkValue = self.builder.tkvariables['checkValue2'].get()
        if checkValue == 1:
            return "True"
        else:
            return "False"

    def getCheckbox3(self):
        checkValue = self.builder.tkvariables['checkValue3'].get()
        if checkValue == 1:
            return "True"
        else:
            return "False"

    def getCheckbox4(self):
        checkValue = self.builder.tkvariables['checkValue4'].get()
        if checkValue == 1:
            return "True"
        else:
            return "False"

    def getCheckbox5(self):
        checkValue = self.builder.tkvariables['checkValue5'].get()
        if checkValue == 1:
            return "True"
        else:
            return "False"

    def getCheckbox6(self):
        checkValue = self.builder.tkvariables['checkValue6'].get()
        if checkValue == 1:
            return "True"
        else:
            return "False"

    def getCheckbox7(self):
        checkValue = self.builder.tkvariables['checkValue7'].get()
        if checkValue == 1:
            return "True"
        else:
            return "False"

    def getPrevTab40Name(self):
        block_layer_name = self.builder.tkvariables['prevTab40Name'].get()
        return block_layer_name

    def getTab40Name(self):
        block_layer_name = self.builder.tkvariables['tab40Name'].get()
        return block_layer_name

    def getTabCurrName(self):
        block_layer_name = self.builder.tkvariables['tabCurrName'].get()
        return block_layer_name

    def getFaceIdName(self):
        block_layer_name = self.builder.tkvariables['faceIdName'].get()
        return block_layer_name

    def getCsFaceIdName(self):
        block_layer_name = self.builder.tkvariables['csFaceIdName'].get()
        return block_layer_name

    def getCsTab40Name(self):
        block_layer_name = self.builder.tkvariables['csTab40Name'].get()
        return block_layer_name

    def getBcuoidName(self):
        block_layer_name = self.builder.tkvariables['bcuoidName'].get()
        return block_layer_name

    def update_clock(self):
        elapsed = self.done_time - datetime.datetime.now()
        h = (elapsed.seconds / 3600)
        m = elapsed.seconds / 60
        s = elapsed.seconds % 60
        self.builder.tkvariables['time'].set("ETC: " + "%02d:%02d:%02d" % (h, m, s) + " PER VINTAGE SELECTED")
        self.master.after(1000, self.update_clock)

    ####################################################################################################################
    # Core method for QC that calls above methods
    ####################################################################################################################

    def execute(self):
        start = time.time()
        self.update_clock()
        mspFME_Int = os.getcwd() + r'\Resources\oidmu2msp_v2.fmw'  # integer
        mspFME_Percent = os.getcwd() + r'\Resources\oidmu2msp.fmw'  # percentage
        mspFME = os.getcwd() + r'\Resources\oidmu2msp.fmw'  # default
        blocksFME = os.getcwd() + r'\Resources\natgeo2tabblock.fmw'
        table_drop = "yes"
        workspace_gdb = self.getGDB()
        fileParam = self.getFileParameter()

        # Setup arcpy environment
        arcpy.env.workspace = workspace_gdb
        arcpy.env.overwriteOutput = True

        def QC_Check(msp_layer_name, block_layer_name, vintage):
            global blkCur, blkCur
            filename = block_layer_name + "_" + vintage + "_Results.csv"
            with open(filename, 'wb') as csvfile:
                # Setup csv file for output results
                fieldnames = ['GEO_VINTAGE', 'TEST_NUMBER', 'RESULT', 'POINT_ID', 'BLOCK_ID']
                writer = csv.writer(csvfile, delimiter=",")
                writer.writerow(fieldnames)
                csvfile.flush()

                # Setup program to refer to correct layers in geo-database
                try:
                    msp_layer = arcpy.MakeFeatureLayer_management(msp_layer_name)  # MSP Layer to Refer to
                    # Filter blocks to the ones with just Address Points
                    block_Layer = arcpy.MakeFeatureLayer_management("_" + block_layer_name)  # Block layer to filter
                    blocksWithPoints = arcpy.SelectLayerByLocation_management(block_Layer, 'INTERSECT', msp_layer)
                    arcpy.CopyFeatures_management(blocksWithPoints, (workspace_gdb + "//blocks4QC"))
                    block_layer_name = arcpy.MakeFeatureLayer_management((workspace_gdb + "//blocks4QC"))
                    blkCur = arcpy.SearchCursor(block_layer_name)  # Block Layer to Refer to
                except IOError:
                    tkMessageBox.showinfo('QC Error', 'There was an error writing to the geo-database that was '
                                                      'entered. \nPlease make a different empty one and try again.')
                except UnboundLocalError:
                    quit()

                counter = 0
                passes = 0
                fails = 0
                checks = 0

                for blk in blkCur:
                    counter += 1
                    print ("Testing block: " + blk.OID)
                    featBlk = arcpy.MakeFeatureLayer_management(block_layer_name, where_clause="""OID = '"""
                                                                                               + blk.OID + """'""")

                    tempPnts = arcpy.SelectLayerByLocation_management(msp_layer, 'INTERSECT', featBlk,
                                                                      selection_type='NEW_SELECTION')
                    curTemp = arcpy.SearchCursor(tempPnts)
                    blkTestFail = False

                    # Validates if the msp point is in the correct block
                    for i in curTemp:
                        # If msp is not in the right block, record point and set block test to FAIL
                        if vintage == "PREV_TAB40OID":
                            if i.PREV_TAB40OID != blk.OID:
                                print "Failue at point OIDMU: ", i.OIDMU
                                blkTestFail = True
                                writer.writerow(["PREV_TAB40", counter, "POINT FAILURE", i.OIDMU, blk.OID])
                                csvfile.flush()
                                fails += 1
                                checks += 1

                        if vintage == "TAB40OID":
                            if i.TAB40OID != blk.OID:
                                print "Failue at point OIDMU: ", i.OIDMU
                                blkTestFail = True
                                writer.writerow(["TAB40", counter, "POINT FAILURE", i.OIDMU, blk.OID])
                                csvfile.flush()
                                fails += 1
                                checks += 1

                        if vintage == "TAB_CURR_OID":
                            if i.TAB_CURR_OID != blk.OID:
                                print "Failue at point OIDMU: ", i.OIDMU
                                blkTestFail = True
                                writer.writerow(["TAB_CURR", counter, "POINT FAILURE", i.OIDMU, blk.OID])
                                csvfile.flush()
                                fails += 1
                                checks += 1

                        if vintage == "FACE_ID":
                            if i.FACE_ID != blk.OID:
                                print "Failue at point OIDMU: ", i.OIDMU
                                blkTestFail = True
                                writer.writerow(["FACE_ID", counter, "POINT FAILURE", i.OIDMU, blk.OID])
                                csvfile.flush()
                                fails += 1
                                checks += 1

                        if vintage == "CS_FACE_ID":
                            if i.CS_FACE_ID != blk.OID:
                                print "Failue at point OIDMU: ", i.OIDMU
                                blkTestFail = True
                                writer.writerow(["CS_FACE_ID", counter, "POINT FAILURE", i.OIDMU, blk.OID])
                                csvfile.flush()
                                fails += 1
                                checks += 1

                        if vintage == "CS_TAB40OID":
                            if i.CS_TAB40OID != blk.OID:
                                print "Failue at point OIDMU: ", i.OIDMU
                                blkTestFail = True
                                writer.writerow(["CS_TAB40", counter, "POINT FAILURE", i.OIDMU, blk.OID])
                                csvfile.flush()
                                fails += 1
                                checks += 1

                        if vintage == "BCUOID":
                            if i.BCUOID != blk.OID:
                                print "Failue at point OIDMU: ", i.OIDMU
                                blkTestFail = True
                                writer.writerow(["BCU", counter, "POINT FAILURE", i.OIDMU, blk.OID])
                                csvfile.flush()
                                fails += 1
                                checks += 1

                    if blkTestFail:
                        print "Failure at Block OID"
                        print ""
                        fails += 1
                        checks += 1

                    # If all msp points in right block, record block pass
                    else:
                        print "\tBlock OID:", blk.OID, "passes"
                        print ""
                        writer.writerow([str(vintage), counter, "BLOCK PASSES", "ALL POINTS PASS", blk.OID])
                        csvfile.flush()
                        passes += 1
                        checks += 1

                arcpy.Delete_management(featBlk)  # delete from memory
            csvfile.close()

            # cleanup
            arcpy.Delete_management(block_layer_name)  # delete from memory
            passesS = "{0:.0f}%".format((passes / checks) * 100)
            failsS = "{0:.0f}%".format((fails / checks) * 100)

            tkMessageBox.showinfo('QC Complete', os.path.abspath(filename) + ' results have been saved to the '
                                                                             'directory. \nPass Percentage: ' + passesS +
                                  '\nFailure Percentage: ' + failsS)

        if fileParam != "":
            fileParam = pd.read_csv(fileParam, header=0, thousands=',')

            # get parameters in file
            for index, row in fileParam.iterrows():
                stcou = str(row['county_list'])
                records = str(row['records'])

                try:
                    recordCheck = int(records)
                except ValueError:
                    recordCheck = float(records)

                if isinstance(recordCheck, int):
                    mspFME = mspFME_Int
                else:
                    mspFME = mspFME_Percent

                name = str(row['name'])
                workspace_gdb = row['gdb_path']
                arcpy.env.workspace = workspace_gdb
                arcpy.env.overwriteOutput = True

                num = np.array([[row['prev_tab40oid']],
                                [row['tab40oid']],
                                [row['tab_curr_oid']],
                                [row['face_id']],
                                [row['CS_Face_ID']],
                                [row['cs_tab40oid']],
                                [row['bcuoid']]])
                cols = ['Vintage']
                codes = ['PREV_TAB40OID', 'TAB40OID', 'TAB_CURR_OID', 'FACE_ID', 'CS_FACE_ID', 'CS_TAB40OID', 'BCUOID']
                vintages = pd.DataFrame(num, index=codes, columns=cols)

                tkMessageBox.showinfo('QC Executing', 'Processing your information... '
                                                      '\nConnecting to the database: mafdata.DSFGEO_NATIONAL')

                # Execute FME MSP Data Workspace
                print "Collecting MSP point data from the database..."
                fmeCMD1 = 'FME ' + mspFME + ' --USER ' + self.getJBID() + ' --PW ' + self.getPassword() + ' --FILEGDB ' + workspace_gdb + \
                          ' --DROP_TABLE ' + table_drop + ' --STCOU ' + stcou + ' --Layer_Name ' + name + ' --Records ' + records
                subprocess.call(fmeCMD1, shell=False)  # updates workspace_gdb
                print "Data successfully added to working geo-database for quality check process."

                # Execute FME Block Data Workspace and QC
                for index1, row1 in vintages.iterrows():
                    if row1['Vintage']:
                        vintage = str(index1)
                        print "QC selected for " + vintage
                        block_layer_name = str(stcou).replace('_', "")
                        print "Block Layer Name: " + block_layer_name

                        print "Collecting geographic block data from the database..."
                        fmeCMD2 = 'fme ' + blocksFME + ' --USER ' + self.getJBID() + ' --PW ' + self.getPassword() + ' --FILEGDB ' + workspace_gdb + \
                                  ' --DROP_TABLE ' + table_drop + ' --STCOU ' + stcou + ' --Vintage_Loop ' + vintage + \
                                  ' --Layer_Name ' + block_layer_name
                        # Execute FME Workspace, QC, and confirm to Loop again
                        subprocess.call(fmeCMD2, shell=False)  # updates workspace_gdb

                        print "Data successfully added to working geo-database. Initiation of QC Checking is beginning..."
                        QC_Check(name, block_layer_name, vintage)

            end = time.time() - start
            print ("Total time for program execution: " + str(end) + " seconds.")

        else:
            # Get List of selected vintages to QC on from GUI
            num = np.array([[self.getCheckbox1(), self.getPrevTab40Name()],
                            [self.getCheckbox2(), self.getTab40Name()],
                            [self.getCheckbox3(), self.getTabCurrName()],
                            [self.getCheckbox3(), self.getTabCurrName()],
                            [self.getCheckbox4(), self.getFaceIdName()],
                            [self.getCheckbox5(), self.getCsFaceIdName()],
                            [self.getCheckbox6(), self.getCsTab40Name()],
                            [self.getCheckbox7(), self.getBcuoidName()]])
            cols = [' CheckValue ', ' Layer Name ']
            codes = ['PREV_TAB40OID', 'TAB40OID', 'TAB_CURR_OID', 'FACE_ID', 'CS_FACE_ID', 'CS_TAB40OID', 'BCUOID', '']
            vintages = pd.DataFrame(num, index=codes, columns=cols)

            tkMessageBox.showinfo('QC Executing', 'Processing your information... '
                                                  '\nConnecting to the database: mafdata.DSFGEO_NATIONAL')

            # Execute FME MSP Data Workspace
            print "Collecting MSP point data from the database..."
            fmeCMD1 = 'FME ' + mspFME + ' --USER ' + self.getJBID() + ' --PW ' + self.getPassword() + ' --FILEGDB ' + workspace_gdb + \
                      ' --DROP_TABLE ' + table_drop + ' --STCOU ' + self.getSTCOU() + ' --Layer_Name ' + self.getMSP() \
                      + ' --Records ' + str(self.getRecords())
            subprocess.call(fmeCMD1, shell=False)  # updates workspace_gdb
            print "Data successfully added to working geo-database for quality check process."

            # Execute FME Block Data Workspace and QC
            for index, row in vintages.iterrows():
                if row[' CheckValue '] == "True":
                    vintage = str(index)
                    print "QC selected for " + vintage
                    block_layer_name = str(
                        row[' Layer Name '])  # did not equal input, could not QC debug here for value
                    print "Block Layer Name: " + block_layer_name

                    print "Collecting geographic block data from the database..."
                    fmeCMD2 = 'fme ' + blocksFME + ' --USER ' + self.getJBID() + ' --PW ' + self.getPassword() + ' --FILEGDB ' + workspace_gdb + \
                              ' --DROP_TABLE ' + table_drop + ' --STCOU ' + self.getSTCOU() + ' --Vintage_Loop ' + vintage + \
                              ' --Layer_Name ' + block_layer_name
                    # Execute FME Workspace, QC, and confirm to Loop again
                    subprocess.call(fmeCMD2, shell=False)  # updates workspace_gdb

                    print "Data successfully added to working geo-database. Initiation of QC Checking is beginning..."
                    QC_Check(self.getMSP(), block_layer_name, vintage)

        end = time.time() - start
        print ("Total time for program execution: " + str(end) + " seconds.")

    ####################################################################################################################
    # For testing get() methods on GUI
    def toString(self):
        print "Printing vintages dataframe..."
        # tkMessageBox.showinfo('From callback', 'Executing toString() on variables...')
        num = np.array([[self.getCheckbox1(), self.getPrevTab40Name()],
                        [self.getCheckbox2(), self.getTab40Name()],
                        [self.getCheckbox3(), self.getTabCurrName()],
                        [self.getCheckbox3(), self.getTabCurrName()],
                        [self.getCheckbox4(), self.getFaceIdName()],
                        [self.getCheckbox5(), self.getCsFaceIdName()],
                        [self.getCheckbox6(), self.getCsTab40Name()],
                        [self.getCheckbox7(), self.getBcuoidName()]])
        cols = [' CheckValue ', ' Layer Name ']
        codes = ['PREV_TAB40OID', 'TAB40OID', 'TAB_CURR_OID', 'FACE_ID', 'CS_FACE_ID', 'CS_TAB40OID', 'BCUOID', '']
        vintages = pd.DataFrame(num, index=codes, columns=cols)
        print(str(vintages))

        print ("Username: " + self.getJBID() + "\n" +
               "Password: " + self.getPassword() + "\n" +
               "STCOU: " + self.getSTCOU() + "\n" +
               "Records: " + str(self.getRecords()) + "\n" +
               "MSP Name: " + self.getMSP() + "\n"
                                              "GDB: " + self.getGDB() + "\n")

    def entry_invalid(self):
        tkMessageBox.showinfo('WBGCON1 Warning', 'Invalid entry input.')

########################################################################################################################
if __name__ == '__main__':
    root = tk.Tk()
    app = Application(root)
    root.mainloop()

__author__ = 'Matt Wilchek'
