#testMagSym
import sys
import wx
import numpy as np
import GSASIIpath
GSASIIpath.SetBinaryPath()
import GSASIIspc as G2spc
import GSASIIctrlGUI as G2G
import GSASIIphsGUI as G2phsGUI

try:
    wx.NewId
except AttributeError:
    wx.NewId = wx.NewIdRef
    
[wxID_FILEEXIT, 
] = [wx.NewId() for _init_coll_File_Items in range(1)]
WACV = wx.ALIGN_CENTER_VERTICAL

class testSytSym(wx.Frame):

    def _init_ctrls(self, parent):
        wx.Frame.__init__(self, name='testSytSym', parent=parent,
            size=[800,300],style=wx.DEFAULT_FRAME_STYLE, title='Test space group site symmetry')
        self.testSSMenu = wx.MenuBar()
        self.File = wx.Menu(title='')
        self.File.Append(wxID_FILEEXIT,'Exit')
        self.Bind(wx.EVT_MENU, self.OnFileExit, id=wxID_FILEEXIT)
        self.testSSMenu.Append(menu=self.File, title='Run')
        self.SetMenuBar(self.testSSMenu)
        self.testSSPanel = wx.Window(self)        
        
    def __init__(self, parent):
        self._init_ctrls(parent)
        self.Bind(wx.EVT_CLOSE, self.ExitMain)    
        self.dataFrame = None
        Data = {'SGData':G2spc.SpcGroup('P 1')[1],}
        self.propVec = '0,0,0'
        self.XYZ = '0,0,0'
        self.UpdateData(Data)

    def ExitMain(self, event):
        sys.exit()
        
    def OnFileExit(self,event):
        if self.dataFrame:
            self.dataFrame.Clear() 
            self.dataFrame.Destroy()
        self.Close()
        
    def UpdateData(self,Data):
        
        def OnSpaceGroup(event):
            SpGrp = 'P 1'
            SpcGp = G2phsGUI.GetSpGrpfromUser(self,SpGrp)
            SGErr,SGData = G2spc.SpcGroup(SpcGp)
            if SGErr:
                text = [G2spc.SGErrors(SGErr)+'\nSpace Group set to previous']
                SGTxt.SetLabel(Data['SGData']['SpGrp'])
                msg = 'Space Group Error'
                Style = wx.ICON_EXCLAMATION
                Text = '\n'.join(text)
                wx.MessageBox(Text,caption=msg,style=Style)
            else:
                text,table = G2spc.SGPrint(SGData,AddInv=True)
                Data['SGData'] = SGData
                SGTxt.SetLabel(Data['SGData']['SpGrp'])
                msg = 'Space Group Information'
                SgNo = G2spc.SpaceGroupNumber(SpcGp)
                if SgNo+1:
                    text[0] += ', No. '+str(SgNo)
                G2G.SGMessageBox(self,msg,text,table).Show()
            self.UpdateData(Data)
            
        def OnXYZ(event):
            Obj = event.GetEventObject()
            self.XYZ = Obj.GetValue()
            try:
                XYZ= np.array(eval('['+self.XYZ+']'),dtype=np.float)
                print('for:',XYZ)
                SytSym,Mul,Nop,dupDir = G2spc.SytSym(XYZ,SGData)
                print('dupDir',dupDir.keys())
                CSIX = G2spc.GetCSxinel(SytSym)
                CSIU = G2spc.GetCSuinel(SytSym)
                StrXYZ = [str(sxyz) for sxyz in CSIX[0]]
                ValXYZ = [str(val) for val in CSIX[1]]
                CSIXtxt.SetLabel(' site sym: %6s, mult: %3d, CSI-X: %s %s'%(SytSym,Mul,StrXYZ,ValXYZ))
                StrUIJ = [str(suij) for suij in CSIU[0]]
                ValUIJ = [str(val) for val in CSIU[1]]
                CSIUtxt.SetLabel(' site sym: %6s, mult: %3d, CSI-U: %s %s'%(SytSym,Mul,StrUIJ,ValUIJ))
            except:
                print('Bad X,Y,Z entry: ',Obj.GetValue())
                self.XYZ = '0,0,0'
                Obj.SetValue(self.XYZ)
                                
        def OnShowOps(event):
            text,table = G2spc.SGPrint(SGData)
            msg = 'Space Group Information'
            SgNo = G2spc.SpaceGroupNumber(SGData['SpGrp'])
            if SgNo+1:
                text[0] += ', No. '+str(SgNo)
            G2G.SGMessageBox(self,msg,text,table).Show()
            
        def OnShowGen(event):
            GenText = G2spc.TextGen(SGData,reverse=True)
            print(' Symmetry generators for %s:'%text[0].split(':')[1])
            for item in GenText:
                print(item)
                           
        def OnTestHKL(event):
            print('Extinctions for '+Data['SGData']['MagSpGrp'])
            hkls = np.mgrid[-6:6,-6:6,-6:6]
            HKLs = hkls.reshape((3,-1)).T
            for hkl in HKLs[1:]:    #skip 0,0,0
                ext = G2spc.checkMagextc(hkl,SGData)
                if ext: print(hkl)

        SGData = Data['SGData']
        self.testSSPanel.DestroyChildren()
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        topSizer = wx.FlexGridSizer(0,2,5,5)
        topSizer.Add(wx.StaticText(self.testSSPanel,-1,'  Space group: '),0,WACV)
        SpGrp = Data['SGData']['SpGrp']
        SGTxt = wx.Button(self.testSSPanel,wx.ID_ANY,SpGrp,size=(100,-1))
        SGTxt.Bind(wx.EVT_BUTTON,OnSpaceGroup)
        topSizer.Add(SGTxt,0,WACV)
        text,table = G2spc.SGPrint(SGData,AddInv=True)
        topSizer.Add(wx.StaticText(self.testSSPanel,label=' Special position test:'),0,WACV)
        SpPos = wx.BoxSizer(wx.HORIZONTAL)
        SpPos.Add(wx.StaticText(self.testSSPanel,label=' X,Y,Z:'),0,WACV)
        xyz = wx.TextCtrl(self.testSSPanel,value=self.XYZ,style=wx.TE_PROCESS_ENTER)
        xyz.Bind(wx.EVT_TEXT_ENTER,OnXYZ)        
        SpPos.Add(xyz,0,WACV)
        topSizer.Add(SpPos,0,WACV)
        mainSizer.Add(topSizer)
        XYZ= np.array(eval('['+self.XYZ+']'),dtype=np.float)
        SytSym,Mul,Nop,dupDir = G2spc.SytSym(XYZ,SGData)
        CSIX = G2spc.GetCSxinel(SytSym)
        CSIU = G2spc.GetCSuinel(SytSym)
        StrXYZ = [str(sxyz) for sxyz in CSIX[0]]
        ValXYZ = [str(val) for val in CSIX[1]]
        StrUIJ = [str(suij) for suij in CSIU[0]]
        ValUIJ = [str(val) for val in CSIU[1]]
        CSIXtxt = wx.StaticText(self.testSSPanel,label=' site sym: %6s, mult: %3d, CSI-X: %s %s'%(SytSym,Mul,StrXYZ,ValXYZ))
        mainSizer.Add(CSIXtxt,0,WACV)
        mainSizer.Add((5,5),0)
        CSIUtxt = wx.StaticText(self.testSSPanel,label=' site sym: %6s, mult: %3d, CSI-U: %s %s'%(SytSym,Mul,StrUIJ,ValUIJ))
        mainSizer.Add(CSIUtxt,0,WACV)
        testHKL = wx.Button(self.testSSPanel,-1,'Extinction test')
        testHKL.Bind(wx.EVT_BUTTON,OnTestHKL)
        mainSizer.Add(testHKL,0,WACV)
        printSizer = wx.BoxSizer(wx.HORIZONTAL)
        showOps = wx.Button(self.testSSPanel,-1,'Show sym. ops')
        showOps.Bind(wx.EVT_BUTTON,OnShowOps)
        printSizer.Add(showOps,0,WACV)
        showGen = wx.Button(self.testSSPanel,-1,'Print generators')
        showGen.Bind(wx.EVT_BUTTON,OnShowGen)
        printSizer.Add(showGen,0,WACV)
        mainSizer.Add(printSizer,0,WACV)
        self.testSSPanel.SetSizer(mainSizer)
        Size = mainSizer.Fit(self.testSSPanel)
        Size[0] = 800
        Size[1] = max(Size[1],350)
        self.testSSPanel.SetSize(Size)
            
class testSytSmain(wx.App):
    def OnInit(self):
        self.main = testSytSym(None)
        self.main.Show()
        self.SetTopWindow(self.main)
        return True

def main():
    'Starts main application to compute and plot derivatives'
    GSASIIpath.InvokeDebugOpts()
    application = testSytSmain(0)
    application.MainLoop()
    
if __name__ == '__main__':
    main()
            
        
