from __future__ import division
import arcpy
import os
import pandas as pd
import subprocess
import re
import csv
import cx_Oracle as Oracle
import time
import sys

pd.set_option('display.height', 1000)
pd.set_option('display.max_rows', 10)
pd.set_option('display.width', 1000)
master_record_count = 0
jellyPath = r'\\geo017app-fs\ACAPB\Kevin H\GQ_Standardizer_Research\misc\Substitution_Confidence_Richard\jellyfish-0.5.1'
sys.path.append(jellyPath)
import jellyfish

prodtran = 'PRODTRAN'


def getPass():
    import Tkinter
    global passWord
    top = Tkinter.Tk()
    l1 = Tkinter.Label(top, text="Password:")
    e1 = Tkinter.Entry(top, show="*")

    def pressedButton():
        global passWord
        passWord = e1.get()
        top.destroy()

    b1 = Tkinter.Button(top, text="Execute", command=pressedButton)
    l1.pack()
    e1.pack()
    b1.pack()
    top.mainloop()
    pw = passWord
    del passWord
    return pw


def removeLetters(string):
    """
    Local method used in execute() to remove HN(s) that have letters in them to compare range.
    :param string:
    :return:
    """
    sep = ' '
    string = re.sub(r'[a-zA-Z]', r'', string)
    return string.split(sep, 1)[0]


paramsFile = 'InputList.txt'
with (open(paramsFile, 'r')) as temp:
    paramasList = temp.readlines()

# USER parameters
userName = paramasList[1].replace('\n', '')
records = paramasList[3].replace('\n', '')
print "if you're seeing this, look for the 'tk - \\Remote' window under the idle/python group and enter your password"
print "this script will not continue until you enter your password!"
password = getPass()

tempList = [x.replace('\n', '') for x in paramasList[5:]]
tempList = [x for x in tempList if len(x) == 5]
print "found", len(tempList), "state-county FIPS in input file, if this is wrong, check your input formatting!"
print "list of FIPS in input for user:", userName
for i in tempList:
    print '\t', i

stcou_list_string = ', '.join(tempList)
gdbPath = os.getcwd() + '\\OutputResults\Results.gdb'
failed_gdb = os.getcwd() + '\\OutputResults\FailedRecords.gdb'
vintage = "TAB40OID"

# Derived parameters
stcou_list = map(str, stcou_list_string.split(', '))
# use arcpy to make a new empty gdb if you really need it...
try:
    arcpy.CreateFileGDB_management(os.path.dirname(gdbPath), os.path.basename(gdbPath))
except Exception:
    print "gdb already exists, hopefully this script still works anyway and it doesn't *really* need to be empty?"
    # arcpy.CreateFileGDB_management(os.path.dirname(gdbPath),os.path.basename(gdbPath))
print "************This Program will QC WBGCON 2 Records from the MAFDATA.DSF_GEONATIONAL Table************"

print ""  # \n
print "Throughout the QC Process layers will be made in the your GeoDatabase."

print ""
print "The vintage used to QC WBGCON 2 Records will be under vintage: " + str(57)
print ""
print "Beginning the QC process..."

blocksAR = os.getcwd() + r'\Resources\faceoid2ar.fmw'
blocksAR_v2 = os.getcwd() + r'\Resources\faceoid2ar_v2.fmw'
faces4AR = os.getcwd() + r'\Resources\none2filegdb.fmw'
faces4AR_v2 = os.getcwd() + r'\Resources\none2filegdb_v2.fmw'
oidmu2msp = os.getcwd() + r'\Resources\oidmu2msp.fmw'
table_drop = "yes"
workspace_gdb = gdbPath
df_cols = ['FACE_ID', 'GEOID', 'OIDMU', 'OIDAR']
failed_records = pd.DataFrame(columns=df_cols)

# Setup arcpy environment
arcpy.env.workspace = workspace_gdb
arcpy.env.overwriteOutput = True

# Connect to PRODTRAN Database and Get Data into Dataframe
connection = Oracle.connect(userName, password, prodtran)
start = time.time()
for index in stcou_list:

    filename = str(index) + "_vintage" + str(57) + "_Results.csv"
    statefp = filename[0:2]
    countyfp = filename[2:]
    with open(filename, 'wb') as csvfile:

        # Setup csv file for output results
        fieldnames = ['BLOCK_GEOID', 'OIDMU', 'OIDAR', 'Range_Value_Test', 'DISPLAYNAME_Test', 'ZIP_Test', 'Note']
        writer = csv.writer(csvfile, delimiter=",")
        writer.writerow(fieldnames)
        csvfile.flush()

        faceListQuery = """select * from (
                                    select face_id as ID_LIST, count(*) total
                                    from mafdata.DSFGEO_NATIONAL
                                    where stcou = '%s' and wbgcon = '2'
                                    group by face_id
                                    order by count(*) desc)
                                    where rownum <= %s""" \
                        % (index, records)

        face_list = pd.read_sql(faceListQuery, con=connection)

        for item in face_list.ID_LIST:
            face_id = str(item)

            # Richard's address.isprefloc change here
            mafunitQuery = """select f.OID as ID_LIST, C.HN, d.DISPLAYNAME, c.ZIP, a.* from mafdata.DSFGEO_NATIONAL a
                                        join maftiger.mafunit b on a.OIDMU = b.OID
                                        join face f on f.face_id = a.face_id
                                        join maftiger.address c on b.OID = c.OIDMU
                                        join maftiger.featurename d on c.OIDFN = d.OID
                                        and c.isprefloc = 'Y'  
                                        and a.face_id = '%s'""" \
                           % face_id

            dataOut = pd.read_sql(mafunitQuery, con=connection)
            dataOut = dataOut.astype(str)
            dataOut.set_index('OIDMU', inplace=True)

            # Get list of mafunit records...
            idList = dataOut['ID_LIST'].unique().tolist()
            idListString = ','.join(map(str, idList))  # convert ID List to one giant string

            print "Collecting Geographic Address Ranges (polylines) from the database according to records to QC..."
            fmeCMD1 = 'FME ' + blocksAR + ' --USER ' + userName + ' --PW ' + password + ' --ID_LIST ' \
                      + idListString + ' --FILEGDB ' + workspace_gdb + ' --VINTAGE ' + '57' + ' --DROP_TABLE ' \
                      + table_drop
            print "Polylines successfully added to working geo-database for quality check process."
            subprocess.call(fmeCMD1, shell=False)  # updates workspace_gdb
            print ""

            print "Collecting Geographic Tabblocks associated to Address Ranges collected previously from MAFTIGER to QC..."
            fmeCMD2 = 'FME ' + faces4AR + ' --USER ' + userName + ' --PW ' + password + ' --ID_LIST ' \
                      + idListString + ' --FILEGDB ' + workspace_gdb + ' --VINTAGE ' + '57' + ' --DROP_TABLE ' \
                      + table_drop
            subprocess.call(fmeCMD2, shell=False)  # updates workspace_gdb
            print "Tabblocks successfully added to working geo-database for quality check process."

            addressLines = arcpy.MakeFeatureLayer_management("TOPOGEOM_AR", "TOPOGEOM_AR")  # FMW Roads generated
            blocks = arcpy.MakeFeatureLayer_management("TOPOGEOM_TABBLOCK",
                                                       "TOPOGEOM_TABBLOCK")  # FMW Block data generated

            blocks_cur = arcpy.SearchCursor(blocks)

            for blk in blocks_cur:
                print "_____________________________________________________________________________________________"
                print "Face ID: " + face_id + " for OIDAR Analysis"

                tempBlk = arcpy.MakeFeatureLayer_management(blocks,
                                                            where_clause="""GEOID = '""" + blk.GEOID + """'""")
                blocksWithLines = arcpy.SelectLayerByLocation_management("TOPOGEOM_AR", 'SHARE_A_LINE_SEGMENT_WITH',
                                                                         tempBlk, selection_type='NEW_SELECTION')

                # Create list of roads around selected block according to MAFTIGER #################################
                breakString = str(blk.GEOID)
                stateFP = breakString[:2]
                breakString = breakString[2:]
                countyFP = breakString[:3]
                breakString = breakString[3:]
                tractce = breakString[:6]
                blockce = breakString[6:]

                rightRoads = """select ar.oid, ar.fromhn, ar.tohn, ar.zip, ar.side, ar.parity, fn.displayname, FN.NAME,
                                                EF.OIDFN, ED.OID as oided, ED.EDGE_ID, E.GEOMETRY, tb.oid as oidtb, tb.statefp, tb.countyfp
                                                from MAFTIGER.AR ar, MAFTIGER.MT_RELATION$ r1, MAFTIGER.MT_EDGE$ e, MAFTIGER.MT_RELATION$ r2, MAFTIGER.TABBLOCK tb,
                                                maftiger.arroadrel arrd, maftiger.featurename fn, maftiger.elemfeat ef, MAFTIGER.EDGE ed
                                                where (side = 'R' and e.right_face_id = r2.topo_id)
                                                and ar.oid = arrd.oidar
                                                and arrd.oidef = ef.oid
                                                and ef.oidfn = fn.oid
                                                and AR.OID = R1.TG_ID
                                                and R1.TG_LAYER_ID = 4001
                                                and R1.TOPO_ID = E.EDGE_ID
                                                and (E.Right_FACE_ID = R2.TOPO_ID or E.left_face_id = r2.topo_id)
                                                and R2.TG_ID = TB.OID
                                                and R2.TG_LAYER_ID = 2101
                                                and TB.OID in (
                                                select x.OID from MAFTIGER.TABBLOCK x
                                                where X.STATEFP = '%s'
                                                and X.countyfp = '%s'
                                                and X.tractce = '%s' --change/use GEOID to get needed OID
                                                and X.blockce = '%s'
                                                and x.vintage = '57'
                                                )
                                                and AR.MTFCC = 'D1000'
                                                and ED.EDGE_ID = E.EDGE_ID""" \
                             % (stateFP, countyFP, tractce, blockce)
                leftRoads = """select ar.oid, ar.fromhn, ar.tohn, ar.zip, ar.side, ar.parity, fn.displayname, FN.NAME,
                                                EF.OIDFN, ED.OID as oided, ED.EDGE_ID, E.GEOMETRY, tb.oid as oidtb, tb.statefp, tb.countyfp
                                                from MAFTIGER.AR ar, MAFTIGER.MT_RELATION$ r1, MAFTIGER.MT_EDGE$ e, MAFTIGER.MT_RELATION$ r2, MAFTIGER.TABBLOCK tb,
                                                maftiger.arroadrel arrd, maftiger.featurename fn, maftiger.elemfeat ef, MAFTIGER.EDGE ed
                                                where (side = 'L' and e.left_face_id = r2.topo_id)
                                                and ar.oid = arrd.oidar
                                                and arrd.oidef = ef.oid
                                                and ef.oidfn = fn.oid
                                                and AR.OID = R1.TG_ID
                                                and R1.TG_LAYER_ID = 4001
                                                and R1.TOPO_ID = E.EDGE_ID
                                                and (E.Right_FACE_ID = R2.TOPO_ID or E.left_face_id = r2.topo_id)
                                                and R2.TG_ID = TB.OID
                                                and R2.TG_LAYER_ID = 2101
                                                and TB.OID in (
                                                select x.OID from MAFTIGER.TABBLOCK x
                                                where X.STATEFP = '%s'
                                                and X.countyfp = '%s'
                                                and X.tractce = '%s' --change/use GEOID to get needed OID
                                                and X.blockce = '%s'
                                                and x.vintage = '57'
                                                )
                                                and AR.MTFCC = 'D1000'
                                                and ED.EDGE_ID = E.EDGE_ID""" \
                            % (stateFP, countyFP, tractce, blockce)

                rightRoads4Block = pd.read_sql(rightRoads, con=connection)
                leftRoads4Block = pd.read_sql(leftRoads, con=connection)
                frames = [rightRoads4Block, leftRoads4Block]

                mafBlockWithLines = pd.concat(frames)

                ####################################################################################################

                # Updates blocksWithLines selection with correct OIDARs on the appropriate side ####################
                tempLines2 = arcpy.UpdateCursor(blocksWithLines)
                for l in tempLines2:
                    correct = True
                    for index, row in mafBlockWithLines.iterrows():
                        if str(l.DISPLAYNAME) == str(row['DISPLAYNAME']):
                            if str(l.SIDE) == str(row['SIDE']):
                                correct = True
                                break
                            else:
                                correct = False
                        else:
                            correct = False
                    if not correct:
                        blocksWithLines = arcpy.SelectLayerByAttribute_management(blocksWithLines,
                                                                                  "REMOVE_FROM_SELECTION",
                                                                                  where_clause="""OIDAR = '""" + l.OIDAR +
                                                                                               """'""")
                ####################################################################################################

                # Identify total number of roads around selected block #############################################
                roadCount = 0
                lineCount = arcpy.SearchCursor(blocksWithLines)
                for _ in lineCount:
                    roadCount += 1
                print "Total Address Range IDs around Block: " + str(roadCount)
                print "Expectation:  MAFDATA.DSFGEO_NATIONAL OIDAR List should have " + str(roadCount) + " matches"
                ####################################################################################################

                # core QC Check between data in mafdata.DSFGEO_NATIONAL and related AR data ########################
                # 1 - Check if DSFGEO Housing Number data is in range between Address Range Low and High
                # 2 - Check if Address Range Line Zip Code = DSFGEO Data zip code
                # 3 - Check if Address Range Street Display Name is approximate to DSFGEO data Display name

                tempLines = arcpy.SearchCursor(blocksWithLines)
                print ""
                print mafBlockWithLines
                print ""
                print "~~~~~~~~~~~~~~~Checking if the below DSF GEO Lines Match in the above~~~~~~~~~~~~~~~"
                total_checks = 0

                unique_oidar = []
                for x in tempLines:
                    if str(x.OIDAR) not in unique_oidar:
                        match_found = False
                        zip_found = False
                        displayname_found = False
                        rangeValues_found = False
                        OIDMU = "NULL"
                        OIDAR = "NULL"
                        notes = ""
                        fails = 0
                        passes = 0
                        checks = 0

                        print ""
                        print "Comparing: OIDAR - " + x.getValue('OIDAR') + " Range - " + str(x.FROMHN) + " to " + str(
                            x.TOHN) + " Name - " + str(x.DISPLAYNAME) + " from selected block..."

                        # Compare subset edges with Address Range data from mafdata.DSFGEO_NATIONAL
                        for thing, row in dataOut.iterrows():
                            if str(x.OIDAR) == str(row['OIDAR']).replace(".0", ""):
                                unique_oidar.append(str(x.OIDAR))
                                checks += 1
                                match_found = True
                                OIDMU = str(thing)
                                OIDAR = str(row['OIDAR']).replace(".0", "")
                                tempTOHN = removeLetters(str(x.TOHN))
                                tempFROMHN = removeLetters(str(x.FROMHN))
                                tempHN = removeLetters(str(row['HN']))
                                street1 = str(x.DISPLAYNAME)
                                street2 = str(row['DISPLAYNAME'])

                                try:
                                    if (int(tempFROMHN) <= int(tempHN) <= int(tempTOHN)) or \
                                            (int(tempTOHN) <= int(tempHN) <= int(tempFROMHN)):
                                        rangeValues_found = True
                                except ValueError:
                                    print "Could not compare HN Range, value was not base 10; marked True."
                                    rangeValues_found = True

                                if street1 == street2:
                                    displayname_found = True
                                else:
                                    jwScore = jellyfish.jaro_winkler(unicode(street1), unicode(street2))
                                    if jwScore >= 0.8:
                                        displayname_found = True

                                if str(x.ZIP) == str(row['ZIP']):
                                    zip_found = True

                                if not rangeValues_found or not displayname_found or not zip_found:
                                    if not rangeValues_found:
                                        rangeValues_found = "FAIL"
                                    else:
                                        rangeValues_found = "PASS"

                                    if not displayname_found:
                                        displayname_found = "FAIL"
                                    else:
                                        displayname_found = "PASS"

                                    if not zip_found:
                                        zip_found = "FAIL"
                                    else:
                                        zip_found = "PASS"

                                    writer.writerow(
                                        [str(blk.GEOID), OIDMU, OIDAR, rangeValues_found, displayname_found,
                                         zip_found, notes])
                                    temp_df = pd.DataFrame([[str(face_id), str(blk.GEOID), str(OIDMU), str(OIDAR)]],
                                                           columns=df_cols)
                                    failed_records = failed_records.append(temp_df, ignore_index=True)
                                    csvfile.flush()
                                    fails += 1

                                if rangeValues_found and displayname_found and zip_found:
                                    passes += 1

                        """  # Commented out to avoid recorded data with records to compare with in dsf_geo
                        if not match_found:
                            notes = "OID Record: " + str(x.OID) + " " + str(x.DISPLAYNAME) + " with OIDAR " + str(
                                x.OIDAR) + " from maftiger has no match in table MAFDATA.DSFGEO_NATIONAL based on the " 
                                           "records pulled."
                            print "# Failure at ----> " + notes
                            print ""
                            temp_df = pd.DataFrame([[str(face_id), str(blk.GEOID), str(OIDMU), str(OIDAR)]], columns=df_cols)
                            failed_records = failed_records.append(temp_df, ignore_index=True)
                            writer.writerow(
                                [str(blk.GEOID), OIDMU, OIDAR, str(rangeValues_found), str(displayname_found),
                                 str(zip_found), notes])
                            csvfile.flush()
                        """

                        try:
                            pass_rate = float(passes / checks) * 100
                            passesS = "{0:.0f}%".format(pass_rate)
                        except ZeroDivisionError:
                            passesS = "0%"

                        try:
                            fail_rate = float(fails / checks) * 100
                            failsS = "{0:.0f}%".format(fail_rate)
                        except ZeroDivisionError:
                            failsS = "0%"

                        print "Has a total of: " + str(
                            checks) + " OIDMU records to Quality Check from mafdata.DSFGEO_NATIONAL."
                        print "Results: " + passesS + " records passed, " + failsS + " records failed."
                        total_checks += checks

                        if passesS == "100%":
                            writer.writerow(
                                [str(blk.GEOID), "ALL OIDMU PASS", OIDAR, "ALL PASS", "ALL PASS",
                                 "ALL PASS", notes])
                            csvfile.flush()

                print ""
                print "There were a total of " + str(total_checks) + " records to check under the block."
                master_record_count += total_checks
                print "____________________________________________________________________________________________"

                arcpy.Delete_management(tempBlk)

            ########################################################################################################
            # Clean up
            arcpy.Delete_management("TOPOGEOM_AR")  # delete from memory
            arcpy.Delete_management("TOPOGEOM_TABBLOCK")  # delete from memory
            arcpy.Delete_management(addressLines)  # delete from memory
            arcpy.Delete_management(blocks)  # delete from memory
            ########################################################################################################

# Get Workspace for Failed Records to Double Check
# Get list of failed records...
# Setup arcpy environment
for item_stcou in stcou_list:
    arcpy.env.workspace = failed_gdb
    arcpy.ResetEnvironments()
    arcpy.env.overwriteOutput = False

    cursor = connection.cursor()

    cursor.execute("""create table temp1 as 
                                select * from (
                                select face_id as ID_LIST
                                from mafdata.DSFGEO_NATIONAL
                                where stcou in (%s) and wbgcon = '2'
                                group by face_id
                                order by count(*) desc)""" \
                   % str(item_stcou))

    print "Collecting Geographic Address Ranges (polylines) from the database according to failed records..."
    fmeCMD1_fail = 'FME ' + blocksAR_v2 + ' --USER ' + userName + ' --PW ' + password + ' --FILEGDB ' \
                   + failed_gdb + ' --VINTAGE ' + '57' + ' --DROP_TABLE ' + table_drop
    print "Polylines successfully added to working geo-database for quality check process."
    subprocess.call(fmeCMD1_fail, shell=False)  # updates failed_gdb
    print ""
    time.sleep(5)
    print "Collecting Geographic Tabblocks associated to Address Ranges collected previously from failed records..."
    fmeCMD2_fail = 'FME ' + faces4AR_v2 + ' --USER ' + userName + ' --PW ' + password + ' --FILEGDB ' \
                   + failed_gdb + ' --VINTAGE ' + '57' + ' --DROP_TABLE ' + table_drop
    subprocess.call(fmeCMD2_fail, shell=False)  # updates failed_gdb
    print "Tabblocks successfully added to working geo-database for quality check process."
    time.sleep(5)

    cursor.execute('DROP TABLE TEMP1')

print failed_records.groupby(["OIDMU"])
failedidList = failed_records['FACE_ID'].unique().tolist()
failedidList = ','.join(map(str, failedidList))  # convert ID List to one giant string
print "List of failed FACE IDs: " + failedidList
print ""
failed_oidmu = failed_records['OIDMU'].unique().tolist()
failed_oidmu = ','.join(map(str, failed_oidmu))  # convert ID List to one giant string
failed_oidmu = failed_oidmu.replace('NULL,', '')

if len(failed_oidmu) > 1:
    print "List of failed OIDMUs: " + failed_oidmu
    print""
    table_drop = "No"
    arcpy.env.workspace = failed_gdb
    arcpy.ResetEnvironments()
    arcpy.env.overwriteOutput = False
    fmeCMD3_fail = 'FME ' + oidmu2msp + ' --USER ' + userName + ' --PW ' + password + ' --FILEGDB ' + \
                   failed_gdb + ' --DROP_TABLE ' + table_drop + ' --OIDMU ' + failed_oidmu + \
                   ' --Layer_Name ' + 'msp'
    subprocess.call(fmeCMD3_fail, shell=False)  # updates failed_gdb
    print "MSPs successfully added to working geo-database for quality check process."
else:
    print "No OIDMU records were recorded as a FAIL in this QC Session."

print "QC Process Complete for all state county list. "
end = time.time()
print "Total execution time: " + str(end - start), "seconds"
print "Total OIDMU Records checked: " + str(master_record_count)
