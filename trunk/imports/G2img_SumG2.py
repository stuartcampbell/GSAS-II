# -*- coding: utf-8 -*-
########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### SVN repository information ###################
'''
*Module G2img_SumG2: Python pickled image*
------------------------------------------

'''

import cPickle
import GSASIIobj as G2obj
import GSASIIpath
GSASIIpath.SetVersionNumber("$Revision$")
class G2_ReaderClass(G2obj.ImportImage):
    '''Routine to read an image that has been pickled in Python. Images
    in this format are created by the "Sum image data" command. At least for
    now, only one image is permitted per file.
    '''
    def __init__(self):
        super(self.__class__,self).__init__( # fancy way to self-reference
            extensionlist=('.G2img',),
            strictExtension=True,
            formatName = 'GSAS-II image',
            longFormatName = 'cPickled image from GSAS-II'
            )

    def ContentsValidator(self, filepointer):
        '''test by trying to unpickle (should be quick)
        '''
        try:
            cPickle.load(filepointer)
        except:
            return False
        return True
        
    def Reader(self,filename,filepointer, ParentFrame=None, **unused):
        '''Read using cPickle
        '''
        Fp = open(filename,'rb')
        self.Comments,self.Data,self.Npix,self.Image = cPickle.load(Fp)
        Fp.close()
        self.LoadImage(ParentFrame,filename)
        return True
