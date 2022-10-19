# -*- coding: utf-8 -*-
########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### SVN repository information ###################
'''
*Module G2pwd_BrukerRAW: Bruker v.1-v.3 .raw data*
---------------------------------------------------

Routine to read in powder data from a Bruker versions 1-3 .raw file

'''

from __future__ import division, print_function
import os
import os.path as ospath
import struct as st
import numpy as np
import GSASIIobj as G2obj
import GSASIIctrlGUI as G2G
import GSASIIpath
GSASIIpath.SetVersionNumber("$Revision$")
class raw_ReaderClass(G2obj.ImportPowderData):
    'Routines to import powder data from a binary Bruker .RAW file'
    def __init__(self):
        super(self.__class__,self).__init__( # fancy way to self-reference
            extensionlist=('.RAW',),
            strictExtension=False,
            formatName = 'Bruker RAW',
            longFormatName = 'Bruker .RAW powder data file'
            )
        self.scriptable = True

    # Validate the contents -- make sure we only have valid lines
    def Read(self,fp,nbytes):
        data = fp.read(nbytes)
        if 'bytes' in str(type(data)):
            data = data.decode('latin-1')
        return data
    
    def ContentsValidator(self, filename):
        'Look through the file for expected types of lines in a valid Bruker RAW file'
        fp = open(filename,'rb')
        head = self.Read(fp,7)
        if 'bytes' in str(type(head)):
            head = head.decode('latin-1')
        if head[:4] == 'RAW ':
            self.formatName = 'Bruker RAW ver. 1'
        elif head[:4] == 'RAW2':
            self.formatName = 'Bruker RAW ver. 2'
        elif head == 'RAW1.01':
            self.formatName = 'Bruker RAW ver. 3'
        elif head == 'RAW4.00':
            self.formatName = 'Bruker RAW ver. 4'
            self.errors += "Sorry, this is a Version 4 Bruker file. "
            self.errors += "We need documentation for it so that it can be implemented in GSAS-II. "
            self.errors += "Use PowDLL (http://users.uoi.gr/nkourkou/powdll/) to convert it to ASCII xy."
            print(self.errors)
            fp.close()
            return False
        else:
            self.errors = 'Unexpected information in header: '
            if all([ord(c) < 128 and ord(c) != 0 for c in str(head)]): # show only if ASCII
                self.errors += '  '+str(head)
            else: 
                self.errors += '  (binary)'
            fp.close()
            return False
        fp.close()
        return True
            
    def Reader(self,filename, ParentFrame=None, **kwarg):
        'Read a Bruker RAW file'
        self.comments = []
        self.powderentry[0] = filename
        fp = open(filename,'rb')
        if 'ver. 1' in self.formatName:
            raise Exception    #for now
        elif 'ver. 2' in self.formatName:
            fp.seek(4)
            nBlock = int(st.unpack('<i',fp.read(4))[0])
            fp.seek(168)
            self.comments.append('Date/Time='+self.Read(fp,20))
            self.comments.append('Anode='+self.Read(fp,2))
            self.comments.append('Ka1=%.5f'%(st.unpack('<f',fp.read(4))[0]))
            self.comments.append('Ka2=%.5f'%(st.unpack('<f',fp.read(4))[0]))
            self.comments.append('Ka2/Ka1=%.5f'%(st.unpack('<f',fp.read(4))[0]))
            fp.seek(206)
            self.comments.append('Kb=%.5f'%(st.unpack('<f',fp.read(4))[0]))
            pos = 256
            fp.seek(pos)
            blockNum = kwarg.get('blocknum',0)
            self.idstring = ospath.basename(filename) + ' Scan '+str(blockNum)
            if blockNum <= nBlock:
                for iBlock in range(blockNum):
                    headLen = int(st.unpack('<H',fp.read(2))[0])
                    nSteps = int(st.unpack('<H',fp.read(2))[0])
                    if iBlock+1 == blockNum:
                        fp.seek(pos+12)
                        step = st.unpack('<f',fp.read(4))[0]
                        start2Th = st.unpack('<f',fp.read(4))[0]
                        pos += headLen      #position at start of data block
                        fp.seek(pos)                                    
                        x = np.array([start2Th+i*step for i in range(nSteps)])
                        y = np.array([max(1.,st.unpack('<f',fp.read(4))[0]) for i in range(nSteps)])
                        y = np.where(y<0.,y,1.)
                        w = 1./y
                        self.powderdata = [x,y,w,np.zeros(nSteps),np.zeros(nSteps),np.zeros(nSteps)]
                        break
                    pos += headLen+4*nSteps
                    fp.seek(pos)
                if blockNum == nBlock:
                    self.repeat = False                                   
                else:
                    self.repeat = True
            fp.close()
        elif 'ver. 3' in self.formatName:
            fp.seek(12)
            nBlock = int(st.unpack('<i',fp.read(4))[0])
            self.comments.append('Date='+self.Read(fp,10))
            self.comments.append('Time='+self.Read(fp,10))
            fp.seek(326)
            self.comments.append('Sample='+self.Read(fp,60))
            fp.seek(564)
            radius = st.unpack('<f',fp.read(4))[0]
            self.comments.append('Gonio. radius=%.2f'%(radius))
            self.Sample['Gonio. radius'] = radius
            fp.seek(608)
            self.comments.append('Anode='+self.Read(fp,4))
            fp.seek(616)
            self.comments.append('Ka mean=%.5f'%(st.unpack('<d',fp.read(8))[0]))
            self.comments.append('Ka1=%.5f'%(st.unpack('<d',fp.read(8))[0]))
            self.comments.append('Ka2=%.5f'%(st.unpack('<d',fp.read(8))[0]))
            self.comments.append('Kb=%.5f'%(st.unpack('<d',fp.read(8))[0]))
            self.comments.append('Ka2/Ka1=%.5f'%(st.unpack('<d',fp.read(8))[0]))
            pos = 712
            fp.seek(pos)      #position at 1st block header
            blockNum = kwarg.get('blocknum',0)
            self.idstring = ospath.basename(filename) + ' Scan '+str(blockNum)
            if blockNum <= nBlock:
                for iBlock in range(blockNum):
                    headLen = int(st.unpack('<i',fp.read(4))[0])
                    nSteps = int(st.unpack('<i',fp.read(4))[0])
                    if not nSteps: break
                    if nBlock > 1:
                        fp.seek(pos+256)
                        headLen += st.unpack('<i',fp.read(4))[0]
                    else:
                        headLen += 40
                    if iBlock+1 == blockNum:
                        fp.seek(pos+8)
                        st.unpack('<d',fp.read(8))[0]
                        start2Th = st.unpack('<d',fp.read(8))[0]
                        fp.seek(pos+212)
                        temp = st.unpack('<f',fp.read(4))[0]
                        if temp > 0.:
                            self.Sample['Temperature'] = temp                                                        
                        fp.seek(pos+176)
                        step = st.unpack('<d',fp.read(8))[0]
                        pos += headLen      #position at start of data block
                        fp.seek(pos)
                        x = np.array([start2Th+i*step for i in range(nSteps)])
                        try:
                            y = np.array([max(1.,st.unpack('<f',fp.read(4))[0]) for i in range(nSteps)])
                        except: #this is absurd
                            fp.seek(pos-40)
                            y = np.array([max(1.,st.unpack('<f',fp.read(4))[0]) for i in range(nSteps)])
                        w = 1./y
                        self.powderdata = [x,y,w,np.zeros(nSteps),np.zeros(nSteps),np.zeros(nSteps)]
                        break
                    pos += headLen+4*nSteps
                    fp.seek(pos)
                if blockNum == nBlock:
                    self.repeat = False
                else:
                    self.repeat = True
            fp.close()
            
        elif 'ver. 4' in self.formatName:   #does not work - format still elusive
            fp.seek(12)   #ok
            self.comments.append('Date='+self.Read(fp,10))
            self.comments.append('Time='+self.Read(fp,10))
            fp.seek(144)
            self.comments.append('Sample='+self.Read(fp,60))
            fp.seek(564)  # where is it?
            radius = st.unpack('<f',fp.read(4))[0]
            self.comments.append('Gonio. radius=%.2f'%(radius))
            self.Sample['Gonio. radius'] = radius
            fp.seek(516)  #ok
            self.comments.append('Anode='+self.Read(fp,4))
            fp.seek(472)  #ok
            self.comments.append('Ka mean=%.5f'%(st.unpack('<d',fp.read(8))[0]))
            self.comments.append('Ka1=%.5f'%(st.unpack('<d',fp.read(8))[0]))
            self.comments.append('Ka2=%.5f'%(st.unpack('<d',fp.read(8))[0]))
            self.comments.append('Kb=%.5f'%(st.unpack('<d',fp.read(8))[0]))
            self.comments.append('Ka2/Ka1=%.5f'%(st.unpack('<d',fp.read(8))[0]))
            fp.seek(pos)  #deliberate fail here - pos not known from file contents
            self.idstring = ospath.basename(filename) + ' Scan '+str(1)
            nSteps = int(st.unpack('<i',fp.read(4))[0])
            st.unpack('<d',fp.read(8))[0]
            start2Th = st.unpack('<d',fp.read(8))[0]
            fp.seek(pos+176)
            step = st.unpack('<d',fp.read(8))[0]
            pos += headLen      #position at start of data block
            fp.seek(pos)                                    
            x = np.array([start2Th+i*step for i in range(nSteps)])
            y = np.array([max(1.,st.unpack('<f',fp.read(4))[0]) for i in range(nSteps)])
            w = 1./y
            self.powderdata = [x,y,w,np.zeros(nSteps),np.zeros(nSteps),np.zeros(nSteps)]
            fp.close()
        else:
            return False
            
        return True

class brml_ReaderClass(G2obj.ImportPowderData):
    'Routines to import powder data from a zip Bruker .brml file'
    def __init__(self):
        super(self.__class__,self).__init__( # fancy way to self-reference
            extensionlist=('.brml',),
            strictExtension=False,
            formatName = 'Bruker brml',
            longFormatName = 'Bruker .brml powder data file'
            )
        self.scriptable = True
        self.data = None

    def ContentsValidator(self, filename):
        try:
            import xmltodict as xml
        except:
            print('Attempting to conda install xmltodict - please wait')
            res = GSASIIpath.condaInstall('xmltodict')
            if res:
                msg = 'Installation of the xmltodict package failed with error:\n' + str(res)
                G2G.G2MessageBox(self,msg,'Install xmltodict Error')
                return False
        import zipfile as ZF
        
        with ZF.ZipFile(filename, 'r') as zipObj:
            zipObj.extract('Experiment0/RawData0.xml')
        with open('Experiment0/RawData0.xml') as fd:
            self.data = dict(xml.parse(fd.read()))
            self.formatName = 'Bruker .brml file'
        os.remove('Experiment0/RawData0.xml')
        os.rmdir('Experiment0')
        self.idstring = ospath.basename(filename) + ' Bank 1'
        self.powderentry[0] = filename
        self.comments = []
        return True
            
    def Reader(self,filename, ParentFrame=None, **kwarg):
        'Read a Bruker brml file'
        print(filename)
        nSteps = int(self.data['RawData']['DataRoutes']['DataRoute'][1]['ScanInformation']['MeasurementPoints'])
        
        x = np.zeros(nSteps, dtype=float)
        y = np.zeros(nSteps, dtype=float)
        w = np.zeros(nSteps, dtype=float) 
        
        effTime = float(self.data['RawData']['DataRoutes']['DataRoute'][1]['ScanInformation']['TimePerStepEffective'])
        
        # Extract 2-theta angle and counts from the XML document
        i=0
        while i < nSteps :
            entry = self.data['RawData']['DataRoutes']['DataRoute'][1]['Datum'][i].split(',')
            x[i] = float(entry[2])
            y[i] = float(entry[4])*float(entry[0])/effTime
            i = i + 1
            
        w = np.where(y>0,1/y,0.)
        self.powderdata = [x,y,w,np.zeros(nSteps),np.zeros(nSteps),np.zeros(nSteps)]
        
        
            
        return True
