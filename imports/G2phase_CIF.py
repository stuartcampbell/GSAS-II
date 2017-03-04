# -*- coding: utf-8 -*-
########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### SVN repository information ###################
'''
*Module G2phase_CIF: Coordinates from CIF*
------------------------------------------

Parses a CIF using  PyCifRW from James Hester and pulls out the
structural information.

If a CIF generated by ISODISTORT is encountered, extra information is
added to the phase entry and constraints are generated. 

'''
# Routines to import Phase information from CIF files
import sys
import random as ran
import numpy as np
import re
import GSASIIIO as G2IO
import GSASIIobj as G2obj
import GSASIIspc as G2spc
import GSASIIElem as G2elem
import GSASIIlattice as G2lat
import GSASIIpy3 as G2p3
import GSASIIpath
GSASIIpath.SetVersionNumber("$Revision$")
import CifFile as cif # PyCifRW from James Hester

class CIFPhaseReader(G2IO.ImportPhase):
    'Implements a phase importer from a possibly multi-block CIF file'
    def __init__(self):
        super(self.__class__,self).__init__( # fancy way to say ImportPhase.__init__
            extensionlist=('.CIF','.cif','.txt'),
            strictExtension=False,
            formatName = 'CIF',
            longFormatName = 'Crystallographic Information File import'
            )
        
    def ContentsValidator(self, filepointer):
        return self.CIFValidator(filepointer)

    def Reader(self,filename,filepointer, ParentFrame=None, usedRanIdList=[], **unused):
        self.isodistort_warnings = ''
        self.Phase = G2IO.SetNewPhase(Name='new phase',SGData=G2IO.P1SGData) # create a new empty phase dict
        # make sure the ranId is really unique!
        while self.Phase['ranId'] in usedRanIdList:
            self.Phase['ranId'] = ran.randint(0,sys.maxint)
        returnstat = False
        cellitems = (
            '_cell_length_a','_cell_length_b','_cell_length_c',
            '_cell_angle_alpha','_cell_angle_beta','_cell_angle_gamma',)
#        cellwaveitems = (
#            '_cell_wave_vector_seq_id',
#            '_cell_wave_vector_x','_cell_wave_vector_y','_cell_wave_vector_z')
        reqitems = (
             '_atom_site_fract_x',
             '_atom_site_fract_y',
             '_atom_site_fract_z',
            )
        phasenamefields = (
            '_chemical_name_common',
            '_pd_phase_name',
            '_chemical_formula_sum'
            )
        self.ShowBusy() # this can take a while
        cf = G2IO.ReadCIF(filename)
        self.DoneBusy()
        # scan blocks for structural info
        self.errors = 'Error during scan of blocks for datasets'
        str_blklist = []
        for blk in cf.keys():
            for r in reqitems+cellitems:
                if r not in cf[blk].keys():
                    break
            else:
                str_blklist.append(blk)
        if not str_blklist:
            selblk = None # no block to choose
        elif len(str_blklist) == 1: # only one choice
            selblk = 0
        else:                       # choose from options
            choice = []
            for blknm in str_blklist:
                choice.append('')
                # accumumlate some info about this phase
                choice[-1] += blknm + ': '
                for i in phasenamefields: # get a name for the phase
                    name = cf[blknm].get(i).strip()
                    if name is None or name == '?' or name == '.':
                        continue
                    else:
                        choice[-1] += name.strip()[:20] + ', '
                        break
                na = len(cf[blknm].get("_atom_site_fract_x"))
                if na == 1:
                    choice[-1] += '1 atom'
                else:
                    choice[-1] += ('%d' % nd) + ' atoms'
                choice[-1] += ', cell: '
                fmt = "%.2f,"
                for i,key in enumerate(cellitems):
                    if i == 3: fmt = "%.f,"
                    if i == 5: fmt = "%.f"
                    choice[-1] += fmt % cif.get_number_with_esd(
                        cf[blknm].get(key))[0]
                sg = cf[blknm].get("_symmetry_space_group_name_H-M",'')
                if not sg: sg = cf[blknm].get("_space_group_name_H-M_alt",'')
                if sg: choice[-1] += ', (' + sg.strip() + ')'
            selblk = self.PhaseSelector(
                choice,
                ParentFrame=ParentFrame,
                title= 'Select a phase from one the CIF data_ blocks below',
                size=(600,100)
                )
        self.errors = 'Error during reading of selected block'
        if selblk is None:
            returnstat = False # no block selected or available
        else:
            blknm = str_blklist[selblk]
            blk = cf[str_blklist[selblk]]
            E = True
            Super = False
            SpGrp = blk.get("_symmetry_space_group_name_H-M",'')
            if not SpGrp:
                SpGrp = blk.get("_space_group_name_H-M_alt",'')
            if not SpGrp:
                sspgrp = blk.get("_space_group_ssg_name",'').split('(')
                SpGrp = sspgrp[0]
                SuperSg = '('+sspgrp[1].replace('\\','')
                Super = True
                SuperVec = [[0,0,.1],False,4]
            # try normalizing the space group, to see if we can pick the space group out of a table
            SpGrpNorm = G2spc.StandardizeSpcName(SpGrp)
            if SpGrpNorm:
                E,SGData = G2spc.SpcGroup(SpGrpNorm)
            # nope, try the space group "out of the Box"
            if E and SpGrp:
                E,SGData = G2spc.SpcGroup(SpGrp)
            if E:
                if not SpGrp:
                    self.warnings += 'No space group name was found in the CIF.'
                    self.warnings += '\nThe space group has been set to "P 1". '
                    self.warnings += "Change this in phase's General tab."
                else:
                    self.warnings += 'ERROR in space group symbol '+SpGrp
                    self.warnings += '\nThe space group has been set to "P 1". '
                    self.warnings += "Change this in phase's General tab."
                    self.warnings += '\nAre there spaces separating axial fields?\n\nError msg: '
                    self.warnings += G2spc.SGErrors(E)
                SGData = G2IO.SGData # P 1
            self.Phase['General']['SGData'] = SGData
            # cell parameters
            cell = []
            for lbl in cellitems:
                cell.append(cif.get_number_with_esd(blk[lbl])[0])
            Volume = G2lat.calc_V(G2lat.cell2A(cell))
            self.Phase['General']['Cell'] = [False,]+cell+[Volume,]
            # read in atoms
            self.errors = 'Error during reading of atoms'
            atomlbllist = [] # table to look up atom IDs
            atomloop = blk.GetLoop('_atom_site_label')
            atomkeys = [i.lower() for i in atomloop.keys()]
            if not blk.get('_atom_site_type_symbol'):
                self.isodistort_warnings += '\natom types are missing. \n Check & revise atom types as needed'
            if blk.get('_atom_site_aniso_label'):
                anisoloop = blk.GetLoop('_atom_site_aniso_label')
                anisokeys = [i.lower() for i in anisoloop.keys()]
                anisolabels = blk.get('_atom_site_aniso_label')
            else:
                anisoloop = None
                anisokeys = []
                anisolabels = []
            if Super:
                occFloop = None
                occCloop = None
                occFdict = {}
                occCdict = {}
                displSloop = None
                displFloop = None
                dispSdict = {}
                dispFdict = {}
                UijFloop = None
                UijFdict = {}
                if blk.get('_atom_site_occ_Fourier_atom_site_label'):
                    occFloop = blk.GetLoop('_atom_site_occ_Fourier_atom_site_label')
                    occFdict = dict(occFloop.items())
                if blk.get('_atom_site_occ_special_func_atom_site_label'):  #Crenel (i.e. Block Wave) occ
                    occCloop = blk.GetLoop('_atom_site_occ_special_func_atom_site_label')
                    occCdict = dict(occCloop.items())
                if blk.get('_atom_site_displace_Fourier_atom_site_label'):
                    displFloop = blk.GetLoop('_atom_site_displace_Fourier_atom_site_label')
                    displFdict = dict(displFloop.items())                            
                if blk.get('_atom_site_displace_special_func_atom_site_label'): #sawtooth
                    displSloop = blk.GetLoop('_atom_site_displace_special_func_atom_site_label')
                    displSdict = dict(displSloop.items())
                if blk.get('_atom_site_U_Fourier_atom_site_label'):
                    UijFloop = blk.GetLoop('_atom_site_U_Fourier_atom_site_label')
                    UijFdict = dict(UijFloop.items())
            self.Phase['Atoms'] = []
            G2AtomDict = {  '_atom_site_type_symbol' : 1,
                            '_atom_site_label' : 0,
                            '_atom_site_fract_x' : 3,
                            '_atom_site_fract_y' : 4,
                            '_atom_site_fract_z' : 5,
                            '_atom_site_occupancy' : 6,
                            '_atom_site_aniso_u_11' : 11,
                            '_atom_site_aniso_u_22' : 12,
                            '_atom_site_aniso_u_33' : 13,
                            '_atom_site_aniso_u_12' : 14,
                            '_atom_site_aniso_u_13' : 15,
                            '_atom_site_aniso_u_23' : 16, }

            ranIdlookup = {}
            for aitem in atomloop:
                atomlist = ['','','',0,0,0,1.0,'',0,'I',0.01,0,0,0,0,0,0,0]
                atomlist[-1] = ran.randint(0,sys.maxint) # add a random Id
                while atomlist[-1] in ranIdlookup:
                    atomlist[-1] = ran.randint(0,sys.maxint) # make it unique
                for val,key in zip(aitem,atomkeys):
                    col = G2AtomDict.get(key)
                    if col >= 3:
                        atomlist[col] = cif.get_number_with_esd(val)[0]
                        if col >= 11: atomlist[9] = 'A' # if any Aniso term is defined, set flag
                    elif col is not None:
                        atomlist[col] = val
                    elif key in ('_atom_site_thermal_displace_type',
                               '_atom_site_adp_type'):   #Iso or Aniso?
                        if val.lower() == 'uani':
                            atomlist[9] = 'A'
                    elif key == '_atom_site_u_iso_or_equiv':
                        uisoval =cif.get_number_with_esd(val)[0]
                        if uisoval is not None: atomlist[10] = uisoval
                if not atomlist[1] and atomlist[0]:
                    typ = atomlist[0].rstrip('0123456789-+')
                    if G2elem.CheckElement(typ):
                        atomlist[1] = typ
                    if not atomlist[1]:
                        atomlist[1] = 'Xe'
                        self.warnings += ' Atom type '+typ+' not recognized; Xe assumed\n'
                if atomlist[0] in anisolabels: # does this atom have aniso values in separate loop?
                    atomlist[9] = 'A'  # set the aniso flag
                    for val,key in zip( # load the values
                            anisoloop.GetKeyedPacket('_atom_site_aniso_label',atomlist[0]), 
                            anisokeys):
                        col = G2AtomDict.get(key)
                        if col:
                            atomlist[col] = cif.get_number_with_esd(val)[0]
                atomlist[7],atomlist[8] = G2spc.SytSym(atomlist[3:6],SGData)[:2]
                atomlist[1] = G2elem.FixValence(atomlist[1])
                self.Phase['Atoms'].append(atomlist)
                ranIdlookup[atomlist[0]] = atomlist[-1]
                if atomlist[0] in atomlbllist:
                    self.warnings += ' ERROR: repeated atom label: '+atomlist[0]
                else:
                    atomlbllist.append(atomlist[0])
                if Super:
                    Sfrac = []
                    Sadp = []                      
                    Spos = np.zeros((4,6))
                    nim = -1
                    for i,item in enumerate(displFdict['_atom_site_displace_Fourier_atom_site_label']):
                        if item == atomlist[0]:
                            waveType = 'Fourier'                                
                            ix = ['x','y','z'].index(displFdict['_atom_site_displace_Fourier_axis'][i])
                            im = int(displFdict['_atom_site_displace_Fourier_wave_vector_seq_id'][i])
                            if im != nim:
                                nim = im
                            val = displFdict['_atom_site_displace_Fourier_param_sin'][i]
                            Spos[im-1][ix] = cif.get_number_with_esd(val)[0]
                            val = displFdict['_atom_site_displace_Fourier_param_cos'][i]
                            Spos[im-1][ix+3] = cif.get_number_with_esd(val)[0]
                    if nim >= 0:
                        Spos = [[spos,False] for spos in Spos[:nim]]
                    else:
                        Spos = []
                    if UijFdict:
                        nim = -1
                        Sadp = np.zeros((4,12))
                        for i,item in enumerate(UijFdict['_atom_site_U_Fourier_atom_site_label']):
                            if item == atomlist[0]:
                                ix = ['U11','U22','U33','U12','U13','U23'].index(UijFdict['_atom_site_U_Fourier_tens_elem'][i])
                                im = int(UijFdict['_atom_site_U_Fourier_wave_vector_seq_id'][i])
                                if im != nim:
                                    nim = im
                                val = UijFdict['_atom_site_U_Fourier_param_sin'][i]
                                Sadp[im-1][ix] = cif.get_number_with_esd(val)[0]
                                val = UijFdict['_atom_site_U_Fourier_param_cos'][i]
                                Sadp[im-1][ix+6] = cif.get_number_with_esd(val)[0]
                        if nim >= 0:
                            Sadp = [[sadp,False] for sadp in Sadp[:nim]]
                        else:
                            Sadp = []
                    
                    SSdict = {'SS1':{'waveType':waveType,'Sfrac':Sfrac,'Spos':Spos,'Sadp':Sadp,'Smag':[]}}
                    atomlist.append(SSdict)
            if len(atomlbllist) != len(self.Phase['Atoms']):
                self.isodistort_warnings += '\nRepeated atom labels prevents ISODISTORT decode'
            for lbl in phasenamefields: # get a name for the phase
                name = blk.get(lbl)
                if name is None:
                    continue
                name = name.strip()
                if name == '?' or name == '.':
                    continue
                else:
                    break
            else: # no name found, use block name for lack of a better choice
                name = blknm
            self.Phase['General']['Name'] = name.strip()[:20]
            self.Phase['General']['Super'] = Super
            if Super:
                self.Phase['General']['Type'] = 'modulated'
                self.Phase['General']['SuperVec'] = SuperVec
                self.Phase['General']['SuperSg'] = SuperSg
                self.Phase['General']['SSGData'] = G2spc.SSpcGroup(SGData,SuperSg)[1]
            if not self.isodistort_warnings:
                if blk.get('_iso_displacivemode_label') or blk.get('_iso_occupancymode_label'):
                    self.errors = "Error while processing ISODISTORT constraints"
                    self.ISODISTORT_proc(blk,atomlbllist,ranIdlookup)
            else:
                self.warnings += self.isodistort_warnings
            returnstat = True
        return returnstat

    def ISODISTORT_proc(self,blk,atomlbllist,ranIdlookup):
        'Process ISODISTORT items to create constraints etc.'
        varLookup = {'dx':'dAx','dy':'dAy','dz':'dAz','do':'Afrac'}
        'Maps ISODISTORT parm names to GSAS-II names'
        #----------------------------------------------------------------------
        # read in the ISODISTORT displacement modes
        #----------------------------------------------------------------------
        self.Constraints = []
        explaination = {}
        if blk.get('_iso_displacivemode_label'):
            modelist = []
            shortmodelist = []
            for lbl in blk.get('_iso_displacivemode_label'):
                modelist.append(lbl)
                # assume lbl is of form SSSSS[x,y,z]AAAA(a,b,...)BBBBB
                # where SSSSS is the parent spacegroup, [x,y,z] is a location 
                regexp = re.match(r'.*?\[.*?\](.*?)\(.*?\)(.*)',lbl)
                # this extracts the AAAAA and BBBBB parts of the string
                if regexp:
                    lbl = regexp.expand(r'\1\2') # parse succeeded, make a short version
                G2obj.MakeUniqueLabel(lbl,shortmodelist) # make unique and add to list
            # read in the coordinate offset variables names and map them to G2 names/objects
            coordVarLbl = []
            G2varLbl = []
            G2varObj = []
            error = False
            for lbl in blk.get('_iso_deltacoordinate_label'):
                coordVarLbl.append(lbl)
                if '_' in lbl:
                    albl = lbl[:lbl.rfind('_')]
                    vlbl = lbl[lbl.rfind('_')+1:]
                else:
                    self.warnings += ' ERROR: _iso_deltacoordinate_label not parsed: '+lbl
                    error = True
                    continue
                if albl not in atomlbllist:
                    self.warnings += ' ERROR: _iso_deltacoordinate_label atom not found: '+lbl
                    error = True
                    continue
                else:
                    anum = atomlbllist.index(albl)
                var = varLookup.get(vlbl)
                if not var:
                    self.warnings += ' ERROR: _iso_deltacoordinate_label variable not found: '+lbl
                    error = True
                    continue
                G2varLbl.append('::'+var+':'+str(anum)) # variable name, less phase ID
                G2varObj.append(G2obj.G2VarObj(
                    (self.Phase['ranId'],None,var,ranIdlookup[albl])
                    ))
            if error:
                raise Exception,"Error decoding variable labels"

            if len(G2varObj) != len(modelist):
                print "non-square input"
                raise Exception,"Rank of _iso_displacivemode != _iso_deltacoordinate"

            error = False
            ParentCoordinates = {}
            for lbl,exp in zip(
                blk.get('_iso_coordinate_label'),
                blk.get('_iso_coordinate_formula'),
                ):
                if '_' in lbl:
                    albl = lbl[:lbl.rfind('_')]
                    vlbl = lbl[lbl.rfind('_')+1:]
                else:
                    self.warnings += ' ERROR: _iso_coordinate_label not parsed: '+lbl
                    error = True
                    continue
                if vlbl not in 'xyz' or len(vlbl) != 1:
                    self.warnings += ' ERROR: _iso_coordinate_label coordinate not parsed: '+lbl
                    error = True
                    continue
                i = 'xyz'.index(vlbl)
                if not ParentCoordinates.get(albl):
                    ParentCoordinates[albl] = [None,None,None]
                if '+' in exp:
                    val = exp.split('+')[0].strip()
                    val = G2p3.FormulaEval(val)
                    if val is None:
                        self.warnings += ' ERROR: _iso_coordinate_formula coordinate not interpreted: '+lbl
                        error = True
                        continue
                    ParentCoordinates[albl][i] = val
                else:
                    ParentCoordinates[albl][i] = G2p3.FormulaEval(exp)
            if error:
                print self.warnings
                raise Exception,"Error decoding variable labels"
            # get mapping of modes to atomic coordinate displacements
            displacivemodematrix = np.zeros((len(G2varObj),len(G2varObj)))
            for row,col,val in zip(
                blk.get('_iso_displacivemodematrix_row'),
                blk.get('_iso_displacivemodematrix_col'),
                blk.get('_iso_displacivemodematrix_value'),):
                displacivemodematrix[int(row)-1,int(col)-1] = float(val)
            # Invert to get mapping of atom displacements to modes
            displacivemodeInvmatrix = np.linalg.inv(displacivemodematrix)
            # create the constraints
            for i,row in enumerate(displacivemodeInvmatrix):
                constraint = []
                for j,(lbl,k) in enumerate(zip(coordVarLbl,row)):
                    if k == 0: continue
                    constraint.append([k,G2varObj[j]])
                constraint += [shortmodelist[i],False,'f']
                self.Constraints.append(constraint)
            #----------------------------------------------------------------------
            # save the ISODISTORT info for "mode analysis"
            if 'ISODISTORT' not in self.Phase: self.Phase['ISODISTORT'] = {}
            self.Phase['ISODISTORT'].update({
                'IsoModeList' : modelist,
                'G2ModeList' : shortmodelist,
                'IsoVarList' : coordVarLbl,
                'G2VarList' : G2varObj,
                'ParentStructure' : ParentCoordinates,
                'Var2ModeMatrix' : displacivemodeInvmatrix,
                'Mode2VarMatrix' : displacivemodematrix,
                })
            # make explaination dictionary
            for mode,shortmode in zip(modelist,shortmodelist):
                explaination[shortmode] = "ISODISTORT full name "+str(mode)
        #----------------------------------------------------------------------
        # now read in the ISODISTORT occupancy modes
        #----------------------------------------------------------------------
        if blk.get('_iso_occupancymode_label'):
            modelist = []
            shortmodelist = []
            for lbl in blk.get('_iso_occupancymode_label'):
                modelist.append(lbl)
                # assume lbl is of form SSSSS[x,y,z]AAAA(a,b,...)BBBBB
                # where SSSSS is the parent spacegroup, [x,y,z] is a location 
                regexp = re.match(r'.*?\[.*?\](.*?)\(.*?\)(.*)',lbl)
                # this extracts the AAAAA and BBBBB parts of the string
                if regexp:
                    lbl = regexp.expand(r'\1\2') # parse succeeded, make a short version
                lbl = lbl.replace('order','o')
                G2obj.MakeUniqueLabel(lbl,shortmodelist) # make unique and add to list
            # read in the coordinate offset variables names and map them to G2 names/objects
            occVarLbl = []
            G2varLbl = []
            G2varObj = []
            error = False
            for lbl in blk.get('_iso_deltaoccupancy_label'):
                occVarLbl.append(lbl)
                if '_' in lbl:
                    albl = lbl[:lbl.rfind('_')]
                    vlbl = lbl[lbl.rfind('_')+1:]
                else:
                    self.warnings += ' ERROR: _iso_deltaoccupancy_label not parsed: '+lbl
                    error = True
                    continue
                if albl not in atomlbllist:
                    self.warnings += ' ERROR: _iso_deltaoccupancy_label atom not found: '+lbl
                    error = True
                    continue
                else:
                    anum = atomlbllist.index(albl)
                var = varLookup.get(vlbl)
                if not var:
                    self.warnings += ' ERROR: _iso_deltaoccupancy_label variable not found: '+lbl
                    error = True
                    continue
                G2varLbl.append('::'+var+':'+str(anum)) # variable name, less phase ID
                G2varObj.append(G2obj.G2VarObj(
                    (self.Phase['ranId'],None,var,ranIdlookup[albl])
                    ))
            if error:
                raise Exception,"Error decoding variable labels"

            if len(G2varObj) != len(modelist):
                print "non-square input"
                raise Exception,"Rank of _iso_occupancymode != _iso_deltaoccupancy"

            error = False
            ParentCoordinates = {}
            for lbl,exp in zip(
                blk.get('_iso_occupancy_label'),
                blk.get('_iso_occupancy_formula'),
                ):
                if '_' in lbl:
                    albl = lbl[:lbl.rfind('_')]
                    vlbl = lbl[lbl.rfind('_')+1:]
                else:
                    self.warnings += ' ERROR: _iso_occupancy_label not parsed: '+lbl
                    error = True
                    continue
                if vlbl != 'occ':
                    self.warnings += ' ERROR: _iso_occupancy_label coordinate not parsed: '+lbl
                    error = True
                    continue
                if '+' in exp:
                    val = exp.split('+')[0].strip()
                    val = G2p3.FormulaEval(val)
                    if val is None:
                        self.warnings += ' ERROR: _iso_occupancy_formula coordinate not interpreted: '+lbl
                        error = True
                        continue
                    ParentCoordinates[albl] = val
            if error:
                raise Exception,"Error decoding occupancy labels"
            # get mapping of modes to atomic coordinate displacements
            occupancymodematrix = np.zeros((len(G2varObj),len(G2varObj)))
            for row,col,val in zip(
                blk.get('_iso_occupancymodematrix_row'),
                blk.get('_iso_occupancymodematrix_col'),
                blk.get('_iso_occupancymodematrix_value'),):
                occupancymodematrix[int(row)-1,int(col)-1] = float(val)
            # Invert to get mapping of atom displacements to modes
            occupancymodeInvmatrix = np.linalg.inv(occupancymodematrix)
            # create the constraints
            for i,row in enumerate(occupancymodeInvmatrix):
                constraint = []
                for j,(lbl,k) in enumerate(zip(occVarLbl,row)):
                    if k == 0: continue
                    constraint.append([k,G2varObj[j]])
                constraint += [shortmodelist[i],False,'f']
                self.Constraints.append(constraint)
            #----------------------------------------------------------------------
            # save the ISODISTORT info for "mode analysis"
            if 'ISODISTORT' not in self.Phase: self.Phase['ISODISTORT'] = {}
            self.Phase['ISODISTORT'].update({
                'OccModeList' : modelist,
                'G2OccModeList' : shortmodelist,
                'OccVarList' : occVarLbl,
                'G2OccVarList' : G2varObj,
                'BaseOcc' : ParentCoordinates,
                'Var2OccMatrix' : occupancymodeInvmatrix,
                'Occ2VarMatrix' : occupancymodematrix,
                })
            # make explaination dictionary
            for mode,shortmode in zip(modelist,shortmodelist):
                explaination[shortmode] = "ISODISTORT full name "+str(mode)
        #----------------------------------------------------------------------
        # done with read
        #----------------------------------------------------------------------
        if explaination: self.Constraints.append(explaination)

        # # debug: show the mode var to mode relations
        # for i,row in enumerate(displacivemodeInvmatrix):
        #     l = ''
        #     for j,(lbl,k) in enumerate(zip(coordVarLbl,row)):
        #         if k == 0: continue
        #         if l: l += ' + '
        #         #l += lbl+' * '+str(k)
        #         l += G2varLbl[j]+' * '+str(k)
        #     print str(i) + ': '+shortmodelist[i]+' = '+l
        # print 70*'='

        # # debug: Get the ISODISTORT offset values
        # coordVarDelta = {}
        # for lbl,val in zip(
        #     blk.get('_iso_deltacoordinate_label'),
        #     blk.get('_iso_deltacoordinate_value'),):
        #     coordVarDelta[lbl] = float(val)
        # modeVarDelta = {}
        # for lbl,val in zip(
        #     blk.get('_iso_displacivemode_label'),
        #     blk.get('_iso_displacivemode_value'),):
        #     modeVarDelta[lbl] = cif.get_number_with_esd(val)[0]

        # print 70*'='
        # # compute the mode values from the reported coordinate deltas
        # for i,row in enumerate(displacivemodeInvmatrix):
        #     l = ''
        #     sl = ''
        #     s = 0.
        #     for lbl,k in zip(coordVarLbl,row):
        #         if k == 0: continue
        #         if l: l += ' + '
        #         l += lbl+' * '+str(k)
        #         if sl: sl += ' + '
        #         sl += str(coordVarDelta[lbl])+' * '+str(k)
        #         s += coordVarDelta[lbl] * k
        #     print 'a'+str(i)+' = '+l
        #     print '\t= '+sl
        #     print  modelist[i],shortmodelist[i],modeVarDelta[modelist[i]],s
        #     print

        # print 70*'='
        # # compute the coordinate displacements from the reported mode values
        # for i,lbl,row in zip(range(len(coordVarLbl)),coordVarLbl,displacivemodematrix):
        #     l = ''
        #     sl = ''
        #     s = 0.0
        #     for j,k in enumerate(row):
        #         if k == 0: continue
        #         if l: l += ' + '
        #         l += 'a'+str(j+1)+' * '+str(k)
        #         if sl: sl += ' + '
        #         sl += str(shortmodelist[j]) +' = '+ str(modeVarDelta[modelist[j]]) + ' * '+str(k)
        #         s += modeVarDelta[modelist[j]] * k
        #     print lbl+' = '+l
        #     print '\t= '+sl
        #     print lbl,G2varLbl[i],coordVarDelta[lbl],s
        #     print

        # determine the coordinate delta values from deviations from the parent structure
        # for atmline in self.Phase['Atoms']:
        #     lbl = atmline[0]
        #     x,y,z = atmline[3:6]
        #     if lbl not in ParentCoordinates:
        #         print lbl,x,y,z
        #         continue
        #     px,py,pz = ParentCoordinates[lbl]
        #     print lbl,x,y,z,x-px,y-py,z-pz
