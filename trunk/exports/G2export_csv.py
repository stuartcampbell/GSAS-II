#!/usr/bin/env python
# -*- coding: utf-8 -*-
########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### SVN repository information ###################
'''
*Module G2export_csv: Spreadsheet export*
-------------------------------------------

Code to create .csv (comma-separated variable) files for
GSAS-II data export to a spreadsheet program, etc.

'''
from __future__ import division, print_function
import os.path
import numpy as np
import GSASIIpath
GSASIIpath.SetVersionNumber("$Revision$")
import GSASIIIO as G2IO
import GSASIIpy3 as G2py3
import GSASIIobj as G2obj
import GSASIImath as G2mth
import GSASIIpwd as G2pwd
import GSASIIlattice as G2lat

def WriteList(obj,headerItems):
    '''Write a CSV header

    :param object obj: Exporter object
    :param list headerItems: items to write as a header
    '''
    line = ''
    for lbl in headerItems:
        if line: line += ','
        line += '"'+lbl+'"'
    obj.Write(line)

class ExportPhaseCSV(G2IO.ExportBaseclass):
    '''Used to create a csv file for a phase

    :param wx.Frame G2frame: reference to main GSAS-II frame
    '''
    def __init__(self,G2frame):
        super(self.__class__,self).__init__( # fancy way to say <parentclass>.__init__
            G2frame=G2frame,
            formatName = 'CSV file',
            extension='.csv',
            longFormatName = 'Export phase as comma-separated (csv) file'
            )
        self.exporttype = ['phase']
        self.multiple = True # allow multiple phases to be selected

    def Writer(self,hist,phasenam,mode='w'):
        self.OpenFile(mode=mode)
        # test for aniso atoms
        aniso = False
        AtomsList = self.GetAtoms(phasenam)
        for lbl,typ,mult,xyz,td in AtomsList:
            if len(td) != 1:
                aniso = True
                break
        if mode == 'w':
            lbllist = ['hist','phase','a','b','c','alpha','beta','gamma','volume']
            lbllist += ["atm label","elem","mult","x","y","z","frac","Uiso"]
            if aniso: lbllist += ['U11','U22','U33','U12','U13','U23']
            WriteList(self,lbllist)
            
        cellList,cellSig = self.GetCell(phasenam)
        line = '"' + str(hist)+ '","' + str(phasenam) + '"'
        for defsig,val in zip(
            3*[-0.00001] + 3*[-0.001] + [-0.01], # sets sig. figs.
            cellList
            ):
            txt = G2mth.ValEsd(val,defsig)
            if line: line += ','
            line += txt
        self.Write(line)

        # get atoms and print separated by commas
        AtomsList = self.GetAtoms(phasenam)
        for lbl,typ,mult,xyz,td in AtomsList:
            line = ",,,,,,,,,"
            line += '"' + lbl + '","' + typ + '",' + str(mult) + ','
            for val,sig in xyz:
                line += G2mth.ValEsd(val,-abs(sig))
                line += ","
            if len(td) == 1:
                line += G2mth.ValEsd(td[0][0],-abs(td[0][1]))
            else:
                line += ","
                for val,sig in td:
                    line += G2mth.ValEsd(val,-abs(sig))
                    line += ","
            self.Write(line)

        if mode == 'w':
            print('Phase '+phasenam+' written to file '+self.fullpath)
        self.CloseFile()
    
    def Exporter(self,event=None):
        '''Export a phase as a csv file
        '''
        # the export process starts here
        self.InitExport(event)
        # load all of the tree into a set of dicts
        self.loadTree()
        # create a dict with refined values and their uncertainties
        self.loadParmDict()
        if self.ExportSelect(): return # set export parameters; get file name
        self.OpenFile()
        # if more than one phase is selected, put them into a single file
        for phasenam in self.phasenam:
            phasedict = self.Phases[phasenam] # pointer to current phase info            
            i = self.Phases[phasenam]['pId']
            self.Write('"'+"Phase "+str(phasenam)+" from "+str(self.G2frame.GSASprojectfile)+'"')
            self.Write('\n"Space group:","'+str(phasedict['General']['SGData']['SpGrp'].strip())+'"')
            # get cell parameters & print them
            cellList,cellSig = self.GetCell(phasenam)
            WriteList(self,['a','b','c','alpha','beta','gamma','volume'])

            line = ''
            for defsig,val in zip(
                3*[-0.00001] + 3*[-0.001] + [-0.01], # sign values to use when no sigma
                cellList
                ):
                txt = G2mth.ValEsd(val,defsig)
                if line: line += ','
                line += txt
            self.Write(line)
                
            # get atoms and print separated by commas
            AtomsList = self.GetAtoms(phasenam)
            # check for aniso atoms
            aniso = False
            for lbl,typ,mult,xyz,td in AtomsList:
                if len(td) != 1: aniso = True               
            lbllist = ["label","elem","mult","x","y","z","frac","Uiso"]
            if aniso: lbllist += ['U11','U22','U33','U12','U13','U23']
            WriteList(self,lbllist)
                
            for lbl,typ,mult,xyz,td in AtomsList:
                line = '"' + lbl + '","' + typ + '",' + str(mult) + ','
                for val,sig in xyz:
                    line += G2mth.ValEsd(val,-abs(sig))
                    line += ","
                if len(td) == 1:
                    line += G2mth.ValEsd(td[0][0],-abs(td[0][1]))
                else:
                    line += ","
                    for val,sig in td:
                        line += G2mth.ValEsd(val,-abs(sig))
                        line += ","
                self.Write(line)
            print('Phase '+phasenam+' written to file '+self.fullpath)
        self.CloseFile()

class ExportPowderCSV(G2IO.ExportBaseclass):
    '''Used to create a csv file for a powder data set

    :param wx.Frame G2frame: reference to main GSAS-II frame
    '''
    def __init__(self,G2frame):
        super(self.__class__,self).__init__( # fancy way to say <parentclass>.__init__
            G2frame=G2frame,
            formatName = 'CSV file',
            extension='.csv',
            longFormatName = 'Export powder data as comma-separated (csv) file'
            )
        self.exporttype = ['powder']
        #self.multiple = False # only allow one histogram to be selected
        self.multiple = True

    def Writer(self,TreeName,filename=None):
        #print filename
        self.OpenFile(filename)
        histblk = self.Histograms[TreeName]
        Parms = self.Histograms[TreeName]['Instrument Parameters'][0]
        for parm in Parms:
            if parm in ['Type','Source',]:
                line = '"Instparm: %s","%s"'%(parm,Parms[parm][0])
            elif parm in ['Lam','Zero',]:
                line = '"Instparm: %s",%10.6f'%(parm,Parms[parm][1])
            else:
                line = '"Instparm: %s",%10.2f'%(parm,Parms[parm][1])
            self.Write(line)
        WriteList(self,("x","y_obs","weight","y_calc","y_bkg","Q"))
        digitList = 2*((13,3),) + ((13,5),) + 3*((13,3),)
        for vallist in zip(histblk['Data'][0],
                       histblk['Data'][1],
                       histblk['Data'][2],
                       histblk['Data'][3],
                       histblk['Data'][4],
                       #histblk['Data'][5],
                       2*np.pi/G2lat.Pos2dsp(Parms,histblk['Data'][0])
                       ):
            line = ""
            for val,digits in zip(vallist,digitList):
                if line: line += ','
                line += G2py3.FormatValue(val,digits)
            self.Write(line)
        self.CloseFile()
        
    def Exporter(self,event=None):
        '''Export a set of powder data as a csv file
        '''
        # the export process starts here
        self.InitExport(event)
        # load all of the tree into a set of dicts
        self.loadTree()
        if self.ExportSelect( # set export parameters
            AskFile='single' # get a file name/directory to save in
            ): return
        filenamelist = []
        for hist in self.histnam:
            if len(self.histnam) == 1:
                name = self.filename
            else:    # multiple files: create a unique name from the histogram
                name = self.MakePWDRfilename(hist)
            fileroot = os.path.splitext(G2obj.MakeUniqueLabel(name,filenamelist))[0]
            # create the file
            self.filename = os.path.join(self.dirname,fileroot + self.extension)
            self.Writer(hist)
            print('Histogram '+hist+' written to file '+self.fullpath)

class ExportMultiPowderCSV(G2IO.ExportBaseclass):
    '''Used to create a csv file for a stack of powder data sets suitable for display 
    purposes only; no y-calc or weights are exported only x & y-obs
    :param wx.Frame G2frame: reference to main GSAS-II frame
    '''
    def __init__(self,G2frame):
        super(self.__class__,self).__init__( # fancy way to say <parentclass>.__init__
            G2frame=G2frame,
            formatName = 'stacked CSV file',
            extension='.csv',
            longFormatName = 'Export powder data sets as a (csv) file - x,y-o1,y-o2,... only'
            )
        self.exporttype = ['powder']
        #self.multiple = False # only allow one histogram to be selected
        self.multiple = True

    def Exporter(self,event=None):
        '''Export a set of powder data as a single csv file
        '''
        # the export process starts here
        self.InitExport(event)
        # load all of the tree into a set of dicts
        self.loadTree()
        if self.ExportSelect( # set export parameters
            AskFile='ask' # only one file is ever written
            ): return
        csvData = []
        headList = ["x",]
        digitList = []
        self.filename = os.path.join(self.dirname,os.path.splitext(self.filename)[0]
                                     + self.extension)
        for ihst,hist in enumerate(self.histnam):
            histblk = self.Histograms[hist]
            headList.append('y_obs_'+G2obj.StripUnicode(hist[5:].replace(' ','_')))
            if not ihst:
                digitList = [(13,3),]
                csvData.append(histblk['Data'][0])
            digitList += [(13,3),]
            csvData.append(histblk['Data'][1])
            print('Histogram '+hist+' added to file...')
        self.OpenFile()
        WriteList(self,headList)
        for vallist in np.array(csvData).T:
            line = ""
            for val,digits in zip(vallist,digitList):
                if line: line += ','
                line += G2py3.FormatValue(val,digits)
            self.Write(line)
        self.CloseFile()
        print('...file '+self.fullpath+' written')

class ExportPowderReflCSV(G2IO.ExportBaseclass):
    '''Used to create a csv file of reflections from a powder data set

    :param wx.Frame G2frame: reference to main GSAS-II frame
    '''
    def __init__(self,G2frame):
        super(self.__class__,self).__init__( # fancy way to say <parentclass>.__init__
            G2frame=G2frame,
            formatName = 'reflection list as CSV',
            extension='.csv',
            longFormatName = 'Export powder reflection list as a comma-separated (csv) file'
            )
        self.exporttype = ['powder']
        self.multiple = False # only allow one histogram to be selected

    def Exporter(self,event=None):
        '''Export a set of powder reflections as a csv file
        '''
        self.InitExport(event)
        # load all of the tree into a set of dicts
        self.loadTree()
        if self.ExportSelect(): return  # set export parameters, get file name
        self.OpenFile()
        hist = self.histnam[0] # there should only be one histogram, in any case take the 1st
        histblk = self.Histograms[hist]
        self.Write('"Histogram"')
        self.Write('"'+hist+'"')
        self.Write('')
        # table of phases
        self.Write('"Phase name","phase #"')
        for i,phasenam in enumerate(sorted(histblk['Reflection Lists'])):
            self.Write('"'+str(phasenam)+'",'+str(i))
        self.Write('')
        # note addition of a phase # flag at end (i)
        for i,phasenam in enumerate(sorted(histblk['Reflection Lists'])):
            phasDict = histblk['Reflection Lists'][phasenam]
            tname = {'T':'TOF','C':'2-theta'}[phasDict['Type'][2]]
            if phasDict.get('Super',False):
                WriteList(self,("h","k","l","m","d-sp",tname,"F_obs","F_calc","phase","mult","sig","gam","FWHM","Prfo","phase #"))
                if 'T' in phasDict['Type']:
                    fmt = "{:.0f},{:.0f},{:.0f},{:.0f},{:.5f},{:.3f},{:.3f},{:.3f},{:.2f},{:.0f},{:.3f},{:.3f},{:.3f},{:.4f},{:d}"
                else:
                    fmt = "{:.0f},{:.0f},{:.0f},{:.0f},{:.5f},{:.3f},{:.3f},{:.3f},{:.2f},{:.0f},{:.5f},{:.5f},{:.5f},{:.4f},{:d}"
                refList = phasDict['RefList']
                for refItem in refList:
                    if 'T' in phasDict['Type']:
                        h,k,l,m,mult,dsp,pos,sig,gam,Fobs,Fcalc,phase,Icorr,x,x,x,Prfo = refItem[:17]
                        FWHM = G2pwd.getgamFW(gam,sig)
                        self.Write(fmt.format(h,k,l,m,dsp,pos,Fobs,Fcalc,phase,mult,sig,gam,FWHM,i))
                    else:        #convert to deg        
                        h,k,l,m,mult,dsp,pos,sig,gam,Fobs,Fcalc,phase,Icorr,Prfo = refItem[:14]
                        s = np.sqrt(max(sig,0.0001))/100.   #var -> sig in deg
                        g = gam/100.    #-> deg
                        FWHM = G2pwd.getgamFW(g,s)
                        self.Write(fmt.format(h,k,l,m,dsp,pos,Fobs,Fcalc,phase,mult,s,g,FWHM,i))
            else:
                WriteList(self,("h","k","l","d-sp",tname,"F_obs","F_calc","phase","mult","sig","gam","FWHM","Prfo","phase #"))
                if 'T' in phasDict['Type']:
                    fmt = "{:.0f},{:.0f},{:.0f},{:.5f},{:.3f},{:.3f},{:.3f},{:.2f},{:.0f},{:.3f},{:.3f},{:.3f},{:.4f},{:d}"
                else:
                    fmt = "{:.0f},{:.0f},{:.0f},{:.5f},{:.3f},{:.3f},{:.3f},{:.2f},{:.0f},{:.5f},{:.5f},{:.5f},{:.4f},{:d}"
                refList = phasDict['RefList']
                for refItem in refList:
                    if 'T' in phasDict['Type']:
                        h,k,l,mult,dsp,pos,sig,gam,Fobs,Fcalc,phase,Icorr,x,x,x,Prfo = refItem[:16]
                        FWHM = G2pwd.getgamFW(gam,sig)
                        self.Write(fmt.format(h,k,l,dsp,pos,Fobs,Fcalc,phase,mult,sig,gam,FWHM,Prfo,i))
                    else:        #convert to deg        
                        h,k,l,mult,dsp,pos,sig,gam,Fobs,Fcalc,phase,Icorr,Prfo = refItem[:13]
                        g = gam/100.
                        s = np.sqrt(max(sig,0.0001))/100.
                        FWHM = G2pwd.getgamFW(g,s)
                        self.Write(fmt.format(h,k,l,dsp,pos,Fobs,Fcalc,phase,mult,s,g,FWHM,Prfo,i))
        self.CloseFile()
        print(hist+' reflections written to file '+self.fullpath)

class ExportSingleCSV(G2IO.ExportBaseclass):
    '''Used to create a csv file with single crystal reflection data

    :param wx.Frame G2frame: reference to main GSAS-II frame
    '''
    def __init__(self,G2frame):
        super(self.__class__,self).__init__( # fancy way to say <parentclass>.__init__
            G2frame=G2frame,
            formatName = 'CSV file',
            extension='.csv',
            longFormatName = 'Export reflection list as a comma-separated (csv) file'
            )
        self.exporttype = ['single']
        self.multiple = False # only allow one histogram to be selected

    def Exporter(self,event=None):
        '''Export a set of single crystal data as a csv file
        '''
        # the export process starts here
        self.InitExport(event)
        # load all of the tree into a set of dicts
        self.loadTree()
        if self.ExportSelect(): return  # set export parameters, get file name
        self.OpenFile()
        hist = self.histnam[0] # there should only be one histogram, in any case take the 1st
        histblk = self.Histograms[hist]
        for i,phasenam in enumerate(sorted(histblk['Reflection Lists'])):
            phasDict = histblk['Reflection Lists'][phasenam]
            tname = {'T':'TOF','C':'2-theta'}[phasDict['Type'][2]]
            if phasDict.get('Super',False):
                WriteList(self,("h","k","l","m",'d-sp',tname,"F_obs","F_calc","phase","mult","phase #"))
                fmt = "{:.0f},{:.0f},{:.0f},{:.0f},{:.5f},{:.3f},{:.3f},{:.3f},{:.2f},{:.0f},{:d}"
                refList = phasDict['RefList']
                for refItem in refList:
                    h,k,l,m,mult,dsp,pos,sig,gam,Fobs,Fcalc,phase,Icorr = refItem[:13]
                    self.Write(fmt.format(h,k,l,m,dsp,pos,Fobs,Fcalc,phase,mult,i))                
            else:
                WriteList(self,("h","k","l",'d-sp',tname,"F_obs","F_calc","phase","mult","phase #"))
                fmt = "{:.0f},{:.0f},{:.0f},{:.5f},{:.3f},{:.3f},{:.3f},{:.2f},{:.0f},{:d}"
                refList = phasDict['RefList']
                for refItem in refList:
                    h,k,l,mult,dsp,pos,sig,gam,Fobs,Fcalc,phase,Icorr = refItem[:12]
                    self.Write(fmt.format(h,k,l,dsp,pos,Fobs,Fcalc,phase,mult,i))
        self.CloseFile()
        print(hist+' written to file '+self.fullname)                        

class ExportStrainCSV(G2IO.ExportBaseclass):
    '''Used to create a csv file with single crystal reflection data

    :param wx.Frame G2frame: reference to main GSAS-II frame
    '''
    def __init__(self,G2frame):
        super(self.__class__,self).__init__( # fancy way to say <parentclass>.__init__
            G2frame=G2frame,
            formatName = 'Strain CSV file',
            extension='.csv',
            longFormatName = 'Export strain results as a comma-separated (csv) file'
            )
        self.exporttype = ['image']
        self.multiple = False # only allow one histogram to be selected

    def Exporter(self,event=None):
        '''Export a set of single crystal data as a csv file
        '''
        # the export process starts here
        self.InitExport(event)
        # load all of the tree into a set of dicts
        self.loadTree()
        if self.ExportSelect(): return  # set export parameters, get file name
        self.OpenFile()
        hist = self.histnam[0] # there should only be one histogram, in any case take the 1st
        histblk = self.Histograms[hist]
        StrSta = histblk['Stress/Strain']
        WriteList(self,("Dset","Dcalc","e11","sig(e11)","e12","sig(e12)","e22","sig(e22)"))
        fmt = 2*"{:.5f},"+6*"{:.0f},"
        fmt1 = "{:.5f}"
        fmt2 = "{:.2f},{:.5f},{:.5f}"
        for item in StrSta['d-zero']:
            Emat = item['Emat']
            Esig = item['Esig']
            self.Write(fmt.format(item['Dset'],item['Dcalc'],Emat[0],Esig[0],Emat[1],Esig[1],Emat[2],Esig[2]))
        for item in StrSta['d-zero']:
            WriteList(self,("Azm","dobs","dcalc","Dset="+fmt1.format(item['Dset'])))
            ring = np.vstack((item['ImtaObs'],item['ImtaCalc']))
            for dat in ring.T:
                self.Write(fmt2.format(dat[1],dat[0],dat[2]))            
        self.CloseFile()
        print(hist+' written to file '+self.fullpath)
