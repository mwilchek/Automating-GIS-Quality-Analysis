import Tkinter
import csv
import pandas as pd
import os
import re


class OracleStandardizer():
    def __init__(self, userName, passWord, env):
        """

        :param userName:
        :param passWord:
        :param env:
        :return Oracle Standardizer object: With default user name and password for Oracle
        """
        self.userName = userName
        self.passWord = passWord
        self.env = env

    def getLogin(self):
        """

        :return:
        """
        global userName
        global passWord

        top = Tkinter.Tk()

        l1 = Tkinter.Label(top, text="BondID:")
        e1 = Tkinter.Entry(top)

        l2 = Tkinter.Label(top, text="Password:")
        e2 = Tkinter.Entry(top, show="*")

        def pressedButton():
            global userName
            global passWord
            userName = e1.get()
            passWord = e2.get()
            top.destroy()

        b1 = Tkinter.Button(top, text="Execute", command=pressedButton)

        l1.pack()
        e1.pack()
        l2.pack()
        e2.pack()
        b1.pack()

        top.mainloop()

        return OracleStandardizer(userName, passWord)

    def read_file(self, dataIn):
        """
        Standard read method for all file objects used for testing
        :param dataIn:
        :return:
        """
        csvReader = pd.read_csv(dataIn)
        return csvReader

    def useCSVBind(self, df, db, cur):
        """

        :param df:
        :param db:
        :param cur:
        :return:
        """
        # Convert dataframe to csv format for Oracle Standardizer
        df.to_csv('readDataIn.csv', sep='|', index=False)
        readDataIn = os.path.abspath('readDataIn.csv')

        with open(readDataIn, 'r') as infile, open(r'readDataIn1.csv', 'w') as outfile:
            data = infile.read()
            data = data.replace("\"", "")
            outfile.write(data)

        readDataIn1 = os.path.abspath('readDataIn1.csv')
        os.remove('readDataIn.csv')
        dictList = []

        # Standardize data
        with open(readDataIn1, 'rb') as csvfile:
            csvReader = csv.DictReader(csvfile, delimiter='|')
            for item in csvReader:
                newThing = item['ADDRESS']  # error here
                query1 = '''select MTLIBS.MTDSF.standardize_address(:new,' ').hnp||
                MTLIBS.MTDSF.standardize_address(:new,' ').hn||
                MTLIBS.MTDSF.standardize_address(:new,' ').hnp2||
                MTLIBS.MTDSF.standardize_address(:new,' ').hn2||
                MTLIBS.MTDSF.standardize_address(:new,' ').hns HN,
                MTLIBS.MTDSF.standardize_address(:new,' ').snpd snpd,
                MTLIBS.MTDSF.standardize_address(:new,' ').snpt snpt,
                MTLIBS.MTDSF.standardize_address(:new,' ').osn osn,
                MTLIBS.MTDSF.standardize_address(:new,' ').msn msn,
                MTLIBS.MTDSF.standardize_address(:new,' ').ssn ssn,
                MTLIBS.MTDSF.standardize_address(:new,' ').snst snst,
                MTLIBS.MTDSF.standardize_address(:new,' ').snsd snsd,
                MTLIBS.MTDSF.standardize_address(:new,' ').sne sne,
                MTLIBS.MTDSF.standardize_address(:new,' ').wsd wsd,
                MTLIBS.MTDSF.standardize_address(:new,' ').wsi wsi,
                '' as RANGE_FROM,
                '' as RANGE_TO,
                '' as ST,
                '' as COU,
                '' as TCT,
                '' as BCU,
                '' as TABBLK,
                '' as MAFID
                FROM DUAL'''

                Q = cur.execute(query1, new=newThing)

                columns = [i[0] for i in Q.description]
                dataOut = [dict(zip(columns, row)) for row in Q]
                item.pop('ADDRESS')
                dataOut[0].update(item)
                dictList.append(dataOut)

        os.remove('readDataIn1.csv')
        return dictList

    def getBCU(self, dataIn, db, cur):
        """

        :param dataIn:
        :param db:
        :param cur:
        :return:
        """
        outDictList = []

        # loop through all dictionaries in the list to get lat/lon and perform query
        for item in dataIn:
            inLat = item[0]['LATITUDE']
            inLon = item[0]['LONGITUDE']

            query2 = ''' select st, cou, tct, tabblk, bcu.bcu from
            (
            select :lon, :lat as coords, tab.statefp st, tab.countyfp cou, tab.tractce tct, tab.blockce tabblk
            from maftiger.tabblock tab
            where tab.vintage in
            (
            '40'
            )
            and sdo_contains
            (
            tab.sdogeometry,
                (
                select SDO_GEOMETRY
                    (
                    2001,
                    8265,
                    SDO_POINT_TYPE
                        (
                        :lon,:lat,null
                        ),
                    null,
                    null
                    )
                from dual
                )
            )
            = 'TRUE'
            ) tab
            join
            (--bcu geography from a lat/long (vintage 90):
            select :lon,:lat as coords, bcu.bcuid bcu
            from maftiger.bcu bcu
            where bcu.vintage in
            (
            '90'
            )
            and sdo_anyinteract
            (
            bcu.sdogeometry,
                (
                SDO_GEOMETRY
                    (
                    2003,
                    8265,
                    null,
                    SDO_ELEM_INFO_ARRAY
                        (
                        1,
                        1003,
                        3
                        ),
                    SDO_ORDINATE_ARRAY
                        (
                        :lon,:lat,:lon,:lat
                        )
                    )

                )
            )
            = 'TRUE'
            ) bcu on tab.coords = bcu.coords '''

            Q2 = cur.execute(query2, lat=inLat, lon=inLon)

            columns = [i[0] for i in Q2.description]
            dataOut = [dict(zip(columns, row)) for row in Q2]
            dataOut[0].update(item[0])
            outDictList.append(dataOut[0])

        return outDictList

    def writeToCSV(self, outputData):
        """

        :param outputData:
        :return:
        """
        filename = "localExtractionFile.csv"
        keys = ['INPUTID', 'HN', 'RANGE_FROM', 'RANGE_TO', 'SNPD', 'SNPT',
                'OSN', 'MSN', 'SSN', 'SNST', 'SNSD', 'SNE', 'WSD', 'WSI',
                'ZIP', 'MTFCC', 'GQ_NAME', 'LATITUDE', 'LONGITUDE', 'ST',
                'COU', 'TCT', 'BCU', 'TABBLK', 'MAFID']
        with open(filename, 'wb') as outCSV:
            dict_writer = csv.DictWriter(outCSV, keys, delimiter='|')  
            dict_writer.writeheader()
            for item in outputData:  # error here, no output data apparently
                dict_writer.writerows(item)
                outCSV.flush()

        outCSV.close()
        outFile = os.path.abspath(filename)

        return outFile

    def getBlockingInfo(self, outFile):
        """
        Get list of blocks that are relevant by zip code to the standardized data
        :param outFile:
        :return:
        """
        blockingFileName = "blockingList.txt"
        zipSet = set()
        blockingList = []
        with open(outFile) as csvfile:
            reader = csv.DictReader(csvfile, delimiter='|')
            for row in reader:
                if re.match('^[0-9]{5}$', row['ZIP']):
                    zipSet.add(row['ZIP'])

            for item in zipSet:
                blockingList.append(item)

        outCSV = open(blockingFileName, 'w')
        writer = csv.writer(outCSV, delimiter='|')
        for item in blockingList:
            writer.writerow([item])
            outCSV.flush()

        outCSV.close()
        blockingFile = os.path.abspath(blockingFileName)

        return blockingFile
