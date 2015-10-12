# -*- coding: utf-8 -*-
########### SVN repository information ###################
# $Date: 2014-12-27 11:14:59 -0600 (Sat, 27 Dec 2014) $
# $Author: $
# $Revision: $
# $URL: $
# $Id: $
########### SVN repository information ###################
'''
*Module G2img_ADSC: .img image file*
--------------------------------------

Routine to read an ADSC .img file

'''

import sys
import os
import GSASIIIO as G2IO
import GSASIIpath
GSASIIpath.SetVersionNumber("$Revision: $")
class ADSC_ReaderClass(G2IO.ImportImage):
    def __init__(self):
        super(self.__class__,self).__init__( # fancy way to self-reference
            extensionlist=('.img',),
            strictExtension=True,
            formatName = 'ADSC image',
            longFormatName = 'ADSC image file'
            )

    def ContentsValidator(self, filepointer):
        '''no test at this time
        '''
        return True
        
    def Reader(self,filename,filepointer, ParentFrame=None, **unused):
        '''Read using Bob's routine
        '''
        filepointer.close() # close the file, since it will be reopened below. 
        filepointer = None
        self.Comments,self.Data,self.Npix,self.Image = G2IO.GetImgData(filename)
        Image[0][0] = 0
        if self.Npix == 0 or not self.Comments:
            return False
        return True
