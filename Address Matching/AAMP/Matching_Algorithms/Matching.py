__author__ = 'holme311'
import time
import sys
from operator import itemgetter

jellyPath = r'\\geo017app-fs\ACAPB\Kevin H\GQ_Standardizer_Research\misc\Substitution_Confidence_Richard\jellyfish-0.5.1'
sys.path.append(jellyPath)
import jellyfish


class Match():    
    def __init__(self, blockFile, localFile, foreignFile, outputFile, bType, mLevel, tHold, lvl, deets):
        self.blockFile = blockFile
        self.localFile = localFile
        self.foreignFile = foreignFile
        self.outputFile = outputFile
        self.bType = bType
        self.mLevel = mLevel
        self.tHold = tHold
        self.lvl = lvl
        self.deets = deets

     ####################################################################################################################

    # Main matching core
    def run(self, blockFile, localFile, foreignFile, outputFile, bType, mLevel, tHold, lvl, deets):
        print("initializing...\n")
        stTime = time.time()
        mtchPut = open(outputFile, 'a')

        print '####################'
        print '# LOADING DATASETS #'
        print '####################\n'

        #extracting blocking list
        bList = self.getBlockingInfo(blockFile)
        #extracting local file records
        locDict = self.getLocDict(localFile)
        #extracting foreign file records
        forDict = self.getForDict(foreignFile)

        print '\n####################'
        print '''##### AAMP'ING! ####'''
        print '####################'

        #for each blocking element, block and match
        for item in bList[:2]:
            print '\nblocking & matching within ' + bType + ' ' + item + '...'
            #start timing block level extraction/matching
            stTime2 = time.time()
            #run blocking function for local/fireign datasets.  2 dictionaries returned
            locBckt, forBckt = self.blockThis(locDict, forDict, bType, item)
            #run HN matching function on blocked local/foreign dictionaries
            hnMtchs = self.hnMtch3((locBckt, forBckt), mLevel)
            stMtches = self.stMtch(hnMtchs, tHold, lvl)
            terMtches = self.terMtch(stMtches)
            ranks = self.scoRank(terMtches)
            fnlLst = self.outPutt(ranks, deets)
            matches = fnlLst
            forMatches = format(len(matches), ',d')
            comps = len(locBckt.values())*len(forBckt.values())
            formComps = format(comps, ',d')
            endTime2 = time.time()
            elapsed2 = endTime2 - stTime2
            formElapsed2 = '{:0,.2f}'.format(elapsed2)
            print str(formComps)+' comparisons in '+str(formElapsed2)+' secs, resulting in '+str(forMatches)+' matches'
            print 'writing results...'
            for mtch in matches:
                for bit in mtch:
                    mtchPut.write(str(bit)+'|')
                    mtchPut.flush()
                mtchPut.write('\n')
                mtchPut.flush()
            print 'done'
        mtchPut.close()
        
        endTime = time.time()
        elapsed = endTime - stTime
        formElapsed = '{:0,.2f}'.format(elapsed)
        print '\nD-O-N-E!  Elapsed time: ' + str(formElapsed) + 'secs.'



    def getLocDict(self, localFile):
        # source pull
        # self.sList = sList
        sList = localFile               #format and file type should not change

        ############
        print '\nloading local data into dictionary...'
        locListIn = sList
        locListRead = file(locListIn).read()
        locListRecs = locListRead.split('\n')
        locDict = {}
        for rec in locListRecs[:-1]:
            items = rec.split('|')
            locDict[items[0]] = [items]
        locCount = len(locDict.keys())
        formLocCnt = format(locCount, ',d')
        print 'done - number of total local records: %s' % formLocCnt

        return locDict



    def getForDict(self, foreignFile):
        # foreign pull
        # self.fList = fList
        fList = foreignFile             #format and file type should not change

        ############
        print '\nloading foreign data into dictionary...'
        forListIn = fList
        forListRead = file(forListIn).read()
        forListRecs = forListRead.split('\n')
        forDict = {}
        for rec in forListRecs[:-1]:
            items = rec.split('|')
            forDict[items[0]] = [items]
        forCount = len(forDict.keys())
        formForCnt = format(forCount, ',d')
        print 'done - number of total foreign records: %s' % formForCnt

        return forDict



    def getBlockingInfo(self, blockFile):
        """
        Parses Blocking List text file associated to the Local File
        :param file object: File to get blocking list.
        :return: Blocking List.
        :return: Blocking types.
        """
        # blocking list
        # self.bList = bList
        bList = blockFile

        # blocking stuff
        print 'loading blocking elements...'
        bListIn = bList
        bListRead = file(bListIn).read()
        bListRecs = bListRead.split('\r\n')
        #bType = bListRecs[0]             ####-->>bType not in post-extraction blocking lists.  Either have Melinda add it, or pass from user feed.
        bList = bListRecs#[1:]
        bCount = len(bList)
        print 'done - number of blocking elements: %s' % str(bCount)

        return bList



    def blockThis(self, locDict, forDict, typ, val):                                                            #takes in local and foreign datasets, blocking level, and blocking value
        """
        Takes imported local, foreign, and blocking data and spits out 'blocked' matching buckets (dictionaries)
        Use this in conjunction with looping of blocking elements
        :param Local Dictionary:
        :param Foreign Dictionary:
        :param typ: Blocking data type
        :param val: Blocking data values
        :return Location Bucket: Dictionary type
        :return Foreign Bucket: Dictionary type
        """
        locBckt = {}                                                                                            #dictionary repository for blocked local records
        forBckt = {}                                                                                            #dictionary repository for blocked foreign records
        if typ == 'ZIP':                                                                                        #if blocking level selected is 'ZIP'
            bPos = 14                                                                                           #ZIP position in input datasets
        # insert other blocking possibilities here                                                              #COU, BCU, etc...
        # if typ == 'STCOU':...
        for locRec in locDict.values():                                                                         #for each local record
            locItems = locRec[0]                                                                                #local data items
            locZIP = locItems[bPos]                                                                             #local ZIP
            if locZIP == val:                                                                                   #if local ZIP matches ZIP blocking value
                locBckt[locItems[0]] = locItems                                                                 #add key (local ID) and local data items to local dictionary repository
        for forRec in forDict.values():                                                                         #for each foreign record
            forItems = forRec[0]                                                                                #foreign data items
            forZIP = forItems[bPos]                                                                             #foreign ZIP
            if forZIP == val:                                                                                   #if foreign ZIP matches ZIP blocking value
                forBckt[forItems[0]] = forItems                                                                 #add key (foreign ID) and foreign data items to local dictionary repository
        locBlocked = len(locBckt.keys())                                                                        #tallying # of local records in dictionary
        formLocBlocked = format(locBlocked, ',d')                                                               #formatting local record tally
        forBlocked = len(forBckt.keys())                                                                        #tallying # of foreign records in dictionary
        formForBlocked = format(forBlocked, ',d')                                                               #formatting foreign record tally
        print 'number of blocked local records: %s' % formLocBlocked                                            #report # of local records blocked
        print 'number of blocked foreign records: %s' % formForBlocked                                          #report # of foreign records blocked
        return locBckt, forBckt


    

    def hnMtch3(self, (locBckt, forBckt), mLevel):                                                              #takes in blocked local data, blocked foreign data, and WSID matching level
        """
        Takes blocked local & foreign dictionaries, and performs HN blocking.
        Matches reported to dictionaries where HN is key
        :param Location Bucket: Dictionary type
        :param Foreign Bucket: Dictionary type
        :param mLevel: user selection for BSA or WSID level matching ('WIDE' or 'NARROW')
        :return Housing Number Matches: Dictionary type where local id is key       
        """
        hnMtchs = {}                                                                                            #dictionary repository for HN-based matches
        idPos = 0                                                                                               #position of unique ID in input datasets
        hnPos = 1                                                                                               #position of HN in input datasets
        wsidPos = 13                                                                                            #position of WSID in input datasets
        for locRec in locBckt.values():                                                                         #for each local record
            locID = locRec[idPos]                                                                               #local ID
            locHN = locRec[hnPos]                                                                               #local HN
            locWSID = locRec[wsidPos]                                                                           #local WSID
            for forRec in forBckt.values():                                                                     #for each foreign record
                forID = forRec[idPos]                                                                           #foreign ID
                forHN = forRec[hnPos]                                                                           #foreign HN
                forWSID = forRec[wsidPos]                                                                       #foreign WSID
                # add something around here for HN or HN RANGE matching....
                if mLevel == 'NARROW':                                                                          #NARROW matching is WSID-specific
                    if (locHN == forHN and locWSID == forWSID):                                                 #if an exact match between the local & foregin HN & WSID
                        if locID in hnMtchs.keys():                                                             #if match key (local ID) already in matches destination
                            hnMtchs[locID] += [[locRec,forRec]]                                                 #append local & foreign data to matches
                        else:                                                                                   #if match key (local ID) not present in matches destination
                            hnMtchs[locID] = [[locRec,forRec]]                                                  #append key (local ID) and local & foreign data to matches
                if mLevel == 'WIDE':                                                                            #WIDE matching is WSID-agnostic
                    if locHN == forHN:                                                                          #if an exact match between the local & foregin HN only
                        if locID in hnMtchs.keys():                                                             #if match key (local ID) already in matches destination
                            hnMtchs[locID] += [[locRec,forRec]]                                                 #append local & foreign data to matches
                        else:                                                                                   #if match key (local ID) not present in matches destination
                            hnMtchs[locID] = [[locRec,forRec]]                                                  #append key (local ID) and local & foreign data to matches
        return(hnMtchs)




    def stMtch(self, hnMtchs, tHold, lvl):                                                                      #takes in HN blocked local data, HN blocked foreign data, JW threshold, and pre/suffix matching level
        """
        Identifies Street name matches from HN blocked output
        :param Housing Number Matches: Dictionary generated from "def hnMtch3()"        
        :param tHold: Double Integer for street base name JW Scoring Threshold
        :param lvl: user selection for street prefix/suffic level matching ('EXACT','CLOSE','ALL')
            'ALL': report base name score with no additional checks (current)     FASTEST MATCHING, SLOWEST REPORTING!
            'EXACT': only report out base name score if all other street name fields match exactly    SLOWER MATCHING, FASTEST REPORTING!
            'CLOSE': only report out base name score if 'fuzzy' matching between local and foreign other street fields.  BEST MIX???
        :return: Street Matches: Dictionary type where local id is key
        """
        stMtches = {}                                                                                           #dictionary repository for final matches
        inputIDPos = 0                                                                                          #position of ID in local/foreign data dictionary 'values' 
        snpdPos = 4                                                                                             #position of SNPD in local/foreign data dictionary 'values'  
        snptPos = 5                                                                                             #position of SNPT in local/foreign data dictionary 'values'
        osnPos = 6                                                                                              #position of OSN in local/foreign data dictionary 'values'
        msnPos = 7                                                                                              #position of MSN in local/foreign data dictionary 'values'
        ssnPos = 8                                                                                              #position of SSN in local/foreign data dictionary 'values'
        snstPos = 9                                                                                             #position of SNST in local/foreign data dictionary 'values'
        snsdPos = 10                                                                                            #position of SNSD in local/foreign data dictionary 'values'
        snePos = 11                                                                                             #position of SNE in local/foreign data dictionary 'values'
        for locKey in hnMtchs.keys():                                                                           #for HN key in local dictionary         
            for hnMtchPair in hnMtchs[locKey]:
                locVals = hnMtchPair[0]
                forVals = hnMtchPair[1]
                locInputID = locVals[inputIDPos]                                                                #local ID
                locSNPD = locVals[snpdPos]                                                                      #local street name prefix directional
                locSNPT = locVals[snptPos]                                                                      #local street name prefix type
                locOSN = locVals[osnPos]                                                                        #local street OSN base name
                locMSN = locVals[msnPos]                                                                        #local street MSN base name
                locSSN = locVals[ssnPos]                                                                        #local street SSN base name
                locSNST = locVals[snstPos]                                                                      #local street name type
                locSNSD = locVals[snsdPos]                                                                      #local street name suffix directional
                locSNE = locVals[snePos]
                forSNPD = forVals[snpdPos]                                                                      #foreign street name prefix directional
                forSNPT = forVals[snptPos]                                                                      #foreign street name prefix type
                forOSN = forVals[osnPos]                                                                        #foreign street OSN base name
                forMSN = forVals[msnPos]                                                                        #foreign street MSN base name
                forSSN = forVals[ssnPos]                                                                        #foreign street SSN base name
                forSNST = forVals[snstPos]                                                                      #foreign street name type
                forSNSD = forVals[snsdPos]                                                                      #foreign street name suffix directional
                forSNE = forVals[snePos]                                                                        #foreign street name extension
                locNames = (locOSN,locMSN,locSSN)                                                               #listing of local base street name fields
                forNames = (forOSN,forMSN,forSSN)                                                               #listing of foreign base street name fields
                scores = []
                for name1 in locNames:
                    for name2 in forNames:
                        if name1 == name2:                                                                      #EXACT BASE NAME MATCH (SCORE = 1)
                            if lvl == 'ALL':                                                                    #If 'ALL" selected (parameter)
                                scores.append(1)                                                                #Report base-name match score.  No additional conditionals...
                            if lvl == 'EXACT':                                                                  #If "EXACT" selected (parameter)
                                                                                                                #only report out base-name match score if ALL OTHER street fields match EXACTLY
                                if locSNPD == forSNPD and locSNPT == forSNPT and locSNST == forSNST and locSNSD == forSNSD and locSNE == forSNE:      
                                    scores.append(1)                                                            #report base-name match score
                                else:
                                    scores.append(0)                                                            #Otherwise, report the match score as 0
                            if lvl == 'CLOSE':                                                                  #if "CLOSE" selected (parameter)
                                                                                                                #only report out base-name match score if ALL OTHER street fields 'closely' match (either they both match exactly or one is null and the other is not null
                                '''NOTE: can more be done so that things like directional 'N' match to 'NW'...things wehre BOTH are not null and different, but close enough? '''
                                if (((locSNPD == forSNPD) or (locSNPD == '' and forSNPD != '') or (locSNPD != '' and forSNPD == '')) and                                        
                                ((locSNPT == forSNPT) or (locSNPT == '' and forSNPT != '') or (locSNPT != '' and forSNPT == '')) and
                                ((locSNST == forSNST) or (locSNST == '' and forSNST != '') or (locSNST != '' and forSNST == '')) and
                                ((locSNSD == forSNSD) or (locSNSD == '' and forSNSD != '') or (locSNSD != '' and forSNSD == '')) and 
                                ((locSNE == forSNE) or (locSNE == '' and forSNE != '') or (locSNE != '' and forSNE == ''))):
                                    scores.append(1)                                                            #Report base-name match score
                                else:
                                    scores.append(0)                                                            #Otherwise, report the match score as 0
                        else:                                                                                   #if thee is no exact base street name match, try equivocated matching
                            jwScore = jellyfish.jaro_winkler(unicode(name1),unicode(name2))                     #determine JW score of name match
                            if tHold <= jwScore < 1:                                                            #if within the JW break (parameter), an equivocated match.
                                if lvl == 'ALL':                                                                #If 'ALL" selected (parameter)
                                    scores.append(jwScore)                                                      #report base-name match score.  No additional conditionals...
                                if lvl == 'EXACT':                                                              #If "EXACT" selected (parameter)
                                                                                                                #only report out JW score if ALL OTHER street fields match EXACTLY
                                    if locSNPD == forSNPD and locSNPT == forSNPT and locSNST == forSNST and locSNSD == forSNSD and locSNE == forSNE:
                                        scores.append(jwScore)                                                  #Report JW of base-name match score
                                    else:
                                        scores.append(0)                                                        #Otherwise, report the match score as 0
                                if lvl == 'CLOSE':                                                              #If "EXACT" selected (parameter)
                                                                                                                #only report out base-name match score if ALL OTHER street fields 'closely' match (either they both match exactly or one is null and the other is not null
                                    '''NOTE: can more be done so that things like directional 'N' match to 'NW'...things wehre BOTH are not null and different, but close enough? ''' 
                                    if (((locSNPD == forSNPD) or (locSNPD == '' and forSNPD != '') or (locSNPD != '' and forSNPD == '')) and                                        
                                    ((locSNPT == forSNPT) or (locSNPT == '' and forSNPT != '') or (locSNPT != '' and forSNPT == '')) and
                                    ((locSNST == forSNST) or (locSNST == '' and forSNST != '') or (locSNST != '' and forSNST == '')) and
                                    ((locSNSD == forSNSD) or (locSNSD == '' and forSNSD != '') or (locSNSD != '' and forSNSD == '')) and 
                                    ((locSNE == forSNE) or (locSNE == '' and forSNE != '') or (locSNE != '' and forSNE == ''))):
                                        scores.append(jwScore)                                                  #Report JW of base-name match score
                                    else:
                                        scores.append(0)                                                        #Otherwise, report the match score as 0
                            else:                                                                               #if not an exact of JW base-name match, it's not a match
                                scores.append(0)                                                                #assign a score of 0
                mtchScore = 0                                                                                   #used to determine if any of 9 name matches are 'good' or not
                for score in scores:                                                                            #loop through all 9 name scores recorded (0, 1, or JW)
                    mtchScore+=score                                                                            #add them together
                if mtchScore > 0:                                                                               #if the final score is >0, then there is at least 1 'good' name match
                    if locInputID in stMtches.keys():                                                           #if local ID already a key in the match dictionary
                        stMtches[locInputID] += [[locVals,forVals,scores]]                                      #add the local data, foreign data, and name match scores to the dictionary as a match
                    else:                                                                                       #if local ID is not yet a key in the match dictonary
                        stMtches[locInputID] = [[locVals,forVals,scores]]                                       #report the key and the local data, foreign data, and name match scores to the dictionary as a match
        return stMtches



    def terMtch(self, stMtches):                                                                                #takes in post-street matched records.  Key= local ID, Values = local and foreign match pair, name scores
        """
        Method for tertiary matching
        :param Street Matches: Dictionary type that is generated from "def stMtch()"
        :return Tertiary Matches: Dictionary type
        """
        terMtches = {}                                                                                          #repository dictionary for final results
        inPos = 0                                                                                               #position of ID in local/foreign data dictionary 'values'
        snpdPos = 4                                                                                             #position of SNPD in local/foreign data dictionary 'values'                                                                                           
        snptPos = 5                                                                                             #position of SNPT in local/foreign data dictionary 'values'
        snstPos = 9                                                                                             #position of SNST in local/foreign data dictionary 'values'
        snsdPos = 10                                                                                            #position of SNSD in local/foreign data dictionary 'values'
        snePos = 11                                                                                             #position of SNE in local/foreign data dictionary 'values'
        wsdPos = 12                                                                                             #position of WSD in local/foreign data dictionary 'values'
        wsiPos = 13                                                                                             #position of WSI in local/foreign data dictionary 'values'
        zipPos = 14                                                                                             #position of ZIP in local/foreign data dictionary 'values'
        mtfccPos = 15                                                                                           #position of MTFCC in local/foreign data dictionary 'values'
        gqPos = 16                                                                                              #position of GQ NAME in local/foreign data dictionary 'values'
        stPos = 19                                                                                              #position of ST in local/foreign data dictionary 'values'
        couPos = 20                                                                                             #position of COU in local/foreign data dictionary 'values'
        tctPos = 21                                                                                             #position of TCT in local/foreign data dictionary 'values'
        bcuPos = 22                                                                                             #position of BCU in local/foreign data dictionary 'values'
        tabblkPos = 23                                                                                          #position of TABBLK in local/foreign data dictionary 'values'
        for mtchKey in stMtches.keys():                                                                         #for each local ID key
            for mtch in stMtches[mtchKey]:                                                                      #for each foreign match associated with local ID
                locStuff = mtch[0]                                                                              #'local stuff' list 
                forStuff = mtch[1]                                                                              #'foreign stuff' list 
                nmeScores = mtch[2]                                                                             #name match scores from street name matching            
                locInputID = locStuff[inPos]                                                                    #local ID
                locSNPD = locStuff[snpdPos]                                                                     #local SNPD
                locSNPT = locStuff[snptPos]                                                                     #local SNPT
                locSNST = locStuff[snstPos]                                                                     #local SNST
                locSNSD = locStuff[snsdPos]                                                                     #local SNSD
                locSNE = locStuff[snePos]                                                                       #local SNE
                locWSD = locStuff[wsdPos]                                                                       #local WSD
                locWSI = locStuff[wsiPos]                                                                       #local WSI
                locZIP = locStuff[zipPos]                                                                       #local ZIP
                locMTFCC = locStuff[mtfccPos]                                                                   #local MTFCC
                locGQ = locStuff[gqPos]                                                                         #local GQ Name
                locST = locStuff[stPos]                                                                         #local ST FIPS
                locCOU = locStuff[couPos]                                                                       #local COU FIPS
                locTCT = locStuff[tctPos]                                                                       #local Tract code
                locBCU = locStuff[bcuPos]                                                                       #local BCU code
                locBLK = locStuff[tabblkPos]                                                                    #local Block code
                #foreign tertiary items
                forSNPD = forStuff[snpdPos]                                                                     #foregin SNPD
                forSNPT = forStuff[snptPos]                                                                     #foreign SNPT
                forSNST = forStuff[snstPos]                                                                     #foreign SNST
                forSNSD = forStuff[snsdPos]                                                                     #foreign SNSD
                forSNE = forStuff[snePos]                                                                       #foreign SNE
                forWSD = forStuff[wsdPos]                                                                       #foreign WSD
                forWSI = forStuff[wsiPos]                                                                       #foreign WSI
                forZIP = forStuff[zipPos]                                                                       #foreign ZIP
                forMTFCC = forStuff[mtfccPos]                                                                   #foreign MTFCC
                forGQ = forStuff[gqPos]                                                                         #foreign GQ Name
                forST = forStuff[stPos]                                                                         #foreign ST FIPS
                forCOU = forStuff[couPos]                                                                       #foreign COU FIPS
                forTCT = forStuff[tctPos]                                                                       #foreign Tract code
                forBCU = forStuff[bcuPos]                                                                       #foreign BCU code
                forBLK = forStuff[tabblkPos]                                                                    #foreign Block code

                #do binary (0 or 1) scoring on tertiary items...ranking uses tertiary scoring in addition to name scoring to come up with final score to rank on
                #could add weights to any individual scores (i.e. terscores.append(1*weight). Leaving as-is for now.
                #start scoring
                terScores = []                                                                                  #placeholder for scoring values
                if locSNPD == forSNPD:                                                                          #if local/foreign SNPDs match, add '1' to scoring list
                    terScores.append(1)
                else:                                                                                           #if they don't match, add '0' to scoring list
                    terScores.append(0)
                if locSNPT == forSNPT:                                                                          #if local/foreign SNPTs match, add '1' to scoring list
                    terScores.append(1)
                else:                                                                                           #if they don't match, add '0' to scoring list
                    terScores.append(0)
                if locSNST == forSNST:                                                                          #if local/foreign SNSTs match, add '1' to scoring list
                    terScores.append(1)
                else:                                                                                           #if they don't match, add '0' to scoring list
                    terScores.append(0)
                if locSNSD == forSNSD:                                                                          #if local/foreign SNSDs match, add '1' to scoring list
                    terScores.append(1)
                else:                                                                                           #if they don't match, add '0' to scoring list
                    terScores.append(0)
                if locSNE == forSNE:                                                                            #if local/foreign SNEs match, add '1' to scoring list
                    terScores.append(1)
                else:                                                                                           #if they don't match, add '0' to scoring list
                    terScores.append(0)
                if locWSD == forWSD:                                                                            #if local/foreign WSDs match, add '1' to scoring list
                    terScores.append(1)
                else:                                                                                           #if they don't match, add '0' to scoring list
                    terScores.append(0)
                if locWSI == forWSI:                                                                            #if local/foreign WSIs match, add '1' to scoring list
                    terScores.append(1)
                else:                                                                                           #if they don't match, add '0' to scoring list
                    terScores.append(0)
                if locZIP == forZIP:                                                                            #if local/foreign ZIPs match, add '1' to scoring list
                    terScores.append(1)
                else:                                                                                           #if they don't match, add '0' to scoring list
                    terScores.append(0)                
                if locMTFCC == forMTFCC:                                                                        #if local/foreign MTFCCs match, add '1' to scoring list
                    terScores.append(1)
                else:                                                                                           #if they don't match, add '0' to scoring list
                    terScores.append(0)
                if locGQ == forGQ:                                                                              #if local/foreign GQ Names match, add '1' to scoring list
                    terScores.append(1)
                else:                                                                                           #if they don't match...
                    if locGQ != '' and forGQ != '':                                                             #if both the local and foreign GQ Name is not null
                       jwScore = jellyfish.jaro_winkler(unicode(locGQ),unicode(forGQ))                          #determine the JW difference score between the local/foreign GQ Name
                       rJW = round(jwScore,2)                                                                   #round the JW score to 2 decimal places
                       if rJW > .8:                                                                             #if the score is >.80 (no sense floating GQ Name mismatches to the top of multiple matches)
                           terScores.append(rJW)                                                                # add the JW score to scoring list
                       else:                                                                                    #otherwise add '0' to scoring list
                           terScores.append(0)
                    else:                                                                                       #if local or foreign GQ name is null, report '0' to scoring list
                        terScores.append(0)                
                if locST == forST:                                                                              #if local/foreign STs match, add '1' to scoring list
                    terScores.append(1)
                else:                                                                                           #if they don't match, add '0' to scoring list
                    terScores.append(0)
                if locCOU == forCOU:                                                                            #if local/foreign COUs match, add '1' to scoring list
                    terScores.append(1)
                else:                                                                                           #if they don't match, add '0' to scoring list
                    terScores.append(0)
                if locTCT == forTCT:                                                                            #if local/foreign TCTs match, add '1' to scoring list
                    terScores.append(1)
                else:                                                                                           #if they don't match, add '0' to scoring list
                    terScores.append(0)
                if locBCU == forBCU:                                                                            #if local/foreign BCUs match, add '1' to scoring list
                    terScores.append(1)
                else:                                                                                           #if they don't match, add '0' to scoring list
                    terScores.append(0)
                if locBLK == forBLK:                                                                            #if local/foreign Blocks match, add '1' to scoring list
                    terScores.append(1)
                else:                                                                                           #if they don't match, add '0' to scoring list
                    terScores.append(0)                            
                #put output dictionary together with input 'stuff' and tertiary scoring
                if locInputID in terMtches.keys():
                    terMtches[locInputID] += [[locStuff,forStuff,nmeScores,terScores]]
                else:
                    terMtches[locInputID] = [[locStuff,forStuff,nmeScores,terScores]]
        return terMtches


        

    def scoRank(self, terMtches):  # Add something for adjusting/weighting ind. terScores?                      #takes in post-tertiary matched records.  Key=local ID, Values = local and foreign match pair, name scores, tertiary scores
        """
        Integrates best street name score w/ tertiary scoring matches
        :param Tertiary Matches: generated from "def terMtch()"; Dictionary Type
        :return Final Scoring Rank of Matches: Dictionary type, where local ID is key
        """
        ranks = {}                                                                                              #repository dictionary for final results
        scored = {}                                                                                             #temp dictionary for storing overall match score for all foreign matches per each local record
        inPos = 0                                                                                               #ID position in input datasets
        for key in terMtches.keys():                                                                            #for each local record
            for mtch in terMtches[key]:                                                                         #for each match per local record
                locStuff = mtch[0]                                                                              #local data items
                forStuff = mtch[1]                                                                              #foreign data items
                nmeScores = mtch[2]                                                                             #base name matching scores
                terScores = mtch[3]                                                                             #tertiary matching scores
                locInputId = locStuff[inPos]                                                                    #local ID
                # develop overall match score
                overScore = 0                                                                                   #overall score, starting at 0
                maxNme = max(nmeScores)                                                                         #take largest name match score
                overScore += maxNme                                                                             #add largets name match score to overall score
                for i in terScores:                                                                             #for each score in all the tertiary scores
                    overScore += i                                                                              #add the tertiary score to the overall score
                if locInputId in scored.keys():                                                                 #if the local ID is already in the 'scored' temp dictionary
                    scored[locInputId] += [[locStuff, forStuff, nmeScores, terScores, [overScore]]]             #append the local data, foreign data, name scores, tertiary scores, and overall score to the key (local ID)
                else:                                                                                           #if the local ID is not already in the 'scored' temp dictionary
                    scored[locInputId] = [[locStuff, forStuff, nmeScores, terScores, [overScore]]]              #add the key (local ID) and local data, foreign data, name scores, tertiary scores, and overall score
        # go through again by key and rank from scores
        for iKey in scored.keys():                                                                              #for each local record in the temp 'scores' dictionary
            matchNum = len(scored[iKey])                                                                        #number of matches per local record
            if matchNum == 1:                                                                                   #if only one match for the local record
                rank = [1]                                                                                      #give it a rank of 1
                rec = scored[iKey][0]                                                                           #take that (single) record with local data, foreign data, name scores, tertiary scores, and overall score
                rec.append(rank)                                                                                #append the rank value
                ranks[iKey] = [rec]                                                                             #add everything to the 'rank' repository dictionary (local data, foreign data, name scores, tertiary scores, overall score, rank)
            else:                                                                                               #if >1 match per local record
                sortIt = sorted(scored[iKey], key=itemgetter(4), reverse=True)                                  #sort on overall score list within each key (local ID)
                for numB in range(matchNum):                                                                    #for each match per local record
                    sortIt[(numB)].append([numB + 1])                                                           #give rank position in order within sorted list
                ranks[iKey] = sortIt                                                                            #add everything to the 'rank' repository dictionary (local data, foreign data, name scores, tertiary scores, overall score, rank)
        return ranks




    def outPutt(self, ranks, deets):                                                                            #takes in post-ranked matched records, and reporting detail level.  Key=local ID, Values = local and foreign match pair, name scores, tertiary scores, final score, rank
        '''
        Integrates ranked matches into output-friendly formatted string
        :param Ranksed Matches: generated from "def scoRank()"; Dictionary Type
        :deets: user defined selection for level of reporting detail
            'ALL' - All matches and data elements, scores, rank reported
            'BEST' - Only BEST match reported, and only local/forign IDs
        :return Final Scoring Rank of Matches: Dictionary type, where local ID is key
        '''
        fnlLst = []                                                                                             #final listing of the matching output (for writing to disk)
        if deets == 'BEST':                                                                                     #BEST designed to only report rank=1 match, with only IDs of local/foreign records
            fnlLst.append(['LOCAL_ID','FOREIGN_ID','MAFID'])                                                    #header for 'BEST' result reporting
        else:                                                                                                   #header for 'ALL' result reporting
            fnlLst.append(['L_INPUTID','L_HN','L_RANGE_FROM','L_RANGE_TO','L_SNPD','L_SNPT','L_OSN','L_MSN','L_SSN','L_SNST','L_SNSD','L_SNE','L_WSD','L_WSI','L_ZIP','L_MTFCC','L_GQ_NAME','L_LATITUDE','L_LONGITUDE','L_ST','L_COU','L_TCT','L_BCU','L_TABBLK','F_INPUTID','F_HN','F_RANGE_FROM','F_RANGE_TO','F_SNPD','F_SNPT','F_OSN','F_MSN','F_SSN','F_SNST','F_SNSD','F_SNE','F_WSD','F_WSI','F_ZIP','F_MTFCC','F_GQ_NAME','F_LATITUDE','F_LONGITUDE','F_ST','F_COU','F_TCT','F_BCU','F_TABBLK','MAFID','LOSN_FOSN','LOSN_FMSN','LOSN_FSSN','LMSN_FOSN','LMSN_FMSN','LMSN_FSSN','LSSN_FOSN','LSSN_FMSN','LSSN_FSSN','SNPD_CH','SNPT_CH','SNST_CH','SNSD_CH','SNE_CH','MTFCC_CH','GQ_CH','ST_CH','COU_CH','TCT_CH','BCU_CH','BLK_CH','FNL_SCORE','RANK'])        
        for key in ranks.keys():                                                                                #for each local record
            if deets == 'BEST':                                                                                 #if BEST selected
                besty = ranks[key][0]                                                                           #first match in dictionary values is the highest ranked, so just pull the 1st item
                locStuff = besty[0]                                                                             #local data items
                forStuff = besty[1]                                                                             #foreign data items
                lclID = locStuff[0]                                                                             #local ID
                forID = forStuff[0]                                                                             #foreign ID
                mafid = forStuff[24]                                                                            #foreign MAFID
                fnlLst.append([lclID,forID,mafid])                                                              #append the IDs to the final reporting listing
            if deets == 'ALL':                                                                                  #if ALL selected
                for lclGrp in ranks[key]:                                                                       #for each match associated with the local ID
                    sngLst = []                                                                                 #blank intermediary list used for compiling all record info
                    locStuff = lclGrp[0]                                                                        #local data items
                    forStuff = lclGrp[1]                                                                        #foreign data items
                    nameScores = lclGrp[2]                                                                      #base name scores (all)
                    terScores = lclGrp[3]                                                                       #tertiary matching scores
                    finScore = lclGrp[4]                                                                        #final score
                    finRank = lclGrp[5]                                                                         #final rank
                    for i in locStuff[:-1]:                                                                     #seems to have an extraneous (empty) data item, so don't report it out, or the data won't match the header
                        sngLst.append(i)                                                                        #add each local element to intermediary list
                    for i in forStuff[:-1]:                                                                     #seems to have an extraneous (empty) data item, so don't report it out, or the data won't match the header
                        sngLst.append(i)                                                                        #add each foreign element to intermediary list
                    for i in nameScores:
                        sngLst.append(i)                                                                        #add each base name score to intermediary list
                    for i in terScores:
                        sngLst.append(i)                                                                        #add each tertiary score to intermediary list
                    for i in finScore:
                        sngLst.append(i)                                                                        #add total score to intermediary list
                    for i in finRank:
                        sngLst.append(i)                                                                        #add rank to intermediary list
                    fnlLst.append(sngLst)                                                                       #add intermediary list to final reporting list
        return fnlLst



    

########################################################################################################################

# Interesting Data Structure Resources:
# https://stackoverflow.com/questions/26664685/pythonic-alternative-to-nested-dictionaries-with-the-same-keys
# http://knuth.luther.edu/~leekent/CS2Plus/chap10/chap10.html

if __name__ == '__main__':
    local_file = Match()
    local_file.run()
