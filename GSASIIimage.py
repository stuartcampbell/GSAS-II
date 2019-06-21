# -*- coding: utf-8 -*-
#GSASII image calculations: ellipse fitting & image integration        
########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### SVN repository information ###################
'''
*GSASIIimage: Image calc module*
================================

Ellipse fitting & image integration

'''
from __future__ import division, print_function
import math
import time
import numpy as np
import numpy.linalg as nl
import numpy.ma as ma
from scipy.optimize import leastsq
import scipy.interpolate as scint
import copy
import GSASIIpath
GSASIIpath.SetVersionNumber("$Revision$")
try:
    import GSASIIplot as G2plt
except ImportError: # expected in scriptable w/o matplotlib and/or wx
    pass
import GSASIIlattice as G2lat
import GSASIIpwd as G2pwd
import GSASIIspc as G2spc
import GSASIImath as G2mth
import GSASIIfiles as G2fil

# trig functions in degrees
sind = lambda x: math.sin(x*math.pi/180.)
asind = lambda x: 180.*math.asin(x)/math.pi
tand = lambda x: math.tan(x*math.pi/180.)
atand = lambda x: 180.*math.atan(x)/math.pi
atan2d = lambda y,x: 180.*math.atan2(y,x)/math.pi
cosd = lambda x: math.cos(x*math.pi/180.)
acosd = lambda x: 180.*math.acos(x)/math.pi
rdsq2d = lambda x,p: round(1.0/math.sqrt(x),p)
#numpy versions
npsind = lambda x: np.sin(x*np.pi/180.)
npasind = lambda x: 180.*np.arcsin(x)/np.pi
npcosd = lambda x: np.cos(x*np.pi/180.)
npacosd = lambda x: 180.*np.arccos(x)/np.pi
nptand = lambda x: np.tan(x*np.pi/180.)
npatand = lambda x: 180.*np.arctan(x)/np.pi
npatan2d = lambda y,x: 180.*np.arctan2(y,x)/np.pi
nxs = np.newaxis
debug = False
    
def pointInPolygon(pXY,xy):
    'Needs a doc string'
    #pXY - assumed closed 1st & last points are duplicates
    Inside = False
    N = len(pXY)
    p1x,p1y = pXY[0]
    for i in range(N+1):
        p2x,p2y = pXY[i%N]
        if (max(p1y,p2y) >= xy[1] > min(p1y,p2y)) and (xy[0] <= max(p1x,p2x)):
            if p1y != p2y:
                xinters = (xy[1]-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
            if p1x == p2x or xy[0] <= xinters:
                Inside = not Inside
        p1x,p1y = p2x,p2y
    return Inside
    
def peneCorr(tth,dep,dist,tilt=0.,azm=0.):
    'Needs a doc string'
#    return dep*(1.-npcosd(abs(tilt*npsind(azm))-tth*npcosd(azm)))  #something wrong here
    return dep*(1.-npcosd(tth))*dist**2/1000.         #best one
#    return dep*npsind(tth)             #not as good as 1-cos2Q
        
def makeMat(Angle,Axis):
    '''Make rotation matrix from Angle and Axis

    :param float Angle: in degrees
    :param int Axis: 0 for rotation about x, 1 for about y, etc.
    '''
    cs = npcosd(Angle)
    ss = npsind(Angle)
    M = np.array(([1.,0.,0.],[0.,cs,-ss],[0.,ss,cs]),dtype=np.float32)
    return np.roll(np.roll(M,Axis,axis=0),Axis,axis=1)
                    
def FitEllipse(xy):
    
    def ellipse_center(p):
        ''' gives ellipse center coordinates
        '''
        b,c,d,f,a = p[1]/2., p[2], p[3]/2., p[4]/2., p[0]
        num = b*b-a*c
        x0=(c*d-b*f)/num
        y0=(a*f-b*d)/num
        return np.array([x0,y0])
    
    def ellipse_angle_of_rotation( p ):
        ''' gives rotation of ellipse major axis from x-axis
        range will be -90 to 90 deg
        '''
        b,c,a = p[1]/2., p[2], p[0]
        return 0.5*npatand(2*b/(a-c))
    
    def ellipse_axis_length( p ):
        ''' gives ellipse radii in [minor,major] order
        '''
        b,c,d,f,g,a = p[1]/2., p[2], p[3]/2., p[4]/2, p[5], p[0]
        up = 2*(a*f*f+c*d*d+g*b*b-2*b*d*f-a*c*g)
        down1=(b*b-a*c)*( (c-a)*np.sqrt(1+4*b*b/((a-c)*(a-c)))-(c+a))
        down2=(b*b-a*c)*( (a-c)*np.sqrt(1+4*b*b/((a-c)*(a-c)))-(c+a))
        res1=np.sqrt(up/down1)
        res2=np.sqrt(up/down2)
        return np.array([ res2,res1])
    
    xy = np.array(xy)
    x = np.asarray(xy.T[0])[:,np.newaxis]
    y = np.asarray(xy.T[1])[:,np.newaxis]
    D =  np.hstack((x*x, x*y, y*y, x, y, np.ones_like(x)))
    S = np.dot(D.T,D)
    C = np.zeros([6,6])
    C[0,2] = C[2,0] = 2; C[1,1] = -1
    E, V =  nl.eig(np.dot(nl.inv(S), C))
    n = np.argmax(np.abs(E))
    a = V[:,n]
    cent = ellipse_center(a)
    phi = ellipse_angle_of_rotation(a)
    radii = ellipse_axis_length(a)
    phi += 90.
    if radii[0] > radii[1]:
        radii = [radii[1],radii[0]]
        phi -= 90.
    return cent,phi,radii

def FitDetector(rings,varyList,parmDict,Print=True,covar=False):
    '''Fit detector calibration paremeters

    :param np.array rings: vector of ring positions
    :param list varyList: calibration parameters to be refined
    :param dict parmDict: all calibration parameters
    :param bool Print: set to True (default) to print the results
    :param bool covar: set to True to return the covariance matrix (default is False)
    :returns: [chisq,vals,sigList] unless covar is True, then 
        [chisq,vals,sigList,coVarMatrix] is returned
    '''
        
    def CalibPrint(ValSig,chisq,Npts):
        print ('Image Parameters: chi**2: %12.3g, Np: %d'%(chisq,Npts))
        ptlbls = 'names :'
        ptstr =  'values:'
        sigstr = 'esds  :'
        for name,value,sig in ValSig:
            ptlbls += "%s" % (name.rjust(12))
            if name == 'phi':
                ptstr += Fmt[name] % (value%360.)
            else:
                ptstr += Fmt[name] % (value)
            if sig:
                sigstr += Fmt[name] % (sig)
            else:
                sigstr += 12*' '
        print (ptlbls)
        print (ptstr)
        print (sigstr)        
        
    def ellipseCalcD(B,xyd,varyList,parmDict):
        
        x,y,dsp = xyd
        varyDict = dict(zip(varyList,B))
        parms = {}
        for parm in parmDict:
            if parm in varyList:
                parms[parm] = varyDict[parm]
            else:
                parms[parm] = parmDict[parm]
        phi = parms['phi']-90.               #get rotation of major axis from tilt axis
        tth = 2.0*npasind(parms['wave']/(2.*dsp))
        phi0 = npatan2d(y-parms['det-Y'],x-parms['det-X'])
        dxy = peneCorr(tth,parms['dep'],parms['dist'],parms['tilt'],phi0)
        stth = npsind(tth)
        cosb = npcosd(parms['tilt'])
        tanb = nptand(parms['tilt'])        
        tbm = nptand((tth-parms['tilt'])/2.)
        tbp = nptand((tth+parms['tilt'])/2.)
        d = parms['dist']+dxy
        fplus = d*tanb*stth/(cosb+stth)
        fminus = d*tanb*stth/(cosb-stth)
        vplus = d*(tanb+(1+tbm)/(1-tbm))*stth/(cosb+stth)
        vminus = d*(tanb+(1-tbp)/(1+tbp))*stth/(cosb-stth)
        R0 = np.sqrt((vplus+vminus)**2-(fplus+fminus)**2)/2.      #+minor axis
        R1 = (vplus+vminus)/2.                                    #major axis
        zdis = (fplus-fminus)/2.
        Robs = np.sqrt((x-parms['det-X'])**2+(y-parms['det-Y'])**2)
        rsqplus = R0**2+R1**2
        rsqminus = R0**2-R1**2
        R = rsqminus*npcosd(2.*phi0-2.*phi)+rsqplus
        Q = np.sqrt(2.)*R0*R1*np.sqrt(R-2.*zdis**2*npsind(phi0-phi)**2)
        P = 2.*R0**2*zdis*npcosd(phi0-phi)
        Rcalc = (P+Q)/R
        M = (Robs-Rcalc)*10.        #why 10? does make "chi**2" more reasonable
        return M
        
    names = ['dist','det-X','det-Y','tilt','phi','dep','wave']
    fmt = ['%12.3f','%12.3f','%12.3f','%12.3f','%12.3f','%12.4f','%12.6f']
    Fmt = dict(zip(names,fmt))
    p0 = [parmDict[key] for key in varyList]
    result = leastsq(ellipseCalcD,p0,args=(rings.T,varyList,parmDict),full_output=True,ftol=1.e-8)
    chisq = np.sum(result[2]['fvec']**2)/(rings.shape[0]-len(p0))   #reduced chi^2 = M/(Nobs-Nvar)
    parmDict.update(zip(varyList,result[0]))
    vals = list(result[0])
    sig = list(np.sqrt(chisq*np.diag(result[1])))
    sigList = np.zeros(7)
    for i,name in enumerate(varyList):
        sigList[i] = sig[varyList.index(name)]
    ValSig = zip(varyList,vals,sig)
    if Print:
        CalibPrint(ValSig,chisq,rings.shape[0])
    if covar:
        return [chisq,vals,sigList,result[1]]
    else:
        return [chisq,vals,sigList]

def ImageLocalMax(image,w,Xpix,Ypix):
    'Needs a doc string'
    w2 = w*2
    sizey,sizex = image.shape
    xpix = int(Xpix)            #get reference corner of pixel chosen
    ypix = int(Ypix)
    if not w:
        ZMax = np.sum(image[ypix-2:ypix+2,xpix-2:xpix+2])
        return xpix,ypix,ZMax,0.0001
    if (w2 < xpix < sizex-w2) and (w2 < ypix < sizey-w2) and image[ypix,xpix]:
        ZMax = image[ypix-w:ypix+w,xpix-w:xpix+w]
        Zmax = np.argmax(ZMax)
        ZMin = image[ypix-w2:ypix+w2,xpix-w2:xpix+w2]
        Zmin = np.argmin(ZMin)
        xpix += Zmax%w2-w
        ypix += Zmax//w2-w
        return xpix,ypix,np.ravel(ZMax)[Zmax],max(0.0001,np.ravel(ZMin)[Zmin])   #avoid neg/zero minimum
    else:
        return 0,0,0,0      
    
def makeRing(dsp,ellipse,pix,reject,scalex,scaley,image,mul=1):
    'Needs a doc string'
    def ellipseC():
        'compute estimate of ellipse circumference'
        if radii[0] < 0:        #hyperbola
#            theta = npacosd(1./np.sqrt(1.+(radii[0]/radii[1])**2))
#            print (theta)
            return 0
        apb = radii[1]+radii[0]
        amb = radii[1]-radii[0]
        return np.pi*apb*(1+3*(amb/apb)**2/(10+np.sqrt(4-3*(amb/apb)**2)))
        
    cent,phi,radii = ellipse
    cphi = cosd(phi-90.)        #convert to major axis rotation
    sphi = sind(phi-90.)
    ring = []
    C = int(ellipseC())*mul         #ring circumference in mm
    azm = []
    for i in range(0,C,1):      #step around ring in 1mm increments
        a = 360.*i/C
        x = radii[1]*cosd(a-phi+90.)        #major axis
        y = radii[0]*sind(a-phi+90.)
        X = (cphi*x-sphi*y+cent[0])*scalex      #convert mm to pixels
        Y = (sphi*x+cphi*y+cent[1])*scaley
        X,Y,I,J = ImageLocalMax(image,pix,X,Y)
        if I and J and float(I)/J > reject:
            X += .5                             #set to center of pixel
            Y += .5
            X /= scalex                         #convert back to mm
            Y /= scaley
            if [X,Y,dsp] not in ring:           #no duplicates!
                ring.append([X,Y,dsp])
                azm.append(a)
    if len(ring) < 10:
        ring = []
        azm = []
    return ring,azm
    
def GetEllipse2(tth,dxy,dist,cent,tilt,phi):
    '''uses Dandelin spheres to find ellipse or hyperbola parameters from detector geometry
    on output
    radii[0] (b-minor axis) set < 0. for hyperbola
    
    '''
    radii = [0,0]
    stth = sind(tth)
    cosb = cosd(tilt)
    tanb = tand(tilt)
    tbm = tand((tth-tilt)/2.)
    tbp = tand((tth+tilt)/2.)
    sinb = sind(tilt)
    d = dist+dxy
    if tth+abs(tilt) < 90.:      #ellipse
        fplus = d*tanb*stth/(cosb+stth)
        fminus = d*tanb*stth/(cosb-stth)
        vplus = d*(tanb+(1+tbm)/(1-tbm))*stth/(cosb+stth)
        vminus = d*(tanb+(1-tbp)/(1+tbp))*stth/(cosb-stth)
        radii[0] = np.sqrt((vplus+vminus)**2-(fplus+fminus)**2)/2.      #+minor axis
        radii[1] = (vplus+vminus)/2.                                    #major axis
        zdis = (fplus-fminus)/2.
    else:   #hyperbola!
        f = d*abs(tanb)*stth/(cosb+stth)
        v = d*(abs(tanb)+tand(tth-abs(tilt)))
        delt = d*stth*(1.+stth*cosb)/(abs(sinb)*cosb*(stth+cosb))
        eps = (v-f)/(delt-v)
        radii[0] = -eps*(delt-f)/np.sqrt(eps**2-1.)                     #-minor axis
        radii[1] = eps*(delt-f)/(eps**2-1.)                             #major axis
        if tilt > 0:
            zdis = f+radii[1]*eps
        else:
            zdis = -f
#NB: zdis is || to major axis & phi is rotation of minor axis
#thus shift from beam to ellipse center is [Z*sin(phi),-Z*cos(phi)]
    elcent = [cent[0]+zdis*sind(phi),cent[1]-zdis*cosd(phi)]
    return elcent,phi,radii
    
def GetEllipse(dsp,data):
    '''uses Dandelin spheres to find ellipse or hyperbola parameters from detector geometry
    as given in image controls dictionary (data) and a d-spacing (dsp)
    '''
    cent = data['center']
    tilt = data['tilt']
    phi = data['rotation']
    dep = data.get('DetDepth',0.0)
    tth = 2.0*asind(data['wavelength']/(2.*dsp))
    dist = data['distance']
    dxy = peneCorr(tth,dep,dist,tilt)
    return GetEllipse2(tth,dxy,dist,cent,tilt,phi)
        
def GetDetectorXY(dsp,azm,data):
    '''Get detector x,y position from d-spacing (dsp), azimuth (azm,deg) 
    & image controls dictionary (data)
    it seems to be only used in plotting 
    '''    
    elcent,phi,radii = GetEllipse(dsp,data)
    phi = data['rotation']-90.          #to give rotation of major axis
    tilt = data['tilt']
    dist = data['distance']
    cent = data['center']
    tth = 2.0*asind(data['wavelength']/(2.*dsp))
    stth = sind(tth)
    cosb = cosd(tilt)
    if radii[0] > 0.:
        sinb = sind(tilt)
        tanb = tand(tilt)
        fplus = dist*tanb*stth/(cosb+stth)
        fminus = dist*tanb*stth/(cosb-stth)
        zdis = (fplus-fminus)/2.
        rsqplus = radii[0]**2+radii[1]**2
        rsqminus = radii[0]**2-radii[1]**2
        R = rsqminus*cosd(2.*azm-2.*phi)+rsqplus
        Q = np.sqrt(2.)*radii[0]*radii[1]*np.sqrt(R-2.*zdis**2*sind(azm-phi)**2)
        P = 2.*radii[0]**2*zdis*cosd(azm-phi)
        radius = (P+Q)/R
        xy = np.array([radius*cosd(azm),radius*sind(azm)])
        xy += cent
    else:   #hyperbola - both branches (one is way off screen!)
        sinb = abs(sind(tilt))
        tanb = abs(tand(tilt))
        f = dist*tanb*stth/(cosb+stth)
        v = dist*(tanb+tand(tth-abs(tilt)))
        delt = dist*stth*(1+stth*cosb)/(sinb*cosb*(stth+cosb))
        ecc = (v-f)/(delt-v)
        R = radii[1]*(ecc**2-1)/(1-ecc*cosd(azm))
        if tilt > 0.:
            offset = 2.*radii[1]*ecc+f      #select other branch
            xy = [-R*cosd(azm)-offset,-R*sind(azm)]
        else:
            offset = -f
            xy = [-R*cosd(azm)-offset,R*sind(azm)]
        xy = -np.array([xy[0]*cosd(phi)+xy[1]*sind(phi),xy[0]*sind(phi)-xy[1]*cosd(phi)])
        xy += cent
    return xy
    
def GetDetXYfromThAzm(Th,Azm,data):
    '''Computes a detector position from a 2theta angle and an azimultal
    angle (both in degrees) - apparently not used!
    '''
    dsp = data['wavelength']/(2.0*npsind(Th))    
    return GetDetectorXY(dsp,Azm,data)
                    
def GetTthAzmDsp(x,y,data): #expensive
    '''Computes a 2theta, etc. from a detector position and calibration constants - checked
    OK for ellipses & hyperbola.

    :returns: np.array(tth,azm,G,dsp) where tth is 2theta, azm is the azimutal angle,
       G is ? and dsp is the d-space
    '''
    wave = data['wavelength']
    cent = data['center']
    tilt = data['tilt']
    dist = data['distance']/cosd(tilt)
    x0 = dist*tand(tilt)
    phi = data['rotation']
    dep = data.get('DetDepth',0.)
    azmthoff = data['azmthOff']
    dx = np.array(x-cent[0],dtype=np.float32)
    dy = np.array(y-cent[1],dtype=np.float32)
    D = ((dx-x0)**2+dy**2+dist**2)      #sample to pixel distance
    X = np.array(([dx,dy,np.zeros_like(dx)]),dtype=np.float32).T
    X = np.dot(X,makeMat(phi,2))
    Z = np.dot(X,makeMat(tilt,0)).T[2]
    tth = npatand(np.sqrt(dx**2+dy**2-Z**2)/(dist-Z))
    dxy = peneCorr(tth,dep,dist,tilt,npatan2d(dy,dx))
    DX = dist-Z+dxy
    DY = np.sqrt(dx**2+dy**2-Z**2)
    tth = npatan2d(DY,DX) 
    dsp = wave/(2.*npsind(tth/2.))
    azm = (npatan2d(dy,dx)+azmthoff+720.)%360.
    G = D/dist**2       #for geometric correction = 1/cos(2theta)^2 if tilt=0.
    return np.array([tth,azm,G,dsp])
    
def GetTth(x,y,data):
    'Give 2-theta value for detector x,y position; calibration info in data'
    return GetTthAzmDsp(x,y,data)[0]
    
def GetTthAzm(x,y,data):
    'Give 2-theta, azimuth values for detector x,y position; calibration info in data'
    return GetTthAzmDsp(x,y,data)[0:2]
    
def GetTthAzmG(x,y,data):
    '''Give 2-theta, azimuth & geometric corr. values for detector x,y position;
     calibration info in data - only used in integration
    '''
    'Needs a doc string - checked OK for ellipses & hyperbola'
    tilt = data['tilt']
    dist = data['distance']/npcosd(tilt)
    x0 = data['distance']*nptand(tilt)
    MN = -np.inner(makeMat(data['rotation'],2),makeMat(tilt,0))
    distsq = data['distance']**2
    dx = x-data['center'][0]
    dy = y-data['center'][1]
    G = ((dx-x0)**2+dy**2+distsq)/distsq       #for geometric correction = 1/cos(2theta)^2 if tilt=0.
    Z = np.dot(np.dstack([dx.T,dy.T,np.zeros_like(dx.T)]),MN).T[2]
    xyZ = dx**2+dy**2-Z**2    
    tth = npatand(np.sqrt(xyZ)/(dist-Z))
    dxy = peneCorr(tth,data['DetDepth'],dist,tilt,npatan2d(dy,dx))
    tth = npatan2d(np.sqrt(xyZ),dist-Z+dxy) 
    azm = (npatan2d(dy,dx)+data['azmthOff']+720.)%360.
    return tth,azm,G

def GetDsp(x,y,data):
    'Give d-spacing value for detector x,y position; calibration info in data'
    return GetTthAzmDsp(x,y,data)[3]
       
def GetAzm(x,y,data):
    'Give azimuth value for detector x,y position; calibration info in data'
    return GetTthAzmDsp(x,y,data)[1]
    
def meanAzm(a,b):
    AZM = lambda a,b: npacosd(0.5*(npsind(2.*b)-npsind(2.*a))/(np.pi*(b-a)/180.))/2.
    azm = AZM(a,b)
#    quad = int((a+b)/180.)
#    if quad == 1:
#        azm = 180.-azm
#    elif quad == 2:
#        azm += 180.
#    elif quad == 3:
#        azm = 360-azm
    return azm      
       
def ImageCompress(image,scale):
    ''' Reduces size of image by selecting every n'th point
    param: image array: original image
    param: scale int: intervsl between selected points 
    returns: array: reduced size image
    '''
    if scale == 1:
        return image
    else:
        return image[::scale,::scale]
        
def checkEllipse(Zsum,distSum,xSum,ySum,dist,x,y):
    'Needs a doc string'
    avg = np.array([distSum/Zsum,xSum/Zsum,ySum/Zsum])
    curr = np.array([dist,x,y])
    return abs(avg-curr)/avg < .02

def GetLineScan(image,data):
    Nx,Ny = data['size']
    pixelSize = data['pixelSize']
    scalex = 1000./pixelSize[0]         #microns --> 1/mm
    scaley = 1000./pixelSize[1]
    wave = data['wavelength']
    numChans = data['outChannels']
    LUtth = np.array(data['IOtth'],dtype=np.float)
    azm = data['linescan'][1]-data['azmthOff']
    Tx = np.array([tth for tth in np.linspace(LUtth[0],LUtth[1],numChans+1)])
    Ty = np.zeros_like(Tx)
    dsp = wave/(2.0*npsind(Tx/2.0))
    xy = np.array([GetDetectorXY(d,azm,data) for d in dsp]).T
    xy[1] *= scalex
    xy[0] *= scaley
    xy = np.array(xy,dtype=int)
    Xpix = ma.masked_outside(xy[1],0,Ny-1)
    Ypix = ma.masked_outside(xy[0],0,Nx-1)
    xpix = Xpix[~(Xpix.mask+Ypix.mask)].compressed()
    ypix = Ypix[~(Xpix.mask+Ypix.mask)].compressed()
    Ty = image[xpix,ypix]
    Tx = ma.array(Tx,mask=Xpix.mask+Ypix.mask).compressed()
    return [Tx,Ty]

def EdgeFinder(image,data):
    '''this makes list of all x,y where I>edgeMin suitable for an ellipse search?
    Not currently used but might be useful in future?
    '''
    import numpy.ma as ma
    Nx,Ny = data['size']
    pixelSize = data['pixelSize']
    edgemin = data['edgemin']
    scalex = pixelSize[0]/1000.
    scaley = pixelSize[1]/1000.    
    tay,tax = np.mgrid[0:Nx,0:Ny]
    tax = np.asfarray(tax*scalex,dtype=np.float32)
    tay = np.asfarray(tay*scaley,dtype=np.float32)
    tam = ma.getmask(ma.masked_less(image.flatten(),edgemin))
    tax = ma.compressed(ma.array(tax.flatten(),mask=tam))
    tay = ma.compressed(ma.array(tay.flatten(),mask=tam))
    return zip(tax,tay)
    
def MakeFrameMask(data,frame):
    import polymask as pm
    pixelSize = data['pixelSize']
    scalex = pixelSize[0]/1000.
    scaley = pixelSize[1]/1000.
    blkSize = 512
    Nx,Ny = data['size']
    nXBlks = (Nx-1)//blkSize+1
    nYBlks = (Ny-1)//blkSize+1
    tam = ma.make_mask_none(data['size'])
    for iBlk in range(nXBlks):
        iBeg = iBlk*blkSize
        iFin = min(iBeg+blkSize,Nx)
        for jBlk in range(nYBlks):
            jBeg = jBlk*blkSize
            jFin = min(jBeg+blkSize,Ny)                
            nI = iFin-iBeg
            nJ = jFin-jBeg
            tax,tay = np.mgrid[iBeg+0.5:iFin+.5,jBeg+.5:jFin+.5]         #bin centers not corners
            tax = np.asfarray(tax*scalex,dtype=np.float32)
            tay = np.asfarray(tay*scaley,dtype=np.float32)
            tamp = ma.make_mask_none((1024*1024))
            tamp = ma.make_mask(pm.polymask(nI*nJ,tax.flatten(),
                tay.flatten(),len(frame),frame,tamp)[:nI*nJ])^True  #switch to exclude around frame
            if tamp.shape:
                tamp = np.reshape(tamp[:nI*nJ],(nI,nJ))
                tam[iBeg:iFin,jBeg:jFin] = ma.mask_or(tamp[0:nI,0:nJ],tam[iBeg:iFin,jBeg:jFin])
            else:
                tam[iBeg:iFin,jBeg:jFin] = True
    return tam.T
    
def ImageRecalibrate(G2frame,ImageZ,data,masks):
    '''Called to repeat the calibration on an image, usually called after
    calibration is done initially to improve the fit.

    :param G2frame: The top-level GSAS-II frame or None, to skip plotting
    :param np.Array ImageZ: the image to calibrate
    :param dict data: the Controls dict for the image
    :param dict masks: a dict with masks
    :returns: a list containing vals,varyList,sigList,parmDict,covar
    '''
    import ImageCalibrants as calFile
    G2fil.G2Print ('Image recalibration:')
    time0 = time.time()
    pixelSize = data['pixelSize']
    scalex = 1000./pixelSize[0]
    scaley = 1000./pixelSize[1]
    pixLimit = data['pixLimit']
    cutoff = data['cutoff']
    data['rings'] = []
    data['ellipses'] = []
    if data['DetDepth'] > 0.5:          #patch - redefine DetDepth
        data['DetDepth'] /= data['distance']
    if not data['calibrant']:
        G2fil.G2Print ('warning: no calibration material selected')
        return []    
    skip = data['calibskip']
    dmin = data['calibdmin']
    if data['calibrant'] not in calFile.Calibrants:
        G2fil.G2Print('Warning: %s not in local copy of image calibrants file'%data['calibrant'])
        return []
    Bravais,SGs,Cells = calFile.Calibrants[data['calibrant']][:3]
    HKL = []
    for bravais,sg,cell in zip(Bravais,SGs,Cells):
        A = G2lat.cell2A(cell)
        if sg:
            SGData = G2spc.SpcGroup(sg)[1]
            hkl = G2pwd.getHKLpeak(dmin,SGData,A)
            HKL += list(hkl)
        else:
            hkl = G2lat.GenHBravais(dmin,bravais,A)
            HKL += list(hkl)
    HKL = G2lat.sortHKLd(HKL,True,False)
    varyList = [item for item in data['varyList'] if data['varyList'][item]]
    parmDict = {'dist':data['distance'],'det-X':data['center'][0],'det-Y':data['center'][1],
        'setdist':data.get('setdist',data['distance']),
        'tilt':data['tilt'],'phi':data['rotation'],'wave':data['wavelength'],'dep':data['DetDepth']}
    Found = False
    wave = data['wavelength']
    frame = masks['Frames']
    tam = ma.make_mask_none(ImageZ.shape)
    if frame:
        tam = ma.mask_or(tam,MakeFrameMask(data,frame))
    for iH,H in enumerate(HKL):
        if debug:   print (H) 
        dsp = H[3]
        tth = 2.0*asind(wave/(2.*dsp))
        if tth+abs(data['tilt']) > 90.:
            G2fil.G2Print ('next line is a hyperbola - search stopped')
            break
        ellipse = GetEllipse(dsp,data)
        Ring = makeRing(dsp,ellipse,pixLimit,cutoff,scalex,scaley,ma.array(ImageZ,mask=tam))[0]
        if Ring:
            if iH >= skip:
                data['rings'].append(np.array(Ring))
            data['ellipses'].append(copy.deepcopy(ellipse+('r',)))
            Found = True
        elif not Found:         #skipping inner rings, keep looking until ring found 
            continue
        else:                   #no more rings beyond edge of detector
            data['ellipses'].append([])
            continue
    if not data['rings']:
        G2fil.G2Print ('no rings found; try lower Min ring I/Ib',mode='warn')
        return []    
        
    rings = np.concatenate((data['rings']),axis=0)
    [chisq,vals,sigList,covar] = FitDetector(rings,varyList,parmDict,True,True)
    data['wavelength'] = parmDict['wave']
    data['distance'] = parmDict['dist']
    data['center'] = [parmDict['det-X'],parmDict['det-Y']]
    data['rotation'] = np.mod(parmDict['phi'],360.0)
    data['tilt'] = parmDict['tilt']
    data['DetDepth'] = parmDict['dep']
    data['chisq'] = chisq
    N = len(data['ellipses'])
    data['ellipses'] = []           #clear away individual ellipse fits
    for H in HKL[:N]:
        ellipse = GetEllipse(H[3],data)
        data['ellipses'].append(copy.deepcopy(ellipse+('b',)))    
    G2fil.G2Print ('calibration time = %.3f'%(time.time()-time0))
    if G2frame:
        G2plt.PlotImage(G2frame,newImage=True)        
    return [vals,varyList,sigList,parmDict,covar]

def ImageCalibrate(G2frame,data):
    '''Called to perform an initial image calibration after points have been
    selected for the inner ring.
    '''
    import ImageCalibrants as calFile
    G2fil.G2Print ('Image calibration:')
    time0 = time.time()
    ring = data['ring']
    pixelSize = data['pixelSize']
    scalex = 1000./pixelSize[0]
    scaley = 1000./pixelSize[1]
    pixLimit = data['pixLimit']
    cutoff = data['cutoff']
    varyDict = data['varyList']
    if varyDict['dist'] and varyDict['wave']:
        G2fil.G2Print ('ERROR - you can not simultaneously calibrate distance and wavelength')
        return False
    if len(ring) < 5:
        G2fil.G2Print ('ERROR - not enough inner ring points for ellipse')
        return False
        
    #fit start points on inner ring
    data['ellipses'] = []
    data['rings'] = []
    outE = FitEllipse(ring)
    fmt  = '%s X: %.3f, Y: %.3f, phi: %.3f, R1: %.3f, R2: %.3f'
    fmt2 = '%s X: %.3f, Y: %.3f, phi: %.3f, R1: %.3f, R2: %.3f, chi**2: %.3f, Np: %d'
    if outE:
        G2fil.G2Print (fmt%('start ellipse: ',outE[0][0],outE[0][1],outE[1],outE[2][0],outE[2][1]))
        ellipse = outE
    else:
        return False
        
    #setup 360 points on that ring for "good" fit
    data['ellipses'].append(ellipse[:]+('g',))
    Ring = makeRing(1.0,ellipse,pixLimit,cutoff,scalex,scaley,G2frame.ImageZ)[0]
    if Ring:
        ellipse = FitEllipse(Ring)
        Ring = makeRing(1.0,ellipse,pixLimit,cutoff,scalex,scaley,G2frame.ImageZ)[0]    #do again
        ellipse = FitEllipse(Ring)
    else:
        G2fil.G2Print ('1st ring not sufficiently complete to proceed',mode='warn')
        return False
    if debug:
        G2fil.G2Print (fmt2%('inner ring:    ',ellipse[0][0],ellipse[0][1],ellipse[1],
            ellipse[2][0],ellipse[2][1],0.,len(Ring)))     #cent,phi,radii
    data['ellipses'].append(ellipse[:]+('r',))
    data['rings'].append(np.array(Ring))
    G2plt.PlotImage(G2frame,newImage=True)
    
#setup for calibration
    data['rings'] = []
    if not data['calibrant']:
        G2fil.G2Print ('Warning: no calibration material selected')
        return True
    
    skip = data['calibskip']
    dmin = data['calibdmin']
#generate reflection set
    Bravais,SGs,Cells = calFile.Calibrants[data['calibrant']][:3]
    HKL = []
    for bravais,sg,cell in zip(Bravais,SGs,Cells):
        A = G2lat.cell2A(cell)
        if sg:
            SGData = G2spc.SpcGroup(sg)[1]
            hkl = G2pwd.getHKLpeak(dmin,SGData,A)
            #G2fil.G2Print(hkl)
            HKL += list(hkl)
        else:
            hkl = G2lat.GenHBravais(dmin,bravais,A)
            HKL += list(hkl)
    HKL = G2lat.sortHKLd(HKL,True,False)[skip:]
#set up 1st ring
    elcent,phi,radii = ellipse              #from fit of 1st ring
    dsp = HKL[0][3]
    G2fil.G2Print ('1st ring: try %.4f'%(dsp))
    if varyDict['dist']:
        wave = data['wavelength']
        tth = 2.0*asind(wave/(2.*dsp))
    else:   #varyDict['wave']!
        dist = data['distance']
        tth = npatan2d(radii[0],dist)
        data['wavelength'] = wave =  2.0*dsp*sind(tth/2.0)
    Ring0 = makeRing(dsp,ellipse,3,cutoff,scalex,scaley,G2frame.ImageZ)[0]
    ttth = nptand(tth)
    ctth = npcosd(tth)
#1st estimate of tilt; assume ellipse - don't know sign though
    if varyDict['tilt']:
        tilt = npasind(np.sqrt(max(0.,1.-(radii[0]/radii[1])**2))*ctth)
        if not tilt:
            G2fil.G2Print ('WARNING - selected ring was fitted as a circle')
            G2fil.G2Print (' - if detector was tilted we suggest you skip this ring - WARNING')
    else:
        tilt = data['tilt']
#1st estimate of dist: sample to detector normal to plane
    if varyDict['dist']:
        data['distance'] = dist = radii[0]**2/(ttth*radii[1])
    else:
        dist = data['distance']
    if varyDict['tilt']:
#ellipse to cone axis (x-ray beam); 2 choices depending on sign of tilt
        zdisp = radii[1]*ttth*tand(tilt)
        zdism = radii[1]*ttth*tand(-tilt)
#cone axis position; 2 choices. Which is right?     
#NB: zdisp is || to major axis & phi is rotation of minor axis
#thus shift from beam to ellipse center is [Z*sin(phi),-Z*cos(phi)]
        centp = [elcent[0]+zdisp*sind(phi),elcent[1]-zdisp*cosd(phi)]
        centm = [elcent[0]+zdism*sind(phi),elcent[1]-zdism*cosd(phi)]
#check get same ellipse parms either way
#now do next ring; estimate either way & do a FitDetector each way; best fit is correct one
        fail = True
        i2 = 1
        while fail:
            dsp = HKL[i2][3]
            G2fil.G2Print ('2nd ring: try %.4f'%(dsp))
            tth = 2.0*asind(wave/(2.*dsp))
            ellipsep = GetEllipse2(tth,0.,dist,centp,tilt,phi)
            G2fil.G2Print (fmt%('plus ellipse :',ellipsep[0][0],ellipsep[0][1],ellipsep[1],ellipsep[2][0],ellipsep[2][1]))
            Ringp = makeRing(dsp,ellipsep,3,cutoff,scalex,scaley,G2frame.ImageZ)[0]
            parmDict = {'dist':dist,'det-X':centp[0],'det-Y':centp[1],
                'tilt':tilt,'phi':phi,'wave':wave,'dep':0.0}        
            varyList = [item for item in varyDict if varyDict[item]]
            if len(Ringp) > 10:
                chip = FitDetector(np.array(Ring0+Ringp),varyList,parmDict,True)[0]
                tiltp = parmDict['tilt']
                phip = parmDict['phi']
                centp = [parmDict['det-X'],parmDict['det-Y']]
                fail = False
            else:
                chip = 1e6
            ellipsem = GetEllipse2(tth,0.,dist,centm,-tilt,phi)
            G2fil.G2Print (fmt%('minus ellipse:',ellipsem[0][0],ellipsem[0][1],ellipsem[1],ellipsem[2][0],ellipsem[2][1]))
            Ringm = makeRing(dsp,ellipsem,3,cutoff,scalex,scaley,G2frame.ImageZ)[0]
            if len(Ringm) > 10:
                parmDict['tilt'] *= -1
                chim = FitDetector(np.array(Ring0+Ringm),varyList,parmDict,True)[0]
                tiltm = parmDict['tilt']
                phim = parmDict['phi']
                centm = [parmDict['det-X'],parmDict['det-Y']]
                fail = False
            else:
                chim = 1e6
            if fail:
                i2 += 1
        if chip < chim:
            data['tilt'] = tiltp
            data['center'] = centp
            data['rotation'] = phip
        else:
            data['tilt'] = tiltm
            data['center'] = centm
            data['rotation'] = phim
        data['ellipses'].append(ellipsep[:]+('b',))
        data['rings'].append(np.array(Ringp))
        data['ellipses'].append(ellipsem[:]+('r',))
        data['rings'].append(np.array(Ringm))
        G2plt.PlotImage(G2frame,newImage=True)
    if data['DetDepth'] > 0.5:          #patch - redefine DetDepth
        data['DetDepth'] /= data['distance']
    parmDict = {'dist':data['distance'],'det-X':data['center'][0],'det-Y':data['center'][1],
        'tilt':data['tilt'],'phi':data['rotation'],'wave':data['wavelength'],'dep':data['DetDepth']}
    varyList = [item for item in varyDict if varyDict[item]]
    data['rings'] = []
    data['ellipses'] = []
    for i,H in enumerate(HKL):
        dsp = H[3]
        tth = 2.0*asind(wave/(2.*dsp))
        if tth+abs(data['tilt']) > 90.:
            G2fil.G2Print ('next line is a hyperbola - search stopped')
            break
        if debug:   print ('HKLD:'+str(H[:4])+'2-theta: %.4f'%(tth))
        elcent,phi,radii = ellipse = GetEllipse(dsp,data)
        data['ellipses'].append(copy.deepcopy(ellipse+('g',)))
        if debug:   print (fmt%('predicted ellipse:',elcent[0],elcent[1],phi,radii[0],radii[1]))
        Ring = makeRing(dsp,ellipse,pixLimit,cutoff,scalex,scaley,G2frame.ImageZ)[0]
        if Ring:
            data['rings'].append(np.array(Ring))
            rings = np.concatenate((data['rings']),axis=0)
            if i:
                chisq = FitDetector(rings,varyList,parmDict,False)[0]
                data['distance'] = parmDict['dist']
                data['center'] = [parmDict['det-X'],parmDict['det-Y']]
                data['rotation'] = parmDict['phi']
                data['tilt'] = parmDict['tilt']
                data['DetDepth'] = parmDict['dep']
                data['chisq'] = chisq
                elcent,phi,radii = ellipse = GetEllipse(dsp,data)
                if debug:   print (fmt2%('fitted ellipse:   ',elcent[0],elcent[1],phi,radii[0],radii[1],chisq,len(rings)))
            data['ellipses'].append(copy.deepcopy(ellipse+('r',)))
#            G2plt.PlotImage(G2frame,newImage=True)
        else:
            if debug:   print ('insufficient number of points in this ellipse to fit')
#            break
    G2plt.PlotImage(G2frame,newImage=True)
    fullSize = len(G2frame.ImageZ)/scalex
    if 2*radii[1] < .9*fullSize:
        G2fil.G2Print ('Are all usable rings (>25% visible) used? Try reducing Min ring I/Ib')
    N = len(data['ellipses'])
    if N > 2:
        FitDetector(rings,varyList,parmDict)[0]
        data['wavelength'] = parmDict['wave']
        data['distance'] = parmDict['dist']
        data['center'] = [parmDict['det-X'],parmDict['det-Y']]
        data['rotation'] = parmDict['phi']
        data['tilt'] = parmDict['tilt']
        data['DetDepth'] = parmDict['dep']
    for H in HKL[:N]:
        ellipse = GetEllipse(H[3],data)
        data['ellipses'].append(copy.deepcopy(ellipse+('b',)))
    G2fil.G2Print ('calibration time = %.3f'%(time.time()-time0))
    G2plt.PlotImage(G2frame,newImage=True)        
    return True
    
def Make2ThetaAzimuthMap(data,iLim,jLim): #most expensive part of integration!
    'Needs a doc string'
    #transforms 2D image from x,y space to 2-theta,azimuth space based on detector orientation
    pixelSize = data['pixelSize']
    scalex = pixelSize[0]/1000.
    scaley = pixelSize[1]/1000.
    
    tay,tax = np.mgrid[iLim[0]+0.5:iLim[1]+.5,jLim[0]+.5:jLim[1]+.5]         #bin centers not corners
    tax = np.asfarray(tax*scalex,dtype=np.float32).flatten()
    tay = np.asfarray(tay*scaley,dtype=np.float32).flatten()
    nI = iLim[1]-iLim[0]
    nJ = jLim[1]-jLim[0]
    TA = np.array(GetTthAzmG(np.reshape(tax,(nI,nJ)),np.reshape(tay,(nI,nJ)),data))     #includes geom. corr. as dist**2/d0**2 - most expensive step
    TA[1] = np.where(TA[1]<0,TA[1]+360,TA[1])
    return TA           #2-theta, azimuth & geom. corr. arrays

def MakeMaskMap(data,masks,iLim,jLim,tamp):
    import polymask as pm
    pixelSize = data['pixelSize']
    scalex = pixelSize[0]/1000.
    scaley = pixelSize[1]/1000.
    
    tay,tax = np.mgrid[iLim[0]+0.5:iLim[1]+.5,jLim[0]+.5:jLim[1]+.5]         #bin centers not corners
    tax = np.asfarray(tax*scalex,dtype=np.float32).flatten()
    tay = np.asfarray(tay*scaley,dtype=np.float32).flatten()
    nI = iLim[1]-iLim[0]
    nJ = jLim[1]-jLim[0]
    #make position masks here
    frame = masks['Frames']
    tam = ma.make_mask_none((nI*nJ))
    if frame:
        tam = ma.mask_or(tam,ma.make_mask(pm.polymask(nI*nJ,tax,
            tay,len(frame),frame,tamp)[:nI*nJ])^True)
    polygons = masks['Polygons']
    for polygon in polygons:
        if polygon:
            tam = ma.mask_or(tam,ma.make_mask(pm.polymask(nI*nJ,tax,
                tay,len(polygon),polygon,tamp)[:nI*nJ]))
    for X,Y,rsq in masks['Points'].T:
        tam = ma.mask_or(tam,ma.getmask(ma.masked_less((tax-X)**2+(tay-Y)**2,rsq)))
    if tam.shape: 
        tam = np.reshape(tam,(nI,nJ))
    else:
        tam = ma.make_mask_none((nI,nJ))
    for xline in masks.get('Xlines',[]):    #a y pixel position
        if iLim[0] <= xline <= iLim[1]:
            tam[xline-iLim[0],:] = True
    for yline in masks.get('Ylines',[]):    #a x pixel position
        if jLim[0] <= yline <= jLim[1]:
            tam[:,yline-jLim[0]] = True            
    return tam           #position mask

def Fill2ThetaAzimuthMap(masks,TA,tam,image):
    'Needs a doc string'
    Zlim = masks['Thresholds'][1]
    rings = masks['Rings']
    arcs = masks['Arcs']
    TA = np.dstack((ma.getdata(TA[1]),ma.getdata(TA[0]),ma.getdata(TA[2])))    #azimuth, 2-theta, dist
    tax,tay,tad = np.dsplit(TA,3)    #azimuth, 2-theta, dist**2/d0**2
    for tth,thick in rings:
        tam = ma.mask_or(tam.flatten(),ma.getmask(ma.masked_inside(tay.flatten(),max(0.01,tth-thick/2.),tth+thick/2.)))
    for tth,azm,thick in arcs:
        tamt = ma.getmask(ma.masked_inside(tay.flatten(),max(0.01,tth-thick/2.),tth+thick/2.))
        tama = ma.getmask(ma.masked_inside(tax.flatten(),azm[0],azm[1]))
        tam = ma.mask_or(tam.flatten(),tamt*tama)
    taz = ma.masked_outside(image.flatten(),int(Zlim[0]),Zlim[1])
    tabs = np.ones_like(taz)
    tam = ma.mask_or(tam.flatten(),ma.getmask(taz))
    tax = ma.compressed(ma.array(tax.flatten(),mask=tam))   #azimuth
    tay = ma.compressed(ma.array(tay.flatten(),mask=tam))   #2-theta
    taz = ma.compressed(ma.array(taz.flatten(),mask=tam))   #intensity
    tad = ma.compressed(ma.array(tad.flatten(),mask=tam))   #dist**2/d0**2
    tabs = ma.compressed(ma.array(tabs.flatten(),mask=tam)) #ones - later used for absorption corr.
    return tax,tay,taz,tad,tabs

def MakeUseTA(data,blkSize=128):
    Nx,Ny = data['size']
    nXBlks = (Nx-1)//blkSize+1
    nYBlks = (Ny-1)//blkSize+1
    useTA = []
    for iBlk in range(nYBlks):
        iBeg = iBlk*blkSize
        iFin = min(iBeg+blkSize,Ny)
        useTAj = []
        for jBlk in range(nXBlks):
            jBeg = jBlk*blkSize
            jFin = min(jBeg+blkSize,Nx)
            TA = Make2ThetaAzimuthMap(data,(iBeg,iFin),(jBeg,jFin))          #2-theta & azimuth arrays & create position mask
            useTAj.append(TA)
        useTA.append(useTAj)
    return useTA

def MakeUseMask(data,masks,blkSize=128):
    Masks = copy.deepcopy(masks)
    Masks['Points'] = np.array(Masks['Points']).T           #get spots as X,Y,R arrays
    if np.any(masks['Points']):
        Masks['Points'][2] = np.square(Masks['Points'][2]/2.)
    Nx,Ny = data['size']
    nXBlks = (Nx-1)//blkSize+1
    nYBlks = (Ny-1)//blkSize+1
    useMask = []
    tamp = ma.make_mask_none((1024*1024))       #NB: this array size used in the fortran histogram2d
    for iBlk in range(nYBlks):
        iBeg = iBlk*blkSize
        iFin = min(iBeg+blkSize,Ny)
        useMaskj = []
        for jBlk in range(nXBlks):
            jBeg = jBlk*blkSize
            jFin = min(jBeg+blkSize,Nx)
            mask = MakeMaskMap(data,Masks,(iBeg,iFin),(jBeg,jFin),tamp)          #2-theta & azimuth arrays & create position mask
            useMaskj.append(mask)
        useMask.append(useMaskj)
    return useMask

def ImageIntegrate(image,data,masks,blkSize=128,returnN=False,useTA=None,useMask=None):
    'Integrate an image; called from OnIntegrateAll and OnIntegrate in G2imgGUI'    #for q, log(q) bins need data['binType']
    import histogram2d as h2d
    G2fil.G2Print ('Begin image integration; image range: %d %d'%(np.min(image),np.max(image)))
    CancelPressed = False
    LUtth = np.array(data['IOtth'])
    LRazm = np.array(data['LRazimuth'],dtype=np.float64)
    numAzms = data['outAzimuths']
    numChans = (data['outChannels']//4)*4
    Dazm = (LRazm[1]-LRazm[0])/numAzms
    if '2-theta' in data.get('binType','2-theta'):
        lutth = LUtth                
    elif 'log(q)' in data['binType']:
        lutth = np.log(4.*np.pi*npsind(LUtth/2.)/data['wavelength'])
    elif 'q' == data['binType'].lower():
        lutth = 4.*np.pi*npsind(LUtth/2.)/data['wavelength']
    dtth = (lutth[1]-lutth[0])/numChans
    muT = data.get('SampleAbs',[0.0,''])[0]
    if data['DetDepth'] > 0.5:          #patch - redefine DetDepth
        data['DetDepth'] /= data['distance']
    if 'SASD' in data['type']:
        muT = -np.log(muT)/2.       #Transmission to 1/2 thickness muT
    Masks = copy.deepcopy(masks)
    Masks['Points'] = np.array(Masks['Points']).T           #get spots as X,Y,R arrays
    if np.any(masks['Points']):
        Masks['Points'][2] = np.square(Masks['Points'][2]/2.)
    NST = np.zeros(shape=(numAzms,numChans),order='F',dtype=np.float32)
    H0 = np.zeros(shape=(numAzms,numChans),order='F',dtype=np.float32)
    H2 = np.linspace(lutth[0],lutth[1],numChans+1)
    Nx,Ny = data['size']
    nXBlks = (Nx-1)//blkSize+1
    nYBlks = (Ny-1)//blkSize+1
    tbeg = time.time()
    times = [0,0,0,0,0]
    tamp = ma.make_mask_none((1024*1024))       #NB: this array size used in the fortran histogram2d
    for iBlk in range(nYBlks):
        iBeg = iBlk*blkSize
        iFin = min(iBeg+blkSize,Ny)
        for jBlk in range(nXBlks):
            jBeg = jBlk*blkSize
            jFin = min(jBeg+blkSize,Nx)
            # next is most expensive step!
            t0 = time.time()
            if useTA:
                TA = useTA[iBlk][jBlk]
            else:
                TA = Make2ThetaAzimuthMap(data,(iBeg,iFin),(jBeg,jFin))           #2-theta & azimuth arrays & create position mask
            times[1] += time.time()-t0
            t0 = time.time()
            if useMask:
                tam = useMask[iBlk][jBlk]
            else:
                tam = MakeMaskMap(data,Masks,(iBeg,iFin),(jBeg,jFin),tamp)
            Block = image[iBeg:iFin,jBeg:jFin]
            tax,tay,taz,tad,tabs = Fill2ThetaAzimuthMap(Masks,TA,tam,Block)    #and apply masks
            pol = G2pwd.Polarization(data['PolaVal'][0],tay,tax-90.)[0]         #for pixel pola correction
            times[0] += time.time()-t0
            t0 = time.time()
            tax = np.where(tax > LRazm[1],tax-360.,tax)                 #put azm inside limits if possible
            tax = np.where(tax < LRazm[0],tax+360.,tax)
            if data.get('SampleAbs',[0.0,''])[1]:
                if 'Cylind' in data['SampleShape']:
                    muR = muT*(1.+npsind(tax)**2/2.)/(npcosd(tay))      #adjust for additional thickness off sample normal
                    tabs = G2pwd.Absorb(data['SampleShape'],muR,tay)
                elif 'Fixed' in data['SampleShape']:    #assumes flat plate sample normal to beam
                    tabs = G2pwd.Absorb('Fixed',muT,tay)
            if 'log(q)' in data.get('binType',''):
                tay = np.log(4.*np.pi*npsind(tay/2.)/data['wavelength'])
            elif 'q' == data.get('binType','').lower():
                tay = 4.*np.pi*npsind(tay/2.)/data['wavelength']
            times[2] += time.time()-t0
            t0 = time.time()
            taz = np.array((taz*tad/tabs),dtype='float32')/pol
            if any([tax.shape[0],tay.shape[0],taz.shape[0]]):
                NST,H0 = h2d.histogram2d(len(tax),tax,tay,taz,
                    numAzms,numChans,LRazm,lutth,Dazm,dtth,NST,H0)
            times[3] += time.time()-t0
    G2fil.G2Print('End integration loops')
    t0 = time.time()
    #prepare masked arrays of bins with pixels for interpolation setup
    H2msk = [ma.array(H2[:-1],mask=np.logical_not(nst)) for nst in NST]
    H0msk = [ma.array(np.divide(h0,nst),mask=np.logical_not(nst)) for nst,h0 in zip(NST,H0)]
    #make linear interpolators; outside limits give NaN
    H0int = [scint.interp1d(h2msk.compressed(),h0msk.compressed(),bounds_error=False) for h0msk,h2msk in zip(H0msk,H2msk)]
    #do interpolation on all points - fills in the empty bins; leaves others the same
    H0 = np.array([h0int(H2[:-1]) for h0int in H0int])
    H0 = np.nan_to_num(H0)
    if 'log(q)' in data.get('binType',''):
        H2 = 2.*npasind(np.exp(H2)*data['wavelength']/(4.*np.pi))
    elif 'q' == data.get('binType','').lower():
        H2 = 2.*npasind(H2*data['wavelength']/(4.*np.pi))
    if Dazm:        
        H1 = np.array([azm for azm in np.linspace(LRazm[0],LRazm[1],numAzms+1)])
    else:
        H1 = LRazm
    if 'SASD' not in data['type']:
        H0 *= np.array(G2pwd.Polarization(data['PolaVal'][0],H2[:-1],0.)[0])
    H0 /= npcosd(H2[:-1])           #**2? I don't think so, **1 is right for powders
    if 'SASD' in data['type']:
        H0 /= npcosd(H2[:-1])           #one more for small angle scattering data?
    if data['Oblique'][1]:
        H0 /= G2pwd.Oblique(data['Oblique'][0],H2[:-1])
    times[4] += time.time()-t0
    G2fil.G2Print ('Step times: \n apply masks  %8.3fs xy->th,azm   %8.3fs fill map     %8.3fs \
        \n binning      %8.3fs cleanup      %8.3fs'%(times[0],times[1],times[2],times[3],times[4]))
    G2fil.G2Print ("Elapsed time:","%8.3fs"%(time.time()-tbeg))
    G2fil.G2Print ('Integration complete')
    if returnN:     #As requested by Steven Weigand
        return H0,H1,H2,NST,CancelPressed
    else:
        return H0,H1,H2,CancelPressed
    
def MakeStrStaRing(ring,Image,Controls):
    ellipse = GetEllipse(ring['Dset'],Controls)
    pixSize = Controls['pixelSize']
    scalex = 1000./pixSize[0]
    scaley = 1000./pixSize[1]
    Ring = np.array(makeRing(ring['Dset'],ellipse,ring['pixLimit'],ring['cutoff'],scalex,scaley,Image)[0]).T   #returns x,y,dsp for each point in ring
    if len(Ring):
        ring['ImxyObs'] = copy.copy(Ring[:2])
        TA = GetTthAzm(Ring[0],Ring[1],Controls)       #convert x,y to tth,azm
        TA[0] = Controls['wavelength']/(2.*npsind(TA[0]/2.))      #convert 2th to d
        ring['ImtaObs'] = TA
        ring['ImtaCalc'] = np.zeros_like(ring['ImtaObs'])
        Ring[0] = TA[0]
        Ring[1] = TA[1]
        return Ring,ring
    else:
        ring['ImxyObs'] = [[],[]]
        ring['ImtaObs'] = [[],[]]
        ring['ImtaCalc'] = [[],[]]
        return [],[]    #bad ring; no points found
    
def FitStrSta(Image,StrSta,Controls):
    'Needs a doc string'
    
    StaControls = copy.deepcopy(Controls)
    phi = StrSta['Sample phi']
    wave = Controls['wavelength']
    pixelSize = Controls['pixelSize']
    scalex = 1000./pixelSize[0]
    scaley = 1000./pixelSize[1]
    StaType = StrSta['Type']
    StaControls['distance'] += StrSta['Sample z']*cosd(phi)

    for ring in StrSta['d-zero']:       #get observed x,y,d points for the d-zeros
        dset = ring['Dset']
        Ring,R = MakeStrStaRing(ring,Image,StaControls)
        if len(Ring):
            ring.update(R)
            p0 = ring['Emat']
            val,esd,covMat = FitStrain(Ring,p0,dset,wave,phi,StaType)
            ring['Emat'] = val
            ring['Esig'] = esd
            ellipse = FitEllipse(R['ImxyObs'].T)
            ringxy,ringazm = makeRing(ring['Dcalc'],ellipse,0,0.,scalex,scaley,Image)
            ring['ImxyCalc'] = np.array(ringxy).T[:2]
            ringint = np.array([float(Image[int(x*scalex),int(y*scaley)]) for y,x in np.array(ringxy)[:,:2]])
            ringint /= np.mean(ringint)
            ring['Ivar'] = np.var(ringint)
            ring['covMat'] = covMat
            G2fil.G2Print ('Variance in normalized ring intensity: %.3f'%(ring['Ivar']))
    CalcStrSta(StrSta,Controls)
    
def IntStrSta(Image,StrSta,Controls):
    StaControls = copy.deepcopy(Controls)
    pixelSize = Controls['pixelSize']
    scalex = 1000./pixelSize[0]
    scaley = 1000./pixelSize[1]
    phi = StrSta['Sample phi']
    StaControls['distance'] += StrSta['Sample z']*cosd(phi)
    RingsAI = []
    for ring in StrSta['d-zero']:       #get observed x,y,d points for the d-zeros
        Ring,R = MakeStrStaRing(ring,Image,StaControls)
        if len(Ring):
            ellipse = FitEllipse(R['ImxyObs'].T)
            ringxy,ringazm = makeRing(ring['Dcalc'],ellipse,0,0.,scalex,scaley,Image,5)
            ring['ImxyCalc'] = np.array(ringxy).T[:2]
            ringint = np.array([float(Image[int(x*scalex),int(y*scaley)]) for y,x in np.array(ringxy)[:,:2]])
            ringint /= np.mean(ringint)
            G2fil.G2Print (' %s %.3f %s %.3f %s %d'%('d-spacing',ring['Dcalc'],'sig(MRD):',np.sqrt(np.var(ringint)),'# points:',len(ringint)))
            RingsAI.append(np.array(zip(ringazm,ringint)).T)
    return RingsAI
    
def CalcStrSta(StrSta,Controls):

    wave = Controls['wavelength']
    phi = StrSta['Sample phi']
    StaType = StrSta['Type']
    for ring in StrSta['d-zero']:
        Eij = ring['Emat']
        E = [[Eij[0],Eij[1],0],[Eij[1],Eij[2],0],[0,0,0]]
        th,azm = ring['ImtaObs']
        th0 = np.ones_like(azm)*npasind(wave/(2.*ring['Dset']))
        V = -np.sum(np.sum(E*calcFij(90.,phi,azm,th0).T/1.e6,axis=2),axis=1)
        if StaType == 'True':
            ring['ImtaCalc'] = np.array([np.exp(V)*ring['Dset'],azm])
        else:
            ring['ImtaCalc'] = np.array([(V+1.)*ring['Dset'],azm])
        dmin = np.min(ring['ImtaCalc'][0])
        dmax = np.max(ring['ImtaCalc'][0])
        if ring.get('fixDset',True):
            if abs(Eij[0]) < abs(Eij[2]):         #tension
                ring['Dcalc'] = dmin+(dmax-dmin)/4.
            else:                       #compression
                ring['Dcalc'] = dmin+3.*(dmax-dmin)/4.
        else:
            ring['Dcalc'] = np.mean(ring['ImtaCalc'][0])

def calcFij(omg,phi,azm,th):
    '''    Uses parameters as defined by Bob He & Kingsley Smith, Adv. in X-Ray Anal. 41, 501 (1997)

    :param omg: his omega = sample omega rotation; 0 when incident beam || sample surface, 
        90 when perp. to sample surface
    :param phi: his phi = sample phi rotation; usually = 0, axis rotates with omg.
    :param azm: his chi = azimuth around incident beam
    :param th:  his theta = theta
    '''
    a = npsind(th)*npcosd(omg)+npsind(azm)*npcosd(th)*npsind(omg)
    b = -npcosd(azm)*npcosd(th)
    c = npsind(th)*npsind(omg)-npsind(azm)*npcosd(th)*npcosd(omg)
    d = a*npsind(phi)+b*npcosd(phi)
    e = a*npcosd(phi)-b*npsind(phi)
    Fij = np.array([
        [d**2,d*e,c*d],
        [d*e,e**2,c*e],
        [c*d,c*e,c**2]])
    return -Fij

def FitStrain(rings,p0,dset,wave,phi,StaType):
    'Needs a doc string'
    def StrainPrint(ValSig,dset):
        print ('Strain tensor for Dset: %.6f'%(dset))
        ptlbls = 'names :'
        ptstr =  'values:'
        sigstr = 'esds  :'
        for name,fmt,value,sig in ValSig:
            ptlbls += "%s" % (name.rjust(12))
            ptstr += fmt % (value)
            if sig:
                sigstr += fmt % (sig)
            else:
                sigstr += 12*' '
        print (ptlbls)
        print (ptstr)
        print (sigstr)
        
    def strainCalc(p,xyd,dset,wave,phi,StaType):
        E = np.array([[p[0],p[1],0],[p[1],p[2],0],[0,0,0]])
        dspo,azm,dsp = xyd
        th = npasind(wave/(2.0*dspo))
        V = -np.sum(np.sum(E*calcFij(90.,phi,azm,th).T/1.e6,axis=2),axis=1)
        if StaType == 'True':
            dspc = dset*np.exp(V)
        else:
            dspc = dset*(V+1.)
        return dspo-dspc
        
    names = ['e11','e12','e22']
    fmt = ['%12.2f','%12.2f','%12.2f']
    result = leastsq(strainCalc,p0,args=(rings,dset,wave,phi,StaType),full_output=True)
    vals = list(result[0])
    chisq = np.sum(result[2]['fvec']**2)/(rings.shape[1]-3)     #reduced chi^2 = M/(Nobs-Nvar)
    covM = result[1]
    covMatrix = covM*chisq
    sig = list(np.sqrt(chisq*np.diag(result[1])))
    ValSig = zip(names,fmt,vals,sig)
    StrainPrint(ValSig,dset)
    return vals,sig,covMatrix

def FitImageSpots(Image,ImMax,ind,pixSize,nxy):
    
    def calcMean(nxy,pixSize,img):
        gdx,gdy = np.mgrid[0:nxy,0:nxy]
        gdx = ma.array((gdx-nxy//2)*pixSize[0]/1000.,mask=~ma.getmaskarray(ImBox))
        gdy = ma.array((gdy-nxy//2)*pixSize[1]/1000.,mask=~ma.getmaskarray(ImBox))
        posx = ma.sum(gdx)/ma.count(gdx)
        posy = ma.sum(gdy)/ma.count(gdy)
        return posx,posy
    
    def calcPeak(values,nxy,pixSize,img):
        back,mag,px,py,sig = values
        peak = np.zeros([nxy,nxy])+back
        nor = 1./(2.*np.pi*sig**2)
        gdx,gdy = np.mgrid[0:nxy,0:nxy]
        gdx = (gdx-nxy//2)*pixSize[0]/1000.
        gdy = (gdy-nxy//2)*pixSize[1]/1000.
        arg = (gdx-px)**2+(gdy-py)**2        
        peak += mag*nor*np.exp(-arg/(2.*sig**2))
        return ma.compressed(img-peak)/np.sqrt(ma.compressed(img))
    
    def calc2Peak(values,nxy,pixSize,img):
        back,mag,px,py,sigx,sigy,rho = values
        peak = np.zeros([nxy,nxy])+back
        nor = 1./(2.*np.pi*sigx*sigy*np.sqrt(1.-rho**2))
        gdx,gdy = np.mgrid[0:nxy,0:nxy]
        gdx = (gdx-nxy//2)*pixSize[0]/1000.
        gdy = (gdy-nxy//2)*pixSize[1]/1000.
        argnor = -1./(2.*(1.-rho**2))
        arg = (gdx-px)**2/sigx**2+(gdy-py)**2/sigy**2-2.*rho*(gdx-px)*(gdy-py)/(sigx*sigy)        
        peak += mag*nor*np.exp(argnor*arg)
        return ma.compressed(img-peak)/np.sqrt(ma.compressed(img))        
    
    nxy2 = nxy//2
    ImBox = Image[ind[1]-nxy2:ind[1]+nxy2+1,ind[0]-nxy2:ind[0]+nxy2+1]
    back = np.min(ImBox)
    mag = np.sum(ImBox-back)
    vals = [back,mag,0.,0.,0.2,0.2,0.]
    ImBox = ma.array(ImBox,dtype=float,mask=ImBox>0.75*ImMax)
    px = (ind[0]+.5)*pixSize[0]/1000.
    py = (ind[1]+.5)*pixSize[1]/1000.
    if ma.any(ma.getmaskarray(ImBox)):
        vals = calcMean(nxy,pixSize,ImBox)
        posx,posy = [px+vals[0],py+vals[1]]
        return [posx,posy,6.]
    else:
        result = leastsq(calc2Peak,vals,args=(nxy,pixSize,ImBox),full_output=True)
        vals = result[0]
        ratio = vals[4]/vals[5]
        if 0.5 < ratio < 2.0 and vals[2] < 2. and vals[3] < 2.:
            posx,posy = [px+vals[2],py+vals[3]]
            return [posx,posy,min(6.*vals[4],6.)]
        else:
            return None
    
def AutoSpotMasks(Image,Masks,Controls):
    
    G2fil.G2Print ('auto spot search')
    nxy = 15
    rollImage = lambda rho,roll: np.roll(np.roll(rho,roll[0],axis=0),roll[1],axis=1)
    pixelSize = Controls['pixelSize']
    spotMask = ma.array(Image,mask=(Image<np.mean(Image)))
    indices = (-1,0,1)
    rolls = np.array([[ix,iy] for ix in indices for iy in indices])
    time0 = time.time()
    for roll in rolls:
        if np.any(roll):        #avoid [0,0]
            spotMask = ma.array(spotMask,mask=(spotMask-rollImage(Image,roll)<0.),dtype=float)
    mags = spotMask[spotMask.nonzero()]
    indx = np.transpose(spotMask.nonzero())
    size1 = mags.shape[0]
    magind = [[indx[0][0],indx[0][1],mags[0]],]
    for ind,mag in list(zip(indx,mags))[1:]:        #remove duplicates
#            ind[0],ind[1],I,J = ImageLocalMax(Image,nxy,ind[0],ind[1])
        if (magind[-1][0]-ind[0])**2+(magind[-1][1]-ind[1])**2 > 16:
            magind.append([ind[0],ind[1],Image[ind[0],ind[1]]])  
    magind = np.array(magind).T
    indx = np.array(magind[0:2],dtype=np.int32)
    mags = magind[2]
    size2 = mags.shape[0]
    G2fil.G2Print ('Initial search done: %d -->%d %.2fs'%(size1,size2,time.time()-time0))
    nx,ny = Image.shape
    ImMax = np.max(Image)
    peaks = []
    nxy2 = nxy//2
    mult = 0.001
    num = 1e6
    while num>500:
        mult += .0001            
        minM = mult*np.max(mags)
        num = ma.count(ma.array(mags,mask=mags<=minM))
        G2fil.G2Print('try',mult,minM,num)
    minM = mult*np.max(mags)
    G2fil.G2Print ('Find biggest spots:',mult,num,minM)
    for i,mag in enumerate(mags):
        if mag > minM:
            if (nxy2 < indx[0][i] < nx-nxy2-1) and (nxy2 < indx[1][i] < ny-nxy2-1):
#                    G2fil.G2Print ('try:%d %d %d %.2f'%(i,indx[0][i],indx[1][i],mags[i]))
                peak = FitImageSpots(Image,ImMax,[indx[1][i],indx[0][i]],pixelSize,nxy)
                if peak and not any(np.isnan(np.array(peak))):
                    peaks.append(peak)
#                    G2fil.G2Print (' Spot found: %s'%str(peak))
    peaks = G2mth.sortArray(G2mth.sortArray(peaks,1),0)
    Peaks = [peaks[0],]
    for peak in peaks[1:]:
        if GetDsp(peak[0],peak[1],Controls) >= 1.:      #toss non-diamond low angle spots
            continue
        if (peak[0]-Peaks[-1][0])**2+(peak[1]-Peaks[-1][1])**2 > peak[2]*Peaks[-1][2] :
            Peaks.append(peak)
#            G2fil.G2Print (' Spot found: %s'%str(peak))
    G2fil.G2Print ('Spots found: %d time %.2fs'%(len(Peaks),time.time()-time0))
    Masks['Points'] = Peaks
    return None
