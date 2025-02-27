from __future__ import absolute_import
from nose.tools import assert_equals, assert_not_equal
from nose import with_setup
import rowingdata
import datetime
import numpy as np
import pandas as pd
from parameterized import parameterized
import unittest
from pytz import utc
import six

from unittest import mock

class TestCumValues:
    df = pd.read_csv('testdata/cumvalues.csv')

    testcombis = [
        ('a','A'),
        ('b','B'),
        ('c','C'),
        ('d','D'),
        ('e','E'),
        ('f','F'),
        ('g','G'),
        ('h','H'),
        ]

    delta = 0.0001
    
    for e,r in testcombis:
        if e in df.index and r in df.index:
            expectedresult = df.loc[:,r]
            result = rowingdata.csvparsers.make_cumvalues(df.loc[:,e])[0]
            for i in range(len(result)):
                assert_equals(
                    np.abs(result.iloc[i]-expectedresult.iloc[i]
                    )<delta,True)

class TestBasicRowingData:
    row=rowingdata.rowingdata(csvfile='testdata/testdata.csv')

    def test_filetype(self):
        assert_equals(rowingdata.get_file_type('testdata/testdata.csv'),'csv')
    
    def test_basic_rowingdata(self):
        assert_equals(self.row.rowtype,'Indoor Rower')
        assert_equals(self.row.dragfactor,104.42931937172774)
        assert_equals(self.row.number_of_rows,191)
        assert_equals(self.row.rowdatetime,datetime.datetime(2016,5,20,13,41,26,962390,utc))
        totaldist=self.row.df['cum_dist'].max()
        totaltime=self.row.df['TimeStamp (sec)'].max()-self.row.df['TimeStamp (sec)'].min()
        totaltime=totaltime+self.row.df.ix[0,' ElapsedTime (sec)']
        assert_equals(totaltime, 540.04236011505122)
        assert_equals(totaldist, 2000)
        checks = self.row.check_consistency()
        assert_equals(checks['velo_time_distance'],True)
        #        assert_equals(checks['velo_valid'],True)

    def test_intervals_rowingdata(self):
        ts,ds,st=self.row.intervalstats_values()
        assert_equals(ts,[139.7,0.0,130.1,0.0,134.4,0.0,132.8,0.0])
        assert_equals(ds,[510,0,499,0,498,0,491,0])
        assert_equals(st,[4,3,4,3,4,3,4,3])
        sum=int(10*np.array(ts).sum())/10.
        assert_equals(sum,537.0)
        self.row.updateinterval_string('4x500m')
        assert_equals(len(self.row.df[' lapIdx'].unique()),4)
        ts,ds,st=self.row.intervalstats_values()
        assert_equals(ts,[137.0,0.0,130.2,0.0,134.8,0.0,135.1,0.0])
        assert_equals(ds,[500,0,500,0,500,0,500,0])
        assert_equals(st,[5,3,5,3,5,3,5,3])
        sum=int(10*np.array(ts).sum())/10.
        assert_equals(sum,537.0)

        str = self.row.intervalstats()
        assert_equals(len(str),281)
                      
class TestStringParser:
    def teststringparser(self):
        s1='8x500m/2min'
        s2='10km'
        s3='3min/3min+3min'
        s4='3min/3min + 3min'
        s5='4x((500m+500m)/2min)'
        s6='2x500m/500m'
        s7='4x30sec/30sec+5min/1min+2x10min'

        r1=[500,'meters','work',120,'seconds','rest',
              500,'meters','work',120,'seconds','rest',
              500,'meters','work',120,'seconds','rest',
              500,'meters','work',120,'seconds','rest',
              500,'meters','work',120,'seconds','rest',
              500,'meters','work',120,'seconds','rest',
              500,'meters','work',120,'seconds','rest',
              500,'meters','work',120,'seconds','rest'
        ]

        r2=[10000,'meters','work']

        r3=[180,'seconds','work',180,'seconds','rest',180,'seconds','work']
        r4=[180,'seconds','work',180,'seconds','rest',180,'seconds','work']

        r5=[500,'meters','work',500,'meters','work',120,'seconds','rest',
              500,'meters','work',500,'meters','work',120,'seconds','rest',
              500,'meters','work',500,'meters','work',120,'seconds','rest',
              500,'meters','work',500,'meters','work',120,'seconds','rest'
        ]

        r6=[500,'meters','work',500,'meters','rest',
              500,'meters','work',500,'meters','rest']

        r7=[30,'seconds','work',30,'seconds','rest',
              30,'seconds','work',30,'seconds','rest',
              30,'seconds','work',30,'seconds','rest',
              30,'seconds','work',30,'seconds','rest',
              300,'seconds','work',60,'seconds','rest',
              600,'seconds','work',600,'seconds','work']

        t1=rowingdata.trainingparser.parse(s1)
        t2=rowingdata.trainingparser.parse(s2)
        t3=rowingdata.trainingparser.parse(s3)
        t4=rowingdata.trainingparser.parse(s4)
        t5=rowingdata.trainingparser.parse(s5)
        t6=rowingdata.trainingparser.parse(s6)
        t7=rowingdata.trainingparser.parse(s7)

        assert_equals(t1,r1)
        assert_equals(t2,r2)
        assert_equals(t3,r3)
        assert_equals(t4,r4)
        assert_equals(t5,r5)
        assert_equals(t6,r6)
        assert_equals(t7,r7)

class TestPhysics:
    row = rowingdata.rowingdata(csvfile='testdata/testdata.csv')

    def test_getpower(self):
        velo = 4.0
        r = rowingdata.getrower()
        rg = rowingdata.getrigging()
        row = rowingdata.SpeedCoach2Parser('testdata/SpeedCoach2v2.12.csv')
        row = rowingdata.rowingdata(df=row.df)
        result = row.otw_setpower_silent(skiprows=40)
        assert_equals(result,1)

class TestBearing:
    row = rowingdata.rowingdata(csvfile='testdata/testdata.csv')

    def test_bearing(self):
        velo = 4.0
        r = rowingdata.getrower()
        rg = rowingdata.getrigging()
        row = rowingdata.SpeedCoach2Parser('testdata/SpeedCoach2v2.12.csv')
        row = rowingdata.rowingdata(df=row.df)
        result = row.add_bearing()
        assert_equals(result,1)

class TestCumCP:
    def test_cumcp(self):
        row1 = rowingdata.rowingdata(csvfile='testdata/testdata.csv')
        row2 = rowingdata.rowingdata(csvfile='testdata/testdata.csv')
        df = rowingdata.cumcpdata([row1,row2])
        isempty = df.empty

        assert_equals(isempty,False)
        
    def test_histo(self):
        row1 = rowingdata.rowingdata(csvfile='testdata/testdata.csv')
        row2 = rowingdata.rowingdata(csvfile='testdata/testdata.csv')
        power = rowingdata.histodata([row1,row2])
        isempty = len(power)==0

        assert_equals(isempty,False)

class TestOperations:
    def test_add_overlap(self):
        row1 = rowingdata.rowingdata(csvfile='testdata/testdata.csv')
        row2 = rowingdata.rowingdata(csvfile='testdata/testdata.csv')

        row = row1+row2

        len1 = len(row)
        len2 = len(row1)

        assert_equals(len1,len2)

    def test_getvalues(self):
        row = rowingdata.rowingdata(csvfile='testdata/testdata.csv')
        spm = row.getvalues(' Cadence (stokes/min)')

        assert_equals(len(row),len(spm))

    def test_repair(self):
        row = rowingdata.rowingdata(csvfile='testdata/testdata.csv')
        len1 = len(row)

        row.repair()

        len2 = len(row)

        assert_equals(len1,len2)

    def test_spmfromtimestamp(self):
        row = rowingdata.rowingdata(csvfile='testdata/testdata.csv')
        row.spm_fromtimestamps()
        
class TestSummaries:
    def test_summary(self):
        row = rowingdata.rowingdata(csvfile='testdata/testdata.csv')
        summary = row.summary()
        emptysummary = len(summary) == 0

        assert_equals(emptysummary,False)

class TestCharts:
    @mock.patch("matplotlib.pyplot.figure")
    @mock.patch("matplotlib.figure.Figure")
    def test_plot_erg(self,mock_fig, mock_Fig):
        row = rowingdata.rowingdata(csvfile='testdata/testdata.csv')
        row.plotmeters_erg()
        row.plottime_erg()
        fig = row.get_metersplot_erg2('aap')
        fig = row.get_timeplot_erg2('aap')
        fig = row.get_pacehrplot('aap')
        fig = row.get_paceplot('aap')
        fig = row.get_metersplot_erg('aap')
        fig = row.get_timeplot_erg('aap')
        row.plottime_hr()
        row.piechart()
        row.power_piechart()
        fig = row.get_power_piechart('aap')
        fig = row.get_piechart('aap')

    @mock.patch("matplotlib.pyplot.figure")
    @mock.patch("matplotlib.figure.Figure")
    def test_plot_otw(self, mock_fig, mock_Fig):
        row = rowingdata.SpeedCoach2Parser(csvfile='testdata/Speedcoach2example.csv')
        row = rowingdata.rowingdata(df=row.df)
        row.plotmeters_otw()

        row.plottime_otw()
        row.plottime_otwpower()
        fig = row.get_timeplot_otw('aap')
        fig = row.get_metersplot_otw('aap')
        fig = row.get_time_otwpower('aap')
        fig = row.get_metersplot_otwpower('aap')
        fig = row.get_timeplot_otwempower('aap')
        fig = row.get_metersplot_otwempower('aap')
        
class TestCorrectedRowingData:
    row=rowingdata.rowingdata(csvfile='testdata/correctedpainsled.csv')

    def test_filetype(self):
        assert_equals(rowingdata.get_file_type('testdata/testdata.csv'),'csv')
    
    def test_basic_rowingdata(self):
        assert_equals(self.row.rowtype,'Indoor Rower')
        assert_equals(self.row.dragfactor,95.8808988764045)
        assert_equals(self.row.number_of_rows,445)
        assert_equals(self.row.rowdatetime,datetime.datetime(2017,5,30,19,4,16,383211,utc))
        totaldist=self.row.df['cum_dist'].max()
        totaltime=self.row.df['TimeStamp (sec)'].max()-self.row.df['TimeStamp (sec)'].min()
        totaltime=totaltime+self.row.df.ix[0,' ElapsedTime (sec)']
        assert_equals(totaltime, 1309.9480600738525)
        assert_equals(totaldist, 5000)
        assert_equals(
            self.row.df[' Cadence (stokes/min)'].mean(),
            20.339325842696628
        )


class TestTCXExport:
    def testtcxexport(self):
        csvfile='testdata/Speedcoach2example.csv'
        assert_equals(rowingdata.get_file_type(csvfile),'speedcoach2')
        r=rowingdata.SpeedCoach2Parser(csvfile=csvfile)
        summarystring = r.summary()
        row=rowingdata.rowingdata(df=r.df)
        assert_equals(row.number_of_rows,97)
        tcxfile = 'testdata/testtcx.tcx'
        row.exporttotcx(tcxfile)
        assert_equals(rowingdata.get_file_type(tcxfile),'tcx')
        r2 = rowingdata.TCXParser(tcxfile)
        row=rowingdata.rowingdata(df=r.df)
        assert_equals(row.number_of_rows,97)
        
class TestErgData:
    def testergdata(self):
        csvfile='testdata/ergdata_example.csv'
        assert_equals(rowingdata.get_file_type(csvfile),'ergdata')
        r=rowingdata.ErgDataParser(csvfile=csvfile)
        row=rowingdata.rowingdata(df=r.df)
        assert_equals(row.number_of_rows,180)
        totaldist=row.df['cum_dist'].max()
        assert_equals(totaldist,1992)
        totaltime=row.df['TimeStamp (sec)'].max()-row.df['TimeStamp (sec)'].min()
        assert_equals(int(totaltime),520)
        checks = row.check_consistency()
        assert_equals(checks['velo_time_distance'],True)
        #        assert_equals(checks['velo_valid'],True)

class TestpainsledDesktopParser:
    def testpainsleddesktop(self):
        csvfile='testdata/painsled_desktop_example.csv'
        assert_equals(rowingdata.get_file_type(csvfile),'painsleddesktop')
        r=rowingdata.painsledDesktopParser(csvfile=csvfile)
        row=rowingdata.rowingdata(df=r.df)
        assert_equals(row.number_of_rows,638)
        totaldist=row.df['cum_dist'].max()
        assert_equals(totaldist,7097)
        assert_equals(row.rowdatetime,datetime.datetime(2016,3,29,17,41,27,93000,utc))
        totaltime=row.df['TimeStamp (sec)'].max()-row.df['TimeStamp (sec)'].min()
        assert_equals(int(totaltime),1802)
        checks = row.check_consistency()
        assert_equals(checks['velo_time_distance'],True)
        #        assert_equals(checks['velo_valid'],True)

class TestBoatCoachParser:
    def testboatcoach(self):
        csvfile='testdata/boatcoach.csv'
        assert_equals(rowingdata.get_file_type(csvfile),'boatcoach')
        r=rowingdata.BoatCoachParser(csvfile=csvfile)
        row=rowingdata.rowingdata(df=r.df)
        assert_equals(row.number_of_rows,119)
        totaldist=row.df['cum_dist'].max()
        assert_equals(totaldist,499)
        assert_equals(row.rowdatetime,datetime.datetime(2016,11,28,8,37,2,0,utc))
        totaltime=row.df['TimeStamp (sec)'].max()-row.df['TimeStamp (sec)'].min()
        assert_equals(int(totaltime),118)
        checks = row.check_consistency()
        assert_equals(checks['velo_time_distance'],True)
        #        assert_equals(checks['velo_valid'],True)
        
class TestspeedcoachParser:
    def testspeedcoach(self):
        csvfile='testdata/speedcoachexample.csv'
        assert_equals(rowingdata.get_file_type(csvfile),'speedcoach')
        r=rowingdata.speedcoachParser(csvfile=csvfile)
        row=rowingdata.rowingdata(df=r.df)
        assert_equals(row.number_of_rows,476)
        totaldist=row.df['cum_dist'].max()
        assert_equals(totaldist,9520)
        totaltime=row.df['TimeStamp (sec)'].max()-row.df['TimeStamp (sec)'].min()
        assert_equals(totaltime,3176.5)
        checks = row.check_consistency()
        assert_equals(checks['velo_time_distance'],True)
        #        assert_equals(checks['velo_valid'],True)
        
class TestErgStickParser:
    def testergstick(self):
        csvfile='testdata/ergstick.csv'
        assert_equals(rowingdata.get_file_type(csvfile),'ergstick')
        r=rowingdata.ErgStickParser(csvfile=csvfile)
        row=rowingdata.rowingdata(df=r.df)
        assert_equals(row.number_of_rows,2400)
        totaldist=row.df['cum_dist'].max()
        assert_equals(int(totaldist),4959)
        totaltime=row.df['TimeStamp (sec)'].max()-row.df['TimeStamp (sec)'].min()
        assert_equals(int(totaltime),1201)
        checks = row.check_consistency()
        assert_equals(checks['velo_time_distance'],True)
        #        assert_equals(checks['velo_valid'],True)
        
class TestMysteryParser:
    def testmystery(self):
        csvfile='testdata/mystery.csv'
        assert_equals(rowingdata.get_file_type(csvfile),'mystery')
        r=rowingdata.MysteryParser(csvfile=csvfile)
        row=rowingdata.rowingdata(df=r.df)
        assert_equals(row.number_of_rows,4550)
        totaldist=row.df['cum_dist'].max()
        assert_equals(totaldist,7478)
        totaltime=row.df['TimeStamp (sec)'].max()-row.df['TimeStamp (sec)'].min()
        assert_equals(int(totaltime),2325)
        checks = row.check_consistency()
        assert_equals(checks['velo_time_distance'],True)
        #        assert_equals(checks['velo_valid'],True)
        
class TestRowProParser:
    def testrowpro(self):
        csvfile='testdata/RP_testdata.csv'
        assert_equals(rowingdata.get_file_type(csvfile),'rp')
        r=rowingdata.RowProParser(csvfile=csvfile)
        row=rowingdata.rowingdata(df=r.df)
        assert_equals(row.number_of_rows,988)
        totaldist=row.df['cum_dist'].max()
        assert_equals(totaldist,10000)
        assert_equals(row.rowdatetime,datetime.datetime(2016,3,15,19,49,48,863000,utc))
        totaltime=row.df['TimeStamp (sec)'].max()-row.df['TimeStamp (sec)'].min()
        assert_equals(int(10*totaltime),22653)
        checks = row.check_consistency()
        assert_equals(checks['velo_time_distance'],True)
        #         assert_equals(checks['velo_valid'],True)



        
class TestAddPowerZones:
    row = rowingdata.rowingdata(csvfile='testdata/testdata.csv')

    def test_bearing(self):
        r = rowingdata.getrower()
        rg = rowingdata.getrigging()
        row = rowingdata.SpeedCoach2Parser('testdata/SpeedCoach2v2.12.csv')
        row = rowingdata.rowingdata(df=row.df)
        result = rowingdata.addpowerzones(row.df, 225, [23,53,76,87,91])


        
class TestRowProParserIntervals:
    def testrowprointervals(self):
        csvfile='testdata/RP_interval.csv'
        assert_equals(rowingdata.get_file_type(csvfile),'rp')
        r=rowingdata.RowProParser(csvfile=csvfile)
        row=rowingdata.rowingdata(df=r.df)
        assert_equals(row.number_of_rows,1674)
        totaldist=row.df['cum_dist'].max()
        assert_equals(int(totaldist),19026)
        assert_equals(row.rowdatetime,datetime.datetime(2016,1,12,19,23,10,878000,utc))
        totaltime=row.df['TimeStamp (sec)'].max()-row.df['TimeStamp (sec)'].min()
        assert_equals(int(totaltime),4800)
        checks = row.check_consistency()
        assert_equals(checks['velo_time_distance'],True)
        #        assert_equals(checks['velo_valid'],True)
        
class TestSpeedCoach2Parser:
    def testspeedcoach2(self):
        csvfile='testdata/Speedcoach2example.csv'
        assert_equals(rowingdata.get_file_type(csvfile),'speedcoach2')
        r=rowingdata.SpeedCoach2Parser(csvfile=csvfile)
        row=rowingdata.rowingdata(df=r.df)
        assert_equals(row.number_of_rows,97)
        totaldist=row.df['cum_dist'].max()
        assert_equals(int(10*totaldist),7516)
        assert_equals(row.rowdatetime,datetime.datetime(2016,7,28,11,35,1,500000,utc))
        totaltime=row.df['TimeStamp (sec)'].max()-row.df['TimeStamp (sec)'].min()
        assert_equals(int(totaltime),170)
        checks = row.check_consistency()
        assert_equals(checks['velo_time_distance'],True)
        #        assert_equals(checks['velo_valid'],True)
        
class TestSpeedCoach2_v127Parser:
    def testspeedcoach2v127(self):
        csvfile='testdata/SpeedCoach2Linkv1.27.csv'
        assert_equals(rowingdata.get_file_type(csvfile),'speedcoach2')
        r=rowingdata.SpeedCoach2Parser(csvfile=csvfile)
        row=rowingdata.rowingdata(df=r.df)
        assert_equals(row.number_of_rows,1408)
        totaldist=row.df['cum_dist'].max()
        assert_equals(totaldist,14344.5)
        assert_equals(row.rowdatetime,datetime.datetime(2016,11,5,9,2,3,200000,utc))
        totaltime=row.df['TimeStamp (sec)'].max()-row.df['TimeStamp (sec)'].min()
        assert_equals(int(10*totaltime),45018)
        checks = row.check_consistency()
        assert_equals(checks['velo_time_distance'],True)
        #        assert_equals(checks['velo_valid'],True)

class TestCurveData:
    def testcurvedata(self):
        file = 'testdata/rp3_curve.csv'
        r = rowingdata.RowPerfectParser(file)
        row = rowingdata.rowingdata(df=r.df)
        df = row.get_instroke_data('curve_data')
        assert_equals(len(df),468)
        cs = row.get_instroke_columns()
        assert_equals(len(cs),1)
        assert_equals(cs[0],'curve_data')

        file = 'testdata/quiske_per_stroke_left.csv'
        r = rowingdata.QuiskeParser(file)
        row = rowingdata.rowingdata(df=r.df)
        df = row.get_instroke_data('oar angle velocity curve')
        assert_equals(len(df),25)
        cs = row.get_instroke_columns()
        assert_equals(len(cs),2)
        assert_equals(cs[0],'boat accelerator curve')

        
class TestFITParser:
    def testfit(self):
        fitfile='testdata/3x250m.fit'
        assert_equals(rowingdata.get_file_type(fitfile),'fit')
        r=rowingdata.FITParser(fitfile)
        row=rowingdata.rowingdata(df=r.df)
        assert_equals(row.number_of_rows,94)
        totaldist=row.df['cum_dist'].max()
        assert_equals(int(totaldist),750)
        assert_equals(row.rowdatetime,datetime.datetime(2016,7,28,9,35,29,0,utc))
        totaltime=row.df['TimeStamp (sec)'].max()-row.df['TimeStamp (sec)'].min()
        assert_equals(int(10*totaltime),4870)
        checks = row.check_consistency()
        assert_equals(checks['velo_time_distance'],False)
        #assert_equals(checks['velo_valid'],True)
        
    def testfitsummary(self):
        fitfile='testdata/3x250m.fit'
        r = rowingdata.FitSummaryData(fitfile)
        r.setsummary()
        assert_equals(r.summarytext[72:75],'250')

class TestSequence(unittest.TestCase):
    list=pd.read_csv('testdata/testdatasummary.csv')
    lijst=[]
    for i in list.index:
        filename=list.ix[i,'filename']
        expected=list.ix[i,1:]
        lijst.append(
            (filename,filename,expected)
            )

    @parameterized.expand(lijst)
    
    def test_check(self, name, filename, expected):
        f2='testdata/'+filename
        res=rowingdata.checkdatafiles.checkfile(f2)
        filetype = rowingdata.get_file_type(f2)
        if filetype  not in ['unknown','c2log']:
            assert_not_equal(res,0)
        if res != 0:
            for key,value in six.iteritems(res):
                if key != 'summary':
                    if expected[key] != 0:
                        assert_equals(value,expected[key])
                elif key == 'summary':
                    assert_not_equal(value,'')


                      
