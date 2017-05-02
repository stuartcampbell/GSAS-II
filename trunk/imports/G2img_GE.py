# -*- coding: utf-8 -*-
########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### SVN repository information ###################
'''
*Module G2img_GE: summed GE image file*
---------------------------------------

This shows an example of an importer that will handle files with
more than a single image. 

'''

import os
import numpy as np
import GSASIIobj as G2obj
import GSASIIpath
GSASIIpath.SetVersionNumber("$Revision$")
class GE_ReaderClass(G2obj.ImportImage):
    '''Routine to read a GE image, typically from APS Sector 1.
        
        The image files may be of form .geX (where X is ' ', 1, 2, 3 or 4),
        which is a raw image from the detector. These files may contain more
        than one image and have a rudimentary header. 
        Files with extension .sum or .cor are 4 byte integers/pixel, one image/file.
        Files with extension .avg are 2 byte integers/pixel, one image/file.
    '''

    def __init__(self):
        super(self.__class__,self).__init__( # fancy way to self-reference
            extensionlist=('.sum','.cor','.avg','.ge','.ge1','.ge2','.ge3','.ge4'),
            strictExtension=True,
            formatName = 'GE image',
            longFormatName = 'Summed GE image file'
            )

    def ContentsValidator(self, filepointer):
        '''just a test on file size
        '''
        if '.sum' not in str(filepointer):
            try:
                statinfo = os.stat(str(filepointer).split("'")[1])
                fsize = statinfo.st_size
                self.nimages = (fsize-8192)/(2*2048**2)
            except:
                return False    #bad file size
        return True
        
    def Reader(self,filename,filepointer, ParentFrame=None, **kwarg):
        '''Read using GE file reader, :func:`GetGEsumData`
        '''
        #rdbuffer = kwarg.get('buffer')
        imagenum = kwarg.get('blocknum')
        #sum = kwarg.get('sum')
        if imagenum is None: imagenum = 1
        self.Comments,self.Data,self.Npix,self.Image,more = \
            GetGEsumData(self,filename,imagenum=imagenum)
        if self.Npix == 0 or not self.Comments:
            return False
        self.LoadImage(ParentFrame,filename,imagenum)
        self.repeatcount = imagenum
        self.repeat = more
        return True

class GEsum_ReaderClass(G2obj.ImportImage):
    '''Routine to read multiple GE images & sum them, typically from APS Sector 1.
        
        The image files may be of form .geX (where X is ' ', 1, 2, 3 or 4),
        which is a raw image from the detector. These files may contain more
        than one image and have a rudimentary header. 
        Files with extension .sum or .cor are 4 byte integers/pixel, one image/file.
        Files with extension .avg are 2 byte integers/pixel, one image/file.
    '''

    def __init__(self):
        super(self.__class__,self).__init__( # fancy way to self-reference
            extensionlist=('.ge1','.ge2','.ge3','.ge4'),
            strictExtension=True,
            formatName = 'sum GE multi-image',
            longFormatName = 'sum of GE multi-image file'
            )

    def ContentsValidator(self, filepointer):
        '''just a test on file size
        '''
        try:
            statinfo = os.stat(str(filepointer).split("'")[1])
            fsize = statinfo.st_size
            nimages = (fsize-8192)/(2*2048**2)
        except:
            return False    #bad file size
        return True
        
    def Reader(self,filename,filepointer, ParentFrame=None, **kwarg):
        '''Read using GE file reader, :func:`GetGEsumData`
        '''
        #rdbuffer = kwarg.get('buffer')
        imagenum = kwarg.get('blocknum')
        if imagenum is None: imagenum = 1
        self.Comments,self.Data,self.Npix,self.Image,more = \
            GetGEsumData(self,filename,imagenum=imagenum,sum=True)
        if self.Npix == 0 or not self.Comments:
            return False
        self.LoadImage(ParentFrame,filename,imagenum)
        self.repeatcount = imagenum
        self.repeat = more
        return True

def GetGEsumData(self,filename,imagenum=1,sum=False):
    '''Read G.E. detector images from various files as produced at 1-ID and
    with Detector Pool detector. Also sums multiple image files if desired
    '''
    import struct as st
    import cPickle
    import time
    more = False
    time0 = time.time()
    File = open(filename,'rb')
    if filename.split('.')[-1] in ['sum',]:
        head = ['GE detector sum  data from APS 1-ID',]
        sizexy = [2048,2048]
        Npix = sizexy[0]*sizexy[1]
        image = np.array(np.frombuffer(File.read(4*Npix),dtype=np.float32),dtype=np.int32)
    elif filename.split('.')[-1] in ['avg','cor']:
        File.seek(0,2)
        last = File.tell()
        pos = last-2*(2048**2)
        File.seek(pos)
        head = ['GE detector avg or cor data from APS 1-ID',]
        sizexy = [2048,2048]
        Npix = sizexy[0]*sizexy[1]
        image = np.array(np.frombuffer(File.read(2*Npix),dtype=np.int16),dtype=np.int32)
    else:
        head = ['GE detector raw data',]
        File.seek(18)
        size,nframes = st.unpack('<ih',File.read(6))
        # number of frames seems to be 3 for single-image files
        if size != 2048:
            print('Warning GE image size unexpected: '+str(size))
            return 0,0,0,0,False # probably should quit now
        if imagenum > nframes:
            print('Error: attempt to read image #'+str(imagenum)+
                  ' from file with '+str(nframes)+' images.')
            return 0,0,0,0,False
        elif imagenum < nframes:
            more = True
        sizexy = [2048,2048]
        Npix = sizexy[0]*sizexy[1]
        pos = 8192 + (imagenum-1)*2*Npix
        File.seek(pos)
        image = np.array(np.frombuffer(File.read(2*Npix),dtype=np.int16),dtype=np.int32)
        if len(image) != sizexy[1]*sizexy[0]:
            print('not enough images while reading GE file: '+filename+'image #'+str(imagenum))
            return 0,0,0,0,False            
        head += ['file: '+filename+' image #'+str(imagenum),]
        if sum:    #will ignore imagenum
            print 'Frames to read %d'%(nframes),
            while nframes > 1: #OK, this will sum the frames.
                try:
                    image += np.array(np.frombuffer(File.read(2*Npix),dtype=np.int16),dtype=np.int32)
                except ValueError:
                    break
                nframes -= 1
                print '%d'%(nframes),
            print ''   
            more = False
            filename = os.path.splitext(filename)[0]+'.G2img'
            File = open(filename,'wb')
            Data = {'pixelSize':[200,200],'wavelength':0.15,'distance':250.0,'center':[204.8,204.8],'size':sizexy}
            image = np.reshape(image,(sizexy[1],sizexy[0]))
            cPickle.dump([head,Data,Npix,image],File,1)
            File.close()
            self.sumfile = filename
            self.formatName = 'GSAS-II image'
            sum = False
    image = np.reshape(image,(sizexy[1],sizexy[0]))
    data = {'pixelSize':[200,200],'wavelength':0.15,'distance':250.0,'center':[204.8,204.8],'size':sizexy}
    File.close()
    print 'Image read time %.2fs'%(time.time()-time0)
    if GSASIIpath.GetConfigValue('debug'):
        print 'Read GE file: '+filename+' image #'+'%04d'%(imagenum)
    return head,data,Npix,image,more
