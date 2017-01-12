# -*- coding: utf-8 -*-
#GSASII - image data display routines
########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### SVN repository information ###################
'''
*GSASIIimgGUI: Image GUI*
-------------------------

Control image display and processing

'''
import os
import copy
import glob
import re
import math
import sys
import wx
import wx.lib.scrolledpanel as wxscroll
import wx.lib.mixins.listctrl  as  listmix
import matplotlib as mpl
import numpy as np
import GSASIIpath
GSASIIpath.SetVersionNumber("$Revision$")
import GSASIIimage as G2img
import GSASIImath as G2mth
import GSASIIplot as G2plt
import GSASIIIO as G2IO
import GSASIIgrid as G2gd
import GSASIIctrls as G2G
import GSASIIpy3 as G2py3

VERY_LIGHT_GREY = wx.Colour(235,235,235)
WACV = wx.ALIGN_CENTER_VERTICAL

# trig functions in degrees
sind = lambda x: math.sin(x*math.pi/180.)
tand = lambda x: math.tan(x*math.pi/180.)
cosd = lambda x: math.cos(x*math.pi/180.)
asind = lambda x: 180.*math.asin(x)/math.pi
    
################################################################################
##### Image Data
################################################################################

def GetImageZ(G2frame,data,newRange=False):
    '''Gets image & applies dark, background & flat background corrections
    :param wx.Frame G2frame: main GSAS-II frame
    param: dict data: Image Controls dictionary
    return: array sumImg: corrected image for background/dark/flat back
    '''
    
    Npix,imagefile,imagetag = G2IO.GetCheckImageFile(G2frame,G2frame.Image)
    formatName = data.get('formatName','')
    sumImg = G2IO.GetImageData(G2frame,imagefile,True,ImageTag=imagetag,FormatName=formatName)
    if sumImg is None:
        return []
    if not 'dark image' in data:
        return sumImg
    darkImg,darkScale = data['dark image']
    if darkImg:
        Did = G2gd.GetPatternTreeItemId(G2frame, G2frame.root, darkImg)
        if Did:
            Ddata = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,Did,'Image Controls'))
            dformatName = Ddata.get('formatName','')
            Npix,darkfile,imagetag = G2IO.GetCheckImageFile(G2frame,Did)
            darkImage = G2IO.GetImageData(G2frame,darkfile,True,ImageTag=imagetag,FormatName=dformatName)
            if darkImg is not None:                
                sumImg += np.array(darkImage*darkScale,dtype='int32')
    if not 'background image' in data:
        return sumImg
    backImg,backScale = data['background image']            
    if backImg:     #ignores any transmission effect in the background image
        Bid = G2gd.GetPatternTreeItemId(G2frame, G2frame.root, backImg)
        if Bid:
            Npix,backfile,imagetag = G2IO.GetCheckImageFile(G2frame,Bid)
            Bdata = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,Bid,'Image Controls'))
            bformatName = Bdata.get('formatName','')
            backImage = G2IO.GetImageData(G2frame,backfile,True,ImageTag=imagetag,FormatName=bformatName)
            if darkImg and backImage is not None:
                Did = G2gd.GetPatternTreeItemId(G2frame, G2frame.root,darkImg)
                if Did:
                    Ddata = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,Did,'Image Controls'))
                    dformatName = Ddata.get('formatName','')
                    Npix,darkfile,imagetag = G2IO.GetCheckImageFile(G2frame,Did)
                    darkImage = G2IO.GetImageData(G2frame,darkfile,True,ImageTag=imagetag,FormatName=dformatName)
                    if darkImage is not None:
                        backImage += np.array(darkImage*darkScale,dtype='int32')
            if backImage is not None:
                sumImg += np.array(backImage*backScale,dtype='int32')
    if darkImg: del darkImg         #force cleanup
    if backImg: del backImg
    sumImg -= int(data.get('Flat Bkg',0))
    Imax = np.max(sumImg)
    if 'range' not in data or newRange:
        data['range'] = [(0,Imax),[0,Imax]]
    return sumImg

def UpdateImageData(G2frame,data):
    
    def OnPixVal(invalid,value,tc):
        G2plt.PlotExposedImage(G2frame,newPlot=True,event=tc.event)
        
    if G2frame.dataDisplay:
        G2frame.dataDisplay.Destroy()
    if not G2frame.dataFrame.GetStatusBar():
        G2frame.dataFrame.CreateStatusBar()
    G2frame.dataDisplay = wx.Panel(G2frame.dataFrame)
    G2frame.ImageZ = GetImageZ(G2frame,data)
    mainSizer = wx.BoxSizer(wx.VERTICAL)
    mainSizer.Add(wx.StaticText(G2frame.dataDisplay,
        label='Do not change anything here unless you are absolutely sure!'),0,WACV)
    mainSizer.Add(wx.StaticText(G2frame.dataDisplay,label=' Image size: %d by %d'%(data['size'][0],data['size'][1])),0,WACV)
    pixSize = wx.FlexGridSizer(0,4,5,5)
    pixLabels = [u' Pixel X-dimension (\xb5m)',u' Pixel Y-dimension (\xb5m)']
    for i,[pixLabel,pix] in enumerate(zip(pixLabels,data['pixelSize'])):
        pixSize.Add(wx.StaticText(G2frame.dataDisplay,label=pixLabel),0,WACV)
        pixVal = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data['pixelSize'],i,nDig=(10,3),
            typeHint=float,OnLeave=OnPixVal)
        pixSize.Add(pixVal,0,WACV)
    mainSizer.Add(pixSize,0)
    
    mainSizer.Layout()    
    G2frame.dataDisplay.SetSizer(mainSizer)
    fitSize = mainSizer.Fit(G2frame.dataFrame)
    G2frame.dataFrame.setSizePosLeft(fitSize)

################################################################################
##### Image Controls
################################################################################                    
def UpdateImageControls(G2frame,data,masks,IntegrateOnly=False):
    '''Shows and handles the controls on the "Image Controls"
    data tree entry
    '''
    import ImageCalibrants as calFile
#patch
    if 'Flat Bkg' not in data:
        data['Flat Bkg'] = 0.0
    if 'GonioAngles' not in data:
        data['GonioAngles'] = [0.,0.,0.]
    if 'DetDepth' not in data:
        data['DetDepth'] = 0.
    if 'SampleAbs' not in data:
        data['SampleShape'] = 'Cylinder'
        data['SampleAbs'] = [0.0,False]
    if 'binType' not in data:
        if 'PWDR' in data['type']:
            data['binType'] = '2-theta'
        elif 'SASD' in data['type']:
            data['binType'] = 'log(q)'
    if 'varyList' not in data:
        data['varyList'] = {'dist':True,'det-X':True,'det-Y':True,'tilt':True,'phi':True,'dep':False,'wave':False}
#end patch

# Menu items
            
    def OnCalibrate(event):
        G2frame.dataFrame.GetStatusBar().SetStatusText('Select > 4 points on 1st used ring; LB to pick, RB on point to delete else RB to finish')
        G2frame.ifGetRing = True
                
    def OnRecalibrate(event):
        G2img.ImageRecalibrate(G2frame,data,masks)
        wx.CallLater(100,UpdateImageControls,G2frame,data,masks)
        
    def OnRecalibAll(event):
        Names = G2gd.GetPatternTreeDataNames(G2frame,['IMG ',])
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Image calibration controls','Select images to recalibrate:',Names)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                items = dlg.GetSelections()
                G2frame.EnablePlot = False
                for item in items:
                    name = Names[item]
                    print 'calibrating',name
                    G2frame.Image = G2gd.GetPatternTreeItemId(G2frame,G2frame.root,name)
                    CId = G2gd.GetPatternTreeItemId(G2frame,G2frame.Image,'Image Controls')
                    Data = G2frame.PatternTree.GetItemPyData(CId)
                    G2frame.ImageZ = GetImageZ(G2frame,Data)
                    Data['setRings'] = True
                    Mid = G2gd.GetPatternTreeItemId(G2frame,G2frame.Image,'Masks')
                    Masks = G2frame.PatternTree.GetItemPyData(Mid)
                    G2img.ImageRecalibrate(G2frame,Data,Masks)
        finally:
            dlg.Destroy()
        G2plt.PlotExposedImage(G2frame,event=None)
        wx.CallLater(100,UpdateImageControls,G2frame,data,masks)
        
    def OnClearCalib(event):
        data['ring'] = []
        data['rings'] = []
        data['ellipses'] = []
        G2plt.PlotExposedImage(G2frame,event=event)
            
    def ResetThresholds():
        Imin = max(0.,np.min(G2frame.ImageZ))
        Imax = np.max(G2frame.ImageZ)
        data['range'] = [(0,Imax),[Imin,Imax]]
        masks['Thresholds'] = [(0,Imax),[Imin,Imax]]
        MaxSizer.GetChildren()[2].Window.SetValue(Imax)   #tricky 
        MaxSizer.GetChildren()[5].Window.SetValue(Imin)   #tricky
         
    def OnIntegrate(event):
        '''Integrate image in response to a menu event or from the AutoIntegrate
        dialog. In the latter case, event=None. 
        '''
        CleanupMasks(masks)
        blkSize = 128   #this seems to be optimal; will break in polymask if >1024
        Nx,Ny = data['size']
        nXBlks = (Nx-1)/blkSize+1
        nYBlks = (Ny-1)/blkSize+1
        Nup = nXBlks*nYBlks*3+1     #exact count expected so AUTO_HIDE works!
        sumImg = GetImageZ(G2frame,data)
        if IntegrateOnly:
            G2frame.Integrate = G2img.ImageIntegrate(sumImg,data,masks,blkSize,
                wx.ProgressDialog("Elapsed time","2D image integration\nPress Cancel to pause after current image",
                Nup,style = wx.PD_ELAPSED_TIME|wx.PD_AUTO_HIDE|wx.PD_CAN_ABORT))            
        else:
            G2frame.Integrate = G2img.ImageIntegrate(sumImg,data,masks,blkSize,
                wx.ProgressDialog("Elapsed time","2D image integration",Nup,
                style = wx.PD_ELAPSED_TIME|wx.PD_AUTO_HIDE))
        G2frame.PauseIntegration = G2frame.Integrate[-1]
        del sumImg  #force cleanup
        Id = G2IO.SaveIntegration(G2frame,G2frame.PickId,data,(event is None))
        G2frame.PatternId = Id
        G2frame.PatternTree.SelectItem(Id)
        G2frame.PatternTree.Expand(Id)
        for item in G2frame.MakePDF: item.Enable(True)
        
    def OnIntegrateAll(event):
        Names = G2gd.GetPatternTreeDataNames(G2frame,['IMG ',])
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Image integration controls','Select images to integrate:',Names)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                items = dlg.GetSelections()
                G2frame.EnablePlot = False
                for item in items:
                    name = Names[item]
                    G2frame.Image = G2gd.GetPatternTreeItemId(G2frame,G2frame.root,name)
                    CId = G2gd.GetPatternTreeItemId(G2frame,G2frame.Image,'Image Controls')
                    Data = G2frame.PatternTree.GetItemPyData(CId)
                    blkSize = 128   #this seems to be optimal; will break in polymask if >1024
                    Nx,Ny = Data['size']
                    nXBlks = (Nx-1)/blkSize+1
                    nYBlks = (Ny-1)/blkSize+1
                    Nup = nXBlks*nYBlks*3+3
                    image = GetImageZ(G2frame,Data)
                    Masks = G2frame.PatternTree.GetItemPyData(
                        G2gd.GetPatternTreeItemId(G2frame,G2frame.Image,'Masks'))
                    image = GetImageZ(G2frame,Data)
                    G2frame.Integrate = G2img.ImageIntegrate(image,Data,Masks,blkSize,
                        wx.ProgressDialog("Elapsed time","2D image integration",Nup,
                        style = wx.PD_ELAPSED_TIME|wx.PD_AUTO_HIDE|wx.PD_CAN_ABORT))
                    del image   #force cleanup
                    pId = G2IO.SaveIntegration(G2frame,CId,Data)
                    if G2frame.Integrate[-1]:       #Cancel from progress bar?
                        break
                else:
                    G2frame.EnablePlot = True
                    G2frame.PatternTree.SelectItem(pId)
                    G2frame.PatternTree.Expand(pId)
                    G2frame.PatternId = pId
        finally:
            dlg.Destroy()
        
    def OnCopyControls(event):
        Names = G2gd.GetPatternTreeDataNames(G2frame,['IMG ',])
        if len(Names) == 1:
            G2frame.ErrorDialog('Nothing to copy controls to','There must be more than one "IMG" pattern')
            return
        Source = G2frame.PatternTree.GetItemText(G2frame.Image)
        Names.pop(Names.index(Source))
# select targets & do copy
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Copy image controls','Copy controls from '+Source+' to:',Names)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                items = dlg.GetSelections()
                G2frame.EnablePlot = False
                for item in items:
                    name = Names[item]
                    Id = G2gd.GetPatternTreeItemId(G2frame,G2frame.root,name)
                    CId = G2gd.GetPatternTreeItemId(G2frame,Id,'Image Controls')
                    oldData = copy.deepcopy(G2frame.PatternTree.GetItemPyData(CId))
                    Data = copy.deepcopy(data)
                    Data['range'][0] = oldData['range'][0]
                    Data['size'] = oldData['size']
                    Data['GonioAngles'] = oldData.get('GonioAngles', [0.,0.,0.])
                    Data['ring'] = []
                    Data['rings'] = []
                    Data['ellipses'] = []
                    if name == Data['dark image'][0]:
                        Data['dark image'] = ['',-1.]
                    if name == Data['background image'][0]:
                        Data['background image'] = ['',-1.]
                    G2frame.PatternTree.SetItemPyData(G2gd.GetPatternTreeItemId(G2frame,Id, 'Image Controls'),Data)
        finally:
            dlg.Destroy()
            G2frame.PatternTree.SelectItem(G2frame.PickId)
            
    def OnCopySelected(event):
        Names = G2gd.GetPatternTreeDataNames(G2frame,['IMG ',])
        if len(Names) == 1:
            G2frame.ErrorDialog('Nothing to copy controls to','There must be more than one "IMG" pattern')
            return
        Source = G2frame.PatternTree.GetItemText(G2frame.Image)
        # Assemble a list of item labels
        keyList = ['type','wavelength','calibrant','distance','center',
                    'tilt','rotation','azmthOff','fullIntegrate','LRazimuth',
                    'IOtth','outChannels','outAzimuths','invert_x','invert_y','DetDepth',
                    'calibskip','pixLimit','cutoff','calibdmin','Flat Bkg','varyList',
                    'binType','SampleShape','PolaVal','SampleAbs','dark image','background image']
        keyText = [i+'='+str(data[i]) for i in keyList]
        # sort both lists together, ordered by keyText
        selectedKeys = []
        dlg = G2G.G2MultiChoiceDialog(
            G2frame.dataFrame,
            'Select which image controls\nto copy',
            'Select image controls', keyText)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                selectedKeys = [keyList[i] for i in dlg.GetSelections()]
        finally:
            dlg.Destroy()
        if not selectedKeys: return # nothing to copy
        copyDict = {}
        for parm in selectedKeys:
            copyDict[parm] = data[parm]
        dlg = G2G.G2MultiChoiceDialog(
            G2frame.dataFrame,
            'Copy image controls from\n'+Source+' to...',
            'Copy image controls', Names)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                result = dlg.GetSelections()
                for i in result: 
                    item = Names[i]
                    Id = G2gd.GetPatternTreeItemId(G2frame,G2frame.root,item)
                    Controls = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,Id,'Image Controls'))
                    Controls.update(copy.deepcopy(copyDict))
        finally:
            dlg.Destroy()            
                
    def OnSaveControls(event):
        pth = G2G.GetExportPath(G2frame)
        dlg = wx.FileDialog(G2frame, 'Choose image controls file', pth, '', 
            'image control files (*.imctrl)|*.imctrl',wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                # make sure extension is .imctrl
                filename = os.path.splitext(filename)[0]+'.imctrl'
                WriteControls(filename,data)
        finally:
            dlg.Destroy()

    def WriteControls(filename,data):
        File = open(filename,'w')
        keys = ['type','wavelength','calibrant','distance','center',
            'tilt','rotation','azmthOff','fullIntegrate','LRazimuth',
            'IOtth','outChannels','outAzimuths','invert_x','invert_y','DetDepth',
            'calibskip','pixLimit','cutoff','calibdmin','Flat Bkg','varyList',
            'binType','SampleShape','PolaVal','SampleAbs','dark image','background image']
        for key in keys:
            if key not in data:     #uncalibrated!
                continue
            File.write(key+':'+str(data[key])+'\n')
        File.close()
        
    def OnSaveMultiControls(event):
        '''Save controls from multiple images
        '''
        imglist = []
        item, cookie = G2frame.PatternTree.GetFirstChild(G2frame.root)
        while item:
            name = G2frame.PatternTree.GetItemText(item)
            if name.startswith('IMG '): 
                imglist.append(name)                
            item, cookie = G2frame.PatternTree.GetNextChild(G2frame.root, cookie)
        if not imglist:
            print('No images!')
            return
        dlg = G2G.G2MultiChoiceDialog(G2frame, 'Which images to select?',
                                      'Select images', imglist, wx.CHOICEDLG_STYLE)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                treeEntries = [imglist[i] for i in dlg.GetSelections()]
        finally:
            dlg.Destroy()
        if not treeEntries:
            print('No images selected!')
            return
        pth = G2G.GetExportPath(G2frame)
        dlg = wx.DirDialog(
            G2frame, 'Select directory for output files',pth,wx.DD_DEFAULT_STYLE)
        dlg.CenterOnParent()
        outdir = None
        try:
            if dlg.ShowModal() == wx.ID_OK:
                outdir = dlg.GetPath()
        finally:
            dlg.Destroy()
        if not outdir:
            print('No directory')
            return
        for img in treeEntries:
            item = G2gd.GetPatternTreeItemId(G2frame,G2frame.root,img)
            data = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(
                G2frame,item,'Image Controls'))
            Npix,imagefile,imagetag = G2frame.PatternTree.GetImageLoc(item)
            filename = os.path.join(outdir,
                                    os.path.splitext(os.path.split(imagefile)[1])[0]
                                    + '.imctrl')
            print('writing '+filename)
            WriteControls(filename,data)
            
    def OnLoadControls(event):
        cntlList = ['wavelength','distance','tilt','invert_x','invert_y','type',
            'fullIntegrate','outChannels','outAzimuths','LRazimuth','IOtth','azmthOff','DetDepth',
            'calibskip','pixLimit','cutoff','calibdmin','Flat Bkg','varyList',
            'PolaVal','SampleAbs','dark image','background image']
        pth = G2G.GetImportPath(G2frame)
        if not pth: pth = '.'
        dlg = wx.FileDialog(G2frame, 'Choose image controls file', pth, '', 
            'image control files (*.imctrl)|*.imctrl',wx.OPEN)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                File = open(filename,'r')
                save = {}
                S = File.readline()
                while S:
                    if S[0] == '#':
                        S = File.readline()
                        continue
                    [key,val] = S.strip().split(':',1)
                    if key in ['type','calibrant','binType','SampleShape',]:    #strings
                        save[key] = val
                    elif key in ['varyList',]:
                        save[key] = eval(val)   #dictionary
                    elif key in ['rotation']:
                        save[key] = float(val)
                    elif key in ['center',]:
                        if ',' in val:
                            save[key] = eval(val)
                        else:
                            vals = val.strip('[] ').split()
                            save[key] = [float(vals[0]),float(vals[1])] 
                    elif key in cntlList:
                        save[key] = eval(val)
                    S = File.readline()
                data.update(save)
                # next line removed. Previous updates tree contents. The next
                # makes a copy of data, puts it into tree and "disconnects" data
                # from tree contents (later changes to data are lost!)
                #G2frame.PatternTree.SetItemPyData(G2gd.GetPatternTreeItemId(G2frame,G2frame.Image, 'Image Controls'),copy.deepcopy(data))
                File.close()
        finally:
            dlg.Destroy()
        G2frame.ImageZ = GetImageZ(G2frame,data)
        ResetThresholds()
        G2plt.PlotExposedImage(G2frame,event=event)
        wx.CallLater(100,UpdateImageControls,G2frame,data,masks)
        
    def OnTransferAngles(event):
        '''Sets the integration range for the selected Images based on the difference in detector distance
        '''
        Names = G2gd.GetPatternTreeDataNames(G2frame,['IMG ',])
        if len(Names) == 1:
            G2frame.ErrorDialog('Nothing images to transfer integration angles to','Need more "IMG"s')
            return
        Source = G2frame.PatternTree.GetItemText(G2frame.Image)
        Names.pop(Names.index(Source))
# select targets & do copy
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Xfer angles','Transfer integration range from '+Source+' to:',Names)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                xferAng = lambda tth,dist1,dist2: asind(dist1 * sind(tth) / dist2)
                items = dlg.GetSelections()
                G2frame.EnablePlot = False
                Id = G2gd.GetPatternTreeItemId(G2frame,G2frame.root,Source)
                data = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,Id,'Image Controls'))
                ttmin0,ttmax0 = data['IOtth']
                dist0 = data['distance']
                print 'distance =',dist0,' integration range: ',data['IOtth']
                for item in items:
                    name = Names[item]
                    Id = G2gd.GetPatternTreeItemId(G2frame,G2frame.root,name)
                    data = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,Id,'Image Controls'))
                    dist1 = data['distance']
                    data['IOtth'] = [xferAng(ttmin0,dist0,dist1),xferAng(ttmax0,dist0,dist1)]
                    print 'distance =',dist1,' integration range: ',data['IOtth']
        finally:
            dlg.Destroy()
            G2frame.PatternTree.SelectItem(G2frame.PickId)        
            
# Sizers
    Indx = {}                                    
    def ComboSizer():

        def OnDataType(event):
            data['type'] = typeSel.GetValue()[:4]
            if 'SASD' in data['type']:
                data['SampleAbs'][0] = np.exp(-data['SampleAbs'][0]) #switch from muT to trans!
                if data['binType'] == '2-theta': data['binType'] = 'log(q)'  #switch default bin type
            elif 'PWDR' in data['type']:
                data['SampleAbs'][0] = -np.log(data['SampleAbs'][0])  #switch from trans to muT!
                if data['binType'] == 'log(q)': data['binType'] = '2-theta'  #switch default bin type                 
            wx.CallLater(100,UpdateImageControls,G2frame,data,masks)
    
        def OnNewColorBar(event):
            data['color'] = colSel.GetValue()
            wx.CallAfter(G2plt.PlotExposedImage,G2frame,event=event)
        
        def OnAzmthOff(invalid,value,tc):
            wx.CallAfter(G2plt.PlotExposedImage,G2frame,event=tc.event)
        
        comboSizer = wx.BoxSizer(wx.HORIZONTAL)
        comboSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' Type of image data: '),0,WACV)
        typeSel = wx.ComboBox(parent=G2frame.dataDisplay,value=typeDict[data['type']],choices=typeList,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        typeSel.SetValue(data['type'])
        typeSel.Bind(wx.EVT_COMBOBOX, OnDataType)
        comboSizer.Add(typeSel,0,WACV)
        comboSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' Color bar '),0,WACV)
        colSel = wx.ComboBox(parent=G2frame.dataDisplay,value=data['color'],choices=colorList,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        colSel.Bind(wx.EVT_COMBOBOX, OnNewColorBar)
        comboSizer.Add(colSel,0,WACV)
        comboSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' Azimuth offset '),0,WACV)
        azmthOff = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data,'azmthOff',nDig=(10,2),
            typeHint=float,OnLeave=OnAzmthOff)
        comboSizer.Add(azmthOff,0,WACV)
        return comboSizer
        
    def MaxSizer():
        '''Defines a sizer with sliders and TextCtrl widgets for controlling the colormap
        for the image, as well as callback routines. 
        '''
        def OnNewVal(invalid,value,tc):
            '''Called when a Imax or Imin value is typed into a Validated TextCrtl (which puts
            the value into the data['range'] nested list).
            This adjusts the slider positions to match the current values
            '''
            scaleSel.SetSelection(len(scaleChoices)-1)
            r11 = min(max(Range[1][1],Range[1][0]+1),Range[0][1]) # keep values in range
            if r11 != Range[1][1]:
                Range[1][1] = r11
                maxVal.SetValue(int(Range[1][1]))
            r10 = max(min(Range[1][0],Range[1][1]-1),Range[0][0])
            if r10 != Range[1][0]:
                Range[1][0] = r10
                minVal.SetValue(int(Range[1][0]))
            sqrtDeltZero = math.sqrt(max(1.0,Range[0][1]-max(0.0,Range[1][0])-1)) # sqrt(Imax0-Imin-1)
            sqrtDeltOne  = math.sqrt(max(1.0,Range[1][1]-max(0.0,Range[1][0])-1)) # sqrt(Imax-Imin-1)
            sv1 = min(100,max(0,int(0.5+100.*sqrtDeltOne/sqrtDeltZero)))
            maxSel.SetValue(sv1)
            DeltOne  = max(1.0,Range[1][1]-max(0.0,Range[0][0])-1)
            sv0 = min(100,max(0,int(0.5+100.*(Range[1][0]-Range[0][0])/DeltOne)))
            minSel.SetValue(sv0)
            new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('2D Powder Image','mpl',newImage=False)
            Page.ImgObj.set_clim([Range[1][0],Range[1][1]])
            if mplOld:
                Page.canvas.draw()
            else:
                Page.canvas.draw_idle()
            
        G2frame.prevMaxValue = None    
        def OnMaxSlider(event):
            val = maxSel.GetValue()
            if G2frame.prevMaxValue == val: return # if this val has been processed, no need to repeat
            scaleSel.SetSelection(len(scaleChoices)-1)
            G2frame.prevMaxValue = val
            sqrtDeltZero = math.sqrt(max(1.0,Range[0][1]-max(0.0,Range[1][0])-1)) # sqrt(Imax0-Imin-1)
            Range[1][1] = int(0.5 + (val * sqrtDeltZero / 100.)**2 + Range[1][0] + 1)
            maxVal.SetValue(int(0.5+Range[1][1]))
            DeltOne  = max(1.0,Range[1][1]-max(0.0,Range[0][0])-1)
            minSel.SetValue(int(0.5 + 100*(Range[1][0]/DeltOne)))
            sv0 = min(100,max(0,int(0.5+100.*(Range[1][0]-Range[0][0])/DeltOne)))
            minSel.SetValue(sv0)
            new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('2D Powder Image','mpl',newImage=False)
            Page.ImgObj.set_clim([Range[1][0],Range[1][1]])
            if mplOld:
                Page.canvas.draw()
            else:
                Page.canvas.draw_idle()
            
        G2frame.prevMinValue = None    
        def OnMinSlider(event):
            val = minSel.GetValue()
            scaleSel.SetSelection(len(scaleChoices)-1)
            if G2frame.prevMinValue == val: return # if this val has been processed, no need to repeat
            G2frame.prevMinValue = val
            DeltOne  = max(1.0,Range[1][1]-max(0.0,Range[0][0])-1) # Imax-Imin0-1
            Range[1][0] = max(0,int(0.5 + val * DeltOne / 100 + Range[0][0]))
            minVal.SetValue(int(Range[1][0]))
            sqrtDeltZero = math.sqrt(max(1.0,Range[0][1]-max(0.0,Range[1][0])-1)) # sqrt(Imax0-Imin-1)
            sqrtDeltOne  = math.sqrt(max(1.0,Range[1][1]-max(0.0,Range[1][0])-1)) # sqrt(Imax-Imin-1)
            sv1 = min(100,max(0,int(0.5+100.*sqrtDeltOne/sqrtDeltZero)))
            maxSel.SetValue(sv1)
            new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('2D Powder Image','mpl',newImage=False)
            Page.ImgObj.set_clim([Range[1][0],Range[1][1]])
            if mplOld:
                Page.canvas.draw()
            else:
                Page.canvas.draw_idle()
            
        def OnAutoSet(event):
            '''Responds to a button labeled 95%, etc; Sets the Imax and Imin values
            for the image so that 95% (etc.) of pixels are inside the color map limits.
            An equal number of pixels are dropped at the minimum and maximum levels.
            '''
            try:
                val = int(event.GetEventObject().GetStringSelection()[:-1])
                margin = (100-val)/2.
            except:
                margin = 0
                event.GetEventObject().SetSelection(0)
            new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('2D Powder Image','mpl',newImage=False)
            if margin == 0:
                Range[1] = list(Range[0])
            else:
                Range[1][0] = int(np.percentile(Page.ImgObj.get_array().compressed(),margin))
                Range[1][1] = int(np.percentile(Page.ImgObj.get_array().compressed(),100-margin))
            sqrtDeltZero = math.sqrt(max(1.0,Range[0][1]-max(0.0,Range[1][0])-1)) # sqrt(Imax0-Imin-1)
            sqrtDeltOne  = math.sqrt(max(1.0,Range[1][1]-max(0.0,Range[1][0])-1)) # sqrt(Imax-Imin-1)
            sv1 = min(100,max(0,int(0.5+100.*sqrtDeltOne/sqrtDeltZero)))
            maxSel.SetValue(sv1)
            DeltOne  = max(1.0,Range[1][1]-max(0.0,Range[0][0])-1)
            sv0 = min(100,max(0,int(0.5+100.*(Range[1][0]-Range[0][0])/DeltOne)))
            minSel.SetValue(sv0)
            minVal.SetValue(int(Range[1][0]))
            maxVal.SetValue(int(Range[1][1]))
            new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('2D Powder Image','mpl',newImage=False)
            Page.ImgObj.set_clim([Range[1][0],Range[1][1]])
            if mplOld:
                Page.canvas.draw()
            else:
                Page.canvas.draw_idle()

        mplv = mpl.__version__.split('.')
        mplOld = mplv[0] == '1' and int(mplv[1]) < 4 # use draw_idle for newer matplotlib versions
        # Plot color scaling uses limits as below:
        #   (Imin0, Imax0) => Range[0] = data['range'][0] # lowest to highest pixel intensity
        #   [Imin, Imax] => Range[1] = data['range'][1] #   lowest to highest pixel intensity on cmap scale
        maxSizer = wx.GridBagSizer(0,0)
        r = c = 0
        maxSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' Max intensity'),(r,c))
        c += 1
        # maxSel is a slider with 101 steps scaled from Imin+1 to Imax0 with sqrt scaling
        # slider value = sv = 100 * sqrt((Imax-Imin-1)/(Imax0-Imin-1))
        # Imax = (sv * sqrt(Imax0-Imin-1) / 100)**2 + Imin + 1
        sqrtDeltZero = math.sqrt(max(1.0,Range[0][1]-max(0.0,Range[1][0])-1)) # sqrt(Imax0-Imin-1)
        sqrtDeltOne  = math.sqrt(max(1.0,Range[1][1]-max(0.0,Range[1][0])-1)) # sqrt(Imax-Imin-1)
        sv1 = min(100,max(0,int(0.5+100.*sqrtDeltOne/sqrtDeltZero)))
        maxSel = wx.Slider(parent=G2frame.dataDisplay,style=wx.SL_HORIZONTAL,value=sv1,size=(300,-1))
        maxSizer.Add(maxSel,(r,c),flag=wx.EXPAND)
        maxSizer.AddGrowableCol(c)
        c += 1
        maxSel.Bind(wx.EVT_SLIDER, OnMaxSlider)
        maxVal = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,Range[1],1,min=Range[0][0]+1,
            max=Range[0][1],typeHint=int,OnLeave=OnNewVal)
        maxSizer.Add(maxVal,(r,c))
        c += 1
        scaleChoices = ("100%","99%","95%","90%","80%","?")
        scaleSel = wx.Choice(G2frame.dataDisplay,choices=scaleChoices,size=(-1,-1))
        if (Range[1][0] == Range[0][0] and
            Range[1][1] == Range[0][1]):
            scaleSel.SetSelection(0)
        else:
            scaleSel.SetSelection(len(scaleChoices)-1)
        scaleSel.Bind(wx.EVT_CHOICE,OnAutoSet)
        maxSizer.Add(scaleSel,(r,c),(2,1),flag=wx.ALIGN_CENTER)
        c = 0
        r = 1
        maxSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' Min intensity'),(r,c))
        c += 1
        # minSel is a slider with 101 steps scaled from Imin0 to Imax-1 with linear scaling
        # slider value = sv0 = 100 * (Imin-Imin0)/(Imax-Imin0-1)
        # Imin = sv0 * (Imax-Imin0-1) / 100 + Imin0
        DeltOne  = max(1.0,Range[1][1]-max(0.0,Range[0][0])-1) # Imax-Imin0-1
        sv0 = min(100,max(0,int(0.5+100.*(Range[1][0]-Range[0][0])/DeltOne)))
        minSel = wx.Slider(parent=G2frame.dataDisplay,style=wx.SL_HORIZONTAL,value=sv0,size=(300,-1))
        maxSizer.Add(minSel,(r,c),flag=wx.EXPAND|wx.ALL)
        c += 1
        minSel.Bind(wx.EVT_SLIDER, OnMinSlider)
        minVal = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,Range[1],0,
            max=Range[0][1],typeHint=int,OnLeave=OnNewVal)
        maxSizer.Add(minVal,(r,c))
        return maxSizer
        
    def CalibCoeffSizer():
        
        def OnCalRef(event):
            Obj = event.GetEventObject()
            name = Indx[Obj]
            data['varyList'][name] = Obj.GetValue()
            
        calibSizer = wx.FlexGridSizer(0,2,5,5)
        calibSizer.SetFlexibleDirection(wx.HORIZONTAL)
        calibSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' Calibration coefficients'),0,WACV)    
        calibSizer.Add((5,0),0)
        Names = ['det-X','det-Y','wave','dist','tilt','phi']
        if 'PWDR' in data['type']:
            Names.append('dep') 
        Parms = {'dist':['Distance',(10,3),data,'distance'],'det-X':['Beam center X',(10,3),data['center'],0],
            'det-Y':['Beam center Y',(10,3),data['center'],1],'tilt':['Tilt angle',(10,3),data,'tilt'],
            'phi':['Tilt rotation',(10,2),data,'rotation'],'dep':['Penetration',(10,2),data,'DetDepth'],
            'wave':['Wavelength',(10,6),data,'wavelength']}
        for name in Names:
            calSel = wx.CheckBox(parent=G2frame.dataDisplay,label=Parms[name][0])
            calibSizer.Add(calSel,0,WACV)
            calSel.Bind(wx.EVT_CHECKBOX, OnCalRef)
            calSel.SetValue(data['varyList'][name])
            Indx[calSel] = name
            if name == 'wave':
                calVal = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,Parms[name][2],
                    Parms[name][3],min=0.01,max=10.,nDig=Parms[name][1],typeHint=float)
            else:
                calVal = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,Parms[name][2],
                    Parms[name][3],nDig=Parms[name][1],typeHint=float)
            calibSizer.Add(calVal,0,WACV)
        return calibSizer
    
    def IntegrateSizer():
        
        def OnNewBinType(event):
            data['binType'] = binSel.GetValue()
            wx.CallLater(100,UpdateImageControls,G2frame,data,masks)
        
        def OnIOtth(invalid,value,tc):
            Ltth = float(G2frame.InnerTth.GetValue())
            Utth = float(G2frame.OuterTth.GetValue())
            if Ltth > Utth:
                Ltth,Utth = Utth,Ltth
            if 'Q' in data['binType']:
                data['IOtth'] = [2.*asind(Ltth*wave/(4.*math.pi)),2.*asind(Utth*wave/(4.*math.pi))]
            else:
                data['IOtth'] = [Ltth,Utth]
            G2frame.InnerTth.SetValue(Ltth)
            G2frame.OuterTth.SetValue(Utth)
            wx.CallAfter(G2plt.PlotExposedImage,G2frame,event=tc.event)
        
        def OnLRazim(invalid,value,tc):
            Lazm = float(G2frame.Lazim.GetValue())%360.
            Razm = float(G2frame.Razim.GetValue())%360.
            if Lazm > Razm:
                Razm += 360.
            if data['fullIntegrate']:
                Razm = Lazm+360.
            G2frame.Lazim.SetValue(Lazm)
            G2frame.Razim.SetValue(Razm)
            data['LRazimuth'] = [Lazm,Razm]
            wx.CallAfter(G2plt.PlotExposedImage,G2frame,event=tc.event)
                
        def OnNumOutAzms(invalid,value,tc):
            wx.CallAfter(G2plt.PlotExposedImage,G2frame,event=tc.event)
        
        def OnOblique(event):
            data['Oblique'][1] = not data['Oblique'][1]
                
        def OnSampleShape(event):
            data['SampleShape'] = samShape.GetValue()
            if 'Cylind' in data['SampleShape']:
                data['SampleAbs'][0] = 0.0
            elif 'Fixed' in data['SampleShape']:
                data['SampleAbs'][0] = 1.0
            wx.CallLater(100,UpdateImageControls,G2frame,data,masks)
                           
        def OnSamAbs(event):
            data['SampleAbs'][1] = not data['SampleAbs'][1]
                            
        def OnShowLines(event):
            data['showLines'] = not data['showLines']
            G2plt.PlotExposedImage(G2frame,event=event)
            
        def OnFullIntegrate(event):
            Lazm = float(G2frame.Lazim.GetValue())
            if data['fullIntegrate']:
                data['fullIntegrate'] = False
                data['LRazimuth'] = [Lazm,Lazm+20.]
            else:
                data['fullIntegrate'] = True
                data['LRazimuth'] = [Lazm,Lazm+360.]
            wx.CallLater(100,UpdateImageControls,G2frame,data,masks)
            G2plt.PlotExposedImage(G2frame,event=event)
            
        def OnSetDefault(event):
            if data['setDefault']:
                G2frame.imageDefault = {}
                data['setDefault'] = False
            else:
                G2frame.imageDefault = copy.copy(data)
                data['setDefault'] = True
                
        def OnCenterAzm(event):
            data['centerAzm'] = not data['centerAzm']
            wx.CallAfter(G2plt.PlotExposedImage,G2frame,event=event)
                
        def OnApplyPola(event):
            data['PolaVal'][1] = not data['PolaVal'][1]
                
        dataSizer = wx.FlexGridSizer(0,2,5,3)
        dataSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' Integration coefficients'),0,WACV)    
        dataSizer.Add((5,0),0)
        if 'PWDR' in data['type']:
            binChoice = ['2-theta','Q']
        elif 'SASD' in data['type']:
            binChoice = ['2-theta','Q','log(q)']
        dataSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' Bin style: Constant step bins in'),0,WACV)            
        binSel = wx.ComboBox(parent=G2frame.dataDisplay,value=data['binType'],choices=binChoice,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        binSel.Bind(wx.EVT_COMBOBOX, OnNewBinType)
        dataSizer.Add(binSel,0,WACV)
        binType = '2-theta'
        if 'q' in data['binType'].lower():
            binType = 'Q'
        dataSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' Inner/Outer '+binType),0,WACV)            
        IOtth = data['IOtth'][:]
        if 'Q' in data['binType']:
            wave = data['wavelength']
            IOtth = [4.*math.pi*sind(IOtth[0]/2.)/wave,4.*math.pi*sind(IOtth[1]/2.)/wave]
        littleSizer = wx.BoxSizer(wx.HORIZONTAL)
        G2frame.InnerTth = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,IOtth,0,nDig=(8,3,'f'),min=0.001,typeHint=float,OnLeave=OnIOtth)
        littleSizer.Add(G2frame.InnerTth,0,WACV)
        G2frame.OuterTth = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,IOtth,1,nDig=(8,3,'f'),min=0.001,typeHint=float,OnLeave=OnIOtth)
        littleSizer.Add(G2frame.OuterTth,0,WACV)
        dataSizer.Add(littleSizer,0,)
        dataSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' Start/End azimuth'),0,WACV)
        LRazim = data['LRazimuth']
        littleSizer = wx.BoxSizer(wx.HORIZONTAL)
        G2frame.Lazim = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,LRazim,0,nDig=(6,1,'f'),typeHint=float,OnLeave=OnLRazim)
        littleSizer.Add(G2frame.Lazim,0,WACV)
        G2frame.Razim = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,LRazim,1,nDig=(6,1,'f'),typeHint=float,OnLeave=OnLRazim)
        if data['fullIntegrate']:
            G2frame.Razim.Enable(False)
            G2frame.Razim.SetBackgroundColour(VERY_LIGHT_GREY)
            G2frame.Razim.SetValue(LRazim[0]+360.)
        littleSizer.Add(G2frame.Razim,0,WACV)
        dataSizer.Add(littleSizer,0,)
        dataSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' No. 2-theta/azimuth bins'),0,WACV)
        littleSizer = wx.BoxSizer(wx.HORIZONTAL)
        outChan = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data,'outChannels',typeHint=int,min=10)
        littleSizer.Add(outChan,0,WACV)
        outAzim = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data,'outAzimuths',nDig=(10,4),min=1,typeHint=int,OnLeave=OnNumOutAzms)
        littleSizer.Add(outAzim,0,WACV)
        dataSizer.Add(littleSizer,0,)
        samplechoice = ['Cylinder','Fixed flat plate',]
        dataSizer.Add(wx.StaticText(G2frame.dataDisplay,label='Select sample shape'),0,WACV)
        samShape = wx.ComboBox(G2frame.dataDisplay,value=data['SampleShape'],choices=samplechoice,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        samShape.Bind(wx.EVT_COMBOBOX,OnSampleShape)
        dataSizer.Add(samShape,0,WACV)
        #SampleShape - cylinder or flat plate choice?
        littleSizer = wx.BoxSizer(wx.HORIZONTAL)
        samabs = wx.CheckBox(parent=G2frame.dataDisplay,label='Apply sample absorption?')
        dataSizer.Add(samabs,0,WACV)
        samabs.Bind(wx.EVT_CHECKBOX, OnSamAbs)
        samabs.SetValue(data['SampleAbs'][1])
        minmax = [0.,2.]
        if 'Cylind' in data['SampleShape']: #cylinder mu*R; flat plate transmission
            littleSizer.Add(wx.StaticText(G2frame.dataDisplay,label='mu*R (0.00-2.0) '),0,WACV)
        elif 'Fixed' in data['SampleShape']:
            littleSizer.Add(wx.StaticText(G2frame.dataDisplay,label='transmission '),0,WACV) #for flat plate
            minmax = [.05,1.0]
        samabsVal = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data['SampleAbs'],0,nDig=(10,3),
            typeHint=float,min=minmax[0],max=minmax[1])
        littleSizer.Add(samabsVal,0,WACV)
        dataSizer.Add(littleSizer,0,)        
        if 'PWDR' in data['type']:
            littleSizer = wx.BoxSizer(wx.HORIZONTAL)
            oblique = wx.CheckBox(parent=G2frame.dataDisplay,label='Apply detector absorption?')
            dataSizer.Add(oblique,0,WACV)
            oblique.Bind(wx.EVT_CHECKBOX, OnOblique)
            oblique.SetValue(data['Oblique'][1])
            littleSizer.Add(wx.StaticText(G2frame.dataDisplay,label='Value (0.01-0.99)  '),0,WACV)
            obliqVal = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data['Oblique'],0,nDig=(10,3),typeHint=float,min=0.01,max=0.99)
            littleSizer.Add(obliqVal,0,WACV)
            dataSizer.Add(littleSizer,0,)
        if 'SASD' in data['type']:
            littleSizer = wx.BoxSizer(wx.HORIZONTAL)
            setPolariz = wx.CheckBox(parent=G2frame.dataDisplay,label='Apply polarization?')
            dataSizer.Add(setPolariz,0,WACV)
            setPolariz.Bind(wx.EVT_CHECKBOX, OnApplyPola)
            setPolariz.SetValue(data['PolaVal'][1])
            littleSizer.Add(wx.StaticText(G2frame.dataDisplay,label='Value (0.001-0.999)  '),0,WACV)
            polaVal = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data['PolaVal'],0,nDig=(10,3),typeHint=float,min=0.001,max=0.999)
            littleSizer.Add(polaVal,0,WACV)
            dataSizer.Add(littleSizer,0,)
        
        showLines = wx.CheckBox(parent=G2frame.dataDisplay,label='Show integration limits?')
        dataSizer.Add(showLines,0,WACV)
        showLines.Bind(wx.EVT_CHECKBOX, OnShowLines)
        showLines.SetValue(data['showLines'])
        fullIntegrate = wx.CheckBox(parent=G2frame.dataDisplay,label='Do full integration?')
        dataSizer.Add(fullIntegrate,0,WACV)
        fullIntegrate.Bind(wx.EVT_CHECKBOX, OnFullIntegrate)
        fullIntegrate.SetValue(data['fullIntegrate'])
        setDefault = wx.CheckBox(parent=G2frame.dataDisplay,label='Use for all new images?')
        dataSizer.Add(setDefault,0,WACV)
        setDefault.Bind(wx.EVT_CHECKBOX, OnSetDefault)
        setDefault.SetValue(data['setDefault'])
        centerAzm = wx.CheckBox(parent=G2frame.dataDisplay,label='Azimuth at bin center?')
        dataSizer.Add(centerAzm,0,WACV)
        centerAzm.Bind(wx.EVT_CHECKBOX, OnCenterAzm)
        centerAzm.SetValue(data['centerAzm'])
        return dataSizer
        
    def BackSizer():
        
        global oldFlat
        def OnBackImage(event):
            data['background image'][0] = backImage.GetValue()
            G2frame.ImageZ = GetImageZ(G2frame,data)
            ResetThresholds()
            wx.CallAfter(G2plt.PlotExposedImage,G2frame,event=event)
            
        def OnDarkImage(event):
            data['dark image'][0] = darkImage.GetValue()
            G2frame.ImageZ = GetImageZ(G2frame,data)
            ResetThresholds()
            wx.CallAfter(G2plt.PlotExposedImage,G2frame,event=event)
            
        def OnFlatBkg(invalid,value,tc):
            global oldFlat
            G2frame.ImageZ += int(oldFlat-data['Flat Bkg'])
            oldFlat = data['Flat Bkg']
            ResetThresholds()
            wx.CallAfter(G2plt.PlotExposedImage,G2frame,event=tc.event)

        def OnMult(invalid,value,tc):
            G2frame.ImageZ = GetImageZ(G2frame,data)
            ResetThresholds()
            wx.CallAfter(G2plt.PlotExposedImage,G2frame,event=tc.event)
        
        backSizer = wx.FlexGridSizer(0,6,5,5)
        oldFlat = data.get('Flat Bkg',0.)

        backSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,' Dark image'),0,WACV)
        Choices = ['',]+G2gd.GetPatternTreeDataNames(G2frame,['IMG ',])
        Source = G2frame.PatternTree.GetItemText(G2frame.Image)
        Choices.pop(Choices.index(Source))
        darkImage = wx.ComboBox(parent=G2frame.dataDisplay,value=data['dark image'][0],choices=Choices,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        darkImage.Bind(wx.EVT_COMBOBOX,OnDarkImage)
        backSizer.Add(darkImage)
        backSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,' multiplier'),0,WACV)
        darkMult = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data['dark image'],1,nDig=(10,3),
            typeHint=float,OnLeave=OnMult)
        backSizer.Add(darkMult,0,WACV)
        backSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,' Flat Bkg: '),0,WACV)
        flatbkg = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data,'Flat Bkg',nDig=(10,0),
            typeHint=float,OnLeave=OnFlatBkg)
        backSizer.Add(flatbkg,0,WACV)

        backSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,' Background image'),0,WACV)
        backImage = wx.ComboBox(parent=G2frame.dataDisplay,value=data['background image'][0],choices=Choices,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        backImage.Bind(wx.EVT_COMBOBOX,OnBackImage)
        backSizer.Add(backImage)
        backSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,' multiplier'),0,WACV)
        backMult = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data['background image'],1,nDig=(10,3),
            typeHint=float,OnLeave=OnMult)
        backSizer.Add(backMult,0,WACV)
        return backSizer
                        
    def CalibSizer():
                
        def OnNewCalibrant(event):
            data['calibrant'] = calSel.GetValue().strip()
            if data['calibrant']:
                G2frame.dataFrame.ImageEdit.Enable(id=G2gd.wxID_IMRECALIBRATE,enable=True)
                G2frame.dataFrame.ImageEdit.Enable(id=G2gd.wxID_IMCALIBRATE,enable=True)
                G2frame.dataFrame.ImageEdit.Enable(id=G2gd.wxID_IMRECALIBALL,enable=True)
                data['calibskip'] = calFile.Calibrants[data['calibrant']][3]
                limits = calFile.Calibrants[data['calibrant']][4]
                data['calibdmin'],data['pixLimit'],data['cutoff'] = limits
                pixLimit.SetValue(str(limits[1]))
                cutOff.SetValue(limits[2])
                calibSkip.SetValue(str(data['calibskip']))
                G2frame.calibDmin.SetValue(limits[0])
            else:
                G2frame.dataFrame.ImageEdit.Enable(id=G2gd.wxID_IMRECALIBRATE,enable=False)
                G2frame.dataFrame.ImageEdit.Enable(id=G2gd.wxID_IMCALIBRATE,enable=False)
                G2frame.dataFrame.ImageEdit.Enable(id=G2gd.wxID_IMRECALIBALL,enable=False)
                
        def OnCalibSkip(event):
            data['calibskip'] = int(calibSkip.GetValue())
            
        def OnPixLimit(event):
            data['pixLimit'] = int(pixLimit.GetValue())
            
        def OnSetRings(event):
            data['setRings'] = not data['setRings']
            G2plt.PlotExposedImage(G2frame,event=event)
    
        calibSizer = wx.FlexGridSizer(0,3,5,5)
        comboSizer = wx.BoxSizer(wx.HORIZONTAL)    
        comboSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' Calibrant '),0,WACV)
        calSel = wx.ComboBox(parent=G2frame.dataDisplay,value=data['calibrant'],choices=calList,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        calSel.Bind(wx.EVT_COMBOBOX, OnNewCalibrant)
        comboSizer.Add(calSel,0,WACV)
        calibSizer.Add(comboSizer,0)
        
        comboSizer = wx.BoxSizer(wx.HORIZONTAL)    
        comboSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' Calib lines to skip   '),0,WACV)
        calibSkip  = wx.ComboBox(parent=G2frame.dataDisplay,value=str(data['calibskip']),choices=[str(i) for i in range(25)],
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        calibSkip.Bind(wx.EVT_COMBOBOX, OnCalibSkip)
        comboSizer.Add(calibSkip,0,WACV)
        calibSizer.Add(comboSizer,0)
        
        comboSizer = wx.BoxSizer(wx.HORIZONTAL)        
        comboSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' Min calib d-spacing '),0,WACV)
        G2frame.calibDmin = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data,'calibdmin',nDig=(10,2),typeHint=float,min=0.25)
        comboSizer.Add(G2frame.calibDmin,0,WACV)
        calibSizer.Add(comboSizer,0)
        
        comboSizer = wx.BoxSizer(wx.HORIZONTAL)
        comboSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' Min ring I/Ib '),0,WACV)
        cutOff = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data,'cutoff',nDig=(10,1),typeHint=float,min=0.1)
        comboSizer.Add(cutOff,0,WACV)
        calibSizer.Add(comboSizer,0)
        
        comboSizer = wx.BoxSizer(wx.HORIZONTAL)
        comboSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' Pixel search range '),0,WACV)
        pixLimit = wx.ComboBox(parent=G2frame.dataDisplay,value=str(data['pixLimit']),choices=['1','2','5','10','15','20'],
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        pixLimit.Bind(wx.EVT_COMBOBOX, OnPixLimit)
        comboSizer.Add(pixLimit,0,WACV)
        calibSizer.Add(comboSizer,0)
        
        comboSizer = wx.BoxSizer(wx.HORIZONTAL)
        setRings = wx.CheckBox(parent=G2frame.dataDisplay,label='Show ring picks?')
        comboSizer.Add(setRings,0)
        setRings.Bind(wx.EVT_CHECKBOX, OnSetRings)
        setRings.SetValue(data['setRings'])
        calibSizer.Add(comboSizer,0)
        return calibSizer
        
    def GonioSizer():
        
        def OnGlobalEdit(event):
            Names = []
            Items = []
            if G2frame.PatternTree.GetCount():
                id, cookie = G2frame.PatternTree.GetFirstChild(G2frame.root)
                while id:
                    name = G2frame.PatternTree.GetItemText(id)
                    if 'IMG' in name:
                        ctrls = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,id,'Image Controls'))
                        Names.append(name)
                        Items.append(ctrls['GonioAngles'])
                    id, cookie = G2frame.PatternTree.GetNextChild(G2frame.root, cookie)
                if len(Names) == 1:
                    G2frame.ErrorDialog('Nothing for global editing','There must be more than one "IMG" pattern')
                    return
                dlg = G2G.G2HistoDataDialog(G2frame,' Edit sample goniometer data:',
                    'Edit data',['Omega','Chi','Phi'],['%.2f','%.2f','%.2f'],Names,Items)
            try:
                if dlg.ShowModal() == wx.ID_OK:
                    result = dlg.GetData()      #?? what was this for?
                    id, cookie = G2frame.PatternTree.GetFirstChild(G2frame.root)
                    while id:
                        name = G2frame.PatternTree.GetItemText(id)
                        if 'IMG' in name:
                            ctrls = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,id,'Image Controls'))
                            vals = Items[Names.index(name)]
                            ctrls['GonioAngles'] = vals
#                            G2frame.PatternTree.SetItemPyData(G2gd.GetPatternTreeItemId(G2frame,id, 'Image Controls'),ctrls)
                        id, cookie = G2frame.PatternTree.GetNextChild(G2frame.root, cookie)
            finally:
                dlg.Destroy()
                G2frame.PatternTree.SelectItem(G2frame.PickId)
        
        gonioSizer = wx.BoxSizer(wx.HORIZONTAL)
        names = ['Omega','Chi','Phi']
        gonioSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,'Sample goniometer angles: '),0,WACV)
        for i,name in enumerate(names):
            gonioSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,name),0,WACV)
            angle = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data['GonioAngles'],i,nDig=(8,2),typeHint=float)
            gonioSizer.Add(angle,0,WACV)
        globEdit = wx.Button(G2frame.dataDisplay,-1,'Global edit')
        globEdit.Bind(wx.EVT_BUTTON,OnGlobalEdit)
        gonioSizer.Add(globEdit,0,WACV)
        return gonioSizer
        
# Image Controls main code             
                            
    #fix for old files:
    if 'azmthOff' not in data:
        data['azmthOff'] = 0.0
    if 'background image' not in data:
        data['background image'] = ['',-1.0]
    if 'dark image' not in data:
        data['dark image'] = ['',-1.0]
    if 'centerAzm' not in data:
        data['centerAzm'] = False
    if 'Oblique' not in data:
        data['Oblique'] = [0.5,False]
    if 'PolaVal' not in data:
        data['PolaVal'] = [0.99,False]
    #end fix
    
    if IntegrateOnly:
        OnIntegrate(None)
        return
    
    colorList = sorted([m for m in mpl.cm.datad.keys() if not m.endswith("_r")],key=lambda s: s.lower())
    calList = sorted([m for m in calFile.Calibrants.keys()],key=lambda s: s.lower())
    typeList = ['PWDR - powder diffraction data','SASD - small angle scattering data',
        'REFL - reflectometry data']
    if not data.get('type'):                        #patch for old project files
        data['type'] = 'PWDR'
    typeDict = {'PWDR':typeList[0],'SASD':typeList[1],'REFL':typeList[2]}
    if G2frame.dataDisplay:
        G2frame.dataDisplay.Destroy()
    G2gd.SetDataMenuBar(G2frame,G2frame.dataFrame.ImageMenu)
    if not G2frame.dataFrame.GetStatusBar():
        G2frame.dataFrame.CreateStatusBar()
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnCalibrate, id=G2gd.wxID_IMCALIBRATE)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnRecalibrate, id=G2gd.wxID_IMRECALIBRATE)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnRecalibAll, id=G2gd.wxID_IMRECALIBALL)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnClearCalib, id=G2gd.wxID_IMCLEARCALIB)
    if data.get('calibrant'):
        mode = True
    else:
        mode = False
    G2frame.dataFrame.ImageEdit.Enable(id=G2gd.wxID_IMRECALIBRATE,enable=mode)
    G2frame.dataFrame.ImageEdit.Enable(id=G2gd.wxID_IMCALIBRATE,enable=mode)
    G2frame.dataFrame.ImageEdit.Enable(id=G2gd.wxID_IMRECALIBALL,enable=mode)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnIntegrate, id=G2gd.wxID_IMINTEGRATE)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnIntegrateAll, id=G2gd.wxID_INTEGRATEALL)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnCopyControls, id=G2gd.wxID_IMCOPYCONTROLS)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnCopySelected, id=G2gd.wxID_IMCOPYSELECTED)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnSaveControls, id=G2gd.wxID_IMSAVECONTROLS)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnSaveMultiControls, id=G2gd.wxID_SAVESELECTEDCONTROLS)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnLoadControls, id=G2gd.wxID_IMLOADCONTROLS)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnTransferAngles, id=G2gd.wxID_IMXFERCONTROLS)
    def OnDestroy(event):
        G2frame.autoIntFrame = None
    def OnAutoInt(event):
        if G2frame.autoIntFrame: # ensure only one open at a time
            G2frame.autoIntFrame.Raise()
            return
        G2frame.autoIntFrame = AutoIntFrame(G2frame,PollTime=10.0)
        G2frame.autoIntFrame.Bind(wx.EVT_WINDOW_DESTROY,OnDestroy) # clean up name on window close 
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnAutoInt, id=G2gd.wxID_IMAUTOINTEG)
    G2frame.dataDisplay = wx.Panel(G2frame.dataFrame)

    mainSizer = wx.BoxSizer(wx.VERTICAL)
    mainSizer.Add((5,10),0)    
    mainSizer.Add(ComboSizer(),0,wx.ALIGN_LEFT)
    mainSizer.Add((5,5),0)
    Range = data['range'] # allows code to be same in Masks
    MaxSizer = MaxSizer()               #keep this so it can be changed in BackSizer   
    mainSizer.Add(MaxSizer,0,wx.ALIGN_LEFT|wx.EXPAND|wx.ALL)
    
    mainSizer.Add((5,5),0)
    DataSizer = wx.FlexGridSizer(0,2,5,0)
    DataSizer.Add(CalibCoeffSizer(),0)
    DataSizer.Add(IntegrateSizer(),0)        
    mainSizer.Add(DataSizer,0)
    mainSizer.Add((5,5),0)            
    mainSizer.Add(BackSizer(),0)
    mainSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' Calibration controls:'),0,WACV)
    mainSizer.Add((5,5),0)
    mainSizer.Add(CalibSizer(),0,WACV)
    mainSizer.Add((5,5),0)
    mainSizer.Add(GonioSizer(),0,WACV)   
        
    mainSizer.Layout()    
    G2frame.dataDisplay.SetSizer(mainSizer)
    fitSize = mainSizer.Fit(G2frame.dataFrame)
    G2frame.dataFrame.setSizePosLeft(fitSize)
    
################################################################################
##### Masks
################################################################################
def CleanupMasks(data):
    '''If a mask creation is not completed, an empty mask entry is created in the
    masks array. This cleans them out. It is called when the masks page is first loaded
    and before saving them or after reading them in. This should also probably be done
    before they are used for integration.
    '''
    for key in ['Points','Rings','Arcs','Polygons']:
        data[key] = data.get(key,[])
        l1 = len(data[key])
        data[key] = [i for i in data[key] if len(i)]
        l2 = len(data[key])
        if GSASIIpath.GetConfigValue('debug') and l1 != l2:
            print 'Mask Cleanup:',key,'was',l1,'entries','now',l2
    
def UpdateMasks(G2frame,data):
    '''Shows and handles the controls on the "Masks" data tree entry
    '''
    
    def OnTextMsg(event):
        Obj = event.GetEventObject()
        Obj.SetToolTipString('Drag this mask on 2D Powder Image with mouse to change ')

    def Replot(*args,**kwargs):
        wx.CallAfter(G2plt.PlotExposedImage,G2frame)

    def onDeleteMask(event):
        Obj = event.GetEventObject()
        typ = Obj.locationcode.split('+')[1]
        num = int(Obj.locationcode.split('+')[2])
        del(data[typ][num])
        wx.CallAfter(UpdateMasks,G2frame,data)
        G2plt.PlotExposedImage(G2frame,event=event)

    def onDeleteFrame(event):
        data['Frames'] = []
        wx.CallAfter(UpdateMasks,G2frame,data)
        G2plt.PlotExposedImage(G2frame,event=event)

    def OnCopyMask(event):
        Names = G2gd.GetPatternTreeDataNames(G2frame,['IMG ',])
        if len(Names) == 1:
            G2frame.ErrorDialog('Nothing to copy masks to','There must be more than one "IMG" pattern')
            return
        Source = G2frame.PatternTree.GetItemText(G2frame.Image)
        Names.pop(Names.index(Source))
        Data = copy.deepcopy(data)
        Thresh = Data.pop('Thresholds')     # & remove it as well
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Copy mask data','Copy masks from '+Source+' to:',Names)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                items = dlg.GetSelections()
                for item in items:
                    name = Names[item]
                    Id = G2gd.GetPatternTreeItemId(G2frame,G2frame.root,name)
                    MId = G2gd.GetPatternTreeItemId(G2frame,Id,'Masks')
                    Mask = G2frame.PatternTree.GetItemPyData(MId)
                    Mask.update(copy.deepcopy(Data))
                    Mask['Thresholds'][1][0] = Thresh[1][0]  #copy only lower threshold 
                    G2frame.PatternTree.SetItemPyData(G2gd.GetPatternTreeItemId(G2frame,Id, 'Masks'),Mask)
        finally:
            dlg.Destroy()

    def OnSaveMask(event):
        CleanupMasks(data)
        pth = G2G.GetExportPath(G2frame)
        dlg = wx.FileDialog(G2frame, 'Choose image mask file', pth, '', 
            'image mask files (*.immask)|*.immask',wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                filename = os.path.splitext(filename)[0]+'.immask'
                File = open(filename,'w')
                keys = ['Points','Rings','Arcs','Polygons','Frames','Thresholds']
                for key in keys:
                    File.write(key+':'+str(data[key])+'\n')
                File.close()
        finally:
            dlg.Destroy()
        
    def OnLoadMask(event):
        if event.Id == G2gd.wxID_MASKLOADNOT:
            ignoreThreshold = True
        else:
            ignoreThreshold = False
        pth = G2G.GetImportPath(G2frame)
        if not pth: pth = '.'
        dlg = wx.FileDialog(G2frame, 'Choose image mask file', pth, '', 
            'image mask files (*.immask)|*.immask',wx.OPEN)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                File = open(filename,'r')
                save = {}
                oldThreshold = data['Thresholds'][0]
                S = File.readline()
                while S:
                    if S[0] == '#':
                        S = File.readline()
                        continue
                    [key,val] = S.strip().split(':',1)
                    if key in ['Points','Rings','Arcs','Polygons','Frames','Thresholds']:
                        if ignoreThreshold and key == 'Thresholds':
                            S = File.readline() 
                            continue
                        save[key] = eval(val)
                        if key == 'Thresholds':
                            save[key][0] = oldThreshold
                            save[key][1][1] = min(oldThreshold[1],save[key][1][1])
                    S = File.readline()
                File.close()
                data.update(save)
                CleanupMasks(data)
                wx.CallAfter(UpdateMasks,G2frame,data)
                G2plt.PlotExposedImage(G2frame,event=event)                
        finally:
            dlg.Destroy()
            
    def OnAutoSpotMask(event):
        'Do auto search for spot masks'
        if wx.MessageDialog(G2frame.dataDisplay,'NB: This will clear any old spot masks','Auto Spot Masks', wx.OK|wx.CANCEL).ShowModal() == wx.ID_OK:
            Controls = copy.deepcopy(G2frame.PatternTree.GetItemPyData( 
            G2gd.GetPatternTreeItemId(G2frame,G2frame.PatternId,'Image Controls')))
            Error = G2img.AutoSpotMasks(G2frame.ImageZ,data,Controls)
            if not Error is None:
                G2frame.ErrorDialog('Auto spot search error',Error)
            wx.CallAfter(UpdateMasks,G2frame,data)
            wx.CallAfter(G2plt.PlotExposedImage,G2frame,event=event)                
            
    def ToggleSpotMaskMode(event):
        G2plt.ToggleMultiSpotMask(G2frame)
        
    def OnNewArcMask(event):
        'Start a new arc mask'
        G2frame.MaskKey = 'a'
        G2plt.OnStartMask(G2frame)
        
    def OnNewRingMask(event):
        'Start a new ring mask'
        G2frame.MaskKey = 'r'
        G2plt.OnStartMask(G2frame)
        
    def OnNewPolyMask(event):
        'Start a new polygon mask'
        G2frame.MaskKey = 'p'
        G2plt.OnStartMask(G2frame)
        
    def OnNewFrameMask(event):
        'Start a new Frame mask'
        G2frame.MaskKey = 'f'
        G2plt.OnStartMask(G2frame)
        
    def MaxSizer():
        '''Defines a sizer with sliders and TextCtrl widgets for controlling the colormap
        for the image, as well as callback routines. 
        '''
        def OnNewVal(invalid,value,tc):
            '''Called when a Imax or Imin value is typed into a Validated TextCrtl (which puts
            the value into the data['range'] nested list).
            This adjusts the slider positions to match the current values
            '''
            scaleSel.SetSelection(len(scaleChoices)-1)
            r11 = min(max(Range[1][1],Range[1][0]+1),Range[0][1]) # keep values in range
            if r11 != Range[1][1]:
                Range[1][1] = r11
                maxVal.SetValue(int(Range[1][1]))
            r10 = max(min(Range[1][0],Range[1][1]-1),Range[0][0])
            if r10 != Range[1][0]:
                Range[1][0] = r10
                minVal.SetValue(int(Range[1][0]))
            sqrtDeltZero = math.sqrt(max(1.0,Range[0][1]-max(0.0,Range[1][0])-1)) # sqrt(Imax0-Imin-1)
            sqrtDeltOne  = math.sqrt(max(1.0,Range[1][1]-max(0.0,Range[1][0])-1)) # sqrt(Imax-Imin-1)
            sv1 = min(100,max(0,int(0.5+100.*sqrtDeltOne/sqrtDeltZero)))
            maxSel.SetValue(sv1)
            DeltOne  = max(1.0,Range[1][1]-max(0.0,Range[0][0])-1)
            sv0 = min(100,max(0,int(0.5+100.*(Range[1][0]-Range[0][0])/DeltOne)))
            minSel.SetValue(sv0)
            new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('2D Powder Image','mpl',newImage=False)
            Page.ImgObj.set_clim([Range[1][0],Range[1][1]])
            if mplOld:
                Page.canvas.draw()
            else:
                Page.canvas.draw_idle()
            
        G2frame.prevMaxValue = None    
        def OnMaxSlider(event):
            val = maxSel.GetValue()
            if G2frame.prevMaxValue == val: return # if this val has been processed, no need to repeat
            scaleSel.SetSelection(len(scaleChoices)-1)
            G2frame.prevMaxValue = val
            sqrtDeltZero = math.sqrt(max(1.0,Range[0][1]-max(0.0,Range[1][0])-1)) # sqrt(Imax0-Imin-1)
            Range[1][1] = int(0.5 + (val * sqrtDeltZero / 100.)**2 + Range[1][0] + 1)
            maxVal.SetValue(int(0.5+Range[1][1]))
            DeltOne  = max(1.0,Range[1][1]-max(0.0,Range[0][0])-1)
            minSel.SetValue(int(0.5 + 100*(Range[1][0]/DeltOne)))
            sv0 = min(100,max(0,int(0.5+100.*(Range[1][0]-Range[0][0])/DeltOne)))
            minSel.SetValue(sv0)
            new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('2D Powder Image','mpl',newImage=False)
            Page.ImgObj.set_clim([Range[1][0],Range[1][1]])
            if mplOld:
                Page.canvas.draw()
            else:
                Page.canvas.draw_idle()
            
        G2frame.prevMinValue = None    
        def OnMinSlider(event):
            val = minSel.GetValue()
            scaleSel.SetSelection(len(scaleChoices)-1)
            if G2frame.prevMinValue == val: return # if this val has been processed, no need to repeat
            G2frame.prevMinValue = val
            DeltOne  = max(1.0,Range[1][1]-max(0.0,Range[0][0])-1) # Imax-Imin0-1
            Range[1][0] = max(0,int(0.5 + val * DeltOne / 100 + Range[0][0]))
            minVal.SetValue(int(Range[1][0]))
            sqrtDeltZero = math.sqrt(max(1.0,Range[0][1]-max(0.0,Range[1][0])-1)) # sqrt(Imax0-Imin-1)
            sqrtDeltOne  = math.sqrt(max(1.0,Range[1][1]-max(0.0,Range[1][0])-1)) # sqrt(Imax-Imin-1)
            sv1 = min(100,max(0,int(0.5+100.*sqrtDeltOne/sqrtDeltZero)))
            maxSel.SetValue(sv1)
            new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('2D Powder Image','mpl',newImage=False)
            Page.ImgObj.set_clim([Range[1][0],Range[1][1]])
            if mplOld:
                Page.canvas.draw()
            else:
                Page.canvas.draw_idle()
            
        def OnAutoSet(event):
            '''Responds to a button labeled 95%, etc; Sets the Imax and Imin values
            for the image so that 95% (etc.) of pixels are inside the color map limits.
            An equal number of pixels are dropped at the minimum and maximum levels.
            '''
            try:
                val = int(event.GetEventObject().GetStringSelection()[:-1])
                margin = (100-val)/2.
            except:
                margin = 0
                event.GetEventObject().SetSelection(0)
            new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('2D Powder Image','mpl',newImage=False)
            if margin == 0:
                Range[1] = list(Range[0])
            else:
                Range[1][0] = int(np.percentile(Page.ImgObj.get_array().compressed(),margin))
                Range[1][1] = int(np.percentile(Page.ImgObj.get_array().compressed(),100-margin))
            sqrtDeltZero = math.sqrt(max(1.0,Range[0][1]-max(0.0,Range[1][0])-1)) # sqrt(Imax0-Imin-1)
            sqrtDeltOne  = math.sqrt(max(1.0,Range[1][1]-max(0.0,Range[1][0])-1)) # sqrt(Imax-Imin-1)
            sv1 = min(100,max(0,int(0.5+100.*sqrtDeltOne/sqrtDeltZero)))
            maxSel.SetValue(sv1)
            DeltOne  = max(1.0,Range[1][1]-max(0.0,Range[0][0])-1)
            sv0 = min(100,max(0,int(0.5+100.*(Range[1][0]-Range[0][0])/DeltOne)))
            minSel.SetValue(sv0)
            minVal.SetValue(int(Range[1][0]))
            maxVal.SetValue(int(Range[1][1]))
            new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('2D Powder Image','mpl',newImage=False)
            Page.ImgObj.set_clim([Range[1][0],Range[1][1]])
            if mplOld:
                Page.canvas.draw()
            else:
                Page.canvas.draw_idle()

        mplv = mpl.__version__.split('.')
        mplOld = mplv[0] == '1' and int(mplv[1]) < 4 # use draw_idle for newer matplotlib versions
        # Plot color scaling uses limits as below:
        #   (Imin0, Imax0) => Range[0] = data['range'][0] # lowest to highest pixel intensity
        #   [Imin, Imax] => Range[1] = data['range'][1] #   lowest to highest pixel intensity on cmap scale
        maxSizer = wx.GridBagSizer(0,0)
        r = c = 0
        maxSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' Max intensity'),(r,c))
        c += 1
        # maxSel is a slider with 101 steps scaled from Imin+1 to Imax0 with sqrt scaling
        # slider value = sv = 100 * sqrt((Imax-Imin-1)/(Imax0-Imin-1))
        # Imax = (sv * sqrt(Imax0-Imin-1) / 100)**2 + Imin + 1
        sqrtDeltZero = math.sqrt(max(1.0,Range[0][1]-max(0.0,Range[1][0])-1)) # sqrt(Imax0-Imin-1)
        sqrtDeltOne  = math.sqrt(max(1.0,Range[1][1]-max(0.0,Range[1][0])-1)) # sqrt(Imax-Imin-1)
        sv1 = min(100,max(0,int(0.5+100.*sqrtDeltOne/sqrtDeltZero)))
        maxSel = wx.Slider(parent=G2frame.dataDisplay,style=wx.SL_HORIZONTAL,value=sv1,size=(300,-1))
        maxSizer.Add(maxSel,(r,c),flag=wx.EXPAND)
        maxSizer.AddGrowableCol(c)
        c += 1
        maxSel.Bind(wx.EVT_SLIDER, OnMaxSlider)
        maxVal = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,Range[1],1,min=Range[0][0]+1,
            max=Range[0][1],typeHint=int,OnLeave=OnNewVal)
        maxSizer.Add(maxVal,(r,c))
        c += 1
        scaleChoices = ("100%","99%","95%","90%","80%","?")
        scaleSel = wx.Choice(G2frame.dataDisplay,choices=scaleChoices,size=(-1,-1))
        if (Range[1][0] == Range[0][0] and
            Range[1][1] == Range[0][1]):
            scaleSel.SetSelection(0)
        else:
            scaleSel.SetSelection(len(scaleChoices)-1)
        scaleSel.Bind(wx.EVT_CHOICE,OnAutoSet)
        maxSizer.Add(scaleSel,(r,c),(2,1),flag=wx.ALIGN_CENTER)
        c = 0
        r = 1
        maxSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' Min intensity'),(r,c))
        c += 1
        # minSel is a slider with 101 steps scaled from Imin0 to Imax-1 with linear scaling
        # slider value = sv0 = 100 * (Imin-Imin0)/(Imax-Imin0-1)
        # Imin = sv0 * (Imax-Imin0-1) / 100 + Imin0
        DeltOne  = max(1.0,Range[1][1]-max(0.0,Range[0][0])-1) # Imax-Imin0-1
        sv0 = min(100,max(0,int(0.5+100.*(Range[1][0]-Range[0][0])/DeltOne)))
        minSel = wx.Slider(parent=G2frame.dataDisplay,style=wx.SL_HORIZONTAL,value=sv0,size=(300,-1))
        maxSizer.Add(minSel,(r,c),flag=wx.EXPAND|wx.ALL)
        c += 1
        minSel.Bind(wx.EVT_SLIDER, OnMinSlider)
        minVal = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,Range[1],0,
            max=Range[0][1],typeHint=int,OnLeave=OnNewVal)
        maxSizer.Add(minVal,(r,c))
        return maxSizer

    startScroll = None
    if G2frame.dataDisplay:
        startScroll = G2frame.dataDisplay.GetScrollPos(wx.VERTICAL) # save scroll position
        G2frame.dataDisplay.Destroy()
    else:
        CleanupMasks(data) # posting page for 1st time; clean out anything unfinished
    G2gd.SetDataMenuBar(G2frame,G2frame.dataFrame.MaskMenu)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnCopyMask, id=G2gd.wxID_MASKCOPY)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnLoadMask, id=G2gd.wxID_MASKLOAD)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnLoadMask, id=G2gd.wxID_MASKLOADNOT)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnSaveMask, id=G2gd.wxID_MASKSAVE)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnAutoSpotMask, id=G2gd.wxID_FINDSPOTS)
    G2frame.dataFrame.Bind(wx.EVT_MENU, ToggleSpotMaskMode, id=G2gd.wxID_NEWMASKSPOT)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnNewArcMask, id=G2gd.wxID_NEWMASKARC)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnNewRingMask, id=G2gd.wxID_NEWMASKRING)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnNewPolyMask, id=G2gd.wxID_NEWMASKPOLY)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnNewFrameMask, id=G2gd.wxID_NEWMASKFRAME)
    if not G2frame.dataFrame.GetStatusBar():
        G2frame.dataFrame.CreateStatusBar()
    if G2frame.MaskKey == 'f':
        G2frame.dataFrame.GetStatusBar().SetStatusText('Frame mask active - LB pick next point, RB close polygon')
    elif G2frame.MaskKey == 'p':
        G2frame.dataFrame.GetStatusBar().SetStatusText('Polygon mask active - LB pick next point, RB close polygon')
    elif G2frame.MaskKey == 'a':
        G2frame.dataFrame.GetStatusBar().SetStatusText('Arc mask active - LB pick arc location')
    elif G2frame.MaskKey == 'r':
        G2frame.dataFrame.GetStatusBar().SetStatusText('Ring mask active - LB pick ring location')
    else:
        G2frame.dataFrame.GetStatusBar().SetStatusText("To add mask: press a,r,s,p or f on 2D image for arc/ring/spot/polygon/frame")
    G2frame.dataDisplay = wxscroll.ScrolledPanel(G2frame.dataFrame)
    mainSizer = wx.BoxSizer(wx.VERTICAL)
    mainSizer.Add((5,10),0)

    thresh = data['Thresholds']         #min/max intensity range
    Spots = data['Points']               #x,y,radius in mm
    Rings = data['Rings']               #radius, thickness
    Polygons = data['Polygons']         #3+ x,y pairs
    if 'Frames' not in data:
        data['Frames'] = []
    frame = data['Frames']             #3+ x,y pairs
    Arcs = data['Arcs']                 #radius, start/end azimuth, thickness

    ######################################################################
    CId = G2gd.GetPatternTreeItemId(G2frame,G2frame.Image,'Image Controls')
    controlData = G2frame.PatternTree.GetItemPyData(CId)
    Range = controlData['range']
    MaxSizer = MaxSizer()               #keep this so it can be changed in BackSizer   
    mainSizer.Add(MaxSizer,0,wx.ALIGN_LEFT|wx.EXPAND|wx.ALL)

    littleSizer = wx.FlexGridSizer(0,3,0,5)
    littleSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' Lower/Upper limits '),0,WACV)
    Text = wx.TextCtrl(G2frame.dataDisplay,value=str(thresh[0][0]),style=wx.TE_READONLY)
    littleSizer.Add(Text,0,WACV)
    Text.SetBackgroundColour(VERY_LIGHT_GREY)
    Text = wx.TextCtrl(G2frame.dataDisplay,value=str(thresh[0][1]),style=wx.TE_READONLY)
    littleSizer.Add(Text,0,WACV)
    Text.SetBackgroundColour(VERY_LIGHT_GREY)
    littleSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' Lower/Upper thresholds '),0,WACV)
    lowerThreshold = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,loc=thresh[1],key=0,
        min=thresh[0][0],OnLeave=Replot,typeHint=int)
    littleSizer.Add(lowerThreshold,0,WACV)
    upperThreshold = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,loc=thresh[1],key=1,
        max=thresh[0][1],OnLeave=Replot,typeHint=int)
    littleSizer.Add(upperThreshold,0,WACV)
    mainSizer.Add(littleSizer,0,)
    if len(Spots):
        lbl = wx.StaticText(parent=G2frame.dataDisplay,label=' Spot masks')
        lbl.SetBackgroundColour(wx.Colour(200,200,210))
        mainSizer.Add(lbl,0,wx.EXPAND|wx.ALIGN_CENTER,0)
        littleSizer = wx.FlexGridSizer(0,3,0,5)
        littleSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' position, mm'),0,WACV)
        littleSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' diameter, mm'),0,WACV)
        littleSizer.Add((5,0),0)
        for i in range(len(Spots)):
            if len(Spots[i]):
                x,y,d = Spots[i]
                spotText = wx.TextCtrl(parent=G2frame.dataDisplay,value=("%.2f,%.2f" % (x,y)),
                    style=wx.TE_READONLY)
                spotText.SetBackgroundColour(VERY_LIGHT_GREY)
                littleSizer.Add(spotText,0,WACV)
                spotText.Bind(wx.EVT_ENTER_WINDOW,OnTextMsg)
                spotDiameter = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,loc=Spots[i],key=2,
                    max=100.,OnLeave=Replot,nDig=[8,2])
                littleSizer.Add(spotDiameter,0,WACV)
                spotDelete = G2G.G2LoggedButton(G2frame.dataDisplay,label='delete?',
                    locationcode='Delete+Points+'+str(i),handler=onDeleteMask)
                littleSizer.Add(spotDelete,0,WACV)
        mainSizer.Add(littleSizer,0,)
    if Rings:
        lbl = wx.StaticText(parent=G2frame.dataDisplay,label=' Ring masks')
        lbl.SetBackgroundColour(wx.Colour(200,200,210))
        mainSizer.Add(lbl,0,wx.EXPAND|wx.ALIGN_CENTER,0)
        littleSizer = wx.FlexGridSizer(0,3,0,5)
        littleSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' 2-theta,deg'),0,WACV)
        littleSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' thickness, deg'),0,WACV)
        littleSizer.Add((5,0),0)
        for i in range(len(Rings)):
            if Rings[i]:
                ringText = wx.TextCtrl(parent=G2frame.dataDisplay,value=("%.3f" % (Rings[i][0])),
                    style=wx.TE_READONLY)
                ringText.SetBackgroundColour(VERY_LIGHT_GREY)
                ringText.Bind(wx.EVT_ENTER_WINDOW,OnTextMsg)
                littleSizer.Add(ringText,0,WACV)
                ringThick = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,loc=Rings[i],key=1,
                    min=0.001,max=1.,OnLeave=Replot,nDig=[8,3])
                littleSizer.Add(ringThick,0,WACV)
                ringDelete = G2G.G2LoggedButton(G2frame.dataDisplay,label='delete?',
                    locationcode='Delete+Rings+'+str(i),handler=onDeleteMask)
                littleSizer.Add(ringDelete,0,WACV)
        mainSizer.Add(littleSizer,0,)
    if Arcs:
        lbl = wx.StaticText(parent=G2frame.dataDisplay,label=' Arc masks')
        lbl.SetBackgroundColour(wx.Colour(200,200,210))
        mainSizer.Add(lbl,0,wx.EXPAND|wx.ALIGN_CENTER,0)
        littleSizer = wx.FlexGridSizer(0,4,0,5)
        littleSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' 2-theta,deg'),0,WACV)
        littleSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' azimuth, deg'),0,WACV)
        littleSizer.Add(wx.StaticText(parent=G2frame.dataDisplay,label=' thickness, deg'),0,WACV)
        littleSizer.Add((5,0),0)
        for i in range(len(Arcs)):
            if Arcs[i]:
                tth,azimuth,thick = Arcs[i]
                arcText = wx.TextCtrl(parent=G2frame.dataDisplay,value=("%.3f" % (tth)),
                    style=wx.TE_READONLY)
                arcText.SetBackgroundColour(VERY_LIGHT_GREY)
                arcText.Bind(wx.EVT_ENTER_WINDOW,OnTextMsg)
                littleSizer.Add(arcText,0,WACV)
                azmText = wx.TextCtrl(parent=G2frame.dataDisplay,value=("%d,%d" % (azimuth[0],azimuth[1])),
                    style=wx.TE_READONLY)
                azmText.SetBackgroundColour(VERY_LIGHT_GREY)
                azmText.Bind(wx.EVT_ENTER_WINDOW,OnTextMsg)
                littleSizer.Add(azmText,0,WACV)
                arcThick = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,loc=Arcs[i],key=2,
                    min=0.001,max=20.,OnLeave=Replot,nDig=[8,3])
                littleSizer.Add(arcThick,0,WACV)
                arcDelete = G2G.G2LoggedButton(G2frame.dataDisplay,label='delete?',
                    locationcode='Delete+Arcs+'+str(i),handler=onDeleteMask)
                littleSizer.Add(arcDelete,0,WACV)
        mainSizer.Add(littleSizer,0,)
    if Polygons:
        lbl = wx.StaticText(parent=G2frame.dataDisplay,
            label=' Polygon masks (on plot RB vertex drag to move,\nLB vertex drag to insert)')
        lbl.SetBackgroundColour(wx.Colour(200,200,210))
        mainSizer.Add(lbl,0,wx.EXPAND|wx.ALIGN_CENTER,0)
        littleSizer = wx.FlexGridSizer(0,2,0,5)
        for i in range(len(Polygons)):
            if Polygons[i]:
                polyList = []
                for x,y in Polygons[i]:
                    polyList.append("%.2f, %.2f"%(x,y))
                polyText = wx.ComboBox(G2frame.dataDisplay,value=polyList[0],choices=polyList,style=wx.CB_READONLY)
                littleSizer.Add(polyText,0,WACV)
                polyDelete = G2G.G2LoggedButton(G2frame.dataDisplay,label='delete?',
                    locationcode='Delete+Polygons+'+str(i),handler=onDeleteMask)
                littleSizer.Add(polyDelete,0,WACV)
        mainSizer.Add(littleSizer,0,)
    if frame:
        lbl = wx.StaticText(parent=G2frame.dataDisplay,
            label=' Frame mask (on plot RB vertex drag to move,LB vertex drag to insert)')
        lbl.SetBackgroundColour(wx.Colour(200,200,210))
        mainSizer.Add(lbl,0,wx.EXPAND|wx.ALIGN_CENTER,0)
        littleSizer = wx.FlexGridSizer(0,2,0,5)
        frameList = []
        for x,y in frame:
            frameList.append("%.2f, %.2f"%(x,y))
        frameText = wx.ComboBox(G2frame.dataDisplay,value=frameList[0],choices=frameList,style=wx.CB_READONLY)
        littleSizer.Add(frameText,0,WACV)
        frameDelete = G2G.G2LoggedButton(G2frame.dataDisplay,label='delete?',
            locationcode='Delete+Frame',handler=onDeleteFrame)
        littleSizer.Add(frameDelete,0,WACV)
        mainSizer.Add(littleSizer,0,)
    mainSizer.Layout()    
    G2frame.dataDisplay.SetSizer(mainSizer)
    G2frame.dataDisplay.SetupScrolling()
    Size = mainSizer.Fit(G2frame.dataFrame)
    Size[0] += 50 # room for scrollbar & status msg
    Size[1] = min(Size[1],500)
    G2frame.dataFrame.setSizePosLeft(Size)    
    if startScroll: # reset scroll to saved position
        G2frame.dataDisplay.Scroll(0,startScroll) # set to saved scroll position
        wx.Yield()

################################################################################
##### Stress/Strain
################################################################################

def UpdateStressStrain(G2frame,data):
    '''Shows and handles the controls on the "Stress/Strain"
    data tree entry
    '''
    
    def OnAppendDzero(event):
        data['d-zero'].append({'Dset':1.0,'Dcalc':0.0,'pixLimit':10,'cutoff':1.0,
            'ImxyObs':[[],[]],'ImtaObs':[[],[]],'ImtaCalc':[[],[]],'Emat':[1.0,1.0,1.0]})
        UpdateStressStrain(G2frame,data)
        
    def OnUpdateDzero(event):
        for item in data['d-zero']:
            if item['Dcalc']:   #skip unrefined ones
                item['Dset'] = item['Dcalc']
        UpdateStressStrain(G2frame,data)
            
    def OnCopyStrSta(event):
        Names = G2gd.GetPatternTreeDataNames(G2frame,['IMG ',])
        if len(Names) == 1:
            G2frame.ErrorDialog('Nothing to copy controls to','There must be more than one "IMG" pattern')
            return
        Source = G2frame.PatternTree.GetItemText(G2frame.Image)
        Names.pop(Names.index(Source))
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Copy stress/strain controls','Copy controls from '+Source+' to:',Names)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                items = dlg.GetSelections()
                for item in items:
                    name = Names[item]
                    Id = G2gd.GetPatternTreeItemId(G2frame,G2frame.root,name)
                    CId = G2gd.GetPatternTreeItemId(G2frame,Id,'Stress/Strain')
                    oldData = G2frame.PatternTree.GetItemPyData(CId)
                    load = oldData.get('Sample load',0.0)
                    Data = copy.deepcopy(data)
                    Data['Sample load'] = load
                    G2frame.PatternTree.SetItemPyData(G2gd.GetPatternTreeItemId(G2frame,Id,'Stress/Strain'),Data)
        finally:
            dlg.Destroy()
            G2frame.PatternTree.SelectItem(G2frame.PickId)

    def OnLoadStrSta(event):
        pth = G2G.GetImportPath(G2frame)
        if not pth: pth = '.'
        dlg = wx.FileDialog(G2frame, 'Choose stress/strain file', pth, '', 
            'image control files (*.strsta)|*.strsta',wx.OPEN)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                File = open(filename,'r')
                S = File.read()
                data = eval(S)
                Controls = G2frame.PatternTree.GetItemPyData(
                    G2gd.GetPatternTreeItemId(G2frame,G2frame.Image, 'Image Controls'))
                G2img.FitStrSta(G2frame.ImageZ,data,Controls)
                UpdateStressStrain(G2frame,data)
                G2plt.PlotExposedImage(G2frame,event=event)
                G2plt.PlotStrain(G2frame,data,newPlot=True)
                File.close()
        finally:
            dlg.Destroy()

    def OnSaveStrSta(event):
        pth = G2G.GetExportPath(G2frame)
        dlg = wx.FileDialog(G2frame, 'Choose stress/strain file', pth, '', 
            'image control files (*.strsta)|*.strsta',wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                File = open(filename,'w')
                keys = ['Type','Sample phi','Sample z','Sample load']
                keys2 = ['Dset','Dcalc','pixLimit','cutoff','Emat']
                File.write('{\n\t')
                for key in keys:
                    if key in 'Type':
                        File.write("'"+key+"':'"+data[key]+"',")
                    else:
                        File.write("'"+key+"':"+str(data[key])+',')
                File.write('\n\t'+"'d-zero':[\n")
                for data2 in data['d-zero']:
                    File.write('\t\t{')
                    for key in keys2:
                        File.write("'"+key+"':"+str(data2[key])+',')
                    File.write("'ImxyObs':[[],[]],'ImtaObs':[[],[]],'ImtaCalc':[[],[]]},\n")
                File.write('\t]\n}')
                File.close()
        finally:
            dlg.Destroy()
            
    def OnStrStaSample(event):
        filename = ''
        pth = G2G.GetImportPath(G2frame)
        if not pth: pth = '.'
        dlg = wx.FileDialog(G2frame, 'Choose multihistogram metadata text file', pth, '', 
            'metadata file (*.*)|*.*',wx.OPEN)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
                File = open(filename,'r')
                S = File.readline()
                newItems = []
                itemNames = []
                Comments = []
                while S:
                    if S[0] == '#':
                        Comments.append(S)
                        S = File.readline()
                        continue
                    S = S.replace(',',' ').replace('\t',' ')
                    Stuff = S[:-1].split()
                    itemNames.append(Stuff[0])
                    newItems.append(Stuff[1:])
                    S = File.readline()                
                File.close()
        finally:
            dlg.Destroy()
        if not filename:
            G2frame.ErrorDialog('Nothing to do','No file selected')
            return
        dataDict = dict(zip(itemNames,newItems))
        ifany = False
        Names = [' ','Sample phi','Sample z','Sample load']
        dlg = G2G.G2ColumnIDDialog( G2frame,' Choose multihistogram metadata columns:',
            'Select columns',Comments,Names,np.array(newItems).T)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                colNames,newData = dlg.GetSelection()
                dataDict = dict(zip(itemNames,newData.T))
                for item in colNames:
                    if item != ' ':
                        ifany = True
        finally:
            dlg.Destroy()
        if not ifany:
            G2frame.ErrorDialog('Nothing to do','No columns identified')
            return
        histList = []
        item, cookie = G2frame.PatternTree.GetFirstChild(G2frame.root)        
        while item:
            name = G2frame.PatternTree.GetItemText(item)
            if name.startswith('IMG'):
                histList.append(name)
            item, cookie = G2frame.PatternTree.GetNextChild(G2frame.root, cookie)
        colIds = {}
        for i,name in enumerate(colNames):
            if name != ' ':
                colIds[name] = i
        for hist in histList:
            name = hist.split()[1]  #this is file name
            if name in dataDict:
                newItems = {}
                for item in colIds:
                    newItems[item] = float(dataDict[name][colIds[item]])
                Id = G2gd.GetPatternTreeItemId(G2frame,G2frame.root,hist)
                stsrData = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,Id,'Stress/Strain'))
                stsrData.update(newItems)        
        UpdateStressStrain(G2frame,data)        
    
    def OnPlotStrSta(event):
        Controls = G2frame.PatternTree.GetItemPyData(
            G2gd.GetPatternTreeItemId(G2frame,G2frame.Image, 'Image Controls'))
        RingInt = G2img.IntStrSta(G2frame.ImageZ,data,Controls)
        Names = ['d=%.3f'%(ring['Dcalc']) for ring in data['d-zero']]
        G2plt.PlotExposedImage(G2frame,event=event)
        G2frame.G2plotNB.Delete('Ring Intensities')
        G2plt.PlotXY(G2frame,RingInt,labelX='Azimuth',
            labelY='MRD',newPlot=True,Title='Ring Intensities',
            names=Names,lines=True)
        
    def OnFitStrSta(event):
        Controls = G2frame.PatternTree.GetItemPyData(
            G2gd.GetPatternTreeItemId(G2frame,G2frame.Image, 'Image Controls'))
        G2img.FitStrSta(G2frame.ImageZ,data,Controls)
        print 'Strain fitting finished'
        UpdateStressStrain(G2frame,data)
        G2plt.PlotExposedImage(G2frame,event=event)
        G2plt.PlotStrain(G2frame,data,newPlot=True)
        
    def OnFitAllStrSta(event):
        choices = G2gd.GetPatternTreeDataNames(G2frame,['IMG ',])
        sel = []
        dlg = G2G.G2MultiChoiceDialog(G2frame,'Stress/Strain fitting','Select images to fit:',choices)
        dlg.SetSelections(sel)
        names = []
        if dlg.ShowModal() == wx.ID_OK:
            for sel in dlg.GetSelections():
                names.append(choices[sel])
        else:
            return
        if not names:
            return
        dlg.Destroy()
        SeqResult = {}
        Reverse = False
        CopyForward = False
        choice = ['Reverse sequence','Copy from prev.',]
        dlg = wx.MultiChoiceDialog(G2frame.dataFrame,'Sequential controls','Select controls',choice)
        if dlg.ShowModal() == wx.ID_OK:
            for sel in dlg.GetSelections():
                if sel:
                    CopyForward = True
                else:
                    Reverse = True
        dlg.Destroy()
        dlg = wx.ProgressDialog('Sequential IMG Strain fit','Data set name = '+names[0],len(names), 
            style = wx.PD_ELAPSED_TIME|wx.PD_AUTO_HIDE|wx.PD_REMAINING_TIME|wx.PD_CAN_ABORT)          
        wx.BeginBusyCursor()
        goodnames = []
        if Reverse:
            names.reverse()
        try:
            for i,name in enumerate(names):
                print ' Sequential strain fit for ',name
                GoOn = dlg.Update(i,newmsg='Data set name = '+name)[0]
                if not GoOn:
                    break
                Id =  G2gd.GetPatternTreeItemId(G2frame,G2frame.root,name)
                G2frame.Image = Id
                Controls = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,Id, 'Image Controls'))
                StaCtrls = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,Id, 'Stress/Strain'))
                if not len(StaCtrls['d-zero']):
                    continue
                goodnames.append(name)
                Npix,imagefile,imagetag = G2frame.PatternTree.GetImageLoc(Id)
                image = GetImageZ(G2frame,Controls)
                sig = []
                varyList = []
                variables = []
                if i and CopyForward:
                    for j,ring in enumerate(StaCtrls['d-zero']):
                        ring['Emat'] = variables[4*j:4*j+3]
                #get results from previous & put in StaCtrls
                G2img.FitStrSta(image,StaCtrls,Controls)
                G2plt.PlotStrain(G2frame,StaCtrls,newPlot=True)
                parmDict = {'Sample load':StaCtrls['Sample load'],}
                varyNames = ['e11','e12','e22']
                for j,item in enumerate(StaCtrls['d-zero']):
                    variables += item['Emat']
                    sig += item['Esig']
                    varylist = ['%d;%s'%(j,Name) for Name in varyNames]
                    varyList += varylist
                    parmDict.update(dict(zip(varylist,item['Emat'])))
                    parmDict['%d;Dcalc'%(j)] = item['Dcalc']
                    parmDict['%d;Ivar'%(j)] = item['Ivar']
                    variables.append(item['Ivar'])
                    varyList.append('%d;Ivar'%(j))
                    sig.append(0.)
                SeqResult[name] = {'variables':variables,'varyList':varyList,'sig':sig,'Rvals':[],
                    'covMatrix':np.eye(len(variables)),'title':name,'parmDict':parmDict}
            else:
                SeqResult['histNames'] = goodnames
                dlg.Destroy()
                print ' ***** Sequential strain refinement successful *****'
        finally:
            wx.EndBusyCursor()    
        if Reverse:
            names.reverse()
        SeqResult['histNames'] = names
        Id =  G2gd.GetPatternTreeItemId(G2frame,G2frame.root,'Sequential strain fit results')
        if Id:
            G2frame.PatternTree.SetItemPyData(Id,SeqResult)
        else:
            Id = G2frame.PatternTree.AppendItem(parent=G2frame.root,text='Sequential strain fit results')
            G2frame.PatternTree.SetItemPyData(Id,SeqResult)
        G2frame.PatternTree.SelectItem(Id)
        print 'All images fitted'
        
    def SamSizer():
        
        def OnStrainType(event):
            data['Type'] = strType.GetValue()
        
        samSizer = wx.BoxSizer(wx.HORIZONTAL)
        samSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,label=' Strain type: '),0,WACV)
        strType = wx.ComboBox(G2frame.dataDisplay,value=data['Type'],choices=['True','Conventional'],
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        strType.SetValue(data['Type'])
        strType.Bind(wx.EVT_COMBOBOX, OnStrainType)
        samSizer.Add(strType,0,WACV)
        
        samSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,label=' Sample phi: '),0,WACV)
        samPhi = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data,'Sample phi',nDig=(10,3),typeHint=float,min=-360.,max=360.)
        samSizer.Add(samPhi,0,WACV)
        samSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,label=' Sample delta-z(mm): '),0,WACV)
        samZ = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data,'Sample z',nDig=(10,3),typeHint=float)
        samSizer.Add(samZ,0,WACV)
        samSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,label=' Sample load(MPa): '),0,WACV)
        samLoad = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data,'Sample load',
                nDig=[8,3],typeHint=float,)
        samSizer.Add(samLoad,0,WACV)

        return samSizer
        
    def DzeroSizer():
    
        def OnDzero(invalid,value,tc):
            data['d-zero'] = G2mth.sortArray(data['d-zero'],'Dset',reverse=True)
            Ring,R = G2img.MakeStrStaRing(data['d-zero'][Indx[tc.GetId()]],G2frame.ImageZ,Controls)
            if len(Ring):
                data['d-zero'][Indx[tc.GetId()]].update(R)
            else:
                G2frame.ErrorDialog('Strain peak selection','WARNING - No points found for this ring selection')
                
            wx.CallAfter(UpdateStressStrain,G2frame,data)
            G2plt.PlotExposedImage(G2frame,event=tc.event,newPlot=False)
            G2plt.PlotStrain(G2frame,data,newPlot=True)
            
        def OnDeleteDzero(event):
            Obj = event.GetEventObject()
            del(data['d-zero'][delIndx.index(Obj)])
            UpdateStressStrain(G2frame,data)
            G2plt.PlotExposedImage(G2frame,event=event,newPlot=True)
            G2plt.PlotStrain(G2frame,data,newPlot=True)
        
        def OnCutOff(invalid,value,tc):
            Ring,R = G2img.MakeStrStaRing(data['d-zero'][Indx[tc.GetId()]],G2frame.ImageZ,Controls)
            G2plt.PlotExposedImage(G2frame,event=tc.event)
            G2plt.PlotStrain(G2frame,data,newPlot=True)
        
        def OnPixLimit(event):
            Obj = event.GetEventObject()
            data['d-zero'][Indx[Obj.GetId()]]['pixLimit'] = int(Obj.GetValue())
            Ring,R = G2img.MakeStrStaRing(data['d-zero'][Indx[Obj.GetId()]],G2frame.ImageZ,Controls)
            G2plt.PlotExposedImage(G2frame,event=event)
            G2plt.PlotStrain(G2frame,data,newPlot=True)
            
        Indx = {}
        delIndx = []    
        dzeroSizer = wx.FlexGridSizer(0,8,5,5)
        for id,dzero in enumerate(data['d-zero']):
            dzeroSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,label=(' d-zero #%d: '%(id))),0,WACV)
            dZero = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data['d-zero'][id],'Dset',
                min=0.25,max=20.,nDig=(10,5),typeHint=float,OnLeave=OnDzero)
            dzeroSizer.Add(dZero,0,WACV)
            Indx[dZero.GetId()] = id
            dzeroSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,label=(' d-zero ave: %.5f'%(dzero['Dcalc']))),0,WACV)
                
            dzeroSizer.Add(wx.StaticText(G2frame.dataDisplay,label=' Min ring I/Ib '),0,WACV)
            cutOff = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data['d-zero'][id],'cutoff',
                    min=0.5,max=20.,nDig=(10,1),typeHint=float,OnLeave=OnCutOff)
            Indx[cutOff.GetId()] = id
            dzeroSizer.Add(cutOff,0,WACV)
        
            dzeroSizer.Add(wx.StaticText(G2frame.dataDisplay,label=' Pixel search range '),0,WACV)
            pixLimit = wx.ComboBox(parent=G2frame.dataDisplay,value=str(dzero['pixLimit']),choices=['1','2','5','10','15','20'],
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
            pixLimit.Bind(wx.EVT_COMBOBOX, OnPixLimit)
            Indx[pixLimit.GetId()] = id
            dzeroSizer.Add(pixLimit,0,WACV)                
                
            dzeroDelete = wx.CheckBox(parent=G2frame.dataDisplay,label='delete?')
            dzeroDelete.Bind(wx.EVT_CHECKBOX,OnDeleteDzero)
            delIndx.append(dzeroDelete)
            dzeroSizer.Add(dzeroDelete,0,WACV)
            
            dzeroSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,label=(' Strain tensor:')),WACV)
            names = ['e11','e12','e22']
            for i in range(3):
                dzeroSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,label=names[i]),0,WACV)
                tensorElem = wx.TextCtrl(G2frame.dataDisplay,-1,value='%.2f'%(dzero['Emat'][i]),style=wx.TE_READONLY)
                tensorElem.SetBackgroundColour(VERY_LIGHT_GREY)
                dzeroSizer.Add(tensorElem,0,WACV)
            dzeroSizer.Add((5,5),0)             
        return dzeroSizer
        
# patches
    if 'Sample load' not in data:
        data['Sample load'] = 0.0
# end patches
    
    if G2frame.dataDisplay:
        G2frame.dataDisplay.Destroy()
    Controls = G2frame.PatternTree.GetItemPyData(
        G2gd.GetPatternTreeItemId(G2frame,G2frame.Image, 'Image Controls'))        
    G2gd.SetDataMenuBar(G2frame,G2frame.dataFrame.StrStaMenu)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnAppendDzero, id=G2gd.wxID_APPENDDZERO)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnUpdateDzero, id=G2gd.wxID_UPDATEDZERO)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnFitStrSta, id=G2gd.wxID_STRSTAFIT)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnPlotStrSta, id=G2gd.wxID_STRSTAPLOT)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnFitAllStrSta, id=G2gd.wxID_STRSTAALLFIT)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnCopyStrSta, id=G2gd.wxID_STRSTACOPY)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnLoadStrSta, id=G2gd.wxID_STRSTALOAD)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnSaveStrSta, id=G2gd.wxID_STRSTASAVE)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnStrStaSample, id=G2gd.wxID_STRSTSAMPLE)        
    if not G2frame.dataFrame.GetStatusBar():
        G2frame.dataFrame.CreateStatusBar()
    if G2frame.StrainKey == 'a':    #probably doesn't happen
        G2frame.dataFrame.GetStatusBar().SetStatusText('Add strain ring active - LB pick d-zero value')
    else:
        G2frame.dataFrame.GetStatusBar().SetStatusText("To add strain data: On 2D Powder Image, key a:add ring")
        
    G2frame.dataDisplay = wxscroll.ScrolledPanel(G2frame.dataFrame)
    mainSizer = wx.BoxSizer(wx.VERTICAL)
    mainSizer.Add((5,10),0)
    mainSizer.Add(SamSizer())
    mainSizer.Add((5,10),0)
    mainSizer.Add(DzeroSizer())
    
    mainSizer.Layout()    
    G2frame.dataDisplay.SetSizer(mainSizer)
    G2frame.dataDisplay.SetAutoLayout(1)
    G2frame.dataDisplay.SetupScrolling()
    Size = mainSizer.Fit(G2frame.dataFrame)
    Size[0] += 25
    G2frame.dataFrame.setSizePosLeft(Size)    

###########################################################################
# Autointegration follows 
def ReadMask(filename):
    'Read a mask (.immask) file'
    File = open(filename,'r')
    save = {}
    S = File.readline()
    while S:
        if S[0] == '#':
            S = File.readline()
            continue
        [key,val] = S.strip().split(':',1)
        if key in ['Points','Rings','Arcs','Polygons','Frames','Thresholds']:
            save[key] = eval(val)
        S = File.readline()
    File.close()
    CleanupMasks(save)
    return save

def ReadControls(filename):
    'read an image controls (.imctrl) file'
    cntlList = ['wavelength','distance','tilt','invert_x','invert_y','type',
            'fullIntegrate','outChannels','outAzimuths','LRazimuth','IOtth','azmthOff','DetDepth',
            'calibskip','pixLimit','cutoff','calibdmin','Flat Bkg',
            'PolaVal','SampleAbs','dark image','background image']
    File = open(filename,'r')
    save = {}
    S = File.readline()
    while S:
        if S[0] == '#':
            S = File.readline()
            continue
        [key,val] = S.strip().split(':',1)
        if key in ['type','calibrant','binType','SampleShape',]:    #strings
            save[key] = val
        elif key in ['rotation']:
            save[key] = float(val)
        elif key in ['center',]:
            if ',' in val:
                save[key] = eval(val)
            else:
                vals = val.strip('[] ').split()
                save[key] = [float(vals[0]),float(vals[1])] 
        elif key in cntlList:
            save[key] = eval(val)
        S = File.readline()
    File.close()
    return save

def Read_imctrl(imctrl_file):
    '''Read an image control file and record control parms into a dict, with some simple
    type conversions
    '''
    save = {'filename':imctrl_file}
    immask_file = os.path.splitext(imctrl_file)[0]+'.immask'
    if os.path.exists(immask_file):
        save['maskfile'] = immask_file
    else:
        save['maskfile'] = '(none)'
    cntlList = ['wavelength','distance','tilt','invert_x','invert_y','type',
                        'fullIntegrate','outChannels','outAzimuths','LRazimuth','IOtth','azmthOff','DetDepth',
                        'calibskip','pixLimit','cutoff','calibdmin','Flat Bkg',
                        'PolaVal','SampleAbs','dark image','background image']
    File = open(imctrl_file,'r')
    fullIntegrate = False
    try:
        S = File.readline()
        while S:
            if S[0] == '#':
                S = File.readline()
                continue
            [key,val] = S.strip().split(':',1)
            if val.find(':') != -1:
                #print 'rejecting ',key,val
                S = File.readline()
                continue
            if key in ['type','calibrant','binType','SampleShape',]:    #strings
                save[key] = val
            elif key == 'rotation':
                save[key] = float(val)
            elif key == 'fullIntegrate':
                fullIntegrate = eval(val)
            elif key == 'LRazimuth':
                save['LRazimuth_min'],save['LRazimuth_max'] = eval(val)[0:2]
            elif key == 'IOtth':
                save['IOtth_min'],save['IOtth_max'] = eval(val)[0:2]
            elif key == 'center':
                if ',' in val:
                    vals = eval(val)
                else:
                    vals = val.strip('[] ').split()
                    vals = [float(vals[0]),float(vals[1])] 
                save['center_x'],save['center_y'] = vals[0:2]
            elif key in cntlList:
                save[key] = eval(val)
            S = File.readline()
    finally:
        File.close()
        if fullIntegrate: save['LRazimuth_min'],save['LRazimuth_max'] = 0.,0.
    return save
    
class AutoIntFrame(wx.Frame):
    '''Creates a wx.Frame window for the Image AutoIntegration.
    The intent is that this will be used as a non-modal dialog window.
    
    Implements a Start button that morphs into a pause and resume button.
    This button starts a processing loop that is repeated every
    :meth:`PollTime` seconds.

    :param wx.Frame G2frame: main GSAS-II frame
    :param float PollTime: frequency in seconds to repeat calling the
      processing loop. (Default is 3.0 seconds.)
    '''

    def __init__(self,G2frame,PollTime=60.0):
        def OnStart(event):
            '''Called when the start button is pressed. Changes button label 
            to Pause. When Pause is pressed the label changes to Resume.
            When either Start or Resume is pressed, the processing loop
            is started. When Pause is pressed, the loop is stopped. 
            '''
            # check inputs for errors before starting
            #err = ''
            #if not any([self.params[fmt] for fmt in self.fmtlist]):
            #    err += '\nPlease select at least one output format\n'
            #if err:
            #    G2G.G2MessageBox(self,err)
            #    return
            self.Pause = False
            # change button label
            if self.btnstart.GetLabel() != 'Pause':
                self.btnstart.SetLabel('Pause')
                self.Status.SetStatusText('Press Pause to delay integration or Reset to prepare to reintegrate all images')
                if self.timer.IsRunning(): self.timer.Stop()
                self.PreventReEntryTimer = False
                self.StartLoop()
                self.OnTimerLoop(None) # run once immediately
                if not self.Pause:
                    # no pause, so start timer to check for new files
                    self.timer.Start(int(1000*PollTime),oneShot=False)
                    return
            # we will get to this point if Paused
            self.OnPause()
            
        def OnReset(event):
            '''Called when Reset button is pressed. This stops the
            processing loop and resets the list of integrated files so
            all images can be reintegrated. 
            '''
            self.btnstart.SetLabel('Restart')
            self.Status.SetStatusText('Press Restart to reload and re-integrate images matching filter')
            if self.timer.IsRunning(): self.timer.Stop()
            self.Reset = True
            self.Pause = True
            
        def OnQuit(event):
            '''Stop the processing loop and close the Frame
            '''
            if self.timer.IsRunning(): self.timer.Stop() # make sure we stop first
            wx.CallAfter(self.Destroy)
            
        def OnBrowse(event):
            '''Responds when the Browse button is pressed to load a file.
            The routine determines which button was pressed and gets the
            appropriate file type and loads it into the appropriate place
            in the dict.
            '''
            if btn3 == event.GetEventObject():
                dlg = wx.DirDialog(
                    self, 'Select directory for output files',
                    self.params['outdir'],wx.DD_DEFAULT_STYLE)
                dlg.CenterOnParent()
                try:
                    if dlg.ShowModal() == wx.ID_OK:
                        self.params['outdir'] = dlg.GetPath()
                        fInp3.SetValue(self.params['outdir'])
                finally:
                    dlg.Destroy()
                return
                
        def OnRadioSelect(event):
            '''Respond to a radiobutton selection and when in table
            mode, get distance-dependent parameters from user. 
            '''
            self.Evaluator = None
            if self.useTable.GetValue():
                dlg = None
                try:
                    dlg = IntegParmTable(self) # create the dialog
                    dlg.CenterOnParent()
                    if dlg.ShowModal() == wx.ID_OK:
                        self.ImgTblParms = dlg.parms
                        self.IMfileList = dlg.IMfileList
                        self.Evaluator = DefineEvaluator(dlg)
                        self.params['Mode'] = 'table'
                        self.editTable.Enable(True)
                    else:
                        self.useActive.SetValue(True)
                finally:
                    if dlg: dlg.Destroy()
            elif self.useActive.GetValue():
                self.params['Mode'] = 'active'
                self.imageBase = G2frame.Image
                self.useActive.SetLabel("Active Image: "+
                        G2frame.PatternTree.GetItemText(self.imageBase))
                self.editTable.Enable(False)
            else:
                print('unexpected mode in OnRadioSelect')

        def OnEditTable(event):
            '''Called to edit the distance-dependent parameter look-up table.
            Should be called only when table is defined and active.
            '''
            try:
                dlg = IntegParmTable(self.G2frame,self.ImgTblParms,self.IMfileList)
                dlg.CenterOnParent()
                if dlg.ShowModal() == wx.ID_OK:
                    self.ImgTblParms = dlg.parms
                    self.IMfileList = dlg.IMfileList
                    self.Evaluator = DefineEvaluator(dlg)
                    self.params['Mode'] = 'table'
                    self.editTable.Enable(True)
                else:
                    self.useActive.SetValue(True)
                    self.params['Mode'] = 'active'
                    self.imageBase = G2frame.Image
                    self.useActive.SetLabel("Active Image: "+
                            G2frame.PatternTree.GetItemText(self.imageBase))
                    self.editTable.Enable(False)
            finally:
                dlg.Destroy()

        ##################################################
        # beginning of __init__ processing
        ##################################################
        self.G2frame = G2frame
        self.ImgTblParms = None
        self.IMfileList = None
        self.Evaluator = None
        self.params = {}
        self.Reset = False
        self.Pause = False
        self.PreventReEntryShowMatch = False
        self.PreventReEntryTimer = False
        self.params['IMGfile'] = ''
        self.params['MaskFile'] = ''
        self.params['IgnoreMask'] = True
        self.fmtlist = G2IO.ExportPowderList(G2frame)
        self.timer = wx.Timer()
        self.timer.Bind(wx.EVT_TIMER,self.OnTimerLoop)
        self.imageBase = G2frame.Image

        G2frame.PatternTree.GetSelection()
        size,imagefile,imagetag = G2frame.PatternTree.GetImageLoc(self.imageBase)        
        self.imagedir,fileroot = os.path.split(imagefile)
        self.params['filter'] = '*'+os.path.splitext(fileroot)[1]
        self.params['outdir'] = os.path.abspath(self.imagedir)
        wx.Frame.__init__(self, G2frame, title='Automatic Integration',
                          style=wx.DEFAULT_FRAME_STYLE ^ wx.CLOSE_BOX)
        self.Status = self.CreateStatusBar()
        self.Status.SetStatusText('Press Start to load and integrate images matching filter')
        mnpnl = wx.Panel(self)
        mnsizer = wx.BoxSizer(wx.VERTICAL)
        # box for integration controls & masks input
        lbl = wx.StaticBox(mnpnl, wx.ID_ANY, "Integration Control")
        lblsizr = wx.StaticBoxSizer(lbl, wx.VERTICAL)
        lblsizr.Add(wx.StaticText(mnpnl, wx.ID_ANY,'Use integration parameters from:'))
        self.useActive = wx.RadioButton(mnpnl, wx.ID_ANY, 
                            style = wx.RB_GROUP)
        self.useActive.Bind(wx.EVT_RADIOBUTTON, OnRadioSelect)
        self.useActive.SetLabel("Active Image: "+
                                G2frame.PatternTree.GetItemText(self.imageBase))
        lblsizr.Add(self.useActive,1,wx.EXPAND,1)
        self.useActive.SetValue(True)
        minisizer = wx.BoxSizer(wx.HORIZONTAL)
        self.useTable = wx.RadioButton(mnpnl, wx.ID_ANY, "From distance look-up table")
        minisizer.Add(self.useTable,0,wx.ALIGN_LEFT|wx.ALL,1)
        self.useTable.Bind(wx.EVT_RADIOBUTTON, OnRadioSelect)
        self.editTable = wx.Button(mnpnl,  wx.ID_ANY, "Edit table")
        minisizer.Add(self.editTable,0,wx.ALIGN_LEFT,10)
        self.editTable.Enable(False)
        self.editTable.Bind(wx.EVT_BUTTON, OnEditTable)
        # bind button and deactivate be default
        lblsizr.Add(minisizer)
        mnsizer.Add(lblsizr,1,wx.EXPAND,1)

        # file filter stuff
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(mnpnl, wx.ID_ANY,'Image filter'))
        flterInp = G2G.ValidatedTxtCtrl(mnpnl,self.params,'filter',OnLeave=self.ShowMatchingFiles)
        sizer.Add(flterInp)
        mnsizer.Add(sizer,0,wx.ALIGN_RIGHT,1)
        self.ListBox = wx.ListBox(mnpnl,size=(-1,100))
        mnsizer.Add(self.ListBox,0,wx.EXPAND,1)
        self.ShowMatchingFiles(self.params['filter'])
        # box for output selections
        lbl = wx.StaticBox(mnpnl, wx.ID_ANY, "Output settings")
        lblsizr = wx.StaticBoxSizer(lbl, wx.VERTICAL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(mnpnl, wx.ID_ANY,'Write to: '))
        fInp3 = G2G.ValidatedTxtCtrl(mnpnl,self.params,'outdir',notBlank=False,size=(300,-1))
        sizer.Add(fInp3)
        btn3 = wx.Button(mnpnl,  wx.ID_ANY, "Browse")
        btn3.Bind(wx.EVT_BUTTON, OnBrowse)
        sizer.Add(btn3)
        lblsizr.Add(sizer)
        #lblsizr.Add(wx.StaticText(mnpnl, wx.ID_ANY,'Select format(s): '))
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(mnpnl, wx.ID_ANY,'Select format(s): '))
        for dfmt in self.fmtlist:
            fmt = dfmt[1:]
            self.params[fmt] = False
            btn = G2G.G2CheckBox(mnpnl,dfmt,self.params,fmt)
            sizer.Add(btn)
        lblsizr.Add(sizer)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(wx.StaticText(mnpnl, wx.ID_ANY,'Separate dir for each format: '))
        self.params['SeparateDir'] = False
        sizer.Add(G2G.G2CheckBox(mnpnl,'',self.params,'SeparateDir'))
        lblsizr.Add(sizer)
        mnsizer.Add(lblsizr,0,wx.ALIGN_CENTER,1)

        # buttons on bottom
        mnsizer.Add(wx.StaticText(mnpnl, wx.ID_ANY,'AutoIntegration controls'),0,wx.TOP,5)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add((20,-1))
        self.btnstart = wx.Button(mnpnl,  wx.ID_ANY, "Start")
        self.btnstart.Bind(wx.EVT_BUTTON, OnStart)
        sizer.Add(self.btnstart)
        self.btnreset = wx.Button(mnpnl,  wx.ID_ANY, "Reset")
        self.btnreset.Bind(wx.EVT_BUTTON, OnReset)
        sizer.Add(self.btnreset)
        sizer.Add((20,-1),wx.EXPAND,1)
        self.btnclose = wx.Button(mnpnl,  wx.ID_ANY, "Close")
        self.btnclose.Bind(wx.EVT_BUTTON, OnQuit)
        sizer.Add(self.btnclose)
        sizer.Add((20,-1))
        mnsizer.Add(sizer,0,wx.EXPAND|wx.BOTTOM|wx.TOP,5)
        
        # finish up window
        mnpnl.SetSizer(mnsizer)
        OnRadioSelect(None) # disable widgets
        mnsizer.Fit(self)
        self.CenterOnParent()
        self.Show()

    def ShowMatchingFiles(self,value,invalid=False,**kwargs):
        G2frame = self.G2frame
        if invalid: return
        msg = ''
        if self.PreventReEntryShowMatch: return
        self.PreventReEntryShowMatch = True
        imageFileList = []
        for img in G2gd.GetPatternTreeDataNames(G2frame,['IMG ']):
            imgId = G2gd.GetPatternTreeItemId(G2frame,G2frame.root,img)
            size,imagefile,imagetag = G2frame.PatternTree.GetImageLoc(imgId)
            if imagefile not in imageFileList: imageFileList.append(imagefile)
            if img not in G2frame.IntegratedList:
                if msg: msg += '\n'
                msg += '  ' + img
        if msg: msg = "Loaded images to integrate:\n" + msg + "\n"
        msg1 = ""
        try:
            imageList = sorted(
                glob.glob(os.path.join(self.imagedir,value)))
            if not imageList:
                msg1 = 'Warning: No files match search string '+os.path.join(self.imagedir,value)
            else:
                for fil in imageList:
                    if fil not in imageFileList: msg1 += '\n  '+fil
                if msg1:
                    msg += 'Files to integrate from '+os.path.join(self.imagedir,value)+msg1
                else:
                    msg += 'All files integrated'
        except IndexError:
            msg += 'Error searching for files named '+os.path.join(self.imagedir,value)
        self.ListBox.Clear()
        self.ListBox.AppendItems(msg.split('\n'))
        self.PreventReEntryShowMatch = False
        return
        
    def OnPause(self):
        '''Respond to Pause, changes text on button/Status line, if needed
        Stops timer
        self.Pause should already be True
        '''
        if self.timer.IsRunning(): self.timer.Stop()
        if self.btnstart.GetLabel() == 'Restart':
            return
        if self.btnstart.GetLabel() != 'Resume':
            print('\nPausing autointegration\n')
            self.btnstart.SetLabel('Resume')
            self.Status.SetStatusText(
                    'Press Resume to continue integration or Reset to prepare to reintegrate all images')
        self.Pause = True
            
    def IntegrateImage(self,img):
        '''Integrates a single image'''
        G2frame = self.G2frame
        imgId = G2gd.GetPatternTreeItemId(G2frame,G2frame.root,img)
        G2frame.Image = imgId
        G2frame.PickId = G2gd.GetPatternTreeItemId(G2frame,G2frame.Image, 'Image Controls')
        # do integration
        size,imagefile,imagetag = G2frame.PatternTree.GetImageLoc(imgId)
        masks = G2frame.PatternTree.GetItemPyData(
            G2gd.GetPatternTreeItemId(G2frame,G2frame.Image, 'Masks'))
        data = G2frame.PatternTree.GetItemPyData(G2frame.PickId)
        # simulate a Image Controls press, since that is where the
        # integration is hidden
        UpdateImageControls(G2frame,data,masks,IntegrateOnly=True)
        G2frame.IntegratedList.append(img) # note this as integrated
        # split name and control number
        s = re.split(r'(\d+)\Z',os.path.split(os.path.splitext(imagefile)[0])[1])
        namepre = s[0]
        if len(s) > 1:
            namenum = s[1]
        else:
            namenum = ''
        for Id in G2frame.IntgOutList: # loop over newly created PDWR entry(ies)
            # save the created PWDR tree names so that a reset can delete them
            G2frame.Image = Id
            treename = G2frame.PatternTree.GetItemText(Id)
            G2frame.AutointPWDRnames.append(treename)
            # write out the images in the selected formats
            Sdata = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,Id, 'Sample Parameters'))
            # determine the name for the current file
            fileroot = namepre
            if len(G2frame.IntgOutList) > 1:
                fileroot += "_AZM"
                if 'Azimuth' in Sdata:
                    fileroot += str(int(10*Sdata['Azimuth']))
                fileroot += "_" 
            fileroot += namenum
            # loop over selected formats
            for dfmt in self.fmtlist:
                if not self.params[dfmt[1:]]: continue
                if self.params['SeparateDir']:
                    subdir = dfmt[1:]
                else:
                    subdir = ''
                fil = os.path.join(self.params['outdir'],subdir,fileroot)
                print('writing file '+fil+dfmt)
                G2IO.ExportPowder(G2frame,treename,fil,dfmt)
                
    def EnableButtons(self,flag):
        '''Relabels and enable/disables the buttons at window bottom when auto-integration is running
        '''
        # for unclear reasons disabling these buttons causes OnRadioSelect to be invoked
        # on windows
        if sys.platform != "win32":
            for item in (self.btnstart,self.btnreset,self.btnclose): item.Enable(flag)
        if flag:
            self.btnstart.SetLabel('Pause')
        else:
            self.btnstart.SetLabel('(running)')
        wx.Yield()
                
    def ResetFromTable(self,dist):
        '''Sets integration parameters based on values from
        the lookup table
        '''
        #dist = self.controlsDict['distance']
        interpDict,imgctrl,immask = self.Evaluator(dist) # interpolated calibration values
        #if GSASIIpath.GetConfigValue('debug'):
        if GSASIIpath.GetConfigValue('debug'):
            print 'interpolated values: ',interpDict
        self.ImageControls = ReadControls(imgctrl)
        self.ImageControls.update(interpDict)
        self.ImageControls['showLines'] = True
        self.ImageControls['ring'] = []
        self.ImageControls['rings'] = []
        self.ImageControls['ellipses'] = []
        self.ImageControls['setDefault'] = False
        for i in 'range','size','GonioAngles':
            if i in self.ImageControls:
                del self.ImageControls[i]
        # load copy of Image Masks
        if immask:
            self.ImageMasks = ReadMask(immask)
            if list(self.ImageMasks['Thresholds'][0]) == self.ImageMasks['Thresholds'][1]:     #avoid copy of unchanged thresholds
                del self.ImageMasks['Thresholds']
        else:
            self.ImageMasks = {'Points':[],'Rings':[],'Arcs':[],'Polygons':[],'Frames':[]}
        
    def StartLoop(self):
        '''Save current Image params for use in future integrations
        also label the window so users understand what is being used
        '''
        print '\nStarting new autointegration\n'
        G2frame = self.G2frame
        # show current IMG base
        if self.params['Mode'] != 'table':
            self.useActive.SetLabel("Active Image: "+
                                    G2frame.PatternTree.GetItemText(self.imageBase))
            # load copy of Image Controls from current image and clean up
            # items that should not be copied
            self.ImageControls = copy.deepcopy(
                G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(
                    G2frame,self.imageBase, 'Image Controls')))
            self.ImageControls['showLines'] = True
            self.ImageControls['ring'] = []
            self.ImageControls['rings'] = []
            self.ImageControls['ellipses'] = []
            self.ImageControls['setDefault'] = False
            del self.ImageControls['range']
            del self.ImageControls['size']
            del self.ImageControls['GonioAngles']
            # load copy of Image Masks, keep thresholds
            self.ImageMasks = copy.deepcopy(
                G2frame.PatternTree.GetItemPyData(
                    G2gd.GetPatternTreeItemId(G2frame,self.imageBase, 'Masks')))
            self.Thresholds = self.ImageMasks['Thresholds'][:]
            if list(self.Thresholds[0]) == self.Thresholds[1]:     #avoid copy of unchanged thresholds
                del self.ImageMasks['Thresholds']   
        # make sure all output directories exist
        if self.params['SeparateDir']:
            for dfmt in self.fmtlist:
                if not self.params[dfmt[1:]]: continue
                dir = os.path.join(self.params['outdir'],dfmt[1:])
                if not os.path.exists(dir): os.makedirs(dir)
        else:
            if not os.path.exists(self.params['outdir']):
                os.makedirs(self.params['outdir'])
        if self.Reset: # special things to do after Reset has been pressed
            self.G2frame.IntegratedList = []
            
            if self.params['Mode'] != 'table': # reset controls and masks for all IMG items in tree to master
                for img in G2gd.GetPatternTreeDataNames(G2frame,['IMG ']):
                    # update controls from master
                    controlsDict = G2frame.PatternTree.GetItemPyData(
                        G2gd.GetPatternTreeItemId(G2frame,self.imageBase, 'Image Controls'))
                    controlsDict.update(self.ImageControls)
                    # update masks from master
                    ImageMasks = G2frame.PatternTree.GetItemPyData(
                        G2gd.GetPatternTreeItemId(G2frame,self.imageBase, 'Masks'))
                    ImageMasks.update(self.ImageMasks)
            # delete all PWDR items created after last Start was pressed 
            idlist = []
            item, cookie = G2frame.PatternTree.GetFirstChild(G2frame.root)
            while item:
                itemName = G2frame.PatternTree.GetItemText(item)
                if itemName in G2frame.AutointPWDRnames:
                    idlist.append(item)
                item, cookie = G2frame.PatternTree.GetNextChild(G2frame.root, cookie)
            for item in idlist:
                G2frame.PatternTree.Delete(item)
            wx.Yield()
            self.Reset = False
        G2frame.AutointPWDRnames = [] # list of created PWDR tree item names

    def OnTimerLoop(self,event):
        '''A method that is called every :meth:`PollTime` seconds that is
        used to check for new files and process them. This is called only
        after the "Start" button is pressed (then its label reads "Pause").
        '''
        G2frame = self.G2frame
        try:
            self.currImageList = sorted(
                glob.glob(os.path.join(self.imagedir,self.params['filter'])))
            self.ShowMatchingFiles(self.params['filter'])
        except IndexError:
            self.currImageList = []
            return

        if self.PreventReEntryTimer: return
        self.PreventReEntryTimer = True
        imageFileList = []
        # integrate the images that have already been read in, but
        # have not yet been processed
        for img in G2gd.GetPatternTreeDataNames(G2frame,['IMG ']):
            imgId = G2gd.GetPatternTreeItemId(G2frame,G2frame.root,img)
            size,imagefile,imagetag = G2frame.PatternTree.GetImageLoc(imgId)
            # Create a list of image files that have been read in
            if imagefile not in imageFileList: imageFileList.append(imagefile)
            # skip if already integrated
            if img in G2frame.IntegratedList: continue
            controlsDict = G2frame.PatternTree.GetItemPyData(
                G2gd.GetPatternTreeItemId(G2frame,imgId, 'Image Controls'))
            ImageMasks = G2frame.PatternTree.GetItemPyData(
                G2gd.GetPatternTreeItemId(G2frame,imgId, 'Masks'))
            if self.params['Mode'] == 'table': # look up parameter values from table
                self.ResetFromTable(controlsDict['distance'])
            # update controls from master
            controlsDict.update(self.ImageControls)
            # update masks from master w/o Thresholds
            ImageMasks.update(self.ImageMasks)
            self.EnableButtons(False)
            try:
                self.IntegrateImage(img)
            finally:
                self.EnableButtons(True)
            self.Pause |= G2frame.PauseIntegration
            self.G2frame.oldImagefile = '' # mark image as changed; reread as needed
            wx.Yield()
            self.ShowMatchingFiles(self.params['filter'])
            wx.Yield()
            if self.Pause:
                self.OnPause()
                self.PreventReEntryTimer = False
                return

        # loop over image files matching glob, reading in any new ones
        for newImage in self.currImageList:

            if newImage in imageFileList or self.Pause: continue # already read?
            for imgId in G2IO.ReadImages(G2frame,newImage):
                controlsDict = G2frame.PatternTree.GetItemPyData(
                    G2gd.GetPatternTreeItemId(G2frame,imgId, 'Image Controls'))
                ImageMasks = G2frame.PatternTree.GetItemPyData(
                    G2gd.GetPatternTreeItemId(G2frame,imgId, 'Masks'))
                if self.params['Mode'] == 'table': # look up parameter values from table
                    self.ResetFromTable(controlsDict['distance'])
                # update controls from master
                controlsDict.update(self.ImageControls)
                # update masks from master w/o Thresholds
                ImageMasks.update(self.ImageMasks)
                # now integrate the image
                img = G2frame.PatternTree.GetItemText(imgId)
                self.EnableButtons(False)
                try:
                    self.IntegrateImage(img)
                finally:
                    self.EnableButtons(True)
                self.Pause |= G2frame.PauseIntegration
                self.G2frame.oldImagefile = '' # mark image as changed; reread as needed
                wx.Yield()
                self.ShowMatchingFiles(self.params['filter'])
                wx.Yield()
            if self.Pause:
                self.OnPause()
                break
        
        if GSASIIpath.GetConfigValue('debug'):
            import datetime
            print ("Timer tick at {:%d %b %Y %H:%M:%S}\n".format(datetime.datetime.now()))
        self.PreventReEntryTimer = False

def DefineEvaluator(dlg):
    '''Creates a function that provides interpolated values for a given distance value
    '''
    def Evaluator(dist):
        '''Interpolate image parameters for a supplied distance value

        :param float dist: distance to use for interpolation
        :returns: a list with 3 items:

          * a dict with parameter values,
          * the closest imctrl and
          * the closest maskfile (or None)
        '''            
        x = np.array([float(i) for i in parms[0]])
        closest = abs(x-dist).argmin()
        D = {'distance':dist}
        imctfile = IMfileList[closest]
        if parms[-1][closest].lower() != '(none)':
            maskfile = parms[-1][closest]
        else:
            maskfile = None
        for c in range(1,cols-1):
            lbl = ParmList[c]
            if lbl in nonInterpVars:
                if lbl in ['outChannels',]:
                    D[lbl] = int(float(parms[c][closest]))
                else:
                    D[lbl] = float(parms[c][closest])
            else:
                y = np.array([float(i) for i in parms[c]])
                D[lbl] = np.interp(dist,x,y)
        # full integration when angular range is 0
        D['fullIntegrate'] = (D['LRazimuth_min'] == D['LRazimuth_max'])
        # conversion for paired values
        for a,b in ('center_x','center_y'),('LRazimuth_min','LRazimuth_max'),('IOtth_min','IOtth_max'):
            r = a.split('_')[0]
            D[r] = [D[a],D[b]]
            if r in ['LRazimuth',]:
                D[r] = [int(D[a]),int(D[b])]
            del D[a]
            del D[b]
        return D,imctfile,maskfile
    # save local copies of values needed in Evaluator
    parms = dlg.ReadImageParmTable()
    IMfileList = dlg.IMfileList
    cols = dlg.list.GetColumnCount()
    ParmList = dlg.ParmList
    nonInterpVars = dlg.nonInterpVars
    return Evaluator

class IntegParmTable(wx.Dialog):
    '''Creates a dialog window with a table of integration parameters.
    :meth:`ShowModal` will return wx.ID_OK if the process has been successful.
    In this case, :func:`DefineEvaluator` should be called to obtain a function that
    creates a dictionary with interpolated parameter values.
    '''
    ParmList = ('distance','center_x','center_y','wavelength','tilt','rotation','DetDepth',
            'LRazimuth_min','LRazimuth_max','IOtth_min','IOtth_max','outChannels',
            'maskfile',
            )
    nonInterpVars = ('tilt','rotation','LRazimuth_min','LRazimuth_max','IOtth_min','IOtth_max',
                     'outChannels')  # values in this list are taken from nearest rather than interpolated
    HeaderList = ('Det Dist','X cntr','Y cntr','wavelength','tilt','rotation','DetDepth',
            'Azimuth min','Azimuth max','2Th min','2Th max','Int. pts',
            'Mask File',
            )
    def __init__(self,parent,parms=None,IMfileList=None):
        self.G2frame = parent.G2frame
        wx.Dialog.__init__(self,parent,style=wx.RESIZE_BORDER|wx.DEFAULT_DIALOG_STYLE)
        if parms:
            self.parms = parms # list of values by column
            self.IMfileList = IMfileList # list of .imctrl file names for each entry in table
        else:
            self.parms = [] # list of values by column
            self.IMfileList = [] # list of .imctrl file names for each entry in table
            files = []
            try:
                pth = G2G.GetImportPath(self.G2frame)
                if not pth: pth = '.'
                dlg = wx.FileDialog(parent, 'Read previous table or build new table by selecting image control files', pth,
                    style=wx.OPEN| wx.MULTIPLE,
                    wildcard='Integration table (*.imtbl)|*.imtbl|image control files (.imctrl)|*.imctrl')
                dlg.CenterOnParent()
                if dlg.ShowModal() == wx.ID_OK:
                    files = dlg.GetPaths()
                    self.parms,self.IMfileList = self.ReadFiles(files)
            finally:
                dlg.Destroy()
            if not files:
                wx.CallAfter(self.EndModal,wx.ID_CANCEL)
                return
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.list = ImgIntLstCtrl(self, wx.ID_ANY,
                      style=wx.LC_REPORT 
                          | wx.BORDER_SUNKEN
                         #| wx.BORDER_NONE
                         )
        mainSizer.Add(self.list,1,wx.EXPAND,1)
        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        btn = wx.Button(self, wx.ID_OK)
        btnsizer.Add(btn)
        btn = wx.Button(self, wx.ID_ANY,'Save as file')
        btn.Bind(wx.EVT_BUTTON,self._onSave)
        btnsizer.Add(btn)
        btn = wx.Button(self, wx.ID_CLOSE,'Quit')
        btn.Bind(wx.EVT_BUTTON,self._onClose)
        btnsizer.Add(btn)
        mainSizer.Add(btnsizer, 0, wx.ALIGN_CENTER|wx.ALL, 5)    
        self.SetSizer(mainSizer)
        self.list.FillList(self.parms)
        mainSizer.Layout()
        mainSizer.Fit(self)
        
    def ReadFiles(self,files):
        '''Reads a list of .imctrl files or a single .imtbl file
        '''
        tmpDict = {}
        if not files: return
        # option 1, a dump from a previous save
        if os.path.splitext(files[0])[1] == '.imtbl':
            fp = open(files[0],'r')
            S = fp.readline()
            while S:
                if S[0] != '#':
                    [key,val] = S[:-1].split(':',1)
                    tmpDict[key] = eval(val)
                S = fp.readline()
            fp.close()
            # delete entries where files do not exist
            m1 = [i for i,f in enumerate(tmpDict['filenames']) if not os.path.exists(f)]
            if m1:
                print('\nimctrl file not found:')
                for i in m1: print('\t#'+str(i)+': '+tmpDict['filenames'][i])
            m2 = [i for i,f in enumerate(tmpDict['maskfile']) if not (os.path.exists(f) or f.startswith('('))]
            if m2:
                print('\nmask file not found')
                for i in m2: print('\t#'+str(i)+': '+tmpDict['maskfile'][i])
            m3 = [i for i,d in enumerate(tmpDict['distance']) if d < 0]
            if m3:
                print('\nDropping entries due to negative distance: '+str(m3))
            m = sorted(set(m1 + m2 + m3))
            m.reverse()
            for c in m:
                for key in tmpDict:
                    del tmpDict[key][c]
            fileList = tmpDict.get('filenames','[]')
            parms = []
            for key in self.ParmList:
                try:
                    float(tmpDict[key][0])
                    parms.append([str(G2py3.FormatSigFigs(val1,sigfigs=5)) for val1 in tmpDict[key]])
                except ValueError:
                    parms.append(tmpDict[key])
                except IndexError:
                    print('No valid image control entries read')
                    wx.CallAfter(self.EndModal,wx.ID_CANCEL)
                    return [[]],[]
            return parms,fileList
        # option 2, read in a list of files
        for file in files: # read all files; place in dict by distance
            imgDict = Read_imctrl(file)
            tmpDict[imgDict.get('distance')] = imgDict
        parms = [[] for key in self.ParmList]
        fileList = []
        for d in sorted(tmpDict):
            fileList.append(tmpDict[d].get('filename'))
            if d is None: continue
            if d < 0: continue
            for i,key in enumerate(self.ParmList):
                val = tmpDict[d].get(key)
                try:
                    val = str(G2py3.FormatSigFigs(val,sigfigs=5))
                except:
                    val = str(val)
                parms[i].append(val)
        return parms,fileList
    
    def ReadImageParmTable(self):
        '''Reads possibly edited values from the ListCtrl table and returns a list
        of values for each column.
        '''
        rows = self.list.GetItemCount()
        cols = self.list.GetColumnCount()
        parms = []
        for c in range(cols):
            parms.append([])
            for r in range(rows):
                parms[c].append(self.list.GetItem(r,c).GetText())
        return parms

    def _onClose(self,event):
        'Called when Cancel button is pressed'
        self.EndModal(wx.ID_CANCEL)
        
    def _onSave(self,event):
        'Called when save button is pressed; creates a .imtbl file'
        fil = ''
        if self.G2frame.GSASprojectfile:
            fil = os.path.splitext(self.G2frame.GSASprojectfile)[0]+'.imtbl'
        dir,f = os.path.split(fil)
        pth = G2G.GetExportPath(self.G2frame)
        try:
            dlg = wx.FileDialog(self, 'Save table data as',
                        defaultDir=pth, defaultFile=f, style=wx.SAVE,
                        wildcard='G2 Image Param Table file (*.imtbl)|*.imtbl')
            dlg.CenterOnParent()
            if dlg.ShowModal() != wx.ID_OK: return
            fil = dlg.GetPath()
            fil = os.path.splitext(fil)[0]+'.imtbl'
        finally:
            dlg.Destroy()        
        parms = self.ReadImageParmTable()
        print('Writing image parameter table as '+fil)
        fp = open(fil,'w')
        for c in range(len(parms)-1):
            lbl = self.ParmList[c]
            fp.write(lbl+': '+str([eval(i) for i in parms[c]])+'\n')
        lbl = self.ParmList[c+1]
        fp.write(lbl+': '+str(parms[c+1])+'\n')
        lbl = 'filenames'
        fp.write(lbl+': '+str(self.IMfileList)+'\n')
        fp.close()
    
class ImgIntLstCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin,listmix.TextEditMixin):
    '''Creates a custom ListCtrl for editing Image Integration parameters
    '''
    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=(1000,200), style=0):
        self.parent=parent
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        listmix.TextEditMixin.__init__(self)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDouble)
        #self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick)
    def FillList(self,parms):
        'Places the current parms into the table'
        self.ClearAll()
        self.rowlen = len(self.parent.ParmList)
        for i,lbl in enumerate(self.parent.HeaderList):
            self.InsertColumn(i, lbl)
        for r,d in enumerate(parms[0]):
            if float(d) < 0: continue
            index = self.InsertStringItem(sys.maxint, d)
            for j in range(1,len(parms)):
                self.SetStringItem(index, j, parms[j][r])
        for i,lbl in enumerate(self.parent.ParmList):
            self.SetColumnWidth(i, wx.LIST_AUTOSIZE)

    def OnDouble(self,evt):
        'respond to a double-click'
        self.CloseEditor()
        fil = '(none)'
        pth = G2G.GetImportPath(self.parent.G2frame)
        if not pth: pth = '.'
        try:
            dlg = wx.FileDialog(self, 'Select mask or control file to add (Press cancel if none)', pth,
                                style=wx.OPEN,
                                wildcard='Add GSAS-II mask file (.immask)|*.immask|add image control file (.imctrl)|*.imctrl')
            dlg.CenterOnParent()
            if dlg.ShowModal() == wx.ID_OK:
                fil = dlg.GetPath()
        finally:
            dlg.Destroy()
        if os.path.splitext(fil)[1] != '.imctrl':
            self.SetStringItem(self.curRow, self.rowlen-1, fil)
            self.SetColumnWidth(self.rowlen-1, wx.LIST_AUTOSIZE)
        else:
            # insert or overwrite an instrument parameter set
            if not os.path.exists(fil):
                print('Does not exist: '+fil)
                return
            imgDict = Read_imctrl(fil)
            dist = imgDict['distance']
            parms = self.parent.ReadImageParmTable()
            x = np.array([float(i) for i in parms[0]])
            closest = abs(x-dist).argmin()
            closeX = x[closest]
            # fix IMfileList
            for c,lbl in enumerate(self.parent.ParmList):
                try:
                    vali = G2py3.FormatSigFigs(float(imgDict[lbl]),sigfigs=5)
                except ValueError:
                    vali = imgDict[lbl]
                if abs(closeX-dist) < 1.: # distance is within 1 mm, replace
                    parms[c][closest] = vali
                elif dist > closeX: # insert after
                    parms[c].insert(closest+1,vali)
                else:
                    parms[c].insert(closest,vali)
            if abs(closeX-dist) < 1.: # distance is within 1 mm, replace
                self.parent.IMfileList[closest] = fil
            elif dist > closeX: # insert after
                self.parent.IMfileList.insert(closest+1,fil)
            else:
                self.parent.IMfileList.insert(closest,fil)
            self.FillList(parms)
# Autointegration end
###########################################################################
