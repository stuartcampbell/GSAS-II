# -*- coding: utf-8 -*-
'''
*GSASIIstrMath - structure math routines*
-----------------------------------------
'''
########### SVN repository information ###################
# $Date: 2013-05-17 12:13:15 -0500 (Fri, 17 May 2013) $
# $Author: vondreele $
# $Revision: 920 $
# $URL: https://subversion.xor.aps.anl.gov/pyGSAS/trunk/GSASIIstrMath.py $
# $Id: GSASIIstrMath.py 920 2013-05-17 17:13:15Z vondreele $
########### SVN repository information ###################
import time
import math
import copy
import numpy as np
import numpy.ma as ma
import numpy.linalg as nl
import scipy.optimize as so
import GSASIIpath
GSASIIpath.SetVersionNumber("$Revision: 920 $")
import GSASIIElem as G2el
import GSASIIlattice as G2lat
import GSASIIspc as G2spc
import GSASIIpwd as G2pwd
import GSASIImapvars as G2mv
import GSASIImath as G2mth

sind = lambda x: np.sin(x*np.pi/180.)
cosd = lambda x: np.cos(x*np.pi/180.)
tand = lambda x: np.tan(x*np.pi/180.)
asind = lambda x: 180.*np.arcsin(x)/np.pi
acosd = lambda x: 180.*np.arccos(x)/np.pi
atan2d = lambda y,x: 180.*np.arctan2(y,x)/np.pi
    
ateln2 = 8.0*math.log(2.0)

################################################################################
##### Rigid Body Models
################################################################################
        
def ApplyRBModels(parmDict,Phases,rigidbodyDict,Update=False):
    ''' Takes RB info from RBModels in Phase and RB data in rigidbodyDict along with
    current RB values in parmDict & modifies atom contents (xyz & Uij) of parmDict
    '''
    atxIds = ['Ax:','Ay:','Az:']
    atuIds = ['AU11:','AU22:','AU33:','AU12:','AU13:','AU23:']
    RBIds = rigidbodyDict.get('RBIds',{'Vector':[],'Residue':[]})  #these are lists of rbIds
    if not RBIds['Vector'] and not RBIds['Residue']:
        return
    VRBIds = RBIds['Vector']
    RRBIds = RBIds['Residue']
    if Update:
        RBData = rigidbodyDict
    else:
        RBData = copy.deepcopy(rigidbodyDict)     # don't mess with original!
    if RBIds['Vector']:                       # first update the vector magnitudes
        VRBData = RBData['Vector']
        for i,rbId in enumerate(VRBIds):
            if VRBData[rbId]['useCount']:
                for j in range(len(VRBData[rbId]['VectMag'])):
                    name = '::RBV;'+str(j)+':'+str(i)
                    VRBData[rbId]['VectMag'][j] = parmDict[name]
    for phase in Phases:
        Phase = Phases[phase]
        General = Phase['General']
        cell = General['Cell'][1:7]
        Amat,Bmat = G2lat.cell2AB(cell)
        AtLookup = G2mth.FillAtomLookUp(Phase['Atoms'])
        pfx = str(Phase['pId'])+'::'
        if Update:
            RBModels = Phase['RBModels']
        else:
            RBModels =  copy.deepcopy(Phase['RBModels']) # again don't mess with original!
        for irb,RBObj in enumerate(RBModels.get('Vector',[])):
            jrb = VRBIds.index(RBObj['RBId'])
            rbsx = str(irb)+':'+str(jrb)
            for i,px in enumerate(['RBVPx:','RBVPy:','RBVPz:']):
                RBObj['Orig'][0][i] = parmDict[pfx+px+rbsx]
            for i,po in enumerate(['RBVOa:','RBVOi:','RBVOj:','RBVOk:']):
                RBObj['Orient'][0][i] = parmDict[pfx+po+rbsx]
            RBObj['Orient'][0] = G2mth.normQ(RBObj['Orient'][0])
            TLS = RBObj['ThermalMotion']
            if 'T' in TLS[0]:
                for i,pt in enumerate(['RBVT11:','RBVT22:','RBVT33:','RBVT12:','RBVT13:','RBVT23:']):
                    TLS[1][i] = parmDict[pfx+pt+rbsx]
            if 'L' in TLS[0]:
                for i,pt in enumerate(['RBVL11:','RBVL22:','RBVL33:','RBVL12:','RBVL13:','RBVL23:']):
                    TLS[1][i+6] = parmDict[pfx+pt+rbsx]
            if 'S' in TLS[0]:
                for i,pt in enumerate(['RBVS12:','RBVS13:','RBVS21:','RBVS23:','RBVS31:','RBVS32:','RBVSAA:','RBVSBB:']):
                    TLS[1][i+12] = parmDict[pfx+pt+rbsx]
            if 'U' in TLS[0]:
                TLS[1][0] = parmDict[pfx+'RBVU:'+rbsx]
            XYZ,Cart = G2mth.UpdateRBXYZ(Bmat,RBObj,RBData,'Vector')
            UIJ = G2mth.UpdateRBUIJ(Bmat,Cart,RBObj)
            for i,x in enumerate(XYZ):
                atId = RBObj['Ids'][i]
                for j in [0,1,2]:
                    parmDict[pfx+atxIds[j]+str(AtLookup[atId])] = x[j]
                if UIJ[i][0] == 'A':
                    for j in range(6):
                        parmDict[pfx+atuIds[j]+str(AtLookup[atId])] = UIJ[i][j+2]
                elif UIJ[i][0] == 'I':
                    parmDict[pfx+'AUiso:'+str(AtLookup[atId])] = UIJ[i][1]
            
        for irb,RBObj in enumerate(RBModels.get('Residue',[])):
            jrb = RRBIds.index(RBObj['RBId'])
            rbsx = str(irb)+':'+str(jrb)
            for i,px in enumerate(['RBRPx:','RBRPy:','RBRPz:']):
                RBObj['Orig'][0][i] = parmDict[pfx+px+rbsx]
            for i,po in enumerate(['RBROa:','RBROi:','RBROj:','RBROk:']):
                RBObj['Orient'][0][i] = parmDict[pfx+po+rbsx]                
            RBObj['Orient'][0] = G2mth.normQ(RBObj['Orient'][0])
            TLS = RBObj['ThermalMotion']
            if 'T' in TLS[0]:
                for i,pt in enumerate(['RBRT11:','RBRT22:','RBRT33:','RBRT12:','RBRT13:','RBRT23:']):
                    RBObj['ThermalMotion'][1][i] = parmDict[pfx+pt+rbsx]
            if 'L' in TLS[0]:
                for i,pt in enumerate(['RBRL11:','RBRL22:','RBRL33:','RBRL12:','RBRL13:','RBRL23:']):
                    RBObj['ThermalMotion'][1][i+6] = parmDict[pfx+pt+rbsx]
            if 'S' in TLS[0]:
                for i,pt in enumerate(['RBRS12:','RBRS13:','RBRS21:','RBRS23:','RBRS31:','RBRS32:','RBRSAA:','RBRSBB:']):
                    RBObj['ThermalMotion'][1][i+12] = parmDict[pfx+pt+rbsx]
            if 'U' in TLS[0]:
                RBObj['ThermalMotion'][1][0] = parmDict[pfx+'RBRU:'+rbsx]
            for itors,tors in enumerate(RBObj['Torsions']):
                tors[0] = parmDict[pfx+'RBRTr;'+str(itors)+':'+rbsx]
            XYZ,Cart = G2mth.UpdateRBXYZ(Bmat,RBObj,RBData,'Residue')
            UIJ = G2mth.UpdateRBUIJ(Bmat,Cart,RBObj)
            for i,x in enumerate(XYZ):
                atId = RBObj['Ids'][i]
                for j in [0,1,2]:
                    parmDict[pfx+atxIds[j]+str(AtLookup[atId])] = x[j]
                if UIJ[i][0] == 'A':
                    for j in range(6):
                        parmDict[pfx+atuIds[j]+str(AtLookup[atId])] = UIJ[i][j+2]
                elif UIJ[i][0] == 'I':
                    parmDict[pfx+'AUiso:'+str(AtLookup[atId])] = UIJ[i][1]
                    
def ApplyRBModelDervs(dFdvDict,parmDict,rigidbodyDict,Phase):
    'Needs a doc string'
    atxIds = ['dAx:','dAy:','dAz:']
    atuIds = ['AU11:','AU22:','AU33:','AU12:','AU13:','AU23:']
    TIds = ['T11:','T22:','T33:','T12:','T13:','T23:']
    LIds = ['L11:','L22:','L33:','L12:','L13:','L23:']
    SIds = ['S12:','S13:','S21:','S23:','S31:','S32:','SAA:','SBB:']
    PIds = ['Px:','Py:','Pz:']
    OIds = ['Oa:','Oi:','Oj:','Ok:']
    RBIds = rigidbodyDict.get('RBIds',{'Vector':[],'Residue':[]})  #these are lists of rbIds
    if not RBIds['Vector'] and not RBIds['Residue']:
        return
    VRBIds = RBIds['Vector']
    RRBIds = RBIds['Residue']
    RBData = rigidbodyDict
    for item in parmDict:
        if 'RB' in item:
            dFdvDict[item] = 0.        #NB: this is a vector which is no. refl. long & must be filled!
    General = Phase['General']
    cell = General['Cell'][1:7]
    Amat,Bmat = G2lat.cell2AB(cell)
    rpd = np.pi/180.
    rpd2 = rpd**2
    g = nl.inv(np.inner(Bmat,Bmat))
    gvec = np.sqrt(np.array([g[0][0]**2,g[1][1]**2,g[2][2]**2,
        g[0][0]*g[1][1],g[0][0]*g[2][2],g[1][1]*g[2][2]]))
    AtLookup = G2mth.FillAtomLookUp(Phase['Atoms'])
    pfx = str(Phase['pId'])+'::'
    RBModels =  Phase['RBModels']
    for irb,RBObj in enumerate(RBModels.get('Vector',[])):
        VModel = RBData['Vector'][RBObj['RBId']]
        Q = RBObj['Orient'][0]
        Pos = RBObj['Orig'][0]
        jrb = VRBIds.index(RBObj['RBId'])
        rbsx = str(irb)+':'+str(jrb)
        dXdv = []
        for iv in range(len(VModel['VectMag'])):
            dCdv = []
            for vec in VModel['rbVect'][iv]:
                dCdv.append(G2mth.prodQVQ(Q,vec))
            dXdv.append(np.inner(Bmat,np.array(dCdv)).T)
        XYZ,Cart = G2mth.UpdateRBXYZ(Bmat,RBObj,RBData,'Vector')
        for ia,atId in enumerate(RBObj['Ids']):
            atNum = AtLookup[atId]
            dx = 0.00001
            for iv in range(len(VModel['VectMag'])):
                for ix in [0,1,2]:
                    dFdvDict['::RBV;'+str(iv)+':'+str(jrb)] += dXdv[iv][ia][ix]*dFdvDict[pfx+atxIds[ix]+str(atNum)]
            for i,name in enumerate(['RBVPx:','RBVPy:','RBVPz:']):
                dFdvDict[pfx+name+rbsx] += dFdvDict[pfx+atxIds[i]+str(atNum)]
            for iv in range(4):
                Q[iv] -= dx
                XYZ1 = G2mth.RotateRBXYZ(Bmat,Cart,G2mth.normQ(Q))
                Q[iv] += 2.*dx
                XYZ2 = G2mth.RotateRBXYZ(Bmat,Cart,G2mth.normQ(Q))
                Q[iv] -= dx
                dXdO = (XYZ2[ia]-XYZ1[ia])/(2.*dx)
                for ix in [0,1,2]:
                    dFdvDict[pfx+'RBV'+OIds[iv]+rbsx] += dXdO[ix]*dFdvDict[pfx+atxIds[ix]+str(atNum)]
            X = G2mth.prodQVQ(Q,Cart[ia])
            dFdu = np.array([dFdvDict[pfx+Uid+str(AtLookup[atId])] for Uid in atuIds]).T/gvec
            dFdu = G2lat.U6toUij(dFdu.T)
            dFdu = np.tensordot(Amat,np.tensordot(Amat,dFdu,([1,0])),([0,1]))            
            dFdu = G2lat.UijtoU6(dFdu)
            atNum = AtLookup[atId]
            if 'T' in RBObj['ThermalMotion'][0]:
                for i,name in enumerate(['RBVT11:','RBVT22:','RBVT33:','RBVT12:','RBVT13:','RBVT23:']):
                    dFdvDict[pfx+name+rbsx] += dFdu[i]
            if 'L' in RBObj['ThermalMotion'][0]:
                dFdvDict[pfx+'RBVL11:'+rbsx] += rpd2*(dFdu[1]*X[2]**2+dFdu[2]*X[1]**2-dFdu[5]*X[1]*X[2])
                dFdvDict[pfx+'RBVL22:'+rbsx] += rpd2*(dFdu[0]*X[2]**2+dFdu[2]*X[0]**2-dFdu[4]*X[0]*X[2])
                dFdvDict[pfx+'RBVL33:'+rbsx] += rpd2*(dFdu[0]*X[1]**2+dFdu[1]*X[0]**2-dFdu[3]*X[0]*X[1])
                dFdvDict[pfx+'RBVL12:'+rbsx] += rpd2*(-dFdu[3]*X[2]**2-2.*dFdu[2]*X[0]*X[1]+
                    dFdu[4]*X[1]*X[2]+dFdu[5]*X[0]*X[2])
                dFdvDict[pfx+'RBVL13:'+rbsx] += rpd2*(-dFdu[4]*X[1]**2-2.*dFdu[1]*X[0]*X[2]+
                    dFdu[3]*X[1]*X[2]+dFdu[5]*X[0]*X[1])
                dFdvDict[pfx+'RBVL23:'+rbsx] += rpd2*(-dFdu[5]*X[0]**2-2.*dFdu[0]*X[1]*X[2]+
                    dFdu[3]*X[0]*X[2]+dFdu[4]*X[0]*X[1])
            if 'S' in RBObj['ThermalMotion'][0]:
                dFdvDict[pfx+'RBVS12:'+rbsx] += rpd*(dFdu[5]*X[1]-2.*dFdu[1]*X[2])
                dFdvDict[pfx+'RBVS13:'+rbsx] += rpd*(-dFdu[5]*X[2]+2.*dFdu[2]*X[1])
                dFdvDict[pfx+'RBVS21:'+rbsx] += rpd*(-dFdu[4]*X[0]+2.*dFdu[0]*X[2])
                dFdvDict[pfx+'RBVS23:'+rbsx] += rpd*(dFdu[4]*X[2]-2.*dFdu[2]*X[0])
                dFdvDict[pfx+'RBVS31:'+rbsx] += rpd*(dFdu[3]*X[0]-2.*dFdu[0]*X[1])
                dFdvDict[pfx+'RBVS32:'+rbsx] += rpd*(-dFdu[3]*X[1]+2.*dFdu[1]*X[0])
                dFdvDict[pfx+'RBVSAA:'+rbsx] += rpd*(dFdu[4]*X[1]-dFdu[3]*X[2])
                dFdvDict[pfx+'RBVSBB:'+rbsx] += rpd*(dFdu[5]*X[0]-dFdu[3]*X[2])
            if 'U' in RBObj['ThermalMotion'][0]:
                dFdvDict[pfx+'RBVU:'+rbsx] += dFdvDict[pfx+'AUiso:'+str(AtLookup[atId])]


    for irb,RBObj in enumerate(RBModels.get('Residue',[])):
        Q = RBObj['Orient'][0]
        Pos = RBObj['Orig'][0]
        jrb = RRBIds.index(RBObj['RBId'])
        torData = RBData['Residue'][RBObj['RBId']]['rbSeq']
        rbsx = str(irb)+':'+str(jrb)
        XYZ,Cart = G2mth.UpdateRBXYZ(Bmat,RBObj,RBData,'Residue')
        for itors,tors in enumerate(RBObj['Torsions']):     #derivative error?
            tname = pfx+'RBRTr;'+str(itors)+':'+rbsx           
            orId,pvId = torData[itors][:2]
            pivotVec = Cart[orId]-Cart[pvId]
            QA = G2mth.AVdeg2Q(-0.001,pivotVec)
            QB = G2mth.AVdeg2Q(0.001,pivotVec)
            for ir in torData[itors][3]:
                atNum = AtLookup[RBObj['Ids'][ir]]
                rVec = Cart[ir]-Cart[pvId]
                dR = G2mth.prodQVQ(QB,rVec)-G2mth.prodQVQ(QA,rVec)
                dRdT = np.inner(Bmat,G2mth.prodQVQ(Q,dR))/.002
                for ix in [0,1,2]:
                    dFdvDict[tname] += dRdT[ix]*dFdvDict[pfx+atxIds[ix]+str(atNum)]
        for ia,atId in enumerate(RBObj['Ids']):
            atNum = AtLookup[atId]
            dx = 0.00001
            for i,name in enumerate(['RBRPx:','RBRPy:','RBRPz:']):
                dFdvDict[pfx+name+rbsx] += dFdvDict[pfx+atxIds[i]+str(atNum)]
            for iv in range(4):
                Q[iv] -= dx
                XYZ1 = G2mth.RotateRBXYZ(Bmat,Cart,G2mth.normQ(Q))
                Q[iv] += 2.*dx
                XYZ2 = G2mth.RotateRBXYZ(Bmat,Cart,G2mth.normQ(Q))
                Q[iv] -= dx
                dXdO = (XYZ2[ia]-XYZ1[ia])/(2.*dx)
                for ix in [0,1,2]:
                    dFdvDict[pfx+'RBR'+OIds[iv]+rbsx] += dXdO[ix]*dFdvDict[pfx+atxIds[ix]+str(atNum)]
            X = G2mth.prodQVQ(Q,Cart[ia])
            dFdu = np.array([dFdvDict[pfx+Uid+str(AtLookup[atId])] for Uid in atuIds]).T/gvec
            dFdu = G2lat.U6toUij(dFdu.T)
            dFdu = np.tensordot(Amat.T,np.tensordot(Amat,dFdu,([1,0])),([0,1]))
            dFdu = G2lat.UijtoU6(dFdu)
            atNum = AtLookup[atId]
            if 'T' in RBObj['ThermalMotion'][0]:
                for i,name in enumerate(['RBRT11:','RBRT22:','RBRT33:','RBRT12:','RBRT13:','RBRT23:']):
                    dFdvDict[pfx+name+rbsx] += dFdu[i]
            if 'L' in RBObj['ThermalMotion'][0]:
                dFdvDict[pfx+'RBRL11:'+rbsx] += rpd2*(dFdu[1]*X[2]**2+dFdu[2]*X[1]**2-dFdu[5]*X[1]*X[2])
                dFdvDict[pfx+'RBRL22:'+rbsx] += rpd2*(dFdu[0]*X[2]**2+dFdu[2]*X[0]**2-dFdu[4]*X[0]*X[2])
                dFdvDict[pfx+'RBRL33:'+rbsx] += rpd2*(dFdu[0]*X[1]**2+dFdu[1]*X[0]**2-dFdu[3]*X[0]*X[1])
                dFdvDict[pfx+'RBRL12:'+rbsx] += rpd2*(-dFdu[3]*X[2]**2-2.*dFdu[2]*X[0]*X[1]+
                    dFdu[4]*X[1]*X[2]+dFdu[5]*X[0]*X[2])
                dFdvDict[pfx+'RBRL13:'+rbsx] += rpd2*(dFdu[4]*X[1]**2-2.*dFdu[1]*X[0]*X[2]+
                    dFdu[3]*X[1]*X[2]+dFdu[5]*X[0]*X[1])
                dFdvDict[pfx+'RBRL23:'+rbsx] += rpd2*(dFdu[5]*X[0]**2-2.*dFdu[0]*X[1]*X[2]+
                    dFdu[3]*X[0]*X[2]+dFdu[4]*X[0]*X[1])
            if 'S' in RBObj['ThermalMotion'][0]:
                dFdvDict[pfx+'RBRS12:'+rbsx] += rpd*(dFdu[5]*X[1]-2.*dFdu[1]*X[2])
                dFdvDict[pfx+'RBRS13:'+rbsx] += rpd*(-dFdu[5]*X[2]+2.*dFdu[2]*X[1])
                dFdvDict[pfx+'RBRS21:'+rbsx] += rpd*(-dFdu[4]*X[0]+2.*dFdu[0]*X[2])
                dFdvDict[pfx+'RBRS23:'+rbsx] += rpd*(dFdu[4]*X[2]-2.*dFdu[2]*X[0])
                dFdvDict[pfx+'RBRS31:'+rbsx] += rpd*(dFdu[3]*X[0]-2.*dFdu[0]*X[1])
                dFdvDict[pfx+'RBRS32:'+rbsx] += rpd*(-dFdu[3]*X[1]+2.*dFdu[1]*X[0])
                dFdvDict[pfx+'RBRSAA:'+rbsx] += rpd*(dFdu[4]*X[1]-dFdu[3]*X[2])
                dFdvDict[pfx+'RBRSBB:'+rbsx] += rpd*(dFdu[5]*X[0]-dFdu[3]*X[2])
            if 'U' in RBObj['ThermalMotion'][0]:
                dFdvDict[pfx+'RBRU:'+rbsx] += dFdvDict[pfx+'AUiso:'+str(AtLookup[atId])]
    
################################################################################
##### Penalty & restraint functions 
################################################################################

def penaltyFxn(HistoPhases,parmDict,varyList):
    'Needs a doc string'
    Histograms,Phases,restraintDict,rigidbodyDict = HistoPhases
    pNames = []
    pVals = []
    pWt = []
    negWt = {}
    for phase in Phases:
        pId = Phases[phase]['pId']
        negWt[pId] = Phases[phase]['General']['Pawley neg wt']
        General = Phases[phase]['General']
        textureData = General['SH Texture']
        SGData = General['SGData']
        AtLookup = G2mth.FillAtomLookUp(Phases[phase]['Atoms'])
        cell = General['Cell'][1:7]
        Amat,Bmat = G2lat.cell2AB(cell)
        if phase not in restraintDict:
            continue
        phaseRest = restraintDict[phase]
        names = [['Bond','Bonds'],['Angle','Angles'],['Plane','Planes'],
            ['Chiral','Volumes'],['Torsion','Torsions'],['Rama','Ramas'],
            ['ChemComp','Sites'],['Texture','HKLs']]
        for name,rest in names:
            itemRest = phaseRest[name]
            if itemRest[rest] and itemRest['Use']:
                wt = itemRest['wtFactor']
                if name in ['Bond','Angle','Plane','Chiral']:
                    for i,[indx,ops,obs,esd] in enumerate(itemRest[rest]):
                        pNames.append(str(pId)+':'+name+':'+str(i))
                        XYZ = np.array(G2mth.GetAtomCoordsByID(pId,parmDict,AtLookup,indx))
                        XYZ = G2mth.getSyXYZ(XYZ,ops,SGData)
                        if name == 'Bond':
                            calc = G2mth.getRestDist(XYZ,Amat)
                        elif name == 'Angle':
                            calc = G2mth.getRestAngle(XYZ,Amat)
                        elif name == 'Plane':
                            calc = G2mth.getRestPlane(XYZ,Amat)
                        elif name == 'Chiral':
                            calc = G2mth.getRestChiral(XYZ,Amat)
                        pVals.append(obs-calc)
                        pWt.append(wt/esd**2)
                elif name in ['Torsion','Rama']:
                    coeffDict = itemRest['Coeff']
                    for i,[indx,ops,cofName,esd] in enumerate(itemRest[rest]):
                        pNames.append(str(pId)+':'+name+':'+str(i))
                        XYZ = np.array(G2mth.GetAtomCoordsByID(pId,parmDict,AtLookup,indx))
                        XYZ = G2mth.getSyXYZ(XYZ,ops,SGData)
                        if name == 'Torsion':
                            tor = G2mth.getRestTorsion(XYZ,Amat)
                            restr,calc = G2mth.calcTorsionEnergy(tor,coeffDict[cofName])
                        else:
                            phi,psi = G2mth.getRestRama(XYZ,Amat)
                            restr,calc = G2mth.calcRamaEnergy(phi,psi,coeffDict[cofName])                               
                        pVals.append(obs-calc)
                        pWt.append(wt/esd**2)
                elif name == 'ChemComp':
                    for i,[indx,factors,obs,esd] in enumerate(itemRest[rest]):
                        pNames.append(str(pId)+':'+name+':'+str(i))
                        mul = np.array(G2mth.GetAtomItemsById(Atoms,AtLookUp,indx,cs+1))
                        frac = np.array(G2mth.GetAtomItemsById(Atoms,AtLookUp,indx,cs-1))
                        calc = np.sum(mul*frac*factors)
                        pVals.append(obs-calc)
                        pWt.append(wt/esd**2)                    
                elif name == 'Texture':
                    SHkeys = textureData['SH Coeff'][1].keys()
                    SHCoef = G2mth.GetSHCoeff(pId,parmDict,SHkeys)
                    shModels = ['cylindrical','none','shear - 2/m','rolling - mmm']
                    SamSym = dict(zip(shModels,['0','-1','2/m','mmm']))
                    for i,[hkl,grid,esd1,ifesd2,esd2] in enumerate(itemRest[rest]):
                        PH = np.array(hkl)
                        phi,beta = G2lat.CrsAng(np.array(hkl),cell,SGData)
                        ODFln = G2lat.Flnh(False,SHCoef,phi,beta,SGData)
                        R,P,Z = G2mth.getRestPolefig(ODFln,SamSym[textureData['Model']],grid)
                        Z1 = -ma.masked_greater(Z,0.0)
                        IndZ1 = np.array(ma.nonzero(Z1))
                        for ind in IndZ1.T:
                            pNames.append('%d:%s:%d:%.2f:%.2f'%(pId,name,i,R[ind[0],ind[1]],P[ind[0],ind[1]]))
                            pVals.append(Z1[ind[0]][ind[1]])
                            pWt.append(wt/esd1**2)
                        if ifesd2:
                            Z2 = 1.-Z
                            for ind in np.ndindex(grid,grid):
                                pNames.append('%d:%s:%d:%.2f:%.2f'%(pId,name+'-unit',i,R[ind[0],ind[1]],P[ind[0],ind[1]]))
                                pVals.append(Z1[ind[0]][ind[1]])
                                pWt.append(wt/esd2**2)
         
    for item in varyList:
        if 'PWLref' in item and parmDict[item] < 0.:
            pId = int(item.split(':')[0])
            if negWt[pId]:
                pNames.append(item)
                pVals.append(-parmDict[item])
                pWt.append(negWt[pId])
    pVals = np.array(pVals)
    pWt = np.array(pWt)         #should this be np.sqrt?
    return pNames,pVals,pWt
    
def penaltyDeriv(pNames,pVal,HistoPhases,parmDict,varyList):
    'Needs a doc string'
    Histograms,Phases,restraintDict,rigidbodyDict = HistoPhases
    pDerv = np.zeros((len(varyList),len(pVal)))
    for phase in Phases:
#        if phase not in restraintDict:
#            continue
        pId = Phases[phase]['pId']
        General = Phases[phase]['General']
        SGData = General['SGData']
        AtLookup = G2mth.FillAtomLookUp(Phases[phase]['Atoms'])
        cell = General['Cell'][1:7]
        Amat,Bmat = G2lat.cell2AB(cell)
        textureData = General['SH Texture']

        SHkeys = textureData['SH Coeff'][1].keys()
        SHCoef = G2mth.GetSHCoeff(pId,parmDict,SHkeys)
        shModels = ['cylindrical','none','shear - 2/m','rolling - mmm']
        SamSym = dict(zip(shModels,['0','-1','2/m','mmm']))
        sam = SamSym[textureData['Model']]
        phaseRest = restraintDict.get(phase,{})
        names = {'Bond':'Bonds','Angle':'Angles','Plane':'Planes',
            'Chiral':'Volumes','Torsion':'Torsions','Rama':'Ramas',
            'ChemComp':'Sites','Texture':'HKLs'}
        lasthkl = np.array([0,0,0])
        for ip,pName in enumerate(pNames):
            pnames = pName.split(':')
            if pId == int(pnames[0]):
                name = pnames[1]
                if 'PWL' in pName:
                    pDerv[varyList.index(pName)][ip] += 1.
                    continue
                id = int(pnames[2]) 
                itemRest = phaseRest[name]
                if name in ['Bond','Angle','Plane','Chiral']:
                    indx,ops,obs,esd = itemRest[names[name]][id]
                    dNames = []
                    for ind in indx:
                        dNames += [str(pId)+'::dA'+Xname+':'+str(AtLookup[ind]) for Xname in ['x','y','z']]
                    XYZ = np.array(G2mth.GetAtomCoordsByID(pId,parmDict,AtLookup,indx))
                    if name == 'Bond':
                        deriv = G2mth.getRestDeriv(G2mth.getRestDist,XYZ,Amat,ops,SGData)
                    elif name == 'Angle':
                        deriv = G2mth.getRestDeriv(G2mth.getRestAngle,XYZ,Amat,ops,SGData)
                    elif name == 'Plane':
                        deriv = G2mth.getRestDeriv(G2mth.getRestPlane,XYZ,Amat,ops,SGData)
                    elif name == 'Chiral':
                        deriv = G2mth.getRestDeriv(G2mth.getRestChiral,XYZ,Amat,ops,SGData)
                elif name in ['Torsion','Rama']:
                    coffDict = itemRest['Coeff']
                    indx,ops,cofName,esd = itemRest[names[name]][id]
                    dNames = []
                    for ind in indx:
                        dNames += [str(pId)+'::dA'+Xname+':'+str(AtLookup[ind]) for Xname in ['x','y','z']]
                    XYZ = np.array(G2mth.GetAtomCoordsByID(pId,parmDict,AtLookup,indx))
                    if name == 'Torsion':
                        deriv = G2mth.getTorsionDeriv(XYZ,Amat,coffDict[cofName])
                    else:
                        deriv = G2mth.getRamaDeriv(XYZ,Amat,coffDict[cofName])
                elif name == 'ChemComp':
                    indx,factors,obs,esd = itemRest[names[name]][id]
                    dNames = []
                    for ind in indx:
                        dNames += [str(pId)+'::Afrac:'+str(AtLookup[ind])]
                        mul = np.array(G2mth.GetAtomItemsById(Atoms,AtLookUp,indx,cs+1))
                        deriv = mul*factors
                elif 'Texture' in name:
                    deriv = []
                    dNames = []
                    hkl,grid,esd1,ifesd2,esd2 = itemRest[names[name]][id]
                    hkl = np.array(hkl)
                    if np.any(lasthkl-hkl):
                        PH = np.array(hkl)
                        phi,beta = G2lat.CrsAng(np.array(hkl),cell,SGData)
                        ODFln = G2lat.Flnh(False,SHCoef,phi,beta,SGData)
                        lasthkl = copy.copy(hkl)                        
                    if 'unit' in name:
                        pass
                    else:
                        gam = float(pnames[3])
                        psi = float(pnames[4])
                        for SHname in ODFln:
                            l,m,n = eval(SHname[1:])
                            Ksl = G2lat.GetKsl(l,m,sam,psi,gam)[0]
                            dNames += [str(pId)+'::'+SHname]
                            deriv.append(-ODFln[SHname][0]*Ksl/SHCoef[SHname])
                for dName,drv in zip(dNames,deriv):
                    try:
                        ind = varyList.index(dName)
                        pDerv[ind][ip] += drv
                    except ValueError:
                        pass
    return pDerv

################################################################################
##### Function & derivative calculations
################################################################################        
                    
def GetAtomFXU(pfx,calcControls,parmDict):
    'Needs a doc string'
    Natoms = calcControls['Natoms'][pfx]
    Tdata = Natoms*[' ',]
    Mdata = np.zeros(Natoms)
    IAdata = Natoms*[' ',]
    Fdata = np.zeros(Natoms)
    FFdata = []
    BLdata = []
    Xdata = np.zeros((3,Natoms))
    dXdata = np.zeros((3,Natoms))
    Uisodata = np.zeros(Natoms)
    Uijdata = np.zeros((6,Natoms))
    keys = {'Atype:':Tdata,'Amul:':Mdata,'Afrac:':Fdata,'AI/A:':IAdata,
        'dAx:':dXdata[0],'dAy:':dXdata[1],'dAz:':dXdata[2],
        'Ax:':Xdata[0],'Ay:':Xdata[1],'Az:':Xdata[2],'AUiso:':Uisodata,
        'AU11:':Uijdata[0],'AU22:':Uijdata[1],'AU33:':Uijdata[2],
        'AU12:':Uijdata[3],'AU13:':Uijdata[4],'AU23:':Uijdata[5]}
    for iatm in range(Natoms):
        for key in keys:
            parm = pfx+key+str(iatm)
            if parm in parmDict:
                keys[key][iatm] = parmDict[parm]
    return Tdata,Mdata,Fdata,Xdata,dXdata,IAdata,Uisodata,Uijdata
    
def StructureFactor(refList,G,hfx,pfx,SGData,calcControls,parmDict):
    ''' Compute structure factors for all h,k,l for phase
    puts the result, F^2, in each ref[8] in refList
    input:
    
    :param list refList: [ref] where each ref = h,k,l,m,d,...,[equiv h,k,l],phase[equiv] 
    :param np.array G:      reciprocal metric tensor
    :param str pfx:    phase id string
    :param dict SGData: space group info. dictionary output from SpcGroup
    :param dict calcControls:
    :param dict ParmDict:

    '''        
    twopi = 2.0*np.pi
    twopisq = 2.0*np.pi**2
    phfx = pfx.split(':')[0]+hfx
    ast = np.sqrt(np.diag(G))
    Mast = twopisq*np.multiply.outer(ast,ast)
    FFtables = calcControls['FFtables']
    BLtables = calcControls['BLtables']
    Tdata,Mdata,Fdata,Xdata,dXdata,IAdata,Uisodata,Uijdata = GetAtomFXU(pfx,calcControls,parmDict)
    FF = np.zeros(len(Tdata))
    if 'N' in parmDict[hfx+'Type']:
        FP,FPP = G2el.BlenRes(Tdata,BLtables,parmDict[hfx+'Lam'])
    else:
        FP = np.array([FFtables[El][hfx+'FP'] for El in Tdata])
        FPP = np.array([FFtables[El][hfx+'FPP'] for El in Tdata])
    Uij = np.array(G2lat.U6toUij(Uijdata))
    bij = Mast*Uij.T
    for refl in refList:
        fbs = np.array([0,0])
        H = refl[:3]
        SQ = 1./(2.*refl[4])**2
        SQfactor = 4.0*SQ*twopisq
        Bab = parmDict[phfx+'BabA']*np.exp(-parmDict[phfx+'BabU']*SQfactor)
        if not len(refl[-1]):                #no form factors
            if 'N' in parmDict[hfx+'Type']:
                refl[-1] = G2el.getBLvalues(BLtables)
            else:       #'X'
                refl[-1] = G2el.getFFvalues(FFtables,SQ)
        for i,El in enumerate(Tdata):
            FF[i] = refl[-1][El]           
        Uniq = refl[11]
        phi = refl[12]
        phase = twopi*(np.inner(Uniq,(dXdata.T+Xdata.T))+phi[:,np.newaxis])
        sinp = np.sin(phase)
        cosp = np.cos(phase)
        occ = Mdata*Fdata/len(Uniq)
        biso = -SQfactor*Uisodata
        Tiso = np.where(biso<1.,np.exp(biso),1.0)
        HbH = np.array([-np.inner(h,np.inner(bij,h)) for h in Uniq])
        Tuij = np.where(HbH<1.,np.exp(HbH),1.0)
        Tcorr = Tiso*Tuij
        fa = np.array([(FF+FP-Bab)*occ*cosp*Tcorr,-FPP*occ*sinp*Tcorr])
        fas = np.sum(np.sum(fa,axis=1),axis=1)        #real
        if not SGData['SGInv']:
            fb = np.array([(FF+FP-Bab)*occ*sinp*Tcorr,FPP*occ*cosp*Tcorr])
            fbs = np.sum(np.sum(fb,axis=1),axis=1)
        fasq = fas**2
        fbsq = fbs**2        #imaginary
        refl[9] = np.sum(fasq)+np.sum(fbsq)
        refl[10] = atan2d(fbs[0],fas[0])
    
def StructureFactorDerv(refList,G,hfx,pfx,SGData,calcControls,parmDict):
    'Needs a doc string'
    twopi = 2.0*np.pi
    twopisq = 2.0*np.pi**2
    phfx = pfx.split(':')[0]+hfx
    ast = np.sqrt(np.diag(G))
    Mast = twopisq*np.multiply.outer(ast,ast)
    FFtables = calcControls['FFtables']
    BLtables = calcControls['BLtables']
    Tdata,Mdata,Fdata,Xdata,dXdata,IAdata,Uisodata,Uijdata = GetAtomFXU(pfx,calcControls,parmDict)
    FF = np.zeros(len(Tdata))
    if 'N' in parmDict[hfx+'Type']:
        FP = 0.
        FPP = 0.
    else:
        FP = np.array([FFtables[El][hfx+'FP'] for El in Tdata])
        FPP = np.array([FFtables[El][hfx+'FPP'] for El in Tdata])
    Uij = np.array(G2lat.U6toUij(Uijdata))
    bij = Mast*Uij.T
    dFdvDict = {}
    dFdfr = np.zeros((len(refList),len(Mdata)))
    dFdx = np.zeros((len(refList),len(Mdata),3))
    dFdui = np.zeros((len(refList),len(Mdata)))
    dFdua = np.zeros((len(refList),len(Mdata),6))
    dFdbab = np.zeros((len(refList),2))
    for iref,refl in enumerate(refList):
        H = np.array(refl[:3])
        SQ = 1./(2.*refl[4])**2             # or (sin(theta)/lambda)**2
        SQfactor = 8.0*SQ*np.pi**2
        dBabdA = np.exp(-parmDict[phfx+'BabU']*SQfactor)
        Bab = parmDict[phfx+'BabA']*dBabdA
        for i,El in enumerate(Tdata):            
            FF[i] = refl[-1][El]           
        Uniq = refl[11]
        phi = refl[12]
        phase = twopi*(np.inner((dXdata.T+Xdata.T),Uniq)+phi[np.newaxis,:])
        sinp = np.sin(phase)
        cosp = np.cos(phase)
        occ = Mdata*Fdata/len(Uniq)
        biso = -SQfactor*Uisodata
        Tiso = np.where(biso<1.,np.exp(biso),1.0)
        HbH = -np.inner(H,np.inner(bij,H))
        Hij = np.array([Mast*np.multiply.outer(U,U) for U in Uniq])
        Hij = np.array([G2lat.UijtoU6(Uij) for Uij in Hij])
        Tuij = np.where(HbH<1.,np.exp(HbH),1.0)
        Tcorr = Tiso*Tuij
        fot = (FF+FP-Bab)*occ*Tcorr
        fotp = FPP*occ*Tcorr
        fa = np.array([fot[:,np.newaxis]*cosp,fotp[:,np.newaxis]*cosp])       #non positions
        fb = np.array([fot[:,np.newaxis]*sinp,-fotp[:,np.newaxis]*sinp])
        
        fas = np.sum(np.sum(fa,axis=1),axis=1)
        fbs = np.sum(np.sum(fb,axis=1),axis=1)
        fax = np.array([-fot[:,np.newaxis]*sinp,-fotp[:,np.newaxis]*sinp])   #positions
        fbx = np.array([fot[:,np.newaxis]*cosp,-fot[:,np.newaxis]*cosp])
        #sum below is over Uniq
        dfadfr = np.sum(fa/occ[:,np.newaxis],axis=2)
        dfadx = np.sum(twopi*Uniq*fax[:,:,:,np.newaxis],axis=2)
        dfadui = np.sum(-SQfactor*fa,axis=2)
        dfadua = np.sum(-Hij*fa[:,:,:,np.newaxis],axis=2)
        dfadba = np.sum(-cosp*(occ*Tcorr)[:,np.newaxis],axis=1)
        #NB: the above have been checked against PA(1:10,1:2) in strfctr.for      
        dFdfr[iref] = 2.*(fas[0]*dfadfr[0]+fas[1]*dfadfr[1])*Mdata/len(Uniq)
        dFdx[iref] = 2.*(fas[0]*dfadx[0]+fas[1]*dfadx[1])
        dFdui[iref] = 2.*(fas[0]*dfadui[0]+fas[1]*dfadui[1])
        dFdua[iref] = 2.*(fas[0]*dfadua[0]+fas[1]*dfadua[1])
        dFdbab[iref] = np.array([np.sum(dfadba*dBabdA),np.sum(-dfadba*parmDict[phfx+'BabA']*SQfactor*dBabdA)]).T
        if not SGData['SGInv']:
            dfbdfr = np.sum(fb/occ[:,np.newaxis],axis=2)        #problem here if occ=0 for some atom
            dfbdx = np.sum(twopi*Uniq*fbx[:,:,:,np.newaxis],axis=2)          
            dfbdui = np.sum(-SQfactor*fb,axis=2)
            dfbdua = np.sum(-Hij*fb[:,:,:,np.newaxis],axis=2)
            dfbdba = np.sum(-sinp*(occ*Tcorr)[:,np.newaxis],axis=1)
            dFdfr[iref] += 2.*(fbs[0]*dfbdfr[0]-fbs[1]*dfbdfr[1])*Mdata/len(Uniq)
            dFdx[iref] += 2.*(fbs[0]*dfbdx[0]+fbs[1]*dfbdx[1])
            dFdui[iref] += 2.*(fbs[0]*dfbdui[0]-fbs[1]*dfbdui[1])
            dFdua[iref] += 2.*(fbs[0]*dfbdua[0]+fbs[1]*dfbdua[1])
            dFdbab[iref] += np.array([np.sum(dfbdba*dBabdA),np.sum(-dfbdba*parmDict[phfx+'BabA']*SQfactor*dBabdA)]).T
        #loop over atoms - each dict entry is list of derivatives for all the reflections
    for i in range(len(Mdata)):     
        dFdvDict[pfx+'Afrac:'+str(i)] = dFdfr.T[i]
        dFdvDict[pfx+'dAx:'+str(i)] = dFdx.T[0][i]
        dFdvDict[pfx+'dAy:'+str(i)] = dFdx.T[1][i]
        dFdvDict[pfx+'dAz:'+str(i)] = dFdx.T[2][i]
        dFdvDict[pfx+'AUiso:'+str(i)] = dFdui.T[i]
        dFdvDict[pfx+'AU11:'+str(i)] = dFdua.T[0][i]
        dFdvDict[pfx+'AU22:'+str(i)] = dFdua.T[1][i]
        dFdvDict[pfx+'AU33:'+str(i)] = dFdua.T[2][i]
        dFdvDict[pfx+'AU12:'+str(i)] = 2.*dFdua.T[3][i]
        dFdvDict[pfx+'AU13:'+str(i)] = 2.*dFdua.T[4][i]
        dFdvDict[pfx+'AU23:'+str(i)] = 2.*dFdua.T[5][i]
        dFdvDict[pfx+'BabA'] = dFdbab.T[0]
        dFdvDict[pfx+'BabU'] = dFdbab.T[1]
    return dFdvDict
    
def SCExtinction(ref,phfx,hfx,pfx,calcControls,parmDict,varyList):
    ''' Single crystal extinction function; puts correction in ref[13] and returns
    corrections needed for derivatives
    '''
    ref[13] = 1.0
    dervCor = 1.0
    dervDict = {}
    if calcControls[phfx+'EType'] != 'None':
        cos2T = 1.0-0.5*(parmDict[hfx+'Lam']/ref[4])**2         #cos(2theta)
        if 'SXC' in parmDict[hfx+'Type']:
            AV = 7.9406e5/parmDict[pfx+'Vol']**2
            PL = np.sqrt(1.0-cos2T**2)/parmDict[hfx+'Lam']
            P12 = (calcControls[phfx+'Cos2TM']+cos2T**4)/(calcControls[phfx+'Cos2TM']+cos2T**2)
        elif 'SNT' in parmDict[hfx+'Type']:
            AV = 1.e7/parmDict[pfx+'Vol']**2
            PL = 1./(4.*refl[4]**2)
            P12 = 1.0
        elif 'SNC' in parmDict[hfx+'Type']:
            AV = 1.e7/parmDict[pfx+'Vol']**2
            PL = np.sqrt(1.0-cos2T**2)/parmDict[hfx+'Lam']
            P12 = 1.0
            
        PLZ = AV*P12*parmDict[hfx+'Lam']**2*ref[7]
        if 'Primary' in calcControls[phfx+'EType']:
            PLZ *= 1.5
        else:
            PLZ *= calcControls[phfx+'Tbar']
                        
        if 'Primary' in calcControls[phfx+'EType']:
            PSIG = parmDict[phfx+'Ep']
        elif 'I & II' in calcControls[phfx+'EType']:
            PSIG = parmDict[phfx+'Eg']/np.sqrt(1.+(parmDict[phfx+'Es']*PL/parmDict[phfx+'Eg'])**2)
        elif 'Type II' in calcControls[phfx+'EType']:
            PSIG = parmDict[phfx+'Es']
        else:       # 'Secondary Type I'
            PSIG = parmDict[phfx+'Eg']/PL
            
        AG = 0.58+0.48*cos2T+0.24*cos2T**2
        AL = 0.025+0.285*cos2T
        BG = 0.02-0.025*cos2T
        BL = 0.15-0.2*(0.75-cos2T)**2
        if cos2T < 0.:
            BL = -0.45*cos2T
        CG = 2.
        CL = 2.
        PF = PLZ*PSIG
        
        if 'Gaussian' in calcControls[phfx+'EApprox']:
            PF4 = 1.+CG*PF+AG*PF**2/(1.+BG*PF)
            extCor = np.sqrt(PF4)
            PF3 = 0.5*(CG+2.*AG*PF/(1.+BG*PF)-AG*PF**2*BG/(1.+BG*PF)**2)/(PF4*extCor)
        else:
            PF4 = 1.+CL*PF+AL*PF**2/(1.+BL*PF)
            extCor = np.sqrt(PF4)
            PF3 = 0.5*(CL+2.*AL*PF/(1.+BL*PF)-AL*PF**2*BL/(1.+BL*PF)**2)/(PF4*extCor)

        dervCor = (1.+PF)*PF3
        if 'Primary' in calcControls[phfx+'EType'] and phfx+'Ep' in varyList:
            dervDict[phfx+'Ep'] = -ref[7]*PLZ*PF3
        if 'II' in calcControls[phfx+'EType'] and phfx+'Es' in varyList:
            dervDict[phfx+'Es'] = -ref[7]*PLZ*PF3*(PSIG/parmDict[phfx+'Es'])**3
        if 'I' in calcControls[phfx+'EType'] and phfx+'Eg' in varyList:
            dervDict[phfx+'Eg'] = -ref[7]*PLZ*PF3*(PSIG/parmDict[phfx+'Eg'])**3*PL**2
               
        ref[13] = 1./extCor
    return dervCor,dervDict
        
    
def Dict2Values(parmdict, varylist):
    '''Use before call to leastsq to setup list of values for the parameters 
    in parmdict, as selected by key in varylist'''
    return [parmdict[key] for key in varylist] 
    
def Values2Dict(parmdict, varylist, values):
    ''' Use after call to leastsq to update the parameter dictionary with 
    values corresponding to keys in varylist'''
    parmdict.update(zip(varylist,values))
    
def GetNewCellParms(parmDict,varyList):
    'Needs a doc string'
    newCellDict = {}
    Anames = ['A'+str(i) for i in range(6)]
    Ddict = dict(zip(['D11','D22','D33','D12','D13','D23'],Anames))
    for item in varyList:
        keys = item.split(':')
        if keys[2] in Ddict:
            key = keys[0]+'::'+Ddict[keys[2]]       #key is e.g. '0::A0'
            parm = keys[0]+'::'+keys[2]             #parm is e.g. '0::D11'
            newCellDict[parm] = [key,parmDict[key]+parmDict[item]]
    return newCellDict          # is e.g. {'0::D11':A0+D11}
    
def ApplyXYZshifts(parmDict,varyList):
    '''
    takes atom x,y,z shift and applies it to corresponding atom x,y,z value
    
    :param dict parmDict: parameter dictionary
    :param list varyList: list of variables
    :returns: newAtomDict - dictionary of new atomic coordinate names & values; key is parameter shift name

    '''
    newAtomDict = {}
    for item in parmDict:
        if 'dA' in item:
            parm = ''.join(item.split('d'))
            parmDict[parm] += parmDict[item]
            newAtomDict[item] = [parm,parmDict[parm]]
    return newAtomDict
    
def SHTXcal(refl,g,pfx,hfx,SGData,calcControls,parmDict):
    'Spherical harmonics texture'
    IFCoup = 'Bragg' in calcControls[hfx+'instType']
    odfCor = 1.0
    H = refl[:3]
    cell = G2lat.Gmat2cell(g)
    Sangls = [parmDict[pfx+'SH omega'],parmDict[pfx+'SH chi'],parmDict[pfx+'SH phi']]
    Gangls = [parmDict[hfx+'Omega'],parmDict[hfx+'Chi'],parmDict[hfx+'Phi'],parmDict[hfx+'Azimuth']]
    phi,beta = G2lat.CrsAng(H,cell,SGData)
    psi,gam,x,x = G2lat.SamAng(refl[5]/2.,Gangls,Sangls,IFCoup) #ignore 2 sets of angle derivs.
    SHnames = G2lat.GenSHCoeff(SGData['SGLaue'],parmDict[pfx+'SHmodel'],parmDict[pfx+'SHorder'])
    for item in SHnames:
        L,M,N = eval(item.strip('C'))
        Kcl = G2lat.GetKcl(L,N,SGData['SGLaue'],phi,beta)
        Ksl,x,x = G2lat.GetKsl(L,M,parmDict[pfx+'SHmodel'],psi,gam)
        Lnorm = G2lat.Lnorm(L)
        odfCor += parmDict[pfx+item]*Lnorm*Kcl*Ksl
    return odfCor
    
def SHTXcalDerv(refl,g,pfx,hfx,SGData,calcControls,parmDict):
    'Spherical harmonics texture derivatives'
    FORPI = 4.0*np.pi
    IFCoup = 'Bragg' in calcControls[hfx+'instType']
    odfCor = 1.0
    dFdODF = {}
    dFdSA = [0,0,0]
    H = refl[:3]
    cell = G2lat.Gmat2cell(g)
    Sangls = [parmDict[pfx+'SH omega'],parmDict[pfx+'SH chi'],parmDict[pfx+'SH phi']]
    Gangls = [parmDict[hfx+'Omega'],parmDict[hfx+'Chi'],parmDict[hfx+'Phi'],parmDict[hfx+'Azimuth']]
    phi,beta = G2lat.CrsAng(H,cell,SGData)
    psi,gam,dPSdA,dGMdA = G2lat.SamAng(refl[5]/2.,Gangls,Sangls,IFCoup)
    SHnames = G2lat.GenSHCoeff(SGData['SGLaue'],parmDict[pfx+'SHmodel'],parmDict[pfx+'SHorder'])
    for item in SHnames:
        L,M,N = eval(item.strip('C'))
        Kcl = G2lat.GetKcl(L,N,SGData['SGLaue'],phi,beta)
        Ksl,dKsdp,dKsdg = G2lat.GetKsl(L,M,parmDict[pfx+'SHmodel'],psi,gam)
        Lnorm = G2lat.Lnorm(L)
        odfCor += parmDict[pfx+item]*Lnorm*Kcl*Ksl
        dFdODF[pfx+item] = Lnorm*Kcl*Ksl
        for i in range(3):
            dFdSA[i] += parmDict[pfx+item]*Lnorm*Kcl*(dKsdp*dPSdA[i]+dKsdg*dGMdA[i])
    return odfCor,dFdODF,dFdSA
    
def SHPOcal(refl,g,phfx,hfx,SGData,calcControls,parmDict):
    'spherical harmonics preferred orientation (cylindrical symmetry only)'
    odfCor = 1.0
    H = refl[:3]
    cell = G2lat.Gmat2cell(g)
    Sangl = [0.,0.,0.]
    if 'Bragg' in calcControls[hfx+'instType']:
        Gangls = [0.,90.,0.,parmDict[hfx+'Azimuth']]
        IFCoup = True
    else:
        Gangls = [0.,0.,0.,parmDict[hfx+'Azimuth']]
        IFCoup = False
    phi,beta = G2lat.CrsAng(H,cell,SGData)
    psi,gam,x,x = G2lat.SamAng(refl[5]/2.,Gangls,Sangl,IFCoup) #ignore 2 sets of angle derivs.
    SHnames = G2lat.GenSHCoeff(SGData['SGLaue'],'0',calcControls[phfx+'SHord'],False)
    for item in SHnames:
        L,N = eval(item.strip('C'))
        Kcsl,Lnorm = G2lat.GetKclKsl(L,N,SGData['SGLaue'],psi,phi,beta) 
        odfCor += parmDict[phfx+item]*Lnorm*Kcsl
    return odfCor
    
def SHPOcalDerv(refl,g,phfx,hfx,SGData,calcControls,parmDict):
    'spherical harmonics preferred orientation derivatives (cylindrical symmetry only)'
    FORPI = 12.5663706143592
    odfCor = 1.0
    dFdODF = {}
    H = refl[:3]
    cell = G2lat.Gmat2cell(g)
    Sangl = [0.,0.,0.]
    if 'Bragg' in calcControls[hfx+'instType']:
        Gangls = [0.,90.,0.,parmDict[hfx+'Azimuth']]
        IFCoup = True
    else:
        Gangls = [0.,0.,0.,parmDict[hfx+'Azimuth']]
        IFCoup = False
    phi,beta = G2lat.CrsAng(H,cell,SGData)
    psi,gam,x,x = G2lat.SamAng(refl[5]/2.,Gangls,Sangl,IFCoup) #ignore 2 sets of angle derivs.
    SHnames = G2lat.GenSHCoeff(SGData['SGLaue'],'0',calcControls[phfx+'SHord'],False)
    for item in SHnames:
        L,N = eval(item.strip('C'))
        Kcsl,Lnorm = G2lat.GetKclKsl(L,N,SGData['SGLaue'],psi,phi,beta) 
        odfCor += parmDict[phfx+item]*Lnorm*Kcsl
        dFdODF[phfx+item] = Kcsl*Lnorm
    return odfCor,dFdODF
    
def GetPrefOri(refl,G,g,phfx,hfx,SGData,calcControls,parmDict):
    'Needs a doc string'
    POcorr = 1.0
    if calcControls[phfx+'poType'] == 'MD':
        MD = parmDict[phfx+'MD']
        if MD != 1.0:
            MDAxis = calcControls[phfx+'MDAxis']
            sumMD = 0
            for H in refl[11]:            
                cosP,sinP = G2lat.CosSinAngle(H,MDAxis,G)
                A = 1.0/np.sqrt((MD*cosP)**2+sinP**2/MD)
                sumMD += A**3
            POcorr = sumMD/len(refl[11])
    else:   #spherical harmonics
        if calcControls[phfx+'SHord']:
            POcorr = SHPOcal(refl,g,phfx,hfx,SGData,calcControls,parmDict)
    return POcorr
    
def GetPrefOriDerv(refl,G,g,phfx,hfx,SGData,calcControls,parmDict):
    'Needs a doc string'
    POcorr = 1.0
    POderv = {}
    if calcControls[phfx+'poType'] == 'MD':
        MD = parmDict[phfx+'MD']
        MDAxis = calcControls[phfx+'MDAxis']
        sumMD = 0
        sumdMD = 0
        for H in refl[11]:            
            cosP,sinP = G2lat.CosSinAngle(H,MDAxis,G)
            A = 1.0/np.sqrt((MD*cosP)**2+sinP**2/MD)
            sumMD += A**3
            sumdMD -= (1.5*A**5)*(2.0*MD*cosP**2-(sinP/MD)**2)
        POcorr = sumMD/len(refl[11])
        POderv[phfx+'MD'] = sumdMD/len(refl[11])
    else:   #spherical harmonics
        if calcControls[phfx+'SHord']:
            POcorr,POderv = SHPOcalDerv(refl,g,phfx,hfx,SGData,calcControls,parmDict)
    return POcorr,POderv
    
def GetAbsorb(refl,hfx,calcControls,parmDict):
    'Needs a doc string'
    if 'Debye' in calcControls[hfx+'instType']:
        return G2pwd.Absorb('Cylinder',parmDict[hfx+'Absorption'],refl[5],0,0)
    else:
        return 1.0
    
def GetAbsorbDerv(refl,hfx,calcControls,parmDict):
    'Needs a doc string'
    if 'Debye' in calcControls[hfx+'instType']:
        return G2pwd.AbsorbDerv('Cylinder',parmDict[hfx+'Absorption'],refl[5],0,0)
    else:
        return 0.0
    
def GetIntensityCorr(refl,G,g,pfx,phfx,hfx,SGData,calcControls,parmDict):
    'Needs a doc string'
    Icorr = parmDict[phfx+'Scale']*parmDict[hfx+'Scale']*refl[3]               #scale*multiplicity
    if 'X' in parmDict[hfx+'Type']:
        Icorr *= G2pwd.Polarization(parmDict[hfx+'Polariz.'],refl[5],parmDict[hfx+'Azimuth'])[0]
    Icorr *= GetPrefOri(refl,G,g,phfx,hfx,SGData,calcControls,parmDict)
    if pfx+'SHorder' in parmDict:
        Icorr *= SHTXcal(refl,g,pfx,hfx,SGData,calcControls,parmDict)
    Icorr *= GetAbsorb(refl,hfx,calcControls,parmDict)
    refl[13] = Icorr        
    
def GetIntensityDerv(refl,G,g,pfx,phfx,hfx,SGData,calcControls,parmDict):
    'Needs a doc string'
    dIdsh = 1./parmDict[hfx+'Scale']
    dIdsp = 1./parmDict[phfx+'Scale']
    if 'X' in parmDict[hfx+'Type']:
        pola,dIdPola = G2pwd.Polarization(parmDict[hfx+'Polariz.'],refl[5],parmDict[hfx+'Azimuth'])
        dIdPola /= pola
    else:       #'N'
        dIdPola = 0.0
    POcorr,dIdPO = GetPrefOriDerv(refl,G,g,phfx,hfx,SGData,calcControls,parmDict)
    for iPO in dIdPO:
        dIdPO[iPO] /= POcorr
    dFdODF = {}
    dFdSA = [0,0,0]
    if pfx+'SHorder' in parmDict:
        odfCor,dFdODF,dFdSA = SHTXcalDerv(refl,g,pfx,hfx,SGData,calcControls,parmDict)
        for iSH in dFdODF:
            dFdODF[iSH] /= odfCor
        for i in range(3):
            dFdSA[i] /= odfCor
    dFdAb = GetAbsorbDerv(refl,hfx,calcControls,parmDict)
    return dIdsh,dIdsp,dIdPola,dIdPO,dFdODF,dFdSA,dFdAb
        
def GetSampleSigGam(refl,wave,G,GB,phfx,calcControls,parmDict):
    'Needs a doc string'
    costh = cosd(refl[5]/2.)
    #crystallite size
    if calcControls[phfx+'SizeType'] == 'isotropic':
        Sgam = 1.8*wave/(np.pi*parmDict[phfx+'Size;i']*costh)
    elif calcControls[phfx+'SizeType'] == 'uniaxial':
        H = np.array(refl[:3])
        P = np.array(calcControls[phfx+'SizeAxis'])
        cosP,sinP = G2lat.CosSinAngle(H,P,G)
        Sgam = (1.8*wave/np.pi)/(parmDict[phfx+'Size;i']*parmDict[phfx+'Size;a']*costh)
        Sgam *= np.sqrt((sinP*parmDict[phfx+'Size;a'])**2+(cosP*parmDict[phfx+'Size;i'])**2)
    else:           #ellipsoidal crystallites
        Sij =[parmDict[phfx+'Size:%d'%(i)] for i in range(6)]
        H = np.array(refl[:3])
        lenR = G2pwd.ellipseSize(H,Sij,GB)
        Sgam = 1.8*wave/(np.pi*costh*lenR)
    #microstrain                
    if calcControls[phfx+'MustrainType'] == 'isotropic':
        Mgam = 0.018*parmDict[phfx+'Mustrain;i']*tand(refl[5]/2.)/np.pi
    elif calcControls[phfx+'MustrainType'] == 'uniaxial':
        H = np.array(refl[:3])
        P = np.array(calcControls[phfx+'MustrainAxis'])
        cosP,sinP = G2lat.CosSinAngle(H,P,G)
        Si = parmDict[phfx+'Mustrain;i']
        Sa = parmDict[phfx+'Mustrain;a']
        Mgam = 0.018*Si*Sa*tand(refl[5]/2.)/(np.pi*np.sqrt((Si*cosP)**2+(Sa*sinP)**2))
    else:       #generalized - P.W. Stephens model
        pwrs = calcControls[phfx+'MuPwrs']
        sum = 0
        for i,pwr in enumerate(pwrs):
            sum += parmDict[phfx+'Mustrain:'+str(i)]*refl[0]**pwr[0]*refl[1]**pwr[1]*refl[2]**pwr[2]
        Mgam = 0.018*refl[4]**2*tand(refl[5]/2.)*sum
    gam = Sgam*parmDict[phfx+'Size;mx']+Mgam*parmDict[phfx+'Mustrain;mx']
    sig = (Sgam*(1.-parmDict[phfx+'Size;mx']))**2+(Mgam*(1.-parmDict[phfx+'Mustrain;mx']))**2
    sig /= ateln2
    return sig,gam
        
def GetSampleSigGamDerv(refl,wave,G,GB,phfx,calcControls,parmDict):
    'Needs a doc string'
    gamDict = {}
    sigDict = {}
    costh = cosd(refl[5]/2.)
    tanth = tand(refl[5]/2.)
    #crystallite size derivatives
    if calcControls[phfx+'SizeType'] == 'isotropic':
        Sgam = 1.8*wave/(np.pi*parmDict[phfx+'Size;i']*costh)
        gamDict[phfx+'Size;i'] = -1.8*wave*parmDict[phfx+'Size;mx']/(np.pi*costh)
        sigDict[phfx+'Size;i'] = -3.6*Sgam*wave*(1.-parmDict[phfx+'Size;mx'])**2/(np.pi*costh*ateln2)
    elif calcControls[phfx+'SizeType'] == 'uniaxial':
        H = np.array(refl[:3])
        P = np.array(calcControls[phfx+'SizeAxis'])
        cosP,sinP = G2lat.CosSinAngle(H,P,G)
        Si = parmDict[phfx+'Size;i']
        Sa = parmDict[phfx+'Size;a']
        gami = (1.8*wave/np.pi)/(Si*Sa)
        sqtrm = np.sqrt((sinP*Sa)**2+(cosP*Si)**2)
        Sgam = gami*sqtrm
        gam = Sgam/costh
        dsi = (gami*Si*cosP**2/(sqtrm*costh)-gam/Si)
        dsa = (gami*Sa*sinP**2/(sqtrm*costh)-gam/Sa)
        gamDict[phfx+'Size;i'] = dsi*parmDict[phfx+'Size;mx']
        gamDict[phfx+'Size;a'] = dsa*parmDict[phfx+'Size;mx']
        sigDict[phfx+'Size;i'] = 2.*dsi*Sgam*(1.-parmDict[phfx+'Size;mx'])**2/ateln2
        sigDict[phfx+'Size;a'] = 2.*dsa*Sgam*(1.-parmDict[phfx+'Size;mx'])**2/ateln2
    else:           #ellipsoidal crystallites
        const = 1.8*wave/(np.pi*costh)
        Sij =[parmDict[phfx+'Size:%d'%(i)] for i in range(6)]
        H = np.array(refl[:3])
        lenR,dRdS = G2pwd.ellipseSizeDerv(H,Sij,GB)
        Sgam = 1.8*wave/(np.pi*costh*lenR)
        for i,item in enumerate([phfx+'Size:%d'%(j) for j in range(6)]):
            gamDict[item] = -(const/lenR**2)*dRdS[i]*parmDict[phfx+'Size;mx']
            sigDict[item] = -2.*Sgam*(const/lenR**2)*dRdS[i]*(1.-parmDict[phfx+'Size;mx'])**2/ateln2
    gamDict[phfx+'Size;mx'] = Sgam
    sigDict[phfx+'Size;mx'] = -2.*Sgam**2*(1.-parmDict[phfx+'Size;mx'])/ateln2
            
    #microstrain derivatives                
    if calcControls[phfx+'MustrainType'] == 'isotropic':
        Mgam = 0.018*parmDict[phfx+'Mustrain;i']*tand(refl[5]/2.)/np.pi
        gamDict[phfx+'Mustrain;i'] =  0.018*tanth*parmDict[phfx+'Mustrain;mx']/np.pi
        sigDict[phfx+'Mustrain;i'] =  0.036*Mgam*tanth*(1.-parmDict[phfx+'Mustrain;mx'])**2/(np.pi*ateln2)        
    elif calcControls[phfx+'MustrainType'] == 'uniaxial':
        H = np.array(refl[:3])
        P = np.array(calcControls[phfx+'MustrainAxis'])
        cosP,sinP = G2lat.CosSinAngle(H,P,G)
        Si = parmDict[phfx+'Mustrain;i']
        Sa = parmDict[phfx+'Mustrain;a']
        gami = 0.018*Si*Sa*tanth/np.pi
        sqtrm = np.sqrt((Si*cosP)**2+(Sa*sinP)**2)
        Mgam = gami/sqtrm
        dsi = -gami*Si*cosP**2/sqtrm**3
        dsa = -gami*Sa*sinP**2/sqtrm**3
        gamDict[phfx+'Mustrain;i'] = (Mgam/Si+dsi)*parmDict[phfx+'Mustrain;mx']
        gamDict[phfx+'Mustrain;a'] = (Mgam/Sa+dsa)*parmDict[phfx+'Mustrain;mx']
        sigDict[phfx+'Mustrain;i'] = 2*(Mgam/Si+dsi)*Mgam*(1.-parmDict[phfx+'Mustrain;mx'])**2/ateln2
        sigDict[phfx+'Mustrain;a'] = 2*(Mgam/Sa+dsa)*Mgam*(1.-parmDict[phfx+'Mustrain;mx'])**2/ateln2       
    else:       #generalized - P.W. Stephens model
        pwrs = calcControls[phfx+'MuPwrs']
        const = 0.018*refl[4]**2*tanth
        sum = 0
        for i,pwr in enumerate(pwrs):
            term = refl[0]**pwr[0]*refl[1]**pwr[1]*refl[2]**pwr[2]
            sum += parmDict[phfx+'Mustrain:'+str(i)]*term
            gamDict[phfx+'Mustrain:'+str(i)] = const*term*parmDict[phfx+'Mustrain;mx']
            sigDict[phfx+'Mustrain:'+str(i)] = \
                2.*const*term*(1.-parmDict[phfx+'Mustrain;mx'])**2/ateln2
        Mgam = 0.018*refl[4]**2*tand(refl[5]/2.)*sum
        for i in range(len(pwrs)):
            sigDict[phfx+'Mustrain:'+str(i)] *= Mgam
    gamDict[phfx+'Mustrain;mx'] = Mgam
    sigDict[phfx+'Mustrain;mx'] = -2.*Mgam**2*(1.-parmDict[phfx+'Mustrain;mx'])/ateln2
    return sigDict,gamDict
        
def GetReflPos(refl,wave,G,hfx,calcControls,parmDict):
    'Needs a doc string'
    h,k,l = refl[:3]
    dsq = 1./G2lat.calc_rDsq2(np.array([h,k,l]),G)
    d = np.sqrt(dsq)

    refl[4] = d
    pos = 2.0*asind(wave/(2.0*d))+parmDict[hfx+'Zero']
    const = 9.e-2/(np.pi*parmDict[hfx+'Gonio. radius'])                  #shifts in microns
    if 'Bragg' in calcControls[hfx+'instType']:
        pos -= const*(4.*parmDict[hfx+'Shift']*cosd(pos/2.0)+ \
            parmDict[hfx+'Transparency']*sind(pos)*100.0)            #trans(=1/mueff) in cm
    else:               #Debye-Scherrer - simple but maybe not right
        pos -= const*(parmDict[hfx+'DisplaceX']*cosd(pos)+parmDict[hfx+'DisplaceY']*sind(pos))
    return pos

def GetReflPosDerv(refl,wave,A,hfx,calcControls,parmDict):
    'Needs a doc string'
    dpr = 180./np.pi
    h,k,l = refl[:3]
    dstsq = G2lat.calc_rDsq(np.array([h,k,l]),A)
    dst = np.sqrt(dstsq)
    pos = refl[5]-parmDict[hfx+'Zero']
    const = dpr/np.sqrt(1.0-wave**2*dstsq/4.0)
    dpdw = const*dst
    dpdA = np.array([h**2,k**2,l**2,h*k,h*l,k*l])
    dpdA *= const*wave/(2.0*dst)
    dpdZ = 1.0
    const = 9.e-2/(np.pi*parmDict[hfx+'Gonio. radius'])                  #shifts in microns
    if 'Bragg' in calcControls[hfx+'instType']:
        dpdSh = -4.*const*cosd(pos/2.0)
        dpdTr = -const*sind(pos)*100.0
        return dpdA,dpdw,dpdZ,dpdSh,dpdTr,0.,0.
    else:               #Debye-Scherrer - simple but maybe not right
        dpdXd = -const*cosd(pos)
        dpdYd = -const*sind(pos)
        return dpdA,dpdw,dpdZ,0.,0.,dpdXd,dpdYd
            
def GetHStrainShift(refl,SGData,phfx,parmDict):
    'Needs a doc string'
    laue = SGData['SGLaue']
    uniq = SGData['SGUniq']
    h,k,l = refl[:3]
    if laue in ['m3','m3m']:
        Dij = parmDict[phfx+'D11']*(h**2+k**2+l**2)+ \
            refl[4]**2*parmDict[phfx+'eA']*((h*k)**2+(h*l)**2+(k*l)**2)/(h**2+k**2+l**2)**2
    elif laue in ['6/m','6/mmm','3m1','31m','3']:
        Dij = parmDict[phfx+'D11']*(h**2+k**2+h*k)+parmDict[phfx+'D33']*l**2
    elif laue in ['3R','3mR']:
        Dij = parmDict[phfx+'D11']*(h**2+k**2+l**2)+parmDict[phfx+'D12']*(h*k+h*l+k*l)
    elif laue in ['4/m','4/mmm']:
        Dij = parmDict[phfx+'D11']*(h**2+k**2)+parmDict[phfx+'D33']*l**2
    elif laue in ['mmm']:
        Dij = parmDict[phfx+'D11']*h**2+parmDict[phfx+'D22']*k**2+parmDict[phfx+'D33']*l**2
    elif laue in ['2/m']:
        Dij = parmDict[phfx+'D11']*h**2+parmDict[phfx+'D22']*k**2+parmDict[phfx+'D33']*l**2
        if uniq == 'a':
            Dij += parmDict[phfx+'D23']*k*l
        elif uniq == 'b':
            Dij += parmDict[phfx+'D13']*h*l
        elif uniq == 'c':
            Dij += parmDict[phfx+'D12']*h*k
    else:
        Dij = parmDict[phfx+'D11']*h**2+parmDict[phfx+'D22']*k**2+parmDict[phfx+'D33']*l**2+ \
            parmDict[phfx+'D12']*h*k+parmDict[phfx+'D13']*h*l+parmDict[phfx+'D23']*k*l
    return -Dij*refl[4]**2*tand(refl[5]/2.0)
            
def GetHStrainShiftDerv(refl,SGData,phfx):
    'Needs a doc string'
    laue = SGData['SGLaue']
    uniq = SGData['SGUniq']
    h,k,l = refl[:3]
    if laue in ['m3','m3m']:
        dDijDict = {phfx+'D11':h**2+k**2+l**2,
            phfx+'eA':refl[4]**2*((h*k)**2+(h*l)**2+(k*l)**2)/(h**2+k**2+l**2)**2}
    elif laue in ['6/m','6/mmm','3m1','31m','3']:
        dDijDict = {phfx+'D11':h**2+k**2+h*k,phfx+'D33':l**2}
    elif laue in ['3R','3mR']:
        dDijDict = {phfx+'D11':h**2+k**2+l**2,phfx+'D12':h*k+h*l+k*l}
    elif laue in ['4/m','4/mmm']:
        dDijDict = {phfx+'D11':h**2+k**2,phfx+'D33':l**2}
    elif laue in ['mmm']:
        dDijDict = {phfx+'D11':h**2,phfx+'D22':k**2,phfx+'D33':l**2}
    elif laue in ['2/m']:
        dDijDict = {phfx+'D11':h**2,phfx+'D22':k**2,phfx+'D33':l**2}
        if uniq == 'a':
            dDijDict[phfx+'D23'] = k*l
        elif uniq == 'b':
            dDijDict[phfx+'D13'] = h*l
        elif uniq == 'c':
            dDijDict[phfx+'D12'] = h*k
            names.append()
    else:
        dDijDict = {phfx+'D11':h**2,phfx+'D22':k**2,phfx+'D33':l**2,
            phfx+'D12':h*k,phfx+'D13':h*l,phfx+'D23':k*l}
    for item in dDijDict:
        dDijDict[item] *= -refl[4]**2*tand(refl[5]/2.0)
    return dDijDict
    
def GetFobsSq(Histograms,Phases,parmDict,calcControls):
    'Needs a doc string'
    histoList = Histograms.keys()
    histoList.sort()
    for histogram in histoList:
        if 'PWDR' in histogram[:4]:
            Histogram = Histograms[histogram]
            hId = Histogram['hId']
            hfx = ':%d:'%(hId)
            Limits = calcControls[hfx+'Limits']
            shl = max(parmDict[hfx+'SH/L'],0.0005)
            Ka2 = False
            kRatio = 0.0
            if hfx+'Lam1' in parmDict.keys():
                Ka2 = True
                lamRatio = 360*(parmDict[hfx+'Lam2']-parmDict[hfx+'Lam1'])/(np.pi*parmDict[hfx+'Lam1'])
                kRatio = parmDict[hfx+'I(L2)/I(L1)']
            x,y,w,yc,yb,yd = Histogram['Data']
            xB = np.searchsorted(x,Limits[0])
            xF = np.searchsorted(x,Limits[1])
            ymb = np.array(y-yb)
            ymb = np.where(ymb,ymb,1.0)
            ycmb = np.array(yc-yb)
            ratio = 1./np.where(ycmb,ycmb/ymb,1.e10)          
            refLists = Histogram['Reflection Lists']
            for phase in refLists:
                Phase = Phases[phase]
                pId = Phase['pId']
                phfx = '%d:%d:'%(pId,hId)
                refList = refLists[phase]
                sumFo = 0.0
                sumdF = 0.0
                sumFosq = 0.0
                sumdFsq = 0.0
                for refl in refList:
                    if 'C' in calcControls[hfx+'histType']:
                        yp = np.zeros_like(yb)
                        Wd,fmin,fmax = G2pwd.getWidthsCW(refl[5],refl[6],refl[7],shl)
                        iBeg = max(xB,np.searchsorted(x,refl[5]-fmin))
                        iFin = max(xB,min(np.searchsorted(x,refl[5]+fmax),xF))
                        iFin2 = iFin
                        yp[iBeg:iFin] = refl[13]*refl[9]*G2pwd.getFCJVoigt3(refl[5],refl[6],refl[7],shl,x[iBeg:iFin])    #>90% of time spent here
                        if Ka2:
                            pos2 = refl[5]+lamRatio*tand(refl[5]/2.0)       # + 360/pi * Dlam/lam * tan(th)
                            Wd,fmin,fmax = G2pwd.getWidthsCW(pos2,refl[6],refl[7],shl)
                            iBeg2 = max(xB,np.searchsorted(x,pos2-fmin))
                            iFin2 = min(np.searchsorted(x,pos2+fmax),xF)
                            if not iBeg2+iFin2:       #peak below low limit - skip peak
                                continue
                            elif not iBeg2-iFin2:     #peak above high limit - done
                                break
                            yp[iBeg2:iFin2] += refl[13]*refl[9]*kRatio*G2pwd.getFCJVoigt3(pos2,refl[6],refl[7],shl,x[iBeg2:iFin2])        #and here
                        refl[8] = np.sum(np.where(ratio[iBeg:iFin2]>0.,yp[iBeg:iFin2]*ratio[iBeg:iFin2]/(refl[13]*(1.+kRatio)),0.0))
                    elif 'T' in calcControls[hfx+'histType']:
                        print 'TOF Undefined at present'
                        raise Exception    #no TOF yet
                    Fo = np.sqrt(np.abs(refl[8]))
                    Fc = np.sqrt(np.abs(refl[9]))
                    sumFo += Fo
                    sumFosq += refl[8]**2
                    sumdF += np.abs(Fo-Fc)
                    sumdFsq += (refl[8]-refl[9])**2
                Histogram['Residuals'][phfx+'Rf'] = min(100.,(sumdF/sumFo)*100.)
                Histogram['Residuals'][phfx+'Rf^2'] = min(100.,np.sqrt(sumdFsq/sumFosq)*100.)
                Histogram['Residuals'][phfx+'Nref'] = len(refList)
                Histogram['Residuals']['hId'] = hId
        elif 'HKLF' in histogram[:4]:
            Histogram = Histograms[histogram]
            Histogram['Residuals']['hId'] = Histograms[histogram]['hId']
                
def getPowderProfile(parmDict,x,varylist,Histogram,Phases,calcControls,pawleyLookup):
    'Needs a doc string'
    
    def GetReflSigGam(refl,wave,G,GB,hfx,phfx,calcControls,parmDict):
        U = parmDict[hfx+'U']
        V = parmDict[hfx+'V']
        W = parmDict[hfx+'W']
        X = parmDict[hfx+'X']
        Y = parmDict[hfx+'Y']
        tanPos = tand(refl[5]/2.0)
        Ssig,Sgam = GetSampleSigGam(refl,wave,G,GB,phfx,calcControls,parmDict)
        sig = U*tanPos**2+V*tanPos+W+Ssig     #save peak sigma
        sig = max(0.001,sig)
        gam = X/cosd(refl[5]/2.0)+Y*tanPos+Sgam     #save peak gamma
        gam = max(0.001,gam)
        return sig,gam
                
    hId = Histogram['hId']
    hfx = ':%d:'%(hId)
    bakType = calcControls[hfx+'bakType']
    yb = G2pwd.getBackground(hfx,parmDict,bakType,x)
    yc = np.zeros_like(yb)
        
    if 'C' in calcControls[hfx+'histType']:    
        shl = max(parmDict[hfx+'SH/L'],0.002)
        Ka2 = False
        if hfx+'Lam1' in parmDict.keys():
            wave = parmDict[hfx+'Lam1']
            Ka2 = True
            lamRatio = 360*(parmDict[hfx+'Lam2']-parmDict[hfx+'Lam1'])/(np.pi*parmDict[hfx+'Lam1'])
            kRatio = parmDict[hfx+'I(L2)/I(L1)']
        else:
            wave = parmDict[hfx+'Lam']
    else:
        print 'TOF Undefined at present'
        raise ValueError
    for phase in Histogram['Reflection Lists']:
        refList = Histogram['Reflection Lists'][phase]
        Phase = Phases[phase]
        pId = Phase['pId']
        pfx = '%d::'%(pId)
        phfx = '%d:%d:'%(pId,hId)
        hfx = ':%d:'%(hId)
        SGData = Phase['General']['SGData']
        A = [parmDict[pfx+'A%d'%(i)] for i in range(6)]
        G,g = G2lat.A2Gmat(A)       #recip & real metric tensors
        GA,GB = G2lat.Gmat2AB(G)    #Orthogonalization matricies
        Vst = np.sqrt(nl.det(G))    #V*
        if not Phase['General'].get('doPawley'):
            time0 = time.time()
            StructureFactor(refList,G,hfx,pfx,SGData,calcControls,parmDict)
#            print 'sf calc time: %.3fs'%(time.time()-time0)
        time0 = time.time()
        for refl in refList:
            if 'C' in calcControls[hfx+'histType']:
                h,k,l = refl[:3]
                refl[5] = GetReflPos(refl,wave,G,hfx,calcControls,parmDict)         #corrected reflection position
                Lorenz = 1./(2.*sind(refl[5]/2.)**2*cosd(refl[5]/2.))           #Lorentz correction
                refl[5] += GetHStrainShift(refl,SGData,phfx,parmDict)               #apply hydrostatic strain shift
                refl[6:8] = GetReflSigGam(refl,wave,G,GB,hfx,phfx,calcControls,parmDict)    #peak sig & gam
                GetIntensityCorr(refl,G,g,pfx,phfx,hfx,SGData,calcControls,parmDict)    #puts corrections in refl[13]
                refl[13] *= Vst*Lorenz
                if Phase['General'].get('doPawley'):
                    try:
                        pInd =pfx+'PWLref:%d'%(pawleyLookup[pfx+'%d,%d,%d'%(h,k,l)])
                        refl[9] = parmDict[pInd]
                    except KeyError:
#                        print ' ***Error %d,%d,%d missing from Pawley reflection list ***'%(h,k,l)
                        continue
                Wd,fmin,fmax = G2pwd.getWidthsCW(refl[5],refl[6],refl[7],shl)
                iBeg = np.searchsorted(x,refl[5]-fmin)
                iFin = np.searchsorted(x,refl[5]+fmax)
                if not iBeg+iFin:       #peak below low limit - skip peak
                    continue
                elif not iBeg-iFin:     #peak above high limit - done
                    break
                yc[iBeg:iFin] += refl[13]*refl[9]*G2pwd.getFCJVoigt3(refl[5],refl[6],refl[7],shl,ma.getdata(x[iBeg:iFin]))    #>90% of time spent here
                if Ka2:
                    pos2 = refl[5]+lamRatio*tand(refl[5]/2.0)       # + 360/pi * Dlam/lam * tan(th)
                    Wd,fmin,fmax = G2pwd.getWidthsCW(pos2,refl[6],refl[7],shl)
                    iBeg = np.searchsorted(x,pos2-fmin)
                    iFin = np.searchsorted(x,pos2+fmax)
                    if not iBeg+iFin:       #peak below low limit - skip peak
                        continue
                    elif not iBeg-iFin:     #peak above high limit - done
                        return yc,yb
                    yc[iBeg:iFin] += refl[13]*refl[9]*kRatio*G2pwd.getFCJVoigt3(pos2,refl[6],refl[7],shl,ma.getdata(x[iBeg:iFin]))        #and here
            elif 'T' in calcControls[hfx+'histType']:
                print 'TOF Undefined at present'
                raise Exception    #no TOF yet
#        print 'profile calc time: %.3fs'%(time.time()-time0)
    return yc,yb
    
def getPowderProfileDerv(parmDict,x,varylist,Histogram,Phases,rigidbodyDict,calcControls,pawleyLookup):
    'Needs a doc string'
    
    def cellVaryDerv(pfx,SGData,dpdA): 
        if SGData['SGLaue'] in ['-1',]:
            return [[pfx+'A0',dpdA[0]],[pfx+'A1',dpdA[1]],[pfx+'A2',dpdA[2]],
                [pfx+'A3',dpdA[3]],[pfx+'A4',dpdA[4]],[pfx+'A5',dpdA[5]]]
        elif SGData['SGLaue'] in ['2/m',]:
            if SGData['SGUniq'] == 'a':
                return [[pfx+'A0',dpdA[0]],[pfx+'A1',dpdA[1]],[pfx+'A2',dpdA[2]],[pfx+'A3',dpdA[3]]]
            elif SGData['SGUniq'] == 'b':
                return [[pfx+'A0',dpdA[0]],[pfx+'A1',dpdA[1]],[pfx+'A2',dpdA[2]],[pfx+'A4',dpdA[4]]]
            else:
                return [[pfx+'A0',dpdA[0]],[pfx+'A1',dpdA[1]],[pfx+'A2',dpdA[2]],[pfx+'A5',dpdA[5]]]
        elif SGData['SGLaue'] in ['mmm',]:
            return [[pfx+'A0',dpdA[0]],[pfx+'A1',dpdA[1]],[pfx+'A2',dpdA[2]]]
        elif SGData['SGLaue'] in ['4/m','4/mmm']:
            return [[pfx+'A0',dpdA[0]],[pfx+'A2',dpdA[2]]]
        elif SGData['SGLaue'] in ['6/m','6/mmm','3m1', '31m', '3']:
            return [[pfx+'A0',dpdA[0]],[pfx+'A2',dpdA[2]]]
        elif SGData['SGLaue'] in ['3R', '3mR']:
            return [[pfx+'A0',dpdA[0]+dpdA[1]+dpdA[2]],[pfx+'A3',dpdA[3]+dpdA[4]+dpdA[5]]]                       
        elif SGData['SGLaue'] in ['m3m','m3']:
            return [[pfx+'A0',dpdA[0]]]
            
    # create a list of dependent variables and set up a dictionary to hold their derivatives
    dependentVars = G2mv.GetDependentVars()
    depDerivDict = {}
    for j in dependentVars:
        depDerivDict[j] = np.zeros(shape=(len(x)))
    #print 'dependent vars',dependentVars
    lenX = len(x)                
    hId = Histogram['hId']
    hfx = ':%d:'%(hId)
    bakType = calcControls[hfx+'bakType']
    dMdv = np.zeros(shape=(len(varylist),len(x)))
    dMdb,dMddb,dMdpk = G2pwd.getBackgroundDerv(hfx,parmDict,bakType,x)
    if hfx+'Back:0' in varylist: # for now assume that Back:x vars to not appear in constraints
        bBpos =varylist.index(hfx+'Back:0')
        dMdv[bBpos:bBpos+len(dMdb)] = dMdb
    names = [hfx+'DebyeA',hfx+'DebyeR',hfx+'DebyeU']
    for name in varylist:
        if 'Debye' in name:
            id = int(name.split(':')[-1])
            parm = name[:int(name.rindex(':'))]
            ip = names.index(parm)
            dMdv[varylist.index(name)] = dMddb[3*id+ip]
    names = [hfx+'BkPkpos',hfx+'BkPkint',hfx+'BkPksig',hfx+'BkPkgam']
    for name in varylist:
        if 'BkPk' in name:
            id = int(name.split(':')[-1])
            parm = name[:int(name.rindex(':'))]
            ip = names.index(parm)
            dMdv[varylist.index(name)] = dMdpk[4*id+ip]
    cw = np.diff(x)
    cw = np.append(cw,cw[-1])
    if 'C' in calcControls[hfx+'histType']:    
        shl = max(parmDict[hfx+'SH/L'],0.002)
        Ka2 = False
        if hfx+'Lam1' in parmDict.keys():
            wave = parmDict[hfx+'Lam1']
            Ka2 = True
            lamRatio = 360*(parmDict[hfx+'Lam2']-parmDict[hfx+'Lam1'])/(np.pi*parmDict[hfx+'Lam1'])
            kRatio = parmDict[hfx+'I(L2)/I(L1)']
        else:
            wave = parmDict[hfx+'Lam']
    else:
        print 'TOF Undefined at present'
        raise ValueError
    for phase in Histogram['Reflection Lists']:
        refList = Histogram['Reflection Lists'][phase]
        Phase = Phases[phase]
        SGData = Phase['General']['SGData']
        pId = Phase['pId']
        pfx = '%d::'%(pId)
        phfx = '%d:%d:'%(pId,hId)
        A = [parmDict[pfx+'A%d'%(i)] for i in range(6)]
        G,g = G2lat.A2Gmat(A)       #recip & real metric tensors
        GA,GB = G2lat.Gmat2AB(G)    #Orthogonalization matricies
        if not Phase['General'].get('doPawley'):
            time0 = time.time()
            dFdvDict = StructureFactorDerv(refList,G,hfx,pfx,SGData,calcControls,parmDict)
#            print 'sf-derv time %.3fs'%(time.time()-time0)
            ApplyRBModelDervs(dFdvDict,parmDict,rigidbodyDict,Phase)
        time0 = time.time()
        for iref,refl in enumerate(refList):
            if 'C' in calcControls[hfx+'histType']:        #CW powder
                h,k,l = refl[:3]
                dIdsh,dIdsp,dIdpola,dIdPO,dFdODF,dFdSA,dFdAb = GetIntensityDerv(refl,G,g,pfx,phfx,hfx,SGData,calcControls,parmDict)
                Wd,fmin,fmax = G2pwd.getWidthsCW(refl[5],refl[6],refl[7],shl)
                iBeg = np.searchsorted(x,refl[5]-fmin)
                iFin = np.searchsorted(x,refl[5]+fmax)
                if not iBeg+iFin:       #peak below low limit - skip peak
                    continue
                elif not iBeg-iFin:     #peak above high limit - done
                    break
                pos = refl[5]
                tanth = tand(pos/2.0)
                costh = cosd(pos/2.0)
                lenBF = iFin-iBeg
                dMdpk = np.zeros(shape=(6,lenBF))
                dMdipk = G2pwd.getdFCJVoigt3(refl[5],refl[6],refl[7],shl,ma.getdata(x[iBeg:iFin]))
                for i in range(5):
                    dMdpk[i] += 100.*cw[iBeg:iFin]*refl[13]*refl[9]*dMdipk[i]
                dervDict = {'int':dMdpk[0],'pos':dMdpk[1],'sig':dMdpk[2],'gam':dMdpk[3],'shl':dMdpk[4],'L1/L2':np.zeros_like(dMdpk[0])}
                if Ka2:
                    pos2 = refl[5]+lamRatio*tanth       # + 360/pi * Dlam/lam * tan(th)
                    iBeg2 = np.searchsorted(x,pos2-fmin)
                    iFin2 = np.searchsorted(x,pos2+fmax)
                    if iBeg2-iFin2:
                        lenBF2 = iFin2-iBeg2
                        dMdpk2 = np.zeros(shape=(6,lenBF2))
                        dMdipk2 = G2pwd.getdFCJVoigt3(pos2,refl[6],refl[7],shl,ma.getdata(x[iBeg2:iFin2]))
                        for i in range(5):
                            dMdpk2[i] = 100.*cw[iBeg2:iFin2]*refl[13]*refl[9]*kRatio*dMdipk2[i]
                        dMdpk2[5] = 100.*cw[iBeg2:iFin2]*refl[13]*dMdipk2[0]
                        dervDict2 = {'int':dMdpk2[0],'pos':dMdpk2[1],'sig':dMdpk2[2],'gam':dMdpk2[3],'shl':dMdpk2[4],'L1/L2':dMdpk2[5]*refl[9]}
                if Phase['General'].get('doPawley'):
                    dMdpw = np.zeros(len(x))
                    try:
                        pIdx = pfx+'PWLref:'+str(pawleyLookup[pfx+'%d,%d,%d'%(h,k,l)])
                        idx = varylist.index(pIdx)
                        dMdpw[iBeg:iFin] = dervDict['int']/refl[9]
                        if Ka2:
                            dMdpw[iBeg2:iFin2] += dervDict2['int']/refl[9]
                        dMdv[idx] = dMdpw
                    except: # ValueError:
                        pass
                dpdA,dpdw,dpdZ,dpdSh,dpdTr,dpdX,dpdY = GetReflPosDerv(refl,wave,A,hfx,calcControls,parmDict)
                names = {hfx+'Scale':[dIdsh,'int'],hfx+'Polariz.':[dIdpola,'int'],phfx+'Scale':[dIdsp,'int'],
                    hfx+'U':[tanth**2,'sig'],hfx+'V':[tanth,'sig'],hfx+'W':[1.0,'sig'],
                    hfx+'X':[1.0/costh,'gam'],hfx+'Y':[tanth,'gam'],hfx+'SH/L':[1.0,'shl'],
                    hfx+'I(L2)/I(L1)':[1.0,'L1/L2'],hfx+'Zero':[dpdZ,'pos'],hfx+'Lam':[dpdw,'pos'],
                    hfx+'Shift':[dpdSh,'pos'],hfx+'Transparency':[dpdTr,'pos'],hfx+'DisplaceX':[dpdX,'pos'],
                    hfx+'DisplaceY':[dpdY,'pos'],hfx+'Absorption':[dFdAb,'int'],}
                for name in names:
                    item = names[name]
                    if name in varylist:
                        dMdv[varylist.index(name)][iBeg:iFin] += item[0]*dervDict[item[1]]
                        if Ka2:
                            dMdv[varylist.index(name)][iBeg2:iFin2] += item[0]*dervDict2[item[1]]
                    elif name in dependentVars:
                        depDerivDict[name][iBeg:iFin] += item[0]*dervDict[item[1]]
                        if Ka2:
                            depDerivDict[name][iBeg2:iFin2] += item[0]*dervDict2[item[1]]
                for iPO in dIdPO:
                    if iPO in varylist:
                        dMdv[varylist.index(iPO)][iBeg:iFin] += dIdPO[iPO]*dervDict['int']
                        if Ka2:
                            dMdv[varylist.index(iPO)][iBeg2:iFin2] += dIdPO[iPO]*dervDict2['int']
                    elif iPO in dependentVars:
                        depDerivDict[iPO][iBeg:iFin] += dIdPO[iPO]*dervDict['int']
                        if Ka2:
                            depDerivDict[iPO][iBeg2:iFin2] += dIdPO[iPO]*dervDict2['int']
                for i,name in enumerate(['omega','chi','phi']):
                    aname = pfx+'SH '+name
                    if aname in varylist:
                        dMdv[varylist.index(aname)][iBeg:iFin] += dFdSA[i]*dervDict['int']
                        if Ka2:
                            dMdv[varylist.index(aname)][iBeg2:iFin2] += dFdSA[i]*dervDict2['int']
                    elif aname in dependentVars:
                        depDerivDict[aname][iBeg:iFin] += dFdSA[i]*dervDict['int']
                        if Ka2:
                            depDerivDict[aname][iBeg2:iFin2] += dFdSA[i]*dervDict2['int']
                for iSH in dFdODF:
                    if iSH in varylist:
                        dMdv[varylist.index(iSH)][iBeg:iFin] += dFdODF[iSH]*dervDict['int']
                        if Ka2:
                            dMdv[varylist.index(iSH)][iBeg2:iFin2] += dFdODF[iSH]*dervDict2['int']
                    elif iSH in dependentVars:
                        depDerivDict[iSH][iBeg:iFin] += dFdODF[iSH]*dervDict['int']
                        if Ka2:
                            depDerivDict[iSH][iBeg2:iFin2] += dFdODF[iSH]*dervDict2['int']
                cellDervNames = cellVaryDerv(pfx,SGData,dpdA)
                for name,dpdA in cellDervNames:
                    if name in varylist:
                        dMdv[varylist.index(name)][iBeg:iFin] += dpdA*dervDict['pos']
                        if Ka2:
                            dMdv[varylist.index(name)][iBeg2:iFin2] += dpdA*dervDict2['pos']
                    elif name in dependentVars:
                        depDerivDict[name][iBeg:iFin] += dpdA*dervDict['pos']
                        if Ka2:
                            depDerivDict[name][iBeg2:iFin2] += dpdA*dervDict2['pos']
                dDijDict = GetHStrainShiftDerv(refl,SGData,phfx)
                for name in dDijDict:
                    if name in varylist:
                        dMdv[varylist.index(name)][iBeg:iFin] += dDijDict[name]*dervDict['pos']
                        if Ka2:
                            dMdv[varylist.index(name)][iBeg2:iFin2] += dDijDict[name]*dervDict2['pos']
                    elif name in dependentVars:
                        depDerivDict[name][iBeg:iFin] += dDijDict[name]*dervDict['pos']
                        if Ka2:
                            depDerivDict[name][iBeg2:iFin2] += dDijDict[name]*dervDict2['pos']
                sigDict,gamDict = GetSampleSigGamDerv(refl,wave,G,GB,phfx,calcControls,parmDict)
                for name in gamDict:
                    if name in varylist:
                        dMdv[varylist.index(name)][iBeg:iFin] += gamDict[name]*dervDict['gam']
                        if Ka2:
                            dMdv[varylist.index(name)][iBeg2:iFin2] += gamDict[name]*dervDict2['gam']
                    elif name in dependentVars:
                        depDerivDict[name][iBeg:iFin] += gamDict[name]*dervDict['gam']
                        if Ka2:
                            depDerivDict[name][iBeg2:iFin2] += gamDict[name]*dervDict2['gam']
                for name in sigDict:
                    if name in varylist:
                        dMdv[varylist.index(name)][iBeg:iFin] += sigDict[name]*dervDict['sig']
                        if Ka2:
                            dMdv[varylist.index(name)][iBeg2:iFin2] += sigDict[name]*dervDict2['sig']
                    elif name in dependentVars:
                        depDerivDict[name][iBeg:iFin] += sigDict[name]*dervDict['sig']
                        if Ka2:
                            depDerivDict[name][iBeg2:iFin2] += sigDict[name]*dervDict2['sig']
                for name in ['BabA','BabU']:
                    if phfx+name in varylist:
                        dMdv[varylist.index(phfx+name)][iBeg:iFin] += dFdvDict[pfx+name][iref]*dervDict['int']*cw[iBeg:iFin]
                        if Ka2:
                            dMdv[varylist.index(phfx+name)][iBeg2:iFin2] += dFdvDict[pfx+name][iref]*dervDict2['int']*cw[iBeg2:iFin2]
                    elif phfx+name in dependentVars:                    
                        depDerivDict[phfx+name][iBeg:iFin] += dFdvDict[pfx+name][iref]*dervDict['int']*cw[iBeg:iFin]
                        if Ka2:
                            depDerivDict[phfx+name][iBeg2:iFin2] += dFdvDict[pfx+name][iref]*dervDict2['int']*cw[iBeg2:iFin2]                  
            elif 'T' in calcControls[hfx+'histType']:
                print 'TOF Undefined at present'
                raise Exception    #no TOF yet
            if not Phase['General'].get('doPawley'):
                #do atom derivatives -  for RB,F,X & U so far              
                corr = dervDict['int']/refl[9]
                if Ka2:
                    corr2 = dervDict2['int']/refl[9]
                for name in varylist+dependentVars:
                    if '::RBV;' in name:
                        pass
                    else:
                        try:
                            aname = name.split(pfx)[1][:2]
                            if aname not in ['Af','dA','AU','RB']: continue # skip anything not an atom or rigid body param
                        except IndexError:
                            continue
                    if name in varylist:
                        dMdv[varylist.index(name)][iBeg:iFin] += dFdvDict[name][iref]*corr
                        if Ka2:
                            dMdv[varylist.index(name)][iBeg2:iFin2] += dFdvDict[name][iref]*corr2
                    elif name in dependentVars:
                        depDerivDict[name][iBeg:iFin] += dFdvDict[name][iref]*corr
                        if Ka2:
                            depDerivDict[name][iBeg2:iFin2] += dFdvDict[name][iref]*corr2
#        print 'profile derv time: %.3fs'%(time.time()-time0)
    # now process derivatives in constraints
    G2mv.Dict2Deriv(varylist,depDerivDict,dMdv)
    return dMdv

def dervRefine(values,HistoPhases,parmDict,varylist,calcControls,pawleyLookup,dlg):
    '''Loop over histograms and compute derivatives of the fitting
    model (M) with respect to all parameters.  Results are returned in
    a Jacobian matrix (aka design matrix) of dimensions (n by m) where
    n is the number of parameters and m is the number of data
    points. This can exceed memory when m gets large. This routine is
    used when refinement derivatives are selected as "analtytic
    Jacobian" in Controls.

    :returns: Jacobian numpy.array dMdv for all histograms concatinated
    '''
    parmDict.update(zip(varylist,values))
    G2mv.Dict2Map(parmDict,varylist)
    Histograms,Phases,restraintDict,rigidbodyDict = HistoPhases
    nvar = len(varylist)
    dMdv = np.empty(0)
    histoList = Histograms.keys()
    histoList.sort()
    for histogram in histoList:
        if 'PWDR' in histogram[:4]:
            Histogram = Histograms[histogram]
            hId = Histogram['hId']
            hfx = ':%d:'%(hId)
            wtFactor = calcControls[hfx+'wtFactor']
            Limits = calcControls[hfx+'Limits']
            x,y,w,yc,yb,yd = Histogram['Data']
            W = wtFactor*w
            xB = np.searchsorted(x,Limits[0])
            xF = np.searchsorted(x,Limits[1])
            dMdvh = np.sqrt(W[xB:xF])*getPowderProfileDerv(parmDict,x[xB:xF],
                varylist,Histogram,Phases,rigidbodyDict,calcControls,pawleyLookup)
        elif 'HKLF' in histogram[:4]:
            Histogram = Histograms[histogram]
            nobs = Histogram['Residuals']['Nobs']
            phase = Histogram['Reflection Lists']
            Phase = Phases[phase]
            hId = Histogram['hId']
            hfx = ':%d:'%(hId)
            wtFactor = calcControls[hfx+'wtFactor']
            pfx = '%d::'%(Phase['pId'])
            phfx = '%d:%d:'%(Phase['pId'],hId)
            SGData = Phase['General']['SGData']
            A = [parmDict[pfx+'A%d'%(i)] for i in range(6)]
            G,g = G2lat.A2Gmat(A)       #recip & real metric tensors
            refList = Histogram['Data']
            dFdvDict = StructureFactorDerv(refList,G,hfx,pfx,SGData,calcControls,parmDict)
            ApplyRBModelDervs(dFdvDict,parmDict,rigidbodyDict,Phase)
            dMdvh = np.zeros((len(varylist),len(refList)))
            dependentVars = G2mv.GetDependentVars()
            depDerivDict = {}
            for j in dependentVars:
                depDerivDict[j] = np.zeros(shape=(len(refList)))
            if calcControls['F**2']:
                for iref,ref in enumerate(refList):
                    if ref[6] > 0:
                        dervCor,dervDict = SCExtinction(ref,phfx,hfx,pfx,calcControls,parmDict,varylist) #puts correction in refl[13]
                        w = 1.0/ref[6]
                        if w*ref[5] >= calcControls['minF/sig']:
                            for j,var in enumerate(varylist):
                                if var in dFdvDict:
                                    dMdvh[j][iref] = w*dFdvDict[var][iref]*parmDict[phfx+'Scale']*dervCor
                            for var in dependentVars:
                                if var in dFdvDict:
                                    depDerivDict[var][iref] = w*dFdvDict[var][iref]*parmDict[phfx+'Scale']*dervCor
                            if phfx+'Scale' in varylist:
                                dMdvh[varylist.index(phfx+'Scale')][iref] = w*ref[9]*dervCor
                            elif phfx+'Scale' in dependentVars:
                                depDerivDict[phfx+'Scale'][iref] = w*ref[9]*dervCor
                            for item in ['Ep','Es','Eg']:
                                if phfx+item in varylist:
                                    dMdvh[varylist.index(phfx+item)][iref] = w*dervDict[phfx+item]*parmDict[phfx+'Scale']
                                elif phfx+item in dependentVars:
                                    depDerivDict[phfx+item][iref] = w*dervDict[phfx+item]*parmDict[phfx+'Scale']
                            for item in ['BabA','BabU']:
                                if phfx+item in varylist:
                                    dMdvh[varylist.index(phfx+item)][iref] = w*dervCor*dFdvDict[pfx+item][iref]*parmDict[phfx+'Scale']
                                elif phfx+item in dependentVars:
                                    depDerivDict[phfx+item][iref] = w*dervCor*dFdvDict[pfx+item][iref]*parmDict[phfx+'Scale']
            else:
                for iref,ref in enumerate(refList):
                    if ref[5] > 0.:
                        dervCor,dervDict = SCExtinction(ref,phfx,hfx,pfx,calcControls,parmDict,varylist) #puts correction in refl[13]
                        Fo = np.sqrt(ref[5])
                        Fc = np.sqrt(ref[7])
                        w = 1.0/ref[6]
                        if 2.0*Fo*w*Fo >= calcControls['minF/sig']:
                            for j,var in enumerate(varylist):
                                if var in dFdvDict:
                                    dMdvh[j][iref] = w*dFdvDict[var][iref]*dervCor*parmDict[phfx+'Scale']
                            for var in dependentVars:
                                if var in dFdvDict:
                                    depDerivDict[var][iref] = w*dFdvDict[var][iref]*dervCor*parmDict[phfx+'Scale']
                            if phfx+'Scale' in varylist:
                                dMdvh[varylist.index(phfx+'Scale')][iref] = w*ref[9]*dervCor
                            elif phfx+'Scale' in dependentVars:
                                depDerivDict[phfx+'Scale'][iref] = w*ref[9]*dervCor                           
                            for item in ['Ep','Es','Eg']:
                                if phfx+item in varylist:
                                    dMdvh[varylist.index(phfx+item)][iref] = w*dervDict[phfx+item]*parmDict[phfx+'Scale']
                                elif phfx+item in dependentVars:
                                    depDerivDict[phfx+item][iref] = w*dervDict[phfx+item]*parmDict[phfx+'Scale']
                            for item in ['BabA','BabU']:
                                if phfx+item in varylist:
                                    dMdvh[varylist.index(phfx+item)][iref] = w*dervCor*dFdvDict[pfx+item][iref]*parmDict[phfx+'Scale']
                                elif phfx+item in dependentVars:
                                    depDerivDict[phfx+item][iref] = w*dFdvDict[pfx+item][iref]*parmDict[phfx+'Scale']*dervCor
            # now process derivatives in constraints
            G2mv.Dict2Deriv(varylist,depDerivDict,dMdvh)
        else:
            continue        #skip non-histogram entries
        if len(dMdv):
            dMdv = np.concatenate((dMdv.T,np.sqrt(wtFactor)*dMdvh.T)).T
        else:
            dMdv = np.sqrt(wtFactor)*dMdvh
            
    pNames,pVals,pWt = penaltyFxn(HistoPhases,parmDict,varylist)
    if np.any(pVals):
        dpdv = penaltyDeriv(pNames,pVals,HistoPhases,parmDict,varylist)
        dMdv = np.concatenate((dMdv.T,(np.sqrt(pWt)*dpdv).T)).T
        
    return dMdv

def HessRefine(values,HistoPhases,parmDict,varylist,calcControls,pawleyLookup,dlg):
    '''Loop over histograms and compute derivatives of the fitting
    model (M) with respect to all parameters.  For each histogram, the
    Jacobian matrix, dMdv, with dimensions (n by m) where n is the
    number of parameters and m is the number of data points *in the
    histogram*. The (n by n) Hessian is computed from each Jacobian
    and it is returned.  This routine is used when refinement
    derivatives are selected as "analtytic Hessian" in Controls.

    :returns: Vec,Hess where Vec is the least-squares vector and Hess is the Hessian
    '''
    'Needs a doc string'
    parmDict.update(zip(varylist,values))
    G2mv.Dict2Map(parmDict,varylist)
    Histograms,Phases,restraintDict,rigidbodyDict = HistoPhases
    ApplyRBModels(parmDict,Phases,rigidbodyDict)        #,Update=True??
    nvar = len(varylist)
    Hess = np.empty(0)
    histoList = Histograms.keys()
    histoList.sort()
    for histogram in histoList:
        if 'PWDR' in histogram[:4]:
            Histogram = Histograms[histogram]
            hId = Histogram['hId']
            hfx = ':%d:'%(hId)
            wtFactor = calcControls[hfx+'wtFactor']
            Limits = calcControls[hfx+'Limits']
            x,y,w,yc,yb,yd = Histogram['Data']
            W = wtFactor*w
            dy = y-yc
            xB = np.searchsorted(x,Limits[0])
            xF = np.searchsorted(x,Limits[1])
            dMdvh = getPowderProfileDerv(parmDict,x[xB:xF],
                varylist,Histogram,Phases,rigidbodyDict,calcControls,pawleyLookup)
            Wt = ma.sqrt(W[xB:xF])[np.newaxis,:]
            Dy = dy[xB:xF][np.newaxis,:]
            dMdvh *= Wt
            if dlg:
                dlg.Update(Histogram['Residuals']['wR'],newmsg='Hessian for histogram %d\nAll data Rw=%8.3f%s'%(hId,Histogram['Residuals']['wR'],'%'))[0]
            if len(Hess):
                Hess += np.inner(dMdvh,dMdvh)
                dMdvh *= Wt*Dy
                Vec += np.sum(dMdvh,axis=1)
            else:
                Hess = np.inner(dMdvh,dMdvh)
                dMdvh *= Wt*Dy
                Vec = np.sum(dMdvh,axis=1)
        elif 'HKLF' in histogram[:4]:
            Histogram = Histograms[histogram]
            nobs = Histogram['Residuals']['Nobs']
            phase = Histogram['Reflection Lists']
            Phase = Phases[phase]
            hId = Histogram['hId']
            hfx = ':%d:'%(hId)
            wtFactor = calcControls[hfx+'wtFactor']
            pfx = '%d::'%(Phase['pId'])
            phfx = '%d:%d:'%(Phase['pId'],hId)
            SGData = Phase['General']['SGData']
            A = [parmDict[pfx+'A%d'%(i)] for i in range(6)]
            G,g = G2lat.A2Gmat(A)       #recip & real metric tensors
            refList = Histogram['Data']
            time0 = time.time()
            dFdvDict = StructureFactorDerv(refList,G,hfx,pfx,SGData,calcControls,parmDict)  #accurate for powders!
            ApplyRBModelDervs(dFdvDict,parmDict,rigidbodyDict,Phase)
            dMdvh = np.zeros((len(varylist),len(refList)))
            dependentVars = G2mv.GetDependentVars()
            depDerivDict = {}
            for j in dependentVars:
                depDerivDict[j] = np.zeros(shape=(len(refList)))
            wdf = np.zeros(len(refList))
            if calcControls['F**2']:
                for iref,ref in enumerate(refList):
                    if ref[6] > 0:
                        dervCor,dervDict = SCExtinction(ref,phfx,hfx,pfx,calcControls,parmDict,varylist) #puts correction in refl[13]
                        w =  1.0/ref[6]
                        if w*ref[5] >= calcControls['minF/sig']:
                            wdf[iref] = w*(ref[5]-ref[7])
                            for j,var in enumerate(varylist):
                                if var in dFdvDict:
                                    dMdvh[j][iref] = w*dFdvDict[var][iref]*dervCor*parmDict[phfx+'Scale']
                            for var in dependentVars:
                                if var in dFdvDict:
                                    depDerivDict[var][iref] = w*dFdvDict[var][iref]*dervCor*parmDict[phfx+'Scale']
                            if phfx+'Scale' in varylist:
                                dMdvh[varylist.index(phfx+'Scale')][iref] = w*ref[9]*dervCor
                            elif phfx+'Scale' in dependentVars:
                                depDerivDict[phfx+'Scale'][iref] = w*ref[9]*dervCor
                            for item in ['Ep','Es','Eg']:
                                if phfx+item in varylist:
                                    dMdvh[varylist.index(phfx+item)][iref] = w*dervDict[phfx+item]*parmDict[phfx+'Scale']
                                elif phfx+item in dependentVars:
                                    depDerivDict[phfx+item][iref] = w*dervDict[phfx+item]*parmDict[phfx+'Scale']
                            for item in ['BabA','BabU']:
                                if phfx+item in varylist:
                                    dMdvh[varylist.index(phfx+item)][iref] = w*dFdvDict[pfx+item][iref]*parmDict[phfx+'Scale']*dervCor
                                elif phfx+item in dependentVars:
                                    depDerivDict[phfx+item][iref] = w*dFdvDict[pfx+item][iref]*parmDict[phfx+'Scale']*dervCor
            else:
                for iref,ref in enumerate(refList):
                    if ref[5] > 0.:
                        dervCor,dervDict = SCExtinction(ref,phfx,hfx,pfx,calcControls,parmDict,varylist) #puts correction in refl[13]
                        Fo = np.sqrt(ref[5])
                        Fc = np.sqrt(ref[7])
                        w = 1.0/ref[6]
                        if 2.0*Fo*w*Fo >= calcControls['minF/sig']:
                            wdf[iref] = 2.0*Fo*w*(Fo-Fc)
                            for j,var in enumerate(varylist):
                                if var in dFdvDict:
                                    dMdvh[j][iref] = w*dFdvDict[var][iref]*dervCor*parmDict[phfx+'Scale']
                            for var in dependentVars:
                                if var in dFdvDict:
                                    depDerivDict[var][iref] = w*dFdvDict[var][iref]*dervCor*parmDict[phfx+'Scale']
                            if phfx+'Scale' in varylist:
                                dMdvh[varylist.index(phfx+'Scale')][iref] = w*ref[9]*dervCor
                            elif phfx+'Scale' in dependentVars:
                                depDerivDict[phfx+'Scale'][iref] = w*ref[9]*dervCor                           
                            for item in ['Ep','Es','Eg']:
                                if phfx+item in varylist:
                                    dMdvh[varylist.index(phfx+item)][iref] = w*dervDict[phfx+item]*parmDict[phfx+'Scale']
                                elif phfx+item in dependentVars:
                                    depDerivDict[phfx+item][iref] = w*dervDict[phfx+item]*parmDict[phfx+'Scale']
                            for item in ['BabA','BabU']:
                                if phfx+item in varylist:
                                    dMdvh[varylist.index(phfx+item)][iref] = w*dFdvDict[pfx+item][iref]*parmDict[phfx+'Scale']*dervCor
                                elif phfx+item in dependentVars:
                                    depDerivDict[phfx+item][iref] = w*dFdvDict[pfx+item][iref]*parmDict[phfx+'Scale']*dervCor
            # now process derivatives in constraints
            G2mv.Dict2Deriv(varylist,depDerivDict,dMdvh)

            if dlg:
                dlg.Update(Histogram['Residuals']['wR'],newmsg='Hessian for histogram %d Rw=%8.3f%s'%(hId,Histogram['Residuals']['wR'],'%'))[0]
            if len(Hess):
                Vec += wtFactor*np.sum(dMdvh*wdf,axis=1)
                Hess += wtFactor*np.inner(dMdvh,dMdvh)
            else:
                Vec = wtFactor*np.sum(dMdvh*wdf,axis=1)
                Hess = wtFactor*np.inner(dMdvh,dMdvh)
        else:
            continue        #skip non-histogram entries
    pNames,pVals,pWt = penaltyFxn(HistoPhases,parmDict,varylist)
    if np.any(pVals):
        dpdv = penaltyDeriv(pNames,pVals,HistoPhases,parmDict,varylist)
        Vec += np.sum(dpdv*pWt*pVals,axis=1)
        Hess += np.inner(dpdv*pWt,dpdv)
    return Vec,Hess

def errRefine(values,HistoPhases,parmDict,varylist,calcControls,pawleyLookup,dlg):        
    'Needs a doc string'
    parmDict.update(zip(varylist,values))
    Values2Dict(parmDict, varylist, values)
    G2mv.Dict2Map(parmDict,varylist)
    Histograms,Phases,restraintDict,rigidbodyDict = HistoPhases
    M = np.empty(0)
    SumwYo = 0
    Nobs = 0
    ApplyRBModels(parmDict,Phases,rigidbodyDict)
    histoList = Histograms.keys()
    histoList.sort()
    for histogram in histoList:
        if 'PWDR' in histogram[:4]:
            Histogram = Histograms[histogram]
            hId = Histogram['hId']
            hfx = ':%d:'%(hId)
            wtFactor = calcControls[hfx+'wtFactor']
            Limits = calcControls[hfx+'Limits']
            x,y,w,yc,yb,yd = Histogram['Data']
            W = wtFactor*w
            yc *= 0.0                           #zero full calcd profiles
            yb *= 0.0
            yd *= 0.0
            xB = np.searchsorted(x,Limits[0])
            xF = np.searchsorted(x,Limits[1])
            Histogram['Residuals']['Nobs'] = ma.count(x[xB:xF])
            Nobs += Histogram['Residuals']['Nobs']
            Histogram['Residuals']['sumwYo'] = ma.sum(W[xB:xF]*y[xB:xF]**2)
            SumwYo += Histogram['Residuals']['sumwYo']
            yc[xB:xF],yb[xB:xF] = getPowderProfile(parmDict,x[xB:xF],
                varylist,Histogram,Phases,calcControls,pawleyLookup)
            yc[xB:xF] += yb[xB:xF]
            yd[xB:xF] = y[xB:xF]-yc[xB:xF]
            wdy = -ma.sqrt(W[xB:xF])*(yd[xB:xF])
            Histogram['Residuals']['R'] = min(100.,ma.sum(ma.abs(yd[xB:xF]))/ma.sum(y[xB:xF])*100.)
            Histogram['Residuals']['wR'] = min(100.,ma.sqrt(ma.sum(wdy**2)/Histogram['Residuals']['sumwYo'])*100.)
            sumYmB = ma.sum(ma.where(yc[xB:xF]!=yb[xB:xF],ma.abs(y[xB:xF]-yb[xB:xF]),0.))
            sumwYmB2 = ma.sum(ma.where(yc[xB:xF]!=yb[xB:xF],W[xB:xF]*(y[xB:xF]-yb[xB:xF])**2,0.))
            sumYB = ma.sum(ma.where(yc[xB:xF]!=yb[xB:xF],ma.abs(y[xB:xF]-yc[xB:xF])*ma.abs(y[xB:xF]-yb[xB:xF])/y[xB:xF],0.))
            sumwYB2 = ma.sum(ma.where(yc[xB:xF]!=yb[xB:xF],W[xB:xF]*(ma.abs(y[xB:xF]-yc[xB:xF])*ma.abs(y[xB:xF]-yb[xB:xF])/y[xB:xF])**2,0.))
            Histogram['Residuals']['Rb'] = min(100.,100.*sumYB/sumYmB)
            Histogram['Residuals']['wRb'] = min(100.,100.*ma.sqrt(sumwYB2/sumwYmB2))
            Histogram['Residuals']['wRmin'] = min(100.,100.*ma.sqrt(Histogram['Residuals']['Nobs']/Histogram['Residuals']['sumwYo']))
            if dlg:
                dlg.Update(Histogram['Residuals']['wR'],newmsg='For histogram %d Rw=%8.3f%s'%(hId,Histogram['Residuals']['wR'],'%'))[0]
            M = np.concatenate((M,wdy))
#end of PWDR processing
        elif 'HKLF' in histogram[:4]:
            Histogram = Histograms[histogram]
            phase = Histogram['Reflection Lists']
            Phase = Phases[phase]
            hId = Histogram['hId']
            hfx = ':%d:'%(hId)
            wtFactor = calcControls[hfx+'wtFactor']
            pfx = '%d::'%(Phase['pId'])
            phfx = '%d:%d:'%(Phase['pId'],hId)
            SGData = Phase['General']['SGData']
            A = [parmDict[pfx+'A%d'%(i)] for i in range(6)]
            G,g = G2lat.A2Gmat(A)       #recip & real metric tensors
            refList = Histogram['Data']
            time0 = time.time()
            StructureFactor(refList,G,hfx,pfx,SGData,calcControls,parmDict)
#            print 'sf-calc time: %.3f'%(time.time()-time0)
            df = np.zeros(len(refList))
            sumwYo = 0
            sumFo = 0
            sumFo2 = 0
            sumdF = 0
            sumdF2 = 0
            nobs = 0
            if calcControls['F**2']:
                for i,ref in enumerate(refList):
                    if ref[6] > 0:
                        SCExtinction(ref,phfx,hfx,pfx,calcControls,parmDict,varylist) #puts correction in refl[13]
                        w = 1.0/ref[6]
                        ref[7] = parmDict[phfx+'Scale']*ref[9]
                        ref[7] *= ref[13]                       #correct Fc^2 for extinction
                        ref[8] = ref[5]/parmDict[phfx+'Scale']
                        if w*ref[5] >= calcControls['minF/sig']:
                            sumFo2 += ref[5]
                            Fo = np.sqrt(ref[5])
                            sumFo += Fo
                            sumFo2 += ref[5]
                            sumdF += abs(Fo-np.sqrt(ref[7]))
                            sumdF2 += abs(ref[5]-ref[7])
                            nobs += 1
                            df[i] = -w*(ref[5]-ref[7])
                            sumwYo += (w*ref[5])**2
            else:
                for i,ref in enumerate(refList):
                    if ref[5] > 0.:
                        SCExtinction(ref,phfx,hfx,pfx,calcControls,parmDict,varylist) #puts correction in refl[13]
                        ref[7] = parmDict[phfx+'Scale']*ref[9]
                        ref[7] *= ref[13]                       #correct Fc^2 for extinction
                        Fo = np.sqrt(ref[5])
                        Fc = np.sqrt(ref[7])
                        w = 2.0*Fo/ref[6]
                        if w*Fo >= calcControls['minF/sig']:
                            sumFo += Fo
                            sumFo2 += ref[5]
                            sumdF += abs(Fo-Fc)
                            sumdF2 += abs(ref[5]-ref[7])
                            nobs += 1
                            df[i] = -w*(Fo-Fc)
                            sumwYo += (w*Fo)**2
            Histogram['Residuals']['Nobs'] = nobs
            Histogram['Residuals']['sumwYo'] = sumwYo
            SumwYo += sumwYo
            Histogram['Residuals']['wR'] = min(100.,np.sqrt(np.sum(df**2)/Histogram['Residuals']['sumwYo'])*100.)
            Histogram['Residuals'][phfx+'Rf'] = 100.*sumdF/sumFo
            Histogram['Residuals'][phfx+'Rf^2'] = 100.*sumdF2/sumFo2
            Histogram['Residuals'][phfx+'Nref'] = nobs
            Nobs += nobs
            if dlg:
                dlg.Update(Histogram['Residuals']['wR'],newmsg='For histogram %d Rw=%8.3f%s'%(hId,Histogram['Residuals']['wR'],'%'))[0]
            M = np.concatenate((M,wtFactor*df))
# end of HKLF processing
    Histograms['sumwYo'] = SumwYo
    Histograms['Nobs'] = Nobs
    Rw = min(100.,np.sqrt(np.sum(M**2)/SumwYo)*100.)
    if dlg:
        GoOn = dlg.Update(Rw,newmsg='%s%8.3f%s'%('All data Rw =',Rw,'%'))[0]
        if not GoOn:
            parmDict['saved values'] = values
            dlg.Destroy()
            raise Exception         #Abort!!
    pDict,pVals,pWt = penaltyFxn(HistoPhases,parmDict,varylist)
    if np.any(pVals):
        pSum = np.sum(pWt*pVals**2)
        print 'Penalty function: %.3f on %d terms'%(pSum,len(pVals))
        Nobs += len(pVals)
        M = np.concatenate((M,np.sqrt(pWt)*pVals))
    return M
                        
