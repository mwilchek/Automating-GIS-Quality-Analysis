# MAD Data Extraction Module
# Import libraries
import csv
import os
import pandas as pd
import shutil
from MAF_DataExtraction_Thread import mafThread


fmeWS = 'ZIP_MTDB_EXTRACT.fmw'
fmeWS2 = 'test\ZIP_MTDB_EXTRACT.fmw'


class MAFextract():
    def run(self, blocks_4_maf, oracle_user, folder_loc):
        """
        Core method to retrieve MAF data for Matching
        :param blocks_4_maf: block list as a csv doc from OracleStandardizer.standardize()
        :param oracle_user: OracleStandardizer object with username and password
        :return mafData: csv file of associated maf data from zip code list
        """
        jbid = oracle_user.userName
        password = oracle_user.passWord
        env = oracle_user.env
        output_path = folder_loc

        one_zip = self.check_for_one_zip(blocks_4_maf)

        if not one_zip:
            print("Checking Oracle credentials to MAF...")
            block_string1, block_string2 = self.split_data(blocks_4_maf)
            print 'block_string1 is: ' + block_string1
            print 'block_string2 is: ' + block_string2

            threads = []
            # Create new threads for parallel programming to increase performance
            thread1 = mafThread(1, fmeWS, env, jbid, password, block_string1, output_path)
            thread2 = mafThread(2, fmeWS2, env, jbid, password, block_string2, output_path)

            # Start new Threads
            thread1.start()
            thread2.start()

            # Add threads to thread list
            threads.append(thread1)
            threads.append(thread2)

            # Wait for all threads to complete
            for t in threads:
                t.join()
            print "Exiting Main Thread - Data Extraction Complete"

            # join the outputs and remove the split results
            with open((output_path + r'\mafData.txt'), 'wb') as wfd:
                for f in [(output_path + r'\1_copy.txt'), (output_path + r'\2_copy.txt')]:
                    with open(f, 'rb') as fd:
                        shutil.copyfileobj(fd, wfd, 1024*1024*10)

            os.remove((output_path + r'\1_copy.txt'))
            os.remove((output_path + r'\2_copy.txt'))

            foreign_file = os.path.join(output_path + r'\mafData.txt')
            return foreign_file

        if one_zip:
            print("Checking Oracle credentials to MAF...")
            block_string1 = self.extract_with_one(blocks_4_maf)
            threads = []
            thread1 = mafThread(1, fmeWS, env, jbid, password, block_string1, output_path)
            thread1.start()
            threads.append(thread1)
            for t in threads:
                t.join()
            print "Exiting Data Extraction - Complete"
            foreign_file = os.path.join(output_path + r'\1_copy.txt')
            return foreign_file

    ####################################################################################################################
    # Local Methods
    def check_for_one_zip(self, blocks_4_maf):
        records = pd.read_csv(blocks_4_maf, header=None)
        if records.shape[0] == 1:
            return True

    def extract_with_one(self, blocks_4_maf):
        blockList = []
        inCSV = blocks_4_maf
        with open(inCSV) as csvfile:
            reader = csv.reader(csvfile, delimiter='|')
            for row in reader:
                for item in row:
                    blockList.append(item)
        list1 = blockList[0:]
        list1 = ','.join(list1)
        return list1

    def split_data(self, blocks_4_maf):
        """
        Updated openCSV method that returns 2 Strings of block list; so it cuts original list in half
        :param csv file object:
        :return Block list as a giant string:
        """

        blockList = []
        inCSV = blocks_4_maf
        with open(inCSV) as csvfile:
            reader = csv.reader(csvfile, delimiter='|')
            for row in reader:
                for item in row:
                    blockList.append(item)

        list1 = blockList[0:(len(blockList)/2)]
        list2 = blockList[len(blockList)/2:]

        list1 = ','.join(list1)
        list2 = ','.join(list2)

        return list1, list2

        ################################################################################################################

########################################################################################################################
if __name__ == '__main__':
    maf_data = MAFextract()
    maf_data.run()

__author__ = 'Matt Wilchek'