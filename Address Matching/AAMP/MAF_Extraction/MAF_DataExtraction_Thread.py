import os
import cx_Oracle as Oracle
import pandas as pd
import threading


class mafThread(threading.Thread):
    def __init__(self, threadID, fmeWS, env, jbid, password, string_list, folder_loc):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.fmeWS = fmeWS
        self.env = env
        self.jbid = jbid
        self.password = password
        self.string_list = string_list
        self.folder_loc = folder_loc

    def extract(self, file_name, env, jbid, password, block_string, folder_loc):
        query = """ select * from
                    (
                    select 
                    inputid,  
                    RTRIM(LTRIM(MTLIBS.MTDSF.standardize_address(hn||' '||street||' '||wsid,' ').hnp||MTLIBS.MTDSF.standardize_address(hn||' '||street||' '||wsid,' ').hn||MTLIBS.MTDSF.standardize_address(hn||' '||street||' '||wsid,' ').hnp2||MTLIBS.MTDSF.standardize_address(hn||' '||street||' '||wsid,' ').hn2||' '||MTLIBS.MTDSF.standardize_address(hn||' '||street||' '||wsid,' ').hns)) hn,
                    range_from,
                    range_to,
                    MTLIBS.MTDSF.standardize_address(hn||' '||street||' '||wsid,' ').snpd snpd,
                    MTLIBS.MTDSF.standardize_address(hn||' '||street||' '||wsid,' ').snpt snpt,
                    MTLIBS.MTDSF.standardize_address(hn||' '||street||' '||wsid,' ').osn osn,
                    MTLIBS.MTDSF.standardize_address(hn||' '||street||' '||wsid,' ').msn msn,
                    MTLIBS.MTDSF.standardize_address(hn||' '||street||' '||wsid,' ').ssn ssn,
                    MTLIBS.MTDSF.standardize_address(hn||' '||street||' '||wsid,' ').snst snst,
                    MTLIBS.MTDSF.standardize_address(hn||' '||street||' '||wsid,' ').snsd snsd,
                    MTLIBS.MTDSF.standardize_address(hn||' '||street||' '||wsid,' ').sne sne,
                    MTLIBS.MTDSF.standardize_address(hn||' '||street||' '||wsid,' ').wsd wsd,
                    MTLIBS.MTDSF.standardize_address(hn||' '||street||' '||wsid,' ').wsi wsi,
                    zip, mtfcc, gq_name, latitude, longitude, st, cou, tct, bcu, tabblk, mafid
                    from
                        (
                        select addr.oid inputid, addr.hn, '' range_from, '' range_to, upper(fn.displayname) street, cde.descr, RTRIM(LTRIM(cde.descr||' '||addr.wsid1)) WSID, addr.zip, 
                        mu.mtfcc, gq.gqname gq_name, mu_latlong.latitude, mu_latlong.longitude, mu_geo.*, mu.mafid  
                        from maftiger.mafunit mu
                        join maftiger.address addr on mu.oid = addr.oidmu
                        left join maftiger.featurename fn on addr.oidfn = fn.oid
                        left join maftiger.gq on mu.oid = gq.oidmu
                        left join 
                            (  -- wsid code translation
                            select * from mafdata.stancode
                            where category = 'WS'
                            )
                            cde on addr.wsdesc1 = cde.code
                        left join
                            ( --oidmu w/ geocode info
                            select bloks.oid as oidmu, bloks.statefp st, bloks.countyfp cou, bloks.tractce tct, bcus.bcuid bcu, bloks.blockce tabblk  
                            from
                                (  --oidmu w/ tabblock info    
                                select mu.oid, mu.mafid, blk.statefp, blk.countyfp, blk.tractce, blk.blockce     
                                from maftiger.mafunit mu
                                join maftiger.featmafunitrel feat on mu.oid = feat.oidmu
                                join maftiger.tabblock blk on feat.oidfe = blk.oid
                                and feat.ispref = 'Y'
                                and blk.vintage = '40'        
                                ) bloks
                            join
                                (  --oidmu w/ bcu info
                                select mu.oid, mu.mafid, bcu.statefp, bcu.countyfp, bcu.tractce, bcu.bcuid
                                from maftiger.mafunit mu
                                join maftiger.face face on mu.oidfa = face.oid
                                join maftiger.mt_relation$ mtr1 on FACE.OID = mtr1.tg_id
                                join maftiger.mt_relation$ mtr2 on mtr1.topo_id = mtr2.topo_id
                                join maftiger.bcu bcu on mtr2.tg_id = bcu.oid
                                and mtr1.tg_layer_id = '8301'
                                and mtr2.tg_layer_id = '2881'
                                and bcu.vintage = '90'        
                                ) bcus
                            on bloks.oid = bcus.oid
                            ) mu_geo
                            on mu.oid = mu_geo.oidmu
                        left join
                            (  -- oidmu w/ lat/long info
                            select feat.oidmu, mtnode.geometry.sdo_point.y latitude, mtnode.geometry.sdo_point.x longitude
                            from maftiger.msp msp
                            join maftiger.mt_relation$ mtr1 on msp.oid = mtr1.tg_id
                            join maftiger.mt_node$ mtnode on mtr1.topo_id = mtnode.node_id
                            join maftiger.featmafunitrel feat on msp.oid = feat.oidfe 
                            where mtr1.tg_layer_id = '5001'
                            and feat.ispref = 'Y'    
                            ) mu_latlong
                            on mu.oid = mu_latlong.oidmu    
                        --where (addr.isprefloc='Y' or addr.isprefmail = 'Y')           --not pulling any preferred addresses....can be done through post-match filtering  
                        )
                    --ADD BLOCKING PARAMETERS!!!
                    where zip in (%s)
                    )
                    where hn is not null """ \
                % block_string

        connection = Oracle.connect(jbid, password, env)
        maf_data_df = pd.read_sql(query, con=connection)
        out_file_name = file_name
        path = (os.path.join(folder_loc, out_file_name) + ".txt")
        maf_data_df.to_csv(path, header=["INPUTID", "HN", "RANGE_FROM", "RANGE_TO", "SNPD", "SNPT", "OSN", "MSN", "SSN",
                                         "SNST", "SNSD", "SNE", "WSD", "WSI", "ZIP", "MTFCC", "GQ_NAME",
                                         "LATITUDE", "LONGITUDE", "ST", "COU", "TCT", "BCU", "TABBLK", "MAFID"],
                           index=None, sep='|', mode='a')
        connection.close()
        return path

    def runZIPfme2(self, file_name, fmeWS, env, jbid, password, block_string, folder_loc):
        """
        Call FME ZIP workspace; will create a csv of data extracted from the MAF database
        different workspaces for different blocking types
        :param jbid: username for Oracle database connection
        :param password: password for Oracle database connection
        :param block_string: String made from local openCSV method
        :return mafData: associated MAF data as a local csv in a temp directory
        """

        fmeWS = fmeWS
        #fmeWSFolder = (os.getcwd() + r'\FME_Workspaces')
        out_file_name = file_name

        print 'running fme'

        fmeCommand = 'FME ' + fmeWS + \
                     ' --DB_CONNECT ' + env + \
                     ' --USERNAME ' + jbid + \
                     ' --PASSWORD ' + password + \
                     ' --destData ' + folder_loc + \
                     ' --FileName ' + out_file_name + \
                     ' --ZIP_List ' + block_string

        # subprocess.call(fmeCommand, shell=False, cwd=fmeWSFolder)
        maf_data = os.path.join(folder_loc, out_file_name)

        return maf_data

    def run(self):
        print "Starting Thread Extraction: " + str(self.threadID)
        self.extract((str(self.threadID) + "_copy"), self.env, self.jbid, self.password, self.string_list,
                     self.folder_loc)
        # self.runZIPfme2((str(self.threadID) + "_copy"), self.fmeWS, self.env, self.jbid, self.password,
        # self.string_list,
        # self.folder_loc)
        print "Exiting Thread: " + str(self.threadID)


__author__ = 'Matt Wilchek'
