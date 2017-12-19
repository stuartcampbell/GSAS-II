# -*- coding: utf-8 -*-
#GSASIIctrlGUI - Custom GSAS-II GUI controls
########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### SVN repository information ###################
'''
*GSASIIctrlGUI: Custom GUI controls*
---------------------------------------------

A library of GUI controls for reuse throughout GSAS-II

'''
from __future__ import division, print_function
import os
import sys
try:
    import wx
    import wx.grid as wg
    # import wx.wizard as wz
    import wx.aui
    import wx.lib.scrolledpanel as wxscroll
    import wx.html        # could postpone this for quicker startup
    import matplotlib as mpl
except ImportError:
    raise
    # Dumm 'wx' so this file can be imported
    vals = ('TreeCtrl TextCtrl PyValidator Button ComboBox Choice CheckBox'.split() +
            'Dialog ID_ANY OPEN'.split())
    class Placeholder(object):
        def __init__(self, vals):
            for val in vals:
                setattr(self, val, object)
        def __getattr__(self, value):
            if value[0].isupper():
                return object
            return Placeholder([])
    wx = Placeholder(vals)
    wxscroll = Placeholder(['ScrolledPanel'])
    if 'phoenix' in wx.version():
        wg = Placeholder('Grid GridTableBase GridCellEditor'.split())
    else:
        wg = Placeholder('Grid PyGridTableBase PyGridCellEditor'.split())
import time
import copy
import webbrowser     # could postpone this for quicker startup

import GSASIIpath
GSASIIpath.SetVersionNumber("$Revision$")
import GSASIIdataGUI as G2gd
import GSASIIpwdGUI as G2pdG
import GSASIIpy3 as G2py3
import GSASIIlog as log
import GSASIIobj as G2obj

# Define a short names for convenience
WHITE = (255,255,255)
DULL_YELLOW = (230,230,190)
# Don't depend on wx, for scriptable
try:
    VERY_LIGHT_GREY = wx.Colour(235,235,235)
    WACV = wx.ALIGN_CENTER_VERTICAL
except:
    # Don't depend on GUI
    pass

################################################################################
#### Fixed definitions for wx Ids 
################################################################################
def Define_wxId(*args):
    '''routine to create unique global wx Id symbols in this module. 
    '''
    for arg in args:
        if GSASIIpath.GetConfigValue('debug') and not arg.startswith('wxID_'):
            print ('Problem in name'+arg)
        if arg in globals():
            if GSASIIpath.GetConfigValue('debug'): print (arg+'already defined')
            continue
        exec('global '+arg+';'+arg+' = wx.NewId()')

################################################################################
#### Tree Control
################################################################################
class G2TreeCtrl(wx.TreeCtrl):
    '''Create a wrapper around the standard TreeCtrl so we can "wrap"
    various events.
    
    This logs when a tree item is selected (in :meth:`onSelectionChanged`)

    This also wraps lists and dicts pulled out of the tree to track where
    they were retrieved from.
    '''
    #def SelectItem(self,event):
    #    print 'Select Item'
    #    import GSASIIobj as G2obj
    #    G2obj.HowDidIgetHere()
    #    wx.TreeCtrl.SelectItem(self,event)
        
    def __init__(self,parent=None,*args,**kwargs):
        super(self.__class__,self).__init__(parent=parent,*args,**kwargs)
        self.G2frame = parent.GetTopLevelParent()
        self.root = self.AddRoot('Loaded Data: ')
        self.SelectionChanged = None
        self.textlist = None
        log.LogInfo['Tree'] = self

    def _getTreeItemsList(self,item):
        '''Get the full tree hierarchy from a reference to a tree item.
        Note that this effectively hard-codes phase and histogram names in the
        returned list. We may want to make these names relative in the future.
        '''
        textlist = [self.GetItemText(item)]
        parent = self.GetItemParent(item)
        while parent:
            if parent == self.root: break
            textlist.insert(0,self.GetItemText(parent))
            parent = self.GetItemParent(parent)
        return textlist
    
    def GetItemPyData(self,id):
        if 'phoenix' in wx.version():
            return wx.TreeCtrl.GetItemData(self,id)
        else:
            return wx.TreeCtrl.GetItemPyData(self,id)

    def SetItemPyData(self,id,data):
        if 'phoenix' in wx.version():
            return wx.TreeCtrl.SetItemData(self,id,data)
        else:
            return wx.TreeCtrl.SetItemPyData(self,id,data)

    def onSelectionChanged(self,event):
        '''Log each press on a tree item here. 
        '''
        if not self.G2frame.treePanel:
            return
        if self.SelectionChanged:
            textlist = self._getTreeItemsList(event.GetItem())
            if log.LogInfo['Logging'] and event.GetItem() != self.root:
                textlist[0] = self.GetRelativeHistNum(textlist[0])
                if textlist[0] == "Phases" and len(textlist) > 1:
                    textlist[1] = self.GetRelativePhaseNum(textlist[1])
                log.MakeTreeLog(textlist)
            if textlist == self.textlist:
                return      #same as last time - don't get it again
            self.textlist = textlist
            self.SelectionChanged(event)

    def Bind(self,eventtype,handler,*args,**kwargs):
        '''Override the Bind() function so that page change events can be trapped
        '''
        if eventtype == wx.EVT_TREE_SEL_CHANGED:
            self.SelectionChanged = handler
            wx.TreeCtrl.Bind(self,eventtype,self.onSelectionChanged)
            return
        wx.TreeCtrl.Bind(self,eventtype,handler,*args,**kwargs)

    # commented out, disables Logging
    # def GetItemPyData(self,*args,**kwargs):
    #    '''Override the standard method to wrap the contents
    #    so that the source can be logged when changed
    #    '''
    #    data = super(self.__class__,self).GetItemPyData(*args,**kwargs)
    #    textlist = self._getTreeItemsList(args[0])
    #    if type(data) is dict:
    #        return log.dictLogged(data,textlist)
    #    if type(data) is list:
    #        return log.listLogged(data,textlist)
    #    if type(data) is tuple: #N.B. tuples get converted to lists
    #        return log.listLogged(list(data),textlist)
    #    return data

    def GetRelativeHistNum(self,histname):
        '''Returns list with a histogram type and a relative number for that
        histogram, or the original string if not a histogram
        '''
        histtype = histname.split()[0]
        if histtype != histtype.upper(): # histograms (only) have a keyword all in caps
            return histname
        item, cookie = self.GetFirstChild(self.root)
        i = 0
        while item:
            itemtext = self.GetItemText(item)
            if itemtext == histname:
                return histtype,i
            elif itemtext.split()[0] == histtype:
                i += 1
            item, cookie = self.GetNextChild(self.root, cookie)
        else:
            raise Exception("Histogram not found: "+histname)

    def ConvertRelativeHistNum(self,histtype,histnum):
        '''Converts a histogram type and relative histogram number to a
        histogram name in the current project
        '''
        item, cookie = self.GetFirstChild(self.root)
        i = 0
        while item:
            itemtext = self.GetItemText(item)
            if itemtext.split()[0] == histtype:
                if i == histnum: return itemtext
                i += 1
            item, cookie = self.GetNextChild(self.root, cookie)
        else:
            raise Exception("Histogram #'+str(histnum)+' of type "+histtype+' not found')
        
    def GetRelativePhaseNum(self,phasename):
        '''Returns a phase number if the string matches a phase name
        or else returns the original string
        '''
        item, cookie = self.GetFirstChild(self.root)
        while item:
            itemtext = self.GetItemText(item)
            if itemtext == "Phases":
                parent = item
                item, cookie = self.GetFirstChild(parent)
                i = 0
                while item:
                    itemtext = self.GetItemText(item)
                    if itemtext == phasename:
                        return i
                    item, cookie = self.GetNextChild(parent, cookie)
                    i += 1
                else:
                    return phasename # not a phase name
            item, cookie = self.GetNextChild(self.root, cookie)
        else:
            raise Exception("No phases found ")

    def ConvertRelativePhaseNum(self,phasenum):
        '''Converts relative phase number to a phase name in
        the current project
        '''
        item, cookie = self.GetFirstChild(self.root)
        while item:
            itemtext = self.GetItemText(item)
            if itemtext == "Phases":
                parent = item
                item, cookie = self.GetFirstChild(parent)
                i = 0
                while item:
                    if i == phasenum:
                        return self.GetItemText(item)
                    item, cookie = self.GetNextChild(parent, cookie)
                    i += 1
                else:
                    raise Exception("Phase "+str(phasenum)+" not found")
            item, cookie = self.GetNextChild(self.root, cookie)
        else:
            raise Exception("No phases found ")

    def GetImageLoc(self,TreeId):
        '''Get Image data from the Tree. Handles cases where the
        image name is specified, as well as where the image file name is
        a tuple containing the image file and an image number
        '''
        
        size,imagefile = self.GetItemPyData(TreeId)
        if type(imagefile) is tuple or type(imagefile) is list:
            return size,imagefile[0],imagefile[1]
        else:
            return size,imagefile,None

    def UpdateImageLoc(self,TreeId,imagefile):
        '''Saves a new imagefile name in the Tree. Handles cases where the
        image name is specified, as well as where the image file name is
        a tuple containing the image file and an image number
        '''
        
        idata = self.GetItemPyData(TreeId)
        if type(idata[1]) is tuple or type(idata[1]) is list:
            idata[1] = list(idata[1])
            idata[1][0] = [imagefile,idata[1][1]]
        else:
            idata[1]  = imagefile
        
    def SaveExposedItems(self):
        '''Traverse the top level tree items and save names of exposed (expanded) tree items.
        Done before a refinement.
        '''
        self.ExposedItems = []
        item, cookie = self.GetFirstChild(self.root)
        while item:
            name = self.GetItemText(item)
            if self.IsExpanded(item): self.ExposedItems.append(name)
            item, cookie = self.GetNextChild(self.root, cookie)
#        print 'exposed:',self.ExposedItems

    def RestoreExposedItems(self):
        '''Traverse the top level tree items and restore exposed (expanded) tree items
        back to their previous state (done after a reload of the tree after a refinement)
        '''
        item, cookie = self.GetFirstChild(self.root)
        while item:
            name = self.GetItemText(item)
            if name in self.ExposedItems: self.Expand(item)
            item, cookie = self.GetNextChild(self.root, cookie)

################################################################################
#### TextCtrl that stores input as entered with optional validation
################################################################################
class ValidatedTxtCtrl(wx.TextCtrl):
    '''Create a TextCtrl widget that uses a validator to prevent the
    entry of inappropriate characters and changes color to highlight
    when invalid input is supplied. As valid values are typed,
    they are placed into the dict or list where the initial value
    came from. The type of the initial value must be int,
    float or str or None (see :obj:`key` and :obj:`typeHint`);
    this type (or the one in :obj:`typeHint`) is preserved.

    Float values can be entered in the TextCtrl as numbers or also
    as algebraic expressions using operators + - / \* () and \*\*,
    in addition pi, sind(), cosd(), tand(), and sqrt() can be used,
    as well as appreviations s, sin, c, cos, t, tan and sq. 

    :param wx.Panel parent: name of panel or frame that will be
      the parent to the TextCtrl. Can be None.

    :param dict/list loc: the dict or list with the initial value to be
      placed in the TextCtrl. 

    :param int/str key: the dict key or the list index for the value to be
      edited by the TextCtrl. The ``loc[key]`` element must exist, but may
      have value None. If None, the type for the element is taken from
      :obj:`typeHint` and the value for the control is set initially
      blank (and thus invalid.) This is a way to specify a field without a
      default value: a user must set a valid value.
       
      If the value is not None, it must have a base
      type of int, float, str or unicode; the TextCrtl will be initialized
      from this value.
      
    :param list nDig: number of digits, places and optionally the format 
       ([nDig,nPlc,fmt]) after decimal to use for display of float. The format 
       is either 'f' (default) or 'g'. Alternately, None can be specified which 
       causes numbers to be displayed with approximately 5 significant figures
       (Default=None).

    :param bool notBlank: if True (default) blank values are invalid
      for str inputs.
      
    :param number min: minimum allowed valid value. If None (default) the
      lower limit is unbounded.
      NB: test in NumberValidator is val >= min not val > min

    :param number max: maximum allowed valid value. If None (default) the
      upper limit is unbounded
      NB: test in NumberValidator is val <= max not val < max
      
    :param list exclLim: if True exclude min/max value ([exclMin,exclMax]); 
      (Default=[False,False]) 

    :param function OKcontrol: specifies a function or method that will be
      called when the input is validated. The called function is supplied
      with one argument which is False if the TextCtrl contains an invalid
      value and True if the value is valid.
      Note that this function should check all values
      in the dialog when True, since other entries might be invalid.
      The default for this is None, which indicates no function should
      be called.

    :param function OnLeave: specifies a function or method that will be
      called when the focus for the control is lost.
      The called function is supplied with (at present) three keyword arguments:

      * invalid: (*bool*) True if the value for the TextCtrl is invalid
      * value:   (*int/float/str*)  the value contained in the TextCtrl
      * tc:      (*wx.TextCtrl*)  the TextCtrl object

      The number of keyword arguments may be increased in the future should needs arise,
      so it is best to code these functions with a \*\*kwargs argument so they will
      continue to run without errors

      The default for OnLeave is None, which indicates no function should
      be called.

    :param type typeHint: the value of typeHint is overrides the initial value
      for the dict/list element ``loc[key]``, if set to 
      int or float, which specifies the type for input to the TextCtrl.
      Defaults as None, which is ignored.

    :param bool CIFinput: for str input, indicates that only printable
      ASCII characters may be entered into the TextCtrl. Forces output
      to be ASCII rather than Unicode. For float and int input, allows
      use of a single '?' or '.' character as valid input.

    :param dict OnLeaveArgs: a dict with keyword args that are passed to
      the :attr:`OnLeave` function. Defaults to ``{}``

    :param bool ASCIIonly: if set as True will remove unicode characters from
      strings

    :param (other): other optional keyword parameters for the
      wx.TextCtrl widget such as size or style may be specified.
    '''
    def __init__(self,parent,loc,key,nDig=None,notBlank=True,min=None,max=None,
        OKcontrol=None,OnLeave=None,typeHint=None,CIFinput=False,exclLim=[False,False],
        OnLeaveArgs={}, ASCIIonly=False, **kw):
        # save passed values needed outside __init__
        self.result = loc
        self.key = key
        self.nDig = nDig
        self.OKcontrol=OKcontrol
        self.OnLeave = OnLeave
        self.OnLeaveArgs = OnLeaveArgs
        self.CIFinput = CIFinput
        self.notBlank = notBlank
        self.ASCIIonly = ASCIIonly
        self.type = str
        # initialization
        self.invalid = False   # indicates if the control has invalid contents
        self.evaluated = False # set to True when the validator recognizes an expression
        val = loc[key]
        if 'style' in kw: # add a "Process Enter" to style
            kw['style'] += kw['style'] | wx.TE_PROCESS_ENTER
        else:
            kw['style'] = wx.TE_PROCESS_ENTER
        if 'int' in str(type(val)) or typeHint is int:
            self.type = int
            wx.TextCtrl.__init__(self,parent,wx.ID_ANY,
                validator=NumberValidator(int,result=loc,key=key,min=min,max=max,
                    exclLim=exclLim,OKcontrol=OKcontrol,CIFinput=CIFinput),**kw)
            if val is not None:
                self._setValue(val)
            else: # no default is invalid for a number
                self.invalid = True
                self._IndicateValidity()

        elif 'float' in str(type(val)) or typeHint is float:
            self.type = float
            wx.TextCtrl.__init__(self,parent,wx.ID_ANY,
                validator=NumberValidator(float,result=loc,key=key,min=min,max=max,
                    exclLim=exclLim,OKcontrol=OKcontrol,CIFinput=CIFinput),**kw)
            if val is not None:
                self._setValue(val)
            else:
                self.invalid = True
                self._IndicateValidity()

        elif isinstance(val,str) or isinstance(val,unicode) or typeHint is str:
            if self.CIFinput:
                wx.TextCtrl.__init__(
                    self,parent,wx.ID_ANY,
                    validator=ASCIIValidator(result=loc,key=key),
                    **kw)
            else:
                wx.TextCtrl.__init__(self,parent,wx.ID_ANY,**kw)
            if val is not None:
                self.SetValue(val)
            if notBlank:
                self.Bind(wx.EVT_CHAR,self._onStringKey)
                self.ShowStringValidity() # test if valid input
            else:
                self.invalid = False
                self.Bind(wx.EVT_CHAR,self._GetStringValue)
        elif val is None:
            raise Exception("ValidatedTxtCtrl error: value of "+str(key)+
                             " element is None and typeHint not defined as int or float")
        else:
            raise Exception("ValidatedTxtCtrl error: Unknown element ("+str(key)+
                             ") type: "+str(type(val)))
        # When the mouse is moved away or the widget loses focus,
        # display the last saved value, if an expression
        self.Bind(wx.EVT_LEAVE_WINDOW, self._onLeaveWindow)
        self.Bind(wx.EVT_TEXT_ENTER, self._onLoseFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self._onLoseFocus)
        # patch for wx 2.9 on Mac
        i,j= wx.__version__.split('.')[0:2]
        if int(i)+int(j)/10. > 2.8 and 'wxOSX' in wx.PlatformInfo:
            self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    def SetValue(self,val):
        if self.result is not None: # note that this bypasses formatting
            self.result[self.key] = val
            log.LogVarChange(self.result,self.key)
        self._setValue(val)

    def _setValue(self,val,show=True):
        '''Check the validity of an int or float value and convert to a str.
        Possibly format it. If show is True, display the formatted value in
        the Text widget.
        '''
        self.invalid = False
        if self.type is int:
            try:
                if int(val) != val:
                    self.invalid = True
                else:
                    val = int(val)
            except:
                if self.CIFinput and (val == '?' or val == '.'):
                    pass
                else:
                    self.invalid = True
            if show: wx.TextCtrl.SetValue(self,str(val))
        elif self.type is float:
            try:
                val = float(val) # convert strings, if needed
            except:
                if self.CIFinput and (val == '?' or val == '.'):
                    pass
                else:
                    self.invalid = True
            if self.nDig and show:
                wx.TextCtrl.SetValue(self,str(G2py3.FormatValue(val,self.nDig)))
            elif show:
                wx.TextCtrl.SetValue(self,str(G2py3.FormatSigFigs(val)).rstrip('0'))
        else:
            if self.ASCIIonly:
                s = ''
                for c in val:
                    if ord(c) < 128: s += c
                if val != s:
                    val = s
                    show = True
            if show:
                try:
                    wx.TextCtrl.SetValue(self,str(val))
                except:
                    wx.TextCtrl.SetValue(self,val)
            self.ShowStringValidity() # test if valid input
            return
        
        self._IndicateValidity()
        if self.OKcontrol:
            self.OKcontrol(not self.invalid)

    def OnKeyDown(self,event):
        'Special callback for wx 2.9+ on Mac where backspace is not processed by validator'
        key = event.GetKeyCode()
        if key in [wx.WXK_BACK, wx.WXK_DELETE]:
            if self.Validator: wx.CallAfter(self.Validator.TestValid,self)
        if key == wx.WXK_RETURN or key == wx.WXK_NUMPAD_ENTER:
            self._onLoseFocus(None)
        if event: event.Skip()
                    
    def _onStringKey(self,event):
        if event: event.Skip()
        if self.invalid: # check for validity after processing the keystroke
            wx.CallAfter(self.ShowStringValidity,True) # was invalid
        else:
            wx.CallAfter(self.ShowStringValidity,False) # was valid

    def _IndicateValidity(self):
        'Set the control colors to show invalid input'
        if self.invalid:
            ins = self.GetInsertionPoint()
            self.SetForegroundColour("red")
            self.SetBackgroundColour("yellow")
            self.SetFocus()
            self.Refresh() # this selects text on some Linuxes
            self.SetSelection(0,0)   # unselect
            self.SetInsertionPoint(ins) # put insertion point back 
        else: # valid input
            self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
            self.SetForegroundColour("black")
            self.Refresh()

    def ShowStringValidity(self,previousInvalid=True):
        '''Check if input is valid. Anytime the input is
        invalid, call self.OKcontrol (if defined) because it is fast.
        If valid, check for any other invalid entries only when
        changing from invalid to valid, since that is slower.
        
        :param bool previousInvalid: True if the TextCtrl contents were
          invalid prior to the current change.
          
        '''
        val = self.GetValue().strip()
        if self.notBlank:
            self.invalid = not val
        else:
            self.invalid = False
        self._IndicateValidity()
        if self.invalid:
            if self.OKcontrol:
                self.OKcontrol(False)
        elif self.OKcontrol and previousInvalid:
            self.OKcontrol(True)
        # always store the result
        if self.CIFinput: # for CIF make results ASCII
            self.result[self.key] = val.encode('ascii','replace') 
        else:
            self.result[self.key] = val
        log.LogVarChange(self.result,self.key)

    def _GetStringValue(self,event):
        '''Get string input and store.
        '''
        if event: event.Skip() # process keystroke
        wx.CallAfter(self._SaveStringValue)
        
    def _SaveStringValue(self):
        val = self.GetValue().strip()
        # always store the result
        if self.CIFinput: # for CIF make results ASCII
            self.result[self.key] = val.encode('ascii','replace') 
        else:
            self.result[self.key] = val
        log.LogVarChange(self.result,self.key)

    def _onLeaveWindow(self,event):
        '''If the mouse leaves the text box, save the result, if valid,
        but (unlike _onLoseFocus) don't update the textbox contents.
        '''
        if not self.IsModified():   #ignore mouse crusing
            return
        if self.evaluated and not self.invalid: # deal with computed expressions
            self.evaluated = False # expression has been recast as value, reset flag
        if self.invalid: # don't update an invalid expression
            if event: event.Skip()
            return
        self._setValue(self.result[self.key],show=False) # save value quietly
        if self.OnLeave:
            self.event = event
            self.OnLeave(invalid=self.invalid,value=self.result[self.key],
                tc=self,**self.OnLeaveArgs)
        if event: event.Skip()
            
    def _onLoseFocus(self,event):
        '''Enter has been pressed or focus transferred to another control,
        Evaluate and update the current control contents
        '''
        if event: event.Skip()
        if not self.IsModified():   #ignore mouse crusing
            return
        if self.evaluated: # deal with computed expressions
            if self.invalid: # don't substitute for an invalid expression
                return 
            self.evaluated = False # expression has been recast as value, reset flag
            self._setValue(self.result[self.key])
        elif self.result is not None: # show formatted result, as Bob wants
            if not self.invalid: # don't update an invalid expression
                self._setValue(self.result[self.key])
        if self.OnLeave:
            self.event = event
            self.OnLeave(invalid=self.invalid,value=self.result[self.key],
                tc=self,**self.OnLeaveArgs)

################################################################################
class NumberValidator(wx.PyValidator):
    '''A validator to be used with a TextCtrl to prevent
    entering characters other than digits, signs, and for float
    input, a period and exponents.
    
    The value is checked for validity after every keystroke
      If an invalid number is entered, the box is highlighted.
      If the number is valid, it is saved in result[key]

    :param type typ: the base data type. Must be int or float.

    :param bool positiveonly: If True, negative integers are not allowed
      (default False). This prevents the + or - keys from being pressed.
      Used with typ=int; ignored for typ=float.

    :param number min: Minimum allowed value. If None (default) the
      lower limit is unbounded

    :param number max: Maximum allowed value. If None (default) the
      upper limit is unbounded
      
    :param list exclLim: if True exclude min/max value ([exclMin,exclMax]); 
     (Default=[False,False]) 

    :param dict/list result: List or dict where value should be placed when valid

    :param any key: key to use for result (int for list)

    :param function OKcontrol: function or class method to control
      an OK button for a window. 
      Ignored if None (default)

    :param bool CIFinput: allows use of a single '?' or '.' character
      as valid input.
      
    '''
    def __init__(self, typ, positiveonly=False, min=None, max=None,exclLim=[False,False],
        result=None, key=None, OKcontrol=None, CIFinput=False):
        'Create the validator'
        if 'phoenix' in wx.version():
            wx.Validator.__init__(self)
        else:
            wx.PyValidator.__init__(self)
        # save passed parameters
        self.typ = typ
        self.positiveonly = positiveonly
        self.min = min
        self.max = max
        self.exclLim = exclLim
        self.result = result
        self.key = key
        self.OKcontrol = OKcontrol
        self.CIFinput = CIFinput
        # set allowed keys by data type
        self.Bind(wx.EVT_CHAR, self.OnChar)
        if self.typ == int and self.positiveonly:
            self.validchars = '0123456789'
        elif self.typ == int:
            self.validchars = '0123456789+-'
        elif self.typ == float:
            # allow for above and sind, cosd, sqrt, tand, pi, and abbreviations
            # also addition, subtraction, division, multiplication, exponentiation
            self.validchars = '0123456789.-+eE/cosindcqrtap()*'
        else:
            self.validchars = None
            return
        if self.CIFinput:
            self.validchars += '?.'
    def Clone(self):
        'Create a copy of the validator, a strange, but required component'
        return NumberValidator(typ=self.typ, 
                               positiveonly=self.positiveonly,
                               min=self.min, max=self.max,
                               result=self.result, key=self.key,
                               OKcontrol=self.OKcontrol,
                               CIFinput=self.CIFinput)
    def TransferToWindow(self):
        'Needed by validator, strange, but required component'
        return True # Prevent wxDialog from complaining.
    def TransferFromWindow(self):
        'Needed by validator, strange, but required component'
        return True # Prevent wxDialog from complaining.
    def TestValid(self,tc):
        '''Check if the value is valid by casting the input string
        into the current type.

        Set the invalid variable in the TextCtrl object accordingly.

        If the value is valid, save it in the dict/list where
        the initial value was stored, if appropriate. 

        :param wx.TextCtrl tc: A reference to the TextCtrl that the validator
          is associated with.
        '''
        tc.invalid = False # assume valid
        if self.CIFinput:
            val = tc.GetValue().strip()
            if val == '?' or val == '.':
                self.result[self.key] = val
                log.LogVarChange(self.result,self.key)
                return
        try:
            val = self.typ(tc.GetValue())
        except (ValueError, SyntaxError):
            if self.typ is float: # for float values, see if an expression can be evaluated
                val = G2py3.FormulaEval(tc.GetValue())
                if val is None:
                    tc.invalid = True
                    return
                else:
                    tc.evaluated = True
            else: 
                tc.invalid = True
                return
        if self.max != None:
            if val >= self.max and self.exclLim[1]:
                tc.invalid = True
            elif val > self.max:
                tc.invalid = True
        if self.min != None:
            if val <= self.min and self.exclLim[0]:
                tc.invalid = True
            elif val < self.min:
                tc.invalid = True  # invalid
        if self.key is not None and self.result is not None and not tc.invalid:
            self.result[self.key] = val
            log.LogVarChange(self.result,self.key)

    def ShowValidity(self,tc):
        '''Set the control colors to show invalid input

        :param wx.TextCtrl tc: A reference to the TextCtrl that the validator
          is associated with.

        '''
        if tc.invalid:
            ins = tc.GetInsertionPoint()
            tc.SetForegroundColour("red")
            tc.SetBackgroundColour("yellow")
            tc.SetFocus()
            tc.Refresh() # this selects text on some Linuxes
            tc.SetSelection(0,0)   # unselect
            tc.SetInsertionPoint(ins) # put insertion point back 
            return False
        else: # valid input
            tc.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
            tc.SetForegroundColour("black")
            tc.Refresh()
            return True

    def CheckInput(self,previousInvalid):
        '''called to test every change to the TextCtrl for validity and
        to change the appearance of the TextCtrl

        Anytime the input is invalid, call self.OKcontrol
        (if defined) because it is fast. 
        If valid, check for any other invalid entries only when
        changing from invalid to valid, since that is slower.

        :param bool previousInvalid: True if the TextCtrl contents were
          invalid prior to the current change.
        '''
        tc = self.GetWindow()
        self.TestValid(tc)
        self.ShowValidity(tc)
        # if invalid
        if tc.invalid and self.OKcontrol:
            self.OKcontrol(False)
        if not tc.invalid and self.OKcontrol and previousInvalid:
            self.OKcontrol(True)

    def OnChar(self, event):
        '''Called each type a key is pressed
        ignores keys that are not allowed for int and float types
        '''
        key = event.GetKeyCode()
        tc = self.GetWindow()
        if key == wx.WXK_RETURN or key == wx.WXK_NUMPAD_ENTER:
            if tc.invalid:
                self.CheckInput(True) 
            else:
                self.CheckInput(False) 
            if event: event.Skip()
            return
        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255: # control characters get processed
            if event: event.Skip()
            if tc.invalid:
                wx.CallAfter(self.CheckInput,True) 
            else:
                wx.CallAfter(self.CheckInput,False) 
            return
        elif chr(key) in self.validchars: # valid char pressed?
            if event: event.Skip()
            if tc.invalid:
                wx.CallAfter(self.CheckInput,True) 
            else:
                wx.CallAfter(self.CheckInput,False) 
            return
        if not wx.Validator_IsSilent(): wx.Bell()
        return  # Returning without calling event.Skip, which eats the keystroke

################################################################################
class ASCIIValidator(wx.PyValidator):
    '''A validator to be used with a TextCtrl to prevent
    entering characters other than ASCII characters.
    
    The value is checked for validity after every keystroke
      If an invalid number is entered, the box is highlighted.
      If the number is valid, it is saved in result[key]

    :param dict/list result: List or dict where value should be placed when valid

    :param any key: key to use for result (int for list)

    '''
    def __init__(self, result=None, key=None):
        'Create the validator'
        import string
        wx.PyValidator.__init__(self)
        # save passed parameters
        self.result = result
        self.key = key
        self.validchars = string.ascii_letters + string.digits + string.punctuation + string.whitespace
        self.Bind(wx.EVT_CHAR, self.OnChar)
    def Clone(self):
        'Create a copy of the validator, a strange, but required component'
        return ASCIIValidator(result=self.result, key=self.key)
        tc = self.GetWindow()
        tc.invalid = False # make sure the validity flag is defined in parent
    def TransferToWindow(self):
        'Needed by validator, strange, but required component'
        return True # Prevent wxDialog from complaining.
    def TransferFromWindow(self):
        'Needed by validator, strange, but required component'
        return True # Prevent wxDialog from complaining.
    def TestValid(self,tc):
        '''Check if the value is valid by casting the input string
        into ASCII. 

        Save it in the dict/list where the initial value was stored

        :param wx.TextCtrl tc: A reference to the TextCtrl that the validator
          is associated with.
        '''
        self.result[self.key] = tc.GetValue().encode('ascii','replace')
        log.LogVarChange(self.result,self.key)

    def OnChar(self, event):
        '''Called each type a key is pressed
        ignores keys that are not allowed for int and float types
        '''
        key = event.GetKeyCode()
        tc = self.GetWindow()
        if key == wx.WXK_RETURN or key == wx.WXK_NUMPAD_ENTER:
            self.TestValid(tc)
            if event: event.Skip()
            return
        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255: # control characters get processed
            if event: event.Skip()
            self.TestValid(tc)
            return
        elif chr(key) in self.validchars: # valid char pressed?
            if event: event.Skip()
            self.TestValid(tc)
            return
        if not wx.Validator_IsSilent():
            wx.Bell()
        return  # Returning without calling event.Skip, which eats the keystroke

################################################################################
def HorizontalLine(sizer,parent):
    '''Draws a horizontal line as wide as the window.
    This shows up on the Mac as a very thin line, no matter what I do
    '''
    line = wx.StaticLine(parent, size=(-1,3), style=wx.LI_HORIZONTAL)
    sizer.Add(line, 0, wx.EXPAND|wx.ALIGN_CENTER|wx.ALL, 5)

################################################################################
class G2LoggedButton(wx.Button):
    '''A version of wx.Button that creates logging events. Bindings are saved
    in the object, and are looked up rather than directly set with a bind.
    An index to these buttons is saved as log.ButtonBindingLookup
    :param wx.Panel parent: parent widget
    :param int id: Id for button
    :param str label: label for button
    :param str locationcode: a label used internally to uniquely indentify the button
    :param function handler: a routine to call when the button is pressed
    '''
    def __init__(self,parent,id=wx.ID_ANY,label='',locationcode='',
                 handler=None,*args,**kwargs):
        super(self.__class__,self).__init__(parent,id,label,*args,**kwargs)
        self.label = label
        self.handler = handler
        self.locationcode = locationcode
        key = locationcode + '+' + label # hash code to find button
        self.Bind(wx.EVT_BUTTON,self.onPress)
        log.ButtonBindingLookup[key] = self
    def onPress(self,event):
        'create log event and call handler'
        log.MakeButtonLog(self.locationcode,self.label)
        self.handler(event)
        
################################################################################
class EnumSelector(wx.ComboBox):
    '''A customized :class:`wxpython.ComboBox` that selects items from a list
    of choices, but sets a dict (list) entry to the corresponding
    entry from the input list of values.

    :param wx.Panel parent: the parent to the :class:`~wxpython.ComboBox` (usually a
      frame or panel)
    :param dict dct: a dict (or list) to contain the value set
      for the :class:`~wxpython.ComboBox`.
    :param item: the dict key (or list index) where ``dct[item]`` will 
      be set to the value selected in the :class:`~wxpython.ComboBox`. Also, dct[item]
      contains the starting value shown in the widget. If the value
      does not match an entry in :data:`values`, the first value
      in :data:`choices` is used as the default, but ``dct[item]`` is
      not changed.    
    :param list choices: a list of choices to be displayed to the
      user such as
      ::
      
      ["default","option 1","option 2",]

      Note that these options will correspond to the entries in 
      :data:`values` (if specified) item by item. 
    :param list values: a list of values that correspond to
      the options in :data:`choices`, such as
      ::
      
      [0,1,2]
      
      The default for :data:`values` is to use the same list as
      specified for :data:`choices`.
    :param (other): additional keyword arguments accepted by
      :class:`~wxpython.ComboBox` can be specified.
    '''
    def __init__(self,parent,dct,item,choices,values=None,**kw):
        if values is None:
            values = choices
        if dct[item] in values:
            i = values.index(dct[item])
        else:
            i = 0
        startval = choices[i]
        wx.ComboBox.__init__(self,parent,wx.ID_ANY,startval,
                             choices = choices,
                             style=wx.CB_DROPDOWN|wx.CB_READONLY,
                             **kw)
        self.choices = choices
        self.values = values
        self.dct = dct
        self.item = item
        self.Bind(wx.EVT_COMBOBOX, self.onSelection)
    def onSelection(self,event):
        # respond to a selection by setting the enum value in the CIF dictionary
        if self.GetValue() in self.choices: # should always be true!
            self.dct[self.item] = self.values[self.choices.index(self.GetValue())]
        else:
            self.dct[self.item] = self.values[0] # unknown

################################################################################
class G2ChoiceButton(wx.Choice):
    '''A customized version of a wx.Choice that automatically initializes
    the control to match a supplied value and saves the choice directly
    into an array or list. Optionally a function can be called each time a
    choice is selected. The widget can be used with an array item that is set to 
    to the choice by number (``indLoc[indKey]``) or by string value
    (``strLoc[strKey]``) or both. The initial value is taken from ``indLoc[indKey]``
    if not None or ``strLoc[strKey]`` if not None. 

    :param wx.Panel parent: name of panel or frame that will be
      the parent to the widget. Can be None.
    :param list choiceList: a list or tuple of choices to offer the user.
    :param dict/list indLoc: a dict or list with the initial value to be
      placed in the Choice button. If this is None, this is ignored. 
    :param int/str indKey: the dict key or the list index for the value to be
      edited by the Choice button. If indLoc is not None then this
      must be specified and the ``indLoc[indKey]`` will be set. If the value
      for ``indLoc[indKey]`` is not None, it should be an integer in
      range(len(choiceList)). The Choice button will be initialized to the
      choice corresponding to the value in this element if not None.
    :param dict/list strLoc: a dict or list with the string value corresponding to
      indLoc/indKey. Default (None) means that this is not used. 
    :param int/str strKey: the dict key or the list index for the string value 
      The ``strLoc[strKey]`` element must exist or strLoc must be None (default).
    :param function onChoice: name of a function to call when the choice is made.
    '''
    def __init__(self,parent,choiceList,indLoc=None,indKey=None,strLoc=None,strKey=None,
                 onChoice=None,**kwargs):
        wx.Choice.__init__(self,parent,choices=choiceList,id=wx.ID_ANY,**kwargs)
        self.choiceList = choiceList
        self.indLoc = indLoc
        self.indKey = indKey
        self.strLoc = strLoc
        self.strKey = strKey
        self.onChoice = None
        self.SetSelection(wx.NOT_FOUND)
        if self.indLoc is not None and self.indLoc.get(self.indKey) is not None:
            self.SetSelection(self.indLoc[self.indKey])
            if self.strLoc is not None:
                self.strLoc[self.strKey] = self.GetStringSelection()
                log.LogVarChange(self.strLoc,self.strKey)
        elif self.strLoc is not None and self.strLoc.get(self.strKey) is not None:
            try:
                self.SetSelection(choiceList.index(self.strLoc[self.strKey]))
                if self.indLoc is not None:
                    self.indLoc[self.indKey] = self.GetSelection()
                    log.LogVarChange(self.indLoc,self.indKey)
            except ValueError:
                pass
        self.Bind(wx.EVT_CHOICE, self._OnChoice)
        #if self.strLoc is not None: # make sure strLoc gets initialized
        #    self._OnChoice(None) # note that onChoice will not be called
        self.onChoice = onChoice
    def _OnChoice(self,event):
        if self.indLoc is not None:
            self.indLoc[self.indKey] = self.GetSelection()
            log.LogVarChange(self.indLoc,self.indKey)
        if self.strLoc is not None:
            self.strLoc[self.strKey] = self.GetStringSelection()
            log.LogVarChange(self.strLoc,self.strKey)
        if self.onChoice:
            self.onChoice()

############################################################### Custom checkbox that saves values into dict/list as used
class G2CheckBox(wx.CheckBox):
    '''A customized version of a CheckBox that automatically initializes
    the control to a supplied list or dict entry and updates that
    entry as the widget is used.

    :param wx.Panel parent: name of panel or frame that will be
      the parent to the widget. Can be None.
    :param str label: text to put on check button
    :param dict/list loc: the dict or list with the initial value to be
      placed in the CheckBox. 
    :param int/str key: the dict key or the list index for the value to be
      edited by the CheckBox. The ``loc[key]`` element must exist.
      The CheckBox will be initialized from this value.
      If the value is anything other that True (or 1), it will be taken as
      False.
    :param function OnChange: specifies a function or method that will be
      called when the CheckBox is changed (Default is None). 
      The called function is supplied with one argument, the calling event.
    '''
    def __init__(self,parent,label,loc,key,OnChange=None):
        wx.CheckBox.__init__(self,parent,id=wx.ID_ANY,label=label)
        self.loc = loc
        self.key = key
        self.OnChange = OnChange
        self.SetValue(self.loc[self.key]==True)
        self.Bind(wx.EVT_CHECKBOX, self._OnCheckBox)
    def _OnCheckBox(self,event):
        self.loc[self.key] = self.GetValue()
        log.LogVarChange(self.loc,self.key)
        if self.OnChange: self.OnChange(event)
                    
################################################################################
#### Commonly used dialogs
################################################################################
def CallScrolledMultiEditor(parent,dictlst,elemlst,prelbl=[],postlbl=[],
                 title='Edit items',header='',size=(300,250),
                             CopyButton=False, ASCIIonly=False, **kw):
    '''Shell routine to call a ScrolledMultiEditor dialog. See
    :class:`ScrolledMultiEditor` for parameter definitions.

    :returns: True if the OK button is pressed; False if the window is closed
      with the system menu or the Cancel button.

    '''
    dlg = ScrolledMultiEditor(parent,dictlst,elemlst,prelbl,postlbl,
                              title,header,size,
                              CopyButton, ASCIIonly, **kw)
    if dlg.ShowModal() == wx.ID_OK:
        dlg.Destroy()
        return True
    else:
        dlg.Destroy()
        return False

################################################################################
class ScrolledMultiEditor(wx.Dialog):
    '''Define a window for editing a potentially large number of dict- or
    list-contained values with validation for each item. Edited values are
    automatically placed in their source location. If invalid entries
    are provided, the TextCtrl is turned yellow and the OK button is disabled.

    The type for each TextCtrl validation is determined by the
    initial value of the entry (int, float or string). 
    Float values can be entered in the TextCtrl as numbers or also
    as algebraic expressions using operators + - / \* () and \*\*,
    in addition pi, sind(), cosd(), tand(), and sqrt() can be used,
    as well as appreviations s(), sin(), c(), cos(), t(), tan() and sq(). 

    :param wx.Frame parent: name of parent window, or may be None

    :param tuple dictlst: a list of dicts or lists containing values to edit

    :param tuple elemlst: a list of keys for each item in a dictlst. Must have the
      same length as dictlst.

    :param wx.Frame parent: name of parent window, or may be None
    
    :param tuple prelbl: a list of labels placed before the TextCtrl for each
      item (optional)
   
    :param tuple postlbl: a list of labels placed after the TextCtrl for each
      item (optional)

    :param str title: a title to place in the frame of the dialog

    :param str header: text to place at the top of the window. May contain
      new line characters. 

    :param wx.Size size: a size parameter that dictates the
      size for the scrolled region of the dialog. The default is
      (300,250). 

    :param bool CopyButton: if True adds a small button that copies the
      value for the current row to all fields below (default is False)
      
    :param bool ASCIIonly: if set as True will remove unicode characters from
      strings
      
    :param list minvals: optional list of minimum values for validation
      of float or int values. Ignored if value is None.
    :param list maxvals: optional list of maximum values for validation
      of float or int values. Ignored if value is None.
    :param list sizevals: optional list of wx.Size values for each input
      widget. Ignored if value is None.
      
    :param tuple checkdictlst: an optional list of dicts or lists containing bool
      values (similar to dictlst). 
    :param tuple checkelemlst: an optional list of dicts or lists containing bool
      key values (similar to elemlst). Must be used with checkdictlst.
    :param string checklabel: a string to use for each checkbutton
      
    :returns: the wx.Dialog created here. Use method .ShowModal() to display it.
    
    *Example for use of ScrolledMultiEditor:*

    ::

        dlg = <pkg>.ScrolledMultiEditor(frame,dictlst,elemlst,prelbl,postlbl,
                                        header=header)
        if dlg.ShowModal() == wx.ID_OK:
             for d,k in zip(dictlst,elemlst):
                 print d[k]

    *Example definitions for dictlst and elemlst:*

    ::
      
          dictlst = (dict1,list1,dict1,list1)
          elemlst = ('a', 1, 2, 3)

      This causes items dict1['a'], list1[1], dict1[2] and list1[3] to be edited.
    
    Note that these items must have int, float or str values assigned to
    them. The dialog will force these types to be retained. String values
    that are blank are marked as invalid. 
    '''
    
    def __init__(self,parent,dictlst,elemlst,prelbl=[],postlbl=[],
                 title='Edit items',header='',size=(300,250),
                 CopyButton=False, ASCIIonly=False,
                 minvals=[],maxvals=[],sizevals=[],
                 checkdictlst=[], checkelemlst=[], checklabel=""):
        if len(dictlst) != len(elemlst):
            raise Exception("ScrolledMultiEditor error: len(dictlst) != len(elemlst) "+str(len(dictlst))+" != "+str(len(elemlst)))
        if len(checkdictlst) != len(checkelemlst):
            raise Exception("ScrolledMultiEditor error: len(checkdictlst) != len(checkelemlst) "+str(len(checkdictlst))+" != "+str(len(checkelemlst)))
        wx.Dialog.__init__( # create dialog & sizer
            self,parent,wx.ID_ANY,title,
            style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.orig = []
        self.dictlst = dictlst
        self.elemlst = elemlst
        self.checkdictlst = checkdictlst
        self.checkelemlst = checkelemlst
        self.StartCheckValues = [checkdictlst[i][checkelemlst[i]] for i in range(len(checkdictlst))]
        self.ButtonIndex = {}
        for d,i in zip(dictlst,elemlst):
            self.orig.append(d[i])
        # add a header if supplied
        if header:
            subSizer = wx.BoxSizer(wx.HORIZONTAL)
            subSizer.Add((-1,-1),1,wx.EXPAND)
            subSizer.Add(wx.StaticText(self,wx.ID_ANY,header))
            subSizer.Add((-1,-1),1,wx.EXPAND)
            mainSizer.Add(subSizer,0,wx.EXPAND,0)
        # make OK button now, because we will need it for validation
        self.OKbtn = wx.Button(self, wx.ID_OK)
        self.OKbtn.SetDefault()
        # create scrolled panel and sizer
        panel = wxscroll.ScrolledPanel(self, wx.ID_ANY,size=size,
            style = wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        cols = 4
        if CopyButton: cols += 1
        subSizer = wx.FlexGridSizer(cols=cols,hgap=2,vgap=2)
        self.ValidatedControlsList = [] # make list of TextCtrls
        self.CheckControlsList = [] # make list of CheckBoxes
        for i,(d,k) in enumerate(zip(dictlst,elemlst)):
            if i >= len(prelbl): # label before TextCtrl, or put in a blank
                subSizer.Add((-1,-1)) 
            else:
                subSizer.Add(wx.StaticText(panel,wx.ID_ANY,str(prelbl[i])))
            kargs = {}
            if i < len(minvals):
                if minvals[i] is not None: kargs['min']=minvals[i]
            if i < len(maxvals):
                if maxvals[i] is not None: kargs['max']=maxvals[i]
            if i < len(sizevals):
                if sizevals[i]: kargs['size']=sizevals[i]
            if CopyButton:
                import wx.lib.colourselect as wscs  # is there a way to test? 
                but = wscs.ColourSelect(label='v', # would like to use u'\u2193' or u'\u25BC' but not in WinXP
                    parent=panel,colour=(255,255,200),size=wx.Size(30,23),
                    style=wx.RAISED_BORDER)
                but.Bind(wx.EVT_BUTTON, self._OnCopyButton)
                but.SetToolTipString('Press to copy adjacent value to all rows below')
                self.ButtonIndex[but] = i
                subSizer.Add(but)
            # create the validated TextCrtl, store it and add it to the sizer
            ctrl = ValidatedTxtCtrl(panel,d,k,OKcontrol=self.ControlOKButton,ASCIIonly=ASCIIonly,
                                    **kargs)
            self.ValidatedControlsList.append(ctrl)
            subSizer.Add(ctrl)
            if i < len(postlbl): # label after TextCtrl, or put in a blank
                subSizer.Add(wx.StaticText(panel,wx.ID_ANY,str(postlbl[i])))
            else:
                subSizer.Add((-1,-1))
            if i < len(checkdictlst):
                ch = G2CheckBox(panel,checklabel,checkdictlst[i],checkelemlst[i])
                self.CheckControlsList.append(ch)
                subSizer.Add(ch)                    
            else:
                subSizer.Add((-1,-1))
        # finish up ScrolledPanel
        panel.SetSizer(subSizer)
        panel.SetAutoLayout(1)
        panel.SetupScrolling()
        # patch for wx 2.9 on Mac
        i,j= wx.__version__.split('.')[0:2]
        if int(i)+int(j)/10. > 2.8 and 'wxOSX' in wx.PlatformInfo:
            panel.SetMinSize((subSizer.GetSize()[0]+30,panel.GetSize()[1]))        
        mainSizer.Add(panel,1, wx.ALL|wx.EXPAND,1)

        # Sizer for OK/Close buttons. N.B. on Close changes are discarded
        # by restoring the initial values
        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        btnsizer.Add(self.OKbtn)
        btn = wx.Button(self, wx.ID_CLOSE,"Cancel") 
        btn.Bind(wx.EVT_BUTTON,self._onClose)
        btnsizer.Add(btn)
        mainSizer.Add(btnsizer, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        # size out the window. Set it to be enlarged but not made smaller
        self.SetSizer(mainSizer)
        mainSizer.Fit(self)
        self.SetMinSize(self.GetSize())

    def _OnCopyButton(self,event):
        'Implements the copy down functionality'
        but = event.GetEventObject()
        n = self.ButtonIndex.get(but)
        if n is None: return
        for i,(d,k,ctrl) in enumerate(zip(self.dictlst,self.elemlst,self.ValidatedControlsList)):
            if i < n: continue
            if i == n:
                val = d[k]
                continue
            d[k] = val
            ctrl.SetValue(val)
        for i in range(len(self.checkdictlst)):
            if i < n: continue
            self.checkdictlst[i][self.checkelemlst[i]] = self.checkdictlst[n][self.checkelemlst[n]]
            self.CheckControlsList[i].SetValue(self.checkdictlst[i][self.checkelemlst[i]])
    def _onClose(self,event):
        'Used on Cancel: Restore original values & close the window'
        for d,i,v in zip(self.dictlst,self.elemlst,self.orig):
            d[i] = v
        for i in range(len(self.checkdictlst)):
            self.checkdictlst[i][self.checkelemlst[i]] = self.StartCheckValues[i]
        self.EndModal(wx.ID_CANCEL)
        
    def ControlOKButton(self,setvalue):
        '''Enable or Disable the OK button for the dialog. Note that this is
        passed into the ValidatedTxtCtrl for use by validators.

        :param bool setvalue: if True, all entries in the dialog are
          checked for validity. if False then the OK button is disabled.

        '''
        if setvalue: # turn button on, do only if all controls show as valid
            for ctrl in self.ValidatedControlsList:
                if ctrl.invalid:
                    self.OKbtn.Disable()
                    return
            else:
                self.OKbtn.Enable()
        else:
            self.OKbtn.Disable()

###############################################  Multichoice Dialog with set all, toggle & filter options
class G2MultiChoiceDialog(wx.Dialog):
    '''A dialog similar to MultiChoiceDialog except that buttons are
    added to set all choices and to toggle all choices.

    :param wx.Frame ParentFrame: reference to parent frame
    :param str title: heading above list of choices
    :param str header: Title to place on window frame 
    :param list ChoiceList: a list of choices where one more will be selected
    :param bool toggle: If True (default) the toggle and select all buttons
      are displayed
    :param bool monoFont: If False (default), use a variable-spaced font;
      if True use a equally-spaced font.
    :param bool filterBox: If True (default) an input widget is placed on
      the window and only entries matching the entered text are shown.
    :param dict extraOpts: a dict containing a entries of form label_i and value_i with extra
      options to present to the user, where value_i is the default value. 
      Options are listed ordered by the value_i values.
    :param kw: optional keyword parameters for the wx.Dialog may
      be included such as size [which defaults to `(320,310)`] and
      style (which defaults to `wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.CENTRE| wx.OK | wx.CANCEL`);
      note that `wx.OK` and `wx.CANCEL` style items control 
      the presence of the eponymous buttons in the dialog.
    :returns: the name of the created dialog  
    '''
    def __init__(self,parent, title, header, ChoiceList, toggle=True,
                 monoFont=False, filterBox=True, extraOpts={}, **kw):
        # process keyword parameters, notably style
        options = {'size':(320,310), # default Frame keywords
                   'style':wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.CENTRE| wx.OK | wx.CANCEL,
                   }
        options.update(kw)
        self.ChoiceList = ['%4d) %s'%(i,item) for i,item in enumerate(ChoiceList)] # numbered list of choices (list of str values)
        self.Selections = len(self.ChoiceList) * [False,] # selection status for each choice (list of bools)
        self.filterlist = range(len(self.ChoiceList)) # list of the choice numbers that have been filtered (list of int indices)
        self.Stride = 1
        if options['style'] & wx.OK:
            useOK = True
            options['style'] ^= wx.OK
        else:
            useOK = False
        if options['style'] & wx.CANCEL:
            useCANCEL = True
            options['style'] ^= wx.CANCEL
        else:
            useCANCEL = False        
        # create the dialog frame
        wx.Dialog.__init__(self,parent,wx.ID_ANY,header,**options)
        # fill the dialog
        Sizer = wx.BoxSizer(wx.VERTICAL)
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        topSizer.Add(wx.StaticText(self,wx.ID_ANY,title,size=(-1,35)),
            1,wx.ALL|wx.EXPAND|WACV,1)
        if filterBox:
            self.timer = wx.Timer()
            self.timer.Bind(wx.EVT_TIMER,self.Filter)
            topSizer.Add(wx.StaticText(self,wx.ID_ANY,'Name \nFilter: '),0,wx.ALL|WACV,1)
            self.filterBox = wx.TextCtrl(self, wx.ID_ANY, size=(80,-1),style=wx.TE_PROCESS_ENTER)
            self.filterBox.Bind(wx.EVT_TEXT,self.onChar)
            self.filterBox.Bind(wx.EVT_TEXT_ENTER,self.Filter)
            topSizer.Add(self.filterBox,0,wx.ALL|WACV,0)
        Sizer.Add(topSizer,0,wx.ALL|wx.EXPAND,8)
        self.settingRange = False
        self.rangeFirst = None
        self.clb = wx.CheckListBox(self, wx.ID_ANY, (30,30), wx.DefaultSize, self.ChoiceList)
        self.clb.Bind(wx.EVT_CHECKLISTBOX,self.OnCheck)
        if monoFont:
            font1 = wx.Font(self.clb.GetFont().GetPointSize(),
                            wx.MODERN, wx.NORMAL, wx.NORMAL, False)
            self.clb.SetFont(font1)
        Sizer.Add(self.clb,1,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
        Sizer.Add((-1,10))
        # set/toggle buttons
        if toggle:
            tSizer = wx.FlexGridSizer(cols=2,hgap=5,vgap=5)
            tSizer.Add(wx.StaticText(self,label=' Apply stride:'),0,WACV)
            numbs = [str(i+1) for i in range(9)]+[str(2*i+10) for i in range(6)]
            self.stride = wx.ComboBox(self,value='1',choices=numbs,style=wx.CB_READONLY|wx.CB_DROPDOWN)
            self.stride.Bind(wx.EVT_COMBOBOX,self.OnStride)
            tSizer.Add(self.stride,0,WACV)
            setBut = wx.Button(self,wx.ID_ANY,'Set All')
            setBut.Bind(wx.EVT_BUTTON,self._SetAll)
            tSizer.Add(setBut)
            togBut = wx.Button(self,wx.ID_ANY,'Toggle All')
            togBut.Bind(wx.EVT_BUTTON,self._ToggleAll)
            tSizer.Add(togBut)
            self.rangeBut = wx.ToggleButton(self,wx.ID_ANY,'Set Range')
            self.rangeBut.Bind(wx.EVT_TOGGLEBUTTON,self.SetRange)
            tSizer.Add(self.rangeBut)
            self.rangeCapt = wx.StaticText(self,wx.ID_ANY,'')
            tSizer.Add(self.rangeCapt)
            Sizer.Add(tSizer,0,wx.LEFT,12)
        # Extra widgets
        Sizer.Add((-1,5),0,wx.LEFT,0)
        bSizer = wx.BoxSizer(wx.VERTICAL)
        for lbl in sorted(extraOpts.keys()):
            if not lbl.startswith('label'): continue
            key = lbl.replace('label','value')
            if key not in extraOpts: continue
            eSizer = wx.BoxSizer(wx.HORIZONTAL)
            if type(extraOpts[key]) is bool:
                eSizer.Add(G2CheckBox(self,extraOpts[lbl],extraOpts,key))
            else:
                eSizer.Add(wx.StaticText(self,wx.ID_ANY,extraOpts[lbl]))
                eSizer.Add(ValidatedTxtCtrl(self,extraOpts,key))
            bSizer.Add(eSizer,0,wx.LEFT,0)
        Sizer.Add(bSizer,0,wx.CENTER,0)
        Sizer.Add((-1,5),0,wx.LEFT,0)
        # OK/Cancel buttons
        btnsizer = wx.StdDialogButtonSizer()
        if useOK:
            self.OKbtn = wx.Button(self, wx.ID_OK)
            self.OKbtn.SetDefault()
            btnsizer.AddButton(self.OKbtn)
            self.OKbtn.Bind(wx.EVT_BUTTON,self.onOk)
        if useCANCEL:
            btn = wx.Button(self, wx.ID_CANCEL)
            btn.Bind(wx.EVT_BUTTON,self.onCancel)
            btnsizer.AddButton(btn)
        btnsizer.Realize()
        Sizer.Add((-1,5))
        Sizer.Add(btnsizer,0,wx.ALIGN_RIGHT,50)
        Sizer.Add((-1,20))
        # OK done, let's get outa here
        self.SetSizer(Sizer)
        Sizer.Fit(self)
        self.CenterOnParent()
        
    def onOk(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_OK)              
        
    def onCancel(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_CANCEL)
        
    def OnStride(self,event):
        self.Stride = int(self.stride.GetValue())

    def SetRange(self,event):
        '''Respond to a press of the Set Range button. Set the range flag and
        the caption next to the button
        '''
        self.settingRange = self.rangeBut.GetValue()
        if self.settingRange:
            self.rangeCapt.SetLabel('Select range start')
        else:
            self.rangeCapt.SetLabel('')            
        self.rangeFirst = None
        
    def GetSelections(self):
        'Returns a list of the indices for the selected choices'
        # update self.Selections with settings for displayed items
        for i in range(len(self.filterlist)):
            self.Selections[self.filterlist[i]] = self.clb.IsChecked(i)
        # return all selections, shown or hidden
        return [i for i in range(len(self.Selections)) if self.Selections[i]]
        
    def SetSelections(self,selList):
        '''Sets the selection indices in selList as selected. Resets any previous
        selections for compatibility with wx.MultiChoiceDialog. Note that
        the state for only the filtered items is shown.

        :param list selList: indices of items to be selected. These indices
          are referenced to the order in self.ChoiceList
        '''
        self.Selections = len(self.ChoiceList) * [False,] # reset selections
        for sel in selList:
            self.Selections[sel] = True
        self._ShowSelections()

    def _ShowSelections(self):
        'Show the selection state for displayed items'
        self.clb.SetChecked(
            [i for i in range(len(self.filterlist)) if self.Selections[self.filterlist[i]]]
            ) # Note anything previously checked will be cleared.
            
    def _SetAll(self,event):
        'Set all viewed choices on'
        self.clb.SetChecked(range(0,len(self.filterlist),self.Stride))
        self.stride.SetValue('1')
        self.Stride = 1
        
    def _ToggleAll(self,event):
        'flip the state of all viewed choices'
        for i in range(len(self.filterlist)):
            self.clb.Check(i,not self.clb.IsChecked(i))
            
    def onChar(self,event):
        'Respond to keyboard events in the Filter box'
        self.OKbtn.Enable(False)
        if self.timer.IsRunning():
            self.timer.Stop()
        self.timer.Start(1000,oneShot=True)
        if event: event.Skip()
        
    def OnCheck(self,event):
        '''for CheckListBox events; if Set Range is in use, this sets/clears all
        entries in range between start and end according to the value in start.
        Repeated clicks on the start change the checkbox state, but do not trigger
        the range copy. 
        The caption next to the button is updated on the first button press.
        '''
        if self.settingRange:
            id = event.GetInt()
            if self.rangeFirst is None:
                name = self.clb.GetString(id)
                self.rangeCapt.SetLabel(name+' to...')
                self.rangeFirst = id
            elif self.rangeFirst == id:
                pass
            else:
                for i in range(min(self.rangeFirst,id), max(self.rangeFirst,id)+1,self.Stride):
                    self.clb.Check(i,self.clb.IsChecked(self.rangeFirst))
                self.rangeBut.SetValue(False)
                self.rangeCapt.SetLabel('')
            return
        
    def Filter(self,event):
        '''Read text from filter control and select entries that match. Called by
        Timer after a delay with no input or if Enter is pressed.
        '''
        if self.timer.IsRunning():
            self.timer.Stop()
        self.GetSelections() # record current selections
        txt = self.filterBox.GetValue()
        self.clb.Clear()
        
        self.Update()
        self.filterlist = []
        if txt:
            txt = txt.lower()
            ChoiceList = []
            for i,item in enumerate(self.ChoiceList):
                if item.lower().find(txt) != -1:
                    ChoiceList.append(item)
                    self.filterlist.append(i)
        else:
            self.filterlist = range(len(self.ChoiceList))
            ChoiceList = self.ChoiceList
        self.clb.AppendItems(ChoiceList)
        self._ShowSelections()
        self.OKbtn.Enable(True)

def SelectEdit1Var(G2frame,array,labelLst,elemKeysLst,dspLst,refFlgElem):
    '''Select a variable from a list, then edit it and select histograms
    to copy it to.

    :param wx.Frame G2frame: main GSAS-II frame
    :param dict array: the array (dict or list) where values to be edited are kept
    :param list labelLst: labels for each data item
    :param list elemKeysLst: a list of lists of keys needed to be applied (see below)
      to obtain the value of each parameter
    :param list dspLst: list list of digits to be displayed (10,4) is 10 digits
      with 4 decimal places. Can be None.
    :param list refFlgElem: a list of lists of keys needed to be applied (see below)
      to obtain the refine flag for each parameter or None if the parameter
      does not have refine flag.

    Example::
      array = data 
      labelLst = ['v1','v2']
      elemKeysLst = [['v1'], ['v2',0]]
      refFlgElem = [None, ['v2',1]]

     * The value for v1 will be in data['v1'] and this cannot be refined while,
     * The value for v2 will be in data['v2'][0] and its refinement flag is data['v2'][1]
    '''
    def unkey(dct,keylist):
        '''dive into a nested set of dicts/lists applying keys in keylist
        consecutively
        '''
        d = dct
        for k in keylist:
            d = d[k]
        return d

    def OnChoice(event):
        'Respond when a parameter is selected in the Choice box'
        if 'phoenix' in wx.version():
            valSizer.Clear(True)
        else:
            valSizer.DeleteWindows()
        lbl = event.GetString()
        copyopts['currentsel'] = lbl
        i = labelLst.index(lbl)
        OKbtn.Enable(True)
        ch.SetLabel(lbl)
        args = {}
        if dspLst[i]:
            args = {'nDig':dspLst[i]}
        Val = ValidatedTxtCtrl(
            dlg,
            unkey(array,elemKeysLst[i][:-1]),
            elemKeysLst[i][-1],
            **args)
        copyopts['startvalue'] = unkey(array,elemKeysLst[i])
        #unkey(array,elemKeysLst[i][:-1])[elemKeysLst[i][-1]] = 
        valSizer.Add(Val,0,wx.LEFT,5)
        dlg.SendSizeEvent()
        
    # SelectEdit1Var execution begins here
    saveArray = copy.deepcopy(array) # keep original values
    TreeItemType = G2frame.GPXtree.GetItemText(G2frame.PickId)
    copyopts = {'InTable':False,"startvalue":None,'currentsel':None}        
    hst = G2frame.GPXtree.GetItemText(G2frame.PatternId)
    histList = G2pdG.GetHistsLikeSelected(G2frame)
    if not histList:
        G2frame.ErrorDialog('No match','No histograms match '+hst,G2frame)
        return
    dlg = wx.Dialog(G2frame,wx.ID_ANY,'Set a parameter value',
        style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
    mainSizer = wx.BoxSizer(wx.VERTICAL)
    mainSizer.Add((5,5))
    subSizer = wx.BoxSizer(wx.HORIZONTAL)
    subSizer.Add((-1,-1),1,wx.EXPAND)
    subSizer.Add(wx.StaticText(dlg,wx.ID_ANY,'Select a parameter and set a new value'))
    subSizer.Add((-1,-1),1,wx.EXPAND)
    mainSizer.Add(subSizer,0,wx.EXPAND,0)
    mainSizer.Add((0,10))

    subSizer = wx.FlexGridSizer(0,2,5,0)
    subSizer.Add(wx.StaticText(dlg,wx.ID_ANY,'Parameter: '))
    ch = wx.Choice(dlg, wx.ID_ANY, choices = sorted(labelLst))
    ch.SetSelection(-1)
    ch.Bind(wx.EVT_CHOICE, OnChoice)
    subSizer.Add(ch)
    subSizer.Add(wx.StaticText(dlg,wx.ID_ANY,'Value: '))
    valSizer = wx.BoxSizer(wx.HORIZONTAL)
    subSizer.Add(valSizer)
    mainSizer.Add(subSizer)

    mainSizer.Add((-1,20))
    subSizer = wx.BoxSizer(wx.HORIZONTAL)
    subSizer.Add(G2CheckBox(dlg, 'Edit in table ', copyopts, 'InTable'))
    mainSizer.Add(subSizer)

    btnsizer = wx.StdDialogButtonSizer()
    OKbtn = wx.Button(dlg, wx.ID_OK,'Continue')
    OKbtn.Enable(False)
    OKbtn.SetDefault()
    OKbtn.Bind(wx.EVT_BUTTON,lambda event: dlg.EndModal(wx.ID_OK))
    btnsizer.AddButton(OKbtn)
    btn = wx.Button(dlg, wx.ID_CANCEL)
    btnsizer.AddButton(btn)
    btnsizer.Realize()
    mainSizer.Add((-1,5),1,wx.EXPAND,1)
    mainSizer.Add(btnsizer,0,wx.ALIGN_CENTER,0)
    mainSizer.Add((-1,10))

    dlg.SetSizer(mainSizer)
    dlg.CenterOnParent()
    if dlg.ShowModal() != wx.ID_OK:
        array.update(saveArray)
        dlg.Destroy()
        return
    dlg.Destroy()

    copyList = []
    lbl = copyopts['currentsel']
    dlg = G2MultiChoiceDialog(G2frame,'Copy parameter '+lbl+' from\n'+hst,
        'Copy parameters', histList)
    dlg.CenterOnParent()
    try:
        if dlg.ShowModal() == wx.ID_OK:
            for i in dlg.GetSelections(): 
                copyList.append(histList[i])
        else:
            # reset the parameter since cancel was pressed
            array.update(saveArray)
            return
    finally:
        dlg.Destroy()

    prelbl = [hst]
    i = labelLst.index(lbl)
    keyLst = elemKeysLst[i]
    refkeys = refFlgElem[i]
    dictlst = [unkey(array,keyLst[:-1])]
    if refkeys is not None:
        refdictlst = [unkey(array,refkeys[:-1])]
    else:
        refdictlst = None
    Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,hst)
    hstData = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id,'Instrument Parameters'))[0]
    for h in copyList:
        Id = G2gd.GetGPXtreeItemId(G2frame,G2frame.root,h)
        instData = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id,'Instrument Parameters'))[0]
        if len(hstData) != len(instData) or hstData['Type'][0] != instData['Type'][0]:  #don't mix data types or lam & lam1/lam2 parms!
            print (h+' not copied - instrument parameters not commensurate')
            continue
        hData = G2frame.GPXtree.GetItemPyData(G2gd.GetGPXtreeItemId(G2frame,Id,TreeItemType))
        if TreeItemType == 'Instrument Parameters':
            hData = hData[0]
        #copy the value if it is changed or we will not edit in a table
        valNow = unkey(array,keyLst)
        if copyopts['startvalue'] != valNow or not copyopts['InTable']:
            unkey(hData,keyLst[:-1])[keyLst[-1]] = valNow
        prelbl += [h]
        dictlst += [unkey(hData,keyLst[:-1])]
        if refdictlst is not None:
            refdictlst += [unkey(hData,refkeys[:-1])]
    if refdictlst is None:
        args = {}
    else:
        args = {'checkdictlst':refdictlst,
                'checkelemlst':len(dictlst)*[refkeys[-1]],
                'checklabel':'Refine?'}
    if copyopts['InTable']:
        dlg = ScrolledMultiEditor(
            G2frame,dictlst,
            len(dictlst)*[keyLst[-1]],prelbl,
            header='Editing parameter '+lbl,
            CopyButton=True,**args)
        dlg.CenterOnParent()
        if dlg.ShowModal() != wx.ID_OK:
            array.update(saveArray)
        dlg.Destroy()

################################################################        Single choice Dialog with filter options
class G2SingleChoiceDialog(wx.Dialog):
    '''A dialog similar to wx.SingleChoiceDialog except that a filter can be
    added.

    :param wx.Frame ParentFrame: reference to parent frame
    :param str title: heading above list of choices
    :param str header: Title to place on window frame 
    :param list ChoiceList: a list of choices where one will be selected
    :param bool monoFont: If False (default), use a variable-spaced font;
      if True use a equally-spaced font.
    :param bool filterBox: If True (default) an input widget is placed on
      the window and only entries matching the entered text are shown.
    :param kw: optional keyword parameters for the wx.Dialog may
      be included such as size [which defaults to `(320,310)`] and
      style (which defaults to ``wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.CENTRE | wx.OK | wx.CANCEL``);
      note that ``wx.OK`` and ``wx.CANCEL`` controls
      the presence of the eponymous buttons in the dialog.
    :returns: the name of the created dialog
    '''
    def __init__(self,parent, title, header, ChoiceList, 
                 monoFont=False, filterBox=True, **kw):
        # process keyword parameters, notably style
        options = {'size':(320,310), # default Frame keywords
                   'style':wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.CENTRE| wx.OK | wx.CANCEL,
                   }
        options.update(kw)
        self.ChoiceList = ChoiceList
        self.filterlist = range(len(self.ChoiceList))
        if options['style'] & wx.OK:
            useOK = True
            options['style'] ^= wx.OK
        else:
            useOK = False
        if options['style'] & wx.CANCEL:
            useCANCEL = True
            options['style'] ^= wx.CANCEL
        else:
            useCANCEL = False        
        # create the dialog frame
        wx.Dialog.__init__(self,parent,wx.ID_ANY,header,**options)
        # fill the dialog
        Sizer = wx.BoxSizer(wx.VERTICAL)
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        h = max(35,17*int(len(title)/26.+1)) # adjust height of title box with guessed # of lines
        topSizer.Add(
            wx.StaticText(self,wx.ID_ANY,title,size=(-1,h)),
            1,wx.ALL|wx.EXPAND|WACV,1)
        if filterBox:
            self.timer = wx.Timer()
            self.timer.Bind(wx.EVT_TIMER,self.Filter)
            topSizer.Add(wx.StaticText(self,wx.ID_ANY,'Filter: '),0,wx.ALL,1)
            self.filterBox = wx.TextCtrl(self, wx.ID_ANY, size=(80,-1),
                                         style=wx.TE_PROCESS_ENTER)
            self.filterBox.Bind(wx.EVT_CHAR,self.onChar)
            self.filterBox.Bind(wx.EVT_TEXT_ENTER,self.Filter)
            topSizer.Add(self.filterBox,0,wx.ALL,0)
        Sizer.Add(topSizer,0,wx.ALL|wx.EXPAND,8)
        self.clb = wx.ListBox(self, wx.ID_ANY, (30,30), wx.DefaultSize, ChoiceList)
        self.clb.Bind(wx.EVT_LEFT_DCLICK,self.onDoubleClick)
        if monoFont:
            font1 = wx.Font(self.clb.GetFont().GetPointSize(),
                            wx.MODERN, wx.NORMAL, wx.NORMAL, False)
            self.clb.SetFont(font1)
        Sizer.Add(self.clb,1,wx.LEFT|wx.RIGHT|wx.EXPAND,10)
        Sizer.Add((-1,10))
        # OK/Cancel buttons
        btnsizer = wx.StdDialogButtonSizer()
        if useOK:
            self.OKbtn = wx.Button(self, wx.ID_OK)
            self.OKbtn.SetDefault()
            btnsizer.AddButton(self.OKbtn)
        if useCANCEL:
            btn = wx.Button(self, wx.ID_CANCEL)
            btnsizer.AddButton(btn)
        btnsizer.Realize()
        Sizer.Add((-1,5))
        Sizer.Add(btnsizer,0,wx.ALIGN_RIGHT,50)
        Sizer.Add((-1,20))
        # OK done, let's get outa here
        self.SetSizer(Sizer)
    def GetSelection(self):
        'Returns the index of the selected choice'
        i = self.clb.GetSelection()
        if i < 0 or i >= len(self.filterlist):
            return wx.NOT_FOUND
        return self.filterlist[i]
    def onChar(self,event):
        self.OKbtn.Enable(False)
        if self.timer.IsRunning():
            self.timer.Stop()
        self.timer.Start(1000,oneShot=True)
        if event: event.Skip()
    def Filter(self,event):
        if self.timer.IsRunning():
            self.timer.Stop()
        txt = self.filterBox.GetValue()
        self.clb.Clear()
        self.Update()
        self.filterlist = []
        if txt:
            txt = txt.lower()
            ChoiceList = []
            for i,item in enumerate(self.ChoiceList):
                if item.lower().find(txt) != -1:
                    ChoiceList.append(item)
                    self.filterlist.append(i)
        else:
            self.filterlist = range(len(self.ChoiceList))
            ChoiceList = self.ChoiceList
        self.clb.AppendItems(ChoiceList)
        self.OKbtn.Enable(True)
    def onDoubleClick(self,event):
        self.EndModal(wx.ID_OK)
        
################################################################################
class FlagSetDialog(wx.Dialog):
    ''' Creates popup with table of variables to be checked for e.g. refinement flags
    '''
    def __init__(self,parent,title,colnames,rownames,flags):
        wx.Dialog.__init__(self,parent,-1,title,
            pos=wx.DefaultPosition,style=wx.DEFAULT_DIALOG_STYLE)
        self.panel = None
        self.colnames = colnames
        self.rownames = rownames
        self.flags = flags
        self.newflags = copy.copy(flags)
        self.Draw()
        
    def Draw(self):
        Indx = {}
        
        def OnSelection(event):
            Obj = event.GetEventObject()
            [name,ia] = Indx[Obj.GetId()]
            self.newflags[name][ia] = Obj.GetValue()
            
        if self.panel:
            self.panel.DestroyChildren()  #safe: wx.Panel
            self.panel.Destroy()
        self.panel = wx.Panel(self)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        flagSizer = wx.FlexGridSizer(0,len(self.colnames),5,5)
        for item in self.colnames:
            flagSizer.Add(wx.StaticText(self.panel,label=item),0,WACV)
        for ia,atm in enumerate(self.rownames):
            flagSizer.Add(wx.StaticText(self.panel,label=atm),0,WACV)
            for name in self.colnames[1:]:
                if self.flags[name][ia]:
                    self.newflags[name][ia] = False     #default is off
                    flg = wx.CheckBox(self.panel,-1,label='')
                    flg.Bind(wx.EVT_CHECKBOX,OnSelection)
                    Indx[flg.GetId()] = [name,ia]
                    flagSizer.Add(flg,0,WACV)
                else:
                    flagSizer.Add(wx.StaticText(self.panel,label='na'),0,WACV)
            
        mainSizer.Add(flagSizer,0)
        OkBtn = wx.Button(self.panel,-1,"Ok")
        OkBtn.Bind(wx.EVT_BUTTON, self.OnOk)
        CancelBtn = wx.Button(self.panel,-1,'Cancel')
        CancelBtn.Bind(wx.EVT_BUTTON, self.OnCancel)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20),1)
        btnSizer.Add(OkBtn)
        btnSizer.Add(CancelBtn)
        btnSizer.Add((20,20),1)
        mainSizer.Add(btnSizer,0,wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        self.panel.SetSizer(mainSizer)
        self.panel.Fit()
        self.Fit()
        
    def GetSelection(self):
        return self.newflags

    def OnOk(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_OK)              
        
    def OnCancel(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_CANCEL)

###################################################################,#############
def G2MessageBox(parent,msg,title='Error'):
    '''Simple code to display a error or warning message
    '''
    dlg = wx.MessageDialog(parent,StripIndents(msg), title, wx.OK)
    dlg.ShowModal()
    dlg.Destroy()
    
################################################################################
class PickTwoDialog(wx.Dialog):
    '''This does not seem to be in use
    '''
    def __init__(self,parent,title,prompt,names,choices):
        wx.Dialog.__init__(self,parent,-1,title, 
            pos=wx.DefaultPosition,style=wx.DEFAULT_DIALOG_STYLE)
        self.panel = None
        self.prompt = prompt
        self.choices = choices
        self.names = names
        self.Draw()

    def Draw(self):
        Indx = {}
        
        def OnSelection(event):
            Obj = event.GetEventObject()
            id = Indx[Obj.GetId()]
            self.choices[id] = Obj.GetValue().encode()  #to avoid Unicode versions
            self.Draw()
            
        if self.panel:
            self.panel.DestroyChildren()  #safe: wx.Panel
            self.panel.Destroy()
        self.panel = wx.Panel(self)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(wx.StaticText(self.panel,-1,self.prompt),0,wx.ALIGN_CENTER)
        for isel,name in enumerate(self.choices):
            lineSizer = wx.BoxSizer(wx.HORIZONTAL)
            lineSizer.Add(wx.StaticText(self.panel,-1,'Reference atom '+str(isel+1)),0,wx.ALIGN_CENTER)
            nameList = self.names[:]
            if isel:
                if self.choices[0] in nameList:
                    nameList.remove(self.choices[0])
            choice = wx.ComboBox(self.panel,-1,value=name,choices=nameList,
                style=wx.CB_READONLY|wx.CB_DROPDOWN)
            Indx[choice.GetId()] = isel
            choice.Bind(wx.EVT_COMBOBOX, OnSelection)
            lineSizer.Add(choice,0,WACV)
            mainSizer.Add(lineSizer)
        OkBtn = wx.Button(self.panel,-1,"Ok")
        OkBtn.Bind(wx.EVT_BUTTON, self.OnOk)
        CancelBtn = wx.Button(self.panel,-1,'Cancel')
        CancelBtn.Bind(wx.EVT_BUTTON, self.OnCancel)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20),1)
        btnSizer.Add(OkBtn)
        btnSizer.Add(CancelBtn)
        btnSizer.Add((20,20),1)
        mainSizer.Add(btnSizer,0,wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        self.panel.SetSizer(mainSizer)
        self.panel.Fit()
        self.Fit()
        
    def GetSelection(self):
        return self.choices

    def OnOk(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_OK)              
        
    def OnCancel(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_CANCEL)

################################################################################
class SingleFloatDialog(wx.Dialog):
    '''Dialog to obtain a single float value from user

    :param wx.Frame parent: name of parent frame
    :param str title: title string for dialog
    :param str prompt: string to tell user what they are inputing
    :param str value: default input value, if any
    :param list limits: upper and lower value used to set bounds for entry, use [None,None]
      for no bounds checking, [None,val] for only upper bounds, etc. Default is [0,1].
      Values outside of limits will be ignored.
    :param str format: string to format numbers. Defaults to '%.5g'. Use '%d' to have
      integer input (but dlg.GetValue will still return a float). 
    
    Typical usage::

            limits = (0,1)
            dlg = G2G.SingleFloatDialog(G2frame,'New value','Enter new value for...',default,limits)
            if dlg.ShowModal() == wx.ID_OK:
                parm = dlg.GetValue()
            dlg.Destroy()    

    '''
    # TODO: better to generalize this for int & float, use validated text control, OK as default.
    # then make SingleFloatDialog & SingleIntDialog as wrappers. Would be good to remove the %-style
    # format, too. 
    def __init__(self,parent,title,prompt,value,limits=[0.,1.],format='%.5g'):
        wx.Dialog.__init__(self,parent,-1,title, 
            pos=wx.DefaultPosition,style=wx.DEFAULT_DIALOG_STYLE)
        self.panel = None
        self.limits = limits
        self.value = value
        self.prompt = prompt
        self.format = format
        self.Draw()
        
    def Draw(self):
        
        def OnValItem(event):
            if event: event.Skip()
            try:
                val = float(valItem.GetValue())
                if self.limits[0] is not None and val < self.limits[0]:
                    raise ValueError
                if self.limits[1] is not None and val > self.limits[1]:
                    raise ValueError
            except ValueError:
                val = self.value
            self.value = val
            valItem.SetValue(self.format%(self.value))
            
        if self.panel: self.panel.Destroy()
        self.panel = wx.Panel(self)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(wx.StaticText(self.panel,-1,self.prompt),0,wx.ALIGN_CENTER)
        valItem = wx.TextCtrl(self.panel,-1,value=self.format%(self.value),style=wx.TE_PROCESS_ENTER)
        mainSizer.Add(valItem,0,wx.ALIGN_CENTER)
        valItem.Bind(wx.EVT_TEXT_ENTER,OnValItem)
        valItem.Bind(wx.EVT_KILL_FOCUS,OnValItem)
        OkBtn = wx.Button(self.panel,-1,"Ok")
        OkBtn.Bind(wx.EVT_BUTTON, self.OnOk)
        CancelBtn = wx.Button(self.panel,-1,'Cancel')
        CancelBtn.Bind(wx.EVT_BUTTON, self.OnCancel)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20),1)
        btnSizer.Add(OkBtn)
        btnSizer.Add(CancelBtn)
        btnSizer.Add((20,20),1)
        mainSizer.Add(btnSizer,0,wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        self.panel.SetSizer(mainSizer)
        self.panel.Fit()
        self.Fit()

    def GetValue(self):
        return self.value
        
    def OnOk(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_OK)              
        
    def OnCancel(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_CANCEL)

class SingleIntDialog(SingleFloatDialog):
    '''Dialog to obtain a single int value from user

    :param wx.Frame parent: name of parent frame
    :param str title: title string for dialog
    :param str prompt: string to tell user what they are inputing
    :param str value: default input value, if any
    :param list limits: upper and lower value used to set bounds for entries. Default
      is [None,None] -- for no bounds checking; use [None,val] for only upper bounds, etc.
      Default is [0,1]. Values outside of limits will be ignored.
    
    Typical usage::

            limits = (0,None)  # allows zero or positive values only
            dlg = G2G.SingleIntDialog(G2frame,'New value','Enter new value for...',default,limits)
            if dlg.ShowModal() == wx.ID_OK:
                parm = dlg.GetValue()
            dlg.Destroy()    

    '''
    def __init__(self,parent,title,prompt,value,limits=[None,None]):
        SingleFloatDialog.__init__(self,parent,title,prompt,value,limits=limits,format='%d')
    def GetValue(self):
        return int(self.value)

################################################################################
class MultiFloatDialog(wx.Dialog):
    'Dialog to obtain a multi float value from user'
    def __init__(self,parent,title,prompts,values,limits=[[0.,1.],],formats=['%.5g',]):
        wx.Dialog.__init__(self,parent,-1,title, 
            pos=wx.DefaultPosition,style=wx.DEFAULT_DIALOG_STYLE)
        self.panel = None
        self.limits = limits
        self.values = values
        self.prompts = prompts
        self.formats = formats
        self.Draw()
        
    def Draw(self):
        
        def OnValItem(event):
            if event: event.Skip()
            Obj = event.GetEventObject()
            id,limits,format = Indx[Obj]
            try:
                val = float(Obj.GetValue())
                if val < limits[0] or val > limits[1]:
                    raise ValueError
            except ValueError:
                val = self.values[id]
            self.values[id] = val
            Obj.SetValue(format%(val))
            
        Indx = {}
        if self.panel: self.panel.Destroy()
        self.panel = wx.Panel(self)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        lineSizer = wx.FlexGridSizer(0,2,5,5)
        for id,[prompt,value,limits,format] in enumerate(zip(self.prompts,self.values,self.limits,self.formats)):
            lineSizer.Add(wx.StaticText(self.panel,label=prompt),0,wx.ALIGN_CENTER)
            valItem = wx.TextCtrl(self.panel,value=format%(value),style=wx.TE_PROCESS_ENTER)
            Indx[valItem] = [id,limits,format]
            lineSizer.Add(valItem,0,wx.ALIGN_CENTER)
            valItem.Bind(wx.EVT_TEXT_ENTER,OnValItem)
            valItem.Bind(wx.EVT_KILL_FOCUS,OnValItem)
        mainSizer.Add(lineSizer)
        OkBtn = wx.Button(self.panel,-1,"Ok")
        OkBtn.Bind(wx.EVT_BUTTON, self.OnOk)
        CancelBtn = wx.Button(self.panel,-1,'Cancel')
        CancelBtn.Bind(wx.EVT_BUTTON, self.OnCancel)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20),1)
        btnSizer.Add(OkBtn)
        btnSizer.Add(CancelBtn)
        btnSizer.Add((20,20),1)
        mainSizer.Add(btnSizer,0,wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        self.panel.SetSizer(mainSizer)
        self.panel.Fit()
        self.Fit()

    def GetValues(self):
        return self.values
        
    def OnOk(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_OK)              
        
    def OnCancel(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_CANCEL)

################################################################################
class SingleStringDialog(wx.Dialog):
    '''Dialog to obtain a single string value from user
    
    :param wx.Frame parent: name of parent frame
    :param str title: title string for dialog
    :param str prompt: string to tell use what they are inputting
    :param str value: default input value, if any
    '''
    def __init__(self,parent,title,prompt,value='',size=(200,-1),help=''):
        wx.Dialog.__init__(self,parent,wx.ID_ANY,title,pos=wx.DefaultPosition,
            style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.value = value
        self.prompt = prompt
        self.CenterOnParent()
        self.panel = wx.Panel(self)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(wx.StaticText(self.panel,-1,self.prompt),0,wx.ALIGN_CENTER)
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.valItem = wx.TextCtrl(self.panel,-1,value=self.value,size=size)
        sizer1.Add(self.valItem,0,wx.ALIGN_CENTER)
        if help:
            sizer1.Add(HelpButton(self.panel,help),0,wx.ALIGN_RIGHT|wx.ALL)
        mainSizer.Add(sizer1,0,wx.ALIGN_CENTER)
        btnsizer = wx.StdDialogButtonSizer()
        OKbtn = wx.Button(self.panel, wx.ID_OK)
        OKbtn.SetDefault()
        btnsizer.AddButton(OKbtn)
        btn = wx.Button(self.panel, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()
        mainSizer.Add(btnsizer,0,wx.ALIGN_CENTER)
        self.panel.SetSizer(mainSizer)
        self.panel.Fit()
        self.Fit()

    def Show(self):
        '''Use this method after creating the dialog to post it
        :returns: True if the user pressed OK; False if the User pressed Cancel
        '''
        if self.ShowModal() == wx.ID_OK:
            self.value = self.valItem.GetValue()
            return True
        else:
            return False

    def GetValue(self):
        '''Use this method to get the value entered by the user
        :returns: string entered by user
        '''
        return self.value

################################################################################
class MultiStringDialog(wx.Dialog):
    '''Dialog to obtain a multi string values from user
    
    :param wx.Frame parent: name of parent frame
    :param str title: title string for dialog
    :param str prompts: strings to tell use what they are inputting
    :param str values: default input values, if any
    :param int size: length of the input box in pixels
    '''
    def __init__(self,parent,title,prompts,values=[],size=-1):
        
        wx.Dialog.__init__(self,parent,wx.ID_ANY,title, 
                           pos=wx.DefaultPosition,
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.values = values
        self.prompts = prompts
        self.CenterOnParent()
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        promptSizer = wx.FlexGridSizer(0,2,5,5)
        self.Indx = {}
        for prompt,value in zip(prompts,values):
            promptSizer.Add(wx.StaticText(self,-1,prompt),0,WACV)
            valItem = wx.TextCtrl(self,-1,value=value,style=wx.TE_PROCESS_ENTER,size=(size,-1))
            self.Indx[valItem.GetId()] = prompt
            valItem.Bind(wx.EVT_TEXT,self.newValue)
            promptSizer.Add(valItem,1,WACV|wx.EXPAND,1)
        mainSizer.Add(promptSizer,1,wx.ALL|wx.EXPAND,1)
        btnsizer = wx.StdDialogButtonSizer()
        OKbtn = wx.Button(self, wx.ID_OK)
        OKbtn.SetDefault()
        btnsizer.AddButton(OKbtn)
        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()
        mainSizer.Add(btnsizer,0,wx.ALIGN_CENTER)
        self.SetSizer(mainSizer)
        self.Fit()
        
    def newValue(self,event):
        Obj = event.GetEventObject()
        item = self.Indx[Obj.GetId()]
        id = self.prompts.index(item)
        self.values[id] = Obj.GetValue()

    def Show(self):
        '''Use this method after creating the dialog to post it
        :returns: True if the user pressed OK; False if the User pressed Cancel
        '''
        if self.ShowModal() == wx.ID_OK:
            return True
        else:
            return False

    def GetValues(self):
        '''Use this method to get the value entered by the user
        :returns: string entered by user
        '''
        return self.values

################################################################################
class G2ColumnIDDialog(wx.Dialog):
    '''A dialog for matching column data to desired items; some columns may be ignored.
    
    :param wx.Frame ParentFrame: reference to parent frame
    :param str title: heading above list of choices
    :param str header: Title to place on window frame 
    :param list ChoiceList: a list of possible choices for the columns
    :param list ColumnData: lists of column data to be matched with ChoiceList
    :param bool monoFont: If False (default), use a variable-spaced font;
      if True use a equally-spaced font.
    :param kw: optional keyword parameters for the wx.Dialog may
      be included such as size [which defaults to `(320,310)`] and
      style (which defaults to ``wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.CENTRE | wx.OK | wx.CANCEL``);
      note that ``wx.OK`` and ``wx.CANCEL`` controls
      the presence of the eponymous buttons in the dialog.
    :returns: the name of the created dialog
    
    '''

    def __init__(self,parent, title, header,Comments,ChoiceList, ColumnData,
                 monoFont=False, **kw):

        def OnOk(sevent):
            OK = True
            selCols = []
            for col in self.sel:
                item = col.GetValue()
                if item != ' ' and item in selCols:
                    OK = False
                    break
                else:
                    selCols.append(item)
            parent = self.GetParent()
            if not OK:
                parent.ErrorDialog('Duplicate',item+' selected more than once')
                return
            parent.Raise()
            self.EndModal(wx.ID_OK)
            
        def OnModify(event):
            if event: event.Skip()
            Obj = event.GetEventObject()
            icol,colData = Indx[Obj.GetId()]
            modify = Obj.GetValue()
            if not modify:
                return
            #print 'Modify column',icol,' by', modify
            for i,item in enumerate(self.ColumnData[icol]):
                self.ColumnData[icol][i] = str(eval(item+modify))
            colData.SetValue('\n'.join(self.ColumnData[icol]))
            Obj.SetValue('')
            
        # process keyword parameters, notably style
        options = {'size':(600,310), # default Frame keywords
                   'style':wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.CENTRE| wx.OK | wx.CANCEL,
                   }
        options.update(kw)
        self.Comments = ''.join(Comments)
        self.ChoiceList = ChoiceList
        self.ColumnData = ColumnData
        nCol = len(ColumnData)
        if options['style'] & wx.OK:
            useOK = True
            options['style'] ^= wx.OK
        else:
            useOK = False
        if options['style'] & wx.CANCEL:
            useCANCEL = True
            options['style'] ^= wx.CANCEL
        else:
            useCANCEL = False        
        # create the dialog frame
        wx.Dialog.__init__(self,parent,wx.ID_ANY,header,**options)
        panel = wxscroll.ScrolledPanel(self)
        # fill the dialog
        Sizer = wx.BoxSizer(wx.VERTICAL)
        Sizer.Add((-1,5))
        Sizer.Add(wx.StaticText(panel,label=title),0,WACV)
        if self.Comments:
            Sizer.Add(wx.StaticText(panel,label=' Header lines:'),0,WACV)
            Sizer.Add(wx.TextCtrl(panel,value=self.Comments,size=(200,-1),
                style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_DONTWRAP),0,wx.ALL|wx.EXPAND|WACV,8)
        columnsSizer = wx.FlexGridSizer(0,nCol,5,10)
        self.sel = []
        self.mod = []
        Indx = {}
        for icol,col in enumerate(self.ColumnData):
            colSizer = wx.BoxSizer(wx.VERTICAL)
            colSizer.Add(wx.StaticText(panel,label=' Column #%d Select:'%(icol)),0,WACV)
            self.sel.append(wx.ComboBox(panel,value=' ',choices=self.ChoiceList,style=wx.CB_READONLY|wx.CB_DROPDOWN))
            colSizer.Add(self.sel[-1])
            colData = wx.TextCtrl(panel,value='\n'.join(self.ColumnData[icol]),size=(120,-1),
                style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_DONTWRAP)
            colSizer.Add(colData,0,WACV)
            colSizer.Add(wx.StaticText(panel,label=' Modify by:'),0,WACV)
            mod = wx.TextCtrl(panel,size=(120,-1),value='',style=wx.TE_PROCESS_ENTER)
            mod.Bind(wx.EVT_TEXT_ENTER,OnModify)
            mod.Bind(wx.EVT_KILL_FOCUS,OnModify)
            Indx[mod.GetId()] = [icol,colData]
            colSizer.Add(mod,0,WACV)
            columnsSizer.Add(colSizer)
        Sizer.Add(columnsSizer)
        Sizer.Add(wx.StaticText(panel,label=' For modify by, enter arithmetic string eg. "-12345.67". "+","-","*","/","**" all allowed'),0,WACV) 
        Sizer.Add((-1,10))
        # OK/Cancel buttons
        btnsizer = wx.StdDialogButtonSizer()
        if useOK:
            self.OKbtn = wx.Button(panel, wx.ID_OK)
            self.OKbtn.SetDefault()
            btnsizer.AddButton(self.OKbtn)
            self.OKbtn.Bind(wx.EVT_BUTTON, OnOk)
        if useCANCEL:
            btn = wx.Button(panel, wx.ID_CANCEL)
            btnsizer.AddButton(btn)
        btnsizer.Realize()
        Sizer.Add((-1,5))
        Sizer.Add(btnsizer,0,wx.ALIGN_LEFT,20)
        Sizer.Add((-1,5))
        # OK done, let's get outa here
        panel.SetSizer(Sizer)
        panel.SetAutoLayout(1)
        panel.SetupScrolling()
        Size = [450,375]
        panel.SetSize(Size)
        Size[0] += 25; Size[1]+= 25
        self.SetSize(Size)
        
    def GetSelection(self):
        'Returns the selected sample parm for each column'
        selCols = []
        for item in self.sel:
            selCols.append(item.GetValue())
        return selCols,self.ColumnData
    
################################################################################
class G2HistoDataDialog(wx.Dialog):
    '''A dialog for editing histogram data globally.
    
    :param wx.Frame ParentFrame: reference to parent frame
    :param str title: heading above list of choices
    :param str header: Title to place on window frame 
    :param list ParmList: a list of names for the columns
    :param list ParmFmt: a list of formatting strings for the columns
    :param list: HistoList: a list of histogram names
    :param list ParmData: a list of lists of data matched to ParmList; one for each item in HistoList
    :param bool monoFont: If False (default), use a variable-spaced font;
      if True use a equally-spaced font.
    :param kw: optional keyword parameters for the wx.Dialog may
      be included such as size [which defaults to `(320,310)`] and
      style (which defaults to 
      ``wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.CENTRE | wx.OK | wx.CANCEL``);
      note that ``wx.OK`` and ``wx.CANCEL`` controls the presence of the eponymous buttons in the dialog.
    :returns: the modified ParmData
    
    '''

    def __init__(self,parent, title, header,ParmList,ParmFmt,HistoList,ParmData,
                 monoFont=False, **kw):

        def OnOk(sevent):
            parent.Raise()
            self.EndModal(wx.ID_OK)
            
        def OnModify(event):
            Obj = event.GetEventObject()
            irow,it = Indx[Obj.GetId()]
            try:
                val = float(Obj.GetValue())
            except ValueError:
                val = self.ParmData[irow][it]
            self.ParmData[irow][it] = val
            Obj.SetValue(self.ParmFmt[it]%val)
                        
        # process keyword parameters, notably style
        options = {'size':(600,310), # default Frame keywords
                   'style':wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.CENTRE| wx.OK | wx.CANCEL,
                   }
        options.update(kw)
        self.ParmList = ParmList
        self.ParmFmt = ParmFmt
        self.HistoList = HistoList
        self.ParmData = ParmData
        nCol = len(ParmList)
        if options['style'] & wx.OK:
            useOK = True
            options['style'] ^= wx.OK
        else:
            useOK = False
        if options['style'] & wx.CANCEL:
            useCANCEL = True
            options['style'] ^= wx.CANCEL
        else:
            useCANCEL = False        
        # create the dialog frame
        wx.Dialog.__init__(self,parent,wx.ID_ANY,header,**options)
        panel = wxscroll.ScrolledPanel(self)
        # fill the dialog
        Sizer = wx.BoxSizer(wx.VERTICAL)
        Sizer.Add((-1,5))
        Sizer.Add(wx.StaticText(panel,label=title),0,WACV)
        dataSizer = wx.FlexGridSizer(0,nCol+1,0,0)
        self.sel = []
        self.mod = []
        Indx = {}
        for item in ['Histogram',]+self.ParmList:
            dataSizer.Add(wx.StaticText(panel,-1,label=' %10s '%(item)),0,WACV)
        for irow,name in enumerate(self.HistoList):
            dataSizer.Add(wx.StaticText(panel,label=name),0,WACV|wx.LEFT|wx.RIGHT,10)
            for it,item in enumerate(self.ParmData[irow]):
                dat = wx.TextCtrl(panel,-1,value=self.ParmFmt[it]%(item),style=wx.TE_PROCESS_ENTER)
                dataSizer.Add(dat,0,WACV)
                dat.Bind(wx.EVT_TEXT_ENTER,OnModify)
                dat.Bind(wx.EVT_KILL_FOCUS,OnModify)
                Indx[dat.GetId()] = [irow,it]
        Sizer.Add(dataSizer)
        Sizer.Add((-1,10))
        # OK/Cancel buttons
        btnsizer = wx.StdDialogButtonSizer()
        if useOK:
            self.OKbtn = wx.Button(panel, wx.ID_OK)
            self.OKbtn.SetDefault()
            btnsizer.AddButton(self.OKbtn)
            self.OKbtn.Bind(wx.EVT_BUTTON, OnOk)
        if useCANCEL:
            btn = wx.Button(panel, wx.ID_CANCEL)
            btnsizer.AddButton(btn)
        btnsizer.Realize()
        Sizer.Add((-1,5))
        Sizer.Add(btnsizer,0,wx.ALIGN_LEFT,20)
        Sizer.Add((-1,5))
        # OK done, let's get outa here
        panel.SetSizer(Sizer)
        panel.SetAutoLayout(1)
        panel.SetupScrolling()
        Size = [450,375]
        panel.SetSize(Size)
        Size[0] += 25; Size[1]+= 25
        self.SetSize(Size)
        
    def GetData(self):
        'Returns the modified ParmData'
        return self.ParmData
    
################################################################################
def ItemSelector(ChoiceList, ParentFrame=None,
                 title='Select an item',
                 size=None, header='Item Selector',
                 useCancel=True,multiple=False):
    ''' Provide a wx dialog to select a single item or multiple items from list of choices

    :param list ChoiceList: a list of choices where one will be selected
    :param wx.Frame ParentFrame: Name of parent frame (default None)
    :param str title: heading above list of choices (default 'Select an item')
    :param wx.Size size: Size for dialog to be created (default None -- size as needed)
    :param str header: Title to place on window frame (default 'Item Selector')
    :param bool useCancel: If True (default) both the OK and Cancel buttons are offered
    :param bool multiple: If True then multiple items can be selected (default False)
    
    :returns: the selection index or None or a selection list if multiple is true

    Called by GSASIIdataGUI.OnReOrgSelSeq() Which is not fully implemented. 
    '''
    if multiple:
        if useCancel:
            dlg = G2MultiChoiceDialog(
                ParentFrame,title, header, ChoiceList)
        else:
            dlg = G2MultiChoiceDialog(
                ParentFrame,title, header, ChoiceList,
                style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.OK|wx.CENTRE)
    else:
        if useCancel:
            dlg = wx.SingleChoiceDialog(
                ParentFrame,title, header, ChoiceList)
        else:
            dlg = wx.SingleChoiceDialog(
                ParentFrame,title, header,ChoiceList,
                style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.OK|wx.CENTRE)
    if size: dlg.SetSize(size)
    if dlg.ShowModal() == wx.ID_OK:
        if multiple:
            dlg.Destroy()
            return dlg.GetSelections()
        else:
            dlg.Destroy()
            return dlg.GetSelection()
    else:
        dlg.Destroy()
        return None
    dlg.Destroy()

######################################################### Column-order selection dialog
def GetItemOrder(parent,keylist,vallookup,posdict):
    '''Creates a panel where items can be ordered into columns
    
    :param list keylist: is a list of keys for column assignments
    :param dict vallookup: is a dict keyed by names in keylist where each item is a dict. 
       Each inner dict contains variable names as keys and their associated values 
    :param dict posdict: is a dict keyed by names in keylist where each item is a dict. 
       Each inner dict contains column numbers as keys and their associated
       variable name as a value. This is used for both input and output.
       
    '''
    dlg = wx.Dialog(parent,style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
    sizer = wx.BoxSizer(wx.VERTICAL)
    spanel = OrderBox(dlg,keylist,vallookup,posdict)
    spanel.Fit()
    sizer.Add(spanel,1,wx.EXPAND)
    btnsizer = wx.StdDialogButtonSizer()
    btn = wx.Button(dlg, wx.ID_OK)
    btn.SetDefault()
    btnsizer.AddButton(btn)
    #btn = wx.Button(dlg, wx.ID_CANCEL)
    #btnsizer.AddButton(btn)
    btnsizer.Realize()
    sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.EXPAND|wx.ALL, 5)
    dlg.SetSizer(sizer)
    sizer.Fit(dlg)
    dlg.ShowModal()

################################################################################
class MultiIntegerDialog(wx.Dialog):
    '''Input a series of integers based on prompts
    '''
    def __init__(self,parent,title,prompts,values):
        wx.Dialog.__init__(self,parent,-1,title, 
            pos=wx.DefaultPosition,style=wx.DEFAULT_DIALOG_STYLE)
        self.panel = wx.Panel(self)         #just a dummy - gets destroyed in Draw!
        self.values = values
        self.prompts = prompts
        self.Draw()
        
    def Draw(self):
        
        def OnValItem(event):
            event.Skip()
            Obj = event.GetEventObject()
            ind = Indx[Obj.GetId()]
            try:
                val = int(Obj.GetValue())
                if val <= 0:
                    raise ValueError
            except ValueError:
                val = self.values[ind]
            self.values[ind] = val
            Obj.SetValue('%d'%(val))
            
        self.panel.Destroy()
        self.panel = wx.Panel(self)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        Indx = {}
        for ival,[prompt,value] in enumerate(zip(self.prompts,self.values)):
            mainSizer.Add(wx.StaticText(self.panel,-1,prompt),0,wx.ALIGN_CENTER)
            valItem = wx.TextCtrl(self.panel,-1,value='%d'%(value),style=wx.TE_PROCESS_ENTER)
            mainSizer.Add(valItem,0,wx.ALIGN_CENTER)
            Indx[valItem.GetId()] = ival
            valItem.Bind(wx.EVT_TEXT_ENTER,OnValItem)
            valItem.Bind(wx.EVT_KILL_FOCUS,OnValItem)
        OkBtn = wx.Button(self.panel,-1,"Ok")
        OkBtn.Bind(wx.EVT_BUTTON, self.OnOk)
        CancelBtn = wx.Button(self.panel,-1,'Cancel')
        CancelBtn.Bind(wx.EVT_BUTTON, self.OnCancel)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.Add((20,20),1)
        btnSizer.Add(OkBtn)
        btnSizer.Add(CancelBtn)
        btnSizer.Add((20,20),1)
        mainSizer.Add(btnSizer,0,wx.EXPAND|wx.BOTTOM|wx.TOP, 10)
        self.panel.SetSizer(mainSizer)
        self.panel.Fit()
        self.Fit()

    def GetValues(self):
        return self.values
        
    def OnOk(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_OK)              
        
    def OnCancel(self,event):
        parent = self.GetParent()
        parent.Raise()
        self.EndModal(wx.ID_CANCEL)

################################################################################
class OrderBox(wxscroll.ScrolledPanel):
    '''Creates a panel with scrollbars where items can be ordered into columns
    
    :param list keylist: is a list of keys for column assignments
    :param dict vallookup: is a dict keyed by names in keylist where each item is a dict. 
      Each inner dict contains variable names as keys and their associated values 
    :param dict posdict: is a dict keyed by names in keylist where each item is a dict. 
      Each inner dict contains column numbers as keys and their associated
      variable name as a value. This is used for both input and output.
      
    '''
    def __init__(self,parent,keylist,vallookup,posdict,*arg,**kw):
        self.keylist = keylist
        self.vallookup = vallookup
        self.posdict = posdict
        self.maxcol = 0
        for nam in keylist:
            posdict = self.posdict[nam]
            if posdict.keys():
                self.maxcol = max(self.maxcol, max(posdict))
        wxscroll.ScrolledPanel.__init__(self,parent,wx.ID_ANY,*arg,**kw)
        self.GBsizer = wx.GridBagSizer(4,4)
        self.SetBackgroundColour(WHITE)
        self.SetSizer(self.GBsizer)
        colList = [str(i) for i in range(self.maxcol+2)]
        for i in range(self.maxcol+1):
            wid = wx.StaticText(self,wx.ID_ANY,str(i),style=wx.ALIGN_CENTER)
            wid.SetBackgroundColour(DULL_YELLOW)
            wid.SetMinSize((50,-1))
            self.GBsizer.Add(wid,(0,i),flag=wx.ALIGN_CENTER|wx.EXPAND)
        self.chceDict = {}
        for row,nam in enumerate(self.keylist):
            posdict = self.posdict[nam]
            for col in posdict:
                lbl = posdict[col]
                pnl = wx.Panel(self,wx.ID_ANY)
                pnl.SetBackgroundColour(VERY_LIGHT_GREY)
                insize = wx.BoxSizer(wx.VERTICAL)
                wid = wx.Choice(pnl,wx.ID_ANY,choices=colList)
                insize.Add(wid,0,wx.EXPAND|wx.BOTTOM,3)
                wid.SetSelection(col)
                self.chceDict[wid] = (row,col)
                wid.Bind(wx.EVT_CHOICE,self.OnChoice)
                wid = wx.StaticText(pnl,wx.ID_ANY,lbl)
                insize.Add(wid,0,flag=wx.EXPAND)
                try:
                    val = G2py3.FormatSigFigs(self.vallookup[nam][lbl],maxdigits=8)
                except KeyError:
                    val = '?'
                wid = wx.StaticText(pnl,wx.ID_ANY,'('+val+')')
                insize.Add(wid,0,flag=wx.EXPAND)
                pnl.SetSizer(insize)
                self.GBsizer.Add(pnl,(row+1,col),flag=wx.EXPAND)
        self.SetAutoLayout(1)
        self.SetupScrolling()
        self.SetMinSize((
            min(700,self.GBsizer.GetSize()[0]),
            self.GBsizer.GetSize()[1]+20))
    def OnChoice(self,event):
        '''Called when a column is assigned to a variable
        '''
        row,col = self.chceDict[event.EventObject] # which variable was this?
        newcol = event.Selection # where will it be moved?
        if newcol == col:
            return # no change: nothing to do!
        prevmaxcol = self.maxcol # save current table size
        key = self.keylist[row] # get the key for the current row
        lbl = self.posdict[key][col] # selected variable name
        lbl1 = self.posdict[key].get(col+1,'') # next variable name, if any
        # if a posXXX variable is selected, and the next variable is posXXX, move them together
        repeat = 1
        if lbl[:3] == 'pos' and lbl1[:3] == 'int' and lbl[3:] == lbl1[3:]:
            repeat = 2
        for i in range(repeat): # process the posXXX and then the intXXX (or a single variable)
            col += i
            newcol += i
            if newcol in self.posdict[key]:
                # find first non-blank after newcol
                for mtcol in range(newcol+1,self.maxcol+2):
                    if mtcol not in self.posdict[key]: break
                l1 = range(mtcol,newcol,-1)+[newcol]
                l = range(mtcol-1,newcol-1,-1)+[col]
            else:
                l1 = [newcol]
                l = [col]
            # move all of the items, starting from the last column
            for newcol,col in zip(l1,l):
                #print 'moving',col,'to',newcol
                self.posdict[key][newcol] = self.posdict[key][col]
                del self.posdict[key][col]
                self.maxcol = max(self.maxcol,newcol)
                obj = self.GBsizer.FindItemAtPosition((row+1,col))
                self.GBsizer.SetItemPosition(obj.GetWindow(),(row+1,newcol))
                for wid in obj.GetWindow().Children:
                    if wid in self.chceDict:
                        self.chceDict[wid] = (row,newcol)
                        wid.SetSelection(self.chceDict[wid][1])
        # has the table gotten larger? If so we need new column heading(s)
        if prevmaxcol != self.maxcol:
            for i in range(prevmaxcol+1,self.maxcol+1):
                wid = wx.StaticText(self,wx.ID_ANY,str(i),style=wx.ALIGN_CENTER)
                wid.SetBackgroundColour(DULL_YELLOW)
                wid.SetMinSize((50,-1))
                self.GBsizer.Add(wid,(0,i),flag=wx.ALIGN_CENTER|wx.EXPAND)
            colList = [str(i) for i in range(self.maxcol+2)]
            for wid in self.chceDict:
                wid.SetItems(colList)
                wid.SetSelection(self.chceDict[wid][1])
        self.GBsizer.Layout()
        self.FitInside()
        
################################################################################
def GetImportFile(G2frame, message, defaultDir="", defaultFile="", style=wx.FD_OPEN,
                  *args, **kwargs):
    '''Uses a customized dialog that gets files from the appropriate import directory. 
    Arguments are used the same as in :func:`wx.FileDialog`. Selection of
    multiple files is allowed if argument style includes wx.FD_MULTIPLE.

    The default initial directory (unless overridden with argument defaultDir)
    is found in G2frame.TutorialImportDir, config setting Import_directory or
    G2frame.LastImportDir, see :func:`GetImportPath`.

    The path of the first file entered is used to set G2frame.LastImportDir
    and optionally config setting Import_directory.

    :returns: a list of files or an empty list
    '''
    dlg = wx.FileDialog(G2frame, message, defaultDir, defaultFile, *args,
                        style=style, **kwargs)
    pth = GetImportPath(G2frame)
    if not defaultDir and pth: dlg.SetDirectory(pth)
    try:
        if dlg.ShowModal() == wx.ID_OK:
            if style & wx.FD_MULTIPLE:
                filelist = dlg.GetPaths()
                if len(filelist) == 0: return []
            else:
                filelist = [dlg.GetPath(),]
            # not sure if we want to do this (why use wx.CHANGE_DIR?)
            if style & wx.FD_CHANGE_DIR: # to get Mac/Linux to change directory like windows!
                os.chdir(dlg.GetDirectory())
        else: # cancel was pressed
            return []
    finally:
        dlg.Destroy()
    # save the path of the first file and reset the TutorialImportDir variable
    pth = os.path.split(os.path.abspath(filelist[0]))[0]
    if GSASIIpath.GetConfigValue('Save_paths'): SaveImportDirectory(pth)
    G2frame.LastImportDir = pth
    G2frame.TutorialImportDir = None
    return filelist

def GetImportPath(G2frame):
    '''Determines the default location to use for importing files. Tries sequentially
    G2frame.TutorialImportDir, config var Import_directory and G2frame.LastImportDir.
    
    :returns: a string containing the path to be used when reading files or None
      if none of the above are specified.
    '''
    if G2frame.TutorialImportDir:
        if os.path.exists(G2frame.TutorialImportDir):
            return G2frame.TutorialImportDir
        elif GSASIIpath.GetConfigValue('debug'):
            print('Tutorial location (TutorialImportDir) not found: '+G2frame.TutorialImportDir)
    pth = GSASIIpath.GetConfigValue('Import_directory')
    if pth:
        pth = os.path.expanduser(pth)
        if os.path.exists(pth):
            return pth
        elif GSASIIpath.GetConfigValue('debug'):
            print('Ignoring Config Import_directory value: '+
                      GSASIIpath.GetConfigValue('Import_directory'))
    if G2frame.LastImportDir:
        if os.path.exists(G2frame.LastImportDir):
            return G2frame.LastImportDir
        elif GSASIIpath.GetConfigValue('debug'):
            print('Warning: G2frame.LastImportDir not found = '+G2frame.LastImportDir)
    return None

def GetExportPath(G2frame):
    '''Determines the default location to use for writing files. Tries sequentially
    G2frame.LastExportDir and G2frame.LastGPXdir.
    
    :returns: a string containing the path to be used when writing files or '.'
      if none of the above are specified.
    '''
    if G2frame.LastExportDir:
        return G2frame.LastExportDir
    elif G2frame.LastGPXdir:
        return G2frame.LastGPXdir
    else:
        return '.'

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
        self.panel = None
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
        if self.panel: self.panel.Destroy()
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
            bRadii = ValidatedTxtCtrl(self.panel,data['BondRadii'],id,nDig=(10,3))
            radiiSizer.Add(bRadii,0,WACV)
            if self.Angle:
                aRadii = ValidatedTxtCtrl(self.panel,data['AngleRadii'],id,nDig=(10,3))
                radiiSizer.Add(aRadii,0,WACV)
        mainSizer.Add(radiiSizer,0,wx.EXPAND)
        if self.Angle:
            factorSizer = wx.FlexGridSizer(0,2,5,5)
            Names = ['Bond','Angle']
            for i,name in enumerate(Names):
                factorSizer.Add(wx.StaticText(self.panel,-1,name+' search factor'),0,WACV)
                bondFact = ValidatedTxtCtrl(self.panel,data['Factors'],i,nDig=(10,3))
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
        wx.CallAfter(self.Draw,self.data)
                
################################################################################
class ShowLSParms(wx.Dialog):
    '''Create frame to show least-squares parameters
    '''
    def __init__(self,parent,title,parmDict,varyList,fullVaryList,
                 size=(375,430)):
        
        wx.Dialog.__init__(self,parent,wx.ID_ANY,title,size=size,
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.panel = wxscroll.ScrolledPanel(self)
        self.parmChoice = 'Phase'
        self.parmDict = parmDict
        self.varyList = varyList
        self.fullVaryList = fullVaryList

        self.parmNames = list(parmDict.keys())
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

        if self.panel.GetSizer(): self.panel.GetSizer().Clear(True)
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
                ch = HelpButton(self.panel,G2obj.fmtVarDescr(name))
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
#####  Customized Grid Support
################################################################################           
class GSGrid(wg.Grid):
    '''Basic wx.Grid implementation
    '''
    def __init__(self, parent, name=''):
        wg.Grid.__init__(self,parent,-1,name=name)
        if hasattr(parent.TopLevelParent,'currentGrids'):
            parent.TopLevelParent.currentGrids.append(self)      # save a reference to the grid in the Frame
        self.SetScrollRate(0,0)         #GSAS-II grids have no scroll bars by default
            
    def Clear(self):
        wg.Grid.ClearGrid(self)
        
    def SetCellReadOnly(self,r,c,readonly=True):
        self.SetReadOnly(r,c,isReadOnly=readonly)
        
    def SetCellStyle(self,r,c,color="white",readonly=True):
        self.SetCellBackgroundColour(r,c,color)
        self.SetReadOnly(r,c,isReadOnly=readonly)
        
    def GetSelection(self):
        #this is to satisfy structure drawing stuff in G2plt when focus changes
        return None

    def InstallGridToolTip(self, rowcolhintcallback,
                           colLblCallback=None,rowLblCallback=None):
        '''code to display a tooltip for each item on a grid
        from http://wiki.wxpython.org/wxGrid%20ToolTips (buggy!), expanded to
        column and row labels using hints from
        https://groups.google.com/forum/#!topic/wxPython-users/bm8OARRVDCs

        :param function rowcolhintcallback: a routine that returns a text
          string depending on the selected row and column, to be used in
          explaining grid entries.
        :param function colLblCallback: a routine that returns a text
          string depending on the selected column, to be used in
          explaining grid columns (if None, the default), column labels
          do not get a tooltip.
        :param function rowLblCallback: a routine that returns a text
          string depending on the selected row, to be used in
          explaining grid rows (if None, the default), row labels
          do not get a tooltip.
        '''
        prev_rowcol = [None,None,None]
        def OnMouseMotion(event):
            # event.GetRow() and event.GetCol() would be nice to have here,
            # but as this is a mouse event, not a grid event, they are not
            # available and we need to compute them by hand.
            x, y = self.CalcUnscrolledPosition(event.GetPosition())
            row = self.YToRow(y)
            col = self.XToCol(x)
            hinttext = ''
            win = event.GetEventObject()
            if [row,col,win] == prev_rowcol: # no change from last position
                if event: event.Skip()
                return
            if win == self.GetGridWindow() and row >= 0 and col >= 0:
                hinttext = rowcolhintcallback(row, col)
            elif win == self.GetGridColLabelWindow() and col >= 0:
                if colLblCallback: hinttext = colLblCallback(col)
            elif win == self.GetGridRowLabelWindow() and row >= 0:
                if rowLblCallback: hinttext = rowLblCallback(row)
            else: # this should be the upper left corner, which is empty
                if event: event.Skip()
                return
            if hinttext is None: hinttext = ''
            win.SetToolTipString(hinttext)
            prev_rowcol[:] = [row,col,win]
            if event: event.Skip()

        wx.EVT_MOTION(self.GetGridWindow(), OnMouseMotion)
        if colLblCallback: wx.EVT_MOTION(self.GetGridColLabelWindow(), OnMouseMotion)
        if rowLblCallback: wx.EVT_MOTION(self.GetGridRowLabelWindow(), OnMouseMotion)
                                                    
################################################################################           
class Table(wg.PyGridTableBase):
    '''Basic data table for use with GSgrid
    '''
    def __init__(self, data=[], rowLabels=None, colLabels=None, types = None):
        if 'phoenix' in wx.version():
            wg.GridTableBase.__init__(self)
        else:
            wg.PyGridTableBase.__init__(self)
        self.colLabels = colLabels
        self.rowLabels = rowLabels
        self.dataTypes = types
        self.data = data
        
    def AppendRows(self, numRows=1):
        self.data.append([])
        return True
        
    def CanGetValueAs(self, row, col, typeName):
        if self.dataTypes:
            colType = self.dataTypes[col].split(':')[0]
            if typeName == colType:
                return True
            else:
                return False
        else:
            return False

    def CanSetValueAs(self, row, col, typeName):
        return self.CanGetValueAs(row, col, typeName)

    def DeleteRow(self,pos):
        data = self.GetData()
        self.SetData([])
        new = []
        for irow,row in enumerate(data):
            if irow != pos:
                new.append(row)
        self.SetData(new)
        
    def GetColLabelValue(self, col):
        if self.colLabels:
            return self.colLabels[col]
            
    def GetData(self):
        data = []
        for row in range(self.GetNumberRows()):
            data.append(self.GetRowValues(row))
        return data
        
    def GetNumberCols(self):
        try:
            return len(self.colLabels)
        except TypeError:
            return None
        
    def GetNumberRows(self):
        return len(self.data)
        
    def GetRowLabelValue(self, row):
        if self.rowLabels:
            return self.rowLabels[row]
        
    def GetColValues(self, col):
        data = []
        for row in range(self.GetNumberRows()):
            data.append(self.GetValue(row, col))
        return data
        
    def GetRowValues(self, row):
        data = []
        for col in range(self.GetNumberCols()):
            data.append(self.GetValue(row, col))
        return data
        
    def GetTypeName(self, row, col):
        try:
            if self.data[row][col] is None: return None
            return self.dataTypes[col]
        except (TypeError,IndexError):
            return None

    def GetValue(self, row, col):
        try:
            if self.data[row][col] is None: return ""
            return self.data[row][col]
        except IndexError:
            return None
            
    def InsertRows(self, pos, rows):
        for row in range(rows):
            self.data.insert(pos,[])
            pos += 1
        
    def IsEmptyCell(self,row,col):
        try:
            return not self.data[row][col]
        except IndexError:
            return True
        
    def OnKeyPress(self, event):
        dellist = self.GetSelectedRows()
        if event.GetKeyCode() == wx.WXK_DELETE and dellist:
            grid = self.GetView()
            for i in dellist: grid.DeleteRow(i)
                
    def SetColLabelValue(self, col, label):
        numcols = self.GetNumberCols()
        if col > numcols-1:
            self.colLabels.append(label)
        else:
            self.colLabels[col]=label
        
    def SetData(self,data):
        for row in range(len(data)):
            self.SetRowValues(row,data[row])
                
    def SetRowLabelValue(self, row, label):
        self.rowLabels[row]=label
            
    def SetRowValues(self,row,data):
        self.data[row] = data
            
    def SetValue(self, row, col, value):
        def innerSetValue(row, col, value):
            try:
                self.data[row][col] = value
            except TypeError:
                return
            except IndexError: # has this been tested? 
                #print row,col,value
                # add a new row
                if row > self.GetNumberRows():
                    self.data.append([''] * self.GetNumberCols())
                elif col > self.GetNumberCols():
                    for row in range(self.GetNumberRows()): # bug fixed here
                        self.data[row].append('')
                #print self.data
                self.data[row][col] = value
        innerSetValue(row, col, value)

################################################################################
class GridFractionEditor(wg.PyGridCellEditor):
    '''A grid cell editor class that allows entry of values as fractions as well
    as sine and cosine values [as s() and c()]
    '''
    def __init__(self,grid):
        if 'phoenix' in wx.version():
            wg.GridCellEditor.__init__(self)
        else:
            wg.PyGridCellEditor.__init__(self)

    def Create(self, parent, id, evtHandler):
        self._tc = wx.TextCtrl(parent, id, "")
        self._tc.SetInsertionPoint(0)
        self.SetControl(self._tc)

        if evtHandler:
            self._tc.PushEventHandler(evtHandler)

        self._tc.Bind(wx.EVT_CHAR, self.OnChar)

    def SetSize(self, rect):
        self._tc.SetDimensions(rect.x, rect.y, rect.width+2, rect.height+2,
                               wx.SIZE_ALLOW_MINUS_ONE)

    def BeginEdit(self, row, col, grid):
        self.startValue = grid.GetTable().GetValue(row, col)
        self._tc.SetValue(str(self.startValue))
        self._tc.SetInsertionPointEnd()
        self._tc.SetFocus()
        self._tc.SetSelection(0, self._tc.GetLastPosition())

    def EndEdit(self, row, col, grid, oldVal=None):
        changed = False

        self.nextval = self.startValue
        val = self._tc.GetValue().lower().strip()
        if val != self.startValue:
            changed = True
            neg = False
            if val.startswith('-'):
                neg = True
                val = val[1:]
            # allow old GSAS s20 and c20 etc for sind(20) and cosd(20)
            if val.startswith('s') and '(' not in val:
                val = 'sind('+val.strip('s')+')'
            elif val.startswith('c') and '(' not in val:
                val = 'cosd('+val.strip('c')+')'
            if neg:
                val = '-' + val
            val = G2py3.FormulaEval(val)
            if val is not None:
                self.nextval = val
            else:
                return None
            if oldVal is None: # this arg appears in 2.9+; before, we should go ahead & change the table
                grid.GetTable().SetValue(row, col, val) # update the table
            # otherwise self.ApplyEdit gets called

        self.startValue = ''
        self._tc.SetValue('')
        return changed
    
    def ApplyEdit(self, row, col, grid):
        """ Called only in wx >= 2.9
        Save the value of the control into the grid if EndEdit() returns as True
        """
        grid.GetTable().SetValue(row, col, self.nextval) # update the table

    def Reset(self):
        self._tc.SetValue(self.startValue)
        self._tc.SetInsertionPointEnd()

    def Clone(self,grid):
        return GridFractionEditor(grid)

    def StartingKey(self, evt):
        self.OnChar(evt)
        if evt.GetSkipped():
            self._tc.EmulateKeyPress(evt)

    def OnChar(self, evt):
        key = evt.GetKeyCode()
        if key < 32 or key >= 127:
            evt.Skip()
        elif chr(key).lower() in '.+-*/0123456789cosind()':
            evt.Skip()
        else:
            evt.StopPropagation()
            
################################################################################
#####  Customized Notebook
################################################################################           
class GSNoteBook(wx.aui.AuiNotebook):
    '''Notebook used in various locations; implemented with wx.aui extension
    '''
    def __init__(self, parent, name='',size = None,style=wx.aui.AUI_NB_TOP |
        wx.aui.AUI_NB_SCROLL_BUTTONS):
        wx.aui.AuiNotebook.__init__(self, parent, style=style)
        if size: self.SetSize(size)
        self.parent = parent
        self.PageChangeHandler = None
        
    def PageChangeEvent(self,event):
        pass
#        G2frame = self.parent.G2frame
#        page = event.GetSelection()
#        if self.PageChangeHandler:
#            if log.LogInfo['Logging']:
#                log.MakeTabLog(
#                    G2frame.dataWindow.GetTitle(),
#                    G2frame.dataDisplay.GetPageText(page)
#                    )
#            self.PageChangeHandler(event)
            
#    def Bind(self,eventtype,handler,*args,**kwargs):
#        '''Override the Bind() function so that page change events can be trapped
#        '''
#        if eventtype == wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED:
#            self.PageChangeHandler = handler
#            wx.aui.AuiNotebook.Bind(self,eventtype,self.PageChangeEvent)
#            return
#        wx.aui.AuiNotebook.Bind(self,eventtype,handler,*args,**kwargs)
                                                      
    def Clear(self):        
        GSNoteBook.DeleteAllPages(self)
        
    def FindPage(self,name):
        numPage = self.GetPageCount()
        for page in range(numPage):
            if self.GetPageText(page) == name:
                return page
        return None

    def ChangeSelection(self,page):
        # in wx.Notebook ChangeSelection is like SetSelection, but it
        # does not invoke the event related to pressing the tab button
        # I don't see a way to do that in aui.
        oldPage = self.GetSelection()
        self.SetSelection(page)
        return oldPage

    # def __getattribute__(self,name):
    #     '''This method provides a way to print out a message every time
    #     that a method in a class is called -- to see what all the calls
    #     might be, or where they might be coming from.
    #     Cute trick for debugging!
    #     '''
    #     attr = object.__getattribute__(self, name)
    #     if hasattr(attr, '__call__'):
    #         def newfunc(*args, **kwargs):
    #             print('GSauiNoteBook calling %s' %attr.__name__)
    #             result = attr(*args, **kwargs)
    #             return result
    #         return newfunc
    #     else:
    #         return attr
            
################################################################################
#### Help support routines
################################################################################
class MyHelp(wx.Menu):
    '''
    A class that creates the contents of a help menu.
    The menu will start with two entries:

    * 'Help on <helpType>': where helpType is a reference to an HTML page to
      be opened
    * About: opens an About dialog using OnHelpAbout. N.B. on the Mac this
      gets moved to the App menu to be consistent with Apple style.

    NOTE: for this to work properly with respect to system menus, the title
    for the menu must be &Help, or it will not be processed properly:

    ::

       menu.Append(menu=MyHelp(self,...),title="&Help")

    '''
    def __init__(self,frame,includeTree=False,morehelpitems=[]):
        wx.Menu.__init__(self,'')
        self.HelpById = {}
        self.frame = frame
        self.Append(wx.ID_ABOUT,'&About GSAS-II','')
        frame.Bind(wx.EVT_MENU, self.OnHelpAbout, id=wx.ID_ABOUT)
        if GSASIIpath.whichsvn():
            helpobj = self.Append(wx.ID_ANY,'&Check for updates','')
            frame.Bind(wx.EVT_MENU, self.OnCheckUpdates, helpobj)
            helpobj = self.Append(wx.ID_ANY,'&Regress to an old GSAS-II version','')
            frame.Bind(wx.EVT_MENU, self.OnSelectVersion, helpobj)
            # if GSASIIpath.svnTestBranch():
            #     msg = "&Switch back to standard GSAS-II version"
            # else:
            #     msg = "&Switch to test (2frame) GSAS-II version"
            # helpobj = self.Append(
            #     help='', id=wx.ID_ANY, kind=wx.ITEM_NORMAL,text=msg)
            # frame.Bind(wx.EVT_MENU, self.OnSelectBranch, helpobj)
        # provide special help topic names for extra items in help menu
        for lbl,indx in morehelpitems:
            helpobj = self.Append(wx.ID_ANY,lbl,'')
            frame.Bind(wx.EVT_MENU, self.OnHelpById, helpobj)
            self.HelpById[helpobj.GetId()] = indx
        # add help lookup(s) in gsasii.html
        self.AppendSeparator()
        if includeTree:
            helpobj = self.Append(wx.ID_ANY,'Help on Data tree','')
            frame.Bind(wx.EVT_MENU, self.OnHelpById, id=helpobj.GetId())
            self.HelpById[helpobj.GetId()] = 'Data tree'
        helpobj = self.Append(wx.ID_ANY,'Help on current data tree item','')
        frame.Bind(wx.EVT_MENU, self.OnHelpById, id=helpobj.GetId())
       
    def OnHelpById(self,event):
        '''Called when Help on... is pressed in a menu. Brings up a web page
        for documentation. Uses the helpKey value from the dataWindow window
        unless a special help key value has been defined for this menu id in
        self.HelpById

        Note that self should now (2frame) be child of the main window (G2frame)
        '''
        if hasattr(self.frame,'dataWindow'):  # Debug code: check this is called from menu in G2frame
            # should always be true in 2 Frame version
            dW = self.frame.dataWindow
        else:
            print('help error: not called from standard menu?')
            print (self)
            return            
        try:
            helpKey = dW.helpKey # look up help from helpKey in data window
            #if GSASIIpath.GetConfigValue('debug'): print 'dataWindow help: key=',helpKey
        except AttributeError:
            helpKey = ''
            if GSASIIpath.GetConfigValue('debug'): print('No helpKey for current dataWindow!')
        helpType = self.HelpById.get(event.GetId(),helpKey) # see if there is a special help topic
        #if GSASIIpath.GetConfigValue('debug'): print 'helpKey=',helpKey,'  helpType=',helpType
        if helpType == 'Tutorials':
            dlg = OpenTutorial(self.frame)
            dlg.ShowModal()
            dlg.Destroy()
            return
        else:
            ShowHelp(helpType,self.frame)

    def OnHelpAbout(self, event):
        "Display an 'About GSAS-II' box"
        import GSASII
        try:
            import wx.adv as wxadv  # AboutBox moved here in Phoenix
        except:
            wxadv = wx
        info = wxadv.AboutDialogInfo()
        info.Name = 'GSAS-II'
        ver = GSASIIpath.svnGetRev()
        if not ver:
            ver = GSASIIpath.GetVersionNumber()
        info.SetVersion(ver)
        #info.Developers = ['Robert B. Von Dreele','Brian H. Toby']
        info.Copyright = ('(c) ' + time.strftime('%Y') +
''' Argonne National Laboratory
This product includes software developed
by the UChicago Argonne, LLC, as 
Operator of Argonne National Laboratory.''')
        info.Description = '''General Structure Analysis System-II (GSAS-II)
Robert B. Von Dreele and Brian H. Toby

Please cite as:
  B.H. Toby & R.B. Von Dreele, J. Appl. Cryst. 46, 544-549 (2013) 
For small angle use cite: 
  R.B. Von Dreele, J. Appl. Cryst. 47, 1748-9 (2014)
For DIFFaX use cite: 
  M.M.J. Treacy, J.M. Newsam & M.W. Deem, 
  Proc. Roy. Soc. Lond. A 433, 499-520 (1991)
'''
        info.WebSite = ("https://subversion.xray.aps.anl.gov/trac/pyGSAS","GSAS-II home page")
        wxadv.AboutBox(info)

    def OnCheckUpdates(self,event):
        '''Check if the GSAS-II repository has an update for the current source files
        and perform that update if requested.
        '''            
        if not GSASIIpath.whichsvn():
            dlg = wx.MessageDialog(self.frame,
                                   'No Subversion','Cannot update GSAS-II because subversion (svn) was not found.',
                                   wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return
        wx.BeginBusyCursor()
        local = GSASIIpath.svnGetRev()
        if local is None: 
            wx.EndBusyCursor()
            dlg = wx.MessageDialog(self.frame,
                                   'Unable to run subversion on the GSAS-II current directory. Is GSAS-II installed correctly?',
                                   'Subversion error',
                                   wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return
        print ('Installed GSAS-II version: '+local)
        repos = GSASIIpath.svnGetRev(local=False)
        wx.EndBusyCursor()
        # has the current branch disappeared? If so, switch to the trunk -- not fully tested
        if (repos is None and "not found" in GSASIIpath.svnLastError.lower()
            and "path" in GSASIIpath.svnLastError.lower()):
            print('Repository is gone, will switch to trunk')
            GSASIIpath.svnSwitch2branch()
            return
        elif repos is None: 
            dlg = wx.MessageDialog(self.frame,
                                   'Unable to access the GSAS-II server. Is this computer on the internet?',
                                   'Server unavailable',
                                   wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return
        print ('GSAS-II version on server: '+repos)
        if local == repos:
            dlg = wx.MessageDialog(self.frame,
                                   'GSAS-II is up-to-date. Version '+local+' is already loaded.',
                                   'GSAS-II Up-to-date',
                                   wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return
        mods = GSASIIpath.svnFindLocalChanges()
        if mods:
            dlg = wx.MessageDialog(self.frame,
                                   'You have version '+local+
                                   ' of GSAS-II installed, but the current version is '+repos+
                                   '. However, '+str(len(mods))+
                                   ' file(s) on your local computer have been modified.'
                                   ' Updating will attempt to merge your local changes with '
                                   'the latest GSAS-II version, but if '
                                   'conflicts arise, local changes will be '
                                   'discarded. It is also possible that the '
                                   'local changes my prevent GSAS-II from running. '
                                   'Press OK to start an update if this is acceptable:',
                                   'Local GSAS-II Mods',
                                   wx.OK|wx.CANCEL)
            if dlg.ShowModal() != wx.ID_OK:
                dlg.Destroy()
                return
            else:
                dlg.Destroy()
        else:
            dlg = wx.MessageDialog(self.frame,
                                   'You have version '+local+
                                   ' of GSAS-II installed, but the current version is '+repos+
                                   '. Press OK to start an update:',
                                   'GSAS-II Updates',
                                   wx.OK|wx.CANCEL)
            if dlg.ShowModal() != wx.ID_OK:
                dlg.Destroy()
                return
            dlg.Destroy()
        print ('start updates')
        dlg = wx.MessageDialog(self.frame,
                               'Your project will now be saved, GSAS-II will exit and an update '
                               'will be performed and GSAS-II will restart. Press Cancel to '
                               'abort the update',
                               'Start update?',
                               wx.OK|wx.CANCEL)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        dlg.Destroy()
        self.frame.OnFileSave(event)
        GPX = self.frame.GSASprojectfile
        GSASIIpath.svnUpdateProcess(projectfile=GPX)
        return

    def OnSelectVersion(self,event):
        '''Allow the user to select a specific version of GSAS-II
        '''
        if not GSASIIpath.whichsvn():
            dlg = wx.MessageDialog(self,'No Subversion','Cannot update GSAS-II because subversion (svn) '+
                                   'was not found.'
                                   ,wx.OK)
            dlg.ShowModal()
            return
        local = GSASIIpath.svnGetRev()
        if local is None: 
            dlg = wx.MessageDialog(self.frame,
                                   'Unable to run subversion on the GSAS-II current directory. Is GSAS-II installed correctly?',
                                   'Subversion error',
                                   wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return
        mods = GSASIIpath.svnFindLocalChanges()
        if mods:
            dlg = wx.MessageDialog(self.frame,
                                   'You have version '+local+
                                   ' of GSAS-II installed'
                                   '. However, '+str(len(mods))+
                                   ' file(s) on your local computer have been modified.'
                                   ' Downdating will attempt to merge your local changes with '
                                   'the selected GSAS-II version. '
                                   'Downdating is not encouraged because '
                                   'if merging is not possible, your local changes will be '
                                   'discarded. It is also possible that the '
                                   'local changes my prevent GSAS-II from running. '
                                   'Press OK to continue anyway.',
                                   'Local GSAS-II Mods',
                                   wx.OK|wx.CANCEL)
            if dlg.ShowModal() != wx.ID_OK:
                dlg.Destroy()
                return
            dlg.Destroy()
        if GSASIIpath.svnGetRev(local=False) is None:
            dlg = wx.MessageDialog(self.frame,
                                   'Error obtaining current GSAS-II version. Is internet access working correctly?',
                                   'Subversion error',
                                   wx.OK)
            dlg.ShowModal()
            dlg.Destroy()
            return
        dlg = downdate(parent=self.frame)
        if dlg.ShowModal() == wx.ID_OK:
            ver = dlg.getVersion()
        else:
            dlg.Destroy()
            return
        dlg.Destroy()
        print('start regress to '+str(ver))
        self.frame.OnFileSave(event)
        GPX = self.frame.GSASprojectfile
        GSASIIpath.svnUpdateProcess(projectfile=GPX,version=str(ver))
        return

    # def OnSelectBranch(self,event):
    #     '''Allow the user to select branch of GSAS-II or return to trunk
    #     N.B. Name of branch to use is hard-coded here. Must contain a slash
    #     '''
    #     testbranch = '/branch/2frame'
    #     if not GSASIIpath.svnTestBranch():
    #         dlg = wx.MessageDialog(self.frame,
    #                                'Switching to test GSAS-II version',
    #                                'Confirm Switch',
    #                                wx.OK|wx.CANCEL)
    #         if dlg.ShowModal() != wx.ID_OK: return
    #         branch = testbranch
    #     else:
    #         dlg = wx.MessageDialog(self.frame,
    #                                'Switching back to standard GSAS-II version',
    #                                'Confirm Switch',
    #                                wx.OK|wx.CANCEL)
    #         if dlg.ShowModal() != wx.ID_OK: return
    #         branch = 'trunk'
    #     print('start switch')
    #     self.frame.OnFileSave(event)
    #     GPX = self.frame.GSASprojectfile
    #     GSASIIpath.svnUpdateProcess(projectfile=GPX,branch=branch)

################################################################################
class HelpButton(wx.Button):
    '''Create a help button that displays help information.
    The text is displayed in a modal message window.

    TODO: it might be nice if it were non-modal: e.g. it stays around until
    the parent is deleted or the user closes it, but this did not work for
    me. 

    :param parent: the panel which will be the parent of the button
    :param str msg: the help text to be displayed
    '''
    def __init__(self,parent,msg):
        if sys.platform == "darwin": 
            wx.Button.__init__(self,parent,wx.ID_HELP)
        else:
            wx.Button.__init__(self,parent,wx.ID_ANY,'?',style=wx.BU_EXACTFIT)
        self.Bind(wx.EVT_BUTTON,self._onPress)
        self.msg=StripIndents(msg)
        self.parent = parent
    def _onClose(self,event):
        self.dlg.EndModal(wx.ID_CANCEL)
    def _onPress(self,event):
        'Respond to a button press by displaying the requested text'
        #dlg = wx.MessageDialog(self.parent,self.msg,'Help info',wx.OK)
        self.dlg = wx.Dialog(self.parent,wx.ID_ANY,'Help information', 
                        style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        #self.dlg.SetBackgroundColour(wx.WHITE)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        txt = wx.StaticText(self.dlg,wx.ID_ANY,self.msg)
        mainSizer.Add(txt,1,wx.ALL|wx.EXPAND,10)
        txt.SetBackgroundColour(wx.WHITE)

        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        btn = wx.Button(self.dlg, wx.ID_CLOSE) 
        btn.Bind(wx.EVT_BUTTON,self._onClose)
        btnsizer.Add(btn)
        mainSizer.Add(btnsizer, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        self.dlg.SetSizer(mainSizer)
        mainSizer.Fit(self.dlg)
        self.dlg.CenterOnParent()
        self.dlg.ShowModal()
        self.dlg.Destroy()
################################################################################
class MyHtmlPanel(wx.Panel):
    '''Defines a panel to display HTML help information, as an alternative to
    displaying help information in a web browser.
    '''
    def __init__(self, frame, id):
        self.frame = frame
        wx.Panel.__init__(self, frame, id)
        sizer = wx.BoxSizer(wx.VERTICAL)
        back = wx.Button(self, -1, "Back")
        back.Bind(wx.EVT_BUTTON, self.OnBack)
        self.htmlwin = G2HtmlWindow(self, id, size=(750,450))
        sizer.Add(self.htmlwin, 1,wx.EXPAND)
        sizer.Add(back, 0, wx.ALIGN_LEFT, 0)
        self.SetSizer(sizer)
        sizer.Fit(frame)        
        self.Bind(wx.EVT_SIZE,self.OnHelpSize)
    def OnHelpSize(self,event):         #does the job but weirdly!!
        anchor = self.htmlwin.GetOpenedAnchor()
        if anchor:            
            self.htmlwin.ScrollToAnchor(anchor)
            wx.CallAfter(self.htmlwin.ScrollToAnchor,anchor)
            if event: event.Skip()
    def OnBack(self, event):
        self.htmlwin.HistoryBack()
    def LoadFile(self,file):
        pos = file.rfind('#')
        if pos != -1:
            helpfile = file[:pos]
            helpanchor = file[pos+1:]
        else:
            helpfile = file
            helpanchor = None
        self.htmlwin.LoadPage(helpfile)
        if helpanchor is not None:
            self.htmlwin.ScrollToAnchor(helpanchor)
            xs,ys = self.htmlwin.GetViewStart()
            self.htmlwin.Scroll(xs,ys-1)
################################################################################
class G2HtmlWindow(wx.html.HtmlWindow):
    '''Displays help information in a primitive HTML browser type window
    '''
    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
        wx.html.HtmlWindow.__init__(self, parent, *args, **kwargs)
    def LoadPage(self, *args, **kwargs):
        wx.html.HtmlWindow.LoadPage(self, *args, **kwargs)
        self.TitlePage()
    def OnLinkClicked(self, *args, **kwargs):
        wx.html.HtmlWindow.OnLinkClicked(self, *args, **kwargs)
        xs,ys = self.GetViewStart()
        self.Scroll(xs,ys-1)
        self.TitlePage()
    def HistoryBack(self, *args, **kwargs):
        wx.html.HtmlWindow.HistoryBack(self, *args, **kwargs)
        self.TitlePage()
    def TitlePage(self):
        self.parent.frame.SetTitle(self.GetOpenedPage() + ' -- ' + 
            self.GetOpenedPageTitle())

################################################################################
def StripIndents(msg):
    'Strip indentation from multiline strings'
    msg1 = msg.replace('\n ','\n')
    while msg != msg1:
        msg = msg1
        msg1 = msg.replace('\n ','\n')
    return msg.replace('\n\t','\n')

def StripUnicode(string,subs='.'):
    '''Strip non-ASCII characters from strings
    
    :param str string: string to strip Unicode characters from
    :param str subs: character(s) to place into string in place of each
      Unicode character. Defaults to '.'

    :returns: a new string with only ASCII characters
    '''
    s = ''
    for c in string:
        if ord(c) < 128:
            s += c
        else:
            s += subs
    return s.encode('ascii','replace')
        
################################################################################
# configuration routines (for editing config.py)
def SaveGPXdirectory(path):
    if GSASIIpath.GetConfigValue('Starting_directory') == path: return
    vars = GetConfigValsDocs()
    try:
        vars['Starting_directory'][1] = path
        if GSASIIpath.GetConfigValue('debug'): print('Saving GPX path: '+path)
        SaveConfigVars(vars)
    except KeyError:
        pass

def SaveImportDirectory(path):
    if GSASIIpath.GetConfigValue('Import_directory') == path: return
    vars = GetConfigValsDocs()
    try:
        vars['Import_directory'][1] = path
        if GSASIIpath.GetConfigValue('debug'): print('Saving Import path: '+path)
        SaveConfigVars(vars)
    except KeyError:
        pass

def GetConfigValsDocs():
    '''Reads the module referenced in fname (often <module>.__file__) and
    return a dict with names of global variables as keys.
    For each global variable, the value contains four items:

    :returns: a dict where keys are names defined in module config_example.py
      where the value is a list of four items, as follows:

         * item 0: the default value
         * item 1: the current value
         * item 2: the initial value (starts same as item 1)
         * item 3: the "docstring" that follows variable definition

    '''
    import config_example
    import ast
    fname = os.path.splitext(config_example.__file__)[0]+'.py' # convert .pyc to .py
    with open(fname, 'r') as f:
        fstr = f.read()
    fstr = fstr.replace('\r\n', '\n').replace('\r', '\n')
    if not fstr.endswith('\n'):
        fstr += '\n'
    tree = ast.parse(fstr)
    d = {}
    key = None
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign):
            key = node.targets[0].id
            d[key] = [config_example.__dict__.get(key),
                      GSASIIpath.configDict.get(key),
                      GSASIIpath.configDict.get(key),'']
        elif isinstance(node,ast.Expr) and key:
            d[key][3] = node.value.s.strip()
        else:
            key = None
    return d

def SaveConfigVars(vars,parent=None):
    '''Write the current config variable values to config.py

    :params dict vars: a dictionary of variable settings and meanings as
      created in :func:`GetConfigValsDocs`.
    :param parent: wx.Frame object or None (default) for parent
      of error message if no file can be written.
    :returns: True if unable to write the file, None otherwise
    '''
    # try to write to where an old config file is located
    try:
        import config
        savefile = config.__file__
    except ImportError: # no config.py file yet
        savefile = os.path.join(GSASIIpath.path2GSAS2,'config.py')
    # try to open file for write
    try:
        savefile = os.path.splitext(savefile)[0]+'.py' # convert .pyc to .py
        fp = open(savefile,'w')
    except IOError:  # can't write there, write in local mods directory
        # create a local mods directory, if needed
        g2local = os.path.expanduser('~/.G2local/')
        if not os.path.exists(g2local):
            try:
                print(u'Creating directory '+g2local)
                os.mkdir(g2local)
            except:
                if parent:
                    G2MessageBox(parent,u'Error trying to create directory '+g2local,
                        'Unable to save')
                else:
                    print(u'Error trying to create directory '+g2local)
                return True
            sys.path.insert(0,os.path.expanduser('~/.G2local/'))
        savefile = os.path.join(os.path.expanduser('~/.G2local/'),'config.py')
        try:
            fp = open(savefile,'w')
        except IOError:
            if parent:
                G2MessageBox(parent,'Error trying to write configuration to '+savefile,
                    'Unable to save')
            else:
                print('Error trying to write configuration to '+savefile)
            return True
    import datetime
    fp.write("'''\n")
    fp.write("*config.py: Configuration options*\n----------------------------------\n")
    fp.write("This file created in SelectConfigSetting on {:%d %b %Y %H:%M}\n".
             format(datetime.datetime.now()))
    fp.write("'''\n\n")
    fp.write("import os.path\n")
    fp.write("import GSASIIpath\n\n")
    for var in sorted(vars.keys(),key=lambda s: s.lower()):
        if vars[var][1] is None: continue
        if vars[var][1] == '': continue
        if vars[var][0] == vars[var][1]: continue
        try:
            float(vars[var][1]) # test for number
            fp.write(var + ' = ' + str(vars[var][1])+'\n')
        except:
            try:
                eval(vars[var][1]) # test for an expression
                fp.write(var + ' = ' + str(vars[var][1])+'\n')
            except: # must be a string
                varstr = vars[var][1]
                if '\\' in varstr:
                    fp.write(var + ' = os.path.normpath("' + varstr.replace('\\','/') +'")\n')
                else:
                    fp.write(var + ' = "' + str(varstr)+'"\n')
        if vars[var][3]:
            fp.write("'''" + str(vars[var][3]) + "\n'''\n\n")
    fp.close()
    print('wrote file '+savefile)

class SelectConfigSetting(wx.Dialog):
    '''Dialog to select configuration variables and set associated values.
    '''
    def __init__(self,parent=None):
        style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        wx.Dialog.__init__(self, parent, wx.ID_ANY, 'Set Config Variable', style=style)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.vars = GetConfigValsDocs()
        
        label = wx.StaticText(
            self,  wx.ID_ANY,
            'Select a GSAS-II configuration variable to change'
            )
        self.sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.choice = {}
        btn = G2ChoiceButton(self, sorted(self.vars.keys(),key=lambda s: s.lower()),
            strLoc=self.choice,strKey=0,onChoice=self.OnSelection)
        btn.SetLabel("")
        self.sizer.Add(btn)

        self.varsizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.varsizer,1,wx.ALL|wx.EXPAND,1)
        
        self.doclbl = wx.StaticBox(self, wx.ID_ANY, "")
        self.doclblsizr = wx.StaticBoxSizer(self.doclbl)
        self.docinfo = wx.StaticText(self,  wx.ID_ANY, "")
        self.doclblsizr.Add(self.docinfo, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.sizer.Add(self.doclblsizr, 0, wx.ALIGN_LEFT|wx.EXPAND|wx.ALL, 5)
        btnsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.saveBtn = wx.Button(self,-1,"Save current settings")
        btnsizer.Add(self.saveBtn, 0, wx.ALL, 2) 
        self.saveBtn.Bind(wx.EVT_BUTTON, self.OnSave)
        self.saveBtn.Enable(False)
        self.applyBtn = wx.Button(self,-1,"Use current (no save)")
        btnsizer.Add(self.applyBtn, 0, wx.ALL, 2) 
        self.applyBtn.Bind(wx.EVT_BUTTON, self.OnApplyChanges)
        self.applyBtn.Enable(False)
        
        btn = wx.Button(self,wx.ID_CANCEL)
        btnsizer.Add(btn, 0, wx.ALL, 2) 
        self.sizer.Add(btnsizer, 0, wx.ALIGN_CENTRE|wx.ALL, 5) 
                
        self.SetSizer(self.sizer)
        self.sizer.Fit(self)
        self.CenterOnParent()
        
    def OnChange(self,event=None):
        ''' Check if anything been changed. Turn the save button on/off.
        '''
        for var in self.vars:
            if self.vars[var][0] is None and self.vars[var][1] is not None:
                # make blank strings into None, if that is the default
                if self.vars[var][1].strip() == '': self.vars[var][1] = None
            if self.vars[var][1] != self.vars[var][2]:
                #print 'changed',var,self.vars[var][:3]
                self.saveBtn.Enable(True)
                self.applyBtn.Enable(True)
                break
        else:
            self.saveBtn.Enable(False)
            self.applyBtn.Enable(False)
        try:
            self.resetBtn.Enable(True)
        except:
            pass
        
    def OnApplyChanges(self,event=None):
        'Set config variables to match the current settings'
        GSASIIpath.SetConfigValue(self.vars)
        self.EndModal(wx.ID_OK)
        import GSASIImpsubs as G2mp
        G2mp.ResetMP()
        
    def OnSave(self,event):
        '''Write the config variables to config.py and then set them
        as the current settings
        '''
        if not SaveConfigVars(self.vars,parent=self):
            self.OnApplyChanges() # force a reload of the config settings
        else:
            self.EndModal(wx.ID_OK)

    def OnBoolSelect(self,event):
        'Respond to a change in a True/False variable'
        rb = event.GetEventObject()
        var = self.choice[0]
        self.vars[var][1] = (rb.GetSelection() == 0)
        self.OnChange()
        wx.CallAfter(self.OnSelection)
        
    def onSelDir(self,event):
        'Select a directory from a menu'
        dlg = wx.DirDialog(self, "Choose a directory:",style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            var = self.choice[0]
            self.vars[var][1] = dlg.GetPath()
            self.strEd.SetValue(self.vars[var][1])
            self.OnChange()
        dlg.Destroy()
        
    def OnSelection(self):
        'show a selected variable'
        def OnNewColorBar(event):
            self.vars['Contour_color'][1] = self.colSel.GetValue()
            self.OnChange(event)

        if 'phoenix' in wx.version():
            self.varsizer.Clear(True)
        else:
            self.varsizer.DeleteWindows()
        var = self.choice[0]
        showdef = True
        if var not in self.vars:
            raise Exception("How did this happen?")
        if type(self.vars[var][0]) is int:
            ed = ValidatedTxtCtrl(self,self.vars[var],1,typeHint=int,OKcontrol=self.OnChange)
            self.varsizer.Add(ed, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        elif type(self.vars[var][0]) is float:
            ed = ValidatedTxtCtrl(self,self.vars[var],1,typeHint=float,OKcontrol=self.OnChange)
            self.varsizer.Add(ed, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        elif type(self.vars[var][0]) is bool:
            showdef = False
            lbl = "value for "+var
            ch = []
            for i,v in enumerate((True,False)):
                s = str(v)
                if v == self.vars[var][0]:
                    defopt = i
                    s += ' (default)'
                ch += [s]
            rb = wx.RadioBox(self, wx.ID_ANY, lbl, wx.DefaultPosition, wx.DefaultSize,
                ch, 1, wx.RA_SPECIFY_COLS)
            # set initial value
            if self.vars[var][1] is None:
                rb.SetSelection(defopt)
            elif self.vars[var][1]:
                rb.SetSelection(0)
            else:
                rb.SetSelection(1)
            rb.Bind(wx.EVT_RADIOBOX,self.OnBoolSelect)
            self.varsizer.Add(rb, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        else:
            if var.endswith('_directory') or var.endswith('_location'):
                btn = wx.Button(self,wx.ID_ANY,'Select from dialog...')
                sz = (400,-1)
            else:
                btn = None
                sz = (250,-1)
            if var == 'Contour_color':
                if self.vars[var][1] is None:
                    self.vars[var][1] = 'Paired'
                colorList = sorted([m for m in mpl.cm.datad.keys() ],key=lambda s: s.lower())   #if not m.endswith("_r")
                self.colSel = wx.ComboBox(self,value=self.vars[var][1],choices=colorList,
                    style=wx.CB_READONLY|wx.CB_DROPDOWN)
                self.colSel.Bind(wx.EVT_COMBOBOX, OnNewColorBar)
                self.varsizer.Add(self.colSel, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
            else:
                self.strEd = ValidatedTxtCtrl(self,self.vars[var],1,typeHint=str,
                    OKcontrol=self.OnChange,size=sz)
                if self.vars[var][1] is not None:
                    self.strEd.SetValue(self.vars[var][1])
                self.varsizer.Add(self.strEd, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
            if btn:
                btn.Bind(wx.EVT_BUTTON,self.onSelDir)
                self.varsizer.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5) 
        # button for reset to default value
        lbl = "Reset to Default"
        if showdef: # spell out default when needed
            lbl += ' (='+str(self.vars[var][0])+')'
            #label = wx.StaticText(self,  wx.ID_ANY, 'Default value = '+str(self.vars[var][0]))
            #self.varsizer.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
        self.resetBtn = wx.Button(self,-1,lbl)
        self.resetBtn.Bind(wx.EVT_BUTTON, self.OnClear)
        if self.vars[var][1] is not None and self.vars[var][1] != '': # show current value, if one
            #label = wx.StaticText(self,  wx.ID_ANY, 'Current value = '+str(self.vars[var][1]))
            #self.varsizer.Add(label, 0, wx.ALIGN_LEFT|wx.ALL, 5)
            self.resetBtn.Enable(True)
        else:
            self.resetBtn.Enable(False)
        self.varsizer.Add(self.resetBtn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        # show meaning, if defined
        self.doclbl.SetLabel("Description of "+str(var)) 
        if self.vars[var][3]:
            self.docinfo.SetLabel(self.vars[var][3])
        else:
            self.docinfo.SetLabel("(not documented)")
        self.sizer.Fit(self)
        self.CenterOnParent()
        wx.CallAfter(self.SendSizeEvent)

    def OnClear(self, event):
        var = self.choice[0]
        self.vars[var][1] = self.vars[var][0]
        self.OnChange()
        wx.CallAfter(self.OnSelection)
        
################################################################################
class downdate(wx.Dialog):
    '''Dialog to allow a user to select a version of GSAS-II to install
    '''
    def __init__(self,parent=None):
        style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        wx.Dialog.__init__(self, parent, wx.ID_ANY, 'Select Version', style=style)
        pnl = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        insver = GSASIIpath.svnGetRev(local=True)
        curver = int(GSASIIpath.svnGetRev(local=False))
        label = wx.StaticText(
            pnl,  wx.ID_ANY,
            'Select a specific GSAS-II version to install'
            )
        sizer.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add(
            wx.StaticText(pnl,  wx.ID_ANY,
                          'Currently installed version: '+str(insver)),
            0, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(sizer1)
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add(
            wx.StaticText(pnl,  wx.ID_ANY,
                          'Select GSAS-II version to install: '),
            0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.spin = wx.SpinCtrl(pnl, wx.ID_ANY,size=(150,-1))
        self.spin.SetRange(1, curver)
        self.spin.SetValue(curver)
        self.Bind(wx.EVT_SPINCTRL, self._onSpin, self.spin)
        self.Bind(wx.EVT_KILL_FOCUS, self._onSpin, self.spin)
        sizer1.Add(self.spin)
        sizer.Add(sizer1)

        line = wx.StaticLine(pnl,-1, size=(-1,3), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.EXPAND|wx.ALIGN_CENTER|wx.ALL, 10)

        self.text = wx.StaticText(pnl,  wx.ID_ANY, "")
        sizer.Add(self.text, 0, wx.ALIGN_LEFT|wx.EXPAND|wx.ALL, 5)

        line = wx.StaticLine(pnl,-1, size=(-1,3), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.EXPAND|wx.ALIGN_CENTER|wx.ALL, 10)
        sizer.Add(
            wx.StaticText(
                pnl,  wx.ID_ANY,
                'If "Install" is pressed, your project will be saved;\n'
                'GSAS-II will exit; The specified version will be loaded\n'
                'and GSAS-II will restart. Press "Cancel" to abort.'),
            0, wx.EXPAND|wx.ALL, 10)
        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(pnl, wx.ID_OK, "Install")
        btn.SetDefault()
        btnsizer.AddButton(btn)
        btn = wx.Button(pnl, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()
        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        pnl.SetSizer(sizer)
        sizer.Fit(self)
        self.topsizer=sizer
        self.CenterOnParent()
        self._onSpin(None)

    def _onSpin(self,event):
        'Called to load info about the selected version in the dialog'
        if event: event.Skip()
        ver = self.spin.GetValue()
        d = GSASIIpath.svnGetLog(version=ver)
        date = d.get('date','?').split('T')[0]
        s = '(Version '+str(ver)+' created '+date
        s += ' by '+d.get('author','?')+')'
        msg = d.get('msg')
        if msg: s += '\n\nComment: '+msg
        self.text.SetLabel(s)
        self.topsizer.Fit(self)

    def getVersion(self):
        'Get the version number in the dialog'
        return self.spin.GetValue()

################################################################################
#### Display Help information
################################################################################
# define some globals 
htmlPanel = None
htmlFrame = None
htmlFirstUse = True
#helpLocDict = {}  # to be implemented if we ever split gsasii.html over multiple files
path2GSAS2 = os.path.dirname(os.path.realpath(__file__)) # save location of this file
def ShowHelp(helpType,frame):
    '''Called to bring up a web page for documentation.'''
    global htmlFirstUse,htmlPanel,htmlFrame
    # no defined link to use, create a default based on key
    helplink = 'gsasII.html'
    if helpType:
        helplink += '#'+helpType.replace(')','').replace('(','_').replace(' ','_')
    # determine if a web browser or the internal viewer should be used for help info
    if GSASIIpath.GetConfigValue('Help_mode'):
        helpMode = GSASIIpath.GetConfigValue('Help_mode')
    else:
        helpMode = 'browser'
    if helpMode == 'internal':
        helplink = os.path.join(path2GSAS2,'help',helplink)
        try:
            htmlPanel.LoadFile(helplink)
            htmlFrame.Raise()
        except:
            htmlFrame = wx.Frame(frame, -1, size=(610, 510))
            htmlFrame.Show(True)
            htmlFrame.SetTitle("HTML Window") # N.B. reset later in LoadFile
            htmlPanel = MyHtmlPanel(htmlFrame,-1)
            htmlPanel.LoadFile(helplink)
    else:
        if sys.platform == "darwin": # for Mac, force use of safari to preserve anchors on file URLs
            wb = webbrowser.MacOSXOSAScript('safari')
        else:
            wb = webbrowser
        helplink = os.path.join(path2GSAS2,'help',helplink)
        pfx = "file://"
        if sys.platform.lower().startswith('win'):
            pfx = ''
        #if GSASIIpath.GetConfigValue('debug'): print 'Help link=',pfx+helplink
        if htmlFirstUse:
            wb.open_new(pfx+helplink)
            htmlFirstUse = False
        else:
            wb.open(pfx+helplink, new=0, autoraise=True)

def ShowWebPage(URL,frame):
    '''Called to show a tutorial web page.
    '''
    global htmlFirstUse,htmlPanel,htmlFrame
    # determine if a web browser or the internal viewer should be used for help info
    if GSASIIpath.GetConfigValue('Help_mode'):
        helpMode = GSASIIpath.GetConfigValue('Help_mode')
    else:
        helpMode = 'browser'
    if helpMode == 'internal':
        try:
            htmlPanel.LoadFile(URL)
            htmlFrame.Raise()
        except:
            htmlFrame = wx.Frame(frame, -1, size=(610, 510))
            htmlFrame.Show(True)
            htmlFrame.SetTitle("HTML Window") # N.B. reset later in LoadFile
            htmlPanel = MyHtmlPanel(htmlFrame,-1)
            htmlPanel.LoadFile(URL)
    else:
        if URL.startswith('http'): 
            pfx = ''
        elif sys.platform.lower().startswith('win'):
            pfx = ''
        else:
            pfx = "file://"
        if htmlFirstUse:
            webbrowser.open_new(pfx+URL)
            htmlFirstUse = False
        else:
            webbrowser.open(pfx+URL, new=0, autoraise=True)

################################################################################
#### Tutorials support
################################################################################
G2BaseURL = "https://subversion.xray.aps.anl.gov/pyGSAS"
tutorialIndex = (
    # tutorial dir,      web page file name,      title for page
    ['Getting started'],
    ['StartingGSASII', 'Starting GSAS.htm', 'Starting GSAS-II'],

    ['Rietveld fitting'],
       
    ['LabData', 'Laboratory X.htm', 'Fitting laboratory X-ray powder data for fluoroapatite'],
    ['CWNeutron', 'Neutron CW Powder Data.htm', 'CW Neutron Powder fit for Yttrium-Iron Garnet'],
    ['CWCombined', 'Combined refinement.htm', 'Combined X-ray/CW-neutron refinement of PbSO4'],
    ['TOF-CW Joint Refinement', 'TOF combined XN Rietveld refinement in GSAS.htm', 'Combined X-ray/TOF-neutron Rietveld refinement'],
    ['BkgFit', 'FitBkgTut.htm',  'Fitting the Starting Background using Fixed Points'],
    
    ['Parametric Rietveld fitting'],
    ['SeqRefine', 'SequentialTutorial.htm', 'Sequential refinement of multiple datasets'],
    ['SeqParametric', 'ParametricFitting.htm', '     Parametric Fitting and Pseudo Variables for Sequential Fits'],

    ['Structure solution'],
    ['FitPeaks', 'Fit Peaks.htm', 'Fitting individual peaks & autoindexing'],
    ['CFjadarite', 'Charge Flipping in GSAS.htm', '     Charge Flipping structure solution for jadarite'],
    ['CFsucrose', 'Charge Flipping - sucrose.htm','     Charge Flipping structure solution for sucrose'],
    ['CFXraySingleCrystal', 'CFSingleCrystal.htm', 'Charge Flipping structure solution with Xray single crystal data'],       
    ['TOF Charge Flipping', 'Charge Flipping with TOF single crystal data in GSASII.htm', 'Charge flipping with neutron TOF single crystal data'],
    ['MCsimanneal', 'MCSA in GSAS.htm', 'Monte-Carlo simulated annealing structure determination'],

    ['Stacking Fault Modeling'],
    ['StackingFaults-I', 'Stacking Faults-I.htm', 'Stacking fault simulations for diamond'],
    ['StackingFaults-II', 'Stacking Faults II.htm', 'Stacking fault simulations for Keokuk kaolinite'],
    ['StackingFaults-III', 'Stacking Faults-III.htm', 'Stacking fault simulations for Georgia kaolinite'],

    ['Image Calibration/Integration'],
    ['2DCalibration', 'Calibration of an area detector in GSAS.htm', 'Calibration of an area detector'],
    ['2DIntegration', 'Integration of area detector data in GSAS.htm', '     Integration of area detector data'],
    ['TOF Calibration', 'Calibration of a TOF powder diffractometer.htm', 'Calibration of a Neutron TOF diffractometer'],

    ['Small-Angle Scattering'],       
    ['2DStrain', 'Strain fitting of 2D data in GSAS-II.htm', 'Strain fitting of 2D data'],
    ['2DTexture', 'Texture analysis of 2D data in GSAS-II.htm', 'Texture analysis of 2D data'],
              
    ['SAsize', 'Small Angle Size Distribution.htm', 'Small angle x-ray data size distribution (alumina powder)'],
    ['SAfit', 'Fitting Small Angle Scattering Data.htm', '     Fitting small angle x-ray data (alumina powder)'],
    ['SAimages', 'Small Angle Image Processing.htm', 'Image Processing of small angle x-ray data'],
    ['SAseqref', 'Sequential Refinement of Small Angle Scattering Data.htm', 'Sequential refinement with small angle scattering data'],

    ['Other'],    
    ['MerohedralTwins', 'Merohedral twin refinement in GSAS.htm', 'Merohedral twin refinements'],
    ['TOF Single Crystal Refinement', 'TOF single crystal refinement in GSAS.htm', 'Single crystal refinement from TOF data'],
    ['PythonScript','Scripting.htm','Scripting a GSAS-II Refinement from Python']
    
    #['ExampleDir', 'ExamplePage.html', 'Example Tutorial Title'],
    )
'''A catalog of GSAS-II tutorials with headings. This is the master list of GSAS-II tutorials and must be updated when tutorials are
added. Each item has either one or three items. 
Titles are single item in a list or tuple. Tutorials have three items: (a) the name of the directory,
(b) the name of the web page and (c) a title for the tutorial. 
Tutorials that depend on a previous tutorial being completed should have the title for
the tutorial indented by five spaces.

Note that :data:`tutorialCatalog` is generated from this tuple. 
Also see :mod:`makeTutorial` which is used to read this and create a web page.
'''

#A catalog of GSAS-II tutorials generated from the table in :data:`tutorialIndex`
tutorialCatalog = [l for l in tutorialIndex if len(l) == 3]

class OpenTutorial(wx.Dialog):
    '''Open a tutorial web page, optionally copying the web page, screen images and
    data file(s) to the local disk.
    '''
    
    def __init__(self,parent):
        style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        wx.Dialog.__init__(self, parent, wx.ID_ANY, 'Open Tutorial', style=style)
        self.G2frame = self.frame = parent
        pnl = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)        
        label = wx.StaticText(
            pnl,  wx.ID_ANY,
            'Select the tutorial to be run and the mode of access'
            )
        msg = '''GSAS-II tutorials and their sample data files
        require a fair amount of storage space; few users will
        use all of them. This dialog allows users to load selected
        tutorials (along with their sample data) to their computer;
        optionally all tutorials can be downloaded.

        Downloaded tutorials can be viewed and run without internet
        access. Tutorials can also be viewed without download, but
        users will need to download the sample data files manually.

        The location used to download tutorials is set using the
        "Set download location" which is saved as the "Tutorial_location"
        configuration option see File/Preference or the
        config_example.py file. System managers can select to have
        tutorial files installed at a shared location.
        '''
        self.SetTutorialPath()
        hlp = HelpButton(pnl,msg)
        sizer1.Add((-1,-1),1, wx.EXPAND, 0)
        sizer1.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 0)
        sizer1.Add((-1,-1),1, wx.EXPAND, 0)
        sizer1.Add(hlp,0,wx.ALIGN_RIGHT|wx.ALL)
        sizer.Add(sizer1,0,wx.EXPAND|wx.ALL,0)
        sizer.Add((10,10))
        sizer0 = wx.BoxSizer(wx.HORIZONTAL)        
        sizer1a = wx.BoxSizer(wx.VERTICAL)
        sizer1b = wx.BoxSizer(wx.VERTICAL)
        btn = wx.Button(pnl, wx.ID_ANY, "Download a tutorial and view")
        btn.Bind(wx.EVT_BUTTON, self.SelectAndDownload)
        sizer1a.Add(btn,0,WACV)
        btn = wx.Button(pnl, wx.ID_ANY, "Select from downloaded tutorials")
        btn.Bind(wx.EVT_BUTTON, self.onSelectDownloaded)
        sizer1a.Add(btn,0,WACV)
        btn = wx.Button(pnl, wx.ID_ANY, "Browse tutorial on web")
        btn.Bind(wx.EVT_BUTTON, self.onWebBrowse)
        sizer1a.Add(btn,0,WACV)
        btn = wx.Button(pnl, wx.ID_ANY, "Update downloaded tutorials")
        btn.Bind(wx.EVT_BUTTON, self.UpdateDownloaded)
        sizer1b.Add(btn,0,WACV)
        btn = wx.Button(pnl, wx.ID_ANY, "Download all tutorials")
        btn.Bind(wx.EVT_BUTTON, self.DownloadAll)
        sizer1b.Add(btn,0,WACV)
        sizer0.Add(sizer1a,0,wx.EXPAND|wx.ALL,0)
        sizer0.Add(sizer1b,0,wx.EXPAND|wx.ALL,0)
        sizer.Add(sizer0,5,wx.EXPAND|wx.ALL,5)
        
        sizer.Add((10,10))
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        btn = wx.Button(pnl, wx.ID_ANY, "Set download location")
        btn.Bind(wx.EVT_BUTTON, self.SelectDownloadLoc)
        sizer1.Add(btn,0,WACV)
        self.dataLoc = wx.StaticText(pnl, wx.ID_ANY,self.tutorialPath)
        sizer1.Add(self.dataLoc,0,WACV)
        sizer.Add(sizer1)
        
        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(pnl, wx.ID_CANCEL,"Done")
        btnsizer.AddButton(btn)
        btnsizer.Realize()
        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER|wx.ALL, 5)
        pnl.SetSizer(sizer)
        sizer.Fit(self)
        self.topsizer=sizer
        self.CenterOnParent()

    def SetTutorialPath(self):
        '''Get the tutorial location if set; if not pick a default
        directory in a logical place
        '''
        if GSASIIpath.GetConfigValue('Tutorial_location'):
            self.tutorialPath = os.path.abspath(GSASIIpath.GetConfigValue('Tutorial_location'))
        elif (sys.platform.lower().startswith('win') and
              os.path.exists(os.path.abspath(os.path.expanduser('~/My Documents')))):
            self.tutorialPath = os.path.abspath(os.path.expanduser('~/My Documents/G2tutorials'))
        elif (sys.platform.lower().startswith('win') and
              os.path.exists(os.path.abspath(os.path.expanduser('~/Documents')))):
            self.tutorialPath = os.path.abspath(os.path.expanduser('~/Documents/G2tutorials'))
        else:
            self.tutorialPath = os.path.abspath(os.path.expanduser('~/G2tutorials'))

    def SelectAndDownload(self,event):
        '''Make a list of all tutorials on web and allow user to choose one to
        download and then view
        '''
        indices = [j for j,i in enumerate(tutorialCatalog)
            if not os.path.exists(os.path.join(self.tutorialPath,i[0],i[1]))]
        if not indices:
            G2MessageBox(self,'All tutorials are downloaded','None to download')
            return
        choices = [tutorialCatalog[i][2] for i in indices]
        selected = self.ChooseTutorial(choices)
        if selected is None: return
        j = indices[selected]
        fullpath = os.path.join(self.tutorialPath,tutorialCatalog[j][0],tutorialCatalog[j][1])
        fulldir = os.path.join(self.tutorialPath,tutorialCatalog[j][0])
        URL = G2BaseURL+'/Tutorials/'+tutorialCatalog[j][0]+'/'
        if GSASIIpath.svnInstallDir(URL,fulldir):
            ShowWebPage(fullpath,self.frame)
        else:
            G2MessageBox(self,'Error downloading tutorial','Download error')
        self.EndModal(wx.ID_OK)
        self.G2frame.TutorialImportDir = os.path.join(self.tutorialPath,tutorialCatalog[j][0],'data')

    def onSelectDownloaded(self,event):
        '''Select a previously downloaded tutorial
        '''
        indices = [j for j,i in enumerate(tutorialCatalog)
            if os.path.exists(os.path.join(self.tutorialPath,i[0],i[1]))]
        if not indices:
            G2MessageBox(self,
                         'There are no downloaded tutorials in '+self.tutorialPath,
                         'None downloaded')
            return
        choices = [tutorialCatalog[i][2] for i in indices]
        selected = self.ChooseTutorial(choices)
        if selected is None: return
        j = indices[selected]
        fullpath = os.path.join(self.tutorialPath,tutorialCatalog[j][0],tutorialCatalog[j][1])
        self.EndModal(wx.ID_OK)
        ShowWebPage(fullpath,self.frame)
        self.G2frame.TutorialImportDir = os.path.join(self.tutorialPath,tutorialCatalog[j][0],'data')
        
    def onWebBrowse(self,event):
        '''Make a list of all tutorials on web and allow user to view one.
        '''
        choices = [i[2] for i in tutorialCatalog]
        selected = self.ChooseTutorial(choices)
        if selected is None: return        
        tutdir = tutorialCatalog[selected][0]
        tutfil = tutorialCatalog[selected][1]
        # open web page remotely, don't worry about data
        URL = G2BaseURL+'/Tutorials/'+tutdir+'/'+tutfil
        self.EndModal(wx.ID_OK)
        ShowWebPage(URL,self.frame)
        
    def ChooseTutorial(self,choices):
        'choose a tutorial from a list'
        def onDoubleClick(event):
            'double-click closes the dialog'
            dlg.EndModal(wx.ID_OK)
        dlg = wx.Dialog(self,wx.ID_ANY,
                        'Select a tutorial to view. NB: indented ones require prerequisite',
                        style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        pnl = wx.Panel(dlg)
        sizer = wx.BoxSizer(wx.VERTICAL)
        listbox = wx.ListBox(pnl, wx.ID_ANY, choices=choices,
                             size=(450, 100),
                             style=wx.LB_SINGLE)
        sizer.Add(listbox,1,WACV|wx.EXPAND|wx.ALL,1)
        listbox.Bind(wx.EVT_LISTBOX_DCLICK, onDoubleClick)
        sizer.Add((10,10))
        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(pnl, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        OKbtn = wx.Button(pnl, wx.ID_OK)
        OKbtn.SetDefault()
        btnsizer.AddButton(OKbtn)
        btnsizer.Realize()
        sizer.Add((-1,5))
        sizer.Add(btnsizer,0,wx.ALIGN_RIGHT,50)
        
        pnl.SetSizer(sizer)
        sizer.Fit(dlg)
        self.CenterOnParent()
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        selected = listbox.GetSelection()
        dlg.Destroy()
        wx.Yield() # close window right away so user sees something happen
        if selected < 0: return
        return selected

    def UpdateDownloaded(self,event):
        'Find the downloaded tutorials and run an svn update on them'
        updated = 0
        for i in tutorialCatalog:
            if not os.path.exists(os.path.join(self.tutorialPath,i[0],i[1])): continue
            print('Updating '+i[0])
            GSASIIpath.svnUpdateDir(os.path.join(self.tutorialPath,i[0]))
            updated += 0
        if not updated:
            G2MessageBox(self,'Warning, you have no downloaded tutorials','None Downloaded')
        self.EndModal(wx.ID_OK)
        
    def DownloadAll(self,event):
        'Download or update all tutorials'
        fail = ''
        for i in tutorialCatalog:
            if os.path.exists(os.path.join(self.tutorialPath,i[0],i[1])):
                print('Updating '+i[0])
                GSASIIpath.svnUpdateDir(os.path.join(self.tutorialPath,i[0]))
            else:
                fulldir = os.path.join(self.tutorialPath,i[0])
                URL = G2BaseURL+'/Tutorials/'+i[0]+'/'
                if not GSASIIpath.svnInstallDir(URL,fulldir):
                    if fail: fail += ', '
                    fail += i[0]
        if fail: 
            G2MessageBox(self,'Error downloading tutorial(s)\n\t'+fail,'Download error')
        self.EndModal(wx.ID_OK)
                    
    def SelectDownloadLoc(self,event):
        '''Select a download location,
        Cancel resets to the default
        '''
        dlg = wx.DirDialog(self, "Choose a directory for tutorial downloads:",
                           defaultPath=self.tutorialPath)#,style=wx.DD_DEFAULT_STYLE)
                           #)
        try:
            if dlg.ShowModal() != wx.ID_OK:
                return
            pth = dlg.GetPath()
        finally:
            dlg.Destroy()

        if not os.path.exists(pth):
            try:
                os.makedirs(pth)    #failing for no obvious reason
            except OSError:
                msg = 'The selected directory is not valid.\n\t'
                msg += pth
                msg += '\n\nAn attempt to create the directory failed'
                G2MessageBox(self.frame,msg)
                return
        if os.path.exists(os.path.join(pth,"help")) and os.path.exists(os.path.join(pth,"Exercises")):
            print("Note that you may have old tutorial files in the following directories")
            print('\t'+os.path.join(pth,"help"))
            print('\t'+os.path.join(pth,"Exercises"))
            print('Subdirectories in the above can be deleted to save space\n\n')
        self.tutorialPath = pth
        self.dataLoc.SetLabel(self.tutorialPath)
        if GSASIIpath.GetConfigValue('Tutorial_location') == pth: return
        vars = GetConfigValsDocs()
        try:
            vars['Tutorial_location'][1] = pth
            if GSASIIpath.GetConfigValue('debug'): print('Saving Tutorial_location: '+pth)
            GSASIIpath.SetConfigValue(vars)
            SaveConfigVars(vars)
        except KeyError:
            pass
            
if __name__ == '__main__':
    app = wx.PySimpleApp()
    GSASIIpath.InvokeDebugOpts()
    frm = wx.Frame(None) # create a frame
    frm.Show(True)
    
    #======================================================================
    # test Grid with GridFractionEditor
    #======================================================================
    # tbl = [[1.,2.,3.],[1.1,2.1,3.1]]
    # colTypes = 3*[wg.GRID_VALUE_FLOAT+':10,5',]
    # Gtbl = Table(tbl,types=colTypes,rowLabels=['a','b'],colLabels=['1','2','3'])
    # Grid = GSGrid(frm)
    # Grid.SetTable(Gtbl,True)
    # for i in (0,1,2):
    #     attr = wx.grid.GridCellAttr()
    #     attr.IncRef()
    #     attr.SetEditor(GridFractionEditor(Grid))
    #     Grid.SetColAttr(i, attr)
    # frm.SetSize((400,200))
    # app.MainLoop()
    # sys.exit()
    #======================================================================
    # test Tutorial access
    #======================================================================
    # dlg = OpenTutorial(frm)
    # if dlg.ShowModal() == wx.ID_OK:
    #     print "OK"
    # else:
    #     print "Cancel"
    # dlg.Destroy()
    # sys.exit()
    #======================================================================
    # test ScrolledMultiEditor
    #======================================================================
    # Data1 = {
    #      'Order':1,
    #      'omega':'string',
    #      'chi':2.0,
    #      'phi':'',
    #      }
    # elemlst = sorted(Data1.keys())
    # prelbl = sorted(Data1.keys())
    # dictlst = len(elemlst)*[Data1,]
    #Data2 = [True,False,False,True]
    #Checkdictlst = len(Data2)*[Data2,]
    #Checkelemlst = range(len(Checkdictlst))
    # print 'before',Data1,'\n',Data2
    # dlg = ScrolledMultiEditor(
    #     frm,dictlst,elemlst,prelbl,
    #     checkdictlst=Checkdictlst,checkelemlst=Checkelemlst,
    #     checklabel="Refine?",
    #     header="test")
    # if dlg.ShowModal() == wx.ID_OK:
    #     print "OK"
    # else:
    #     print "Cancel"
    # print 'after',Data1,'\n',Data2
    # dlg.Destroy()
    Data3 = {
         'Order':1.0,
         'omega':1.1,
         'chi':2.0,
         'phi':2.3,
         'Order1':1.0,
         'omega1':1.1,
         'chi1':2.0,
         'phi1':2.3,
         'Order2':1.0,
         'omega2':1.1,
         'chi2':2.0,
         'phi2':2.3,
         }
    elemlst = sorted(Data3.keys())
    dictlst = len(elemlst)*[Data3,]
    prelbl = elemlst[:]
    prelbl[0]="this is a much longer label to stretch things out"
    Data2 = len(elemlst)*[False,]
    Data2[1] = Data2[3] = True
    Checkdictlst = len(elemlst)*[Data2,]
    Checkelemlst = range(len(Checkdictlst))
    #print 'before',Data3,'\n',Data2
    #print dictlst,"\n",elemlst
    #print Checkdictlst,"\n",Checkelemlst
    # dlg = ScrolledMultiEditor(
    #     frm,dictlst,elemlst,prelbl,
    #     checkdictlst=Checkdictlst,checkelemlst=Checkelemlst,
    #     checklabel="Refine?",
    #     header="test",CopyButton=True)
    # if dlg.ShowModal() == wx.ID_OK:
    #     print "OK"
    # else:
    #     print "Cancel"
    #print 'after',Data3,'\n',Data2

    # Data2 = list(range(100))
    # elemlst += range(2,6)
    # postlbl += range(2,6)
    # dictlst += len(range(2,6))*[Data2,]

    # prelbl = range(len(elemlst))
    # postlbl[1] = "a very long label for the 2nd item to force a horiz. scrollbar"
    # header="""This is a longer\nmultiline and perhaps silly header"""
    # dlg = ScrolledMultiEditor(frm,dictlst,elemlst,prelbl,postlbl,
    #                           header=header,CopyButton=True)
    # print Data1
    # if dlg.ShowModal() == wx.ID_OK:
    #     for d,k in zip(dictlst,elemlst):
    #         print k,d[k]
    # dlg.Destroy()
    # if CallScrolledMultiEditor(frm,dictlst,elemlst,prelbl,postlbl,
    #                            header=header):
    #     for d,k in zip(dictlst,elemlst):
    #         print k,d[k]

    #======================================================================
    # test G2MultiChoiceDialog
    #======================================================================
    choices = []
    for i in range(21):
        choices.append("option_"+str(i))
    od = {
        'label_1':'This is a bool','value_1':True,
        'label_2':'This is a int','value_2':-1,
        'label_3':'This is a float','value_3':1.0,
        'label_4':'This is a string','value_4':'test',}
    dlg = G2MultiChoiceDialog(frm, 'Sequential refinement',
                              'Select dataset to include',
                              choices,extraOpts=od)
    sel = range(2,11,2)
    dlg.SetSelections(sel)
    dlg.SetSelections((1,5))
    if dlg.ShowModal() == wx.ID_OK:
        for sel in dlg.GetSelections():
            print (sel,choices[sel])
    print (od)
    od = {}
    dlg = G2MultiChoiceDialog(frm, 'Sequential refinement',
                              'Select dataset to include',
                              choices,extraOpts=od)
    sel = range(2,11,2)
    dlg.SetSelections(sel)
    dlg.SetSelections((1,5))
    if dlg.ShowModal() == wx.ID_OK: pass
    #======================================================================
    # test wx.MultiChoiceDialog
    #======================================================================
    # dlg = wx.MultiChoiceDialog(frm, 'Sequential refinement',
    #                           'Select dataset to include',
    #                           choices)
    # sel = range(2,11,2)
    # dlg.SetSelections(sel)
    # dlg.SetSelections((1,5))
    # if dlg.ShowModal() == wx.ID_OK:
    #     for sel in dlg.GetSelections():
    #         print sel,choices[sel]

    # pnl = wx.Panel(frm)
    # siz = wx.BoxSizer(wx.VERTICAL)

    # td = {'Goni':200.,'a':1.,'calc':1./3.,'string':'s'}
    # for key in sorted(td):
    #     txt = ValidatedTxtCtrl(pnl,td,key)
    #     siz.Add(txt)
    # pnl.SetSizer(siz)
    # siz.Fit(frm)
    # app.MainLoop()
    # print td
