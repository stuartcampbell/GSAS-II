# -*- coding: utf-8 -*-
#GSASIIgrid - data display routines
########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### SVN repository information ###################
'''
*GSASIIgrid: Basic GUI routines*
--------------------------------

'''
import wx
import wx.grid as wg
#import wx.wizard as wz
#import wx.aui
import wx.lib.scrolledpanel as wxscroll
import time
import copy
import sys
import os
import random as ran
import numpy as np
import numpy.ma as ma
import scipy.optimize as so
import GSASIIpath
GSASIIpath.SetVersionNumber("$Revision$")
import GSASIImath as G2mth
import GSASIIIO as G2IO
import GSASIIstrIO as G2stIO
import GSASIIlattice as G2lat
import GSASIIplot as G2plt
import GSASIIpwdGUI as G2pdG
import GSASIIimgGUI as G2imG
import GSASIIphsGUI as G2phG
import GSASIIspc as G2spc
import GSASIImapvars as G2mv
import GSASIIconstrGUI as G2cnstG
import GSASIIrestrGUI as G2restG
import GSASIIpy3 as G2py3
import GSASIIobj as G2obj
import GSASIIexprGUI as G2exG
import GSASIIlog as log
import GSASIIctrls as G2G

# trig functions in degrees
sind = lambda x: np.sin(x*np.pi/180.)
tand = lambda x: np.tan(x*np.pi/180.)
cosd = lambda x: np.cos(x*np.pi/180.)

# Define a short name for convenience
WACV = wx.ALIGN_CENTER_VERTICAL

[ wxID_FOURCALC, wxID_FOURSEARCH, wxID_FOURCLEAR, wxID_PEAKSMOVE, wxID_PEAKSCLEAR, 
    wxID_CHARGEFLIP, wxID_PEAKSUNIQUE, wxID_PEAKSDELETE, wxID_PEAKSDA,
    wxID_PEAKSDISTVP, wxID_PEAKSVIEWPT, wxID_FINDEQVPEAKS,wxID_SHOWBONDS,wxID_MULTIMCSA,
    wxID_SINGLEMCSA,wxID_4DCHARGEFLIP,wxID_TRANSFORMSTRUCTURE,
] = [wx.NewId() for item in range(17)]

[ wxID_PWDRADD, wxID_HKLFADD, wxID_PWDANALYSIS, wxID_PWDCOPY, wxID_PLOTCTRLCOPY, 
    wxID_DATADELETE,wxID_DATACOPY,wxID_DATACOPYFLAGS,wxID_DATASELCOPY,wxID_DATAUSE,
] = [wx.NewId() for item in range(10)]

[ wxID_ATOMSEDITADD, wxID_ATOMSEDITINSERT, wxID_ATOMSEDITDELETE, 
    wxID_ATOMSMODIFY, wxID_ATOMSTRANSFORM, wxID_ATOMSVIEWADD, wxID_ATOMVIEWINSERT,
    wxID_RELOADDRAWATOMS,wxID_ATOMSDISAGL,wxID_ATOMMOVE,wxID_MAKEMOLECULE,
    wxID_ASSIGNATMS2RB,wxID_ATOMSPDISAGL, wxID_ISODISP,wxID_ADDHATOM,wxID_UPDATEHATOM,
    wxID_WAVEVARY,wxID_ATOMSROTATE, wxID_ATOMSDENSITY, wxID_VALIDPROTEIN,
    wxID_ATOMSSETALL, wxID_ATOMSSETSEL,
] = [wx.NewId() for item in range(22)]

[ wxID_DRAWATOMSTYLE, wxID_DRAWATOMLABEL, wxID_DRAWATOMCOLOR, wxID_DRAWATOMRESETCOLOR, 
    wxID_DRAWVIEWPOINT, wxID_DRAWTRANSFORM, wxID_DRAWDELETE, wxID_DRAWFILLCELL, 
    wxID_DRAWADDEQUIV, wxID_DRAWFILLCOORD, wxID_DRAWDISAGLTOR,  wxID_DRAWPLANE,
    wxID_DRAWDISTVP, wxID_DRAWADDSPHERE,wxID_DRWAEDITRADII,
] = [wx.NewId() for item in range(15)]

[ wxID_DRAWRESTRBOND, wxID_DRAWRESTRANGLE, wxID_DRAWRESTRPLANE, wxID_DRAWRESTRCHIRAL,
] = [wx.NewId() for item in range(4)]

[ wxID_ADDMCSAATOM,wxID_ADDMCSARB,wxID_CLEARMCSARB,wxID_MOVEMCSA,wxID_MCSACLEARRESULTS,
] = [wx.NewId() for item in range(5)]

[ wxID_CLEARTEXTURE,wxID_REFINETEXTURE,
] = [wx.NewId() for item in range(2)]

[ wxID_LOADDIFFAX,wxID_LAYERSIMULATE,wxID_SEQUENCESIMULATE, wxID_LAYERSFIT, wxID_COPYPHASE,
] = [wx.NewId() for item in range(5)]

[ wxID_PAWLEYLOAD, wxID_PAWLEYESTIMATE, wxID_PAWLEYUPDATE, wxID_PAWLEYSELALL, wxID_PAWLEYSELNONE,
  wxID_PAWLEYSELTOGGLE, wxID_PAWLEYSET, 
] = [wx.NewId() for item in range(7)]

[ wxID_IMCALIBRATE,wxID_IMRECALIBRATE,wxID_IMINTEGRATE, wxID_IMCLEARCALIB,wxID_IMRECALIBALL,  
    wxID_IMCOPYCONTROLS, wxID_INTEGRATEALL, wxID_IMSAVECONTROLS, wxID_IMLOADCONTROLS, wxID_IMAUTOINTEG,
    wxID_IMCOPYSELECTED, wxID_SAVESELECTEDCONTROLS, wxID_IMXFERCONTROLS,wxID_IMRESETDIST,
] = [wx.NewId() for item in range(14)]

[ wxID_MASKCOPY, wxID_MASKSAVE, wxID_MASKLOAD, wxID_NEWMASKSPOT,wxID_NEWMASKARC,wxID_NEWMASKRING,
    wxID_NEWMASKFRAME, wxID_NEWMASKPOLY,wxID_MASKLOADNOT,wxID_FINDSPOTS,wxID_DELETESPOTS
] = [wx.NewId() for item in range(11)]

[ wxID_STRSTACOPY, wxID_STRSTAFIT, wxID_STRSTASAVE, wxID_STRSTALOAD,wxID_STRSTSAMPLE,
    wxID_APPENDDZERO,wxID_STRSTAALLFIT,wxID_UPDATEDZERO,wxID_STRSTAPLOT,wxID_STRRINGSAVE,
] = [wx.NewId() for item in range(10)]

[ wxID_BACKCOPY,wxID_LIMITCOPY, wxID_SAMPLECOPY, wxID_SAMPLECOPYSOME, wxID_BACKFLAGCOPY, wxID_SAMPLEFLAGCOPY,
    wxID_SAMPLESAVE, wxID_SAMPLELOAD,wxID_ADDEXCLREGION,wxID_SETSCALE,wxID_SAMPLE1VAL,wxID_ALLSAMPLELOAD,
    wxID_MAKEBACKRDF,wxID_RESCALEALL,
] = [wx.NewId() for item in range(14)]

[ wxID_INSTPRMRESET,wxID_CHANGEWAVETYPE,wxID_INSTCOPY, wxID_INSTFLAGCOPY, wxID_INSTLOAD,
    wxID_INSTSAVE, wxID_INST1VAL, wxID_INSTCALIB,wxID_INSTSAVEALL,
] = [wx.NewId() for item in range(9)]

[ wxID_UNDO,wxID_LSQPEAKFIT,wxID_LSQONECYCLE,wxID_RESETSIGGAM,wxID_CLEARPEAKS,wxID_AUTOSEARCH,
    wxID_PEAKSCOPY, wxID_SEQPEAKFIT,
] = [wx.NewId() for item in range(8)]

[  wxID_INDXRELOAD, wxID_INDEXPEAKS, wxID_REFINECELL, wxID_COPYCELL, wxID_MAKENEWPHASE,
    wxID_EXPORTCELLS,
] = [wx.NewId() for item in range(6)]

[ wxID_CONSTRAINTADD,wxID_EQUIVADD,wxID_HOLDADD,wxID_FUNCTADD,wxID_ADDRIDING,
  wxID_CONSPHASE, wxID_CONSHIST, wxID_CONSHAP, wxID_CONSGLOBAL,wxID_EQUIVALANCEATOMS,
] = [wx.NewId() for item in range(10)]

[ wxID_RESTRAINTADD, wxID_RESTSELPHASE,wxID_RESTDELETE, wxID_RESRCHANGEVAL, 
    wxID_RESTCHANGEESD,wxID_AARESTRAINTADD,wxID_AARESTRAINTPLOT,
] = [wx.NewId() for item in range(7)]

[ wxID_RIGIDBODYADD,wxID_DRAWDEFINERB,wxID_RIGIDBODYIMPORT,wxID_RESIDUETORSSEQ,
    wxID_AUTOFINDRESRB,wxID_GLOBALRESREFINE,wxID_RBREMOVEALL,wxID_COPYRBPARMS,
    wxID_GLOBALTHERM,wxID_VECTORBODYADD
] = [wx.NewId() for item in range(10)]

[ wxID_RENAMESEQSEL,wxID_SAVESEQSEL,wxID_SAVESEQSELCSV,wxID_SAVESEQCSV,wxID_PLOTSEQSEL,
  wxID_ORGSEQSEL,wxADDSEQVAR,wxDELSEQVAR,wxEDITSEQVAR,wxCOPYPARFIT,wxID_AVESEQSEL,
  wxADDPARFIT,wxDELPARFIT,wxEDITPARFIT,wxDOPARFIT,wxADDSEQDIST,wxADDSEQANGLE
] = [wx.NewId() for item in range(17)]

[ wxID_MODELCOPY,wxID_MODELFIT,wxID_MODELADD,wxID_ELEMENTADD,wxID_ELEMENTDELETE,
    wxID_ADDSUBSTANCE,wxID_LOADSUBSTANCE,wxID_DELETESUBSTANCE,wxID_COPYSUBSTANCE,
    wxID_MODELUNDO,wxID_MODELFITALL,wxID_MODELCOPYFLAGS,wxID_RELOADSUBSTANCES,
    wxID_MODELPLOT,
] = [wx.NewId() for item in range(14)]

[ wxID_SELECTPHASE,wxID_PWDHKLPLOT,wxID_PWD3DHKLPLOT,wxID_3DALLHKLPLOT,wxID_MERGEHKL,
] = [wx.NewId() for item in range(5)]

[ wxID_PDFCOPYCONTROLS, wxID_PDFSAVECONTROLS, wxID_PDFLOADCONTROLS, wxID_PDFCOMPUTE, 
    wxID_PDFCOMPUTEALL, wxID_PDFADDELEMENT, wxID_PDFDELELEMENT, wxID_PDFPKSFIT,
    wxID_PDFPKSFITALL,wxID_PDFCOPYPEAKS,wxID_CLEARPDFPEAKS,
] = [wx.NewId() for item in range(11)]

[ wxID_MCRON,wxID_MCRLIST,wxID_MCRSAVE,wxID_MCRPLAY,
] = [wx.NewId() for item in range(4)]

VERY_LIGHT_GREY = wx.Colour(235,235,235)

commonTrans = {'abc':np.eye(3),'a-cb':np.array([[1.,0.,0.],[0.,0.,-1.],[0.,1.,0.]]),
    'ba-c':np.array([[0.,1.,0.],[1.,0.,0.],[0.,0.,-1.]]),'-cba':np.array([[0.,0.,-1.],[0.,1.,0.],[1.,0.,0.]]),
    'bca':np.array([[0.,1.,0.],[0.,0.,1.],[1.,0.,0.]]),'cab':np.array([[0.,0.,1.],[1.,0.,0.],[0.,1.,0.]]),
    'R->H':np.array([[1.,-1.,0.],[0.,1.,-1.],[1.,1.,1.]]),'H->R':np.array([[2./3,1./3,1./3],[-1./3,1./3,1./3],[-1./3,-2./3,1./3]]),
    'P->A':np.array([[-1.,0.,0.],[0.,-1.,1.],[0.,1.,1.]]),'R->O':np.array([[-1.,0.,0.],[0.,-1.,0.],[0.,0.,1.]]),
    'P->B':np.array([[-1.,0.,1.],[0.,-1.,0.],[1.,0.,1.]]),'B->P':np.array([[-.5,0.,.5],[0.,-1.,0.],[.5,0.,.5]]),
    'P->C':np.array([[1.,1.,0.],[1.,-1.,0.],[0.,0.,-1.]]),'C->P':np.array([[.5,.5,0.],[.5,-.5,0.],[0.,0.,-1.]]),
    'P->F':np.array([[-1.,1.,1.],[1.,-1.,1.],[1.,1.,-1.]]),'F->P':np.array([[0.,.5,.5],[.5,0.,.5],[.5,.5,0.]]),   
    'P->I':np.array([[0.,1.,1.],[1.,0.,1.],[1.,1.,0.]]),'I->P':np.array([[-.5,.5,.5],[.5,-.5,.5],[.5,.5,-.5]]),    
    'A->P':np.array([[-1.,0.,0.],[0.,-.5,.5],[0.,.5,.5]]),'O->R':np.array([[-1.,0.,0.],[0.,-1.,0.],[0.,0.,1.]]), 
    'abc*':np.eye(3), }
commonNames = ['abc','bca','cab','a-cb','ba-c','-cba','P->A','A->P','P->B','B->P','P->C','C->P',
    'P->I','I->P','P->F','F->P','H->R','R->H','R->O','O->R','abc*','setting 1->2']          #don't put any new ones after the setting one!

# Should SGMessageBox, SymOpDialog, DisAglDialog be moved? 

################################################################################
#### GSAS-II class definitions
################################################################################

class SGMessageBox(wx.Dialog):
    ''' Special version of MessageBox that displays space group & super space group text
    in two blocks
    '''
    def __init__(self,parent,title,text,table,):
        wx.Dialog.__init__(self,parent,wx.ID_ANY,title,pos=wx.DefaultPosition,
            style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.text = text
        self.table = table
        self.panel = wx.Panel(self)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add((0,10))
        for line in text:
            mainSizer.Add(wx.StaticText(self.panel,label='     %s     '%(line)),0,WACV)
        ncol = self.table[0].count(',')+1
        tableSizer = wx.FlexGridSizer(0,2*ncol+3,0,0)
        for j,item in enumerate(self.table):
            num,flds = item.split(')')
            tableSizer.Add(wx.StaticText(self.panel,label='     %s  '%(num+')')),0,WACV|wx.ALIGN_LEFT)            
            flds = flds.replace(' ','').split(',')
            for i,fld in enumerate(flds):
                if i < ncol-1:
                    tableSizer.Add(wx.StaticText(self.panel,label='%s, '%(fld)),0,WACV|wx.ALIGN_RIGHT)
                else:
                    tableSizer.Add(wx.StaticText(self.panel,label='%s'%(fld)),0,WACV|wx.ALIGN_RIGHT)
            if not j%2:
                tableSizer.Add((20,0))
        mainSizer.Add(tableSizer,0,wx.ALIGN_LEFT)
        btnsizer = wx.StdDialogButtonSizer()
        OKbtn = wx.Button(self.panel, wx.ID_OK)
        OKbtn.Bind(wx.EVT_BUTTON, self.OnOk)
        OKbtn.SetDefault()
        btnsizer.AddButton(OKbtn)
        btnsizer.Realize()
        mainSizer.Add((0,10))
        mainSizer.Add(btnsizer,0,wx.ALIGN_CENTER)
        self.panel.SetSizer(mainSizer)
        self.panel.Fit()
        self.Fit()
        size = self.GetSize()
        self.SetSize([size[0]+20,size[1]])

    def Show(self):
        '''Use this method after creating the dialog to post it
        '''
        self.ShowModal()
        return

    def OnOk(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_OK)

class SGMagSpinBox(wx.Dialog):
    ''' Special version of MessageBox that displays magnetic spin text
    '''
    def __init__(self,parent,title,text,table,names,spins,):
        wx.Dialog.__init__(self,parent,wx.ID_ANY,title,pos=wx.DefaultPosition,
            style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER,size=wx.Size(420,350))
        self.text = text
        self.table = table
        self.names = names
        self.spins = spins
        self.panel = wxscroll.ScrolledPanel(self)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add((0,10))
        first = text[0].split(':')[-1].strip()
        cents = [0,]
        if 'P' != first[0]:
            cents = text[-1].split(';')
        for line in text:
            mainSizer.Add(wx.StaticText(self.panel,label='     %s     '%(line)),0,WACV)
        ncol = self.table[0].count(',')+2
        for ic,cent in enumerate(cents):
            if cent:
                cent = cent.strip(' (').strip(')+\n') 
                mainSizer.Add(wx.StaticText(self.panel,label=' for (%s)+'%(cent)),0,WACV)
            tableSizer = wx.FlexGridSizer(0,2*ncol+3,0,0)
            for j,item in enumerate(self.table):
                flds = item.split(')')[1]
                tableSizer.Add(wx.StaticText(self.panel,label='  (%2d)  '%(j+1)),0,WACV|wx.ALIGN_LEFT)            
                flds = flds.replace(' ','').split(',')
                for i,fld in enumerate(flds):
                    if i < ncol-1:
                        text = wx.StaticText(self.panel,label='%s, '%(fld))
                        tableSizer.Add(text,0,WACV|wx.ALIGN_RIGHT)
                    else:
                        text = wx.StaticText(self.panel,label='%s '%(fld))
                        tableSizer.Add(text,0,WACV|wx.ALIGN_RIGHT)
                text = wx.StaticText(self.panel,label=' (%s) '%(self.names[j]))
                if self.spins[j+ic*len(self.table)] < 0:
                    text.SetForegroundColour('Red')
                tableSizer.Add(text,0,WACV|wx.ALIGN_RIGHT)
                if not j%2:
                    tableSizer.Add((20,0))
            mainSizer.Add(tableSizer,0,wx.ALIGN_CENTER)
            
        btnsizer = wx.StdDialogButtonSizer()
        OKbtn = wx.Button(self.panel, wx.ID_OK)
        OKbtn.SetDefault()
        btnsizer.AddButton(OKbtn)
        btnsizer.Realize()
        mainSizer.Add((0,10))
        mainSizer.Add(btnsizer,0,wx.ALIGN_CENTER)
        self.panel.SetSizer(mainSizer)
        size = np.array(self.GetSize())
        self.panel.SetupScrolling()
        size = [size[0]-5,size[1]-20]       #this fiddling is needed for older wx!
        self.panel.SetSize(size)
        self.panel.SetAutoLayout(1)

    def Show(self):
        '''Use this method after creating the dialog to post it
        '''
        self.ShowModal()
        return    

################################################################################
class SymOpDialog(wx.Dialog):
    '''Class to select a symmetry operator
    '''
    def __init__(self,parent,SGData,New=True,ForceUnit=False):
        wx.Dialog.__init__(self,parent,-1,'Select symmetry operator',
            pos=wx.DefaultPosition,style=wx.DEFAULT_DIALOG_STYLE)
        panel = wx.Panel(self)
        self.SGData = SGData
        self.New = New
        self.Force = ForceUnit
        self.OpSelected = [0,0,0,[0,0,0],False,False]
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        if ForceUnit:
            choice = ['No','Yes']
            self.force = wx.RadioBox(panel,-1,'Force to unit cell?',choices=choice)
            self.force.Bind(wx.EVT_RADIOBOX, self.OnOpSelect)
            mainSizer.Add(self.force,0,WACV|wx.TOP,5)
#        if SGData['SGInv']:
        choice = ['No','Yes']
        self.inv = wx.RadioBox(panel,-1,'Choose inversion?',choices=choice)
        self.inv.Bind(wx.EVT_RADIOBOX, self.OnOpSelect)
        mainSizer.Add(self.inv,0,WACV)
        if SGData['SGLatt'] != 'P':
            LattOp = G2spc.Latt2text(SGData['SGLatt']).split(';')
            self.latt = wx.RadioBox(panel,-1,'Choose cell centering?',choices=LattOp)
            self.latt.Bind(wx.EVT_RADIOBOX, self.OnOpSelect)
            mainSizer.Add(self.latt,0,WACV)
        if SGData['SGLaue'] in ['-1','2/m','mmm','4/m','4/mmm']:
            Ncol = 2
        else:
            Ncol = 3
        OpList = []
        for Opr in SGData['SGOps']:
            OpList.append(G2spc.MT2text(Opr))
        self.oprs = wx.RadioBox(panel,-1,'Choose space group operator?',choices=OpList,
            majorDimension=Ncol)
        self.oprs.Bind(wx.EVT_RADIOBOX, self.OnOpSelect)
        mainSizer.Add(self.oprs,0,WACV|wx.BOTTOM,5)
        mainSizer.Add(wx.StaticText(panel,-1,"   Choose unit cell?"),0,WACV)
        cellSizer = wx.BoxSizer(wx.HORIZONTAL)
        cellName = ['X','Y','Z']
        self.cell = []
        for i in range(3):
            self.cell.append(wx.SpinCtrl(panel,-1,cellName[i],size=wx.Size(50,20)))
            self.cell[-1].SetRange(-3,3)
            self.cell[-1].SetValue(0)
            self.cell[-1].Bind(wx.EVT_SPINCTRL, self.OnOpSelect)
            cellSizer.Add(self.cell[-1],0,WACV)
        mainSizer.Add(cellSizer,0,WACV|wx.BOTTOM,5)
        if self.New:
            choice = ['No','Yes']
            self.new = wx.RadioBox(panel,-1,'Generate new positions?',choices=choice)
            self.new.Bind(wx.EVT_RADIOBOX, self.OnOpSelect)
            mainSizer.Add(self.new,0,WACV)

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

    def OnOpSelect(self,event):
#        if self.SGData['SGInv']:
        self.OpSelected[0] = self.inv.GetSelection()
        if self.SGData['SGLatt'] != 'P':
            self.OpSelected[1] = self.latt.GetSelection()
        self.OpSelected[2] = self.oprs.GetSelection()
        for i in range(3):
            self.OpSelected[3][i] = float(self.cell[i].GetValue())
        if self.New:
            self.OpSelected[4] = self.new.GetSelection()
        if self.Force:
            self.OpSelected[5] = self.force.GetSelection()

    def GetSelection(self):
        return self.OpSelected

    def OnOk(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_OK)

    def OnCancel(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_CANCEL)
        
################################################################################
class SphereEnclosure(wx.Dialog):
    ''' Add atoms within sphere of enclosure to drawing
    
    :param wx.Frame parent: reference to parent frame (or None)
    :param general: general data (includes drawing data)
    :param atoms: drawing atoms data
    :param indx: list of selected atoms (may be empty)
    
    '''
    def __init__(self,parent,general,drawing,indx):
        wx.Dialog.__init__(self,parent,wx.ID_ANY,'Setup phase transformation', 
            pos=wx.DefaultPosition,style=wx.DEFAULT_DIALOG_STYLE)
        self.panel = wx.Panel(self)         #just a dummy - gets destroyed in Draw!
        self.General = general
        self.Drawing = drawing
        self.indx = indx
        self.Sphere = 1.0
        self.centers = []
        self.atomTypes = [[item,True] for item in self.General['AtomTypes']]
        
        self.Draw()
        
    def Draw(self):
        
        def OnAtomType(event):
            Obj = event.GetEventObject()
            id = Ind[Obj.GetId()]
            self.atomTypes[id][1] = Obj.GetValue()
        
        self.panel.Destroy()
        self.panel = wx.Panel(self)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(wx.StaticText(self.panel,label=' Sphere of enclosure controls:'),0,WACV)
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        atoms = []
        if len(self.indx):
            topSizer.Add(wx.StaticText(self.panel,label=' Sphere centered at atoms: '),0,WACV)
            cx,ct,cs = self.Drawing['atomPtrs'][:3]
            for id in self.indx:
                atom = self.Drawing['Atoms'][id]
                self.centers.append(atom[cx:cx+3])
                atoms.append('%s(%s)'%(atom[ct-1],atom[cs-1]))
            topSizer.Add(wx.ComboBox(self.panel,choices=atoms,value=atoms[0],
                style=wx.CB_READONLY|wx.CB_DROPDOWN),0,WACV)
        else:
            topSizer.Add(wx.StaticText(self.panel,label=' Sphere centered at drawing view point'),0,WACV)
            self.centers.append(self.Drawing['viewPoint'][0])
        mainSizer.Add(topSizer,0,WACV)
        sphereSizer = wx.BoxSizer(wx.HORIZONTAL)
        sphereSizer.Add(wx.StaticText(self.panel,label=' Sphere radius: '),0,WACV)
        radius = G2G.ValidatedTxtCtrl(self.panel,self.Sphere,nDig=(10,3),size=(65,25))
        sphereSizer.Add(radius,0,WACV)
        mainSizer.Add(sphereSizer,0,WACV)
        mainSizer.Add(wx.StaticText(self.panel,label=' Target selected atoms:'),0,WACV)
        atSizer = wx.BoxSizer(wx.HORIZONTAL)
        Ind = {}
        for i,item in enumerate(self.atomTypes):
            atm = wx.CheckBox(self.panel,label=item[0])
            atm.SetValue(item[1])
            atm.Bind(wx.EVT_CHECKBOX, OnAtomType)
            Ind[atm.GetId()] = i
            atSizer.Add(atm,0,WACV)
        mainSizer.Add(atSizer,0,WACV)
        
        OkBtn = wx.Button(self.panel,-1,"Ok")
        OkBtn.Bind(wx.EVT_BUTTON, self.OnOk)
        cancelBtn = wx.Button(self.panel,-1,"Cancel")
        cancelBtn.Bind(wx.EVT_BUTTON, self.OnCancel)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20),1)
        btnSizer.Add(OkBtn)
        btnSizer.Add((20,20),1)
        btnSizer.Add(cancelBtn)
        btnSizer.Add((20,20),1)
        
        mainSizer.Add(btnSizer,0,wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        self.panel.SetSizer(mainSizer)
        self.panel.Fit()
        self.Fit()
        
    def GetSelection(self):
        used = []
        for atm in self.atomTypes:
            if atm[1]:
                used.append(str(atm[0]))
        return self.centers,self.Sphere,used

    def OnOk(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_OK)

    def OnCancel(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_CANCEL)
        
################################################################################
class TransformDialog(wx.Dialog):
    ''' Phase transformation
    
    :param wx.Frame parent: reference to parent frame (or None)
    :param phase: phase data
    
    #NB: commonNames & commonTrans defined at top of this file 
    '''
    def __init__(self,parent,phase):
        wx.Dialog.__init__(self,parent,wx.ID_ANY,'Setup phase transformation', 
            pos=wx.DefaultPosition,style=wx.DEFAULT_DIALOG_STYLE)
        self.panel = wx.Panel(self)         #just a dummy - gets destroyed in Draw!
        self.Phase = copy.deepcopy(phase)   #will be a new phase!
#        self.Super = phase['General']['Super']
#        if self.Super:
#            self.Trans = np.eye(4)
#            self.Vec = np.zeros(4)
#        else:
        self.Trans = np.eye(3)
        self.Vec = np.zeros(3)
        self.oldSpGrp = phase['General']['SGData']['SpGrp']
        self.oldSGdata = phase['General']['SGData']
        self.newSpGrp = self.Phase['General']['SGData']['SpGrp']
        self.oldCell = phase['General']['Cell'][1:8]
        self.newCell = self.Phase['General']['Cell'][1:8]
        self.Common = 'abc'
        self.ifMag = False
        self.ifConstr = True
        self.Draw()

    def Draw(self):
                
        def OnCommon(event):
            Obj = event.GetEventObject()
            self.Common = Obj.GetValue()
            if '*' in self.Common:
                A,B = G2lat.cell2AB(self.oldCell[:6])
                self.newCell[2:5] = [A[2,2],90.,90.]
                a,b = G2lat.cell2AB(self.newCell[:6])
                self.Trans = np.inner(a.T,B)    #correct!
                self.ifConstr = False
                self.newSpGrp = 'P 1'
                SGErr,SGData = G2spc.SpcGroup(self.newSpGrp)
                self.Phase['General']['SGData'] = SGData
            else:
                if self.Common == commonNames[-1]:      #change setting
                    self.Vec = G2spc.spg2origins[self.oldSpGrp]
                    self.newSpGrp = self.oldSpGrp
                else:
                    self.Trans = commonTrans[self.Common]
                    if 'R' == self.Common[-1]:
                        self.newSpGrp += ' r'
                        SGErr,SGData = G2spc.SpcGroup(self.newSpGrp)
                        self.Phase['General']['SGData'] = SGData
                        SGTxt.SetValue(self.newSpGrp)
            OnTest(event)
       
        def OnSpaceGroup(event):
            event.Skip()
            Flds = SGTxt.GetValue().split()
            Flds[0] = Flds[0].upper()
            #get rid of extra spaces between fields first
            for fld in Flds: fld = fld.strip()
            SpcGp = ' '.join(Flds)
            if SpcGp == self.newSpGrp: #didn't change it!
                return
            # try a lookup on the user-supplied name
            SpGrpNorm = G2spc.StandardizeSpcName(SpcGp)
            if SpGrpNorm:
                SGErr,SGData = G2spc.SpcGroup(SpGrpNorm)
            else:
                SGErr,SGData = G2spc.SpcGroup(SpcGp)
            if SGErr:
                text = [G2spc.SGErrors(SGErr)+'\nSpace Group set to previous']
                SGTxt.SetValue(self.newSpGrp)
                msg = 'Space Group Error'
                Style = wx.ICON_EXCLAMATION
                Text = '\n'.join(text)
                wx.MessageBox(Text,caption=msg,style=Style)
            else:
                text,table = G2spc.SGPrint(SGData)
                self.Phase['General']['SGData'] = SGData
                self.newSpGrp = SpcGp
                SGTxt.SetValue(self.Phase['General']['SGData']['SpGrp'])
                msg = 'Space Group Information'
                SGMessageBox(self.panel,msg,text,table).Show()
            if self.Phase['General']['Type'] == 'magnetic':
                Nops = len(SGData['SGOps'])*len(SGData['SGCen'])
                if SGData['SGInv']:
                    Nops *= 2
                SGData['SpnFlp'] = Nops*[1,]
#            if self.Phase['General']['Type'] in ['modulated',]:
#                self.Phase['General']['SuperSg'] = SetDefaultSSsymbol()
#                self.Phase['General']['SSGData'] = G2spc.SSpcGroup(generalData['SGData'],generalData['SuperSg'])[1]

        def OnTest(event):
            self.newCell = G2lat.TransformCell(self.oldCell[:6],self.Trans)
            wx.CallAfter(self.Draw)
            
        def OnMag(event):
            self.ifMag = mag.GetValue()
            
        def OnConstr(event):
            self.ifConstr = constr.GetValue()

        self.panel.Destroy()
        self.panel = wx.Panel(self)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        MatSizer = wx.BoxSizer(wx.HORIZONTAL)
        transSizer = wx.BoxSizer(wx.VERTICAL)
        transSizer.Add(wx.StaticText(self.panel,label=" XYZ Transformation matrix & vector: M*X+V = X'"))
#        if self.Super:
#            Trmat = wx.FlexGridSizer(4,4,0,0)
#        else:
        commonSizer = wx.BoxSizer(wx.HORIZONTAL)
        commonSizer.Add(wx.StaticText(self.panel,label=' Common transformations: '),0,WACV)
        if self.oldSpGrp not in G2spc.spg2origins:
            common = wx.ComboBox(self.panel,value=self.Common,choices=commonNames[:-1],
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
        else:
            common = wx.ComboBox(self.panel,value=self.Common,choices=commonNames,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
        common.Bind(wx.EVT_COMBOBOX,OnCommon)
        commonSizer.Add(common,0,WACV)
        transSizer.Add(commonSizer)
        Trmat = wx.FlexGridSizer(3,5,0,0)
        for iy,line in enumerate(self.Trans):
            for ix,val in enumerate(line):
                item = G2G.ValidatedTxtCtrl(self.panel,self.Trans[iy],ix,nDig=(10,3),size=(65,25))
                Trmat.Add(item)
            Trmat.Add((25,0),0)
            vec = G2G.ValidatedTxtCtrl(self.panel,self.Vec,iy,nDig=(10,3),size=(65,25))
            Trmat.Add(vec)
        transSizer.Add(Trmat)
        MatSizer.Add((10,0),0)
        MatSizer.Add(transSizer)
        mainSizer.Add(MatSizer)
        mainSizer.Add(wx.StaticText(self.panel,label=' Old lattice parameters:'),0,WACV)
        mainSizer.Add(wx.StaticText(self.panel,label=
            ' a = %.5f       b = %.5f      c = %.5f'%(self.oldCell[0],self.oldCell[1],self.oldCell[2])),0,WACV)
        mainSizer.Add(wx.StaticText(self.panel,label=' alpha = %.3f beta = %.3f gamma = %.3f'%
            (self.oldCell[3],self.oldCell[4],self.oldCell[5])),0,WACV)
        mainSizer.Add(wx.StaticText(self.panel,label=' volume = %.3f'%(self.oldCell[6])),0,WACV)
        mainSizer.Add(wx.StaticText(self.panel,label=' New lattice parameters:'),0,WACV)
        mainSizer.Add(wx.StaticText(self.panel,label=
            ' a = %.5f       b = %.5f      c = %.5f'%(self.newCell[0],self.newCell[1],self.newCell[2])),0,WACV)
        mainSizer.Add(wx.StaticText(self.panel,label=' alpha = %.3f beta = %.3f gamma = %.3f'%
            (self.newCell[3],self.newCell[4],self.newCell[5])),0,WACV)
        mainSizer.Add(wx.StaticText(self.panel,label=' volume = %.3f'%(self.newCell[6])),0,WACV)
        sgSizer = wx.BoxSizer(wx.HORIZONTAL)
        sgSizer.Add(wx.StaticText(self.panel,label='  Space group: '),0,WACV)
        SGTxt = wx.TextCtrl(self.panel,value=self.newSpGrp,style=wx.TE_PROCESS_ENTER)
        SGTxt.Bind(wx.EVT_TEXT_ENTER,OnSpaceGroup)
        SGTxt.Bind(wx.EVT_KILL_FOCUS,OnSpaceGroup)
        sgSizer.Add(SGTxt,0,WACV)
        mainSizer.Add(sgSizer,0,WACV)
        if 'magnetic' not in self.Phase['General']['Type']:
            mag = wx.CheckBox(self.panel,label=' Make new phase magnetic?')
            mag.Bind(wx.EVT_CHECKBOX,OnMag)
            mainSizer.Add(mag,0,WACV)
            mainSizer.Add(wx.StaticText(self.panel, \
                label=' NB: Nonmagnetic atoms will be deleted from new phase'),0,WACV)
            constr = wx.CheckBox(self.panel,label=' Make constraints between phases?')
            mainSizer.Add(wx.StaticText(self.panel, \
                label=' Constraints not correct for non-diagonal transforms'),0,WACV)
            constr.SetValue(self.ifConstr)
            constr.Bind(wx.EVT_CHECKBOX,OnConstr)
            mainSizer.Add(constr,0,WACV)

        TestBtn = wx.Button(self.panel,-1,"Test")
        TestBtn.Bind(wx.EVT_BUTTON, OnTest)
        OkBtn = wx.Button(self.panel,-1,"Ok")
        OkBtn.Bind(wx.EVT_BUTTON, self.OnOk)
        cancelBtn = wx.Button(self.panel,-1,"Cancel")
        cancelBtn.Bind(wx.EVT_BUTTON, self.OnCancel)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20),1)
        btnSizer.Add(TestBtn)
        btnSizer.Add((20,20),1)
        btnSizer.Add(OkBtn)
        btnSizer.Add((20,20),1)
        btnSizer.Add(cancelBtn)
        btnSizer.Add((20,20),1)
        
        mainSizer.Add(btnSizer,0,wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        self.panel.SetSizer(mainSizer)
        self.panel.Fit()
        self.Fit()
        
    def GetSelection(self):
        if self.ifMag:
            self.Phase['General']['Name'] += ' mag'
        else:
            self.Phase['General']['Name'] += ' %s'%(self.Common)
        self.Phase['General']['Cell'][1:] = G2lat.TransformCell(self.oldCell[:6],self.Trans)            
        return self.Phase,self.Trans,self.Vec,self.ifMag,self.ifConstr,self.Common

    def OnOk(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_OK)

    def OnCancel(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_CANCEL)
################################################################################
class UseMagAtomDialog(wx.Dialog):
    '''Get user selected magnetic atoms after cell transformation
    '''
    def __init__(self,parent,Atoms,atCodes):
        wx.Dialog.__init__(self,parent,wx.ID_ANY,'Magnetic atom selection', 
            pos=wx.DefaultPosition,style=wx.DEFAULT_DIALOG_STYLE)
        self.panel = wx.Panel(self)         #just a dummy - gets destroyed in Draw!
        self.Atoms = Atoms
        self.atCodes = atCodes
        self.Use = len(self.Atoms)*[True,]
        self.Draw()
        
    def Draw(self):
        
        def OnUseChk(event):
            Obj = event.GetEventObject()
            iuse = Indx[Obj.GetId()]
            self.Use[iuse] = not self.Use[iuse]
            Obj.SetValue(self.Use[iuse])
        
        self.panel.Destroy()
        self.panel = wx.Panel(self)
        Indx = {}
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        mainSizer.Add(wx.StaticText(self.panel,label=' Name, x, y, z:'),0,WACV)
        atmSizer = wx.FlexGridSizer(0,2,5,5)
        for iuse,[use,atom] in enumerate(zip(self.Use,self.Atoms)):
            useChk = wx.CheckBox(self.panel,label='Use?')
            Indx[useChk.GetId()] = iuse
            useChk.SetValue(use)
            useChk.Bind(wx.EVT_CHECKBOX, OnUseChk)
            atmSizer.Add(useChk,0,WACV)
            text = ' %s %10.5f %10.5f %10.5f'%(atom[0],atom[3],atom[4],atom[5])
            atmSizer.Add(wx.StaticText(self.panel,label=text),0,WACV)
        mainSizer.Add(atmSizer)
        
        OkBtn = wx.Button(self.panel,-1,"Ok")
        OkBtn.Bind(wx.EVT_BUTTON, self.OnOk)
        cancelBtn = wx.Button(self.panel,-1,"Use All")
        cancelBtn.Bind(wx.EVT_BUTTON, self.OnCancel)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20),1)
        btnSizer.Add(OkBtn)
        btnSizer.Add((20,20),1)
        btnSizer.Add(cancelBtn)
        btnSizer.Add((20,20),1)
        
        mainSizer.Add(btnSizer,0,wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        self.panel.SetSizer(mainSizer)
        self.panel.Fit()
        self.Fit()
        
    def GetSelection(self):
        useAtoms = []
        useatCodes = []
        for use,atom,code in zip(self.Use,self.Atoms,self.atCodes):
            if use:
                useAtoms.append(atom)
                useatCodes.append(code)
        return useAtoms,useatCodes

    def OnOk(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_OK)

    def OnCancel(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_CANCEL)
            
                
################################################################################
class RotationDialog(wx.Dialog):
    ''' Get Rotate & translate matrix & vector - currently not used
    needs rethinking - possible use to rotate a group of atoms about some
    vector/origin + translation
    
    '''
    def __init__(self,parent):
        wx.Dialog.__init__(self,parent,wx.ID_ANY,'Atom group rotation/translation', 
            pos=wx.DefaultPosition,style=wx.DEFAULT_DIALOG_STYLE)
        self.panel = wx.Panel(self)         #just a dummy - gets destroyed in Draw!
        self.Trans = np.eye(3)
        self.Vec = np.zeros(3)
        self.rotAngle = 0.
        self.rotVec = np.array([0.,0.,1.])
        self.Expand = ''
        self.Draw()

    def Draw(self):

        def OnExpand(event):
            self.Expand = expand.GetValue()
            
        def OnRotAngle(event):
            event.Skip()
            self.rotAngle = float(rotangle.GetValue())
            rotangle.SetValue('%5.3f'%(self.rotAngle))
            Q = G2mth.AVdeg2Q(self.rotAngle,self.rotVec)
            self.Trans = G2mth.Q2Mat(Q)
            self.Draw()
            
        def OnRotVec(event):
            event.Skip()
            vals = rotvec.GetValue()
            vals = vals.split()
            self.rotVec = np.array([float(val) for val in vals])
            rotvec.SetValue('%5.3f %5.3f %5.3f'%(self.rotVec[0],self.rotVec[1],self.rotVec[2]))
            Q = G2mth.AVdeg2Q(self.rotAngle,self.rotVec)
            self.Trans = G2mth.Q2Mat(Q)
            self.Draw()
            
        self.panel.Destroy()
        self.panel = wx.Panel(self)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        MatSizer = wx.BoxSizer(wx.HORIZONTAL)
        transSizer = wx.BoxSizer(wx.VERTICAL)
        transSizer.Add(wx.StaticText(self.panel,label=" XYZ Transformation matrix && vector: "+ \
            "\n B*M*A*(X-V)+V = X'\n A,B: Cartesian transformation matrices"))
        Trmat = wx.FlexGridSizer(3,5,0,0)
        for iy,line in enumerate(self.Trans):
            for ix,val in enumerate(line):
                item = G2G.ValidatedTxtCtrl(self.panel,self.Trans[iy],ix,nDig=(10,3),size=(65,25))
                Trmat.Add(item)
            Trmat.Add((25,0),0)
            vec = G2G.ValidatedTxtCtrl(self.panel,self.Vec,iy,nDig=(10,3),size=(65,25))
            Trmat.Add(vec)
        transSizer.Add(Trmat)
        MatSizer.Add((10,0),0)
        MatSizer.Add(transSizer)
        mainSizer.Add(MatSizer)
        rotationBox = wx.BoxSizer(wx.HORIZONTAL)
        rotationBox.Add(wx.StaticText(self.panel,label=' Rotation angle: '),0,WACV)
        rotangle = wx.TextCtrl(self.panel,value='%5.3f'%(self.rotAngle),
            size=(50,25),style=wx.TE_PROCESS_ENTER)
        rotangle.Bind(wx.EVT_TEXT_ENTER,OnRotAngle)
        rotangle.Bind(wx.EVT_KILL_FOCUS,OnRotAngle)
        rotationBox.Add(rotangle,0,WACV)
        rotationBox.Add(wx.StaticText(self.panel,label=' about vector: '),0,WACV)
        rotvec = wx.TextCtrl(self.panel,value='%5.3f %5.3f %5.3f'%(self.rotVec[0],self.rotVec[1],self.rotVec[2]),
            size=(100,25),style=wx.TE_PROCESS_ENTER)
        rotvec.Bind(wx.EVT_TEXT_ENTER,OnRotVec)
        rotvec.Bind(wx.EVT_KILL_FOCUS,OnRotVec)
        rotationBox.Add(rotvec,0,WACV)
        mainSizer.Add(rotationBox,0,WACV)
        expandChoice = ['','xy','xz','yz','xyz']
        expandBox = wx.BoxSizer(wx.HORIZONTAL)
        expandBox.Add(wx.StaticText(self.panel,label=' Expand -1 to +1 on: '),0,WACV)
        expand = wx.ComboBox(self.panel,value=self.Expand,choices=expandChoice,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        expand.Bind(wx.EVT_COMBOBOX,OnExpand)
        expandBox.Add(expand,0,WACV)
        expandBox.Add(wx.StaticText(self.panel,label=' and find unique atoms '),0,WACV)        
        mainSizer.Add(expandBox)
                
        OkBtn = wx.Button(self.panel,-1,"Ok")
        OkBtn.Bind(wx.EVT_BUTTON, self.OnOk)
        cancelBtn = wx.Button(self.panel,-1,"Cancel")
        cancelBtn.Bind(wx.EVT_BUTTON, self.OnCancel)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20),1)
        btnSizer.Add(OkBtn)
        btnSizer.Add((20,20),1)
        btnSizer.Add(cancelBtn)
        btnSizer.Add((20,20),1)
        
        mainSizer.Add(btnSizer,0,wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        self.panel.SetSizer(mainSizer)
        self.panel.Fit()
        self.Fit()

    def GetSelection(self):
        return self.Trans,self.Vec,self.Expand

    def OnOk(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_OK)

    def OnCancel(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_CANCEL)    
        
################################################################################
class DIFFaXcontrols(wx.Dialog):
    ''' Solicit items needed to prepare DIFFaX control.dif file
    '''
    def __init__(self,parent,ctrls,parms=None):
        wx.Dialog.__init__(self,parent,wx.ID_ANY,'DIFFaX controls', 
            pos=wx.DefaultPosition,style=wx.DEFAULT_DIALOG_STYLE)
        self.panel = wx.Panel(self)         #just a dummy - gets destroyed in Draw!
        self.ctrls = ctrls
        self.calcType = 'powder pattern'
        self.plane = 'h0l'
        self.planeChoice = ['h0l','0kl','hhl','h-hl',]
        self.lmax = '2'
        self.lmaxChoice = [str(i+1) for i in range(6)]
        self.Parms = parms
        self.Parm = None
        if self.Parms != None:
            self.Parm = self.Parms[0]
        self.parmRange = [0.,1.]
        self.parmStep = 2
        self.Inst = 'Gaussian'
        self.Draw()
        
    def Draw(self):
        
        def OnCalcType(event):
            self.calcType = calcType.GetValue()
            wx.CallAfter(self.Draw)
            
        def OnPlane(event):
            self.plane = plane.GetValue()
            
        def OnMaxL(event):
            self.lmax = lmax.GetValue()
            
        def OnParmSel(event):
            self.Parm = parmsel.GetValue()
            
        def OnNumStep(event):
            self.parmStep = int(numStep.GetValue())
            
        def OnParmRange(event):
            event.Skip()
            vals = parmrange.GetValue().split()
            try:
                vals = [float(vals[0]),float(vals[1])]
            except ValueError:
                vals = self.parmRange
            parmrange.SetValue('%.3f %.3f'%(vals[0],vals[1]))
            self.parmRange = vals
            
        def OnInstSel(event):
            self.Inst = instsel.GetValue()
        
        self.panel.Destroy()
        self.panel = wx.Panel(self)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(wx.StaticText(self.panel,label=' Controls for DIFFaX'),0,WACV)
        if self.Parms:
            mainSizer.Add(wx.StaticText(self.panel,label=' Sequential powder pattern simulation'),0,WACV)
        else:
            calcChoice = ['powder pattern','selected area']
            calcSizer = wx.BoxSizer(wx.HORIZONTAL)
            calcSizer.Add(wx.StaticText(self.panel,label=' Select calculation type: '),0,WACV)
            calcType = wx.ComboBox(self.panel,value=self.calcType,choices=calcChoice,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
            calcType.Bind(wx.EVT_COMBOBOX,OnCalcType)
            calcSizer.Add(calcType,0,WACV)
            mainSizer.Add(calcSizer)
        if self.Parms:
            parmSel = wx.BoxSizer(wx.HORIZONTAL)
            parmSel.Add(wx.StaticText(self.panel,label=' Select parameter to vary: '),0,WACV)
            parmsel = wx.ComboBox(self.panel,value=self.Parm,choices=self.Parms,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
            parmsel.Bind(wx.EVT_COMBOBOX,OnParmSel)
            parmSel.Add(parmsel,0,WACV)
            mainSizer.Add(parmSel)
            mainSizer.Add(wx.StaticText(self.panel,label=' Enter parameter range & no. steps: '),0,WACV)
            parmRange =  wx.BoxSizer(wx.HORIZONTAL)
            numChoice = [str(i+1) for i in range(10)]
            parmrange = wx.TextCtrl(self.panel,value='%.3f %.3f'%(self.parmRange[0],self.parmRange[1]),
                style=wx.TE_PROCESS_ENTER)
            parmrange.Bind(wx.EVT_TEXT_ENTER,OnParmRange)
            parmrange.Bind(wx.EVT_KILL_FOCUS,OnParmRange)
            parmRange.Add(parmrange,0,WACV)
            numStep = wx.ComboBox(self.panel,value=str(self.parmStep),choices=numChoice,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
            numStep.Bind(wx.EVT_COMBOBOX,OnNumStep)
            parmRange.Add(numStep,0,WACV)
            mainSizer.Add(parmRange)            
        if 'selected' in self.calcType:
            planeSizer = wx.BoxSizer(wx.HORIZONTAL)
            planeSizer.Add(wx.StaticText(self.panel,label=' Select plane: '),0,WACV)
            plane = wx.ComboBox(self.panel,value=self.plane,choices=self.planeChoice,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
            plane.Bind(wx.EVT_COMBOBOX,OnPlane)
            planeSizer.Add(plane,0,WACV)
            planeSizer.Add(wx.StaticText(self.panel,label=' Max. l index: '),0,WACV)
            lmax = wx.ComboBox(self.panel,value=self.lmax,choices=self.lmaxChoice,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
            lmax.Bind(wx.EVT_COMBOBOX,OnMaxL)
            planeSizer.Add(lmax,0,WACV)            
            mainSizer.Add(planeSizer)
        else:
            instChoice = ['None','Mean Gaussian','Gaussian',]
            instSizer = wx.BoxSizer(wx.HORIZONTAL)
            instSizer.Add(wx.StaticText(self.panel,label=' Select instrument broadening: '),0,WACV)
            instsel = wx.ComboBox(self.panel,value=self.Inst,choices=instChoice,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
            instsel.Bind(wx.EVT_COMBOBOX,OnInstSel)
            instSizer.Add(instsel,0,WACV)
            mainSizer.Add(instSizer)
        OkBtn = wx.Button(self.panel,-1,"Ok")
        OkBtn.Bind(wx.EVT_BUTTON, self.OnOk)
        cancelBtn = wx.Button(self.panel,-1,"Cancel")
        cancelBtn.Bind(wx.EVT_BUTTON, self.OnCancel)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20),1)
        btnSizer.Add(OkBtn)
        btnSizer.Add((20,20),1)
        btnSizer.Add(cancelBtn)
        btnSizer.Add((20,20),1)
        
        mainSizer.Add(btnSizer,0,wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        self.panel.SetSizer(mainSizer)
        self.panel.Fit()
        self.Fit()
        
    def GetSelection(self):
        if 'powder' in self.calcType:
            return 'PWDR',self.Inst,self.Parm,self.parmRange,self.parmStep
        elif 'selected' in self.calcType:
            return 'SADP',self.plane,self.lmax

    def OnOk(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_OK)

    def OnCancel(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_CANCEL)
           
        
################################################################################
class MergeDialog(wx.Dialog):
    ''' HKL transformation & merge dialog
    
    :param wx.Frame parent: reference to parent frame (or None)
    :param data: HKLF data
    
    #NB: commonNames & commonTrans defined at top of this file     
    '''        
    def __init__(self,parent,data):
        wx.Dialog.__init__(self,parent,wx.ID_ANY,'Setup HKLF merge', 
            pos=wx.DefaultPosition,style=wx.DEFAULT_DIALOG_STYLE)
        self.panel = wx.Panel(self)         #just a dummy - gets destroyed in Draw!
        self.data = data
        self.Super = data[1]['Super']
        if self.Super:
            self.Trans = np.eye(4)
        else:
            self.Trans = np.eye(3)
        self.Cent = 'noncentrosymmetric'
        self.Laue = '1'
        self.Class = 'triclinic'
        self.Common = 'abc'
        self.Draw()
        
    def Draw(self):
                
        def OnCent(event):
            Obj = event.GetEventObject()
            self.Cent = Obj.GetValue()
            self.Laue = ''
            wx.CallAfter(self.Draw)
            
        def OnLaue(event):
            Obj = event.GetEventObject()
            self.Laue = Obj.GetValue()
            wx.CallAfter(self.Draw)
            
        def OnClass(event):
            Obj = event.GetEventObject()
            self.Class = Obj.GetValue()
            self.Laue = ''
            wx.CallAfter(self.Draw)
            
        def OnCommon(event):
            Obj = event.GetEventObject()
            self.Common = Obj.GetValue()
            self.Trans = commonTrans[self.Common]
            wx.CallAfter(self.Draw)
       
        self.panel.Destroy()
        self.panel = wx.Panel(self)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        MatSizer = wx.BoxSizer(wx.HORIZONTAL)
        transSizer = wx.BoxSizer(wx.VERTICAL)
        transSizer.Add(wx.StaticText(self.panel,label=" HKL Transformation matrix: M*H = H'"))
        if self.Super:
            Trmat = wx.FlexGridSizer(4,4,0,0)
        else:
            commonSizer = wx.BoxSizer(wx.HORIZONTAL)
            commonSizer.Add(wx.StaticText(self.panel,label=' Common transformations: '),0,WACV)
            common = wx.ComboBox(self.panel,value=self.Common,choices=commonNames[:-2], #not the last two!
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
            common.Bind(wx.EVT_COMBOBOX,OnCommon)
            commonSizer.Add(common,0,WACV)
            transSizer.Add(commonSizer)
            Trmat = wx.FlexGridSizer(3,3,0,0)
        for iy,line in enumerate(self.Trans):
            for ix,val in enumerate(line):
                item = G2G.ValidatedTxtCtrl(self.panel,self.Trans[iy],ix,nDig=(10,3),size=(65,25))
                Trmat.Add(item)
        transSizer.Add(Trmat)
        MatSizer.Add((10,0),0)
        MatSizer.Add(transSizer)
        mainSizer.Add(MatSizer)
        laueClass = ['triclinic','monoclinic','orthorhombic','trigonal(H)','tetragonal','hexagonal','cubic']
        centroLaue = {'triclinic':['-1',],'monoclinic':['2/m','1 1 2/m','2/m 1 1',],
            'orthorhombic':['m m m',],'trigonal(H)':['-3','-3 m 1','-3 1 m',],    \
            'tetragonal':['4/m','4/m m m',],'hexagonal':['6/m','6/m m m',],'cubic':['m 3','m 3 m']}
        noncentroLaue = {'triclinic':['1',],'monoclinic':['2','2 1 1','1 1 2','m','m 1 1','1 1 m',],
            'orthorhombic':['2 2 2','m m 2','m 2 m','2 m m',],
            'trigonal(H)':['3','3 1 2','3 2 1','3 m 1','3 1 m',],
            'tetragonal':['4','-4','4 2 2','4 m m','-4 2 m','-4 m 2',], \
            'hexagonal':['6','-6','6 2 2','6 m m','-6 m 2','-6 2 m',],'cubic':['2 3','4 3 2','-4 3 m']}
        centChoice = ['noncentrosymmetric','centrosymmetric']
        mainSizer.Add(wx.StaticText(self.panel,label=' Select Laue class for new lattice:'),0,WACV)
        Class = wx.ComboBox(self.panel,value=self.Class,choices=laueClass,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        Class.Bind(wx.EVT_COMBOBOX,OnClass)
        mainSizer.Add(Class,0,WACV)
        mainSizer.Add(wx.StaticText(self.panel,label=' Target Laue symmetry:'),0,WACV)
        Cent = wx.ComboBox(self.panel,value=self.Cent,choices=centChoice,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        Cent.Bind(wx.EVT_COMBOBOX,OnCent)
        mergeSizer = wx.BoxSizer(wx.HORIZONTAL)
        mergeSizer.Add(Cent,0,WACV)
        mergeSizer.Add((10,0),0)
        Choice = centroLaue[self.Class]
        if 'non' in self.Cent:
            Choice = noncentroLaue[self.Class]
        Laue = wx.ComboBox(self.panel,value=self.Laue,choices=Choice,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        Laue.Bind(wx.EVT_COMBOBOX,OnLaue)
        mergeSizer.Add(Laue,0,WACV)
        mainSizer.Add(mergeSizer)

        OkBtn = wx.Button(self.panel,-1,"Ok")
        OkBtn.Bind(wx.EVT_BUTTON, self.OnOk)
        cancelBtn = wx.Button(self.panel,-1,"Cancel")
        cancelBtn.Bind(wx.EVT_BUTTON, self.OnCancel)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20),1)
        if self.Laue:
            btnSizer.Add(OkBtn)
            btnSizer.Add((20,20),1)
        btnSizer.Add(cancelBtn)
        btnSizer.Add((20,20),1)
        
        mainSizer.Add(btnSizer,0,wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        self.panel.SetSizer(mainSizer)
        self.panel.Fit()
        self.Fit()
        
    def GetSelection(self):
        return self.Trans,self.Cent,self.Laue

    def OnOk(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_OK)

    def OnCancel(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_CANCEL)

        
################################################################################
class AddHatomDialog(wx.Dialog):
    '''H atom addition dialog. After :meth:`ShowModal` returns, the results 
    are found in dict :attr:`self.data`, which is accessed using :meth:`GetData`.
    
    :param wx.Frame parent: reference to parent frame (or None)
    :param dict Neigh: a dict of atom names with list of atom name, dist pairs for neighboring atoms
    :param dict phase: a dict containing the phase as defined by
      :ref:`Phase Tree Item <Phase_table>`    
    '''
    def __init__(self,parent,Neigh,phase):
        wx.Dialog.__init__(self,parent,wx.ID_ANY,'H atom add', 
            pos=wx.DefaultPosition,style=wx.DEFAULT_DIALOG_STYLE)
        self.panel = wxscroll.ScrolledPanel(self)         #just a dummy - gets destroyed in Draw!
        self.Neigh = Neigh
        self.phase = phase
        self.Hatoms = []
        self.Draw(self.Neigh,self.phase)
            
    def Draw(self,Neigh,phase):
        '''Creates the contents of the dialog. Normally called
        by :meth:`__init__`.
        '''
        def OnHSelect(event):
            Obj = event.GetEventObject()
            item,i = Indx[Obj.GetId()]
            for obj in Indx[item]:
                obj.SetValue(False)
            Obj.SetValue(True)
            self.Neigh[item][2] = i
            
        def OnBond(event):
            Obj = event.GetEventObject()
            inei,ibond = Indx[Obj.GetId()]
            self.Neigh[inei][1][0][ibond][2] = Obj.GetValue()
            
        self.panel.Destroy()
        self.panel = wxscroll.ScrolledPanel(self,style = wx.DEFAULT_DIALOG_STYLE)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(wx.StaticText(self.panel,-1,'H atom add controls for phase %s:'%(phase['General']['Name'])),
            0,wx.LEFT|wx.TOP,10)
        mainSizer.Add(wx.StaticText(self.panel,-1,'NB: Check selections as they may not be correct'),0,WACV|wx.LEFT,10)
        mainSizer.Add(wx.StaticText(self.panel,-1," Atom:  Add # H's          Use: Neighbors, dist"),0,wx.TOP|wx.LEFT,5)
        nHatms = ['0','1','2','3']
        dataSizer = wx.FlexGridSizer(0,3,0,0)
        Indx = {}
        for inei,neigh in enumerate(Neigh):
            dataSizer.Add(wx.StaticText(self.panel,-1,' %s:  '%(neigh[0])),0,WACV)
            nH = 1      #for O atom
            if 'C' in neigh[0] or 'N' in neigh[0]:
                nH = 4-len(neigh[1][0])
            checks = wx.BoxSizer(wx.HORIZONTAL)
            Ids = []
            for i in range(nH+1):
                nHs = wx.CheckBox(self.panel,-1,label=nHatms[i])
                if i == neigh[2]:
                    nHs.SetValue(True)
                Indx[nHs.GetId()] = [inei,i]
                Ids.append(nHs)
                nHs.Bind(wx.EVT_CHECKBOX, OnHSelect)
                checks.Add(nHs,0,WACV)
            Indx[inei] = Ids
            dataSizer.Add(checks,0,WACV)
            lineSizer = wx.BoxSizer(wx.HORIZONTAL)
            for ib,bond in enumerate(neigh[1][0]):
                Bond = wx.CheckBox(self.panel,-1,label=': %s, %.3f'%(bond[0],bond[1]))
                Bond.SetValue(bond[2])
                Indx[Bond.GetId()] = [inei,ib]
                Bond.Bind(wx.EVT_CHECKBOX,OnBond)                
                lineSizer.Add(Bond,0,WACV)                
            dataSizer.Add(lineSizer,0,WACV|wx.RIGHT,10)
        mainSizer.Add(dataSizer,0,wx.LEFT,5)

        CancelBtn = wx.Button(self.panel,-1,'Cancel')
        CancelBtn.Bind(wx.EVT_BUTTON, self.OnCancel)
        OkBtn = wx.Button(self.panel,-1,'Ok')
        OkBtn.Bind(wx.EVT_BUTTON, self.OnOk)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20),1)
        btnSizer.Add(OkBtn)
        btnSizer.Add((20,20),1)
        btnSizer.Add(CancelBtn)
        btnSizer.Add((20,20),1)
        mainSizer.Add(btnSizer,0,wx.BOTTOM|wx.TOP, 10)
        self.panel.SetSizer(mainSizer)
        size = np.array(self.GetSize())
        self.panel.SetupScrolling()
        self.panel.SetAutoLayout(1)
        size = [size[0]-5,size[1]-20]       #this fiddling is needed for older wx!
        self.panel.SetSize(size)
        
    def GetData(self):
        'Returns the values from the dialog'
        for neigh in self.Neigh:
            for ibond,bond in enumerate(neigh[1][0]):
                if not bond[2]:
                    neigh[1][1][1][ibond] = 0   #deselected bond
            neigh[1][1][1] = [a for a in  neigh[1][1][1] if a]
        return self.Neigh       #has #Hs to add for each entry
        
    def OnOk(self,event):
        'Called when the OK button is pressed'
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_OK)              

    def OnCancel(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_CANCEL)

################################################################################
class DisAglDialog(wx.Dialog):
    '''Distance/Angle Controls input dialog. After
    :meth:`ShowModal` returns, the results are found in
    dict :attr:`self.data`, which is accessed using :meth:`GetData`.

    :param wx.Frame parent: reference to parent frame (or None)
    :param dict data: a dict containing the current
      search ranges or an empty dict, which causes default values
      to be used.
      Will be used to set element `DisAglCtls` in 
      :ref:`Phase Tree Item <Phase_table>`
    :param dict default:  A dict containing the default
      search ranges for each element.
    :param bool Reset: if True (default), show Reset button
    :param bool Angle: if True (default), show angle radii
    '''
    def __init__(self,parent,data,default,Reset=True,Angle=True):
        text = 'Distance Angle Controls'
        if not Angle:
            text = 'Distance Controls'
        wx.Dialog.__init__(self,parent,wx.ID_ANY,text, 
            pos=wx.DefaultPosition,style=wx.DEFAULT_DIALOG_STYLE)
        self.default = default
        self.Reset = Reset
        self.Angle = Angle
        self.panel = wx.Panel(self)         #just a dummy - gets destroyed in Draw!
        self._default(data,self.default)
        self.Draw(self.data)
                
    def _default(self,data,default):
        '''Set starting values for the search values, either from
        the input array or from defaults, if input is null
        '''
        if data:
            self.data = copy.deepcopy(data) # don't mess with originals
        else:
            self.data = {}
            self.data['Name'] = default['Name']
            self.data['Factors'] = [0.85,0.85]
            self.data['AtomTypes'] = default['AtomTypes']
            self.data['BondRadii'] = default['BondRadii'][:]
            self.data['AngleRadii'] = default['AngleRadii'][:]

    def Draw(self,data):
        '''Creates the contents of the dialog. Normally called
        by :meth:`__init__`.
        '''
        self.panel.Destroy()
        self.panel = wx.Panel(self)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(wx.StaticText(self.panel,-1,'Controls for phase '+data['Name']),
            0,WACV|wx.LEFT,10)
        mainSizer.Add((10,10),1)
        
        ncol = 3
        if not self.Angle:
            ncol=2
        radiiSizer = wx.FlexGridSizer(0,ncol,5,5)
        radiiSizer.Add(wx.StaticText(self.panel,-1,' Type'),0,WACV)
        radiiSizer.Add(wx.StaticText(self.panel,-1,'Bond radii'),0,WACV)
        if self.Angle:
            radiiSizer.Add(wx.StaticText(self.panel,-1,'Angle radii'),0,WACV)
        self.objList = {}
        for id,item in enumerate(self.data['AtomTypes']):
            radiiSizer.Add(wx.StaticText(self.panel,-1,' '+item),0,WACV)
            bRadii = G2G.ValidatedTxtCtrl(self.panel,data['BondRadii'],id,nDig=(10,3))
            radiiSizer.Add(bRadii,0,WACV)
            if self.Angle:
                aRadii = G2G.ValidatedTxtCtrl(self.panel,data['AngleRadii'],id,nDig=(10,3))
                radiiSizer.Add(aRadii,0,WACV)
        mainSizer.Add(radiiSizer,0,wx.EXPAND)
        if self.Angle:
            factorSizer = wx.FlexGridSizer(0,2,5,5)
            Names = ['Bond','Angle']
            for i,name in enumerate(Names):
                factorSizer.Add(wx.StaticText(self.panel,-1,name+' search factor'),0,WACV)
                bondFact = G2G.ValidatedTxtCtrl(self.panel,data['Factors'],i,nDig=(10,3))
                factorSizer.Add(bondFact)
            mainSizer.Add(factorSizer,0,wx.EXPAND)
        
        OkBtn = wx.Button(self.panel,-1,"Ok")
        OkBtn.Bind(wx.EVT_BUTTON, self.OnOk)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20),1)
        btnSizer.Add(OkBtn)
        if self.Reset:
            ResetBtn = wx.Button(self.panel,-1,'Reset')
            ResetBtn.Bind(wx.EVT_BUTTON, self.OnReset)
            btnSizer.Add(ResetBtn)
        btnSizer.Add((20,20),1)
        mainSizer.Add(btnSizer,0,wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        self.panel.SetSizer(mainSizer)
        self.panel.Fit()
        self.Fit()
    
    def GetData(self):
        'Returns the values from the dialog'
        return self.data
        
    def OnOk(self,event):
        'Called when the OK button is pressed'
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_OK)              
        
    def OnReset(self,event):
        'Called when the Reset button is pressed'
        data = {}
        self._default(data,self.default)
        self.Draw(self.data)
                
################################################################################
class ShowLSParms(wx.Dialog):
    '''Create frame to show least-squares parameters
    '''
    def __init__(self,parent,title,parmDict,varyList,fullVaryList,
                 size=(375,430)):
        
        wx.Dialog.__init__(self,parent,wx.ID_ANY,title,size=size,
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.panel = wxscroll.ScrolledPanel(self)         #just a dummy - gets destroyed in DrawPanel!
        self.parmChoice = 'Phase'
        self.parmDict = parmDict
        self.varyList = varyList
        self.fullVaryList = fullVaryList

        self.parmNames = parmDict.keys()
        self.parmNames.sort()
        splitNames = [item.split(':') for item in self.parmNames if len(item) > 3 and not isinstance(self.parmDict[item],basestring)]
        self.globNames = [':'.join(item) for item in splitNames if not item[0] and not item[1]]
        self.globVars = list(set([' ',]+[item[2] for item in splitNames if not item[0] and not item[1]]))
        self.globVars.sort()
        self.hisNames = [':'.join(item) for item in splitNames if not item[0] and item[1]]
        self.hisNums = list(set([int(item.split(':')[1]) for item in self.hisNames]))
        self.hisNums.sort()
        self.hisNums = [' ',]+[str(item) for item in self.hisNums]
        self.hisVars = list(set([' ',]+[item[2] for item in splitNames if not item[0]]))
        self.hisVars.sort()
        self.phasNames = [':'.join(item) for item in splitNames if not item[1] and 'is' not in item[2]]
        self.phasNums = [' ',]+list(set([item.split(':')[0] for item in self.phasNames]))
        if '' in self.phasNums: self.phasNums.remove('')
        self.phasVars = list(set([' ',]+[item[2] for item in splitNames if not item[1] and 'is' not in item[2]]))
        self.phasVars.sort()
        self.phasNums.sort()
        self.hapNames = [':'.join(item) for item in splitNames if item[0] and item[1]]
        self.hapVars = list(set([' ',]+[item[2] for item in splitNames if item[0] and item[1]]))
        self.hapVars.sort()
        self.hisNum = ' '
        self.phasNum = ' '
        self.varName = ' '
        self.listSel = 'Refined'
        self.DrawPanel()
        
            
    def DrawPanel(self):
            
        def _OnParmSel(event):
            self.parmChoice = parmSel.GetStringSelection()
            self.varName = ' '
            wx.CallLater(100,self.DrawPanel)
            
        def OnPhasSel(event):
            event.Skip()
            self.phasNum = phasSel.GetValue()
            self.varName = ' '
            wx.CallLater(100,self.DrawPanel)

        def OnHistSel(event):
            event.Skip()
            self.hisNum = histSel.GetValue()
            self.varName = ' '
            wx.CallLater(100,self.DrawPanel)
            
        def OnVarSel(event):
            self.varName = varSel.GetValue()
            self.phasNum = ' '
            self.hisNum = ' '
            wx.CallLater(100,self.DrawPanel)
            
        def OnListSel(event):
            self.listSel = listSel.GetStringSelection()
            wx.CallLater(100,self.DrawPanel)

        if self.panel:
            #self.panel.DestroyChildren() # Bad on Mac: deletes scroll bars
            sizer = self.panel.GetSizer()
            if sizer: sizer.DeleteWindows()

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        num = len(self.varyList)
        mainSizer.Add(wx.StaticText(self.panel,label=' Number of refined variables: '+str(num)),0)
        if len(self.varyList) != len(self.fullVaryList):
            num = len(self.fullVaryList) - len(self.varyList)
            mainSizer.Add(wx.StaticText(self.panel,label=' + '+str(num)+' parameters are varied via constraints'))
        choiceDict = {'Global':self.globNames,'Phase':self.phasNames,'Phase/Histo':self.hapNames,'Histogram':self.hisNames}
        choice = ['Phase','Phase/Histo','Histogram']
        if len(self.globNames):
            choice += ['Global',]
        parmSizer = wx.FlexGridSizer(0,3,5,5)
        parmSel = wx.RadioBox(self.panel,wx.ID_ANY,'Parameter type:',choices=choice,
            majorDimension=1,style=wx.RA_SPECIFY_COLS)
        parmSel.Bind(wx.EVT_RADIOBOX,_OnParmSel)
        parmSel.SetStringSelection(self.parmChoice)
        parmSizer.Add(parmSel,0)
        numSizer = wx.BoxSizer(wx.VERTICAL)
        numSizer.Add((5,25),0)
        if self.parmChoice in ['Phase','Phase/Histo'] and len(self.phasNums) > 1:
            numSizer.Add(wx.StaticText(self.panel,label='Phase'),0)
            phasSel = wx.ComboBox(self.panel,choices=self.phasNums,value=self.phasNum,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
            phasSel.Bind(wx.EVT_COMBOBOX,OnPhasSel)
            numSizer.Add(phasSel,0)
        if self.parmChoice in ['Histogram','Phase/Histo'] and len(self.hisNums) > 1:
            numSizer.Add(wx.StaticText(self.panel,label='Histogram'),0)
            histSel = wx.ComboBox(self.panel,choices=self.hisNums,value=self.hisNum,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
            histSel.Bind(wx.EVT_COMBOBOX,OnHistSel)
#            histSel = wx.TextCtrl(self.panel,size=(50,25),value='0',style=wx.TE_PROCESS_ENTER)
#            histSel.Bind(wx.EVT_TEXT_ENTER,OnHistSel)
#            histSel.Bind(wx.EVT_KILL_FOCUS,OnHistSel)
            numSizer.Add(histSel,0)
        parmSizer.Add(numSizer)
        varSizer = wx.BoxSizer(wx.VERTICAL)
        if self.parmChoice in ['Phase',]:
            varSel = wx.ComboBox(self.panel,choices=self.phasVars,value=self.varName,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
            varSel.Bind(wx.EVT_COMBOBOX,OnVarSel)
        elif self.parmChoice in ['Histogram',]:
            varSel = wx.ComboBox(self.panel,choices=self.hisVars,value=self.varName,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
            varSel.Bind(wx.EVT_COMBOBOX,OnVarSel)
        elif self.parmChoice in ['Phase/Histo',]:
            varSel = wx.ComboBox(self.panel,choices=self.hapVars,value=self.varName,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
            varSel.Bind(wx.EVT_COMBOBOX,OnVarSel)
        if self.parmChoice != 'Global': 
            varSizer.Add(wx.StaticText(self.panel,label='Parameter'))
            varSizer.Add(varSel,0)
        parmSizer.Add(varSizer,0)
        mainSizer.Add(parmSizer,0)
        listChoice = ['All','Refined']
        listSel = wx.RadioBox(self.panel,wx.ID_ANY,'Parameter type:',choices=listChoice,
            majorDimension=0,style=wx.RA_SPECIFY_COLS)
        listSel.SetStringSelection(self.listSel)
        listSel.Bind(wx.EVT_RADIOBOX,OnListSel)
        mainSizer.Add(listSel,0)
        subSizer = wx.FlexGridSizer(cols=4,hgap=2,vgap=2)
        subSizer.Add((-1,-1))
        subSizer.Add(wx.StaticText(self.panel,wx.ID_ANY,'Parameter name  '))
        subSizer.Add(wx.StaticText(self.panel,wx.ID_ANY,'refine?'))
        subSizer.Add(wx.StaticText(self.panel,wx.ID_ANY,'value'),0,wx.ALIGN_RIGHT)
        explainRefine = False
        for name in choiceDict[self.parmChoice]:
            # skip entries without numerical values
            if isinstance(self.parmDict[name],basestring): continue
            if 'Refined' in self.listSel and (name not in self.fullVaryList
                                              ) and (name not in self.varyList):
                continue
            if 'Phase' in self.parmChoice:
                if self.phasNum != ' ' and name.split(':')[0] != self.phasNum: continue
            if 'Histo' in self.parmChoice:
                if self.hisNum != ' ' and name.split(':')[1] != self.hisNum: continue
            if (self.varName != ' ') and (self.varName not in name): continue
            try:
                value = G2py3.FormatSigFigs(self.parmDict[name])
            except TypeError:
                value = str(self.parmDict[name])+' -?' # unexpected
                #continue
            v = G2obj.getVarDescr(name)
            if v is None or v[-1] is None:
                subSizer.Add((-1,-1))
            else:                
                ch = G2G.HelpButton(self.panel,G2obj.fmtVarDescr(name))
                subSizer.Add(ch,0,wx.LEFT|wx.RIGHT|WACV|wx.ALIGN_CENTER,1)
            subSizer.Add(wx.StaticText(self.panel,wx.ID_ANY,str(name)))
            if name in self.varyList:
                subSizer.Add(wx.StaticText(self.panel,label='R'))   #TODO? maybe a checkbox for one stop refinemnt flag setting?
            elif name in self.fullVaryList:
                subSizer.Add(wx.StaticText(self.panel,label='C'))
                explainRefine = True
            else:
                subSizer.Add((-1,-1))
            subSizer.Add(wx.StaticText(self.panel,label=value),0,wx.ALIGN_RIGHT)

        mainSizer.Add(subSizer,0)
        if explainRefine:
            mainSizer.Add(
                wx.StaticText(self.panel,label='"R" indicates a refined variable\n'+
                    '"C" indicates generated from a constraint'),0, wx.ALL,0)
        # make OK button 
        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        btn = wx.Button(self.panel, wx.ID_CLOSE,"Close") 
        btn.Bind(wx.EVT_BUTTON,self._onClose)
        btnsizer.Add(btn)
        mainSizer.Add(btnsizer, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        # Allow window to be enlarged but not made smaller
        self.panel.SetSizer(mainSizer)
        self.panel.SetAutoLayout(1)
        self.panel.SetupScrolling()
        self.panel.SetMinSize(self.GetSize())

    def _onClose(self,event):
        self.EndModal(wx.ID_CANCEL)
 
################################################################################
class DataFrame(wx.Frame):
    '''Create the data item window and all the entries in menus used in
    that window. For Linux and windows, the menu entries are created for the
    current data item window, but in the Mac the menu is accessed from all
    windows. This means that a different menu is posted depending on which
    data item is posted. On the Mac, all the menus contain the data tree menu
    items, but additional menus are added specific to the data item. 

    Note that while the menus are created here, 
    the binding for the menus is done later in various GSASII*GUI modules,
    where the functions to be called are defined.
    '''
    def Bind(self,eventtype,handler,*args,**kwargs):
        '''Override the Bind() function: on the Mac the binding is to
        the main window, so that menus operate with any window on top.
        For other platforms, either wrap calls that will be logged
        or call the default wx.Frame Bind() to bind to the menu item directly.

        Note that bindings can be made to objects by Id or by direct reference to the
        object. As a convention, when bindings are to objects, they are not logged
        but when bindings are by Id, they are logged.
        '''
        if sys.platform == "darwin": # mac
            self.G2frame.Bind(eventtype,handler,*args,**kwargs)
            return
        if eventtype == wx.EVT_MENU and 'id' in kwargs:
            menulabels = log.SaveMenuCommand(kwargs['id'],self.G2frame,handler)
            if menulabels:
                #print 'intercepting bind for',handler,menulabels,kwargs['id']
                wx.Frame.Bind(self,eventtype,self.G2frame.MenuBinding,*args,**kwargs)
                return
            wx.Frame.Bind(self,eventtype,handler,*args,**kwargs)      
        
    def PrefillDataMenu(self,menu,empty=False):
        '''Create the "standard" part of data frame menus. Note that on Linux and
        Windows nothing happens here. On Mac, this menu duplicates the
        tree menu, but adds an extra help command for the data item and a separator. 
        '''
        self.datamenu = menu
        self.G2frame.dataMenuBars.append(menu)
        if sys.platform == "darwin": # mac                         
            self.G2frame.FillMainMenu(menu,addhelp=False) # add the data tree menu items
            if not empty:
                menu.Append(wx.Menu(title=''),title='|') # add a separator
        
    def PostfillDataMenu(self,empty=False):
        '''Add the help menu to the data frame menus. Note that on Linux and
        Windows, this is the standard help Menu but without the update commands but adds an extra help
        command for the data item. 
        On Mac, this is the entire help menu including the update commands, a separator and the
        extra help command for the data item. 
        '''
        menu = self.datamenu
        if sys.platform == "darwin": # mac
            if not empty:
                menu.Append(wx.Menu(title=''),title='|') # add another separator
            HelpMenu=G2G.MyHelp(self,includeTree=True,
                morehelpitems=[('&Tutorials','Tutorials'),])
            menu.Append(menu=HelpMenu,title='&Help')
        else: # other
            menu.Append(menu=G2G.MyHelp(self),title='&Help')

    def _init_menus(self):
        'define all GSAS-II data frame menus'

        # for use where no menu or data frame help is provided
        self.BlankMenu = wx.MenuBar()
        
        # Controls
        self.ControlsMenu = wx.MenuBar()
        self.PrefillDataMenu(self.ControlsMenu,empty=True)
        self.PostfillDataMenu(empty=True)
        
        # Notebook
        self.DataNotebookMenu = wx.MenuBar() 
        self.PrefillDataMenu(self.DataNotebookMenu,empty=True)
        self.PostfillDataMenu(empty=True)
        
        # Comments
        self.DataCommentsMenu = wx.MenuBar()
        self.PrefillDataMenu(self.DataCommentsMenu,empty=True)
        self.PostfillDataMenu(empty=True)
        
        # Constraints
        self.ConstraintMenu = wx.MenuBar()
        self.PrefillDataMenu(self.ConstraintMenu)
        self.ConstraintTab = wx.Menu(title='')
        self.ConstraintMenu.Append(menu=self.ConstraintTab, title='Select tab')
        for id,txt in (
            (wxID_CONSPHASE,'Phase'),
            (wxID_CONSHAP,'Histogram/Phase'),
            (wxID_CONSHIST,'Histogram'),
            (wxID_CONSGLOBAL,'Global')):
            self.ConstraintTab.Append(
                id=id, kind=wx.ITEM_NORMAL,text=txt,
                help='Select '+txt+' constraint editing tab')
        self.ConstraintEdit = wx.Menu(title='')
        self.ConstraintMenu.Append(menu=self.ConstraintEdit, title='Edit Constr.') # renamed from Edit due to Mac adding extra items to menu
        self.ConstraintEdit.Append(id=wxID_HOLDADD, kind=wx.ITEM_NORMAL,text='Add hold',
            help='Prevent refinement of parameter values')
        self.ConstraintEdit.Append(id=wxID_EQUIVADD, kind=wx.ITEM_NORMAL,text='Add equivalence',
            help='Force parameter values to be equivalent')
        self.ConstraintEdit.Append(id=wxID_CONSTRAINTADD, kind=wx.ITEM_NORMAL,text='Add constraint equation',
            help='Add a constraint equation to apply to parameter values')
        self.ConstraintEdit.Append(id=wxID_FUNCTADD, kind=wx.ITEM_NORMAL,text='Add New Var',
            help='Create a variable composed of existing parameters')
        self.ConstraintEdit.Append(id=wxID_EQUIVALANCEATOMS, kind=wx.ITEM_NORMAL,text='Make atoms equivalent',
            help='Force atom parameter values to be equivalent')
        self.ConstraintEdit.Enable(wxID_EQUIVALANCEATOMS,False)
#        self.ConstraintEdit.Append(id=wxID_ADDRIDING, kind=wx.ITEM_NORMAL,text='Add H riding constraints',
#            help='Add H atom riding constraints between atom parameter values')
#        self.ConstraintEdit.Enable(wxID_ADDRIDING,False)
        self.PostfillDataMenu()

        # item = self.ConstraintEdit.Append(id=wx.ID_ANY,kind=wx.ITEM_NORMAL,text='Update GUI')
        # def UpdateGSASIIconstrGUI(event):
        #     import GSASIIconstrGUI
        #     reload(GSASIIconstrGUI)
        #     import GSASIIobj
        #     reload(GSASIIobj)
        # self.Bind(wx.EVT_MENU,UpdateGSASIIconstrGUI,id=item.GetId())

        # Rigid bodies
        self.RigidBodyMenu = wx.MenuBar()
        self.PrefillDataMenu(self.RigidBodyMenu)
        self.ResidueRBMenu = wx.Menu(title='')
        self.ResidueRBMenu.Append(id=wxID_RIGIDBODYIMPORT, kind=wx.ITEM_NORMAL,text='Import XYZ',
            help='Import rigid body XYZ from file')
        self.ResidueRBMenu.Append(id=wxID_RESIDUETORSSEQ, kind=wx.ITEM_NORMAL,text='Define sequence',
            help='Define torsion sequence')
        self.ResidueRBMenu.Append(id=wxID_RIGIDBODYADD, kind=wx.ITEM_NORMAL,text='Import residues',
            help='Import residue rigid bodies from macro file')
        self.RigidBodyMenu.Append(menu=self.ResidueRBMenu, title='Edit Body')
        self.PostfillDataMenu()

        self.VectorBodyMenu = wx.MenuBar()
        self.PrefillDataMenu(self.VectorBodyMenu)
        self.VectorRBEdit = wx.Menu(title='')
        self.VectorRBEdit.Append(id=wxID_VECTORBODYADD, kind=wx.ITEM_NORMAL,text='Add rigid body',
            help='Add vector rigid body')
        self.VectorBodyMenu.Append(menu=self.VectorRBEdit, title='Edit Vector Body')
        self.PostfillDataMenu()

                    
        # Restraints
        self.RestraintTab = wx.Menu(title='')
        self.RestraintEdit = wx.Menu(title='')
        self.RestraintEdit.Append(id=wxID_RESTSELPHASE, kind=wx.ITEM_NORMAL,text='Select phase',
            help='Select phase')
        self.RestraintEdit.Append(id=wxID_RESTRAINTADD, kind=wx.ITEM_NORMAL,text='Add restraints',
            help='Add restraints')
        self.RestraintEdit.Enable(wxID_RESTRAINTADD,True)    #gets disabled if macromolecule phase
        self.RestraintEdit.Append(id=wxID_AARESTRAINTADD, kind=wx.ITEM_NORMAL,text='Add residue restraints',
            help='Add residue based restraints for macromolecules from macro file')
        self.RestraintEdit.Enable(wxID_AARESTRAINTADD,False)    #gets enabled if macromolecule phase
        self.RestraintEdit.Append(id=wxID_AARESTRAINTPLOT, kind=wx.ITEM_NORMAL,text='Plot residue restraints',
            help='Plot selected residue based restraints for macromolecules from macro file')
        self.RestraintEdit.Enable(wxID_AARESTRAINTPLOT,False)    #gets enabled if macromolecule phase
        self.RestraintEdit.Append(id=wxID_RESRCHANGEVAL, kind=wx.ITEM_NORMAL,text='Change value',
            help='Change observed value')
        self.RestraintEdit.Append(id=wxID_RESTCHANGEESD, kind=wx.ITEM_NORMAL,text='Change esd',
            help='Change esd in observed value')
        self.RestraintEdit.Append(id=wxID_RESTDELETE, kind=wx.ITEM_NORMAL,text='Delete restraints',
            help='Delete selected restraints')

        self.RestraintMenu = wx.MenuBar()
        self.PrefillDataMenu(self.RestraintMenu)
        self.RestraintMenu.Append(menu=self.RestraintTab, title='Select tab')
        self.RestraintMenu.Append(menu=self.RestraintEdit, title='Edit Restr.')
        self.PostfillDataMenu()
            
        # Sequential results
        self.SequentialMenu = wx.MenuBar()
        self.PrefillDataMenu(self.SequentialMenu)
        self.SequentialFile = wx.Menu(title='')
        self.SequentialMenu.Append(menu=self.SequentialFile, title='Columns')
        self.SequentialFile.Append(id=wxID_RENAMESEQSEL, kind=wx.ITEM_NORMAL,text='Rename selected',
            help='Rename selected sequential refinement columns')
        self.SequentialFile.Append(id=wxID_SAVESEQSEL, kind=wx.ITEM_NORMAL,text='Save selected as text',
            help='Save selected sequential refinement results as a text file')
        self.SequentialFile.Append(id=wxID_SAVESEQCSV, kind=wx.ITEM_NORMAL,text='Save all as CSV',
            help='Save all sequential refinement results as a CSV spreadsheet file')
        self.SequentialFile.Append(id=wxID_SAVESEQSELCSV, kind=wx.ITEM_NORMAL,text='Save selected as CSV',
            help='Save selected sequential refinement results as a CSV spreadsheet file')
        self.SequentialFile.Append(id=wxID_PLOTSEQSEL, kind=wx.ITEM_NORMAL,text='Plot selected',
            help='Plot selected sequential refinement results')
        self.SequentialFile.Append(id=wxID_AVESEQSEL, kind=wx.ITEM_NORMAL,text='Compute average',
            help='Compute average for selected parameter')            
        self.SequentialFile.Append(id=wxID_ORGSEQSEL, kind=wx.ITEM_NORMAL,text='Reorganize',
            help='Reorganize variables where variables change')
        self.SequentialPvars = wx.Menu(title='')
        self.SequentialMenu.Append(menu=self.SequentialPvars, title='Pseudo Vars')
        self.SequentialPvars.Append(
            id=wxADDSEQVAR, kind=wx.ITEM_NORMAL,text='Add Formula',
            help='Add a new custom pseudo-variable')
        self.SequentialPvars.Append(
            id=wxADDSEQDIST, kind=wx.ITEM_NORMAL,text='Add Distance',
            help='Add a new bond distance pseudo-variable')
        self.SequentialPvars.Append(
            id=wxADDSEQANGLE, kind=wx.ITEM_NORMAL,text='Add Angle',
            help='Add a new bond angle pseudo-variable')
        self.SequentialPvars.Append(
            id=wxDELSEQVAR, kind=wx.ITEM_NORMAL,text='Delete',
            help='Delete an existing pseudo-variable')
        self.SequentialPvars.Append(
            id=wxEDITSEQVAR, kind=wx.ITEM_NORMAL,text='Edit',
            help='Edit an existing pseudo-variable')

        self.SequentialPfit = wx.Menu(title='')
        self.SequentialMenu.Append(menu=self.SequentialPfit, title='Parametric Fit')
        self.SequentialPfit.Append(
            id=wxADDPARFIT, kind=wx.ITEM_NORMAL,text='Add equation',
            help='Add a new equation to minimize')
        self.SequentialPfit.Append(
            id=wxCOPYPARFIT, kind=wx.ITEM_NORMAL,text='Copy equation',
            help='Copy an equation to minimize - edit it next')
        self.SequentialPfit.Append(
            id=wxDELPARFIT, kind=wx.ITEM_NORMAL,text='Delete equation',
            help='Delete an equation for parametric minimization')
        self.SequentialPfit.Append(
            id=wxEDITPARFIT, kind=wx.ITEM_NORMAL,text='Edit equation',
            help='Edit an existing parametric minimization equation')
        self.SequentialPfit.Append(
            id=wxDOPARFIT, kind=wx.ITEM_NORMAL,text='Fit to equation(s)',
            help='Perform a parametric minimization')
        # fill sequential Export menu
        self.SeqExportLookup = {}
        self.SequentialEx = wx.Menu(title='')
        self.SequentialMenu.Append(menu=self.SequentialEx, title='Seq Export')
        for lbl,txt in (('Phase','Export selected phase(s)'),
                        ('Project','Export entire sequential fit')):
            objlist = []
            for obj in self.G2frame.exporterlist:
                if lbl.lower() in obj.exporttype:
                    try:
                        obj.Writer
                    except AttributeError:
                        continue
                    objlist.append(obj)
            if objlist:
                submenu = wx.Menu()
                item = self.SequentialEx.AppendMenu(
                    wx.ID_ANY, lbl+' as',
                    submenu, help=txt)
                for obj in objlist:
                    item = submenu.Append(
                        wx.ID_ANY,
                        help=obj.longFormatName,
                        kind=wx.ITEM_NORMAL,
                        text=obj.formatName)
                    self.SeqExportLookup[item.GetId()] = (obj,lbl) # lookup table for submenu item
        
        self.PostfillDataMenu()
            
        # PWDR & SASD
        self.PWDRMenu = wx.MenuBar()
        self.PrefillDataMenu(self.PWDRMenu)
        self.ErrorAnal = wx.Menu(title='')
        self.PWDRMenu.Append(menu=self.ErrorAnal,title='Commands')
        self.ErrorAnal.Append(id=wxID_PWDANALYSIS,kind=wx.ITEM_NORMAL,text='Error Analysis',
            help='Error analysis on powder pattern')
        self.ErrorAnal.Append(id=wxID_PWDCOPY,kind=wx.ITEM_NORMAL,text='Copy params',
            help='Copy of PWDR parameters')
        self.ErrorAnal.Append(id=wxID_PLOTCTRLCOPY,kind=wx.ITEM_NORMAL,text='Copy plot controls',
            help='Copy of PWDR plot controls')
        self.moveDiffCurve = self.ErrorAnal.Append(id=wx.ID_ANY,kind=wx.ITEM_NORMAL,text='Move diff. curve',
            help='Click on position where difference curve is placed')
        self.moveTickLoc = self.ErrorAnal.Append(id=wx.ID_ANY,kind=wx.ITEM_NORMAL,text='Move ticks',
            help='Move mouse to where tick marks should be positioned')
        self.moveTickSpc = self.ErrorAnal.Append(id=wx.ID_ANY,kind=wx.ITEM_NORMAL,text='Set tick space',
            help='Click to set spacing between phase tick marks')
        self.PostfillDataMenu()
            
        # HKLF 
        self.HKLFMenu = wx.MenuBar()
        self.PrefillDataMenu(self.HKLFMenu)
        self.ErrorAnal = wx.Menu(title='')
        self.HKLFMenu.Append(menu=self.ErrorAnal,title='Commands')
        self.ErrorAnal.Append(id=wxID_PWDANALYSIS,kind=wx.ITEM_NORMAL,text='Error Analysis',
            help='Error analysis on single crystal data')
        self.ErrorAnal.Append(id=wxID_MERGEHKL,kind=wx.ITEM_NORMAL,text='Merge HKLs',
            help='Transform & merge HKLF data to new histogram')
        self.ErrorAnal.Append(id=wxID_PWD3DHKLPLOT,kind=wx.ITEM_NORMAL,text='Plot 3D HKLs',
            help='Plot HKLs from single crystal data in 3D')
        self.ErrorAnal.Append(id=wxID_3DALLHKLPLOT,kind=wx.ITEM_NORMAL,text='Plot all 3D HKLs',
            help='Plot HKLs from all single crystal data in 3D')
        self.ErrorAnal.Append(id=wxID_PWDCOPY,kind=wx.ITEM_NORMAL,text='Copy params',
            help='Copy of HKLF parameters')
        self.PostfillDataMenu()
            
        # PWDR / Limits
        self.LimitMenu = wx.MenuBar()
        self.PrefillDataMenu(self.LimitMenu)
        self.LimitEdit = wx.Menu(title='')
        self.LimitMenu.Append(menu=self.LimitEdit, title='Edit Limits')
        self.LimitEdit.Append(id=wxID_LIMITCOPY, kind=wx.ITEM_NORMAL,text='Copy',
            help='Copy limits to other histograms')
        self.LimitEdit.Append(id=wxID_ADDEXCLREGION, kind=wx.ITEM_NORMAL,text='Add exclude',
            help='Add excluded region - select a point on plot; drag to adjust')            
        self.PostfillDataMenu()
            
        # PDR / Background
        self.BackMenu = wx.MenuBar()
        self.PrefillDataMenu(self.BackMenu)
        self.BackEdit = wx.Menu(title='')
        self.BackMenu.Append(menu=self.BackEdit, title='File')
        self.BackEdit.Append(id=wxID_BACKCOPY, kind=wx.ITEM_NORMAL,text='Copy',
            help='Copy background parameters to other histograms')
        self.BackEdit.Append(id=wxID_BACKFLAGCOPY, kind=wx.ITEM_NORMAL,text='Copy flags',
            help='Copy background refinement flags to other histograms')
        self.BackEdit.Append(id=wxID_PEAKSMOVE, kind=wx.ITEM_NORMAL,text='Move peaks',
            help='Move background peaks to Peak List')
        self.BackEdit.Append(id=wxID_MAKEBACKRDF, kind=wx.ITEM_NORMAL,text='Plot RDF',
            help='Plot radial distribution from differences')
        self.BackFixed = wx.Menu(title='') # fixed background point menu
        self.BackMenu.Append(menu=self.BackFixed, title='Fixed Points')
        self.wxID_BackPts = {}
        self.wxID_BackPts['Add'] = wx.NewId() # N.B. not using wxID_ global as for other menu items
        self.BackFixed.Append(id=self.wxID_BackPts['Add'], kind=wx.ITEM_RADIO,text='Add',
            help='Add fixed background points with mouse clicks')
        self.wxID_BackPts['Move'] = wx.NewId() 
        item = self.BackFixed.Append(id=self.wxID_BackPts['Move'], kind=wx.ITEM_RADIO,text='Move',
            help='Move selected fixed background points with mouse drags')
        item.Check(True)
        self.wxID_BackPts['Del'] = wx.NewId()
        self.BackFixed.Append(id=self.wxID_BackPts['Del'], kind=wx.ITEM_RADIO,text='Delete',
            help='Delete fixed background points with mouse clicks')
        self.wxID_BackPts['Clear'] = wx.NewId() 
        self.BackFixed.Append(id=self.wxID_BackPts['Clear'], kind=wx.ITEM_NORMAL,text='Clear',
            help='Clear fixed background points')
        self.wxID_BackPts['Fit'] = wx.NewId() 
        self.BackFixed.Append(id=self.wxID_BackPts['Fit'], kind=wx.ITEM_NORMAL,text='Fit background',
            help='Fit background function to fixed background points')
        self.PostfillDataMenu()
            
        # PDR / Instrument Parameters
        self.InstMenu = wx.MenuBar()
        self.PrefillDataMenu(self.InstMenu)
        self.InstEdit = wx.Menu(title='')
        self.InstMenu.Append(menu=self.InstEdit, title='Operations')
        self.InstEdit.Append(help='Calibrate from indexed peaks', 
            id=wxID_INSTCALIB, kind=wx.ITEM_NORMAL,text='Calibrate')            
        self.InstEdit.Append(help='Reset instrument profile parameters to default', 
            id=wxID_INSTPRMRESET, kind=wx.ITEM_NORMAL,text='Reset profile')            
        self.InstEdit.Append(help='Load instrument profile parameters from file', 
            id=wxID_INSTLOAD, kind=wx.ITEM_NORMAL,text='Load profile...')            
        self.InstEdit.Append(help='Save instrument profile parameters to file', 
            id=wxID_INSTSAVE, kind=wx.ITEM_NORMAL,text='Save profile...')
        self.InstEdit.Append(help='Save all instrument profile parameters to one file', 
            id=wxID_INSTSAVEALL, kind=wx.ITEM_NORMAL,text='Save all profile...')            
        self.InstEdit.Append(help='Copy instrument profile parameters to other histograms', 
            id=wxID_INSTCOPY, kind=wx.ITEM_NORMAL,text='Copy')
        self.InstEdit.Append(id=wxID_INSTFLAGCOPY, kind=wx.ITEM_NORMAL,text='Copy flags',
            help='Copy instrument parameter refinement flags to other histograms')
#        self.InstEdit.Append(help='Change radiation type (Ka12 - synch)', 
#            id=wxID_CHANGEWAVETYPE, kind=wx.ITEM_NORMAL,text='Change radiation')
        self.InstEdit.Append(id=wxID_INST1VAL, kind=wx.ITEM_NORMAL,text='Set one value',
            help='Set one instrument parameter value across multiple histograms')

        self.PostfillDataMenu()
        
        # PDR / Sample Parameters
        self.SampleMenu = wx.MenuBar()
        self.PrefillDataMenu(self.SampleMenu)
        self.SampleEdit = wx.Menu(title='')
        self.SampleMenu.Append(menu=self.SampleEdit, title='Command')
        self.SetScale = self.SampleEdit.Append(id=wxID_SETSCALE, kind=wx.ITEM_NORMAL,text='Set scale',
            help='Set scale by matching to another histogram')
        self.SampleEdit.Append(id=wxID_SAMPLELOAD, kind=wx.ITEM_NORMAL,text='Load',
            help='Load sample parameters from file')
        self.SampleEdit.Append(id=wxID_SAMPLESAVE, kind=wx.ITEM_NORMAL,text='Save',
            help='Save sample parameters to file')
        self.SampleEdit.Append(id=wxID_SAMPLECOPY, kind=wx.ITEM_NORMAL,text='Copy',
            help='Copy refinable and most other sample parameters to other histograms')
        self.SampleEdit.Append(id=wxID_SAMPLECOPYSOME, kind=wx.ITEM_NORMAL,text='Copy selected...',
            help='Copy selected sample parameters to other histograms')
        self.SampleEdit.Append(id=wxID_SAMPLEFLAGCOPY, kind=wx.ITEM_NORMAL,text='Copy flags',
            help='Copy sample parameter refinement flags to other histograms')
        self.SampleEdit.Append(id=wxID_SAMPLE1VAL, kind=wx.ITEM_NORMAL,text='Set one value',
            help='Set one sample parameter value across multiple histograms')
        self.SampleEdit.Append(id=wxID_ALLSAMPLELOAD, kind=wx.ITEM_NORMAL,text='Load all',
            help='Load sample parmameters over multiple histograms')
        self.SampleEdit.Append(id=wxID_RESCALEALL, kind=wx.ITEM_NORMAL,text='Rescale all',
            help='Rescale all data with selected range')
        

        self.PostfillDataMenu()
        self.SetScale.Enable(False)

        # PDR / Peak List
        self.PeakMenu = wx.MenuBar()
        self.PrefillDataMenu(self.PeakMenu)
        self.PeakEdit = wx.Menu(title='')
        self.PeakMenu.Append(menu=self.PeakEdit, title='Peak Fitting')
        self.peaksSel = self.PeakEdit.Append(wx.ID_ANY,
            help='Set refinement flags for selected peaks',
            kind=wx.ITEM_NORMAL,
            text='Set sel. ref flags...')
        self.peaksAll = self.PeakEdit.Append(wx.ID_ANY,
            help='Set refinement flags for all peaks',
            kind=wx.ITEM_NORMAL,
            text='Set all ref flags...')
        self.AutoSearch = self.PeakEdit.Append(help='Automatic peak search', 
            id=wxID_AUTOSEARCH, kind=wx.ITEM_NORMAL,text='Auto search')
        self.UnDo = self.PeakEdit.Append(help='Undo last least squares refinement', 
            id=wxID_UNDO, kind=wx.ITEM_NORMAL,text='UnDo')
        self.PeakFit = self.PeakEdit.Append(id=wxID_LSQPEAKFIT, kind=wx.ITEM_NORMAL,text='Peakfit', 
            help='Peak fitting' )
        self.PFOneCycle = self.PeakEdit.Append(id=wxID_LSQONECYCLE, kind=wx.ITEM_NORMAL,text='Peakfit one cycle', 
            help='One cycle of Peak fitting' )
        self.PeakEdit.Append(id=wxID_RESETSIGGAM, kind=wx.ITEM_NORMAL, 
            text='Reset sig and gam',help='Reset sigma and gamma to global fit' )
        self.PeakCopy = self.PeakEdit.Append(help='Copy peaks to other histograms', 
            id=wxID_PEAKSCOPY, kind=wx.ITEM_NORMAL,text='Peak copy')
        self.SeqPeakFit = self.PeakEdit.Append(id=wxID_SEQPEAKFIT, kind=wx.ITEM_NORMAL,text='Seq PeakFit', 
            help='Sequential Peak fitting for all histograms' )
        self.PeakEdit.Append(id=wxID_CLEARPEAKS, kind=wx.ITEM_NORMAL,text='Clear peaks', 
            help='Clear the peak list' )
        self.movePeak = self.PeakEdit.Append(id=wx.ID_ANY,kind=wx.ITEM_NORMAL,text='Move selected peak',
            help='Select a peak in the table, then use this to move it with the mouse.')
        self.PostfillDataMenu()
        self.UnDo.Enable(False)
        self.PeakFit.Enable(False)
        self.PFOneCycle.Enable(False)
        self.AutoSearch.Enable(True)
        
        # PDR / Index Peak List
        self.IndPeaksMenu = wx.MenuBar()
        self.PrefillDataMenu(self.IndPeaksMenu)
        self.IndPeaksEdit = wx.Menu(title='')
        self.IndPeaksMenu.Append(menu=self.IndPeaksEdit,title='Operations')
        self.IndPeaksEdit.Append(help='Load/Reload index peaks from peak list',id=wxID_INDXRELOAD, 
            kind=wx.ITEM_NORMAL,text='Load/Reload')
        self.PostfillDataMenu()
        
        # PDR / Unit Cells List
        self.IndexMenu = wx.MenuBar()
        self.PrefillDataMenu(self.IndexMenu)
        self.IndexEdit = wx.Menu(title='')
        self.IndexMenu.Append(menu=self.IndexEdit, title='Cell Index/Refine')
        self.IndexPeaks = self.IndexEdit.Append(help='', id=wxID_INDEXPEAKS, kind=wx.ITEM_NORMAL,
            text='Index Cell')
        self.CopyCell = self.IndexEdit.Append( id=wxID_COPYCELL, kind=wx.ITEM_NORMAL,text='Copy Cell', 
            help='Copy selected unit cell from indexing to cell refinement fields')
        self.RefineCell = self.IndexEdit.Append( id=wxID_REFINECELL, kind=wx.ITEM_NORMAL, 
            text='Refine Cell',help='Refine unit cell parameters from indexed peaks')
        self.MakeNewPhase = self.IndexEdit.Append( id=wxID_MAKENEWPHASE, kind=wx.ITEM_NORMAL,
            text='Make new phase',help='Make new phase from selected unit cell')
        self.ExportCells = self.IndexEdit.Append( id=wxID_EXPORTCELLS, kind=wx.ITEM_NORMAL,
            text='Export cell list',help='Export cell list to csv file')
        self.PostfillDataMenu()
        self.IndexPeaks.Enable(False)
        self.CopyCell.Enable(False)
        self.RefineCell.Enable(False)
        self.MakeNewPhase.Enable(False)
        
        # PDR / Reflection Lists
        self.ReflMenu = wx.MenuBar()
        self.PrefillDataMenu(self.ReflMenu)
        self.ReflEdit = wx.Menu(title='')
        self.ReflMenu.Append(menu=self.ReflEdit, title='Reflection List')
        self.SelectPhase = self.ReflEdit.Append(help='Select phase for reflection list',id=wxID_SELECTPHASE, 
            kind=wx.ITEM_NORMAL,text='Select phase')
        self.ReflEdit.Append(id=wxID_PWDHKLPLOT,kind=wx.ITEM_NORMAL,text='Plot HKLs',
            help='Plot HKLs from powder pattern')
        self.ReflEdit.Append(id=wxID_PWD3DHKLPLOT,kind=wx.ITEM_NORMAL,text='Plot 3D HKLs',
            help='Plot HKLs from powder pattern in 3D')
        self.PostfillDataMenu()
        
        # SASD / Instrument Parameters
        self.SASDInstMenu = wx.MenuBar()
        self.PrefillDataMenu(self.SASDInstMenu)
        self.SASDInstEdit = wx.Menu(title='')
        self.SASDInstMenu.Append(menu=self.SASDInstEdit, title='Operations')
        self.InstEdit.Append(help='Reset instrument profile parameters to default', 
            id=wxID_INSTPRMRESET, kind=wx.ITEM_NORMAL,text='Reset profile')
        self.SASDInstEdit.Append(help='Copy instrument profile parameters to other histograms', 
            id=wxID_INSTCOPY, kind=wx.ITEM_NORMAL,text='Copy')
        self.PostfillDataMenu()
        
        #SASD & REFL/ Substance editor
        self.SubstanceMenu = wx.MenuBar()
        self.PrefillDataMenu(self.SubstanceMenu)
        self.SubstanceEdit = wx.Menu(title='')
        self.SubstanceMenu.Append(menu=self.SubstanceEdit, title='Edit substance')
        self.SubstanceEdit.Append(id=wxID_LOADSUBSTANCE, kind=wx.ITEM_NORMAL,text='Load substance',
            help='Load substance from file')
        self.SubstanceEdit.Append(id=wxID_RELOADSUBSTANCES, kind=wx.ITEM_NORMAL,text='Reload substances',
            help='Reload all substances from file')
        self.SubstanceEdit.Append(id=wxID_ADDSUBSTANCE, kind=wx.ITEM_NORMAL,text='Add substance',
            help='Add new substance to list')
        self.SubstanceEdit.Append(id=wxID_COPYSUBSTANCE, kind=wx.ITEM_NORMAL,text='Copy substances',
            help='Copy substances')
        self.SubstanceEdit.Append(id=wxID_DELETESUBSTANCE, kind=wx.ITEM_NORMAL,text='Delete substance',
            help='Delete substance from list')            
        self.SubstanceEdit.Append(id=wxID_ELEMENTADD, kind=wx.ITEM_NORMAL,text='Add elements',
            help='Add elements to substance')
        self.SubstanceEdit.Append(id=wxID_ELEMENTDELETE, kind=wx.ITEM_NORMAL,text='Delete elements',
            help='Delete elements from substance')
        self.PostfillDataMenu()
        
        # SASD/ Models
        self.ModelMenu = wx.MenuBar()
        self.PrefillDataMenu(self.ModelMenu)
        self.ModelEdit = wx.Menu(title='')
        self.ModelMenu.Append(menu=self.ModelEdit, title='Models')
        self.ModelEdit.Append(id=wxID_MODELADD,kind=wx.ITEM_NORMAL,text='Add',
            help='Add new term to model')
        self.ModelEdit.Append(id=wxID_MODELFIT, kind=wx.ITEM_NORMAL,text='Fit',
            help='Fit model parameters to data')
        self.SasdUndo = self.ModelEdit.Append(id=wxID_MODELUNDO, kind=wx.ITEM_NORMAL,text='Undo',
            help='Undo model fit')
        self.SasdUndo.Enable(False)            
        self.ModelEdit.Append(id=wxID_MODELFITALL, kind=wx.ITEM_NORMAL,text='Sequential fit',
            help='Sequential fit of model parameters to all SASD data')
        self.ModelEdit.Append(id=wxID_MODELCOPY, kind=wx.ITEM_NORMAL,text='Copy',
            help='Copy model parameters to other histograms')
        self.ModelEdit.Append(id=wxID_MODELCOPYFLAGS, kind=wx.ITEM_NORMAL,text='Copy flags',
            help='Copy model refinement flags to other histograms')
        self.PostfillDataMenu()
        
        # REFD/ Models
        self.REFDModelMenu = wx.MenuBar()
        self.PrefillDataMenu(self.REFDModelMenu)
        self.REFDModelEdit = wx.Menu(title='')
        self.REFDModelMenu.Append(menu=self.REFDModelEdit, title='Models')
        self.REFDModelEdit.Append(id=wxID_MODELFIT, kind=wx.ITEM_NORMAL,text='Fit',
            help='Fit model parameters to data')
        self.REFDUndo = self.REFDModelEdit.Append(id=wxID_MODELUNDO, kind=wx.ITEM_NORMAL,text='Undo',
            help='Undo model fit')
        self.REFDUndo.Enable(False)            
        self.REFDModelEdit.Append(id=wxID_MODELFITALL, kind=wx.ITEM_NORMAL,text='Sequential fit',
            help='Sequential fit of model parameters to all REFD data')
        self.REFDModelEdit.Append(id=wxID_MODELCOPY, kind=wx.ITEM_NORMAL,text='Copy',
            help='Copy model parameters to other histograms')
        self.REFDModelEdit.Append(id=wxID_MODELPLOT, kind=wx.ITEM_NORMAL,text='Plot',
            help='Plot model SDL for selected histograms')
        self.PostfillDataMenu()

        # IMG / Image Controls
        self.ImageMenu = wx.MenuBar()
        self.PrefillDataMenu(self.ImageMenu)
        
        self.ImageEdit = wx.Menu(title='')
        self.ImageMenu.Append(menu=self.ImageEdit, title='Calibration')
        self.ImageEdit.Append(help='Calibrate detector by fitting to calibrant lines', 
            id=wxID_IMCALIBRATE, kind=wx.ITEM_NORMAL,text='Calibrate')
        self.ImageEdit.Append(help='Recalibrate detector by fitting to calibrant lines', 
            id=wxID_IMRECALIBRATE, kind=wx.ITEM_NORMAL,text='Recalibrate')
        self.ImageEdit.Append(help='Recalibrate all images by fitting to calibrant lines', 
            id=wxID_IMRECALIBALL, kind=wx.ITEM_NORMAL,text='Recalibrate all')            
        self.ImageEdit.Append(help='Clear calibration data points and rings',
            id=wxID_IMCLEARCALIB, kind=wx.ITEM_NORMAL,text='Clear calibration')
        
        ImageIntegrate = wx.Menu(title='')
        self.ImageMenu.Append(menu=ImageIntegrate, title='Integration')
        ImageIntegrate.Append(help='Integrate selected image',id=wxID_IMINTEGRATE, 
            kind=wx.ITEM_NORMAL,text='Integrate')
        ImageIntegrate.Append(help='Integrate all images selected from list',id=wxID_INTEGRATEALL,
            kind=wx.ITEM_NORMAL,text='Integrate all')
        ImageIntegrate.Append(help='Open Auto-integration window to integrate a series of images', 
            id=wxID_IMAUTOINTEG, kind=wx.ITEM_NORMAL,text='Auto Integrate')

        ImageParams = wx.Menu(title='')
        self.ImageMenu.Append(menu=ImageParams, title='Parms')
        ImageParams.Append(help='Copy image controls to other images', 
            id=wxID_IMCOPYCONTROLS, kind=wx.ITEM_NORMAL,text='Copy Controls')
        ImageParams.Append(help='Copy selected image controls to other images', 
            id=wxID_IMCOPYSELECTED, kind=wx.ITEM_NORMAL,text='Copy Selected')
        ImageParams.Append(help='Save image controls to file', 
            id=wxID_IMSAVECONTROLS, kind=wx.ITEM_NORMAL,text='Save Controls')
        ImageParams.Append(help='Save controls from selected images to file', 
            id=wxID_SAVESELECTEDCONTROLS, kind=wx.ITEM_NORMAL,text='Save Multiple Controls')
        ImageParams.Append(help='Load image controls from file',
            id=wxID_IMLOADCONTROLS, kind=wx.ITEM_NORMAL,text='Load Controls')
        ImageParams.Append(help='Transfer integration range for other detector distances', 
            id=wxID_IMXFERCONTROLS, kind=wx.ITEM_NORMAL,text='Xfer angles')
        ImageParams.Append(help='Reset all detector dist to set dist', 
            id=wxID_IMRESETDIST, kind=wx.ITEM_NORMAL,text='Reset dist')
        
        self.PostfillDataMenu()
            
        # IMG / Masks
        self.MaskMenu = wx.MenuBar()
        self.PrefillDataMenu(self.MaskMenu)
        self.MaskEdit = wx.Menu(title='')
        self.MaskMenu.Append(menu=self.MaskEdit, title='Operations')
        submenu = wx.Menu()
        self.MaskEdit.AppendMenu(
            wx.ID_ANY,'Create new', submenu,
            help=''
            )
        self.MaskEdit.Append(help='Copy mask to other images', 
            id=wxID_MASKCOPY, kind=wx.ITEM_NORMAL,text='Copy mask')
        self.MaskEdit.Append(help='Save mask to file', 
            id=wxID_MASKSAVE, kind=wx.ITEM_NORMAL,text='Save mask')
        self.MaskEdit.Append(help='Load mask from file; ignoring threshold', 
            id=wxID_MASKLOADNOT, kind=wx.ITEM_NORMAL,text='Load mask')
        self.MaskEdit.Append(help='Load mask from file keeping the threshold value', 
            id=wxID_MASKLOAD, kind=wx.ITEM_NORMAL,text='Load mask w/threshold')
        self.MaskEdit.Append(help='Auto search for spot masks; NB: will clear old spot masks', 
            id=wxID_FINDSPOTS, kind=wx.ITEM_NORMAL,text='Auto spot masks')
        self.MaskEdit.Append(help='Delete all spot masks', 
            id=wxID_DELETESPOTS, kind=wx.ITEM_NORMAL,text='Delete spot masks')        
        submenu.Append(help='Create an arc mask with mouse input', 
            id=wxID_NEWMASKARC, kind=wx.ITEM_NORMAL,text='Arc mask')
        submenu.Append(help='Create a frame mask with mouse input', 
            id=wxID_NEWMASKFRAME, kind=wx.ITEM_NORMAL,text='Frame mask')
        submenu.Append(help='Create a polygon mask with mouse input', 
            id=wxID_NEWMASKPOLY, kind=wx.ITEM_NORMAL,text='Polygon mask')
        submenu.Append(help='Create a ring mask with mouse input', 
            id=wxID_NEWMASKRING, kind=wx.ITEM_NORMAL,text='Ring mask')
        submenu.Append(help='Create spot masks with mouse input', 
            id=wxID_NEWMASKSPOT, kind=wx.ITEM_NORMAL,text='Spot mask')
        self.PostfillDataMenu()
            
        # IMG / Stress/Strain
        self.StrStaMenu = wx.MenuBar()
        self.PrefillDataMenu(self.StrStaMenu)
        self.StrStaEdit = wx.Menu(title='')
        self.StrStaMenu.Append(menu=self.StrStaEdit, title='Operations')
        self.StrStaEdit.Append(help='Append d-zero for one ring', 
            id=wxID_APPENDDZERO, kind=wx.ITEM_NORMAL,text='Append d-zero')
        self.StrStaEdit.Append(help='Fit stress/strain data', 
            id=wxID_STRSTAFIT, kind=wx.ITEM_NORMAL,text='Fit stress/strain')
        self.StrStaEdit.Append(help='Plot intensity distribution', 
            id=wxID_STRSTAPLOT, kind=wx.ITEM_NORMAL,text='Plot intensity distribution')
        self.StrStaEdit.Append(help='Save intensity distribution', 
            id=wxID_STRRINGSAVE, kind=wx.ITEM_NORMAL,text='Save intensity distribution')
        self.StrStaEdit.Append(help='Update d-zero from ave d-zero',
            id=wxID_UPDATEDZERO, kind=wx.ITEM_NORMAL,text='Update d-zero')        
        self.StrStaEdit.Append(help='Fit stress/strain data for all images', 
            id=wxID_STRSTAALLFIT, kind=wx.ITEM_NORMAL,text='All image fit')
        self.StrStaEdit.Append(help='Copy stress/strain data to other images', 
            id=wxID_STRSTACOPY, kind=wx.ITEM_NORMAL,text='Copy stress/strain')
        self.StrStaEdit.Append(help='Save stress/strain data to file', 
            id=wxID_STRSTASAVE, kind=wx.ITEM_NORMAL,text='Save stress/strain')
        self.StrStaEdit.Append(help='Load stress/strain data from file', 
            id=wxID_STRSTALOAD, kind=wx.ITEM_NORMAL,text='Load stress/strain')
        self.StrStaEdit.Append(help='Load sample data from file', 
            id=wxID_STRSTSAMPLE, kind=wx.ITEM_NORMAL,text='Load sample data')
        self.PostfillDataMenu()
            
        # PDF / PDF Controls
        self.PDFMenu = wx.MenuBar()
        self.PrefillDataMenu(self.PDFMenu)
        self.PDFEdit = wx.Menu(title='')
        self.PDFMenu.Append(menu=self.PDFEdit, title='PDF Controls')
        self.PDFEdit.Append(help='Add one or more elements to sample composition',id=wxID_PDFADDELEMENT, kind=wx.ITEM_NORMAL,
            text='Add elements')
        self.PDFEdit.Append(help='Delete element from sample composition',id=wxID_PDFDELELEMENT, kind=wx.ITEM_NORMAL,
            text='Delete element')
        self.PDFEdit.Append(help='Copy PDF controls', id=wxID_PDFCOPYCONTROLS, kind=wx.ITEM_NORMAL,
            text='Copy controls')
        self.PDFEdit.Append(help='Load PDF controls from file',id=wxID_PDFLOADCONTROLS, kind=wx.ITEM_NORMAL,
            text='Load Controls')
        self.PDFEdit.Append(help='Save PDF controls to file', id=wxID_PDFSAVECONTROLS, kind=wx.ITEM_NORMAL,
            text='Save controls')
        self.PDFEdit.Append(help='Compute PDF', id=wxID_PDFCOMPUTE, kind=wx.ITEM_NORMAL,
            text='Compute PDF')
        self.PDFEdit.Append(help='Compute all PDFs with or w/o optimization',
                            id=wxID_PDFCOMPUTEALL, kind=wx.ITEM_NORMAL,
            text='Compute all PDFs')
#        self.PDFEdit.Append(help='Optimize PDF', id=wxID_PDFOPT, kind=wx.ITEM_NORMAL,
#            text='Optimize corrections for r<Rmin section of current G(r)')
        self.PostfillDataMenu()
        
        # PDF / PDF Peaks
        self.PDFPksMenu = wx.MenuBar()
        self.PrefillDataMenu(self.PDFPksMenu)
        self.PDFPksEdit = wx.Menu(title='')
        self.PDFPksMenu.Append(menu=self.PDFPksEdit, title='PDF Peaks')
        self.PDFPksEdit.Append(help='Fit PDF peaks', id=wxID_PDFPKSFIT, kind=wx.ITEM_NORMAL,
            text='PDF peak fit')
        self.PDFPksEdit.Append(help='Sequential Peak fitting for all PDFs', id=wxID_PDFPKSFITALL, kind=wx.ITEM_NORMAL,
            text='Seq PDF peak fit')
        self.PDFPksEdit.Append(help='Copy PDF peaks', id=wxID_PDFCOPYPEAKS, kind=wx.ITEM_NORMAL,
            text='Copy peaks')
        self.PDFPksEdit.Append(help='Clear PDF peaks', id=wxID_CLEARPDFPEAKS, kind=wx.ITEM_NORMAL,
            text='Clear peaks')        
        self.PostfillDataMenu()

        
        # Phase / General tab
        self.DataGeneral = wx.MenuBar()
        self.PrefillDataMenu(self.DataGeneral)
        self.DataGeneral.Append(menu=wx.Menu(title=''),title='Select tab')
        self.GeneralCalc = wx.Menu(title='')
        self.DataGeneral.Append(menu=self.GeneralCalc,title='Compute')
        self.GeneralCalc.Append(help='Compute Fourier map',id=wxID_FOURCALC, kind=wx.ITEM_NORMAL,
            text='Fourier map')
        self.GeneralCalc.Append(help='Search Fourier map',id=wxID_FOURSEARCH, kind=wx.ITEM_NORMAL,
            text='Search map')
        self.GeneralCalc.Append(help='Run charge flipping',id=wxID_CHARGEFLIP, kind=wx.ITEM_NORMAL,
            text='Charge flipping')
        self.GeneralCalc.Append(help='Run 4D charge flipping',id=wxID_4DCHARGEFLIP, kind=wx.ITEM_NORMAL,
            text='4D Charge flipping')
        self.GeneralCalc.Enable(wxID_4DCHARGEFLIP,False)   
        self.GeneralCalc.Append(help='Clear map',id=wxID_FOURCLEAR, kind=wx.ITEM_NORMAL,
            text='Clear map')
        self.GeneralCalc.Append(help='Run Monte Carlo - Simulated Annealing',id=wxID_SINGLEMCSA, kind=wx.ITEM_NORMAL,
            text='MC/SA')
        self.GeneralCalc.Append(help='Run Monte Carlo - Simulated Annealing on multiprocessors',id=wxID_MULTIMCSA, kind=wx.ITEM_NORMAL,
            text='Multi MC/SA')            #currently not useful
        self.GeneralCalc.Append(help='Transform crystal structure',id=wxID_TRANSFORMSTRUCTURE, kind=wx.ITEM_NORMAL,
            text='Transform')
        self.PostfillDataMenu()
        
        # Phase / Data tab
        self.DataMenu = wx.MenuBar()
        self.PrefillDataMenu(self.DataMenu)
        self.DataMenu.Append(menu=wx.Menu(title=''),title='Select tab')
        self.DataEdit = wx.Menu(title='')
        self.DataMenu.Append(menu=self.DataEdit, title='Edit Phase')
        self.DataEdit.Append(id=wxID_DATACOPY, kind=wx.ITEM_NORMAL,text='Copy data',
            help='Copy phase data to other histograms')
        self.DataEdit.Append(id=wxID_DATACOPYFLAGS, kind=wx.ITEM_NORMAL,text='Copy flags',
            help='Copy phase data flags to other histograms')
        self.DataEdit.Append(id=wxID_DATASELCOPY, kind=wx.ITEM_NORMAL,text='Copy selected data',
            help='Copy selected phase data to other histograms')
        self.DataEdit.Append(id=wxID_DATAUSE, kind=wx.ITEM_NORMAL,text='Select used data',
            help='Select all histograms to use')
        self.DataEdit.Append(id=wxID_PWDRADD, kind=wx.ITEM_NORMAL,text='Add powder histograms',
            help='Select new powder histograms to be used for this phase')
        self.DataEdit.Append(id=wxID_HKLFADD, kind=wx.ITEM_NORMAL,text='Add single crystal histograms',
            help='Select new single crystal histograms to be used for this phase')
        self.DataEdit.Append(id=wxID_DATADELETE, kind=wx.ITEM_NORMAL,text='Remove histograms',
            help='Remove histograms from use for this phase')
        self.PostfillDataMenu()
            
        # Phase / Atoms tab
        self.AtomsMenu = wx.MenuBar()
        self.PrefillDataMenu(self.AtomsMenu)
        self.AtomsMenu.Append(menu=wx.Menu(title=''),title='Select tab')
        self.AtomEdit = wx.Menu(title='')
        self.AtomCompute = wx.Menu(title='')
        self.AtomsMenu.Append(menu=self.AtomEdit, title='Edit Atoms')
        self.AtomsMenu.Append(menu=self.AtomCompute, title='Compute')
        submenu = wx.Menu()
        self.AtomEdit.AppendMenu(wx.ID_ANY, 'On selected atoms...', submenu, 
            help='Set/Act on selected atoms')
        submenu.Append(wxID_ATOMSSETSEL,
            help='Set refinement flags for selected atoms',
            kind=wx.ITEM_NORMAL,
            text='Refine selected')
        submenu.Append(id=wxID_ATOMSMODIFY, kind=wx.ITEM_NORMAL,text='Modify parameters',
            help='Modify parameters values for all selected atoms')
        submenu.Append(id=wxID_ATOMSEDITINSERT, kind=wx.ITEM_NORMAL,text='Insert atom',
            help='Inserts an H atom before all selected atoms')
        submenu.Append(id=wxID_ADDHATOM, kind=wx.ITEM_NORMAL,text='Calc H atoms',
            help='Insert H atoms in expected bonding positions for selected atoms')
        submenu.Append(id=wxID_ATOMSEDITDELETE, kind=wx.ITEM_NORMAL,text='Delete atom',
            help='Delete selected atoms')
        submenu.Append(id=wxID_ATOMSTRANSFORM, kind=wx.ITEM_NORMAL,text='Transform atoms',
            help='Symmetry transform selected atoms')
#        self.AtomEdit.Append(id=wxID_ATOMSROTATE, kind=wx.ITEM_NORMAL,text='Rotate atoms',
#            help='Select atoms to rotate first')
        submenu.Append(wxID_ATOMSSETALL,
            help='Set refinement flags for all atoms',
            kind=wx.ITEM_NORMAL,
            text='Select All')
        
        self.AtomEdit.Append(id=wxID_ATOMSEDITADD, kind=wx.ITEM_NORMAL,text='Append atom',
            help='Appended as an H atom')
        self.AtomEdit.Append(id=wxID_ATOMSVIEWADD, kind=wx.ITEM_NORMAL,text='Append view point',
            help='Appended as an H atom')
        self.AtomEdit.Append(id=wxID_ATOMVIEWINSERT, kind=wx.ITEM_NORMAL,text='Insert view point',
            help='Select atom row to insert before; inserted as an H atom')
        self.AtomEdit.Append(id=wxID_UPDATEHATOM, kind=wx.ITEM_NORMAL,text='Update H atoms',
            help='Update H atoms in standard positions')
        self.AtomEdit.Append(id=wxID_ATOMMOVE, kind=wx.ITEM_NORMAL,text='Move selected atom to view point',
            help='Select a single atom to be moved to view point in plot')
        self.AtomEdit.Append(id=wxID_MAKEMOLECULE, kind=wx.ITEM_NORMAL,text='Assemble molecule',
            help='Select a single atom to assemble as a molecule from scattered atom positions')
        self.AtomEdit.Append(id=wxID_RELOADDRAWATOMS, kind=wx.ITEM_NORMAL,text='Reload draw atoms',
            help='Reload atom drawing list')
        submenu = wx.Menu()
        self.AtomEdit.AppendMenu(wx.ID_ANY, 'Reimport atoms', submenu, 
            help='Reimport atoms from file; sequence must match')
        # setup a cascade menu for the formats that have been defined
        self.ReImportMenuId = {}  # points to readers for each menu entry
        for reader in self.G2frame.ImportPhaseReaderlist:
            item = submenu.Append(
                wx.ID_ANY,help=reader.longFormatName,
                kind=wx.ITEM_NORMAL,text='reimport coordinates from '+reader.formatName+' file')
            self.ReImportMenuId[item.GetId()] = reader
        item = submenu.Append(
            wx.ID_ANY,
            help='Reimport coordinates, try to determine format from file',
            kind=wx.ITEM_NORMAL,
            text='guess format from file')
        self.ReImportMenuId[item.GetId()] = None # try all readers

        self.AtomCompute.Append(id=wxID_ATOMSDISAGL, kind=wx.ITEM_NORMAL,text='Show Distances && Angles',
            help='Compute distances & angles for selected atoms')
        self.AtomCompute.Append(id=wxID_ATOMSPDISAGL, kind=wx.ITEM_NORMAL,text='Save Distances && Angles',
            help='Compute distances & angles for selected atoms')
        self.AtomCompute.Append(id=wxID_ATOMSDENSITY, kind=wx.ITEM_NORMAL,
            text='Density',help='Compute density for current phase')
        self.AtomCompute.Append(id=wxID_VALIDPROTEIN, kind=wx.ITEM_NORMAL,
            text='Protein quality',help='Protein quality analysis')
        self.AtomCompute.ISOcalc = self.AtomCompute.Append(id=wxID_ISODISP, kind=wx.ITEM_NORMAL,
            text='ISODISTORT mode values',help='Compute values of ISODISTORT modes from atom parameters')
        
        self.PostfillDataMenu()
        
        # Phase / Imcommensurate "waves" tab 
        self.WavesData = wx.MenuBar()
        self.PrefillDataMenu(self.WavesData)
        self.WavesData.Append(menu=wx.Menu(title=''),title='Select tab')
        self.WavesDataEdit = wx.Menu(title='')
        self.WavesData.Append(menu=self.WavesDataEdit, title='Edit Wave')
        self.WavesDataEdit.Append(id=wxID_WAVEVARY, kind=wx.ITEM_NORMAL,text='Global wave vary',
            help='Global setting of wave vary flags')
        self.PostfillDataMenu()
        
        # Phase / Layer tab 
        self.LayerData = wx.MenuBar()
        self.PrefillDataMenu(self.LayerData)
        self.LayerData.Append(menu=wx.Menu(title=''),title='Select tab')
        self.LayerDataEdit = wx.Menu(title='')
        self.LayerData.Append(menu=self.LayerDataEdit, title='Operations')
        self.LayerDataEdit.Append(id=wxID_LOADDIFFAX, kind=wx.ITEM_NORMAL,text='Load from DIFFaX file',
            help='Load layer info from DIFFaX file')
        self.LayerDataEdit.Append(id=wxID_COPYPHASE, kind=wx.ITEM_NORMAL,text='Copy phase cell',
            help='Copy phase cell from another project')
        self.LayerDataEdit.Append(id=wxID_LAYERSIMULATE, kind=wx.ITEM_NORMAL,text='Simulate pattern',
            help='Simulate diffraction pattern from layer stacking')
        self.LayerDataEdit.Append(id=wxID_LAYERSFIT, kind=wx.ITEM_NORMAL,text='Fit pattern',
            help='Fit diffraction pattern with layer stacking model')
        self.LayerDataEdit.Append(id=wxID_SEQUENCESIMULATE, kind=wx.ITEM_NORMAL,text='Sequence simulations',
            help='Sequence simulation changing one parameter')
        self.PostfillDataMenu()
                 
        # Phase / Draw Options tab
        self.DataDrawOptions = wx.MenuBar()
        self.PrefillDataMenu(self.DataDrawOptions)
        self.DataDrawOptions.Append(menu=wx.Menu(title=''),title='Select tab')
        self.PostfillDataMenu()
        
        # Phase / Draw Atoms tab 
        self.DrawAtomsMenu = wx.MenuBar()
        self.PrefillDataMenu(self.DrawAtomsMenu)
        self.DrawAtomsMenu.Append(menu=wx.Menu(title=''),title='Select tab')
        self.DrawAtomEdit = wx.Menu(title='')
        self.DrawAtomCompute = wx.Menu(title='')
        self.DrawAtomRestraint = wx.Menu(title='')
        self.DrawAtomRigidBody = wx.Menu(title='')
        self.DrawAtomsMenu.Append(menu=self.DrawAtomEdit, title='Edit Figure')
        self.DrawAtomsMenu.Append(menu=self.DrawAtomCompute,title='Compute')
        self.DrawAtomsMenu.Append(menu=self.DrawAtomRestraint, title='Restraints')
        self.DrawAtomsMenu.Append(menu=self.DrawAtomRigidBody, title='Rigid body')
        self.DrawAtomEdit.Append(id=wxID_DRAWATOMSTYLE, kind=wx.ITEM_NORMAL,text='Atom style',
            help='Select atoms first')
        self.DrawAtomEdit.Append(id=wxID_DRAWATOMLABEL, kind=wx.ITEM_NORMAL,text='Atom label',
            help='Select atoms first')
        self.DrawAtomEdit.Append(id=wxID_DRAWATOMCOLOR, kind=wx.ITEM_NORMAL,text='Atom color',
            help='Select atoms first')
        self.DrawAtomEdit.Append(id=wxID_DRAWATOMRESETCOLOR, kind=wx.ITEM_NORMAL,text='Reset atom colors',
            help='Resets all atom colors to defaults')
        self.DrawAtomEdit.Append(id=wxID_DRWAEDITRADII, kind=wx.ITEM_NORMAL,text='Edit atom radii',
            help='Edit drawing atom radii')
        self.DrawAtomEdit.Append(id=wxID_DRAWVIEWPOINT, kind=wx.ITEM_NORMAL,text='View point',
            help='View point is 1st atom selected')
        self.DrawAtomEdit.Append(id=wxID_DRAWADDEQUIV, kind=wx.ITEM_NORMAL,text='Add atoms',
            help='Add symmetry & cell equivalents to drawing set from selected atoms')
        self.DrawAtomEdit.Append(id=wxID_DRAWADDSPHERE, kind=wx.ITEM_NORMAL,text='Add sphere of atoms',
            help='Add atoms within sphere of enclosure')
        self.DrawAtomEdit.Append(id=wxID_DRAWTRANSFORM, kind=wx.ITEM_NORMAL,text='Transform draw atoms',
            help='Transform selected atoms by symmetry & cell translations')
        self.DrawAtomEdit.Append(id=wxID_DRAWFILLCOORD, kind=wx.ITEM_NORMAL,text='Fill CN-sphere',
            help='Fill coordination sphere for selected atoms')            
        self.DrawAtomEdit.Append(id=wxID_DRAWFILLCELL, kind=wx.ITEM_NORMAL,text='Fill unit cell',
            help='Fill unit cell with selected atoms')
        self.DrawAtomEdit.Append(id=wxID_DRAWDELETE, kind=wx.ITEM_NORMAL,text='Delete atoms',
            help='Delete atoms from drawing set')
        self.DrawAtomCompute.Append(id=wxID_DRAWDISTVP, kind=wx.ITEM_NORMAL,text='View pt. dist.',
            help='Compute distance of selected atoms from view point')   
        self.DrawAtomCompute.Append(id=wxID_DRAWDISAGLTOR, kind=wx.ITEM_NORMAL,text='Dist. Ang. Tors.',
            help='Compute distance, angle or torsion for 2-4 selected atoms')   
        self.DrawAtomCompute.Append(id=wxID_DRAWPLANE, kind=wx.ITEM_NORMAL,text='Best plane',
            help='Compute best plane for 4+ selected atoms')   
        self.DrawAtomRestraint.Append(id=wxID_DRAWRESTRBOND, kind=wx.ITEM_NORMAL,text='Add bond restraint',
            help='Add bond restraint for selected atoms (2)')
        self.DrawAtomRestraint.Append(id=wxID_DRAWRESTRANGLE, kind=wx.ITEM_NORMAL,text='Add angle restraint',
            help='Add angle restraint for selected atoms (3: one end 1st)')
        self.DrawAtomRestraint.Append(id=wxID_DRAWRESTRPLANE, kind=wx.ITEM_NORMAL,text='Add plane restraint',
            help='Add plane restraint for selected atoms (4+)')
        self.DrawAtomRestraint.Append(id=wxID_DRAWRESTRCHIRAL, kind=wx.ITEM_NORMAL,text='Add chiral restraint',
            help='Add chiral restraint for selected atoms (4: center atom 1st)')
        self.DrawAtomRigidBody.Append(id=wxID_DRAWDEFINERB, kind=wx.ITEM_NORMAL,text='Define rigid body',
            help='Define rigid body with selected atoms')
        self.PostfillDataMenu()

        # Phase / MCSA tab
        self.MCSAMenu = wx.MenuBar()
        self.PrefillDataMenu(self.MCSAMenu)
        self.MCSAMenu.Append(menu=wx.Menu(title=''),title='Select tab')
        self.MCSAEdit = wx.Menu(title='')
        self.MCSAMenu.Append(menu=self.MCSAEdit, title='MC/SA')
        self.MCSAEdit.Append(id=wxID_ADDMCSAATOM, kind=wx.ITEM_NORMAL,text='Add atom', 
            help='Add single atom to MC/SA model')
        self.MCSAEdit.Append(id=wxID_ADDMCSARB, kind=wx.ITEM_NORMAL,text='Add rigid body', 
            help='Add rigid body to MC/SA model' )
        self.MCSAEdit.Append(id=wxID_CLEARMCSARB, kind=wx.ITEM_NORMAL,text='Clear rigid bodies', 
            help='Clear all atoms & rigid bodies from MC/SA model' )
        self.MCSAEdit.Append(id=wxID_MOVEMCSA, kind=wx.ITEM_NORMAL,text='Move MC/SA solution', 
            help='Move MC/SA solution to atom list' )
        self.MCSAEdit.Append(id=wxID_MCSACLEARRESULTS, kind=wx.ITEM_NORMAL,text='Clear results', 
            help='Clear table of MC/SA results' )
        self.PostfillDataMenu()
            
        # Phase / Texture tab
        self.TextureMenu = wx.MenuBar()
        self.PrefillDataMenu(self.TextureMenu)
        self.TextureMenu.Append(menu=wx.Menu(title=''),title='Select tab')
        self.TextureEdit = wx.Menu(title='')
        self.TextureMenu.Append(menu=self.TextureEdit, title='Texture')
        self.TextureEdit.Append(id=wxID_REFINETEXTURE, kind=wx.ITEM_NORMAL,text='Refine texture', 
            help='Refine the texture coefficients from sequential results')
#        self.TextureEdit.Append(id=wxID_CLEARTEXTURE, kind=wx.ITEM_NORMAL,text='Clear texture', 
#            help='Clear the texture coefficients' )
        self.PostfillDataMenu()
            
        # Phase / Pawley tab
        self.PawleyMenu = wx.MenuBar()
        self.PrefillDataMenu(self.PawleyMenu)
        self.PawleyMenu.Append(menu=wx.Menu(title=''),title='Select tab')
        self.PawleyEdit = wx.Menu(title='')
        self.PawleyMenu.Append(menu=self.PawleyEdit,title='Operations')
        self.PawleyEdit.Append(id=wxID_PAWLEYSET, kind=wx.ITEM_NORMAL,text='Pawley settings',
            help='Change Pawley refinement settings')
        self.PawleyEdit.Append(id=wxID_PAWLEYLOAD, kind=wx.ITEM_NORMAL,text='Pawley create',
            help='Initialize Pawley reflection list')
        self.PawleyEdit.Append(id=wxID_PAWLEYESTIMATE, kind=wx.ITEM_NORMAL,text='Pawley estimate',
            help='Estimate initial Pawley intensities')
        self.PawleyEdit.Append(id=wxID_PAWLEYUPDATE, kind=wx.ITEM_NORMAL,text='Pawley update',
            help='Update negative Pawley intensities with -0.5*Fobs and turn off refinement')
        self.PawleyEdit.Append(id=wxID_PAWLEYSELALL, kind=wx.ITEM_NORMAL,text='Select all',
            help='Select all reflections to be refined')
        self.PawleyEdit.Append(id=wxID_PAWLEYSELNONE, kind=wx.ITEM_NORMAL,text='Select none',
            help='Set flag for all reflections for no refinement')
        self.PawleyEdit.Append(id=wxID_PAWLEYSELTOGGLE, kind=wx.ITEM_NORMAL,text='Toggle Selection',
            help='Toggle Selection flag for all reflections to opposite setting')
        self.PostfillDataMenu()
            
        # Phase / Map peaks tab
        self.MapPeaksMenu = wx.MenuBar()
        self.PrefillDataMenu(self.MapPeaksMenu)
        self.MapPeaksMenu.Append(menu=wx.Menu(title=''),title='Select tab')
        self.MapPeaksEdit = wx.Menu(title='')
        self.MapPeaksMenu.Append(menu=self.MapPeaksEdit, title='Map peaks')
        self.MapPeaksEdit.Append(id=wxID_PEAKSMOVE, kind=wx.ITEM_NORMAL,text='Move peaks', 
            help='Move selected peaks to atom list')
        self.MapPeaksEdit.Append(id=wxID_PEAKSVIEWPT, kind=wx.ITEM_NORMAL,text='View point',
            help='View point is 1st peak selected')
        self.MapPeaksEdit.Append(id=wxID_PEAKSDISTVP, kind=wx.ITEM_NORMAL,text='View pt. dist.',
            help='Compute distance of selected peaks from view point')   
        self.MapPeaksEdit.Append(id=wxID_SHOWBONDS, kind=wx.ITEM_NORMAL,text='Hide bonds',
            help='Hide or show bonds between peak positions')   
        self.MapPeaksEdit.Append(id=wxID_PEAKSDA, kind=wx.ITEM_NORMAL,text='Calc dist/ang', 
            help='Calculate distance or angle for selection')
        self.MapPeaksEdit.Append(id=wxID_FINDEQVPEAKS, kind=wx.ITEM_NORMAL,text='Equivalent peaks', 
            help='Find equivalent peaks')
        self.MapPeaksEdit.Append(id=wxID_PEAKSUNIQUE, kind=wx.ITEM_NORMAL,text='Unique peaks', 
            help='Select unique set')
        self.MapPeaksEdit.Append(id=wxID_PEAKSDELETE, kind=wx.ITEM_NORMAL,text='Delete peaks', 
            help='Delete selected peaks')
        self.MapPeaksEdit.Append(id=wxID_PEAKSCLEAR, kind=wx.ITEM_NORMAL,text='Clear peaks', 
            help='Clear the map peak list')
        self.PostfillDataMenu()

        # Phase / Rigid bodies tab
        self.RigidBodiesMenu = wx.MenuBar()
        self.PrefillDataMenu(self.RigidBodiesMenu)
        self.RigidBodiesMenu.Append(menu=wx.Menu(title=''),title='Select tab')
        self.RigidBodiesEdit = wx.Menu(title='')
        self.RigidBodiesMenu.Append(menu=self.RigidBodiesEdit, title='Edit Body')
        self.RigidBodiesEdit.Append(id=wxID_ASSIGNATMS2RB, kind=wx.ITEM_NORMAL,text='Assign atoms to rigid body',
            help='Select & position rigid body in structure of existing atoms')
        self.RigidBodiesEdit.Append(id=wxID_AUTOFINDRESRB, kind=wx.ITEM_NORMAL,text='Auto find residues',
            help='Auto find of residue RBs in macromolecule')
        self.RigidBodiesEdit.Append(id=wxID_COPYRBPARMS, kind=wx.ITEM_NORMAL,text='Copy rigid body parms',
            help='Copy rigid body location & TLS parameters')
        self.RigidBodiesEdit.Append(id=wxID_GLOBALTHERM, kind=wx.ITEM_NORMAL,text='Global thermal motion',
            help='Global setting of residue thermal motion models')
        self.RigidBodiesEdit.Append(id=wxID_GLOBALRESREFINE, kind=wx.ITEM_NORMAL,text='Global residue refine',
            help='Global setting of residue RB refinement flags')
        self.RigidBodiesEdit.Append(id=wxID_RBREMOVEALL, kind=wx.ITEM_NORMAL,text='Remove all rigid bodies',
            help='Remove all rigid body assignment for atoms')
        self.PostfillDataMenu()
    # end of GSAS-II menu definitions
        
    def _init_ctrls(self, parent,name=None,size=None,pos=None):
        wx.Frame.__init__(
            self,parent=parent,
            #style=wx.DEFAULT_FRAME_STYLE ^ wx.CLOSE_BOX | wx.FRAME_FLOAT_ON_PARENT ,
            style=wx.DEFAULT_FRAME_STYLE ^ wx.CLOSE_BOX,
            size=size,pos=pos,title='GSAS-II data display')
        self._init_menus()
        if name:
            self.SetLabel(name)
        self.Show()
        
    def __init__(self,parent,frame,data=None,name=None, size=None,pos=None):
        self.G2frame = frame
        self._init_ctrls(parent,name,size,pos)
        self.data = data
        clientSize = wx.ClientDisplayRect()
        Size = self.GetSize()
        xPos = clientSize[2]-Size[0]
        self.SetPosition(wx.Point(xPos,clientSize[1]+250))
        self.AtomGrid = []
        self.selectedRow = 0
        self.lastSize = Size        
        self.manualPhaseSize = None
        self.userReSize = False
        wx.Frame.Bind(self,wx.EVT_SIZE,self.OnReSize)
            
    def OnReSize(self,event):
        '''Keep track of size changes for Phase windows
        '''
        id = self.G2frame.PatternTree.GetSelection()
        try:
            parent = self.G2frame.PatternTree.GetItemParent(id)
        except:         #avoid bad tree item on start via gpx file selection 
            parent = 0
        if self.userReSize and parent and self.G2frame.PatternTree.GetItemText(parent) == "Phases":
            newSize = event.EventObject.GetSize()
            if newSize[1] < 200: return             #avois spurious small window after Refine
            if self.lastSize == newSize:
#                if GSASIIpath.GetConfigValue('debug'):
#                    print 'no save size=',self.lastSize
                return
            self.manualPhaseSize = newSize
            self.lastSize = event.EventObject.GetSize()
#            if GSASIIpath.GetConfigValue('debug'):
#                print 'Saving Phase size=',self.manualPhaseSize
                #HowDidIgetHere()
        event.Skip()

    def SendSizeEvent(self):
        '''Prevent SendSizeEvent from overriding the saved size
        '''
        self.userReSize = False
        wx.Frame.SendSizeEvent(self)
        self.userReSize = True
        
    def setSizePosLeft(self,Size):
        '''Place the dataFrame window so that the upper left-hand corner remains in the same place;
        The size is dictated by parameter Width, unless overridden by a previous Phase window resize
        '''
        self.userReSize = False
#        if GSASIIpath.GetConfigValue('debug'):
#            print 'setSizePosLeft size',Size,self.lastSize
        Size = list(Size)
        id = self.G2frame.PatternTree.GetSelection()
        try:            #avoid bad tree item on start via gpx file selection 
            pid = self.G2frame.PatternTree.GetItemParent(id)
        except:
            pid = 0
        if pid:
            parent = self.G2frame.PatternTree.GetItemText(pid)
            # is this a phase window and has a previous window has been resized?
            if self.manualPhaseSize and parent == "Phases":
                Size = list(self.manualPhaseSize)
        Pos = self.GetPosition()
        clientSize = wx.ClientDisplayRect()     #display window size (e.g. 1304x768)
        Size[1] = min(Size[1],clientSize[2]-300)
        Size[0] = max(Size[0],300)
#        print 'current position/width:',Pos,Width
        self.SetSize(Size)
        Size[1] += 1        #kluge to ensure scrollbar settings & window properly displayed
        self.SetSize(Size)
        Pos[0] += self.lastSize[0]-Size[0]
        offSet = 0
        if Pos[0] < clientSize[2]:
            offSet = Pos[0]+Size[0]-clientSize[2]
        if offSet > 0:
            Pos[0] -= offSet
        self.SetPosition(wx.Point(Pos[0],Pos[1]))
        self.lastSize = Size
        self.userReSize = True
        
    def Clear(self):
        self.ClearBackground()
        self.DestroyChildren()
                   

################################################################################
#####  Notebook Tree Item editor
################################################################################                  
def UpdateNotebook(G2frame,data):
    '''Called when the data tree notebook entry is selected. Allows for
    editing of the text in that tree entry
    '''
    def OnNoteBook(event):
        event.Skip()
        data = G2frame.dataDisplay.GetValue().split('\n')
        G2frame.PatternTree.SetItemPyData(GetPatternTreeItemId(G2frame,G2frame.root,'Notebook'),data)
        if 'nt' not in os.name:
            G2frame.dataDisplay.AppendText('\n')
                    
    if G2frame.dataDisplay:
        G2frame.dataDisplay.Destroy()
    G2frame.dataFrame.SetLabel('Notebook')
    G2frame.dataDisplay = wx.TextCtrl(parent=G2frame.dataFrame,size=G2frame.dataFrame.GetClientSize(),
        style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER | wx.TE_DONTWRAP)
    G2frame.dataDisplay.Bind(wx.EVT_TEXT_ENTER,OnNoteBook)
    G2frame.dataDisplay.Bind(wx.EVT_KILL_FOCUS,OnNoteBook)
    for line in data:
        G2frame.dataDisplay.AppendText(line+"\n")
    G2frame.dataDisplay.AppendText('Notebook entry @ '+time.ctime()+"\n")
    G2frame.dataFrame.setSizePosLeft([400,250])
            
################################################################################
#####  Controls Tree Item editor
################################################################################           
def UpdateControls(G2frame,data):
    '''Edit overall GSAS-II controls in main Controls data tree entry
    '''
    #patch
    if 'deriv type' not in data:
        data = {}
        data['deriv type'] = 'analytic Hessian'
        data['min dM/M'] = 0.001
        data['shift factor'] = 1.
        data['max cyc'] = 3        
        data['F**2'] = False
    if 'SVDtol' not in data:
        data['SVDtol'] = 1.e-6
    if 'shift factor' not in data:
        data['shift factor'] = 1.
    if 'max cyc' not in data:
        data['max cyc'] = 3
    if 'F**2' not in data:
        data['F**2'] = False
    if 'Author' not in data:
        data['Author'] = 'no name'
    if 'FreePrm1' not in data:
        data['FreePrm1'] = 'Sample humidity (%)'
    if 'FreePrm2' not in data:
        data['FreePrm2'] = 'Sample voltage (V)'
    if 'FreePrm3' not in data:
        data['FreePrm3'] = 'Applied load (MN)'
    if 'Copy2Next' not in data:
        data['Copy2Next'] = False
    if 'Reverse Seq' not in data:
        data['Reverse Seq'] = False
    if 'UsrReject' not in data:
        data['UsrReject'] = {'minF/sig':0,'MinExt':0.01,'MaxDF/F':20.,'MaxD':500.,'MinD':0.05}
    if 'HatomFix' not in data:
        data['HatomFix'] = False
    if 'Marquardt' not in data:
        data['Marquardt'] = -3
    
    #end patch

    def SeqSizer():
        
        def OnSelectData(event):
            choices = GetPatternTreeDataNames(G2frame,['PWDR','HKLF',])
            sel = []
            try:
                if 'Seq Data' in data:
                    for item in data['Seq Data']:
                        sel.append(choices.index(item))
                    sel = [choices.index(item) for item in data['Seq Data']]
            except ValueError:  #data changed somehow - start fresh
                sel = []
            dlg = G2G.G2MultiChoiceDialog(G2frame.dataFrame, 'Sequential refinement',
                'Select dataset to include',choices)
            dlg.SetSelections(sel)
            names = []
            if dlg.ShowModal() == wx.ID_OK:
                for sel in dlg.GetSelections():
                    names.append(choices[sel])
                data['Seq Data'] = names                
                G2frame.EnableSeqRefineMenu()
            dlg.Destroy()
            wx.CallAfter(UpdateControls,G2frame,data)
            
        def OnReverse(event):
            data['Reverse Seq'] = reverseSel.GetValue()
            
        def OnCopySel(event):
            data['Copy2Next'] = copySel.GetValue() 
                    
        seqSizer = wx.BoxSizer(wx.VERTICAL)
        dataSizer = wx.BoxSizer(wx.HORIZONTAL)
        dataSizer.Add(wx.StaticText(G2frame.dataDisplay,label=' Sequential Refinement: '),0,WACV)
        selSeqData = wx.Button(G2frame.dataDisplay,-1,label=' Select data')
        selSeqData.Bind(wx.EVT_BUTTON,OnSelectData)
        dataSizer.Add(selSeqData,0,WACV)
        SeqData = data.get('Seq Data',[])
        if not SeqData:
            lbl = ' (no data selected)'
        else:
            lbl = ' ('+str(len(SeqData))+' dataset(s) selected)'

        dataSizer.Add(wx.StaticText(G2frame.dataDisplay,label=lbl),0,WACV)
        seqSizer.Add(dataSizer,0)
        if SeqData:
            selSizer = wx.BoxSizer(wx.HORIZONTAL)
            reverseSel = wx.CheckBox(G2frame.dataDisplay,-1,label=' Reverse order?')
            reverseSel.Bind(wx.EVT_CHECKBOX,OnReverse)
            reverseSel.SetValue(data['Reverse Seq'])
            selSizer.Add(reverseSel,0,WACV)
            copySel =  wx.CheckBox(G2frame.dataDisplay,-1,label=' Copy results to next histogram?')
            copySel.Bind(wx.EVT_CHECKBOX,OnCopySel)
            copySel.SetValue(data['Copy2Next'])
            selSizer.Add(copySel,0,WACV)
            seqSizer.Add(selSizer,0)
        return seqSizer
        
    def LSSizer():        
        
        def OnDerivType(event):
            data['deriv type'] = derivSel.GetValue()
            derivSel.SetValue(data['deriv type'])
            wx.CallAfter(UpdateControls,G2frame,data)
            
        def OnMaxCycles(event):
            data['max cyc'] = int(maxCyc.GetValue())
            maxCyc.SetValue(str(data['max cyc']))
            
        def OnMarqLam(event):
            data['Marquardt'] = int(marqLam.GetValue())
            marqLam.SetValue(str(data['Marquardt']))
                        
        def OnFactor(event):
            event.Skip()
            try:
                value = min(max(float(Factr.GetValue()),0.00001),100.)
            except ValueError:
                value = 1.0
            data['shift factor'] = value
            Factr.SetValue('%.5f'%(value))
            
        def OnFsqRef(event):
            data['F**2'] = fsqRef.GetValue()
            
        LSSizer = wx.FlexGridSizer(cols=4,vgap=5,hgap=5)
        LSSizer.Add(wx.StaticText(G2frame.dataDisplay,label=' Refinement derivatives: '),0,WACV)
        Choice=['analytic Jacobian','numeric','analytic Hessian']   #TODO +'SVD refine' - what flags will it need?
        derivSel = wx.ComboBox(parent=G2frame.dataDisplay,value=data['deriv type'],choices=Choice,
            style=wx.CB_READONLY|wx.CB_DROPDOWN)
        derivSel.SetValue(data['deriv type'])
        derivSel.Bind(wx.EVT_COMBOBOX, OnDerivType)
            
        LSSizer.Add(derivSel,0,WACV)
        LSSizer.Add(wx.StaticText(G2frame.dataDisplay,label=' Min delta-M/M: '),0,WACV)
        LSSizer.Add(G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data,'min dM/M',nDig=(10,2,'g'),min=1.e-9,max=1.),0,WACV)
        if 'Hessian' in data['deriv type']:
            LSSizer.Add(wx.StaticText(G2frame.dataDisplay,label=' Max cycles: '),0,WACV)
            Choice = ['0','1','2','3','5','10','15','20']
            maxCyc = wx.ComboBox(parent=G2frame.dataDisplay,value=str(data['max cyc']),choices=Choice,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
            maxCyc.Bind(wx.EVT_COMBOBOX, OnMaxCycles)
            LSSizer.Add(maxCyc,0,WACV)
            LSSizer.Add(wx.StaticText(G2frame.dataDisplay,label=' Initial lambda = 10**'),0,WACV)
            MarqChoice = ['-3','-2','-1','0','1','2','3','4']
            marqLam = wx.ComboBox(parent=G2frame.dataDisplay,value=str(data['Marquardt']),choices=MarqChoice,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
            marqLam.Bind(wx.EVT_COMBOBOX,OnMarqLam)
            LSSizer.Add(marqLam,0,WACV)
            LSSizer.Add(wx.StaticText(G2frame.dataDisplay,label=' SVD zero tolerance:'),0,WACV)
            LSSizer.Add(G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data,'SVDtol',nDig=(10,1,'g'),min=1.e-9,max=.01),0,WACV)
        else:       #TODO what for SVD refine?
            LSSizer.Add(wx.StaticText(G2frame.dataDisplay,label=' Initial shift factor: '),0,WACV)
            Factr = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data,'shift factor',nDig=(10,5),min=1.e-5,max=100.)
            LSSizer.Add(Factr,0,WACV)
        if G2frame.Sngl:
            userReject = data['UsrReject']
            usrRej = {'minF/sig':[' Min obs/sig (0-5): ',[0,5], ],'MinExt':[' Min extinct. (0-.9): ',[0,.9],],
                'MaxDF/F':[' Max delt-F/sig (3-1000): ',[3.,1000.],],'MaxD':[' Max d-spacing (3-500): ',[3,500],],
                'MinD':[' Min d-spacing (0.1-2.0): ',[0.1,2.0],]}

            fsqRef = wx.CheckBox(G2frame.dataDisplay,-1,label='Refine HKLF as F^2? ')
            fsqRef.SetValue(data['F**2'])
            fsqRef.Bind(wx.EVT_CHECKBOX,OnFsqRef)
            LSSizer.Add(fsqRef,0,WACV)
            LSSizer.Add((1,0),)
            for item in usrRej:
                LSSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,label=usrRej[item][0]),0,WACV)
                usrrej = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,userReject,item,nDig=(10,2),
                    min=usrRej[item][1][0],max=usrRej[item][1][1])
                LSSizer.Add(usrrej,0,WACV)
        return LSSizer
        
    def AuthSizer():

        def OnAuthor(event):
            event.Skip()
            data['Author'] = auth.GetValue()

        Author = data['Author']
        authSizer = wx.BoxSizer(wx.HORIZONTAL)
        authSizer.Add(wx.StaticText(G2frame.dataDisplay,label=' CIF Author (last, first):'),0,WACV)
        auth = wx.TextCtrl(G2frame.dataDisplay,-1,value=Author,style=wx.TE_PROCESS_ENTER)
        auth.Bind(wx.EVT_TEXT_ENTER,OnAuthor)
        auth.Bind(wx.EVT_KILL_FOCUS,OnAuthor)
        authSizer.Add(auth,0,WACV)
        return authSizer
        
        
    if G2frame.dataDisplay:
        G2frame.dataDisplay.Destroy()
    if not G2frame.dataFrame.GetStatusBar():
        Status = G2frame.dataFrame.CreateStatusBar()
        Status.SetStatusText('')
    G2frame.dataFrame.SetLabel('Controls')
    G2frame.dataDisplay = wx.Panel(G2frame.dataFrame)
    SetDataMenuBar(G2frame,G2frame.dataFrame.ControlsMenu)
    mainSizer = wx.BoxSizer(wx.VERTICAL)
    mainSizer.Add((5,5),0)
    mainSizer.Add(wx.StaticText(G2frame.dataDisplay,label=' Refinement Controls:'),0,WACV)    
    mainSizer.Add(LSSizer())
    mainSizer.Add((5,5),0)
    mainSizer.Add(SeqSizer())
    mainSizer.Add((5,5),0)
    mainSizer.Add(AuthSizer())
    mainSizer.Add((5,5),0)
        
    mainSizer.Layout()    
    G2frame.dataDisplay.SetSizer(mainSizer)
    G2frame.dataFrame.setSizePosLeft(mainSizer.Fit(G2frame.dataFrame))
     
################################################################################
#####  Comments
################################################################################           
       
def UpdateComments(G2frame,data):                   

    if G2frame.dataDisplay:
        G2frame.dataDisplay.Destroy()
    G2frame.dataFrame.SetLabel('Comments')
    G2frame.dataDisplay = wx.TextCtrl(parent=G2frame.dataFrame,size=G2frame.dataFrame.GetClientSize(),
        style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_DONTWRAP)
    for line in data:
        if '\n' not in line:
            G2frame.dataDisplay.AppendText(line+'\n')
        else:
            G2frame.dataDisplay.AppendText(line)
    G2frame.dataFrame.setSizePosLeft([400,250])
            
################################################################################
#####  Display of Sequential Results
################################################################################           
       
def UpdateSeqResults(G2frame,data,prevSize=None):
    """
    Called when the Sequential Results data tree entry is selected
    to show results from a sequential refinement.
    
    :param wx.Frame G2frame: main GSAS-II data tree windows

    :param dict data: a dictionary containing the following items:  

            * 'histNames' - list of histogram names in order as processed by Sequential Refinement
            * 'varyList' - list of variables - identical over all refinements in sequence
              note that this is the original list of variables, prior to processing
              constraints.
            * 'variableLabels' -- a dict of labels to be applied to each parameter
              (this is created as an empty dict if not present in data).
            * keyed by histName - dictionaries for all data sets processed, which contains:

              * 'variables'- result[0] from leastsq call
              * 'varyList' - list of variables passed to leastsq call (not same as above)
              * 'sig' - esds for variables
              * 'covMatrix' - covariance matrix from individual refinement
              * 'title' - histogram name; same as dict item name
              * 'newAtomDict' - new atom parameters after shifts applied
              * 'newCellDict' - refined cell parameters after shifts to A0-A5 from Dij terms applied'
    """
    def GetSampleParms():
        '''Make a dictionary of the sample parameters that are not the same over the
        refinement series. Controls here is local
        '''
        if 'IMG' in histNames[0]:
            sampleParmDict = {'Sample load':[],}
        else:
            sampleParmDict = {'Temperature':[],'Pressure':[],'Time':[],
                'FreePrm1':[],'FreePrm2':[],'FreePrm3':[],'Omega':[],
                'Chi':[],'Phi':[],'Azimuth':[],}
        Controls = G2frame.PatternTree.GetItemPyData(
            GetPatternTreeItemId(G2frame,G2frame.root, 'Controls'))
        sampleParm = {}
        for name in histNames:
            if 'IMG' in name:
                if name not in data:
                    continue
                for item in sampleParmDict:
                    sampleParmDict[item].append(data[name]['parmDict'].get(item,0))
            else:
                if 'PDF' in name:
                    name = 'PWDR' + name[4:]
                Id = GetPatternTreeItemId(G2frame,G2frame.root,name)
                if Id:
                    sampleData = G2frame.PatternTree.GetItemPyData(GetPatternTreeItemId(G2frame,Id,'Sample Parameters'))
                    for item in sampleParmDict:
                        sampleParmDict[item].append(sampleData.get(item,0))
        for item in sampleParmDict:
            if sampleParmDict[item]:
                frstValue = sampleParmDict[item][0]
                if np.any(np.array(sampleParmDict[item])-frstValue):
                    if item.startswith('FreePrm'):
                        sampleParm[Controls[item]] = sampleParmDict[item]
                    else:
                        sampleParm[item] = sampleParmDict[item]
        return sampleParm

    def GetColumnInfo(col):
        '''returns column label, lists of values and errors (or None) for each column in the table
        for plotting. The column label is reformatted from Unicode to MatPlotLib encoding
        '''
        colName = G2frame.SeqTable.GetColLabelValue(col)
        plotName = variableLabels.get(colName,colName)
        plotName = plotSpCharFix(plotName)
        return plotName,G2frame.colList[col],G2frame.colSigs[col]
            
    def PlotSelect(event):
        'Plots a row (covariance) or column on double-click'
        cols = G2frame.dataDisplay.GetSelectedCols()
        rows = G2frame.dataDisplay.GetSelectedRows()
        if cols:
            G2plt.PlotSelectedSequence(G2frame,cols,GetColumnInfo,SelectXaxis)
        elif rows:
            name = histNames[rows[0]]       #only does 1st one selected
            G2plt.PlotCovariance(G2frame,data[name])
        else:
            G2frame.ErrorDialog(
                'Select row or columns',
                'Nothing selected in table. Click on column or row label(s) to plot. N.B. Grid selection can be a bit funky.'
                )
            
    def OnPlotSelSeq(event):
        'plot the selected columns or row from menu command'
        cols = sorted(G2frame.dataDisplay.GetSelectedCols()) # ignore selection order
        rows = G2frame.dataDisplay.GetSelectedRows()
        if cols:
            G2plt.PlotSelectedSequence(G2frame,cols,GetColumnInfo,SelectXaxis)
        elif rows:
            name = histNames[rows[0]]       #only does 1st one selected
            G2plt.PlotCovariance(G2frame,data[name])
        else:
            G2frame.ErrorDialog(
                'Select columns',
                'No columns or rows selected in table. Click on row or column labels to select fields for plotting.'
                )
                
    def OnAveSelSeq(event):
        'average the selected columns from menu command'
        cols = sorted(G2frame.dataDisplay.GetSelectedCols()) # ignore selection order
        useCol = -np.array(G2frame.SeqTable.GetColValues(0),dtype=bool)
        if cols:
            for col in cols:
                items = GetColumnInfo(col)[1]
                noneMask = np.array([item is None for item in items])
                info = ma.array(items,mask=useCol+noneMask)
                ave = ma.mean(ma.compressed(info))
                sig = ma.std(ma.compressed(info))
                print ' Average for '+G2frame.SeqTable.GetColLabelValue(col)+': '+'%.6g'%(ave)+' +/- '+'%.6g'%(sig)
        else:
            G2frame.ErrorDialog(
                'Select columns',
                'No columns selected in table. Click on column labels to select fields for averaging.'
                )
                
    def OnRenameSelSeq(event):
        cols = sorted(G2frame.dataDisplay.GetSelectedCols()) # ignore selection order
        colNames = [G2frame.SeqTable.GetColLabelValue(c) for c in cols]
        newNames = colNames[:]
        for i,name in enumerate(colNames):
            if name in variableLabels:
                newNames[i] = variableLabels[name]
        if not cols:
            G2frame.ErrorDialog('Select columns',
                'No columns selected in table. Click on column labels to select fields for rename.')
            return
        dlg = G2G.MultiStringDialog(G2frame.dataDisplay,'Set column names',colNames,newNames)
        if dlg.Show():
            newNames = dlg.GetValues()            
            variableLabels.update(dict(zip(colNames,newNames)))
        data['variableLabels'] = variableLabels 
        dlg.Destroy()
        UpdateSeqResults(G2frame,data,G2frame.dataDisplay.GetSize()) # redisplay variables
        G2plt.PlotSelectedSequence(G2frame,cols,GetColumnInfo,SelectXaxis)
            
    def OnReOrgSelSeq(event):
        'Reorder the columns'
        G2G.GetItemOrder(G2frame,VaryListChanges,vallookup,posdict)    
        UpdateSeqResults(G2frame,data,G2frame.dataDisplay.GetSize()) # redisplay variables

    def OnSaveSelSeqCSV(event):
        'export the selected columns to a .csv file from menu command'
        OnSaveSelSeq(event,csv=True)
        
    def OnSaveSeqCSV(event):
        'export all columns to a .csv file from menu command'
        OnSaveSelSeq(event,csv=True,allcols=True)
        
    def OnSaveSelSeq(event,csv=False,allcols=False):
        'export the selected columns to a .txt or .csv file from menu command'
        def WriteCSV():
            def WriteList(headerItems):
                line = ''
                for lbl in headerItems:
                    if line: line += ','
                    line += '"'+lbl+'"'
                return line
            head = ['name']
            for col in cols:
                item = G2frame.SeqTable.GetColLabelValue(col)
                # get rid of labels that have Unicode characters
                if not all([ord(c) < 128 and ord(c) != 0 for c in item]): item = '?'
                if col in havesig:
                    head += [item,'esd-'+item]
                else:
                    head += [item]
            SeqFile.write(WriteList(head)+'\n')
            for row,name in enumerate(saveNames):
                line = '"'+saveNames[row]+'"'
                for col in cols:
                    if col in havesig:
                        line += ','+str(saveData[col][row])+','+str(saveSigs[col][row])
                    else:
                        line += ','+str(saveData[col][row])
                SeqFile.write(line+'\n')
        def WriteSeq():
            lenName = len(saveNames[0])
            line = '  %s  '%('name'.center(lenName))
            for col in cols:
                item = G2frame.SeqTable.GetColLabelValue(col)
                if col in havesig:
                    line += ' %12s %12s '%(item.center(12),'esd'.center(12))
                else:
                    line += ' %12s '%(item.center(12))
            SeqFile.write(line+'\n')
            for row,name in enumerate(saveNames):
                line = " '%s' "%(saveNames[row])
                for col in cols:
                    if col in havesig:
                        line += ' %12.6f %12.6f '%(saveData[col][row],saveSigs[col][row])
                    else:
                        line += ' %12.6f '%saveData[col][row]
                SeqFile.write(line+'\n')

        # start of OnSaveSelSeq code
        if allcols:
            cols = range(G2frame.SeqTable.GetNumberCols())
        else:
            cols = sorted(G2frame.dataDisplay.GetSelectedCols()) # ignore selection order
        nrows = G2frame.SeqTable.GetNumberRows()
        if not cols:
            G2frame.ErrorDialog('Select columns',
                             'No columns selected in table. Click on column labels to select fields for output.')
            return
        saveNames = [G2frame.SeqTable.GetRowLabelValue(r) for r in range(nrows)]
        saveData = {}
        saveSigs = {}
        havesig = []
        for col in cols:
            name,vals,sigs = GetColumnInfo(col)
            saveData[col] = vals
            if sigs:
                havesig.append(col)
                saveSigs[col] = sigs
        if csv:
            wild = 'CSV output file (*.csv)|*.csv'
        else:
            wild = 'Text output file (*.txt)|*.txt'
        pth = G2G.GetExportPath(G2frame)
        dlg = wx.FileDialog(
            G2frame,
            'Choose text output file for your selection', pth, '', 
            wild,wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                SeqTextFile = dlg.GetPath()
                SeqTextFile = G2IO.FileDlgFixExt(dlg,SeqTextFile) 
                SeqFile = open(SeqTextFile,'w')
                if csv:
                    WriteCSV()
                else:
                    WriteSeq()
                SeqFile.close()
        finally:
            dlg.Destroy()
                
    def striphist(var,insChar=''):
        'strip a histogram number from a var name'
        sv = var.split(':')
        if len(sv) <= 1: return var
        if sv[1]:
            sv[1] = insChar
        return ':'.join(sv)
        
    def plotSpCharFix(lbl):
        'Change selected unicode characters to their matplotlib equivalent'
        for u,p in [
            (u'\u03B1',r'$\alpha$'),
            (u'\u03B2',r'$\beta$'),
            (u'\u03B3',r'$\gamma$'),
            (u'\u0394\u03C7',r'$\Delta\chi$'),
            ]:
            lbl = lbl.replace(u,p)
        return lbl
    
    def SelectXaxis():
        'returns a selected column number (or None) as the X-axis selection'
        ncols = G2frame.SeqTable.GetNumberCols()
        colNames = [G2frame.SeqTable.GetColLabelValue(r) for r in range(ncols)]
        dlg = G2G.G2SingleChoiceDialog(
            G2frame.dataDisplay,
            'Select x-axis parameter for plot or Cancel for sequence number',
            'Select X-axis',
            colNames)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                col = dlg.GetSelection()
            else:
                col = None
        finally:
            dlg.Destroy()
        return col
    
    def EnablePseudoVarMenus():
        'Enables or disables the PseudoVar menu items that require existing defs'
        if data['SeqPseudoVars']:
            val = True
        else:
            val = False
        G2frame.dataFrame.SequentialPvars.Enable(wxDELSEQVAR,val)
        G2frame.dataFrame.SequentialPvars.Enable(wxEDITSEQVAR,val)

    def DelPseudoVar(event):
        'Ask the user to select a pseudo var expression to delete'
        choices = data['SeqPseudoVars'].keys()
        selected = G2G.ItemSelector(
            choices,G2frame.dataFrame,
            multiple=True,
            title='Select expressions to remove',
            header='Delete expression')
        if selected is None: return
        for item in selected:
            del data['SeqPseudoVars'][choices[item]]
        if selected:
            UpdateSeqResults(G2frame,data,G2frame.dataDisplay.GetSize()) # redisplay variables

    def EditPseudoVar(event):
        'Edit an existing pseudo var expression'
        choices = data['SeqPseudoVars'].keys()
        if len(choices) == 1:
            selected = 0
        else:
            selected = G2G.ItemSelector(
                choices,G2frame.dataFrame,
                multiple=False,
                title='Select an expression to edit',
                header='Edit expression')
        if selected is not None:
            dlg = G2exG.ExpressionDialog(
                G2frame.dataDisplay,PSvarDict,
                data['SeqPseudoVars'][choices[selected]],
                header="Edit the PseudoVar expression",
                VarLabel="PseudoVar #"+str(selected+1),
                fit=False)
            newobj = dlg.Show(True)
            if newobj:
                calcobj = G2obj.ExpressionCalcObj(newobj)
                del data['SeqPseudoVars'][choices[selected]]
                data['SeqPseudoVars'][calcobj.eObj.expression] = newobj
                UpdateSeqResults(G2frame,data,G2frame.dataDisplay.GetSize()) # redisplay variables
        
    def AddNewPseudoVar(event):
        'Create a new pseudo var expression'
        dlg = G2exG.ExpressionDialog(G2frame.dataDisplay,PSvarDict,
            header='Enter an expression for a PseudoVar here',
            VarLabel = "New PseudoVar",fit=False)
        obj = dlg.Show(True)
        dlg.Destroy()
        if obj:
            calcobj = G2obj.ExpressionCalcObj(obj)
            data['SeqPseudoVars'][calcobj.eObj.expression] = obj
            UpdateSeqResults(G2frame,data,G2frame.dataDisplay.GetSize()) # redisplay variables
            
    def AddNewDistPseudoVar(event):
        obj = None
        dlg = G2exG.BondDialog(
            G2frame.dataDisplay,Phases,PSvarDict,
            header='Select a Bond here',
            VarLabel = "New Bond")
        if dlg.ShowModal() == wx.ID_OK:
            pName,Oatom,Tatom = dlg.GetSelection()
            if Tatom:
                Phase = Phases[pName]
                General = Phase['General']
                cx,ct = General['AtomPtrs'][:2]
                pId = Phase['pId']
                SGData = General['SGData']
                sB = Tatom.find('(')+1
                symNo = 0
                if sB:
                    sF = Tatom.find(')')
                    symNo = int(Tatom[sB:sF])
                cellNo = [0,0,0]
                cB = Tatom.find('[')
                if cB>0:
                    cF = Tatom.find(']')+1
                    cellNo = eval(Tatom[cB:cF])
                Atoms = Phase['Atoms']
                aNames = [atom[ct-1] for atom in Atoms]
                oId = aNames.index(Oatom)
                tId = aNames.index(Tatom.split(' +')[0])
                # create an expression object
                obj = G2obj.ExpressionObj()
                obj.expression = 'Dist(%s,\n%s)'%(Oatom,Tatom.split(' d=')[0].replace(' ',''))
                obj.distance_dict = {'pId':pId,'SGData':SGData,'symNo':symNo,'cellNo':cellNo}
                obj.distance_atoms = [oId,tId]
        else: 
            dlg.Destroy()
            return
        dlg.Destroy()
        if obj:
            data['SeqPseudoVars'][obj.expression] = obj
            UpdateSeqResults(G2frame,data,G2frame.dataDisplay.GetSize()) # redisplay variables

    def AddNewAnglePseudoVar(event):
        obj = None
        dlg = G2exG.AngleDialog(
            G2frame.dataDisplay,Phases,PSvarDict,
            header='Enter an Angle here',
            VarLabel = "New Angle")
        if dlg.ShowModal() == wx.ID_OK:
            pName,Oatom,Tatoms = dlg.GetSelection()
            if Tatoms:
                Phase = Phases[pName]
                General = Phase['General']
                cx,ct = General['AtomPtrs'][:2]
                pId = Phase['pId']
                SGData = General['SGData']
                Atoms = Phase['Atoms']
                aNames = [atom[ct-1] for atom in Atoms]
                tIds = []
                symNos = []
                cellNos = []
                oId = aNames.index(Oatom)
                Tatoms = Tatoms.split(';')
                for Tatom in Tatoms:
                    sB = Tatom.find('(')+1
                    symNo = 0
                    if sB:
                        sF = Tatom.find(')')
                        symNo = int(Tatom[sB:sF])
                    symNos.append(symNo)
                    cellNo = [0,0,0]
                    cB = Tatom.find('[')
                    if cB>0:
                        cF = Tatom.find(']')+1
                        cellNo = eval(Tatom[cB:cF])
                    cellNos.append(cellNo)
                    tIds.append(aNames.index(Tatom.split('+')[0]))
                # create an expression object
                obj = G2obj.ExpressionObj()
                obj.expression = 'Angle(%s,%s,\n%s)'%(Tatoms[0],Oatom,Tatoms[1])
                obj.angle_dict = {'pId':pId,'SGData':SGData,'symNo':symNos,'cellNo':cellNos}
                obj.angle_atoms = [oId,tIds]
        else: 
            dlg.Destroy()
            return
        dlg.Destroy()
        if obj:
            data['SeqPseudoVars'][obj.expression] = obj
            UpdateSeqResults(G2frame,data,G2frame.dataDisplay.GetSize()) # redisplay variables
            
    def UpdateParmDict(parmDict):
        '''generate the atom positions and the direct & reciprocal cell values,
        because they might be needed to evaluate the pseudovar
        '''
        Ddict = dict(zip(['D11','D22','D33','D12','D13','D23'],
                         ['A'+str(i) for i in range(6)])
                     )
        delList = []
        phaselist = []
        for item in parmDict: 
            if ':' not in item: continue
            key = item.split(':')
            if len(key) < 3: continue
            # remove the dA[xyz] terms, they would only bring confusion
            if key[0] and key[0] not in phaselist: phaselist.append(key[0])
            if key[2].startswith('dA'):
                delList.append(item)
            # compute and update the corrected reciprocal cell terms using the Dij values
            elif key[2] in Ddict:
                akey = key[0]+'::'+Ddict[key[2]]
                parmDict[akey] -= parmDict[item]
                delList.append(item)
        for item in delList:
            del parmDict[item]                
        for i in phaselist:
            pId = int(i)
            # apply cell symmetry
            A,zeros = G2stIO.cellFill(str(pId)+'::',SGdata[pId],parmDict,zeroDict[pId])
            # convert to direct cell & add the unique terms to the dictionary
            for i,val in enumerate(G2lat.A2cell(A)):
                if i in uniqCellIndx[pId]:
                    lbl = str(pId)+'::'+cellUlbl[i]
                    parmDict[lbl] = val
            lbl = str(pId)+'::'+'Vol'
            parmDict[lbl] = G2lat.calc_V(A)
        return parmDict

    def EvalPSvarDeriv(calcobj,parmDict,sampleDict,var,ESD):
        '''Evaluate an expression derivative with respect to a
        GSAS-II variable name.

        Note this likely could be faster if the loop over calcobjs were done
        inside after the Dict was created. 
        '''
        if not ESD:
            return 0.
        step = ESD/10
        Ddict = dict(zip(['D11','D22','D33','D12','D13','D23'],
                         ['A'+str(i) for i in range(6)])
                     )
        results = []
        phaselist = []
        VparmDict = sampleDict.copy()
        for incr in step,-step:
            VparmDict.update(parmDict.copy())           
            # as saved, the parmDict has updated 'A[xyz]' values, but 'dA[xyz]'
            # values are not zeroed: fix that!
            VparmDict.update({item:0.0 for item in parmDict if 'dA' in item})
            VparmDict[var] += incr
            G2mv.Dict2Map(VparmDict,[]) # apply constraints
            # generate the atom positions and the direct & reciprocal cell values now, because they might
            # needed to evaluate the pseudovar
            for item in VparmDict:
                if item in sampleDict:
                    continue 
                if ':' not in item: continue
                key = item.split(':')
                if len(key) < 3: continue
                # apply any new shifts to atom positions
                if key[2].startswith('dA'):
                    VparmDict[''.join(item.split('d'))] += VparmDict[item]
                    VparmDict[item] = 0.0
                # compute and update the corrected reciprocal cell terms using the Dij values
                if key[2] in Ddict:
                    if key[0] not in phaselist: phaselist.append(key[0])
                    akey = key[0]+'::'+Ddict[key[2]]
                    VparmDict[akey] -= VparmDict[item]
            for i in phaselist:
                pId = int(i)
                # apply cell symmetry
                A,zeros = G2stIO.cellFill(str(pId)+'::',SGdata[pId],VparmDict,zeroDict[pId])
                # convert to direct cell & add the unique terms to the dictionary
                for i,val in enumerate(G2lat.A2cell(A)):
                    if i in uniqCellIndx[pId]:
                        lbl = str(pId)+'::'+cellUlbl[i]
                        VparmDict[lbl] = val
                lbl = str(pId)+'::'+'Vol'
                VparmDict[lbl] = G2lat.calc_V(A)
            # dict should be fully updated, use it & calculate
            calcobj.SetupCalc(VparmDict)
            results.append(calcobj.EvalExpression())
        if None in results:
            return None
        return (results[0] - results[1]) / (2.*step)
        
    def EnableParFitEqMenus():
        'Enables or disables the Parametric Fit menu items that require existing defs'
        if data['SeqParFitEqList']:
            val = True
        else:
            val = False
        G2frame.dataFrame.SequentialPfit.Enable(wxDELPARFIT,val)
        G2frame.dataFrame.SequentialPfit.Enable(wxEDITPARFIT,val)
        G2frame.dataFrame.SequentialPfit.Enable(wxDOPARFIT,val)

    def ParEqEval(Values,calcObjList,varyList):
        '''Evaluate the parametric expression(s)
        :param list Values: a list of values for each variable parameter
        :param list calcObjList: a list of :class:`GSASIIobj.ExpressionCalcObj`
          expression objects to evaluate
        :param list varyList: a list of variable names for each value in Values
        '''
        result = []
        for calcobj in calcObjList:
            calcobj.UpdateVars(varyList,Values)
            if calcobj.depSig:
                result.append((calcobj.depVal-calcobj.EvalExpression())/calcobj.depSig)
            else:
                result.append(calcobj.depVal-calcobj.EvalExpression())
        return result

    def DoParEqFit(event,eqObj=None):
        'Parametric fit minimizer'
        varyValueDict = {} # dict of variables and their initial values
        calcObjList = [] # expression objects, ready to go for each data point
        if eqObj is not None:
            eqObjList = [eqObj,]
        else:
            eqObjList = data['SeqParFitEqList']
        UseFlags = G2frame.SeqTable.GetColValues(0)         
        for obj in eqObjList:
            # assemble refined vars for this equation
            varyValueDict.update({var:val for var,val in obj.GetVariedVarVal()})
            # lookup dependent var position
            depVar = obj.GetDepVar()
            if depVar in colLabels:
                indx = colLabels.index(depVar)
            else:
                raise Exception('Dependent variable '+depVar+' not found')
            # assemble a list of the independent variables
            indepVars = obj.GetIndependentVars()
            # loop over each datapoint
            for j,row in enumerate(zip(*G2frame.colList)):
                if not UseFlags[j]: continue
                # assemble equations to fit
                calcobj = G2obj.ExpressionCalcObj(obj)
                # prepare a dict of needed independent vars for this expression
                indepVarDict = {var:row[i] for i,var in enumerate(colLabels) if var in indepVars}
                calcobj.SetupCalc(indepVarDict)                
                # values and sigs for current value of dependent var
                if row[indx] is None: continue
                calcobj.depVal = row[indx]
                calcobj.depSig = G2frame.colSigs[indx][j]
                calcObjList.append(calcobj)
        # varied parameters
        varyList = varyValueDict.keys()
        values = varyValues = [varyValueDict[key] for key in varyList]
        if not varyList:
            print 'no variables to refine!'
            return
        try:
            result = so.leastsq(ParEqEval,varyValues,full_output=True,   #ftol=Ftol,
                args=(calcObjList,varyList))
            values = result[0]
            covar = result[1]
            if covar is None:
                raise Exception
            chisq = np.sum(result[2]['fvec']**2)
            GOF = np.sqrt(chisq/(len(calcObjList)-len(varyList)))
            esdDict = {}
            for i,avar in enumerate(varyList):
                esdDict[avar] = np.sqrt(covar[i,i])
        except:
            print('====> Fit failed')
            return
        print('==== Fit Results ====')
        print '  chisq =  %.2f, GOF = %.2f'%(chisq,GOF)
        for obj in eqObjList:
            obj.UpdateVariedVars(varyList,values)
            ind = '      '
            print('  '+obj.GetDepVar()+' = '+obj.expression)
            for var in obj.assgnVars:
                print(ind+var+' = '+obj.assgnVars[var])
            for var in obj.freeVars:
                avar = "::"+obj.freeVars[var][0]
                val = obj.freeVars[var][1]
                if obj.freeVars[var][2]:
                    print(ind+var+' = '+avar + " = " + G2mth.ValEsd(val,esdDict[avar]))
                else:
                    print(ind+var+' = '+avar + " =" + G2mth.ValEsd(val,0))
        # create a plot for each parametric variable
        for fitnum,obj in enumerate(eqObjList):
            calcobj = G2obj.ExpressionCalcObj(obj)
            # lookup dependent var position
            indx = colLabels.index(obj.GetDepVar())
            # assemble a list of the independent variables
            indepVars = obj.GetIndependentVars()            
            # loop over each datapoint
            fitvals = []
            for j,row in enumerate(zip(*G2frame.colList)):
                calcobj.SetupCalc({var:row[i] for i,var in enumerate(colLabels) if var in indepVars})
                fitvals.append(calcobj.EvalExpression())
            G2plt.PlotSelectedSequence(G2frame,[indx],GetColumnInfo,SelectXaxis,fitnum,fitvals)

    def SingleParEqFit(eqObj):
        DoParEqFit(None,eqObj)

    def DelParFitEq(event):
        'Ask the user to select function to delete'
        txtlst = [obj.GetDepVar()+' = '+obj.expression for obj in data['SeqParFitEqList']]
        selected = G2G.ItemSelector(
            txtlst,G2frame.dataFrame,
            multiple=True,
            title='Select a parametric equation(s) to remove',
            header='Delete equation')
        if selected is None: return
        data['SeqParFitEqList'] = [obj for i,obj in enumerate(data['SeqParFitEqList']) if i not in selected]
        EnableParFitEqMenus()
        if data['SeqParFitEqList']: DoParEqFit(event)
        
    def EditParFitEq(event):
        'Edit an existing parametric equation'
        txtlst = [obj.GetDepVar()+' = '+obj.expression for obj in data['SeqParFitEqList']]
        if len(txtlst) == 1:
            selected = 0
        else:
            selected = G2G.ItemSelector(
                txtlst,G2frame.dataFrame,
                multiple=False,
                title='Select a parametric equation to edit',
                header='Edit equation')
        if selected is not None:
            dlg = G2exG.ExpressionDialog(G2frame.dataDisplay,VarDict,
                data['SeqParFitEqList'][selected],depVarDict=VarDict,
                header="Edit the formula for this minimization function",
                ExtraButton=['Fit',SingleParEqFit])
            newobj = dlg.Show(True)
            if newobj:
                data['SeqParFitEqList'][selected] = newobj
                EnableParFitEqMenus()
            if data['SeqParFitEqList']: DoParEqFit(event)

    def AddNewParFitEq(event):
        'Create a new parametric equation to be fit to sequential results'

        # compile the variable names used in previous freevars to avoid accidental name collisions
        usedvarlist = []
        for obj in data['SeqParFitEqList']:
            for var in obj.freeVars:
                if obj.freeVars[var][0] not in usedvarlist: usedvarlist.append(obj.freeVars[var][0])

        dlg = G2exG.ExpressionDialog(G2frame.dataDisplay,VarDict,depVarDict=VarDict,
            header='Define an equation to minimize in the parametric fit',
            ExtraButton=['Fit',SingleParEqFit],usedVars=usedvarlist)
        obj = dlg.Show(True)
        dlg.Destroy()
        if obj:
            data['SeqParFitEqList'].append(obj)
            EnableParFitEqMenus()
            if data['SeqParFitEqList']: DoParEqFit(event)
                
    def CopyParFitEq(event):
        'Copy an existing parametric equation to be fit to sequential results'
        # compile the variable names used in previous freevars to avoid accidental name collisions
        usedvarlist = []
        for obj in data['SeqParFitEqList']:
            for var in obj.freeVars:
                if obj.freeVars[var][0] not in usedvarlist: usedvarlist.append(obj.freeVars[var][0])
        txtlst = [obj.GetDepVar()+' = '+obj.expression for obj in data['SeqParFitEqList']]
        if len(txtlst) == 1:
            selected = 0
        else:
            selected = G2G.ItemSelector(
                txtlst,G2frame.dataFrame,
                multiple=False,
                title='Select a parametric equation to copy',
                header='Copy equation')
        if selected is not None:
            newEqn = copy.deepcopy(data['SeqParFitEqList'][selected])
            for var in newEqn.freeVars:
                newEqn.freeVars[var][0] = G2obj.MakeUniqueLabel(newEqn.freeVars[var][0],usedvarlist)
            dlg = G2exG.ExpressionDialog(
                G2frame.dataDisplay,VarDict,newEqn,depVarDict=VarDict,
                header="Edit the formula for this minimization function",
                ExtraButton=['Fit',SingleParEqFit])
            newobj = dlg.Show(True)
            if newobj:
                data['SeqParFitEqList'].append(newobj)
                EnableParFitEqMenus()
            if data['SeqParFitEqList']: DoParEqFit(event)
                                            
    def GridSetToolTip(row,col):
        '''Routine to show standard uncertainties for each element in table
        as a tooltip
        '''
        if G2frame.colSigs[col]:
            return u'\u03c3 = '+str(G2frame.colSigs[col][row])
        return ''
        
    def GridColLblToolTip(col):
        '''Define a tooltip for a column. This will be the user-entered value
        (from data['variableLabels']) or the default name
        '''
        if col < 0 or col > len(colLabels):
            print 'Illegal column #',col
            return
        var = colLabels[col]
        return variableLabels.get(var,G2obj.fmtVarDescr(var))
        
    def SetLabelString(event):
        '''Define or edit the label for a column in the table, to be used
        as a tooltip and for plotting
        '''
        col = event.GetCol()
        if col < 0 or col > len(colLabels):
            return
        var = colLabels[col]
        lbl = variableLabels.get(var,G2obj.fmtVarDescr(var))
        dlg = G2G.SingleStringDialog(G2frame.dataFrame,'Set variable label',
                                 'Set a new name for variable '+var,lbl,size=(400,-1))
        if dlg.Show():
            variableLabels[var] = dlg.GetValue()
        dlg.Destroy()

    def DoSequentialExport(event):
        '''Event handler for all Sequential Export menu items
        '''
        vals = G2frame.dataFrame.SeqExportLookup.get(event.GetId())
        if vals is None:
            print('Error: Id not found. This should not happen!')
        G2IO.ExportSequential(G2frame,data,*vals)
    
    #def GridRowLblToolTip(row): return 'Row ='+str(row)
    
    # lookup table for unique cell parameters by symmetry
    cellGUIlist = [
        [['m3','m3m'],(0,)],
        [['3R','3mR'],(0,3)],
        [['3','3m1','31m','6/m','6/mmm','4/m','4/mmm'],(0,2)],
        [['mmm'],(0,1,2)],
        [['2/m'+'a'],(0,1,2,3)],
        [['2/m'+'b'],(0,1,2,4)],
        [['2/m'+'c'],(0,1,2,5)],
        [['-1'],(0,1,2,3,4,5)],
        ]
    # cell labels
    cellUlbl = ('a','b','c',u'\u03B1',u'\u03B2',u'\u03B3') # unicode a,b,c,alpha,beta,gamma

    #======================================================================
    # start processing sequential results here (UpdateSeqResults)
    #======================================================================
    if not data:
        print 'No sequential refinement results'
        return
    variableLabels = data.get('variableLabels',{})
    data['variableLabels'] = variableLabels
    Histograms,Phases = G2frame.GetUsedHistogramsAndPhasesfromTree()
    Controls = G2frame.PatternTree.GetItemPyData(GetPatternTreeItemId(G2frame,G2frame.root,'Controls'))
    # create a place to store Pseudo Vars & Parametric Fit functions, if not present
    if 'SeqPseudoVars' not in data: data['SeqPseudoVars'] = {}
    if 'SeqParFitEqList' not in data: data['SeqParFitEqList'] = []
    histNames = data['histNames']
    if G2frame.dataDisplay:
        G2frame.dataDisplay.Destroy()
    if not G2frame.dataFrame.GetStatusBar():
        Status = G2frame.dataFrame.CreateStatusBar()
        Status.SetStatusText("Select column to export; Double click on column to plot data; on row for Covariance")
    sampleParms = GetSampleParms()

    # make dict of varied atom coords keyed by absolute position
    newAtomDict = data[histNames[0]].get('newAtomDict',{}) # dict with atom positions; relative & absolute
    # Possible error: the next might need to be data[histNames[0]]['varyList']
    # error will arise if there constraints on coordinates?
    atomLookup = {newAtomDict[item][0]:item for item in newAtomDict if item in data['varyList']}
    
    # make dict of varied cell parameters equivalents
    ESDlookup = {} # provides the Dij term for each Ak term (where terms are refined)
    Dlookup = {} # provides the Ak term for each Dij term (where terms are refined)
    # N.B. These Dij vars are missing a histogram #
    newCellDict = {}
    for name in histNames:
        if name in data and 'newCellDict' in data[name]:
            newCellDict.update(data[name]['newCellDict'])
#    newCellDict = data[histNames[0]].get('newCellDict',{})
    cellAlist = []
    for item in newCellDict:
        cellAlist.append(newCellDict[item][0])
        if item in data.get('varyList',[]):
            ESDlookup[newCellDict[item][0]] = item
            Dlookup[item] = newCellDict[item][0]
    # add coordinate equivalents to lookup table
    for parm in atomLookup:
        Dlookup[atomLookup[parm]] = parm
        ESDlookup[parm] = atomLookup[parm]

    # get unit cell & symmetry for all phases & initial stuff for later use
    RecpCellTerms = {}
    SGdata = {}
    uniqCellIndx = {}
    initialCell = {}
    RcellLbls = {}
    zeroDict = {}
    for phase in Phases:
        phasedict = Phases[phase]
        pId = phasedict['pId']
        pfx = str(pId)+'::' # prefix for A values from phase
        RcellLbls[pId] = [pfx+'A'+str(i) for i in range(6)]
        RecpCellTerms[pId] = G2lat.cell2A(phasedict['General']['Cell'][1:7])
        zeroDict[pId] = dict(zip(RcellLbls[pId],6*[0.,]))
        SGdata[pId] = phasedict['General']['SGData']
        laue = SGdata[pId]['SGLaue']
        if laue == '2/m':
            laue += SGdata[pId]['SGUniq']
        for symlist,celllist in cellGUIlist:
            if laue in symlist:
                uniqCellIndx[pId] = celllist
                break
        else: # should not happen
            uniqCellIndx[pId] = range(6)
        for i in uniqCellIndx[pId]:
            initialCell[str(pId)+'::A'+str(i)] =  RecpCellTerms[pId][i]

    SetDataMenuBar(G2frame,G2frame.dataFrame.SequentialMenu)
    G2frame.dataFrame.SetLabel('Sequential refinement results')
    if not G2frame.dataFrame.GetStatusBar():
        Status = G2frame.dataFrame.CreateStatusBar()
        Status.SetStatusText('')
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnRenameSelSeq, id=wxID_RENAMESEQSEL)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnSaveSelSeq, id=wxID_SAVESEQSEL)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnSaveSelSeqCSV, id=wxID_SAVESEQSELCSV)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnSaveSeqCSV, id=wxID_SAVESEQCSV)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnPlotSelSeq, id=wxID_PLOTSEQSEL)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnAveSelSeq, id=wxID_AVESEQSEL)
    G2frame.dataFrame.Bind(wx.EVT_MENU, OnReOrgSelSeq, id=wxID_ORGSEQSEL)
    G2frame.dataFrame.Bind(wx.EVT_MENU, AddNewPseudoVar, id=wxADDSEQVAR)
    G2frame.dataFrame.Bind(wx.EVT_MENU, AddNewDistPseudoVar, id=wxADDSEQDIST)
    G2frame.dataFrame.Bind(wx.EVT_MENU, AddNewAnglePseudoVar, id=wxADDSEQANGLE)
    G2frame.dataFrame.Bind(wx.EVT_MENU, DelPseudoVar, id=wxDELSEQVAR)
    G2frame.dataFrame.Bind(wx.EVT_MENU, EditPseudoVar, id=wxEDITSEQVAR)
    G2frame.dataFrame.Bind(wx.EVT_MENU, AddNewParFitEq, id=wxADDPARFIT)
    G2frame.dataFrame.Bind(wx.EVT_MENU, CopyParFitEq, id=wxCOPYPARFIT)
    G2frame.dataFrame.Bind(wx.EVT_MENU, DelParFitEq, id=wxDELPARFIT)
    G2frame.dataFrame.Bind(wx.EVT_MENU, EditParFitEq, id=wxEDITPARFIT)
    G2frame.dataFrame.Bind(wx.EVT_MENU, DoParEqFit, id=wxDOPARFIT)

    for id in G2frame.dataFrame.SeqExportLookup:        
        G2frame.dataFrame.Bind(wx.EVT_MENU, DoSequentialExport, id=id)

    EnablePseudoVarMenus()
    EnableParFitEqMenus()

    # scan for locations where the variables change
    VaryListChanges = [] # histograms where there is a change
    combinedVaryList = []
    firstValueDict = {}
    vallookup = {}
    posdict = {}
    prevVaryList = []
    foundNames = []
    missing = 0
    for i,name in enumerate(histNames):
        if name not in data:
            if missing < 5:
                print(" Warning: "+name+" not found")
            elif missing == 5:
                print ' Warning: more are missing'
            missing += 1
            continue
        foundNames.append(name)
        maxPWL = 5
        for var,val,sig in zip(data[name]['varyList'],data[name]['variables'],data[name]['sig']):
            svar = striphist(var,'*') # wild-carded
            if 'PWL' in svar:
                if int(svar.split(':')[-1]) > maxPWL:
                    continue
            if svar not in combinedVaryList:
                # add variables to list as they appear
                combinedVaryList.append(svar)
                firstValueDict[svar] = (val,sig)
        if prevVaryList != data[name]['varyList']: # this refinement has a different refinement list from previous
            prevVaryList = data[name]['varyList']
            vallookup[name] = dict(zip(data[name]['varyList'],data[name]['variables']))
            posdict[name] = {}
            for var in data[name]['varyList']:
                svar = striphist(var,'*')
                if 'PWL' in svar:
                    if int(svar.split(':')[-1]) > maxPWL:
                        continue
                posdict[name][combinedVaryList.index(svar)] = svar
            VaryListChanges.append(name)
    if missing:
        print ' Warning: Total of %d data sets missing from sequential results'%(missing)
    if len(VaryListChanges) > 1:
        G2frame.dataFrame.SequentialFile.Enable(wxID_ORGSEQSEL,True)
    else:
        G2frame.dataFrame.SequentialFile.Enable(wxID_ORGSEQSEL,False)
    #-----------------------------------------------------------------------------------
    # build up the data table by columns -----------------------------------------------
    histNames = foundNames
    nRows = len(histNames)
    G2frame.colList = [nRows*[True]]
    G2frame.colSigs = [None]
    colLabels = ['Use']
    Types = [wg.GRID_VALUE_BOOL]
    # start with Rwp values
    if 'IMG ' not in histNames[0][:4]:
        G2frame.colList += [[data[name]['Rvals']['Rwp'] for name in histNames]]
        G2frame.colSigs += [None]
        colLabels += ['Rwp']
        Types += [wg.GRID_VALUE_FLOAT+':10,3',]
    # add % change in Chi^2 in last cycle
    if histNames[0][:4] not in ['SASD','IMG ','REFD'] and Controls.get('ShowCell'):
        G2frame.colList += [[100.*data[name]['Rvals'].get('DelChi2',-1) for name in histNames]]
        G2frame.colSigs += [None]
        colLabels += [u'\u0394\u03C7\u00B2 (%)']
        Types += [wg.GRID_VALUE_FLOAT+':10,5',]
    deltaChiCol = len(colLabels)-1
    # add changing sample parameters to table
    for key in sampleParms:
        G2frame.colList += [sampleParms[key]]
        G2frame.colSigs += [None]
        colLabels += [key]
        Types += [wg.GRID_VALUE_FLOAT,]
    sampleDict = {}
    for i,name in enumerate(histNames):
        sampleDict[name] = dict(zip(sampleParms.keys(),[sampleParms[key][i] for key in sampleParms.keys()])) 
    # add unique cell parameters TODO: review this where the cell symmetry changes (when possible)
    if Controls.get('ShowCell',False) and len(newCellDict):
        for pId in sorted(RecpCellTerms):
            pfx = str(pId)+'::' # prefix for A values from phase
            cells = []
            cellESDs = []
            colLabels += [pfx+cellUlbl[i] for i in uniqCellIndx[pId]]
            colLabels += [pfx+'Vol']
            Types += (len(uniqCellIndx[pId]))*[wg.GRID_VALUE_FLOAT+':10,5',]
            Types += [wg.GRID_VALUE_FLOAT+':10,3',]
            Albls = [pfx+'A'+str(i) for i in range(6)]
            for hId,name in enumerate(histNames):
                phfx = '%d:%d:'%(pId,hId)
                esdLookUp = {}
                dLookup = {}
                for item in data[name]['newCellDict']:
                    if phfx+item.split('::')[1] in data[name]['varyList']:
                        esdLookUp[newCellDict[item][0]] = item
                        dLookup[item] = newCellDict[item][0]
                covData = {'varyList': [dLookup.get(striphist(v),v) for v in data[name]['varyList']],
                    'covMatrix': data[name]['covMatrix']}
                A = RecpCellTerms[pId][:] # make copy of starting A values
                # update with refined values
                for i in range(6):
                    var = str(pId)+'::A'+str(i)
                    if var in cellAlist:
                        try:
                            val = data[name]['newCellDict'][esdLookUp[var]][1] # get refined value 
                            A[i] = val # override with updated value
                        except KeyError:
                            A[i] = None
                # apply symmetry
                cellDict = dict(zip(Albls,A))
                if None in A:
                    c = 6*[None]
                    cE = 6*[None]
                    vol = None
                else:
                    A,zeros = G2stIO.cellFill(pfx,SGdata[pId],cellDict,zeroDict[pId])
                    # convert to direct cell & add only unique values to table
                    c = G2lat.A2cell(A)
                    vol = G2lat.calc_V(A)
                    cE = G2stIO.getCellEsd(pfx,SGdata[pId],A,covData)
                cells += [[c[i] for i in uniqCellIndx[pId]]+[vol]]
                cellESDs += [[cE[i] for i in uniqCellIndx[pId]]+[cE[-1]]]
            G2frame.colList += zip(*cells)
            G2frame.colSigs += zip(*cellESDs)
    # sort out the variables in their selected order
    varcols = 0
    for d in posdict.itervalues():
        varcols = max(varcols,max(d.keys())+1)
    # get labels for each column
    for i in range(varcols):
        lbl = ''
        for h in VaryListChanges:
            if posdict[h].get(i):
                if posdict[h].get(i) in lbl: continue
                if lbl != "": lbl += '/'
                lbl += posdict[h].get(i)
        colLabels.append(lbl)
    Types += varcols*[wg.GRID_VALUE_FLOAT,]
    vals = []
    esds = []
    varsellist = None        # will be a list of variable names in the order they are selected to appear
    # tabulate values for each hist, leaving None for blank columns
    for name in histNames:
        if name in posdict:
            varsellist = [posdict[name].get(i) for i in range(varcols)]
            # translate variable names to how they will be used in the headings
            vs = [striphist(v,'*') for v in data[name]['varyList']]
            # determine the index for each column (or None) in the data[]['variables'] and ['sig'] lists
            sellist = [vs.index(v) if v is not None else None for v in varsellist]
            #sellist = [i if striphist(v,'*') in varsellist else None for i,v in enumerate(data[name]['varyList'])]
        if not varsellist: raise Exception()
        vals.append([data[name]['variables'][s] if s is not None else None for s in sellist])
        esds.append([data[name]['sig'][s] if s is not None else None for s in sellist])
        #GSASIIpath.IPyBreak()
    G2frame.colList += zip(*vals)
    G2frame.colSigs += zip(*esds)
    # compute and add weight fractions to table if varied
    for phase in Phases:
        var = str(Phases[phase]['pId'])+':*:Scale'
        if var not in combinedVaryList: continue
        wtFrList = []
        sigwtFrList = []
        for i,name in enumerate(histNames):
            wtFrSum = 0.
            for phase1 in Phases:
                wtFrSum += Phases[phase1]['Histograms'][name]['Scale'][0]*Phases[phase1]['General']['Mass']
            var = str(Phases[phase]['pId'])+':'+str(i)+':Scale'
            wtFr = Phases[phase]['Histograms'][name]['Scale'][0]*Phases[phase]['General']['Mass']/wtFrSum
            wtFrList.append(wtFr)
            if var in data[name]['varyList']:
                sig = data[name]['sig'][data[name]['varyList'].index(var)]*wtFr/Phases[phase]['Histograms'][name]['Scale'][0]
            else:
                sig = 0.0
            sigwtFrList.append(sig)
        colLabels.append(str(Phases[phase]['pId'])+':*:WgtFrac')
        Types += [wg.GRID_VALUE_FLOAT+':10,5',]
        G2frame.colList += [wtFrList]
        G2frame.colSigs += [sigwtFrList]
                
    # tabulate constrained variables, removing histogram numbers if needed
    # from parameter label
    depValDict = {}
    depSigDict = {}
    for name in histNames:
        for var in data[name].get('depParmDict',{}):
            val,sig = data[name]['depParmDict'][var]
            svar = striphist(var,'*')
            if svar not in depValDict:
               depValDict[svar] = [val]
               depSigDict[svar] = [sig]
            else:
               depValDict[svar].append(val)
               depSigDict[svar].append(sig)
    # add the dependent constrained variables to the table
    for var in sorted(depValDict):
        if len(depValDict[var]) != len(histNames): continue
        colLabels.append(var)
        Types += [wg.GRID_VALUE_FLOAT+':10,5',]
        G2frame.colSigs += [depSigDict[var]]
        G2frame.colList += [depValDict[var]]

    # add atom parameters to table
    colLabels += atomLookup.keys()
    for parm in sorted(atomLookup):
        G2frame.colList += [[data[name]['newAtomDict'][atomLookup[parm]][1] for name in histNames]]
        Types += [wg.GRID_VALUE_FLOAT+':10,5',]
        if atomLookup[parm] in data[histNames[0]]['varyList']:
            col = data[histNames[0]]['varyList'].index(atomLookup[parm])
            G2frame.colSigs += [[data[name]['sig'][col] for name in histNames]]
        else:
            G2frame.colSigs += [None]
    # evaluate Pseudovars, their ESDs and add them to grid
    for expr in data['SeqPseudoVars']:
        obj = data['SeqPseudoVars'][expr]
        calcobj = G2obj.ExpressionCalcObj(obj)
        valList = []
        esdList = []
        for seqnum,name in enumerate(histNames):
            sigs = data[name]['sig']
            G2mv.InitVars()
            parmDict = data[name].get('parmDict')
            constraintInfo = data[name].get('constraintInfo',[[],[],{},[],seqnum])
            groups,parmlist,constrDict,fixedList,ihst = constraintInfo
            varyList = data[name]['varyList']
            parmDict = data[name]['parmDict']
            G2mv.GenerateConstraints(groups,parmlist,varyList,constrDict,fixedList,parmDict,SeqHist=ihst)
            if 'Dist' in expr:
                derivs = G2mth.CalcDistDeriv(obj.distance_dict,obj.distance_atoms, parmDict)
                pId = obj.distance_dict['pId']
                aId,bId = obj.distance_atoms
                varyNames = ['%d::dA%s:%d'%(pId,ip,aId) for ip in ['x','y','z']]
                varyNames += ['%d::dA%s:%d'%(pId,ip,bId) for ip in ['x','y','z']]
                VCoV = G2mth.getVCov(varyNames,varyList,data[name]['covMatrix'])
                esdList.append(np.sqrt(np.inner(derivs,np.inner(VCoV,derivs.T)) ))
#                GSASIIpath.IPyBreak()
            elif 'Angle' in expr:
                derivs = G2mth.CalcAngleDeriv(obj.angle_dict,obj.angle_atoms, parmDict)
                pId = obj.angle_dict['pId']
                aId,bId = obj.angle_atoms
                varyNames = ['%d::dA%s:%d'%(pId,ip,aId) for ip in ['x','y','z']]
                varyNames += ['%d::dA%s:%d'%(pId,ip,bId[0]) for ip in ['x','y','z']]
                varyNames += ['%d::dA%s:%d'%(pId,ip,bId[1]) for ip in ['x','y','z']]
                VCoV = G2mth.getVCov(varyNames,varyList,data[name]['covMatrix'])
                esdList.append(np.sqrt(np.inner(derivs,np.inner(VCoV,derivs.T)) ))
            else:
                derivs = np.array(
                    [EvalPSvarDeriv(calcobj,parmDict.copy(),sampleDict[name],var,ESD)
                     for var,ESD in zip(varyList,sigs)])
                if None in list(derivs):
                    esdList.append(None)
                else:
                    esdList.append(np.sqrt(
                        np.inner(derivs,np.inner(data[name]['covMatrix'],derivs.T)) ))
            PSvarDict = parmDict.copy()
            PSvarDict.update(sampleDict[name])
            UpdateParmDict(PSvarDict)
            calcobj.UpdateDict(PSvarDict)
            valList.append(calcobj.EvalExpression())
#            if calcobj.su is not None: esdList[-1] = calcobj.su
        if not esdList:
            esdList = None
        G2frame.colList += [valList]
        G2frame.colSigs += [esdList]
        colLabels += [expr]
        Types += [wg.GRID_VALUE_FLOAT+':10,3']
    #---- table build done -------------------------------------------------------------

    # Make dict needed for creating & editing pseudovars (PSvarDict).
    
    name = histNames[0]
    parmDict = data[name].get('parmDict',{})
    PSvarDict = parmDict.copy()
    PSvarDict.update(sampleParms)
    UpdateParmDict(PSvarDict)
    # Also dicts of variables 
    # for Parametric fitting from the data table
    parmDict = dict(zip(colLabels,zip(*G2frame.colList)[0])) # scratch dict w/all values in table
    parmDict.update({var:val for var,val in newCellDict.values()}) #  add varied reciprocal cell terms
    del parmDict['Use']
    name = histNames[0]

    #******************************************************************************
    # create a set of values for example evaluation of pseudovars and 
    # this does not work for refinements that have differing numbers of variables.
    #raise Exception
    VarDict = {}
    for i,var in enumerate(colLabels):
        if var in ['Use','Rwp',u'\u0394\u03C7\u00B2 (%)']: continue
        if G2frame.colList[i][0] is None:
            val,sig = firstValueDict.get(var,[None,None])
        elif G2frame.colSigs[i]:
            val,sig = G2frame.colList[i][0],G2frame.colSigs[i][0]
        else:
            val,sig = G2frame.colList[i][0],None
#        if val is None: continue
#        elif sig is None or sig == 0.:
#            VarDict[var] = val
        if striphist(var) not in Dlookup:
            VarDict[var] = val
    # add recip cell coeff. values
    VarDict.update({var:val for var,val in newCellDict.values()})

    G2frame.dataFrame.currentGrids = []
    G2frame.dataDisplay = G2G.GSGrid(parent=G2frame.dataFrame)
    G2frame.SeqTable = G2G.Table([list(cl) for cl in zip(*G2frame.colList)],     # convert from columns to rows
        colLabels=colLabels,rowLabels=histNames,types=Types)
    G2frame.dataDisplay.SetTable(G2frame.SeqTable, True)
    #G2frame.dataDisplay.EnableEditing(False)
    # make all but first column read-only
    for c in range(1,len(colLabels)):
        for r in range(nRows):
            G2frame.dataDisplay.SetCellReadOnly(r,c)
    G2frame.dataDisplay.Bind(wg.EVT_GRID_LABEL_LEFT_DCLICK, PlotSelect)
    G2frame.dataDisplay.Bind(wg.EVT_GRID_LABEL_RIGHT_CLICK, SetLabelString)
    G2frame.dataDisplay.SetRowLabelSize(8*len(histNames[0]))       #pretty arbitrary 8
    G2frame.dataDisplay.SetMargins(0,0)
    G2frame.dataDisplay.AutoSizeColumns(False)
    if prevSize:
        G2frame.dataFrame.setSizePosLeft(prevSize)
    else:
        G2frame.dataFrame.setSizePosLeft([700,350])
    # highlight unconverged shifts 
    if histNames[0][:4] not in ['SASD','IMG ','REFD',]:
        for row,name in enumerate(histNames):
            deltaChi = G2frame.SeqTable.GetValue(row,deltaChiCol)
            if deltaChi > 10.:
                G2frame.dataDisplay.SetCellStyle(row,deltaChiCol,color=wx.Colour(255,0,0))
            elif deltaChi > 1.0:
                G2frame.dataDisplay.SetCellStyle(row,deltaChiCol,color=wx.Colour(255,255,0))
    G2frame.dataDisplay.InstallGridToolTip(GridSetToolTip,GridColLblToolTip)
    G2frame.dataDisplay.SendSizeEvent() # resize needed on mac
    G2frame.dataDisplay.Refresh() # shows colored text on mac
    
################################################################################
#####  Main PWDR panel
################################################################################           
       
def UpdatePWHKPlot(G2frame,kind,item):
    '''Called when the histogram main tree entry is called. Displays the
    histogram weight factor, refinement statistics for the histogram
    and the range of data for a simulation.

    Also invokes a plot of the histogram.
    '''
    def onEditSimRange(event):
        'Edit simulation range'
        inp = [
            min(data[1][0]),
            max(data[1][0]),
            None
            ]
        inp[2] = (inp[1] - inp[0])/(len(data[1][0])-1.)
        names = ('start angle', 'end angle', 'step size')
        dlg = G2G.ScrolledMultiEditor(
            G2frame,[inp] * len(inp), range(len(inp)), names,
            header='Edit simulation range',
            minvals=(0.001,0.001,0.0001),
            maxvals=(180.,180.,.1),
            )
        dlg.CenterOnParent()
        val = dlg.ShowModal()
        dlg.Destroy()
        if val != wx.ID_OK: return
        if inp[0] > inp[1]:
            end,start,step = inp
        else:                
            start,end,step = inp
        step = abs(step)
        N = int((end-start)/step)+1
        newdata = np.linspace(start,end,N,True)
        if len(newdata) < 2: return # too small a range - reject
        data[1] = [newdata,np.zeros_like(newdata),np.ones_like(newdata),
            np.zeros_like(newdata),np.zeros_like(newdata),np.zeros_like(newdata)]
        Tmin = newdata[0]
        Tmax = newdata[-1]
        G2frame.PatternTree.SetItemPyData(GetPatternTreeItemId(G2frame,item,'Limits'),
            [(Tmin,Tmax),[Tmin,Tmax]])
        UpdatePWHKPlot(G2frame,kind,item) # redisplay data screen

    def OnPlot3DHKL(event):
        refList = data[1]['RefList']
        FoMax = np.max(refList.T[8+Super])
        Hmin = np.array([int(np.min(refList.T[0])),int(np.min(refList.T[1])),int(np.min(refList.T[2]))])
        Hmax = np.array([int(np.max(refList.T[0])),int(np.max(refList.T[1])),int(np.max(refList.T[2]))])
        Vpoint = np.array([int(np.mean(refList.T[0])),int(np.mean(refList.T[1])),int(np.mean(refList.T[2]))])
        controls = {'Type' : 'Fosq','Iscale' : False,'HKLmax' : Hmax,'HKLmin' : Hmin,'Zone':False,'viewKey':'L',
            'FoMax' : FoMax,'Scale' : 1.0,'Drawing':{'viewPoint':[Vpoint,[]],'default':Vpoint[:],
            'backColor':[0,0,0],'depthFog':False,'Zclip':10.0,'cameraPos':10.,'Zstep':0.05,'viewUp':[0,1,0],
            'Scale':1.0,'oldxy':[],'viewDir':[0,0,1]},'Super':Super,'SuperVec':SuperVec}
        G2plt.Plot3DSngl(G2frame,newPlot=True,Data=controls,hklRef=refList,Title=phaseName)
        
    def OnPlotAll3DHKL(event):
        choices = GetPatternTreeDataNames(G2frame,['HKLF',])
        dlg = G2G.G2MultiChoiceDialog(G2frame, 'Select reflection sets to plot',
            'Use data',choices)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                refNames = [choices[i] for i in dlg.GetSelections()]
            else:
                return
        finally:
            dlg.Destroy()
        refList = np.zeros(0)
        for name in refNames:
            Id = GetPatternTreeItemId(G2frame,G2frame.root, name)
            reflData = G2frame.PatternTree.GetItemPyData(Id)[1]
            if len(refList):
                refList = np.concatenate((refList,reflData['RefList']))
            else:
                refList = reflData['RefList']
            
        FoMax = np.max(refList.T[8+Super])
        Hmin = np.array([int(np.min(refList.T[0])),int(np.min(refList.T[1])),int(np.min(refList.T[2]))])
        Hmax = np.array([int(np.max(refList.T[0])),int(np.max(refList.T[1])),int(np.max(refList.T[2]))])
        Vpoint = [int(np.mean(refList.T[0])),int(np.mean(refList.T[1])),int(np.mean(refList.T[2]))]
        controls = {'Type' : 'Fosq','Iscale' : False,'HKLmax' : Hmax,'HKLmin' : Hmin,'Zone':False,'viewKey':'L',
            'FoMax' : FoMax,'Scale' : 1.0,'Drawing':{'viewPoint':[Vpoint,[]],'default':Vpoint[:],
            'backColor':[0,0,0],'depthFog':False,'Zclip':10.0,'cameraPos':10.,'Zstep':0.05,'viewUp':[0,1,0],
            'Scale':1.0,'oldxy':[],'viewDir':[1,0,0]},'Super':Super,'SuperVec':SuperVec}
        G2plt.Plot3DSngl(G2frame,newPlot=True,Data=controls,hklRef=refList,Title=phaseName)
                  
    def OnMergeHKL(event):
        Name = G2frame.PatternTree.GetItemText(G2frame.PatternId)
        Inst = G2frame.PatternTree.GetItemPyData(GetPatternTreeItemId(G2frame,
            G2frame.PatternId,'Instrument Parameters'))
        CId = GetPatternTreeItemId(G2frame,G2frame.PatternId,'Comments')
        if CId:
            Comments = G2frame.PatternTree.GetItemPyData(CId)
        else:
            Comments = []
        refList = np.copy(data[1]['RefList'])
        Comments.append(' Merging %d reflections from %s'%(len(refList),Name))
        dlg = MergeDialog(G2frame,data)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                Trans,Cent,Laue = dlg.GetSelection()
            else:
                return
        finally:
            dlg.Destroy()
        Super = data[1]['Super']
        refList,badRefs = G2lat.transposeHKLF(Trans,Super,refList)
        if len(badRefs):    #do I want to list badRefs?
            G2frame.ErrorDialog('Failed transformation','Matrix yields fractional hkl indices')
            return
        Comments.append(" Transformation M*H = H' applied; M=")
        Comments.append(str(Trans))
        refList = G2lat.LaueUnique(Laue,refList)
        dlg = wx.ProgressDialog('Build HKL dictonary','',len(refList)+1, 
            style = wx.PD_ELAPSED_TIME|wx.PD_AUTO_HIDE)
        HKLdict = {}
        for ih,hkl in enumerate(refList):
            if str(hkl[:3+Super]) not in HKLdict:
                HKLdict[str(hkl[:3+Super])] = [hkl[:3+Super],[hkl[3+Super:],]]
            else:
                HKLdict[str(hkl[:3+Super])][1].append(hkl[3+Super:])
            dlg.Update(ih)
        dlg.Destroy()
        mergeRef = []
        dlg = wx.ProgressDialog('Processing merge','',len(HKLdict)+1, 
            style = wx.PD_ELAPSED_TIME|wx.PD_AUTO_HIDE)
        sumDf = 0.
        sumFo = 0.
        for ih,hkl in enumerate(HKLdict):
            HKL = HKLdict[hkl]
            newHKL = list(HKL[0])+list(HKL[1][0])
            if len(HKL[1]) > 1:
                fos = np.array(HKL[1])
                wFo = 1/fos[:,3]**2
                Fo = np.average(fos[:,2],weights=wFo)
                std = np.std(fos[:,2])
                sig = np.sqrt(np.mean(fos[:,3])**2+std**2)
                sumFo += np.sum(fos[:,2])
                sumDf += np.sum(np.abs(fos[:,2]-Fo))
                dlg.Update(ih)
                newHKL[5+Super] = Fo
                newHKL[6+Super] = sig
                newHKL[8+Super] = Fo
            if newHKL[5+Super] > 0.:
                mergeRef.append(list(newHKL)) 
        dlg.Destroy()
        if Super:
            mergeRef = G2mth.sortArray(G2mth.sortArray(G2mth.sortArray(G2mth.sortArray(mergeRef,3),2),1),0)
        else:
            mergeRef = G2mth.sortArray(G2mth.sortArray(G2mth.sortArray(mergeRef,2),1),0)
        mergeRef = np.array(mergeRef)
        if sumFo:
            mtext = ' merge R = %6.2f%s for %d reflections in %s'%(100.*sumDf/sumFo,'%',mergeRef.shape[0],Laue)
            print mtext
            Comments.append(mtext)
        else:
            print 'nothing to merge for %s reflections'%(mergeRef.shape[0])
        HKLFlist = []
        newName = Name+' '+Laue
        if G2frame.PatternTree.GetCount():
            item, cookie = G2frame.PatternTree.GetFirstChild(G2frame.root)
            while item:
                name = G2frame.PatternTree.GetItemText(item)
                if name.startswith('HKLF ') and name not in HKLFlist:
                    HKLFlist.append(name)
                item, cookie = G2frame.PatternTree.GetNextChild(G2frame.root, cookie)
        newName = G2obj.MakeUniqueLabel(newName,HKLFlist)
        newData = copy.deepcopy(data)
        newData[0]['ranId'] = ran.randint(0,sys.maxint)
        newData[1]['RefList'] = mergeRef
        Id = G2frame.PatternTree.AppendItem(parent=G2frame.root,text=newName)
        G2frame.PatternTree.SetItemPyData(
            G2frame.PatternTree.AppendItem(Id,text='Comments'),Comments)
        G2frame.PatternTree.SetItemPyData(Id,newData)
        G2frame.PatternTree.SetItemPyData(
            G2frame.PatternTree.AppendItem(Id,text='Instrument Parameters'),Inst)
        G2frame.PatternTree.SetItemPyData(
            G2frame.PatternTree.AppendItem(Id,text='Reflection List'),{})  #dummy entry for GUI use
                   
    def OnErrorAnalysis(event):
        G2plt.PlotDeltSig(G2frame,kind)
        
#    def OnCompression(event):
#        data[0] = int(comp.GetValue())
        
    def onCopyPlotCtrls(event):
        '''Respond to menu item to copy multiple sections from a histogram.
        Need this here to pass on the G2frame object. 
        '''
        G2pdG.CopyPlotCtrls(G2frame)

    def onCopySelectedItems(event):
        '''Respond to menu item to copy multiple sections from a histogram.
        Need this here to pass on the G2frame object. 
        '''
        G2pdG.CopySelectedHistItems(G2frame)
           
    data = G2frame.PatternTree.GetItemPyData(item)
#patches
    if not data:
        return
    if 'wtFactor' not in data[0]:
        data[0] = {'wtFactor':1.0}
#    if kind == 'PWDR' and 'Compression' not in data[0]:
#        data[0]['Compression'] = 1
    #if isinstance(data[1],list) and kind == 'HKLF':
    if 'list' in str(type(data[1])) and kind == 'HKLF':
        RefData = {'RefList':[],'FF':[]}
        for ref in data[1]:
            RefData['RefList'].append(ref[:11]+[ref[13],])
            RefData['FF'].append(ref[14])
        data[1] = RefData
        G2frame.PatternTree.SetItemPyData(item,data)
#end patches
    if G2frame.dataDisplay:
        G2frame.dataDisplay.Destroy()
    if kind in ['PWDR','SASD','REFD']:
        SetDataMenuBar(G2frame,G2frame.dataFrame.PWDRMenu)
        G2frame.dataFrame.Bind(wx.EVT_MENU, OnErrorAnalysis, id=wxID_PWDANALYSIS)
        G2frame.dataFrame.Bind(wx.EVT_MENU, onCopySelectedItems, id=wxID_PWDCOPY)
        G2frame.dataFrame.Bind(wx.EVT_MENU, onCopyPlotCtrls, id=wxID_PLOTCTRLCOPY)
    elif kind in ['HKLF',]:
        SetDataMenuBar(G2frame,G2frame.dataFrame.HKLFMenu)
        G2frame.dataFrame.Bind(wx.EVT_MENU, OnErrorAnalysis, id=wxID_PWDANALYSIS)
        G2frame.dataFrame.Bind(wx.EVT_MENU, OnMergeHKL, id=wxID_MERGEHKL)
        G2frame.dataFrame.Bind(wx.EVT_MENU, OnPlot3DHKL, id=wxID_PWD3DHKLPLOT)
        G2frame.dataFrame.Bind(wx.EVT_MENU, OnPlotAll3DHKL, id=wxID_3DALLHKLPLOT)
#        G2frame.dataFrame.Bind(wx.EVT_MENU, onCopySelectedItems, id=wxID_PWDCOPY)
    G2frame.dataDisplay = wx.Panel(G2frame.dataFrame)
    
    mainSizer = wx.BoxSizer(wx.VERTICAL)
    mainSizer.Add((5,5),)
    wtSizer = wx.BoxSizer(wx.HORIZONTAL)
    wtSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,' Weight factor: '),0,WACV)
    wtval = G2G.ValidatedTxtCtrl(G2frame.dataDisplay,data[0],'wtFactor',nDig=(10,3),min=1.e-9)
    wtSizer.Add(wtval,0,WACV)
#    if kind == 'PWDR':         #possible future compression feature; NB above patch as well
#        wtSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,' Compression factor: '),0,WACV)
#        choice = ['1','2','3','4','5','6']
#        comp = wx.ComboBox(parent=G2frame.dataDisplay,choices=choice,
#            style=wx.CB_READONLY|wx.CB_DROPDOWN)
#        comp.SetValue(str(data[0]['Compression']))
#        comp.Bind(wx.EVT_COMBOBOX, OnCompression)
#        wtSizer.Add(comp,0,WACV)
    mainSizer.Add(wtSizer)
    if data[0].get('Dummy'):
        simSizer = wx.BoxSizer(wx.HORIZONTAL)
        Tmin = min(data[1][0])
        Tmax = max(data[1][0])
        num = len(data[1][0])
        step = (Tmax - Tmin)/(num-1)
        t = u'2\u03b8' # 2theta
        lbl =  u'Simulation range: {:.2f} to {:.2f} {:s}\nwith {:.4f} steps ({:d} points)'
        lbl += u'\n(Edit range resets observed intensities).'
        lbl = lbl.format(Tmin,Tmax,t,step,num)
        simSizer.Add(wx.StaticText(G2frame.dataDisplay,wx.ID_ANY,lbl),
                    0,WACV)
        but = wx.Button(G2frame.dataDisplay,wx.ID_ANY,"Edit range")
        but.Bind(wx.EVT_BUTTON,onEditSimRange)
        simSizer.Add(but,0,WACV)
        mainSizer.Add(simSizer)
    if 'Nobs' in data[0]:
        mainSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,
            ' Data residual wR: %.3f%% on %d observations'%(data[0]['wR'],data[0]['Nobs'])))
        if kind == 'PWDR':
            mainSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,
                ' Durbin-Watson statistic: %.3f'%(data[0].get('Durbin-Watson',0.))))
        for value in data[0]:
            if 'Nref' in value:
                pfx = value.split('Nref')[0]
                name = data[0].get(pfx.split(':')[0]+'::Name','?')
                if 'SS' in value:
                    mainSizer.Add((5,5),)
                    mainSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,' For incommensurate phase '+name+':'))
                    for m,(Rf2,Rf,Nobs) in enumerate(zip(data[0][pfx+'Rf^2'],data[0][pfx+'Rf'],data[0][value])):
                        mainSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,
                            u' m = +/- %d: RF\u00b2: %.3f%%, RF: %.3f%% on %d reflections  '% \
                            (m,Rf2,Rf,Nobs)))
                else:
                    mainSizer.Add((5,5),)
                    mainSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,' For phase '+name+':'))
                    mainSizer.Add(wx.StaticText(G2frame.dataDisplay,-1,
                        u' Unweighted phase residuals RF\u00b2: %.3f%%, RF: %.3f%% on %d reflections  '% \
                        (data[0][pfx+'Rf^2'],data[0][pfx+'Rf'],data[0][value])))
                    
    mainSizer.Add((5,5),)
    mainSizer.Layout()    
    G2frame.dataDisplay.SetSizer(mainSizer)
    Size = mainSizer.Fit(G2frame.dataFrame)
    Size[1] += 10
    G2frame.dataFrame.setSizePosLeft(Size)
    G2frame.PatternTree.SetItemPyData(item,data)
    G2frame.PatternId = item
    if kind in ['PWDR','SASD','REFD',]:
        NewPlot = True
        if 'xylim' in dir(G2frame):
            NewPlot = False
        G2plt.PlotPatterns(G2frame,plotType=kind,newPlot=NewPlot)
    elif kind == 'HKLF':
        Name = G2frame.PatternTree.GetItemText(item)
        phaseName = G2pdG.IsHistogramInAnyPhase(G2frame,Name)
        if phaseName:
            pId = GetPatternTreeItemId(G2frame,G2frame.root,'Phases')
            phaseId =  GetPatternTreeItemId(G2frame,pId,phaseName)
            General = G2frame.PatternTree.GetItemPyData(phaseId)['General']
            Super = General.get('Super',0)
            SuperVec = General.get('SuperVec',[])
        else:
            Super = 0
            SuperVec = []       
        refList = data[1]['RefList']
#        GSASIIpath.IPyBreak()
        FoMax = np.max(refList.T[5+data[1].get('Super',0)])
        page = G2frame.G2plotNB.nb.GetSelection()
        tab = ''
        if page >= 0:
            tab = G2frame.G2plotNB.nb.GetPageText(page)
        if '3D' in tab:
            Page = G2frame.G2plotNB.nb.GetPage(page)
            controls = Page.controls
            G2plt.Plot3DSngl(G2frame,newPlot=False,Data=controls,hklRef=refList,Title=phaseName)
        else:
            controls = {'Type' : 'Fo','ifFc' : True,     
                'HKLmax' : [int(np.max(refList.T[0])),int(np.max(refList.T[1])),int(np.max(refList.T[2]))],
                'HKLmin' : [int(np.min(refList.T[0])),int(np.min(refList.T[1])),int(np.min(refList.T[2]))],
                'FoMax' : FoMax,'Zone' : '001','Layer' : 0,'Scale' : 1.0,'Super':Super,'SuperVec':SuperVec}
            G2plt.PlotSngl(G2frame,newPlot=True,Data=controls,hklRef=refList)
                 
################################################################################
#####  Pattern tree routines
################################################################################           
       
def GetPatternTreeDataNames(G2frame,dataTypes):
    '''Finds all items in tree that match a 4 character prefix
    
    :param wx.Frame G2frame: Data tree frame object
    :param list dataTypes: Contains one or more data tree item types to be matched
      such as ['IMG '] or ['PWDR','HKLF']
    :returns: a list of tree item names for the matching items  
    '''
    names = []
    item, cookie = G2frame.PatternTree.GetFirstChild(G2frame.root)        
    while item:
        name = G2frame.PatternTree.GetItemText(item)
        if name[:4] in dataTypes:
            names.append(name)
        item, cookie = G2frame.PatternTree.GetNextChild(G2frame.root, cookie)
    return names
                          
def GetPatternTreeItemId(G2frame, parentId, itemText):
    '''Find the tree item that matches the text in itemText starting with parentId

    :param wx.Frame G2frame: Data tree frame object
    :param wx.TreeItemId parentId: tree item to start search with
    :param str itemText: text for tree item
    '''
    item, cookie = G2frame.PatternTree.GetFirstChild(parentId)
    while item:
        if G2frame.PatternTree.GetItemText(item) == itemText:
            return item
        item, cookie = G2frame.PatternTree.GetNextChild(parentId, cookie)
    return 0                

def SelectDataTreeItem(G2frame,item):
    '''Called from :meth:`GSASII.GSASII.OnDataTreeSelChanged` when a item is selected on the tree.
    Also called from GSASII.OnPatternTreeEndDrag, OnAddPhase -- might be better to select item, triggering
    the the bind to SelectDataTreeItem

    Also Called in GSASIIphsGUI.UpdatePhaseData by OnTransform callback. 
    '''
    if G2frame.PickIdText == G2frame.GetTreeItemsList(item): # don't redo the current data tree item 
        return
    oldPage = None # will be set later if already on a Phase item
    if G2frame.dataFrame:
        # save or finish processing of outstanding events
        for grid in G2frame.dataFrame.currentGrids:  # complete any open wx.Grid edits
            #if GSASIIpath.GetConfigValue('debug'): print 'Testing grid edit in',grid
            try: 
                if grid.IsCellEditControlEnabled(): # complete any grid edits in progress
                    if GSASIIpath.GetConfigValue('debug'): print 'Completing grid edit in',grid
                    grid.HideCellEditControl()
                    grid.DisableCellEditControl()
            except:
                pass
        if G2frame.dataFrame.GetLabel() == 'Comments': # save any recently entered comments 
            try:
                data = [G2frame.dataDisplay.GetValue()]
                G2frame.dataDisplay.Clear() 
                Id = GetPatternTreeItemId(G2frame,G2frame.root, 'Comments')
                if Id: G2frame.PatternTree.SetItemPyData(Id,data)
            except:     #clumsy but avoids dead window problem when opening another project
                pass
        elif G2frame.dataFrame.GetLabel() == 'Notebook': # save any recent notebook entries
            try:
                data = [G2frame.dataDisplay.GetValue()]
                G2frame.dataDisplay.Clear() 
                Id = GetPatternTreeItemId(G2frame,G2frame.root, 'Notebook')
                if Id: G2frame.PatternTree.SetItemPyData(Id,data)
            except:     #clumsy but avoids dead window problem when opening another project
                pass
        elif 'Phase Data for' in G2frame.dataFrame.GetLabel():
            if G2frame.dataDisplay: 
                oldPage = G2frame.dataDisplay.GetSelection()
        G2frame.dataFrame.Clear()
        G2frame.dataFrame.SetLabel('')
    else:
        #create the frame for the data item window
        G2frame.dataFrame = DataFrame(parent=G2frame.mainPanel,frame=G2frame)
        G2frame.dataFrame.PhaseUserSize = None
        
    SetDataMenuBar(G2frame)
    G2frame.dataFrame.Raise()            
    G2frame.dataFrame.currentGrids = [] # this will contain pointers to a grid placed in the frame
    G2frame.PickId = item
    G2frame.PickIdText = None
    parentID = G2frame.root
    #for i in G2frame.ExportPattern: i.Enable(False)
    defWid = [250,150]
    if item == G2frame.root:
        G2frame.dataFrame.helpKey = "Data tree"
        G2frame.dataFrame.setSizePosLeft(defWid)
        wx.TextCtrl(parent=G2frame.dataFrame,size=G2frame.dataFrame.GetClientSize(),
                    value='Select an item from the tree to see/edit parameters')        
        return
    else:
        parentID = G2frame.PatternTree.GetItemParent(item)
        # save name of calling tree item for help. N.B. may want to override this later
        prfx = G2frame.PatternTree.GetItemText(item).split()[0]
        prfx1 = G2frame.PatternTree.GetItemText(parentID).split()[0]
        if prfx in ('IMG','PKS','PWDR','SASD','HKLF','PDF','refd',):
            G2frame.dataFrame.helpKey = prfx
        elif prfx1 in ('IMG','PKS','PWDR','SASD','HKLF','PDF','REFD',):
            suffix = G2frame.PatternTree.GetItemText(item)
            suffix1 = suffix.split()[0]
            if '(Q)' in suffix1 or '(R)' in suffix1: suffix = suffix1
            G2frame.dataFrame.helpKey = prfx1 + '_' + suffix
        else:
            G2frame.dataFrame.helpKey = G2frame.PatternTree.GetItemText(item) # save name of calling tree item for help
    if G2frame.PatternTree.GetItemParent(item) == G2frame.root:
        G2frame.PatternId = 0
        if G2frame.PatternTree.GetItemText(item) == 'Notebook':
            SetDataMenuBar(G2frame,G2frame.dataFrame.DataNotebookMenu)
            #for i in G2frame.ExportPattern: i.Enable(False)
            data = G2frame.PatternTree.GetItemPyData(item)
            UpdateNotebook(G2frame,data)
        elif G2frame.PatternTree.GetItemText(item) == 'Controls':
            #for i in G2frame.ExportPattern: i.Enable(False)
            data = G2frame.PatternTree.GetItemPyData(item)
            if not data:           #fill in defaults
                data = copy.copy(G2obj.DefaultControls)    #least squares controls
                G2frame.PatternTree.SetItemPyData(item,data)                             
            for i in G2frame.Refine: i.Enable(True)
            G2frame.EnableSeqRefineMenu()
            UpdateControls(G2frame,data)
        elif G2frame.PatternTree.GetItemText(item).startswith('Sequential '):
            G2frame.dataFrame.helpKey = 'Sequential'  # for now all sequential refinements are documented in one place
            data = G2frame.PatternTree.GetItemPyData(item)
            UpdateSeqResults(G2frame,data)
        elif G2frame.PatternTree.GetItemText(item) == 'Covariance':
            data = G2frame.PatternTree.GetItemPyData(item)
            G2frame.dataFrame.setSizePosLeft(defWid)
            text = ''
            if 'Rvals' in data:
                Nvars = len(data['varyList'])
                Rvals = data['Rvals']
                text = '\nFinal residuals: \nwR = %.3f%% \nchi**2 = %.1f \nGOF = %.2f'%(Rvals['Rwp'],Rvals['chisq'],Rvals['GOF'])
                text += '\nNobs = %d \nNvals = %d'%(Rvals['Nobs'],Nvars)
                if 'lamMax' in Rvals:
                    text += '\nlog10 MaxLambda = %.1f'%(np.log10(Rvals['lamMax']))
            wx.TextCtrl(parent=G2frame.dataFrame,size=G2frame.dataFrame.GetClientSize(),
                value='See plot window for covariance display'+text,style=wx.TE_MULTILINE)
            G2plt.PlotCovariance(G2frame,data)
        elif G2frame.PatternTree.GetItemText(item) == 'Constraints':
            data = G2frame.PatternTree.GetItemPyData(item)
            G2cnstG.UpdateConstraints(G2frame,data)
        elif G2frame.PatternTree.GetItemText(item) == 'Rigid bodies':
            data = G2frame.PatternTree.GetItemPyData(item)
            G2cnstG.UpdateRigidBodies(G2frame,data)
        elif G2frame.PatternTree.GetItemText(item) == 'Restraints':
            data = G2frame.PatternTree.GetItemPyData(item)
            Phases = G2frame.GetPhaseData()
            phaseName = ''
            if Phases:
                phaseName = Phases.keys()[0]
            G2frame.dataFrame.setSizePosLeft(defWid)
            G2restG.UpdateRestraints(G2frame,data,Phases,phaseName)
        elif G2frame.PatternTree.GetItemText(item).startswith('IMG '):
            G2frame.Image = item
            G2frame.dataFrame.SetTitle('Image Data')
            data = G2frame.PatternTree.GetItemPyData(GetPatternTreeItemId(
                G2frame,item,'Image Controls'))
            G2imG.UpdateImageData(G2frame,data)
            G2plt.PlotImage(G2frame,newPlot=True)
        elif G2frame.PatternTree.GetItemText(item).startswith('PKS '):
            G2plt.PlotPowderLines(G2frame)
        elif G2frame.PatternTree.GetItemText(item).startswith('PWDR '):
            G2frame.PatternId = item
            #for i in G2frame.ExportPattern: i.Enable(True)
            if G2frame.EnablePlot:
                UpdatePWHKPlot(G2frame,'PWDR',item)
        elif G2frame.PatternTree.GetItemText(item).startswith('SASD '):
            G2frame.PatternId = item
            #for i in G2frame.ExportPattern: i.Enable(True)
            if G2frame.EnablePlot:
                UpdatePWHKPlot(G2frame,'SASD',item)
        elif G2frame.PatternTree.GetItemText(item).startswith('REFD '):
            G2frame.PatternId = item
            #for i in G2frame.ExportPattern: i.Enable(True)
            if G2frame.EnablePlot:
                UpdatePWHKPlot(G2frame,'REFD',item)
        elif G2frame.PatternTree.GetItemText(item).startswith('HKLF '):
            G2frame.Sngl = True
            UpdatePWHKPlot(G2frame,'HKLF',item)
        elif G2frame.PatternTree.GetItemText(item).startswith('PDF '):
            G2frame.PatternId = item
            for i in G2frame.ExportPDF: i.Enable(True) # this should be done on .gpx load; is done on OnMakePDFs (GSASII.py)
            data = G2frame.PatternTree.GetItemPyData(GetPatternTreeItemId(G2frame,item,'PDF Controls'))
            G2pdG.UpdatePDFGrid(G2frame,data)
            if len(data['G(R)']):
                G2plt.PlotISFG(G2frame,data,plotType='G(R)')
        elif G2frame.PatternTree.GetItemText(item) == 'Phases':
            G2frame.dataFrame.setSizePosLeft(defWid)
            wx.TextCtrl(parent=G2frame.dataFrame,size=G2frame.dataFrame.GetClientSize(),
                value='Select one phase to see its parameters')            
    elif G2frame.PatternTree.GetItemText(item) == 'PDF Peaks':
        G2frame.PatternId = G2frame.PatternTree.GetItemParent(item)
        peaks = G2frame.PatternTree.GetItemPyData(GetPatternTreeItemId(G2frame,G2frame.PatternId,'PDF Peaks'))
        data = G2frame.PatternTree.GetItemPyData(GetPatternTreeItemId(G2frame,G2frame.PatternId,'PDF Controls'))
        G2pdG.UpdatePDFPeaks(G2frame,peaks,data)
        if len(data['G(R)']):
            G2plt.PlotISFG(G2frame,data,plotType='G(R)',newPlot=True,peaks=peaks)            
    elif G2frame.PatternTree.GetItemText(item) == 'PDF Controls':
        for i in G2frame.ExportPDF: i.Enable(True) # this should be done on .gpx load; is done on OnMakePDFs (GSASII.py)
        G2frame.dataFrame.helpKey = G2frame.PatternTree.GetItemText(item) # special treatment to avoid PDF_PDF Controls
        G2frame.PatternId = G2frame.PatternTree.GetItemParent(item)
        data = G2frame.PatternTree.GetItemPyData(item)
        G2pdG.UpdatePDFGrid(G2frame,data)
        if len(data['G(R)']):
            if 'I(Q)' in data:  G2plt.PlotISFG(G2frame,data,plotType='I(Q)')
            if 'S(Q)' in data:  G2plt.PlotISFG(G2frame,data,plotType='S(Q)')
            if 'F(Q)' in data:  G2plt.PlotISFG(G2frame,data,plotType='F(Q)')
            G2plt.PlotISFG(G2frame,data,plotType='G(R)')
    elif G2frame.PatternTree.GetItemText(parentID) == 'Phases':
        data = G2frame.PatternTree.GetItemPyData(item)
        G2phG.UpdatePhaseData(G2frame,item,data,oldPage)
    elif G2frame.PatternTree.GetItemText(item) == 'Comments':
        SetDataMenuBar(G2frame,G2frame.dataFrame.DataCommentsMenu)
        G2frame.PatternId = G2frame.PatternTree.GetItemParent(item)
        data = G2frame.PatternTree.GetItemPyData(item)
        UpdateComments(G2frame,data)
    elif G2frame.PatternTree.GetItemText(item) == 'Image Controls':
        G2frame.dataFrame.SetTitle('Image Controls')
        G2frame.Image = G2frame.PatternTree.GetItemParent(item)
        masks = G2frame.PatternTree.GetItemPyData(
            GetPatternTreeItemId(G2frame,G2frame.Image, 'Masks'))
        data = G2frame.PatternTree.GetItemPyData(item)
        G2frame.ImageZ = G2imG.GetImageZ(G2frame,data)
        G2imG.UpdateImageControls(G2frame,data,masks)
        G2plt.PlotImage(G2frame,newPlot=False)
    elif G2frame.PatternTree.GetItemText(item) == 'Masks':
        G2frame.dataFrame.SetTitle('Masks')
        G2frame.Image = G2frame.PatternTree.GetItemParent(item)
        masks = G2frame.PatternTree.GetItemPyData(item)
        data = G2frame.PatternTree.GetItemPyData(
            GetPatternTreeItemId(G2frame,G2frame.Image, 'Image Controls'))
        G2frame.ImageZ = G2imG.GetImageZ(G2frame,data)
        G2imG.UpdateMasks(G2frame,masks)
        G2plt.PlotImage(G2frame,newPlot=False)
    elif G2frame.PatternTree.GetItemText(item) == 'Stress/Strain':
        G2frame.dataFrame.SetTitle('Stress/Strain')
        G2frame.Image = G2frame.PatternTree.GetItemParent(item)
        data = G2frame.PatternTree.GetItemPyData(
            GetPatternTreeItemId(G2frame,G2frame.Image, 'Image Controls'))
        G2frame.ImageZ = G2imG.GetImageZ(G2frame,data,newRange=False)
        strsta = G2frame.PatternTree.GetItemPyData(item)
        G2plt.PlotStrain(G2frame,strsta,newPlot=True)
        G2plt.PlotImage(G2frame,newPlot=False)
        G2imG.UpdateStressStrain(G2frame,strsta)
    elif G2frame.PatternTree.GetItemText(item) == 'Peak List':
        G2frame.PatternId = G2frame.PatternTree.GetItemParent(item)
        for i in G2frame.ExportPeakList: i.Enable(True)
        data = G2frame.PatternTree.GetItemPyData(item)
#patch
        if 'list' in str(type(data)):
            data = {'peaks':data,'sigDict':{}}
            G2frame.PatternTree.SetItemPyData(item,data)
#end patch
        G2pdG.UpdatePeakGrid(G2frame,data)
        G2plt.PlotPatterns(G2frame)
    elif G2frame.PatternTree.GetItemText(item) == 'Background':
        G2frame.PatternId = G2frame.PatternTree.GetItemParent(item)
        data = G2frame.PatternTree.GetItemPyData(item)
        G2pdG.UpdateBackground(G2frame,data)
        G2plt.PlotPatterns(G2frame)
    elif G2frame.PatternTree.GetItemText(item) == 'Limits':
        G2frame.PatternId = G2frame.PatternTree.GetItemParent(item)
        datatype = G2frame.PatternTree.GetItemText(G2frame.PatternId)[:4]
        data = G2frame.PatternTree.GetItemPyData(item)
        G2pdG.UpdateLimitsGrid(G2frame,data,datatype)
        G2plt.PlotPatterns(G2frame,plotType=datatype)
    elif G2frame.PatternTree.GetItemText(item) == 'Instrument Parameters':
        G2frame.PatternId = G2frame.PatternTree.GetItemParent(item)
        data = G2frame.PatternTree.GetItemPyData(item)[0]
        G2pdG.UpdateInstrumentGrid(G2frame,data)
        if 'P' in data['Type'][0]:          #powder data only
            G2plt.PlotPeakWidths(G2frame)
    elif G2frame.PatternTree.GetItemText(item) == 'Models':
        G2frame.PatternId = G2frame.PatternTree.GetItemParent(item)
        data = G2frame.PatternTree.GetItemPyData(item)
        if prfx1 == 'SASD':
            G2pdG.UpdateModelsGrid(G2frame,data)
        elif prfx1 == 'REFD':
            G2pdG.UpdateREFDModelsGrid(G2frame,data)
        G2plt.PlotPatterns(G2frame,plotType=prfx1)
        if prfx1 == 'SASD' and len(data['Size']['Distribution']):
            G2plt.PlotSASDSizeDist(G2frame)
    elif G2frame.PatternTree.GetItemText(item) == 'Substances':
        G2frame.PatternId = G2frame.PatternTree.GetItemParent(item)
        data = G2frame.PatternTree.GetItemPyData(item)
        G2pdG.UpdateSubstanceGrid(G2frame,data)
    elif G2frame.PatternTree.GetItemText(item) == 'Sample Parameters':
        G2frame.PatternId = G2frame.PatternTree.GetItemParent(item)
        data = G2frame.PatternTree.GetItemPyData(item)
        datatype = G2frame.PatternTree.GetItemPyData(G2frame.PatternId)[2][:4]

        if 'Temperature' not in data:           #temp fix for old gpx files
            data = {'Scale':[1.0,True],'Type':'Debye-Scherrer','Absorption':[0.0,False],'DisplaceX':[0.0,False],
                'DisplaceY':[0.0,False],'Diffuse':[],'Temperature':300.,'Pressure':1.0,
                    'FreePrm1':0.,'FreePrm2':0.,'FreePrm3':0.,
                    'Gonio. radius':200.0}
            G2frame.PatternTree.SetItemPyData(item,data)
    
        G2pdG.UpdateSampleGrid(G2frame,data)
        G2plt.PlotPatterns(G2frame,plotType=datatype)
    elif G2frame.PatternTree.GetItemText(item) == 'Index Peak List':
        G2frame.PatternId = G2frame.PatternTree.GetItemParent(item)
        for i in G2frame.ExportPeakList: i.Enable(True)
        data = G2frame.PatternTree.GetItemPyData(item)
#patch
        if len(data) != 2:
            data = [data,[]]
            G2frame.PatternTree.SetItemPyData(item,data)
#end patch
        G2pdG.UpdateIndexPeaksGrid(G2frame,data)
        if 'PKS' in G2frame.PatternTree.GetItemText(G2frame.PatternId):
            G2plt.PlotPowderLines(G2frame)
        else:
            G2plt.PlotPatterns(G2frame)
    elif G2frame.PatternTree.GetItemText(item) == 'Unit Cells List':
        G2frame.PatternId = G2frame.PatternTree.GetItemParent(item)
        data = G2frame.PatternTree.GetItemPyData(item)
        if not data:
            data.append([0,0.0,4,25.0,0,'P1',1,1,1,90,90,90]) #zero error flag, zero value, max Nc/No, start volume
            data.append([0,0,0,0,0,0,0,0,0,0,0,0,0,0])      #Bravais lattice flags
            data.append([])                                 #empty cell list
            data.append([])                                 #empty dmin
            data.append({})                                 #empty superlattice stuff
            G2frame.PatternTree.SetItemPyData(item,data)                             
#patch
        if len(data) < 5:
            data.append({'Use':False,'ModVec':[0,0,0.1],'maxH':1,'ssSymb':''})                                 #empty superlattice stuff
            G2frame.PatternTree.SetItemPyData(item,data)  
#end patch
        G2pdG.UpdateUnitCellsGrid(G2frame,data)
        if 'PKS' in G2frame.PatternTree.GetItemText(G2frame.PatternId):
            G2plt.PlotPowderLines(G2frame)
        else:
            G2plt.PlotPatterns(G2frame)
    elif G2frame.PatternTree.GetItemText(item) == 'Reflection Lists':   #powder reflections
        G2frame.PatternId = G2frame.PatternTree.GetItemParent(item)
        data = G2frame.PatternTree.GetItemPyData(item)
        G2frame.RefList = ''
        if len(data):
            G2frame.RefList = data.keys()[0]
        G2pdG.UpdateReflectionGrid(G2frame,data)
        G2plt.PlotPatterns(G2frame)
    elif G2frame.PatternTree.GetItemText(item) == 'Reflection List':    #HKLF reflections
        G2frame.PatternId = G2frame.PatternTree.GetItemParent(item)
        name = G2frame.PatternTree.GetItemText(G2frame.PatternId)
        data = G2frame.PatternTree.GetItemPyData(G2frame.PatternId)
        G2pdG.UpdateReflectionGrid(G2frame,data,HKLF=True,Name=name)

    if G2frame.PickId:
        G2frame.PickIdText = G2frame.GetTreeItemsList(G2frame.PickId)
    G2frame.dataFrame.Raise()

def SetDataMenuBar(G2frame,menu=None):
    '''Set the menu for the data frame. On the Mac put this
    menu for the data tree window instead.

    Note that data frame items do not have menus, for these (menu=None)
    display a blank menu or on the Mac display the standard menu for
    the data tree window.
    '''
    if sys.platform == "darwin":
        if menu is None:
            G2frame.SetMenuBar(G2frame.GSASIIMenu)
        else:
            G2frame.SetMenuBar(menu)
    else:
        if menu is None:
            G2frame.dataFrame.SetMenuBar(G2frame.dataFrame.BlankMenu)
        else:
            G2frame.dataFrame.SetMenuBar(menu)

def HowDidIgetHere():
    '''Show a traceback with calls that brought us to the current location.
    Used for debugging.
    '''
    import traceback
    print 70*'*'    
    for i in traceback.format_list(traceback.extract_stack()[:-1]): print(i.strip().rstrip())
    print 70*'*'    
        
