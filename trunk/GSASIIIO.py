# -*- coding: utf-8 -*-
########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### SVN repository information ###################
'''
*GSASIIIO: Misc I/O routines*
=============================

Module with miscellaneous routines for input and output. Many
are GUI routines to interact with user.

Includes support for image reading.

Also includes base classes for data import routines.

'''
"""GSASIIIO: functions for IO of data
   Copyright: 2008, Robert B. Von Dreele (Argonne National Laboratory)
"""
import wx
import math
import numpy as np
import cPickle
import sys
import re
import random as ran
import GSASIIpath
GSASIIpath.SetVersionNumber("$Revision$")
import GSASIIgrid as G2gd
import GSASIIspc as G2spc
import GSASIIobj as G2obj
import GSASIIlattice as G2lat
import GSASIIpwdGUI as G2pdG
import GSASIIimage as G2img
import GSASIIElem as G2el
import GSASIIstrIO as G2stIO
import GSASIImapvars as G2mv
import GSASIIctrls as G2G
import os
import os.path as ospath

DEBUG = False       #=True for various prints
TRANSP = False      #=true to transpose images for testing
if GSASIIpath.GetConfigValue('Transpose'): TRANSP = True
npsind = lambda x: np.sin(x*np.pi/180.)

def sfloat(S):
    'Convert a string to float. An empty field or a unconvertable value is treated as zero'
    if S.strip():
        try:
            return float(S)
        except ValueError:
            pass
    return 0.0

def sint(S):
    'Convert a string to int. An empty field is treated as zero'
    if S.strip():
        return int(S)
    else:
        return 0

def trim(val):
    '''Simplify a string containing leading and trailing spaces
    as well as newlines, tabs, repeated spaces etc. into a shorter and
    more simple string, by replacing all ranges of whitespace
    characters with a single space. 

    :param str val: the string to be simplified

    :returns: the (usually) shortened version of the string
    '''
    return re.sub('\s+', ' ', val).strip()

def makeInstDict(names,data,codes):
    inst = dict(zip(names,zip(data,data,codes)))
    for item in inst:
        inst[item] = list(inst[item])
    return inst

def FileDlgFixExt(dlg,file):
    'this is needed to fix a problem in linux wx.FileDialog'
    ext = dlg.GetWildcard().split('|')[2*dlg.GetFilterIndex()+1].strip('*')
    if ext not in file:
        file += ext
    return file
        
def GetPowderPeaks(fileName):
    'Read powder peaks from a file'
    sind = lambda x: math.sin(x*math.pi/180.)
    asind = lambda x: 180.*math.asin(x)/math.pi
    wave = 1.54052
    File = open(fileName,'Ur')
    Comments = []
    peaks = []
    S = File.readline()
    while S:
        if S[:1] == '#':
            Comments.append(S[:-1])
        else:
            item = S.split()
            if len(item) == 1:
                peaks.append([float(item[0]),1.0])
            elif len(item) > 1:
                peaks.append([float(item[0]),float(item[0])])
        S = File.readline()
    File.close()
    if Comments:
       print 'Comments on file:'
       for Comment in Comments: 
            print Comment
            if 'wavelength' in Comment:
                wave = float(Comment.split('=')[1])
    Peaks = []
    if peaks[0][0] > peaks[-1][0]:          # d-spacings - assume CuKa
        for peak in peaks:
            dsp = peak[0]
            sth = wave/(2.0*dsp)
            if sth < 1.0:
                tth = 2.0*asind(sth)
            else:
                break
            Peaks.append([tth,peak[1],True,False,0,0,0,dsp,0.0])
    else:                                   #2-thetas - assume Cuka (for now)
        for peak in peaks:
            tth = peak[0]
            dsp = wave/(2.0*sind(tth/2.0))
            Peaks.append([tth,peak[1],True,False,0,0,0,dsp,0.0])
    limits = [1000.,0.]
    for peak in Peaks:
        limits[0] = min(limits[0],peak[0])
        limits[1] = max(limits[1],peak[0])
    limits[0] = max(1.,(int(limits[0]-1.)/5)*5.)
    limits[1] = min(170.,(int(limits[1]+1.)/5)*5.)
    return Comments,Peaks,limits,wave

def CheckImageFile(G2frame,imagefile):
    '''Try to locate an image file if the project and image have been moved
    together. If the image file cannot be found, request the location from
    the user.

    :param wx.Frame G2frame: main GSAS-II Frame and data object
    :param str imagefile: name of image file
    :returns: imagefile, if it exists, or the name of a file
      that does exist or False if the user presses Cancel

    '''
    if not os.path.exists(imagefile):
        print 'Image file '+imagefile+' not found'
        fil = imagefile.replace('\\','/') # windows?!
        # see if we can find a file with same name or in a similarly named sub-dir
        pth,fil = os.path.split(fil)
        prevpth = None
        while pth and pth != prevpth:
            prevpth = pth
            if os.path.exists(os.path.join(G2frame.dirname,fil)):
                print 'found image file '+os.path.join(G2frame.dirname,fil)
                return os.path.join(G2frame.dirname,fil)
            pth,enddir = os.path.split(pth)
            fil = os.path.join(enddir,fil)
        # not found as a subdirectory, drop common parts of path for last saved & image file names
        #    if image was .../A/B/C/imgs/ima.ge
        #      & GPX was  .../A/B/C/refs/fil.gpx but is now .../NEW/TEST/TEST1
        #    will look for .../NEW/TEST/TEST1/imgs/ima.ge, .../NEW/TEST/imgs/ima.ge, .../NEW/imgs/ima.ge and so on
        Controls = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,G2frame.root, 'Controls'))
        gpxPath = Controls.get('LastSavedAs','').replace('\\','/').split('/') # blank in older .GPX files
        imgPath = imagefile.replace('\\','/').split('/')
        for p1,p2 in zip(gpxPath,imgPath):
            if p1 == p2:
                gpxPath.pop(0),imgPath.pop(0)
            else:
                break
        fil = os.path.join(*imgPath) # file with non-common prefix elements
        prevpth = None
        pth = os.path.abspath(G2frame.dirname)
        while pth and pth != prevpth:
            prevpth = pth
            if os.path.exists(os.path.join(pth,fil)):
                print 'found image file '+os.path.join(pth,fil)
                return os.path.join(pth,fil)
            pth,enddir = os.path.split(pth)
        #GSASIIpath.IPyBreak()

    if not os.path.exists(imagefile):
        dlg = wx.FileDialog(G2frame, 'Previous image file not found; open here', '.', '',\
        'Any image file (*.edf;*.tif;*.tiff;*.mar*;*.ge*;*.avg;*.sum;*.img;*.cor;*.stl)\
        |*.edf;*.tif;*.tiff;*.mar*;*.ge*;*.avg;*.sum;*.img;*.cor;*.stl|\
        European detector file (*.edf)|*.edf|\
        Any detector tif (*.tif;*.tiff)|*.tif;*.tiff|\
        MAR file (*.mar*)|*.mar*|\
        GE Image (*.ge*;*.avg;*.sum;*.cor)|*.ge*;*.avg;*.sum;*.cor|\
        ADSC Image (*.img)|*.img|\
        Rigaku-Axis4 (*.stl)|*.stl|\
        All files (*.*)|*.*',wx.OPEN|wx.CHANGE_DIR)
        try:
            dlg.SetFilename(''+ospath.split(imagefile)[1])
            if dlg.ShowModal() == wx.ID_OK:
                imagefile = dlg.GetPath()
            else:
                imagefile = False
        finally:
            dlg.Destroy()
    return imagefile

def EditImageParms(parent,Data,Comments,Image,filename):
    dlg = wx.Dialog(parent, wx.ID_ANY, 'Edit image parameters',
                    style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
    def onClose(event):
        dlg.EndModal(wx.ID_OK)
    mainsizer = wx.BoxSizer(wx.VERTICAL)
    h,w = Image.shape[:2]
    mainsizer.Add(wx.StaticText(dlg,wx.ID_ANY,
                                'File '+str(filename)+'\nImage size: '+str(h)+' x '+str(w)),
                  0,wx.ALIGN_LEFT|wx.ALL, 2)
    
    vsizer = wx.BoxSizer(wx.HORIZONTAL)
    vsizer.Add(wx.StaticText(dlg,wx.ID_ANY,u'Wavelength (\xC5) '),
               0,wx.ALIGN_LEFT|wx.ALL, 2)
    wdgt = G2G.ValidatedTxtCtrl(dlg,Data,'wavelength')
    vsizer.Add(wdgt)
    mainsizer.Add(vsizer,0,wx.ALIGN_LEFT|wx.ALL, 2)

    vsizer = wx.BoxSizer(wx.HORIZONTAL)
    vsizer.Add(wx.StaticText(dlg,wx.ID_ANY,u'Pixel size (\xb5m). Width '),
               0,wx.ALIGN_LEFT|wx.ALL, 2)
    wdgt = G2G.ValidatedTxtCtrl(dlg,Data['pixelSize'],0,
                                 size=(50,-1))
    vsizer.Add(wdgt)
    vsizer.Add(wx.StaticText(dlg,wx.ID_ANY,u'  Height '),
               wx.ALIGN_LEFT|wx.ALL, 2)
    wdgt = G2G.ValidatedTxtCtrl(dlg,Data['pixelSize'],1,
                                 size=(50,-1))
    vsizer.Add(wdgt)
    mainsizer.Add(vsizer,0,wx.ALIGN_LEFT|wx.ALL, 2)

    vsizer = wx.BoxSizer(wx.HORIZONTAL)
    vsizer.Add(wx.StaticText(dlg,wx.ID_ANY,u'Sample to detector (mm) '),
               0,wx.ALIGN_LEFT|wx.ALL, 2)
    wdgt = G2G.ValidatedTxtCtrl(dlg,Data,'distance')
    vsizer.Add(wdgt)
    mainsizer.Add(vsizer,0,wx.ALIGN_LEFT|wx.ALL, 2)

    vsizer = wx.BoxSizer(wx.HORIZONTAL)
    vsizer.Add(wx.StaticText(dlg,wx.ID_ANY,u'Beam center (pixels). X = '),
               0,wx.ALIGN_LEFT|wx.ALL, 2)
    wdgt = G2G.ValidatedTxtCtrl(dlg,Data['center'],0,
                                 size=(75,-1))
    vsizer.Add(wdgt)
    vsizer.Add(wx.StaticText(dlg,wx.ID_ANY,u'  Y = '),
               wx.ALIGN_LEFT|wx.ALL, 2)
    wdgt = G2G.ValidatedTxtCtrl(dlg,Data['center'],1,
                                 size=(75,-1))
    vsizer.Add(wdgt)
    mainsizer.Add(vsizer,0,wx.ALIGN_LEFT|wx.ALL, 2)

    vsizer = wx.BoxSizer(wx.HORIZONTAL)
    vsizer.Add(wx.StaticText(dlg,wx.ID_ANY,u'Comments '),
               0,wx.ALIGN_LEFT|wx.ALL, 2)
    wdgt = G2G.ValidatedTxtCtrl(dlg,Comments,0,size=(250,-1))
    vsizer.Add(wdgt)
    mainsizer.Add(vsizer,0,wx.ALIGN_LEFT|wx.ALL, 2)

    btnsizer = wx.StdDialogButtonSizer()
    OKbtn = wx.Button(dlg, wx.ID_OK, 'Continue')
    OKbtn.SetDefault()
    OKbtn.Bind(wx.EVT_BUTTON,onClose)
    btnsizer.AddButton(OKbtn) # not sure why this is needed
    btnsizer.Realize()
    mainsizer.Add(btnsizer, 1, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND, 5)
    dlg.SetSizer(mainsizer)
    dlg.CenterOnParent()
    dlg.ShowModal()
    
def ReadLoadImage(imagefile,G2frame):
    '''Read a GSAS-II image file and load it into the data tree
    Called only from GSASII.OnImageRead (depreciated).
    '''
    # if a zip file, open and extract
    if os.path.splitext(imagefile)[1].lower() == '.zip':
        extractedfile = ExtractFileFromZip(imagefile,parent=G2frame)
        if extractedfile is not None and extractedfile != imagefile:
            imagefile = extractedfile
    Comments,Data,Npix,Image = GetImageData(G2frame,imagefile) # can only read 1st image
    if Comments:
        LoadImage2Tree(imagefile,G2frame,Comments,Data,Npix,Image)
    
def LoadImage2Tree(imagefile,G2frame,Comments,Data,Npix,Image):
    '''Load an image into the tree. Saves the location of the image, as well as the
    ImageTag (where there is more than one image in the file), if defined.
    '''
    ImgNames = []
    if G2frame.PatternTree.GetCount(): # get a list of existing Image entries
        item, cookie = G2frame.PatternTree.GetFirstChild(G2frame.root)
        while item:
            name = G2frame.PatternTree.GetItemText(item)
            if name.startswith('IMG'): ImgNames.append(name)        
            item, cookie = G2frame.PatternTree.GetNextChild(G2frame.root, cookie)
    TreeLbl = 'IMG '+os.path.basename(imagefile)
    ImageTag = Data.get('ImageTag')
    if ImageTag:
        TreeLbl += ' #'+str(ImageTag)
        imageInfo = (imagefile,ImageTag)
    else:
        imageInfo = imagefile
    TreeName = G2obj.MakeUniqueLabel(TreeLbl,ImgNames)
    Id = G2frame.PatternTree.AppendItem(parent=G2frame.root,text=TreeName)
    G2frame.PatternTree.SetItemPyData(G2frame.PatternTree.AppendItem(Id,text='Comments'),Comments)
    Imax = np.amax(Image)
    Imin = max(0.0,np.amin(Image))          #force positive
    if G2frame.imageDefault:
        Data = copy.copy(G2frame.imageDefault)
        Data['showLines'] = True
        Data['ring'] = []
        Data['rings'] = []
        Data['cutoff'] = 10
        Data['pixLimit'] = 20
        Data['edgemin'] = 100000000
        Data['calibdmin'] = 0.5
        Data['calibskip'] = 0
        Data['ellipses'] = []
        Data['calibrant'] = ''
        Data['GonioAngles'] = [0.,0.,0.]
        Data['DetDepthRef'] = False
    else:
        Data['type'] = 'PWDR'
        Data['color'] = 'Paired'
        Data['tilt'] = 0.0
        Data['rotation'] = 0.0
        Data['showLines'] = False
        Data['ring'] = []
        Data['rings'] = []
        Data['cutoff'] = 10
        Data['pixLimit'] = 20
        Data['calibdmin'] = 0.5
        Data['calibskip'] = 0
        Data['edgemin'] = 100000000
        Data['ellipses'] = []
        Data['GonioAngles'] = [0.,0.,0.]
        Data['DetDepth'] = 0.
        Data['DetDepthRef'] = False
        Data['calibrant'] = ''
        Data['IOtth'] = [2.0,5.0]
        Data['LRazimuth'] = [135,225]
        Data['azmthOff'] = 0.0
        Data['outChannels'] = 2500
        Data['outAzimuths'] = 1
        Data['centerAzm'] = False
        Data['fullIntegrate'] = False
        Data['setRings'] = False
        Data['background image'] = ['',-1.0]                            
        Data['dark image'] = ['',-1.0]
        Data['Flat Bkg'] = 0.0
    Data['setDefault'] = False
    Data['range'] = [(Imin,Imax),[Imin,Imax]]
    G2frame.PatternTree.SetItemPyData(G2frame.PatternTree.AppendItem(Id,text='Image Controls'),Data)
    Masks = {'Points':[],'Rings':[],'Arcs':[],'Polygons':[],'Frames':[],'Thresholds':[(Imin,Imax),[Imin,Imax]]}
    G2frame.PatternTree.SetItemPyData(G2frame.PatternTree.AppendItem(Id,text='Masks'),Masks)
    G2frame.PatternTree.SetItemPyData(G2frame.PatternTree.AppendItem(Id,text='Stress/Strain'),
        {'Type':'True','d-zero':[],'Sample phi':0.0,'Sample z':0.0,'Sample load':0.0})
    G2frame.PatternTree.SetItemPyData(Id,[Npix,imageInfo])
    G2frame.PickId = Id
    G2frame.PickIdText = G2frame.GetTreeItemsList(G2frame.PickId)
    G2frame.Image = Id

def GetImageData(G2frame,imagefile,imageOnly=False,ImageTag=None):
    '''Read a single image with an image importer. 

    :param wx.Frame G2frame: main GSAS-II Frame and data object.
    :param str imagefile: name of image file
    :param bool imageOnly: If True return only the image,
      otherwise  (default) return more (see below)
    :param int/str ImageTag: specifies a particular image to be read from a file.
      First image is read if None (default).

    :returns: an image as a numpy array or a list of four items:
      Comments, Data, Npix and the Image, as selected by imageOnly

    '''
    # determine which formats are compatible with this file
    primaryReaders = []
    secondaryReaders = []
    for rd in G2frame.ImportImageReaderlist:
        flag = rd.ExtensionValidator(imagefile)
        if flag is None: 
            secondaryReaders.append(rd)
        elif flag:
            primaryReaders.append(rd)
    if len(secondaryReaders) + len(primaryReaders) == 0:
        print('Error: No matching format for file '+filename)
        raise Exception('No image read')
    fp = None
    errorReport = ''
    fp = open(imagefile,'Ur')
    for rd in primaryReaders+secondaryReaders:
        rd.ReInitialize() # purge anything from a previous read
        fp.seek(0)  # rewind
        rd.errors = "" # clear out any old errors
        if not rd.ContentsValidator(fp): # rejected on cursory check
            errorReport += "\n  "+rd.formatName + ' validator error'
            if rd.errors: 
                errorReport += ': '+rd.errors
                continue
        rdbuffer = {} # create temporary storage for file reader
        if imageOnly:
            ParentFrame = None # prevent GUI access on reread
        else:
            ParentFrame = G2frame
        if GSASIIpath.GetConfigValue('debug'):
            flag = rd.Reader(imagefile,fp,ParentFrame,blocknum=ImageTag)
        else:
            flag = False
            try:
                flag = rd.Reader(imagefile,fp,ParentFrame,blocknum=ImageTag)
            except rd.ImportException as detail:
                rd.errors += "\n  Read exception: "+str(detail)
            except Exception as detail:
                import traceback
                rd.errors += "\n  Unhandled read exception: "+str(detail)
                rd.errors += "\n  Traceback info:\n"+str(traceback.format_exc())
        if flag: # this read succeeded
            if rd.Image is None:
                raise Exception('No image read. Strange!')
            if GSASIIpath.GetConfigValue('Transpose'):
                print 'Transposing Image!'
                rd.Image = rd.Image.T
            #rd.readfilename = imagefile
            if imageOnly:
                return rd.Image
            else:
                return rd.Comments,rd.Data,rd.Npix,rd.Image
    else:
        print('Error reading file '+filename)
        print('Error messages(s)\n'+errorReport)
        raise Exception('No image read')    

def ReadImages(G2frame,imagefile):
    '''Read one or more images from a file and put them into the Tree
    using image importers. Called only in :meth:`AutoIntFrame.OnTimerLoop`.

    :param wx.Frame G2frame: main GSAS-II Frame and data object.
    :param str imagefile: name of image file 

    :returns: a list of the id's of the IMG tree items created 
    '''
    # determine which formats are compatible with this file
    primaryReaders = []
    secondaryReaders = []
    for rd in G2frame.ImportImageReaderlist:
        flag = rd.ExtensionValidator(imagefile)
        if flag is None:
            secondaryReaders.append(rd)
        elif flag:
            primaryReaders.append(rd)
    if len(secondaryReaders) + len(primaryReaders) == 0:
        print('Error: No matching format for file '+filename)
        raise Exception('No image read')
    errorReport = ''
    fp = open(imagefile,'Ur')
    rdbuffer = {} # create temporary storage for file reader
    for rd in primaryReaders+secondaryReaders:
        rd.ReInitialize() # purge anything from a previous read
        fp.seek(0)  # rewind
        rd.errors = "" # clear out any old errors
        if not rd.ContentsValidator(fp): # rejected on cursory check
            errorReport += "\n  "+rd.formatName + ' validator error'
            if rd.errors: 
                errorReport += ': '+rd.errors
                continue
        ParentFrame = G2frame
        block = 0
        repeat = True
        CreatedIMGitems = []
        while repeat: # loop if the reader asks for another pass on the file
            block += 1
            repeat = False
            if GSASIIpath.GetConfigValue('debug'):
                flag = rd.Reader(imagefile,fp,ParentFrame,blocknum=block,Buffer=rdbuffer)
            else:
                flag = False
                try:
                    flag = rd.Reader(imagefile,fp,ParentFrame,blocknum=block,Buffer=rdbuffer)
                except rd.ImportException as detail:
                    rd.errors += "\n  Read exception: "+str(detail)
                except Exception as detail:
                    import traceback
                    rd.errors += "\n  Unhandled read exception: "+str(detail)
                    rd.errors += "\n  Traceback info:\n"+str(traceback.format_exc())
            if flag: # this read succeeded
                if rd.Image is None:
                    raise Exception('No image read. Strange!')
                if GSASIIpath.GetConfigValue('Transpose'):
                    print 'Transposing Image!'
                    rd.Image = rd.Image.T
                rd.Data['ImageTag'] = rd.repeatcount
                LoadImage2Tree(imagefile,G2frame,rd.Comments,rd.Data,rd.Npix,rd.Image)
                repeat = rd.repeat
            CreatedIMGitems.append(G2frame.Image)
        if CreatedIMGitems: return CreatedIMGitems
    else:
        print('Error reading file '+filename)
        print('Error messages(s)\n'+errorReport)
        return []
        #raise Exception('No image read')    
        
def PutG2Image(filename,Comments,Data,Npix,image):
    'Write an image as a python pickle - might be better as an .edf file?'
    File = open(filename,'wb')
    cPickle.dump([Comments,Data,Npix,image],File,1)
    File.close()
    return
    
# should get moved to importer when ready to test
def GetEdfData(filename,imageOnly=False):    
    'Read European detector data edf file'
    import struct as st
    import array as ar
    if not imageOnly:
        print 'Read European detector data edf file: ',filename
    File = open(filename,'rb')
    fileSize = os.stat(filename).st_size
    head = File.read(3072)
    lines = head.split('\n')
    sizexy = [0,0]
    pixSize = [154,154]     #Pixium4700?
    cent = [0,0]
    wave = 1.54187  #default <CuKa>
    dist = 1000.
    head = ['European detector data',]
    for line in lines:
        line = line.replace(';',' ').strip()
        fields = line.split()
        if 'Dim_1' in line:
            sizexy[0] = int(fields[2])
        elif 'Dim_2' in line:
            sizexy[1] = int(fields[2])
        elif 'DataType' in line:
            dType = fields[2]
        elif 'wavelength' in line:
            wave = float(fields[2])
        elif 'Size' in line:
            imSize = int(fields[2])
#        elif 'DataType' in lines:
#            dType = fields[2]
        elif 'pixel_size_x' in line:
            pixSize[0] = float(fields[2])
        elif 'pixel_size_y' in line:
            pixSize[1] = float(fields[2])
        elif 'beam_center_x' in line:
            cent[0] = float(fields[2])
        elif 'beam_center_y' in line:
            cent[1] = float(fields[2])
        elif 'refined_distance' in line:
            dist = float(fields[2])
        if line:
            head.append(line)
        else:   #blank line at end of header
            break  
    File.seek(fileSize-imSize)
    if dType == 'UnsignedShort':        
        image = np.array(ar.array('H',File.read(imSize)),dtype=np.int32)
    elif dType == 'UnsignedInt':
        image = np.array(ar.array('L',File.read(imSize)),dtype=np.int32)
    elif dType == 'UnsignedLong':
        image = np.array(ar.array('L',File.read(imSize)),dtype=np.int32)
    elif dType == 'SignedInteger':
        image = np.array(ar.array('l',File.read(imSize)),dtype=np.int32)
    image = np.reshape(image,(sizexy[1],sizexy[0]))
    data = {'pixelSize':pixSize,'wavelength':wave,'distance':dist,'center':cent,'size':sizexy}
    Npix = sizexy[0]*sizexy[1]
    File.close()    
    if imageOnly:
        return image
    else:
        return head,data,Npix,image
        
# should get moved to importer when ready to test
def GetRigaku(filename,imageOnly=False):
    'Read Rigaku R-Axis IV image file'
    import struct as st
    import array as ar
    if not imageOnly:
        print 'Read Rigaku R-Axis IV file: ',filename    
    File = open(filename,'rb')
    fileSize = os.stat(filename).st_size
    Npix = (fileSize-6000)/2
    Head = File.read(6000)
    head = ['Rigaku R-Axis IV detector data',]
    image = np.array(ar.array('H',File.read(fileSize-6000)),dtype=np.int32)
    print fileSize,image.shape
    print head
    if Npix == 9000000:
        sizexy = [3000,3000]
        pixSize = [100.,100.]        
    elif Npix == 2250000:
        sizexy = [1500,1500]
        pixSize = [200.,200.]
    else:
        sizexy = [6000,6000]
        pixSize = [50.,50.] 
    image = np.reshape(image,(sizexy[1],sizexy[0]))        
    data = {'pixelSize':pixSize,'wavelength':1.5428,'distance':250.0,'center':[150.,150.],'size':sizexy}  
    File.close()    
    if imageOnly:
        return image
    else:
        return head,data,Npix,image
    
# should get moved to importer when ready to test        
def GetImgData(filename,imageOnly=False):
    'Read an ADSC image file'
    import struct as st
    import array as ar
    if not imageOnly:
        print 'Read ADSC img file: ',filename
    File = open(filename,'rb')
    head = File.read(511)
    lines = head.split('\n')
    head = []
    center = [0,0]
    for line in lines[1:-2]:
        line = line.strip()[:-1]
        if line:
            if 'SIZE1' in line:
                size = int(line.split('=')[1])
                Npix = size*size
            elif 'WAVELENGTH' in line:
                wave = float(line.split('=')[1])
            elif 'BIN' in line:
                if line.split('=')[1] == '2x2':
                    pixel=(102,102)
                else:
                    pixel = (51,51)
            elif 'DISTANCE' in line:
                distance = float(line.split('=')[1])
            elif 'CENTER_X' in line:
                center[0] = float(line.split('=')[1])
            elif 'CENTER_Y' in line:
                center[1] = float(line.split('=')[1])
            head.append(line)
    data = {'pixelSize':pixel,'wavelength':wave,'distance':distance,'center':center,'size':[size,size]}
    image = []
    row = 0
    pos = 512
    File.seek(pos)
    image = np.array(ar.array('H',File.read(2*Npix)),dtype=np.int32)
    image = np.reshape(image,(sizexy[1],sizexy[0]))
#    image = np.zeros(shape=(size,size),dtype=np.int32)    
#    while row < size:
#        File.seek(pos)
#        line = ar.array('H',File.read(2*size))
#        image[row] = np.asarray(line)
#        row += 1
#        pos += 2*size
    File.close()
    if imageOnly:
        return image
    else:
        return lines[1:-2],data,Npix,image
       
# should get moved to importer when ready to test
def GetMAR345Data(filename,imageOnly=False):
    'Read a MAR-345 image plate image'
    import array as ar
    import struct as st
    try:
        import pack_f as pf
    except:
        msg = wx.MessageDialog(None, message="Unable to load the GSAS MAR image decompression, pack_f",
                               caption="Import Error",
                               style=wx.ICON_ERROR | wx.OK | wx.STAY_ON_TOP)
        msg.ShowModal()
        return None,None,None,None

    if not imageOnly:
        print 'Read Mar345 file: ',filename
    File = open(filename,'rb')
    head = File.read(4095)
    numbers = st.unpack('<iiiiiiiiii',head[:40])
    lines = head[128:].split('\n')
    head = []
    for line in lines:
        line = line.strip()
        if 'PIXEL' in line:
            values = line.split()
            pixel = (int(values[2]),int(values[4]))     #in microns
        elif 'WAVELENGTH' in line:
            wave = float(line.split()[1])
        elif 'DISTANCE' in line:
            distance = float(line.split()[1])           #in mm
        elif 'CENTER' in line:
            values = line.split()
            center = [float(values[2])/10.,float(values[4])/10.]    #make in mm from pixels
        if line: 
            head.append(line)
    data = {'pixelSize':pixel,'wavelength':wave,'distance':distance,'center':center}
    for line in head:
        if 'FORMAT' in line[0:6]:
            items = line.split()
            sizex = int(items[1])
            Npix = int(items[3])
            sizey = int(Npix/sizex)
    pos = 4096
    data['size'] = [sizex,sizey]
    File.seek(pos)
    line = File.read(8)
    while 'CCP4' not in line:       #get past overflow list for now
        line = File.read(8)
        pos += 8
    pos += 37
    File.seek(pos)
    raw = File.read()
    File.close()
    image = np.zeros(shape=(sizex,sizey),dtype=np.int32)
    
    image = np.flipud(pf.pack_f(len(raw),raw,sizex,sizey,image).T)  #transpose to get it right way around & flip
    if imageOnly:
        return image
    else:
        return head,data,Npix,image
        
def ProjFileOpen(G2frame):
    'Read a GSAS-II project file and load into the G2 data tree'
    if not os.path.exists(G2frame.GSASprojectfile):
        print ('\n*** Error attempt to open project file that does not exist:\n   '+
               str(G2frame.GSASprojectfile))
        return
    LastSavedUsing = None
    file = open(G2frame.GSASprojectfile,'rb')
    print 'load from file: ',G2frame.GSASprojectfile
    G2frame.SetTitle("GSAS-II data tree: "+
                     os.path.split(G2frame.GSASprojectfile)[1])
    wx.BeginBusyCursor()
    try:
        while True:
            try:
                data = cPickle.load(file)
            except EOFError:
                break
            datum = data[0]
            
            Id = G2frame.PatternTree.AppendItem(parent=G2frame.root,text=datum[0])
            if 'PWDR' in datum[0]:                
                if 'ranId' not in datum[1][0]: # patch: add random Id if not present
                    datum[1][0]['ranId'] = ran.randint(0,sys.maxint)
                G2frame.PatternTree.SetItemPyData(Id,datum[1][:3])  #temp. trim off junk (patch?)
            elif datum[0].startswith('HKLF'): 
                if 'ranId' not in datum[1][0]: # patch: add random Id if not present
                    datum[1][0]['ranId'] = ran.randint(0,sys.maxint)
                G2frame.PatternTree.SetItemPyData(Id,datum[1])
            else:
                G2frame.PatternTree.SetItemPyData(Id,datum[1])             
                if datum[0] == 'Controls' and 'LastSavedUsing' in datum[1]:
                    LastSavedUsing = datum[1]['LastSavedUsing']
                if datum[0] == 'Controls' and 'PythonVersions' in datum[1] and GSASIIpath.GetConfigValue('debug'):
                    print('Packages used to create .GPX file:')
                    if 'dict' in str(type(datum[1]['PythonVersions'])):  #patch
                        for p in sorted(datum[1]['PythonVersions'],key=lambda s: s.lower()):
                            print("{:>14s}: {:s}".format(p[0],p[1]))
                    else:
                        for p in datum[1]['PythonVersions']:
                            print("{:<12s} {:s}".format(p[0]+':',p[1]))
            for datus in data[1:]:
                sub = G2frame.PatternTree.AppendItem(Id,datus[0])
#patch
                if datus[0] == 'Instrument Parameters' and len(datus[1]) == 1:
                    if 'PWDR' in datum[0]:
                        datus[1] = [dict(zip(datus[1][3],zip(datus[1][0],datus[1][1],datus[1][2]))),{}]
                    else:
                        datus[1] = [dict(zip(datus[1][2],zip(datus[1][0],datus[1][1]))),{}]
                    for item in datus[1][0]:               #zip makes tuples - now make lists!
                        datus[1][0][item] = list(datus[1][0][item])
#end patch
                G2frame.PatternTree.SetItemPyData(sub,datus[1])
            if 'IMG' in datum[0]:                   #retrieve image default flag & data if set
                Data = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,Id,'Image Controls'))
                if Data['setDefault']:
                    G2frame.imageDefault = Data                
        file.close()
        if LastSavedUsing:
            print('GPX load successful. Last saved with GSAS-II version '+LastSavedUsing)
        else:
            print('project load successful')
        G2frame.NewPlot = True
    except:
        msg = wx.MessageDialog(G2frame,message="Error reading file "+
            str(G2frame.GSASprojectfile)+". This is not a GSAS-II .gpx file",
            caption="Load Error",style=wx.ICON_ERROR | wx.OK | wx.STAY_ON_TOP)
        msg.ShowModal()
    finally:
        wx.EndBusyCursor()
        G2frame.Status.SetStatusText('To reorder tree items, use mouse RB to drag/drop them')
    
def ProjFileSave(G2frame):
    'Save a GSAS-II project file'
    if not G2frame.PatternTree.IsEmpty():
        file = open(G2frame.GSASprojectfile,'wb')
        print 'save to file: ',G2frame.GSASprojectfile
        # stick the file name into the tree and version info into tree so they are saved.
        # (Controls should always be created at this point)
        try:
            Controls = G2frame.PatternTree.GetItemPyData(
                G2gd.GetPatternTreeItemId(G2frame,G2frame.root, 'Controls'))
            Controls['LastSavedAs'] = os.path.abspath(G2frame.GSASprojectfile)
            Controls['LastSavedUsing'] = str(GSASIIpath.GetVersionNumber())
            Controls['PythonVersions'] = G2frame.PackageVersions
        except:
            pass
        wx.BeginBusyCursor()
        try:
            item, cookie = G2frame.PatternTree.GetFirstChild(G2frame.root)
            while item:
                data = []
                name = G2frame.PatternTree.GetItemText(item)
                data.append([name,G2frame.PatternTree.GetItemPyData(item)])
                item2, cookie2 = G2frame.PatternTree.GetFirstChild(item)
                while item2:
                    name = G2frame.PatternTree.GetItemText(item2)
                    data.append([name,G2frame.PatternTree.GetItemPyData(item2)])
                    item2, cookie2 = G2frame.PatternTree.GetNextChild(item, cookie2)                            
                item, cookie = G2frame.PatternTree.GetNextChild(G2frame.root, cookie)                            
                cPickle.dump(data,file,1)
            file.close()
        finally:
            wx.EndBusyCursor()
        print('project save successful')

def SaveIntegration(G2frame,PickId,data):
    'Save image integration results as powder pattern(s)'
    azms = G2frame.Integrate[1]
    X = G2frame.Integrate[2][:-1]
    N = len(X)
    Id = G2frame.PatternTree.GetItemParent(PickId)
    name = G2frame.PatternTree.GetItemText(Id)
    name = name.replace('IMG ',data['type']+' ')
    Comments = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,Id, 'Comments'))
    if 'PWDR' in name:
        names = ['Type','Lam','Zero','Polariz.','U','V','W','X','Y','SH/L','Azimuth'] 
        codes = [0 for i in range(11)]
    elif 'SASD' in name:
        names = ['Type','Lam','Zero','Azimuth'] 
        codes = [0 for i in range(4)]
        X = 4.*np.pi*npsind(X/2.)/data['wavelength']    #convert to q
    Xminmax = [X[0],X[-1]]
    LRazm = data['LRazimuth']
    Azms = []
    dazm = 0.
    if data['fullIntegrate'] and data['outAzimuths'] == 1:
        Azms = [45.0,]                              #a poor man's average?
    else:
        for i,azm in enumerate(azms[:-1]):
            if azm > 360. and azms[i+1] > 360.:
                Azms.append(G2img.meanAzm(azm%360.,azms[i+1]%360.))
            else:    
                Azms.append(G2img.meanAzm(azm,azms[i+1]))
        dazm = np.min(np.abs(np.diff(azms)))/2.
    G2frame.IntgOutList = []
    for i,azm in enumerate(azms[:-1]):
        Aname = name+" Azm= %.2f"%((azm+dazm)%360.)
        item, cookie = G2frame.PatternTree.GetFirstChild(G2frame.root)
        nOcc = 0
        while item:
            Name = G2frame.PatternTree.GetItemText(item)
            if Aname in Name:
                nOcc += 1
            item, cookie = G2frame.PatternTree.GetNextChild(G2frame.root, cookie)
        if nOcc:
            Aname += '(%d)'%(nOcc)
        Sample = G2pdG.SetDefaultSample()
        Sample['Gonio. radius'] = data['distance']
        Sample['Omega'] = data['GonioAngles'][0]
        Sample['Chi'] = data['GonioAngles'][1]
        Sample['Phi'] = data['GonioAngles'][2]
        Sample['Azimuth'] = (azm+dazm)%360.    #put here as bin center 
        if 'PWDR' in Aname:
            parms = ['PXC',data['wavelength'],0.0,0.99,1.0,-0.10,0.4,0.30,1.0,0.0001,Azms[i]]    #set polarization for synchrotron radiation!
        elif 'SASD' in Aname:
            Sample['Trans'] = data['SampleAbs'][0]
            parms = ['LXC',data['wavelength'],0.0,Azms[i]]
        Y = G2frame.Integrate[0][i]
        W = np.where(Y>0.,1./Y,1.e-6)                    #probably not true
        Id = G2frame.PatternTree.AppendItem(parent=G2frame.root,text=Aname)
        G2frame.IntgOutList.append(Id)
        G2frame.PatternTree.SetItemPyData(G2frame.PatternTree.AppendItem(Id,text='Comments'),Comments)                    
        G2frame.PatternTree.SetItemPyData(G2frame.PatternTree.AppendItem(Id,text='Limits'),[tuple(Xminmax),Xminmax])
        if 'PWDR' in Aname:
            G2frame.PatternTree.SetItemPyData(G2frame.PatternTree.AppendItem(Id,text='Background'),[['chebyschev',1,3,1.0,0.0,0.0],
                {'nDebye':0,'debyeTerms':[],'nPeaks':0,'peaksList':[]}])
        inst = [dict(zip(names,zip(parms,parms,codes))),{}]
        for item in inst[0]:
            inst[0][item] = list(inst[0][item])
        G2frame.PatternTree.SetItemPyData(G2frame.PatternTree.AppendItem(Id,text='Instrument Parameters'),inst)
        if 'PWDR' in Aname:
            G2frame.PatternTree.SetItemPyData(G2frame.PatternTree.AppendItem(Id,text='Sample Parameters'),Sample)
            G2frame.PatternTree.SetItemPyData(G2frame.PatternTree.AppendItem(Id,text='Peak List'),{'sigDict':{},'peaks':[]})
            G2frame.PatternTree.SetItemPyData(G2frame.PatternTree.AppendItem(Id,text='Index Peak List'),[[],[]])
            G2frame.PatternTree.SetItemPyData(G2frame.PatternTree.AppendItem(Id,text='Unit Cells List'),[])
            G2frame.PatternTree.SetItemPyData(G2frame.PatternTree.AppendItem(Id,text='Reflection Lists'),{})
        elif 'SASD' in Aname:             
            G2frame.PatternTree.SetItemPyData(G2frame.PatternTree.AppendItem(Id,text='Substances'),G2pdG.SetDefaultSubstances())
            G2frame.PatternTree.SetItemPyData(G2frame.PatternTree.AppendItem(Id,text='Sample Parameters'),Sample)
            G2frame.PatternTree.SetItemPyData(G2frame.PatternTree.AppendItem(Id,text='Models'),G2pdG.SetDefaultSASDModel())
        valuesdict = {
            'wtFactor':1.0,
            'Dummy':False,
            'ranId':ran.randint(0,sys.maxint),
            'Offset':[0.0,0.0],'delOffset':0.02,'refOffset':-1.0,'refDelt':0.01,
            'qPlot':False,'dPlot':False,'sqrtPlot':False
            }
        G2frame.PatternTree.SetItemPyData(
            Id,[valuesdict,
                [np.array(X),np.array(Y),np.array(W),np.zeros(N),np.zeros(N),np.zeros(N)]])
    return Id       #last powder pattern generated
            
# def powderFxyeSave(G2frame,exports,powderfile):
#     'Save a powder histogram as a GSAS FXYE file'
#     head,tail = ospath.split(powderfile)
#     name,ext = tail.split('.')
#     for i,export in enumerate(exports):
#         filename = ospath.join(head,name+'-%03d.'%(i)+ext)
#         prmname = filename.strip(ext)+'prm'
#         prm = open(prmname,'w')      #old style GSAS parm file
#         PickId = G2gd.GetPatternTreeItemId(G2frame, G2frame.root, export)
#         Inst = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame, \
#             PickId, 'Instrument Parameters'))[0]
#         prm.write( '            123456789012345678901234567890123456789012345678901234567890        '+'\n')
#         prm.write( 'INS   BANK      1                                                               '+'\n')
#         prm.write(('INS   HTYPE   %sR                                                              '+'\n')%(Inst['Type'][0]))
#         if 'Lam1' in Inst:              #Ka1 & Ka2
#             prm.write(('INS  1 ICONS%10.7f%10.7f    0.0000               0.990    0     0.500   '+'\n')%(Inst['Lam1'][0],Inst['Lam2'][0]))
#         elif 'Lam' in Inst:             #single wavelength
#             prm.write(('INS  1 ICONS%10.7f%10.7f    0.0000               0.990    0     0.500   '+'\n')%(Inst['Lam'][1],0.0))
#         prm.write( 'INS  1 IRAD     0                                                               '+'\n')
#         prm.write( 'INS  1I HEAD                                                                    '+'\n')
#         prm.write( 'INS  1I ITYP    0    0.0000  180.0000         1                                 '+'\n')
#         prm.write(('INS  1DETAZM%10.3f                                                          '+'\n')%(Inst['Azimuth'][0]))
#         prm.write( 'INS  1PRCF1     3    8   0.00100                                                '+'\n')
#         prm.write(('INS  1PRCF11     %15.6g%15.6g%15.6g%15.6g   '+'\n')%(Inst['U'][1],Inst['V'][1],Inst['W'][1],0.0))
#         prm.write(('INS  1PRCF12     %15.6g%15.6g%15.6g%15.6g   '+'\n')%(Inst['X'][1],Inst['Y'][1],Inst['SH/L'][1]/2.,Inst['SH/L'][1]/2.))
#         prm.close()
#         file = open(filename,'w')
#         print 'save powder pattern to file: ',filename
#         x,y,w,yc,yb,yd = G2frame.PatternTree.GetItemPyData(PickId)[1]
#         file.write(powderfile+'\n')
#         file.write('Instrument parameter file:'+ospath.split(prmname)[1]+'\n')
#         file.write('BANK 1 %d %d CONS %.2f %.2f 0 0 FXYE\n'%(len(x),len(x),\
#             100.*x[0],100.*(x[1]-x[0])))
#         s = list(np.sqrt(1./np.array(w)))        
#         XYW = zip(x,y,s)
#         for X,Y,S in XYW:
#             file.write("%15.6g %15.6g %15.6g\n" % (100.*X,Y,max(S,1.0)))
#         file.close()
#         print 'powder pattern file '+filename+' written'
        
# def powderXyeSave(G2frame,exports,powderfile):
#     'Save a powder histogram as a Topas XYE file'
#     head,tail = ospath.split(powderfile)
#     name,ext = tail.split('.')
#     for i,export in enumerate(exports):
#         filename = ospath.join(head,name+'-%03d.'%(i)+ext)
#         PickId = G2gd.GetPatternTreeItemId(G2frame, G2frame.root, export)
#         file = open(filename,'w')
#         file.write('#%s\n'%(export))
#         print 'save powder pattern to file: ',filename
#         x,y,w,yc,yb,yd = G2frame.PatternTree.GetItemPyData(PickId)[1]
#         s = list(np.sqrt(1./np.array(w)))        
#         XYW = zip(x,y,s)
#         for X,Y,W in XYW:
#             file.write("%15.6g %15.6g %15.6g\n" % (X,Y,W))
#         file.close()
#         print 'powder pattern file '+filename+' written'
        
def PDFSave(G2frame,exports):
    'Save a PDF G(r) and S(Q) in column formats'
    for export in exports:
        PickId = G2gd.GetPatternTreeItemId(G2frame, G2frame.root, export)
        SQname = 'S(Q)'+export[4:]
        GRname = 'G(R)'+export[4:]
        sqfilename = ospath.join(G2frame.dirname,export.replace(' ','_')[5:]+'.sq')
        grfilename = ospath.join(G2frame.dirname,export.replace(' ','_')[5:]+'.gr')
        sqId = G2gd.GetPatternTreeItemId(G2frame, PickId, SQname)
        grId = G2gd.GetPatternTreeItemId(G2frame, PickId, GRname)
        sqdata = np.array(G2frame.PatternTree.GetItemPyData(sqId)[1][:2]).T
        grdata = np.array(G2frame.PatternTree.GetItemPyData(grId)[1][:2]).T
        sqfile = open(sqfilename,'w')
        grfile = open(grfilename,'w')
        sqfile.write('#T S(Q) %s\n'%(export))
        grfile.write('#T G(R) %s\n'%(export))
        sqfile.write('#L Q     S(Q)\n')
        grfile.write('#L R     G(R)\n')
        for q,sq in sqdata:
            sqfile.write("%15.6g %15.6g\n" % (q,sq))
        sqfile.close()
        for r,gr in grdata:
            grfile.write("%15.6g %15.6g\n" % (r,gr))
        grfile.close()
    
def PeakListSave(G2frame,file,peaks):
    'Save powder peaks to a data file'
    print 'save peak list to file: ',G2frame.peaklistfile
    if not peaks:
        dlg = wx.MessageDialog(G2frame, 'No peaks!', 'Nothing to save!', wx.OK)
        try:
            result = dlg.ShowModal()
        finally:
            dlg.Destroy()
        return
    for peak in peaks:
        file.write("%10.4f %12.2f %10.3f %10.3f \n" % \
            (peak[0],peak[2],peak[4],peak[6]))
    print 'peak list saved'
              
def IndexPeakListSave(G2frame,peaks):
    'Save powder peaks from the indexing list'
    file = open(G2frame.peaklistfile,'wa')
    print 'save index peak list to file: ',G2frame.peaklistfile
    wx.BeginBusyCursor()
    try:
        if not peaks:
            dlg = wx.MessageDialog(G2frame, 'No peaks!', 'Nothing to save!', wx.OK)
            try:
                result = dlg.ShowModal()
            finally:
                dlg.Destroy()
            return
        for peak in peaks:
            file.write("%12.6f\n" % (peak[7]))
        file.close()
    finally:
        wx.EndBusyCursor()
    print 'index peak list saved'
    
def SetNewPhase(Name='New Phase',SGData=None,cell=None,Super=None):
    '''Create a new phase dict with default values for various parameters

    :param str Name: Name for new Phase

    :param dict SGData: space group data from :func:`GSASIIspc:SpcGroup`;
      defaults to data for P 1

    :param list cell: unit cell parameter list; defaults to
      [1.0,1.0,1.0,90.,90,90.,1.]

    '''
    if SGData is None: SGData = G2spc.SpcGroup('P 1')[1]
    if cell is None: cell=[1.0,1.0,1.0,90.,90,90.,1.]
    phaseData = {
        'ranId':ran.randint(0,sys.maxint),
        'General':{
            'Name':Name,
            'Type':'nuclear',
            'AtomPtrs':[3,1,7,9],
            'SGData':SGData,
            'Cell':[False,]+cell,
            'Pawley dmin':1.0,
            'Data plot type':'None',
            'SH Texture':{
                'Order':0,
                'Model':'cylindrical',
                'Sample omega':[False,0.0],
                'Sample chi':[False,0.0],
                'Sample phi':[False,0.0],
                'SH Coeff':[False,{}],
                'SHShow':False,
                'PFhkl':[0,0,1],
                'PFxyz':[0,0,1],
                'PlotType':'Pole figure',
                'Penalty':[['',],0.1,False,1.0]}},
        'Atoms':[],
        'Drawing':{},
        'Histograms':{},
        'Pawley ref':[],
        'RBModels':{},
        }
    if Super and Super.get('Use',False):
        phaseData['General'].update({'Type':'modulated','Super':True,'SuperSg':Super['ssSymb']})
        phaseData['General']['SSGData'] = G2spc.SSpcGroup(SGData,Super['ssSymb'])
        phaseData['General']['SuperVec'] = [Super['ModVec'],False,Super['maxH']]

    return phaseData
       
class MultipleChoicesDialog(wx.Dialog):
    '''A dialog that offers a series of choices, each with a
    title and a wx.Choice widget. Intended to be used Modally. 
    typical input:

        *  choicelist=[ ('a','b','c'), ('test1','test2'),('no choice',)]
        *  headinglist = [ 'select a, b or c', 'select 1 of 2', 'No option here']
        
    selections are placed in self.chosen when OK is pressed
    '''
    def __init__(self,choicelist,headinglist,
                 head='Select options',
                 title='Please select from options below',
                 parent=None):
        self.chosen = []
        wx.Dialog.__init__(
            self,parent,wx.ID_ANY,head, 
            pos=wx.DefaultPosition,style=wx.DEFAULT_DIALOG_STYLE)
        panel = wx.Panel(self)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add((10,10),1)
        topLabl = wx.StaticText(panel,wx.ID_ANY,title)
        mainSizer.Add(topLabl,0,wx.ALIGN_CENTER_VERTICAL|wx.CENTER,10)
        self.ChItems = []
        for choice,lbl in zip(choicelist,headinglist):
            mainSizer.Add((10,10),1)
            self.chosen.append(0)
            topLabl = wx.StaticText(panel,wx.ID_ANY,' '+lbl)
            mainSizer.Add(topLabl,0,wx.ALIGN_LEFT,10)
            self.ChItems.append(wx.Choice(self, wx.ID_ANY, (100, 50), choices = choice))
            mainSizer.Add(self.ChItems[-1],0,wx.ALIGN_CENTER,10)

        OkBtn = wx.Button(panel,-1,"Ok")
        OkBtn.Bind(wx.EVT_BUTTON, self.OnOk)
        cancelBtn = wx.Button(panel,-1,"Cancel")
        cancelBtn.Bind(wx.EVT_BUTTON, self.OnCancel)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20),1)
        btnSizer.Add(OkBtn)
        btnSizer.Add((20,20),1)
        btnSizer.Add(cancelBtn)
        btnSizer.Add((20,20),1)
        mainSizer.Add(btnSizer,0,wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        panel.SetSizer(mainSizer)
        panel.Fit()
        self.Fit()
        
    def OnOk(self,event):
        parent = self.GetParent()
        if parent is not None: parent.Raise()
        # save the results from the choice widgets
        self.chosen = []
        for w in self.ChItems:
            self.chosen.append(w.GetSelection())
        self.EndModal(wx.ID_OK)              
            
    def OnCancel(self,event):
        parent = self.GetParent()
        if parent is not None: parent.Raise()
        self.chosen = []
        self.EndModal(wx.ID_CANCEL)              
            
def ExtractFileFromZip(filename, selection=None, confirmread=True,
                       confirmoverwrite=True, parent=None,
                       multipleselect=False):
    '''If the filename is a zip file, extract a file from that
    archive.

    :param list Selection: used to predefine the name of the file
      to be extracted. Filename case and zip directory name are
      ignored in selection; the first matching file is used.

    :param bool confirmread: if True asks the user to confirm before expanding
      the only file in a zip

    :param bool confirmoverwrite: if True asks the user to confirm
      before overwriting if the extracted file already exists

    :param bool multipleselect: if True allows more than one zip
      file to be extracted, a list of file(s) is returned.
      If only one file is present, do not ask which one, otherwise
      offer a list of choices (unless selection is used).
    
    :returns: the name of the file that has been created or a
      list of files (see multipleselect)

    If the file is not a zipfile, return the name of the input file.
    If the zipfile is empty or no file has been selected, return None
    '''
    import zipfile # do this now, since we can save startup time by doing this only on need
    import shutil
    zloc = os.path.split(filename)[0]
    if not zipfile.is_zipfile(filename):
        #print("not zip")
        return filename

    z = zipfile.ZipFile(filename,'r')
    zinfo = z.infolist()

    if len(zinfo) == 0:
        #print('Zip has no files!')
        zlist = [-1]
    if selection:
        choices = [os.path.split(i.filename)[1].lower() for i in zinfo]
        if selection.lower() in choices:
            zlist = [choices.index(selection.lower())]
        else:
            print('debug: file '+str(selection)+' was not found in '+str(filename))
            zlist = [-1]
    elif len(zinfo) == 1 and confirmread:
        result = wx.ID_NO
        dlg = wx.MessageDialog(
            parent,
            'Is file '+str(zinfo[0].filename)+
            ' what you want to extract from '+
            str(os.path.split(filename)[1])+'?',
            'Confirm file', 
            wx.YES_NO | wx.ICON_QUESTION)
        try:
            result = dlg.ShowModal()
        finally:
            dlg.Destroy()
        if result == wx.ID_NO:
            zlist = [-1]
        else:
            zlist = [0]
    elif len(zinfo) == 1:
        zlist = [0]
    elif multipleselect:
        # select one or more from a from list
        choices = [i.filename for i in zinfo]
        dlg = G2G.G2MultiChoiceDialog(parent,'Select file(s) to extract from zip file '+str(filename),
            'Choose file(s)',choices)
        if dlg.ShowModal() == wx.ID_OK:
            zlist = dlg.GetSelections()
        else:
            zlist = []
        dlg.Destroy()
    else:
        # select one from a from list
        choices = [i.filename for i in zinfo]
        dlg = wx.SingleChoiceDialog(parent,
            'Select file to extract from zip file'+str(filename),'Choose file',
            choices,)
        if dlg.ShowModal() == wx.ID_OK:
            zlist = [dlg.GetSelection()]
        else:
            zlist = [-1]
        dlg.Destroy()
        
    outlist = []
    for zindex in zlist:
        if zindex >= 0:
            efil = os.path.join(zloc, os.path.split(zinfo[zindex].filename)[1])
            if os.path.exists(efil) and confirmoverwrite:
                result = wx.ID_NO
                dlg = wx.MessageDialog(parent,
                    'File '+str(efil)+' already exists. OK to overwrite it?',
                    'Confirm overwrite',wx.YES_NO | wx.ICON_QUESTION)
                try:
                    result = dlg.ShowModal()
                finally:
                    dlg.Destroy()
                if result == wx.ID_NO:
                    zindex = -1
        if zindex >= 0:
            # extract the file to the current directory, regardless of it's original path
            #z.extract(zinfo[zindex],zloc)
            eloc,efil = os.path.split(zinfo[zindex].filename)
            outfile = os.path.join(zloc, efil)
            fpin = z.open(zinfo[zindex])
            fpout = file(outfile, "wb")
            shutil.copyfileobj(fpin, fpout)
            fpin.close()
            fpout.close()
            outlist.append(outfile)
    z.close()
    if multipleselect and len(outlist) >= 1:
        return outlist
    elif len(outlist) == 1:
        return outlist[0]
    else:
        return None

######################################################################
# base classes for reading various types of data files
#   not used directly, only by subclassing
######################################################################
try:
    E,SGData = G2spc.SpcGroup('P 1') # data structure for default space group
except: # errors on doc build
    SGData = None
P1SGData = SGData
class ImportBaseclass(object):
    '''Defines a base class for the reading of input files (diffraction
    data, coordinates,...). See :ref:`Writing a Import Routine<Import_routines>`
    for an explanation on how to use a subclass of this class. 
    '''
    class ImportException(Exception):
        '''Defines an Exception that is used when an import routine hits an expected error,
        usually in .Reader.

        Good practice is that the Reader should define a value in self.errors that
        tells the user some information about what is wrong with their file.         
        '''
        pass

    def __init__(self,
                 formatName,
                 longFormatName=None,
                 extensionlist=[],
                 strictExtension=False,
                 ):
        self.formatName = formatName # short string naming file type
        if longFormatName: # longer string naming file type
            self.longFormatName = longFormatName
        else:
            self.longFormatName = formatName
        # define extensions that are allowed for the file type
        # for windows, remove any extensions that are duplicate, as case is ignored
        if sys.platform == 'windows' and extensionlist:
            extensionlist = list(set([s.lower() for s in extensionlist]))
        self.extensionlist = extensionlist
        # If strictExtension is True, the file will not be read, unless
        # the extension matches one in the extensionlist
        self.strictExtension = strictExtension
        self.errors = ''
        self.warnings = ''
        # used for readers that will use multiple passes to read
        # more than one data block
        self.repeat = False
        self.selections = []
        self.repeatcount = 0
        self.readfilename = '?'
        #print 'created',self.__class__

    def ReInitialize(self):
        'Reinitialize the Reader to initial settings'
        self.errors = ''
        self.warnings = ''
        self.repeat = False
        self.repeatcount = 0
        self.readfilename = '?'

    def BlockSelector(self, ChoiceList, ParentFrame=None,
                      title='Select a block',
                      size=None, header='Block Selector',
                      useCancel=True):
        ''' Provide a wx dialog to select a block if the file contains more
        than one set of data and one must be selected
        '''
        if useCancel:
            dlg = wx.SingleChoiceDialog(
                ParentFrame,title, header,ChoiceList)
        else:
            dlg = wx.SingleChoiceDialog(
                ParentFrame,title, header,ChoiceList,
                style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.OK|wx.CENTRE)
        if size: dlg.SetSize(size)
        dlg.CenterOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            sel = dlg.GetSelection()
            return sel
        else:
            return None
        dlg.Destroy()

    def MultipleBlockSelector(self, ChoiceList, ParentFrame=None,
        title='Select a block',size=None, header='Block Selector'):
        '''Provide a wx dialog to select a block of data if the
        file contains more than one set of data and one must be
        selected.

        :returns: a list of the selected blocks
        '''
        dlg = wx.MultiChoiceDialog(ParentFrame,title, header,ChoiceList+['Select all'],
            wx.CHOICEDLG_STYLE)
        dlg.CenterOnParent()
        if size: dlg.SetSize(size)
        if dlg.ShowModal() == wx.ID_OK:
            sel = dlg.GetSelections()
        else:
            return []
        dlg.Destroy()
        selected = []
        if len(ChoiceList) in sel:
            return range(len(ChoiceList))
        else:
            return sel
        return selected

    def MultipleChoicesDialog(self, choicelist, headinglist, ParentFrame=None, **kwargs):
        '''A modal dialog that offers a series of choices, each with a title and a wx.Choice
        widget. Typical input:
        
           * choicelist=[ ('a','b','c'), ('test1','test2'),('no choice',)]
           
           * headinglist = [ 'select a, b or c', 'select 1 of 2', 'No option here']
           
        optional keyword parameters are: head (window title) and title
        returns a list of selected indicies for each choice (or None)
        '''
        result = None
        dlg = MultipleChoicesDialog(choicelist,headinglist,
            parent=ParentFrame, **kwargs)          
        dlg.CenterOnParent()
        if dlg.ShowModal() == wx.ID_OK:
            result = dlg.chosen
        dlg.Destroy()
        return result

    def ShowBusy(self):
        wx.BeginBusyCursor()
#        wx.Yield() # make it happen now!

    def DoneBusy(self):
        wx.EndBusyCursor()
        wx.Yield() # make it happen now!
        
#    def Reader(self, filename, filepointer, ParentFrame=None, **unused):
#        '''This method must be supplied in the child class to read the file. 
#        if the read fails either return False or raise an Exception
#        preferably of type ImportException. 
#        '''
#        #start reading
#        raise ImportException("Error occurred while...")
#        self.errors += "Hint for user on why the error occur
#        return False # if an error occurs
#        return True # if read OK

    def ExtensionValidator(self, filename):
        '''This methods checks if the file has the correct extension
        Return False if this filename will not be supported by this reader
        Return True if the extension matches the list supplied by the reader
        Return None if the reader allows un-registered extensions
        '''
        if filename:
            ext = os.path.splitext(filename)[1]
            if sys.platform == 'windows': ext = ext.lower()
            if ext in self.extensionlist: return True
            if self.strictExtension: return False
        return None

    def ContentsValidator(self, filepointer):
        '''This routine will attempt to determine if the file can be read
        with the current format.
        This will typically be overridden with a method that 
        takes a quick scan of [some of]
        the file contents to do a "sanity" check if the file
        appears to match the selected format. 
        Expected to be called via self.Validator()
        '''
        #filepointer.seek(0) # rewind the file pointer
        return True

    def CIFValidator(self, filepointer):
        '''A :meth:`ContentsValidator` for use to validate CIF files.
        '''
        for i,l in enumerate(filepointer):
            if i >= 1000: return True
            '''Encountered only blank lines or comments in first 1000
            lines. This is unlikely, but assume it is CIF anyway, since we are
            even less likely to find a file with nothing but hashes and
            blank lines'''
            line = l.strip()
            if len(line) == 0: # ignore blank lines
                continue 
            elif line.startswith('#'): # ignore comments
                continue 
            elif line.startswith('data_'): # on the right track, accept this file
                return True
            else: # found something invalid
                self.errors = 'line '+str(i+1)+' contains unexpected data:\n'
                self.errors += '  '+str(l)
                self.errors += '  Note: a CIF should only have blank lines or comments before'
                self.errors += '        a data_ statement begins a block.'
                return False 

class ImportPhase(ImportBaseclass):
    '''Defines a base class for the reading of files with coordinates

    Objects constructed that subclass this (in import/G2phase_*.py etc.) will be used
    in :meth:`GSASII.GSASII.OnImportPhase`. 
    See :ref:`Writing a Import Routine<Import_Routines>`
    for an explanation on how to use this class. 

    '''
    def __init__(self,formatName,longFormatName=None,extensionlist=[],
        strictExtension=False,):
        # call parent __init__
        ImportBaseclass.__init__(self,formatName,longFormatName,
            extensionlist,strictExtension)
        self.Phase = None # a phase must be created with G2IO.SetNewPhase in the Reader
        self.Constraints = None

    def PhaseSelector(self, ChoiceList, ParentFrame=None,
        title='Select a phase', size=None,header='Phase Selector'):
        ''' Provide a wx dialog to select a phase if the file contains more
        than one phase
        '''
        return self.BlockSelector(ChoiceList,ParentFrame,title,
            size,header)

class ImportStructFactor(ImportBaseclass):
    '''Defines a base class for the reading of files with tables
    of structure factors.

    Structure factors are read with a call to :meth:`GSASII.GSASII.OnImportSfact`
    which in turn calls :meth:`GSASII.GSASII.OnImportGeneric`, which calls
    methods :meth:`ExtensionValidator`, :meth:`ContentsValidator` and
    :meth:`Reader`.

    See :ref:`Writing a Import Routine<Import_Routines>`
    for an explanation on how to use import classes in general. The specifics 
    for reading a structure factor histogram require that
    the ``Reader()`` routine in the import
    class need to do only a few things: It
    should load :attr:`RefDict` item ``'RefList'`` with the reflection list,
    and set :attr:`Parameters` with the instrument parameters
    (initialized with :meth:`InitParameters` and set with :meth:`UpdateParameters`).
    '''
    def __init__(self,formatName,longFormatName=None,extensionlist=[],
        strictExtension=False,):
        ImportBaseclass.__init__(self,formatName,longFormatName,
            extensionlist,strictExtension)

        # define contents of Structure Factor entry
        self.Parameters = []
        'self.Parameters is a list with two dicts for data parameter settings'
        self.InitParameters()
        self.RefDict = {'RefList':[],'FF':{},'Super':0}
        self.Banks = []             #for multi bank data (usually TOF)
        '''self.RefDict is a dict containing the reflection information, as read from the file.
        Item 'RefList' contains the reflection information. See the
        :ref:`Single Crystal Reflection Data Structure<XtalRefl_table>`
        for the contents of each row. Dict element 'FF'
        contains the form factor values for each element type; if this entry
        is left as initialized (an empty list) it will be initialized as needed later. 
        '''
    def ReInitialize(self):
        'Reinitialize the Reader to initial settings'
        ImportBaseclass.ReInitialize(self)
        self.InitParameters()
        self.Banks = []             #for multi bank data (usually TOF)
        self.RefDict = {'RefList':[],'FF':{},'Super':0}
        
    def InitParameters(self):
        'initialize the instrument parameters structure'
        Lambda = 0.70926
        HistType = 'SXC'
        self.Parameters = [{'Type':[HistType,HistType], # create the structure
                            'Lam':[Lambda,Lambda]
                            }, {}]
        'Parameters is a list with two dicts for data parameter settings'

    def UpdateParameters(self,Type=None,Wave=None):
        'Revise the instrument parameters'
        if Type is not None:
            self.Parameters[0]['Type'] = [Type,Type]
        if Wave is not None:
            self.Parameters[0]['Lam'] = [Wave,Wave]           
                       
######################################################################
class ImportPowderData(ImportBaseclass):
    '''Defines a base class for the reading of files with powder data.

    Objects constructed that subclass this (in import/G2pwd_*.py etc.) will be used
    in :meth:`GSASII.GSASII.OnImportPowder`. 
    See :ref:`Writing a Import Routine<Import_Routines>`
    for an explanation on how to use this class. 
    '''
    def __init__(self,
                 formatName,
                 longFormatName=None,
                 extensionlist=[],
                 strictExtension=False,
                 ):
        ImportBaseclass.__init__(self,formatName,
                                            longFormatName,
                                            extensionlist,
                                            strictExtension)
        self.clockWd = None  # used in TOF
        self.ReInitialize()
        
    def ReInitialize(self):
        'Reinitialize the Reader to initial settings'
        ImportBaseclass.ReInitialize(self)
        self.powderentry = ['',None,None] #  (filename,Pos,Bank)
        self.powderdata = [] # Powder dataset
        '''A powder data set is a list with items [x,y,w,yc,yb,yd]:
                np.array(x), # x-axis values
                np.array(y), # powder pattern intensities
                np.array(w), # 1/sig(intensity)^2 values (weights)
                np.array(yc), # calc. intensities (zero)
                np.array(yb), # calc. background (zero)
                np.array(yd), # obs-calc profiles
        '''                            
        self.comments = []
        self.idstring = ''
        self.Sample = G2pdG.SetDefaultSample() # default sample parameters
        self.Controls = {}  # items to be placed in top-level Controls 
        self.GSAS = None     # used in TOF
        self.repeat_instparm = True # Should a parm file be
        #                             used for multiple histograms? 
        self.instparm = None # name hint from file of instparm to use
        self.instfile = '' # full path name to instrument parameter file
        self.instbank = '' # inst parm bank number
        self.instmsg = ''  # a label that gets printed to show
                           # where instrument parameters are from
        self.numbanks = 1
        self.instdict = {} # place items here that will be transferred to the instrument parameters
        self.pwdparms = {} # place parameters that are transferred directly to the tree
                           # here (typically from an existing GPX file)
######################################################################
class ImportSmallAngleData(ImportBaseclass):
    '''Defines a base class for the reading of files with small angle data.
    See :ref:`Writing a Import Routine<Import_Routines>`
    for an explanation on how to use this class. 
    '''
    def __init__(self,formatName,longFormatName=None,extensionlist=[],
        strictExtension=False,):
            
        ImportBaseclass.__init__(self,formatName,longFormatName,extensionlist,
            strictExtension)
        self.ReInitialize()
        
    def ReInitialize(self):
        'Reinitialize the Reader to initial settings'
        ImportBaseclass.ReInitialize(self)
        self.smallangleentry = ['',None,None] #  (filename,Pos,Bank)
        self.smallangledata = [] # SASD dataset
        '''A small angle data set is a list with items [x,y,w,yc,yd]:
                np.array(x), # x-axis values
                np.array(y), # powder pattern intensities
                np.array(w), # 1/sig(intensity)^2 values (weights)
                np.array(yc), # calc. intensities (zero)
                np.array(yd), # obs-calc profiles
                np.array(yb), # preset bkg
        '''                            
        self.comments = []
        self.idstring = ''
        self.Sample = G2pdG.SetDefaultSample()
        self.GSAS = None     # used in TOF
        self.clockWd = None  # used in TOF
        self.numbanks = 1
        self.instdict = {} # place items here that will be transferred to the instrument parameters

######################################################################
class ImportImage(ImportBaseclass):
    '''Defines a base class for the reading of images

    Images are read in only these places:
    
      * Initial reading is typically done from a menu item
        with a call to :meth:`GSASII.GSASII.OnImportImage`
        which in turn calls :meth:`GSASII.GSASII.OnImportGeneric`. That calls
        methods :meth:`ExtensionValidator`, :meth:`ContentsValidator` and
        :meth:`Reader`. This returns a list of reader objects for each read image. 

      * Images are read alternatively in :func:`GSASIIIO.ReadImages`, which puts image info
        directly into the data tree.

      * Images are reloaded with :func:`GSASIIIO.GetImageData`.

    .. _Image_import_routines:

    When reading an image, the ``Reader()`` routine in the ImportImage class
    should set:
    
      * :attr:`Comments`: a list of strings (str),
      * :attr:`Npix`: the number of pixels in the image (int),
      * :attr:`Image`: the actual image as a numpy array (np.array)
      * :attr:`Data`: a dict defining image parameters (dict). Within this dict the following
        data items are needed:
        
         * 'pixelSize': size of each pixel in microns (such as ``[200,200]``.
         * 'wavelength': wavelength in Angstoms.
         * 'distance': distance of detector from sample in cm.
         * 'center': uncalibrated center of beam on detector (such as ``[204.8,204.8]``.
         * 'size': size of image (such as ``[2048,2048]``).
         * 'ImageTag': image number or other keyword used to retrieve image from
           a multi-image data file (defaults to ``1`` if not specified).

    optional data items:
    
      * :attr:`repeat`: set to True if there are additional images to
        read in the file, False otherwise
      * :attr:`repeatcount`: set to the number of the image.
      
    Note that the above is initialized with :meth:`InitParameters`.
    (Also see :ref:`Writing a Import Routine<Import_Routines>`
    for an explanation on how to use import classes in general.)
    '''
    def __init__(self,formatName,longFormatName=None,extensionlist=[],
        strictExtension=False,):
        ImportBaseclass.__init__(self,formatName,longFormatName,
            extensionlist,strictExtension)
        self.InitParameters()
        
    def ReInitialize(self):
        'Reinitialize the Reader to initial settings -- not used at present'
        ImportBaseclass.ReInitialize(self)
        self.InitParameters()
        
    def InitParameters(self):
        'initialize the instrument parameters structure'
        self.Comments = ['No comments']
        self.Data = {}
        self.Npix = 0
        self.Image = None
        self.repeat = False
        self.repeatcount = 1

    def LoadImage(self,ParentFrame,imagefile,imagetag=None):
        '''Optionally, call this after reading in an image to load it into the tree.
        This saves time by preventing a reread of the same information.
        '''
        if ParentFrame:
            ParentFrame.ImageZ = self.Image   # store the image for plotting
            ParentFrame.oldImagefile = imagefile # save the name of the last image file read
            ParentFrame.oldImageTag = imagetag   # save the tag of the last image file read            

######################################################################
class ExportBaseclass(object):
    '''Defines a base class for the exporting of GSAS-II results.

    This class is subclassed in the various exports/G2export_*.py files. Those files
    are imported in :meth:`GSASII.GSASII._init_Exports` which defines the
    appropriate menu items for each one and the .Exporter method is called
    directly from the menu item.

    Routines may also define a .Writer method, which is used to write a single
    file without invoking any GUI objects.
    '''
    def __init__(self,
                 G2frame,
                 formatName,
                 extension,
                 longFormatName=None,
                 ):
        self.G2frame = G2frame
        self.formatName = formatName # short string naming file type
        self.extension = extension
        if longFormatName: # longer string naming file type
            self.longFormatName = longFormatName
        else:
            self.longFormatName = formatName
        self.OverallParms = {}
        self.Phases = {}
        self.Histograms = {}
        self.powderDict = {}
        self.xtalDict = {}
        self.parmDict = {}
        self.sigDict = {}
        # updated in InitExport:
        self.currentExportType = None # type of export that has been requested
        # updated in ExportSelect (when used):
        self.phasenam = None # a list of selected phases
        self.histnam = None # a list of selected histograms
        self.filename = None # name of file to be written (single export) or template (multiple files)
        self.dirname = '' # name of directory where file(s) will be written
        self.fullpath = '' # name of file being written -- full path
        
        # items that should be defined in a subclass of this class
        self.exporttype = []  # defines the type(s) of exports that the class can handle.
        # The following types are defined: 'project', "phase", "powder", "single"
        self.multiple = False # set as True if the class can export multiple phases or histograms
        # self.multiple is ignored for "project" exports

    def InitExport(self,event):
        '''Determines the type of menu that called the Exporter and
        misc initialization. 
        '''
        self.filename = None # name of file to be written (single export)
        self.dirname = '' # name of file to be written (multiple export)
        if event:
            self.currentExportType = self.G2frame.ExportLookup.get(event.Id)

    def MakePWDRfilename(self,hist):
        '''Make a filename root (no extension) from a PWDR histogram name

        :param str hist: the histogram name in data tree (starts with "PWDR ")
        '''
        file0 = ''
        file1 = hist[5:]
        # replace repeated blanks
        while file1 != file0:
            file0 = file1
            file1 = file0.replace('  ',' ').strip()
        file0 = file1.replace('Azm= ','A')
        # if angle has unneeded decimal places on aziumuth, remove them
        if file0[-3:] == '.00': file0 = file0[:-3]
        file0 = file0.replace('.','_')
        file0 = file0.replace(' ','_')
        return file0

    def ExportSelect(self,AskFile='ask'):
        '''Selects histograms or phases when needed. Sets a default file name when
        requested in self.filename; always sets a default directory in self.dirname.

        :param bool AskFile: Determines how this routine processes getting a
          location to store the current export(s).
          
          * if AskFile is 'ask' (default option), get the name of the file to be written;
            self.filename and self.dirname are always set. In the case where
            multiple files must be generated, the export routine should do this
            based on self.filename as a template.
          * if AskFile is 'dir', get the name of the directory to be used;
            self.filename is not used, but self.dirname is always set. The export routine
            will always generate the file name.
          * if AskFile is 'single', get only the name of the directory to be used when
            multiple items will be written (as multiple files) are used
            *or* a complete file name is requested when a single file
            name is selected. self.dirname is always set and self.filename used
            only when a single file is selected.
          * if AskFile is 'default', creates a name of the file to be used from
            the name of the project (.gpx) file. If the project has not been saved,
            then the name of file is requested.
            self.filename and self.dirname are always set. In the case where
            multiple file names must be generated, the export routine should do this
            based on self.filename.
          * if AskFile is 'default-dir', sets self.dirname from the project (.gpx)
            file. If the project has not been saved, then a directory is requested.
            self.filename is not used.

        :returns: True in case of an error
        '''
        
        numselected = 1
        if self.currentExportType == 'phase':
            if len(self.Phases) == 0:
                self.G2frame.ErrorDialog(
                    'Empty project',
                    'Project does not contain any phases.')
                return True
            elif len(self.Phases) == 1:
                self.phasenam = self.Phases.keys()
            elif self.multiple: 
                choices = sorted(self.Phases.keys())
                phasenum = G2G.ItemSelector(choices,self.G2frame,multiple=True)
                if phasenum is None: return True
                self.phasenam = [choices[i] for i in phasenum]
                if not self.phasenam: return True
                numselected = len(self.phasenam)
            else:
                choices = sorted(self.Phases.keys())
                phasenum = G2G.ItemSelector(choices,self.G2frame)
                if phasenum is None: return True
                self.phasenam = [choices[phasenum]]
                numselected = len(self.phasenam)
        elif self.currentExportType == 'single':
            if len(self.xtalDict) == 0:
                self.G2frame.ErrorDialog(
                    'Empty project',
                    'Project does not contain any single crystal data.')
                return True
            elif len(self.xtalDict) == 1:
                self.histnam = self.xtalDict.values()
            elif self.multiple:
                choices = sorted(self.xtalDict.values())
                hnum = G2G.ItemSelector(choices,self.G2frame,multiple=True)
                if not hnum: return True
                self.histnam = [choices[i] for i in hnum]
                numselected = len(self.histnam)
            else:
                choices = sorted(self.xtalDict.values())
                hnum = G2G.ItemSelector(choices,self.G2frame)
                if hnum is None: return True
                self.histnam = [choices[hnum]]
                numselected = len(self.histnam)
        elif self.currentExportType == 'powder':
            if len(self.powderDict) == 0:
                self.G2frame.ErrorDialog(
                    'Empty project',
                    'Project does not contain any powder data.')
                return True
            elif len(self.powderDict) == 1:
                self.histnam = self.powderDict.values()
            elif self.multiple:
                choices = sorted(self.powderDict.values())
                hnum = G2G.ItemSelector(choices,self.G2frame,multiple=True)
                if not hnum: return True
                self.histnam = [choices[i] for i in hnum]
                numselected = len(self.histnam)
            else:
                choices = sorted(self.powderDict.values())
                hnum = G2G.ItemSelector(choices,self.G2frame)
                if hnum is None: return True
                self.histnam = [choices[hnum]]
                numselected = len(self.histnam)
        elif self.currentExportType == 'image':
            if len(self.Histograms) == 0:
                self.G2frame.ErrorDialog(
                    'Empty project',
                    'Project does not contain any images.')
                return True
            elif len(self.Histograms) == 1:
                self.histnam = self.Histograms.keys()
            else:
                choices = sorted(self.Histograms.keys())
                hnum = G2G.ItemSelector(choices,self.G2frame,multiple=self.multiple)
                if self.multiple:
                    if not hnum: return True
                    self.histnam = [choices[i] for i in hnum]
                else:
                    if hnum is None: return True
                    self.histnam = [choices[hnum]]
                numselected = len(self.histnam)
        if self.currentExportType == 'map':
            # search for phases with maps
            mapPhases = []
            choices = []
            for phasenam in sorted(self.Phases):
                phasedict = self.Phases[phasenam] # pointer to current phase info            
                if len(phasedict['General']['Map'].get('rho',[])):
                    mapPhases.append(phasenam)
                    if phasedict['General']['Map'].get('Flip'):
                        choices.append('Charge flip map: '+str(phasenam))
                    elif phasedict['General']['Map'].get('MapType'):
                        choices.append(
                            str(phasedict['General']['Map'].get('MapType'))
                            + ' map: ' + str(phasenam))
                    else:
                        choices.append('unknown map: '+str(phasenam))
            # select a map if needed
            if len(mapPhases) == 0:
                self.G2frame.ErrorDialog(
                    'Empty project',
                    'Project does not contain any maps.')
                return True
            elif len(mapPhases) == 1:
                self.phasenam = mapPhases
            else: 
                phasenum = G2G.ItemSelector(choices,self.G2frame,multiple=self.multiple)
                if self.multiple:
                    if not phasenum: return True
                    self.phasenam = [mapPhases[i] for i in phasenum]
                else:
                    if phasenum is None: return True
                    self.phasenam = [mapPhases[phasenum]]
            numselected = len(self.phasenam)

        # items selected, now set self.dirname and usually self.filename 
        if AskFile == 'ask' or (AskFile == 'single' and numselected == 1) or (
            AskFile == 'default' and not self.G2frame.GSASprojectfile
            ):
            filename = self.askSaveFile()
            if not filename: return True
            self.dirname,self.filename = os.path.split(filename)
        elif AskFile == 'dir' or AskFile == 'single' or (
            AskFile == 'default-dir' and not self.G2frame.GSASprojectfile
            ):
            self.dirname = self.askSaveDirectory()
            if not self.dirname: return True
        elif AskFile == 'default-dir' or AskFile == 'default':
            self.dirname,self.filename = os.path.split(
                os.path.splitext(self.G2frame.GSASprojectfile)[0] + self.extension
                )
        else:
            raise Exception('This should not happen!')
        
    def loadParmDict(self):
        '''Load the GSAS-II refinable parameters from the tree into a dict (self.parmDict). Update
        refined values to those from the last cycle and set the uncertainties for the
        refined parameters in another dict (self.sigDict).

        Expands the parm & sig dicts to include values derived from constraints.
        '''
        self.parmDict = {}
        self.sigDict = {}
        rigidbodyDict = {}
        covDict = {}
        consDict = {}
        Histograms,Phases = self.G2frame.GetUsedHistogramsAndPhasesfromTree()
        if self.G2frame.PatternTree.IsEmpty(): return # nothing to do
        item, cookie = self.G2frame.PatternTree.GetFirstChild(self.G2frame.root)
        while item:
            name = self.G2frame.PatternTree.GetItemText(item)
            if name == 'Rigid bodies':
                 rigidbodyDict = self.G2frame.PatternTree.GetItemPyData(item)
            elif name == 'Covariance':
                 covDict = self.G2frame.PatternTree.GetItemPyData(item)
            elif name == 'Constraints':
                 consDict = self.G2frame.PatternTree.GetItemPyData(item)
            item, cookie = self.G2frame.PatternTree.GetNextChild(self.G2frame.root, cookie)
        rbVary,rbDict =  G2stIO.GetRigidBodyModels(rigidbodyDict,Print=False)
        self.parmDict.update(rbDict)
        rbIds = rigidbodyDict.get('RBIds',{'Vector':[],'Residue':[]})
        Natoms,atomIndx,phaseVary,phaseDict,pawleyLookup,FFtables,BLtables,maxSSwave =  G2stIO.GetPhaseData(
            Phases,RestraintDict=None,rbIds=rbIds,Print=False)
        self.parmDict.update(phaseDict)
        hapVary,hapDict,controlDict =  G2stIO.GetHistogramPhaseData(
            Phases,Histograms,Print=False,resetRefList=False)
        self.parmDict.update(hapDict)
        histVary,histDict,controlDict =  G2stIO.GetHistogramData(Histograms,Print=False)
        self.parmDict.update(histDict)
        self.parmDict.update(zip(
            covDict.get('varyList',[]),
            covDict.get('variables',[])))
        self.sigDict = dict(zip(
            covDict.get('varyList',[]),
            covDict.get('sig',[])))
        # expand to include constraints: first compile a list of constraints
        constList = []
        for item in consDict:
            if item.startswith('_'): continue
            constList += consDict[item]
        # now process the constraints
        G2mv.InitVars()
        constDict,fixedList,ignored = G2stIO.ProcessConstraints(constList)
        varyList = covDict.get('varyListStart')
        if varyList is None and len(constDict) == 0:
            # no constraints can use varyList
            varyList = covDict.get('varyList')
        elif varyList is None:
            # old GPX file from before pre-constraint varyList is saved
            print ' *** Old refinement: Please use Calculate/Refine to redo  ***'
            raise Exception(' *** Export aborted ***')
        else:
            varyList = list(varyList)
        try:
            groups,parmlist = G2mv.GroupConstraints(constDict)
            G2mv.GenerateConstraints(groups,parmlist,varyList,constDict,fixedList,self.parmDict)
        except:
            # this really should not happen
            print ' *** ERROR - constraints are internally inconsistent ***'
            errmsg, warnmsg = G2mv.CheckConstraints(varyList,constDict,fixedList)
            print 'Errors',errmsg
            if warnmsg: print 'Warnings',warnmsg
            raise Exception(' *** CIF creation aborted ***')
        # add the constrained values to the parameter dictionary
        G2mv.Dict2Map(self.parmDict,varyList)
        # and add their uncertainties into the esd dictionary (sigDict)
        if covDict.get('covMatrix') is not None:
            self.sigDict.update(G2mv.ComputeDepESD(covDict['covMatrix'],covDict['varyList'],self.parmDict))

    def loadTree(self):
        '''Load the contents of the data tree into a set of dicts
        (self.OverallParms, self.Phases and self.Histogram as well as self.powderDict
        & self.xtalDict)
        
        * The childrenless data tree items are overall parameters/controls for the
          entire project and are placed in self.OverallParms
        * Phase items are placed in self.Phases
        * Data items are placed in self.Histogram. The key for these data items
          begin with a keyword, such as PWDR, IMG, HKLF,... that identifies the data type.
        '''
        self.OverallParms = {}
        self.powderDict = {}
        self.xtalDict = {}
        self.Phases = {}
        self.Histograms = {}
        if self.G2frame.PatternTree.IsEmpty(): return # nothing to do
        histType = None        
        if self.currentExportType == 'phase':
            # if exporting phases load them here
            sub = G2gd.GetPatternTreeItemId(self.G2frame,self.G2frame.root,'Phases')
            if not sub:
                print 'no phases found'
                return True
            item, cookie = self.G2frame.PatternTree.GetFirstChild(sub)
            while item:
                phaseName = self.G2frame.PatternTree.GetItemText(item)
                self.Phases[phaseName] =  self.G2frame.PatternTree.GetItemPyData(item)
                item, cookie = self.G2frame.PatternTree.GetNextChild(sub, cookie)
            return
        elif self.currentExportType == 'single':
            histType = 'HKLF'
        elif self.currentExportType == 'powder':
            histType = 'PWDR'
        elif self.currentExportType == 'image':
            histType = 'IMG'

        if histType: # Loading just one kind of tree entry
            item, cookie = self.G2frame.PatternTree.GetFirstChild(self.G2frame.root)
            while item:
                name = self.G2frame.PatternTree.GetItemText(item)
                if name.startswith(histType):
                    if self.Histograms.get(name): # there is already an item with this name
                        print('Histogram name '+str(name)+' is repeated. Renaming')
                        if name[-1] == '9':
                            name = name[:-1] + '10'
                        elif name[-1] in '012345678':
                            name = name[:-1] + str(int(name[-1])+1)
                        else:                            
                            name += '-1'
                    self.Histograms[name] = {}
                    # the main info goes into Data, but the 0th
                    # element contains refinement results, carry
                    # that over too now. 
                    self.Histograms[name]['Data'] = self.G2frame.PatternTree.GetItemPyData(item)[1]
                    self.Histograms[name][0] = self.G2frame.PatternTree.GetItemPyData(item)[0]
                    item2, cookie2 = self.G2frame.PatternTree.GetFirstChild(item)
                    while item2: 
                        child = self.G2frame.PatternTree.GetItemText(item2)
                        self.Histograms[name][child] = self.G2frame.PatternTree.GetItemPyData(item2)
                        item2, cookie2 = self.G2frame.PatternTree.GetNextChild(item, cookie2)
                item, cookie = self.G2frame.PatternTree.GetNextChild(self.G2frame.root, cookie)
            # index powder and single crystal histograms by number
            for hist in self.Histograms:
                if hist.startswith("PWDR"): 
                    d = self.powderDict
                elif hist.startswith("HKLF"): 
                    d = self.xtalDict
                else:
                    return                    
                i = self.Histograms[hist].get('hId')
                if i is None and not d.keys():
                    i = 0
                elif i is None or i in d.keys():
                    i = max(d.keys())+1
                d[i] = hist
            return
        # else standard load: using all interlinked phases and histograms
        self.Histograms,self.Phases = self.G2frame.GetUsedHistogramsAndPhasesfromTree()
        item, cookie = self.G2frame.PatternTree.GetFirstChild(self.G2frame.root)
        while item:
            name = self.G2frame.PatternTree.GetItemText(item)
            item2, cookie2 = self.G2frame.PatternTree.GetFirstChild(item)
            if not item2: 
                self.OverallParms[name] = self.G2frame.PatternTree.GetItemPyData(item)
            item, cookie = self.G2frame.PatternTree.GetNextChild(self.G2frame.root, cookie)
        # index powder and single crystal histograms
        for hist in self.Histograms:
            i = self.Histograms[hist]['hId']
            if hist.startswith("PWDR"): 
                self.powderDict[i] = hist
            elif hist.startswith("HKLF"): 
                self.xtalDict[i] = hist

    def dumpTree(self,mode='type'):
        '''Print out information on the data tree dicts loaded in loadTree
        '''
        print '\nOverall'
        if mode == 'type':
            def Show(arg): return type(arg)
        else:
            def Show(arg): return arg
        for key in self.OverallParms:
            print '  ',key,Show(self.OverallParms[key])
        print 'Phases'
        for key1 in self.Phases:
            print '    ',key1,Show(self.Phases[key1])
        print 'Histogram'
        for key1 in self.Histograms:
            print '    ',key1,Show(self.Histograms[key1])
            for key2 in self.Histograms[key1]:
                print '      ',key2,Show(self.Histograms[key1][key2])

    def defaultSaveFile(self):
        return os.path.abspath(
            os.path.splitext(self.G2frame.GSASprojectfile
                             )[0]+self.extension)
        
    def askSaveFile(self):
        '''Ask the user to supply a file name

        :returns: a file name (str) or None if Cancel is pressed
        '''
        defnam = os.path.splitext(
            os.path.split(self.G2frame.GSASprojectfile)[1]
            )[0]+self.extension
        dlg = wx.FileDialog(
            self.G2frame, 'Input name for file to write', '.', defnam,
            self.longFormatName+' (*'+self.extension+')|*'+self.extension,
            wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT|wx.CHANGE_DIR)
        dlg.CenterOnParent()
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                # make sure extension is correct
                filename = os.path.splitext(filename)[0]+self.extension
            else:
                filename = None
        finally:
            dlg.Destroy()
        return filename

    def askSaveDirectory(self):
        '''Ask the user to supply a directory name. Path name is used as the
        starting point for the next export path search. 

        :returns: a directory name (str) or None if Cancel is pressed
        '''
        if self.G2frame.exportDir:
            startdir = self.G2frame.exportDir
        elif self.G2frame.GSASprojectfile:
            startdir = os.path.split(self.G2frame.GSASprojectfile)[0]
        elif self.G2frame.dirname:
            startdir = self.G2frame.dirname
        else:
            startdir = ''
        dlg = wx.DirDialog(
            self.G2frame, 'Input directory where file(s) will be written', startdir,
            wx.DD_DEFAULT_STYLE)
        dlg.CenterOnParent()
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                self.G2frame.exportDir = filename
            else:
                filename = None
        finally:
            dlg.Destroy()
        return filename

    # Tools for file writing. 
    def OpenFile(self,fil=None,mode='w'):
        '''Open the output file

        :param str fil: The name of the file to open. If None (default)
          the name defaults to self.dirname + self.filename.
          If an extension is supplied, it is not overridded,
          but if not, the default extension is used. 
        :returns: the file object opened by the routine which is also
          saved as self.fp
        '''
        if not fil:
            if not os.path.splitext(self.filename)[1]:
                self.filename += self.extension
            fil = os.path.join(self.dirname,self.filename)
        self.fullpath = os.path.abspath(fil)
        self.fp = open(self.fullpath,mode)
        return self.fp

    def Write(self,line):
        '''write a line of output, attaching a line-end character

        :param str line: the text to be written. 
        '''
        self.fp.write(line+'\n')
    def CloseFile(self,fp=None):
        '''Close a file opened in OpenFile

        :param file fp: the file object to be closed. If None (default)
          file object self.fp is closed. 
        '''
        if fp is None:
            fp = self.fp
            self.fp = None
        fp.close()
    # Tools to pull information out of the data arrays
    def GetCell(self,phasenam):
        """Gets the unit cell parameters and their s.u.'s for a selected phase

        :param str phasenam: the name for the selected phase
        :returns: `cellList,cellSig` where each is a 7 element list corresponding
          to a, b, c, alpha, beta, gamma, volume where `cellList` has the
          cell values and `cellSig` has their uncertainties.
        """
        phasedict = self.Phases[phasenam] # pointer to current phase info
        try:
            pfx = str(phasedict['pId'])+'::'
            A,sigA = G2stIO.cellFill(pfx,phasedict['General']['SGData'],self.parmDict,self.sigDict)
            cellSig = G2stIO.getCellEsd(pfx,phasedict['General']['SGData'],A,
                self.OverallParms['Covariance'])  # returns 7 vals, includes sigVol
            cellList = G2lat.A2cell(A) + (G2lat.calc_V(A),)
            return cellList,cellSig
        except KeyError:
            cell = phasedict['General']['Cell'][1:]
            return cell,7*[0]
    
    def GetAtoms(self,phasenam):
        """Gets the atoms associated with a phase. Can be used with standard
        or macromolecular phases

        :param str phasenam: the name for the selected phase
        :returns: a list of items for eac atom where each item is a list containing:
          label, typ, mult, xyz, and td, where

          * label and typ are the atom label and the scattering factor type (str)
          * mult is the site multiplicity (int)
          * xyz is contains a list with four pairs of numbers:
            x, y, z and fractional occupancy and
            their standard uncertainty (or a negative value)
          * td is contains a list with either one or six pairs of numbers:
            if one number it is U\ :sub:`iso` and with six numbers it is
            U\ :sub:`11`, U\ :sub:`22`, U\ :sub:`33`, U\ :sub:`12`, U\ :sub:`13` & U\ :sub:`23`
            paired with their standard uncertainty (or a negative value)
        """
        phasedict = self.Phases[phasenam] # pointer to current phase info            
        cx,ct,cs,cia = phasedict['General']['AtomPtrs']
        cfrac = cx+3
        fpfx = str(phasedict['pId'])+'::Afrac:'        
        atomslist = []
        for i,at in enumerate(phasedict['Atoms']):
            if phasedict['General']['Type'] == 'macromolecular':
                label = '%s_%s_%s_%s'%(at[ct-1],at[ct-3],at[ct-4],at[ct-2])
            else:
                label = at[ct-1]
            fval = self.parmDict.get(fpfx+str(i),at[cfrac])
            fsig = self.sigDict.get(fpfx+str(i),-0.009)
            mult = at[cs+1]
            typ = at[ct]
            xyz = []
            for j,v in enumerate(('x','y','z')):
                val = at[cx+j]
                pfx = str(phasedict['pId'])+'::dA'+v+':'+str(i)
                sig = self.sigDict.get(pfx,-0.000009)
                xyz.append((val,sig))
            xyz.append((fval,fsig))
            td = []
            if at[cia] == 'I':
                pfx = str(phasedict['pId'])+'::AUiso:'+str(i)
                val = self.parmDict.get(pfx,at[cia+1])
                sig = self.sigDict.get(pfx,-0.0009)
                td.append((val,sig))
            else:
                for i,var in enumerate(('AU11','AU22','AU33','AU12','AU13','AU23')):
                    pfx = str(phasedict['pId'])+'::'+var+':'+str(i)
                    val = self.parmDict.get(pfx,at[cia+2+i])
                    sig = self.sigDict.get(pfx,-0.0009)
                    td.append((val,sig))
            atomslist.append((label,typ,mult,xyz,td))
        return atomslist
######################################################################
def ExportPowderList(G2frame):
    '''Returns a list of extensions supported by :func:`GSASIIIO:ExportPowder`
    
    :param wx.Frame G2frame: the GSAS-II main data tree window
    '''
    extList = []
    for obj in G2frame.exporterlist:
        if 'powder' in obj.exporttype:
            try:
                obj.Writer
                extList.append(obj.extension)
            except AttributeError:
                pass
    return extList

def ExportPowder(G2frame,TreeName,fileroot,extension):
    '''Writes a single powder histogram using the Export routines

    :param wx.Frame G2frame: the GSAS-II main data tree window
    :param str TreeName: the name of the histogram (PWDR ...) in the data tree
    :param str fileroot: name for file to be written, extension ignored
    :param str extension: extension for file to be written (start with '.'). Must
      match a powder export routine that has a Writer object. 
    '''
    filename = os.path.abspath(os.path.splitext(fileroot)[0]+extension)
    for obj in G2frame.exporterlist:
        if obj.extension == extension and 'powder' in obj.exporttype:
            obj.currentExportType = 'powder'
            obj.InitExport(None)
            obj.loadTree() # load all histograms in tree into dicts
            if TreeName not in obj.Histograms:
                raise Exception('Histogram not found: '+str(TreeName))
            try:
                obj.Writer
            except AttributeError:
                continue
            try:
                obj.Writer(TreeName,filename)
                return
            except Exception,err:
                print('Export Routine for '+extension+' failed.')
                print err
    else:
        print('No Export routine supports extension '+extension)

def ReadCIF(URLorFile):
    '''Open a CIF, which may be specified as a file name or as a URL using PyCifRW
    (from James Hester).
    The open routine gets confused with DOS names that begin with a letter and colon
    "C:\dir\" so this routine will try to open the passed name as a file and if that
    fails, try it as a URL

    :param str URLorFile: string containing a URL or a file name. Code will try first
      to open it as a file and then as a URL.

    :returns: a PyCifRW CIF object.
    '''
    import CifFile as cif # PyCifRW from James Hester

    # alternate approach:
    #import urllib
    #ciffile = 'file:'+urllib.pathname2url(filename)
   
    try:
        fp = open(URLorFile,'r')
        cf = cif.ReadCif(fp)
        fp.close()
        return cf
    except IOError:
        return cif.ReadCif(URLorFile)

if __name__ == '__main__':
    app = wx.PySimpleApp()
    frm = wx.Frame(None) # create a frame
    frm.Show(True)
    filename = '/tmp/notzip.zip'
    filename = '/tmp/all.zip'
    #filename = '/tmp/11bmb_7652.zip'
    
    #selection=None, confirmoverwrite=True, parent=None
    #print ExtractFileFromZip(filename, selection='11bmb_7652.fxye',parent=frm)
    print ExtractFileFromZip(filename,multipleselect=True)
                             #confirmread=False, confirmoverwrite=False)

    # choicelist=[ ('a','b','c'),
    #              ('test1','test2'),('no choice',)]
    # titles = [ 'a, b or c', 'tests', 'No option here']
    # dlg = MultipleChoicesDialog(
    #     choicelist,titles,
    #     parent=frm)
    # if dlg.ShowModal() == wx.ID_OK:
    #     print 'Got OK'
