# -*- coding: utf-8 -*-
########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### SVN repository information ###################
'''
*Module G2sad_xye: read small angle data*
------------------------------------------------

Routines to read in small angle data from an .xye type file, with
two-theta or Q steps. 

'''

import sys
import os.path as ospath
import numpy as np
import GSASIIIO as G2IO
import GSASIIpath
GSASIIpath.SetVersionNumber("$Revision$")
npasind = lambda x: 180.*np.arcsin(x)/np.pi

class txt_XRayReaderClass(G2IO.ImportSmallAngleData):
    'Routines to import X-ray q SAXD data from a .xsad or .xdat file'
    def __init__(self):
        super(self.__class__,self).__init__( # fancy way to self-reference
            extensionlist=('.xsad','.xdat'),
            strictExtension=False,
            formatName = 'q (A-1) step X-ray QIE data',
            longFormatName = 'q (A-1) stepped X-ray text data file in Q,I,E order; E optional'
            )

    # Validate the contents -- make sure we only have valid lines
    def ContentsValidator(self, filepointer):
        'Look through the file for expected types of lines in a valid q-step file'
        Ndata = 0
        for i,S in enumerate(filepointer):
            vals = S.split()
            if len(vals) >= 2:
                try:
                    data = [float(val) for val in vals]
                    Ndata += 1
                except ValueError:
                    pass
        if not Ndata:     
            self.errors = 'No 2 or more column numeric data found'
            return False
        return True # no errors encountered

    def Reader(self,filename,filepointer, ParentFrame=None, **unused):
        print 'Read a q-step text file'
        x = []
        y = []
        w = []
        wave = 1.5428   #Cuka default
        Temperature = 300
        for i,S in enumerate(filepointer):
            if len(S) == 1:     #skip blank line
                continue
            if '=' in S:
                self.comments.append(S[:-1])
                if 'wave' in S.split('=')[0].lower():
                    try:
                        wave = float(S.split('=')[1])
                    except:
                        pass
                continue
            vals = S.split()
            if len(vals) >= 2:
                try:
                    data = [float(val) for val in vals]
                    x.append(float(data[0]))
                    f = float(data[1])
                    if f <= 0.0:
                        del x[-1]
                        continue
                    elif len(vals) > 2:
                        y.append(float(data[1]))
                        w.append(1.0/float(data[2])**2)
                    else:
                        y.append(float(data[1]))
                        w.append(1.0/float(data[1]))
                except ValueError:
                    msg = 'Error in line '+str(i+1)
                    print msg
                    continue
        N = len(x)
        for S in self.comments:
            if 'Temp' in S.split('=')[0]:
                try:
                    Temperature = float(S.split('=')[1])
                except:
                    pass
        self.instdict['wave'] = wave
        self.instdict['type'] = 'LXC'
        x = np.array(x)
        self.smallangledata = [
            x, # x-axis values q
            np.array(y), # small angle pattern intensities
            np.array(w), # 1/sig(intensity)^2 values (weights)
            np.zeros(N), # calc. intensities (zero)
            np.zeros(N), # obs-calc profiles
            np.zeros(N), # fix bkg
            ]
        self.smallangleentry[0] = filename
        self.smallangleentry[2] = 1 # xye file only has one bank
        self.idstring = ospath.basename(filename)
        # scan comments for temperature
        self.Sample['Temperature'] = Temperature

        return True

class txt_nmXRayReaderClass(G2IO.ImportSmallAngleData):
    'Routines to import X-ray q SAXD data from a .xsad or .xdat file, q in nm-1'
    def __init__(self):
        super(self.__class__,self).__init__( # fancy way to self-reference
            extensionlist=('.xsad','.xdat'),
            strictExtension=False,
            formatName = 'q (nm-1) step X-ray QIE data',
            longFormatName = 'q (nm-1) stepped X-ray text data file in Q,I,E order; E optional'
            )

    # Validate the contents -- make sure we only have valid lines
    def ContentsValidator(self, filepointer):
        'Look through the file for expected types of lines in a valid q-step file'
        Ndata = 0
        for i,S in enumerate(filepointer):
            vals = S.split()
            if len(vals) >= 2:
                try:
                    data = [float(val) for val in vals]
                    Ndata += 1
                except ValueError:
                    pass
        if not Ndata:     
            self.errors = 'No 2 or more column numeric data found'
            return False
        return True # no errors encountered

    def Reader(self,filename,filepointer, ParentFrame=None, **unused):
        print 'Read a q-step text file'
        x = []
        y = []
        w = []
        wave = 1.5428   #Cuka default
        Temperature = 300
        for i,S in enumerate(filepointer):
            if len(S) == 1:     #skip blank line
                continue
            if '=' in S:
                self.comments.append(S[:-1])
                if 'wave' in S.split('=')[0].lower():
                    try:
                        wave = float(S.split('=')[1])
                    except:
                        pass
                continue
            vals = S.split()
            if len(vals) >= 2:
                try:
                    data = [float(val) for val in vals]
                    x.append(float(data[0])/10.)        #convert nm-1 to A-1
                    f = float(data[1])
                    if f <= 0.0:
                        x.pop()
                        continue
                    elif len(vals) > 2:
                        y.append(float(data[1]))
                        w.append(1.0/float(data[2])**2)
                    else:
                        y.append(float(data[1]))
                        w.append(1.0/float(data[1]))
                except ValueError:
                    msg = 'Error in line '+str(i+1)
                    print msg
                    continue
        N = len(x)
        for S in self.comments:
            if 'Temp' in S.split('=')[0]:
                try:
                    Temperature = float(S.split('=')[1])
                except:
                    pass
        self.instdict['wave'] = wave
        self.instdict['type'] = 'LXC'
        x = np.array(x)
        self.smallangledata = [
            x, # x-axis values q
            np.array(y), # small angle pattern intensities
            np.array(w), # 1/sig(intensity)^2 values (weights)
            np.zeros(N), # calc. intensities (zero)
            np.zeros(N), # obs-calc profiles
            np.zeros(N), # fix bkg
            ]
        self.smallangleentry[0] = filename
        self.smallangleentry[2] = 1 # xye file only has one bank
        self.idstring = ospath.basename(filename)
        # scan comments for temperature
        self.Sample['Temperature'] = Temperature

        return True

class txt_CWNeutronReaderClass(G2IO.ImportSmallAngleData):
    'Routines to import neutron CW q SAXD data from a .nsad or .ndat file'
    def __init__(self):
        super(self.__class__,self).__init__( # fancy way to self-reference
            extensionlist=('.nsad','.ndat'),
            strictExtension=False,
            formatName = 'q (A-1) step neutron CW QIE data',
            longFormatName = 'q (A-1) stepped neutron CW text data file in Q,I,E order; E optional'
            )

    # Validate the contents -- make sure we only have valid lines
    def ContentsValidator(self, filepointer):
        'Look through the file for expected types of lines in a valid q-step file'
        Ndata = 0
        for i,S in enumerate(filepointer):
            vals = S.split()
            if len(vals) >= 2:
                try:
                    data = [float(val) for val in vals]
                    Ndata += 1
                except ValueError:
                    pass
        if not Ndata:     
            self.errors = 'No 2 or more column numeric data found'
            return False
        return True # no errors encountered

    def Reader(self,filename,filepointer, ParentFrame=None, **unused):
        print 'Read a q-step text file'
        x = []
        y = []
        w = []
        wave = 1.5428   #Cuka default
        Temperature = 300
        for i,S in enumerate(filepointer):
            if len(S) == 1:     #skip blank line
                continue
            if '=' in S:
                self.comments.append(S[:-1])
                if 'wave' in S.split('=')[0].lower():
                    try:
                        wave = float(S.split('=')[1])
                    except:
                        pass
                continue
            vals = S.split()
            if len(vals) >= 2:
                try:
                    data = [float(val) for val in vals]
                    x.append(float(data[0]))
                    f = float(data[1])
                    if f <= 0.0:
                        y.append(0.0)
                        w.append(1.0)
                    elif len(vals) > 2:
                        y.append(float(data[1]))
                        w.append(1.0/float(data[2])**2)
                    else:
                        y.append(float(data[1]))
                        w.append(1.0/float(data[1]))
                except ValueError:
                    msg = 'Error in line '+str(i+1)
                    print msg
                    continue
        N = len(x)
        for S in self.comments:
            if 'Temp' in S.split('=')[0]:
                try:
                    Temperature = float(S.split('=')[1])
                except:
                    pass
        self.instdict['wave'] = wave
        self.instdict['type'] = 'LNC'
        x = np.array(x)
        if np.any(x > 2.):         #q must be nm-1
            x /= 10.
        self.smallangledata = [
            x, # x-axis values q
            np.array(y), # small angle pattern intensities
            np.array(w), # 1/sig(intensity)^2 values (weights)
            np.zeros(N), # calc. intensities (zero)
            np.zeros(N), # obs-calc profiles
            np.zeros(N), # fix bkg
            ]
        self.smallangleentry[0] = filename
        self.smallangleentry[2] = 1 # xye file only has one bank
        self.idstring = ospath.basename(filename)
        # scan comments for temperature
        self.Sample['Temperature'] = Temperature

        return True

class txt_nmCWNeutronReaderClass(G2IO.ImportSmallAngleData):
    'Routines to import neutron CW q in nm-1 SAXD data from a .nsad or .ndat file'
    def __init__(self):
        super(self.__class__,self).__init__( # fancy way to self-reference
            extensionlist=('.nsad','.ndat'),
            strictExtension=False,
            formatName = 'q (nm-1) step neutron CW QIE data',
            longFormatName = 'q (nm-1) stepped neutron CW text data file in Q,I,E order; E optional'
            )

    # Validate the contents -- make sure we only have valid lines
    def ContentsValidator(self, filepointer):
        'Look through the file for expected types of lines in a valid q-step file'
        Ndata = 0
        for i,S in enumerate(filepointer):
            vals = S.split()
            if len(vals) >= 2:
                try:
                    data = [float(val) for val in vals]
                    Ndata += 1
                except ValueError:
                    pass
        if not Ndata:     
            self.errors = 'No 2 or more column numeric data found'
            return False
        return True # no errors encountered

    def Reader(self,filename,filepointer, ParentFrame=None, **unused):
        print 'Read a q-step text file'
        x = []
        y = []
        w = []
        wave = 1.5428   #Cuka default
        Temperature = 300
        for i,S in enumerate(filepointer):
            if len(S) == 1:     #skip blank line
                continue
            if '=' in S:
                self.comments.append(S[:-1])
                if 'wave' in S.split('=')[0].lower():
                    try:
                        wave = float(S.split('=')[1])
                    except:
                        pass
                continue
            vals = S.split()
            if len(vals) >= 2:
                try:
                    data = [float(val) for val in vals]
                    x.append(float(data[0])/10.)    #convert to A-1
                    f = float(data[1])
                    if f <= 0.0:
                        y.append(0.0)
                        w.append(1.0)
                    elif len(vals) > 2:
                        y.append(float(data[1]))
                        w.append(1.0/float(data[2])**2)
                    else:
                        y.append(float(data[1]))
                        w.append(1.0/float(data[1]))
                except ValueError:
                    msg = 'Error in line '+str(i+1)
                    print msg
                    continue
        N = len(x)
        for S in self.comments:
            if 'Temp' in S.split('=')[0]:
                try:
                    Temperature = float(S.split('=')[1])
                except:
                    pass
        self.instdict['wave'] = wave
        self.instdict['type'] = 'LNC'
        x = np.array(x)
        self.smallangledata = [
            x, # x-axis values q
            np.array(y), # small angle pattern intensities
            np.array(w), # 1/sig(intensity)^2 values (weights)
            np.zeros(N), # calc. intensities (zero)
            np.zeros(N), # obs-calc profiles
            np.zeros(N), # fix bkg
            ]
        self.smallangleentry[0] = filename
        self.smallangleentry[2] = 1 # xye file only has one bank
        self.idstring = ospath.basename(filename)
        # scan comments for temperature
        self.Sample['Temperature'] = Temperature

        return True
