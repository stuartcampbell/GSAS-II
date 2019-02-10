#!/usr/bin/env python
# -*- coding: utf-8 -*-
########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### SVN repository information ###################
#
# TODO: integrate 2d data based on a model
#
"""
*GSASIIscriptable: Scripting Interface*
=======================================

Routines for reading, writing, modifying and creating GSAS-II project (.gpx) files.
This file specifies several wrapper classes around GSAS-II data representations.
They all inherit from :class:`G2ObjectWrapper`. The chief class is :class:`G2Project`,
which represents an entire GSAS-II project and provides several methods to access
phases, powder histograms, and execute Rietveld refinements. These routines can be
accessed in two ways: 
the :ref:`CommandlineInterface` provides access a number of features without writing
Python scripts of from the :ref:`API`, which allows much more versatile access from
within Python. 


=====================
Overview
=====================
The most commonly used routines are:

:class:`G2Project`
   Always needed: used to create a new project (.gpx) file or read in an existing one.

:meth:`G2Project.add_powder_histogram`
   Used to read in powder diffraction data to a project file.

:meth:`G2Project.add_simulated_powder_histogram`
   Defines a "dummy" powder diffraction data that will be simulated after a refinement step.

:meth:`G2Project.save`
   Writes the current project to disk.

:meth:`G2Project.do_refinements`
   This is passed a list of dictionaries, where each dict defines a refinement step.
   Passing a list with a single empty dict initiates a refinement with the current
   parameters and flags.
   
:meth:`G2Project.set_refinement`
   This is passed a single dict which is used to set parameters and flags.
   These actions can be performed also in :meth:`G2Project.do_refinements`. 

Refinement dicts
   A refinement dict sets up a single refinement step
   (as used in :meth:`G2Project.do_refinements` and described in
   :ref:`Project_dicts`). 
   It specifies parameter & refinement flag changes, which are usually followed by a refinement and
   optionally by calls to locally-defined Python functions. The keys used in these dicts are
   defined in the :ref:`Refinement_recipe` table, below.

There are several ways to set parameters project using different level objects, as is 
are described in sections below, but the simplest way to access parameters and flags
in a project is to use the above routines. 

=====================
Refinement parameters
=====================
The most complex part of scripting GSAS-II comes in setting up the input to control refinements, which is
described here. 

.. _Project_dicts:

-----------------------------
Project-level Parameter Dict
-----------------------------

As noted below (:ref:`Refinement_parameters_kinds`), there are three types of refinement parameters,
which can be accessed individually by the objects that encapsulate individual phases and histograms
but it will be usually simplest to create a composite dictionary
that is used at the project-level. A dict is created with keys
"set" and "clear" that can be supplied to :meth:`G2Project.set_refinement`
(or :meth:`G2Project.do_refinements`, see :ref:`Refinement_recipe` below) that will
determine parameter values and will determine which parameters will be refined. 

The specific keys and subkeys that can be used are defined in tables 
:ref:`Histogram_parameters_table`, :ref:`Phase_parameters_table` and :ref:`HAP_parameters_table`.

Note that optionally a list of histograms and/or phases can be supplied in the call to 
:meth:`G2Project.set_refinement`, but if not specified, the default is to use all defined
phases and histograms. 

As an example: 

.. code-block::  python

    pardict = {'set': { 'Limits': [0.8, 12.0],
                       'Sample Parameters': ['Absorption', 'Contrast', 'DisplaceX'],
                       'Background': {'type': 'chebyschev', 'refine': True}},
              'clear': {'Instrument Parameters': ['U', 'V', 'W']}}
    my_project.set_refinement(pardict)
    
.. _Refinement_recipe:
    
------------------------
Refinement recipe
------------------------
Building on the :ref:`Project_dicts`,
it is possible to specify a sequence of refinement actions as a list of
these dicts and supplying this list 
as an argument to :meth:`G2Project.do_refinements`.

As an example, this code performs the same actions as in the example in the section above: 

.. code-block::  python
    
    pardict = {'set': { 'Limits': [0.8, 12.0],
                       'Sample Parameters': ['Absorption', 'Contrast', 'DisplaceX'],
                       'Background': {'type': 'chebyschev', 'refine': True}},
              'clear': {'Instrument Parameters': ['U', 'V', 'W']}}
    my_project.do_refinements([pardict])

However, in addition to setting a number of parameters, this example will perform a refinement as well.
If more than one dict is specified in the list, as is done in this example,
two refinement steps will be performed:

.. code-block::  python

    my_project.do_refinements([pardict,pardict1])


The keys defined in the following table
may be used in a dict supplied to :meth:`G2Project.do_refinements`. Note that now keys ``histograms``
and ``phases`` are used to limit actions to specific sets of parameters within the project. 

========== ============================================================================
key         explanation
========== ============================================================================
set                    Specifies a dict with keys and subkeys as described in the
                       :ref:`Refinement_parameters_fmt` section. Items listed here
                       will be set to be refined.
clear                  Specifies a dict, as above for set, except that parameters are
                       cleared and thus will not be refined.
once                   Specifies a dict as above for set, except that parameters are
                       set for the next cycle of refinement and are cleared once the
                       refinement step is completed.
skip                   Normally, once parameters are processed with a set/clear/once
                       action(s), a refinement is started. If skip is defined as True
                       (or any other value) the refinement step is not performed.
output                 If a file name is specified for output is will be used to save
                       the current refinement. 
histograms             Should contain a list of histogram(s) to be used for the
                       set/clear/once action(s) on :ref:`Histogram_parameters_table` or
                       :ref:`HAP_parameters_table`. Note that this will be
                       ignored for :ref:`Phase_parameters_table`. Histograms may be
                       specified as a list of strings [('PWDR ...'),...], indices
                       [0,1,2] or as list of objects [hist1, hist2]. 
phases                 Should contain a list of phase(s) to be used for the
                       set/clear/once action(s) on :ref:`Phase_parameters_table` or 
                       :ref:`HAP_parameters_table`. Note that this will be
                       ignored for :ref:`Histogram_parameters_table`.
                       Phases may be specified as a list of strings
                       [('Phase name'),...], indices [0,1,2] or as list of objects
                       [phase0, phase2]. 
call                   Specifies a function to call after a refinement is completed.
                       The value supplied can be the object (typically a function)
                       that will be called or a string that will evaluate (in the
                       namespace inside :meth:`G2Project.iter_refinements` where
                       ``self`` references the project.)
                       Nothing is called if this is not specified.
callargs               Provides a list of arguments that will be passed to the function
                       in call (if any). If call is defined and callargs is not, the
                       current <tt>G2Project</tt> is passed as a single argument. 
========== ============================================================================

An example that performs a series of refinement steps follows:

.. code-block::  python

    reflist = [
            {"set": { "Limits": { "low": 0.7 },
                      "Background": { "no. coeffs": 3,
                                      "refine": True }}},
            {"set": { "LeBail": True,
                      "Cell": True }},
            {"set": { "Sample Parameters": ["DisplaceX"]}},
            {"set": { "Instrument Parameters": ["U", "V", "W", "X", "Y"]}},
            {"set": { "Mustrain": { "type": "uniaxial",
                                    "refine": "equatorial",
                                    "direction": [0, 0, 1]}}},
            {"set": { "Mustrain": { "type": "uniaxial",
                                    "refine": "axial"}}},
            {"clear": { "LeBail": True},
             "set": { "Atoms": { "Mn": "X" }}},
            {"set": { "Atoms": { "O1": "X", "O2": "X" }}},]
    my_project.do_refinements(reflist)
    

In this example, a separate refinement step will be performed for each dict in the list (since
"skip" is not included). 
Note that in the second from last refinement step, parameters are both set and cleared. 
   
.. _Refinement_parameters_kinds:

----------------------------
Refinement parameter types
----------------------------

Note that parameters and refinement flags used in GSAS-II fall into three classes:

    * **Histogram**: There will be a set of these for each dataset loaded into a
      project file. The parameters available depend on the type of histogram
      (Bragg-Brentano, Single-Crystal, TOF,...). Typical Histogram parameters
      include the overall scale factor, background, instrument and sample parameters;
      see the :ref:`Histogram_parameters_table` table for a list of the histogram
      parameters where access has been provided.
      
    * **Phase**: There will be a set of these for each phase loaded into a
      project file. While some parameters are found in all types of phases,
      others are only found in certain types (modulated, magnetic, protein...).
      Typical phase parameters include unit cell lengths and atomic positions; see the
      :ref:`Phase_parameters_table` table for a list of the phase      
      parameters where access has been provided.
      
    * **Histogram-and-phase** (HAP): There is a set of these for every histogram
      that is associated with each phase, so that if there are ``N`` phases and ``M``
      histograms, there can be ``N*M`` total sets of "HAP" parameters sets (fewer if all
      histograms are not linked to all phases.) Typical HAP parameters include the
      phase fractions, sample microstrain and crystallite size broadening terms,
      hydrostatic strain perturbations of the unit cell and preferred orientation
      values.
      See the :ref:`HAP_parameters_table` table for the HAP parameters where access has
      been provided. 

.. _Refinement_parameters_fmt:

=================================
Specifying Refinement Parameters
=================================

Refinement parameter values and flags to turn refinement on and off are specified within dictionaries,
where the details of these dicts are organized depends on the
type of parameter (see :ref:`Refinement_parameters_kinds`), with a different set
of keys (as described below) for each of the three types of parameters.

.. _Histogram_parameters_table:

--------------------
Histogram parameters
--------------------

This table describes the dictionaries supplied to :func:`G2PwdrData.set_refinements`
and :func:`G2PwdrData.clear_refinements`. As an example, 

.. code-block::  python

   hist.set_refinements({"Background": {"no.coeffs": 3, "refine": True},
                         "Sample Parameters": ["Scale"],
                         "Limits": [10000, 40000]})

With :meth:`G2Project.do_refinements`, these parameters should be placed inside a dict with a key
``set``, ``clear``, or ``once``. Values will be set for all histograms, unless the ``histograms``
key is used to define specific histograms. As an example: 

.. code-block::  python

  gsas_proj.do_refinements([
      {'set': {
          'Background': {'no.coeffs': 3, 'refine': True},
          'Sample Parameters': ['Scale'],
          'Limits': [10000, 40000]},
      'histograms': [1,2]}
                            ])

Note that below in the Instrument Parameters section, 
related profile parameters (such as U and V) are grouped together but
separated by commas to save space in the table.

.. tabularcolumns:: |l|l|p{3.5in}|

===================== ====================  =================================================
key                   subkey                explanation
===================== ====================  =================================================
Limits                                      The range of 2-theta (degrees) or TOF (in 
                                            microsec) range of values to use. Can
                                            be either a dictionary of 'low' and/or 'high',
                                            or a list of 2 items [low, high]
\                     low                   Sets the low limit
\                     high                  Sets the high limit

Sample Parameters                           Should be provided as a **list** of subkeys
                                            to set or clear, e.g. ['DisplaceX', 'Scale']
\                     Absorption
\                     Contrast
\                     DisplaceX             Sample displacement along the X direction
\                     DisplaceY             Sample displacement along the Y direction
\                     Scale                 Histogram Scale factor

Background                                  Sample background. If value is a boolean,
                                            the background's 'refine' parameter is set
                                            to the given boolean. Usually should be a
                                            dictionary with any of the following keys:
\                     type                  The background model, e.g. 'chebyschev'
\                     refine                The value of the refine flag, boolean
\                     no. coeffs            Number of coefficients to use, integer
\                     coeffs                List of floats, literal values for background
\                     FixedPoints           List of (2-theta, intensity) values for fixed points
\                     fit fixed points      If True, triggers a fit to the fixed points to
                                            be calculated. It is calculated when this key is
                                            detected, regardless of calls to refine.

Instrument Parameters                       As in Sample Paramters, provide as a **list** of
                                            subkeys to
                                            set or clear, e.g. ['X', 'Y', 'Zero', 'SH/L']
\                     U, V, W               Gaussian peak profile terms
\                     X, Y, Z               Lorentzian peak profile terms
\                     alpha, beta-0,        TOF profile terms 
                      beta-1, beta-q,
\                     sig-0, sig-1,         TOF profile terms
                      sig-2, sig-q
\                     difA, difB, difC      TOF Calibration constants
\                     Zero                  Zero shift
\                     SH/L                  Finger-Cox-Jephcoat low-angle peak asymmetry
\                     Polariz.              Polarization parameter
\                     Lam                   Lambda, the incident wavelength
===================== ====================  =================================================

.. _Phase_parameters_table:

----------------
Phase parameters
----------------

This table describes the dictionaries supplied to :func:`G2Phase.set_refinements`
and :func:`G2Phase.clear_refinements`. With :meth:`G2Project.do_refinements`,
these parameters should be placed inside a dict with a key
``set``, ``clear``, or ``once``. Values will be set for all phases, unless the ``phases``
key is used to define specific phase(s). 


.. tabularcolumns:: |l|p{4.5in}|

======= ==========================================================
key                   explanation
======= ==========================================================
Cell                  Whether or not to refine the unit cell.
Atoms                 Dictionary of atoms and refinement flags.
                      Each key should be an atom label, e.g.
                      'O3', 'Mn5', and each value should be
                      a string defining what values to refine.
                      Values can be any combination of 'F'
                      for fractional occupancy, 'X' for position,
                      and 'U' for Debye-Waller factor
LeBail                Enables LeBail intensity extraction.
======= ==========================================================


.. _HAP_parameters_table:


Histogram-and-phase parameters
------------------------------

This table describes the dictionaries supplied to :func:`G2Phase.set_HAP_refinements`
and :func:`G2Phase.clear_HAP_refinements`. When supplied to
:meth:`G2Project.do_refinements`, these parameters should be placed inside a dict with a key
``set``, ``clear``, or ``once``. Values will be set for all histograms used in each phase,
unless the ``histograms`` and ``phases`` keys are used to define specific phases and histograms.

.. tabularcolumns:: |l|l|p{3.5in}|

=============  ==========  ============================================================
key             subkey                 explanation
=============  ==========  ============================================================
Babinet                                Should be a **list** of the following
                                       subkeys. If not, assumes both
                                       BabA and BabU
\               BabA
\               BabU
Extinction                             Boolean, True to refine.
HStrain                                Boolean, True to refine all appropriate
                                       $D_ij$ terms.
Mustrain
\               type                   Mustrain model. One of 'isotropic',
                                       'uniaxial', or 'generalized'. Should always
                                       be specified.
\              direction               For uniaxial only. A list of three
                                       integers,
                                       the [hkl] direction of the axis.
\               refine                 Usually boolean, set to True to refine.
                                       or False to clear. 
                                       For uniaxial model, can specify a value
                                       of 'axial' or 'equatorial' to set that flag
                                       to True or a single
                                       boolean sets both axial and equatorial.
Size                                   
\               type                   Size broadening model. One of 'isotropic',
                                       'uniaxial', or 'ellipsoid'. Should always
                                       be specified.
\              direction               For uniaxial only. A list of three
                                       integers,
                                       the [hkl] direction of the axis.
\               refine                 Boolean, True to refine.
\               value                  float, size value in microns 
Pref.Ori.                              Boolean, True to refine
Show                                   Boolean, True to refine
Use                                    Boolean, True to refine
Scale                                  Phase fraction; Boolean, True to refine
=============  ==========  ============================================================

------------------------
Histogram/Phase objects
------------------------
Each phase and powder histogram in a :class:`G2Project` object has an associated
object. Parameters within each individual object can be turned on and off by calling
:meth:`G2PwdrData.set_refinements` or :meth:`G2PwdrData.clear_refinements`
for histogram parameters;
:meth:`G2Phase.set_refinements` or :meth:`G2Phase.clear_refinements`
for phase parameters; and :meth:`G2Phase.set_HAP_refinements` or
:meth:`G2Phase.clear_HAP_refinements`. As an example, if some_histogram is a histogram object (of type :class:`G2PwdrData`), use this to set parameters in that histogram:

.. code-block::  python

    params = { 'Limits': [0.8, 12.0],
               'Sample Parameters': ['Absorption', 'Contrast', 'DisplaceX'],
               'Background': {'type': 'chebyschev', 'refine': True}}
    some_histogram.set_refinements(params)

Likewise to turn refinement flags on, use code such as this:

.. code-block::  python

    params = { 'Instrument Parameters': ['U', 'V', 'W']} 
    some_histogram.set_refinements(params)

and to turn these refinement flags, off use this (Note that the
``.clear_refinements()`` methods will usually will turn off refinement even
if a refinement parameter is set in the dict to True.):

.. code-block::  python

    params = { 'Instrument Parameters': ['U', 'V', 'W']} 
    some_histogram.clear_refinements(params)

For phase parameters, use code such as this:
    
.. code-block::  python

    params = { 'LeBail': True, 'Cell': True,
               'Atoms': { 'Mn1': 'X',
                          'O3': 'XU',
                          'V4': 'FXU'}}
    some_histogram.set_refinements(params)


and here is an example for HAP parameters:

.. code-block::  python

    params = { 'Babinet': 'BabA',
               'Extinction': True,
               'Mustrain': { 'type': 'uniaxial',
                             'direction': [0, 0, 1],
                             'refine': True}}
    some_phase.set_HAP_refinements(params)

Note that the parameters must match the object type and method (phase vs. histogram vs. HAP).

.. _CommandlineInterface:

=======================================
GSASIIscriptable Command-line Interface
=======================================

The routines described above are intended to be called from a Python script, but an
alternate way to access some of the same functionality is to 
invoke the ``GSASIIscriptable.py`` script from 
the command line usually from within a shell script or batch file. This
will usually be done with a command such as::

       python <path/>GSASIIscriptable.py <subcommand> <file.gpx> <options>

    The following subcommands are defined:

        * create, see :func:`create`
        * add, see :func:`add`
        * dump, see :func:`dump`
        * refine, see :func:`refine`
        * seqrefine, see :func:`seqrefine`
        * export, :func:`export`
        * browse, see :func:`IPyBrowse`
        
Run::

   python GSASIIscriptable.py --help

to show the available subcommands, and inspect each subcommand with
`python GSASIIscriptable.py <subcommand> --help` or see the documentation for each of the above routines.

.. _JsonFormat:

-------------------------
Parameters in JSON files
-------------------------

The refine command requires two inputs: an existing GSAS-II project (.gpx) file and
a JSON format file
(see `Introducing JSON <http://json.org/>`_) that contains a single dict.
This dict may have two keys:

refinements:
  This defines the a set of refinement steps in a JSON representation of a
  :ref:`Refinement_recipe` list. 

code:
  This optionally defines Python code that will be executed after the project is loaded,
  but before the refinement is started. This can be used to execute Python code to change
  parameters that are not accessible via a :ref:`Refinement_recipe` dict (note that the
  project object is accessed with variable ``proj``) or to define code that will be called
  later (see key ``call`` in the :ref:`Refinement_recipe` section.)
    
JSON website: `Introducing JSON <http://json.org/>`_.

.. _API:

============================================================
GSASIIscriptable Application Layer (API)
============================================================

The large number of classes and modules in this module are described below.
Most commonly a script will create a G2Project object using :class:`G2Project` and then
perform actions such as
adding a histogram (method :meth:`G2Project.add_powder_histogram`),
adding a phase (method :meth:`G2Project.add_phase`),
or setting parameters and performing a refinement
(method :meth:`G2Project.do_refinements`).

In some cases, it may be easier to use
methods inside :class:`G2PwdrData` or :class:`G2Phase` or these objects 
may offer more options.

---------------------------------------------------------------
Complete Documentation: All classes and functions
---------------------------------------------------------------
"""
from __future__ import division, print_function
import argparse
import os.path as ospath
import datetime as dt
import sys
import platform
if '2' in platform.python_version_tuple()[0]:
    import cPickle
    strtypes = (str,unicode)
else:
    import _pickle as cPickle
    strtypes = (str,bytes)
import imp
import copy
import os
import random as ran

import numpy.ma as ma
import scipy.interpolate as si
import numpy as np
import scipy as sp

import GSASIIpath
GSASIIpath.SetBinaryPath(True)  # for now, this is needed before some of these modules can be imported
import GSASIIobj as G2obj
import GSASIIpwd as G2pwd
import GSASIIstrMain as G2strMain
#import GSASIIIO as G2IO
import GSASIIstrIO as G2strIO
import GSASIIspc as G2spc
import GSASIIElem as G2elem
import GSASIIfiles as G2fil

# Delay imports to not slow down small scripts that don't need them
Readers = {'Pwdr':[], 'Phase':[], 'Image':[]}
'''Readers by reader type'''
exportersByExtension = {}
'''Specifies the list of extensions that are supported for Powder data export'''

def LoadG2fil():
    """Delay importing this module, it is slow"""
    if len(Readers['Pwdr']) > 0: return
    # initialize imports
    Readers['Pwdr'] = G2fil.LoadImportRoutines("pwd", "Powder_Data")
    Readers['Phase'] = G2fil.LoadImportRoutines("phase", "Phase")
    Readers['Image'] = G2fil.LoadImportRoutines("img", "Image")

    # initialize exports
    for obj in exportersByExtension:
        try:
            obj.Writer
        except AttributeError:
            continue
        for typ in obj.exporttype:
            if typ not in exportersByExtension:
                exportersByExtension[typ] = {obj.extension:obj}
            else:
                exportersByExtension[typ][obj.extension] = obj

def LoadDictFromProjFile(ProjFile):
    '''Read a GSAS-II project file and load items to dictionary
    
    :param str ProjFile: GSAS-II project (name.gpx) full file name
    :returns: Project,nameList, where

      * Project (dict) is a representation of gpx file following the GSAS-II tree structure
        for each item: key = tree name (e.g. 'Controls','Restraints',etc.), data is dict
        data dict = {'data':item data whch may be list, dict or None,'subitems':subdata (if any)}
      * nameList (list) has names of main tree entries & subentries used to reconstruct project file

    Example for fap.gpx::

      Project = {                 #NB:dict order is not tree order
        'Phases':{'data':None,'fap':{phase dict}},
        'PWDR FAP.XRA Bank 1':{'data':[histogram data list],'Comments':comments,'Limits':limits, etc},
        'Rigid bodies':{'data': {rigid body dict}},
        'Covariance':{'data':{covariance data dict}},
        'Controls':{'data':{controls data dict}},
        'Notebook':{'data':[notebook list]},
        'Restraints':{'data':{restraint data dict}},
        'Constraints':{'data':{constraint data dict}}]
        }
      nameList = [                #NB: reproduces tree order
        ['Notebook',],
        ['Controls',],
        ['Covariance',],
        ['Constraints',],
        ['Restraints',],
        ['Rigid bodies',],
        ['PWDR FAP.XRA Bank 1',
             'Comments',
             'Limits',
             'Background',
             'Instrument Parameters',
             'Sample Parameters',
             'Peak List',
             'Index Peak List',
             'Unit Cells List',
             'Reflection Lists'],
        ['Phases', 'fap']
        ]
    '''
    # Let IOError be thrown if file does not exist
    if not ospath.exists(ProjFile):
        print ('\n*** Error attempt to open project file that does not exist: \n    {}'.
                   format(ProjFile))
        raise IOError('GPX file {} does not exist'.format(ProjFile))
    try:
        Project, nameList = G2strIO.GetFullGPX(ProjFile)
    except Exception as msg:
        raise IOError(msg)
    return Project,nameList

def SaveDictToProjFile(Project,nameList,ProjFile):
    '''Save a GSAS-II project file from dictionary/nameList created by LoadDictFromProjFile

    :param dict Project: representation of gpx file following the GSAS-II
        tree structure as described for LoadDictFromProjFile
    :param list nameList: names of main tree entries & subentries used to reconstruct project file
    :param str ProjFile: full file name for output project.gpx file (including extension)
    '''
    file = open(ProjFile,'wb')
    try:
        for name in nameList:
            data = []
            item = Project[name[0]]
            data.append([name[0],item['data']])
            for item2 in name[1:]:
                data.append([item2,item[item2]])
            cPickle.dump(data,file,1)
    finally:
        file.close()

# def ImportPowder(reader,filename):
#     '''Use a reader to import a powder diffraction data file

#     :param str reader: a scriptable reader
#     :param str filename: full name of powder data file; can be "multi-Bank" data

#     :returns: list rdlist: list of reader objects containing powder data, one for each
#         "Bank" of data encountered in file. Items in reader object of interest are:

#           * rd.comments: list of str: comments found on powder file
#           * rd.dnames: list of str: data nammes suitable for use in GSASII data tree NB: duplicated in all rd entries in rdlist
#           * rd.powderdata: list of numpy arrays: pos,int,wt,zeros,zeros,zeros as needed for a PWDR entry in  GSASII data tree.
#     '''
#     rdfile,rdpath,descr = imp.find_module(reader)
#     rdclass = imp.load_module(reader,rdfile,rdpath,descr)
#     rd = rdclass.GSAS_ReaderClass()
#     if not rd.scriptable:
#         print(u'**** ERROR: '+reader+u' is not a scriptable reader')
#         return None
#     rdlist = []
#     if rd.ContentsValidator(filename):
#         repeat = True
#         rdbuffer = {} # create temporary storage for file reader
#         block = 0
#         while repeat: # loop if the reader asks for another pass on the file
#             block += 1
#             repeat = False
#             rd.objname = ospath.basename(filename)
#             flag = rd.Reader(filename,None,buffer=rdbuffer,blocknum=block,)
#             if flag:
#                 rdlist.append(copy.deepcopy(rd)) # save the result before it is written over
#                 if rd.repeat:
#                     repeat = True
#         return rdlist
#     print(rd.errors)
#     return None

def SetDefaultDData(dType,histoName,NShkl=0,NDij=0):
    '''Create an initial Histogram dictionary

    Author: Jackson O'Donnell (jacksonhodonnell .at. gmail.com)
    '''
    if dType in ['SXC','SNC']:
        return {'Histogram':histoName,'Show':False,'Scale':[1.0,True],
            'Babinet':{'BabA':[0.0,False],'BabU':[0.0,False]},
            'Extinction':['Lorentzian','None', {'Tbar':0.1,'Cos2TM':0.955,
            'Eg':[1.e-10,False],'Es':[1.e-10,False],'Ep':[1.e-10,False]}],
            'Flack':[0.0,False]}
    elif dType == 'SNT':
        return {'Histogram':histoName,'Show':False,'Scale':[1.0,True],
            'Babinet':{'BabA':[0.0,False],'BabU':[0.0,False]},
            'Extinction':['Lorentzian','None', {
            'Eg':[1.e-10,False],'Es':[1.e-10,False],'Ep':[1.e-10,False]}]}
    elif 'P' in dType:
        return {'Histogram':histoName,'Show':False,'Scale':[1.0,False],
            'Pref.Ori.':['MD',1.0,False,[0,0,1],0,{},[],0.1],
            'Size':['isotropic',[1.,1.,1.],[False,False,False],[0,0,1],
                [1.,1.,1.,0.,0.,0.],6*[False,]],
            'Mustrain':['isotropic',[1000.0,1000.0,1.0],[False,False,False],[0,0,1],
                NShkl*[0.01,],NShkl*[False,]],
            'HStrain':[NDij*[0.0,],NDij*[False,]],
            'Extinction':[0.0,False],'Babinet':{'BabA':[0.0,False],'BabU':[0.0,False]}}


def PreSetup(data):
    '''Create part of an initial (empty) phase dictionary

    from GSASIIphsGUI.py, near end of UpdatePhaseData

    Author: Jackson O'Donnell (jacksonhodonnell .at. gmail.com)
    '''
    if 'RBModels' not in data:
        data['RBModels'] = {}
    if 'MCSA' not in data:
        data['MCSA'] = {'Models':[{'Type':'MD','Coef':[1.0,False,[.8,1.2],],'axis':[0,0,1]}],'Results':[],'AtInfo':{}}
    if 'dict' in str(type(data['MCSA']['Results'])):
        data['MCSA']['Results'] = []
    if 'Modulated' not in data['General']:
        data['General']['Modulated'] = False
#    if 'modulated' in data['General']['Type']:
#        data['General']['Modulated'] = True
#        data['General']['Type'] = 'nuclear'


def SetupGeneral(data, dirname):
    """Helps initialize phase data.

    From GSASIIphsGui.py, function of the same name. Minor changes for imports etc.

    Author: Jackson O'Donnell (jacksonhodonnell .at. gmail.com)
    """
    mapDefault = {'MapType':'','RefList':'','Resolution':0.5,'Show bonds':True,
                'rho':[],'rhoMax':0.,'mapSize':10.0,'cutOff':50.,'Flip':False}
    generalData = data['General']
    atomData = data['Atoms']
    generalData['AtomTypes'] = []
    generalData['Isotopes'] = {}

    if 'Isotope' not in generalData:
        generalData['Isotope'] = {}
    if 'Data plot type' not in generalData:
        generalData['Data plot type'] = 'Mustrain'
    if 'POhkl' not in generalData:
        generalData['POhkl'] = [0,0,1]
    if 'Map' not in generalData:
        generalData['Map'] = mapDefault.copy()
    if 'Flip' not in generalData:
        generalData['Flip'] = {'RefList':'','Resolution':0.5,'Norm element':'None',
            'k-factor':0.1,'k-Max':20.,}
    if 'testHKL' not in generalData['Flip']:
        generalData['Flip']['testHKL'] = [[0,0,2],[2,0,0],[1,1,1],[0,2,0],[1,2,3]]
    if 'doPawley' not in generalData:
        generalData['doPawley'] = False     #ToDo: change to ''
    if 'Pawley dmin' not in generalData:
        generalData['Pawley dmin'] = 1.0
    if 'Pawley neg wt' not in generalData:
        generalData['Pawley neg wt'] = 0.0
    if 'Algolrithm' in generalData.get('MCSA controls',{}) or \
        'MCSA controls' not in generalData:
        generalData['MCSA controls'] = {'Data source':'','Annealing':[50.,0.001,50],
        'dmin':2.0,'Algorithm':'log','Jump coeff':[0.95,0.5],'boltzmann':1.0,
        'fast parms':[1.0,1.0,1.0],'log slope':0.9,'Cycles':1,'Results':[],'newDmin':True}
    if 'AtomPtrs' not in generalData:
        generalData['AtomPtrs'] = [3,1,7,9]
        if generalData['Type'] == 'macromolecular':
            generalData['AtomPtrs'] = [6,4,10,12]
        elif generalData['Type'] == 'magnetic':
            generalData['AtomPtrs'] = [3,1,10,12]
    if generalData['Modulated']:
        generalData['Type'] = 'nuclear'
        if 'Super' not in generalData:
            generalData['Super'] = 1
            generalData['SuperVec'] = [[0,0,.1],False,4]
            generalData['SSGData'] = {}
        if '4DmapData' not in generalData:
            generalData['4DmapData'] = mapDefault.copy()
            generalData['4DmapData'].update({'MapType':'Fobs'})
    if 'Modulated' not in generalData:
        generalData['Modulated'] = False
    if 'HydIds' not in generalData:
        generalData['HydIds'] = {}
    cx,ct,cs,cia = generalData['AtomPtrs']
    generalData['NoAtoms'] = {}
    generalData['BondRadii'] = []
    generalData['AngleRadii'] = []
    generalData['vdWRadii'] = []
    generalData['AtomMass'] = []
    generalData['Color'] = []
    if generalData['Type'] == 'magnetic':
        generalData['MagDmin'] = generalData.get('MagDmin',1.0)
        landeg = generalData.get('Lande g',[])
    generalData['Mydir'] = dirname
    badList = {}
    for iat,atom in enumerate(atomData):
        atom[ct] = atom[ct].lower().capitalize()              #force to standard form
        if generalData['AtomTypes'].count(atom[ct]):
            generalData['NoAtoms'][atom[ct]] += atom[cx+3]*float(atom[cs+1])
        elif atom[ct] != 'UNK':
            Info = G2elem.GetAtomInfo(atom[ct])
            if not Info:
                if atom[ct] not in badList:
                    badList[atom[ct]] = 0
                badList[atom[ct]] += 1
                atom[ct] = 'UNK'
                continue
            atom[ct] = Info['Symbol'] # N.B. symbol might be changed by GetAtomInfo
            generalData['AtomTypes'].append(atom[ct])
            generalData['Z'] = Info['Z']
            generalData['Isotopes'][atom[ct]] = Info['Isotopes']
            generalData['BondRadii'].append(Info['Drad'])
            generalData['AngleRadii'].append(Info['Arad'])
            generalData['vdWRadii'].append(Info['Vdrad'])
            if atom[ct] in generalData['Isotope']:
                if generalData['Isotope'][atom[ct]] not in generalData['Isotopes'][atom[ct]]:
                    isotope = list(generalData['Isotopes'][atom[ct]].keys())[-1]
                    generalData['Isotope'][atom[ct]] = isotope
                generalData['AtomMass'].append(Info['Isotopes'][generalData['Isotope'][atom[ct]]]['Mass'])
            else:
                generalData['Isotope'][atom[ct]] = 'Nat. Abund.'
                if 'Nat. Abund.' not in generalData['Isotopes'][atom[ct]]:
                    isotope = list(generalData['Isotopes'][atom[ct]].keys())[-1]
                    generalData['Isotope'][atom[ct]] = isotope
                generalData['AtomMass'].append(Info['Mass'])
            generalData['NoAtoms'][atom[ct]] = atom[cx+3]*float(atom[cs+1])
            generalData['Color'].append(Info['Color'])
            if generalData['Type'] == 'magnetic':
                if len(landeg) < len(generalData['AtomTypes']):
                    landeg.append(2.0)
    if generalData['Type'] == 'magnetic':
        generalData['Lande g'] = landeg[:len(generalData['AtomTypes'])]

    if badList:
        msg = 'Warning: element symbol(s) not found:'
        for key in badList:
            msg += '\n\t' + key
            if badList[key] > 1:
                msg += ' (' + str(badList[key]) + ' times)'
        raise G2ScriptException("Phase error:\n" + msg)
        # wx.MessageBox(msg,caption='Element symbol error')
    F000X = 0.
    F000N = 0.
    for i,elem in enumerate(generalData['AtomTypes']):
        F000X += generalData['NoAtoms'][elem]*generalData['Z']
        isotope = generalData['Isotope'][elem]
        F000N += generalData['NoAtoms'][elem]*generalData['Isotopes'][elem][isotope]['SL'][0]
    generalData['F000X'] = F000X
    generalData['F000N'] = F000N
    import GSASIImath as G2mth
    generalData['Mass'] = G2mth.getMass(generalData)


def make_empty_project(author=None, filename=None):
    """Creates an dictionary in the style of GSASIIscriptable, for an empty
    project.

    If no author name or filename is supplied, 'no name' and
    <current dir>/test_output.gpx are used , respectively.

    Returns: project dictionary, name list

    Author: Jackson O'Donnell (jacksonhodonnell .at. gmail.com)
    """
    if not filename:
        filename = 'test_output.gpx'
    filename = os.path.abspath(filename)
    gsasii_version = str(GSASIIpath.GetVersionNumber())
    LoadG2fil()
    import matplotlib as mpl
    python_library_versions = G2fil.get_python_versions([mpl, np, sp])

    controls_data = dict(G2obj.DefaultControls)
    controls_data['LastSavedAs'] = filename
    controls_data['LastSavedUsing'] = gsasii_version
    controls_data['PythonVersions'] = python_library_versions
    if author:
        controls_data['Author'] = author

    output = {'Constraints': {'data': {'HAP': [], 'Hist': [], 'Phase': [],
                                       'Global': []}},
              'Controls': {'data': controls_data},
              u'Covariance': {'data': {}},
              u'Notebook': {'data': ['']},
              u'Restraints': {'data': {}},
              u'Rigid bodies': {'data': {'RBIds': {'Residue': [], 'Vector': []},
                                'Residue': {'AtInfo': {}},
                                'Vector':  {'AtInfo': {}}}}}

    names = [[u'Notebook'], [u'Controls'], [u'Covariance'],
             [u'Constraints'], [u'Restraints'], [u'Rigid bodies']]

    return output, names


class G2ImportException(Exception):
    pass

class G2ScriptException(Exception):
    pass

def import_generic(filename, readerlist, fmthint=None, bank=None):
    """Attempt to import a filename, using a list of reader objects.

    Returns the first reader object which worked."""
    # Translated from OnImportGeneric method in GSASII.py
    primaryReaders, secondaryReaders = [], []
    for reader in readerlist:
        if fmthint is not None and fmthint not in reader.formatName: continue
        flag = reader.ExtensionValidator(filename)
        if flag is None:
            secondaryReaders.append(reader)
        elif flag:
            primaryReaders.append(reader)
    if not secondaryReaders and not primaryReaders:
        raise G2ImportException("Could not read file: ", filename)

    with open(filename, 'Ur') as fp:
        rd_list = []

        for rd in primaryReaders + secondaryReaders:
            # Initialize reader
            rd.selections = []
            if bank is None:
                rd.selections = []
            else:
                rd.selections = [bank-1]
            rd.dnames = []
            rd.ReInitialize()
            # Rewind file
            rd.errors = ""
            if not rd.ContentsValidator(filename):
                # Report error
                print("Warning: File {} has a validation error, continuing".format(filename))
            if len(rd.selections) > 1:
                raise G2ImportException("File {} has {} banks. Specify which bank to read with databank param."
                                .format(filename,len(rd.selections)))

            block = 0
            rdbuffer = {}
            repeat = True
            while repeat:
                repeat = False
                block += 1
                rd.objname = os.path.basename(filename)
                try:
                    flag = rd.Reader(filename,buffer=rdbuffer, blocknum=block)
                except:
                    flag = False
                if flag:
                    # Omitting image loading special cases
                    rd.readfilename = filename
                    rd_list.append(copy.deepcopy(rd))
                    repeat = rd.repeat
                else:
                    if GSASIIpath.GetConfigValue('debug'): print("DBG_{} Reader failed to read {}".format(rd.formatName,filename))
            if rd_list:
                if rd.warnings:
                    print("Read warning by", rd.formatName, "reader:",
                          rd.warnings, file=sys.stderr)
                elif bank is None:
                    print("{} read by Reader {}"
                              .format(filename,rd.formatName))
                else:
                    print("{} block # {} read by Reader {}"
                              .format(filename,bank,rd.formatName))
                return rd_list
    raise G2ImportException("No reader could read file: " + filename)


def load_iprms(instfile, reader, bank=None):
    """Loads instrument parameters from a file, and edits the
    given reader.

    Returns a 2-tuple of (Iparm1, Iparm2) parameters
    """
    LoadG2fil()
    ext = os.path.splitext(instfile)[1]

    if ext.lower() == '.instprm':
        # New GSAS File, load appropriate bank
        with open(instfile) as f:
            lines = f.readlines()
        if bank is None: 
            bank = reader.powderentry[2] 
        numbanks = reader.numbanks
        iparms = G2fil.ReadPowderInstprm(lines, bank, numbanks, reader)
        reader.instfile = instfile
        reader.instmsg = '{} (G2 fmt) bank {}'.format(instfile,bank)
        return iparms
    elif ext.lower() not in ('.prm', '.inst', '.ins'):
        raise ValueError('Expected .prm file, found: ', instfile)

    # It's an old GSAS file, load appropriately
    Iparm = {}
    with open(instfile, 'Ur') as fp:
        for line in fp:
            if '#' in line:
                continue
            Iparm[line[:12]] = line[12:-1]
    ibanks = int(Iparm.get('INS   BANK  ', '1').strip())
    if bank is not None:
        # pull out requested bank # bank from the data, and change the bank to 1
        Iparm,IparmC = {},Iparm
        for key in IparmC:
            if 'INS' not in key[:3]: continue   #skip around rubbish lines in some old iparm
            if key[4:6] == "  ":
                Iparm[key] = IparmC[key]
            elif int(key[4:6].strip()) == bank:
                Iparm[key[:4]+' 1'+key[6:]] = IparmC[key]            
        reader.instbank = bank
    elif ibanks == 1:
        reader.instbank = 1
    else: 
        raise G2ImportException("Instrument parameter file has {} banks, select one with instbank param."
                                    .format(ibanks))
    reader.powderentry[2] = 1
    reader.instfile = instfile
    reader.instmsg = '{} bank {}'.format(instfile,reader.instbank)
    return G2fil.SetPowderInstParms(Iparm, reader)

def load_pwd_from_reader(reader, instprm, existingnames=[],bank=None):
    """Loads powder data from a reader object, and assembles it into a GSASII data tree.

    :returns: (name, tree) - 2-tuple of the histogram name (str), and data

    Author: Jackson O'Donnell (jacksonhodonnell .at. gmail.com)
    """
    HistName = 'PWDR ' + G2obj.StripUnicode(reader.idstring, '_')
    HistName = G2obj.MakeUniqueLabel(HistName, existingnames)

    try:
        Iparm1, Iparm2 = instprm
    except ValueError:
        Iparm1, Iparm2 = load_iprms(instprm, reader, bank=bank)
        print('Instrument parameters read:',reader.instmsg)
    Ymin = np.min(reader.powderdata[1])
    Ymax = np.max(reader.powderdata[1])
    valuesdict = {'wtFactor': 1.0,
                  'Dummy': False,
                  'ranId': ran.randint(0, sys.maxsize),
                  'Offset': [0.0, 0.0], 'delOffset': 0.02*Ymax,
                  'refOffset': -0.1*Ymax, 'refDelt': 0.1*Ymax,
                  'Yminmax': [Ymin, Ymax]}
    reader.Sample['ranId'] = valuesdict['ranId']

    # Ending keys:
    # [u'Reflection Lists',
    #  u'Limits',
    #  'data',
    #  u'Index Peak List',
    #  u'Comments',
    #  u'Unit Cells List',
    #  u'Sample Parameters',
    #  u'Peak List',
    #  u'Background',
    #  u'Instrument Parameters']
    Tmin = np.min(reader.powderdata[0])
    Tmax = np.max(reader.powderdata[0])

    default_background = [['chebyschev', False, 3, 1.0, 0.0, 0.0],
                          {'nDebye': 0, 'debyeTerms': [], 'nPeaks': 0, 'peaksList': []}]

    output_dict = {u'Reflection Lists': {},
                   u'Limits': reader.pwdparms.get('Limits', [(Tmin, Tmax), [Tmin, Tmax]]),
                   u'data': [valuesdict, reader.powderdata, HistName],
                   u'Index Peak List': [[], []],
                   u'Comments': reader.comments,
                   u'Unit Cells List': [],
                   u'Sample Parameters': reader.Sample,
                   u'Peak List': {'peaks': [], 'sigDict': {}},
                   u'Background': reader.pwdparms.get('Background', default_background),
                   u'Instrument Parameters': [Iparm1, Iparm2],
                   }

    names = [u'Comments',
             u'Limits',
             u'Background',
             u'Instrument Parameters',
             u'Sample Parameters',
             u'Peak List',
             u'Index Peak List',
             u'Unit Cells List',
             u'Reflection Lists']

    # TODO controls?? GSASII.py:1664-7

    return HistName, [HistName] + names, output_dict


def _deep_copy_into(from_, into):
    """Helper function for reloading .gpx file. See G2Project.reload()

    :author: Jackson O'Donnell (jacksonhodonnell .at. gmail.com)
    """
    if isinstance(from_, dict) and isinstance(into, dict):
        combined_keys = set(from_.keys()).union(into.keys())
        for key in combined_keys:
            if key in from_ and key in into:
                both_dicts = (isinstance(from_[key], dict)
                              and isinstance(into[key], dict))
                both_lists = (isinstance(from_[key], list)
                              and isinstance(into[key], list))
                if both_dicts or both_lists:
                    _deep_copy_into(from_[key], into[key])
                else:
                    into[key] = from_[key]
            elif key in from_:
                into[key] = from_[key]
            else:  # key in into
                del into[key]
    elif isinstance(from_, list) and isinstance(into, list):
        if len(from_) == len(into):
            for i in range(len(from_)):
                both_dicts = (isinstance(from_[i], dict)
                              and isinstance(into[i], dict))
                both_lists = (isinstance(from_[i], list)
                              and isinstance(into[i], list))
                if both_dicts or both_lists:
                    _deep_copy_into(from_[i], into[i])
                else:
                    into[i] = from_[i]
        else:
            into[:] = from_


class G2ObjectWrapper(object):
    """Base class for all GSAS-II object wrappers.

    The underlying GSAS-II format can be accessed as `wrapper.data`. A number
    of overrides are implemented so that the wrapper behaves like a dictionary.

    Author: Jackson O'Donnell (jacksonhodonnell .at. gmail.com)
    """
    def __init__(self, datadict):
        self.data = datadict

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __contains__(self, key):
        return key in self.data

    def get(self, k, d=None):
        return self.data.get(k, d)

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def items(self):
        return self.data.items()


class G2Project(G2ObjectWrapper):    
    """Represents an entire GSAS-II project.

    :param str gpxfile: Existing .gpx file to be loaded. If nonexistent,
            creates an empty project.
    :param str author: Author's name (not yet implemented)
    :param str newgpx: The filename the project should be saved to in
            the future. If both newgpx and gpxfile are present, the project is
            loaded from the gpxfile, then when saved will be written to newgpx.
    :param str filename: Name to be used to save the project. Has same function as
            parameter newgpx (do not use both gpxfile and filename). Use of newgpx
            is preferred over filename.

    There are two ways to initialize this object:

    >>> # Load an existing project file
    >>> proj = G2Project('filename.gpx')
    
    >>> # Create a new project
    >>> proj = G2Project(newgpx='new_file.gpx')
    
    Histograms can be accessed easily.

    >>> # By name
    >>> hist = proj.histogram('PWDR my-histogram-name')
    
    >>> # Or by index
    >>> hist = proj.histogram(0)
    >>> assert hist.id == 0
    
    >>> # Or by random id
    >>> assert hist == proj.histogram(hist.ranId)

    Phases can be accessed the same way.

    >>> phase = proj.phase('name of phase')

    New data can also be loaded via :meth:`~G2Project.add_phase` and
    :meth:`~G2Project.add_powder_histogram`.

    >>> hist = proj.add_powder_histogram('some_data_file.chi',
                                         'instrument_parameters.prm')
    >>> phase = proj.add_phase('my_phase.cif', histograms=[hist])

    Parameters for Rietveld refinement can be turned on and off as well.
    See :meth:`~G2Project.set_refinement`, :meth:`~G2Project.clear_refinements`,
    :meth:`~G2Project.iter_refinements`, :meth:`~G2Project.do_refinements`.
    """
    def __init__(self, gpxfile=None, author=None, filename=None, newgpx=None):
        if filename is not None and newgpx is not None:
            raise G2ScriptException('Do not use filename and newgpx together')
        elif newgpx is not None:
            filename = newgpx
        if gpxfile is None:
            filename = os.path.abspath(os.path.expanduser(filename))
            self.filename = filename
            self.data, self.names = make_empty_project(author=author, filename=filename)
        elif isinstance(gpxfile, str): # TODO: create replacement for isinstance that checks if path exists
                                       # filename is valid, etc. 
            if isinstance(filename, str): 
                self.filename = os.path.abspath(os.path.expanduser(filename)) # both are defined
            else: 
                self.filename = os.path.abspath(os.path.expanduser(gpxfile))
            # TODO set author
            self.data, self.names = LoadDictFromProjFile(gpxfile)
            self.update_ids()
        else:
            raise ValueError("Not sure what to do with gpxfile")

    @classmethod
    def from_dict_and_names(cls, gpxdict, names, filename=None):
        """Creates a :class:`G2Project` directly from
        a dictionary and a list of names. If in doubt, do not use this.

        :returns: a :class:`G2Project`
        """
        out = cls()
        if filename:
            filename = os.path.abspath(os.path.expanduser(filename))
            out.filename = filename
            gpxdict['Controls']['data']['LastSavedAs'] = filename
        else:
            try:
                out.filename = gpxdict['Controls']['data']['LastSavedAs']
            except KeyError:
                out.filename = None
        out.data = gpxdict
        out.names = names

    def save(self, filename=None):
        """Saves the project, either to the current filename, or to a new file.

        Updates self.filename if a new filename provided"""
        # TODO update LastSavedUsing ?
        if filename:
            filename = os.path.abspath(os.path.expanduser(filename))
            self.data['Controls']['data']['LastSavedAs'] = filename
            self.filename = filename
        elif not self.filename:
            raise AttributeError("No file name to save to")
        SaveDictToProjFile(self.data, self.names, self.filename)

    def add_powder_histogram(self, datafile, iparams, phases=[], fmthint=None,
                                 databank=None, instbank=None):
        """Loads a powder data histogram into the project.

        Automatically checks for an instrument parameter file, or one can be
        provided. Note that in unix fashion, "~" can be used to indicate the
        home directory (e.g. ~/G2data/data.fxye).

        :param str datafile: The powder data file to read, a filename.
        :param str iparams: The instrument parameters file, a filename.
        :param list phases: Phases to link to the new histogram
        :param str fmthint: If specified, only importers where the format name
          (reader.formatName, as shown in Import menu) contains the
          supplied string will be tried as importers. If not specified, all
          importers consistent with the file extension will be tried
          (equivalent to "guess format" in menu).
        :param int databank: Specifies a dataset number to read, if file contains 
          more than set of data. This should be 1 to read the first bank in 
          the file (etc.) regardless of the number on the Bank line, etc.
          Default is None which means there should only be one dataset in the 
          file. 
        :param int instbank: Specifies an instrument parameter set to read, if 
          the instrument parameter file contains more than set of parameters. 
          This will match the INS # in an GSAS type file so it will typically 
          be 1 to read the first parameter set in the file (etc.) 
          Default is None which means there should only be one parameter set 
          in the file.

        :returns: A :class:`G2PwdrData` object representing
            the histogram
        """
        LoadG2fil()
        datafile = os.path.abspath(os.path.expanduser(datafile))
        iparams = os.path.abspath(os.path.expanduser(iparams))
        pwdrreaders = import_generic(datafile, Readers['Pwdr'],fmthint=fmthint,bank=databank)
        histname, new_names, pwdrdata = load_pwd_from_reader(
                                          pwdrreaders[0], iparams,
                                          [h.name for h in self.histograms()],bank=instbank)
        if histname in self.data:
            print("Warning - redefining histogram", histname)
        elif self.names[-1][0] == 'Phases':
            self.names.insert(-1, new_names)
        else:
            self.names.append(new_names)
        self.data[histname] = pwdrdata
        self.update_ids()

        for phase in phases:
            phase = self.phase(phase)
            self.link_histogram_phase(histname, phase)

        return self.histogram(histname)

    def add_simulated_powder_histogram(self, histname, iparams, Tmin, Tmax, Tstep,
                                       wavelength=None, scale=None, phases=[]):
        """Loads a powder data histogram into the project.

        Requires an instrument parameter file. 
        Note that in unix fashion, "~" can be used to indicate the
        home directory (e.g. ~/G2data/data.prm). The instrument parameter file
        will determine if the histogram is x-ray, CW neutron, TOF, etc. as well
        as the instrument type. 

        :param str histname: A name for the histogram to be created.
        :param str iparams: The instrument parameters file, a filename.
        :param float Tmin: Minimum 2theta or TOF (ms) for dataset to be simulated
        :param float Tmax: Maximum 2theta or TOF (ms) for dataset to be simulated
        :param float Tstep: Step size in 2theta or TOF (ms) for dataset to be simulated       
        :param float wavelength: Wavelength for CW instruments, overriding the value
           in the instrument parameters file if specified.
        :param float scale: Histogram scale factor which multiplies the pattern. Note that
           simulated noise is added to the pattern, so that if the maximum intensity is
           small, the noise will mask the computed pattern. The scale 
           needs to be a large number for CW neutrons.
           The default, None, provides a scale of 1 for x-rays and TOF; 10,000 for CW neutrons.
        :param list phases: Phases to link to the new histogram. Use proj.phases() to link to
           all defined phases.

        :returns: A :class:`G2PwdrData` object representing the histogram
        """
        LoadG2fil()
        iparams = os.path.abspath(os.path.expanduser(iparams))
        if not os.path.exists(iparams):
            raise G2ScriptException("File does not exist:"+iparams)
        rd = G2obj.ImportPowderData( # Initialize a base class reader
            extensionlist=tuple(),
            strictExtension=False,
            formatName = 'Simulate dataset',
            longFormatName = 'Compute a simulated pattern')
        rd.powderentry[0] = '' # no filename
        rd.powderentry[2] = 1 # only one bank
        rd.comments.append('This is a dummy dataset for powder pattern simulation')
        #Iparm1, Iparm2 = load_iprms(iparams, rd)
        if Tmax < Tmin:
            Tmin,Tmax = Tmax,Tmin
        Tstep = abs(Tstep)
        if 'TOF' in rd.idstring:
                N = (np.log(Tmax)-np.log(Tmin))/Tstep
                x = np.exp((np.arange(0,N))*Tstep+np.log(Tmin*1000.))
                N = len(x)
        else:            
                N = int((Tmax-Tmin)/Tstep)+1
                x = np.linspace(Tmin,Tmax,N,True)
                N = len(x)
        if N < 3:
            raise G2ScriptException("Error: Range is too small or step is too large, <3 points")
        rd.powderdata = [
            np.array(x), # x-axis values
            np.zeros_like(x), # powder pattern intensities
            np.ones_like(x), # 1/sig(intensity)^2 values (weights)
            np.zeros_like(x), # calc. intensities (zero)
            np.zeros_like(x), # calc. background (zero)
            np.zeros_like(x), # obs-calc profiles
            ]
        Tmin = rd.powderdata[0][0]
        Tmax = rd.powderdata[0][-1]
        rd.idstring = histname
        histname, new_names, pwdrdata = load_pwd_from_reader(rd, iparams,
                                                            [h.name for h in self.histograms()])
        if histname in self.data:
            print("Warning - redefining histogram", histname)
        elif self.names[-1][0] == 'Phases':
            self.names.insert(-1, new_names)
        else:
            self.names.append(new_names)
        if scale is not None:
            pwdrdata['Sample Parameters']['Scale'][0] = scale
        elif pwdrdata['Instrument Parameters'][0]['Type'][0].startswith('PNC'):
            pwdrdata['Sample Parameters']['Scale'][0] = 10000.
        self.data[histname] = pwdrdata
        self.update_ids()

        for phase in phases:
            phase = self.phase(phase)
            self.link_histogram_phase(histname, phase)

        return self.histogram(histname)
    
    def add_phase(self, phasefile, phasename=None, histograms=[], fmthint=None):
        """Loads a phase into the project from a .cif file

        :param str phasefile: The CIF file from which to import the phase.
        :param str phasename: The name of the new phase, or None for the default
        :param list histograms: The names of the histograms to associate with
            this phase. Use proj.histograms() to add to all histograms.
        :param str fmthint: If specified, only importers where the format name
          (reader.formatName, as shown in Import menu) contains the
          supplied string will be tried as importers. If not specified, all
          importers consistent with the file extension will be tried
          (equivalent to "guess format" in menu).

        :returns: A :class:`G2Phase` object representing the
            new phase.
        """
        LoadG2fil()
        histograms = [self.histogram(h).name for h in histograms]
        phasefile = os.path.abspath(os.path.expanduser(phasefile))

        # TODO handle multiple phases in a file
        phasereaders = import_generic(phasefile, Readers['Phase'], fmthint=fmthint)
        phasereader = phasereaders[0]
        
        phasename = phasename or phasereader.Phase['General']['Name']
        phaseNameList = [p.name for p in self.phases()]
        phasename = G2obj.MakeUniqueLabel(phasename, phaseNameList)
        phasereader.Phase['General']['Name'] = phasename

        if 'Phases' not in self.data:
            self.data[u'Phases'] = { 'data': None }
        assert phasename not in self.data['Phases'], "phase names should be unique"
        self.data['Phases'][phasename] = phasereader.Phase

        if phasereader.Constraints:
            Constraints = self.data['Constraints']
            for i in phasereader.Constraints:
                if isinstance(i, dict):
                    if '_Explain' not in Constraints:
                        Constraints['_Explain'] = {}
                    Constraints['_Explain'].update(i)
                else:
                    Constraints['Phase'].append(i)

        data = self.data['Phases'][phasename]
        generalData = data['General']
        SGData = generalData['SGData']
        NShkl = len(G2spc.MustrainNames(SGData))
        NDij = len(G2spc.HStrainNames(SGData))
        Super = generalData.get('Super', 0)
        if Super:
            SuperVec = np.array(generalData['SuperVec'][0])
        else:
            SuperVec = []
        UseList = data['Histograms']

        for hist in histograms:
            self.link_histogram_phase(hist, phasename)

        for obj in self.names:
            if obj[0] == 'Phases':
                phasenames = obj
                break
        else:
            phasenames = [u'Phases']
            self.names.append(phasenames)
        phasenames.append(phasename)

        # TODO should it be self.filename, not phasefile?
        SetupGeneral(data, os.path.dirname(phasefile))
        self.index_ids()

        self.update_ids()
        return self.phase(phasename)

    def link_histogram_phase(self, histogram, phase):
        """Associates a given histogram and phase.

        .. seealso::

            :meth:`G2Project.histogram`
            :meth:`G2Project.phase`"""
        hist = self.histogram(histogram)
        phase = self.phase(phase)

        generalData = phase['General']

        if hist.name.startswith('HKLF '):
            raise NotImplementedError("HKLF not yet supported")
        elif hist.name.startswith('PWDR '):
            hist['Reflection Lists'][generalData['Name']] = {}
            UseList = phase['Histograms']
            SGData = generalData['SGData']
            NShkl = len(G2spc.MustrainNames(SGData))
            NDij = len(G2spc.HStrainNames(SGData))
            UseList[hist.name] = SetDefaultDData('PWDR', hist.name, NShkl=NShkl, NDij=NDij)
            UseList[hist.name]['hId'] = hist.id
            for key, val in [('Use', True), ('LeBail', False),
                             ('newLeBail', True),
                             ('Babinet', {'BabA': [0.0, False],
                                          'BabU': [0.0, False]})]:
                if key not in UseList[hist.name]:
                    UseList[hist.name][key] = val
        else:
            raise RuntimeError("Unexpected histogram" + hist.name)


    def reload(self):
        """Reload self from self.filename"""
        data, names = LoadDictFromProjFile(self.filename)
        self.names = names
        # Need to deep copy the new data file data into the current tree,
        # so that any existing G2Phase, or G2PwdrData objects will still be
        # valid
        _deep_copy_into(from_=data, into=self.data)

    def refine(self, newfile=None, printFile=None, makeBack=False):
        # TODO migrate to RefineCore
        # G2strMain.RefineCore(Controls,Histograms,Phases,restraintDict,rigidbodyDict,parmDict,varyList,
	#      calcControls,pawleyLookup,ifPrint,printFile,dlg)
        # index_ids will automatically save the project
        self.index_ids()
        # TODO G2strMain does not properly use printFile
        G2strMain.Refine(self.filename, makeBack=makeBack)
        # Reload yourself
        self.reload()

    def histogram(self, histname):
        """Returns the histogram named histname, or None if it does not exist.

        :param histname: The name of the histogram (str), or ranId or index.
        :returns: A :class:`G2PwdrData` object, or None if
            the histogram does not exist

        .. seealso::
            :meth:`G2Project.histograms`
            :meth:`G2Project.phase`
            :meth:`G2Project.phases`
        """
        if isinstance(histname, G2PwdrData):
            if histname.proj == self:
                return histname
        if histname in self.data:
            return G2PwdrData(self.data[histname], self)
        try:
            # see if histname is an id or ranId
            histname = int(histname)
        except ValueError:
            return

        for histogram in self.histograms():
            if histogram.id == histname or histogram.ranId == histname:
                return histogram

    def histograms(self, typ=None):
        """Return a list of all histograms, as :class:`G2PwdrData` objects

        For now this only finds Powder/Single Xtal histograms, since that is all that is
        currently implemented in this module.

        :param ste typ: The prefix (type) the histogram such as 'PWDR '. If None
          (the default) all known histograms types are found. 
        :returns: a list of objects

        .. seealso::
            :meth:`G2Project.histogram`
            :meth:`G2Project.phase`
            :meth:`G2Project.phases`
        """
        output = []
        # loop through each tree entry. If it is more than one level (more than one item in the
        # list of names). then it must be a histogram, unless labeled Phases or Restraints
        if typ is None:
            for obj in self.names:
                if obj[0].startswith('PWDR ') or obj[0].startswith('HKLF '): 
                    output.append(self.histogram(obj[0]))
        else:
            for obj in self.names:
                if len(obj) > 1 and obj[0].startswith(typ): 
                    output.append(self.histogram(obj[0]))
        return output

    def phase(self, phasename):
        """
        Gives an object representing the specified phase in this project.

        :param str phasename: A reference to the desired phase. Either the phase 
            name (str), the phase's ranId, the phase's index (both int) or
            a phase object (:class:`G2Phase`)
        :returns: A :class:`G2Phase` object
        :raises: KeyError

        .. seealso::
            :meth:`G2Project.histograms`
            :meth:`G2Project.phase`
            :meth:`G2Project.phases`
            """
        if isinstance(phasename, G2Phase):
            if phasename.proj == self:
                return phasename
        phases = self.data['Phases']
        if phasename in phases:
            return G2Phase(phases[phasename], phasename, self)

        try:
            # phasename should be phase index or ranId
            phasename = int(phasename)
        except ValueError:
            return

        for phase in self.phases():
            if phase.id == phasename or phase.ranId == phasename:
                return phase

    def phases(self):
        """
        Returns a list of all the phases in the project.

        :returns: A list of :class:`G2Phase` objects

        .. seealso::
            :meth:`G2Project.histogram`
            :meth:`G2Project.histograms`
            :meth:`G2Project.phase`
            """
        for obj in self.names:
            if obj[0] == 'Phases':
                return [self.phase(p) for p in obj[1:]]
        return []

    def _images(self):
        """Returns a list of all the phases in the project.
        """
        return [i[0] for i in self.names if i[0].startswith('IMG ')]
    
    def image(self, imageRef):
        """
        Gives an object representing the specified image in this project.

        :param str imageRef: A reference to the desired image. Either the Image 
          tree name (str), the image's index (int) or
          a image object (:class:`G2Image`)
        :returns: A :class:`G2Image` object
        :raises: KeyError

        .. seealso::
            :meth:`G2Project.images`
            """
        if isinstance(imageRef, G2Image):
            if imageRef.proj == self:
                return imageRef
            else:
                raise Exception("Image {} not in current selected project".format(imageRef.name))
        if imageRef in self._images():
            return G2Image(self.data[imageRef], imageRef, self)

        try:
            # imageRef should be an index
            num = int(imageRef)
            imageRef = self._images()[num] 
            return G2Image(self.data[imageRef], imageRef, self)
        except ValueError:
            raise Exception("imageRef {} not an object, name or image index in current selected project"
                                .format(imageRef))
        except IndexError:
            raise Exception("imageRef {} out of range (max={}) in current selected project"
                                .format(imageRef,len(self._images())-1))
            
    def images(self):
        """
        Returns a list of all the images in the project.

        :returns: A list of :class:`G2Image` objects
        """
        return [G2Image(self.data[i],i,self) for i in self._images()]
    
    def update_ids(self):
        """Makes sure all phases and histograms have proper hId and pId"""
        # Translated from GetUsedHistogramsAndPhasesfromTree,
        #   GSASIIdataGUI.py:4107
        for i, h in enumerate(self.histograms()):
            h.id = i
        for i, p in enumerate(self.phases()):
            p.id = i

    def do_refinements(self, refinements, histogram='all', phase='all',
                       outputnames=None, makeBack=False):
        """Conducts one or a series of refinements according to the
           input provided in parameter refinements. This is a wrapper
           around :meth:`iter_refinements`

        :param list refinements: A list of dictionaries specifiying changes to be made to
            parameters before refinements are conducted.
            See the :ref:`Refinement_recipe` section for how this is defined. 
        :param str histogram: Name of histogram for refinements to be applied
            to, or 'all'; note that this can be overridden for each refinement
            step via a "histograms" entry in the dict.
        :param str phase: Name of phase for refinements to be applied to, or
            'all'; note that this can be overridden for each refinement
            step via a "phases" entry in the dict.
        :param list outputnames: Provides a list of project (.gpx) file names
            to use for each refinement step (specifying None skips the save step).
            See :meth:`save`. 
            Note that this can be overridden using an "output" entry in the dict.
        :param bool makeBack: determines if a backup ).bckX.gpx) file is made
            before a refinement is performed. The default is False.
            
        To perform a single refinement without changing any parameters, use this
        call:

        .. code-block::  python
        
            my_project.do_refinements([])
        """
        
        for proj in self.iter_refinements(refinements, histogram, phase,
                                          outputnames, makeBack):
            pass
        return self

    def iter_refinements(self, refinements, histogram='all', phase='all',
                         outputnames=None, makeBack=False):
        """Conducts a series of refinements, iteratively. Stops after every
        refinement and yields this project, to allow error checking or
        logging of intermediate results. Parameter use is the same as for
        :meth:`do_refinements` (which calls this method). 

        >>> def checked_refinements(proj):
        ...     for p in proj.iter_refinements(refs):
        ...         # Track intermediate results
        ...         log(p.histogram('0').residuals)
        ...         log(p.phase('0').get_cell())
        ...         # Check if parameter diverged, nonsense answer, or whatever
        ...         if is_something_wrong(p):
        ...             raise Exception("I need a human!")

            
        """
        if outputnames:
            if len(refinements) != len(outputnames):
                raise ValueError("Should have same number of outputs to"
                                 "refinements")
        else:
            outputnames = [None for r in refinements]

        for output, refinedict in zip(outputnames, refinements):
            if 'histograms' in refinedict:
                hist = refinedict['histograms']
            else:
                hist = histogram
            if 'phases' in refinedict:
                ph = refinedict['phases']
            else:
                ph = phase
            if 'output' in refinedict:
                output = refinedict['output']
            self.set_refinement(refinedict, hist, ph)
            # Handle 'once' args - refinements that are disabled after this
            # refinement
            if 'once' in refinedict:
                temp = {'set': refinedict['once']}
                self.set_refinement(temp, hist, ph)

            if output:
                self.save(output)

            if 'skip' not in refinedict:
                self.refine(makeBack=makeBack)
            yield self

            # Handle 'once' args - refinements that are disabled after this
            # refinement
            if 'once' in refinedict:
                temp = {'clear': refinedict['once']}
                self.set_refinement(temp, hist, ph)
            if 'call' in refinedict:
                fxn = refinedict['call']
                if callable(fxn):
                    fxn(*refinedict.get('callargs',[self]))
                elif callable(eval(fxn)):
                    eval(fxn)(*refinedict.get('callargs',[self]))
                else:
                    raise G2ScriptException("Error: call value {} is not callable".format(fxn))

    def set_refinement(self, refinement, histogram='all', phase='all'):
        """Apply specified refinements to a given histogram(s) or phase(s).

        :param dict refinement: The refinements to be conducted
        :param histogram: Specifies either 'all' (default), a single histogram or
          a list of histograms. Histograms may be specified as histogram objects
          (see :class:`G2PwdrData`), the histogram name (str) or the index number (int)
          of the histogram in the project, numbered starting from 0.
          Omitting the parameter or the string 'all' indicates that parameters in
          all histograms should be set. 
        :param phase: Specifies either 'all' (default), a single phase or
          a list of phases. Phases may be specified as phase objects
          (see :class:`G2Phase`), the phase name (str) or the index number (int)
          of the phase in the project, numbered starting from 0.
          Omitting the parameter or the string 'all' indicates that parameters in
          all phases should be set. 

        Note that refinement parameters are categorized as one of three types:

        1. Histogram parameters
        2. Phase parameters
        3. Histogram-and-Phase (HAP) parameters
        
        .. seealso::
            :meth:`G2PwdrData.set_refinements`
            :meth:`G2PwdrData.clear_refinements`
            :meth:`G2Phase.set_refinements`
            :meth:`G2Phase.clear_refinements`
            :meth:`G2Phase.set_HAP_refinements`
            :meth:`G2Phase.clear_HAP_refinements`"""

        if histogram == 'all':
            hists = self.histograms()
        elif isinstance(histogram, list) or isinstance(histogram, tuple):
            hists = []
            for h in histogram:
                if isinstance(h, str) or isinstance(h, int):
                    hists.append(self.histogram(h))
                else:
                    hists.append(h)
        elif isinstance(histogram, str) or isinstance(histogram, int):
            hists = [self.histogram(histogram)]
        else:
            hists = [histogram]

        if phase == 'all':
            phases = self.phases()
        elif isinstance(phase, list) or isinstance(phase, tuple):
            phases = []
            for ph in phase:
                if isinstance(ph, str) or isinstance(ph, int):
                    phases.append(self.phase(ph))
                else:
                    phases.append(ph)
        elif isinstance(phase, str) or isinstance(phase, int):
            phases = [self.phase(phase)]
        else:
            phases = [phase]

        # TODO: HAP parameters:
        #   Babinet
        #   Extinction
        #   HStrain
        #   Mustrain
        #   Pref. Ori
        #   Size

        pwdr_set = {}
        phase_set = {}
        hap_set = {}
        for key, val in refinement.get('set', {}).items():
            # Apply refinement options
            if G2PwdrData.is_valid_refinement_key(key):
                pwdr_set[key] = val
            elif G2Phase.is_valid_refinement_key(key):
                phase_set[key] = val
            elif G2Phase.is_valid_HAP_refinement_key(key):
                hap_set[key] = val
            else:
                raise ValueError("Unknown refinement key", key)

        for hist in hists:
            hist.set_refinements(pwdr_set)
        for phase in phases:
            phase.set_refinements(phase_set)
        for phase in phases:
            phase.set_HAP_refinements(hap_set, hists)

        pwdr_clear = {}
        phase_clear = {}
        hap_clear = {}
        for key, val in refinement.get('clear', {}).items():
            # Clear refinement options
            if G2PwdrData.is_valid_refinement_key(key):
                pwdr_clear[key] = val
            elif G2Phase.is_valid_refinement_key(key):
                phase_clear[key] = val
            elif G2Phase.is_valid_HAP_refinement_key(key):
                hap_set[key] = val
            else:
                raise ValueError("Unknown refinement key", key)

        for hist in hists:
            hist.clear_refinements(pwdr_clear)
        for phase in phases:
            phase.clear_refinements(phase_clear)
        for phase in phases:
            phase.clear_HAP_refinements(hap_clear, hists)

    def index_ids(self):
        import GSASIIstrIO as G2strIO
        self.save()
        return G2strIO.GetUsedHistogramsAndPhases(self.filename)

    def add_constraint_raw(self, cons_scope, constr):
        """Adds a constraint of type consType to the project.
        cons_scope should be one of "Hist", "Phase", "HAP", or "Global".

        WARNING it does not check the constraint is well-constructed"""
        constrs = self.data['Constraints']['data']
        if 'Global' not in constrs:
            constrs['Global'] = []
        constrs[cons_scope].append(constr)

    def hold_many(self, vars, type):
        """Apply holds for all the variables in vars, for constraint of a given type.

        type is passed directly to add_constraint_raw as consType

        :param list vars: A list of variables to hold. Either :class:`GSASIIobj.G2VarObj` objects,
            string variable specifiers, or arguments for :meth:`make_var_obj`
        :param str type: A string constraint type specifier. See
            :class:`G2Project.add_constraint_raw`

        """
        for var in vars:
            if isinstance(var, str):
                var = self.make_var_obj(var)
            elif not isinstance(var, G2obj.G2VarObj):
                var = self.make_var_obj(*var)
            self.add_constraint_raw(type, [[1.0, var], None, None, 'h'])

    def make_var_obj(self, phase=None, hist=None, varname=None, atomId=None,
                     reloadIdx=True):
        """Wrapper to create a G2VarObj. Takes either a string representaiton ("p:h:name:a")
        or individual names of phase, histogram, varname, and atomId.

        Automatically converts string phase, hist, or atom names into the ID required
        by G2VarObj."""

        if reloadIdx:
            self.index_ids()

        # If string representation, short circuit
        if hist is None and varname is None and atomId is None:
            if isinstance(phase, str) and ':' in phase:
                return G2obj.G2VarObj(phase)

        # Get phase index
        phaseObj = None
        if isinstance(phase, G2Phase):
            phaseObj = phase
            phase = G2obj.PhaseRanIdLookup[phase.ranId]
        elif phase in self.data['Phases']:
            phaseObj = self.phase(phase)
            phaseRanId = phaseObj.ranId
            phase = G2obj.PhaseRanIdLookup[phaseRanId]

        # Get histogram index
        if isinstance(hist, G2PwdrData):
            hist = G2obj.HistRanIdLookup[hist.ranId]
        elif hist in self.data:
            histRanId = self.histogram(hist).ranId
            hist = G2obj.HistRanIdLookup[histRanId]

        # Get atom index (if any)
        if isinstance(atomId, G2AtomRecord):
            atomId = G2obj.AtomRanIdLookup[phase][atomId.ranId]
        elif phaseObj:
            atomObj = phaseObj.atom(atomId)
            if atomObj:
                atomRanId = atomObj.ranId
                atomId = G2obj.AtomRanIdLookup[phase][atomRanId]

        return G2obj.G2VarObj(phase, hist, varname, atomId)

    def add_image(self, imagefile, fmthint=None, defaultImage=None):
        """Load an image into a project

        :param str imagefile: The image file to read, a filename.
        :param str fmthint: If specified, only importers where the format name
          (reader.formatName, as shown in Import menu) contains the
          supplied string will be tried as importers. If not specified, all
          importers consistent with the file extension will be tried
          (equivalent to "guess format" in menu).
        :param str defaultImage: The name of an image to use as a default for 
          setting parameters for the image file to read. 

        :returns: a list of G2Image object for the added image(s) [this routine 
          has not yet been tested with files with multiple images...]
        """
        LoadG2fil()
        imagefile = os.path.abspath(os.path.expanduser(imagefile))
        readers = import_generic(imagefile, Readers['Image'], fmthint=fmthint)
        objlist = []
        for rd in readers:
            if rd.SciPy:        #was default read by scipy; needs 1 time fixes
                print('TODO: Image {} read by SciPy. Parameters likely need editing'.format(imagefile))
                #see this: G2IO.EditImageParms(self,rd.Data,rd.Comments,rd.Image,imagefile)
                rd.SciPy = False
            rd.readfilename = imagefile
            if rd.repeatcount == 1 and not rd.repeat: # skip image number if only one in set
                rd.Data['ImageTag'] = None
            else:
                rd.Data['ImageTag'] = rd.repeatcount
            rd.Data['formatName'] = rd.formatName
            if rd.sumfile:
                rd.readfilename = rd.sumfile
            # Load generic metadata, as configured
            G2fil.GetColumnMetadata(rd)
            # Code from G2IO.LoadImage2Tree(rd.readfilename,self,rd.Comments,rd.Data,rd.Npix,rd.Image)
            Imax = np.amax(rd.Image)
            ImgNames = [i[0] for i in self.names if i[0].startswith('IMG ')]
            TreeLbl = 'IMG '+os.path.basename(imagefile)
            ImageTag = rd.Data.get('ImageTag')
            if ImageTag:
                TreeLbl += ' #'+'%04d'%(ImageTag)
                imageInfo = (imagefile,ImageTag)
            else:
                imageInfo = imagefile
            TreeName = G2obj.MakeUniqueLabel(TreeLbl,ImgNames)
            # MT dict to contain image info
            ImgDict = {}
            ImgDict['data'] = [rd.Npix,imageInfo]
            ImgDict['Comments'] = rd.Comments
            if defaultImage:
                if isinstance(defaultImage, G2Image):
                    if defaultImage.proj == self:
                        defaultImage = self.data[defaultImage.name]['data']
                    else:
                        raise Exception("Image {} not in current selected project".format(defaultImage.name))
                elif defaultImage in self._images():
                    defaultImage = self.data[defaultImage]['data']
                else:
                    defaultImage = None
            Data = rd.Data
            if defaultImage:
                Data = copy.copy(defaultImage)
                Data['showLines'] = True
                Data['ring'] = []
                Data['rings'] = []
                Data['cutoff'] = 10.
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
                Data['color'] = GSASIIpath.GetConfigValue('Contour_color','Paired')
                if 'tilt' not in Data:          #defaults if not preset in e.g. Bruker importer
                    Data['tilt'] = 0.0
                    Data['rotation'] = 0.0
                    Data['pixLimit'] = 20
                    Data['calibdmin'] = 0.5
                    Data['cutoff'] = 10.
                Data['showLines'] = False
                Data['calibskip'] = 0
                Data['ring'] = []
                Data['rings'] = []
                Data['edgemin'] = 100000000
                Data['ellipses'] = []
                Data['GonioAngles'] = [0.,0.,0.]
                Data['DetDepth'] = 0.
                Data['DetDepthRef'] = False
                Data['calibrant'] = ''
                Data['IOtth'] = [5.0,50.0]
                Data['LRazimuth'] = [0.,180.]
                Data['azmthOff'] = 0.0
                Data['outChannels'] = 2250
                Data['outAzimuths'] = 1
                Data['centerAzm'] = False
                Data['fullIntegrate'] = GSASIIpath.GetConfigValue('fullIntegrate',True)
                Data['setRings'] = False
                Data['background image'] = ['',-1.0]                            
                Data['dark image'] = ['',-1.0]
                Data['Flat Bkg'] = 0.0
                Data['Oblique'] = [0.5,False]
            Data['setDefault'] = False
            Data['range'] = [(0,Imax),[0,Imax]]
            ImgDict['Image Controls'] = Data
            ImgDict['Masks'] = {'Points':[],'Rings':[],'Arcs':[],'Polygons':[],
                                'Frames':[],'Thresholds':[(0,Imax),[0,Imax]]}
            ImgDict['Stress/Strain']  = {'Type':'True','d-zero':[],'Sample phi':0.0,
                                             'Sample z':0.0,'Sample load':0.0}
            self.names.append([TreeName]+['Comments','Image Controls','Masks','Stress/Strain'])
            self.data[TreeName] = ImgDict
            del rd.Image
            objlist.append(G2Image(self.data[TreeName], TreeName, self))
        return objlist

class G2AtomRecord(G2ObjectWrapper):
    """Wrapper for an atom record. Has convenient accessors via @property.


    Available accessors: label, type, refinement_flags, coordinates,
        occupancy, ranId, id, adp_flag, uiso

    Example:

    >>> atom = some_phase.atom("O3")
    >>> # We can access the underlying data format
    >>> atom.data
    ['O3', 'O-2', '', ... ]
    >>> # We can also use wrapper accessors
    >>> atom.coordinates
    (0.33, 0.15, 0.5)
    >>> atom.refinement_flags
    u'FX'
    >>> atom.ranId
    4615973324315876477
    >>> atom.occupancy
    1.0
    """
    def __init__(self, data, indices, proj):
        self.data = data
        self.cx, self.ct, self.cs, self.cia = indices
        self.proj = proj

    @property
    def label(self):
        return self.data[self.ct-1]

    @property
    def type(self):
        return self.data[self.ct]

    @property
    def refinement_flags(self):
        return self.data[self.ct+1]

    @refinement_flags.setter
    def refinement_flags(self, other):
        # Automatically check it is a valid refinement
        for c in other:
            if c not in ' FXU':
                raise ValueError("Invalid atom refinement: ", other)
        self.data[self.ct+1] = other

    @property
    def coordinates(self):
        return tuple(self.data[self.cx:self.cx+3])

    @property
    def occupancy(self):
        return self.data[self.cx+3]

    @occupancy.setter
    def occupancy(self, val):
        self.data[self.cx+3] = float(val)

    @property
    def ranId(self):
        return self.data[self.cia+8]

    @property
    def adp_flag(self):
        # Either 'I' or 'A'
        return self.data[self.cia]

    @property
    def uiso(self):
        if self.adp_flag == 'I':
            return self.data[self.cia+1]
        else:
            return self.data[self.cia+2:self.cia+8]

    @uiso.setter
    def uiso(self, value):
        if self.adp_flag == 'I':
            self.data[self.cia+1] = float(value)
        else:
            assert len(value) == 6
            self.data[self.cia+2:self.cia+8] = [float(v) for v in value]


class G2PwdrData(G2ObjectWrapper):
    """Wraps a Powder Data Histogram."""
    def __init__(self, data, proj):
        self.data = data
        self.proj = proj

    @staticmethod
    def is_valid_refinement_key(key):
        valid_keys = ['Limits', 'Sample Parameters', 'Background',
                      'Instrument Parameters']
        return key in valid_keys

    @property
    def name(self):
        return self.data['data'][-1]

    @property
    def ranId(self):
        return self.data['data'][0]['ranId']

    @property
    def residuals(self):
        '''Provides a dictionary with with the R-factors for this histogram.
        Includes the weighted and unweighted profile terms (R, Rb, wR, wRb, wRmin)
        as well as the Bragg R-values for each phase (ph:H:Rf and ph:H:Rf^2).
        '''
        data = self.data['data'][0]
        return {key: data[key] for key in data
                if key in ['R', 'Rb', 'wR', 'wRb', 'wRmin']
                   or ':' in key}

    @property
    def InstrumentParameters(self):
        '''Provides a dictionary with with the Instrument Parameters
        for this histogram.
        '''
        return self.data['Instrument Parameters'][0]

    @property
    def SampleParameters(self):
        '''Provides a dictionary with with the Sample Parameters
        for this histogram.
        '''
        return self.data['Sample Parameters']
    
    @property
    def id(self):
        self.proj.update_ids()
        return self.data['data'][0]['hId']

    @id.setter
    def id(self, val):
        self.data['data'][0]['hId'] = val

    def fit_fixed_points(self):
        """Attempts to apply a background fit to the fixed points currently specified."""
        def SetInstParms(Inst):
            dataType = Inst['Type'][0]
            insVary = []
            insNames = []
            insVals = []
            for parm in Inst:
                insNames.append(parm)
                insVals.append(Inst[parm][1])
                if parm in ['U','V','W','X','Y','Z','SH/L','I(L2)/I(L1)','alpha',
                    'beta-0','beta-1','beta-q','sig-0','sig-1','sig-2','sig-q',] and Inst[parm][2]:
                        Inst[parm][2] = False
            instDict = dict(zip(insNames, insVals))
            instDict['X'] = max(instDict['X'], 0.01)
            instDict['Y'] = max(instDict['Y'], 0.01)
            if 'SH/L' in instDict:
                instDict['SH/L'] = max(instDict['SH/L'], 0.002)
            return dataType, instDict, insVary

        bgrnd = self.data['Background']

        # Need our fixed points in order
        bgrnd[1]['FixedPoints'].sort(key=lambda pair: pair[0])
        X = [x for x, y in bgrnd[1]['FixedPoints']]
        Y = [y for x, y in bgrnd[1]['FixedPoints']]

        limits = self.data['Limits'][1]
        if X[0] > limits[0]:
            X = [limits[0]] + X
            Y = [Y[0]] + Y
        if X[-1] < limits[1]:
            X += [limits[1]]
            Y += [Y[-1]]

        # Some simple lookups
        controls = self.proj['Controls']['data']
        inst, inst2 = self.data['Instrument Parameters']
        pwddata = self.data['data'][1]

        # Construct the data for background fitting
        xBeg = np.searchsorted(pwddata[0], limits[0])
        xFin = np.searchsorted(pwddata[0], limits[1])
        xdata = pwddata[0][xBeg:xFin]
        ydata = si.interp1d(X,Y)(ma.getdata(xdata))

        W = [1]*len(xdata)
        Z = [0]*len(xdata)

        dataType, insDict, insVary = SetInstParms(inst)
        bakType, bakDict, bakVary = G2pwd.SetBackgroundParms(bgrnd)

        # Do the fit
        data = np.array([xdata, ydata, W, Z, Z, Z])
        G2pwd.DoPeakFit('LSQ', [], bgrnd, limits, inst, inst2, data,
                        prevVaryList=bakVary, controls=controls)

        # Post-fit
        parmDict = {}
        bakType, bakDict, bakVary = G2pwd.SetBackgroundParms(bgrnd)
        parmDict.update(bakDict)
        parmDict.update(insDict)
        pwddata[3][xBeg:xFin] *= 0
        pwddata[5][xBeg:xFin] *= 0
        pwddata[4][xBeg:xFin] = G2pwd.getBackground('', parmDict, bakType, dataType, xdata)[0]

        # TODO adjust pwddata? GSASIIpwdGUI.py:1041
        # TODO update background
        self.proj.save()

    def getdata(self,datatype):
        '''Provides access to the histogram data of the selected data type

        :param str datatype: must be one of the following values (case is ignored)
        
           * 'X': the 2theta or TOF values for the pattern
           * 'Yobs': the observed intensity values 
           * 'Yweight': the weights for each data point (1/sigma**2)
           * 'Ycalc': the computed intensity values 
           * 'Background': the computed background values
           * 'Residual': the difference between Yobs and Ycalc (obs-calc)

        :returns: an numpy MaskedArray with data values of the requested type
        
        '''
        enums = ['x', 'yobs', 'yweight', 'ycalc', 'background', 'residual']
        if datatype.lower() not in enums:
            raise G2ScriptException("Invalid datatype = "+datatype+" must be one of "+str(enums))
        return self.data['data'][1][enums.index(datatype.lower())]
        
    def y_calc(self):
        return self.data['data'][1][3]

    def Export(self,fileroot,extension):
        '''Write the histogram into a file. The path is specified by fileroot and
        extension.
        
        :param str fileroot: name of the file, optionally with a path (extension is
           ignored)
        :param str extension: includes '.', must match an extension in global
           exportersByExtension['powder'] or a Exception is raised.
        :returns: name of file that was written
        '''
        if extension not in exportersByExtension.get('powder',[]):
            raise G2ScriptException('No Writer for file type = "'+extension+'"')
        fil = os.path.abspath(os.path.splitext(fileroot)[0]+extension)
        obj = exportersByExtension['powder'][extension]
        obj.SetFromArray(hist=self.data,histname=self.name)
        obj.Writer(self.name,fil)
            
    def plot(self, Yobs=True, Ycalc=True, Background=True, Residual=True):
        try:
            import matplotlib.pyplot as plt
            data = self.data['data'][1]
            if Yobs:
                plt.plot(data[0], data[1], label='Yobs')
            if Ycalc:
                plt.plot(data[0], data[3], label='Ycalc')
            if Background:
                plt.plot(data[0], data[4], label='Background')
            if Residual:
                plt.plot(data[0], data[5], label="Residual")
        except ImportError:
            pass

    def get_wR(self):
        """returns the overall weighted profile R factor for a histogram
        
        :returns: a wR value as a percentage or None if not defined
        """
        return self['data'][0].get('wR')

    def set_refinements(self, refs):
        """Sets the refinement parameter 'key' to the specification 'value'

        :param dict refs: A dictionary of the parameters to be set. See
                          :ref:`Histogram_parameters_table` for a description of
                          what these dictionaries should be.

        :returns: None

        """
        do_fit_fixed_points = False
        for key, value in refs.items():
            if key == 'Limits':
                old_limits = self.data['Limits'][1]
                new_limits = value
                if isinstance(new_limits, dict):
                    if 'low' in new_limits:
                        old_limits[0] = new_limits['low']
                    if 'high' in new_limits:
                        old_limits[1] = new_limits['high']
                else:
                    old_limits[0], old_limits[1] = new_limits
            elif key == 'Sample Parameters':
                sample = self.data['Sample Parameters']
                for sparam in value:
                    if sparam not in sample:
                        raise ValueError("Unknown refinement parameter, "
                                         + str(sparam))
                    sample[sparam][1] = True
            elif key == 'Background':
                bkg, peaks = self.data['Background']

                # If True or False, just set the refine parameter
                if value in (True, False):
                    bkg[1] = value
                    return

                if 'type' in value:
                    bkg[0] = value['type']
                if 'refine' in value:
                    bkg[1] = value['refine']
                if 'no. coeffs' in value:
                    cur_coeffs = bkg[2]
                    n_coeffs = value['no. coeffs']
                    if n_coeffs > cur_coeffs:
                        for x in range(n_coeffs - cur_coeffs):
                            bkg.append(0.0)
                    else:
                        for _ in range(cur_coeffs - n_coeffs):
                            bkg.pop()
                    bkg[2] = n_coeffs
                if 'coeffs' in value:
                    bkg[3:] = value['coeffs']
                if 'FixedPoints' in value:
                    peaks['FixedPoints'] = [(float(a), float(b))
                                            for a, b in value['FixedPoints']]
                if value.get('fit fixed points', False):
                    do_fit_fixed_points = True

            elif key == 'Instrument Parameters':
                instrument, secondary = self.data['Instrument Parameters']
                for iparam in value:
                    try:
                        instrument[iparam][2] = True
                    except IndexError:
                        raise ValueError("Invalid key:", iparam)
            else:
                raise ValueError("Unknown key:", key)
        # Fit fixed points after the fact - ensure they are after fixed points
        # are added
        if do_fit_fixed_points:
            # Background won't be fit if refinement flag not set
            orig = self.data['Background'][0][1]
            self.data['Background'][0][1] = True
            self.fit_fixed_points()
            # Restore the previous value
            self.data['Background'][0][1] = orig

    def clear_refinements(self, refs):
        """Clears the refinement parameter 'key' and its associated value.

        :param dict refs: A dictionary of parameters to clear."""
        for key, value in refs.items():
            if key == 'Limits':
                old_limits, cur_limits = self.data['Limits']
                cur_limits[0], cur_limits[1] = old_limits
            elif key == 'Sample Parameters':
                sample = self.data['Sample Parameters']
                for sparam in value:
                    sample[sparam][1] = False
            elif key == 'Background':
                bkg, peaks = self.data['Background']

                # If True or False, just set the refine parameter
                if value in (True, False):
                    bkg[1] = False
                    return

                bkg[1] = False
                if 'FixedPoints' in value:
                    if 'FixedPoints' in peaks:
                        del peaks['FixedPoints']
            elif key == 'Instrument Parameters':
                instrument, secondary = self.data['Instrument Parameters']
                for iparam in value:
                    instrument[iparam][2] = False
            else:
                raise ValueError("Unknown key:", key)

    def add_peak(self,area,dspace=None,Q=None,ttheta=None):
        '''Adds a single peak to the peak list
        :param float area: peak area
        :param float dspace: peak position as d-space (A)
        :param float Q: peak position as Q (A-1)
        :param float ttheta: peak position as 2Theta (deg)

        Note: only one of the parameters dspace, Q or ttheta may be specified
        '''
        import GSASIIlattice as G2lat
        import GSASIImath as G2mth
        if (not dspace) + (not Q) + (not ttheta) != 2:
            print('add_peak error: too many or no peak position(s) specified')
            return
        pos = ttheta
        Parms,Parms2 = self.data['Instrument Parameters']
        if Q:
            pos = G2lat.Dsp2pos(Parms,2.*np.pi/Q)
        elif dspace:
            pos = G2lat.Dsp2pos(Parms,dspace)
        peaks = self.data['Peak List']
        peaks['sigDict'] = {}        #no longer valid
        peaks['peaks'].append(G2mth.setPeakparms(Parms,Parms2,pos,area))

    def set_peakFlags(self,peaklist=None,area=None,pos=None,sig=None,gam=None):
        '''Set refinement flags for peaks
        
        :param list peaklist: a list of peaks to change flags. If None (default), changes
          are made to all peaks.
        :param bool area: Sets or clears the refinement flag for the peak area value.
          If None (the default), no change is made.
        :param bool pos: Sets or clears the refinement flag for the peak position value.
          If None (the default), no change is made.
        :param bool sig: Sets or clears the refinement flag for the peak sig (Gaussian width) value.
          If None (the default), no change is made.
        :param bool gam: Sets or clears the refinement flag for the peak sig (Lorentzian width) value.
          If None (the default), no change is made.
          
        Note that when peaks are first created the area flag is on and the other flags are
        initially off.

        Example::
        
           set_peakFlags(sig=False,gam=True)

        causes the sig refinement flag to be cleared and the gam flag to be set, in both cases for
        all peaks. The position and area flags are not changed from their previous values.
        '''
        peaks = self.data['Peak List']
        if peaklist is None:
            peaklist = range(len(peaks['peaks']))
        for i in peaklist:
            for var,j in [(area,3),(pos,1),(sig,5),(gam,7)]:
                if var is not None:
                    peaks['peaks'][i][j] = var
            
    def refine_peaks(self):
        '''Causes a refinement of peak position, background and instrument parameters
        '''
        import GSASIIpwd as G2pwd
        controls = self.proj.data.get('Controls',{})
        controls = controls.get('data',
                            {'deriv type':'analytic','min dM/M':0.001,}     #fill in defaults if needed
                            )
        peaks = self.data['Peak List']
        Parms,Parms2 = self.data['Instrument Parameters']
        background = self.data['Background']
        limits = self.data['Limits'][1]
        bxye = np.zeros(len(self.data['data'][1][1]))
        peaks['sigDict'] = G2pwd.DoPeakFit('LSQ',peaks['peaks'],background,limits,
                                           Parms,Parms2,self.data['data'][1],bxye,[],
                                           False,controls,None)[0]

    def SaveProfile(self,filename):
        '''Writes a GSAS-II (new style) .instprm file
        '''
        data,Parms2 = self.data['Instrument Parameters']
        filename = os.path.splitext(filename)[0]+'.instprm'         # make sure extension is .instprm
        File = open(filename,'w')
        File.write("#GSAS-II instrument parameter file; do not add/delete items!\n")
        for item in data:
            File.write(item+':'+str(data[item][1])+'\n')
        File.close()
        print ('Instrument parameters saved to: '+filename)

    def LoadProfile(self,filename):
        '''Reads a GSAS-II (new style) .instprm file and overwrites the current parameters
        '''
        filename = os.path.splitext(filename)[0]+'.instprm'         # make sure extension is .instprm
        File = open(filename,'r')
        S = File.readline()
        newItems = []
        newVals = []
        Found = False
        while S:
            if S[0] == '#':
                if Found:
                    break
                if 'Bank' in S:
                    if bank == int(S.split(':')[0].split()[1]):
                        S = File.readline()
                        continue
                    else:
                        S = File.readline()
                        while S and '#Bank' not in S:
                            S = File.readline()
                        continue
                else:   #a non #Bank file
                    S = File.readline()
                    continue
            Found = True
            [item,val] = S[:-1].split(':')
            newItems.append(item)
            try:
                newVals.append(float(val))
            except ValueError:
                newVals.append(val)                        
            S = File.readline()                
        File.close()
        LoadG2fil()
        self.data['Instrument Parameters'][0] = G2fil.makeInstDict(newItems,newVals,len(newVals)*[False,])

        
class G2Phase(G2ObjectWrapper):
    """A wrapper object around a given phase.

    Author: Jackson O'Donnell (jacksonhodonnell .at. gmail.com)
    """
    def __init__(self, data, name, proj):
        self.data = data
        self.name = name
        self.proj = proj

    @staticmethod
    def is_valid_refinement_key(key):
        valid_keys = ["Cell", "Atoms", "LeBail"]
        return key in valid_keys

    @staticmethod
    def is_valid_HAP_refinement_key(key):
        valid_keys = ["Babinet", "Extinction", "HStrain", "Mustrain",
                      "Pref.Ori.", "Show", "Size", "Use", "Scale"]
        return key in valid_keys

    def atom(self, atomlabel):
        """Returns the atom specified by atomlabel, or None if it does not
        exist.

        :param str atomlabel: The name of the atom (e.g. "O2")
        :returns: A :class:`G2AtomRecord` object
            representing the atom.
        """
        # Consult GSASIIobj.py for the meaning of this
        cx, ct, cs, cia = self.data['General']['AtomPtrs']
        ptrs = [cx, ct, cs, cia]
        atoms = self.data['Atoms']
        for atom in atoms:
            if atom[ct-1] == atomlabel:
                return G2AtomRecord(atom, ptrs, self.proj)

    def atoms(self):
        """Returns a list of atoms present in the phase.

        :returns: A list of :class:`G2AtomRecord` objects.

        .. seealso::
            :meth:`G2Phase.atom`
            :class:`G2AtomRecord`
        """
        ptrs = self.data['General']['AtomPtrs']
        output = []
        atoms = self.data['Atoms']
        for atom in atoms:
            output.append(G2AtomRecord(atom, ptrs, self.proj))
        return output

    def histograms(self):
        output = []
        for hname in self.data.get('Histograms', {}).keys():
            output.append(self.proj.histogram(hname))
        return output

    @property
    def ranId(self):
        return self.data['ranId']

    @property
    def id(self):
        return self.data['pId']

    @id.setter
    def id(self, val):
        self.data['pId'] = val

    def get_cell(self):
        """Returns a dictionary of the cell parameters, with keys:
            'length_a', 'length_b', 'length_c', 'angle_alpha', 'angle_beta', 'angle_gamma', 'volume'

        :returns: a dict

        .. seealso::
           :meth:`G2Phase.get_cell_and_esd`

        """
        cell = self.data['General']['Cell']
        return {'length_a': cell[1], 'length_b': cell[2], 'length_c': cell[3],
                'angle_alpha': cell[4], 'angle_beta': cell[5], 'angle_gamma': cell[6],
                'volume': cell[7]}

    def get_cell_and_esd(self):
        """
        Returns a pair of dictionaries, the first representing the unit cell, the second
        representing the estimated standard deviations of the unit cell.

        :returns: a tuple of two dictionaries

        .. seealso::
           :meth:`G2Phase.get_cell`

        """
        # translated from GSASIIstrIO.ExportBaseclass.GetCell
        import GSASIIstrIO as G2stIO
        import GSASIIlattice as G2lat
        import GSASIImapvars as G2mv
        try:
            pfx = str(self.id) + '::'
            sgdata = self['General']['SGData']
            covDict = self.proj['Covariance']['data']

            parmDict = dict(zip(covDict.get('varyList',[]),
                                covDict.get('variables',[])))
            sigDict = dict(zip(covDict.get('varyList',[]),
                               covDict.get('sig',[])))

            if covDict.get('covMatrix') is not None:
                sigDict.update(G2mv.ComputeDepESD(covDict['covMatrix'],
                                                  covDict['varyList'],
                                                  parmDict))

            A, sigA = G2stIO.cellFill(pfx, sgdata, parmDict, sigDict)
            cellSig = G2stIO.getCellEsd(pfx, sgdata, A, self.proj['Covariance']['data'])
            cellList = G2lat.A2cell(A) + (G2lat.calc_V(A),)
            cellDict, cellSigDict = {}, {}
            for i, key in enumerate(['length_a', 'length_b', 'length_c',
                                     'angle_alpha', 'angle_beta', 'angle_gamma',
                                     'volume']):
                cellDict[key] = cellList[i]
                cellSigDict[key] = cellSig[i]
            return cellDict, cellSigDict
        except KeyError:
            cell = self.get_cell()
            return cell, {key: 0.0 for key in cell}

    def export_CIF(self, outputname, quickmode=True):
        """Write this phase to a .cif file named outputname

        :param str outputname: The name of the .cif file to write to
        :param bool quickmode: Currently ignored. Carryover from exports.G2export_CIF"""
        # This code is all taken from exports/G2export_CIF.py
        # Functions copied have the same names
        import GSASIImath as G2mth
        import GSASIImapvars as G2mv
        from exports import G2export_CIF as cif

        CIFdate = dt.datetime.strftime(dt.datetime.now(),"%Y-%m-%dT%H:%M")
        CIFname = os.path.splitext(self.proj.filename)[0]
        CIFname = os.path.split(CIFname)[1]
        CIFname = ''.join([c if ord(c) < 128 else ''
                           for c in CIFname.replace(' ', '_')])
        try:
            author = self.proj['Controls']['data'].get('Author','').strip()
        except KeyError:
            pass
        oneblock = True

        covDict = self.proj['Covariance']['data']
        parmDict = dict(zip(covDict.get('varyList',[]),
                            covDict.get('variables',[])))
        sigDict = dict(zip(covDict.get('varyList',[]),
                           covDict.get('sig',[])))

        if covDict.get('covMatrix') is not None:
            sigDict.update(G2mv.ComputeDepESD(covDict['covMatrix'],
                                              covDict['varyList'],
                                              parmDict))

        with open(outputname, 'w') as fp:
            fp.write(' \n' + 70*'#' + '\n')
            cif.WriteCIFitem(fp, 'data_' + CIFname)
            # from exports.G2export_CIF.WritePhaseInfo
            cif.WriteCIFitem(fp, '\n# phase info for '+str(self.name) + ' follows')
            cif.WriteCIFitem(fp, '_pd_phase_name', self.name)
            # TODO get esds
            cellDict = self.get_cell()
            defsigL = 3*[-0.00001] + 3*[-0.001] + [-0.01] # significance to use when no sigma
            names = ['length_a','length_b','length_c',
                     'angle_alpha','angle_beta ','angle_gamma',
                     'volume']
            for key, val in cellDict.items():
                cif.WriteCIFitem(fp, '_cell_' + key, G2mth.ValEsd(val))

            cif.WriteCIFitem(fp, '_symmetry_cell_setting',
                         self.data['General']['SGData']['SGSys'])

            spacegroup = self.data['General']['SGData']['SpGrp'].strip()
            # regularize capitalization and remove trailing H/R
            spacegroup = spacegroup[0].upper() + spacegroup[1:].lower().rstrip('rh ')
            cif.WriteCIFitem(fp, '_symmetry_space_group_name_H-M', spacegroup)

            # generate symmetry operations including centering and center of symmetry
            SymOpList, offsetList, symOpList, G2oprList, G2opcodes = G2spc.AllOps(
                self.data['General']['SGData'])
            cif.WriteCIFitem(fp, 'loop_\n    _space_group_symop_id\n    _space_group_symop_operation_xyz')
            for i, op in enumerate(SymOpList,start=1):
                cif.WriteCIFitem(fp, '   {:3d}  {:}'.format(i,op.lower()))

            # TODO skipped histograms, exports/G2export_CIF.py:880

            # report atom params
            if self.data['General']['Type'] in ['nuclear','macromolecular']:        #this needs macromolecular variant, etc!
                cif.WriteAtomsNuclear(fp, self.data, self.name, parmDict, sigDict, [])
                # self._WriteAtomsNuclear(fp, parmDict, sigDict)
            else:
                raise G2ScriptException("no export for "+str(self.data['General']['Type'])+" coordinates implemented")
            # report cell contents
            cif.WriteComposition(fp, self.data, self.name, parmDict)
            if not quickmode and self.data['General']['Type'] == 'nuclear':      # report distances and angles
                # WriteDistances(fp,self.name,SymOpList,offsetList,symOpList,G2oprList)
                raise NotImplementedError("only quickmode currently supported")
            if 'Map' in self.data['General'] and 'minmax' in self.data['General']['Map']:
                cif.WriteCIFitem(fp,'\n# Difference density results')
                MinMax = self.data['General']['Map']['minmax']
                cif.WriteCIFitem(fp,'_refine_diff_density_max',G2mth.ValEsd(MinMax[0],-0.009))
                cif.WriteCIFitem(fp,'_refine_diff_density_min',G2mth.ValEsd(MinMax[1],-0.009))


    def set_refinements(self, refs):
        """Sets the refinement parameter 'key' to the specification 'value'

        :param dict refs: A dictionary of the parameters to be set. See
                          :ref:`Phase_parameters_table` for a description of
                          this dictionary.

        :returns: None"""
        for key, value in refs.items():
            if key == "Cell":
                self.data['General']['Cell'][0] = value

            elif key == "Atoms":
                for atomlabel, atomrefinement in value.items():
                    if atomlabel == 'all':
                        for atom in self.atoms():
                            atom.refinement_flags = atomrefinement
                    else:
                        atom = self.atom(atomlabel)
                        if atom is None:
                            raise ValueError("No such atom: " + atomlabel)
                        atom.refinement_flags = atomrefinement

            elif key == "LeBail":
                hists = self.data['Histograms']
                for hname, hoptions in hists.items():
                    if 'LeBail' not in hoptions:
                        hoptions['newLeBail'] = bool(True)
                    hoptions['LeBail'] = bool(value)
            else:
                raise ValueError("Unknown key:", key)

    def clear_refinements(self, refs):
        """Clears a given set of parameters.

        :param dict refs: The parameters to clear"""
        for key, value in refs.items():
            if key == "Cell":
                self.data['General']['Cell'][0] = False
            elif key == "Atoms":
                cx, ct, cs, cia = self.data['General']['AtomPtrs']

                for atomlabel in value:
                    atom = self.atom(atomlabel)
                    # Set refinement to none
                    atom.refinement_flags = ' '
            elif key == "LeBail":
                hists = self.data['Histograms']
                for hname, hoptions in hists.items():
                    if 'LeBail' not in hoptions:
                        hoptions['newLeBail'] = True
                    hoptions['LeBail'] = False
            else:
                raise ValueError("Unknown key:", key)

    def set_HAP_refinements(self, refs, histograms='all'):
        """Sets the given HAP refinement parameters between this phase and
        the given histograms

        :param dict refs: A dictionary of the parameters to be set. See
                          :ref:`HAP_parameters_table` for a description of this
                          dictionary.
        :param histograms: Either 'all' (default) or a list of the histograms
            whose HAP parameters will be set with this phase. Histogram and phase
            must already be associated

        :returns: None
        """
        if histograms == 'all':
            histograms = self.data['Histograms'].values()
        else:
            histograms = [self.data['Histograms'][h.name] for h in histograms]

        for key, val in refs.items():
            for h in histograms:
                if key == 'Babinet':
                    try:
                        sets = list(val)
                    except ValueError:
                        sets = ['BabA', 'BabU']
                    for param in sets:
                        if param not in ['BabA', 'BabU']:
                            raise ValueError("Not sure what to do with" + param)
                        for hist in histograms:
                            hist['Babinet'][param][1] = True
                elif key == 'Extinction':
                    for h in histograms:
                        h['Extinction'][1] = bool(val)
                elif key == 'HStrain':
                    for h in histograms:
                        h['HStrain'][1] = [bool(val) for p in h['HStrain'][1]]
                elif key == 'Mustrain':
                    for h in histograms:
                        mustrain = h['Mustrain']
                        newType = None
                        direction = None
                        if isinstance(val, strtypes):
                            if val in ['isotropic', 'uniaxial', 'generalized']:
                                newType = val
                            else:
                                raise ValueError("Not a Mustrain type: " + val)
                        elif isinstance(val, dict):
                            newType = val.get('type', None)
                            direction = val.get('direction', None)

                        if newType:
                            mustrain[0] = newType
                            if newType == 'isotropic':
                                mustrain[2][0] = True == val.get('refine',False)
                                mustrain[5] = [False for p in mustrain[4]]
                            elif newType == 'uniaxial':
                                if 'refine' in val:
                                    mustrain[2][0] = False
                                    types = val['refine']
                                    if isinstance(types, strtypes):
                                        types = [types]
                                    elif isinstance(types, bool):
                                        mustrain[2][1] = types
                                        mustrain[2][2] = types
                                        types = []
                                    else:
                                        raise ValueError("Not sure what to do with: "
                                                         + str(types))
                                else:
                                    types = []

                                for unitype in types:
                                    if unitype == 'equatorial':
                                        mustrain[2][0] = True
                                    elif unitype == 'axial':
                                        mustrain[2][1] = True
                                    else:
                                        msg = 'Invalid uniaxial mustrain type'
                                        raise ValueError(msg + ': ' + unitype)
                            else:  # newtype == 'generalized'
                                mustrain[2] = [False for p in mustrain[1]]
                                if 'refine' in val:
                                    mustrain[5] = [True == val['refine']]*len(mustrain[5])

                        if direction:
                            if len(direction) != 3:
                                raise ValueError("Expected hkl, found", direction)
                            direction = [int(n) for n in direction]
                            mustrain[3] = direction
                elif key == 'Size':
                    newSize = None
                    if 'value' in val:
                        newSize = float(val['value'])
                    for h in histograms:
                        size = h['Size']
                        newType = None
                        direction = None
                        if isinstance(val, strtypes):
                            if val in ['isotropic', 'uniaxial', 'ellipsoidal']:
                                newType = val
                            else:
                                raise ValueError("Not a valid Size type: " + val)
                        elif isinstance(val, dict):
                            newType = val.get('type', None)
                            direction = val.get('direction', None)

                        if newType:
                            size[0] = newType
                            refine = True == val.get('refine')
                            if newType == 'isotropic' and refine is not None:
                                size[2][0] = bool(refine)
                                if newSize: size[1][0] = newSize
                            elif newType == 'uniaxial' and refine is not None:
                                size[2][1] = bool(refine)
                                size[2][2] = bool(refine)
                                if newSize: size[1][1] = size[1][2] =newSize
                            elif newType == 'ellipsoidal' and refine is not None:
                                size[5] = [bool(refine) for p in size[5]]
                                if newSize: size[4] = [newSize for p in size[4]]

                        if direction:
                            if len(direction) != 3:
                                raise ValueError("Expected hkl, found", direction)
                            direction = [int(n) for n in direction]
                            size[3] = direction
                elif key == 'Pref.Ori.':
                    for h in histograms:
                        h['Pref.Ori.'][2] = bool(val)
                elif key == 'Show':
                    for h in histograms:
                        h['Show'] = bool(val)
                elif key == 'Use':
                    for h in histograms:
                        h['Use'] = bool(val)
                elif key == 'Scale':
                    for h in histograms:
                        h['Scale'][1] = bool(val)
                else:
                    print(u'Unknown HAP key: '+key)

    def getHAPvalues(self, histname):
        """Returns a dict with HAP values for the selected histogram

        :param histogram: is a histogram object (:class:`G2PwdrData`) or
            a histogram name or the index number of the histogram

        :returns: HAP value dict
        """
        if isinstance(histname, G2PwdrData):
            histname = histname.name
        elif histname in self.data['Histograms']:
            pass
        elif type(histname) is int:
            histname = self.proj.histograms()[histname].name
        else:
            raise G2ScriptException("Invalid histogram reference: "+str(histname))
        return self.data['Histograms'][histname]
                    
    def clear_HAP_refinements(self, refs, histograms='all'):
        """Clears the given HAP refinement parameters between this phase and
        the given histograms

        :param dict refs: A dictionary of the parameters to be cleared.
        :param histograms: Either 'all' (default) or a list of the histograms
            whose HAP parameters will be cleared with this phase. Histogram and
            phase must already be associated

        :returns: None
        """
        if histograms == 'all':
            histograms = self.data['Histograms'].values()
        else:
            histograms = [self.data['Histograms'][h.name] for h in histograms]

        for key, val in refs.items():
            for h in histograms:
                if key == 'Babinet':
                    try:
                        sets = list(val)
                    except ValueError:
                        sets = ['BabA', 'BabU']
                    for param in sets:
                        if param not in ['BabA', 'BabU']:
                            raise ValueError("Not sure what to do with" + param)
                        for hist in histograms:
                            hist['Babinet'][param][1] = False
                elif key == 'Extinction':
                    for h in histograms:
                        h['Extinction'][1] = False
                elif key == 'HStrain':
                    for h in histograms:
                        h['HStrain'][1] = [False for p in h['HStrain'][1]]
                elif key == 'Mustrain':
                    for h in histograms:
                        mustrain = h['Mustrain']
                        mustrain[2] = [False for p in mustrain[2]]
                        mustrain[5] = [False for p in mustrain[4]]
                elif key == 'Pref.Ori.':
                    for h in histograms:
                        h['Pref.Ori.'][2] = False
                elif key == 'Show':
                    for h in histograms:
                        h['Show'] = False
                elif key == 'Size':
                    for h in histograms:
                        size = h['Size']
                        size[2] = [False for p in size[2]]
                        size[5] = [False for p in size[5]]
                elif key == 'Use':
                    for h in histograms:
                        h['Use'] = False
                elif key == 'Scale':
                    for h in histograms:
                        h['Scale'][1] = False
                else:
                    print(u'Unknown HAP key: '+key)

class G2Image(G2ObjectWrapper):
    """Wrapper for an IMG tree entry, containing an image and various metadata.
    """
    # parameters in 
    ControlList = {
        'int': ['calibskip', 'pixLimit', 'edgemin', 'outChannels',
                    'outAzimuths'],
        'float': ['cutoff', 'setdist', 'wavelength', 'Flat Bkg',
                      'azmthOff', 'tilt', 'calibdmin', 'rotation',
                      'distance', 'DetDepth'],
        'bool': ['setRings', 'setDefault', 'centerAzm', 'fullIntegrate',
                     'DetDepthRef', 'showLines'],
        'str': ['SampleShape', 'binType', 'formatName', 'color',
                    'type', 'calibrant'],
        'list': ['GonioAngles', 'IOtth', 'LRazimuth', 'Oblique', 'PolaVal',
                   'SampleAbs', 'center', 'ellipses', 'linescan',
                    'pixelSize', 'range', 'ring', 'rings', 'size', ],
        'dict': ['varylist'],
#        'image': ['background image', 'dark image', 'Gain map'],
        }
    '''Defines the items known to exist in the Image Controls tree section 
    and their data types.
    '''

    def __init__(self, data, name, proj):
        self.data = data
        self.name = name
        self.proj = proj

    def setControl(self,arg,value):
        '''Set an Image Controls parameter in the current image.
        If the parameter is not found an exception is raised.

        :param str arg: the name of a parameter (dict entry) in the 
          image. The parameter must be found in :data:`ControlList`
          or an exception is raised.
        :param value: the value to set the parameter. The value is 
          cast as the appropriate type from :data:`ControlList`.
        '''
        for typ in self.ControlList:
            if arg in self.ControlList[typ]: break
        else:
            raise Exception('arg {} not defined in G2Image.setControl'
                                .format(arg))
        try:
            if typ == 'int':
                self.data['Image Controls'][arg] = int(value)
            elif typ == 'float':
                self.data['Image Controls'][arg] = float(value)
            elif typ == 'bool':
                self.data['Image Controls'][arg] = bool(value)
            elif typ == 'str':
                self.data['Image Controls'][arg] = str(value)
            elif typ == 'list':
                self.data['Image Controls'][arg] = list(value)
            elif typ == 'dict':
                self.data['Image Controls'][arg] = dict(value)
            else:
                raise Exception('Unknown type {} for arg {} in  G2Image.setControl'
                                    .format(typ,arg))
        except:
            raise Exception('Error formatting value {} as type {} for arg {} in  G2Image.setControl'
                                    .format(value,typ,arg))

    def getControl(self,arg):
        '''Return an Image Controls parameter in the current image.
        If the parameter is not found an exception is raised.

        :param str arg: the name of a parameter (dict entry) in the 
          image. 
        :returns: the value as a int, float, list,...
        '''
        if arg in self.data['Image Controls']:
            return self.data['Image Controls'][arg]
        raise Exception('arg {} not defined in G2Image.getControl'.format(arg))

    def findControl(self,arg):
        '''Finds the Image Controls parameter(s) in the current image
        that match the string in arg.

          Example: findControl('calib') will return 
          [['calibskip', 'int'], ['calibdmin', 'float'], ['calibrant', 'str']]

        :param str arg: a string containing part of the name of a 
          parameter (dict entry) in the image's Image Controls. 
        :returns: a list of matching entries in form 
          [['item','type'], ['item','type'],...] where each 'item' string 
          contains the sting in arg.
        '''
        matchList = []
        for typ in self.ControlList:
            for item in self.ControlList[typ]:
                if arg in item:
                    matchList.append([item,typ])
        return matchList

    def setControlFile(self,typ,imageRef,mult=None):
        '''Set a image to be used as a background/dark/gain map image

        :param str typ: specifies image type, which must be one of:
           'background image', 'dark image', 'gain map'; N.B. only the first
           four characters must be specified and case is ignored.
        :param imageRef: 
        :param float mult:
        '''
#        'image': ['background image', 'dark image', 'Gain map'],
        if 'back' in typ.lower():
            key = 'background image'
            mult = float(mult)
        elif 'dark' in typ.lower():
            key = 'dark image'
            mult = float(mult)
        elif 'gain' in typ.lower():
            #key = 'Gain map'
            if mult is not None:
                print('Ignoring multiplier for Gain map')
            mult = None
        else:
            raise Exception("Invalid typ {} for setControlFile".format(typ))
        imgNam = self.proj.image(imageRef).name
        if mult is None:
            self.data['Image Controls']['Gain map'] = imgNam
        else:
            self.data['Image Controls'][key] = [imgNam,mult]

    def loadControls(self,filename):
        '''load controls from a .imctrl file
        :param str filename: specifies a file to be read, which should end 
          with .imctrl
        '''
        File = open(filename,'r')
        Slines = File.readlines()
        File.close()
        G2fil.LoadControls(Slines,self.data['Image Controls'])
        print('file {} read into {}'.format(filename,self.name))

    def saveControls(self,filename):
        '''write current controls values to a .imctrl file
        :param str filename: specifies a file to write, which should end 
          with .imctrl
        '''
        G2fil.WriteControls(filename,self.data['Image Controls'])
        print('file {} written from {}'.format(filename,self.name))

##########################
# Command Line Interface #
##########################
# Each of these takes an argparse.Namespace object as their argument,
# representing the parsed command-line arguments for the relevant subcommand.
# The argument specification for each is in the subcommands dictionary (see
# below)

commandhelp={}
commandhelp["create"] = "creates a GSAS-II project, optionally adding histograms and/or phases"
def create(args):
    """Implements the create command-line subcommand. This creates a GSAS-II project, optionally adding histograms and/or phases::

  usage: GSASIIscriptable.py create [-h] [-d HISTOGRAMS [HISTOGRAMS ...]]
                                  [-i IPARAMS [IPARAMS ...]]
                                  [-p PHASES [PHASES ...]]
                                  filename
                                  
positional arguments::

  filename              the project file to create. should end in .gpx

optional arguments::

  -h, --help            show this help message and exit
  -d HISTOGRAMS [HISTOGRAMS ...], --histograms HISTOGRAMS [HISTOGRAMS ...]
                        list of datafiles to add as histograms
  -i IPARAMS [IPARAMS ...], --iparams IPARAMS [IPARAMS ...]
                        instrument parameter file, must be one for every
                        histogram
  -p PHASES [PHASES ...], --phases PHASES [PHASES ...]
                        list of phases to add. phases are automatically
                        associated with all histograms given.

    """
    proj = G2Project(gpxname=args.filename)

    hist_objs = []
    if args.histograms:
        for h,i in zip(args.histograms,args.iparams):
            print("Adding histogram from",h,"with instparm ",i)
            hist_objs.append(proj.add_powder_histogram(h, i))

    if args.phases: 
        for p in args.phases:
            print("Adding phase from",p)
            proj.add_phase(p, histograms=hist_objs)
        print('Linking phase(s) to histogram(s):')
        for h in hist_objs:
            print ('   '+h.name)

    proj.save()

commandhelp["add"] = "adds histograms and/or phases to GSAS-II project"
def add(args):
    """Implements the add command-line subcommand. This adds histograms and/or phases to GSAS-II project::

  usage: GSASIIscriptable.py add [-h] [-d HISTOGRAMS [HISTOGRAMS ...]]
                               [-i IPARAMS [IPARAMS ...]]
                               [-hf HISTOGRAMFORMAT] [-p PHASES [PHASES ...]]
                               [-pf PHASEFORMAT] [-l HISTLIST [HISTLIST ...]]
                               filename


positional arguments::

  filename              the project file to open. Should end in .gpx

optional arguments::

  -h, --help            show this help message and exit
  -d HISTOGRAMS [HISTOGRAMS ...], --histograms HISTOGRAMS [HISTOGRAMS ...]
                        list of datafiles to add as histograms
  -i IPARAMS [IPARAMS ...], --iparams IPARAMS [IPARAMS ...]
                        instrument parameter file, must be one for every
                        histogram
  -hf HISTOGRAMFORMAT, --histogramformat HISTOGRAMFORMAT
                        format hint for histogram import. Applies to all
                        histograms
  -p PHASES [PHASES ...], --phases PHASES [PHASES ...]
                        list of phases to add. phases are automatically
                        associated with all histograms given.
  -pf PHASEFORMAT, --phaseformat PHASEFORMAT
                        format hint for phase import. Applies to all phases.
                        Example: -pf CIF
  -l HISTLIST [HISTLIST ...], --histlist HISTLIST [HISTLIST ...]
                        list of histgram indices to associate with added
                        phases. If not specified, phases are associated with
                        all previously loaded histograms. Example: -l 2 3 4
    
    """
    proj = G2Project(args.filename)

    if args.histograms:
        for h,i in zip(args.histograms,args.iparams):
            print("Adding histogram from",h,"with instparm ",i)
            proj.add_powder_histogram(h, i, fmthint=args.histogramformat)

    if args.phases: 
        if not args.histlist:
            histlist = proj.histograms()
        else:
            histlist = [proj.histogram(i) for i in args.histlist]

        for p in args.phases:
            print("Adding phase from",p)
            proj.add_phase(p, histograms=histlist, fmthint=args.phaseformat)
            
        if not args.histlist:
            print('Linking phase(s) to all histogram(s)')
        else:
            print('Linking phase(s) to histogram(s):')
            for h in histlist:
                print ('   '+h.name)

    proj.save()


commandhelp["dump"] = "Shows the contents of a GSAS-II project"
def dump(args):
    """Implements the dump command-line subcommand, which shows the contents of a GSAS-II project::

       usage: GSASIIscriptable.py dump [-h] [-d] [-p] [-r] files [files ...]

positional arguments::

  files

optional arguments::

  -h, --help        show this help message and exit
  -d, --histograms  list histograms in files, overrides --raw
  -p, --phases      list phases in files, overrides --raw
  -r, --raw         dump raw file contents, default
  
    """
    if not args.histograms and not args.phases:
        args.raw = True
    if args.raw:
        import IPython.lib.pretty as pretty

    for fname in args.files:
        if args.raw:
            proj, nameList = LoadDictFromProjFile(fname)
            print("file:", fname)
            print("names:", nameList)
            for key, val in proj.items():
                print(key, ":")
                pretty.pprint(val)
        else:
            proj = G2Project(fname)
            if args.histograms:
                hists = proj.histograms()
                for h in hists:
                    print(fname, "hist", h.id, h.name)
            if args.phases:
                phase_list = proj.phases()
                for p in phase_list:
                    print(fname, "phase", p.id, p.name)


commandhelp["browse"] = "Load a GSAS-II project and then open a IPython shell to browse it"
def IPyBrowse(args):
    """Load a .gpx file and then open a IPython shell to browse it::

  usage: GSASIIscriptable.py browse [-h] files [files ...]

positional arguments::

  files       list of files to browse

optional arguments::

  -h, --help  show this help message and exit

    """
    for fname in args.files:
        proj, nameList = LoadDictFromProjFile(fname)
        msg = "\nfname {} loaded into proj (dict) with names in nameList".format(fname)
        GSASIIpath.IPyBreak_base(msg)
        break


commandhelp["refine"] = '''
Conducts refinements on GSAS-II projects according to a list of refinement
steps in a JSON dict
'''
def refine(args):
    """Implements the refine command-line subcommand:
    conducts refinements on GSAS-II projects according to a JSON refinement dict::

        usage: GSASIIscriptable.py refine [-h] gpxfile [refinements]

positional arguments::

  gpxfile      the project file to refine
  refinements  json file of refinements to apply. if not present refines file
               as-is

optional arguments::

  -h, --help   show this help message and exit
  
    """
    proj = G2Project(args.gpxfile)
    if args.refinements is None:
        proj.refine()
    else:
        import json
        with open(args.refinements) as refs:
            refs = json.load(refs)
        if type(refs) is not dict:
            raise G2ScriptException("Error: JSON object must be a dict.")
        if "code" in refs:
            print("executing code:\n|  ",'\n|  '.join(refs['code']))
            exec('\n'.join(refs['code']))
        proj.do_refinements(refs['refinements'])


commandhelp["seqrefine"] = "Not implemented. Placeholder for eventual sequential refinement implementation"
def seqrefine(args):
    """Future implementation for the seqrefine command-line subcommand """
    raise NotImplementedError("seqrefine is not yet implemented")


commandhelp["export"] = "Export phase as CIF"
def export(args):
    """Implements the export command-line subcommand: Exports phase as CIF::

      usage: GSASIIscriptable.py export [-h] gpxfile phase exportfile

positional arguments::

  gpxfile     the project file from which to export
  phase       identifier of phase to export
  exportfile  the .cif file to export to

optional arguments::

  -h, --help  show this help message and exit

    """
    proj = G2Project(args.gpxfile)
    phase = proj.phase(args.phase)
    phase.export_CIF(args.exportfile)


def _args_kwargs(*args, **kwargs):
    return args, kwargs

# A dictionary of the name of each subcommand, and a tuple
# of its associated function and a list of its arguments
# The arguments are passed directly to the add_argument() method
# of an argparse.ArgumentParser

subcommands = {"create":
               (create, [_args_kwargs('filename',
                                      help='the project file to create. should end in .gpx'),

                         _args_kwargs('-d', '--histograms',
                                      nargs='+',
                                      help='list of datafiles to add as histograms'),
                                      
                         _args_kwargs('-i', '--iparams',
                                      nargs='+',
                                      help='instrument parameter file, must be one'
                                           ' for every histogram'
                                      ),

                         _args_kwargs('-p', '--phases',
                                      nargs='+',
                                      help='list of phases to add. phases are '
                                           'automatically associated with all '
                                           'histograms given.')]),
               "add": (add, [_args_kwargs('filename',
                                      help='the project file to open. Should end in .gpx'),

                         _args_kwargs('-d', '--histograms',
                                      nargs='+',
                                      help='list of datafiles to add as histograms'),
                                      
                         _args_kwargs('-i', '--iparams',
                                      nargs='+',
                                      help='instrument parameter file, must be one'
                                           ' for every histogram'
                                      ),
                                      
                         _args_kwargs('-hf', '--histogramformat',
                                      help='format hint for histogram import. Applies to all'
                                           ' histograms'
                                      ),

                         _args_kwargs('-p', '--phases',
                                      nargs='+',
                                      help='list of phases to add. phases are '
                                           'automatically associated with all '
                                           'histograms given.'),

                         _args_kwargs('-pf', '--phaseformat',
                                      help='format hint for phase import. Applies to all'
                                           ' phases. Example: -pf CIF'
                                      ),
                                      
                         _args_kwargs('-l', '--histlist',
                                      nargs='+',
                                      help='list of histgram indices to associate with added'
                                           ' phases. If not specified, phases are'
                                           ' associated with all previously loaded'
                                           ' histograms. Example: -l 2 3 4')]),
                                           
               "dump": (dump, [_args_kwargs('-d', '--histograms',
                                     action='store_true',
                                     help='list histograms in files, overrides --raw'),

                               _args_kwargs('-p', '--phases',
                                            action='store_true',
                                            help='list phases in files, overrides --raw'),

                               _args_kwargs('-r', '--raw',
                                      action='store_true', help='dump raw file contents, default'),

                               _args_kwargs('files', nargs='+')]),

               "refine":
               (refine, [_args_kwargs('gpxfile', help='the project file to refine'),
                         _args_kwargs('refinements',
                                      help='JSON file of refinements to apply. if not present'
                                           ' refines file as-is',
                                      default=None,
                                      nargs='?')]),

               "seqrefine": (seqrefine, []),
               "export": (export, [_args_kwargs('gpxfile',
                                                help='the project file from which to export'),
                                   _args_kwargs('phase', help='identifier of phase to export'),
                                   _args_kwargs('exportfile', help='the .cif file to export to')]),
               "browse": (IPyBrowse, [_args_kwargs('files', nargs='+',
                                                   help='list of files to browse')])}


def main():
    '''The command-line interface for calling GSASIIscriptable as a shell command,
    where it is expected to be called as::

       python GSASIIscriptable.py <subcommand> <file.gpx> <options>

    The following subcommands are defined:

        * create, see :func:`create`
        * add, see :func:`add`
        * dump, see :func:`dump`
        * refine, see :func:`refine`
        * seqrefine, see :func:`seqrefine`
        * export, :func:`export`
        * browse, see :func:`IPyBrowse`

    .. seealso::
        :func:`create`
        :func:`add`
        :func:`dump`
        :func:`refine`
        :func:`seqrefine`
        :func:`export`
        :func:`IPyBrowse`
    '''
    parser = argparse.ArgumentParser(description=
        "Use of "+os.path.split(__file__)[1]+" Allows GSAS-II actions from command line."
        )
    subs = parser.add_subparsers()

    # Create all of the specified subparsers
    for name, (func, args) in subcommands.items():
        new_parser = subs.add_parser(name,help=commandhelp.get(name),
                                     description='Command "'+name+'" '+commandhelp.get(name))
        for listargs, kwds in args:
            new_parser.add_argument(*listargs, **kwds)
        new_parser.set_defaults(func=func)

    # Parse and trigger subcommand
    result = parser.parse_args()
    result.func(result)

if __name__ == '__main__':
    #fname='/tmp/corundum-template.gpx'
    #prj = G2Project(fname)
    main()
