# Local File Extraction Module
__author__ = 'Matt Wilchek'
from File import dataFile

class LocalExtraction():

    def run(self, input_file, jbid, password, env):
        """
        Primary local method to retrieve user information and local file to standardize
        :param input_file: local input file from user
        :param jbid: username for Oracle database
        :param password: password for Oracle database
        :return local_extraction_file: standardized file for matching
        :return blocks_4_maf: list of zip codes from file for matching
        :return oracle_user: username and password object to re-use
        """
        try:
            file_parse = dataFile(input_file)
            print str(file_parse.get_name())
            file_parse = file_parse.classify(file_parse)
            print ("Standardizing for matching...")
            local_extraction_file, blocks_4_maf, oracle_user = file_parse.standardize(jbid, password, env)

            # returns local standardized file, a list of zip codes, and the login info for the User
            return local_extraction_file, blocks_4_maf, oracle_user

        except classmethod as errorClass:
            print("ERROR: Error caught with datafile class: " + repr(errorClass))

        except ValueError as errorValue:
            print("ERROR: Error caught with returned value: " + repr(errorValue))

        except TypeError as errorType:
            print("ERROR: Error caught with returned value: " + repr(errorType))

if __name__ == '__main__':
    local_file = LocalExtraction()
    local_file.run()