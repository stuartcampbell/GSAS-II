# -*- coding: utf-8 -*-
########### SVN repository information ###################
# $Date: 2014-12-27 11:14:59 -0600 (Sat, 27 Dec 2014) $
# $Author: $
# $Revision: $
# $URL: $
# $Id: $
########### SVN repository information ###################
'''
*Module G2img_G2: Python pickled image*
---------------------------------------

Routine to read an image that has been pickled in Python. Images
in this format are created by the "Sum image data" command. 

'''

import sys
import os
import GSASIIIO as G2IO
import GSASIIpath
GSASIIpath.SetVersionNumber("$Revision: $")
class G2_ReaderClass(G2IO.ImportImage):
    def __init__(self):
        super(self.__class__,self).__init__( # fancy way to self-reference
            extensionlist=('.G2img',),
            strictExtension=True,
            formatName = 'G2 summed image',
            longFormatName = 'Pickled image from GSAS-II "Sum image data" command'
            )

    def ContentsValidator(self, filepointer):
        '''no test at this time
        '''
        return True
        
    def Reader(self,filename,filepointer, ParentFrame=None, **unused):
        '''Read using scipy PNG reader
        '''
        import scipy.misc
        filepointer.close() # close the file, since it will be reopened below. 
        filepointer = None
        Fp = open(filename,'rb')
        self.Comments,self.Data,self.Npix,self.image = cPickle.load(Fp)
        Fp.close()
        return True
# N.B. This replaces G2IO.GetG2Image
