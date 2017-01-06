# -*- coding: utf-8 -*-
'''
*GSASIIplot: plotting routines*
===============================

'''
########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### SVN repository information ###################
import math
import sys
import os.path
import numpy as np
import numpy.ma as ma
import numpy.linalg as nl
import wx
import wx.aui
import wx.glcanvas
import matplotlib as mpl
import mpl_toolkits.mplot3d.axes3d as mp3d
import GSASIIpath
Clip_on = GSASIIpath.GetConfigValue('Clip_on')
GSASIIpath.SetVersionNumber("$Revision$")
import GSASIIgrid as G2gd
import GSASIIimage as G2img
import GSASIIpwd as G2pwd
import GSASIIIO as G2IO
import GSASIIpwdGUI as G2pdG
import GSASIIimgGUI as G2imG
import GSASIIphsGUI as G2phG
import GSASIIlattice as G2lat
import GSASIIspc as G2spc
import GSASIImath as G2mth
import GSASIIctrls as G2G
import pytexture as ptx
#from  OpenGL.GL import *
import OpenGL.GL as GL
import OpenGL.GLU as GLU
import gltext
from matplotlib.backends.backend_wx import _load_bitmap
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as Canvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2Wx as Toolbar

# useful degree trig functions
sind = lambda x: math.sin(x*math.pi/180.)
cosd = lambda x: math.cos(x*math.pi/180.)
tand = lambda x: math.tan(x*math.pi/180.)
asind = lambda x: 180.*math.asin(x)/math.pi
acosd = lambda x: 180.*math.acos(x)/math.pi
atan2d = lambda x,y: 180.*math.atan2(y,x)/math.pi
atand = lambda x: 180.*math.atan(x)/math.pi
# numpy versions
npsind = lambda x: np.sin(x*np.pi/180.)
npcosd = lambda x: np.cos(x*np.pi/180.)
nptand = lambda x: np.tan(x*np.pi/180.)
npacosd = lambda x: 180.*np.arccos(x)/np.pi
npasind = lambda x: 180.*np.arcsin(x)/np.pi
npatand = lambda x: 180.*np.arctan(x)/np.pi
npatan2d = lambda x,y: 180.*np.arctan2(x,y)/np.pi
GkDelta = unichr(0x0394)
Gkrho = unichr(0x03C1)
nxs = np.newaxis
#    GSASIIpath.IPyBreak()
plotDebug = False
    
class _tabPlotWin(wx.Panel):    
    'Creates a basic tabbed plot window for GSAS-II graphics'
    def __init__(self,parent,id=-1,dpi=None,**kwargs):
        self.ReplotRoutine = None
        self.ReplotArgs = []
        self.ReplotKwArgs = {}
        wx.Panel.__init__(self,parent,id=id,**kwargs)
        
class G2PlotMpl(_tabPlotWin):    
    'Creates a Matplotlib 2-D plot in the GSAS-II graphics window'
    def __init__(self,parent,id=-1,dpi=None,**kwargs):
        _tabPlotWin.__init__(self,parent,id=id,**kwargs)
        mpl.rcParams['legend.fontsize'] = 10
        self.figure = mpl.figure.Figure(dpi=dpi,figsize=(5,6))
        self.canvas = Canvas(self,-1,self.figure)
        self.toolbar = GSASIItoolbar(self.canvas)

        self.toolbar.Realize()
        
        sizer=wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas,1,wx.EXPAND)
        sizer.Add(self.toolbar,0,wx.LEFT|wx.EXPAND)
        self.SetSizer(sizer)
        
class G2PlotOgl(_tabPlotWin):
    'Creates an OpenGL plot in the GSAS-II graphics window'
    def __init__(self,parent,id=-1,dpi=None,**kwargs):
        self.figure = _tabPlotWin.__init__(self,parent,id=id,**kwargs)
        if 'win' in sys.platform:           #Windows (& Mac) already double buffered
            self.canvas = wx.glcanvas.GLCanvas(self,-1,**kwargs)
        else:                               #fix from Jim Hester for X systems
            attribs = (wx.glcanvas.WX_GL_DOUBLEBUFFER,)
            self.canvas = wx.glcanvas.GLCanvas(self,-1,attribList=attribs,**kwargs)
        # create GL context
        i,j= wx.__version__.split('.')[0:2]
        if int(i)+int(j)/10. > 2.8:
            self.context = wx.glcanvas.GLContext(self.canvas)
            self.canvas.SetCurrent(self.context)
        else:
            self.context = None
        self.camera = {}
        sizer=wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas,1,wx.EXPAND)
        self.SetSizer(sizer)
        
class G2Plot3D(_tabPlotWin):
    'Creates a 3D Matplotlib plot in the GSAS-II graphics window'
    def __init__(self,parent,id=-1,dpi=None,**kwargs):
        _tabPlotWin.__init__(self,parent,id=id,**kwargs)
        self.figure = mpl.figure.Figure(dpi=dpi,figsize=(6,6))
        self.canvas = Canvas(self,-1,self.figure)
        self.toolbar = GSASIItoolbar(self.canvas)

        self.toolbar.Realize()
        
        sizer=wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas,1,wx.EXPAND)
        sizer.Add(self.toolbar,0,wx.LEFT|wx.EXPAND)
        self.SetSizer(sizer)
                              
class G2PlotNoteBook(wx.Panel):
    'create a tabbed panel to hold a GSAS-II graphics window'
    def __init__(self,parent,id=-1,G2frame=None):
        wx.Panel.__init__(self,parent,id=id)
        #so one can't delete a plot page from tab!!
        self.nb = wx.aui.AuiNotebook(self, \
            style=wx.aui.AUI_NB_DEFAULT_STYLE ^ wx.aui.AUI_NB_CLOSE_ON_ACTIVE_TAB)
        sizer = wx.BoxSizer()
        sizer.Add(self.nb,1,wx.EXPAND)
        self.SetSizer(sizer)
        self.status = parent.CreateStatusBar()
        self.status.SetFieldsCount(2)
        self.status.SetStatusWidths([150,-1])
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        self.nb.Bind(wx.EVT_KEY_UP,self.OnNotebookKey)
        self.G2frame = G2frame
        
        self.plotList = []   # contains the tab label for each plot
        self.panelList = []   # contains the panel object for each plot
        self.skipPageChange = False # set to True when no plot update is needed
        self.allowZoomReset = True # this indicates plot should be updated not initialized
        self.lastRaisedPlotTab = None
        
    def OnNotebookKey(self,event):
        '''Called when a keystroke event gets picked up by the notebook window
        rather the child. This is not expected, but somehow it does sometimes
        on the Mac and perhaps Linux.

        Assume that the page associated with the currently displayed tab
        has a child, .canvas; give that child the focus and pass it the event.
        '''
        try:
            Page = self.nb.GetPage(self.nb.GetSelection())
        except ValueError: # occurs with no plot tabs
            return
        try:
            Page.canvas.SetFocus()
            wx.PostEvent(Page.canvas,event)
        except AttributeError:
            pass

    def SetNoDelete(self,name):
        '''Indicate that a plot does not need to be redrawn
        '''
        if name not in self.plotList:
            print('Error, in SetNoDelete plot not found: '+name)
            return
        page = self.panelList[self.plotList.index(name)]
        page.plotRequiresRedraw = False # plot should not be deleted even if not redrawn
        

    def RegisterRedrawRoutine(self,name,routine=None,args=(),kwargs={}):
        '''Save information to determine how to redraw a plot
        :param str name: label on tab of plot
        :param Object routine: a function to be called
        :param args: a list of positional parameters for the function
        :param kwargs: a dict with keyword parameters for the function
        '''
        if name not in self.plotList:
            print('Error, plot not found: '+name)
            return
        page = self.panelList[self.plotList.index(name)]
        page.replotFunction = routine
        page.replotArgs = args
        page.replotKWargs = kwargs

    def GetTabIndex(self,label):
        '''Look up a tab label and return the index in the notebook (this appears to be
        independent to the order it is dragged to -- at least in Windows) as well as
        the associated wx.Panel

        An exception is raised if the label is not found     
        '''
        for i in range(self.nb.GetPageCount()):
            if label == self.nb.GetPageText(i):
                return i,self.nb.GetPage(i)
        else:
            raise ValueError('Plot not found')

    def RaiseLastPage(self,lastRaisedPlotTab,treeItemPlot):
        '''Raises either the Last tab clicked on or what is drawn by the selected tree item
        This is called after a refinement is completed by :meth:`GSASII.GSASII.ResetPlots`
        '''
        plotNum = None
        if lastRaisedPlotTab in self.plotList:
            plotNum = self.plotList.index(lastRaisedPlotTab)
        elif treeItemPlot in self.plotList:
            plotNum = self.plotList.index(treeItemPlot)
        if plotNum is not None:
            wx.CallAfter(self.SetSelectionNoRefresh,plotNum)

    def FindPlotTab(self,label,type,newImage=True):
        '''Open a plot tab for initial plotting, or raise the tab if it already exists
        Set a flag (Page.plotInvalid) that it has been redrawn
        Record the name of the this plot in self.lastRaisedPlotTab
        '''
        limits = None
        Plot = None
        try:
            new = False
            plotNum,Page = self.GetTabIndex(label)
            if type == 'mpl' or type == '3d':          
                Plot = Page.figure.gca()          #get previous plot
                limits = Plot.get_xlim(),Plot.get_ylim() # save previous limits
#                print 'Plot limits:',limits
                if newImage:
                    Page.figure.clf()
                    Plot = Page.figure.gca()          #get a fresh plot after clf()
            self.SetSelectionNoRefresh(plotNum) # raises plot tab
        except (ValueError,AttributeError):
            new = True
            if type == 'mpl':
                Plot = self.addMpl(label).gca()
            elif type == 'ogl':
                Plot = self.addOgl(label)
            elif type == '3d':
                Plot = mp3d.Axes3D(self.add3D(label))
            plotNum = self.plotList.index(label)
            Page = self.nb.GetPage(plotNum)

        Page.plotInvalid = False # plot has just been drawn
        self.lastRaisedPlotTab = label
        self.RaisePageNoRefresh(Page)
        # Save the help name from the DataItem that has created the plot in Tabbed page object
        # so we can use it in self.OnHelp(). 
        # Are there any cases where plot tabs are created that are not tied to Data Tree entries?
        # One example is GSASII.SumDialog, where a test plot is created. Are there others? 
        try:
            Page.helpKey = self.G2frame.dataFrame.helpKey
        except AttributeError:
            Page.helpKey = 'Data tree'
        return new,plotNum,Page,Plot,limits
    
    def _addPage(self,name,page):
        '''Add the newly created page to the notebook and associated lists.
        :param name: the label placed on the tab, which should be unique
        :param page: the wx.Frame for the matplotlib, openGL, etc. window
        '''
        self.skipPageChange = True
        if name in self.plotList:
            print('Warning: duplicate plot name! Name='+name)
        self.nb.AddPage(page,name)
        self.plotList.append(name) # used to lookup plot in self.panelList
        # Note that order in lists make not agree with actual tab order; use self.nb.GetPageText(i)
        #    where (self=G2plotNB) for latter 
        self.panelList.append(page) # panel object for plot
        self.lastRaisedPlotTab = name
        page.plotInvalid = False # plot has just been drawn
        page.plotRequiresRedraw = True # set to False if plot should be retained even if not refreshed
        page.replotFunction = None # used to specify a routine to redraw the routine
        page.replotArgs = []
        page.replotKWargs = {}
        self.skipPageChange = False
                
    def addMpl(self,name=""):
        'Add a tabbed page with a matplotlib plot'
        page = G2PlotMpl(self.nb)
        self._addPage(name,page)
        return page.figure
        
    def add3D(self,name=""):
        'Add a tabbed page with a 3D plot'
        page = G2Plot3D(self.nb)
        self._addPage(name,page)
        return page.figure
        
    def addOgl(self,name=""):
        'Add a tabbed page with an openGL plot'
        page = G2PlotOgl(self.nb)
        self._addPage(name,page)
        self.RaisePageNoRefresh(page)   # need to give window focus before GL use
        return page.figure
        
    def Delete(self,name):
        'delete a tabbed page'
        try:
            item = self.plotList.index(name)
            del self.plotList[item]
            del self.panelList[item]
            self.nb.DeletePage(item)
        except ValueError:          #no plot of this name - do nothing
            return      
                
    def clear(self):
        'clear all pages from plot window'
        while self.nb.GetPageCount():
            self.nb.DeletePage(0)
        self.plotList = []
        self.panelList = []
        self.status.DestroyChildren()
        
    def Rename(self,oldName,newName):
        'rename a tab'
        try:
            item = self.plotList.index(oldName)
            self.plotList[item] = newName
            self.nb.SetPageText(item,newName)
        except ValueError:          #no plot of this name - do nothing
            return      
        
    def RaisePageNoRefresh(self,Page):
        'Raises a plot tab without triggering a refresh via OnPageChanged'
        if plotDebug: print 'Raise',str(self).split('0x')[1]
        self.skipPageChange = True
        Page.SetFocus()
        self.skipPageChange = False
        
    def SetSelectionNoRefresh(self,plotNum): 
        'Raises a plot tab without triggering a refresh via OnPageChanged' 
        if plotDebug: print 'Select',str(self).split('0x')[1]
        self.skipPageChange = True
        self.nb.SetSelection(plotNum) # raises plot tab 
        Page = self.G2frame.G2plotNB.nb.GetPage(plotNum)
        Page.SetFocus()
        self.skipPageChange = False

    def OnPageChanged(self,event):
        '''respond to someone pressing a tab on the plot window.
        Called when a plot tab is clicked. on some platforms (Mac for sure) this
        is also called when a plot is created or selected with .SetSelection() or
        .SetFocus(). The self.skipPageChange is used variable is set to suppress
        repeated replotting.
        '''
        tabLabel = event.GetEventObject().GetPageText(event.GetSelection())
        self.lastRaisedPlotTab = tabLabel
        if plotDebug: 
            print 'PageChanged, self=',str(self).split('0x')[1],tabLabel,self.skipPageChange
            print 'event type=',event.GetEventType()
        self.status.DestroyChildren()    #get rid of special stuff on status bar
        self.status.SetFields(['',''])  # clear old status message
        self.status.SetStatusWidths([150,-1])
            
    def InvokeTreeItem(self,pid):
        '''This is called to select an item from the tree using the self.allowZoomReset
        flag to prevent a reset to the zoom of the plot (where implemented)
        '''
        self.allowZoomReset = False 
        if pid: self.G2frame.PatternTree.SelectItem(pid)
        self.allowZoomReset = True
        if plotDebug: print 'invoke',str(self).split('0x')[1],str(pid)
            
class GSASIItoolbar(Toolbar):
    'Override the matplotlib toolbar so we can add more icons'
    ON_MPL_HELP = wx.NewId()
    ON_MPL_KEY = wx.NewId()
    arrows = {}
    for direc in ('left','right','up','down','Expand X',
                  'Shrink X','Expand Y','Shrink Y'):
        arrows[direc] = wx.NewId()
    def __init__(self,plotCanvas):
        '''Adds additional icons to toolbar'''
        Toolbar.__init__(self,plotCanvas)
        self.plotCanvas = plotCanvas
        POSITION_OF_CONFIGURE_SUBPLOTS_BTN = 6 # remove one button, nos. start at 1!
        self.DeleteToolByPos(POSITION_OF_CONFIGURE_SUBPLOTS_BTN)    #doesn't work in miniconda
        self.parent = self.GetParent()
        key = os.path.join(os.path.split(__file__)[0],'key.ico')
        self.AddSimpleTool(self.ON_MPL_KEY,_load_bitmap(key),'Key press','Select key press')
        wx.EVT_TOOL(self,self.ON_MPL_KEY,self.OnKey)
        help = os.path.join(os.path.split(__file__)[0],'help.ico')
        self.AddSimpleTool(self.ON_MPL_HELP,_load_bitmap(help),'Help on','Show help on')
        wx.EVT_TOOL(self,self.ON_MPL_HELP,self.OnHelp)
        # add arrow keys to control zooming
        for direc in ('left','right','up','down'):
            wx.EVT_TOOL(self,self.arrows[direc],self.OnArrow)
            icon =  os.path.join(os.path.split(__file__)[0],direc[0]+'arrow.ico')
            self.AddSimpleTool(self.arrows[direc],_load_bitmap(icon),
                               'Shift '+direc,'Shift plot '+direc)
        for direc in ('Expand X','Shrink X','Expand Y','Shrink Y'):
            fil = ''.join([i[0].lower() for i in direc.split()]+['arrow.ico'])
            wx.EVT_TOOL(self,self.arrows[direc],self.OnArrow)
            icon =  os.path.join(os.path.split(__file__)[0],fil)
            self.AddSimpleTool(self.arrows[direc],_load_bitmap(icon),
                               direc,'Zoom: '+direc)
    def OnArrow(self,event):
        'reposition limits to scan or zoom by button press'
        ax = self.plotCanvas.figure.get_axes()[0]
        xmin,xmax,ymin,ymax = ax.axis()
        #print xmin,xmax,ymin,ymax
        if event.Id == self.arrows['right']:
            delta = (xmax-xmin)/10.
            xmin -= delta
            xmax -= delta
        elif event.Id == self.arrows['left']:
            delta = (xmax-xmin)/10.
            xmin += delta
            xmax += delta
        elif event.Id == self.arrows['up']:
            delta = (ymax-ymin)/10.
            ymin -= delta
            ymax -= delta
        elif event.Id == self.arrows['down']:
            delta = (ymax-ymin)/10.
            ymin += delta
            ymax += delta
        elif event.Id == self.arrows['Expand X']:
            delta = (xmax-xmin)/10.
            xmin += delta
            xmax -= delta
        elif event.Id == self.arrows['Expand Y']:
            delta = (ymax-ymin)/10.
            ymin += delta
            ymax -= delta
        elif event.Id == self.arrows['Shrink X']:
            delta = (xmax-xmin)/10.
            xmin -= delta
            xmax += delta
        elif event.Id == self.arrows['Shrink Y']:
            delta = (ymax-ymin)/10.
            ymin -= delta
            ymax += delta
        else:
            # should not happen!
            GSASIIpath.IPyBreak()
        self.parent.toolbar.push_current()
        ax.axis((xmin,xmax,ymin,ymax))
        #print xmin,xmax,ymin,ymax
        self.plotCanvas.figure.canvas.draw()
        self.parent.toolbar.draw()
#        self.parent.toolbar.push_current()
        
    def OnHelp(self,event):
        'Respond to press of help button on plot toolbar'
        bookmark = self.Parent.helpKey  # get help category used to create plot
        #if GSASIIpath.GetConfigValue('debug'): print 'plot help: key=',bookmark
        G2G.ShowHelp(bookmark,self.TopLevelParent)
        
    def OnKey(self,event):
        '''Provide user with list of keystrokes defined for plot as well as an
        alternate way to access the same functionality
        '''
        parent = self.GetParent()
        if parent.Choice:
            dlg = wx.SingleChoiceDialog(parent,'Select','Key press',list(parent.Choice))
            if dlg.ShowModal() == wx.ID_OK:
                sel = dlg.GetSelection()
                event.key = parent.Choice[sel][0]
                parent.keyPress(event)
            dlg.Destroy()
            
################################################################################
##### PlotSngl
################################################################################
            
def PlotSngl(G2frame,newPlot=False,Data=None,hklRef=None,Title=''):
    '''Structure factor plotting package - displays zone of reflections as rings proportional
        to F, F**2, etc. as requested
    '''
    from matplotlib.patches import Circle
    global HKL,HKLF,HKLref
    HKLref = hklRef
    
    def OnSCKeyPress(event):
        i = zones.index(Data['Zone'])
        newPlot = False
        pwdrChoice = {'f':'Fo','s':'Fosq','u':'Unit Fc'}
        hklfChoice = {'1':'|DFsq|>sig','3':'|DFsq|>3sig','w':'|DFsq|/sig','f':'Fo','s':'Fosq','i':'Unit Fc'}
        if event.key == 'h':
            Data['Zone'] = '100'
            newPlot = True
        elif event.key == 'k':
            Data['Zone'] = '010'
            newPlot = True
        elif event.key == 'l':
            Data['Zone'] = '001'
            newPlot = True
        elif event.key == 'i':
            Data['Scale'] *= 1.1
        elif event.key == 'd':
            Data['Scale'] /= 1.1
        elif event.key in ['+','=']:
            Data['Layer'] = min(Data['Layer']+1,HKLmax[i])
        elif event.key == '-':
            Data['Layer'] = max(Data['Layer']-1,HKLmin[i])
        elif event.key == '0':
            Data['Layer'] = 0
            Data['Scale'] = 1.0
        elif event.key in hklfChoice and 'HKLF' in Name:
            Data['Type'] = hklfChoice[event.key]            
            newPlot = True
        elif event.key in pwdrChoice and 'PWDR' in Name:
            Data['Type'] = pwdrChoice[event.key]            
            newPlot = True       
        PlotSngl(G2frame,newPlot,Data,HKLref,Title)

    def OnSCMotion(event):
        xpos = event.xdata
        if xpos:
            xpos = round(xpos)                                        #avoid out of frame mouse position
            ypos = round(event.ydata)
            zpos = Data['Layer']
            if '100' in Data['Zone']:
                HKLtxt = '(%d,%d,%d)'%(zpos,xpos,ypos)
            elif '010' in Data['Zone']:
                HKLtxt = '(%d,%d,%d)'%(xpos,zpos,ypos)
            elif '001' in Data['Zone']:
                HKLtxt = '(%d,%d,%d)'%(xpos,ypos,zpos)
            Page.canvas.SetToolTipString(HKLtxt)
            G2frame.G2plotNB.status.SetStatusText('HKL = '+HKLtxt,0)
                
    def OnSCPress(event):
        zpos = Data['Layer']
        xpos = event.xdata
        if xpos:
            pos = int(round(event.xdata)),int(round(event.ydata))
            if '100' in Data['Zone']:
                hkl = np.array([zpos,pos[0],pos[1]])
            elif '010' in Data['Zone']:
                hkl = np.array([pos[0],zpos,pos[1]])
            elif '001' in Data['Zone']:
                hkl = np.array([pos[0],pos[1],zpos])
            h,k,l = hkl
            hklf = HKLF[np.where(np.all(HKL-hkl == [0,0,0],axis=1))]
            if len(hklf):
                Fosq,sig,Fcsq = hklf[0]
                HKLtxt = '( %.2f %.3f %.2f %.2f)'%(Fosq,sig,Fcsq,(Fosq-Fcsq)/(scale*sig))
                G2frame.G2plotNB.status.SetStatusText('Fosq, sig, Fcsq, delFsq/sig = '+HKLtxt,1)
                
    def OnPick(event):
        pick = event.artist
        HKLtext = pick.get_gid()
        Page.canvas.SetToolTipString(HKLtext)
        G2frame.G2plotNB.status.SetStatusText('H = '+HKLtext,0)
                                 
    Name = G2frame.PatternTree.GetItemText(G2frame.PatternId)
    if not Title:
        Title = Name
    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('Structure Factors','mpl')
    if not new:
        if not newPlot:
            xylim = lim
    else:
        Page.canvas.mpl_connect('button_press_event', OnSCPress)
        Page.canvas.mpl_connect('motion_notify_event', OnSCMotion)
        Page.canvas.mpl_connect('pick_event', OnPick)
        Page.canvas.mpl_connect('key_press_event', OnSCKeyPress)
        Page.keyPress = OnSCKeyPress
        Page.Choice = (' key press','i: increase scale','d: decrease scale',
            'h: select 100 zone','k: select 010 zone','l: select 001 zone',
            'f: select Fo','s: select Fosq','u: select unit Fc',
            '+: increase index','-: decrease index','0: zero layer',)
        if 'HKLF' in Name:
            Page.Choice += ('w: select |DFsq|/sig','1: select |DFsq|>sig','3: select |DFsq|>3sig',)
    Plot.set_aspect(aspect='equal')
    
    Type = Data['Type']            
    scale = Data['Scale']
    HKLmax = Data['HKLmax']
    HKLmin = Data['HKLmin']
    FosqMax = Data['FoMax']
    Super = Data['Super']
    SuperVec = []
    if Super:
        SuperVec = np.array(Data['SuperVec'][0])
    FoMax = math.sqrt(FosqMax)
    xlabel = ['k, h=','h, k=','h, l=']
    ylabel = ['l','l','k']
    zones = ['100','010','001']
    pzone = [[1,2],[0,2],[0,1]]
    izone = zones.index(Data['Zone'])
    Plot.set_title(Data['Type']+' for '+Title)
    HKL = []
    HKLF = []
    sumFo = 0.
    sumDF = 0.
#    GSASIIpath.IPyBreak()
    for refl in HKLref:
        H = refl[:3]
        if 'HKLF' in Name:
            Fosq,sig,Fcsq = refl[5+Super:8+Super]
        else:
            Fosq,sig,Fcsq = refl[8+Super],1.0,refl[9+Super]
        if Super:
            HKL.append(H+SuperVec*refl[3])
        else:
            HKL.append(H)
        HKLF.append([Fosq,sig,Fcsq])
        if H[izone] == Data['Layer']:
            A = 0
            B = 0
            if Type == 'Fosq':
                A = scale*Fosq/FosqMax
                sumFo += A
                B = scale*Fcsq/FosqMax
                C = abs(A-B)
                sumDF += C
            elif Type == 'Fo':
                A = scale*math.sqrt(max(0,Fosq))/FoMax
                sumFo += A
                B = scale*math.sqrt(max(0,Fcsq))/FoMax
                C = abs(A-B)
                sumDF += C
            elif Type == 'Unit Fc':
                A = scale/2
                B = scale/2
                C = 0.0
                if Fcsq and Fosq > 0:
                    A *= min(1.0,Fosq/Fcsq)
                    C = abs(A-B)
            elif Type == '|DFsq|/sig':
                if sig > 0.:
                    A = scale*(Fosq-Fcsq)/(3*sig)
                B = 0
            elif Type == '|DFsq|>sig':
                if sig > 0.:
                    A = scale*(Fosq-Fcsq)/(3*sig)
                if abs(A) < 1.0: A = 0
                B = 0                    
            elif Type == '|DFsq|>3sig':
                if sig > 0.:
                    A = scale*(Fosq-Fcsq)/(3*sig)
                if abs(A) < 3.0: A = 0
                B = 0
            if Super:
                h = H+SuperVec*refl[3]
                if refl[3]:
                    hid = '(%d,%d,%d,%d)'%(refl[0],refl[1],refl[2],refl[3])
                else:
                    hid = '(%d,%d,%d)'%(refl[0],refl[1],refl[2])                
            else:
                h = H
                hid = '(%d,%d,%d)'%(refl[0],refl[1],refl[2])                
            xy = (h[pzone[izone][0]],h[pzone[izone][1]])
            if Type in ['|DFsq|/sig','|DFsq|>sig','|DFsq|>3sig']:
                if A > 0.0:
                    Plot.add_artist(Circle(xy,radius=A,ec='g',fc='w',picker=1.,gid=hid))
                else:
                    Plot.add_artist(Circle(xy,radius=-A,ec='r',fc='w',picker=1.,gid=hid))
            else:
                if A > 0.0 and A > B:
                    Plot.add_artist(Circle(xy,radius=A,ec='g',fc='w'))
                if B:
                    Plot.add_artist(Circle(xy,radius=B,ec='b',fc='w',picker=1.,gid=hid))
                    if A < B:
                        Plot.add_artist(Circle(xy,radius=A,ec='g',fc='w'))
                    radius = C
                    if radius > 0:
                        if A > B:
                            Plot.add_artist(Circle(xy,radius=radius,ec='g',fc='g'))
                        else:                    
                            Plot.add_artist(Circle(xy,radius=radius,ec='r',fc='r'))
#    print 'plot time: %.3f'%(time.time()-time0)
    HKL = np.array(HKL)
    HKLF = np.array(HKLF)
    Plot.set_xlabel(xlabel[izone]+str(Data['Layer']),fontsize=12)
    Plot.set_ylabel(ylabel[izone],fontsize=12)
    if sumFo and sumDF:
        G2frame.G2plotNB.status.SetStatusText(xlabel[izone].split(',')[1]+str(Data['Layer'])+   \
            ' layer R = %6.2f%s'%(100.*sumDF/sumFo,'%'),1)
    else:
        G2frame.G2plotNB.status.SetStatusText('Use K-box to set plot controls',1)
    if not newPlot:
        Page.toolbar.push_current()
        Plot.set_xlim(xylim[0])
        Plot.set_ylim(xylim[1])
#        xylim = []
        Page.toolbar.push_current()
        Page.toolbar.draw()
    else:
        Plot.set_xlim((HKLmin[pzone[izone][0]],HKLmax[pzone[izone][0]]))
        Plot.set_ylim((HKLmin[pzone[izone][1]],HKLmax[pzone[izone][1]]))
        Page.canvas.draw()
        
################################################################################
##### Plot3DSngl
################################################################################

def Plot3DSngl(G2frame,newPlot=False,Data=None,hklRef=None,Title=False):
    '''3D Structure factor plotting package - displays reflections as rings proportional
        to F, F**2, etc. as requested as 3D array
    '''
    super2 = unichr(0xb2)
    global ifBox
    ifBox = False
    def OnKeyBox(event):
        mode = cb.GetValue()
        if mode in ['jpeg','bmp','tiff',]:
            try:
                import Image as Im
            except ImportError:
                try:
                    from PIL import Image as Im
                except ImportError:
                    print "PIL/pillow Image module not present. Cannot save images without this"
                    raise Exception("PIL/pillow Image module not found")
            try:
                Fname = os.path.join(Mydir,generalData['Name']+'.'+mode)
            except NameError:   #for when generalData doesn't exist!
                Fname = (os.path.join(Mydir,'unknown'+'.'+mode)).replace('*','+')
            print Fname+' saved'
            size = Page.canvas.GetSize()
            GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
            if mode in ['jpeg',]:
                Pix = GL.glReadPixels(0,0,size[0],size[1],GL.GL_RGBA,GL.GL_UNSIGNED_BYTE)
                im = Im.new("RGBA", (size[0],size[1]))
            else:
                Pix = GL.glReadPixels(0,0,size[0],size[1],GL.GL_RGB,GL.GL_UNSIGNED_BYTE)
                im = Im.new("RGB", (size[0],size[1]))
            try:
                im.frombytes(Pix)
            except AttributeError:
                im.fromstring(Pix)
            im = im.transpose(Im.FLIP_TOP_BOTTOM)
            im.save(Fname,mode)
            cb.SetValue(' save as/key:')
            G2frame.G2plotNB.status.SetStatusText('Drawing saved to: '+Fname,1)
        else:
            event.key = cb.GetValue()[0]
            cb.SetValue(' save as/key:')
            wx.CallAfter(OnKey,event)
        Page.canvas.SetFocus() # redirect the Focus from the button back to the plot
        
    def OnKey(event):           #on key UP!!
        global ifBox
        Choice = {'F':'Fo','S':'Fosq','U':'Unit','D':'dFsq','W':'dFsq/sig'}
        viewChoice = {'L':np.array([[0,0,1],[1,0,0],[0,1,0]]),'K':np.array([[0,1,0],[0,0,1],[1,0,0]]),'H':np.array([[1,0,0],[0,0,1],[0,1,0]])}
        try:
            keyCode = event.GetKeyCode()
            if keyCode > 255:
                keyCode = 0
            key = chr(keyCode)
        except AttributeError:       #if from OnKeyBox above
            key = str(event.key).upper()
        if key in ['C','H','K','L']:
            if key == 'C':
                Data['Zone'] = False 
                key = 'L'
            Data['viewKey'] = key
            drawingData['viewPoint'][0] = np.array(drawingData['default'])
            drawingData['viewDir'] = viewChoice[key][0]
            drawingData['viewUp'] = viewChoice[key][1]
            drawingData['oldxy'] = []
            if Data['Zone']:
                if key == 'L':
                    Q = [-1,0,0,0]
                else:
                    V0 = viewChoice[key][0]
                    V1 = viewChoice[key][1]
                    V0 = np.inner(Amat,V0)
                    V1 = np.inner(Amat,V1)
                    V0 /= nl.norm(V0)
                    V1 /= nl.norm(V1)
                    A = np.arccos(np.sum(V1*V0))
                    Q = G2mth.AV2Q(-A,viewChoice[key][2])
                G2frame.G2plotNB.status.SetStatusText('zone = %s'%(str(list(viewChoice[key][0]))),1)
            else:
                V0 = viewChoice[key][0]
                V = np.inner(Bmat,V0)
                V /= np.sqrt(np.sum(V**2))
                V *= np.array([0,0,1])
                A = np.arccos(np.sum(V*V0))
                Q = G2mth.AV2Q(-A,viewChoice[key][2])
            drawingData['Quaternion'] = Q
        elif key in 'O':
            drawingData['viewPoint'][0] = [0,0,0]
        elif key in 'Z':
            Data['Zone'] = not Data['Zone']
        elif key in 'B':
            ifBox = not ifBox
        elif key in ['+','=']:
            Data['Scale'] *= 1.25
        elif key == '-':
            Data['Scale'] /= 1.25
        elif key == 'P':
            vec = viewChoice[Data['viewKey']][0]
            drawingData['viewPoint'][0] -= vec
        elif key == 'N':
            vec = viewChoice[Data['viewKey']][0]
            drawingData['viewPoint'][0] += vec
        elif key == '0':
            drawingData['viewPoint'][0] = np.array([0,0,0])
            Data['Scale'] = 1.0
        elif key == 'I':
            Data['Iscale'] = not Data['Iscale']
        elif key in Choice:
            Data['Type'] = Choice[key]
        Draw('key')
            
    Name = G2frame.PatternTree.GetItemText(G2frame.PatternId)
    if Title and Title in G2frame.GetPhaseData(): #NB: save image as e.g. jpeg will fail if False; MyDir is unknown
        generalData = G2frame.GetPhaseData()[Title]['General']
        cell = generalData['Cell'][1:7]
        Mydir = generalData['Mydir']
    else:
        Title = 'Unknown'
        cell = [10,10,10,90,90,90]
        Mydir = G2frame.dirname
    drawingData = Data['Drawing']
    Super = Data['Super']
    SuperVec = []
    if Super:
        SuperVec = np.array(Data['SuperVec'][0])
    Amat,Bmat = G2lat.cell2AB(cell)         #Amat - crystal to cartesian, Bmat - inverse
    Gmat,gmat = G2lat.cell2Gmat(cell)
    B4mat = np.concatenate((np.concatenate((Bmat,[[0],[0],[0]]),axis=1),[[0,0,0,1],]),axis=0)
    drawingData['Quaternion'] = G2mth.AV2Q(2*np.pi,np.inner(Bmat,[0,0,1]))
    Wt = np.array([255,255,255])
    Rd = np.array([255,0,0])
    Gr = np.array([0,255,0])
    Bl = np.array([0,0,255])
    uBox = np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]])
    uEdges = np.array([
        [uBox[0],uBox[1]],[uBox[0],uBox[3]],[uBox[0],uBox[4]],[uBox[1],uBox[2]], 
        [uBox[2],uBox[3]],[uBox[1],uBox[5]],[uBox[2],uBox[6]],[uBox[3],uBox[7]], 
        [uBox[4],uBox[5]],[uBox[5],uBox[6]],[uBox[6],uBox[7]],[uBox[7],uBox[4]]])
    uColors = [Rd,Gr,Bl, Wt,Wt,Wt, Wt,Wt,Wt, Wt,Wt,Wt]
    
    def FillHKLRC():
        sumFo2 = 0.
        sumDF2 = 0.
        sumFo = 0.
        sumDF = 0.
        R = np.zeros(len(hklRef))
        C = []
        HKL = []
        for i,refl in enumerate(hklRef):
            H = refl[:3]
            if 'HKLF' in Name:
                Fosq,sig,Fcsq = refl[5+Super:8+Super]
                if refl[3+Super] < 0:
                    Fosq,sig,Fcsq = [0,1,0]
            else:
                Fosq,sig,Fcsq = refl[8+Super],1.0,refl[9+Super]
            sumFo2 += Fosq
            sumDF2 += abs(Fosq-Fcsq)
            if Fosq > 0.:
                sumFo += np.sqrt(Fosq)
                sumDF += abs(np.sqrt(Fosq)-np.sqrt(Fcsq))
            if Super:
                HKL.append(H+SuperVec*refl[3])
            else:
                HKL.append(H)
            if Data['Type'] == 'Unit':
                R[i] = 0.1
                C.append(Gr)
            elif Data['Type'] == 'Fosq':
                if Fosq > 0:
                    R[i] = Fosq
                    C.append(Gr)
                else:
                    R[i] = -Fosq
                    C.append(Rd)
            elif Data['Type'] == 'Fo':
                if Fosq > 0:
                    R[i] = np.sqrt(Fosq)
                    C.append(Gr)
                else:
                    R[i] = np.sqrt(-Fosq)
                    C.append(Rd)
            elif Data['Type'] == 'dFsq/sig':
                dFsig = (Fosq-Fcsq)/sig
                if dFsig > 0:
                    R[i] = dFsig
                    C.append(Gr)
                else:
                    R[i] = -dFsig
                    C.append(Rd)
            elif Data['Type'] == 'dFsq':
                dF = Fosq-Fcsq
                if dF > 0:
                    R[i] = dF
                    C.append(Gr)
                else:
                    R[i] = -dF
                    C.append(Rd)
        R /= np.max(R)
        R *= Data['Scale']
        R = np.where(R<1.e-5,1.e-5,R)
        if Data['Iscale']:
            R = np.where(R<=1.,R,1.)
            C = np.array(C)
            C = (C.T*R).T
            R = np.ones_like(R)*0.05
        RF = 100.
        RF2 = 100.
        if sumFo and sumDF:
            RF = 100.*sumDF/sumFo
            RF2 = 100.*sumDF2/sumFo2  
        return HKL,zip(list(R),C),RF,RF2

    def GetTruePosition(xy):
        View = GL.glGetIntegerv(GL.GL_VIEWPORT)
        Proj = GL.glGetDoublev(GL.GL_PROJECTION_MATRIX)
        Model = GL.glGetDoublev(GL.GL_MODELVIEW_MATRIX)
        Zmax = 1.
        xy = [int(xy[0]),int(View[3]-xy[1])]
        for i,ref in enumerate(hklRef):
            h,k,l = ref[:3]
            try:
                X,Y,Z = GLU.gluProject(h,k,l,Model,Proj,View)
                XY = [int(X),int(Y)]
                if np.allclose(xy,XY,atol=10) and Z < Zmax:
                    Zmax = Z
                    return [int(h),int(k),int(l)]
            except ValueError:
                return [int(h),int(k),int(l)]
                
                        
    def SetTranslation(newxy):
#first get translation vector in screen coords.       
        oldxy = drawingData['oldxy']
        if not len(oldxy): oldxy = list(newxy)
        dxy = newxy-oldxy
        drawingData['oldxy'] = list(newxy)
        V = np.array([-dxy[0],dxy[1],0.])
#then transform to rotated crystal coordinates & apply to view point        
        Q = drawingData['Quaternion']
        V = np.inner(Bmat,G2mth.prodQVQ(G2mth.invQ(Q),V))
        Tx,Ty,Tz = drawingData['viewPoint'][0]
        Tx += V[0]*0.1
        Ty += V[1]*0.1
        Tz += V[2]*0.1
        drawingData['viewPoint'][0] =  np.array([Tx,Ty,Tz])
        
    def SetRotation(newxy):
        'Perform a rotation in x-y space due to a left-mouse drag'
    #first get rotation vector in screen coords. & angle increment        
        oldxy = drawingData['oldxy']
        if not len(oldxy): oldxy = list(newxy)
        dxy = newxy-oldxy
        drawingData['oldxy'] = list(newxy)
        V = np.array([dxy[1],dxy[0],0.])
        A = 0.25*np.sqrt(dxy[0]**2+dxy[1]**2)
        if not A: return # nothing changed, nothing to do
    # next transform vector back to xtal coordinates via inverse quaternion
    # & make new quaternion
        Q = drawingData['Quaternion']
        V = G2mth.prodQVQ(G2mth.invQ(Q),np.inner(Bmat,V))
        DQ = G2mth.AVdeg2Q(A,V)
        Q = G2mth.prodQQ(Q,DQ)
        drawingData['Quaternion'] = Q
    # finally get new view vector - last row of rotation matrix
        VD = np.inner(Bmat,G2mth.Q2Mat(Q)[2])
        VD /= np.sqrt(np.sum(VD**2))
        drawingData['viewDir'] = VD
        
    def SetRotationZ(newxy):                        
#first get rotation vector (= view vector) in screen coords. & angle increment        
        View = GL.glGetIntegerv(GL.GL_VIEWPORT)
        cent = [View[2]/2,View[3]/2]
        oldxy = drawingData['oldxy']
        if not len(oldxy): oldxy = list(newxy)
        dxy = newxy-oldxy
        drawingData['oldxy'] = list(newxy)
        V = drawingData['viewDir']
        A = [0,0]
        A[0] = dxy[1]*.25
        A[1] = dxy[0]*.25
        if newxy[0] > cent[0]:
            A[0] *= -1
        if newxy[1] < cent[1]:
            A[1] *= -1        
# next transform vector back to xtal coordinates & make new quaternion
        Q = drawingData['Quaternion']
        V = np.inner(Amat,V)
        Qx = G2mth.AVdeg2Q(A[0],V)
        Qy = G2mth.AVdeg2Q(A[1],V)
        Q = G2mth.prodQQ(Q,Qx)
        Q = G2mth.prodQQ(Q,Qy)
        drawingData['Quaternion'] = Q

    def OnMouseDown(event):
        xy = event.GetPosition()
        drawingData['oldxy'] = list(xy)
        
    def OnMouseMove(event):
        if event.ShiftDown():           #don't want any inadvertant moves when picking
            return
        newxy = event.GetPosition()
                                
        if event.Dragging():
            if event.LeftIsDown():
                SetRotation(newxy)
            elif event.RightIsDown():
                SetTranslation(newxy)
                Tx,Ty,Tz = drawingData['viewPoint'][0]
            elif event.MiddleIsDown():
                SetRotationZ(newxy)
            Draw('move')
        else:
            hkl = GetTruePosition(newxy)
            if hkl:
                h,k,l = hkl
                Page.canvas.SetToolTipString('%d,%d,%d'%(h,k,l))
                G2frame.G2plotNB.status.SetStatusText('hkl = %d,%d,%d'%(h,k,l),1)
        
    def OnMouseWheel(event):
        if event.ShiftDown():
            return
        drawingData['cameraPos'] += event.GetWheelRotation()/120.
        drawingData['cameraPos'] = max(0.1,min(20.00,drawingData['cameraPos']))
        Draw('wheel')
        
    def SetBackground():
        R,G,B,A = Page.camera['backColor']
        GL.glClearColor(R,G,B,A)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        
    def SetLights():
        GL.glEnable(GL.GL_DEPTH_TEST)
#        GL.glShadeModel(GL.GL_SMOOTH)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glEnable(GL.GL_LIGHT0)
        GL.glLightModeli(GL.GL_LIGHT_MODEL_TWO_SIDE,0)
        GL.glLightfv(GL.GL_LIGHT0,GL.GL_AMBIENT,[1,1,1,1])
        GL.glLightfv(GL.GL_LIGHT0,GL.GL_DIFFUSE,[1,1,1,1])
        
    def RenderBox(x,y,z):
        GL.glEnable(GL.GL_COLOR_MATERIAL)
        GL.glLineWidth(1)
        GL.glPushMatrix()
        GL.glTranslate(x,y,z)
        GL.glColor4ubv([0,0,0,0])
        GL.glBegin(GL.GL_LINES)
        for line,color in zip(uEdges,uColors):
            GL.glColor3ubv(color)
            GL.glVertex3fv(line[0])
            GL.glVertex3fv(line[1])
        GL.glEnd()
        GL.glPopMatrix()
        GL.glColor4ubv([0,0,0,0])
        GL.glDisable(GL.GL_COLOR_MATERIAL)
        
    def RenderUnitVectors(x,y,z,labxyz=['','','']):
        GL.glEnable(GL.GL_COLOR_MATERIAL)
        GL.glLineWidth(1)
        GL.glPushMatrix()
        GL.glTranslate(x,y,z)
        GL.glBegin(GL.GL_LINES)
        for line,color in zip(uEdges,uColors)[:3]:
            GL.glColor3ubv(color)
            GL.glVertex3fv([0,0,0])
#            GL.glVertex3fv(-line[1])
            GL.glVertex3fv(line[1])
        GL.glEnd()
        GL.glRotate(180,1,0,0)             #fix to flip about x-axis
        for ix,txt in enumerate(labxyz):
            if txt:
                pos = uEdges[ix][1]
                GL.glTranslate(pos[0],-1.5*pos[1],-pos[2])
                text = gltext.TextElement(text=txt,font=Font)
                text.draw_text(scale=0.05)
                GL.glTranslate(-pos[0],1.5*pos[1],pos[2])
        GL.glPopMatrix()
        GL.glColor4ubv([0,0,0,0])
        GL.glDisable(GL.GL_COLOR_MATERIAL)
                
    def RenderDots(XYZ,RC):
        GL.glEnable(GL.GL_COLOR_MATERIAL)
        XYZ = np.array(XYZ)
        GL.glPushMatrix()
        for xyz,rc in zip(XYZ,RC):
            x,y,z = xyz
            r,c = rc
            GL.glColor3ubv(c)
            GL.glPointSize(r*50)
            GL.glBegin(GL.GL_POINTS)
            GL.glVertex3fv(xyz)
            GL.glEnd()
        GL.glPopMatrix()
        GL.glColor4ubv([0,0,0,0])
        GL.glDisable(GL.GL_COLOR_MATERIAL)
        
    def Draw(caller=''):
#useful debug?        
#        if caller:
#            print caller
# end of useful debug
        VS = np.array(Page.canvas.GetSize())
        aspect = float(VS[0])/float(VS[1])
        cPos = drawingData['cameraPos']
        Zclip = drawingData['Zclip']*cPos/20.
        if Data['Zone']:
            Zclip = 0.01
        Q = drawingData['Quaternion']
        Tx,Ty,Tz = drawingData['viewPoint'][0][:3]
        G,g = G2lat.cell2Gmat(cell)
        GS = G
        GS[0][1] = GS[1][0] = math.sqrt(GS[0][0]*GS[1][1])
        GS[0][2] = GS[2][0] = math.sqrt(GS[0][0]*GS[2][2])
        GS[1][2] = GS[2][1] = math.sqrt(GS[1][1]*GS[2][2])
        
        HKL,RC,RF,RF2 = FillHKLRC()
        G2frame.G2plotNB.status.SetStatusText   \
            ('Plot type = %s for %s; RF = %6.2f%%, RF%s = %6.2f%%'%(Data['Type'],Name,RF,super2,RF2),1)
        
        SetBackground()
        GL.glInitNames()
        GL.glPushName(0)
        
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glViewport(0,0,VS[0],VS[1])
        GLU.gluPerspective(20.,aspect,cPos-Zclip,cPos+Zclip)
        GLU.gluLookAt(0,0,cPos,0,0,0,0,1,0)
        SetLights()            
            
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        matRot = G2mth.Q2Mat(Q)
        matRot = np.concatenate((np.concatenate((matRot,[[0],[0],[0]]),axis=1),[[0,0,0,1],]),axis=0)
        GL.glMultMatrixf(matRot.T)
        GL.glMultMatrixf(B4mat)
        GL.glTranslate(-Tx,-Ty,-Tz)
        x,y,z = drawingData['viewPoint'][0]
        if ifBox:
            RenderBox(x,y,z)
        else:
            RenderUnitVectors(x,y,z)
        RenderUnitVectors(0,0,0,labxyz=['h','k','l'])
        RenderDots(HKL,RC)
        try:
            if Page.context: Page.canvas.SetCurrent(Page.context)
        except:
            pass
        Page.canvas.SwapBuffers()

    # PlotStructure execution starts here (N.B. initialization above)
    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('3D Structure Factors','ogl')
    if new:
        Page.views = False
    Font = Page.GetFont()
    Page.Choice = None
    choice = [' save as/key:','jpeg','tiff','bmp','h: view down h','k: view down k','l: view down l',
    'z: zero zone toggle','c: reset to default','o: set view point = 0,0,0','b: toggle box ','+: increase scale','-: decrease scale',
    'f: Fobs','s: Fobs**2','u: unit','d: Fo-Fc','w: DF/sig','i: toggle intensity scaling']
    cb = wx.ComboBox(G2frame.G2plotNB.status,style=wx.CB_DROPDOWN|wx.CB_READONLY,choices=choice)
    cb.Bind(wx.EVT_COMBOBOX, OnKeyBox)
    cb.SetValue(' save as/key:')
    Page.canvas.Bind(wx.EVT_MOUSEWHEEL, OnMouseWheel)
    Page.canvas.Bind(wx.EVT_LEFT_DOWN, OnMouseDown)
    Page.canvas.Bind(wx.EVT_RIGHT_DOWN, OnMouseDown)
    Page.canvas.Bind(wx.EVT_MIDDLE_DOWN, OnMouseDown)
    Page.canvas.Bind(wx.EVT_KEY_UP, OnKey)
    Page.canvas.Bind(wx.EVT_MOTION, OnMouseMove)
#    Page.canvas.Bind(wx.EVT_SIZE, OnSize)
    Page.camera['position'] = drawingData['cameraPos']
    Page.camera['viewPoint'] = np.inner(Amat,drawingData['viewPoint'][0])
    Page.camera['backColor'] = np.array(list(drawingData['backColor'])+[0,])/255.
    Page.controls = Data
    try:
        Page.canvas.SetCurrent()
    except:
        pass
    Draw('main')
#    if firstCall: Draw('main') # draw twice the first time that graphics are displayed

       
################################################################################
##### PlotPatterns
################################################################################
def ReplotPattern(G2frame,newPlot,plotType,PatternName=None,PickName=None):
    '''This does the same as PlotPatterns except that it expects the information
    to be plotted (pattern name, item picked in tree + eventually the reflection list)
    to be passed as names rather than references to wx tree items, defined as class entries
    '''
    if PatternName:
        G2frame.PatternId = G2gd.GetPatternTreeItemId(G2frame, G2frame.root, PatternName)
    if PickName == PatternName:
        G2frame.PickId = G2frame.PatternId
    elif PickName:
        G2frame.PickId = G2gd.GetPatternTreeItemId(G2frame, G2frame.PatternId, PickName)
    # for now I am not sure how to regenerate G2frame.HKL
    G2frame.HKL = [] # TODO
    PlotPatterns(G2frame,newPlot,plotType)

def PlotPatterns(G2frame,newPlot=False,plotType='PWDR'):
    '''Powder pattern plotting package - displays single or multiple powder patterns as intensity vs
    2-theta, q or TOF. Can display multiple patterns as "waterfall plots" or contour plots. Log I 
    plotting available.

    Note that plotting information will be found in:
       G2frame.PatternId (contains the tree item for the current histogram)
       G2frame.PickId (contains the actual selected tree item (can be child of histogram)
       G2frame.HKL (used for tool tip display of hkl for selected phase reflection list)
    '''
    global exclLines
    global DifLine # BHT: probably does not need to be global
    global Ymax
    global Pattern
    plottype = plotType
    
    if not G2frame.PatternId:
        return
    if 'PKS' in plottype:
        PlotPowderLines(G2frame)
        return
#patch
    data = G2frame.PatternTree.GetItemPyData(G2frame.PatternId)
    if 'Offset' not in data[0] and plotType in ['PWDR','SASD']:     #plot offset data
        Ymax = max(data[1][1])
        data[0].update({'Offset':[0.0,0.0],'delOffset':0.02*Ymax,'refOffset':-0.1*Ymax,
            'refDelt':0.1*Ymax,})
        G2frame.PatternTree.SetItemPyData(G2frame.PickId,data)
#end patch
    def OnPlotKeyPress(event):
        try:        #one way to check if key stroke will work on plot
            Parms,Parms2 = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,G2frame.PatternId, 'Instrument Parameters'))
        except TypeError:
            G2frame.G2plotNB.status.SetStatusText('Select '+plottype+' pattern first',1)
            return
        newPlot = False
        if event.key == 'w':
            G2frame.Weight = not G2frame.Weight
            if not G2frame.Weight and 'PWDR' in plottype:
                G2frame.SinglePlot = True
            newPlot = True
        elif event.key == 'e' and 'SASD' in plottype:
            G2frame.ErrorBars = not G2frame.ErrorBars
        elif event.key == 'b':
            G2frame.SubBack = not G2frame.SubBack
            if not G2frame.SubBack:
                G2frame.SinglePlot = True                
        elif event.key == 'n':
            if G2frame.Contour:
                pass
            else:
                G2frame.logPlot = not G2frame.logPlot
                if not G2frame.logPlot:
                    Pattern[0]['Offset'][0] = 0
                newPlot = True
        elif event.key == 's' and 'PWDR' in plottype:
            if G2frame.Contour:
                choice = [m for m in mpl.cm.datad.keys() if not m.endswith("_r")]
                choice.sort()
                dlg = wx.SingleChoiceDialog(G2frame,'Select','Color scheme',choice)
                if dlg.ShowModal() == wx.ID_OK:
                    sel = dlg.GetSelection()
                    G2frame.ContourColor = choice[sel]
                else:
                    G2frame.ContourColor = 'Paired'
                dlg.Destroy()
            elif G2frame.SinglePlot:
                G2frame.plotStyle['sqrtPlot'] = not G2frame.plotStyle['sqrtPlot']
                Ymax = max(Pattern[1][1])
                if G2frame.plotStyle['sqrtPlot']:
                    Pattern[0]['delOffset'] = .002*np.sqrt(Ymax)
                    Pattern[0]['refOffset'] = -0.1*np.sqrt(Ymax)
                    Pattern[0]['refDelt'] = .1*np.sqrt(Ymax)
                else:
                    Pattern[0]['delOffset'] = .02*Ymax
                    Pattern[0]['refOffset'] = -0.1*Ymax
                    Pattern[0]['refDelt'] = .1*Ymax
            newPlot = True
        elif event.key == 'u' and (G2frame.Contour or not G2frame.SinglePlot):
            if G2frame.Contour:
                G2frame.Cmax = min(1.0,G2frame.Cmax*1.2)
            elif Pattern[0]['Offset'][0] < 100.:
                Pattern[0]['Offset'][0] += 1.
        elif event.key == 'd' and (G2frame.Contour or not G2frame.SinglePlot):
            if G2frame.Contour:
                G2frame.Cmax = max(0.0,G2frame.Cmax*0.8)
            elif Pattern[0]['Offset'][0] > 0.:
                Pattern[0]['Offset'][0] -= 1.
        elif event.key == 'l' and not G2frame.SinglePlot:
            Pattern[0]['Offset'][1] -= 1.
        elif event.key == 'r' and not G2frame.SinglePlot:
            Pattern[0]['Offset'][1] += 1.
        elif event.key == 'o' and not G2frame.SinglePlot:
            G2frame.Cmax = 1.0
            Pattern[0]['Offset'] = [0,0]
        elif event.key == 'c' and 'PWDR' in plottype:
            newPlot = True
            if not G2frame.Contour:
                G2frame.SinglePlot = False
                Pattern[0]['Offset'] = [0.,0.]
            else:
                G2frame.SinglePlot = True                
            G2frame.Contour = not G2frame.Contour
        elif event.key == 'q': 
            if 'PWDR' in plottype:
                newPlot = True
                G2frame.plotStyle['qPlot'] = not G2frame.plotStyle['qPlot']
                G2frame.plotStyle['dPlot'] = False
            elif 'SASD' in plottype:
                newPlot = True
                G2frame.plotStyle['sqPlot'] = not G2frame.plotStyle['sqPlot']
        elif event.key == 't' and 'PWDR' in plottype:
            G2frame.plotStyle['dPlot'] = not G2frame.plotStyle['dPlot']
            G2frame.plotStyle['qPlot'] = False
            newPlot = True      
        elif event.key == 'm':
            G2frame.plotStyle['sqrtPlot'] = False
            G2frame.SinglePlot = not G2frame.SinglePlot                
            newPlot = True
        elif event.key == 'f' and not G2frame.SinglePlot:
            choices = G2gd.GetPatternTreeDataNames(G2frame,plotType)
            dlg = G2G.G2MultiChoiceDialog(G2frame.dataFrame,'Select dataset to plot', 
                'Multidata plot selection',choices)
            if dlg.ShowModal() == wx.ID_OK:
                G2frame.selections = []
                select = dlg.GetSelections()
                if select:
                    for id in select:
                        G2frame.selections.append(choices[id])
                else:
                    G2frame.selections = None
            dlg.Destroy()
            newPlot = True
        elif event.key in ['+','=']:
            G2frame.plusPlot = not G2frame.plusPlot
        elif event.key == 'i' and G2frame.Contour:                  #for smoothing contour plot
            choice = ['nearest','bilinear','bicubic','spline16','spline36','hanning',
               'hamming','hermite','kaiser','quadric','catrom','gaussian','bessel',
               'mitchell','sinc','lanczos']
            dlg = wx.SingleChoiceDialog(G2frame,'Select','Interpolation',choice)
            if dlg.ShowModal() == wx.ID_OK:
                sel = dlg.GetSelection()
                G2frame.Interpolate = choice[sel]
            else:
                G2frame.Interpolate = 'nearest'
            dlg.Destroy()
        else:
#            print 'no binding for key',event.key
            #GSASIIpath.IPyBreak()
            return
        wx.CallAfter(PlotPatterns,G2frame,newPlot=newPlot,plotType=plottype)
        
    def OnMotion(event):
        xpos = event.xdata
        if xpos:                                        #avoid out of frame mouse position
            ypos = event.ydata
            Page.canvas.SetCursor(wx.CROSS_CURSOR)
            try:
                Id = G2gd.GetPatternTreeItemId(G2frame,G2frame.PatternId, 'Instrument Parameters')
                if not Id: return
                Parms,Parms2 = G2frame.PatternTree.GetItemPyData(Id)
                if G2frame.plotStyle['qPlot'] and 'PWDR' in plottype:
                    q = xpos
                    dsp = 2.*np.pi/q
                    try:
                        xpos = G2lat.Dsp2pos(Parms,2.0*np.pi/xpos)
                    except ValueError:      #avoid bad value in asin beyond upper limit
                        pass
                elif 'SASD' in plottype:
                    q = xpos
                    dsp = 2.*np.pi/q
                elif G2frame.plotStyle['dPlot']:
                    dsp = xpos
                    q = 2.*np.pi/dsp
                    xpos = G2lat.Dsp2pos(Parms,xpos)
                elif G2frame.Contour and 'T' in Parms['Type'][0]:
                    xpos = X[xpos]                    
                    dsp = G2lat.Pos2dsp(Parms,xpos)
                    q = 2.*np.pi/dsp
                else:
                    dsp = G2lat.Pos2dsp(Parms,xpos)
                    q = 2.*np.pi/dsp
                if G2frame.Contour: #PWDR only
                    if 'C' in Parms['Type'][0]:
                        G2frame.G2plotNB.status.SetStatusText('2-theta =%9.3f d =%9.5f q = %9.5f pattern ID =%5d'%(xpos,dsp,q,int(ypos)),1)
                    else:
                        G2frame.G2plotNB.status.SetStatusText('TOF =%9.3f d =%9.5f q = %9.5f pattern ID =%5d'%(xpos,dsp,q,int(ypos)),1)
                else:
                    if 'C' in Parms['Type'][0]:
                        if 'PWDR' in plottype:
                            if G2frame.plotStyle['sqrtPlot']:
                                G2frame.G2plotNB.status.SetStatusText('2-theta =%9.3f d =%9.5f q = %9.5f sqrt(Intensity) =%9.2f'%(xpos,dsp,q,ypos),1)
                            else:
                                G2frame.G2plotNB.status.SetStatusText('2-theta =%9.3f d =%9.5f q = %9.5f Intensity =%9.2f'%(xpos,dsp,q,ypos),1)
                        elif 'SASD' in plottype:
                            G2frame.G2plotNB.status.SetStatusText('q =%12.5g Intensity =%12.5g d =%9.1f'%(q,ypos,dsp),1)
                    else:
                        if G2frame.plotStyle['sqrtPlot']:
                            G2frame.G2plotNB.status.SetStatusText('TOF =%9.3f d =%9.5f q =%9.5f sqrt(Intensity) =%9.2f'%(xpos,dsp,q,ypos),1)
                        else:
                            G2frame.G2plotNB.status.SetStatusText('TOF =%9.3f d =%9.5f q =%9.5f Intensity =%9.2f'%(xpos,dsp,q,ypos),1)
                if G2frame.itemPicked:
                    Page.canvas.SetToolTipString('%9.5f'%(xpos))
                if G2frame.PickId:
                    found = []
                    pickIdText = G2frame.PatternTree.GetItemText(G2frame.PickId)
                    if pickIdText in ['Index Peak List','Unit Cells List','Reflection Lists'] or \
                        'PWDR' in pickIdText:
                        indx = -1
                        if pickIdText in ['Index Peak List','Unit Cells List',]:
                            indx = -2
                        if len(G2frame.HKL):
                            view = Page.toolbar._views.forward()[0][:2]
                            wid = view[1]-view[0]
                            found = G2frame.HKL[np.where(np.fabs(G2frame.HKL.T[indx]-xpos) < 0.002*wid)]
                        if len(found):
                            if len(found[0]) > 6:   #SS reflections
                                h,k,l,m = found[0][:4]
                                Page.canvas.SetToolTipString('%d,%d,%d,%d'%(int(h),int(k),int(l),int(m)))
                            else:
                                h,k,l = found[0][:3] 
                                Page.canvas.SetToolTipString('%d,%d,%d'%(int(h),int(k),int(l)))
                        else:
                            Page.canvas.SetToolTipString('')

            except TypeError:
                G2frame.G2plotNB.status.SetStatusText('Select '+plottype+' pattern first',1)
                
    def OnPress(event): #ugh - this removes a matplotlib error for mouse clicks in log plots                  
        np.seterr(invalid='ignore')
                                                   
    def onMoveDiffCurve(event):
        '''Respond to a menu command to move the difference curve. 
        '''
        if not DifLine[0]:
            print('No difference curve!')
            return
        G2frame.itemPicked = DifLine[0]
        G2frame.G2plotNB.Parent.Raise()
        OnPick(None)

    def onMoveTopTick(event):
        '''Respond to a menu command to move the tick locations. 
        '''
        if len(Page.phaseList) == 0:
            print("there are tick marks (no phases)")
            return
        G2frame.itemPicked = Page.tickDict[Page.phaseList[0]]
        G2frame.G2plotNB.Parent.Raise()
        OnPick(None)
                
    def onMoveTickSpace(event):
        '''Respond to a menu command to move the tick spacing. 
        '''
        if len(Page.phaseList) == 0:
            print("there are tick marks (no phases)")
            return
        G2frame.itemPicked = Page.tickDict[Page.phaseList[-1]]
        G2frame.G2plotNB.Parent.Raise()
        OnPick(None)
        
    def onMovePeak(event):
        selectedPeaks = list(set([row for row,col in G2frame.dataDisplay.GetSelectedCells()] +
                                G2frame.dataDisplay.GetSelectedRows()))
        if len(selectedPeaks) != 1:
            G2G.G2MessageBox(G2frame,'You must select one peak in the table first. # selected ='+
                             str(len(selectedPeaks)),'Select one peak')
            return
        #GSASIIpath.IPyBreak()
        G2frame.itemPicked = G2frame.Lines[selectedPeaks[0]+2] # 1st 2 lines are limits
        G2frame.G2plotNB.Parent.Raise()
        OnPick(None)
                        
    def OnPick(event):
        '''Respond to an item being picked. This usually means that the item
        will be dragged with the mouse. 
        '''
        def OnDragMarker(event):
            '''Respond to dragging of a plot Marker
            '''
            if event.xdata is None or event.ydata is None: return   # ignore if cursor out of window
            Page.canvas.restore_region(savedplot)
            G2frame.itemPicked.set_data([event.xdata], [event.ydata])
            Page.figure.gca().draw_artist(G2frame.itemPicked)
            Page.canvas.blit(Page.figure.gca().bbox)
            
        def OnDragLine(event):
            '''Respond to dragging of a plot line
            '''
            if event.xdata is None: return   # ignore if cursor out of window
            Page.canvas.restore_region(savedplot)
            coords = G2frame.itemPicked.get_data()
            coords[0][0] = coords[0][1] = event.xdata
            coords = G2frame.itemPicked.set_data(coords)
            Page.figure.gca().draw_artist(G2frame.itemPicked)
            Page.canvas.blit(Page.figure.gca().bbox)

        def OnDragTickmarks(event):
            '''Respond to dragging of the reflection tick marks
            '''
            if event.ydata is None: return   # ignore if cursor out of window
            Page.canvas.restore_region(savedplot)
            if Page.pickTicknum:
                refDelt = -(event.ydata-Pattern[0]['refOffset'])/Page.pickTicknum
                refOffset = Pattern[0]['refOffset']
            else:       #1st row of refl ticks
                refOffset = event.ydata
                refDelt = Pattern[0]['refDelt']
            for pId,phase in enumerate(Page.phaseList):
                pos = refOffset - pId*refDelt
                coords = Page.tickDict[phase].get_data()
                coords[1][:] = pos
                Page.tickDict[phase].set_data(coords)
                Page.figure.gca().draw_artist(Page.tickDict[phase])
            Page.canvas.blit(Page.figure.gca().bbox)

        def OnDragDiffCurve(event):
            '''Respond to dragging of the difference curve
            '''
            if event.ydata is None: return   # ignore if cursor out of window
            Page.canvas.restore_region(savedplot)
            coords = G2frame.itemPicked.get_data()
            coords[1][:] += Page.diffOffset + event.ydata
            Page.diffOffset = -event.ydata
            G2frame.itemPicked.set_data(coords)
            Page.figure.gca().draw_artist(G2frame.itemPicked)
            Page.canvas.blit(Page.figure.gca().bbox)

        try:
            Parms,Parms2 = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,G2frame.PatternId, 'Instrument Parameters'))
        except TypeError:
            return
        if event is None: # called from a menu command rather than by click on mpl artist
            mouse = 1
            pick = G2frame.itemPicked
            ind = np.array([0])
        else: 
            if G2frame.itemPicked is not None: return
            pick = event.artist
            mouse = event.mouseevent
            xpos = pick.get_xdata()
            ypos = pick.get_ydata()
            ind = event.ind
            xy = list(zip(np.take(xpos,ind),np.take(ypos,ind))[0])
            # convert from plot units
            if G2frame.plotStyle['qPlot']:                              #qplot - convert back to 2-theta
                xy[0] = G2lat.Dsp2pos(Parms,2*np.pi/xy[0])
            elif G2frame.plotStyle['dPlot']:                            #dplot - convert back to 2-theta
                xy[0] = G2lat.Dsp2pos(Parms,xy[0])
            if G2frame.plotStyle['sqrtPlot']:
                xy[1] = xy[1]**2
        PatternId = G2frame.PatternId
        PickId = G2frame.PickId
        if G2frame.PatternTree.GetItemText(PickId) == 'Peak List':
            if ind.all() != [0] and ObsLine[0].get_label() in str(pick):    #picked a data point, add a new peak
                data = G2frame.PatternTree.GetItemPyData(G2frame.PickId)
                XY = G2mth.setPeakparms(Parms,Parms2,xy[0],xy[1])
                data['peaks'].append(XY)
                data['sigDict'] = {}    #now invalid
                G2pdG.UpdatePeakGrid(G2frame,data)
                PlotPatterns(G2frame,plotType=plottype)
            else:                                                   #picked a peak list line
                # prepare to animate move of line
                G2frame.itemPicked = pick
                pick.set_linestyle(':') # set line as dotted
                Page = G2frame.G2plotNB.nb.GetPage(plotNum)
                Page.figure.gca()
                Page.canvas.draw() # refresh without dotted line & save bitmap
                savedplot = Page.canvas.copy_from_bbox(Page.figure.gca().bbox)
                G2frame.cid = Page.canvas.mpl_connect('motion_notify_event', OnDragLine)
                pick.set_linestyle('--') # back to dashed
        elif G2frame.PatternTree.GetItemText(PickId) == 'Limits':
            if ind.all() != [0]:                                    #picked a data point
                LimitId = G2gd.GetPatternTreeItemId(G2frame,PatternId, 'Limits')
                data = G2frame.PatternTree.GetItemPyData(LimitId)
                if G2frame.plotStyle['qPlot']:                              #qplot - convert back to 2-theta
                    xy[0] = G2lat.Dsp2pos(Parms,2*np.pi/xy[0])
                elif G2frame.plotStyle['dPlot']:                            #dplot - convert back to 2-theta
                    xy[0] = G2lat.Dsp2pos(Parms,xy[0])
                if G2frame.ifGetExclude:
                    excl = [0,0]
                    excl[0] = max(data[1][0],min(xy[0],data[1][1]))
                    excl[1] = excl[0]+0.1
                    data.append(excl)
                    G2frame.ifGetExclude = False
                else:
                    if mouse.button==1:
                        data[1][0] = min(xy[0],data[1][1])
                    if mouse.button==3:
                        data[1][1] = max(xy[0],data[1][0])
                G2frame.PatternTree.SetItemPyData(LimitId,data)
                G2pdG.UpdateLimitsGrid(G2frame,data,plottype)
                wx.CallAfter(PlotPatterns,G2frame,plotType=plottype)
            else:                                                   #picked a limit line
                # prepare to animate move of line
                G2frame.itemPicked = pick
                pick.set_linestyle(':') # set line as dotted
                Page = G2frame.G2plotNB.nb.GetPage(plotNum)
                Page.figure.gca()
                Page.canvas.draw() # refresh without dotted line & save bitmap
                savedplot = Page.canvas.copy_from_bbox(Page.figure.gca().bbox)
                G2frame.cid = Page.canvas.mpl_connect('motion_notify_event', OnDragLine)
                pick.set_linestyle('--') # back to dashed
                
        elif G2frame.PatternTree.GetItemText(PickId) == 'Models':
            if ind.all() != [0]:                                    #picked a data point
                LimitId = G2gd.GetPatternTreeItemId(G2frame,PatternId, 'Limits')
                data = G2frame.PatternTree.GetItemPyData(LimitId)
                if mouse.button==1:
                    data[1][0] = min(xy[0],data[1][1])
                if mouse.button==3:
                    data[1][1] = max(xy[0],data[1][0])
                G2frame.PatternTree.SetItemPyData(LimitId,data)
                wx.CallAfter(PlotPatterns,G2frame,plotType=plottype)
            else:                                                   #picked a limit line
                G2frame.itemPicked = pick
        elif (G2frame.PatternTree.GetItemText(PickId) == 'Reflection Lists' or
                'PWDR' in G2frame.PatternTree.GetItemText(PickId)
                ):
            G2frame.itemPicked = pick
            Page = G2frame.G2plotNB.nb.GetPage(plotNum)
            Page.figure.gca()
            if DifLine[0] is G2frame.itemPicked:  # pick of difference curve
                Page.canvas.draw() # save bitmap
                savedplot = Page.canvas.copy_from_bbox(Page.figure.gca().bbox)
                Page.diffOffset = Pattern[0]['delOffset']
                G2frame.cid = Page.canvas.mpl_connect('motion_notify_event', OnDragDiffCurve)
            else:                         # pick of plot tick mark (is anything else possible?)
                pick = str(G2frame.itemPicked).split('(',1)[1][:-1]
                if pick not in Page.phaseList: # picked something other than a tickmark
                    return
                Page.pickTicknum = Page.phaseList.index(pick)
                resetlist = []
                for pId,phase in enumerate(Page.phaseList): # set the tickmarks to a lighter color
                    col = Page.tickDict[phase].get_color()
                    rgb = mpl.colors.ColorConverter().to_rgb(col)
                    rgb_light = [(2 + i)/3. for i in rgb]
                    resetlist.append((Page.tickDict[phase],rgb))
                    Page.tickDict[phase].set_color(rgb_light)
                    Page.tickDict[phase].set_zorder(99) # put on top
                Page.canvas.draw() # refresh with dimmed tickmarks 
                savedplot = Page.canvas.copy_from_bbox(Page.figure.gca().bbox)
                for f,v in resetlist:  # reset colors back
                    f.set_zorder(0)
                    f.set_color(v) # reset colors back to original values
                G2frame.cid = Page.canvas.mpl_connect('motion_notify_event', OnDragTickmarks)
            
        elif G2frame.PatternTree.GetItemText(PickId) == 'Background':
            # selected a fixed background point. Can move it or delete it.
            for mode,id in G2frame.dataFrame.wxID_BackPts.iteritems(): # what menu is selected?
                if G2frame.dataFrame.BackMenu.FindItemById(id).IsChecked():
                    break
            # mode will be 'Add' or 'Move' or 'Del'
            if pick.get_marker() == 'D':
                # find the closest point
                backDict = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,G2frame.PatternId, 'Background'))[1]
                d2 = [(x-xy[0])**2+(y-xy[1])**2 for x,y in backDict['FixedPoints']]
                G2frame.fixPtMarker = d2.index(min(d2))
                if mode == 'Move':
                    # animate move of FixedBkg marker
                    G2frame.itemPicked = pick
                    pick.set_marker('|') # change the point appearance
                    Page = G2frame.G2plotNB.nb.GetPage(plotNum)
                    Page.figure.gca()
                    Page.canvas.draw() # refresh with changed point & save bitmap
                    savedplot = Page.canvas.copy_from_bbox(Page.figure.gca().bbox)
                    G2frame.cid = Page.canvas.mpl_connect('motion_notify_event', OnDragMarker)
                    pick.set_marker('D') # put it back
                elif mode == 'Del':
                    del backDict['FixedPoints'][G2frame.fixPtMarker]
                    wx.CallAfter(PlotPatterns,G2frame,plotType=plottype)
                return
                
    def OnRelease(event):
        '''This is called when the mouse button is released when a plot object is dragged
        due to an item pick, or when invoked via a menu item (such as in onMoveDiffCurve),
        or for background points, which may be added/moved/deleted here.
        New peaks are also added here.
        '''
        plotNum = G2frame.G2plotNB.plotList.index('Powder Patterns')
        Page = G2frame.G2plotNB.nb.GetPage(plotNum)
        if G2frame.cid is not None:         # if there is a drag connection, delete it
            Page.canvas.mpl_disconnect(G2frame.cid)
            G2frame.cid = None
        if event.xdata is None or event.ydata is None: # ignore drag if cursor is outside of plot
            wx.CallAfter(PlotPatterns,G2frame,plotType=plottype)
            return
        if not G2frame.PickId:
            return
        
        PickId = G2frame.PickId                             # points to item in tree
        if G2frame.PatternTree.GetItemText(PickId) == 'Background' and event.xdata:
            if Page.toolbar._active:    # prevent ops. if a toolbar zoom button pressed
                return 
            # Background page, deal with fixed background points
            if G2frame.SubBack or G2frame.Weight or G2frame.Contour or not G2frame.SinglePlot:
                return
            backDict = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,G2frame.PatternId, 'Background'))[1]
            if 'FixedPoints' not in backDict: backDict['FixedPoints'] = []
            try:
                Parms,Parms2 = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,G2frame.PatternId, 'Instrument Parameters'))
            except TypeError:
                return
            # unit conversions
            xy = [event.xdata,event.ydata]
            if G2frame.plotStyle['qPlot']:                              #qplot - convert back to 2-theta
                xy[0] = G2lat.Dsp2pos(Parms,2*np.pi/xy[0])
            elif G2frame.plotStyle['dPlot']:                            #dplot - convert back to 2-theta
                xy[0] = G2lat.Dsp2pos(Parms,xy[0])
            if G2frame.plotStyle['sqrtPlot']:
                xy[1] = xy[1]**2
            for mode,id in G2frame.dataFrame.wxID_BackPts.iteritems(): # what menu item is selected?
                if G2frame.dataFrame.BackMenu.FindItemById(id).IsChecked():
                    break
            if mode == 'Add':
                backDict['FixedPoints'].append(xy)
                Plot = Page.figure.gca()
                Plot.plot(event.xdata,event.ydata,'rD',clip_on=Clip_on,picker=3.)
                Page.canvas.draw()
                return
            elif G2frame.itemPicked is not None: # end of drag in move
                backDict['FixedPoints'][G2frame.fixPtMarker] = xy
                G2frame.itemPicked = None
                wx.CallAfter(PlotPatterns,G2frame,plotType=plottype)
                return
        
        if G2frame.itemPicked is None: return
        if DifLine[0] is G2frame.itemPicked:   # respond to dragging of the difference curve
            data = G2frame.PatternTree.GetItemPyData(PickId)
            ypos = event.ydata
            Pattern[0]['delOffset'] = -ypos
            G2frame.itemPicked = None
            wx.CallAfter(PlotPatterns,G2frame,plotType=plottype)
            return
        Parms,Parms2 = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,G2frame.PatternId, 'Instrument Parameters'))
        xpos = event.xdata
        if G2frame.PatternTree.GetItemText(PickId) in ['Peak List','Limits'] and xpos:
            lines = []
            for line in G2frame.Lines: 
                lines.append(line.get_xdata()[0])
            try:
                lineNo = lines.index(G2frame.itemPicked.get_xdata()[0])
            except ValueError:
                lineNo = -1
            if  lineNo in [0,1] or lineNo in exclLines:
                LimitId = G2gd.GetPatternTreeItemId(G2frame,G2frame.PatternId, 'Limits')
                limits = G2frame.PatternTree.GetItemPyData(LimitId)
                id = lineNo/2+1
                id2 = lineNo%2
                if G2frame.plotStyle['qPlot'] and 'PWDR' in plottype:
                    limits[id][id2] = G2lat.Dsp2pos(Parms,2.*np.pi/xpos)
                elif G2frame.plotStyle['dPlot'] and 'PWDR' in plottype:
                    limits[id][id2] = G2lat.Dsp2pos(Parms,xpos)
                else:
                    limits[id][id2] = xpos
                if id > 1 and limits[id][0] > limits[id][1]:
                        limits[id].reverse()
                limits[1][0] = min(max(limits[0][0],limits[1][0]),limits[1][1])
                limits[1][1] = max(min(limits[0][1],limits[1][1]),limits[1][0])
                if G2frame.PatternTree.GetItemText(G2frame.PickId) == 'Limits':
                    G2pdG.UpdateLimitsGrid(G2frame,limits,plottype)
            elif lineNo > 1:
                PeakId = G2gd.GetPatternTreeItemId(G2frame,G2frame.PatternId, 'Peak List')
                peaks = G2frame.PatternTree.GetItemPyData(PeakId)
                if event.button == 3:
                    del peaks['peaks'][lineNo-2]
                else:
                    if G2frame.plotStyle['qPlot']:
                        peaks['peaks'][lineNo-2][0] = G2lat.Dsp2pos(Parms,2.*np.pi/xpos)
                    elif G2frame.plotStyle['dPlot']:
                        peaks['peaks'][lineNo-2][0] = G2lat.Dsp2pos(Parms,xpos)
                    else:
                        peaks['peaks'][lineNo-2][0] = xpos
                    peaks['sigDict'] = {}        #no longer valid
                G2pdG.UpdatePeakGrid(G2frame,peaks)
        elif G2frame.PatternTree.GetItemText(PickId) in ['Models',] and xpos:
            lines = []
            for line in G2frame.Lines: 
                lines.append(line.get_xdata()[0])
            try:
                lineNo = lines.index(G2frame.itemPicked.get_xdata()[0])
            except ValueError:
                lineNo = -1
            if  lineNo in [0,1]:
                LimitId = G2gd.GetPatternTreeItemId(G2frame,G2frame.PatternId, 'Limits')
                data = G2frame.PatternTree.GetItemPyData(LimitId)
                data[1][lineNo] = xpos
                data[1][0] = min(max(data[0][0],data[1][0]),data[1][1])
                data[1][1] = max(min(data[0][1],data[1][1]),data[1][0])
        elif (G2frame.PatternTree.GetItemText(PickId) == 'Reflection Lists' or \
            'PWDR' in G2frame.PatternTree.GetItemText(PickId)) and xpos:
            Id = G2gd.GetPatternTreeItemId(G2frame,PatternId,'Reflection Lists')
#            GSASIIpath.IPyBreak()
            if Id:     
                #Phases = G2frame.PatternTree.GetItemPyData(Id)
                pick = str(G2frame.itemPicked).split('(',1)[1][:-1]
                if 'line' not in pick:       #avoid data points, etc.
                    data = G2frame.PatternTree.GetItemPyData(G2frame.PatternId)
                    num = Page.phaseList.index(pick)
                    if num:
                        data[0]['refDelt'] = -(event.ydata-Pattern[0]['refOffset'])/num
                    else:       #1st row of refl ticks
                        data[0]['refOffset'] = event.ydata
        PlotPatterns(G2frame,plotType=plottype)
        G2frame.itemPicked = None    

    # beginning PlotPatterns execution
    new,plotNum,Page,Plot,limits = G2frame.G2plotNB.FindPlotTab('Powder Patterns','mpl')
    if not new:
        G2frame.xylim = limits
    else:
        if plottype == 'SASD':
            G2frame.logPlot = True
            G2frame.ErrorBars = True
        newPlot = True
        G2frame.Cmax = 1.0
        Page.canvas.mpl_connect('key_press_event', OnPlotKeyPress)
        Page.canvas.mpl_connect('motion_notify_event', OnMotion)
        Page.canvas.mpl_connect('pick_event', OnPick)
        Page.canvas.mpl_connect('button_release_event', OnRelease)
        Page.canvas.mpl_connect('button_press_event',OnPress)
    Phases = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,G2frame.PatternId,'Reflection Lists'))
    Page.phaseList = sorted(Phases.keys()) # define an order for phases (once!)
    if 'PWDR' in G2frame.PatternTree.GetItemText(G2frame.PickId):
        G2frame.dataFrame.Bind(wx.EVT_MENU, onMoveDiffCurve, id=G2frame.dataFrame.moveDiffCurve.GetId())
        G2frame.dataFrame.Bind(wx.EVT_MENU, onMoveTopTick, id=G2frame.dataFrame.moveTickLoc.GetId())
        G2frame.dataFrame.Bind(wx.EVT_MENU, onMoveTickSpace, id=G2frame.dataFrame.moveTickSpc.GetId())
        G2frame.dataFrame.moveDiffCurve.Enable(False)
        G2frame.dataFrame.moveTickLoc.Enable(False)
        G2frame.dataFrame.moveTickSpc.Enable(False)
    elif G2frame.PatternTree.GetItemText(G2frame.PickId) == 'Peak List':
        G2frame.dataFrame.Bind(wx.EVT_MENU, onMovePeak, id=G2frame.dataFrame.movePeak.GetId())
    # save information needed to reload from tree and redraw
    kwargs={'PatternName':G2frame.PatternTree.GetItemText(G2frame.PatternId)}
    if G2frame.PickId:
        kwargs['PickName'] = G2frame.PatternTree.GetItemText(G2frame.PickId)
    #G2frame.G2plotNB.RegisterRedrawRoutine('Powder Patterns',ReplotPattern,
    G2frame.G2plotNB.RegisterRedrawRoutine(G2frame.G2plotNB.lastRaisedPlotTab,ReplotPattern,
                                           (G2frame,newPlot,plotType),kwargs)
    # now start plotting
    G2frame.G2plotNB.status.DestroyChildren()
    Page.tickDict = {}
    DifLine = ['']
    if G2frame.Contour:
        Page.Choice = (' key press','d: lower contour max','u: raise contour max','o: reset contour max',
            'i: interpolation method','s: color scheme','c: contour off')
    else:
        if G2frame.logPlot:
            if 'PWDR' in plottype:
                if G2frame.SinglePlot:
                    Page.Choice = (' key press','n: log(I) off',
                        'c: contour on','q: toggle q plot','t: toggle d-spacing plot',
                            'm: toggle multidata plot','w: toggle divide by sig','+: toggle selection')
                else:
                    Page.Choice = (' key press','n: log(I) off',
                        'd: offset down','l: offset left','r: offset right','u: offset up','o: reset offset',
                        'c: contour on','q: toggle q plot','t: toggle d-spacing plot','f: select data',
                        'm: toggle multidata plot','w: toggle divide by sig','+: toggle selection')
            elif 'SASD' in plottype:
                if G2frame.SinglePlot:
                    Page.Choice = (' key press','b: toggle subtract background file','n: semilog on',
                        'q: toggle S(q) plot','m: toggle multidata plot','w: toggle (Io-Ic)/sig plot','+: toggle selection')
                else:
                    Page.Choice = (' key press','b: toggle subtract background file','n: semilog on',
                        'd: offset down','l: offset left','r: offset right','u: offset up','o: reset offset',
                        'q: toggle S(q) plot','m: toggle multidata plot','w: toggle (Io-Ic)/sig plot','+: toggle selection')
        else:
            if 'PWDR' in plottype:
                if G2frame.SinglePlot:
                    Page.Choice = (' key press',
                        'b: toggle subtract background','n: log(I) on','s: toggle sqrt plot','c: contour on',
                        'q: toggle q plot','t: toggle d-spacing plot','m: toggle multidata plot',
                        'w: toggle divide by sig','+: no selection')
                else:
                    Page.Choice = (' key press','l: offset left','r: offset right','d: offset down',
                        'u: offset up','o: reset offset','b: toggle subtract background','n: log(I) on','c: contour on',
                        'q: toggle q plot','t: toggle d-spacing plot','m: toggle multidata plot','f: select data',
                        'w: toggle divide by sig','+: no selection')
            elif 'SASD' in plottype:
                if G2frame.SinglePlot:
                    Page.Choice = (' key press','b: toggle subtract background file','n: loglog on','e: toggle error bars',
                        'q: toggle S(q) plot','m: toggle multidata plot','w: toggle (Io-Ic)/sig plot','+: no selection')
                else:
                    Page.Choice = (' key press','b: toggle subtract background file','n: loglog on','e: toggle error bars',
                        'd: offset down','l: offset left','r: offset right','u: offset up','o: reset offset',
                        'q: toggle S(q) plot','m: toggle multidata plot','w: toggle (Io-Ic)/sig plot','+: no selection')
    G2frame.cid = None
    Page.keyPress = OnPlotKeyPress    
    PickId = G2frame.PickId
    PatternId = G2frame.PatternId
    colors=['b','g','r','c','m','k']
    Lines = []
    exclLines = []
    if G2frame.SinglePlot and PatternId:
        Pattern = G2frame.PatternTree.GetItemPyData(PatternId)
        Pattern.append(G2frame.PatternTree.GetItemText(PatternId))
        PlotList = [Pattern,]
        Parms,Parms2 = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,
            G2frame.PatternId, 'Instrument Parameters'))
        Sample = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,G2frame.PatternId, 'Sample Parameters'))
        ParmList = [Parms,]
        SampleList = [Sample,]
        Title = Pattern[-1]
    else:     #G2frame.selection   
        Title = os.path.split(G2frame.GSASprojectfile)[1]
        PlotList = []
        ParmList = []
        SampleList = []
        if G2frame.selections is None:
            choices = G2gd.GetPatternTreeDataNames(G2frame,plotType)
        else:
            choices = G2frame.selections
        for item in choices:
            id = G2gd.GetPatternTreeItemId(G2frame,G2frame.root, item)
            Pattern = G2frame.PatternTree.GetItemPyData(id)
            if len(Pattern) < 3:                    # put name on end if needed
                Pattern.append(G2frame.PatternTree.GetItemText(id))
            if 'Offset' not in Pattern[0]:     #plot offset data
                Ymax = max(Pattern[1][1])
                Pattern[0].update({'Offset':[0.0,0.0],'delOffset':0.02*Ymax,'refOffset':-0.1*Ymax,'refDelt':0.1*Ymax,})
            PlotList.append(Pattern)
            ParmList.append(G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,
                id,'Instrument Parameters'))[0])
            SampleList.append(G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,
                id, 'Sample Parameters')))
    lenX = 0
    Ymax = None
    for Pattern in PlotList:
        xye = Pattern[1]
        if xye[1] is None: continue
        if Ymax is None: Ymax = max(xye[1])
        Ymax = max(Ymax,max(xye[1]))
    if Ymax is None: return # nothing to plot
    offsetX = Pattern[0]['Offset'][1]
    offsetY = Pattern[0]['Offset'][0]
    if G2frame.logPlot:
        Title = 'log('+Title+')'
    Plot.set_title(Title)
    if G2frame.plotStyle['qPlot'] or 'SASD' in plottype and not G2frame.Contour:
        Plot.set_xlabel(r'$Q, \AA^{-1}$',fontsize=16)
    elif G2frame.plotStyle['dPlot'] and 'PWDR' in plottype and not G2frame.Contour:
        Plot.set_xlabel(r'$d, \AA$',fontsize=16)
    else:
        if 'C' in ParmList[0]['Type'][0]:        
            Plot.set_xlabel(r'$\mathsf{2\theta}$',fontsize=16)
        else:
            if G2frame.Contour:
                Plot.set_xlabel(r'Channel no.',fontsize=16)            
            else:
                Plot.set_xlabel(r'$TOF, \mathsf{\mu}$s',fontsize=16)            
    if G2frame.Weight:
        if 'PWDR' in plottype:
            Plot.set_ylabel(r'$\mathsf{I/\sigma(I)}$',fontsize=16)
        elif 'SASD' in plottype:
            Plot.set_ylabel(r'$\mathsf{\Delta(I)/\sigma(I)}$',fontsize=16)
    else:
        if 'C' in ParmList[0]['Type'][0]:
            if 'PWDR' in plottype:
                if G2frame.plotStyle['sqrtPlot']:
                    Plot.set_ylabel(r'$\sqrt{Intensity}$',fontsize=16)
                else:
                    Plot.set_ylabel(r'$Intensity$',fontsize=16)
            elif 'SASD' in plottype:
                if G2frame.sqPlot:
                    Plot.set_ylabel(r'$S(Q)=I*Q^{4}$',fontsize=16)
                else:
                    Plot.set_ylabel(r'$Intensity,\ cm^{-1}$',fontsize=16)
        else:
            if G2frame.plotStyle['sqrtPlot']:
                Plot.set_ylabel(r'$\sqrt{Normalized\ intensity}$',fontsize=16)
            else:
                Plot.set_ylabel(r'$Normalized\ intensity$',fontsize=16)
    if G2frame.Contour:
        ContourZ = []
        ContourY = []
        Nseq = 0
    for N,Pattern in enumerate(PlotList):
        Parms = ParmList[N]
        Sample = SampleList[N]
        ifpicked = False
        LimitId = 0
        if Pattern[1] is None: continue # skip over uncomputed simulations
        xye = ma.array(ma.getdata(Pattern[1]))
        if PickId:
            ifpicked = Pattern[2] == G2frame.PatternTree.GetItemText(PatternId)
            LimitId = G2gd.GetPatternTreeItemId(G2frame,G2frame.PatternId,'Limits')
            limits = G2frame.PatternTree.GetItemPyData(LimitId)
            excls = limits[2:]
            for excl in excls:
                xye[0] = ma.masked_inside(xye[0],excl[0],excl[1])
        if G2frame.plotStyle['qPlot'] and 'PWDR' in plottype:
            X = 2.*np.pi/G2lat.Pos2dsp(Parms,xye[0])
        elif G2frame.plotStyle['dPlot'] and 'PWDR' in plottype:
            X = G2lat.Pos2dsp(Parms,xye[0])
        else:
            X = xye[0]
        if not lenX:
            lenX = len(X)
        if 'PWDR' in plottype:
            if G2frame.plotStyle['sqrtPlot']:
                olderr = np.seterr(invalid='ignore') #get around sqrt(-ve) error
                Y = np.where(xye[1]>=0.,np.sqrt(xye[1]),-np.sqrt(-xye[1]))
                np.seterr(invalid=olderr['invalid'])
            else:
                Y = xye[1]+offsetY*N*Ymax/100.0
        elif 'SASD' in plottype:
            B = xye[5]
            if G2frame.sqPlot:
                Y = xye[1]*Sample['Scale'][0]*(1.05)**(offsetY*N)*X**4
            else:
                Y = xye[1]*Sample['Scale'][0]*(1.05)**(offsetY*N)
        if LimitId and ifpicked:
            limits = np.array(G2frame.PatternTree.GetItemPyData(LimitId))
            lims = limits[1]
            if G2frame.plotStyle['qPlot'] and 'PWDR' in plottype:
                lims = 2.*np.pi/G2lat.Pos2dsp(Parms,lims)
            elif G2frame.plotStyle['dPlot'] and 'PWDR' in plottype:
                lims = G2lat.Pos2dsp(Parms,lims)
            Lines.append(Plot.axvline(lims[0],color='g',dashes=(5,5),picker=3.))    
            Lines.append(Plot.axvline(lims[1],color='r',dashes=(5,5),picker=3.))
            for i,item in enumerate(limits[2:]):
                Lines.append(Plot.axvline(item[0],color='m',dashes=(5,5),picker=3.))    
                Lines.append(Plot.axvline(item[1],color='m',dashes=(5,5),picker=3.))
                exclLines += [2*i+2,2*i+3]
        if G2frame.Contour:            
            if lenX == len(X):
                ContourY.append(N)
                ContourZ.append(Y)
                if 'C' in ParmList[0]['Type'][0]:        
                    ContourX = X
                else: #'T'OF
                    ContourX = range(lenX)
                Nseq += 1
                Plot.set_ylabel('Data sequence',fontsize=12)
        else:
            if G2frame.plusPlot:
                pP = '+'
            else:
                pP = ''
            if 'SASD' in plottype and G2frame.logPlot:
                X *= (1.01)**(offsetX*N)
            else:
                xlim = Plot.get_xlim()
                DX = xlim[1]-xlim[0]
                X += 0.002*offsetX*DX*N
            Xum = ma.getdata(X)
            if ifpicked:
                if G2frame.plotStyle['sqrtPlot']:
                    olderr = np.seterr(invalid='ignore') #get around sqrt(-ve) error
                    Z = np.where(xye[3]>=0.,np.sqrt(xye[3]),-np.sqrt(-xye[3]))
                    np.seterr(invalid=olderr['invalid'])
                else:
                    Z = xye[3]+offsetY*N*Ymax/100.0
                if 'PWDR' in plottype:
                    if G2frame.plotStyle['sqrtPlot']:
                        olderr = np.seterr(invalid='ignore') #get around sqrt(-ve) error
                        W = np.where(xye[4]>=0.,np.sqrt(xye[4]),-np.sqrt(-xye[4]))
                        np.seterr(invalid=olderr['invalid'])
                        D = np.where(xye[5],(Y-Z),0.)-Pattern[0]['delOffset']
                    else:
                        W = xye[4]+offsetY*N*Ymax/100.0
                        D = xye[5]-Pattern[0]['delOffset']  #powder background
                elif 'SASD' in plottype:
                    if G2frame.sqPlot:
                        W = xye[4]*X**4
                        Z = xye[3]*X**4
                        B = B*X**4
                    else:
                        W = xye[4]
                    if G2frame.SubBack:
                        YB = Y-B
                        ZB = Z
                    else:
                        YB = Y
                        ZB = Z+B
                    Plot.set_yscale("log",nonposy='mask')
                    if np.any(W>0.):
                        Plot.set_ylim(bottom=np.min(np.trim_zeros(W))/2.,top=np.max(Y)*2.)
                    else:
                        Plot.set_ylim(bottom=np.min(np.trim_zeros(YB))/2.,top=np.max(Y)*2.)
                if G2frame.logPlot:
                    if 'PWDR' in plottype:
                        Plot.set_yscale("log",nonposy='mask')
                        Plot.plot(X,Y,colors[N%6]+pP,picker=3.,clip_on=Clip_on)
                        Plot.plot(X,Z,colors[(N+1)%6],picker=False)
                        Plot.plot(X,W,colors[(N+2)%6],picker=False)     #background
                    elif 'SASD' in plottype:
                        Plot.set_xscale("log",nonposx='mask')
                        Ibeg = np.searchsorted(X,limits[1][0])
                        Ifin = np.searchsorted(X,limits[1][1])
                        if G2frame.Weight:
                            Plot.set_yscale("linear")
                            DS = (YB-ZB)*np.sqrt(xye[2])
                            Plot.plot(X[Ibeg:Ifin],DS[Ibeg:Ifin],colors[(N+3)%6],picker=False)
                            Plot.axhline(0.,color=wx.BLACK)
                            Plot.set_ylim(bottom=np.min(DS[Ibeg:Ifin])*1.2,top=np.max(DS[Ibeg:Ifin])*1.2)                                                    
                        else:
                            Plot.set_yscale("log",nonposy='mask')
                            if G2frame.ErrorBars:
                                if G2frame.sqPlot:
                                    Plot.errorbar(X,YB,yerr=X**4*Sample['Scale'][0]*np.sqrt(1./(Pattern[0]['wtFactor']*xye[2])),
                                        ecolor=colors[N%6],picker=3.,clip_on=Clip_on)
                                else:
                                    Plot.errorbar(X,YB,yerr=Sample['Scale'][0]*np.sqrt(1./(Pattern[0]['wtFactor']*xye[2])),
                                        ecolor=colors[N%6],picker=3.,clip_on=Clip_on)
                            else:
                                Plot.plot(X,YB,colors[N%6]+pP,picker=3.,clip_on=Clip_on)
                            Plot.plot(X,W,colors[(N+2)%6],picker=False)     #const. background
                            Plot.plot(X,ZB,colors[(N+1)%6],picker=False)
                elif G2frame.Weight and 'PWDR' in plottype:
                    DY = xye[1]*np.sqrt(xye[2])
                    Ymax = max(DY)
                    DZ = xye[3]*np.sqrt(xye[2])
                    DS = xye[5]*np.sqrt(xye[2])-Ymax*Pattern[0]['delOffset']
                    ObsLine = Plot.plot(X,DY,colors[N%6]+pP,picker=3.,clip_on=Clip_on)         #Io/sig(Io)
                    Plot.plot(X,DZ,colors[(N+1)%6],picker=False)                    #Ic/sig(Io)
                    DifLine = Plot.plot(X,DS,colors[(N+3)%6],picker=1.)                    #(Io-Ic)/sig(Io)
                    Plot.axhline(0.,color=wx.BLACK)
                else:
                    if G2frame.SubBack:
                        if 'PWDR' in plottype:
                            Plot.plot(Xum,Y-W,colors[N%6]+pP,picker=False,clip_on=Clip_on)  #Io-Ib
                            Plot.plot(X,Z-W,colors[(N+1)%6],picker=False)               #Ic-Ib
                        else:
                            Plot.plot(X,YB,colors[N%6]+pP,picker=3.,clip_on=Clip_on)
                            Plot.plot(X,ZB,colors[(N+1)%6],picker=False)
                    else:
                        if 'PWDR' in plottype:
                            ObsLine = Plot.plot(Xum,Y,colors[N%6]+pP,picker=3.,clip_on=Clip_on)    #Io
                            Plot.plot(X,Z,colors[(N+1)%6],picker=False)                 #Ic
                        else:
                            Plot.plot(X,YB,colors[N%6]+pP,picker=3.,clip_on=Clip_on)
                            Plot.plot(X,ZB,colors[(N+1)%6],picker=False)
                    if 'PWDR' in plottype:
                        Plot.plot(X,W,colors[(N+2)%6],picker=False)                 #Ib
                        DifLine = Plot.plot(X,D,colors[(N+3)%6],picker=1.)                 #Io-Ic
                    Plot.axhline(0.,color=wx.BLACK)
                Page.canvas.SetToolTipString('')
                if PickId:
                    if G2frame.PatternTree.GetItemText(PickId) == 'Peak List':
                        tip = 'On data point: Pick peak - L or R MB. On line: L-move, R-delete'
                        Page.canvas.SetToolTipString(tip)
                        data = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,PatternId, 'Peak List'))
                        selectedPeaks = list(set(
                            [row for row,col in G2frame.dataDisplay.GetSelectedCells()] +
                            G2frame.dataDisplay.GetSelectedRows()))
                        G2frame.dataFrame.movePeak.Enable(len(selectedPeaks) == 1) # allow peak move from table when one peak is selected
                        for i,item in enumerate(data['peaks']):
                            if i in selectedPeaks:
                                Ni = N+1
                            else:
                                Ni = N
                            if G2frame.plotStyle['qPlot']:
                                Lines.append(Plot.axvline(2.*np.pi/G2lat.Pos2dsp(Parms,item[0]),color=colors[Ni%6],picker=2.))
                            elif G2frame.plotStyle['dPlot']:
                                Lines.append(Plot.axvline(G2lat.Pos2dsp(Parms,item[0]),color=colors[Ni%6],picker=2.))
                            else:
                                Lines.append(Plot.axvline(item[0],color=colors[Ni%6],picker=2.))
                    if G2frame.PatternTree.GetItemText(PickId) == 'Limits':
                        tip = 'On data point: Lower limit - L MB; Upper limit - R MB. On limit: MB down to move'
                        Page.canvas.SetToolTipString(tip)
                        data = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,PatternId, 'Limits'))
                        
            else:   #not picked
                if G2frame.logPlot:
                    if 'PWDR' in plottype:
                        Plot.semilogy(X,Y,colors[N%6],picker=False,nonposy='mask')
                    elif 'SASD' in plottype:
                        Plot.semilogy(X,Y,colors[N%6],picker=False,nonposy='mask')
                else:
                    if 'PWDR' in plottype:
                        Plot.plot(X,Y,colors[N%6],picker=False)
                    elif 'SASD' in plottype:
                        Plot.loglog(X,Y,colors[N%6],picker=False,nonposy='mask')
                        Plot.set_ylim(bottom=np.min(np.trim_zeros(Y))/2.,top=np.max(Y)*2.)
                            
                if G2frame.logPlot and 'PWDR' in plottype:
                    Plot.set_ylim(bottom=np.min(np.trim_zeros(Y))/2.,top=np.max(Y)*2.)
    if PickId and not G2frame.Contour:
        Parms,Parms2 = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,PatternId, 'Instrument Parameters'))
        if G2frame.PatternTree.GetItemText(PickId) in ['Index Peak List','Unit Cells List']:
            peaks = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,PatternId, 'Index Peak List'))
            if not len(peaks): return # are there any peaks?
            for peak in peaks[0]:
                if peak[2]:
                    if G2frame.plotStyle['qPlot']:
                        Plot.axvline(2.*np.pi/G2lat.Pos2dsp(Parms,peak[0]),color='b')
                    if G2frame.plotStyle['dPlot']:
                        Plot.axvline(G2lat.Pos2dsp(Parms,peak[0]),color='b')
                    else:
                        Plot.axvline(peak[0],color='b')
            for hkl in G2frame.HKL:
                clr = 'r'
                if len(hkl) > 6 and hkl[3]:
                    clr = 'g'
                if G2frame.plotStyle['qPlot']:
                    Plot.axvline(2.*np.pi/G2lat.Pos2dsp(Parms,hkl[-2]),color=clr,dashes=(5,5))
                if G2frame.plotStyle['dPlot']:
                    Plot.axvline(G2lat.Pos2dsp(Parms,hkl[-2]),color=clr,dashes=(5,5))
                else:
                    Plot.axvline(hkl[-2],color=clr,dashes=(5,5))
        elif G2frame.PatternTree.GetItemText(PickId) in ['Reflection Lists'] or \
            'PWDR' in G2frame.PatternTree.GetItemText(PickId):
            refColors=['b','r','c','g','m','k']
            Phases = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,PatternId,'Reflection Lists'))
            for pId,phase in enumerate(Page.phaseList):
                if 'list' in str(type(Phases[phase])):
                    continue
                peaks = Phases[phase].get('RefList',[])
                if not len(peaks):
                    continue
                if Phases[phase].get('Super',False):
                    peak = np.array([[peak[5],peak[6]] for peak in peaks])
                else:
                    peak = np.array([[peak[4],peak[5]] for peak in peaks])
                pos = Pattern[0]['refOffset']-pId*Pattern[0]['refDelt']*np.ones_like(peak)
                if G2frame.plotStyle['qPlot']:
                    Page.tickDict[phase],j = Plot.plot(2*np.pi/peak.T[0],pos,refColors[pId%6]+'|',mew=1,ms=8,picker=3.,label=phase)
                elif G2frame.plotStyle['dPlot']:
                    Page.tickDict[phase],j = Plot.plot(peak.T[0],pos,refColors[pId%6]+'|',mew=1,ms=8,picker=3.,label=phase)
                else:
                    Page.tickDict[phase],j = Plot.plot(peak.T[1],pos,refColors[pId%6]+'|',mew=1,ms=8,picker=3.,label=phase)
            if len(Phases):
                handles,legends = Plot.get_legend_handles_labels()  #got double entries in the legends for some reason
                if handles:
                    Plot.legend(handles[::2],legends[::2],title='Phases',loc='best')    #skip every other one
            
    if G2frame.Contour:
        acolor = mpl.cm.get_cmap(G2frame.ContourColor)
        Img = Plot.imshow(ContourZ,cmap=acolor,vmin=0,vmax=Ymax*G2frame.Cmax,interpolation=G2frame.Interpolate, 
            extent=[ContourX[0],ContourX[-1],ContourY[0],ContourY[-1]],aspect='auto',origin='lower')
        Page.figure.colorbar(Img)
    else:
        G2frame.Lines = Lines
    if PickId and G2frame.PatternTree.GetItemText(PickId) == 'Background':
        # plot fixed background points
        backDict = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,G2frame.PatternId, 'Background'))[1]
        try:
            Parms,Parms2 = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,G2frame.PatternId, 'Instrument Parameters'))
        except TypeError:
            Parms = None
        for x,y in backDict.get('FixedPoints',[]):
            # "normal" intensity modes only!
            if G2frame.SubBack or G2frame.Weight or G2frame.Contour or not G2frame.SinglePlot:
                break
            if y < 0 and (G2frame.plotStyle['sqrtPlot'] or G2frame.logPlot):
                y = Page.figure.gca().get_ylim()[0] # put out of range point at bottom of plot
            elif G2frame.plotStyle['sqrtPlot']:
                y = math.sqrt(y)
            if G2frame.plotStyle['qPlot']:     #Q - convert from 2-theta
                if Parms:
                    x = 2*np.pi/G2lat.Pos2dsp(Parms,x)
                else:
                    break
            elif G2frame.plotStyle['dPlot']:   #d - convert from 2-theta
                if Parms:
                    x = G2lat.Dsp2pos(Parms,x)
                else:
                    break
            Plot.plot(x,y,'rD',clip_on=Clip_on,picker=3.)
    if not newPlot:
        # this restores previous plot limits (but I'm not sure why there are two .push_current calls)
        Page.toolbar.push_current()
        if G2frame.Contour: # for contour plots expand y-axis to include all histograms
            G2frame.xylim = (G2frame.xylim[0], (0.,len(PlotList)-1.))
        Plot.set_xlim(G2frame.xylim[0])
        Plot.set_ylim(G2frame.xylim[1])
#        xylim = []
        Page.toolbar.push_current()
        Page.toolbar.draw()
    else:
        G2frame.xylim = Plot.get_xlim(),Plot.get_ylim()
        Page.canvas.draw()
    olderr = np.seterr(invalid='ignore') #ugh - this removes a matplotlib error for mouse clicks in log plots
    # and sqrt(-ve) in np.where usage               
#    G2frame.Pwdr = True
    if 'PWDR' in G2frame.PatternTree.GetItemText(G2frame.PickId):
        if len(Page.tickDict.keys()) == 1:
            G2frame.dataFrame.moveTickLoc.Enable(True)
        elif len(Page.tickDict.keys()) > 1:
            G2frame.dataFrame.moveTickLoc.Enable(True)
            G2frame.dataFrame.moveTickSpc.Enable(True)
        if DifLine[0]:
            G2frame.dataFrame.moveDiffCurve.Enable(True)
    
################################################################################
##### PlotDeltSig
################################################################################
            
def PlotDeltSig(G2frame,kind,PatternName=None):
    'Produces normal probability plot for a powder or single crystal histogram'
    if PatternName:
        G2frame.PatternId = G2gd.GetPatternTreeItemId(G2frame, G2frame.root, PatternName)
    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('Error analysis','mpl')
    if new:
        G2frame.Cmax = 1.0
    # save information needed to reload from tree and redraw
    G2frame.G2plotNB.RegisterRedrawRoutine(G2frame.G2plotNB.lastRaisedPlotTab,
                                           PlotDeltSig,(
                                               G2frame,kind,
                                               G2frame.PatternTree.GetItemText(G2frame.PatternId))
                                           )
    Page.Choice = None
    PatternId = G2frame.PatternId
    Pattern = G2frame.PatternTree.GetItemPyData(PatternId)
    Pattern.append(G2frame.PatternTree.GetItemText(PatternId))
    wtFactor = Pattern[0]['wtFactor']
    if kind == 'PWDR':
        limits = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,PatternId, 'Limits'))[1]
        xye = np.array(Pattern[1])
        xmin = np.searchsorted(xye[0],limits[0])
        xmax = np.searchsorted(xye[0],limits[1])
        DS = xye[5][xmin:xmax]*np.sqrt(wtFactor*xye[2][xmin:xmax])
    elif kind == 'HKLF':
        refl = Pattern[1]['RefList']
        im = 0
        if Pattern[1]['Super']:
            im = 1
        DS = []
        for ref in refl:
            if ref[6+im] > 0.:
                DS.append((ref[5+im]-ref[7+im])/ref[6+im])
    G2frame.G2plotNB.status.DestroyChildren()
    DS.sort()
    EDS = np.zeros_like(DS)
    DX = np.linspace(0.,1.,num=len(DS),endpoint=True)
    np.seterr(invalid='ignore')    #avoid problem at DX==0
    T = np.sqrt(np.log(1.0/DX**2))
    top = 2.515517+0.802853*T+0.010328*T**2
    bot = 1.0+1.432788*T+0.189269*T**2+0.001308*T**3
    EDS = np.where(DX>0,-(T-top/bot),(T-top/bot))
    low1 = np.searchsorted(EDS,-1.)
    hi1 = np.searchsorted(EDS,1.)
    slp,intcp = np.polyfit(EDS[low1:hi1],DS[low1:hi1],deg=1)
    frac = 100.*(hi1-low1)/len(DS)
    G2frame.G2plotNB.status.SetStatusText(  \
        'Over range -1. to 1. :'+' slope = %.3f, intercept = %.3f for %.2f%% of the fitted data'%(slp,intcp,frac),1)
    Plot.set_title('Normal probability for '+Pattern[-1])
    Plot.set_xlabel(r'expected $\mathsf{\Delta/\sigma}$',fontsize=14)
    Plot.set_ylabel(r'observed $\mathsf{\Delta/\sigma}$',fontsize=14)
    Plot.plot(EDS,DS,'r+',label='result')
    Plot.plot([-2,2],[-2,2],'k',dashes=(5,5),label='ideal')
    Plot.legend(loc='upper left')
    np.seterr(invalid='warn')
    Page.canvas.draw()
       
################################################################################
##### PlotISFG
################################################################################
            
def PlotISFG(G2frame,newPlot=False,plotType=''):
    ''' Plotting package for PDF analysis; displays I(Q), S(Q), F(Q) and G(r) as single 
    or multiple plots with waterfall and contour plots as options
    '''
    if not plotType:
        plotType = G2frame.G2plotNB.plotList[G2frame.G2plotNB.nb.GetSelection()]
    if plotType not in ['I(Q)','S(Q)','F(Q)','G(R)']:
        return
    superMinusOne = unichr(0xaf)+unichr(0xb9)
    
    def OnPlotKeyPress(event):
        newPlot = False
        if event.key == 'u':
            if G2frame.Contour:
                G2frame.Cmax = min(1.0,G2frame.Cmax*1.2)
            elif Page.Offset[1] < 100.:
               Page.Offset[1] += 1.
        elif event.key == 'd':
            if G2frame.Contour:
                G2frame.Cmax = max(0.0,G2frame.Cmax*0.8)
            elif Page.Offset[1] > 0.:
                Page.Offset[1] -= 1.
        elif event.key == 'l':
            Page.Offset[0] -= 1.
        elif event.key == 'r':
            Page.Offset[0] += 1.
        elif event.key == 'o':
            Page.Offset = [0,0]
        elif event.key == 'm':
            G2frame.SinglePlot = not G2frame.SinglePlot
        elif event.key == 'c':
            newPlot = True
            G2frame.Contour = not G2frame.Contour
            if G2frame.Contour:
                G2frame.SinglePlot = False
                Page.Offset = [0.,0.]
        elif event.key == 'f' and not G2frame.SinglePlot:
            choices = G2gd.GetPatternTreeDataNames(G2frame,'PDF ')
            dlg = G2G.G2MultiChoiceDialog(G2frame.dataFrame,'Select dataset to plot', 
                'Multidata plot selection',choices)
            if dlg.ShowModal() == wx.ID_OK:
                G2frame.PDFselections = []
                select = dlg.GetSelections()
                if select:
                    for id in select:
                        G2frame.PDFselections.append(choices[id])
                else:
                    G2frame.PDFselections = None
            dlg.Destroy()
            newPlot = True
        elif event.key == 's':
            if G2frame.Contour:
                choice = [m for m in mpl.cm.datad.keys() if not m.endswith("_r")]
                choice.sort()
                dlg = wx.SingleChoiceDialog(G2frame,'Select','Color scheme',choice)
                if dlg.ShowModal() == wx.ID_OK:
                    sel = dlg.GetSelection()
                    G2frame.ContourColor = choice[sel]
                else:
                    G2frame.ContourColor = 'Paired'
                dlg.Destroy()
            else:
                G2frame.SinglePlot = not G2frame.SinglePlot                
        elif event.key == 'i':                  #for smoothing contour plot
            choice = ['nearest','bilinear','bicubic','spline16','spline36','hanning',
               'hamming','hermite','kaiser','quadric','catrom','gaussian','bessel',
               'mitchell','sinc','lanczos']
            dlg = wx.SingleChoiceDialog(G2frame,'Select','Interpolation',choice)
            if dlg.ShowModal() == wx.ID_OK:
                sel = dlg.GetSelection()
                G2frame.Interpolate = choice[sel]
            else:
                G2frame.Interpolate = 'nearest'
            dlg.Destroy()
        elif event.key == 't' and not G2frame.Contour:
            G2frame.Legend = not G2frame.Legend
        PlotISFG(G2frame,newPlot=newPlot,plotType=plotType)
        
    def OnMotion(event):
        xpos = event.xdata
        if xpos:                                        #avoid out of frame mouse position
            ypos = event.ydata
            Page.canvas.SetCursor(wx.CROSS_CURSOR)
            try:
                if G2frame.Contour:
                    G2frame.G2plotNB.status.SetStatusText('R =%.3fA pattern ID =%5d'%(xpos,int(ypos)),1)
                else:
                    G2frame.G2plotNB.status.SetStatusText('R =%.3fA %s =%.2f'%(xpos,plotType,ypos),1)                   
            except TypeError:
                G2frame.G2plotNB.status.SetStatusText('Select '+plotType+' pattern first',1)
    
    xylim = []
    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab(plotType,'mpl')
    if not new:
        if not newPlot:
            xylim = lim
    else:
        newPlot = True
        G2frame.Cmax = 1.0
        Page.canvas.mpl_connect('key_press_event', OnPlotKeyPress)
        Page.canvas.mpl_connect('motion_notify_event', OnMotion)
        Page.Offset = [0,0]
    
    G2frame.G2plotNB.status.DestroyChildren()
    if G2frame.Contour:
        Page.Choice = (' key press','d: lower contour max','u: raise contour max',
            'i: interpolation method','s: color scheme','c: contour off','f: select data')
    else:
        Page.Choice = (' key press','l: offset left','r: offset right','d: offset down','u: offset up',
            'o: reset offset','t: toggle legend','c: contour on',
            'm: toggle multiplot','s: toggle single plot','f: select data' )
    Page.keyPress = OnPlotKeyPress
    PatternId = G2frame.PatternId
    if plotType == 'G(R)':
        Plot.set_xlabel(r'r,$\AA$',fontsize=14)
        Plot.set_ylabel(r'G(r), $\AA^{-2}$',fontsize=14)
        Plot.set_title('G(r)')
    else:
        Plot.set_xlabel(r'$Q,\AA^{-1}$'+superMinusOne,fontsize=14)
        Plot.set_ylabel(r''+plotType,fontsize=14)
        Plot.set_title(plotType)
    colors=['b','g','r','c','m','k']
    name = G2frame.PatternTree.GetItemText(PatternId)[4:]
    Pattern = []    
    if G2frame.SinglePlot:
        name = G2frame.PatternTree.GetItemText(PatternId)
        name = plotType+name[4:]
        Id = G2gd.GetPatternTreeItemId(G2frame,PatternId,name)
        Pattern = G2frame.PatternTree.GetItemPyData(Id)
        if Pattern:
            Pattern.append(name)
        PlotList = [Pattern,]
    else:
        PlotList = []
        if G2frame.PDFselections is None:
            choices = G2gd.GetPatternTreeDataNames(G2frame,'PDF ')
        else:
            choices = G2frame.PDFselections
        for item in choices:
            Pid = G2gd.GetPatternTreeItemId(G2frame,G2frame.root,item)
            name = plotType+item[4:]
            Id = G2gd.GetPatternTreeItemId(G2frame,Pid,name)
            Pattern = G2frame.PatternTree.GetItemPyData(Id)
            if Pattern:
                Pattern.append(item)
                PlotList.append(Pattern)
    PDFdata = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,PatternId, 'PDF Controls'))
    numbDen = G2pwd.GetNumDensity(PDFdata['ElList'],PDFdata['Form Vol'])
    Ymax = 0.01
    lenX = 0
    for Pattern in PlotList:
        try:
            xye = Pattern[1]
        except IndexError:
            return
        Ymax = max(Ymax,max(xye[1]))
    if G2frame.Contour:
        ContourZ = []
        ContourY = []
        Nseq = 0
    for N,Pattern in enumerate(PlotList):
        xye = Pattern[1]
        X = xye[0]
        if not lenX:
            lenX = len(X)           
        if G2frame.Contour and len(Pattern)>1:
            Y = xye[1]
            if lenX == len(X):
                ContourY.append(N)
                ContourZ.append(Y)
                ContourX = X
                Nseq += 1
                Plot.set_ylabel('Data sequence',fontsize=12)
        else:
            X = xye[0]+Page.Offset[0]*.005*N
            Y = xye[1]+Page.Offset[1]*.01*N
            if G2frame.Legend:
                Plot.plot(X,Y,colors[N%6],picker=False,label='Azm:'+Pattern[2].split('=')[1])
            else:
                Plot.plot(X,Y,colors[N%6],picker=False)
            if plotType == 'G(R)':
                Xb = [0.,2.5]
                Yb = [0.,-10.*np.pi*numbDen]
                Plot.plot(Xb,Yb,color='k',dashes=(5,5))
            elif plotType == 'F(Q)':
                Plot.axhline(0.,color=wx.BLACK)
            elif plotType == 'S(Q)':
                Plot.axhline(1.,color=wx.BLACK)
    if G2frame.Contour and len(Pattern)>1:
        acolor = mpl.cm.get_cmap(G2frame.ContourColor)
        Img = Plot.imshow(ContourZ,cmap=acolor,vmin=0,vmax=Ymax*G2frame.Cmax,interpolation=G2frame.Interpolate, 
            extent=[ContourX[0],ContourX[-1],ContourY[0],ContourY[-1]],aspect='auto',origin='lower')
        Page.figure.colorbar(Img)
    elif G2frame.Legend:
        Plot.legend(loc='best')
    if not newPlot:
        Page.toolbar.push_current()
        Plot.set_xlim(xylim[0])
        Plot.set_ylim(xylim[1])
        xylim = []
        Page.toolbar.push_current()
        Page.toolbar.draw()
    else:
        Page.canvas.draw()
        
################################################################################
##### PlotCalib
################################################################################
            
def PlotCalib(G2frame,Inst,XY,Sigs,newPlot=False):
    '''plot of CW or TOF peak calibration
    '''
    def OnMotion(event):
        xpos = event.xdata
        if xpos:                                        #avoid out of frame mouse position
            ypos = event.ydata
            Page.canvas.SetCursor(wx.CROSS_CURSOR)
            try:
                G2frame.G2plotNB.status.SetStatusText('X =%9.3f %s =%9.3g'%(xpos,Title,ypos),1)                   
            except TypeError:
                G2frame.G2plotNB.status.SetStatusText('Select '+Title+' pattern first',1)
            found = []
            wid = 1
            view = Page.toolbar._views.forward()
            if view:
                view = view[0][:2]
                wid = view[1]-view[0]
            found = XY[np.where(np.fabs(XY.T[0]-xpos) < 0.005*wid)]
            if len(found):
                pos = found[0][1]
                if 'C' in Inst['Type'][0]: 
                    Page.canvas.SetToolTipString('position=%.4f'%(pos))
                else:
                    Page.canvas.SetToolTipString('position=%.2f'%(pos))
            else:
                Page.canvas.SetToolTipString('')

    xylim = []
    Title = 'Position calibration'
    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab(Title,'mpl')
    if not new:
        if not newPlot:
            xylim = lim
    else:
        newPlot = True
        Page.canvas.mpl_connect('motion_notify_event', OnMotion)
    
    Page.Choice = None
    G2frame.G2plotNB.status.DestroyChildren()
    Plot.set_title(Title)
    Plot.set_xlabel(r'd-spacing',fontsize=14)
    if 'C' in Inst['Type'][0]:
        Plot.set_ylabel(r'$\mathsf{\Delta(2\theta)}$',fontsize=14)
    else:
        Plot.set_ylabel(r'$\mathsf{\Delta}T/T$',fontsize=14)
    for ixy,xyw in enumerate(XY):
        if len(xyw) > 2:
            X,Y,W = xyw
        else:
            X,Y = xyw
            W = 0.
        Yc = G2lat.Dsp2pos(Inst,X)
        if 'C' in Inst['Type'][0]:
            Y = Y-Yc
            E = Sigs[ixy]
            bin = W/2.
        else:
            Y = (Y-Yc)/Yc
            E = Sigs[ixy]/Yc
            bin = W/(2.*Yc)
        if E:
            Plot.errorbar(X,Y,ecolor='k',yerr=E)
        if ixy:
            Plot.plot(X,Y,'kx',picker=3)
        else:
            Plot.plot(X,Y,'kx',label='peak')
        if W:
            if ixy:
                Plot.plot(X,bin,'b+')
            else:
                Plot.plot(X,bin,'b+',label='bin width')
            Plot.plot(X,-bin,'b+')
        Plot.axhline(0.,color='r',linestyle='--')
    Plot.legend(loc='best')
    if not newPlot:
        Page.toolbar.push_current()
        Plot.set_xlim(xylim[0])
        Plot.set_ylim(xylim[1])
#        xylim = []
        Page.toolbar.push_current()
        Page.toolbar.draw()
    else:
        Page.canvas.draw()

################################################################################
##### PlotXY
################################################################################
            
def PlotXY(G2frame,XY,XY2=None,labelX='X',labelY='Y',newPlot=False,
    Title='',lines=False,names=[],names2=[]):
    '''simple plot of xy data
    
    :param wx.Frame G2frame: The main GSAS-II tree "window"
    :param list XY: a list of X,Y array pairs; len(X) = len(Y)
    :param list XY2: a secondary list of X,Y pairs
    :param str labelX: label for X-axis
    :param str labelY: label for Y-axis
    :param bool newPlot: =True if new plot is to be made
    :param str Title: title for plot
    :param bool lines: = True if lines desired for XY plot; XY2 always plotted as lines
    :param list of str names: legend names for each XY plot
    :param list of str names2: legend names for each XY2 plot
    :return nothing
    
    '''
    def OnKeyPress(event):
        if event.key == 'u':
            if Page.Offset[1] < 100.:
                Page.Offset[1] += 1.
        elif event.key == 'd':
            if Page.Offset[1] > 0.:
                Page.Offset[1] -= 1.
        elif event.key == 'l':
            Page.Offset[0] -= 1.
        elif event.key == 'r':
            Page.Offset[0] += 1.
        elif event.key == 'o':
            Page.Offset = [0,0]
        elif event.key == 's':
            if len(XY):
                G2IO.XYsave(G2frame,XY,labelX,labelY,names)
            if XY2 != None:
                G2IO.XYsave(G2frame,XY2,labelX,labelY,names2)
        else:
#            print 'no binding for key',event.key
            #GSASIIpath.IPyBreak()
            return
        wx.CallAfter(PlotXY,G2frame,XY,XY2,labelX,labelY,False,Title,lines,names)

    def OnMotion(event):
        xpos = event.xdata
        if xpos:                                        #avoid out of frame mouse position
            ypos = event.ydata
            Page.canvas.SetCursor(wx.CROSS_CURSOR)
            try:
                G2frame.G2plotNB.status.SetStatusText('X =%9.3f %s =%9.3f'%(xpos,Title,ypos),1)                   
            except TypeError:
                G2frame.G2plotNB.status.SetStatusText('Select '+Title+' pattern first',1)

    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab(Title,'mpl')
    if not new:
        if not newPlot:
            xylim = lim
    else:
        newPlot = True
        Page.canvas.mpl_connect('key_press_event', OnKeyPress)
        Page.canvas.mpl_connect('motion_notify_event', OnMotion)
        Page.Offset = [0,0]
    
    if lines:
        Page.Choice = (' key press','l: offset left','r: offset right','d: offset down',
            'u: offset up','o: reset offset','s: save data as csv file')
    else:
        Page.Choice = None
    G2frame.G2plotNB.status.DestroyChildren()
    Plot.set_title(Title)
    Plot.set_xlabel(r''+labelX,fontsize=14)
    Plot.set_ylabel(r''+labelY,fontsize=14)
    colors=['b','g','r','c','m','k']
    Page.keyPress = OnKeyPress
    Xmax = 0.
    Ymax = 0.    
    for ixy,xy in enumerate(XY):
        X,Y = XY[ixy]
        Xmax = max(Xmax,max(X))
        Ymax = max(Ymax,max(Y))
        if lines:
            dX = Page.Offset[0]*(ixy+1)*Xmax/500.
            dY = Page.Offset[1]*(ixy+1)*Ymax/100.
            if len(names):
                Plot.plot(X+dX,Y+dY,colors[ixy%6],picker=False,label=names[ixy])
            else:
                Plot.plot(X+dX,Y+dY,colors[ixy%6],picker=False)
        else:
            Plot.plot(X,Y,colors[ixy%6]+'+',picker=False)
    if XY2 and len(XY2):
        for ixy,xy in enumerate(XY2):
            X,Y = XY2[ixy]
            dX = Page.Offset[0]*(ixy+1)*Xmax/500.
            dY = Page.Offset[1]*(ixy+1)*Ymax/100.
            if len(names2):
                Plot.plot(X+dX,Y+dY,colors[ixy%6],picker=False,label=names2[ixy])
            else:
                Plot.plot(X+dX,Y+dY,colors[ixy%6],picker=False)
    if len(names):
        Plot.legend(loc='best')
    if not newPlot:
        Page.toolbar.push_current()
        Plot.set_xlim(xylim[0])
        Plot.set_ylim(xylim[1])
        xylim = []
        Page.toolbar.push_current()
        Page.toolbar.draw()
    else:
        Page.canvas.draw()
        
################################################################################
##### PlotXYZ
################################################################################
            
def PlotXYZ(G2frame,XY,Z,labelX='X',labelY='Y',newPlot=False,Title=''):
    '''simple contour plot of xyz data
    
    :param wx.Frame G2frame: The main GSAS-II tree "window"
    :param list XY: a list of X,Y arrays
    :param list Z: a list of Z values for each X,Y pair
    :param str labelX: label for X-axis
    :param str labelY: label for Y-axis
    :param bool newPlot: =True if new plot is to be made
    :param str Title: title for plot
    :return nothing
    
    '''
    def OnKeyPress(event):
        if event.key == 'u':
            G2frame.Cmax = min(1.0,G2frame.Cmax*1.2) 
        elif event.key == 'd':
            G2frame.Cmax = max(0.0,G2frame.Cmax*0.8)
        elif event.key == 'o':
            G2frame.Cmax = 1.0
            
        elif event.key == 'i':
            choice = ['nearest','bilinear','bicubic','spline16','spline36','hanning',
               'hamming','hermite','kaiser','quadric','catrom','gaussian','bessel',
               'mitchell','sinc','lanczos']
            dlg = wx.SingleChoiceDialog(G2frame,'Select','Interpolation',choice)
            if dlg.ShowModal() == wx.ID_OK:
                sel = dlg.GetSelection()
                G2frame.Interpolate = choice[sel]
            else:
                G2frame.Interpolate = 'nearest'
            dlg.Destroy()
            
        elif event.key == 's':
            choice = [m for m in mpl.cm.datad.keys() if not m.endswith("_r")]
            choice.sort()
            dlg = wx.SingleChoiceDialog(G2frame,'Select','Color scheme',choice)
            if dlg.ShowModal() == wx.ID_OK:
                sel = dlg.GetSelection()
                G2frame.ContourColor = choice[sel]
            else:
                G2frame.ContourColor = 'Paired'
            dlg.Destroy()
        wx.CallAfter(PlotXYZ,G2frame,XY,Z,labelX,labelY,False,Title)
    
    def OnMotion(event):
        xpos = event.xdata
        if Xmin<xpos<Xmax:                                        #avoid out of frame mouse position
            ypos = event.ydata
            if Ymin<ypos<Ymax:
                Xwd = Xmax-Xmin
                Ywd = Ymax-Ymin
                Page.canvas.SetCursor(wx.CROSS_CURSOR)
                ix = int(Nxy[0]*(xpos-Xmin)/Xwd)
                iy = int(Nxy[1]*(ypos-Ymin)/Ywd)
                try:
                    G2frame.G2plotNB.status.SetStatusText('%s =%9.3f %s =%9.3f val =%9.3f'% \
                        (labelX,xpos,labelY,ypos,Z[ix,iy]),1)                   
                except TypeError:
                    G2frame.G2plotNB.status.SetStatusText('Select '+Title+' pattern first',1)
                    
    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab(Title,'mpl')
    if not new:
        if not newPlot:
            xylim = lim
    else:
        newPlot = True
        Page.canvas.mpl_connect('motion_notify_event', OnMotion)
        Page.canvas.mpl_connect('key_press_event', OnKeyPress)
    
    Page.Choice = (' key press','d: lower contour max','u: raise contour max','o: reset contour max',
        'i: interpolation method','s: color scheme')
    Page.keyPress = OnKeyPress
    Page.SetFocus()
    G2frame.G2plotNB.status.DestroyChildren()
    Nxy = Z.shape
    Zmax = np.max(Z)
    Xmin = np.min(XY[0])
    Xmax = np.max(XY[0])
    Ymin = np.min(XY.T[0])
    Ymax = np.max(XY.T[0])
    Dx = 0.5*(Xmax-Xmin)/Nxy[0]
    Dy = 0.5*(Ymax-Ymin)/Nxy[1]
    Plot.set_title(Title)
    if labelX:
        Plot.set_xlabel(r''+labelX,fontsize=14)
    else:
        Plot.set_xlabel(r'X',fontsize=14)
    if labelY:
        Plot.set_ylabel(r''+labelY,fontsize=14)
    else:
        Plot.set_ylabel(r'Y',fontsize=14)
    acolor = mpl.cm.get_cmap(G2frame.ContourColor)
    Img = Plot.imshow(Z.T,cmap=acolor,interpolation=G2frame.Interpolate,origin='lower', \
        aspect='auto',extent=[Xmin-Dx,Xmax-Dx,Ymin+Dy,Ymax+Dy],vmin=0,vmax=Zmax*G2frame.Cmax)
    Page.figure.colorbar(Img)
    if not newPlot:
        Page.toolbar.push_current()
        Plot.set_xlim(xylim[0])
        Plot.set_ylim(xylim[1])
        xylim = []
        Page.toolbar.push_current()
        Page.toolbar.draw()
    else:
        Page.canvas.draw()

################################################################################
##### PlotStrain
################################################################################
            
def PlotStrain(G2frame,data,newPlot=False):
    '''plot of strain data, used for diagnostic purposes
    '''
    def OnMotion(event):
        xpos = event.xdata
        if xpos:                                        #avoid out of frame mouse position
            ypos = event.ydata
            Page.canvas.SetCursor(wx.CROSS_CURSOR)
            try:
                G2frame.G2plotNB.status.SetStatusText('d-spacing =%9.5f Azimuth =%9.3f'%(ypos,xpos),1)                   
            except TypeError:
                G2frame.G2plotNB.status.SetStatusText('Select Strain pattern first',1)

    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('Strain','mpl')
    if not new:
        if not newPlot:
            xylim = lim
    else:
        newPlot = True
        Page.canvas.mpl_connect('motion_notify_event', OnMotion)
    
    Page.Choice = None
    G2frame.G2plotNB.status.DestroyChildren()
    Plot.set_title('Strain')
    Plot.set_ylabel(r'd-spacing',fontsize=14)
    Plot.set_xlabel(r'Azimuth',fontsize=14)
    colors=['b','g','r','c','m','k']
    for N,item in enumerate(data['d-zero']):
        Y,X = np.array(item['ImtaObs'])         #plot azimuth as X & d-spacing as Y
        Plot.plot(X,Y,colors[N%6]+'+',picker=False)
        Y,X = np.array(item['ImtaCalc'])
        Plot.plot(X,Y,colors[N%6],picker=False)
        Plot.plot([0.,360.],[item['Dcalc'],item['Dcalc']],colors[5],dashes=(5,5))
    if not newPlot:
        Page.toolbar.push_current()
        Plot.set_xlim(xylim[0])
        Plot.set_ylim(xylim[1])
        xylim = []
        Page.toolbar.push_current()
        Page.toolbar.draw()
    else:
        Page.canvas.draw()
        
################################################################################
##### PlotSASDSizeDist
################################################################################
            
def PlotSASDSizeDist(G2frame):
    
    def OnPageChanged(event):
        PlotText = G2frame.G2plotNB.nb.GetPageText(G2frame.G2plotNB.nb.GetSelection())
        if 'Powder' in PlotText:
            PlotPatterns(G2frame,plotType='SASD',newPlot=True)
        elif 'Size' in PlotText:
            PlotSASDSizeDist(G2frame)
    
    def OnMotion(event):
        xpos = event.xdata
        if xpos:                                        #avoid out of frame mouse position
            ypos = event.ydata
            Page.canvas.SetCursor(wx.CROSS_CURSOR)
            try:
                G2frame.G2plotNB.status.SetStatusText('diameter =%9.3f f(D) =%9.3g'%(xpos,ypos),1)                   
            except TypeError:
                G2frame.G2plotNB.status.SetStatusText('Select Strain pattern first',1)

    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('Size Distribution','mpl')
    if new:
        G2frame.G2plotNB.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED,OnPageChanged)
        Page.canvas.mpl_connect('motion_notify_event', OnMotion)
    Page.Choice = None
    PatternId = G2frame.PatternId
    data = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,PatternId, 'Models'))
    Bins,Dbins,BinMag = data['Size']['Distribution']
    Plot.set_title('Size Distribution')
    Plot.set_xlabel(r'$D, \AA$',fontsize=14)
    Plot.set_ylabel(r'$Volume distribution f(D)$',fontsize=14)
    if data['Size']['logBins']:
        Plot.set_xscale("log",nonposy='mask')
        Plot.set_xlim([np.min(2.*Bins)/2.,np.max(2.*Bins)*2.])
    Plot.bar(2.*Bins-Dbins,BinMag,2.*Dbins,facecolor='white')       #plot diameters
    if 'Size Calc' in data:
        Rbins,Dist = data['Size Calc']
        for i in range(len(Rbins)):
            if len(Rbins[i]):
                Plot.plot(2.*Rbins[i],Dist[i])       #plot diameters
    Page.canvas.draw()

################################################################################
##### PlotPowderLines
################################################################################
            
def PlotPowderLines(G2frame):
    ''' plotting of powder lines (i.e. no powder pattern) as sticks
    '''

    def OnMotion(event):
        xpos = event.xdata
        if xpos:                                        #avoid out of frame mouse position
            Page.canvas.SetCursor(wx.CROSS_CURSOR)
            G2frame.G2plotNB.status.SetStatusText('2-theta =%9.3f '%(xpos,),1)
            if G2frame.PickId and G2frame.PatternTree.GetItemText(G2frame.PickId) in ['Index Peak List','Unit Cells List']:
                found = []
                if len(G2frame.HKL):
                    view = Page.toolbar._views.forward()[0][:2]
                    wid = view[1]-view[0]
                    found = G2frame.HKL[np.where(np.fabs(G2frame.HKL.T[-1]-xpos) < 0.002*wid)]
                if len(found):
                    h,k,l = found[0][:3] 
                    Page.canvas.SetToolTipString('%d,%d,%d'%(int(h),int(k),int(l)))
                else:
                    Page.canvas.SetToolTipString('')

    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('Powder Lines','mpl')
    if new:
        Page.canvas.mpl_connect('motion_notify_event', OnMotion)
    Page.Choice = None
    Plot.set_title('Powder Pattern Lines')
    Plot.set_xlabel(r'$\mathsf{2\theta}$',fontsize=14)
    PatternId = G2frame.PatternId
    peaks = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,PatternId, 'Index Peak List'))[0]
    for peak in peaks:
        Plot.axvline(peak[0],color='b')
    for hkl in G2frame.HKL:
        Plot.axvline(hkl[-2],color='r',dashes=(5,5))
    xmin = peaks[0][0]
    xmax = peaks[-1][0]
    delt = xmax-xmin
    xlim = [max(0,xmin-delt/20.),min(180.,xmax+delt/20.)]
    Plot.set_xlim(xlim)
    Page.canvas.draw()
    Page.toolbar.push_current()

################################################################################
##### PlotPeakWidths
################################################################################
            
def PlotPeakWidths(G2frame,PatternName=None):
    ''' Plotting of instrument broadening terms as function of 2-theta
    Seen when "Instrument Parameters" chosen from powder pattern data tree.
    Parameter PatternName allows the PWDR to be referenced as a string rather than
    a wx tree item, defined in G2frame.PatternId. 
    '''
#    sig = lambda Th,U,V,W: 1.17741*math.sqrt(U*tand(Th)**2+V*tand(Th)+W)*math.pi/18000.
#    gam = lambda Th,X,Y: (X/cosd(Th)+Y*tand(Th))*math.pi/18000.
#    gamFW = lambda s,g: np.exp(np.log(s**5+2.69269*s**4*g+2.42843*s**3*g**2+4.47163*s**2*g**3+0.07842*s*g**4+g**5)/5.)
#    gamFW2 = lambda s,g: math.sqrt(s**2+(0.4654996*g)**2)+.5345004*g  #Ubaldo Bafile - private communication
    if PatternName:
        G2frame.PatternId = G2gd.GetPatternTreeItemId(G2frame, G2frame.root, PatternName)
    PatternId = G2frame.PatternId
    limitID = G2gd.GetPatternTreeItemId(G2frame,PatternId, 'Limits')
    if limitID:
        limits = G2frame.PatternTree.GetItemPyData(limitID)[:2]
    else:
        return
    Parms,Parms2 = G2frame.PatternTree.GetItemPyData( \
        G2gd.GetPatternTreeItemId(G2frame,PatternId, 'Instrument Parameters'))
    if 'PKS' in Parms['Type'][0]:
        return
    elif 'T' in Parms['Type'][0]:
        difC = Parms['difC'][0]
    else:
        lam = G2mth.getWave(Parms)
    try:  # PATCH: deal with older peak lists, before changed to dict to implement TOF
        peaks = G2frame.PatternTree.GetItemPyData(G2gd.GetPatternTreeItemId(G2frame,PatternId, 'Peak List'))['peaks']
    except TypeError:
        print "Your peak list needs reformatting...",
        item = G2gd.GetPatternTreeItemId(G2frame,PatternId, 'Peak List')
        G2frame.PatternTree.SelectItem(item)  
        item = G2gd.GetPatternTreeItemId(G2frame,PatternId, 'Instrument Parameters')
        G2frame.PatternTree.SelectItem(item)
        print "done"
        return
    xylim = []
    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('Peak Widths','mpl')
    if not new:
        if not G2frame.G2plotNB.allowZoomReset: # save previous limits
            xylim = lim
    # save information needed to reload from tree and redraw
    G2frame.G2plotNB.RegisterRedrawRoutine(G2frame.G2plotNB.lastRaisedPlotTab,
            PlotPeakWidths,(G2frame,G2frame.PatternTree.GetItemText(G2frame.PatternId))
            )

    TreeItemText = G2frame.PatternTree.GetItemText(G2frame.PatternId)
    G2frame.G2plotNB.status.SetStatusText('histogram: '+TreeItemText,1)
    Page.Choice = None
    Page.canvas.SetToolTipString('')
    X = []
    Y = []
    Z = []
    W = []
    if 'C' in Parms['Type'][0]:
        Plot.set_title('Instrument and sample peak widths')
        Plot.set_xlabel(r'$Q, \AA^{-1}$',fontsize=14)
        Plot.set_ylabel(r'$\Delta Q/Q, \Delta d/d$',fontsize=14)
        Xmin,Xmax = limits[1]
        X = np.linspace(Xmin,Xmax,num=101,endpoint=True)
        Q = 4.*np.pi*npsind(X/2.)/lam
        Z = np.ones_like(X)
        data = G2mth.setPeakparms(Parms,Parms2,X,Z)
        s = np.sqrt(data[4])*np.pi/18000.   #var -> sig(radians)
        g = data[6]*np.pi/18000.    #centideg -> radians
        G = G2pwd.getgamFW(g,s)/2.  #delt-theta
        Y = s/nptand(X/2.)
        Z = g/nptand(X/2.)
        W = G/nptand(X/2.)
        Plot.plot(Q,Y,color='r',label='Gaussian')
        Plot.plot(Q,Z,color='g',label='Lorentzian')
        Plot.plot(Q,W,color='b',label='G+L')
        
        fit = G2mth.setPeakparms(Parms,Parms2,X,Z,useFit=True)
        sf = np.sqrt(fit[4])*np.pi/18000.
        gf = fit[6]*np.pi/18000.
        Gf = G2pwd.getgamFW(gf,sf)/2.
        Yf = sf/nptand(X/2.)
        Zf = gf/nptand(X/2.)
        Wf = Gf/nptand(X/2.)
        Plot.plot(Q,Yf,color='r',dashes=(5,5),label='Gaussian fit')
        Plot.plot(Q,Zf,color='g',dashes=(5,5),label='Lorentzian fit')
        Plot.plot(Q,Wf,color='b',dashes=(5,5),label='G+L fit')
        
        X = []
        Y = []
        Z = []
        W = []
        for peak in peaks:
            X.append(4.0*math.pi*sind(peak[0]/2.0)/lam)
            try:
                s = math.sqrt(peak[4])*math.pi/18000.
            except ValueError:
                s = 0.01
            g = peak[6]*math.pi/18000.
            G = G2pwd.getgamFW(g,s)/2.
            Y.append(s/tand(peak[0]/2.))
            Z.append(g/tand(peak[0]/2.))
            W.append(G/tand(peak[0]/2.))
        if len(peaks):
            Plot.plot(X,Y,'+',color='r',label='G peak')
            Plot.plot(X,Z,'+',color='g',label='L peak')
            Plot.plot(X,W,'+',color='b',label='G+L peak')
        Plot.legend(loc='best')
        Page.canvas.draw()
    else:   #'T'OF
        Plot.set_title('Instrument and sample peak coefficients')
        Plot.set_xlabel(r'$Q, \AA^{-1}$',fontsize=14)
        Plot.set_ylabel(r'$\alpha, \beta, \Delta Q/Q, \Delta d/d$',fontsize=14)
        Xmin,Xmax = limits[1]
        T = np.linspace(Xmin,Xmax,num=101,endpoint=True)
        Z = np.ones_like(T)
        data = G2mth.setPeakparms(Parms,Parms2,T,Z)
        ds = T/difC
        Q = 2.*np.pi/ds
        A = data[4]
        B = data[6]
        S = 1.17741*np.sqrt(data[8])/T
        G = data[10]/T
        Plot.plot(Q,A,color='r',label='Alpha')
        Plot.plot(Q,B,color='g',label='Beta')
        Plot.plot(Q,S,color='b',label='Gaussian')
        Plot.plot(Q,G,color='m',label='Lorentzian')

        fit = G2mth.setPeakparms(Parms,Parms2,T,Z)
        ds = T/difC
        Q = 2.*np.pi/ds
        Af = fit[4]
        Bf = fit[6]
        Sf = 1.17741*np.sqrt(fit[8])/T
        Gf = fit[10]/T
        Plot.plot(Q,Af,color='r',dashes=(5,5),label='Alpha fit')
        Plot.plot(Q,Bf,color='g',dashes=(5,5),label='Beta fit')
        Plot.plot(Q,Sf,color='b',dashes=(5,5),label='Gaussian fit')
        Plot.plot(Q,Gf,color='m',dashes=(5,5),label='Lorentzian fit')
        
        T = []
        A = []
        B = []
        S = []
        G = []
        W = []
        Q = []
        for peak in peaks:
            T.append(peak[0])
            A.append(peak[4])
            B.append(peak[6])
            Q.append(2.*np.pi*difC/peak[0])
            S.append(1.17741*np.sqrt(peak[8])/peak[0])
            G.append(peak[10]/peak[0])
            
        
        Plot.plot(Q,A,'+',color='r',label='Alpha peak')
        Plot.plot(Q,B,'+',color='g',label='Beta peak')
        Plot.plot(Q,S,'+',color='b',label='Gaussian peak')
        Plot.plot(Q,G,'+',color='m',label='Lorentzian peak')
        Plot.legend(loc='best')
    if xylim and not G2frame.G2plotNB.allowZoomReset:
        # this restores previous plot limits (but I'm not sure why there are two .push_current calls)
        Page.toolbar.push_current()
        Plot.set_xlim(xylim[0])
        Plot.set_ylim(xylim[1])
        Page.toolbar.push_current()
        Page.toolbar.draw()
    else:
        Page.canvas.draw()
    
################################################################################
##### PlotSizeStrainPO
################################################################################
            
def PlotSizeStrainPO(G2frame,data,hist='',Start=False):
    '''Plot 3D mustrain/size/preferred orientation figure. In this instance data is for a phase
    '''
    
    def OnPick(event):
        if plotType not in ['Inv. pole figure',]:
            return
        ind = event.ind[0]
        h,k,l = RefSets[ind]
        msg = '%d,%d,%d=%.2f'%(h,k,l,Rmd[ind])
        Page.canvas.SetToolTipString(msg)

    def rp2xyz(r,p):
        z = npcosd(r)
        xy = np.sqrt(1.-z**2)
        return xy*npcosd(p),xy*npsind(p),z
        
    def OnMotion(event):
        if plotType not in ['Inv. pole figure',]:
            return
        if event.xdata and event.ydata:                 #avoid out of frame errors
            xpos = event.xdata
            ypos = event.ydata
            r = xpos**2+ypos**2
            if r <= 1.0:
                if 'equal' in G2frame.Projection:
                    r,p = 2.*npasind(np.sqrt(r)*sq2),npatan2d(ypos,xpos)
                else:
                    r,p = 2.*npatand(np.sqrt(r)),npatan2d(ypos,xpos)
                if p<0.:
                    p += 360.
                ipf = lut(r*np.pi/180.,p*np.pi/180.)
                xyz = np.inner(Bmat.T,np.array([rp2xyz(r,p)]))
                x,y,z = list(xyz/np.max(np.abs(xyz)))
                G2frame.G2plotNB.status.SetStatusText(
                    'psi =%9.3f, beta =%9.3f, MRD =%9.3f hkl=%5.2f,%5.2f,%5.2f'%(r,p,ipf,x,y,z),1)
    
    import scipy.interpolate as si
    generalData = data['General']
    SGData = generalData['SGData']
    if Start:                   #initialize the spherical harmonics qlmn arrays
        ptx.pyqlmninit()
        Start = False
    cell = generalData['Cell'][1:]
    Amat,Bmat = G2lat.cell2AB(cell[:6])
    useList = data['Histograms']
    phase = generalData['Name']
    plotType = generalData['Data plot type']
    plotDict = {'Mustrain':'Mustrain','Size':'Size','Preferred orientation':'Pref.Ori.','Inv. pole figure':''}
    for ptype in plotDict:
        G2frame.G2plotNB.Delete(ptype)
    if plotType in ['None'] or not useList:
        return        
    if hist == '':
        hist = useList.keys()[0]

    if plotType in ['Mustrain','Size']:
        new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab(plotType,'3d')
    else:
        new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab(plotType,'mpl')
    if not new:
        if not Page.IsShown():
            Page.Show()
    else:
        Page.canvas.mpl_connect('pick_event', OnPick)
        Page.canvas.mpl_connect('motion_notify_event', OnMotion)
    Page.Choice = None
    G2frame.G2plotNB.status.SetStatusText('',1)
    
    PHI = np.linspace(0.,360.,30,True)
    PSI = np.linspace(0.,180.,30,True)
    X = np.outer(npsind(PHI),npsind(PSI))
    Y = np.outer(npcosd(PHI),npsind(PSI))
    Z = np.outer(np.ones(np.size(PHI)),npcosd(PSI))
    try:        #temp patch instead of 'mustrain' for old files with 'microstrain'
        if plotDict[plotType]:
            coeff = useList[hist][plotDict[plotType]]
    except KeyError:
        return
    if plotType in ['Mustrain','Size']:
        if coeff[0] == 'isotropic':
            X *= coeff[1][0]
            Y *= coeff[1][0]
            Z *= coeff[1][0]                                
        elif coeff[0] == 'uniaxial':
            
            def uniaxCalc(xyz,iso,aniso,axes):
                Z = np.array(axes)
                cp = abs(np.dot(xyz,Z))
                sp = np.sqrt(1.-cp**2)
                R = iso*aniso/np.sqrt((iso*cp)**2+(aniso*sp)**2)
                return R*xyz
                
            iso,aniso = coeff[1][:2]
            axes = np.inner(Amat,np.array(coeff[3]))
            axes /= nl.norm(axes)
            Shkl = np.array(coeff[1])
            XYZ = np.dstack((X,Y,Z))
            XYZ = np.nan_to_num(np.apply_along_axis(uniaxCalc,2,XYZ,iso,aniso,axes))
            X,Y,Z = np.dsplit(XYZ,3)
            X = X[:,:,0]
            Y = Y[:,:,0]
            Z = Z[:,:,0]
        
        elif coeff[0] == 'ellipsoidal':
            
            def ellipseCalc(xyz,E,R):
                XYZ = xyz*E.T
                return np.inner(XYZ.T,R)
                
            S6 = coeff[4]
            Sij = G2lat.U6toUij(S6)
            E,R = nl.eigh(Sij)
            XYZ = np.dstack((X,Y,Z))
            XYZ = np.nan_to_num(np.apply_along_axis(ellipseCalc,2,XYZ,E,R))
            X,Y,Z = np.dsplit(XYZ,3)
            X = X[:,:,0]
            Y = Y[:,:,0]
            Z = Z[:,:,0]
            
        elif coeff[0] == 'generalized':
            
            def genMustrain(xyz,SGData,A,Shkl):
                uvw = np.inner(Amat.T,xyz)
                Strm = np.array(G2spc.MustrainCoeff(uvw,SGData))
                Sum = np.sum(np.multiply(Shkl,Strm))
                Sum = np.where(Sum > 0.01,Sum,0.01)
                Sum = np.sqrt(Sum)
                return Sum*xyz
                
            Shkl = np.array(coeff[4])
            if np.any(Shkl):
                XYZ = np.dstack((X,Y,Z))
                XYZ = np.nan_to_num(np.apply_along_axis(genMustrain,2,XYZ,SGData,Amat,Shkl))
                X,Y,Z = np.dsplit(XYZ,3)
                X = X[:,:,0]
                Y = Y[:,:,0]
                Z = Z[:,:,0]
                    
        if np.any(X) and np.any(Y) and np.any(Z):
            np.seterr(all='ignore')
            Plot.plot_surface(X,Y,Z,rstride=1,cstride=1,color='g',linewidth=1)
            xyzlim = np.array([Plot.get_xlim3d(),Plot.get_ylim3d(),Plot.get_zlim3d()]).T
            XYZlim = [min(xyzlim[0]),max(xyzlim[1])]
            Plot.set_xlim3d(XYZlim)
            Plot.set_ylim3d(XYZlim)
            Plot.set_zlim3d(XYZlim)
            Plot.set_aspect('equal')
        if plotType == 'Size':
            Plot.set_title('Crystallite size for '+phase+'\n'+coeff[0]+' model')
            Plot.set_xlabel(r'X, $\mu$m')
            Plot.set_ylabel(r'Y, $\mu$m')
            Plot.set_zlabel(r'Z, $\mu$m')
        else:    
            Plot.set_title(r'$\mu$strain for '+phase+'\n'+coeff[0]+' model')
            Plot.set_xlabel(r'X, $\mu$strain')
            Plot.set_ylabel(r'Y, $\mu$strain')
            Plot.set_zlabel(r'Z, $\mu$strain')
    elif plotType in ['Preferred orientation',]:
        h,k,l = generalData['POhkl']
        if coeff[0] == 'MD':
            print 'March-Dollase preferred orientation plot'
        
        else:
            PH = np.array(generalData['POhkl'])
            phi,beta = G2lat.CrsAng(PH,cell[:6],SGData)
            SHCoef = {}
            for item in coeff[5]:
                L,N = eval(item.strip('C'))
                SHCoef['C%d,0,%d'%(L,N)] = coeff[5][item]                        
            ODFln = G2lat.Flnh(Start,SHCoef,phi,beta,SGData)
            X = np.linspace(0,90.0,26)
            Y = G2lat.polfcal(ODFln,'0',X,0.0)
            Plot.plot(X,Y,color='k',label=str(PH))
            Plot.legend(loc='best')
            Plot.set_title('Axial distribution for HKL='+str(PH)+' in '+phase+'\n'+hist)
            Plot.set_xlabel(r'$\psi$',fontsize=16)
            Plot.set_ylabel('MRD',fontsize=14)
    elif plotType in ['Inv. pole figure',]:
        Id = G2gd.GetPatternTreeItemId(G2frame,G2frame.root,hist)
        rId = G2gd.GetPatternTreeItemId(G2frame,Id,'Reflection Lists')
        RefData = G2frame.PatternTree.GetItemPyData(rId)[phase]
        Type = RefData['Type']
        Refs = RefData['RefList'].T
        ns = 0
        if RefData['Super']:
            ns = 1
        if 'C' in Type:
            obsRMD = Refs[12+ns]
        else:
            obsRMD = Refs[15+ns]
        Phi = []
        Beta = []
        Rmd = []
        Ops = np.array([Op[0].T for Op in SGData['SGOps']])
        refSets = [np.inner(Ops,hkl) for hkl in Refs[:3].T]
        for ir,refSet in enumerate(refSets):
            refSet = np.vstack((refSet,-refSet))    #add Friedel pairs
            refSet = [np.where(ref[2]<0,-1.*ref,ref) for ref in refSet] #take +l of each pair then remove duplicates
            refSet = [str(ref).strip('[]').replace('-0',' 0') for ref in refSet]
            refSet = [np.fromstring(item,sep=' ') for item in set(refSet)]
            refSets[ir] = refSet
        RefSets = []
        for ir,refSet in enumerate(refSets):
            r,beta,phi = G2lat.HKL2SpAng(refSet,cell[:6],SGData)    #radius, inclination, azimuth
            phi *= np.pi/180.
            beta *= np.pi/180.
            Phi += list(phi)
            Beta += list(beta)
            Rmd += len(phi)*[obsRMD[ir],]
            RefSets += refSet
        RefSets = np.array(RefSets)
        Beta = np.abs(np.array(Beta))
        Phi = np.array(Phi)
        Phi=np.where(Phi<0.,Phi+2.*np.pi,Phi)
        Rmd = np.array(Rmd)
        Rmd = np.where(Rmd<0.,0.,Rmd)
        if 'equal' in G2frame.Projection:
            x,y = np.tan(Beta/2.)*np.cos(Phi),np.tan(Beta/2.)*np.sin(Phi)        
        else:
            x,y = np.tan(Beta/2.)*np.cos(Phi),np.tan(Beta/2.)*np.sin(Phi)        
        sq2 = 1.0/math.sqrt(2.0)
        npts = 201
        X,Y = np.meshgrid(np.linspace(1.,-1.,npts),np.linspace(-1.,1.,npts))
        R,P = np.sqrt(X**2+Y**2).flatten(),npatan2d(X,Y).flatten()
        P=np.where(P<0.,P+360.,P)
        if 'equal' in G2frame.Projection:
            R = np.where(R <= 1.,2.*npasind(R*sq2),0.0)
        else:
            R = np.where(R <= 1.,2.*npatand(R),0.0)
        Z = np.zeros_like(R)
#        GSASIIpath.IPyBreak()
        try:
            sfac = 0.1
            while True:
                try:
                    lut = si.SmoothSphereBivariateSpline(Beta,Phi,Rmd,s=sfac)
                    break
                except ValueError:
                    sfac *= 1.05
            Z = [lut(ri*np.pi/180.,p*np.pi/180.) for ri,p in zip(list(R),list(P))]
            print 'IVP for histogramn: %s: interpolate sfactor: %.2f'%(hist,sfac)
        except AttributeError:
            G2frame.G2plotNB.Delete(plotType)
            G2G.G2MessageBox(G2frame,'IVP interpolate error: scipy needs to be 0.11.0 or newer',
                    'IVP error')
            return        
        Z = np.reshape(Z,(npts,npts))
        try:
            CS = Plot.contour(Y,X,Z,aspect='equal')
            Plot.clabel(CS,fontsize=9,inline=1)
        except ValueError:
            pass
        Img = Plot.imshow(Z.T,aspect='equal',cmap=G2frame.ContourColor,extent=[-1,1,-1,1])
        Plot.plot(-x,y,'+',picker=3)
        Page.figure.colorbar(Img)
        Plot.axis('off')
        Plot.set_title('0 0 1 Inverse pole figure for %s\n%s'%(phase,hist))
        
    Page.canvas.draw()
    
################################################################################
##### PlotTexture
################################################################################

def PlotTexture(G2frame,data,Start=False):
    '''Pole figure, inverse pole figure plotting.
    dict generalData contains all phase info needed which is in data
    '''

    shModels = ['cylindrical','none','shear - 2/m','rolling - mmm']
    SamSym = dict(zip(shModels,['0','-1','2/m','mmm']))
#    PatternId = G2frame.PatternId
    generalData = data['General']
    SGData = generalData['SGData']
    pName = generalData['Name']
    textureData = generalData['SH Texture']
    G2frame.G2plotNB.Delete('Texture')
    if not textureData['Order']:
        return                  #no plot!!
    SHData = generalData['SH Texture']
    SHCoef = SHData['SH Coeff'][1]
    cell = generalData['Cell'][1:7]
    Amat,Bmat = G2lat.cell2AB(cell)
    sq2 = 1.0/math.sqrt(2.0)
    
    def rp2xyz(r,p):
        z = npcosd(r)
        xy = np.sqrt(1.-z**2)
        return xy*npsind(p),xy*npcosd(p),z
            
    def OnMotion(event):
        SHData = data['General']['SH Texture']
        if event.xdata and event.ydata:                 #avoid out of frame errors
            xpos = event.xdata
            ypos = event.ydata
            if 'Inverse' in SHData['PlotType']:
                r = xpos**2+ypos**2
                if r <= 1.0:
                    if 'equal' in G2frame.Projection: 
                        r,p = 2.*npasind(np.sqrt(r)*sq2),npatan2d(ypos,xpos)
                    else:
                        r,p = 2.*npatand(np.sqrt(r)),npatan2d(ypos,xpos)
                    ipf = G2lat.invpolfcal(IODFln,SGData,np.array([r,]),np.array([p,]))
                    xyz = np.inner(Bmat,np.array([rp2xyz(r,p)]))
                    y,x,z = list(xyz/np.max(np.abs(xyz)))
                    
                    G2frame.G2plotNB.status.SetStatusText(
                        'psi =%9.3f, beta =%9.3f, MRD =%9.3f hkl=%5.2f,%5.2f,%5.2f'%(r,p,ipf,x,y,z),1)
                
            elif 'Axial' in SHData['PlotType']:
                pass
                
            else:                       #ordinary pole figure
                z = xpos**2+ypos**2
                if z <= 1.0:
                    z = np.sqrt(z)
                    if 'equal' in G2frame.Projection: 
                        r,p = 2.*npasind(z*sq2),npatan2d(ypos,xpos)
                    else:
                        r,p = 2.*npatand(z),npatan2d(ypos,xpos)
                    pf = G2lat.polfcal(ODFln,SamSym[textureData['Model']],np.array([r,]),np.array([p,]))
                    G2frame.G2plotNB.status.SetStatusText('phi =%9.3f, gam =%9.3f, MRD =%9.3f'%(r,p,pf),1)

    if '3D' in SHData['PlotType']:
        new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('Texture','3d')
    else:
        new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('Texture','mpl')
    if not new:
        if not Page.IsShown():
            Page.Show()
    else:
        Page.canvas.mpl_connect('motion_notify_event', OnMotion)
    Page.Choice = None
    G2frame.G2plotNB.status.SetFields(['',''])    
    G2frame.G2plotNB.status.SetStatusWidths([150,-1])
    PH = np.array(SHData['PFhkl'])
    phi,beta = G2lat.CrsAng(PH,cell,SGData)
    ODFln = G2lat.Flnh(Start,SHCoef,phi,beta,SGData)
    if not np.any(ODFln):
        return
    PX = np.array(SHData['PFxyz'])
    gam = atan2d(PX[0],PX[1])
    xy = math.sqrt(PX[0]**2+PX[1]**2)
    xyz = math.sqrt(PX[0]**2+PX[1]**2+PX[2]**2)
    psi = asind(xy/xyz)
    IODFln = G2lat.Glnh(Start,SHCoef,psi,gam,SamSym[textureData['Model']])
    if 'Axial' in SHData['PlotType']:
        X = np.linspace(0,90.0,26)
        Y = G2lat.polfcal(ODFln,SamSym[textureData['Model']],X,0.0)
        Plot.plot(X,Y,color='k',label=str(SHData['PFhkl']))
        Plot.legend(loc='best')
        h,k,l = SHData['PFhkl']
        Plot.set_title('%d %d %d Axial distribution for %s'%(h,k,l,pName))
        Plot.set_xlabel(r'$\psi$',fontsize=16)
        Plot.set_ylabel('MRD',fontsize=14)
        
    else:       
        npts = 201
        if 'Inverse' in SHData['PlotType']:
            X,Y = np.meshgrid(np.linspace(1.,-1.,npts),np.linspace(-1.,1.,npts))
            R,P = np.sqrt(X**2+Y**2).flatten(),npatan2d(X,Y).flatten()
            if 'equal' in G2frame.Projection:
                R = np.where(R <= 1.,2.*npasind(R*sq2),0.0)
            else:
                R = np.where(R <= 1.,2.*npatand(R),0.0)
            Z = np.zeros_like(R)
            Z = G2lat.invpolfcal(IODFln,SGData,R,P)
            Z = np.reshape(Z,(npts,npts))
            try:
                CS = Plot.contour(Y,X,Z,aspect='equal')
                Plot.clabel(CS,fontsize=9,inline=1)
            except ValueError:
                pass
            Img = Plot.imshow(Z.T,aspect='equal',cmap=G2frame.ContourColor,extent=[-1,1,-1,1])
            Page.figure.colorbar(Img)
            x,y,z = SHData['PFxyz']
            Plot.axis('off')
            Plot.set_title('%d %d %d Inverse pole figure for %s'%(int(x),int(y),int(z),pName))
            Plot.set_xlabel(G2frame.Projection.capitalize()+' projection')
            
        elif '3D' in SHData['PlotType']:
            PSI,GAM = np.mgrid[0:31,0:31]
            PSI = PSI.flatten()*6.
            GAM = GAM.flatten()*12.
            P = G2lat.polfcal(ODFln,SamSym[textureData['Model']],PSI,GAM).reshape((31,31))            
            GAM = np.linspace(0.,360.,31,True)
            PSI = np.linspace(0.,180.,31,True)
            X = np.outer(npsind(GAM),npsind(PSI))*P.T
            Y = np.outer(npcosd(GAM),npsind(PSI))*P.T
            Z = np.outer(np.ones(np.size(GAM)),npcosd(PSI))*P.T
            h,k,l = SHData['PFhkl']
            
            if np.any(X) and np.any(Y) and np.any(Z):
                np.seterr(all='ignore')
                Plot.plot_surface(X,Y,Z,rstride=1,cstride=1,color='g',linewidth=1)
                np.seterr(all='ignore')
                xyzlim = np.array([Plot.get_xlim3d(),Plot.get_ylim3d(),Plot.get_zlim3d()]).T
                XYZlim = [min(xyzlim[0]),max(xyzlim[1])]
                Plot.set_xlim3d(XYZlim)
                Plot.set_ylim3d(XYZlim)
                Plot.set_zlim3d(XYZlim)
                Plot.set_aspect('equal')                        
                Plot.set_title('%d %d %d Pole distribution for %s'%(h,k,l,pName))
                Plot.set_xlabel(r'X, MRD')
                Plot.set_ylabel(r'Y, MRD')
                Plot.set_zlabel(r'Z, MRD')
        else:
            X,Y = np.meshgrid(np.linspace(1.,-1.,npts),np.linspace(-1.,1.,npts))
            R,P = np.sqrt(X**2+Y**2).flatten(),npatan2d(X,Y).flatten()
            if 'equal' in G2frame.Projection:
                R = np.where(R <= 1.,2.*npasind(R*sq2),0.0)
            else:
                R = np.where(R <= 1.,2.*npatand(R),0.0)
            Z = np.zeros_like(R)
            Z = G2lat.polfcal(ODFln,SamSym[textureData['Model']],R,P)
            Z = np.reshape(Z,(npts,npts))
            try:
                CS = Plot.contour(Y,X,Z,aspect='equal')
                Plot.clabel(CS,fontsize=9,inline=1)
            except ValueError:
                pass
            Img = Plot.imshow(Z.T,aspect='equal',cmap=G2frame.ContourColor,extent=[-1,1,-1,1])
            Page.figure.colorbar(Img)
            h,k,l = SHData['PFhkl']
            Plot.axis('off')
            Plot.set_title('%d %d %d Pole figure for %s'%(h,k,l,pName))
    Page.canvas.draw()

################################################################################
##### Plot Modulation
################################################################################

def ModulationPlot(G2frame,data,atom,ax,off=0):
    global Off,Atom,Ax,Slab,Off
    Off = off
    Atom = atom
    Ax = ax
    
    def OnMotion(event):
        xpos = event.xdata
        if xpos:                                        #avoid out of frame mouse position
            ypos = event.ydata
            ix = int(round(xpos*10))
            iy = int(round((Slab.shape[0]-1)*(ypos+0.5-Off*0.005)))
            Page.canvas.SetCursor(wx.CROSS_CURSOR)
            try:
                G2frame.G2plotNB.status.SetStatusText('t =%9.3f %s =%9.3f %s=%9.3f'%(xpos,GkDelta+Ax,ypos,Gkrho,Slab[iy,ix]/8.),1)                   
#                GSASIIpath.IPyBreak()                  
            except (TypeError,IndexError):
                G2frame.G2plotNB.status.SetStatusText('Select '+Title+' pattern first',1)
    
    def OnPlotKeyPress(event):
        global Off,Atom,Ax
        if event.key == '0':
            Off = 0
        elif event.key in ['+','=']:
            Off += 1
        elif event.key == '-':
            Off -= 1
        elif event.key in ['l','r',] and mapData['Flip']:
            roll = 1
            if  event.key == 'l':
                roll = -1
            rho = Map['rho']
            Map['rho'] = np.roll(rho,roll,axis=3)
        wx.CallAfter(ModulationPlot,G2frame,data,Atom,Ax,Off)

    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('Modulation','mpl')
    if not new:
        if not Page.IsShown():
            Page.Show()
    else:
        Page.canvas.mpl_connect('motion_notify_event', OnMotion)
        Page.canvas.mpl_connect('key_press_event', OnPlotKeyPress)
    G2frame.G2plotNB.status.DestroyChildren()
    General = data['General']
    cx,ct,cs,cia = General['AtomPtrs']
    mapData = General['Map']
    if mapData['Flip']:
        Page.Choice = ['+: shift up','-: shift down','0: reset shift','l: move left','r: move right']
    else:
        Page.Choice = ['+: shift up','-: shift down','0: reset shift']
    Page.keyPress = OnPlotKeyPress
    Map = General['4DmapData']
    MapType = mapData['MapType']
    rhoSize = np.array(Map['rho'].shape)
    atxyz = np.array(atom[cx:cx+3])
    waveType = atom[-1]['SS1']['waveType']
    Spos = atom[-1]['SS1']['Spos']
    tau = np.linspace(0.,2.,101)
    wave = np.zeros((3,101))
    if len(Spos):
        scof = []
        ccof = []
        for i,spos in enumerate(Spos):
            if waveType in ['ZigZag','Block'] and not i:
                Tminmax = spos[0][:2]
                XYZmax = np.array(spos[0][2:])
                if waveType == 'Block':
                    wave = G2mth.posBlock(tau,Tminmax,XYZmax).T
                elif waveType == 'ZigZag':
                    wave = G2mth.posZigZag(tau,Tminmax,XYZmax).T
            else:
                scof.append(spos[0][:3])
                ccof.append(spos[0][3:])
        wave += G2mth.posFourier(tau,np.array(scof),np.array(ccof))
    if mapData['Flip']:
        Title = 'Charge flip'
    else:
        Title = MapType
    Title += ' map for atom '+atom[0]+    \
        ' at %.4f %.4f %.4f'%(atxyz[0],atxyz[1],atxyz[2])
    ix = -np.array(np.rint(rhoSize[:3]*atxyz)+1,dtype='i')
    ix += (rhoSize[:3]/2)
    ix = ix%rhoSize[:3]
    rho = np.roll(np.roll(np.roll(Map['rho'],ix[0],axis=0),ix[1],axis=1),ix[2],axis=2)
    ix = rhoSize[:3]/2
    ib = 4
    hdx = [2,2,2]       #this needs to be something for an offset correction on atom positions
    if Ax == 'x':
        Doff = (hdx[0]+Off)*.005
        slab = np.sum(np.sum(rho[:,ix[1]-ib:ix[1]+ib,ix[2]-ib:ix[2]+ib,:],axis=2),axis=1)
        Plot.plot(tau,wave[0])
    elif Ax == 'y':
        Doff = (hdx[1]+Off)*.005
        slab = np.sum(np.sum(rho[ix[0]-ib:ix[0]+ib,:,ix[2]-ib:ix[2]+ib,:],axis=2),axis=0)
        Plot.plot(tau,wave[1])
    elif Ax == 'z':
        Doff = (hdx[2]+Off)*.005
        slab = np.sum(np.sum(rho[ix[0]-ib:ix[0]+ib,ix[1]-ib:ix[1]+ib,:,:],axis=1),axis=0)
        Plot.plot(tau,wave[2])
    Plot.set_title(Title)
    Plot.set_xlabel('t')
    Plot.set_ylabel(r'$\mathsf{\Delta}$%s'%(Ax))
    Slab = np.hstack((slab,slab,slab))   
    acolor = mpl.cm.get_cmap('RdYlGn')
    if 'delt' in MapType:
        Plot.contour(Slab[:,:21],20,extent=(0.,2.,-.5+Doff,.5+Doff),cmap=acolor)
    else:
        Plot.contour(Slab[:,:21],20,extent=(0.,2.,-.5+Doff,.5+Doff))
    Plot.set_ylim([-0.25,0.25])
    Page.canvas.draw()
   
################################################################################
##### PlotCovariance
################################################################################
            
def PlotCovariance(G2frame,Data):
    'needs a doc string'
    if not Data:
        print 'No covariance matrix available'
        return
    varyList = Data['varyList']
    values = Data['variables']
    covMatrix = Data['covMatrix']
    sig = np.sqrt(np.diag(covMatrix))
    xvar = np.outer(sig,np.ones_like(sig))
    covArray = np.divide(np.divide(covMatrix,xvar),xvar.T)
    title = ' for\n'+Data['title']
    newAtomDict = Data.get('newAtomDict',{})
    G2frame.G2plotNB.status.DestroyChildren()

    def OnPlotKeyPress(event):
        if event.key == 's':
            choice = [m for m in mpl.cm.datad.keys() if not m.endswith("_r")]
            choice.sort()
            dlg = wx.SingleChoiceDialog(G2frame,'Select','Color scheme',choice)
            if dlg.ShowModal() == wx.ID_OK:
                sel = dlg.GetSelection()
                G2frame.VcovColor = choice[sel]
            else:
                G2frame.VcovColor = 'RdYlGn'
            dlg.Destroy()
        elif event.key == 'p':
            covFile = open(os.path.splitext(G2frame.GSASprojectfile)[0]+'.cov','w')
            covFile.write(128*'*' + '\n')
            covFile.write('*' + 126*' ' + '*\n')
            covFile.write('*{:^126}*\n'.format('Covariance Matrix'))
            covFile.write('*' + 126*' ' + '*\n')
            covFile.write(128*'*' + '\n\n\n\n')
            llen = len(varyList)
            for start in xrange(0, llen, 8):  # split matrix into batches of 7 columns
                if llen >= start + 8:
                    stop = start + 8
                else:
                    stop = llen
                covFile.write(12*' ' + '\t')
                for idx in xrange(start, stop):
                    covFile.write('{:^12}\t'.format(varyList[idx]))
                covFile.write('\n\n')
                for line in xrange(llen):
                    covFile.write('{:>12}\t'.format(varyList[line]))
                    for idx in xrange(start, stop):
                        covFile.write('{: 12.6f}\t'.format(covArray[line][idx]))
                    covFile.write('\n')
                covFile.write('\n\n\n')
            covFile.close()
        PlotCovariance(G2frame,Data)

    def OnMotion(event):
        if event.button:
            ytics = imgAx.get_yticks()
            ytics = np.where(ytics<len(varyList),ytics,-1)
            ylabs = [np.where(0<=i ,varyList[int(i)],' ') for i in ytics]
            imgAx.set_yticklabels(ylabs)            
        if event.xdata and event.ydata:                 #avoid out of frame errors
            xpos = int(event.xdata+.5)
            ypos = int(event.ydata+.5)
            if -1 < xpos < len(varyList) and -1 < ypos < len(varyList):
                if xpos == ypos:
                    value = values[xpos]
                    name = varyList[xpos]
                    if varyList[xpos] in newAtomDict:
                        name,value = newAtomDict[name]                        
                    msg = '%s value = %.4g, esd = %.4g'%(name,value,sig[xpos])
                else:
                    msg = '%s - %s: %5.3f'%(varyList[xpos],varyList[ypos],covArray[xpos][ypos])
                Page.canvas.SetToolTipString(msg)
                G2frame.G2plotNB.status.SetStatusText(msg,1)
                
    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('Covariance','mpl')
    if not new:
        if not Page.IsShown():
            Page.Show()
    else:
        Page.canvas.mpl_connect('motion_notify_event', OnMotion)
        Page.canvas.mpl_connect('key_press_event', OnPlotKeyPress)
    Page.Choice = ['s: to change colors','p: to save covariance as text file']
    Page.keyPress = OnPlotKeyPress
    G2frame.G2plotNB.status.SetFields(['',''])
    G2frame.G2plotNB.status.SetStatusWidths([150,-1])   #need to reset field widths here    
    acolor = mpl.cm.get_cmap(G2frame.VcovColor)
    Img = Plot.imshow(covArray,aspect='equal',cmap=acolor,interpolation='nearest',origin='lower',
        vmin=-1.,vmax=1.)
    imgAx = Img.get_axes()
    ytics = imgAx.get_yticks()
    ylabs = [varyList[int(i)] for i in ytics[:-1]]
    imgAx.set_yticklabels(ylabs)
    Page.figure.colorbar(Img)
    Plot.set_title('V-Cov matrix'+title)
    Plot.set_xlabel('Variable number')
    Plot.set_ylabel('Variable name')
    Page.canvas.draw()
    
################################################################################
##### PlotTorsion
################################################################################

def PlotTorsion(G2frame,phaseName,Torsion,TorName,Names=[],Angles=[],Coeff=[]):
    'needs a doc string'
    
    global names
    names = Names
    sum = np.sum(Torsion)
    torsion = np.log(2*Torsion+1.)/sum
    tMin = np.min(torsion)
    tMax = np.max(torsion)
    torsion = 3.*(torsion-tMin)/(tMax-tMin)
    X = np.linspace(0.,360.,num=45)
    
    def OnPick(event):
        ind = event.ind[0]
        msg = 'atoms:'+names[ind]
        Page.canvas.SetToolTipString(msg)
        try:
            page = G2frame.dataDisplay.GetSelection()
        except:
            return
        if G2frame.dataDisplay.GetPageText(page) == 'Torsion restraints':
            torGrid = G2frame.dataDisplay.GetPage(page).Torsions
            torGrid.ClearSelection()
            for row in range(torGrid.GetNumberRows()):
                if names[ind] in torGrid.GetCellValue(row,0):
                    torGrid.SelectRow(row)
            torGrid.ForceRefresh()
                
    def OnMotion(event):
        if event.xdata and event.ydata:                 #avoid out of frame errors
            xpos = event.xdata
            ypos = event.ydata
            msg = 'torsion,energy: %5.3f %5.3f'%(xpos,ypos)
            Page.canvas.SetToolTipString(msg)

    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('Torsion','mpl')
    if not new:
        if not Page.IsShown():
            Page.Show()
    else:
        Page.canvas.mpl_connect('pick_event', OnPick)
        Page.canvas.mpl_connect('motion_notify_event', OnMotion)

    G2frame.G2plotNB.status.SetStatusText('Use mouse LB to identify torsion atoms',1)
    Plot.plot(X,torsion,'b+')
    if len(Coeff):
        X2 = np.linspace(0.,360.,45)
        Y2 = np.array([-G2mth.calcTorsionEnergy(x,Coeff)[1] for x in X2])
        Plot.plot(X2,Y2,'r')
    if len(Angles):
        Eval = np.array([-G2mth.calcTorsionEnergy(x,Coeff)[1] for x in Angles])
        Plot.plot(Angles,Eval,'ro',picker=5)
    Plot.set_xlim((0.,360.))
    Plot.set_title('Torsion angles for '+TorName+' in '+phaseName)
    Plot.set_xlabel('angle',fontsize=16)
    Plot.set_ylabel('Energy',fontsize=16)
    Page.canvas.draw()
    
################################################################################
##### PlotRama
################################################################################

def PlotRama(G2frame,phaseName,Rama,RamaName,Names=[],PhiPsi=[],Coeff=[]):
    'needs a doc string'

    global names
    names = Names
    rama = np.log(2*Rama+1.)
    rama = np.reshape(rama,(45,45))
    global Phi,Psi
    Phi = []
    Psi = []

    def OnPlotKeyPress(event):
        if event.key == 's':
            choice = [m for m in mpl.cm.datad.keys() if not m.endswith("_r")]
            choice.sort()
            dlg = wx.SingleChoiceDialog(G2frame,'Select','Color scheme',choice)
            if dlg.ShowModal() == wx.ID_OK:
                sel = dlg.GetSelection()
                G2frame.RamaColor = choice[sel]
            else:
                G2frame.RamaColor = 'RdYlGn'
            dlg.Destroy()
        PlotRama(G2frame,phaseName,Rama)

    def OnPick(event):
        ind = event.ind[0]
        msg = 'atoms:'+names[ind]
        Page.canvas.SetToolTipString(msg)
        try:
            page = G2frame.dataDisplay.GetSelection()
        except:
            return
        if G2frame.dataDisplay.GetPageText(page) == 'Ramachandran restraints':
            ramaGrid = G2frame.dataDisplay.GetPage(page).Ramas
            ramaGrid.ClearSelection()
            for row in range(ramaGrid.GetNumberRows()):
                if names[ind] in ramaGrid.GetCellValue(row,0):
                    ramaGrid.SelectRow(row)
            ramaGrid.ForceRefresh()

    def OnMotion(event):
        if event.xdata and event.ydata:                 #avoid out of frame errors
            xpos = event.xdata
            ypos = event.ydata
            msg = 'phi/psi: %5.3f %5.3f'%(xpos,ypos)
            Page.canvas.SetToolTipString(msg)
            
    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('Ramachandran','mpl')
    if not new:
        if not Page.IsShown():
            Page.Show()
    else:
        Page.canvas.mpl_connect('pick_event', OnPick)
        Page.canvas.mpl_connect('motion_notify_event', OnMotion)
        Page.canvas.mpl_connect('key_press_event', OnPlotKeyPress)

    Page.Choice = ['s: to change colors']
    Page.keyPress = OnPlotKeyPress
    G2frame.G2plotNB.status.SetStatusText('Use mouse LB to identify phi/psi atoms',1)
    acolor = mpl.cm.get_cmap(G2frame.RamaColor)
    if RamaName == 'All' or '-1' in RamaName:
        if len(Coeff): 
            X,Y = np.meshgrid(np.linspace(-180.,180.,45),np.linspace(-180.,180.,45))
            Z = np.array([-G2mth.calcRamaEnergy(x,y,Coeff)[1] for x,y in zip(X.flatten(),Y.flatten())])
            Plot.contour(X,Y,np.reshape(Z,(45,45)))
        Img = Plot.imshow(rama,aspect='equal',cmap=acolor,interpolation='nearest',
            extent=[-180,180,-180,180],origin='lower')
        if len(PhiPsi):
            Phi,Psi = PhiPsi.T
            Phi = np.where(Phi>180.,Phi-360.,Phi)
            Psi = np.where(Psi>180.,Psi-360.,Psi)
            Plot.plot(Phi,Psi,'ro',picker=5)
        Plot.set_xlim((-180.,180.))
        Plot.set_ylim((-180.,180.))
    else:
        if len(Coeff): 
            X,Y = np.meshgrid(np.linspace(0.,360.,45),np.linspace(0.,360.,45))
            Z = np.array([-G2mth.calcRamaEnergy(x,y,Coeff)[1] for x,y in zip(X.flatten(),Y.flatten())])
            Plot.contour(X,Y,np.reshape(Z,(45,45)))
        Img = Plot.imshow(rama,aspect='equal',cmap=acolor,interpolation='nearest',
            extent=[0,360,0,360],origin='lower')
        if len(PhiPsi):
            Phi,Psi = PhiPsi.T
            Plot.plot(Phi,Psi,'ro',picker=5)
        Plot.set_xlim((0.,360.))
        Plot.set_ylim((0.,360.))
    Plot.set_title('Ramachandran for '+RamaName+' in '+phaseName)
    Plot.set_xlabel(r'$\phi$',fontsize=16)
    Plot.set_ylabel(r'$\psi$',fontsize=16)
    Page.figure.colorbar(Img)
    Page.canvas.draw()


################################################################################
##### PlotSeq
################################################################################
def PlotSelectedSequence(G2frame,ColumnList,TableGet,SelectX,fitnum=None,fitvals=None):
    '''Plot a result from a sequential refinement

    :param wx.Frame G2frame: The main GSAS-II tree "window"
    :param list ColumnList: list of int values corresponding to columns
      selected as y values
    :param function TableGet: a function that takes a column number
      as argument and returns the column label, the values and there ESDs (or None)
    :param function SelectX: a function that returns a selected column
      number (or None) as the X-axis selection
    '''
    global Title,xLabel,yLabel
    xLabel = yLabel = Title = ''
    def OnMotion(event):
        if event.xdata and event.ydata:                 #avoid out of frame errors
            xpos = event.xdata
            ypos = event.ydata
            msg = '%5.3f %.6g'%(xpos,ypos)
            Page.canvas.SetToolTipString(msg)

    def OnKeyPress(event):
        global Title,xLabel,yLabel
        if event.key == 's':
            G2frame.seqXaxis = G2frame.seqXselect()
            Draw()
        elif event.key == 't':
            dlg = G2G.MultiStringDialog(G2frame,'Set titles & labels',[' Title ',' x-Label ',' y-Label '],
                [Title,xLabel,yLabel])
            if dlg.Show():
                Title,xLabel,yLabel = dlg.GetValues()
            dlg.Destroy()
            Draw()
        elif event.key == 'l':
            G2frame.seqLines = not G2frame.seqLines
            wx.CallAfter(Draw)
            
    def Draw():
        global Title,xLabel,yLabel
        G2frame.G2plotNB.RaisePageNoRefresh(Page)
        G2frame.G2plotNB.status.SetStatusText(  \
            'press L to toggle lines, S to select X axis, T to change titles (reselect column to show?)',1)
        Plot.clear()
        if G2frame.seqXaxis is not None:    
            xName,X,Xsig = Page.seqTableGet(G2frame.seqXaxis)
        else:
            X = np.arange(0,G2frame.SeqTable.GetNumberRows(),1)
            xName = 'Data sequence number'
        for col in Page.seqYaxisList:
            name,Y,sig = Page.seqTableGet(col)
            # deal with missing (None) values
            Xnew = []
            Ynew = []
            Ysnew = []
            for i in range(len(X)):
                if X[i] is None or Y[i] is None: continue
                Xnew.append(X[i])
                Ynew.append(Y[i])
                if sig: Ysnew.append(sig[i])
            if Ysnew:
                if G2frame.seqReverse and not G2frame.seqXaxis:
                    Ynew = Ynew[::-1]
                    Ysnew = Ysnew[::-1]
                if G2frame.seqLines:
                    Plot.errorbar(Xnew,Ynew,yerr=Ysnew,label=name)
                else:
                    Plot.errorbar(Xnew,Ynew,yerr=Ysnew,label=name,linestyle='None',marker='x')
            else:
                if G2frame.seqReverse and not G2frame.seqXaxis:
                    Ynew = Ynew[::-1]
                Plot.plot(Xnew,Ynew)
                Plot.plot(Xnew,Ynew,'o',label=name)
        if Page.fitvals: # TODO: deal with fitting of None values
            if G2frame.seqReverse and not G2frame.seqXaxis:
                Page.fitvals = Page.fitvals[::-1]
            Plot.plot(X,Page.fitvals,label='Fit')
            
        Plot.legend(loc='best')
        if Title:
            Plot.set_title(Title)
        else:
            Plot.set_title('')
        if xLabel:
            Plot.set_xlabel(xLabel)
        else:
            Plot.set_xlabel(xName)
        if yLabel:
            Plot.set_ylabel(yLabel)
        else:
            Plot.set_ylabel('Parameter values')
        Page.canvas.draw()
            
    G2frame.seqXselect = SelectX
    try:
        G2frame.seqXaxis
    except:
        G2frame.seqXaxis = None

    if fitnum is None:
        label = 'Sequential refinement'
    else:
        label = 'Parametric fit #'+str(fitnum+1)
    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab(label,'mpl')
    if not new:
        if not Page.IsShown():
            Page.Show()
    else:
        Page.canvas.mpl_connect('key_press_event', OnKeyPress)
        Page.canvas.mpl_connect('motion_notify_event', OnMotion)
    Page.Choice = ['l - toggle lines','s - select x-axis','t - change titles',]
    Page.keyPress = OnKeyPress
    Page.seqYaxisList = ColumnList
    Page.seqTableGet = TableGet
    Page.fitvals = fitvals
        
    Draw()
                
################################################################################
##### PlotExposedImage & PlotImage
################################################################################
            
def PlotExposedImage(G2frame,newPlot=False,event=None):
    '''General access module for 2D image plotting
    '''
    plotNo = G2frame.G2plotNB.nb.GetSelection()
    if plotNo < 0: return # no plots
    if G2frame.G2plotNB.nb.GetPageText(plotNo) == '2D Powder Image':
        PlotImage(G2frame,newPlot,event,newImage=True)
    elif G2frame.G2plotNB.nb.GetPageText(plotNo) == '2D Integration':
        PlotIntegration(G2frame,newPlot,event)

def OnStartMask(G2frame):
    '''Initiate the start of a Frame or Polygon map, etc.
    Called from a menu command (GSASIIimgGUI) or from OnImPlotKeyPress. 
    Variable G2frame.MaskKey contains a single letter ('f' or 'p', etc.) that
      determines what type of mask is created.    

    :param wx.Frame G2frame: The main GSAS-II tree "window"
    '''
    Masks = G2frame.PatternTree.GetItemPyData(
        G2gd.GetPatternTreeItemId(G2frame,G2frame.Image, 'Masks'))
    if G2frame.MaskKey == 'f':
        new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('2D Powder Image','mpl',newImage=False)
        if Masks['Frames']:
            Masks['Frames'] = []
            PlotImage(G2frame,newImage=True)
            G2frame.MaskKey = 'f'
        Page.figure.suptitle('Defining Frame mask (use right-mouse to end)',color='g',fontweight='bold')
        Page.canvas.draw()
    elif G2frame.MaskKey == 'p':
        Masks['Polygons'].append([])
        new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('2D Powder Image','mpl',newImage=False)
        Page.figure.suptitle('Defining Polygon mask (use right-mouse to end)',color='r',fontweight='bold')
        Page.canvas.draw()
    elif G2frame.MaskKey == 'a':
        new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('2D Powder Image','mpl',newImage=False)
        Page.figure.suptitle('Left-click to create an arc mask',color='r',fontweight='bold')
        Page.canvas.draw()
    elif G2frame.MaskKey == 'r':
        new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('2D Powder Image','mpl',newImage=False)
        Page.figure.suptitle('Left-click to create a ring mask',color='r',fontweight='bold')
        Page.canvas.draw()
    G2imG.UpdateMasks(G2frame,Masks)
    
def OnStartNewDzero(G2frame):
    '''Initiate the start of adding a new d-zero to a strain data set

    :param wx.Frame G2frame: The main GSAS-II tree "window"
    :param str eventkey: a single letter ('a') that
      triggers the addition of a d-zero.    
    '''
    G2frame.dataFrame.GetStatusBar().SetStatusText('Add strain ring active - LB pick d-zero value',0)
    G2frame.PickId = G2gd.GetPatternTreeItemId(G2frame,G2frame.Image, 'Stress/Strain')
    data = G2frame.PatternTree.GetItemPyData(G2frame.PickId)
    return data

def ToggleMultiSpotMask(G2frame):
    '''Turns on and off MultiSpot selection mode; displays a subtitle on plot
    the is cleared by the next PlotImage call
    '''
    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('2D Powder Image','mpl',newImage=False)
    if G2frame.MaskKey == 's':
        G2frame.MaskKey = ''
        Page.Choice[-1] = 's: start multiple spot mask mode'
        wx.CallAfter(PlotImage,G2frame,newImage=True)
    else:
        G2frame.MaskKey = 's'
        (x0,y0),(x1,y1) = Plot.get_position().get_points()
        Page.figure.suptitle('Multiple spot mode on, press s or right-click to end',color='r',fontweight='bold')
        Page.Choice[-1] = 's: stop multiple spot mask mode'
        Page.canvas.draw()

def ComputeArc(angI,angO,wave,azm0=0,azm1=362):
    '''Computes arc/ring arrays in with inner and outer radii from angI,angO
    and beginning and ending azimuths azm0,azm1 (optional).
    Returns the inner and outer ring/arc arrays.
    '''
    Dsp = lambda tth,wave: wave/(2.*npsind(tth/2.))
    xy1 = []
    xy2 = []
    aR = [azm0,azm1,max(3,int(0.5+azm1-azm0))] # number of points should be at least 3
    if azm1-azm0 > 180: aR[2] /= 2  # for more than 180 degrees, steps can be 2 deg.
    Azm = np.linspace(*aR)
    for azm in Azm:
        xy1.append(G2img.GetDetectorXY(Dsp(angI,wave),azm,Data))      #what about hyperbola
        xy2.append(G2img.GetDetectorXY(Dsp(angO,wave),azm,Data))      #what about hyperbola
    return np.array(xy1).T,np.array(xy2).T

def UpdatePolygon(pick,event,polygon):
    '''Update a polygon (or frame) in response to the location of the mouse.
    Delete the selected point if moved on top of another.
    With right button add a point after the current button.
    '''
    Xpos,Ypos = [event.xdata,event.ydata]
    if event.button == 1:
        # find distance to closest point other than selected point
        dlist = [np.sqrt((x-Xpos)**2 + (y-Ypos)**2) for i,(x,y) in enumerate(polygon)]
        dlist[pick.pointNumber] = max(dlist)
        dmin = min(dlist)
        cp = dlist.index(min(dlist)) # closest point
        if dmin < 1.5 and cp != pick.pointNumber:
            del polygon[pick.pointNumber]
        else:
            polygon[pick.pointNumber] = [Xpos,Ypos]
        polygon[-1] = polygon[0][:]
    elif event.button == 3:
        polygon.insert(pick.pointNumber+1,[Xpos,Ypos])

def PlotImage(G2frame,newPlot=False,event=None,newImage=True):
    '''Plot of 2D detector images as contoured plot. Also plot calibration ellipses,
    masks, etc. Plots whatever is in G2frame.ImageZ

    :param wx.Frame G2frame: main GSAS-II frame
    :param bool newPlot: if newPlot is True, the plot is reset (zoomed out, etc.)
    :param event: matplotlib mouse event (or None)
    :param bool newImage: If True, the Figure is cleared and redrawn
    '''
    from matplotlib.patches import Ellipse,Circle
    import numpy.ma as ma
    G2frame.cid = None
    #Dsp = lambda tth,wave: wave/(2.*npsind(tth/2.))
    global Data,Masks,StrSta  # RVD: these are needed for multiple image controls/masks 
    colors=['b','g','r','c','m','k'] 
    Data = G2frame.PatternTree.GetItemPyData(
        G2gd.GetPatternTreeItemId(G2frame,G2frame.Image, 'Image Controls'))
# patch
    if 'invert_x' not in Data:
        Data['invert_x'] = False
        Data['invert_y'] = True
# end patch
    Masks = G2frame.PatternTree.GetItemPyData(
        G2gd.GetPatternTreeItemId(G2frame,G2frame.Image, 'Masks'))
    try:    #may be absent
        StrSta = G2frame.PatternTree.GetItemPyData(
            G2gd.GetPatternTreeItemId(G2frame,G2frame.Image, 'Stress/Strain'))
    except TypeError:   #is missing
        StrSta = {}

    def OnImMotion(event):
        Page.canvas.SetToolTipString('')
        sizexy = Data['size']
        if event.xdata and event.ydata and len(G2frame.ImageZ):                 #avoid out of frame errors
            Page.canvas.SetToolTipString('%8.2f %8.2fmm'%(event.xdata,event.ydata))
            Page.canvas.SetCursor(wx.CROSS_CURSOR)
            item = G2frame.itemPicked
            pixelSize = Data['pixelSize']
            scalex = 1000./pixelSize[0]         #microns --> 1/mm
            scaley = 1000./pixelSize[1]
            if item and G2frame.PatternTree.GetItemText(G2frame.PickId) == 'Image Controls':
                if 'Text' in str(item):
                    Page.canvas.SetToolTipString('%8.3f %8.3fmm'%(event.xdata,event.ydata))
                else:
                    xcent,ycent = Data['center']
                    xpos = event.xdata-xcent
                    ypos = event.ydata-ycent
                    tth,azm = G2img.GetTthAzm(event.xdata,event.ydata,Data)
                    if 'line3' in  str(item) or 'line4' in str(item) and not Data['fullIntegrate']:
                        Page.canvas.SetToolTipString('%6d deg'%(azm))
                    elif 'line1' in  str(item) or 'line2' in str(item):
                        Page.canvas.SetToolTipString('%8.3f deg'%(tth))                           
            else:
                xcent,ycent = Data['center']
                xpos = event.xdata
                ypos = event.ydata
                radius = np.sqrt((xpos-xcent)**2+(ypos-ycent)**2)
                xpix = int(xpos*scalex)
                ypix = int(ypos*scaley)
                Int = 0
                if (0 <= xpix < sizexy[0]) and (0 <= ypix < sizexy[1]):
                    Int = G2frame.ImageZ[ypix][xpix]
                tth,azm,D,dsp = G2img.GetTthAzmDsp(xpos,ypos,Data)
                Q = 2.*math.pi/dsp
                if G2frame.StrainKey:
                    G2frame.G2plotNB.status.SetStatusText('d-zero pick active',0)
                elif G2frame.MaskKey in ['p','f']:
                    G2frame.G2plotNB.status.SetStatusText('Polygon/frame mask pick - LB next point, RB close polygon',1)
                else:
                     G2frame.G2plotNB.status.SetStatusText( \
                        'Detector radius=%.3fmm, 2-th =%.3fdeg, dsp=%.3fA, Q=%.5fA-1, azm %.2fdeg, I=%6d'%(radius,tth,dsp,Q,azm,Int),1)

    def OnImPlotKeyPress(event):
        try:
            treeItem = G2frame.PatternTree.GetItemText(G2frame.PickId)
        except TypeError:
            return
        if treeItem == 'Masks':
            if event.key == 's': # implement multiple spot mode
                ToggleMultiSpotMask(G2frame)
                return
            elif event.key == 't':
                try: # called from menu?
                    Xpos,Ypos = event.xdata,event.ydata
                except AttributeError:
                    G2G.G2MessageBox(G2frame,
                         'You must use the "{}" key from the keyboard'.format(event.key),
                         'Keyboard only')
                    return
                if not (event.xdata and event.ydata): return
                d = GSASIIpath.GetConfigValue('Spot_mask_diameter',1.0)
                spot = [event.xdata,event.ydata,d]
                Masks['Points'].append(spot)
                artist = Circle(spot[:2],radius=spot[2]/2,fc='none',ec='r',picker=3)
                Page.figure.gca().add_artist(artist)
                artist.itemNumber = len(Masks['Points'])-1
                artist.itemType = 'Spot'
                G2imG.UpdateMasks(G2frame,Masks)
                Page.canvas.draw()
                return 
            elif event.key in ['l','p','f','a','r']:
                G2frame.MaskKey = event.key
                OnStartMask(G2frame)
                
        elif treeItem == 'Stress/Strain':
            if event.key in ['a',]:
                G2frame.StrainKey = event.key
                OnStartNewDzero(G2frame)
                wx.CallAfter(PlotImage,G2frame,newImage=False)
                
        elif treeItem == 'Image Controls':
            if event.key in ['c',]:
                Xpos = event.xdata
                if not Xpos:            #got point out of frame
                    return
                Ypos = event.ydata
                dlg = wx.MessageDialog(G2frame,'Are you sure you want to change the center?',
                    'Center change',style=wx.OK|wx.CANCEL)
                try:
                    if dlg.ShowModal() == wx.ID_OK:
                        print 'move center to: ',Xpos,Ypos
                        Data['center'] = [Xpos,Ypos]
                        G2imG.UpdateImageControls(G2frame,Data,Masks)
                        wx.CallAfter(PlotImage,G2frame,newPlot=False)
                finally:
                    dlg.Destroy()
                return
            elif event.key in ['d',]:  # set dmin from plot position
                if not (event.xdata and event.ydata): return
                xpos = event.xdata
                ypos = event.ydata
                tth,azm,D,dsp = G2img.GetTthAzmDsp(xpos,ypos,Data)
                G2frame.calibDmin.SetValue(dsp)
            elif event.key == 'l':
                G2frame.logPlot = not G2frame.logPlot
            elif event.key in ['x',]:
                Data['invert_x'] = not Data['invert_x']
            elif event.key in ['y',]:
                Data['invert_y'] = not Data['invert_y']
            wx.CallAfter(PlotImage,G2frame,newPlot=True)
            
    def OnImPick(event):
        'A object has been picked'
        def OnDragIntBound(event):
            'Respond to the dragging of one of the integration boundaries'
            if event.xdata is None or event.ydata is None:
                # mouse is outside window. Could abort the movement,
                # for now ignore the movement until it moves back in
                return
            tth,azm,D,dsp = G2img.GetTthAzmDsp(event.xdata,event.ydata,Data)
            itemPicked = str(G2frame.itemPicked)
            if 'line1' in itemPicked and 'Line2D' in itemPicked:
                Data['IOtth'][0] = max(tth,0.001)
            elif 'line2' in itemPicked and 'Line2D' in itemPicked:
                Data['IOtth'][1] = tth
            elif 'line3' in itemPicked and 'Line2D' in itemPicked:
                Data['LRazimuth'][0] = int(azm)
                Data['LRazimuth'][0] %= 360
            elif 'line4' in itemPicked  and 'Line2D' in itemPicked:
                Data['LRazimuth'][1] = int(azm)
                Data['LRazimuth'][1] %= 360
            else:
                return
            if Data['LRazimuth'][0] > Data['LRazimuth'][1]: Data['LRazimuth'][1] += 360
            if Data['fullIntegrate']: Data['LRazimuth'][1] = Data['LRazimuth'][0]+360
            #if Data['IOtth'][0] > Data['IOtth'][1]:
            #    Data['IOtth'][0],Data['IOtth'][1] = Data['IOtth'][1],Data['IOtth'][0]
            # compute arcs, etc
            LRAzim = Data['LRazimuth']                  #NB: integers
            Nazm = Data['outAzimuths']
            delAzm = float(LRAzim[1]-LRAzim[0])/Nazm
            AzmthOff = Data['azmthOff']
            IOtth = Data['IOtth']
            wave = Data['wavelength']
            dspI = wave/(2.0*sind(IOtth[0]/2.0))
            ellI = G2img.GetEllipse(dspI,Data)           #=False if dsp didn't yield an ellipse (ugh! a parabola or a hyperbola)
            dspO = wave/(2.0*sind(IOtth[1]/2.0))
            ellO = G2img.GetEllipse(dspO,Data)           #Ditto & more likely for outer ellipse
            Azm = np.arange(LRAzim[0],LRAzim[1]+1.)-AzmthOff
            if ellI:
                xyI = []
                for azm in Azm:
                    xy = G2img.GetDetectorXY(dspI,azm,Data)
                    if np.any(xy):
                        xyI.append(xy)
                if len(xyI):
                    xyI = np.array(xyI)
                    arcxI,arcyI = xyI.T
            if ellO:
                xyO = []
                for azm in Azm:
                    xy = G2img.GetDetectorXY(dspO,azm,Data)
                    if np.any(xy):
                        xyO.append(xy)
                if len(xyO):
                    xyO = np.array(xyO)
                    arcxO,arcyO = xyO.T                

            Page.canvas.restore_region(savedplot)
            if 'line1' in itemPicked and 'Line2D' in itemPicked:
                pick.set_data([arcxI,arcyI])
            elif 'line2' in itemPicked and 'Line2D' in itemPicked:
                pick.set_data([arcxO,arcyO])
            elif 'line3' in itemPicked and 'Line2D' in itemPicked:
                pick.set_data([[arcxI[0],arcxO[0]],[arcyI[0],arcyO[0]]])
            elif 'line4' in itemPicked  and 'Line2D' in itemPicked:
                pick.set_data([[arcxI[-1],arcxO[-1]],[arcyI[-1],arcyO[-1]]])
            Page.figure.gca().draw_artist(pick)
            Page.canvas.blit(Page.figure.gca().bbox)
        def OnDragMask(event):
            'Respond to the dragging of a mask'
            if event.xdata is None or event.ydata is None:
                # mouse is outside window. Could abort the movement,
                # for now ignore the movement until it moves back in
                return
            Xpos,Ypos = [event.xdata,event.ydata]
            #if Page.toolbar._active: return # zoom/pan selected
            itemPicked = str(G2frame.itemPicked)
            Page.canvas.restore_region(savedplot)
            try:
                pickType = pick.itemType
            except:
                pickType = '?'
            if pickType == "Spot":
                itemNum = G2frame.itemPicked.itemNumber
                if event.button == 1:
                    x = Masks['Points'][itemNum][0]+Xpos-XposBeforeDrag
                    y = Masks['Points'][itemNum][1]+Ypos-YposBeforeDrag
                    pick.center=[x,y]
                elif event.button == 3:
                    r = math.sqrt((Xpos-Masks['Points'][itemNum][0])**2+
                              (Ypos-Masks['Points'][itemNum][1])**2)
                    pick.radius = r
                Page.figure.gca().draw_artist(pick)
            elif pickType.startswith('Ring'):
                wave = Data['wavelength']
                itemNum = G2frame.itemPicked.itemNumber
                if event.button == 1:
                    angO = angI = G2img.GetTth(Xpos,Ypos,Data)
                    if pickType == 'RingInner':
                        angO += Masks['Rings'][itemNum][1]
                    else:
                        angI -= Masks['Rings'][itemNum][1]
                    Masks['Rings'][itemNum][0] = (angO+angI)/2
                elif event.button == 3:
                    ang = G2img.GetTth(Xpos,Ypos,Data)
                    t = 2*abs(ang - Masks['Rings'][itemNum][0])
                    angI = Masks['Rings'][itemNum][0] - t/2.
                    angO = Masks['Rings'][itemNum][0] + t/2.
                    Masks['Rings'][itemNum][1] = t
                (x1,y1),(x2,y2) = ComputeArc(angI,angO,wave)
                pI,pO = G2frame.ringList[pick.itemNumber]
                pI.set_data((x1,y1))
                pO.set_data((x2,y2))
                Page.figure.gca().draw_artist(pI)
                Page.figure.gca().draw_artist(pO)
            elif pickType.startswith('Arc'):
                wave = Data['wavelength']
                itemNum = G2frame.itemPicked.itemNumber
                tth,azm,thick = Masks['Arcs'][itemNum]
                tthN,azmN,D,dsp = G2img.GetTthAzmDsp(Xpos,Ypos,Data)
                if event.button == 1:
                    if pickType == 'ArcInner':
                        angO = angI = tthN
                        angO += thick
                        off = 0
                        Masks['Arcs'][itemNum][0] = (angO + angI)/2
                    elif pickType == 'ArcOuter':
                        angO = angI = tthN
                        angI -= thick
                        off = 0
                        Masks['Arcs'][itemNum][0] = (angO + angI)/2
                    elif pickType == 'ArcLower':
                        angO = tth + thick/2
                        angI = tth - thick/2
                        off = azmN - azm[0]
                    elif pickType == 'ArcUpper':
                        angO = tth + thick/2
                        angI = tth - thick/2
                        off = azmN - azm[1]
                    azm[0] += off
                    azm[1] += off
                elif event.button == 3:
                    if pickType == 'ArcInner' or pickType == 'ArcOuter':
                        t = 2*abs(tthN - tth)
                        angI = tth - t/2.
                        angO = tth + t/2.
                        Masks['Arcs'][itemNum][2] = t
                        off = 0
                    elif pickType == 'ArcLower':
                        angO = tth + thick/2
                        angI = tth - thick/2
                        off = azmN - azm[0]
                    elif pickType == 'ArcUpper':
                        angO = tth + thick/2
                        angI = tth - thick/2
                        off = azmN - azm[1]
                    newRange = azm[1] - azm[0] - 2*off
                    if newRange < 2 or newRange > 358: 
                        return # don't let the azimuthal range get too small or large
                    azm[0] += off
                    azm[1] -= off
                (x1,y1),(x2,y2) = ComputeArc(angI,angO,wave,*azm)
                pI,pO,pL,pU = G2frame.arcList[pick.itemNumber]
                pI.set_data((x2,y2))
                pO.set_data((x1,y1))
                pL.set_data(([x1[0],x2[0]],[y1[0],y2[0]]))
                pU.set_data(([x1[-1],x2[-1]],[y1[-1],y2[-1]]))
                Page.figure.gca().draw_artist(pI)
                Page.figure.gca().draw_artist(pO)
                Page.figure.gca().draw_artist(pL)
                Page.figure.gca().draw_artist(pU)
            elif pickType == 'Polygon':
                # respond to drag
                polygon = Masks['Polygons'][pick.itemNumber][:]
                UpdatePolygon(pick,event,polygon)
                xl,yl = np.hsplit(np.array(polygon),2)
                artist = Plot.plot(xl,yl,'r+')[0] # points
                Page.figure.gca().add_artist(artist)
                artist = G2frame.polyList[pick.itemNumber]
                artist.set_data((xl,yl)) # lines
                Page.figure.gca().draw_artist(artist)
            elif pickType == 'Frame':
                polygon = Masks['Frames'][:]
                UpdatePolygon(pick,event,polygon)
                xl,yl = np.hsplit(np.array(polygon),2)
                artist = Plot.plot(xl,yl,'g+')[0] # points
                Page.figure.gca().add_artist(artist)
                artist = G2frame.frameArtist
                artist.set_data((xl,yl)) # lines
                Page.figure.gca().draw_artist(artist)
            else: # non-dragable object
                return
            Page.canvas.blit(Page.figure.gca().bbox)

        if G2frame.itemPicked is not None: return
        if G2frame.PatternTree.GetItemText(G2frame.PickId) == 'Image Controls':
            G2frame.itemPicked = pick = event.artist
            G2frame.mousePicked = event.mouseevent
            # prepare to animate move of integration ranges
            Page = G2frame.G2plotNB.nb.GetPage(plotNum)
            saveLinestyle = pick.get_linestyle()
            pick.set_linestyle(':') # set line as dotted
            Page.figure.gca()
            Page.canvas.draw() # refresh without dotted line & save bitmap
            savedplot = Page.canvas.copy_from_bbox(Page.figure.gca().bbox)
            G2frame.cid = Page.canvas.mpl_connect('motion_notify_event', OnDragIntBound)
            pick.set_linestyle(saveLinestyle) # back to original
        elif G2frame.PatternTree.GetItemText(G2frame.PickId) == 'Masks':
            # prepare to animate dragging of mask
            G2frame.itemPicked = pick = event.artist
            G2frame.mousePicked = event.mouseevent
            XposBeforeDrag,YposBeforeDrag = [event.mouseevent.xdata,event.mouseevent.ydata]
            #GSASIIpath.IPyBreak()
            Page = G2frame.G2plotNB.nb.GetPage(plotNum)
            try:
                pickType = pick.itemType
            except: # should not happen anymore
                pickType = '?'
            if pickType == 'Spot':
                pl = [pick,]
            elif pickType.startswith('Ring'):
                pl = G2frame.ringList[pick.itemNumber]
            elif pickType.startswith('Arc'):
                pl = G2frame.arcList[pick.itemNumber]
            elif pickType == 'Polygon':
                pl = [G2frame.polyList[pick.itemNumber]]
            elif pickType == 'Frame':
                pl = [G2frame.frameArtist,]
            else:
                print('picktype {} should not happen!'.format(pickType))
                GSASIIpath.IPyBreak()
            saveLinestyle = [p.get_linestyle() for p in pl]
            for p in pl: p.set_linestyle('dotted') # set line as dotted
            Page.canvas.draw() # refresh without dotted line & save bitmap
            savedplot = Page.canvas.copy_from_bbox(Page.figure.gca().bbox)
            G2frame.cid = Page.canvas.mpl_connect('motion_notify_event', OnDragMask)
            for p,s in zip(pl,saveLinestyle): p.set_linestyle(s) # set back to original

    def OnImRelease(event):
        '''Called when the mouse is released inside an image plot window
        '''
        try:
            treeItem = G2frame.PatternTree.GetItemText(G2frame.PickId)
        except TypeError:
            return
        new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('2D Powder Image','mpl',newImage=False)
        if G2frame.cid is not None:         # if there is a drag connection, delete it
            Page.canvas.mpl_disconnect(G2frame.cid)
            G2frame.cid = None
        if treeItem not in ['Image Controls','Masks','Stress/Strain']:
            return
        pixelSize = Data['pixelSize']
        scalex = 1000./pixelSize[0]
        scaley = 1000./pixelSize[1]
#        pixLimit = Data['pixLimit']    #can be too tight
        pixLimit = 20       #this makes the search box 40x40 pixels
        if G2frame.itemPicked is None and treeItem == 'Image Controls' and len(G2frame.ImageZ):
            # nothing being dragged, add calibration point (left mouse) or launch calibration (right)
            Xpos = event.xdata
            if not (Xpos and G2frame.ifGetRing):                   #got point out of frame
                return
            Ypos = event.ydata
            if Ypos and not Page.toolbar._active:         #make sure zoom/pan not selected
                if event.button == 1:
                    Xpix = Xpos*scalex
                    Ypix = Ypos*scaley
                    xpos,ypos,I,J = G2img.ImageLocalMax(G2frame.ImageZ,pixLimit,Xpix,Ypix)
                    if I and J:
                        xpos += .5                              #shift to pixel center
                        ypos += .5
                        xpos /= scalex                          #convert to mm
                        ypos /= scaley
                        Data['ring'].append([xpos,ypos])
                elif event.button == 3:
                    G2frame.dataFrame.GetStatusBar().SetStatusText('Calibrating...',0)
                    if G2img.ImageCalibrate(G2frame,Data):
                        G2frame.dataFrame.GetStatusBar().SetStatusText('Calibration successful - Show ring picks to check',0)
                        print 'Calibration successful'
                    else:
                        G2frame.dataFrame.GetStatusBar().SetStatusText('Calibration failed - Show ring picks to diagnose',0)
                        print 'Calibration failed'
                    G2frame.ifGetRing = False
                    G2imG.UpdateImageControls(G2frame,Data,Masks)
                    return
                wx.CallAfter(PlotImage,G2frame,newImage=False)
            return
        elif G2frame.MaskKey and treeItem == 'Masks':
            # nothing being dragged, create a new mask
            Xpos,Ypos = [event.xdata,event.ydata]
            if not Xpos or not Ypos or Page.toolbar._active:  #got point out of frame or zoom/pan selected
                return
            if G2frame.MaskKey == 's':
                if event.button == 3:
                    ToggleMultiSpotMask(G2frame)
                else:
                    d = GSASIIpath.GetConfigValue('Spot_mask_diameter',1.0)
                    spot = [Xpos,Ypos,d]
                    Masks['Points'].append(spot)
                    artist = Circle((Xpos,Ypos),radius=spot[2]/2,fc='none',ec='r',picker=3)
                    Page.figure.gca().add_artist(artist)
                    artist.itemNumber = len(Masks['Points'])-1
                    artist.itemType = 'Spot'
                    G2imG.UpdateMasks(G2frame,Masks)
                    Page.canvas.draw()
                return 
            elif G2frame.MaskKey == 's':
                if event.button == 1:
                    d = GSASIIpath.GetConfigValue('Spot_mask_diameter',1.0)
                    spot = [Xpos,Ypos,d]
                    Masks['Points'].append(spot)
                    G2imG.UpdateMasks(G2frame,Masks)
                G2frame.MaskKey = ''
                wx.CallAfter(PlotImage,G2frame,newImage=True)
                return
            elif G2frame.MaskKey == 'r':
                if event.button == 1:
                    tth = G2img.GetTth(Xpos,Ypos,Data)
                    t = GSASIIpath.GetConfigValue('Ring_mask_thickness',0.1)                
                    Masks['Rings'].append([tth,t])
                    G2imG.UpdateMasks(G2frame,Masks)
                G2frame.MaskKey = ''                
                wx.CallAfter(PlotImage,G2frame,newImage=True)
                return
            elif G2frame.MaskKey == 'a':
                if event.button == 1:
                    tth,azm = G2img.GetTthAzm(Xpos,Ypos,Data)
                    azm = int(azm)                
                    t = GSASIIpath.GetConfigValue('Ring_mask_thickness',0.1)                
                    a = GSASIIpath.GetConfigValue('Arc_mask_azimuth',10.0)                
                    Masks['Arcs'].append([tth,[azm-a/2.,azm+a/2.],t])
                    G2imG.UpdateMasks(G2frame,Masks)
                G2frame.MaskKey = ''
                wx.CallAfter(PlotImage,G2frame,newImage=True)
                return
            elif G2frame.MaskKey =='p' or G2frame.MaskKey =='f':
                if G2frame.MaskKey =='p':
                    polygon = Masks['Polygons'][-1]
                    color = 'r'
                    lbl = 'Polygon'
                else:
                    polygon = Masks['Frames']
                    color = 'g'
                    lbl = 'Frame'
                if event.button == 3: # close the polygon/frame
                    if len(polygon) <= 2: # too few points
                        if G2frame.MaskKey =='p':
                            del Masks['Polygons'][-1]
                        else:
                            Masks['Frames'] = []
                        G2G.G2MessageBox(G2frame.G2plotNB,lbl+' deleted -- not enough points',
                                         'too few points')
                    else:
                        polygon.append(polygon[0][:])
                        # G2frame.G2plotNB.status.SetStatusText('Polygon closed',) # BHT: never gets seen
                    G2frame.MaskKey = ''
                    G2imG.UpdateMasks(G2frame,Masks)
                    wx.CallAfter(PlotImage,G2frame,newImage=True)
                    return
                else:
                    G2frame.G2plotNB.status.SetStatusText('New '+lbl+' point: %.1f,%.1f'%(Xpos,Ypos),1)
                    if len(polygon):
                        xpr,ypr = polygon[-1]
                        Plot.plot((xpr,Xpos),(ypr,Ypos),color)
                    Plot.plot(Xpos,Ypos,color+'+')
                    Page.canvas.draw()
                    polygon.append([Xpos,Ypos])
                    #G2imG.UpdateMasks(G2frame,Masks)
                    return
            G2imG.UpdateMasks(G2frame,Masks)
            wx.CallAfter(PlotImage,G2frame,newImage=False)
        elif treeItem == 'Stress/Strain' and G2frame.StrainKey:
            Xpos,Ypos = [event.xdata,event.ydata]
            if not Xpos or not Ypos or Page.toolbar._active:  #got point out of frame or zoom/pan selected
                return
            dsp = G2img.GetDsp(Xpos,Ypos,Data)
            StrSta['d-zero'].append({'Dset':dsp,'Dcalc':0.0,'pixLimit':10,'cutoff':0.5,
                'ImxyObs':[[],[]],'ImtaObs':[[],[]],'ImtaCalc':[[],[]],'Emat':[1.0,1.0,1.0]})
            R,r = G2img.MakeStrStaRing(StrSta['d-zero'][-1],G2frame.ImageZ,Data)
            if not len(R):
                del StrSta['d-zero'][-1]
                G2frame.ErrorDialog('Strain peak selection','WARNING - No points found for this ring selection')
            StrSta['d-zero'] = G2mth.sortArray(StrSta['d-zero'],'Dset',reverse=True)
            G2frame.StrainKey = ''
            G2imG.UpdateStressStrain(G2frame,StrSta)
            wx.CallAfter(PlotImage,G2frame,newPlot=False)            
        else:   # start here after dragging of integration range lines or a mask
            Xpos,Ypos = [event.xdata,event.ydata]
            if not Xpos or not Ypos or Page.toolbar._active:  #got point out of frame or zoom/pan selected
                return
            tth,azm,dsp = G2img.GetTthAzmDsp(Xpos,Ypos,Data)[:3]
            itemPicked = str(G2frame.itemPicked)
            try:
                pickType = G2frame.itemPicked.itemType
            except:
                pickType = '?'            
            if G2frame.ifGetRing:                          #delete a calibration ring pick
                xypos = [Xpos,Ypos]
                rings = Data['ring']
                for ring in rings:
                    if np.allclose(ring,xypos,.01,0):
                        rings.remove(ring)
            elif 'Line2D' in itemPicked and treeItem == 'Image Controls':
                if 'line1' in itemPicked:
                    Data['IOtth'][0] = max(tth,0.001)
                elif 'line2' in itemPicked:
                    Data['IOtth'][1] = tth
                elif 'line3' in itemPicked:
                    Data['LRazimuth'][0] = int(azm)
                elif 'line4' in itemPicked and not Data['fullIntegrate']:
                    Data['LRazimuth'][1] = int(azm)

                Data['LRazimuth'][0] %= 360
                Data['LRazimuth'][1] %= 360
                if Data['LRazimuth'][0] > Data['LRazimuth'][1]:
                    Data['LRazimuth'][1] += 360                        
                if Data['fullIntegrate']:
                    Data['LRazimuth'][1] = Data['LRazimuth'][0]+360

                if  Data['IOtth'][0] > Data['IOtth'][1]:
                    Data['IOtth'][0],Data['IOtth'][1] = Data['IOtth'][1],Data['IOtth'][0]

                if Data['binType'] == 'Q':
                    wave = Data['wavelength']
                    IOtth = [4.*math.pi*sind(Data['IOtth'][0]/2.)/wave,4.*math.pi*sind(Data['IOtth'][1]/2.)/wave]
                    G2frame.InnerTth.SetValue(IOtth[0])
                    G2frame.OuterTth.SetValue(IOtth[1])
                else:
                    G2frame.InnerTth.SetValue(Data['IOtth'][0])
                    G2frame.OuterTth.SetValue(Data['IOtth'][1])
                G2frame.Lazim.SetValue(Data['LRazimuth'][0])
                G2frame.Razim.SetValue(Data['LRazimuth'][1])
            elif pickType == "Spot" and treeItem == 'Masks':
                # update the selected circle mask with the last drawn values
                spotnum = G2frame.itemPicked.itemNumber
                Masks['Points'][spotnum] = list(G2frame.itemPicked.center) + [
                    2.*G2frame.itemPicked.radius]
                G2imG.UpdateMasks(G2frame,Masks)
            elif pickType.startswith('Ring') and treeItem == 'Masks':
                G2imG.UpdateMasks(G2frame,Masks) # changes saved during animation
            elif pickType.startswith('Arc') and treeItem == 'Masks':
                G2imG.UpdateMasks(G2frame,Masks) # changes saved during animation
            elif pickType == 'Polygon' and treeItem == 'Masks':
                polygon = Masks['Polygons'][G2frame.itemPicked.itemNumber]
                UpdatePolygon(G2frame.itemPicked,event,polygon)
                G2imG.UpdateMasks(G2frame,Masks)
            elif pickType == 'Frame' and treeItem == 'Masks':
                UpdatePolygon(G2frame.itemPicked,event,Masks['Frames'])
                G2imG.UpdateMasks(G2frame,Masks)
            else: # nothing was done, nothing was changed, don't replot
                G2frame.itemPicked = None
                return 
            wx.CallAfter(PlotImage,G2frame,newImage=True)
            G2frame.itemPicked = None
            
    # PlotImage execution starts here
    if not len(G2frame.ImageZ):
        return
    xylim = []
    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('2D Powder Image','mpl',newImage=newImage)
    if newImage:
        G2frame.MaskKey = '' # subtitle will be removed, so turn off mode
    if not new:
        if not newPlot:
            xylim = lim
    else:
        Page.canvas.mpl_connect('key_press_event', OnImPlotKeyPress)
        Page.canvas.mpl_connect('motion_notify_event', OnImMotion)
        Page.canvas.mpl_connect('pick_event', OnImPick)
        Page.canvas.mpl_connect('button_release_event', OnImRelease)
    Page.Choice = None
    Title = G2frame.PatternTree.GetItemText(G2frame.Image)[4:]
    G2frame.G2plotNB.status.DestroyChildren()
    if G2frame.logPlot:
        Title = 'log('+Title+')'
    Plot.set_title(Title)
    try:
        if G2frame.PatternTree.GetItemText(G2frame.PickId) in ['Image Controls',]:
            Page.Choice = (' key press','l: log(I) on','d: set dmin','x: flip x','y: flip y',)
            if G2frame.logPlot:
                Page.Choice[1] = 'l: log(I) off'
            Page.keyPress = OnImPlotKeyPress
        elif G2frame.PatternTree.GetItemText(G2frame.PickId) in ['Masks',]:
            Page.Choice = [' key press','l: log(I) on','a: arc mask','r: ring mask',
                'p: polygon mask','f: frame mask',
                't: add spot mask at mouse position']
            Page.Choice.append('s: start multiple spot mask mode') # this must be the last choice
            if G2frame.logPlot:
                Page.Choice[1] = 'l: log(I) off'
            Page.keyPress = OnImPlotKeyPress
        elif G2frame.PatternTree.GetItemText(G2frame.PickId) in ['Stress/Strain',]:
            Page.Choice = (' key press','a: add new ring',)
            Page.keyPress = OnImPlotKeyPress
    except TypeError:
        pass
    size,imagefile,imagetag = G2frame.PatternTree.GetImageLoc(G2frame.Image)

    imScale = 1
    maxpix = 2048
    if len(G2frame.ImageZ) > maxpix:
        imScale = len(G2frame.ImageZ)/maxpix
    sizexy = Data['size']
    pixelSize = Data['pixelSize']
    Xmax = sizexy[0]*pixelSize[0]/1000.
    Ymax = sizexy[1]*pixelSize[1]/1000.
    xlim = (0,Xmax)
    ylim = (Ymax,0)
    Imin,Imax = Data['range'][1]
    acolor = mpl.cm.get_cmap(Data['color'])
    xcent,ycent = Data['center']
    Plot.set_xlabel('Image x-axis, mm',fontsize=12)
    Plot.set_ylabel('Image y-axis, mm',fontsize=12)
    #do threshold mask - "real" mask - others are just bondaries
    Zlim = Masks['Thresholds'][1]
    wx.BeginBusyCursor()
    try:
        if newImage:
            Imin,Imax = Data['range'][1]
            MA = ma.masked_greater(ma.masked_less(G2frame.ImageZ,Zlim[0]),Zlim[1])
            MaskA = ma.getmaskarray(MA)
            A = G2img.ImageCompress(MA,imScale)
            AM = G2img.ImageCompress(MaskA,imScale)
            if G2frame.logPlot:
                A = np.where(A>Imin,np.where(A<Imax,A,0),0)
                A = np.where(A>0,np.log(A),0)
                AM = np.where(AM>0,np.log(AM),0)
                Imin,Imax = [np.amin(A),np.amax(A)]
            Plot.imshow(AM,aspect='equal',cmap='Reds',
                interpolation='nearest',vmin=0,vmax=2,extent=[0,Xmax,Ymax,0])
            Page.ImgObj = Plot.imshow(A,aspect='equal',cmap=acolor,
                interpolation='nearest',vmin=Imin,vmax=Imax,extent=[0,Xmax,Ymax,0])
            
        Plot.plot(xcent,ycent,'x')
        #G2frame.PatternTree.GetItemText(item)
        if Data['showLines']: # draw integration range arc/circles/lines
            LRAzim = Data['LRazimuth']                  #NB: integers
            Nazm = Data['outAzimuths']
            delAzm = float(LRAzim[1]-LRAzim[0])/Nazm
            AzmthOff = Data['azmthOff']
            IOtth = Data['IOtth']
            wave = Data['wavelength']
            dspI = wave/(2.0*sind(IOtth[0]/2.0))
            ellI = G2img.GetEllipse(dspI,Data)           #=False if dsp didn't yield an ellipse (ugh! a parabola or a hyperbola)
            dspO = wave/(2.0*sind(IOtth[1]/2.0))
            ellO = G2img.GetEllipse(dspO,Data)           #Ditto & more likely for outer ellipse
            Azm = np.arange(LRAzim[0],LRAzim[1]+1.)-AzmthOff
            if ellI:
                xyI = []
                for azm in Azm:
                    xy = G2img.GetDetectorXY(dspI,azm,Data)
                    if np.any(xy):
                        xyI.append(xy)
                if len(xyI):
                    xyI = np.array(xyI)
                    arcxI,arcyI = xyI.T
                    Plot.plot(arcxI,arcyI,picker=3)
            if ellO:
                xyO = []
                for azm in Azm:
                    xy = G2img.GetDetectorXY(dspO,azm,Data)
                    if np.any(xy):
                        xyO.append(xy)
                if len(xyO):
                    xyO = np.array(xyO)
                    arcxO,arcyO = xyO.T                
                    Plot.plot(arcxO,arcyO,picker=3)
            if ellO and ellI:
                Plot.plot([arcxI[0],arcxO[0]],[arcyI[0],arcyO[0]],picker=3)
                Plot.plot([arcxI[-1],arcxO[-1]],[arcyI[-1],arcyO[-1]],picker=3)
            for i in range(Nazm):
                cake = LRAzim[0]+i*delAzm-AzmthOff
                if Data.get('centerAzm',False):
                    cake += delAzm/2.
                ind = np.searchsorted(Azm,cake)
                Plot.plot([arcxI[ind],arcxO[ind]],[arcyI[ind],arcyO[ind]],color='k',dashes=(5,5))
                    
        if G2frame.PickId and G2frame.PatternTree.GetItemText(G2frame.PickId) in ['Image Controls',]:
            for xring,yring in Data['ring']:
                Plot.plot(xring,yring,'r+',picker=3)
            if Data['setRings']:
                N = 0
                for ring in Data['rings']:
                    xring,yring = np.array(ring).T[:2]
                    Plot.plot(xring,yring,'.',color=colors[N%6])
                    N += 1
            for ellipse in Data['ellipses']:      #what about hyperbola?
                cent,phi,[width,height],col = ellipse
                if width > 0:       #ellipses
                    Plot.add_artist(Ellipse([cent[0],cent[1]],2*width,2*height,phi,ec=col,fc='none'))
                    Plot.text(cent[0],cent[1],'+',color=col,ha='center',va='center')
        if G2frame.PickId and G2frame.PatternTree.GetItemText(G2frame.PickId) in ['Stress/Strain',]:
            for N,ring in enumerate(StrSta['d-zero']):
                xring,yring = ring['ImxyObs']
                Plot.plot(xring,yring,colors[N%6]+'.')
        # display the Masks
        if 'Frames' not in Masks: Masks['Frames'] = []  # patch
        for i,spot in enumerate(Masks['Points']):   # drawing spot masks
            if len(spot):
                x,y,d = spot
                artist = Circle((x,y),radius=d/2,fc='none',ec='r',picker=3)
                Plot.add_artist(artist)
                artist.itemNumber = i
                artist.itemType = 'Spot'
                
        G2frame.ringList = []
        for iring,ring in enumerate(Masks['Rings']):    # drawing spot masks
            if ring:
                tth,thick = ring
                wave = Data['wavelength']
                (x1,y1),(x2,y2) = ComputeArc(tth-thick/2.,tth+thick/2.,wave)
                artistO, = Plot.plot(x1,y1,'r',picker=3)  
                artistO.itemNumber = iring
                artistO.itemType = 'RingOuter'
                artistI, = Plot.plot(x2,y2,'r',picker=3)
                artistI.itemNumber = iring
                artistI.itemType = 'RingInner'
                G2frame.ringList.append([artistI,artistO])
                
        G2frame.arcList = []
        for iarc,arc in enumerate(Masks['Arcs']):      # drawing arc masks
            if arc:
                tth,azm,thick = arc           
                wave = Data['wavelength']
                (x1,y1),(x2,y2) = ComputeArc(tth-thick/2.,tth+thick/2.,wave,azm[0],azm[1])
                arcList = []
                arcList.append(Plot.plot(x2,y2,'r',picker=3)[0]) # 'inner'
                arcList[-1].itemNumber = iarc
                arcList[-1].itemType = 'ArcInner'
                arcList.append(Plot.plot(x1,y1,'r',picker=3)[0]) # 'outer'            
                arcList[-1].itemNumber = iarc
                arcList[-1].itemType = 'ArcOuter'          
                arcList.append(Plot.plot([x1[0],x2[0]],[y1[0],y2[0]],'r',picker=3)[0]) # 'lower'
                arcList[-1].itemNumber = iarc
                arcList[-1].itemType = 'ArcLower'
                arcList.append(Plot.plot([x1[-1],x2[-1]],[y1[-1],y2[-1]],'r',picker=3)[0]) # 'upper'
                arcList[-1].itemNumber = iarc
                arcList[-1].itemType = 'ArcUpper'
                G2frame.arcList.append(arcList)
                
        G2frame.polyList = []
        for ipoly,polygon in enumerate(Masks['Polygons']):
            if not polygon: continue # ignore if empty 
            if polygon[0] != polygon[-1]:
                print('Closing polygon {}'.format(ipoly))
                polygon.append(polygon[0][:])
            xl,yl = np.hsplit(np.array(polygon),2)
            G2frame.polyList.append(Plot.plot(xl,yl,'r')[0])            # line
            for i,(x,y) in enumerate(zip(xl[:-1],yl[:-1])):
                artist = Plot.plot(x,y,'r+',picker=10)[0] # point (plus sign)
                artist.itemNumber = ipoly
                artist.itemType = 'Polygon'
                artist.pointNumber = i
                    
        G2frame.frameArtist = []
        if Masks['Frames']:
            polygon = Masks['Frames']
            if polygon[0] != polygon[-1]:
                print('Closing frame mask')
                polygon.append(polygon[0][:])
            xl,yl = np.hsplit(np.array(polygon),2)
            G2frame.frameArtist = Plot.plot(xl,yl,'g')[0]
            for i,(x,y) in enumerate(zip(xl[:-1],yl[:-1])):
                artist = Plot.plot(x,y,'g+',picker=10)[0] # point (plus sign)
                artist.itemType = 'Frame'
                artist.pointNumber = i
        if newImage:
            Page.figure.colorbar(Page.ImgObj)
        Plot.set_xlim(xlim)
        Plot.set_ylim(ylim)
        if Data['invert_x']:
            Plot.invert_xaxis()
        if Data['invert_y']:
            Plot.invert_yaxis()
        if not newPlot and xylim:
            Page.toolbar.push_current()
            Plot.set_xlim(xylim[0])
            Plot.set_ylim(xylim[1])
            xylim = []
            Page.toolbar.push_current()
            Page.toolbar.draw()
            # patch for wx 2.9 on Mac, to force a redraw
            i,j= wx.__version__.split('.')[0:2]
            if int(i)+int(j)/10. > 2.8 and 'wxOSX' in wx.PlatformInfo:
                Page.canvas.draw()
        else:
            Page.canvas.draw()
    finally:
        wx.EndBusyCursor()
    
################################################################################
##### PlotIntegration
################################################################################
            
def PlotIntegration(G2frame,newPlot=False,event=None):
    '''Plot of 2D image after image integration with 2-theta and azimuth as coordinates
    '''
            
    def OnMotion(event):
        Page.canvas.SetToolTipString('')
        Page.canvas.SetCursor(wx.CROSS_CURSOR)
        azm = event.ydata
        tth = event.xdata
        if azm and tth:
            G2frame.G2plotNB.status.SetStatusText(\
                'Detector 2-th =%9.3fdeg, azm = %7.2fdeg'%(tth,azm),1)
                                
    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('2D Integration','mpl')
    if not new:
        if not newPlot:
            xylim = lim
    else:
        Page.canvas.mpl_connect('motion_notify_event', OnMotion)
        Page.views = False
    Page.Choice = None
        
    Data = G2frame.PatternTree.GetItemPyData(
        G2gd.GetPatternTreeItemId(G2frame,G2frame.Image, 'Image Controls'))
    image = G2frame.Integrate[0]
    xsc = G2frame.Integrate[1]
    ysc = G2frame.Integrate[2]
    Imin,Imax = Data['range'][1]
    acolor = mpl.cm.get_cmap(Data['color'])
    Plot.set_title(G2frame.PatternTree.GetItemText(G2frame.Image)[4:])
    Plot.set_ylabel('azimuth',fontsize=12)
    Plot.set_xlabel('2-theta',fontsize=12)
    Img = Plot.imshow(image,cmap=acolor,vmin=Imin,vmax=Imax,interpolation='nearest', \
        extent=[ysc[0],ysc[-1],xsc[-1],xsc[0]],aspect='auto')
    Page.figure.colorbar(Img)
#    if Data['ellipses']:            
#        for ellipse in Data['ellipses']:
#            x,y = np.array(G2img.makeIdealRing(ellipse[:3])) #skip color
#            tth,azm = G2img.GetTthAzm(x,y,Data)
##            azm = np.where(azm < 0.,azm+360,azm)
#            Plot.plot(tth,azm,'b,')
    if not newPlot:
        Page.toolbar.push_current()
        Plot.set_xlim(xylim[0])
        Plot.set_ylim(xylim[1])
        xylim = []
        Page.toolbar.push_current()
        Page.toolbar.draw()
    else:
        Page.canvas.draw()
                
################################################################################
##### PlotTRImage
################################################################################
            
def PlotTRImage(G2frame,tax,tay,taz,newPlot=False):
    '''a test plot routine - not normally used
    ''' 
            
    def OnMotion(event):
        Page.canvas.SetToolTipString('')
        Page.canvas.SetCursor(wx.CROSS_CURSOR)
        azm = event.xdata
        tth = event.ydata
        if azm and tth:
            G2frame.G2plotNB.status.SetStatusText(\
                'Detector 2-th =%9.3fdeg, azm = %7.2fdeg'%(tth,azm),1)
                                
    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('2D Transformed Powder Image','mpl')
    if not new:
        if not newPlot:
            xylim = lim
    else:
        Page.canvas.mpl_connect('motion_notify_event', OnMotion)
        Page.views = False
    Page.Choice = None
    Data = G2frame.PatternTree.GetItemPyData(
        G2gd.GetPatternTreeItemId(G2frame,G2frame.Image, 'Image Controls'))
    Imin,Imax = Data['range'][1]
    step = (Imax-Imin)/5.
    V = np.arange(Imin,Imax,step)
    acolor = mpl.cm.get_cmap(Data['color'])
    Plot.set_title(G2frame.PatternTree.GetItemText(G2frame.Image)[4:])
    Plot.set_xlabel('azimuth',fontsize=12)
    Plot.set_ylabel('2-theta',fontsize=12)
    Plot.contour(tax,tay,taz,V,cmap=acolor)
    if Data['showLines']:
        IOtth = Data['IOtth']
        if Data['fullIntegrate']:
            LRAzim = [-180,180]
        else:
            LRAzim = Data['LRazimuth']                  #NB: integers
        Plot.plot([LRAzim[0],LRAzim[1]],[IOtth[0],IOtth[0]],picker=True)
        Plot.plot([LRAzim[0],LRAzim[1]],[IOtth[1],IOtth[1]],picker=True)
        if not Data['fullIntegrate']:
            Plot.plot([LRAzim[0],LRAzim[0]],[IOtth[0],IOtth[1]],picker=True)
            Plot.plot([LRAzim[1],LRAzim[1]],[IOtth[0],IOtth[1]],picker=True)
    if Data['setRings']:
        rings = np.concatenate((Data['rings']),axis=0)
        for xring,yring,dsp in rings:
            x,y = G2img.GetTthAzm(xring,yring,Data)
            Plot.plot(y,x,'r+')            
    if Data['ellipses']:            
        for ellipse in Data['ellipses']:
            ring = np.array(G2img.makeIdealRing(ellipse[:3])) #skip color
            x,y = np.hsplit(ring,2)
            tth,azm = G2img.GetTthAzm(x,y,Data)
            Plot.plot(azm,tth,'b,')
    if not newPlot:
        Page.toolbar.push_current()
        Plot.set_xlim(xylim[0])
        Plot.set_ylim(xylim[1])
        xylim = []
        Page.toolbar.push_current()
        Page.toolbar.draw()
    else:
        Page.canvas.draw()
        
################################################################################
##### PlotStructure
################################################################################
            
def PlotStructure(G2frame,data,firstCall=False):
    '''Crystal structure plotting package. Can show structures as balls, sticks, lines,
    thermal motion ellipsoids and polyhedra. Magnetic moments shown as black/red 
    arrows according to spin state
    '''

    def FindPeaksBonds(XYZ):
        rFact = data['Drawing'].get('radiusFactor',0.85)    #data['Drawing'] could be empty!
        Bonds = [[] for x in XYZ]
        for i,xyz in enumerate(XYZ):
            Dx = XYZ-xyz
            dist = np.sqrt(np.sum(np.inner(Dx,Amat)**2,axis=1))
            IndB = ma.nonzero(ma.masked_greater(dist,rFact*2.2))
            for j in IndB[0]:
                Bonds[i].append(Dx[j]/2.)
                Bonds[j].append(-Dx[j]/2.)
        return Bonds

    # PlotStructure initialization here
    ForthirdPI = 4.0*math.pi/3.0
    generalData = data['General']
    cell = generalData['Cell'][1:7]
    Vol = generalData['Cell'][7:8][0]
    Amat,Bmat = G2lat.cell2AB(cell)         #Amat - crystal to cartesian, Bmat - inverse
    Gmat,gmat = G2lat.cell2Gmat(cell)
    A4mat = np.concatenate((np.concatenate((Amat,[[0],[0],[0]]),axis=1),[[0,0,0,1],]),axis=0)
    B4mat = np.concatenate((np.concatenate((Bmat,[[0],[0],[0]]),axis=1),[[0,0,0,1],]),axis=0)
    SGData = generalData['SGData']
    SpnFlp = SGData.get('SpnFlp',[1,])
    atomData = data['Atoms']
    mapPeaks = []
    vdWRadii = generalData['vdWRadii']
    if generalData.get('DisAglCtrls',{}):
        BondRadii = generalData['DisAglCtrls']['BondRadii']
    else:
        BondRadii = generalData['BondRadii']
    drawingData = data['Drawing']
    if not drawingData:
        return          #nothing setup, nothing to draw   
    if 'Map Peaks' in data:
        mapPeaks = np.array(data['Map Peaks'])
        peakMax = 100.
        if len(mapPeaks):
            peakMax = np.max(mapPeaks.T[0])
    if 'Plane' not in drawingData:
        drawingData['Plane'] = [[0,0,1],False,False,0.0,[255,255,0]]
    resRBData = data['RBModels'].get('Residue',[])
    vecRBData = data['RBModels'].get('Vector',[])
    rbAtmDict = {}
    for rbObj in resRBData+vecRBData:
        exclList = ['X' for i in range(len(rbObj['Ids']))]
        rbAtmDict.update(dict(zip(rbObj['Ids'],exclList)))
    testRBObj = data.get('testRBObj',{})
    rbObj = testRBObj.get('rbObj',{})
    MCSA = data.get('MCSA',{})
    mcsaModels = MCSA.get('Models',[])
    if len(mcsaModels) > 1:
        XYZs,Types = G2mth.UpdateMCSAxyz(Bmat,MCSA)
        mcsaXYZ = []
        mcsaTypes = []
        neqv = 0
        for xyz,atyp in zip(XYZs,Types):
            equiv = G2spc.GenAtom(xyz,SGData,All=True,Move=False)
            neqv = max(neqv,len(equiv))
            for item in equiv:
                mcsaXYZ.append(item[0]) 
                mcsaTypes.append(atyp)
        mcsaXYZ = np.array(mcsaXYZ)
        mcsaTypes = np.array(mcsaTypes)
        nuniq = mcsaXYZ.shape[0]/neqv
        mcsaXYZ = np.reshape(mcsaXYZ,(nuniq,neqv,3))
        mcsaTypes = np.reshape(mcsaTypes,(nuniq,neqv))
        cent = np.fix(np.sum(mcsaXYZ+2.,axis=0)/nuniq)-2
        cent[0] = [0,0,0]   #make sure 1st one isn't moved
        mcsaXYZ = np.swapaxes(mcsaXYZ,0,1)-cent[:,np.newaxis,:]
        mcsaTypes = np.swapaxes(mcsaTypes,0,1)
        mcsaXYZ = np.reshape(mcsaXYZ,(nuniq*neqv,3))
        mcsaTypes = np.reshape(mcsaTypes,(nuniq*neqv))                        
        mcsaBonds = FindPeaksBonds(mcsaXYZ)        
    drawAtoms = drawingData.get('Atoms',[])
    mapData = {}
    showBonds = False
    if 'Map' in generalData:
        mapData = generalData['Map']
        showBonds = mapData.get('Show bonds',False)
    Wt = np.array([255,255,255])
    Rd = np.array([255,0,0])
    Gr = np.array([0,255,0])
    wxGreen = wx.Colour(0,255,0)
    Bl = np.array([0,0,255])
    Or = np.array([255,128,0])
    wxOrange = wx.Colour(255,128,0)
    uBox = np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]])
    uEdges = np.array([
        [uBox[0],uBox[1]],[uBox[0],uBox[3]],[uBox[0],uBox[4]],[uBox[1],uBox[2]], 
        [uBox[2],uBox[3]],[uBox[1],uBox[5]],[uBox[2],uBox[6]],[uBox[3],uBox[7]], 
        [uBox[4],uBox[5]],[uBox[5],uBox[6]],[uBox[6],uBox[7]],[uBox[7],uBox[4]]])
    mD = 0.1
    mV = np.array([[[-mD,0,0],[mD,0,0]],[[0,-mD,0],[0,mD,0]],[[0,0,-mD],[0,0,mD]]])
    mapPeakVecs = np.inner(mV,Bmat)

    backColor = np.array(list(drawingData['backColor'])+[0,])
    Bc = np.array(list(drawingData['backColor']))
    uColors = [Rd,Gr,Bl,Wt-Bc, Wt-Bc,Wt-Bc,Wt-Bc,Wt-Bc, Wt-Bc,Wt-Bc,Wt-Bc,Wt-Bc]
    G2frame.tau = 0.
    
    def OnKeyBox(event):
        mode = cb.GetValue()
        if mode in ['jpeg','bmp','tiff',]:
            try:
                import Image as Im
            except ImportError:
                try:
                    from PIL import Image as Im
                except ImportError:
                    print "PIL/pillow Image module not present. Cannot save images without this"
                    raise Exception("PIL/pillow Image module not found")
            projFile = G2frame.GSASprojectfile
            Fname = (os.path.splitext(projFile)[0]+'.'+mode).replace('*','+')
            size = Page.canvas.GetSize()
            GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
            if mode in ['jpeg',]:
                Pix = GL.glReadPixels(0,0,size[0],size[1],GL.GL_RGBA, GL.GL_UNSIGNED_BYTE)
                im = Im.new("RGBA", (size[0],size[1]))
            else:
                Pix = GL.glReadPixels(0,0,size[0],size[1],GL.GL_RGB, GL.GL_UNSIGNED_BYTE)
                im = Im.new("RGB", (size[0],size[1]))
            try:
                im.frombytes(Pix)
            except AttributeError:
                im.fromstring(Pix)
            im = im.transpose(Im.FLIP_TOP_BOTTOM)
            im.save(Fname,mode)
            cb.SetValue(' save as/key:')
            G2frame.G2plotNB.status.SetStatusText('Drawing saved to: '+Fname,1)
        else:
            event.key = cb.GetValue()[0]
            cb.SetValue(' save as/key:')
            wx.CallAfter(OnKey,event)
        Page.canvas.SetFocus() # redirect the Focus from the button back to the plot

    def OnKey(event):           #on key UP!!
        keyBox = False
        try:
            keyCode = event.GetKeyCode()
            if keyCode > 255:
                keyCode = 0
            key = chr(keyCode)
        except AttributeError:       #if from OnKeyBox above
            keyBox = True
            key = str(event.key).upper()
        indx = drawingData['selectedAtoms']
        cx,ct = drawingData['atomPtrs'][:2]
        if key in ['C']:
            drawingData['viewPoint'] = [np.array([.5,.5,.5]),[0,0]]
            drawingData['viewDir'] = [0,0,1]
            drawingData['oldxy'] = []
            V0 = np.array([0,0,1])
            V = np.inner(Amat,V0)
            V /= np.sqrt(np.sum(V**2))
            A = np.arccos(np.sum(V*V0))
            Q = G2mth.AV2Q(A,[0,1,0])
            drawingData['Quaternion'] = Q
            SetViewPointText(drawingData['viewPoint'][0])
            SetViewDirText(drawingData['viewDir'])
            Q = drawingData['Quaternion']
            G2frame.G2plotNB.status.SetStatusText('New quaternion: %.2f+, %.2fi+ ,%.2fj+, %.2fk'%(Q[0],Q[1],Q[2],Q[3]),1)
        elif key in ['N']:
            drawAtoms = drawingData['Atoms']
            if not len(drawAtoms):      #no atoms
                return
            pI = drawingData['viewPoint'][1]
            if not len(pI):
                pI = [0,0]
            if indx:
                pI[0] = indx[pI[1]]
                Tx,Ty,Tz = drawAtoms[pI[0]][cx:cx+3]
                pI[1] += 1
                if pI[1] >= len(indx):
                    pI[1] = 0
            else:
                Tx,Ty,Tz = drawAtoms[pI[0]][cx:cx+3]                
                pI[0] += 1
                if pI[0] >= len(drawAtoms):
                    pI[0] = 0
            drawingData['viewPoint'] = [np.array([Tx,Ty,Tz]),pI]
            SetViewPointText(drawingData['viewPoint'][0])
            G2frame.G2plotNB.status.SetStatusText('View point at atom '+drawAtoms[pI[0]][ct-1]+str(pI),1)
                
        elif key in ['P']:
            drawAtoms = drawingData['Atoms']
            if not len(drawAtoms):      #no atoms
                return
            pI = drawingData['viewPoint'][1]
            if not len(pI):
                pI = [0,0]
            if indx:
                pI[0] = indx[pI[1]]
                Tx,Ty,Tz = drawAtoms[pI[0]][cx:cx+3]
                pI[1] -= 1
                if pI[1] < 0:
                    pI[1] = len(indx)-1
            else:
                Tx,Ty,Tz = drawAtoms[pI[0]][cx:cx+3]                
                pI[0] -= 1
                if pI[0] < 0:
                    pI[0] = len(drawAtoms)-1
            drawingData['viewPoint'] = [np.array([Tx,Ty,Tz]),pI]
            SetViewPointText(drawingData['viewPoint'][0])            
            G2frame.G2plotNB.status.SetStatusText('View point at atom '+drawAtoms[pI[0]][ct-1]+str(pI),1)
        elif key in ['U','D','L','R'] and mapData['Flip'] == True:
            dirDict = {'U':[0,1],'D':[0,-1],'L':[-1,0],'R':[1,0]}
            SetMapRoll(dirDict[key])
            if 'rho' in generalData.get('4DmapData',{}):
                Set4DMapRoll(dirDict[key])
            SetPeakRoll(dirDict[key])
            SetMapPeaksText(mapPeaks)
        elif key in ['M',]and generalData['Modulated']:  #make a movie file
            G2frame.tau = 0.
            for i in range(10):
                G2frame.tau += 0.1
                G2frame.G2plotNB.status.SetStatusText('Modulation tau = %.2f'%(G2frame.tau),1)
                data['Drawing']['Atoms'],Fade = G2mth.ApplyModulation(data,G2frame.tau)     #modifies drawing atom array!          
                SetDrawAtomsText(data['Drawing']['Atoms'])
                G2phG.FindBondsDraw(data)           #rebuild bonds & polygons
                if not np.any(Fade):
                    Fade += 1
                Draw('key down',Fade)
        elif key in ['+','-','=','0'] and generalData['Modulated']:
            if keyBox:
                OnKeyPressed(event)
            return
        Draw('key up')
        
    def OnKeyPressed(event):    #On key down for repeating operation - used to change tau...
        try:
            keyCode = event.GetKeyCode()
            if keyCode > 255:
                keyCode = 0
            key = chr(keyCode)
        except AttributeError:       #if from OnKeyBox above
            key = str(event.key).upper()
        if key in ['+','-','=','0'] and generalData['Modulated']:
            if key == '0':
                G2frame.tau = 0.
            elif key in ['+','=']:
                G2frame.tau += 0.1
            elif key == '-':
                G2frame.tau -= 0.1
            G2frame.tau %= 1.   #force 0-1 range
            G2frame.G2plotNB.status.SetStatusText('Modulation tau = %.2f'%(G2frame.tau),1)
            data['Drawing']['Atoms'],Fade = G2mth.ApplyModulation(data,G2frame.tau)     #modifies drawing atom array!          
            SetDrawAtomsText(data['Drawing']['Atoms'])
            G2phG.FindBondsDraw(data)           #rebuild bonds & polygons
            if not np.any(Fade):
                Fade += 1
            Draw('key down',Fade)
            
    def GetTruePosition(xy,Add=False):
        View = GL.glGetIntegerv(GL.GL_VIEWPORT)
        Proj = GL.glGetDoublev(GL.GL_PROJECTION_MATRIX)
        Model = GL.glGetDoublev(GL.GL_MODELVIEW_MATRIX)
        Zmax = 1.
        if Add:
            Indx = GetSelectedAtoms()
        if G2frame.dataDisplay.GetPageText(getSelection()) == 'Map peaks':
            for i,peak in enumerate(mapPeaks):
                x,y,z = peak[1:4]
                X,Y,Z = GLU.gluProject(x,y,z,Model,Proj,View)
                XY = [int(X),int(View[3]-Y)]
                if np.allclose(xy,XY,atol=10) and Z < Zmax:
                    Zmax = Z
                    try:
                        Indx.remove(i)
                        ClearSelectedAtoms()
                        for id in Indx:
                            SetSelectedAtoms(id,Add)
                    except:
                        SetSelectedAtoms(i,Add)
        else:
            cx = drawingData['atomPtrs'][0]
            for i,atom in enumerate(drawAtoms):
                x,y,z = atom[cx:cx+3]
                X,Y,Z = GLU.gluProject(x,y,z,Model,Proj,View)
                XY = [int(X),int(View[3]-Y)]
                if np.allclose(xy,XY,atol=10) and Z < Zmax:
                    Zmax = Z
                    try:
                        Indx.remove(i)
                        ClearSelectedAtoms()
                        for id in Indx:
                            SetSelectedAtoms(id,Add)
                    except:
                        SetSelectedAtoms(i,Add)
                                       
    def OnMouseDown(event):
        xy = event.GetPosition()
        if event.ShiftDown():
            if event.LeftIsDown():
                GetTruePosition(xy)
            elif event.RightIsDown():
                GetTruePosition(xy,True)
        else:
            drawingData['oldxy'] = list(xy)
        
    def OnMouseMove(event):
        if event.ShiftDown():           #don't want any inadvertant moves when picking
            return
        newxy = event.GetPosition()
                                
        if event.Dragging():
            if event.AltDown() and rbObj:
                if event.LeftIsDown():
                    SetRBRotation(newxy)
                    Q = rbObj['Orient'][0]
                    G2frame.G2plotNB.status.SetStatusText('New quaternion: %.2f+, %.2fi+ ,%.2fj+, %.2fk'%(Q[0],Q[1],Q[2],Q[3]),1)
                elif event.RightIsDown():
                    SetRBTranslation(newxy)
                    Tx,Ty,Tz = rbObj['Orig'][0]
                    G2frame.G2plotNB.status.SetStatusText('New view point: %.4f, %.4f, %.4f'%(Tx,Ty,Tz),1)
                elif event.MiddleIsDown():
                    SetRBRotationZ(newxy)
                    Q = rbObj['Orient'][0]
                    G2frame.G2plotNB.status.SetStatusText('New quaternion: %.2f+, %.2fi+ ,%.2fj+, %.2fk'%(Q[0],Q[1],Q[2],Q[3]),1)
                Draw('move')
            elif not event.ControlDown():
                if event.LeftIsDown():
                    SetRotation(newxy)
                    Q = drawingData['Quaternion']
                    G2frame.G2plotNB.status.SetStatusText('New quaternion: %.2f+, %.2fi+ ,%.2fj+, %.2fk'%(Q[0],Q[1],Q[2],Q[3]),1)
                elif event.RightIsDown():
                    SetTranslation(newxy)
                    Tx,Ty,Tz = drawingData['viewPoint'][0]
                    rho = G2mth.getRho([Tx,Ty,Tz],mapData)
                    G2frame.G2plotNB.status.SetStatusText('New view point: %.4f, %.4f, %.4f; density: %.4f'%(Tx,Ty,Tz,rho),1)
                elif event.MiddleIsDown():
                    SetRotationZ(newxy)
                    Q = drawingData['Quaternion']
                    G2frame.G2plotNB.status.SetStatusText('New quaternion: %.2f+, %.2fi+ ,%.2fj+, %.2fk'%(Q[0],Q[1],Q[2],Q[3]),1)
                Draw('move')
        
    def OnMouseWheel(event):
        if event.ShiftDown():
            return
        drawingData['cameraPos'] += event.GetWheelRotation()/24.
        drawingData['cameraPos'] = max(10,min(500,drawingData['cameraPos']))
        G2frame.G2plotNB.status.SetStatusText('New camera distance: %.2f'%(drawingData['cameraPos']),1)
        page = getSelection()
        if page:
            if G2frame.dataDisplay.GetPageText(page) == 'Draw Options':
                G2frame.dataDisplay.cameraPosTxt.SetLabel('Camera Position: '+'%.2f'%(drawingData['cameraPos']))
                G2frame.dataDisplay.cameraSlider.SetValue(drawingData['cameraPos'])
        Draw('wheel')
        
    def getSelection():
        try:
            return G2frame.dataDisplay.GetSelection()
        except AttributeError:
            G2frame.G2plotNB.status.SetStatusText('Select this from Phase data window!',1)
            return 0
            
    def SetViewPointText(VP):
        page = getSelection()
        if page:
            if G2frame.dataDisplay.GetPageText(page) == 'Draw Options':
                G2frame.dataDisplay.viewPoint.SetValue('%.3f %.3f %.3f'%(VP[0],VP[1],VP[2]))
                
    def SetRBOrigText():
        page = getSelection()
        if page:
            if G2frame.dataDisplay.GetPageText(page) == 'RB Models':
                for i,sizer in enumerate(testRBObj['Sizers']['Xsizers']):
                    sizer.SetValue('%8.5f'%(testRBObj['rbObj']['Orig'][0][i]))
                    
    def SetRBOrienText():
        page = getSelection()
        if page:
            if G2frame.dataDisplay.GetPageText(page) == 'RB Models':
                for i,sizer in enumerate(testRBObj['Sizers']['Osizers']):
                    sizer.SetValue('%8.5f'%(testRBObj['rbObj']['Orient'][0][i]))
                
    def SetViewDirText(VD):
        page = getSelection()
        if page:
            if G2frame.dataDisplay.GetPageText(page) == 'Draw Options':
                G2frame.dataDisplay.viewDir.SetValue('%.3f %.3f %.3f'%(VD[0],VD[1],VD[2]))
                
    def SetMapPeaksText(mapPeaks):
        data['Map Peaks'] = mapPeaks
        page = getSelection()
        if page:
            if G2frame.dataDisplay.GetPageText(page) == 'Map peaks':
                G2frame.MapPeaksTable.SetData(data['Map Peaks'])
                panel = G2frame.dataDisplay.GetPage(page).GetChildren()
                names = [child.GetName() for child in panel]
                try:
                    panel[names.index('GridWindow')].Refresh()
                except ValueError:  #different wx versions!
                    panel[names.index('grid window')].Refresh()
            
    def SetDrawAtomsText(drawAtoms):
        page = getSelection()
        if page:
            if G2frame.dataDisplay.GetPageText(page) == 'Draw Atoms':
                table = G2frame.atomTable.GetData()
                for i,atom in enumerate(drawAtoms):
                    table[i][2:5] = atom[2:5]
                G2frame.atomTable.SetData(table)
                panel = G2frame.dataDisplay.GetPage(page).GetChildren()
                names = [child.GetName() for child in panel]
                try:
                    panel[names.index('GridWindow')].Refresh()
                except ValueError:  #different wx versions!
                    panel[names.index('grid window')].Refresh()
            
    def ClearSelectedAtoms():
        page = getSelection()
        if page:
            if G2frame.dataDisplay.GetPageText(page) == 'Draw Atoms':
                G2frame.dataDisplay.GetPage(page).ClearSelection()      #this is the Atoms grid in Draw Atoms
            elif G2frame.dataDisplay.GetPageText(page) == 'Map peaks':
                G2frame.dataDisplay.GetPage(page).ClearSelection()      #this is the Atoms grid in Atoms
            elif G2frame.dataDisplay.GetPageText(page) == 'Atoms':
                G2frame.dataDisplay.GetPage(page).ClearSelection()      #this is the Atoms grid in Atoms
                
                    
    def SetSelectedAtoms(ind,Add=False):
        page = getSelection()
        if page:
            if G2frame.dataDisplay.GetPageText(page) == 'Draw Atoms':
                G2frame.dataDisplay.GetPage(page).SelectRow(ind,Add)      #this is the Atoms grid in Draw Atoms
            elif G2frame.dataDisplay.GetPageText(page) == 'Map peaks':
                G2frame.dataDisplay.GetPage(page).SelectRow(ind,Add)                  
            elif G2frame.dataDisplay.GetPageText(page) == 'Atoms':
                Id = drawAtoms[ind][-3]
                for i,atom in enumerate(atomData):
                    if atom[-1] == Id:
                        G2frame.dataDisplay.GetPage(page).SelectRow(i)      #this is the Atoms grid in Atoms
                  
    def GetSelectedAtoms():
        page = getSelection()
        Ind = []
        if page:
            if G2frame.dataDisplay.GetPageText(page) == 'Draw Atoms':
                Ind = G2frame.dataDisplay.GetPage(page).GetSelectedRows()      #this is the Atoms grid in Draw Atoms
            elif G2frame.dataDisplay.GetPageText(page) == 'Map peaks':
                Ind = G2frame.dataDisplay.GetPage(page).GetSelectedRows()
            elif G2frame.dataDisplay.GetPageText(page) == 'Atoms':
                Ind = G2frame.dataDisplay.GetPage(page).GetSelectedRows()      #this is the Atoms grid in Atoms
        return Ind
                                       
    def SetBackground():
        R,G,B,A = Page.camera['backColor']
        GL.glClearColor(R,G,B,A)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        
    def SetLights():
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glShadeModel(GL.GL_SMOOTH)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glEnable(GL.GL_LIGHT0)
        GL.glLightModeli(GL.GL_LIGHT_MODEL_TWO_SIDE,0)
        GL.glLightfv(GL.GL_LIGHT0,GL.GL_AMBIENT,[.1,.1,.1,1])
        GL.glLightfv(GL.GL_LIGHT0,GL.GL_DIFFUSE,[.8,.8,.8,1])
#        glLightfv(GL_LIGHT0,GL_SPECULAR,[1,1,1,1])
#        glLightfv(GL_LIGHT0,GL_POSITION,[0,0,1,1])
        
    def GetRoll(newxy,rhoshape):
        Q = drawingData['Quaternion']
        dxy = G2mth.prodQVQ(G2mth.invQ(Q),np.inner(Bmat,newxy+[0,]))
        dxy = np.array(dxy*rhoshape)        
        roll = np.where(dxy>0.5,1,np.where(dxy<-.5,-1,0))
        return roll
                
    def SetMapRoll(newxy):
        rho = generalData['Map']['rho']
        roll = GetRoll(newxy,rho.shape)
        generalData['Map']['rho'] = np.roll(np.roll(np.roll(rho,roll[0],axis=0),roll[1],axis=1),roll[2],axis=2)
        drawingData['oldxy'] = list(newxy)
        
    def Set4DMapRoll(newxy):
        rho = generalData['4DmapData']['rho']
        roll = GetRoll(newxy,rho.shape[:3])
        generalData['4DmapData']['rho'] = np.roll(np.roll(np.roll(rho,roll[0],axis=0),roll[1],axis=1),roll[2],axis=2)
        
    def SetPeakRoll(newxy):
        rho = generalData['Map']['rho']
        roll = GetRoll(newxy,rho.shape)
        steps = 1./np.array(rho.shape)
        dxy = roll*steps
        for peak in mapPeaks:
            peak[1:4] += dxy
            peak[1:4] %= 1.
            peak[4] = np.sqrt(np.sum(np.inner(Amat,peak[1:4])**2))
                
    def SetTranslation(newxy):
#first get translation vector in screen coords.       
        oldxy = drawingData['oldxy']
        if not len(oldxy): oldxy = list(newxy)
        dxy = newxy-oldxy
        drawingData['oldxy'] = list(newxy)
        V = np.array([-dxy[0],dxy[1],0.])
#then transform to rotated crystal coordinates & apply to view point        
        Q = drawingData['Quaternion']
        V = np.inner(Bmat,G2mth.prodQVQ(G2mth.invQ(Q),V))
        Tx,Ty,Tz = drawingData['viewPoint'][0]
        Tx += V[0]*0.01
        Ty += V[1]*0.01
        Tz += V[2]*0.01
        drawingData['viewPoint'][0] =  np.array([Tx,Ty,Tz])
        SetViewPointText([Tx,Ty,Tz])
        
    def SetRBTranslation(newxy):
#first get translation vector in screen coords.       
        oldxy = drawingData['oldxy']
        if not len(oldxy): oldxy = list(newxy)
        dxy = newxy-oldxy
        drawingData['oldxy'] = list(newxy)
        V = np.array([-dxy[0],dxy[1],0.])
#then transform to rotated crystal coordinates & apply to RB origin        
        Q = drawingData['Quaternion']
        V = np.inner(Bmat,G2mth.prodQVQ(G2mth.invQ(Q),V))
        Tx,Ty,Tz = rbObj['Orig'][0]
        Tx -= V[0]*0.01
        Ty -= V[1]*0.01
        Tz -= V[2]*0.01
        rbObj['Orig'][0] =  Tx,Ty,Tz
        SetRBOrigText()
        
    def SetRotation(newxy):
        'Perform a rotation in x-y space due to a left-mouse drag'
    #first get rotation vector in screen coords. & angle increment        
        oldxy = drawingData['oldxy']
        if not len(oldxy): oldxy = list(newxy)
        dxy = newxy-oldxy
        drawingData['oldxy'] = list(newxy)
        V = np.array([dxy[1],dxy[0],0.])
        A = 0.25*np.sqrt(dxy[0]**2+dxy[1]**2)
        if not A: return # nothing changed, nothing to do
    # next transform vector back to xtal coordinates via inverse quaternion
    # & make new quaternion
        Q = drawingData['Quaternion']
        V = G2mth.prodQVQ(G2mth.invQ(Q),np.inner(Bmat,V))
        DQ = G2mth.AVdeg2Q(A,V)
        Q = G2mth.prodQQ(Q,DQ)
        drawingData['Quaternion'] = Q
    # finally get new view vector - last row of rotation matrix
        VD = np.inner(Bmat,G2mth.Q2Mat(Q)[2])
        VD /= np.sqrt(np.sum(VD**2))
        drawingData['viewDir'] = VD
        SetViewDirText(VD)
        
    def SetRotationZ(newxy):                        
#first get rotation vector (= view vector) in screen coords. & angle increment        
        View = GL.glGetIntegerv(GL.GL_VIEWPORT)
        cent = [View[2]/2,View[3]/2]
        oldxy = drawingData['oldxy']
        if not len(oldxy): oldxy = list(newxy)
        dxy = newxy-oldxy
        drawingData['oldxy'] = list(newxy)
        V = drawingData['viewDir']
        A = [0,0]
        A[0] = dxy[1]*.25
        A[1] = dxy[0]*.25
        if newxy[0] > cent[0]:
            A[0] *= -1
        if newxy[1] < cent[1]:
            A[1] *= -1        
# next transform vector back to xtal coordinates & make new quaternion
        Q = drawingData['Quaternion']
        V = np.inner(Amat,V)
        Qx = G2mth.AVdeg2Q(A[0],V)
        Qy = G2mth.AVdeg2Q(A[1],V)
        Q = G2mth.prodQQ(Q,Qx)
        Q = G2mth.prodQQ(Q,Qy)
        drawingData['Quaternion'] = Q

    def SetRBRotation(newxy):
#first get rotation vector in screen coords. & angle increment        
        oldxy = drawingData['oldxy']
        if not len(oldxy): oldxy = list(newxy)
        dxy = newxy-oldxy
        drawingData['oldxy'] = list(newxy)
        V = np.array([dxy[1],dxy[0],0.])
        A = 0.25*np.sqrt(dxy[0]**2+dxy[1]**2)
# next transform vector back to xtal coordinates via inverse quaternion
# & make new quaternion
        Q = rbObj['Orient'][0]              #rotate RB to Cart
        QC = drawingData['Quaternion']      #rotate Cart to drawing
        V = G2mth.prodQVQ(G2mth.invQ(QC),V)
        V = G2mth.prodQVQ(G2mth.invQ(Q),V)
        DQ = G2mth.AVdeg2Q(A,V)
        Q = G2mth.prodQQ(Q,DQ)
        rbObj['Orient'][0] = Q
        SetRBOrienText()
        
    def SetRBRotationZ(newxy):                        
#first get rotation vector (= view vector) in screen coords. & angle increment        
        View = GL.glGetIntegerv(GL.GL_VIEWPORT)
        cent = [View[2]/2,View[3]/2]
        oldxy = drawingData['oldxy']
        if not len(oldxy): oldxy = list(newxy)
        dxy = newxy-oldxy
        drawingData['oldxy'] = list(newxy)
        V = drawingData['viewDir']
        A = [0,0]
        A[0] = dxy[1]*.25
        A[1] = dxy[0]*.25
        if newxy[0] < cent[0]:
            A[0] *= -1
        if newxy[1] > cent[1]:
            A[1] *= -1        
# next transform vector back to RB coordinates & make new quaternion
        Q = rbObj['Orient'][0]              #rotate RB to cart
        V = np.inner(Amat,V)
        V = -G2mth.prodQVQ(G2mth.invQ(Q),V)
        Qx = G2mth.AVdeg2Q(A[0],V)
        Qy = G2mth.AVdeg2Q(A[1],V)
        Q = G2mth.prodQQ(Q,Qx)
        Q = G2mth.prodQQ(Q,Qy)
        rbObj['Orient'][0] = Q
        SetRBOrienText()

    def RenderBox():
        GL.glEnable(GL.GL_COLOR_MATERIAL)
        GL.glLineWidth(2)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA,GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glEnable(GL.GL_LINE_SMOOTH)
        GL.glBegin(GL.GL_LINES)
        for line,color in zip(uEdges,uColors):
            GL.glColor3ubv(color)
            GL.glVertex3fv(line[0])
            GL.glVertex3fv(line[1])
        GL.glEnd()
        GL.glColor4ubv([0,0,0,0])
        GL.glDisable(GL.GL_LINE_SMOOTH)
        GL.glDisable(GL.GL_BLEND)
        GL.glDisable(GL.GL_COLOR_MATERIAL)
        
    def RenderUnitVectors(x,y,z):
        GL.glEnable(GL.GL_COLOR_MATERIAL)
        GL.glLineWidth(2)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA,GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glEnable(GL.GL_LINE_SMOOTH)
        GL.glPushMatrix()
        GL.glTranslate(x,y,z)
        GL.glScalef(1/cell[0],1/cell[1],1/cell[2])
        GL.glBegin(GL.GL_LINES)
        for line,color in zip(uEdges,uColors)[:3]:
            GL.glColor3ubv(color)
            GL.glVertex3fv(-line[1]/2.)
            GL.glVertex3fv(line[1]/2.)
        GL.glEnd()
        GL.glPopMatrix()
        GL.glColor4ubv([0,0,0,0])
        GL.glDisable(GL.GL_LINE_SMOOTH)
        GL.glDisable(GL.GL_BLEND)
        GL.glDisable(GL.GL_COLOR_MATERIAL)
        
    def RenderPlane(plane,color):
        fade = list(color) + [.25,]
        GL.glMaterialfv(GL.GL_FRONT_AND_BACK,GL.GL_AMBIENT_AND_DIFFUSE,fade)
        GL.glShadeModel(GL.GL_FLAT)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA,GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glPushMatrix()
        GL.glShadeModel(GL.GL_SMOOTH)
        GL.glPolygonMode(GL.GL_FRONT_AND_BACK,GL.GL_FILL)
        GL.glFrontFace(GL.GL_CW)
        GL.glBegin(GL.GL_TRIANGLE_FAN)
        for vertex in plane:
            GL.glVertex3fv(vertex)
        GL.glEnd()
        GL.glPopMatrix()
        GL.glDisable(GL.GL_BLEND)
        GL.glShadeModel(GL.GL_SMOOTH)
                
    def RenderSphere(x,y,z,radius,color):
        GL.glMaterialfv(GL.GL_FRONT_AND_BACK,GL.GL_DIFFUSE,color)
        GL.glPushMatrix()
        GL.glTranslate(x,y,z)
        GL.glMultMatrixf(B4mat.T)
        q = GLU.gluNewQuadric()
        GLU.gluSphere(q,radius,20,10)
        GL.glPopMatrix()
        
    def RenderDots(XYZ,RC):
        GL.glEnable(GL.GL_COLOR_MATERIAL)
        XYZ = np.array(XYZ)
        GL.glPushMatrix()
        for xyz,rc in zip(XYZ,RC):
            x,y,z = xyz
            r,c = rc
            GL.glColor3fv(c/255.)
            GL.glPointSize(r*50)
            GL.glBegin(GL.GL_POINTS)
            GL.glVertex3fv(xyz)
            GL.glEnd()
        GL.glPopMatrix()
        GL.glColor4ubv([0,0,0,0])
        GL.glDisable(GL.GL_COLOR_MATERIAL)
        
    def RenderSmallSphere(x,y,z,radius,color):
        GL.glMaterialfv(GL.GL_FRONT_AND_BACK,GL.GL_DIFFUSE,color)
        GL.glPushMatrix()
        GL.glTranslate(x,y,z)
        GL.glMultMatrixf(B4mat.T)
        q = GLU.gluNewQuadric()
        GLU.gluSphere(q,radius,4,2)
        GL.glPopMatrix()
                
    def RenderEllipsoid(x,y,z,ellipseProb,E,R4,color):
        s1,s2,s3 = E
        GL.glMaterialfv(GL.GL_FRONT_AND_BACK,GL.GL_DIFFUSE,color)
        GL.glPushMatrix()
        GL.glTranslate(x,y,z)
        GL.glMultMatrixf(B4mat.T)
        GL.glMultMatrixf(R4.T)
        GL.glEnable(GL.GL_NORMALIZE)
        GL.glScale(s1,s2,s3)
        q = GLU.gluNewQuadric()
        GLU.gluSphere(q,ellipseProb,20,10)
        GL.glDisable(GL.GL_NORMALIZE)
        GL.glPopMatrix()
        
    def RenderBonds(x,y,z,Bonds,radius,color,slice=20):
        GL.glMaterialfv(GL.GL_FRONT_AND_BACK,GL.GL_DIFFUSE,color)
        GL.glPushMatrix()
        GL.glTranslate(x,y,z)
        GL.glMultMatrixf(B4mat.T)
        for bond in Bonds:
            GL.glPushMatrix()
            Dx = np.inner(Amat,bond)
            Z = np.sqrt(np.sum(Dx**2))
            if Z:
                azm = atan2d(-Dx[1],-Dx[0])
                phi = acosd(Dx[2]/Z)
                GL.glRotate(-azm,0,0,1)
                GL.glRotate(phi,1,0,0)
                q = GLU.gluNewQuadric()
                GLU.gluCylinder(q,radius,radius,Z,slice,2)
            GL.glPopMatrix()            
        GL.glPopMatrix()
        
    def RenderMoment(x,y,z,Moment,color,slice=20):
        Dx = 0.5*Moment
        Z = np.sqrt(np.sum(Dx**2))
        if Z:
            GL.glMaterialfv(GL.GL_FRONT_AND_BACK,GL.GL_DIFFUSE,color)
            GL.glPushMatrix()
            GL.glTranslate(x,y,z)
            GL.glMultMatrixf(B4mat.T)
            GL.glTranslate(-Dx[0],-Dx[1],-Dx[2])
            azm = atan2d(-Dx[1],-Dx[0])
            phi = acosd(Dx[2]/Z)
            GL.glRotate(-azm,0,0,1)
            GL.glRotate(phi,1,0,0)
            q = GLU.gluNewQuadric()
            GLU.gluQuadricOrientation(q,GLU.GLU_INSIDE)
            GLU.gluDisk(q,0.,.1,slice,1)
            GLU.gluQuadricOrientation(q,GLU.GLU_OUTSIDE)
            GLU.gluCylinder(q,.1,.1,2.*Z,slice,2)
            GL.glTranslate(0,0,2*Z)
            GLU.gluQuadricOrientation(q,GLU.GLU_INSIDE)
            GLU.gluDisk(q,.1,.2,slice,1)
            GLU.gluQuadricOrientation(q,GLU.GLU_OUTSIDE)
            GLU.gluCylinder(q,.2,0.,.4,slice,2)
            GL.glPopMatrix()            
                
    def RenderLines(x,y,z,Bonds,color):
        GL.glShadeModel(GL.GL_FLAT)
        xyz = np.array([x,y,z])
        GL.glEnable(GL.GL_COLOR_MATERIAL)
        GL.glLineWidth(1)
        GL.glColor3fv(color)
        GL.glPushMatrix()
        GL.glBegin(GL.GL_LINES)
        for bond in Bonds:
            GL.glVertex3fv(xyz)
            GL.glVertex3fv(xyz+bond)
        GL.glEnd()
        GL.glColor4ubv([0,0,0,0])
        GL.glPopMatrix()
        GL.glDisable(GL.GL_COLOR_MATERIAL)
        GL.glShadeModel(GL.GL_SMOOTH)
        
    def RenderPolyhedra(x,y,z,Faces,color):
        GL.glShadeModel(GL.GL_FLAT)
        GL.glPushMatrix()
        GL.glTranslate(x,y,z)
        GL.glMaterialfv(GL.GL_FRONT_AND_BACK,GL.GL_DIFFUSE,color)
        GL.glShadeModel(GL.GL_SMOOTH)
        GL.glMultMatrixf(B4mat.T)
        for face,norm in Faces:
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK,GL.GL_FILL)
            GL.glFrontFace(GL.GL_CW)
            GL.glNormal3fv(norm)
            GL.glBegin(GL.GL_TRIANGLES)
            for vert in face:
                GL.glVertex3fv(vert)
            GL.glEnd()
        GL.glPopMatrix()
        GL.glShadeModel(GL.GL_SMOOTH)

    def RenderMapPeak(x,y,z,color,den):
        GL.glShadeModel(GL.GL_FLAT)
        xyz = np.array([x,y,z])
        GL.glEnable(GL.GL_COLOR_MATERIAL)
        GL.glLineWidth(3)
        GL.glColor3fv(2*color*den/255)
        GL.glPushMatrix()
        GL.glBegin(GL.GL_LINES)
        for vec in mapPeakVecs:
            GL.glVertex3fv(vec[0]+xyz)
            GL.glVertex3fv(vec[1]+xyz)
        GL.glEnd()
        GL.glColor4ubv([0,0,0,0])
        GL.glPopMatrix()
        GL.glDisable(GL.GL_COLOR_MATERIAL)
        GL.glShadeModel(GL.GL_SMOOTH)
        
    def RenderBackbone(Backbone,BackboneColor,radius):
        GL.glPushMatrix()
        GL.glMultMatrixf(B4mat.T)
        GL.glEnable(GL.GL_COLOR_MATERIAL)
        GL.glShadeModel(GL.GL_SMOOTH)
#        gle.gleSetJoinStyle(TUBE_NORM_EDGE | TUBE_JN_ANGLE | TUBE_JN_CAP)
#        gle.glePolyCylinder(Backbone,BackboneColor,radius)
        GL.glPopMatrix()        
        GL.glDisable(GL.GL_COLOR_MATERIAL)
        
    def RenderLabel(x,y,z,label,r,color,matRot):
        '''
        color wx.Colour object
        '''       
        GL.glPushMatrix()
        GL.glTranslate(x,y,z)
        GL.glMultMatrixf(B4mat.T)
        GL.glDisable(GL.GL_LIGHTING)
        GL.glRasterPos3f(0,0,0)
        GL.glMultMatrixf(matRot)
        GL.glRotate(180,1,0,0)             #fix to flip about x-axis
        text = gltext.Text(text=label,font=Font,foreground=color)
        text.draw_text(scale=0.025)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glPopMatrix()
        
    def RenderMap(rho,rhoXYZ,indx,Rok):
        GL.glShadeModel(GL.GL_FLAT)
        cLevel = drawingData['contourLevel']
        XYZ = []
        RC = []
        for i,xyz in enumerate(rhoXYZ):
            if not Rok[i]:
                x,y,z = xyz
                I,J,K = indx[i]
                alpha = 1.0
                if cLevel < 1.:
                    alpha = min(1.0,(abs(rho[I,J,K])/mapData['rhoMax']-cLevel)/(1.-cLevel))
                if rho[I,J,K] < 0.:
                    XYZ.append(xyz)
                    RC.append([0.2*alpha,2*Or])
                else:
                    XYZ.append(xyz)
                    RC.append([0.2*alpha,2*Gr])
        RenderDots(XYZ,RC)
        GL.glShadeModel(GL.GL_SMOOTH)
                            
    def Draw(caller='',Fade=[]):
#useful debug?        
#        if caller:
#            print caller,generalData['Name']
# end of useful debug
        vdWRadii = generalData['vdWRadii']
        mapData = generalData['Map']
        D4mapData = generalData.get('4DmapData',{})
        pageName = ''
        page = getSelection()
        if page:
            pageName = G2frame.dataDisplay.GetPageText(page)
        rhoXYZ = []
        rho = []
        if len(D4mapData.get('rho',[])):        #preferentially select 4D map if there
            rho = D4mapData['rho'][:,:,:,int(G2frame.tau*10)]   #pick current tau 3D slice
        elif len(mapData['rho']):               #ordinary 3D map
            rho = mapData['rho']
        if len(rho):
            VP = drawingData['viewPoint'][0]-np.array([.5,.5,.5])
            contLevel = drawingData['contourLevel']*mapData['rhoMax']
            if 'delt-F' in mapData['MapType'] or 'N' in mapData.get('Type',''):
                rho = ma.array(rho,mask=(np.abs(rho)<contLevel))
            else:
                rho = ma.array(rho,mask=(rho<contLevel))
            steps = 1./np.array(rho.shape)
            incre = np.where(VP>=0,VP%steps,VP%steps-steps)
            Vsteps = -np.array(VP/steps,dtype='i')
            rho = np.roll(np.roll(np.roll(rho,Vsteps[0],axis=0),Vsteps[1],axis=1),Vsteps[2],axis=2)
            indx = np.array(ma.nonzero(rho)).T
            rhoXYZ = indx*steps+VP-incre
            Nc = max(len(rhoXYZ),1)
            rcube = 2000.*Vol/(ForthirdPI*Nc)
            rmax = math.exp(math.log(rcube)/3.)**2
            radius = min(drawingData.get('mapSize',10.)**2,rmax)
            view = drawingData['viewPoint'][0]
            Rok = np.sum(np.inner(Amat,rhoXYZ-view).T**2,axis=1)>radius
        Ind = GetSelectedAtoms()
        VS = np.array(Page.canvas.GetSize())
        aspect = float(VS[0])/float(VS[1])
        cPos = drawingData['cameraPos']
        Zclip = drawingData['Zclip']*cPos/200.
        Q = drawingData['Quaternion']
        Tx,Ty,Tz = drawingData['viewPoint'][0]
        cx,ct,cs,ci = drawingData['atomPtrs']
        bondR = drawingData['bondRadius']
        G,g = G2lat.cell2Gmat(cell)
        GS = G
        GS[0][1] = GS[1][0] = math.sqrt(GS[0][0]*GS[1][1])
        GS[0][2] = GS[2][0] = math.sqrt(GS[0][0]*GS[2][2])
        GS[1][2] = GS[2][1] = math.sqrt(GS[1][1]*GS[2][2])
        ellipseProb = G2lat.criticalEllipse(drawingData['ellipseProb']/100.)
        
        SetBackground()
        GL.glInitNames()
        GL.glPushName(0)
        
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glViewport(0,0,VS[0],VS[1])
        GLU.gluPerspective(20.,aspect,cPos-Zclip,cPos+Zclip)
        GLU.gluLookAt(0,0,cPos,0,0,0,0,1,0)
        SetLights()            
            
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        matRot = G2mth.Q2Mat(Q)
        matRot = np.concatenate((np.concatenate((matRot,[[0],[0],[0]]),axis=1),[[0,0,0,1],]),axis=0)
        GL.glMultMatrixf(matRot.T)
        GL.glMultMatrixf(A4mat.T)
        GL.glTranslate(-Tx,-Ty,-Tz)
        if drawingData['showABC']:
            x,y,z = drawingData['viewPoint'][0]
            RenderUnitVectors(x,y,z)
        Backbones = {}
        BackboneColor = []
#        glEnable(GL_BLEND)
#        glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
        if not len(Fade):
            atmFade = np.ones(len(drawingData['Atoms']))
        else:
            atmFade = Fade
        for iat,atom in enumerate(drawingData['Atoms']):
            x,y,z = atom[cx:cx+3]
            Bonds = atom[-2]
            Faces = atom[-1]
            try:
                atNum = generalData['AtomTypes'].index(atom[ct])
            except ValueError:
                atNum = -1
            CL = atom[cs+2]
            if not atmFade[iat]:
                continue
            atColor = atmFade[iat]*np.array(CL)/255.
            if drawingData['showRigidBodies'] and atom[ci] in rbAtmDict:
                bndColor = Or/255.
            else:
                bndColor = atColor
            if iat in Ind and G2frame.dataDisplay.GetPageText(getSelection()) != 'Map peaks':
                atColor = np.array(Gr)/255.
#            color += [.25,]
            radius = 0.5
            if atom[cs] != '':
                try:
                    GL.glLoadName(atom[-3])
                except: #problem with old files - missing code
                    pass
            if 'balls' in atom[cs]:
                vdwScale = drawingData['vdwScale']
                ballScale = drawingData['ballScale']
                if atNum < 0:
                    radius = 0.2
                elif 'H' == atom[ct]:
                    if drawingData['showHydrogen']:
                        if 'vdW' in atom[cs] and atNum >= 0:
                            radius = vdwScale*vdWRadii[atNum]
                        else:
                            radius = ballScale*drawingData['sizeH']
                    else:
                        radius = 0.0
                else:
                    if 'vdW' in atom[cs]:
                        radius = vdwScale*vdWRadii[atNum]
                    else:
                        radius = ballScale*BondRadii[atNum]
                RenderSphere(x,y,z,radius,atColor)
                if 'sticks' in atom[cs]:
                    RenderBonds(x,y,z,Bonds,bondR,bndColor)
            elif 'ellipsoids' in atom[cs]:
                RenderBonds(x,y,z,Bonds,bondR,bndColor)
                if atom[cs+3] == 'A':                    
                    Uij = atom[cs+5:cs+11]
                    U = np.multiply(G2spc.Uij2U(Uij),GS)
                    U = np.inner(Amat,np.inner(U,Amat).T)
                    E,R = nl.eigh(U)
                    R4 = np.concatenate((np.concatenate((R,[[0],[0],[0]]),axis=1),[[0,0,0,1],]),axis=0)
                    E = np.sqrt(E)
                    if atom[ct] == 'H' and not drawingData['showHydrogen']:
                        pass
                    else:
                        RenderEllipsoid(x,y,z,ellipseProb,E,R4,atColor)                    
                else:
                    if atom[ct] == 'H' and not drawingData['showHydrogen']:
                        pass
                    else:
                        radius = ellipseProb*math.sqrt(abs(atom[cs+4]))
                        RenderSphere(x,y,z,radius,atColor)
            elif 'lines' in atom[cs]:
                radius = 0.1
                RenderLines(x,y,z,Bonds,bndColor)
#                RenderBonds(x,y,z,Bonds,0.05,color,6)
            elif atom[cs] == 'sticks':
                radius = 0.1
                RenderBonds(x,y,z,Bonds,bondR,bndColor)
            elif atom[cs] == 'polyhedra':
                RenderPolyhedra(x,y,z,Faces,atColor)
            elif atom[cs] == 'backbone':
                if atom[ct-1].split()[0] in ['C','N']:
                    if atom[2] not in Backbones:
                        Backbones[atom[2]] = []
                    Backbones[atom[2]].append(list(np.inner(Amat,np.array([x,y,z]))))
                    BackboneColor.append(list(atColor))
                    
            if generalData['Type'] == 'magnetic':
                SymOp = int(atom[cs-1].split('+')[0])
                OpNum = G2spc.GetOpNum(SymOp,SGData)-1
                Moment = np.array(atom[cx+3:cx+6])
                color = (Wt-Bc)/255.
                if SpnFlp[OpNum] < 0:
                    color = Rd/255.
                RenderMoment(x,y,z,Moment,color)                    

            if atom[cs+1] == 'type':
                RenderLabel(x,y,z,'  '+atom[ct],radius,wxGreen,matRot)
            elif atom[cs+1] == 'name':
                RenderLabel(x,y,z,'  '+atom[ct-1],radius,wxGreen,matRot)
            elif atom[cs+1] == 'number':
                RenderLabel(x,y,z,'  '+str(iat),radius,wxGreen,matRot)
            elif atom[cs+1] == 'residue' and atom[ct-1] == 'CA':
                RenderLabel(x,y,z,'  '+atom[ct-4],radius,wxGreen,matRot)
            elif atom[cs+1] == '1-letter' and atom[ct-1] == 'CA':
                RenderLabel(x,y,z,'  '+atom[ct-3],radius,wxGreen,matRot)
            elif atom[cs+1] == 'chain' and atom[ct-1] == 'CA':
                RenderLabel(x,y,z,'  '+atom[ct-2],radius,wxGreen,matRot)
#        glDisable(GL_BLEND)
        if len(rhoXYZ):
            RenderMap(rho,rhoXYZ,indx,Rok)
        if len(mapPeaks):
            XYZ = mapPeaks.T[1:4].T
            mapBonds = FindPeaksBonds(XYZ)
            for ind,[mag,x,y,z] in enumerate(mapPeaks[:,:4]):
                if ind in Ind and pageName == 'Map peaks':
                    RenderMapPeak(x,y,z,Gr,1.0)
                else:
                    if mag > 0.:
                        RenderMapPeak(x,y,z,Wt,mag/peakMax)
                    else:
                        RenderMapPeak(x,y,z,Rd,-mag/peakMax)
                if showBonds:
                    RenderLines(x,y,z,mapBonds[ind],Wt)
        if len(testRBObj) and pageName == 'RB Models':
            XYZ = G2mth.UpdateRBXYZ(Bmat,testRBObj['rbObj'],testRBObj['rbData'],testRBObj['rbType'])[0]
            rbBonds = FindPeaksBonds(XYZ)
            for ind,[x,y,z] in enumerate(XYZ):
                aType = testRBObj['rbAtTypes'][ind]
                name = '  '+aType+str(ind)
                color = np.array(testRBObj['AtInfo'][aType][1])
                RenderSphere(x,y,z,0.2,color/255.)
                RenderBonds(x,y,z,rbBonds[ind],0.03,Gr)
                RenderLabel(x,y,z,name,0.2,wxOrange,matRot)
        if len(mcsaModels) > 1 and pageName == 'MC/SA':             #skip the default MD entry
            for ind,[x,y,z] in enumerate(mcsaXYZ):
                aType = mcsaTypes[ind]
                name = '  '+aType+str(ind)
                color = np.array(MCSA['AtInfo'][aType][1])
                RenderSphere(x,y,z,0.2,color/255.)
                RenderBonds(x,y,z,mcsaBonds[ind],0.03,Gr/255.)
                RenderLabel(x,y,z,name,0.2,wxOrange,matRot)
        if Backbones:
            for chain in Backbones:
                Backbone = Backbones[chain]
                RenderBackbone(Backbone,BackboneColor,bondR)
        if drawingData['unitCellBox']:
            RenderBox()
            if drawingData['Plane'][1]:
                H,phase,stack,phase,color = drawingData['Plane']
                Planes = G2lat.PlaneIntercepts(Amat,Bmat,H,phase,stack)
                for plane in Planes:
                    RenderPlane(plane,color)
#        print time.time()-time0
        try:
            if Page.context: Page.canvas.SetCurrent(Page.context)
        except:
            pass
        Page.canvas.SwapBuffers()
        
    def OnSize(event):
        Draw('size')
        
    def OnFocus(event):
        Draw('focus')
        
    # PlotStructure execution starts here (N.B. initialization above)
    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab(generalData['Name'],'ogl')
    if new:
        Page.views = False
    Font = Page.GetFont()
    Page.Choice = None
    if mapData.get('Flip',False):
        choice = [' save as/key:','jpeg','tiff','bmp','c: center on 1/2,1/2,1/2',
            'u: roll up','d: roll down','l: roll left','r: roll right']
    else:
        choice = [' save as/key:','jpeg','tiff','bmp','c: center on 1/2,1/2,1/2','n: next','p: previous']
    if generalData['Modulated'] and len(drawAtoms):
        choice += ['+: increase tau','-: decrease tau','0: set tau = 0']    #add 'm: make modulation movie'

    Tx,Ty,Tz = drawingData['viewPoint'][0]
    rho = G2mth.getRho([Tx,Ty,Tz],mapData)
    G2frame.G2plotNB.status.SetStatusText('View point: %.4f, %.4f, %.4f; density: %.4f'%(Tx,Ty,Tz,rho),1)

    cb = wx.ComboBox(G2frame.G2plotNB.status,style=wx.CB_DROPDOWN|wx.CB_READONLY,choices=choice)
    cb.Bind(wx.EVT_COMBOBOX, OnKeyBox)
    cb.SetValue(' save as/key:')
    Page.canvas.Bind(wx.EVT_LEFT_DOWN, OnMouseDown)
    Page.canvas.Bind(wx.EVT_RIGHT_DOWN, OnMouseDown)
    Page.canvas.Bind(wx.EVT_MIDDLE_DOWN, OnMouseDown)
    Page.canvas.Bind(wx.EVT_KEY_UP, OnKey)
    Page.canvas.Bind(wx.EVT_KEY_DOWN,OnKeyPressed)
    Page.canvas.Bind(wx.EVT_MOTION, OnMouseMove)
    Page.canvas.Bind(wx.EVT_MOUSEWHEEL, OnMouseWheel)
    Page.canvas.Bind(wx.EVT_SIZE, OnSize)
    Page.canvas.Bind(wx.EVT_SET_FOCUS, OnFocus)
    Page.camera['position'] = drawingData['cameraPos']
    Page.camera['viewPoint'] = np.inner(Amat,drawingData['viewPoint'][0])
    Page.camera['backColor'] = backColor/255.
    try:
        Page.canvas.SetCurrent()
    except:
        pass
    wx.CallAfter(Draw,'main')
    if firstCall: Draw('main') # draw twice the first time that graphics are displayed

################################################################################
#### Plot Rigid Body
################################################################################

def PlotRigidBody(G2frame,rbType,AtInfo,rbData,defaults):
    '''RB plotting package. Can show rigid body structures as balls & sticks
    '''

    def FindBonds(XYZ):
        rbTypes = rbData['rbTypes']
        Radii = []
        for Atype in rbTypes:
            Radii.append(AtInfo[Atype][0])
            if Atype == 'H':
                Radii[-1] = 0.5
        Radii = np.array(Radii)
        Bonds = [[] for i in range(len(Radii))]
        for i,xyz in enumerate(XYZ):
            Dx = XYZ-xyz
            dist = np.sqrt(np.sum(Dx**2,axis=1))
            sumR = Radii[i]+Radii
            IndB = ma.nonzero(ma.masked_greater(dist-0.85*sumR,0.))
            for j in IndB[0]:
                Bonds[i].append(Dx[j]*Radii[i]/sumR[j])
                Bonds[j].append(-Dx[j]*Radii[j]/sumR[j])
        return Bonds
                        
    Mydir = G2frame.dirname
    Rd = np.array([255,0,0])
    Gr = np.array([0,255,0])
    Bl = np.array([0,0,255])
    uBox = np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1]])
    uEdges = np.array([[uBox[0],uBox[1]],[uBox[0],uBox[2]],[uBox[0],uBox[3]]])
    uColors = [Rd,Gr,Bl]
    if rbType == 'Vector':
        atNames = [str(i)+':'+Ty for i,Ty in enumerate(rbData['rbTypes'])]
        XYZ = np.array([[0.,0.,0.] for Ty in rbData['rbTypes']])
        for imag,mag in enumerate(rbData['VectMag']):
            XYZ += mag*rbData['rbVect'][imag]
        Bonds = FindBonds(XYZ)
    elif rbType == 'Residue':
#        atNames = [str(i)+':'+Ty for i,Ty in enumerate(rbData['atNames'])]
        atNames = rbData['atNames']
        XYZ = np.copy(rbData['rbXYZ'])      #don't mess with original!
        Seq = rbData['rbSeq']
        for ia,ib,ang,mv in Seq:
            va = XYZ[ia]-XYZ[ib]
            Q = G2mth.AVdeg2Q(ang,va)
            for im in mv:
                vb = XYZ[im]-XYZ[ib]
                vb = G2mth.prodQVQ(Q,vb)
                XYZ[im] = XYZ[ib]+vb
        Bonds = FindBonds(XYZ)
    elif rbType == 'Z-matrix':
        pass

#    def SetRBOrigin():
#        page = getSelection()
#        if page:
#            if G2frame.dataDisplay.GetPageText(page) == 'Rigid bodies':
#                G2frame.MapPeaksTable.SetData(mapPeaks)
#                panel = G2frame.dataDisplay.GetPage(page).GetChildren()
#                names = [child.GetName() for child in panel]
#                panel[names.index('grid window')].Refresh()
            
    def OnMouseDown(event):
        xy = event.GetPosition()
        defaults['oldxy'] = list(xy)

    def OnMouseMove(event):
        newxy = event.GetPosition()
                                
        if event.Dragging():
            if event.LeftIsDown():
                SetRotation(newxy)
                Q = defaults['Quaternion']
                G2frame.G2plotNB.status.SetStatusText('New quaternion: %.2f+, %.2fi+ ,%.2fj+, %.2fk'%(Q[0],Q[1],Q[2],Q[3]),1)
#            elif event.RightIsDown():
#                SetRBOrigin(newxy)
            elif event.MiddleIsDown():
                SetRotationZ(newxy)
                Q = defaults['Quaternion']
                G2frame.G2plotNB.status.SetStatusText('New quaternion: %.2f+, %.2fi+ ,%.2fj+, %.2fk'%(Q[0],Q[1],Q[2],Q[3]),1)
            Draw('move')
        
    def OnMouseWheel(event):
        defaults['cameraPos'] += event.GetWheelRotation()/24
        defaults['cameraPos'] = max(10,min(500,defaults['cameraPos']))
        G2frame.G2plotNB.status.SetStatusText('New camera distance: %.2f'%(defaults['cameraPos']),1)
        Draw('wheel')
        
    def SetBackground():
        R,G,B,A = Page.camera['backColor']
        GL.glClearColor(R,G,B,A)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        
    def SetLights():
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glShadeModel(GL.GL_FLAT)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glEnable(GL.GL_LIGHT0)
        GL.glLightModeli(GL.GL_LIGHT_MODEL_TWO_SIDE,0)
        GL.glLightfv(GL.GL_LIGHT0,GL.GL_AMBIENT,[1,1,1,.8])
        GL.glLightfv(GL.GL_LIGHT0,GL.GL_DIFFUSE,[1,1,1,1])
        
    def SetRotation(newxy):
#first get rotation vector in screen coords. & angle increment        
        oldxy = defaults['oldxy']
        if not len(oldxy): oldxy = list(newxy)
        dxy = newxy-oldxy
        defaults['oldxy'] = list(newxy)
        V = np.array([dxy[1],dxy[0],0.])
        A = 0.25*np.sqrt(dxy[0]**2+dxy[1]**2)
# next transform vector back to xtal coordinates via inverse quaternion
# & make new quaternion
        Q = defaults['Quaternion']
        V = G2mth.prodQVQ(G2mth.invQ(Q),V)
        DQ = G2mth.AVdeg2Q(A,V)
        Q = G2mth.prodQQ(Q,DQ)
        defaults['Quaternion'] = Q
# finally get new view vector - last row of rotation matrix
        VD = G2mth.Q2Mat(Q)[2]
        VD /= np.sqrt(np.sum(VD**2))
        defaults['viewDir'] = VD
        
    def SetRotationZ(newxy):                        
#first get rotation vector (= view vector) in screen coords. & angle increment        
        View = GL.glGetIntegerv(GL.GL_VIEWPORT)
        cent = [View[2]/2,View[3]/2]
        oldxy = defaults['oldxy']
        if not len(oldxy): oldxy = list(newxy)
        dxy = newxy-oldxy
        defaults['oldxy'] = list(newxy)
        V = defaults['viewDir']
        A = [0,0]
        A[0] = dxy[1]*.25
        A[1] = dxy[0]*.25
        if newxy[0] > cent[0]:
            A[0] *= -1
        if newxy[1] < cent[1]:
            A[1] *= -1        
# next transform vector back to xtal coordinates & make new quaternion
        Q = defaults['Quaternion']
        Qx = G2mth.AVdeg2Q(A[0],V)
        Qy = G2mth.AVdeg2Q(A[1],V)
        Q = G2mth.prodQQ(Q,Qx)
        Q = G2mth.prodQQ(Q,Qy)
        defaults['Quaternion'] = Q

    def RenderUnitVectors(x,y,z):
        GL.glEnable(GL.GL_COLOR_MATERIAL)
        GL.glLineWidth(1)
        GL.glPushMatrix()
        GL.glTranslate(x,y,z)
        GL.glBegin(GL.GL_LINES)
        for line,color in zip(uEdges,uColors):
            GL.glColor3ubv(color)
            GL.glVertex3fv(-line[1])
            GL.glVertex3fv(line[1])
        GL.glEnd()
        GL.glPopMatrix()
        GL.glColor4ubv([0,0,0,0])
        GL.glDisable(GL.GL_COLOR_MATERIAL)
                
    def RenderSphere(x,y,z,radius,color):
        GL.glMaterialfv(GL.GL_FRONT_AND_BACK,GL.GL_DIFFUSE,color)
        GL.glPushMatrix()
        GL.glTranslate(x,y,z)
        q = GLU.gluNewQuadric()
        GLU.gluSphere(q,radius,20,10)
        GL.glPopMatrix()
        
    def RenderBonds(x,y,z,Bonds,radius,color,slice=20):
        GL.glMaterialfv(GL.GL_FRONT_AND_BACK,GL.GL_DIFFUSE,color)
        GL.glPushMatrix()
        GL.glTranslate(x,y,z)
        for Dx in Bonds:
            GL.glPushMatrix()
            Z = np.sqrt(np.sum(Dx**2))
            if Z:
                azm = atan2d(-Dx[1],-Dx[0])
                phi = acosd(Dx[2]/Z)
                GL.glRotate(-azm,0,0,1)
                GL.glRotate(phi,1,0,0)
                q = GLU.gluNewQuadric()
                GLU.gluCylinder(q,radius,radius,Z,slice,2)
            GL.glPopMatrix()            
        GL.glPopMatrix()
                
    def RenderLabel(x,y,z,label,matRot):       
        GL.glPushMatrix()
        GL.glTranslate(x,y,z)
        GL.glDisable(GL.GL_LIGHTING)
        GL.glRasterPos3f(0,0,0)
        GL.glMultMatrixf(matRot)
        GL.glRotate(180,1,0,0)             #fix to flip about x-axis
        text = gltext.TextElement(text=label,font=Font,foreground=wx.WHITE)
        text.draw_text(scale=0.025)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glPopMatrix()
        
    def Draw(caller=''):
#useful debug?        
#        if caller:
#            print caller
# end of useful debug
        cPos = defaults['cameraPos']
        VS = np.array(Page.canvas.GetSize())
        aspect = float(VS[0])/float(VS[1])
        Q = defaults['Quaternion']
        SetBackground()
        GL.glInitNames()
        GL.glPushName(0)
        
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glViewport(0,0,VS[0],VS[1])
        GLU.gluPerspective(20.,aspect,1.,500.)
        GLU.gluLookAt(0,0,cPos,0,0,0,0,1,0)
        SetLights()            
            
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        matRot = G2mth.Q2Mat(Q)
        matRot = np.concatenate((np.concatenate((matRot,[[0],[0],[0]]),axis=1),[[0,0,0,1],]),axis=0)
        GL.glMultMatrixf(matRot.T)
        RenderUnitVectors(0.,0.,0.)
        radius = 0.2
        for iat,atom in enumerate(XYZ):
            x,y,z = atom
            CL = AtInfo[rbData['rbTypes'][iat]][1]
            color = np.array(CL)/255.
            RenderSphere(x,y,z,radius,color)
            RenderBonds(x,y,z,Bonds[iat],0.05,color)
            RenderLabel(x,y,z,'  '+atNames[iat],matRot)
        try:
            if Page.context: Page.canvas.SetCurrent(Page.context)
        except:
            pass
        Page.canvas.SwapBuffers()

    def OnSize(event):
        Draw('size')
        
    def OnKeyBox(event):
        mode = cb.GetValue()
        if mode in ['jpeg','bmp','tiff',]:
            try:
                import Image as Im
            except ImportError:
                try:
                    from PIL import Image as Im
                except ImportError:
                    print "PIL/pillow Image module not present. Cannot save images without this"
                    raise Exception("PIL/pillow Image module not found")
            
            Fname = os.path.join(Mydir,Page.name+'.'+mode)
            print Fname+' saved'
            size = Page.canvas.GetSize()
            GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
            if mode in ['jpeg',]:
                Pix = GL.glReadPixels(0,0,size[0],size[1],GL.GL_RGBA, GL.GL_UNSIGNED_BYTE)
                im = Im.new("RGBA", (size[0],size[1]))
            else:
                Pix = GL.glReadPixels(0,0,size[0],size[1],GL.GL_RGB, GL.GL_UNSIGNED_BYTE)
                im = Im.new("RGB", (size[0],size[1]))
            try:
                im.frombytes(Pix)
            except AttributeError:
                im.fromstring(Pix)
            im = im.transpose(Im.FLIP_TOP_BOTTOM)
            im.save(Fname,mode)
            cb.SetValue(' save as/key:')
            G2frame.G2plotNB.status.SetStatusText('Drawing saved to: '+Fname,1)

    # PlotStructure execution starts here (N.B. initialization above)
    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('Rigid body','ogl')
    if new:
        Page.views = False
    Page.name = rbData['RBname']
    Page.Choice = None
    choice = [' save as:','jpeg','tiff','bmp',]
    cb = wx.ComboBox(G2frame.G2plotNB.status,style=wx.CB_DROPDOWN|wx.CB_READONLY,choices=choice)
    cb.Bind(wx.EVT_COMBOBOX, OnKeyBox)
    cb.SetValue(' save as/key:')
    
    Font = Page.GetFont()
    Page.canvas.Bind(wx.EVT_MOUSEWHEEL, OnMouseWheel)
    Page.canvas.Bind(wx.EVT_LEFT_DOWN, OnMouseDown)
    Page.canvas.Bind(wx.EVT_RIGHT_DOWN, OnMouseDown)
    Page.canvas.Bind(wx.EVT_MIDDLE_DOWN, OnMouseDown)
    Page.canvas.Bind(wx.EVT_MOTION, OnMouseMove)
    Page.canvas.Bind(wx.EVT_SIZE, OnSize)
    Page.camera['position'] = defaults['cameraPos']
    Page.camera['backColor'] = np.array([0,0,0,0])
    Page.canvas.SetCurrent()
    Draw('main')
    Draw('main')    #to fill both buffers so save works

################################################################################
#### Plot Layers
################################################################################

def PlotLayers(G2frame,Layers,laySeq,defaults):
    '''Layer plotting package. Can show layer structures as balls & sticks
    '''

    global AtNames,AtTypes,XYZ,Bonds
    def FindBonds(atTypes,XYZ):
        Radii = []
        for Atype in atTypes:
            Radii.append(AtInfo[Atype[0]]['Drad'])
            if Atype[0] == 'H':
                Radii[-1] = 0.5
        Radii = np.array(Radii)
        Bonds = [[] for i in range(len(Radii))]
        for i,xyz in enumerate(XYZ):
            Dx = np.inner(Amat,(XYZ-xyz)).T
            dist = np.sqrt(np.sum(Dx**2,axis=1))
            sumR = Radii[i]+Radii
            IndB = ma.nonzero(ma.masked_greater(dist-0.85*sumR,0.))
            for j in IndB[0]:
                Bonds[i].append(Dx[j]*Radii[i]/sumR[j])
                Bonds[j].append(-Dx[j]*Radii[j]/sumR[j])
        return Bonds
        
    def getAtoms():
        global AtNames,AtTypes,XYZ,Bonds
        AtNames = []
        AtTypes = []
        newXYZ = np.zeros((0,3))
        TX = np.zeros(3)
        for il in range(len(laySeq)):
            layer = laySeq[il]     
            if Layers['Layers'][layer]['SameAs']:
                layer = Names.index(Layers['Layers'][layer]['SameAs'])
            atNames = [atom[0] for atom in Layers['Layers'][layer]['Atoms']]
            atTypes = [[atom[1],il] for atom in Layers['Layers'][layer]['Atoms']]
            XYZ = np.array([atom[2:5] for atom in Layers['Layers'][layer]['Atoms']])
            if '-1' in Layers['Layers'][layer]['Symm']:
                atNames += atNames
                atTypes += atTypes
                XYZ = np.concatenate((XYZ,-XYZ))
            if il:
                TX += np.array(Trans[laySeq[il-1]][laySeq[il]][1:4])
#                TX[0] %= 1.
#                TX[1] %= 1.
                XYZ += TX
            AtNames += atNames
            AtTypes += atTypes
            newXYZ = np.concatenate((newXYZ,XYZ))
        XYZ = newXYZ
        na = max(int(8./cell[0]),1)
        nb = max(int(8./cell[1]),1)
        indA = range(-na,na)
        indB = range(-nb,nb)
        Units = np.array([[h,k,0] for h in indA for k in indB])
        newXYZ = np.zeros((0,3))
        for unit in Units:
            newXYZ = np.concatenate((newXYZ,unit+XYZ))
        if len(Units):
            AtNames *= len(Units)
            AtTypes *= len(Units)
        XYZ = newXYZ
#        GSASIIpath.IPyBreak()
        
        Bonds = FindBonds(AtTypes,XYZ)
                        
    def OnKeyBox(event):
        mode = cb.GetValue()
        if mode in ['jpeg','bmp','tiff',]:
            try:
                import Image as Im
            except ImportError:
                try:
                    from PIL import Image as Im
                except ImportError:
                    print "PIL/pillow Image module not present. Cannot save images without this"
                    raise Exception("PIL/pillow Image module not found")
            projFile = G2frame.GSASprojectfile
            Fname = (os.path.splitext(projFile)[0]+'.'+mode).replace('*','+')
            size = Page.canvas.GetSize()
            GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
            if mode in ['jpeg',]:
                Pix = GL.glReadPixels(0,0,size[0],size[1],GL.GL_RGBA, GL.GL_UNSIGNED_BYTE)
                im = Im.new("RGBA", (size[0],size[1]))
            else:
                Pix = GL.glReadPixels(0,0,size[0],size[1],GL.GL_RGB, GL.GL_UNSIGNED_BYTE)
                im = Im.new("RGB", (size[0],size[1]))
            try:
                im.frombytes(Pix)
            except AttributeError:
                im.fromstring(Pix)
            im = im.transpose(Im.FLIP_TOP_BOTTOM)
            im.save(Fname,mode)
            print ' Drawing saved to: '+Fname
        elif mode[0] in ['L','F']:
            event.key = cb.GetValue()[0]
            wx.CallAfter(OnPlotKeyPress,event)
        Page.canvas.SetFocus() # redirect the Focus from the button back to the plot

    def OnPlotKeyPress(event):
        global AtNames,AtTypes,XYZ,Bonds
        try:
            key = event.GetKeyCode()
            if key > 255:
                key = 0
            keyCode = chr(key)
        except AttributeError:       #if from OnKeyBox above
            keyCode = str(event.key).upper()
        dx = 0.
        dy = 0.
        dz = 0.
        if keyCode == 'L':
            Page.labels = not Page.labels
            Draw('labels')
            return
        elif keyCode =='F' and len(laySeq) == 2:
            Page.fade = not Page.fade
        if len(laySeq) != 2:
            return
        Trans = Layers['Transitions']
        Yi,Xi = laySeq
        dxyz = 0.01
        if keyCode == 'X':
            dx = dxyz
            if event.shiftDown:
                dx *= -1.
            Trans[Yi][Xi][1] += dx
            SetTransText(Yi,Xi,Trans[Yi][Xi],1)
        elif keyCode == 'Y':
            dy = dxyz
            if event.shiftDown:
                dy *= -1.
            Trans[Yi][Xi][2] += dy
            SetTransText(Yi,Xi,Trans[Yi][Xi],2)
        elif keyCode == 'Z':
            dz = dxyz
            if event.shiftDown:
                dz *= -1.
            Trans[Yi][Xi][3] += dz
            SetTransText(Yi,Xi,Trans[Yi][Xi],3)
        getAtoms()
        Draw('shift')
        
    def SetTransText(Yi,Xi,XYZ,id):
        page = G2frame.dataDisplay.GetSelection()
        if page:
            if G2frame.dataDisplay.GetPageText(page) == 'Layers':
                G2frame.dataDisplay.GetPage(page).transGrids[Yi].Refresh()
            
    def OnMouseDown(event):
        xy = event.GetPosition()
        defaults['oldxy'] = list(xy)

    def OnMouseMove(event):
        newxy = event.GetPosition()
                                
        if event.Dragging():
            if event.LeftIsDown():
                SetRotation(newxy)
            elif event.RightIsDown():
                SetTranslation(newxy)
                Tx,Ty,Tz = defaults['viewPoint'][0]
            elif event.MiddleIsDown():
                SetRotationZ(newxy)
            Draw('move')
        
    def OnMouseWheel(event):
        defaults['cameraPos'] += event.GetWheelRotation()/24
        defaults['cameraPos'] = max(10,min(500,defaults['cameraPos']))
        Draw('wheel')
        
    def SetBackground():
        R,G,B,A = Page.camera['backColor']
        GL.glClearColor(R,G,B,A)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        
    def SetLights():
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glShadeModel(GL.GL_FLAT)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glEnable(GL.GL_LIGHT0)
        GL.glLightModeli(GL.GL_LIGHT_MODEL_TWO_SIDE,0)
        GL.glLightfv(GL.GL_LIGHT0,GL.GL_AMBIENT,[1,1,1,.8])
        GL.glLightfv(GL.GL_LIGHT0,GL.GL_DIFFUSE,[1,1,1,1])
        
    def SetTranslation(newxy):
#first get translation vector in screen coords.       
        oldxy = defaults['oldxy']
        if not len(oldxy): oldxy = list(newxy)
        dxy = newxy-oldxy
        defaults['oldxy'] = list(newxy)
        V = np.array([-dxy[0],dxy[1],0.])
#then transform to rotated crystal coordinates & apply to view point        
        Q = defaults['Quaternion']
        V = np.inner(Bmat,G2mth.prodQVQ(G2mth.invQ(Q),V))
        Tx,Ty,Tz = defaults['viewPoint'][0]
        delt = 0.01
        Tx += V[0]*delt
        Ty += V[1]*delt
        Tz += V[2]*delt
        defaults['viewPoint'][0] =  np.array([Tx,Ty,Tz])
        
    def SetRotation(newxy):
#first get rotation vector in screen coords. & angle increment        
        oldxy = defaults['oldxy']
        if not len(oldxy): oldxy = list(newxy)
        dxy = newxy-oldxy
        defaults['oldxy'] = list(newxy)
        V = np.array([dxy[1],dxy[0],0.])
        A = 0.25*np.sqrt(dxy[0]**2+dxy[1]**2)
# next transform vector back to xtal coordinates via inverse quaternion
# & make new quaternion
        Q = defaults['Quaternion']
        V = G2mth.prodQVQ(G2mth.invQ(Q),V)
        DQ = G2mth.AVdeg2Q(A,V)
        Q = G2mth.prodQQ(Q,DQ)
        defaults['Quaternion'] = Q
# finally get new view vector - last row of rotation matrix
        VD = G2mth.Q2Mat(Q)[2]
        VD /= np.sqrt(np.sum(VD**2))
        defaults['viewDir'] = VD
        
    def SetRotationZ(newxy):                        
#first get rotation vector (= view vector) in screen coords. & angle increment        
        View = GL.glGetIntegerv(GL.GL_VIEWPORT)
        cent = [View[2]/2,View[3]/2]
        oldxy = defaults['oldxy']
        if not len(oldxy): oldxy = list(newxy)
        dxy = newxy-oldxy
        defaults['oldxy'] = list(newxy)
        V = defaults['viewDir']
        A = [0,0]
        A[0] = dxy[1]*.25
        A[1] = dxy[0]*.25
        if newxy[0] > cent[0]:
            A[0] *= -1
        if newxy[1] < cent[1]:
            A[1] *= -1        
# next transform vector back to xtal coordinates & make new quaternion
        Q = defaults['Quaternion']
        Qx = G2mth.AVdeg2Q(A[0],V)
        Qy = G2mth.AVdeg2Q(A[1],V)
        Q = G2mth.prodQQ(Q,Qx)
        Q = G2mth.prodQQ(Q,Qy)
        defaults['Quaternion'] = Q

    def RenderUnitVectors(x,y,z):
        GL.glEnable(GL.GL_COLOR_MATERIAL)
        GL.glLineWidth(1)
        GL.glPushMatrix()
        GL.glTranslate(x,y,z)
        GL.glBegin(GL.GL_LINES)
        for line,color in zip(uEdges,uColors):
            GL.glColor3ubv(color)
            GL.glVertex3fv(line[0])
            GL.glVertex3fv(line[1])
        GL.glEnd()
        GL.glPopMatrix()
        GL.glColor4ubv([0,0,0,0])
        GL.glDisable(GL.GL_COLOR_MATERIAL)
                
    def RenderSphere(x,y,z,radius,color):
        GL.glMaterialfv(GL.GL_FRONT_AND_BACK,GL.GL_DIFFUSE,color)
        GL.glPushMatrix()
        GL.glTranslate(x,y,z)
        GL.glMultMatrixf(B4mat.T)
        q = GLU.gluNewQuadric()
        GLU.gluSphere(q,radius,20,10)
        GL.glPopMatrix()
        
    def RenderBonds(x,y,z,Bonds,radius,color,slice=20):
        GL.glMaterialfv(GL.GL_FRONT_AND_BACK,GL.GL_DIFFUSE,color)
        GL.glPushMatrix()
        GL.glTranslate(x,y,z)
        GL.glMultMatrixf(B4mat.T)
        for Dx in Bonds:
            GL.glPushMatrix()
            Z = np.sqrt(np.sum(Dx**2))
            if Z:
                azm = atan2d(-Dx[1],-Dx[0])
                phi = acosd(Dx[2]/Z)
                GL.glRotate(-azm,0,0,1)
                GL.glRotate(phi,1,0,0)
                q = GLU.gluNewQuadric()
                GLU.gluCylinder(q,radius,radius,Z,slice,2)
            GL.glPopMatrix()            
        GL.glPopMatrix()
                
    def RenderLabel(x,y,z,label,matRot):       
        GL.glPushMatrix()
        GL.glTranslate(x,y,z)
        GL.glMultMatrixf(B4mat.T)
        GL.glDisable(GL.GL_LIGHTING)
        GL.glRasterPos3f(0,0,0)
        GL.glMultMatrixf(matRot)
        GL.glRotate(180,1,0,0)             #fix to flip about x-axis
        text = gltext.TextElement(text=label,font=Font,foreground=wx.WHITE)
        text.draw_text(scale=0.025)
        GL.glEnable(GL.GL_LIGHTING)
        GL.glPopMatrix()
        
    def Draw(caller=''):
#useful debug?        
#        if caller:
#            print caller
# end of useful debug
        global AtNames,AtTypes,XYZ,Bonds
        cPos = defaults['cameraPos']
        VS = np.array(Page.canvas.GetSize())
        aspect = float(VS[0])/float(VS[1])
        Tx,Ty,Tz = defaults['viewPoint'][0]
        Q = defaults['Quaternion']
        SetBackground()
        GL.glInitNames()
        GL.glPushName(0)
        
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glViewport(0,0,VS[0],VS[1])
        GLU.gluPerspective(20.,aspect,1.,500.)
        GLU.gluLookAt(0,0,cPos,0,0,0,0,1,0)
        SetLights()            
            
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        matRot = G2mth.Q2Mat(Q)
        matRot = np.concatenate((np.concatenate((matRot,[[0],[0],[0]]),axis=1),[[0,0,0,1],]),axis=0)
        GL.glMultMatrixf(matRot.T)
        GL.glMultMatrixf(A4mat.T)
        GL.glTranslate(-Tx,-Ty,-Tz)
        RenderUnitVectors(0.,0.,0.)
        bondRad = 0.1
        atomRad = 0.5
        if Page.labels:
            bondRad = 0.05
            atomRad = 0.2
        GL.glShadeModel(GL.GL_SMOOTH)
        for iat,atom in enumerate(XYZ):
            x,y,z = atom
            CL = AtInfo[AtTypes[iat][0]]['Color']
            color = np.array(CL)/255.
            if len(laySeq) == 2 and AtTypes[iat][1] and Page.fade:
                color *= .5
            RenderSphere(x,y,z,atomRad,color)
            RenderBonds(x,y,z,Bonds[iat],bondRad,color)
            if Page.labels:
                RenderLabel(x,y,z,'  '+AtNames[iat],matRot)
        try:
            if Page.context: Page.canvas.SetCurrent(Page.context)
        except:
            pass
        Page.canvas.SwapBuffers()

    def OnSize(event):
        Draw('size')
        
    # PlotLayers execution starts here
    cell = Layers['Cell'][1:7]
    Amat,Bmat = G2lat.cell2AB(cell)         #Amat - crystal to cartesian, Bmat - inverse
    A4mat = np.concatenate((np.concatenate((Amat,[[0],[0],[0]]),axis=1),[[0,0,0,1],]),axis=0)
    B4mat = np.concatenate((np.concatenate((Bmat,[[0],[0],[0]]),axis=1),[[0,0,0,1],]),axis=0)
    Trans = Layers['Transitions']
    Wt = np.array([255,255,255])
    Rd = np.array([255,0,0])
    Gr = np.array([0,255,0])
    Bl = np.array([0,0,255])
    Bc = np.array([0,0,0])
    uBox = np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]])
    uEdges = np.array([
        [uBox[0],uBox[1]],[uBox[0],uBox[3]],[uBox[0],uBox[4]],[uBox[1],uBox[2]], 
        [uBox[2],uBox[3]],[uBox[1],uBox[5]],[uBox[2],uBox[6]],[uBox[3],uBox[7]], 
        [uBox[4],uBox[5]],[uBox[5],uBox[6]],[uBox[6],uBox[7]],[uBox[7],uBox[4]]])
    uColors = [Rd,Gr,Bl,Wt-Bc, Wt-Bc,Wt-Bc,Wt-Bc,Wt-Bc, Wt-Bc,Wt-Bc,Wt-Bc,Wt-Bc]
    uEdges[2][1][2] = len(laySeq)
    AtInfo = Layers['AtInfo']
    Names = [layer['Name'] for layer in Layers['Layers']]
    getAtoms()
    
    new,plotNum,Page,Plot,lim = G2frame.G2plotNB.FindPlotTab('Layer','ogl')
    if new:
        Page.views = False
        Page.labels = False
        Page.fade = False
    choice = [' save as:','jpeg','tiff','bmp','use keys for:','L - toggle labels']
    if len(laySeq) == 2:
        choice += ['F - toggle fade','X/shift-X move Dx','Y/shift-Y move Dy','Z/shift-Z move Dz']
    Page.keyPress = OnPlotKeyPress
    Font = Page.GetFont()
    cb = wx.ComboBox(G2frame.G2plotNB.status,style=wx.CB_DROPDOWN|wx.CB_READONLY,choices=choice)
    cb.Bind(wx.EVT_COMBOBOX, OnKeyBox)
    text = [str(Layers['Layers'][seq]['Name']) for seq in laySeq]
    G2frame.G2plotNB.status.SetStatusText(' Layers plotted: '+str(text).replace("'",'')[1:-1],1)
    Page.canvas.Bind(wx.EVT_MOUSEWHEEL, OnMouseWheel)
    Page.canvas.Bind(wx.EVT_LEFT_DOWN, OnMouseDown)
    Page.canvas.Bind(wx.EVT_RIGHT_DOWN, OnMouseDown)
    Page.canvas.Bind(wx.EVT_MIDDLE_DOWN, OnMouseDown)
    Page.canvas.Bind(wx.EVT_MOTION, OnMouseMove)
    Page.canvas.Bind(wx.wx.EVT_KEY_UP, OnPlotKeyPress)
    Page.canvas.Bind(wx.EVT_SIZE, OnSize)
    Page.camera['position'] = defaults['cameraPos']
    Page.camera['backColor'] = np.array([0,0,0,0])
    Page.canvas.SetCurrent()
    wx.CallAfter(Draw,'main')
