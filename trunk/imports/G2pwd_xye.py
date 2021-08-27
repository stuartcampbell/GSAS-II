# -*- coding: utf-8 -*-
########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### SVN repository information ###################
'''
*Module G2pwd_xye: Topas .xye data*
------------------------------------

Routine to read in powder data from a Topas-compatible .xye file

'''

from __future__ import division, print_function
import os.path as ospath
import numpy as np
import GSASIIobj as G2obj
import GSASIIpath

asind = lambda x: 180.*np.arcsin(x)/np.pi

GSASIIpath.SetVersionNumber("$Revision$")
class xye_ReaderClass(G2obj.ImportPowderData):
    'Routines to import powder data from a .xye/.chi file'
    def __init__(self):
        super(self.__class__,self).__init__( # fancy way to self-reference
            extensionlist=('.xye','.qye','.chi','.qchi',),
            strictExtension=False,
            formatName = 'Topas xye or 2th Fit2D chi',
            longFormatName = 'Topas .xye/.qye or 2th Fit2D .chi/.qchi powder data file'
            )
        self.scriptable = True

    # Validate the contents -- make sure we only have valid lines
    def ContentsValidator(self, filename):
        'Look through the file for expected types of lines in a valid Topas file'
        gotCcomment = False
        begin = True
        self.GSAS = False
        self.Chi = False
        Qchi = False
        self.Wave = None
        fp = open(filename,'r')
        if '.chi' in filename:
            self.Chi = True
        if '.qchi' in filename:
            Qchi = True
        if2theta = False
        ifQ = False
        for i,S in enumerate(fp):
            if not S:
                break
            if i > 1000: break
            if begin:
                if self.Chi or Qchi:
                    if i < 4:
                        if  '2-theta' in S.lower():
                            if2theta = True
                        elif  'q ' in S.lower():
                            ifQ = True
                            wave = ''
                            wave = S.split()[1:]
                            if wave: 
                                try:
                                    self.Wave = float(wave[0])
                                except:
                                    pass
                            if not self.Wave:
                                self.errors = 'No wavelength in a Q chi file'
                                fp.close()
                                return False
                        continue
                    else:
                        begin = False
                else:
                    if2theta = True
                    if  i == 0 and 'xydata' in S.lower():
                        continue   # fullprof header
                    if gotCcomment and S.find('*/') > -1:
                        begin = False
                        continue
                    if S.strip().startswith('/*'):
                        gotCcomment = True
                        continue   
                    if S[0] in ["'",'#','!']:
                        if 'q' in S and not self.Wave:
                            wave = S.split()[-1]
                            if wave: 
                                try:
                                    self.Wave = float(wave[0])
                                except:
                                    self.Wave = 0.965   #special for POWGEN "pink" CW data
                        continue       #ignore comments, if any
                    elif S.startswith('TITLE'):
                        continue
                    else:
                        begin = False
                # valid line to read? 
            #vals = S.split()
            if ifQ:
                pass
            elif not if2theta:
                self.errors = 'Not a 2-theta chi file'
                fp.close()
                return False
            vals = S.replace(',',' ').replace(';',' ').split()
            if len(vals) == 2 or len(vals) == 3:
                continue
            else:
                self.errors = 'Unexpected information in line: '+str(i+1)
                if all([ord(c) < 128 and ord(c) != 0 for c in str(S)]): # show only if ASCII
                    self.errors += '  '+str(S)
                else: 
                    self.errors += '  (binary)'
                fp.close()
                return False
        fp.close()
        return True # no errors encountered

    def Reader(self,filename, ParentFrame=None, **unused):
        'Read a Topas file'
        x = []
        y = []
        w = []
        gotCcomment = False
        begin = True
        fp = open(filename,'r')
        for i,S in enumerate(fp):
            self.errors = 'Error reading line: '+str(i+1)
            # or a block of comments delimited by /* and */
            # or (GSAS style) each line can begin with '#'
            # or WinPLOTR style, a '!'
            if begin:
                if self.Chi:
                    if i < 4:
                        continue
                    else:
                        begin = False
                else:        
                    if gotCcomment and S.find('*/') > -1:
                        self.comments.append(S[:-1])
                        begin = False
                        continue
                    if S.strip().startswith('/*'):
                        self.comments.append(S[:-1])
                        gotCcomment = True
                        continue   
                    if S[0] in ["'",'#','!']:
                        self.comments.append(S[:-1])
                        continue       #ignore comments, if any
                    elif  i == 0 and 'xydata' in S.lower():
                        continue   # fullprof header
                    elif S.startswith('TITLE'):
                        self.comments = [S]
                        continue
                    else:
                        begin = False
            # valid line to read
            #vals = S.split()
            vals = S.replace(',',' ').replace(';',' ').split()
            if len(vals) < 2:
                print ('Line '+str(i+1)+' cannot be read:\n\t'+S)
                continue
            try:
                if self.Wave:
                    try:
                        val = min(0.995,self.Wave/(4.*np.pi/float(vals[0])))  #set max at 168deg
                        x.append(2.0*asind(val))
                    except:
                        msg = 'Error converting '+str(vals[0]
                        ) + 'with wavelength ' + str(self.Wave) 
                        break
                else:
                    x.append(float(vals[0]))
                f = float(vals[1])
                if f <= 0.0:
                    y.append(0.0)
                    w.append(0.0)
                elif len(vals) == 3:
                    y.append(float(vals[1]))
                    w.append(1.0/float(vals[2])**2)
                else:
                    y.append(float(vals[1]))
                    w.append(1.0/float(vals[1]))
            except ValueError:
                msg = 'Error parsing number in line '+str(i+1)
                if GSASIIpath.GetConfigValue('debug'):
                    print (msg)
                    print (S.strip())
                break
            except:
                msg = 'Error in line '+str(i+1)
                if GSASIIpath.GetConfigValue('debug'):
                    print (msg)
                    print (S.strip())
                break
        N = len(x)
        self.powderdata = [
            np.array(x), # x-axis values
            np.array(y), # powder pattern intensities
            np.array(w), # 1/sig(intensity)^2 values (weights)
            np.zeros(N), # calc. intensities (zero)
            np.zeros(N), # calc. background (zero)
            np.zeros(N), # obs-calc profiles
            ]
        self.powderentry[0] = filename
        #self.powderentry[1] = pos # bank offset (N/A here)
        #self.powderentry[2] = 1 # xye file only has one bank
        self.idstring = ospath.basename(filename)
        # scan comments for temperature
        Temperature = 300
        for S in self.comments:
            if 'temp' in S.lower().split('=')[0]:
                try:
                    Temperature = float(S.split('=')[1])
                except:
                    pass
        self.Sample['Temperature'] = Temperature
        fp.close()
        return True
