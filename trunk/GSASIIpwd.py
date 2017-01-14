#/usr/bin/env python
# -*- coding: utf-8 -*-
'''
*GSASII powder calculation module*
==================================

'''
########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### SVN repository information ###################
import sys
import math
import time
import os
import subprocess as subp

import numpy as np
import numpy.linalg as nl
import numpy.ma as ma
import random as rand
from numpy.fft import ifft, fft, fftshift
import scipy.interpolate as si
import scipy.stats as st
import scipy.optimize as so

import GSASIIpath
GSASIIpath.SetVersionNumber("$Revision$")
import GSASIIlattice as G2lat
import GSASIIspc as G2spc
import GSASIIElem as G2elem
import GSASIImath as G2mth
import pypowder as pyd
try:
    import pydiffax as pyx
except ImportError:
    print 'pydiffax is not available for this platform - under develpment'

    
# trig functions in degrees
tand = lambda x: math.tan(x*math.pi/180.)
atand = lambda x: 180.*math.atan(x)/math.pi
atan2d = lambda y,x: 180.*math.atan2(y,x)/math.pi
cosd = lambda x: math.cos(x*math.pi/180.)
acosd = lambda x: 180.*math.acos(x)/math.pi
rdsq2d = lambda x,p: round(1.0/math.sqrt(x),p)
#numpy versions
npsind = lambda x: np.sin(x*np.pi/180.)
npasind = lambda x: 180.*np.arcsin(x)/math.pi
npcosd = lambda x: np.cos(x*math.pi/180.)
npacosd = lambda x: 180.*np.arccos(x)/math.pi
nptand = lambda x: np.tan(x*math.pi/180.)
npatand = lambda x: 180.*np.arctan(x)/np.pi
npatan2d = lambda y,x: 180.*np.arctan2(y,x)/np.pi
npT2stl = lambda tth, wave: 2.0*npsind(tth/2.0)/wave    #=d*
npT2q = lambda tth,wave: 2.0*np.pi*npT2stl(tth,wave)    #=2pi*d*
ateln2 = 8.0*math.log(2.0)

################################################################################
#### Powder utilities
################################################################################

def PhaseWtSum(G2frame,histo):
    '''
    Calculate sum of phase mass*shase fraction for PWDR data (exclude magnetic phases)
    
    :param G2frame: GSASII main frame structure
    :param str histo: histogram name
    :returns sum(scale*mass) for phases in histo
    '''
    Histograms,Phases = G2frame.GetUsedHistogramsAndPhasesfromTree()
    wtSum = 0.0
    for phase in Phases:
        if Phases[phase]['General']['Type'] != 'magnetic':
            if histo in Phases[phase]['Histograms']:
                mass = Phases[phase]['General']['Mass']
                phFr = Phases[phase]['Histograms'][histo]['Scale'][0]
                wtSum += mass*phFr
    return wtSum
    
################################################################################
#GSASII pdf calculation routines
################################################################################
        
def Transmission(Geometry,Abs,Diam):
    '''
    Calculate sample transmission

    :param str Geometry: one of 'Cylinder','Bragg-Brentano','Tilting flat plate in transmission','Fixed flat plate'
    :param float Abs: absorption coeff in cm-1
    :param float Diam: sample thickness/diameter in mm
    '''
    if 'Cylinder' in Geometry:      #Lobanov & Alte da Veiga for 2-theta = 0; beam fully illuminates sample
        MuR = Abs*Diam/20.0
        if MuR <= 3.0:
            T0 = 16/(3.*math.pi)
            T1 = -0.045780
            T2 = -0.02489
            T3 = 0.003045
            T = -T0*MuR-T1*MuR**2-T2*MuR**3-T3*MuR**4
            if T < -20.:
                return 2.06e-9
            else:
                return math.exp(T)
        else:
            T1 = 1.433902
            T2 = 0.013869+0.337894
            T3 = 1.933433+1.163198
            T4 = 0.044365-0.04259
            T = (T1-T4)/(1.0+T2*(MuR-3.0))**T3+T4
            return T/100.
    elif 'plate' in Geometry:
        MuR = Abs*Diam/10.
        return math.exp(-MuR)
    elif 'Bragg' in Geometry:
        return 0.0
        
def SurfaceRough(SRA,SRB,Tth):
    ''' Suortti (J. Appl. Cryst, 5,325-331, 1972) surface roughness correction
    :param float SRA: Suortti surface roughness parameter
    :param float SRB: Suortti surface roughness parameter
    :param float Tth: 2-theta(deg) - can be numpy array
    
    '''
    sth = npsind(Tth/2.)
    T1 = np.exp(-SRB/sth)
    T2 = SRA+(1.-SRA)*np.exp(-SRB)
    return (SRA+(1.-SRA)*T1)/T2
    
def SurfaceRoughDerv(SRA,SRB,Tth):
    ''' Suortti surface roughness correction derivatives
    :param float SRA: Suortti surface roughness parameter (dimensionless)
    :param float SRB: Suortti surface roughness parameter (dimensionless)
    :param float Tth: 2-theta(deg) - can be numpy array
    :return list: [dydSRA,dydSRB] derivatives to be used for intensity derivative
    '''
    sth = npsind(Tth/2.)
    T1 = np.exp(-SRB/sth)
    T2 = SRA+(1.-SRA)*np.exp(-SRB)
    Trans = (SRA+(1.-SRA)*T1)/T2
    dydSRA = ((1.-T1)*T2-(1.-np.exp(-SRB))*Trans)/T2**2
    dydSRB = ((SRA-1.)*T1*T2/sth-Trans*(SRA-T2))/T2**2
    return [dydSRA,dydSRB]

def Absorb(Geometry,MuR,Tth,Phi=0,Psi=0):
    '''Calculate sample absorption
    :param str Geometry: one of 'Cylinder','Bragg-Brentano','Tilting Flat Plate in transmission','Fixed flat plate'
    :param float MuR: absorption coeff * sample thickness/2 or radius
    :param Tth: 2-theta scattering angle - can be numpy array
    :param float Phi: flat plate tilt angle - future
    :param float Psi: flat plate tilt axis - future
    '''
    
    def muRunder3(MuR,Sth2):
        T0 = 16.0/(3.*np.pi)
        T1 = (25.99978-0.01911*Sth2**0.25)*np.exp(-0.024551*Sth2)+ \
            0.109561*np.sqrt(Sth2)-26.04556
        T2 = -0.02489-0.39499*Sth2+1.219077*Sth2**1.5- \
            1.31268*Sth2**2+0.871081*Sth2**2.5-0.2327*Sth2**3
        T3 = 0.003045+0.018167*Sth2-0.03305*Sth2**2
        Trns = -T0*MuR-T1*MuR**2-T2*MuR**3-T3*MuR**4
        return np.exp(Trns)
    
    def muRover3(MuR,Sth2):
        T1 = 1.433902+11.07504*Sth2-8.77629*Sth2*Sth2+ \
            10.02088*Sth2**3-3.36778*Sth2**4
        T2 = (0.013869-0.01249*Sth2)*np.exp(3.27094*Sth2)+ \
            (0.337894+13.77317*Sth2)/(1.0+11.53544*Sth2)**1.555039
        T3 = 1.933433/(1.0+23.12967*Sth2)**1.686715- \
            0.13576*np.sqrt(Sth2)+1.163198
        T4 = 0.044365-0.04259/(1.0+0.41051*Sth2)**148.4202
        Trns = (T1-T4)/(1.0+T2*(MuR-3.0))**T3+T4
        return Trns/100.
        
    Sth2 = npsind(Tth/2.0)**2
    if 'Cylinder' in Geometry:      #Lobanov & Alte da Veiga for 2-theta = 0; beam fully illuminates sample
        if 'array' in str(type(MuR)):
            MuRSTh2 = np.concatenate((MuR,Sth2))
            AbsCr = np.where(MuRSTh2[0]<=3.0,muRunder3(MuRSTh2[0],MuRSTh2[1]),muRover3(MuRSTh2[0],MuRSTh2[1]))
            return AbsCr
        else:
            if MuR <= 3.0:
                return muRunder3(MuR,Sth2)
            else:
                return muRover3(MuR,Sth2)
    elif 'Bragg' in Geometry:
        return 1.0
    elif 'Fixed' in Geometry: #assumes sample plane is perpendicular to incident beam
        # and only defined for 2theta < 90
        MuT = 2.*MuR
        T1 = np.exp(-MuT)
        T2 = np.exp(-MuT/npcosd(Tth))
        Tb = MuT-MuT/npcosd(Tth)
        return (T2-T1)/Tb
    elif 'Tilting' in Geometry: #assumes symmetric tilt so sample plane is parallel to diffraction vector
        MuT = 2.*MuR
        cth = npcosd(Tth/2.0)
        return np.exp(-MuT/cth)/cth
        
def AbsorbDerv(Geometry,MuR,Tth,Phi=0,Psi=0):
    'needs a doc string'
    dA = 0.001
    AbsP = Absorb(Geometry,MuR+dA,Tth,Phi,Psi)
    if MuR:
        AbsM = Absorb(Geometry,MuR-dA,Tth,Phi,Psi)
        return (AbsP-AbsM)/(2.0*dA)
    else:
        return (AbsP-1.)/dA
        
def Polarization(Pola,Tth,Azm=0.0):
    """   Calculate angle dependent x-ray polarization correction (not scaled correctly!)

    :param Pola: polarization coefficient e.g 1.0 fully polarized, 0.5 unpolarized
    :param Azm: azimuthal angle e.g. 0.0 in plane of polarization
    :param Tth: 2-theta scattering angle - can be numpy array
      which (if either) of these is "right"?
    :return: (pola, dpdPola)
      * pola = ((1-Pola)*npcosd(Azm)**2+Pola*npsind(Azm)**2)*npcosd(Tth)**2+ \
        (1-Pola)*npsind(Azm)**2+Pola*npcosd(Azm)**2
      * dpdPola: derivative needed for least squares

    """
    pola = ((1.0-Pola)*npcosd(Azm)**2+Pola*npsind(Azm)**2)*npcosd(Tth)**2+   \
        (1.0-Pola)*npsind(Azm)**2+Pola*npcosd(Azm)**2
    dpdPola = -npsind(Tth)**2*(npsind(Azm)**2-npcosd(Azm)**2)
    return pola,dpdPola
    
def Oblique(ObCoeff,Tth):
    'currently assumes detector is normal to beam'
    if ObCoeff:
        return (1.-ObCoeff)/(1.0-np.exp(np.log(ObCoeff)/npcosd(Tth)))
    else:
        return 1.0
                
def Ruland(RulCoff,wave,Q,Compton):
    'needs a doc string'
    C = 2.9978e8
    D = 1.5e-3
    hmc = 0.024262734687
    sinth2 = (Q*wave/(4.0*np.pi))**2
    dlam = (wave**2)*Compton*Q/C
    dlam_c = 2.0*hmc*sinth2-D*wave**2
    return 1.0/((1.0+dlam/RulCoff)*(1.0+(np.pi*dlam_c/(dlam+RulCoff))**2))
    
def LorchWeight(Q):
    'needs a doc string'
    return np.sin(np.pi*(Q[-1]-Q)/(2.0*Q[-1]))
            
def GetAsfMean(ElList,Sthl2):
    '''Calculate various scattering factor terms for PDF calcs

    :param dict ElList: element dictionary contains scattering factor coefficients, etc.
    :param np.array Sthl2: numpy array of sin theta/lambda squared values
    :returns: mean(f^2), mean(f)^2, mean(compton)
    '''
    sumNoAtoms = 0.0
    FF = np.zeros_like(Sthl2)
    FF2 = np.zeros_like(Sthl2)
    CF = np.zeros_like(Sthl2)
    for El in ElList:
        sumNoAtoms += ElList[El]['FormulaNo']
    for El in ElList:
        el = ElList[El]
        ff2 = (G2elem.ScatFac(el,Sthl2)+el['fp'])**2+el['fpp']**2
        cf = G2elem.ComptonFac(el,Sthl2)
        FF += np.sqrt(ff2)*el['FormulaNo']/sumNoAtoms
        FF2 += ff2*el['FormulaNo']/sumNoAtoms
        CF += cf*el['FormulaNo']/sumNoAtoms
    return FF2,FF**2,CF
    
def GetNumDensity(ElList,Vol):
    'needs a doc string'
    sumNoAtoms = 0.0
    for El in ElList:
        sumNoAtoms += ElList[El]['FormulaNo']
    return sumNoAtoms/Vol
           
def CalcPDF(data,inst,limits,xydata):
    '''Computes I(Q), S(Q) & G(r) from Sample, Bkg, etc. diffraction patterns loaded into
    dict xydata; results are placed in xydata.
    Calculation parameters are found in dicts data and inst and list limits.
    The return value is at present an empty list.
    '''
    auxPlot = []
    import copy
    import scipy.fftpack as ft
    Ibeg = np.searchsorted(xydata['Sample'][1][0],limits[0])
    Ifin = np.searchsorted(xydata['Sample'][1][0],limits[1])+1
    #subtract backgrounds - if any & use PWDR limits
#    GSASIIpath.IPyBreak()
    IofQ = copy.deepcopy(xydata['Sample'])
    IofQ[1] = np.array(IofQ[1])[:,Ibeg:Ifin]
    if data['Sample Bkg.']['Name']:
        IofQ[1][1] += (xydata['Sample Bkg.'][1][1][Ibeg:Ifin]+
            data['Sample Bkg.']['Add'])*data['Sample Bkg.']['Mult']
    if data['Container']['Name']:
        xycontainer = (xydata['Container'][1][1]+data['Container']['Add'])*data['Container']['Mult']
        if data['Container Bkg.']['Name']:
            xycontainer += (xydata['Container Bkg.'][1][1][Ibeg:Ifin]+
                data['Container Bkg.']['Add'])*data['Container Bkg.']['Mult']
        IofQ[1][1] += xycontainer[Ibeg:Ifin]
    data['IofQmin'] = IofQ[1][1][Ifin-1]
    IofQ[1][1] -= data.get('Flat Bkg',0.)
    #get element data & absorption coeff.
    ElList = data['ElList']
    Abs = G2lat.CellAbsorption(ElList,data['Form Vol'])
    #Apply angle dependent corrections
    Tth = IofQ[1][0]
    MuR = Abs*data['Diam']/20.0
    IofQ[1][1] /= Absorb(data['Geometry'],MuR,Tth)
    if 'X' in inst['Type'][0]:
        IofQ[1][1] /= Polarization(inst['Polariz.'][1],Tth,Azm=inst['Azimuth'][1])[0]
    if data['DetType'] == 'Image plate':
        IofQ[1][1] *= Oblique(data['ObliqCoeff'],Tth)
    XY = IofQ[1]    
    #convert to Q
#    nQpoints = len(XY[0])     #points for Q interpolation
    nQpoints = 5000
    if 'C' in inst['Type'][0]:
        wave = G2mth.getWave(inst)
        minQ = npT2q(Tth[0],wave)
        maxQ = npT2q(Tth[-1],wave)    
        Qpoints = np.linspace(0.,maxQ,nQpoints,endpoint=True)
        dq = Qpoints[1]-Qpoints[0]
        XY[0] = npT2q(XY[0],wave)
    elif 'T' in inst['Type'][0]:
        difC = inst['difC'][1]
        minQ = 2.*np.pi*difC/Tth[-1]
        maxQ = 2.*np.pi*difC/Tth[0]
        Qpoints = np.linspace(0.,maxQ,nQpoints,endpoint=True)
        dq = Qpoints[1]-Qpoints[0]
        XY[0] = 2.*np.pi*difC/XY[0]
    Qdata = si.griddata(XY[0],XY[1],Qpoints,method='linear',fill_value=XY[1][0])    #interpolate I(Q)
    Qdata -= np.min(Qdata)*data['BackRatio']
    
    qLimits = data['QScaleLim']
    minQ = np.searchsorted(Qpoints,qLimits[0])
    maxQ = np.searchsorted(Qpoints,qLimits[1])
    newdata = []
    if len(IofQ) < 3:
        xydata['IofQ'] = [IofQ[0],[Qpoints,Qdata],'']
    else:
        xydata['IofQ'] = [IofQ[0],[Qpoints,Qdata],IofQ[2]]
    for item in xydata['IofQ'][1]:
        newdata.append(item[:maxQ])
    xydata['IofQ'][1] = newdata
    
    xydata['SofQ'] = copy.deepcopy(xydata['IofQ'])
    FFSq,SqFF,CF = GetAsfMean(ElList,(xydata['SofQ'][1][0]/(4.0*np.pi))**2)  #these are <f^2>,<f>^2,Cf
    Q = xydata['SofQ'][1][0]
#    auxPlot.append([Q,np.copy(CF),'CF-unCorr'])
    ruland = Ruland(data['Ruland'],wave,Q,CF)
#    auxPlot.append([Q,ruland,'Ruland'])      
    CF *= ruland
#    auxPlot.append([Q,CF,'CF-Corr'])
    scale = np.sum((FFSq+CF)[minQ:maxQ])/np.sum(xydata['SofQ'][1][1][minQ:maxQ])
    xydata['SofQ'][1][1] *= scale
    xydata['SofQ'][1][1] -= CF
    xydata['SofQ'][1][1] = xydata['SofQ'][1][1]/SqFF
    scale = len(xydata['SofQ'][1][1][minQ:maxQ])/np.sum(xydata['SofQ'][1][1][minQ:maxQ])
    xydata['SofQ'][1][1] *= scale
    xydata['FofQ'] = copy.deepcopy(xydata['SofQ'])
    xydata['FofQ'][1][1] = xydata['FofQ'][1][0]*(xydata['SofQ'][1][1]-1.0)
    if data['Lorch']:
        xydata['FofQ'][1][1] *= LorchWeight(Q)    
    xydata['GofR'] = copy.deepcopy(xydata['FofQ'])
    nR = len(xydata['GofR'][1][1])
    mul = int(round(2.*np.pi*nR/(data.get('Rmax',100.)*qLimits[1])))
    xydata['GofR'][1][0] = 2.*np.pi*np.linspace(0,nR,nR)/(mul*qLimits[1])
    xydata['GofR'][1][1] = -dq*np.imag(ft.fft(xydata['FofQ'][1][1],mul*nR)[:nR])
    if data.get('noRing',True):
        xydata['GofR'][1][1] = np.where(xydata['GofR'][1][0]<0.5,0.,xydata['GofR'][1][1])
    return auxPlot
    
def MakeRDF(RDFcontrols,background,inst,pwddata):
    import scipy.fftpack as ft
    import scipy.signal as signal
    auxPlot = []
    if 'C' in inst['Type'][0]:
        Tth = pwddata[0]
        wave = G2mth.getWave(inst)
        minQ = npT2q(Tth[0],wave)
        maxQ = npT2q(Tth[-1],wave)
        powQ = npT2q(Tth,wave)  
    elif 'T' in inst['Type'][0]:
        TOF = pwddata[0]
        difC = inst['difC'][1]
        minQ = 2.*np.pi*difC/TOF[-1]
        maxQ = 2.*np.pi*difC/TOF[0]
        powQ = 2.*np.pi*difC/TOF
    piDQ = np.pi/(maxQ-minQ)
    Qpoints = np.linspace(minQ,maxQ,len(pwddata[0]),endpoint=True)
    if RDFcontrols['UseObsCalc']:
        Qdata = si.griddata(powQ,pwddata[1]-pwddata[3],Qpoints,method=RDFcontrols['Smooth'],fill_value=0.)
    else:
        Qdata = si.griddata(powQ,pwddata[1]-pwddata[4],Qpoints,method=RDFcontrols['Smooth'],fill_value=pwddata[1][0])
    Qdata *= np.sin((Qpoints-minQ)*piDQ)/piDQ
    Qdata *= 0.5*np.sqrt(Qpoints)       #Qbin normalization
#    GSASIIpath.IPyBreak()
    dq = Qpoints[1]-Qpoints[0]
    nR = len(Qdata)
    R = 0.5*np.pi*np.linspace(0,nR,nR)/(4.*maxQ)
    iFin = np.searchsorted(R,RDFcontrols['maxR'])
    bBut,aBut = signal.butter(4,0.01)
    Qsmooth = signal.filtfilt(bBut,aBut,Qdata)
#    auxPlot.append([Qpoints,Qdata,'interpolate:'+RDFcontrols['Smooth']])
#    auxPlot.append([Qpoints,Qsmooth,'interpolate:'+RDFcontrols['Smooth']])
    DofR = dq*np.imag(ft.fft(Qsmooth,16*nR)[:nR])
    auxPlot.append([R[:iFin],DofR[:iFin],'D(R)'])    
    return auxPlot

################################################################################        
#GSASII peak fitting routines: Finger, Cox & Jephcoat model        
################################################################################

def factorize(num):
    ''' Provide prime number factors for integer num
    :returns: dictionary of prime factors (keys) & power for each (data)
    '''
    factors = {}
    orig = num

    # we take advantage of the fact that (i +1)**2 = i**2 + 2*i +1
    i, sqi = 2, 4
    while sqi <= num:
        while not num%i:
            num /= i
            factors[i] = factors.get(i, 0) + 1

        sqi += 2*i + 1
        i += 1

    if num != 1 and num != orig:
        factors[num] = factors.get(num, 0) + 1

    if factors:
        return factors
    else:
        return {num:1}          #a prime number!
            
def makeFFTsizeList(nmin=1,nmax=1023,thresh=15):
    ''' Provide list of optimal data sizes for FFT calculations

    :param int nmin: minimum data size >= 1
    :param int nmax: maximum data size > nmin
    :param int thresh: maximum prime factor allowed
    :Returns: list of data sizes where the maximum prime factor is < thresh
    ''' 
    plist = []
    nmin = max(1,nmin)
    nmax = max(nmin+1,nmax)
    for p in range(nmin,nmax):
        if max(factorize(p).keys()) < thresh:
            plist.append(p)
    return plist

np.seterr(divide='ignore')

# Normal distribution

# loc = mu, scale = std
_norm_pdf_C = 1./math.sqrt(2*math.pi)
class norm_gen(st.rv_continuous):
    'needs a doc string'
      
    def pdf(self,x,*args,**kwds):
        loc,scale=kwds['loc'],kwds['scale']
        x = (x-loc)/scale
        return np.exp(-x**2/2.0) * _norm_pdf_C / scale
        
norm = norm_gen(name='norm',longname='A normal',extradoc="""

Normal distribution

The location (loc) keyword specifies the mean.
The scale (scale) keyword specifies the standard deviation.

normal.pdf(x) = exp(-x**2/2)/sqrt(2*pi)
""")

## Cauchy

# median = loc

class cauchy_gen(st.rv_continuous):
    'needs a doc string'

    def pdf(self,x,*args,**kwds):
        loc,scale=kwds['loc'],kwds['scale']
        x = (x-loc)/scale
        return 1.0/np.pi/(1.0+x*x) / scale
        
cauchy = cauchy_gen(name='cauchy',longname='Cauchy',extradoc="""

Cauchy distribution

cauchy.pdf(x) = 1/(pi*(1+x**2))

This is the t distribution with one degree of freedom.
""")
    
    
#GSASII peak fitting routine: Finger, Cox & Jephcoat model        


class fcjde_gen(st.rv_continuous):
    """
    Finger-Cox-Jephcoat D(2phi,2th) function for S/L = H/L
    Ref: J. Appl. Cryst. (1994) 27, 892-900.

    :param x: array -1 to 1
    :param t: 2-theta position of peak
    :param s: sum(S/L,H/L); S: sample height, H: detector opening, 
      L: sample to detector opening distance
    :param dx: 2-theta step size in deg

    :returns: for fcj.pdf

     * T = x*dx+t
     * s = S/L+H/L
     * if x < 0::

        fcj.pdf = [1/sqrt({cos(T)**2/cos(t)**2}-1) - 1/s]/|cos(T)| 

     * if x >= 0: fcj.pdf = 0    
    """
    def _pdf(self,x,t,s,dx):
        T = dx*x+t
        ax2 = abs(npcosd(T))
        ax = ax2**2
        bx = npcosd(t)**2
        bx = np.where(ax>bx,bx,ax)
        fx = np.where(ax>bx,(np.sqrt(bx/(ax-bx))-1./s)/ax2,0.0)
        fx = np.where(fx > 0.,fx,0.0)
        return fx
             
    def pdf(self,x,*args,**kwds):
        loc=kwds['loc']
        return self._pdf(x-loc,*args)
        
fcjde = fcjde_gen(name='fcjde',shapes='t,s,dx')
                
def getWidthsCW(pos,sig,gam,shl):
    '''Compute the peak widths used for computing the range of a peak
    for constant wavelength data. On low-angle side, 50 FWHM are used, 
    on high-angle side 75 are used, low angle side extended for axial divergence
    (for peaks above 90 deg, these are reversed.)
    '''
    widths = [np.sqrt(sig)/100.,gam/100.]
    fwhm = 2.355*widths[0]+widths[1]
    fmin = 50.*(fwhm+shl*abs(npcosd(pos)))
    fmax = 75.0*fwhm
    if pos > 90:
        fmin,fmax = [fmax,fmin]          
    return widths,fmin,fmax
    
def getWidthsTOF(pos,alp,bet,sig,gam):
    '''Compute the peak widths used for computing the range of a peak
    for constant wavelength data. 50 FWHM are used on both sides each 
    extended by exponential coeff.
    '''
    widths = [np.sqrt(sig),gam]
    fwhm = 2.355*widths[0]+2.*widths[1]
    fmin = 50.*fwhm*(1.+1./alp)    
    fmax = 50.*fwhm*(1.+1./bet)
    return widths,fmin,fmax
    
def getFWHM(pos,Inst):
    '''Compute total FWHM from Thompson, Cox & Hastings (1987), J. Appl. Cryst. 20, 79-83
    via getgamFW(g,s).
    
    :param pos: float peak position in deg 2-theta or tof in musec
    :param Inst: dict instrument parameters
    
    :returns float: total FWHM of pseudoVoigt in deg or musec
    ''' 
    
    sig = lambda Th,U,V,W: np.sqrt(max(0.001,U*tand(Th)**2+V*tand(Th)+W))
    sigTOF = lambda dsp,S0,S1,S2,Sq:  S0+S1*dsp**2+S2*dsp**4+Sq/dsp**2
    gam = lambda Th,X,Y: (X/cosd(Th)+Y*tand(Th))
    gamTOF = lambda dsp,X,Y: X*dsp+Y*dsp**2
    if 'C' in Inst['Type'][0]:
        s = sig(pos/2.,Inst['U'][1],Inst['V'][1],Inst['W'][1])
        g = gam(pos/2.,Inst['X'][1],Inst['Y'][1])
        return getgamFW(g,s)/100.  #returns FWHM in deg
    else:
        dsp = pos/Inst['difC'][0]
        s = sigTOF(dsp,Inst['sig-0'][1],Inst['sig-1'][1],Inst['sig-2'][1],Inst['sig-q'][1])
        g = gamTOF(dsp,Inst['X'][1],Inst['Y'][1])
        return getgamFW(g,s)
    
def getgamFW(g,s):
    '''Compute total FWHM from Thompson, Cox & Hastings (1987), J. Appl. Cryst. 20, 79-83
    lambda fxn needs FWHM for both Gaussian & Lorentzian components
    
    :param g: float Lorentzian gamma = FWHM(L)
    :param s: float Gaussian sig
    
    :returns float: total FWHM of pseudoVoigt
    ''' 
    gamFW = lambda s,g: np.exp(np.log(s**5+2.69269*s**4*g+2.42843*s**3*g**2+4.47163*s**2*g**3+0.07842*s*g**4+g**5)/5.)
    return gamFW(2.35482*s,g)   #sqrt(8ln2)*sig = FWHM(G)
                
def getFCJVoigt(pos,intens,sig,gam,shl,xdata):    
    'needs a doc string'
    DX = xdata[1]-xdata[0]
    widths,fmin,fmax = getWidthsCW(pos,sig,gam,shl)
    x = np.linspace(pos-fmin,pos+fmin,256)
    dx = x[1]-x[0]
    Norm = norm.pdf(x,loc=pos,scale=widths[0])
    Cauchy = cauchy.pdf(x,loc=pos,scale=widths[1])
    arg = [pos,shl/57.2958,dx,]
    FCJ = fcjde.pdf(x,*arg,loc=pos)
    if len(np.nonzero(FCJ)[0])>5:
        z = np.column_stack([Norm,Cauchy,FCJ]).T
        Z = fft(z)
        Df = ifft(Z.prod(axis=0)).real
    else:
        z = np.column_stack([Norm,Cauchy]).T
        Z = fft(z)
        Df = fftshift(ifft(Z.prod(axis=0))).real
    Df /= np.sum(Df)
    Df = si.interp1d(x,Df,bounds_error=False,fill_value=0.0)
    return intens*Df(xdata)*DX/dx

def getBackground(pfx,parmDict,bakType,dataType,xdata):
    'needs a doc string'
    if 'T' in dataType:
        q = 2.*np.pi*parmDict[pfx+'difC']/xdata
    elif 'C' in dataType:
        wave = parmDict.get(pfx+'Lam',parmDict.get(pfx+'Lam1',1.0))
        q = npT2q(xdata,wave)
    yb = np.zeros_like(xdata)
    nBak = 0
    cw = np.diff(xdata)
    cw = np.append(cw,cw[-1])
    sumBk = [0.,0.,0]
    while True:
        key = pfx+'Back;'+str(nBak)
        if key in parmDict:
            nBak += 1
        else:
            break
#empirical functions
    if bakType in ['chebyschev','cosine']:
        dt = xdata[-1]-xdata[0]    
        for iBak in range(nBak):
            key = pfx+'Back;'+str(iBak)
            if bakType == 'chebyschev':
                ybi = parmDict[key]*(-1.+2.*(xdata-xdata[0])/dt)**iBak
            elif bakType == 'cosine':
                ybi = parmDict[key]*npcosd(180.*xdata*iBak/xdata[-1])
            yb += ybi
        sumBk[0] = np.sum(yb)
    elif bakType in ['Q^2 power series','Q^-2 power series']:
        QT = 1.
        yb += np.ones_like(yb)*parmDict[pfx+'Back;0']
        for iBak in range(nBak-1):
            key = pfx+'Back;'+str(iBak+1)
            if '-2' in bakType:
                QT *= (iBak+1)*q**-2
            else:
                QT *= q**2/(iBak+1)
            yb += QT*parmDict[key]
        sumBk[0] = np.sum(yb)
    elif bakType in ['lin interpolate','inv interpolate','log interpolate',]:
        if nBak == 1:
            yb = np.ones_like(xdata)*parmDict[pfx+'Back;0']
        elif nBak == 2:
            dX = xdata[-1]-xdata[0]
            T2 = (xdata-xdata[0])/dX
            T1 = 1.0-T2
            yb = parmDict[pfx+'Back;0']*T1+parmDict[pfx+'Back;1']*T2
        else:
            if bakType == 'lin interpolate':
                bakPos = np.linspace(xdata[0],xdata[-1],nBak,True)
            elif bakType == 'inv interpolate':
                bakPos = 1./np.linspace(1./xdata[-1],1./xdata[0],nBak,True)
            elif bakType == 'log interpolate':
                bakPos = np.exp(np.linspace(np.log(xdata[0]),np.log(xdata[-1]),nBak,True))
            bakPos[0] = xdata[0]
            bakPos[-1] = xdata[-1]
            bakVals = np.zeros(nBak)
            for i in range(nBak):
                bakVals[i] = parmDict[pfx+'Back;'+str(i)]
            bakInt = si.interp1d(bakPos,bakVals,'linear')
            yb = bakInt(ma.getdata(xdata))
        sumBk[0] = np.sum(yb)
#Debye function        
    if pfx+'difC' in parmDict:
        ff = 1.
    else:        
        try:
            wave = parmDict[pfx+'Lam']
        except KeyError:
            wave = parmDict[pfx+'Lam1']
        SQ = (q/(4.*np.pi))**2
        FF = G2elem.GetFormFactorCoeff('Si')[0]
        ff = np.array(G2elem.ScatFac(FF,SQ)[0])**2
    iD = 0        
    while True:
        try:
            dbA = parmDict[pfx+'DebyeA;'+str(iD)]
            dbR = parmDict[pfx+'DebyeR;'+str(iD)]
            dbU = parmDict[pfx+'DebyeU;'+str(iD)]
            ybi = ff*dbA*np.sin(q*dbR)*np.exp(-dbU*q**2)/(q*dbR)
            yb += ybi
            sumBk[1] += np.sum(ybi)
            iD += 1       
        except KeyError:
            break
#peaks
    iD = 0
    while True:
        try:
            pkP = parmDict[pfx+'BkPkpos;'+str(iD)]
            pkI = parmDict[pfx+'BkPkint;'+str(iD)]
            pkS = parmDict[pfx+'BkPksig;'+str(iD)]
            pkG = parmDict[pfx+'BkPkgam;'+str(iD)]
            if 'C' in dataType:
                Wd,fmin,fmax = getWidthsCW(pkP,pkS,pkG,.002)
            else: #'T'OF
                Wd,fmin,fmax = getWidthsTOF(pkP,1.,1.,pkS,pkG)
            iBeg = np.searchsorted(xdata,pkP-fmin)
            iFin = np.searchsorted(xdata,pkP+fmax)
            lenX = len(xdata)
            if not iBeg:
                iFin = np.searchsorted(xdata,pkP+fmax)
            elif iBeg == lenX:
                iFin = iBeg
            else:
                iFin = np.searchsorted(xdata,pkP+fmax)
            if 'C' in dataType:
                ybi = pkI*getFCJVoigt3(pkP,pkS,pkG,0.002,xdata[iBeg:iFin])
                yb[iBeg:iFin] += ybi
            else:   #'T'OF
                ybi = pkI*getEpsVoigt(pkP,1.,1.,pkS,pkG,xdata[iBeg:iFin])
                yb[iBeg:iFin] += ybi
            sumBk[2] += np.sum(ybi)
            iD += 1       
        except KeyError:
            break
        except ValueError:
            print '**** WARNING - backround peak '+str(iD)+' sigma is negative; fix & try again ****'
            break        
    return yb,sumBk
    
def getBackgroundDerv(hfx,parmDict,bakType,dataType,xdata):
    'needs a doc string'
    if 'T' in dataType:
        q = 2.*np.pi*parmDict[hfx+'difC']/xdata
    elif 'C' in dataType:
        wave = parmDict.get(hfx+'Lam',parmDict.get(hfx+'Lam1',1.0))
        q = 2.*np.pi*npsind(xdata/2.)/wave
    nBak = 0
    while True:
        key = hfx+'Back;'+str(nBak)
        if key in parmDict:
            nBak += 1
        else:
            break
    dydb = np.zeros(shape=(nBak,len(xdata)))
    dyddb = np.zeros(shape=(3*parmDict[hfx+'nDebye'],len(xdata)))
    dydpk = np.zeros(shape=(4*parmDict[hfx+'nPeaks'],len(xdata)))
    cw = np.diff(xdata)
    cw = np.append(cw,cw[-1])

    if bakType in ['chebyschev','cosine']:
        dt = xdata[-1]-xdata[0]    
        for iBak in range(nBak):    
            if bakType == 'chebyschev':
                dydb[iBak] = (-1.+2.*(xdata-xdata[0])/dt)**iBak
            elif bakType == 'cosine':
                dydb[iBak] = npcosd(180.*xdata*iBak/xdata[-1])
    elif bakType in ['Q^2 power series','Q^-2 power series']:
        QT = 1.
        dydb[0] = np.ones_like(xdata)
        for iBak in range(nBak-1):
            if '-2' in bakType:
                QT *= (iBak+1)*q**-2
            else:
                QT *= q**2/(iBak+1)
            dydb[iBak+1] = QT
    elif bakType in ['lin interpolate','inv interpolate','log interpolate',]:
        if nBak == 1:
            dydb[0] = np.ones_like(xdata)
        elif nBak == 2:
            dX = xdata[-1]-xdata[0]
            T2 = (xdata-xdata[0])/dX
            T1 = 1.0-T2
            dydb = [T1,T2]
        else:
            if bakType == 'lin interpolate':
                bakPos = np.linspace(xdata[0],xdata[-1],nBak,True)
            elif bakType == 'inv interpolate':
                bakPos = 1./np.linspace(1./xdata[-1],1./xdata[0],nBak,True)
            elif bakType == 'log interpolate':
                bakPos = np.exp(np.linspace(np.log(xdata[0]),np.log(xdata[-1]),nBak,True))
            bakPos[0] = xdata[0]
            bakPos[-1] = xdata[-1]
            for i,pos in enumerate(bakPos):
                if i == 0:
                    dydb[0] = np.where(xdata<bakPos[1],(bakPos[1]-xdata)/(bakPos[1]-bakPos[0]),0.)
                elif i == len(bakPos)-1:
                    dydb[i] = np.where(xdata>bakPos[-2],(bakPos[-1]-xdata)/(bakPos[-1]-bakPos[-2]),0.)
                else:
                    dydb[i] = np.where(xdata>bakPos[i],
                        np.where(xdata<bakPos[i+1],(bakPos[i+1]-xdata)/(bakPos[i+1]-bakPos[i]),0.),
                        np.where(xdata>bakPos[i-1],(xdata-bakPos[i-1])/(bakPos[i]-bakPos[i-1]),0.))
    if hfx+'difC' in parmDict:
        ff = 1.
    else:
        wave = parmDict.get(hfx+'Lam',parmDict.get(hfx+'Lam1',1.0))
        q = npT2q(xdata,wave)
        SQ = (q/(4*np.pi))**2
        FF = G2elem.GetFormFactorCoeff('Si')[0]
        ff = np.array(G2elem.ScatFac(FF,SQ)[0])*np.pi**2    #needs pi^2~10. for cw data (why?)
    iD = 0        
    while True:
        try:
            if hfx+'difC' in parmDict:
                q = 2*np.pi*parmDict[hfx+'difC']/xdata
            dbA = parmDict[hfx+'DebyeA;'+str(iD)]
            dbR = parmDict[hfx+'DebyeR;'+str(iD)]
            dbU = parmDict[hfx+'DebyeU;'+str(iD)]
            sqr = np.sin(q*dbR)/(q*dbR)
            cqr = np.cos(q*dbR)
            temp = np.exp(-dbU*q**2)
            dyddb[3*iD] = ff*sqr*temp
            dyddb[3*iD+1] = ff*dbA*temp*(cqr-sqr)/(dbR)
            dyddb[3*iD+2] = -ff*dbA*sqr*temp*q**2
            iD += 1
        except KeyError:
            break
    iD = 0
    while True:
        try:
            pkP = parmDict[hfx+'BkPkpos;'+str(iD)]
            pkI = parmDict[hfx+'BkPkint;'+str(iD)]
            pkS = parmDict[hfx+'BkPksig;'+str(iD)]
            pkG = parmDict[hfx+'BkPkgam;'+str(iD)]
            if 'C' in dataType:
                Wd,fmin,fmax = getWidthsCW(pkP,pkS,pkG,.002)
            else: #'T'OF
                Wd,fmin,fmax = getWidthsTOF(pkP,1.,1.,pkS,pkG)
            iBeg = np.searchsorted(xdata,pkP-fmin)
            iFin = np.searchsorted(xdata,pkP+fmax)
            lenX = len(xdata)
            if not iBeg:
                iFin = np.searchsorted(xdata,pkP+fmax)
            elif iBeg == lenX:
                iFin = iBeg
            else:
                iFin = np.searchsorted(xdata,pkP+fmax)
            if 'C' in dataType:
                Df,dFdp,dFds,dFdg,x = getdFCJVoigt3(pkP,pkS,pkG,.002,xdata[iBeg:iFin])
                dydpk[4*iD][iBeg:iFin] += 100.*cw[iBeg:iFin]*pkI*dFdp
                dydpk[4*iD+1][iBeg:iFin] += 100.*cw[iBeg:iFin]*Df
                dydpk[4*iD+2][iBeg:iFin] += 100.*cw[iBeg:iFin]*pkI*dFds
                dydpk[4*iD+3][iBeg:iFin] += 100.*cw[iBeg:iFin]*pkI*dFdg
            else:   #'T'OF
                Df,dFdp,x,x,dFds,dFdg = getdEpsVoigt(pkP,1.,1.,pkS,pkG,xdata[iBeg:iFin])
                dydpk[4*iD][iBeg:iFin] += pkI*dFdp
                dydpk[4*iD+1][iBeg:iFin] += Df
                dydpk[4*iD+2][iBeg:iFin] += pkI*dFds
                dydpk[4*iD+3][iBeg:iFin] += pkI*dFdg
            iD += 1       
        except KeyError:
            break
        except ValueError:
            print '**** WARNING - backround peak '+str(iD)+' sigma is negative; fix & try again ****'
            break        
    return dydb,dyddb,dydpk

#use old fortran routine
def getFCJVoigt3(pos,sig,gam,shl,xdata):
    'needs a doc string'
    
    Df = pyd.pypsvfcj(len(xdata),xdata-pos,pos,sig,gam,shl)
#    Df = pyd.pypsvfcjo(len(xdata),xdata-pos,pos,sig,gam,shl)
    Df /= np.sum(Df)
    return Df

def getdFCJVoigt3(pos,sig,gam,shl,xdata):
    'needs a doc string'
    
    Df,dFdp,dFds,dFdg,dFdsh = pyd.pydpsvfcj(len(xdata),xdata-pos,pos,sig,gam,shl)
#    Df,dFdp,dFds,dFdg,dFdsh = pyd.pydpsvfcjo(len(xdata),xdata-pos,pos,sig,gam,shl)
    return Df,dFdp,dFds,dFdg,dFdsh

def getPsVoigt(pos,sig,gam,xdata):
    'needs a doc string'
    
    Df = pyd.pypsvoigt(len(xdata),xdata-pos,sig,gam)
    Df /= np.sum(Df)
    return Df

def getdPsVoigt(pos,sig,gam,xdata):
    'needs a doc string'
    
    Df,dFdp,dFds,dFdg = pyd.pydpsvoigt(len(xdata),xdata-pos,sig,gam)
    return Df,dFdp,dFds,dFdg

def getEpsVoigt(pos,alp,bet,sig,gam,xdata):
    'needs a doc string'
    Df = pyd.pyepsvoigt(len(xdata),xdata-pos,alp,bet,sig,gam)
    Df /= np.sum(Df)
    return Df  
    
def getdEpsVoigt(pos,alp,bet,sig,gam,xdata):
    'needs a doc string'
    Df,dFdp,dFda,dFdb,dFds,dFdg = pyd.pydepsvoigt(len(xdata),xdata-pos,alp,bet,sig,gam)
    return Df,dFdp,dFda,dFdb,dFds,dFdg   

def ellipseSize(H,Sij,GB):
    'needs a doc string'
    HX = np.inner(H.T,GB)
    lenHX = np.sqrt(np.sum(HX**2))
    Esize,Rsize = nl.eigh(G2lat.U6toUij(Sij))            
    R = np.inner(HX/lenHX,Rsize)*Esize         #want column length for hkl in crystal
    lenR = np.sqrt(np.sum(R**2))
    return lenR

def ellipseSizeDerv(H,Sij,GB):
    'needs a doc string'
    lenR = ellipseSize(H,Sij,GB)
    delt = 0.001
    dRdS = np.zeros(6)
    for i in range(6):
        Sij[i] -= delt
        lenM = ellipseSize(H,Sij,GB)
        Sij[i] += 2.*delt
        lenP = ellipseSize(H,Sij,GB)
        Sij[i] -= delt
        dRdS[i] = (lenP-lenM)/(2.*delt)
    return lenR,dRdS

def getHKLpeak(dmin,SGData,A,Inst=None):
    'needs a doc string'
    HKL = G2lat.GenHLaue(dmin,SGData,A)        
    HKLs = []
    for h,k,l,d in HKL:
        ext = G2spc.GenHKLf([h,k,l],SGData)[0]
        if not ext:
            if Inst == None:
                HKLs.append([h,k,l,d,0,-1])
            else:
                HKLs.append([h,k,l,d,G2lat.Dsp2pos(Inst,d),-1])
    return HKLs

def getHKLMpeak(dmin,Inst,SGData,SSGData,Vec,maxH,A):
    'needs a doc string'
    HKLs = []
    vec = np.array(Vec)
    vstar = np.sqrt(G2lat.calc_rDsq(vec,A))     #find extra needed for -n SS reflections
    dvec = 1./(maxH*vstar+1./dmin)
    HKL = G2lat.GenHLaue(dvec,SGData,A)        
    SSdH = [vec*h for h in range(-maxH,maxH+1)]
    SSdH = dict(zip(range(-maxH,maxH+1),SSdH))
    for h,k,l,d in HKL:
        ext = G2spc.GenHKLf([h,k,l],SGData)[0]
        if not ext and d >= dmin:
            HKLs.append([h,k,l,0,d,G2lat.Dsp2pos(Inst,d),-1])
        for dH in SSdH:
            if dH:
                DH = SSdH[dH]
                H = [h+DH[0],k+DH[1],l+DH[2]]
                d = float(1/np.sqrt(G2lat.calc_rDsq(H,A)))
                if d >= dmin:
                    HKLM = np.array([h,k,l,dH])
                    if G2spc.checkSSextc(HKLM,SSGData):
                        HKLs.append([h,k,l,dH,d,G2lat.Dsp2pos(Inst,d),-1])    
#    GSASIIpath.IPyBreak()
    return G2lat.sortHKLd(HKLs,True,True,True)

def getPeakProfile(dataType,parmDict,xdata,varyList,bakType):
    'needs a doc string'
    
    yb = getBackground('',parmDict,bakType,dataType,xdata)[0]
    yc = np.zeros_like(yb)
    cw = np.diff(xdata)
    cw = np.append(cw,cw[-1])
    if 'C' in dataType:
        shl = max(parmDict['SH/L'],0.002)
        Ka2 = False
        if 'Lam1' in parmDict.keys():
            Ka2 = True
            lamRatio = 360*(parmDict['Lam2']-parmDict['Lam1'])/(np.pi*parmDict['Lam1'])
            kRatio = parmDict['I(L2)/I(L1)']
        iPeak = 0
        while True:
            try:
                pos = parmDict['pos'+str(iPeak)]
                tth = (pos-parmDict['Zero'])
                intens = parmDict['int'+str(iPeak)]
                sigName = 'sig'+str(iPeak)
                if sigName in varyList:
                    sig = parmDict[sigName]
                else:
                    sig = G2mth.getCWsig(parmDict,tth)
                sig = max(sig,0.001)          #avoid neg sigma^2
                gamName = 'gam'+str(iPeak)
                if gamName in varyList:
                    gam = parmDict[gamName]
                else:
                    gam = G2mth.getCWgam(parmDict,tth)
                gam = max(gam,0.001)             #avoid neg gamma
                Wd,fmin,fmax = getWidthsCW(pos,sig,gam,shl)
                iBeg = np.searchsorted(xdata,pos-fmin)
                iFin = np.searchsorted(xdata,pos+fmin)
                if not iBeg+iFin:       #peak below low limit
                    iPeak += 1
                    continue
                elif not iBeg-iFin:     #peak above high limit
                    return yb+yc
                yc[iBeg:iFin] += intens*getFCJVoigt3(pos,sig,gam,shl,xdata[iBeg:iFin])
                if Ka2:
                    pos2 = pos+lamRatio*tand(pos/2.0)       # + 360/pi * Dlam/lam * tan(th)
                    iBeg = np.searchsorted(xdata,pos2-fmin)
                    iFin = np.searchsorted(xdata,pos2+fmin)
                    if iBeg-iFin:
                        yc[iBeg:iFin] += intens*kRatio*getFCJVoigt3(pos2,sig,gam,shl,xdata[iBeg:iFin])
                iPeak += 1
            except KeyError:        #no more peaks to process
                return yb+yc
    else:
        Pdabc = parmDict['Pdabc']
        difC = parmDict['difC']
        iPeak = 0
        while True:
            try:
                pos = parmDict['pos'+str(iPeak)]                
                tof = pos-parmDict['Zero']
                dsp = tof/difC
                intens = parmDict['int'+str(iPeak)]
                alpName = 'alp'+str(iPeak)
                if alpName in varyList:
                    alp = parmDict[alpName]
                else:
                    if len(Pdabc):
                        alp = np.interp(dsp,Pdabc[0],Pdabc[1])
                    else:
                        alp = G2mth.getTOFalpha(parmDict,dsp)
                alp = max(0.0001,alp)
                betName = 'bet'+str(iPeak)
                if betName in varyList:
                    bet = parmDict[betName]
                else:
                    if len(Pdabc):
                        bet = np.interp(dsp,Pdabc[0],Pdabc[2])
                    else:
                        bet = G2mth.getTOFbeta(parmDict,dsp)
                bet = max(0.0001,bet)
                sigName = 'sig'+str(iPeak)
                if sigName in varyList:
                    sig = parmDict[sigName]
                else:
                    sig = G2mth.getTOFsig(parmDict,dsp)
                gamName = 'gam'+str(iPeak)
                if gamName in varyList:
                    gam = parmDict[gamName]
                else:
                    gam = G2mth.getTOFgamma(parmDict,dsp)
                gam = max(gam,0.001)             #avoid neg gamma
                Wd,fmin,fmax = getWidthsTOF(pos,alp,bet,sig,gam)
                iBeg = np.searchsorted(xdata,pos-fmin)
                iFin = np.searchsorted(xdata,pos+fmax)
                lenX = len(xdata)
                if not iBeg:
                    iFin = np.searchsorted(xdata,pos+fmax)
                elif iBeg == lenX:
                    iFin = iBeg
                else:
                    iFin = np.searchsorted(xdata,pos+fmax)
                if not iBeg+iFin:       #peak below low limit
                    iPeak += 1
                    continue
                elif not iBeg-iFin:     #peak above high limit
                    return yb+yc
                yc[iBeg:iFin] += intens*getEpsVoigt(pos,alp,bet,sig,gam,xdata[iBeg:iFin])
                iPeak += 1
            except KeyError:        #no more peaks to process
                return yb+yc
            
def getPeakProfileDerv(dataType,parmDict,xdata,varyList,bakType):
    'needs a doc string'
# needs to return np.array([dMdx1,dMdx2,...]) in same order as varylist = backVary,insVary,peakVary order
    dMdv = np.zeros(shape=(len(varyList),len(xdata)))
    dMdb,dMddb,dMdpk = getBackgroundDerv('',parmDict,bakType,dataType,xdata)
    if 'Back;0' in varyList:            #background derivs are in front if present
        dMdv[0:len(dMdb)] = dMdb
    names = ['DebyeA','DebyeR','DebyeU']
    for name in varyList:
        if 'Debye' in name:
            parm,id = name.split(';')
            ip = names.index(parm)
            dMdv[varyList.index(name)] = dMddb[3*int(id)+ip]
    names = ['BkPkpos','BkPkint','BkPksig','BkPkgam']
    for name in varyList:
        if 'BkPk' in name:
            parm,id = name.split(';')
            ip = names.index(parm)
            dMdv[varyList.index(name)] = dMdpk[4*int(id)+ip]
    cw = np.diff(xdata)
    cw = np.append(cw,cw[-1])
    if 'C' in dataType:
        shl = max(parmDict['SH/L'],0.002)
        Ka2 = False
        if 'Lam1' in parmDict.keys():
            Ka2 = True
            lamRatio = 360*(parmDict['Lam2']-parmDict['Lam1'])/(np.pi*parmDict['Lam1'])
            kRatio = parmDict['I(L2)/I(L1)']
        iPeak = 0
        while True:
            try:
                pos = parmDict['pos'+str(iPeak)]
                tth = (pos-parmDict['Zero'])
                intens = parmDict['int'+str(iPeak)]
                sigName = 'sig'+str(iPeak)
                if sigName in varyList:
                    sig = parmDict[sigName]
                    dsdU = dsdV = dsdW = 0
                else:
                    sig = G2mth.getCWsig(parmDict,tth)
                    dsdU,dsdV,dsdW = G2mth.getCWsigDeriv(tth)
                sig = max(sig,0.001)          #avoid neg sigma
                gamName = 'gam'+str(iPeak)
                if gamName in varyList:
                    gam = parmDict[gamName]
                    dgdX = dgdY = 0
                else:
                    gam = G2mth.getCWgam(parmDict,tth)
                    dgdX,dgdY = G2mth.getCWgamDeriv(tth)
                gam = max(gam,0.001)             #avoid neg gamma
                Wd,fmin,fmax = getWidthsCW(pos,sig,gam,shl)
                iBeg = np.searchsorted(xdata,pos-fmin)
                iFin = np.searchsorted(xdata,pos+fmin)
                if not iBeg+iFin:       #peak below low limit
                    iPeak += 1
                    continue
                elif not iBeg-iFin:     #peak above high limit
                    break
                dMdpk = np.zeros(shape=(6,len(xdata)))
                dMdipk = getdFCJVoigt3(pos,sig,gam,shl,xdata[iBeg:iFin])
                for i in range(1,5):
                    dMdpk[i][iBeg:iFin] += 100.*cw[iBeg:iFin]*intens*dMdipk[i]
                dMdpk[0][iBeg:iFin] += 100.*cw[iBeg:iFin]*dMdipk[0]
                dervDict = {'int':dMdpk[0],'pos':dMdpk[1],'sig':dMdpk[2],'gam':dMdpk[3],'shl':dMdpk[4]}
                if Ka2:
                    pos2 = pos+lamRatio*tand(pos/2.0)       # + 360/pi * Dlam/lam * tan(th)
                    iBeg = np.searchsorted(xdata,pos2-fmin)
                    iFin = np.searchsorted(xdata,pos2+fmin)
                    if iBeg-iFin:
                        dMdipk2 = getdFCJVoigt3(pos2,sig,gam,shl,xdata[iBeg:iFin])
                        for i in range(1,5):
                            dMdpk[i][iBeg:iFin] += 100.*cw[iBeg:iFin]*intens*kRatio*dMdipk2[i]
                        dMdpk[0][iBeg:iFin] += 100.*cw[iBeg:iFin]*kRatio*dMdipk2[0]
                        dMdpk[5][iBeg:iFin] += 100.*cw[iBeg:iFin]*dMdipk2[0]
                        dervDict = {'int':dMdpk[0],'pos':dMdpk[1],'sig':dMdpk[2],'gam':dMdpk[3],'shl':dMdpk[4],'L1/L2':dMdpk[5]*intens}
                for parmName in ['pos','int','sig','gam']:
                    try:
                        idx = varyList.index(parmName+str(iPeak))
                        dMdv[idx] = dervDict[parmName]
                    except ValueError:
                        pass
                if 'U' in varyList:
                    dMdv[varyList.index('U')] += dsdU*dervDict['sig']
                if 'V' in varyList:
                    dMdv[varyList.index('V')] += dsdV*dervDict['sig']
                if 'W' in varyList:
                    dMdv[varyList.index('W')] += dsdW*dervDict['sig']
                if 'X' in varyList:
                    dMdv[varyList.index('X')] += dgdX*dervDict['gam']
                if 'Y' in varyList:
                    dMdv[varyList.index('Y')] += dgdY*dervDict['gam']
                if 'SH/L' in varyList:
                    dMdv[varyList.index('SH/L')] += dervDict['shl']         #problem here
                if 'I(L2)/I(L1)' in varyList:
                    dMdv[varyList.index('I(L2)/I(L1)')] += dervDict['L1/L2']
                iPeak += 1
            except KeyError:        #no more peaks to process
                break
    else:
        Pdabc = parmDict['Pdabc']
        difC = parmDict['difC']
        iPeak = 0
        while True:
            try:
                pos = parmDict['pos'+str(iPeak)]                
                tof = pos-parmDict['Zero']
                dsp = tof/difC
                intens = parmDict['int'+str(iPeak)]
                alpName = 'alp'+str(iPeak)
                if alpName in varyList:
                    alp = parmDict[alpName]
                else:
                    if len(Pdabc):
                        alp = np.interp(dsp,Pdabc[0],Pdabc[1])
                        dada0 = 0
                    else:
                        alp = G2mth.getTOFalpha(parmDict,dsp)
                        dada0 = G2mth.getTOFalphaDeriv(dsp)
                betName = 'bet'+str(iPeak)
                if betName in varyList:
                    bet = parmDict[betName]
                else:
                    if len(Pdabc):
                        bet = np.interp(dsp,Pdabc[0],Pdabc[2])
                        dbdb0 = dbdb1 = dbdb2 = 0
                    else:
                        bet = G2mth.getTOFbeta(parmDict,dsp)
                        dbdb0,dbdb1,dbdb2 = G2mth.getTOFbetaDeriv(dsp)
                sigName = 'sig'+str(iPeak)
                if sigName in varyList:
                    sig = parmDict[sigName]
                    dsds0 = dsds1 = dsds2 = dsds3 = 0
                else:
                    sig = G2mth.getTOFsig(parmDict,dsp)
                    dsds0,dsds1,dsds2,dsds3 = G2mth.getTOFsigDeriv(dsp)
                gamName = 'gam'+str(iPeak)
                if gamName in varyList:
                    gam = parmDict[gamName]
                    dsdX = dsdY = 0
                else:
                    gam = G2mth.getTOFgamma(parmDict,dsp)
                    dsdX,dsdY = G2mth.getTOFgammaDeriv(dsp)
                gam = max(gam,0.001)             #avoid neg gamma
                Wd,fmin,fmax = getWidthsTOF(pos,alp,bet,sig,gam)
                iBeg = np.searchsorted(xdata,pos-fmin)
                lenX = len(xdata)
                if not iBeg:
                    iFin = np.searchsorted(xdata,pos+fmax)
                elif iBeg == lenX:
                    iFin = iBeg
                else:
                    iFin = np.searchsorted(xdata,pos+fmax)
                if not iBeg+iFin:       #peak below low limit
                    iPeak += 1
                    continue
                elif not iBeg-iFin:     #peak above high limit
                    break
                dMdpk = np.zeros(shape=(7,len(xdata)))
                dMdipk = getdEpsVoigt(pos,alp,bet,sig,gam,xdata[iBeg:iFin])
                for i in range(1,6):
                    dMdpk[i][iBeg:iFin] += intens*cw[iBeg:iFin]*dMdipk[i]
                dMdpk[0][iBeg:iFin] += cw[iBeg:iFin]*dMdipk[0]
                dervDict = {'int':dMdpk[0],'pos':dMdpk[1],'alp':dMdpk[2],'bet':dMdpk[3],'sig':dMdpk[4],'gam':dMdpk[5]}
                for parmName in ['pos','int','alp','bet','sig','gam']:
                    try:
                        idx = varyList.index(parmName+str(iPeak))
                        dMdv[idx] = dervDict[parmName]
                    except ValueError:
                        pass
                if 'alpha' in varyList:
                    dMdv[varyList.index('alpha')] += dada0*dervDict['alp']
                if 'beta-0' in varyList:
                    dMdv[varyList.index('beta-0')] += dbdb0*dervDict['bet']
                if 'beta-1' in varyList:
                    dMdv[varyList.index('beta-1')] += dbdb1*dervDict['bet']
                if 'beta-q' in varyList:
                    dMdv[varyList.index('beta-q')] += dbdb2*dervDict['bet']
                if 'sig-0' in varyList:
                    dMdv[varyList.index('sig-0')] += dsds0*dervDict['sig']
                if 'sig-1' in varyList:
                    dMdv[varyList.index('sig-1')] += dsds1*dervDict['sig']
                if 'sig-2' in varyList:
                    dMdv[varyList.index('sig-2')] += dsds2*dervDict['sig']
                if 'sig-q' in varyList:
                    dMdv[varyList.index('sig-q')] += dsds3*dervDict['sig']
                if 'X' in varyList:
                    dMdv[varyList.index('X')] += dsdX*dervDict['gam']
                if 'Y' in varyList:
                    dMdv[varyList.index('Y')] += dsdY*dervDict['gam']         #problem here
                iPeak += 1
            except KeyError:        #no more peaks to process
                break
    return dMdv
        
def Dict2Values(parmdict, varylist):
    '''Use before call to leastsq to setup list of values for the parameters 
    in parmdict, as selected by key in varylist'''
    return [parmdict[key] for key in varylist] 
    
def Values2Dict(parmdict, varylist, values):
    ''' Use after call to leastsq to update the parameter dictionary with 
    values corresponding to keys in varylist'''
    parmdict.update(zip(varylist,values))
    
def SetBackgroundParms(Background):
    'needs a doc string'
    if len(Background) == 1:            # fix up old backgrounds
        Background.append({'nDebye':0,'debyeTerms':[]})
    bakType,bakFlag = Background[0][:2]
    backVals = Background[0][3:]
    backNames = ['Back;'+str(i) for i in range(len(backVals))]
    Debye = Background[1]           #also has background peaks stuff
    backDict = dict(zip(backNames,backVals))
    backVary = []
    if bakFlag:
        backVary = backNames

    backDict['nDebye'] = Debye['nDebye']
    debyeDict = {}
    debyeList = []
    for i in range(Debye['nDebye']):
        debyeNames = ['DebyeA;'+str(i),'DebyeR;'+str(i),'DebyeU;'+str(i)]
        debyeDict.update(dict(zip(debyeNames,Debye['debyeTerms'][i][::2])))
        debyeList += zip(debyeNames,Debye['debyeTerms'][i][1::2])
    debyeVary = []
    for item in debyeList:
        if item[1]:
            debyeVary.append(item[0])
    backDict.update(debyeDict)
    backVary += debyeVary 

    backDict['nPeaks'] = Debye['nPeaks']
    peaksDict = {}
    peaksList = []
    for i in range(Debye['nPeaks']):
        peaksNames = ['BkPkpos;'+str(i),'BkPkint;'+str(i),'BkPksig;'+str(i),'BkPkgam;'+str(i)]
        peaksDict.update(dict(zip(peaksNames,Debye['peaksList'][i][::2])))
        peaksList += zip(peaksNames,Debye['peaksList'][i][1::2])
    peaksVary = []
    for item in peaksList:
        if item[1]:
            peaksVary.append(item[0])
    backDict.update(peaksDict)
    backVary += peaksVary    
    return bakType,backDict,backVary
    
def DoCalibInst(IndexPeaks,Inst):
    
    def SetInstParms():
        dataType = Inst['Type'][0]
        insVary = []
        insNames = []
        insVals = []
        for parm in Inst:
            insNames.append(parm)
            insVals.append(Inst[parm][1])
            if parm in ['Lam','difC','difA','difB','Zero',]:
                if Inst[parm][2]:
                    insVary.append(parm)
        instDict = dict(zip(insNames,insVals))
        return dataType,instDict,insVary
        
    def GetInstParms(parmDict,Inst,varyList):
        for name in Inst:
            Inst[name][1] = parmDict[name]
        
    def InstPrint(Inst,sigDict):
        print 'Instrument Parameters:'
        if 'C' in Inst['Type'][0]:
            ptfmt = "%12.6f"
        else:
            ptfmt = "%12.3f"
        ptlbls = 'names :'
        ptstr =  'values:'
        sigstr = 'esds  :'
        for parm in Inst:
            if parm in  ['Lam','difC','difA','difB','Zero',]:
                ptlbls += "%s" % (parm.center(12))
                ptstr += ptfmt % (Inst[parm][1])
                if parm in sigDict:
                    sigstr += ptfmt % (sigDict[parm])
                else:
                    sigstr += 12*' '
        print ptlbls
        print ptstr
        print sigstr
        
    def errPeakPos(values,peakDsp,peakPos,peakWt,dataType,parmDict,varyList):
        parmDict.update(zip(varyList,values))
        return np.sqrt(peakWt)*(G2lat.getPeakPos(dataType,parmDict,peakDsp)-peakPos)

    peakPos = []
    peakDsp = []
    peakWt = []
    for peak,sig in zip(IndexPeaks[0],IndexPeaks[1]):
        if peak[2] and peak[3] and sig > 0.:
            peakPos.append(peak[0])
            peakDsp.append(peak[-1])    #d-calc
            peakWt.append(peak[-1]**2/sig**2)   #weight by d**2
    peakPos = np.array(peakPos)
    peakDsp = np.array(peakDsp)
    peakWt = np.array(peakWt)
    dataType,insDict,insVary = SetInstParms()
    parmDict = {}
    parmDict.update(insDict)
    varyList = insVary
    if not len(varyList):
        print '**** ERROR - nothing to refine! ****'
        return False
    while True:
        begin = time.time()
        values =  np.array(Dict2Values(parmDict, varyList))
        result = so.leastsq(errPeakPos,values,full_output=True,ftol=0.000001,
            args=(peakDsp,peakPos,peakWt,dataType,parmDict,varyList))
        ncyc = int(result[2]['nfev']/2)
        runtime = time.time()-begin    
        chisq = np.sum(result[2]['fvec']**2)
        Values2Dict(parmDict, varyList, result[0])
        GOF = chisq/(len(peakPos)-len(varyList))       #reduced chi^2
        print 'Number of function calls:',result[2]['nfev'],' Number of observations: ',len(peakPos),' Number of parameters: ',len(varyList)
        print 'calib time = %8.3fs, %8.3fs/cycle'%(runtime,runtime/ncyc)
        print 'chi**2 = %12.6g, reduced chi**2 = %6.2f'%(chisq,GOF)
        try:
            sig = np.sqrt(np.diag(result[1])*GOF)
            if np.any(np.isnan(sig)):
                print '*** Least squares aborted - some invalid esds possible ***'
            break                   #refinement succeeded - finish up!
        except ValueError:          #result[1] is None on singular matrix
            print '**** Refinement failed - singular matrix ****'
        
    sigDict = dict(zip(varyList,sig))
    GetInstParms(parmDict,Inst,varyList)
    InstPrint(Inst,sigDict)
    return True
            
def DoPeakFit(FitPgm,Peaks,Background,Limits,Inst,Inst2,data,prevVaryList=[],oneCycle=False,controls=None,dlg=None):
    '''Called to perform a peak fit, refining the selected items in the peak
    table as well as selected items in the background.

    :param str FitPgm: type of fit to perform. At present this is ignored.
    :param list Peaks: a list of peaks. Each peak entry is a list with 8 values:
      four values followed by a refine flag where the values are: position, intensity,
      sigma (Gaussian width) and gamma (Lorentzian width). From the Histogram/"Peak List"
      tree entry, dict item "peaks"
    :param list Background: describes the background. List with two items.
      Item 0 specifies a background model and coefficients. Item 1 is a dict.
      From the Histogram/Background tree entry.
    :param list Limits: min and max x-value to use
    :param dict Inst: Instrument parameters
    :param dict Inst2: more Instrument parameters
    :param numpy.array data: a 5xn array. data[0] is the x-values,
      data[1] is the y-values, data[2] are weight values, data[3], [4] and [5] are
      calc, background and difference intensities, respectively. 
    :param list prevVaryList: Used in sequential refinements to override the
      variable list. Defaults as an empty list.
    :param bool oneCycle: True if only one cycle of fitting should be performed
    :param dict controls: a dict specifying two values, Ftol = controls['min dM/M']
      and derivType = controls['deriv type']. If None default values are used. 
    :param wx.Dialog dlg: A dialog box that is updated with progress from the fit.
      Defaults to None, which means no updates are done. 
    '''
    def GetBackgroundParms(parmList,Background):
        iBak = 0
        while True:
            try:
                bakName = 'Back;'+str(iBak)
                Background[0][iBak+3] = parmList[bakName]
                iBak += 1
            except KeyError:
                break
        iDb = 0
        while True:
            names = ['DebyeA;','DebyeR;','DebyeU;']
            try:
                for i,name in enumerate(names):
                    val = parmList[name+str(iDb)]
                    Background[1]['debyeTerms'][iDb][2*i] = val
                iDb += 1
            except KeyError:
                break
        iDb = 0
        while True:
            names = ['BkPkpos;','BkPkint;','BkPksig;','BkPkgam;']
            try:
                for i,name in enumerate(names):
                    val = parmList[name+str(iDb)]
                    Background[1]['peaksList'][iDb][2*i] = val
                iDb += 1
            except KeyError:
                break
                
    def BackgroundPrint(Background,sigDict):
        print 'Background coefficients for',Background[0][0],'function'
        ptfmt = "%12.5f"
        ptstr =  'value: '
        sigstr = 'esd  : '
        for i,back in enumerate(Background[0][3:]):
            ptstr += ptfmt % (back)
            if Background[0][1]:
                prm = 'Back;'+str(i)
                if prm in sigDict:
                    sigstr += ptfmt % (sigDict[prm])
                else:
                    sigstr += " "*12
            if len(ptstr) > 75:
                print ptstr
                if Background[0][1]: print sigstr
                ptstr =  'value: '
                sigstr = 'esd  : '
        if len(ptstr) > 8:
            print ptstr
            if Background[0][1]: print sigstr

        if Background[1]['nDebye']:
            parms = ['DebyeA;','DebyeR;','DebyeU;']
            print 'Debye diffuse scattering coefficients'
            ptfmt = "%12.5f"
            print ' term       DebyeA       esd        DebyeR       esd        DebyeU        esd'
            for term in range(Background[1]['nDebye']):
                line = ' term %d'%(term)
                for ip,name in enumerate(parms):
                    line += ptfmt%(Background[1]['debyeTerms'][term][2*ip])
                    if name+str(term) in sigDict:
                        line += ptfmt%(sigDict[name+str(term)])
                    else:
                        line += " "*12
                print line
        if Background[1]['nPeaks']:
            print 'Coefficients for Background Peaks'
            ptfmt = "%15.3f"
            for j,pl in enumerate(Background[1]['peaksList']):
                names =  'peak %3d:'%(j+1)
                ptstr =  'values  :'
                sigstr = 'esds    :'
                for i,lbl in enumerate(['BkPkpos','BkPkint','BkPksig','BkPkgam']):
                    val = pl[2*i]
                    prm = lbl+";"+str(j)
                    names += '%15s'%(prm)
                    ptstr += ptfmt%(val)
                    if prm in sigDict:
                        sigstr += ptfmt%(sigDict[prm])
                    else:
                        sigstr += " "*15
                print names
                print ptstr
                print sigstr
                            
    def SetInstParms(Inst):
        dataType = Inst['Type'][0]
        insVary = []
        insNames = []
        insVals = []
        for parm in Inst:
            insNames.append(parm)
            insVals.append(Inst[parm][1])
            if parm in ['U','V','W','X','Y','SH/L','I(L2)/I(L1)','alpha',
                'beta-0','beta-1','beta-q','sig-0','sig-1','sig-2','sig-q',] and Inst[parm][2]:
                    insVary.append(parm)
        instDict = dict(zip(insNames,insVals))
        instDict['X'] = max(instDict['X'],0.01)
        instDict['Y'] = max(instDict['Y'],0.01)
        if 'SH/L' in instDict:
            instDict['SH/L'] = max(instDict['SH/L'],0.002)
        return dataType,instDict,insVary
        
    def GetInstParms(parmDict,Inst,varyList,Peaks):
        for name in Inst:
            Inst[name][1] = parmDict[name]
        iPeak = 0
        while True:
            try:
                sigName = 'sig'+str(iPeak)
                pos = parmDict['pos'+str(iPeak)]
                if sigName not in varyList:
                    if 'C' in Inst['Type'][0]:
                        parmDict[sigName] = G2mth.getCWsig(parmDict,pos)
                    else:
                        dsp = G2lat.Pos2dsp(Inst,pos)
                        parmDict[sigName] = G2mth.getTOFsig(parmDict,dsp)
                gamName = 'gam'+str(iPeak)
                if gamName not in varyList:
                    if 'C' in Inst['Type'][0]:
                        parmDict[gamName] = G2mth.getCWgam(parmDict,pos)
                    else:
                        dsp = G2lat.Pos2dsp(Inst,pos)
                        parmDict[gamName] = G2mth.getTOFgamma(parmDict,dsp)
                iPeak += 1
            except KeyError:
                break
        
    def InstPrint(Inst,sigDict):
        print 'Instrument Parameters:'
        ptfmt = "%12.6f"
        ptlbls = 'names :'
        ptstr =  'values:'
        sigstr = 'esds  :'
        for parm in Inst:
            if parm in  ['U','V','W','X','Y','SH/L','I(L2)/I(L1)','alpha',
                'beta-0','beta-1','beta-q','sig-0','sig-1','sig-2','sig-q',]:
                ptlbls += "%s" % (parm.center(12))
                ptstr += ptfmt % (Inst[parm][1])
                if parm in sigDict:
                    sigstr += ptfmt % (sigDict[parm])
                else:
                    sigstr += 12*' '
        print ptlbls
        print ptstr
        print sigstr

    def SetPeaksParms(dataType,Peaks):
        peakNames = []
        peakVary = []
        peakVals = []
        if 'C' in dataType:
            names = ['pos','int','sig','gam']
        else:
            names = ['pos','int','alp','bet','sig','gam']
        for i,peak in enumerate(Peaks):
            for j,name in enumerate(names):
                peakVals.append(peak[2*j])
                parName = name+str(i)
                peakNames.append(parName)
                if peak[2*j+1]:
                    peakVary.append(parName)
        return dict(zip(peakNames,peakVals)),peakVary
                
    def GetPeaksParms(Inst,parmDict,Peaks,varyList):
        if 'C' in Inst['Type'][0]:
            names = ['pos','int','sig','gam']
        else:   #'T'
            names = ['pos','int','alp','bet','sig','gam']
        for i,peak in enumerate(Peaks):
            pos = parmDict['pos'+str(i)]
            if 'difC' in Inst:
                dsp = pos/Inst['difC'][1]
            for j in range(len(names)):
                parName = names[j]+str(i)
                if parName in varyList:
                    peak[2*j] = parmDict[parName]
                elif 'alpha' in parName:
                    peak[2*j] = parmDict['alpha']/dsp
                elif 'beta' in parName:
                    peak[2*j] = G2mth.getTOFbeta(parmDict,dsp)
                elif 'sig' in parName:
                    if 'C' in Inst['Type'][0]:
                        peak[2*j] = G2mth.getCWsig(parmDict,pos)
                    else:
                        peak[2*j] = G2mth.getTOFsig(parmDict,dsp)
                elif 'gam' in parName:
                    if 'C' in Inst['Type'][0]:
                        peak[2*j] = G2mth.getCWgam(parmDict,pos)
                    else:
                        peak[2*j] = G2mth.getTOFgamma(parmDict,dsp)
                        
    def PeaksPrint(dataType,parmDict,sigDict,varyList):
        print 'Peak coefficients:'
        if 'C' in dataType:
            names = ['pos','int','sig','gam']
        else:   #'T'
            names = ['pos','int','alp','bet','sig','gam']            
        head = 13*' '
        for name in names:
            if name in ['alp','bet']:
                head += name.center(8)+'esd'.center(8)
            else:
                head += name.center(10)+'esd'.center(10)
        print head
        if 'C' in dataType:
            ptfmt = {'pos':"%10.5f",'int':"%10.1f",'sig':"%10.3f",'gam':"%10.3f"}
        else:
            ptfmt = {'pos':"%10.2f",'int':"%10.4f",'alp':"%8.3f",'bet':"%8.5f",'sig':"%10.3f",'gam':"%10.3f"}
        for i,peak in enumerate(Peaks):
            ptstr =  ':'
            for j in range(len(names)):
                name = names[j]
                parName = name+str(i)
                ptstr += ptfmt[name] % (parmDict[parName])
                if parName in varyList:
                    ptstr += ptfmt[name] % (sigDict[parName])
                else:
                    if name in ['alp','bet']:
                        ptstr += 8*' '
                    else:
                        ptstr += 10*' '
            print '%s'%(('Peak'+str(i+1)).center(8)),ptstr
                
    def devPeakProfile(values,xdata,ydata, weights,dataType,parmdict,varylist,bakType,dlg):
        parmdict.update(zip(varylist,values))
        return np.sqrt(weights)*getPeakProfileDerv(dataType,parmdict,xdata,varylist,bakType)
            
    def errPeakProfile(values,xdata,ydata,weights,dataType,parmdict,varylist,bakType,dlg):        
        parmdict.update(zip(varylist,values))
        M = np.sqrt(weights)*(getPeakProfile(dataType,parmdict,xdata,varylist,bakType)-ydata)
        Rwp = min(100.,np.sqrt(np.sum(M**2)/np.sum(weights*ydata**2))*100.)
        if dlg:
            GoOn = dlg.Update(Rwp,newmsg='%s%8.3f%s'%('Peak fit Rwp =',Rwp,'%'))[0]
            if not GoOn:
                return -M           #abort!!
        return M
        
    if controls:
        Ftol = controls['min dM/M']
    else:
        Ftol = 0.0001
    if oneCycle:
        Ftol = 1.0
    x,y,w,yc,yb,yd = data               #these are numpy arrays!
    yc *= 0.                            #set calcd ones to zero
    yb *= 0.
    yd *= 0.
    xBeg = np.searchsorted(x,Limits[0])
    xFin = np.searchsorted(x,Limits[1])
    bakType,bakDict,bakVary = SetBackgroundParms(Background)
    dataType,insDict,insVary = SetInstParms(Inst)
    peakDict,peakVary = SetPeaksParms(Inst['Type'][0],Peaks)
    parmDict = {}
    parmDict.update(bakDict)
    parmDict.update(insDict)
    parmDict.update(peakDict)
    parmDict['Pdabc'] = []      #dummy Pdabc
    parmDict.update(Inst2)      #put in real one if there
    if prevVaryList:
        varyList = prevVaryList[:]
    else:
        varyList = bakVary+insVary+peakVary
    fullvaryList = varyList[:]
    while True:
        begin = time.time()
        values =  np.array(Dict2Values(parmDict, varyList))
        Rvals = {}
        badVary = []
        result = so.leastsq(errPeakProfile,values,Dfun=devPeakProfile,full_output=True,ftol=Ftol,col_deriv=True,
               args=(x[xBeg:xFin],y[xBeg:xFin],w[xBeg:xFin],dataType,parmDict,varyList,bakType,dlg))
        ncyc = int(result[2]['nfev']/2)
        runtime = time.time()-begin    
        chisq = np.sum(result[2]['fvec']**2)
        Values2Dict(parmDict, varyList, result[0])
        Rvals['Rwp'] = np.sqrt(chisq/np.sum(w[xBeg:xFin]*y[xBeg:xFin]**2))*100.      #to %
        Rvals['GOF'] = chisq/(xFin-xBeg-len(varyList))       #reduced chi^2
        print 'Number of function calls:',result[2]['nfev'],' Number of observations: ',xFin-xBeg,' Number of parameters: ',len(varyList)
        if ncyc:
            print 'fitpeak time = %8.3fs, %8.3fs/cycle'%(runtime,runtime/ncyc)
        print 'Rwp = %7.2f%%, chi**2 = %12.6g, reduced chi**2 = %6.2f'%(Rvals['Rwp'],chisq,Rvals['GOF'])
        sig = [0]*len(varyList)
        if len(varyList) == 0: break  # if nothing was refined
        try:
            sig = np.sqrt(np.diag(result[1])*Rvals['GOF'])
            if np.any(np.isnan(sig)):
                print '*** Least squares aborted - some invalid esds possible ***'
            break                   #refinement succeeded - finish up!
        except ValueError:          #result[1] is None on singular matrix
            print '**** Refinement failed - singular matrix ****'
            Ipvt = result[2]['ipvt']
            for i,ipvt in enumerate(Ipvt):
                if not np.sum(result[2]['fjac'],axis=1)[i]:
                    print 'Removing parameter: ',varyList[ipvt-1]
                    badVary.append(varyList[ipvt-1])
                    del(varyList[ipvt-1])
                    break
            else: # nothing removed
                break
    if dlg: dlg.Destroy()
    sigDict = dict(zip(varyList,sig))
    yb[xBeg:xFin] = getBackground('',parmDict,bakType,dataType,x[xBeg:xFin])[0]
    yc[xBeg:xFin] = getPeakProfile(dataType,parmDict,x[xBeg:xFin],varyList,bakType)
    yd[xBeg:xFin] = y[xBeg:xFin]-yc[xBeg:xFin]
    GetBackgroundParms(parmDict,Background)
    if bakVary: BackgroundPrint(Background,sigDict)
    GetInstParms(parmDict,Inst,varyList,Peaks)
    if insVary: InstPrint(Inst,sigDict)
    GetPeaksParms(Inst,parmDict,Peaks,varyList)    
    if peakVary: PeaksPrint(dataType,parmDict,sigDict,varyList)
    return sigDict,result,sig,Rvals,varyList,parmDict,fullvaryList,badVary

def calcIncident(Iparm,xdata):
    'needs a doc string'

    def IfunAdv(Iparm,xdata):
        Itype = Iparm['Itype']
        Icoef = Iparm['Icoeff']
        DYI = np.ones((12,xdata.shape[0]))
        YI = np.ones_like(xdata)*Icoef[0]
        
        x = xdata/1000.                 #expressions are in ms
        if Itype == 'Exponential':
            for i in [1,3,5,7,9]:
                Eterm = np.exp(-Icoef[i+1]*x**((i+1)/2))
                YI += Icoef[i]*Eterm
                DYI[i] *= Eterm
                DYI[i+1] *= -Icoef[i]*Eterm*x**((i+1)/2)            
        elif 'Maxwell'in Itype:
            Eterm = np.exp(-Icoef[2]/x**2)
            DYI[1] = Eterm/x**5
            DYI[2] = -Icoef[1]*DYI[1]/x**2
            YI += (Icoef[1]*Eterm/x**5)
            if 'Exponential' in Itype:
                for i in range(3,11,2):
                    Eterm = np.exp(-Icoef[i+1]*x**((i+1)/2))
                    YI += Icoef[i]*Eterm
                    DYI[i] *= Eterm
                    DYI[i+1] *= -Icoef[i]*Eterm*x**((i+1)/2)
            else:   #Chebyschev
                T = (2./x)-1.
                Ccof = np.ones((12,xdata.shape[0]))
                Ccof[1] = T
                for i in range(2,12):
                    Ccof[i] = 2*T*Ccof[i-1]-Ccof[i-2]
                for i in range(1,10):
                    YI += Ccof[i]*Icoef[i+2]
                    DYI[i+2] =Ccof[i]
        return YI,DYI
        
    Iesd = np.array(Iparm['Iesd'])
    Icovar = Iparm['Icovar']
    YI,DYI = IfunAdv(Iparm,xdata)
    YI = np.where(YI>0,YI,1.)
    WYI = np.zeros_like(xdata)
    vcov = np.zeros((12,12))
    k = 0
    for i in range(12):
        for j in range(i,12):
            vcov[i][j] = Icovar[k]*Iesd[i]*Iesd[j]
            vcov[j][i] = Icovar[k]*Iesd[i]*Iesd[j]
            k += 1
    M = np.inner(vcov,DYI.T)
    WYI = np.sum(M*DYI,axis=0)
    WYI = np.where(WYI>0.,WYI,0.)
    return YI,WYI
    
################################################################################
# Stacking fault simulation codes
################################################################################

def GetStackParms(Layers):
    
    Parms = []
#cell parms
    if Layers['Laue'] in ['-3','-3m','4/m','4/mmm','6/m','6/mmm']:
        Parms.append('cellA')
        Parms.append('cellC')
    else:
        Parms.append('cellA')
        Parms.append('cellB')
        Parms.append('cellC')
        if Layers['Laue'] != 'mmm':
            Parms.append('cellG')
#Transition parms
    for iY in range(len(Layers['Layers'])):
        for iX in range(len(Layers['Layers'])):
            Parms.append('TransP;%d;%d'%(iY,iX))
            Parms.append('TransX;%d;%d'%(iY,iX))
            Parms.append('TransY;%d;%d'%(iY,iX))
            Parms.append('TransZ;%d;%d'%(iY,iX))
    return Parms

def StackSim(Layers,ctrls,scale=0.,background={},limits=[],inst={},profile=[]):
    '''Simulate powder or selected area diffraction pattern from stacking faults using DIFFaX
    
    param: Layers dict: 'Laue':'-1','Cell':[False,1.,1.,1.,90.,90.,90,1.],
                        'Width':[[10.,10.],[False,False]],'Toler':0.01,'AtInfo':{},
                        'Layers':[],'Stacking':[],'Transitions':[]}
    param: ctrls string: controls string to be written on DIFFaX controls.dif file
    param: scale float: scale factor
    param: background dict: background parameters
    param: limits list: min/max 2-theta to be calculated
    param: inst dict: instrument parameters dictionary
    param: profile list: powder pattern data
    
    all updated in place    
    '''
    import atmdata
    path = sys.path
    for name in path:
        if 'bin' in name:
            DIFFaX = name+'/DIFFaX.exe'
            print ' Execute ',DIFFaX
            break
    # make form factor file that DIFFaX wants - atom types are GSASII style
    sf = open('data.sfc','w')
    sf.write('GSASII special form factor file for DIFFaX\n\n')
    atTypes = Layers['AtInfo'].keys()
    if 'H' not in atTypes:
        atTypes.insert(0,'H')
    for atType in atTypes:
        if atType == 'H': 
            blen = -.3741
        else:
            blen = Layers['AtInfo'][atType]['Isotopes']['Nat. Abund.']['SL'][0]
        Adat = atmdata.XrayFF[atType]
        text = '%4s'%(atType.ljust(4))
        for i in range(4):
            text += '%11.6f%11.6f'%(Adat['fa'][i],Adat['fb'][i])
        text += '%11.6f%11.6f'%(Adat['fc'],blen)
        text += '%3d\n'%(Adat['Z'])
        sf.write(text)
    sf.close()
    #make DIFFaX control.dif file - future use GUI to set some of these flags
    cf = open('control.dif','w')
    if ctrls == '0\n0\n3\n' or ctrls == '0\n1\n3\n': 
        x0 = profile[0]
        iBeg = np.searchsorted(x0,limits[0])
        iFin = np.searchsorted(x0,limits[1])
        if iFin-iBeg > 20000:
            iFin = iBeg+20000
        Dx = (x0[iFin]-x0[iBeg])/(iFin-iBeg)
        cf.write('GSASII-DIFFaX.dat\n'+ctrls)
        cf.write('%.6f %.6f %.6f\n1\n1\nend\n'%(x0[iBeg],x0[iFin],Dx))
    else:
        cf.write('GSASII-DIFFaX.dat\n'+ctrls)
        inst = {'Type':['XSC','XSC',]}
    cf.close()
    #make DIFFaX data file
    df = open('GSASII-DIFFaX.dat','w')
    df.write('INSTRUMENTAL\n')
    if 'X' in inst['Type'][0]:
        df.write('X-RAY\n')
    elif 'N' in inst['Type'][0]:
        df.write('NEUTRON\n')
    if ctrls == '0\n0\n3\n' or ctrls == '0\n1\n3\n': 
        df.write('%.4f\n'%(G2mth.getMeanWave(inst)))
        U = ateln2*inst['U'][1]/10000.
        V = ateln2*inst['V'][1]/10000.
        W = ateln2*inst['W'][1]/10000.
        HWHM = U*nptand(x0[iBeg:iFin]/2.)**2+V*nptand(x0[iBeg:iFin]/2.)+W
        HW = np.sqrt(np.mean(HWHM))
    #    df.write('PSEUDO-VOIGT 0.015 -0.0036 0.009 0.605 TRIM\n')
        if 'Mean' in Layers['selInst']:
            df.write('GAUSSIAN %.6f TRIM\n'%(HW))     #fast option - might not really matter
        elif 'Gaussian' in Layers['selInst']:
            df.write('GAUSSIAN %.6f %.6f %.6f TRIM\n'%(U,V,W))    #slow - make a GUI option?
        else:
            df.write('None\n')
    else:
        df.write('0.10\nNone\n')
    df.write('STRUCTURAL\n')
    a,b,c = Layers['Cell'][1:4]
    gam = Layers['Cell'][6]
    df.write('%.4f %.4f %.4f %.3f\n'%(a,b,c,gam))
    laue = Layers['Laue']
    if laue == '2/m(ab)':
        laue = '2/m(1)'
    elif laue == '2/m(c)':
        laue = '2/m(2)'
    if 'unknown' in Layers['Laue']:
        df.write('%s %.3f\n'%(laue,Layers['Toler']))
    else:    
        df.write('%s\n'%(laue))
    df.write('%d\n'%(len(Layers['Layers'])))
    if Layers['Width'][0][0] < 1. or Layers['Width'][0][1] < 1.:
        df.write('%.1f %.1f\n'%(Layers['Width'][0][0]*10000.,Layers['Width'][0][0]*10000.))    #mum to A
    layerNames = []
    for layer in Layers['Layers']:
        layerNames.append(layer['Name'])
    for il,layer in enumerate(Layers['Layers']):
        if layer['SameAs']:
            df.write('LAYER %d = %d\n'%(il+1,layerNames.index(layer['SameAs'])+1))
            continue
        df.write('LAYER %d\n'%(il+1))
        if '-1' in layer['Symm']:
            df.write('CENTROSYMMETRIC\n')
        else:
            df.write('NONE\n')
        for ia,atom in enumerate(layer['Atoms']):
            [name,atype,x,y,z,frac,Uiso] = atom
            if '-1' in layer['Symm'] and [x,y,z] == [0.,0.,0.]:
                frac /= 2.
            df.write('%4s %3d %.5f %.5f %.5f %.4f %.2f\n'%(atype.ljust(6),ia,x,y,z,78.9568*Uiso,frac))
    df.write('STACKING\n')
    df.write('%s\n'%(Layers['Stacking'][0]))
    if 'recursive' in Layers['Stacking'][0]:
        df.write('%s\n'%Layers['Stacking'][1])
    else:
        if 'list' in Layers['Stacking'][1]:
            Slen = len(Layers['Stacking'][2])
            iB = 0
            iF = 0
            while True:
                iF += 68
                if iF >= Slen:
                    break
                iF = min(iF,Slen)
                df.write('%s\n'%(Layers['Stacking'][2][iB:iF]))
                iB = iF
        else:
            df.write('%s\n'%Layers['Stacking'][1])    
    df.write('TRANSITIONS\n')
    for iY in range(len(Layers['Layers'])):
        sumPx = 0.
        for iX in range(len(Layers['Layers'])):
            p,dx,dy,dz = Layers['Transitions'][iY][iX][:4]
            p = round(p,3)
            df.write('%.3f %.5f %.5f %.5f\n'%(p,dx,dy,dz))
            sumPx += p
        if sumPx != 1.0:    #this has to be picky since DIFFaX is.
            print 'ERROR - Layer probabilities sum to ',sumPx,' DIFFaX will insist it = 1.0'
            df.close()
            os.remove('data.sfc')
            os.remove('control.dif')
            os.remove('GSASII-DIFFaX.dat')
            return       
    df.close()    
    time0 = time.time()
    try:
        subp.call(DIFFaX)
    except OSError:
        print ' DIFFax.exe is not available for this platform - under development'
    print ' DIFFaX time = %.2fs'%(time.time()-time0)
    if os.path.exists('GSASII-DIFFaX.spc'):
        Xpat = np.loadtxt('GSASII-DIFFaX.spc').T
        iFin = iBeg+Xpat.shape[1]
        bakType,backDict,backVary = SetBackgroundParms(background)
        backDict['Lam1'] = G2mth.getWave(inst)
        profile[4][iBeg:iFin] = getBackground('',backDict,bakType,inst['Type'][0],profile[0][iBeg:iFin])[0]    
        profile[3][iBeg:iFin] = Xpat[-1]*scale+profile[4][iBeg:iFin]
        if not np.any(profile[1]):                   #fill dummy data x,y,w,yc,yb,yd
            rv = st.poisson(profile[3][iBeg:iFin])
            profile[1][iBeg:iFin] = rv.rvs()
            Z = np.ones_like(profile[3][iBeg:iFin])
            Z[1::2] *= -1
            profile[1][iBeg:iFin] = profile[3][iBeg:iFin]+np.abs(profile[1][iBeg:iFin]-profile[3][iBeg:iFin])*Z
            profile[2][iBeg:iFin] = np.where(profile[1][iBeg:iFin]>0.,1./profile[1][iBeg:iFin],1.0)
        profile[5][iBeg:iFin] = profile[1][iBeg:iFin]-profile[3][iBeg:iFin]
    #cleanup files..
        os.remove('GSASII-DIFFaX.spc')
    elif os.path.exists('GSASII-DIFFaX.sadp'):
        Sadp = np.fromfile('GSASII-DIFFaX.sadp','>u2')
        Sadp = np.reshape(Sadp,(256,-1))
        Layers['Sadp']['Img'] = Sadp
        os.remove('GSASII-DIFFaX.sadp')
    os.remove('data.sfc')
    os.remove('control.dif')
    os.remove('GSASII-DIFFaX.dat')
    
def SetPWDRscan(inst,limits,profile):
    
    wave = G2mth.getMeanWave(inst)
    x0 = profile[0]
    iBeg = np.searchsorted(x0,limits[0])
    iFin = np.searchsorted(x0,limits[1])
    if iFin-iBeg > 20000:
        iFin = iBeg+20000
    Dx = (x0[iFin]-x0[iBeg])/(iFin-iBeg)
    pyx.pygetinst(wave,x0[iBeg],x0[iFin],Dx)
    return iFin-iBeg
       
def SetStackingSF(Layers,debug):
# Load scattering factors into DIFFaX arrays
    import atmdata
    atTypes = Layers['AtInfo'].keys()
    aTypes = []
    for atype in atTypes:
        aTypes.append('%4s'%(atype.ljust(4)))
    SFdat = []
    for atType in atTypes:
        Adat = atmdata.XrayFF[atType]
        SF = np.zeros(9)
        SF[:8:2] = Adat['fa']
        SF[1:8:2] = Adat['fb']
        SF[8] = Adat['fc']
        SFdat.append(SF)
    SFdat = np.array(SFdat)
    pyx.pyloadscf(len(atTypes),aTypes,SFdat.T,debug)
    
def SetStackingClay(Layers,Type):
# Controls
    rand.seed()
    ranSeed = rand.randint(1,2**16-1)
    try:    
        laueId = ['-1','2/m(ab)','2/m(c)','mmm','-3','-3m','4/m','4/mmm',
            '6/m','6/mmm'].index(Layers['Laue'])+1
    except ValueError:  #for 'unknown'
        laueId = -1
    if 'SADP' in Type:
        planeId = ['h0l','0kl','hhl','h-hl'].index(Layers['Sadp']['Plane'])+1
        lmax = int(Layers['Sadp']['Lmax'])
    else:
        planeId = 0
        lmax = 0
# Sequences
    StkType = ['recursive','explicit'].index(Layers['Stacking'][0])
    try:
        StkParm = ['infinite','random','list'].index(Layers['Stacking'][1])
    except ValueError:
        StkParm = -1
    if StkParm == 2:    #list
        StkSeq = [int(val) for val in Layers['Stacking'][2].split()]
        Nstk = len(StkSeq)
    else:
        Nstk = 1
        StkSeq = [0,]
    if StkParm == -1:
        StkParm = int(Layers['Stacking'][1])
    Wdth = Layers['Width'][0]
    mult = 1
    controls = [laueId,planeId,lmax,mult,StkType,StkParm,ranSeed]
    LaueSym = Layers['Laue'].ljust(12)
    pyx.pygetclay(controls,LaueSym,Wdth,Nstk,StkSeq)
    return laueId,controls
    
def SetCellAtoms(Layers):
    Cell = Layers['Cell'][1:4]+Layers['Cell'][6:7]
# atoms in layers
    atTypes = Layers['AtInfo'].keys()
    AtomXOU = []
    AtomTp = []
    LayerSymm = []
    LayerNum = []
    layerNames = []
    Natm = 0
    Nuniq = 0
    for layer in Layers['Layers']:
        layerNames.append(layer['Name'])
    for il,layer in enumerate(Layers['Layers']):
        if layer['SameAs']:
            LayerNum.append(layerNames.index(layer['SameAs'])+1)
            continue
        else:
            LayerNum.append(il+1)
            Nuniq += 1
        if '-1' in layer['Symm']:
            LayerSymm.append(1)
        else:
            LayerSymm.append(0)
        for ia,atom in enumerate(layer['Atoms']):
            [name,atype,x,y,z,frac,Uiso] = atom
            Natm += 1
            AtomTp.append('%4s'%(atype.ljust(4)))
            Ta = atTypes.index(atype)+1
            AtomXOU.append([float(Nuniq),float(ia+1),float(Ta),x,y,z,frac,Uiso*78.9568])
    AtomXOU = np.array(AtomXOU)
    Nlayers = len(layerNames)
    pyx.pycellayer(Cell,Natm,AtomTp,AtomXOU.T,Nuniq,LayerSymm,Nlayers,LayerNum)
    return Nlayers
    
def SetStackingTrans(Layers,Nlayers):
# Transitions
    TransX = []
    TransP = []
    for Ytrans in Layers['Transitions']:
        TransP.append([trans[0] for trans in Ytrans])   #get just the numbers
        TransX.append([trans[1:4] for trans in Ytrans])   #get just the numbers
    TransP = np.array(TransP,dtype='float').T
    TransX = np.array(TransX,dtype='float')
#    GSASIIpath.IPyBreak()
    pyx.pygettrans(Nlayers,TransP,TransX)
    
def CalcStackingPWDR(Layers,scale,background,limits,inst,profile,debug):
# Scattering factors
    SetStackingSF(Layers,debug)
# Controls & sequences
    laueId,controls = SetStackingClay(Layers,'PWDR')
# cell & atoms
    Nlayers = SetCellAtoms(Layers)
    Volume = Layers['Cell'][7]    
# Transitions
    SetStackingTrans(Layers,Nlayers)
# PWDR scan
    Nsteps = SetPWDRscan(inst,limits,profile)
# result as Spec
    x0 = profile[0]
    profile[3] = np.zeros(len(profile[0]))
    profile[4] = np.zeros(len(profile[0]))
    profile[5] = np.zeros(len(profile[0]))
    iBeg = np.searchsorted(x0,limits[0])
    iFin = np.searchsorted(x0,limits[1])
    if iFin-iBeg > 20000:
        iFin = iBeg+20000
    Nspec = 20001       
    spec = np.zeros(Nspec,dtype='double')    
    time0 = time.time()
    pyx.pygetspc(controls,Nspec,spec)
    print ' GETSPC time = %.2fs'%(time.time()-time0)
    time0 = time.time()
    U = ateln2*inst['U'][1]/10000.
    V = ateln2*inst['V'][1]/10000.
    W = ateln2*inst['W'][1]/10000.
    HWHM = U*nptand(x0[iBeg:iFin]/2.)**2+V*nptand(x0[iBeg:iFin]/2.)+W
    HW = np.sqrt(np.mean(HWHM))
    BrdSpec = np.zeros(Nsteps)
    if 'Mean' in Layers['selInst']:
        pyx.pyprofile(U,V,W,HW,1,Nsteps,BrdSpec)
    elif 'Gaussian' in Layers['selInst']:
        pyx.pyprofile(U,V,W,HW,4,Nsteps,BrdSpec)
    else:
        BrdSpec = spec[:Nsteps]
    BrdSpec /= Volume
    iFin = iBeg+Nsteps
    bakType,backDict,backVary = SetBackgroundParms(background)
    backDict['Lam1'] = G2mth.getWave(inst)
    profile[4][iBeg:iFin] = getBackground('',backDict,bakType,inst['Type'][0],profile[0][iBeg:iFin])[0]    
    profile[3][iBeg:iFin] = BrdSpec*scale+profile[4][iBeg:iFin]
    if not np.any(profile[1]):                   #fill dummy data x,y,w,yc,yb,yd
        rv = st.poisson(profile[3][iBeg:iFin])
        profile[1][iBeg:iFin] = rv.rvs()
        Z = np.ones_like(profile[3][iBeg:iFin])
        Z[1::2] *= -1
        profile[1][iBeg:iFin] = profile[3][iBeg:iFin]+np.abs(profile[1][iBeg:iFin]-profile[3][iBeg:iFin])*Z
        profile[2][iBeg:iFin] = np.where(profile[1][iBeg:iFin]>0.,1./profile[1][iBeg:iFin],1.0)
    profile[5][iBeg:iFin] = profile[1][iBeg:iFin]-profile[3][iBeg:iFin]
    print ' Broadening time = %.2fs'%(time.time()-time0)
    
def CalcStackingSADP(Layers,debug):
    
# Scattering factors
    SetStackingSF(Layers,debug)
# Controls & sequences
    laueId,controls = SetStackingClay(Layers,'SADP')
# cell & atoms
    Nlayers = SetCellAtoms(Layers)    
# Transitions
    SetStackingTrans(Layers,Nlayers)
# result as Sadp
    Nspec = 20001       
    spec = np.zeros(Nspec,dtype='double')    
    time0 = time.time()
    hkLim,Incr,Nblk = pyx.pygetsadp(controls,Nspec,spec)
    Sapd = np.zeros((256,256))
    iB = 0
    for i in range(hkLim):
        iF = iB+Nblk
        p1 = 127+int(i*Incr)
        p2 = 128-int(i*Incr)
        if Nblk == 128:
            if i:
                Sapd[128:,p1] = spec[iB:iF]
                Sapd[:128,p1] = spec[iF:iB:-1]
            Sapd[128:,p2] = spec[iB:iF]
            Sapd[:128,p2] = spec[iF:iB:-1]
        else:
            if i:
                Sapd[:,p1] = spec[iB:iF]
            Sapd[:,p2] = spec[iB:iF]
        iB += Nblk
    Layers['Sadp']['Img'] = Sapd
    print ' GETSAD time = %.2fs'%(time.time()-time0)
#    GSASIIpath.IPyBreak()
    
#testing data
NeedTestData = True
def TestData():
    'needs a doc string'
#    global NeedTestData
    global bakType
    bakType = 'chebyschev'
    global xdata
    xdata = np.linspace(4.0,40.0,36000)
    global parmDict0
    parmDict0 = {
        'pos0':5.6964,'int0':8835.8,'sig0':1.0,'gam0':1.0,
        'pos1':11.4074,'int1':3922.3,'sig1':1.0,'gam1':1.0,
        'pos2':20.6426,'int2':1573.7,'sig2':1.0,'gam2':1.0,
        'pos3':26.9568,'int3':925.1,'sig3':1.0,'gam3':1.0,
        'U':1.163,'V':-0.605,'W':0.093,'X':0.0,'Y':2.183,'SH/L':0.002,
        'Back0':5.384,'Back1':-0.015,'Back2':.004,
        }
    global parmDict1
    parmDict1 = {
        'pos0':13.4924,'int0':48697.6,'sig0':1.0,'gam0':1.0,
        'pos1':23.4360,'int1':43685.5,'sig1':1.0,'gam1':1.0,
        'pos2':27.1152,'int2':123712.6,'sig2':1.0,'gam2':1.0,
        'pos3':33.7196,'int3':65349.4,'sig3':1.0,'gam3':1.0,
        'pos4':36.1119,'int4':115829.8,'sig4':1.0,'gam4':1.0,
        'pos5':39.0122,'int5':6916.9,'sig5':1.0,'gam5':1.0,
        'U':22.75,'V':-17.596,'W':10.594,'X':1.577,'Y':5.778,'SH/L':0.002,
        'Back0':36.897,'Back1':-0.508,'Back2':.006,
        'Lam1':1.540500,'Lam2':1.544300,'I(L2)/I(L1)':0.5,
        }
    global parmDict2
    parmDict2 = {
        'pos0':5.7,'int0':1000.0,'sig0':0.5,'gam0':0.5,
        'U':2.,'V':-2.,'W':5.,'X':0.5,'Y':0.5,'SH/L':0.02,
        'Back0':5.,'Back1':-0.02,'Back2':.004,
#        'Lam1':1.540500,'Lam2':1.544300,'I(L2)/I(L1)':0.5,
        }
    global varyList
    varyList = []

def test0():
    if NeedTestData: TestData()
    gplot = plotter.add('FCJ-Voigt, 11BM').gca()
    gplot.plot(xdata,getBackground('',parmDict0,bakType,'PXC',xdata)[0])   
    gplot.plot(xdata,getPeakProfile(parmDict0,xdata,varyList,bakType))
    fplot = plotter.add('FCJ-Voigt, Ka1+2').gca()
    fplot.plot(xdata,getBackground('',parmDict1,bakType,'PXC',xdata)[0])   
    fplot.plot(xdata,getPeakProfile(parmDict1,xdata,varyList,bakType))
    
def test1():
    if NeedTestData: TestData()
    time0 = time.time()
    for i in range(100):
        getPeakProfile(parmDict1,xdata,varyList,bakType)
    print '100+6*Ka1-2 peaks=1200 peaks',time.time()-time0
    
def test2(name,delt):
    if NeedTestData: TestData()
    varyList = [name,]
    xdata = np.linspace(5.6,5.8,400)
    hplot = plotter.add('derivatives test for '+name).gca()
    hplot.plot(xdata,getPeakProfileDerv(parmDict2,xdata,varyList,bakType)[0])
    y0 = getPeakProfile(parmDict2,xdata,varyList,bakType)
    parmDict2[name] += delt
    y1 = getPeakProfile(parmDict2,xdata,varyList,bakType)
    hplot.plot(xdata,(y1-y0)/delt,'r+')
    
def test3(name,delt):
    if NeedTestData: TestData()
    names = ['pos','sig','gam','shl']
    idx = names.index(name)
    myDict = {'pos':parmDict2['pos0'],'sig':parmDict2['sig0'],'gam':parmDict2['gam0'],'shl':parmDict2['SH/L']}
    xdata = np.linspace(5.6,5.8,800)
    dx = xdata[1]-xdata[0]
    hplot = plotter.add('derivatives test for '+name).gca()
    hplot.plot(xdata,100.*dx*getdFCJVoigt3(myDict['pos'],myDict['sig'],myDict['gam'],myDict['shl'],xdata)[idx+1])
    y0 = getFCJVoigt3(myDict['pos'],myDict['sig'],myDict['gam'],myDict['shl'],xdata)
    myDict[name] += delt
    y1 = getFCJVoigt3(myDict['pos'],myDict['sig'],myDict['gam'],myDict['shl'],xdata)
    hplot.plot(xdata,(y1-y0)/delt,'r+')

if __name__ == '__main__':
    import GSASIItestplot as plot
    global plotter
    plotter = plot.PlotNotebook()
#    test0()
#    for name in ['int0','pos0','sig0','gam0','U','V','W','X','Y','SH/L','I(L2)/I(L1)']:
    for name,shft in [['int0',0.1],['pos0',0.0001],['sig0',0.01],['gam0',0.00001],
        ['U',0.1],['V',0.01],['W',0.01],['X',0.0001],['Y',0.0001],['SH/L',0.00005]]:
        test2(name,shft)
    for name,shft in [['pos',0.0001],['sig',0.01],['gam',0.0001],['shl',0.00005]]:
        test3(name,shft)
    print "OK"
    plotter.StartEventLoop()
