# -*- coding: utf-8 -*-
'''
*GSASIIlattice: Unit cells*
---------------------------

Perform lattice-related computations

Note that *g* is the reciprocal lattice tensor, and *G* is its inverse,
:math:`G = g^{-1}`, where 

  .. math::

   G = \\left( \\begin{matrix}
   a^2 & a b\\cos\gamma & a c\\cos\\beta \\\\
   a b\\cos\\gamma & b^2 & b c \cos\\alpha \\\\
   a c\\cos\\beta &  b c \\cos\\alpha & c^2
   \\end{matrix}\\right)

The "*A* tensor" terms are defined as
:math:`A = (\\begin{matrix} G_{11} & G_{22} & G_{33} & 2G_{12} & 2G_{13} & 2G_{23}\\end{matrix})` and *A* can be used in this fashion:
:math:`d^* = \sqrt {A_1 h^2 + A_2 k^2 + A_3 l^2 + A_4 hk + A_5 hl + A_6 kl}`, where
*d* is the d-spacing, and :math:`d^*` is the reciprocal lattice spacing, 
:math:`Q = 2 \\pi d^* = 2 \\pi / d`
'''
########### SVN repository information ###################
# $Date$
# $Author$
# $Revision$
# $URL$
# $Id$
########### SVN repository information ###################
import math
import numpy as np
import numpy.linalg as nl
import GSASIIpath
import GSASIImath as G2mth
import GSASIIspc as G2spc
GSASIIpath.SetVersionNumber("$Revision$")
# trig functions in degrees
sind = lambda x: np.sin(x*np.pi/180.)
asind = lambda x: 180.*np.arcsin(x)/np.pi
tand = lambda x: np.tan(x*np.pi/180.)
atand = lambda x: 180.*np.arctan(x)/np.pi
atan2d = lambda y,x: 180.*np.arctan2(y,x)/np.pi
cosd = lambda x: np.cos(x*np.pi/180.)
acosd = lambda x: 180.*np.arccos(x)/np.pi
rdsq2d = lambda x,p: round(1.0/np.sqrt(x),p)
rpd = np.pi/180.
RSQ2PI = 1./np.sqrt(2.*np.pi)
SQ2 = np.sqrt(2.)
RSQPI = 1./np.sqrt(np.pi)

def sec2HMS(sec):
    """Convert time in sec to H:M:S string
    
    :param sec: time in seconds
    :return: H:M:S string (to nearest 100th second)
    
    """
    H = int(sec/3600)
    M = int(sec/60-H*60)
    S = sec-3600*H-60*M
    return '%d:%2d:%.2f'%(H,M,S)
    
def rotdMat(angle,axis=0):
    """Prepare rotation matrix for angle in degrees about axis(=0,1,2)

    :param angle: angle in degrees
    :param axis:  axis (0,1,2 = x,y,z) about which for the rotation
    :return: rotation matrix - 3x3 numpy array

    """
    if axis == 2:
        return np.array([[cosd(angle),-sind(angle),0],[sind(angle),cosd(angle),0],[0,0,1]])
    elif axis == 1:
        return np.array([[cosd(angle),0,-sind(angle)],[0,1,0],[sind(angle),0,cosd(angle)]])
    else:
        return np.array([[1,0,0],[0,cosd(angle),-sind(angle)],[0,sind(angle),cosd(angle)]])
        
def rotdMat4(angle,axis=0):
    """Prepare rotation matrix for angle in degrees about axis(=0,1,2) with scaling for OpenGL 

    :param angle: angle in degrees
    :param axis:  axis (0,1,2 = x,y,z) about which for the rotation
    :return: rotation matrix - 4x4 numpy array (last row/column for openGL scaling)

    """
    Mat = rotdMat(angle,axis)
    return np.concatenate((np.concatenate((Mat,[[0],[0],[0]]),axis=1),[[0,0,0,1],]),axis=0)
    
def fillgmat(cell):
    """Compute lattice metric tensor from unit cell constants

    :param cell: tuple with a,b,c,alpha, beta, gamma (degrees)
    :return: 3x3 numpy array

    """
    a,b,c,alp,bet,gam = cell
    g = np.array([
        [a*a,  a*b*cosd(gam),  a*c*cosd(bet)],
        [a*b*cosd(gam),  b*b,  b*c*cosd(alp)],
        [a*c*cosd(bet) ,b*c*cosd(alp),   c*c]])
    return g
           
def cell2Gmat(cell):
    """Compute real and reciprocal lattice metric tensor from unit cell constants

    :param cell: tuple with a,b,c,alpha, beta, gamma (degrees)
    :return: reciprocal (G) & real (g) metric tensors (list of two numpy 3x3 arrays)

    """
    g = fillgmat(cell)
    G = nl.inv(g)        
    return G,g

def A2Gmat(A,inverse=True):
    """Fill real & reciprocal metric tensor (G) from A.

    :param A: reciprocal metric tensor elements as [G11,G22,G33,2*G12,2*G13,2*G23]
    :param bool inverse: if True return both G and g; else just G
    :return: reciprocal (G) & real (g) metric tensors (list of two numpy 3x3 arrays)

    """
    G = np.zeros(shape=(3,3))
    G = [
        [A[0],  A[3]/2.,  A[4]/2.], 
        [A[3]/2.,A[1],    A[5]/2.], 
        [A[4]/2.,A[5]/2.,    A[2]]]
    if inverse:
        g = nl.inv(G)
        return G,g
    else:
        return G

def Gmat2A(G):
    """Extract A from reciprocal metric tensor (G)

    :param G: reciprocal maetric tensor (3x3 numpy array
    :return: A = [G11,G22,G33,2*G12,2*G13,2*G23]

    """
    return [G[0][0],G[1][1],G[2][2],2.*G[0][1],2.*G[0][2],2.*G[1][2]]
    
def cell2A(cell):
    """Obtain A = [G11,G22,G33,2*G12,2*G13,2*G23] from lattice parameters

    :param cell: [a,b,c,alpha,beta,gamma] (degrees)
    :return: G reciprocal metric tensor as 3x3 numpy array

    """
    G,g = cell2Gmat(cell)
    return Gmat2A(G)

def A2cell(A):
    """Compute unit cell constants from A

    :param A: [G11,G22,G33,2*G12,2*G13,2*G23] G - reciprocal metric tensor
    :return: a,b,c,alpha, beta, gamma (degrees) - lattice parameters

    """
    G,g = A2Gmat(A)
    return Gmat2cell(g)

def Gmat2cell(g):
    """Compute real/reciprocal lattice parameters from real/reciprocal metric tensor (g/G)
    The math works the same either way.

    :param g (or G): real (or reciprocal) metric tensor 3x3 array
    :return: a,b,c,alpha, beta, gamma (degrees) (or a*,b*,c*,alpha*,beta*,gamma* degrees)

    """
    oldset = np.seterr('raise')
    a = np.sqrt(max(0,g[0][0]))
    b = np.sqrt(max(0,g[1][1]))
    c = np.sqrt(max(0,g[2][2]))
    alp = acosd(g[2][1]/(b*c))
    bet = acosd(g[2][0]/(a*c))
    gam = acosd(g[0][1]/(a*b))
    np.seterr(**oldset)
    return a,b,c,alp,bet,gam

def invcell2Gmat(invcell):
    """Compute real and reciprocal lattice metric tensor from reciprocal 
       unit cell constants
       
    :param invcell: [a*,b*,c*,alpha*, beta*, gamma*] (degrees)
    :return: reciprocal (G) & real (g) metric tensors (list of two 3x3 arrays)

    """
    G = fillgmat(invcell)
    g = nl.inv(G)
    return G,g
        
def calc_rVsq(A):
    """Compute the square of the reciprocal lattice volume (1/V**2) from A'

    """
    G,g = A2Gmat(A)
    rVsq = nl.det(G)
    if rVsq < 0:
        return 1
    return rVsq
    
def calc_rV(A):
    """Compute the reciprocal lattice volume (V*) from A
    """
    return np.sqrt(calc_rVsq(A))
    
def calc_V(A):
    """Compute the real lattice volume (V) from A
    """
    return 1./calc_rV(A)

def A2invcell(A):
    """Compute reciprocal unit cell constants from A
    returns tuple with a*,b*,c*,alpha*, beta*, gamma* (degrees)
    """
    G,g = A2Gmat(A)
    return Gmat2cell(G)
    
def Gmat2AB(G):
    """Computes orthogonalization matrix from reciprocal metric tensor G

    :returns: tuple of two 3x3 numpy arrays (A,B)

       * A for crystal to Cartesian transformations A*x = np.inner(A,x) = X 
       * B (= inverse of A) for Cartesian to crystal transformation B*X = np.inner(B,X) = x

    """
    cellstar = Gmat2cell(G)
    g = nl.inv(G)
    cell = Gmat2cell(g)
    A = np.zeros(shape=(3,3))
    # from Giacovazzo (Fundamentals 2nd Ed.) p.75
    A[0][0] = cell[0]                # a
    A[0][1] = cell[1]*cosd(cell[5])  # b cos(gamma)
    A[0][2] = cell[2]*cosd(cell[4])  # c cos(beta)
    A[1][1] = cell[1]*sind(cell[5])  # b sin(gamma)
    A[1][2] = -cell[2]*cosd(cellstar[3])*sind(cell[4]) # - c cos(alpha*) sin(beta)
    A[2][2] = 1/cellstar[2]         # 1/c*
    B = nl.inv(A)
    return A,B
    

def cell2AB(cell):
    """Computes orthogonalization matrix from unit cell constants

    :param tuple cell: a,b,c, alpha, beta, gamma (degrees)
    :returns: tuple of two 3x3 numpy arrays (A,B)
       A for crystal to Cartesian transformations A*x = np.inner(A,x) = X 
       B (= inverse of A) for Cartesian to crystal transformation B*X = np.inner(B,X) = x
    """
    G,g = cell2Gmat(cell) 
    cellstar = Gmat2cell(G)
    A = np.zeros(shape=(3,3))
    # from Giacovazzo (Fundamentals 2nd Ed.) p.75
    A[0][0] = cell[0]                # a
    A[0][1] = cell[1]*cosd(cell[5])  # b cos(gamma)
    A[0][2] = cell[2]*cosd(cell[4])  # c cos(beta)
    A[1][1] = cell[1]*sind(cell[5])  # b sin(gamma)
    A[1][2] = -cell[2]*cosd(cellstar[3])*sind(cell[4]) # - c cos(alpha*) sin(beta)
    A[2][2] = 1/cellstar[2]         # 1/c*
    B = nl.inv(A)
    return A,B
    
def U6toUij(U6):
    """Fill matrix (Uij) from U6 = [U11,U22,U33,U12,U13,U23]
    NB: there is a non numpy version in GSASIIspc: U2Uij

    :param list U6: 6 terms of u11,u22,...
    :returns:
        Uij - numpy [3][3] array of uij
    """
    U = np.array([
        [U6[0],  U6[3]/2.,  U6[4]/2.], 
        [U6[3]/2.,  U6[1],  U6[5]/2.], 
        [U6[4]/2.,  U6[5]/2.,  U6[2]]])
    return U

def UijtoU6(U):
    """Fill vector [U11,U22,U33,U12,U13,U23] from Uij 
    NB: there is a non numpy version in GSASIIspc: Uij2U
    """
    U6 = np.array([U[0][0],U[1][1],U[2][2],U[0][1]*2.,U[0][2]*2.,U[1][2]*2.])
    return U6

def Uij2betaij(Uij,G):
    """
    Convert Uij to beta-ij tensors -- stub for eventual completion
    
    :param Uij: numpy array [Uij]
    :param G: reciprocal metric tensor
    :returns: beta-ij - numpy array [beta-ij]
    """
    pass
    
def cell2GS(cell):
    ''' returns Uij to betaij conversion matrix'''
    G,g = cell2Gmat(cell)
    GS = G
    GS[0][1] = GS[1][0] = math.sqrt(GS[0][0]*GS[1][1])
    GS[0][2] = GS[2][0] = math.sqrt(GS[0][0]*GS[2][2])
    GS[1][2] = GS[2][1] = math.sqrt(GS[1][1]*GS[2][2])
    return GS    
    
def Uij2Ueqv(Uij,GS,Amat):
    ''' returns 1/3 trace of diagonalized U matrix'''
    U = np.multiply(U6toUij(Uij),GS)
    U = np.inner(Amat,np.inner(U,Amat).T)
    E,R = nl.eigh(U)
    return np.sum(E)/3.
        
def CosAngle(U,V,G):
    """ calculate cos of angle between U & V in generalized coordinates 
    defined by metric tensor G

    :param U: 3-vectors assume numpy arrays, can be multiple reflections as (N,3) array
    :param V: 3-vectors assume numpy arrays, only as (3) vector
    :param G: metric tensor for U & V defined space assume numpy array
    :returns:
        cos(phi)
    """
    u = (U.T/np.sqrt(np.sum(np.inner(U,G)*U,axis=1))).T
    v = V/np.sqrt(np.inner(V,np.inner(G,V)))
    cosP = np.inner(u,np.inner(G,v))
    return cosP
    
def CosSinAngle(U,V,G):
    """ calculate sin & cos of angle between U & V in generalized coordinates 
    defined by metric tensor G

    :param U: 3-vectors assume numpy arrays
    :param V: 3-vectors assume numpy arrays
    :param G: metric tensor for U & V defined space assume numpy array
    :returns:
        cos(phi) & sin(phi)
    """
    u = U/np.sqrt(np.inner(U,np.inner(G,U)))
    v = V/np.sqrt(np.inner(V,np.inner(G,V)))
    cosP = np.inner(u,np.inner(G,v))
    sinP = np.sqrt(max(0.0,1.0-cosP**2))
    return cosP,sinP
    
def criticalEllipse(prob):
    """
    Calculate critical values for probability ellipsoids from probability
    """
    if not ( 0.01 <= prob < 1.0):
        return 1.54 
    coeff = np.array([6.44988E-09,4.16479E-07,1.11172E-05,1.58767E-04,0.00130554,
        0.00604091,0.0114921,-0.040301,-0.6337203,1.311582])
    llpr = math.log(-math.log(prob))
    return np.polyval(coeff,llpr)
    
def CellBlock(nCells):
    """
    Generate block of unit cells n*n*n on a side; [0,0,0] centered, n = 2*nCells+1
    currently only works for nCells = 0 or 1 (not >1)
    """
    if nCells:
        N = 2*nCells+1
        N2 = N*N
        N3 = N*N*N
        cellArray = []
        A = np.array(range(N3))
        cellGen = np.array([A/N2-1,A/N%N-1,A%N-1]).T
        for cell in cellGen:
            cellArray.append(cell)
        return cellArray
    else:
        return [0,0,0]
        
def CellAbsorption(ElList,Volume):
    '''Compute unit cell absorption

    :param dict ElList: dictionary of element contents including mu and
      number of atoms be cell
    :param float Volume: unit cell volume
    :returns: mu-total/Volume
    '''
    muT = 0
    for El in ElList:
        muT += ElList[El]['mu']*ElList[El]['FormulaNo']
    return muT/Volume
    
#Permutations and Combinations
# Four routines: combinations,uniqueCombinations, selections & permutations
#These taken from Python Cookbook, 2nd Edition. 19.15 p724-726
#    
def _combinators(_handle, items, n):
    """ factored-out common structure of all following combinators """
    if n==0:
        yield [ ]
        return
    for i, item in enumerate(items):
        this_one = [ item ]
        for cc in _combinators(_handle, _handle(items, i), n-1):
            yield this_one + cc
def combinations(items, n):
    """ take n distinct items, order matters """
    def skipIthItem(items, i):
        return items[:i] + items[i+1:]
    return _combinators(skipIthItem, items, n)
def uniqueCombinations(items, n):
    """ take n distinct items, order is irrelevant """
    def afterIthItem(items, i):
        return items[i+1:]
    return _combinators(afterIthItem, items, n)
def selections(items, n):
    """ take n (not necessarily distinct) items, order matters """
    def keepAllItems(items, i):
        return items
    return _combinators(keepAllItems, items, n)
def permutations(items):
    """ take all items, order matters """
    return combinations(items, len(items))

#reflection generation routines
#for these: H = [h,k,l]; A is as used in calc_rDsq; G - inv metric tensor, g - metric tensor; 
#           cell - a,b,c,alp,bet,gam in A & deg
   
def Pos2dsp(Inst,pos):
    ''' convert powder pattern position (2-theta or TOF, musec) to d-spacing
    '''
    if 'C' in Inst['Type'][0]:
        wave = G2mth.getWave(Inst)
        return wave/(2.0*sind((pos-Inst.get('Zero',[0,0])[1])/2.0))
    else:   #'T'OF - ignore difB
        return TOF2dsp(Inst,pos)
        
def TOF2dsp(Inst,Pos):
    ''' convert powder pattern TOF, musec to d-spacing by successive approximation
    Pos can be numpy array
    '''
    def func(d,pos,Inst):        
        return (pos-Inst['difA'][1]*d**2-Inst['Zero'][1]-Inst['difB'][1]/d)/Inst['difC'][1]
    dsp0 = np.ones_like(Pos)
    while True:      #successive approximations
        dsp = func(dsp0,Pos,Inst)
        if np.allclose(dsp,dsp0,atol=0.000001):
            return dsp
        dsp0 = dsp
    
def Dsp2pos(Inst,dsp):
    ''' convert d-spacing to powder pattern position (2-theta or TOF, musec)
    '''
    if 'C' in Inst['Type'][0]:
        wave = G2mth.getWave(Inst)
        pos = 2.0*asind(wave/(2.*dsp))+Inst.get('Zero',[0,0])[1]             
    else:   #'T'OF
        pos = Inst['difC'][1]*dsp+Inst['Zero'][1]+Inst['difA'][1]*dsp**2+Inst.get('difB',[0,0,False])[1]/dsp
    return pos
    
def getPeakPos(dataType,parmdict,dsp):
    ''' convert d-spacing to powder pattern position (2-theta or TOF, musec)
    '''
    if 'C' in dataType:
        pos = 2.0*asind(parmdict['Lam']/(2.*dsp))+parmdict['Zero']
    else:   #'T'OF
        pos = parmdict['difC']*dsp+parmdict['difA']*dsp**2+parmdict['difB']/dsp+parmdict['Zero']
    return pos
                   
def calc_rDsq(H,A):
    'needs doc string'
    rdsq = H[0]*H[0]*A[0]+H[1]*H[1]*A[1]+H[2]*H[2]*A[2]+H[0]*H[1]*A[3]+H[0]*H[2]*A[4]+H[1]*H[2]*A[5]
    return rdsq
    
def calc_rDsq2(H,G):
    'needs doc string'
    return np.inner(H,np.inner(G,H))
    
def calc_rDsqSS(H,A,vec):
    'needs doc string'
    rdsq = calc_rDsq(H[:3]+(H[3]*vec).T,A)
    return rdsq
       
def calc_rDsqZ(H,A,Z,tth,lam):
    'needs doc string'
    rdsq = calc_rDsq(H,A)+Z*sind(tth)*2.0*rpd/lam**2
    return rdsq
       
def calc_rDsqZSS(H,A,vec,Z,tth,lam):
    'needs doc string'
    rdsq = calc_rDsq(H[:3]+(H[3][:,np.newaxis]*vec).T,A)+Z*sind(tth)*2.0*rpd/lam**2
    return rdsq
       
def calc_rDsqT(H,A,Z,tof,difC):
    'needs doc string'
    rdsq = calc_rDsq(H,A)+Z/difC
    return rdsq
       
def calc_rDsqTSS(H,A,vec,Z,tof,difC):
    'needs doc string'
    rdsq = calc_rDsq(H[:3]+H[3][:,np.newaxis]*vec,A)+Z/difC
    return rdsq
       
def MaxIndex(dmin,A):
    'needs doc string'
    Hmax = [0,0,0]
    try:
        cell = A2cell(A)
    except:
        cell = [1,1,1,90,90,90]
    for i in range(3):
        Hmax[i] = int(round(cell[i]/dmin))
    return Hmax
    
def sortHKLd(HKLd,ifreverse,ifdup,ifSS=False):
    '''needs doc string

    :param HKLd: a list of [h,k,l,d,...];
    :param ifreverse: True for largest d first
    :param ifdup: True if duplicate d-spacings allowed
    '''
    T = []
    N = 3
    if ifSS:
        N = 4
    for i,H in enumerate(HKLd):
        if ifdup:
            T.append((H[N],i))
        else:
            T.append(H[N])            
    D = dict(zip(T,HKLd))
    T.sort()
    if ifreverse:
        T.reverse()
    X = []
    okey = ''
    for key in T: 
        if key != okey: X.append(D[key])    #remove duplicate d-spacings
        okey = key
    return X
    
def SwapIndx(Axis,H):
    'needs doc string'
    if Axis in [1,-1]:
        return H
    elif Axis in [2,-3]:
        return [H[1],H[2],H[0]]
    else:
        return [H[2],H[0],H[1]]
        
def Rh2Hx(Rh):
    'needs doc string'
    Hx = [0,0,0]
    Hx[0] = Rh[0]-Rh[1]
    Hx[1] = Rh[1]-Rh[2]
    Hx[2] = np.sum(Rh)
    return Hx
    
def Hx2Rh(Hx):
    'needs doc string'
    Rh = [0,0,0]
    itk = -Hx[0]+Hx[1]+Hx[2]
    if itk%3 != 0:
        return 0        #error - not rhombohedral reflection
    else:
        Rh[1] = itk/3
        Rh[0] = Rh[1]+Hx[0]
        Rh[2] = Rh[1]-Hx[1]
        if Rh[0] < 0:
            for i in range(3):
                Rh[i] = -Rh[i]
        return Rh
        
def CentCheck(Cent,H):
    'needs doc string'
    h,k,l = H
    if Cent == 'A' and (k+l)%2:
        return False
    elif Cent == 'B' and (h+l)%2:
        return False
    elif Cent == 'C' and (h+k)%2:
        return False
    elif Cent == 'I' and (h+k+l)%2:
        return False
    elif Cent == 'F' and ((h+k)%2 or (h+l)%2 or (k+l)%2):
        return False
    elif Cent == 'R' and (-h+k+l)%3:
        return False
    else:
        return True
                                    
def GetBraviasNum(center,system):
    """Determine the Bravais lattice number, as used in GenHBravais
    
    :param center: one of: 'P', 'C', 'I', 'F', 'R' (see SGLatt from GSASIIspc.SpcGroup)
    :param system: one of 'cubic', 'hexagonal', 'tetragonal', 'orthorhombic', 'trigonal' (for R)
      'monoclinic', 'triclinic' (see SGSys from GSASIIspc.SpcGroup)
    :return: a number between 0 and 13 
      or throws a ValueError exception if the combination of center, system is not found (i.e. non-standard)

    """
    if center.upper() == 'F' and system.lower() == 'cubic':
        return 0
    elif center.upper() == 'I' and system.lower() == 'cubic':
        return 1
    elif center.upper() == 'P' and system.lower() == 'cubic':
        return 2
    elif center.upper() == 'R' and system.lower() == 'trigonal':
        return 3
    elif center.upper() == 'P' and system.lower() == 'hexagonal':
        return 4
    elif center.upper() == 'I' and system.lower() == 'tetragonal':
        return 5
    elif center.upper() == 'P' and system.lower() == 'tetragonal':
        return 6
    elif center.upper() == 'F' and system.lower() == 'orthorhombic':
        return 7
    elif center.upper() == 'I' and system.lower() == 'orthorhombic':
        return 8
    elif center.upper() == 'C' and system.lower() == 'orthorhombic':
        return 9
    elif center.upper() == 'P' and system.lower() == 'orthorhombic':
        return 10
    elif center.upper() == 'C' and system.lower() == 'monoclinic':
        return 11
    elif center.upper() == 'P' and system.lower() == 'monoclinic':
        return 12
    elif center.upper() == 'P' and system.lower() == 'triclinic':
        return 13
    raise ValueError,'non-standard Bravais lattice center=%s, cell=%s' % (center,system)

def GenHBravais(dmin,Bravais,A):
    """Generate the positionally unique powder diffraction reflections
     
    :param dmin: minimum d-spacing in A
    :param Bravais: lattice type (see GetBraviasNum). Bravais is one of::
             0 F cubic
             1 I cubic
             2 P cubic
             3 R hexagonal (trigonal not rhombohedral)
             4 P hexagonal
             5 I tetragonal
             6 P tetragonal
             7 F orthorhombic
             8 I orthorhombic
             9 C orthorhombic
             10 P orthorhombic
             11 C monoclinic
             12 P monoclinic
             13 P triclinic
            
    :param A: reciprocal metric tensor elements as [G11,G22,G33,2*G12,2*G13,2*G23]
    :return: HKL unique d list of [h,k,l,d,-1] sorted with largest d first
            
    """
    import math
    if Bravais in [9,11]:
        Cent = 'C'
    elif Bravais in [1,5,8]:
        Cent = 'I'
    elif Bravais in [0,7]:
        Cent = 'F'
    elif Bravais in [3]:
        Cent = 'R'
    else:
        Cent = 'P'
    Hmax = MaxIndex(dmin,A)
    dminsq = 1./(dmin**2)
    HKL = []
    if Bravais == 13:                       #triclinic
        for l in range(-Hmax[2],Hmax[2]+1):
            for k in range(-Hmax[1],Hmax[1]+1):
                hmin = 0
                if (k < 0): hmin = 1
                if (k ==0 and l < 0): hmin = 1
                for h in range(hmin,Hmax[0]+1):
                    H=[h,k,l]
                    rdsq = calc_rDsq(H,A)
                    if 0 < rdsq <= dminsq:
                        HKL.append([h,k,l,rdsq2d(rdsq,6),-1])
    elif Bravais in [11,12]:                #monoclinic - b unique
        Hmax = SwapIndx(2,Hmax)
        for h in range(Hmax[0]+1):
            for k in range(-Hmax[1],Hmax[1]+1):
                lmin = 0
                if k < 0:lmin = 1
                for l in range(lmin,Hmax[2]+1):
                    [h,k,l] = SwapIndx(-2,[h,k,l])
                    H = []
                    if CentCheck(Cent,[h,k,l]): H=[h,k,l]
                    if H:
                        rdsq = calc_rDsq(H,A)
                        if 0 < rdsq <= dminsq:
                            HKL.append([h,k,l,rdsq2d(rdsq,6),-1])
                    [h,k,l] = SwapIndx(2,[h,k,l])
    elif Bravais in [7,8,9,10]:            #orthorhombic
        for h in range(Hmax[0]+1):
            for k in range(Hmax[1]+1):
                for l in range(Hmax[2]+1):
                    H = []
                    if CentCheck(Cent,[h,k,l]): H=[h,k,l]
                    if H:
                        rdsq = calc_rDsq(H,A)
                        if 0 < rdsq <= dminsq:
                            HKL.append([h,k,l,rdsq2d(rdsq,6),-1])
    elif Bravais in [5,6]:                  #tetragonal
        for l in range(Hmax[2]+1):
            for k in range(Hmax[1]+1):
                for h in range(k,Hmax[0]+1):
                    H = []
                    if CentCheck(Cent,[h,k,l]): H=[h,k,l]
                    if H:
                        rdsq = calc_rDsq(H,A)
                        if 0 < rdsq <= dminsq:
                            HKL.append([h,k,l,rdsq2d(rdsq,6),-1])
    elif Bravais in [3,4]:
        lmin = 0
        if Bravais == 3: lmin = -Hmax[2]                  #hexagonal/trigonal
        for l in range(lmin,Hmax[2]+1):
            for k in range(Hmax[1]+1):
                hmin = k
                if l < 0: hmin += 1
                for h in range(hmin,Hmax[0]+1):
                    H = []
                    if CentCheck(Cent,[h,k,l]): H=[h,k,l]
                    if H:
                        rdsq = calc_rDsq(H,A)
                        if 0 < rdsq <= dminsq:
                            HKL.append([h,k,l,rdsq2d(rdsq,6),-1])

    else:                                   #cubic
        for l in range(Hmax[2]+1):
            for k in range(l,Hmax[1]+1):
                for h in range(k,Hmax[0]+1):
                    H = []
                    if CentCheck(Cent,[h,k,l]): H=[h,k,l]
                    if H:
                        rdsq = calc_rDsq(H,A)
                        if 0 < rdsq <= dminsq:
                            HKL.append([h,k,l,rdsq2d(rdsq,6),-1])
    return sortHKLd(HKL,True,False)
    
def getHKLmax(dmin,SGData,A):
    'finds maximum allowed hkl for given A within dmin'
    SGLaue = SGData['SGLaue']
    if SGLaue in ['3R','3mR']:        #Rhombohedral axes
        Hmax = [0,0,0]
        cell = A2cell(A)
        aHx = cell[0]*math.sqrt(2.0*(1.0-cosd(cell[3])))
        cHx = cell[0]*math.sqrt(3.0*(1.0+2.0*cosd(cell[3])))
        Hmax[0] = Hmax[1] = int(round(aHx/dmin))
        Hmax[2] = int(round(cHx/dmin))
        #print Hmax,aHx,cHx
    else:                           # all others
        Hmax = MaxIndex(dmin,A)
    return Hmax
    
def GenHLaue(dmin,SGData,A):
    """Generate the crystallographically unique powder diffraction reflections
    for a lattice and Bravais type
    
    :param dmin: minimum d-spacing
    :param SGData: space group dictionary with at least
    
        * 'SGLaue': Laue group symbol: one of '-1','2/m','mmm','4/m','6/m','4/mmm','6/mmm', '3m1', '31m', '3', '3R', '3mR', 'm3', 'm3m'
        * 'SGLatt': lattice centering: one of 'P','A','B','C','I','F'
        * 'SGUniq': code for unique monoclinic axis one of 'a','b','c' (only if 'SGLaue' is '2/m') otherwise an empty string
        
    :param A: reciprocal metric tensor elements as [G11,G22,G33,2*G12,2*G13,2*G23]
    :return: HKL = list of [h,k,l,d] sorted with largest d first and is unique 
            part of reciprocal space ignoring anomalous dispersion
            
    """
    import math
    SGLaue = SGData['SGLaue']
    SGLatt = SGData['SGLatt']
    SGUniq = SGData['SGUniq']
    #finds maximum allowed hkl for given A within dmin
    Hmax = getHKLmax(dmin,SGData,A)
        
    dminsq = 1./(dmin**2)
    HKL = []
    if SGLaue == '-1':                       #triclinic
        for l in range(-Hmax[2],Hmax[2]+1):
            for k in range(-Hmax[1],Hmax[1]+1):
                hmin = 0
                if (k < 0) or (k ==0 and l < 0): hmin = 1
                for h in range(hmin,Hmax[0]+1):
                    H = []
                    if CentCheck(SGLatt,[h,k,l]): H=[h,k,l]
                    if H:
                        rdsq = calc_rDsq(H,A)
                        if 0 < rdsq <= dminsq:
                            HKL.append([h,k,l,1/math.sqrt(rdsq)])
    elif SGLaue == '2/m':                #monoclinic
        axisnum = 1 + ['a','b','c'].index(SGUniq)
        Hmax = SwapIndx(axisnum,Hmax)
        for h in range(Hmax[0]+1):
            for k in range(-Hmax[1],Hmax[1]+1):
                lmin = 0
                if k < 0:lmin = 1
                for l in range(lmin,Hmax[2]+1):
                    [h,k,l] = SwapIndx(-axisnum,[h,k,l])
                    H = []
                    if CentCheck(SGLatt,[h,k,l]): H=[h,k,l]
                    if H:
                        rdsq = calc_rDsq(H,A)
                        if 0 < rdsq <= dminsq:
                            HKL.append([h,k,l,1/math.sqrt(rdsq)])
                    [h,k,l] = SwapIndx(axisnum,[h,k,l])
    elif SGLaue in ['mmm','4/m','6/m']:            #orthorhombic
        for l in range(Hmax[2]+1):
            for h in range(Hmax[0]+1):
                kmin = 1
                if SGLaue == 'mmm' or h ==0: kmin = 0
                for k in range(kmin,Hmax[1]+1):
                    H = []
                    if CentCheck(SGLatt,[h,k,l]): H=[h,k,l]
                    if H:
                        rdsq = calc_rDsq(H,A)
                        if 0 < rdsq <= dminsq:
                            HKL.append([h,k,l,1/math.sqrt(rdsq)])
    elif SGLaue in ['4/mmm','6/mmm']:                  #tetragonal & hexagonal
        for l in range(Hmax[2]+1):
            for h in range(Hmax[0]+1):
                for k in range(h+1):
                    H = []
                    if CentCheck(SGLatt,[h,k,l]): H=[h,k,l]
                    if H:
                        rdsq = calc_rDsq(H,A)
                        if 0 < rdsq <= dminsq:
                            HKL.append([h,k,l,1/math.sqrt(rdsq)])
    elif SGLaue in ['3m1','31m','3','3R','3mR']:                  #trigonals
        for l in range(-Hmax[2],Hmax[2]+1):
            hmin = 0
            if l < 0: hmin = 1
            for h in range(hmin,Hmax[0]+1):
                if SGLaue in ['3R','3']:
                    kmax = h
                    kmin = -int((h-1.)/2.)
                else:
                    kmin = 0
                    kmax = h
                    if SGLaue in ['3m1','3mR'] and l < 0: kmax = h-1
                    if SGLaue == '31m' and l < 0: kmin = 1
                for k in range(kmin,kmax+1):
                    H = []
                    if CentCheck(SGLatt,[h,k,l]): H=[h,k,l]
                    if SGLaue in ['3R','3mR']:
                        H = Hx2Rh(H)
                    if H:
                        rdsq = calc_rDsq(H,A)
                        if 0 < rdsq <= dminsq:
                            HKL.append([H[0],H[1],H[2],1/math.sqrt(rdsq)])
    else:                                   #cubic
        for h in range(Hmax[0]+1):
            for k in range(h+1):
                lmin = 0
                lmax = k
                if SGLaue =='m3':
                    lmax = h-1
                    if h == k: lmax += 1
                for l in range(lmin,lmax+1):
                    H = []
                    if CentCheck(SGLatt,[h,k,l]): H=[h,k,l]
                    if H:
                        rdsq = calc_rDsq(H,A)
                        if 0 < rdsq <= dminsq:
                            HKL.append([h,k,l,1/math.sqrt(rdsq)])
    return sortHKLd(HKL,True,True)
    
def GenPfHKLs(nMax,SGData,A):    
    """Generate the unique pole figure reflections for a lattice and Bravais type. 
    Min d-spacing=1.0A & no more than nMax returned
    
    :param nMax: maximum number of hkls returned
    :param SGData: space group dictionary with at least
    
        * 'SGLaue': Laue group symbol: one of '-1','2/m','mmm','4/m','6/m','4/mmm','6/mmm', '3m1', '31m', '3', '3R', '3mR', 'm3', 'm3m'
        * 'SGLatt': lattice centering: one of 'P','A','B','C','I','F'
        * 'SGUniq': code for unique monoclinic axis one of 'a','b','c' (only if 'SGLaue' is '2/m') otherwise an empty string
        
    :param A: reciprocal metric tensor elements as [G11,G22,G33,2*G12,2*G13,2*G23]
    :return: HKL = list of 'h k l' strings sorted with largest d first; no duplicate zones
            
    """
    HKL = np.array(GenHLaue(1.0,SGData,A)).T[:3].T     #strip d-spacings
    N = min(nMax,len(HKL))
    return ['%d %d %d'%(h[0],h[1],h[2]) for h in HKL[:N]]        
        

def GenSSHLaue(dmin,SGData,SSGData,Vec,maxH,A):
    'needs a doc string'
    HKLs = []
    vec = np.array(Vec)
    vstar = np.sqrt(calc_rDsq(vec,A))     #find extra needed for -n SS reflections
    dvec = 1./(maxH*vstar+1./dmin)
    HKL = GenHLaue(dvec,SGData,A)        
    SSdH = [vec*h for h in range(-maxH,maxH+1)]
    SSdH = dict(zip(range(-maxH,maxH+1),SSdH))
    for h,k,l,d in HKL:
        ext = G2spc.GenHKLf([h,k,l],SGData)[0]  #h,k,l must be integral values here
        if not ext and d >= dmin:
            HKLs.append([h,k,l,0,d])
        for dH in SSdH:
            if dH:
                DH = SSdH[dH]
                H = [h+DH[0],k+DH[1],l+DH[2]]
                d = 1/np.sqrt(calc_rDsq(H,A))
                if d >= dmin:
                    HKLM = np.array([h,k,l,dH])
                    if G2spc.checkSSLaue([h,k,l,dH],SGData,SSGData) and G2spc.checkSSextc(HKLM,SSGData):
                        HKLs.append([h,k,l,dH,d])    
    return HKLs

#Spherical harmonics routines
def OdfChk(SGLaue,L,M):
    'needs doc string'
    if not L%2 and abs(M) <= L:
        if SGLaue == '0':                      #cylindrical symmetry
            if M == 0: return True
        elif SGLaue == '-1':
            return True
        elif SGLaue == '2/m':
            if not abs(M)%2: return True
        elif SGLaue == 'mmm':
            if not abs(M)%2 and M >= 0: return True
        elif SGLaue == '4/m':
            if not abs(M)%4: return True
        elif SGLaue == '4/mmm':
            if not abs(M)%4 and M >= 0: return True
        elif SGLaue in ['3R','3']:
            if not abs(M)%3: return True
        elif SGLaue in ['3mR','3m1','31m']:
            if not abs(M)%3 and M >= 0: return True
        elif SGLaue == '6/m':
            if not abs(M)%6: return True
        elif SGLaue == '6/mmm':
            if not abs(M)%6 and M >= 0: return True
        elif SGLaue == 'm3':
            if M > 0:
                if L%12 == 2:
                    if M <= L/12: return True
                else:
                    if M <= L/12+1: return True
        elif SGLaue == 'm3m':
            if M > 0:
                if L%12 == 2:
                    if M <= L/12: return True
                else:
                    if M <= L/12+1: return True
    return False
        
def GenSHCoeff(SGLaue,SamSym,L,IfLMN=True):
    'needs doc string'
    coeffNames = []
    for iord in [2*i+2 for i in range(L/2)]:
        for m in [i-iord for i in range(2*iord+1)]:
            if OdfChk(SamSym,iord,m):
                for n in [i-iord for i in range(2*iord+1)]:
                    if OdfChk(SGLaue,iord,n):
                        if IfLMN:
                            coeffNames.append('C(%d,%d,%d)'%(iord,m,n))
                        else:
                            coeffNames.append('C(%d,%d)'%(iord,n))
    return coeffNames
    
def CrsAng(H,cell,SGData):
    'needs doc string'
    a,b,c,al,be,ga = cell
    SQ3 = 1.732050807569
    H1 = np.array([1,0,0])
    H2 = np.array([0,1,0])
    H3 = np.array([0,0,1])
    H4 = np.array([1,1,1])
    G,g = cell2Gmat(cell)
    Laue = SGData['SGLaue']
    Naxis = SGData['SGUniq']
    if len(H.shape) == 1:
        DH = np.inner(H,np.inner(G,H))
    else:
        DH = np.array([np.inner(h,np.inner(G,h)) for h in H])
    if Laue == '2/m':
        if Naxis == 'a':
            DR = np.inner(H1,np.inner(G,H1))
            DHR = np.inner(H,np.inner(G,H1))
        elif Naxis == 'b':
            DR = np.inner(H2,np.inner(G,H2))
            DHR = np.inner(H,np.inner(G,H2))
        else:
            DR = np.inner(H3,np.inner(G,H3))
            DHR = np.inner(H,np.inner(G,H3))
    elif Laue in ['R3','R3m']:
        DR = np.inner(H4,np.inner(G,H4))
        DHR = np.inner(H,np.inner(G,H4))
    else:
        DR = np.inner(H3,np.inner(G,H3))
        DHR = np.inner(H,np.inner(G,H3))
    DHR /= np.sqrt(DR*DH)
    phi = np.where(DHR <= 1.0,acosd(DHR),0.0)
    if Laue == '-1':
        BA = H.T[1]*a/(b-H.T[0]*cosd(ga))
        BB = H.T[0]*sind(ga)**2
    elif Laue == '2/m':
        if Naxis == 'a':
            BA = H.T[2]*b/(c-H.T[1]*cosd(al))
            BB = H.T[1]*sind(al)**2
        elif Naxis == 'b':
            BA = H.T[0]*c/(a-H.T[2]*cosd(be))
            BB = H.T[2]*sind(be)**2
        else:
            BA = H.T[1]*a/(b-H.T[0]*cosd(ga))
            BB = H.T[0]*sind(ga)**2
    elif Laue in ['mmm','4/m','4/mmm']:
        BA = H.T[1]*a
        BB = H.T[0]*b
    elif Laue in ['3R','3mR']:
        BA = H.T[0]+H.T[1]-2.0*H.T[2]
        BB = SQ3*(H.T[0]-H.T[1])
    elif Laue in ['m3','m3m']:
        BA = H.T[1]
        BB = H.T[0]
    else:
        BA = H.T[0]+2.0*H.T[1]
        BB = SQ3*H.T[0]
    beta = atan2d(BA,BB)
    return phi,beta
    
def SamAng(Tth,Gangls,Sangl,IFCoup):
    """Compute sample orientation angles vs laboratory coord. system

    :param Tth:        Signed theta                                   
    :param Gangls:     Sample goniometer angles phi,chi,omega,azmuth  
    :param Sangl:      Sample angle zeros om-0, chi-0, phi-0          
    :param IFCoup:     True if omega & 2-theta coupled in CW scan
    :returns:  
        psi,gam:    Sample odf angles                              
        dPSdA,dGMdA:    Angle zero derivatives
    """                         
    
    if IFCoup:
        GSomeg = sind(Gangls[2]+Tth)
        GComeg = cosd(Gangls[2]+Tth)
    else:
        GSomeg = sind(Gangls[2])
        GComeg = cosd(Gangls[2])
    GSTth = sind(Tth)
    GCTth = cosd(Tth)      
    GSazm = sind(Gangls[3])
    GCazm = cosd(Gangls[3])
    GSchi = sind(Gangls[1])
    GCchi = cosd(Gangls[1])
    GSphi = sind(Gangls[0]+Sangl[2])
    GCphi = cosd(Gangls[0]+Sangl[2])
    SSomeg = sind(Sangl[0])
    SComeg = cosd(Sangl[0])
    SSchi = sind(Sangl[1])
    SCchi = cosd(Sangl[1])
    AT = -GSTth*GComeg+GCTth*GCazm*GSomeg
    BT = GSTth*GSomeg+GCTth*GCazm*GComeg
    CT = -GCTth*GSazm*GSchi
    DT = -GCTth*GSazm*GCchi
    
    BC1 = -AT*GSphi+(CT+BT*GCchi)*GCphi
    BC2 = DT-BT*GSchi
    BC3 = AT*GCphi+(CT+BT*GCchi)*GSphi
      
    BC = BC1*SComeg*SCchi+BC2*SComeg*SSchi-BC3*SSomeg      
    psi = acosd(BC)
    
    BD = 1.0-BC**2
    C = np.where(BD>1.e-6,rpd/np.sqrt(BD),0.)
    dPSdA = [-C*(-BC1*SSomeg*SCchi-BC2*SSomeg*SSchi-BC3*SComeg),
        -C*(-BC1*SComeg*SSchi+BC2*SComeg*SCchi),
        -C*(-BC1*SSomeg-BC3*SComeg*SCchi)]
      
    BA = -BC1*SSchi+BC2*SCchi
    BB = BC1*SSomeg*SCchi+BC2*SSomeg*SSchi+BC3*SComeg
    gam = atan2d(BB,BA)

    BD = (BA**2+BB**2)/rpd

    dBAdO = 0
    dBAdC = -BC1*SCchi-BC2*SSchi
    dBAdF = BC3*SSchi
    
    dBBdO = BC1*SComeg*SCchi+BC2*SComeg*SSchi-BC3*SSomeg
    dBBdC = -BC1*SSomeg*SSchi+BC2*SSomeg*SCchi
    dBBdF = BC1*SComeg-BC3*SSomeg*SCchi
    
    dGMdA = np.where(BD > 1.e-6,[(BA*dBBdO-BB*dBAdO)/BD,(BA*dBBdC-BB*dBAdC)/BD, \
        (BA*dBBdF-BB*dBAdF)/BD],[np.zeros_like(BD),np.zeros_like(BD),np.zeros_like(BD)])
        
    return psi,gam,dPSdA,dGMdA

BOH = {
'L=2':[[],[],[]],
'L=4':[[0.30469720,0.36418281],[],[]],
'L=6':[[-0.14104740,0.52775103],[],[]],
'L=8':[[0.28646862,0.21545346,0.32826995],[],[]],
'L=10':[[-0.16413497,0.33078546,0.39371345],[],[]],
'L=12':[[0.26141975,0.27266871,0.03277460,0.32589402],
    [0.09298802,-0.23773812,0.49446631,0.0],[]],
'L=14':[[-0.17557309,0.25821932,0.27709173,0.33645360],[],[]],
'L=16':[[0.24370673,0.29873515,0.06447688,0.00377,0.32574495],
    [0.12039646,-0.25330128,0.23950998,0.40962508,0.0],[]],
'L=18':[[-0.16914245,0.17017340,0.34598142,0.07433932,0.32696037],
    [-0.06901768,0.16006562,-0.24743528,0.47110273,0.0],[]],
'L=20':[[0.23067026,0.31151832,0.09287682,0.01089683,0.00037564,0.32573563],
    [0.13615420,-0.25048007,0.12882081,0.28642879,0.34620433,0.0],[]],
'L=22':[[-0.16109560,0.10244188,0.36285175,0.13377513,0.01314399,0.32585583],
    [-0.09620055,0.20244115,-0.22389483,0.17928946,0.42017231,0.0],[]],
'L=24':[[0.22050742,0.31770654,0.11661736,0.02049853,0.00150861,0.00003426,0.32573505],
    [0.13651722,-0.21386648,0.00522051,0.33939435,0.10837396,0.32914497,0.0],
    [0.05378596,-0.11945819,0.16272298,-0.26449730,0.44923956,0.0,0.0]],
'L=26':[[-0.15435003,0.05261630,0.35524646,0.18578869,0.03259103,0.00186197,0.32574594],
    [-0.11306511,0.22072681,-0.18706142,0.05439948,0.28122966,0.35634355,0.0],[]],
'L=28':[[0.21225019,0.32031716,0.13604702,0.03132468,0.00362703,0.00018294,0.00000294,0.32573501],
    [0.13219496,-0.17206256,-0.08742608,0.32671661,0.17973107,0.02567515,0.32619598,0.0],
    [0.07989184,-0.16735346,0.18839770,-0.20705337,0.12926808,0.42715602,0.0,0.0]],
'L=30':[[-0.14878368,0.01524973,0.33628434,0.22632587,0.05790047,0.00609812,0.00022898,0.32573594],
    [-0.11721726,0.20915005,-0.11723436,-0.07815329,0.31318947,0.13655742,0.33241385,0.0],
    [-0.04297703,0.09317876,-0.11831248,0.17355132,-0.28164031,0.42719361,0.0,0.0]],
'L=32':[[0.20533892,0.32087437,0.15187897,0.04249238,0.00670516,0.00054977,0.00002018,0.00000024,0.32573501],
    [0.12775091,-0.13523423,-0.14935701,0.28227378,0.23670434,0.05661270,0.00469819,0.32578978,0.0],
    [0.09703829,-0.19373733,0.18610682,-0.14407046,0.00220535,0.26897090,0.36633402,0.0,0.0]],
'L=34':[[-0.14409234,-0.01343681,0.31248977,0.25557722,0.08571889,0.01351208,0.00095792,0.00002550,0.32573508],
    [-0.11527834,0.18472133,-0.04403280,-0.16908618,0.27227021,0.21086614,0.04041752,0.32688152,0.0],
    [-0.06773139,0.14120811,-0.15835721,0.18357456,-0.19364673,0.08377174,0.43116318,0.0,0.0]]
}

Lnorm = lambda L: 4.*np.pi/(2.0*L+1.)

def GetKcl(L,N,SGLaue,phi,beta):
    'needs doc string'
    import pytexture as ptx
    if SGLaue in ['m3','m3m']:
        if phi.shape:
            Kcl = np.zeros_like(phi)
        else:
            Kcl = 0.
        for j in range(0,L+1,4):
            im = j/4+1
            if phi.shape:
                pcrs = np.array([ptx.pyplmpsi(L,j,1,p)[0] for p in phi]).flatten()
            else:
                pcrs,dum = ptx.pyplmpsi(L,j,1,phi)
            Kcl += BOH['L='+str(L)][N-1][im-1]*pcrs*cosd(j*beta)        
    else:
        if phi.shape:
            pcrs = np.array([ptx.pyplmpsi(L,N,1,p)[0] for p in phi]).flatten()
        else:
            pcrs,dum = ptx.pyplmpsi(L,N,1,phi)
        pcrs *= RSQ2PI
        if N:
            pcrs *= SQ2
        if SGLaue in ['mmm','4/mmm','6/mmm','R3mR','3m1','31m']:
            if SGLaue in ['3mR','3m1','31m']: 
                if N%6 == 3:
                    Kcl = pcrs*sind(N*beta)
                else:
                    Kcl = pcrs*cosd(N*beta)
            else:
                Kcl = pcrs*cosd(N*beta)
        else:
            Kcl = pcrs*(cosd(N*beta)+sind(N*beta))
    return Kcl
    
def GetKsl(L,M,SamSym,psi,gam):
    'needs doc string'
    import pytexture as ptx
    if psi.shape:
        psrs = np.array([ptx.pyplmpsi(L,M,1,p) for p in psi])
        psrs,dpdps = np.reshape(psrs.flatten(),(-1,2)).T
    else:
        psrs,dpdps = ptx.pyplmpsi(L,M,1,psi)
    psrs *= RSQ2PI
    dpdps *= RSQ2PI
    if M:
        psrs *= SQ2
        dpdps *= SQ2
    if SamSym in ['mmm',]:
        dum = cosd(M*gam)
        Ksl = psrs*dum
        dKsdp = dpdps*dum
        dKsdg = -psrs*M*sind(M*gam)
    else:
        dum = cosd(M*gam)+sind(M*gam)
        Ksl = psrs*dum
        dKsdp = dpdps*dum
        dKsdg = psrs*M*(-sind(M*gam)+cosd(M*gam))
    return Ksl,dKsdp,dKsdg 
   
def GetKclKsl(L,N,SGLaue,psi,phi,beta):
    """
    This is used for spherical harmonics description of preferred orientation;
        cylindrical symmetry only (M=0) and no sample angle derivatives returned
    """
    import pytexture as ptx
    Ksl,x = ptx.pyplmpsi(L,0,1,psi)
    Ksl *= RSQ2PI
    if SGLaue in ['m3','m3m']:
        Kcl = 0.0
        for j in range(0,L+1,4):
            im = j/4+1
            pcrs,dum = ptx.pyplmpsi(L,j,1,phi)
            Kcl += BOH['L='+str(L)][N-1][im-1]*pcrs*cosd(j*beta)        
    else:
        pcrs,dum = ptx.pyplmpsi(L,N,1,phi)
        pcrs *= RSQ2PI
        if N:
            pcrs *= SQ2
        if SGLaue in ['mmm','4/mmm','6/mmm','R3mR','3m1','31m']:
            if SGLaue in ['3mR','3m1','31m']: 
                if N%6 == 3:
                    Kcl = pcrs*sind(N*beta)
                else:
                    Kcl = pcrs*cosd(N*beta)
            else:
                Kcl = pcrs*cosd(N*beta)
        else:
            Kcl = pcrs*(cosd(N*beta)+sind(N*beta))
    return Kcl*Ksl,Lnorm(L)
    
def Glnh(Start,SHCoef,psi,gam,SamSym):
    'needs doc string'
    import pytexture as ptx

    if Start:
        ptx.pyqlmninit()
        Start = False
    Fln = np.zeros(len(SHCoef))
    for i,term in enumerate(SHCoef):
        l,m,n = eval(term.strip('C'))
        pcrs,dum = ptx.pyplmpsi(l,m,1,psi)
        pcrs *= RSQPI
        if m == 0:
            pcrs /= SQ2
        if SamSym in ['mmm',]:
            Ksl = pcrs*cosd(m*gam)
        else:
            Ksl = pcrs*(cosd(m*gam)+sind(m*gam))
        Fln[i] = SHCoef[term]*Ksl*Lnorm(l)
    ODFln = dict(zip(SHCoef.keys(),list(zip(SHCoef.values(),Fln))))
    return ODFln

def Flnh(Start,SHCoef,phi,beta,SGData):
    'needs doc string'
    import pytexture as ptx
    
    if Start:
        ptx.pyqlmninit()
        Start = False
    Fln = np.zeros(len(SHCoef))
    for i,term in enumerate(SHCoef):
        l,m,n = eval(term.strip('C'))
        if SGData['SGLaue'] in ['m3','m3m']:
            Kcl = 0.0
            for j in range(0,l+1,4):
                im = j/4+1
                pcrs,dum = ptx.pyplmpsi(l,j,1,phi)
                Kcl += BOH['L='+str(l)][n-1][im-1]*pcrs*cosd(j*beta)        
        else:                #all but cubic
            pcrs,dum = ptx.pyplmpsi(l,n,1,phi)
            pcrs *= RSQPI
            if n == 0:
                pcrs /= SQ2
            if SGData['SGLaue'] in ['mmm','4/mmm','6/mmm','R3mR','3m1','31m']:
               if SGData['SGLaue'] in ['3mR','3m1','31m']: 
                   if n%6 == 3:
                       Kcl = pcrs*sind(n*beta)
                   else:
                       Kcl = pcrs*cosd(n*beta)
               else:
                   Kcl = pcrs*cosd(n*beta)
            else:
                Kcl = pcrs*(cosd(n*beta)+sind(n*beta))
        Fln[i] = SHCoef[term]*Kcl*Lnorm(l)
    ODFln = dict(zip(SHCoef.keys(),list(zip(SHCoef.values(),Fln))))
    return ODFln
    
def polfcal(ODFln,SamSym,psi,gam):
    '''Perform a pole figure computation.
    Note that the the number of gam values must either be 1 or must
    match psi. Updated for numpy 1.8.0
    '''
    import pytexture as ptx
    PolVal = np.ones_like(psi)
    for term in ODFln:
        if abs(ODFln[term][1]) > 1.e-3:
            l,m,n = eval(term.strip('C'))
            psrs,dum = ptx.pyplmpsi(l,m,len(psi),psi)
            if SamSym in ['-1','2/m']:
                if m:
                    Ksl = RSQPI*psrs*(cosd(m*gam)+sind(m*gam))
                else:
                    Ksl = RSQPI*psrs/SQ2
            else:
                if m:
                    Ksl = RSQPI*psrs*cosd(m*gam)
                else:
                    Ksl = RSQPI*psrs/SQ2
            PolVal += ODFln[term][1]*Ksl
    return PolVal
    
def invpolfcal(ODFln,SGData,phi,beta):
    'needs doc string'
    import pytexture as ptx
    
    invPolVal = np.ones_like(beta)
    for term in ODFln:
        if abs(ODFln[term][1]) > 1.e-3:
            l,m,n = eval(term.strip('C'))
            if SGData['SGLaue'] in ['m3','m3m']:
                Kcl = 0.0
                for j in range(0,l+1,4):
                    im = j/4+1
                    pcrs,dum = ptx.pyplmpsi(l,j,len(beta),phi)
                    Kcl += BOH['L='+str(l)][n-1][im-1]*pcrs*cosd(j*beta)        
            else:                #all but cubic
                pcrs,dum = ptx.pyplmpsi(l,n,len(beta),phi)
                pcrs *= RSQPI
                if n == 0:
                    pcrs /= SQ2
                if SGData['SGLaue'] in ['mmm','4/mmm','6/mmm','R3mR','3m1','31m']:
                   if SGData['SGLaue'] in ['3mR','3m1','31m']: 
                       if n%6 == 3:
                           Kcl = pcrs*sind(n*beta)
                       else:
                           Kcl = pcrs*cosd(n*beta)
                   else:
                       Kcl = pcrs*cosd(n*beta)
                else:
                    Kcl = pcrs*(cosd(n*beta)+sind(n*beta))
            invPolVal += ODFln[term][1]*Kcl 
    return invPolVal
    
    
def textureIndex(SHCoef):
    'needs doc string'
    Tindx = 1.0
    for term in SHCoef:
        l = eval(term.strip('C'))[0]
        Tindx += SHCoef[term]**2/(2.0*l+1.)
    return Tindx
    
# self-test materials follow. 
selftestlist = []
'''Defines a list of self-tests'''
selftestquiet = True
def _ReportTest():
    'Report name and doc string of current routine when ``selftestquiet`` is False'
    if not selftestquiet:
        import inspect
        caller = inspect.stack()[1][3]
        doc = eval(caller).__doc__
        if doc is not None:
            print('testing '+__file__+' with '+caller+' ('+doc+')')
        else:
            print('testing '+__file__()+" with "+caller)
NeedTestData = True
def TestData():
    array = np.array
    global NeedTestData
    NeedTestData = False
    global CellTestData
    # output from uctbx computed on platform darwin on 2010-05-28
    CellTestData = [
# cell, g, G, cell*, V, V*
  [(4, 4, 4, 90, 90, 90), 
   array([[  1.60000000e+01,   9.79717439e-16,   9.79717439e-16],
       [  9.79717439e-16,   1.60000000e+01,   9.79717439e-16],
       [  9.79717439e-16,   9.79717439e-16,   1.60000000e+01]]), array([[  6.25000000e-02,   3.82702125e-18,   3.82702125e-18],
       [  3.82702125e-18,   6.25000000e-02,   3.82702125e-18],
       [  3.82702125e-18,   3.82702125e-18,   6.25000000e-02]]), (0.25, 0.25, 0.25, 90.0, 90.0, 90.0), 64.0, 0.015625],
# cell, g, G, cell*, V, V*
  [(4.0999999999999996, 5.2000000000000002, 6.2999999999999998, 100, 80, 130), 
   array([[ 16.81      , -13.70423184,   4.48533243],
       [-13.70423184,  27.04      ,  -5.6887143 ],
       [  4.48533243,  -5.6887143 ,  39.69      ]]), array([[ 0.10206349,  0.05083339, -0.00424823],
       [ 0.05083339,  0.06344997,  0.00334956],
       [-0.00424823,  0.00334956,  0.02615544]]), (0.31947376387537696, 0.25189277536327803, 0.16172643497798223, 85.283666420376008, 94.716333579624006, 50.825714168082683), 100.98576357983838, 0.0099023858863968445],
# cell, g, G, cell*, V, V*
  [(3.5, 3.5, 6, 90, 90, 120), 
   array([[  1.22500000e+01,  -6.12500000e+00,   1.28587914e-15],
       [ -6.12500000e+00,   1.22500000e+01,   1.28587914e-15],
       [  1.28587914e-15,   1.28587914e-15,   3.60000000e+01]]), array([[  1.08843537e-01,   5.44217687e-02,   3.36690552e-18],
       [  5.44217687e-02,   1.08843537e-01,   3.36690552e-18],
       [  3.36690552e-18,   3.36690552e-18,   2.77777778e-02]]), (0.32991443953692895, 0.32991443953692895, 0.16666666666666669, 90.0, 90.0, 60.000000000000021), 63.652867178156257, 0.015710211406520427],
  ]
    global CoordTestData
    CoordTestData = [
# cell, ((frac, ortho),...)
  ((4,4,4,90,90,90,), [
 ((0.10000000000000001, 0.0, 0.0),(0.40000000000000002, 0.0, 0.0)),
 ((0.0, 0.10000000000000001, 0.0),(2.4492935982947065e-17, 0.40000000000000002, 0.0)),
 ((0.0, 0.0, 0.10000000000000001),(2.4492935982947065e-17, -2.4492935982947065e-17, 0.40000000000000002)),
 ((0.10000000000000001, 0.20000000000000001, 0.29999999999999999),(0.40000000000000013, 0.79999999999999993, 1.2)),
 ((0.20000000000000001, 0.29999999999999999, 0.10000000000000001),(0.80000000000000016, 1.2, 0.40000000000000002)),
 ((0.29999999999999999, 0.20000000000000001, 0.10000000000000001),(1.2, 0.80000000000000004, 0.40000000000000002)),
 ((0.5, 0.5, 0.5),(2.0, 1.9999999999999998, 2.0)),
]),
# cell, ((frac, ortho),...)
  ((4.1,5.2,6.3,100,80,130,), [
 ((0.10000000000000001, 0.0, 0.0),(0.40999999999999998, 0.0, 0.0)),
 ((0.0, 0.10000000000000001, 0.0),(-0.33424955703700043, 0.39834311042186865, 0.0)),
 ((0.0, 0.0, 0.10000000000000001),(0.10939835193016617, -0.051013289294572106, 0.6183281045774256)),
 ((0.10000000000000001, 0.20000000000000001, 0.29999999999999999),(0.069695941716497567, 0.64364635296002093, 1.8549843137322766)),
 ((0.20000000000000001, 0.29999999999999999, 0.10000000000000001),(-0.073350319180835066, 1.1440160419710339, 0.6183281045774256)),
 ((0.29999999999999999, 0.20000000000000001, 0.10000000000000001),(0.67089923785616512, 0.74567293154916525, 0.6183281045774256)),
 ((0.5, 0.5, 0.5),(0.92574397446582857, 1.7366491056364828, 3.0916405228871278)),
]),
# cell, ((frac, ortho),...)
  ((3.5,3.5,6,90,90,120,), [
 ((0.10000000000000001, 0.0, 0.0),(0.35000000000000003, 0.0, 0.0)),
 ((0.0, 0.10000000000000001, 0.0),(-0.17499999999999993, 0.3031088913245536, 0.0)),
 ((0.0, 0.0, 0.10000000000000001),(3.6739403974420595e-17, -3.6739403974420595e-17, 0.60000000000000009)),
 ((0.10000000000000001, 0.20000000000000001, 0.29999999999999999),(2.7675166561703527e-16, 0.60621778264910708, 1.7999999999999998)),
 ((0.20000000000000001, 0.29999999999999999, 0.10000000000000001),(0.17500000000000041, 0.90932667397366063, 0.60000000000000009)),
 ((0.29999999999999999, 0.20000000000000001, 0.10000000000000001),(0.70000000000000018, 0.6062177826491072, 0.60000000000000009)),
 ((0.5, 0.5, 0.5),(0.87500000000000067, 1.5155444566227676, 3.0)),
]),
]
    global LaueTestData             #generated by GSAS
    LaueTestData = {
    'R 3 m':[(4.,4.,6.,90.,90.,120.),((1,0,1,6),(1,0,-2,6),(0,0,3,2),(1,1,0,6),(2,0,-1,6),(2,0,2,6),
        (1,1,3,12),(1,0,4,6),(2,1,1,12),(2,1,-2,12),(3,0,0,6),(1,0,-5,6),(2,0,-4,6),(3,0,-3,6),(3,0,3,6),
        (0,0,6,2),(2,2,0,6),(2,1,4,12),(2,0,5,6),(3,1,-1,12),(3,1,2,12),(1,1,6,12),(2,2,3,12),(2,1,-5,12))],
    'R 3':[(4.,4.,6.,90.,90.,120.),((1,0,1,6),(1,0,-2,6),(0,0,3,2),(1,1,0,6),(2,0,-1,6),(2,0,2,6),(1,1,3,6),
        (1,1,-3,6),(1,0,4,6),(3,-1,1,6),(2,1,1,6),(3,-1,-2,6),(2,1,-2,6),(3,0,0,6),(1,0,-5,6),(2,0,-4,6),
        (2,2,0,6),(3,0,3,6),(3,0,-3,6),(0,0,6,2),(3,-1,4,6),(2,0,5,6),(2,1,4,6),(4,-1,-1,6),(3,1,-1,6),
        (3,1,2,6),(4,-1,2,6),(2,2,-3,6),(1,1,-6,6),(1,1,6,6),(2,2,3,6),(2,1,-5,6),(3,-1,-5,6))],
    'P 3':[(4.,4.,6.,90.,90.,120.),((0,0,1,2),(1,0,0,6),(1,0,1,6),(0,0,2,2),(1,0,-1,6),(1,0,2,6),(1,0,-2,6),
        (1,1,0,6),(0,0,3,2),(1,1,1,6),(1,1,-1,6),(1,0,3,6),(1,0,-3,6),(2,0,0,6),(2,0,-1,6),(1,1,-2,6),
        (1,1,2,6),(2,0,1,6),(2,0,-2,6),(2,0,2,6),(0,0,4,2),(1,1,-3,6),(1,1,3,6),(1,0,-4,6),(1,0,4,6),
        (2,0,-3,6),(2,1,0,6),(2,0,3,6),(3,-1,0,6),(2,1,1,6),(3,-1,-1,6),(2,1,-1,6),(3,-1,1,6),(1,1,4,6),
        (3,-1,2,6),(3,-1,-2,6),(1,1,-4,6),(0,0,5,2),(2,1,2,6),(2,1,-2,6),(3,0,0,6),(3,0,1,6),(2,0,4,6),
        (2,0,-4,6),(3,0,-1,6),(1,0,-5,6),(1,0,5,6),(3,-1,-3,6),(2,1,-3,6),(2,1,3,6),(3,-1,3,6),(3,0,-2,6),
        (3,0,2,6),(1,1,5,6),(1,1,-5,6),(2,2,0,6),(3,0,3,6),(3,0,-3,6),(0,0,6,2),(2,0,-5,6),(2,1,-4,6),
        (2,2,-1,6),(3,-1,-4,6),(2,2,1,6),(3,-1,4,6),(2,1,4,6),(2,0,5,6),(1,0,-6,6),(1,0,6,6),(4,-1,0,6),
        (3,1,0,6),(3,1,-1,6),(3,1,1,6),(4,-1,-1,6),(2,2,2,6),(4,-1,1,6),(2,2,-2,6),(3,1,2,6),(3,1,-2,6),
        (3,0,4,6),(3,0,-4,6),(4,-1,-2,6),(4,-1,2,6),(2,2,-3,6),(1,1,6,6),(1,1,-6,6),(2,2,3,6),(3,-1,5,6),
        (2,1,5,6),(2,1,-5,6),(3,-1,-5,6))],
    'P 3 m 1':[(4.,4.,6.,90.,90.,120.),((0,0,1,2),(1,0,0,6),(1,0,-1,6),(1,0,1,6),(0,0,2,2),(1,0,-2,6),
        (1,0,2,6),(1,1,0,6),(0,0,3,2),(1,1,1,12),(1,0,-3,6),(1,0,3,6),(2,0,0,6),(1,1,2,12),(2,0,1,6),
        (2,0,-1,6),(0,0,4,2),(2,0,-2,6),(2,0,2,6),(1,1,3,12),(1,0,-4,6),(1,0,4,6),(2,0,3,6),(2,1,0,12),
        (2,0,-3,6),(2,1,1,12),(2,1,-1,12),(1,1,4,12),(2,1,2,12),(0,0,5,2),(2,1,-2,12),(3,0,0,6),(1,0,-5,6),
        (3,0,1,6),(3,0,-1,6),(1,0,5,6),(2,0,4,6),(2,0,-4,6),(2,1,3,12),(2,1,-3,12),(3,0,-2,6),(3,0,2,6),
        (1,1,5,12),(3,0,-3,6),(0,0,6,2),(2,2,0,6),(3,0,3,6),(2,1,4,12),(2,2,1,12),(2,0,5,6),(2,1,-4,12),
        (2,0,-5,6),(1,0,-6,6),(1,0,6,6),(3,1,0,12),(3,1,-1,12),(3,1,1,12),(2,2,2,12),(3,1,2,12),
        (3,0,4,6),(3,1,-2,12),(3,0,-4,6),(1,1,6,12),(2,2,3,12))],
    'P 3 1 m':[(4.,4.,6.,90.,90.,120.),((0,0,1,2),(1,0,0,6),(0,0,2,2),(1,0,1,12),(1,0,2,12),(1,1,0,6),
        (0,0,3,2),(1,1,-1,6),(1,1,1,6),(1,0,3,12),(2,0,0,6),(2,0,1,12),(1,1,2,6),(1,1,-2,6),(2,0,2,12),
        (0,0,4,2),(1,1,-3,6),(1,1,3,6),(1,0,4,12),(2,1,0,12),(2,0,3,12),(2,1,1,12),(2,1,-1,12),(1,1,-4,6),
        (1,1,4,6),(0,0,5,2),(2,1,-2,12),(2,1,2,12),(3,0,0,6),(1,0,5,12),(2,0,4,12),(3,0,1,12),(2,1,-3,12),
        (2,1,3,12),(3,0,2,12),(1,1,5,6),(1,1,-5,6),(3,0,3,12),(0,0,6,2),(2,2,0,6),(2,1,-4,12),(2,0,5,12),
        (2,2,-1,6),(2,2,1,6),(2,1,4,12),(3,1,0,12),(1,0,6,12),(2,2,2,6),(3,1,-1,12),(2,2,-2,6),(3,1,1,12),
        (3,1,-2,12),(3,0,4,12),(3,1,2,12),(1,1,-6,6),(2,2,3,6),(2,2,-3,6),(1,1,6,6))],
    }
    
    global FLnhTestData
    FLnhTestData = [{
    'C(4,0,0)': (0.965, 0.42760447),
    'C(2,0,0)': (1.0122, -0.80233610),
    'C(2,0,2)': (0.0061, 8.37491546E-03),
    'C(6,0,4)': (-0.0898, 4.37985696E-02),
    'C(6,0,6)': (-0.1369, -9.04081762E-02),
    'C(6,0,0)': (0.5935, -0.18234928),
    'C(4,0,4)': (0.1872, 0.16358127),
    'C(6,0,2)': (0.6193, 0.27573633),
    'C(4,0,2)': (-0.1897, 0.12530720)},[1,0,0]]
def test0():
    if NeedTestData: TestData()
    msg = 'test cell2Gmat, fillgmat, Gmat2cell'
    for (cell, tg, tG, trcell, tV, trV) in CellTestData:
        G, g = cell2Gmat(cell)
        assert np.allclose(G,tG),msg
        assert np.allclose(g,tg),msg
        tcell = Gmat2cell(g)
        assert np.allclose(cell,tcell),msg
        tcell = Gmat2cell(G)
        assert np.allclose(tcell,trcell),msg
selftestlist.append(test0)

def test1():
    'test cell2A and A2Gmat'
    _ReportTest()
    if NeedTestData: TestData()
    msg = 'test cell2A and A2Gmat'
    for (cell, tg, tG, trcell, tV, trV) in CellTestData:
        G, g = A2Gmat(cell2A(cell))
        assert np.allclose(G,tG),msg
        assert np.allclose(g,tg),msg
selftestlist.append(test1)

def test2():
    'test Gmat2A, A2cell, A2Gmat, Gmat2cell'
    _ReportTest()
    if NeedTestData: TestData()
    msg = 'test Gmat2A, A2cell, A2Gmat, Gmat2cell'
    for (cell, tg, tG, trcell, tV, trV) in CellTestData:
        G, g = cell2Gmat(cell)
        tcell = A2cell(Gmat2A(G))
        assert np.allclose(cell,tcell),msg
selftestlist.append(test2)

def test3():
    'test invcell2Gmat'
    _ReportTest()
    if NeedTestData: TestData()
    msg = 'test invcell2Gmat'
    for (cell, tg, tG, trcell, tV, trV) in CellTestData:
        G, g = invcell2Gmat(trcell)
        assert np.allclose(G,tG),msg
        assert np.allclose(g,tg),msg
selftestlist.append(test3)

def test4():
    'test calc_rVsq, calc_rV, calc_V'
    _ReportTest()
    if NeedTestData: TestData()
    msg = 'test calc_rVsq, calc_rV, calc_V'
    for (cell, tg, tG, trcell, tV, trV) in CellTestData:
        assert np.allclose(calc_rV(cell2A(cell)),trV), msg
        assert np.allclose(calc_V(cell2A(cell)),tV), msg
selftestlist.append(test4)

def test5():
    'test A2invcell'
    _ReportTest()
    if NeedTestData: TestData()
    msg = 'test A2invcell'
    for (cell, tg, tG, trcell, tV, trV) in CellTestData:
        rcell = A2invcell(cell2A(cell))
        assert np.allclose(rcell,trcell),msg
selftestlist.append(test5)

def test6():
    'test cell2AB'
    _ReportTest()
    if NeedTestData: TestData()
    msg = 'test cell2AB'
    for (cell,coordlist) in CoordTestData:
        A,B = cell2AB(cell)
        for (frac,ortho) in coordlist:
            to = np.inner(A,frac)
            tf = np.inner(B,to)
            assert np.allclose(ortho,to), msg
            assert np.allclose(frac,tf), msg
            to = np.sum(A*frac,axis=1)
            tf = np.sum(B*to,axis=1)
            assert np.allclose(ortho,to), msg
            assert np.allclose(frac,tf), msg
selftestlist.append(test6)

def test7():
    'test GetBraviasNum(...) and GenHBravais(...)'
    _ReportTest()
    import os.path
    import sys
    import GSASIIspc as spc
    testdir = os.path.join(os.path.split(os.path.abspath( __file__ ))[0],'testinp')
    if os.path.exists(testdir):
        if testdir not in sys.path: sys.path.insert(0,testdir)
    import sgtbxlattinp
    derror = 1e-4
    def indexmatch(hklin, hkllist, system):
        for hklref in hkllist:
            hklref = list(hklref)
            # these permutations are far from complete, but are sufficient to 
            # allow the test to complete
            if system == 'cubic':
                permlist = [(1,2,3),(1,3,2),(2,1,3),(2,3,1),(3,1,2),(3,2,1),]
            elif system == 'monoclinic':
                permlist = [(1,2,3),(-1,2,-3)]
            else:
                permlist = [(1,2,3)]

            for perm in permlist:
                hkl = [abs(i) * hklin[abs(i)-1] / i for i in perm]
                if hkl == hklref: return True
                if [-i for i in hkl] == hklref: return True
        else:
            return False

    for key in sgtbxlattinp.sgtbx7:
        spdict = spc.SpcGroup(key)
        cell = sgtbxlattinp.sgtbx7[key][0]
        system = spdict[1]['SGSys']
        center = spdict[1]['SGLatt']

        bravcode = GetBraviasNum(center, system)

        g2list = GenHBravais(sgtbxlattinp.dmin, bravcode, cell2A(cell))

        assert len(sgtbxlattinp.sgtbx7[key][1]) == len(g2list), 'Reflection lists differ for %s' % key
        for h,k,l,d,num in g2list:
            for hkllist,dref in sgtbxlattinp.sgtbx7[key][1]: 
                if abs(d-dref) < derror:
                    if indexmatch((h,k,l,), hkllist, system):
                        break
            else:
                assert 0,'No match for %s at %s (%s)' % ((h,k,l),d,key)
selftestlist.append(test7)

def test8():
    'test GenHLaue'
    _ReportTest()
    import GSASIIspc as spc
    import sgtbxlattinp
    derror = 1e-4
    dmin = sgtbxlattinp.dmin

    def indexmatch(hklin, hklref, system, axis):
        # these permutations are far from complete, but are sufficient to 
        # allow the test to complete
        if system == 'cubic':
            permlist = [(1,2,3),(1,3,2),(2,1,3),(2,3,1),(3,1,2),(3,2,1),]
        elif system == 'monoclinic' and axis=='b':
            permlist = [(1,2,3),(-1,2,-3)]
        elif system == 'monoclinic' and axis=='a':
            permlist = [(1,2,3),(1,-2,-3)]
        elif system == 'monoclinic' and axis=='c':
            permlist = [(1,2,3),(-1,-2,3)]
        elif system == 'trigonal':
            permlist = [(1,2,3),(2,1,3),(-1,-2,3),(-2,-1,3)]
        elif system == 'rhombohedral':
            permlist = [(1,2,3),(2,3,1),(3,1,2)]
        else:
            permlist = [(1,2,3)]

        hklref = list(hklref)
        for perm in permlist:
            hkl = [abs(i) * hklin[abs(i)-1] / i for i in perm]
            if hkl == hklref: return True
            if [-i for i in hkl] == hklref: return True
        return False

    for key in sgtbxlattinp.sgtbx8:
        spdict = spc.SpcGroup(key)[1]
        cell = sgtbxlattinp.sgtbx8[key][0]
        center = spdict['SGLatt']
        Laue = spdict['SGLaue']
        Axis = spdict['SGUniq']
        system = spdict['SGSys']

        g2list = GenHLaue(dmin,spdict,cell2A(cell))
        #if len(g2list) != len(sgtbxlattinp.sgtbx8[key][1]):
        #    print 'failed',key,':' ,len(g2list),'vs',len(sgtbxlattinp.sgtbx8[key][1])
        #    print 'GSAS-II:'
        #    for h,k,l,d in g2list: print '  ',(h,k,l),d
        #    print 'SGTBX:'
        #    for hkllist,dref in sgtbxlattinp.sgtbx8[key][1]: print '  ',hkllist,dref
        assert len(g2list) == len(sgtbxlattinp.sgtbx8[key][1]), (
            'Reflection lists differ for %s' % key
            )
        #match = True
        for h,k,l,d in g2list:
            for hkllist,dref in sgtbxlattinp.sgtbx8[key][1]: 
                if abs(d-dref) < derror:
                    if indexmatch((h,k,l,), hkllist, system, Axis): break
            else:
                assert 0,'No match for %s at %s (%s)' % ((h,k,l),d,key)
                #match = False
        #if not match: 
            #for hkllist,dref in sgtbxlattinp.sgtbx8[key][1]: print '  ',hkllist,dref
            #print center, Laue, Axis, system
selftestlist.append(test8)
            
def test9():
    'test GenHLaue'
    _ReportTest()
    import GSASIIspc as G2spc
    if NeedTestData: TestData()
    for spc in LaueTestData:
        data = LaueTestData[spc]
        cell = data[0]
        hklm = np.array(data[1])
        H = hklm[-1][:3]
        hklO = hklm.T[:3].T
        A = cell2A(cell)
        dmin = 1./np.sqrt(calc_rDsq(H,A))
        SGData = G2spc.SpcGroup(spc)[1]
        hkls = np.array(GenHLaue(dmin,SGData,A))
        hklN = hkls.T[:3].T
        #print spc,hklO.shape,hklN.shape
        err = True
        for H in hklO:
            if H not in hklN:
                print H,' missing from hkl from GSASII'
                err = False
        assert(err)
selftestlist.append(test9)
        
        
    

if __name__ == '__main__':
    # run self-tests
    selftestquiet = False
    for test in selftestlist:
        test()
    print "OK"
