# -*- coding: utf-8 -*-
'''
*GSASIIpath: locations & updates*
---------------------------------

Routines for dealing with file locations, etc.

Determines the location of the compiled (.pyd or .so) libraries.

Interfaces with subversion (svn): 
Determine the subversion release number by determining the highest version number
where :func:`SetVersionNumber` is called (best done in every GSASII file).
Other routines will update GSASII from the subversion server if svn can be
found.

Accesses configuration options, as defined in config.py
'''

from __future__ import division, print_function
import os
import sys
import platform
import glob
import subprocess
import numpy as np
g2home = 'https://subversion.xray.aps.anl.gov/pyGSAS'
'Define the location of the GSAS-II subversion repository'
    
path2GSAS2 = os.path.dirname(os.path.abspath(os.path.expanduser(__file__))) # location of this file; save before any changes in pwd

# convert version numbers as '1.2.3' to integers (1002) and back (to 1.2)
fmtver = lambda v: str(v//1000)+'.'+str(v%1000)
intver = lambda vs: sum([int(i) for i in vs.split('.')[0:2]]*np.array((1000,1)))

def GetConfigValue(key,default=None):
    '''Return the configuration file value for key or a default value if not present
    
    :param str key: a value to be found in the configuration (config.py) file
    :param default: a value to be supplied is none is in the config file or
      the config file is not found. Defaults to None
    :returns: the value found or the default.
    '''
    try:
        return configDict.get(key,default)
    except NameError: # this happens when building docs
        return None

def SetConfigValue(parmdict):
    '''Set configuration variables from a dictionary where elements are lists
    First item in list is the default value and second is the value to use.
    '''
    global configDict
    for var in parmdict:
        if var in configDict:
            del configDict[var]
        if isinstance(parmdict[var],tuple):
            configDict[var] = parmdict[var]
        else:
            if parmdict[var][1] is None: continue
            if parmdict[var][1] == '': continue
            if parmdict[var][0] == parmdict[var][1]: continue
            configDict[var] = parmdict[var][1]

# routines for looking a version numbers in files
version = -1
def SetVersionNumber(RevString):
    '''Set the subversion version number

    :param str RevString: something like "$Revision$"
      that is set by subversion when the file is retrieved from subversion.

    Place ``GSASIIpath.SetVersionNumber("$Revision$")`` in every python
    file.
    '''
    try:
        RevVersion = int(RevString.split(':')[1].split()[0])
        global version
        version = max(version,RevVersion)
    except:
        pass
        
def GetVersionNumber():
    '''Return the maximum version number seen in :func:`SetVersionNumber`
    '''
    if version > 1000:
        return version
    else:
        return "unknown"

def LoadConfigFile(filename):
    '''Read a GSAS-II configuration file.
    Comments (starting with "%") are removed, as are empty lines
    
    :param str filename: base file name (such as 'file.dat'). Files with this name
      are located from the path and the contents of each are concatenated.
    :returns: a list containing each non-empty (after removal of comments) line
      found in every matching config file.
    '''
    info = []
    for path in sys.path:
        fil = os.path.join(path,filename)
        if not os.path.exists(fil): continue
        try:
            i = 0
            fp = open(fil,'r')
            for line in fp:
                expr = line.split('#')[0].strip()
                if expr:
                    info.append(expr)
                    i += 1
            print(str(i)+' lines read from config file '+fil)
        finally:
            fp.close()
    return info


# routines to interface with subversion
proxycmds = []
'Used to hold proxy information for subversion, set if needed in whichsvn'
svnLocCache = None
'Cached location of svn to avoid multiple searches for it'

def MakeByte2str(arg):
    '''Convert output from subprocess pipes (bytes) to str (unicode) in Python 3.
    In Python 2: Leaves output alone (already str). 
    Leaves stuff of other types alone (including unicode in Py2)
    Works recursively for string-like stuff in nested loops and tuples.

    typical use::

        out = MakeByte2str(out)

    or::

        out,err = MakeByte2str(s.communicate())
    
    '''
    if isinstance(arg,str): return arg
    if isinstance(arg,bytes): return arg.decode()
    if isinstance(arg,list):
        return [MakeByte2str(i) for i in arg]
    if isinstance(arg,tuple):
        return tuple([MakeByte2str(i) for i in arg])
    return arg
                
def getsvnProxy():
    '''Loads a proxy for subversion from the file created by bootstrap.py
    '''
    proxyinfo = os.path.join(path2GSAS2,"proxyinfo.txt")
    if os.path.exists(proxyinfo):
        global proxycmds
        proxycmds = []
        fp = open(proxyinfo,'r')
        host = fp.readline().strip()
        port = fp.readline().strip()
        fp.close()
        setsvnProxy(host,port)
        if not host.strip(): return '',''
        return host,port
    return '',''

def setsvnProxy(host,port):
    '''Sets the svn commands needed to use a proxy
    '''
    global proxycmds
    proxycmds = []
    host = host.strip()
    port = port.strip()
    if not host.strip(): return
    proxycmds.append('--config-option')
    proxycmds.append('servers:global:http-proxy-host='+host)
    proxycmds.append('--config-option')
    proxycmds.append('servers:global:http-proxy-port='+port)
        
def whichsvn():
    '''Returns a path to the subversion exe file, if any is found.
    Searches the current path after adding likely places where GSAS-II
    might install svn. 

    :returns: None if svn is not found or an absolute path to the subversion
      executable file.
    '''
    # use a previosuly cached svn location
    global svnLocCache
    if svnLocCache: return svnLocCache
    # prepare to find svn
    is_exe = lambda fpath: os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    svnprog = 'svn'
    if sys.platform.startswith('win'): svnprog += '.exe'
    host,port = getsvnProxy()
    if GetConfigValue('debug') and host:
        print('Using proxy host {} port {}'.format(host,port))
    # add likely places to find subversion when installed with GSAS-II
    pathlist = os.environ["PATH"].split(os.pathsep)
    pathlist.insert(0,os.path.split(sys.executable)[0])
    pathlist.insert(1,path2GSAS2)
    for rpt in ('..','bin'),('..','Library','bin'),('svn','bin'),('svn',),('.'):
        pt = os.path.normpath(os.path.join(path2GSAS2,*rpt))
        if os.path.exists(pt):
            pathlist.insert(0,pt)    
    # search path for svn or svn.exe
    for path in pathlist:
        exe_file = os.path.join(path, svnprog)
        if is_exe(exe_file):
            try:
                p = subprocess.Popen([exe_file,'help'],stdout=subprocess.PIPE)
                res = p.stdout.read()
                p.communicate()
                svnLocCache = os.path.abspath(exe_file)
                return svnLocCache
            except:
                pass        
    svnLocCache = None

def svnVersion(svn=None):
    '''Get the version number of the current subversion executable

    :returns: a string with a version number such as "1.6.6" or None if
      subversion is not found.

    '''
    if not svn: svn = whichsvn()
    if not svn: return

    cmd = [svn,'--version','--quiet']
    s = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out,err = MakeByte2str(s.communicate())
    if err:
        print ('subversion error!\nout=%s'%out)
        print ('err=%s'%err)
        return None
    return out.strip()

def svnVersionNumber(svn=None):
    '''Get the version number of the current subversion executable

    :returns: a fractional version number such as 1.6 or None if
      subversion is not found.

    '''
    ver = svnVersion(svn)
    if not ver: return 
    M,m = ver.split('.')[:2]
    return int(M)+int(m)/10.

def svnGetLog(fpath=os.path.split(__file__)[0],version=None):
    '''Get the revision log information for a specific version of the specified package

    :param str fpath: path to repository dictionary, defaults to directory where
       the current file is located.
    :param int version: the version number to be looked up or None (default)
       for the latest version.

    :returns: a dictionary with keys (one hopes) 'author', 'date', 'msg', and 'revision'

    '''
    import xml.etree.ElementTree as ET
    svn = whichsvn()
    if not svn: return
    if version is not None:
        vstr = '-r'+str(version)
    else:
        vstr = '-rHEAD'

    cmd = [svn,'log',fpath,'--xml',vstr]
    if proxycmds: cmd += proxycmds
    s = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out,err = MakeByte2str(s.communicate())
    if err:
        print ('out=%s'%out)
        print ('err=%s'%err)
        return None
    x = ET.fromstring(out)
    d = {}
    for i in x.iter('logentry'):
        d = {'revision':i.attrib.get('revision','?')}
        for j in i:
            d[j.tag] = j.text
        break # only need the first
    return d

svnLastError = ''
def svnGetRev(fpath=os.path.split(__file__)[0],local=True):
    '''Obtain the version number for the either the last update of the local version
    or contacts the subversion server to get the latest update version (# of Head).

    :param str fpath: path to repository dictionary, defaults to directory where
       the current file is located
    :param bool local: determines the type of version number, where
       True (default): returns the latest installed update 
       False: returns the version number of Head on the server

    :Returns: the version number as an str or 
       None if there is a subversion error (likely because the path is
       not a repository or svn is not found). The error message is placed in
       global variable svnLastError
    '''

    import xml.etree.ElementTree as ET
    svn = whichsvn()
    if not svn: return
    if local:
        cmd = [svn,'info',fpath,'--xml']
    else:
        cmd = [svn,'info',fpath,'--xml','-rHEAD']
    if svnVersionNumber() >= 1.6:
        cmd += ['--non-interactive', '--trust-server-cert']
    if proxycmds: cmd += proxycmds
    s = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out,err = MakeByte2str(s.communicate())
    if err:
        print ('svn failed\n%s'%out)
        print ('err=%s'%err)
        global svnLastError
        svnLastError = err
        return None
    x = ET.fromstring(out)
    for i in x.iter('entry'):
        rev = i.attrib.get('revision')
        if rev: return rev

def svnFindLocalChanges(fpath=os.path.split(__file__)[0]):
    '''Returns a list of files that were changed locally. If no files are changed,
       the list has length 0

    :param fpath: path to repository dictionary, defaults to directory where
       the current file is located

    :returns: None if there is a subversion error (likely because the path is
       not a repository or svn is not found)

    '''
    import xml.etree.ElementTree as ET
    svn = whichsvn()
    if not svn: return
    cmd = [svn,'status',fpath,'--xml']
    if proxycmds: cmd += proxycmds
    s = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out,err = MakeByte2str(s.communicate())
    if err: return None
    x = ET.fromstring(out)
    changed = []
    for i in x.iter('entry'):
        if i.find('wc-status').attrib.get('item') == 'modified': 
            changed.append(i.attrib.get('path'))
    return changed

def svnUpdateDir(fpath=os.path.split(__file__)[0],version=None,verbose=True):
    '''This performs an update of the files in a local directory from a server. 

    :param str fpath: path to repository dictionary, defaults to directory where
       the current file is located
    :param version: the number of the version to be loaded. Used only
       cast as a string, but should be an integer or something that corresponds to a
       string representation of an integer value when cast. A value of None (default)
       causes the latest version on the server to be used.
    '''
    svn = whichsvn()
    if not svn: return
    if version:
        verstr = '-r' + str(version)
    else:
        verstr = '-rHEAD'
    if verbose: print(u"Updating files at "+fpath)
    cmd = [svn,'update',fpath,verstr,
           '--non-interactive',
           '--accept','theirs-conflict','--force']
    if svnVersionNumber() >= 1.6:
        cmd += ['--trust-server-cert']
    if proxycmds: cmd += proxycmds
    if verbose:
        s = 'subversion command:\n  '
        for i in cmd: s += i + ' '
        print(s)
    s = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out,err = MakeByte2str(s.communicate())
    if err:
        print(60*"=")
        print("****** An error was noted, see below *********")
        print(60*"=")
        print(err)
        sys.exit()
    elif verbose:
        print(out)

def svnUpgrade(fpath=os.path.split(__file__)[0]):
    '''This reformats subversion files, which may be needed if an upgrade of subversion is
    done. 

    :param str fpath: path to repository dictionary, defaults to directory where
       the current file is located
    '''
    svn = whichsvn()
    if not svn: return
    cmd = [svn,'upgrade',fpath,'--non-interactive']
    if proxycmds: cmd += proxycmds
    s = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out,err = MakeByte2str(s.communicate())
    if err:
        print("svn upgrade did not happen (this is probably OK). Messages:")
        print (err)

def svnUpdateProcess(version=None,projectfile=None,branch=None):
    '''perform an update of GSAS-II in a separate python process'''
    if not projectfile:
        projectfile = ''
    else:
        projectfile = os.path.realpath(projectfile)
        print ('restart using %s'%projectfile)
    if branch:
        version = branch
    elif not version:
        version = ''
    else:
        version = str(version)
    # start the upgrade in a separate interpreter (avoids loading .pyd files)
    subprocess.Popen([sys.executable,__file__,projectfile,version])
    sys.exit()

def svnSwitchDir(rpath,filename,baseURL,loadpath=None,verbose=True):
    '''This performs a switch command to move files between subversion trees.
    Note that if the files were previously downloaded, 
    the switch command will update the files to the newest version.
    
    :param str rpath: path to locate files, relative to the GSAS-II
      installation path (defaults to path2GSAS2)
    :param str URL: the repository URL
    :param str loadpath: the prefix for the path, if specified. Defaults to path2GSAS2
    :param bool verbose: if True (default) diagnostics are printed
    '''
    svn = whichsvn()
    if not svn: return
    URL = baseURL[:]
    if baseURL[-1] != '/':
        URL = baseURL + '/' + filename
    else:
        URL = baseURL + filename
    if loadpath:
        fpath = os.path.join(loadpath,rpath,filename)
    else:
        fpath = os.path.join(path2GSAS2,rpath,filename)
    cmd = [svn,'switch',URL,fpath,
           '--non-interactive','--trust-server-cert',
           '--accept','theirs-conflict','--force']
    if svnVersionNumber(svn) > 1.6: cmd += ['--ignore-ancestry']
    if proxycmds: cmd += proxycmds
    if verbose: print(u"Loading files to "+fpath+u"\n  from "+URL)
    s = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out,err = MakeByte2str(s.communicate())
    if err:
        print(60*"=")
        print ("****** An error was noted, see below *********")
        print(60*"=")
        print ('out=%s'%out)
        print ('err=%s'%err)
        return False
    if verbose:
        print('=== Output from svn switch'+(43*'='))
        print(out.strip())
        print((70*'=')+'\n')
    return True

def svnInstallDir(URL,loadpath):
    '''Load a subversion tree into a specified directory

    :param str URL: the repository URL
    :param str loadpath: path to locate files

    '''
    svn = whichsvn()
    if not svn: return
    cmd = [svn,'co',URL,loadpath,'--non-interactive']
    if svnVersionNumber() >= 1.6: cmd += ['--trust-server-cert']
    print("Loading files from "+URL)
    if proxycmds: cmd += proxycmds
    s = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out,err = MakeByte2str(s.communicate())   #this fails too easily
    if err:
        print(60*"=")
        print ("****** An error was noted, see below *********")
        print(60*"=")
        print (err)
        return False
    print ("Files installed at: "+loadpath)
    return True

def GetBinaryPrefix():
    if sys.platform == "win32":
        prefix = 'win'
    elif sys.platform == "darwin":
        prefix = 'mac'
    elif sys.platform.startswith("linux"):
        prefix = 'linux'
    else:
        print(u'Unknown platform: '+sys.platform)
        raise Exception('Unknown platform')
    if platform.architecture()[0] == '64bit':
        bits = '64'
    else:
        bits = '32'

    # format current python version
    pyver = 'p{}.{}'.format(*sys.version_info[0:2])

    items = [prefix,bits,pyver]
    return '_'.join(items)

def svnList(URL,verbose=True):
    '''Get a list of subdirectories from and svn repository
    '''    
    svn = whichsvn()
    if not svn:
        print('**** unable to load files: svn not found ****')
        return ''
    # get binaries matching the required type -- other than for the numpy version
    cmd = [svn, 'list', URL,'--non-interactive', '--trust-server-cert']
    if proxycmds: cmd += proxycmds
    if verbose:
        s = 'Running svn command:\n  '
        for i in cmd: s += i + ' '
        print(s)
    p = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    res,err = MakeByte2str(p.communicate())
    return res

def DownloadG2Binaries(g2home,verbose=True):
    '''Download GSAS-II binaries from appropriate section of the
    GSAS-II svn repository based on the platform, numpy and Python
    version
    '''    
    bindir = GetBinaryPrefix()
    #npver = 'n{}.{}'.format(*np.__version__.split('.')[0:2])
    inpver = intver(np.__version__)
    svn = whichsvn()
    if not svn:
        print('**** unable to load files: svn not found ****')
        return ''
    # get binaries matching the required type -- other than for the numpy version
    cmd = [svn, 'list', g2home + '/Binaries/','--non-interactive', '--trust-server-cert']
    if proxycmds: cmd += proxycmds
    if verbose:
        s = 'Running svn command:\n  '
        for i in cmd: s += i + ' '
        print(s)
    p = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    res,err = MakeByte2str(p.communicate())
    versions = {}
    for d in res.split():
        if d.startswith(bindir):
            v = intver(d.rstrip('/').split('_')[3].lstrip('n'))
            versions[v] = d
    intVersionsList = sorted(versions.keys())
    if not intVersionsList:
        print('No binaries located')
        return
    elif inpver < min(intVersionsList):
        vsel = min(intVersionsList)
        print('Warning: The current numpy version, {}, is older than\n\tthe oldest dist version, {}'
              .format(np.__version__,fmtver(vsel)))
    elif inpver >= max(intVersionsList):
        vsel = max(intVersionsList)
        if verbose: print(
                'FYI: The current numpy version, {}, is newer than the newest dist version {}'
                .format(np.__version__,fmtver(vsel)))
    else:
        vsel = min(intVersionsList)
        for v in intVersionsList:
            if v <= inpver:
                vsel = v
            else:
                if verbose: print(
                        'FYI: Selecting dist version {} as the current numpy version, {},\n\tis older than the next dist version {}'
                        .format(fmtver(vsel),np.__version__,fmtver(v)))
                break
    distdir = g2home + '/Binaries/' + versions[vsel]
    # switch reset command: distdir = g2home + '/trunk/bindist'
    svnSwitchDir('bindist','',distdir,verbose=verbose)
    return os.path.join(path2GSAS2,'bindist')

# def svnTestBranch(loc=None):
#     '''Returns the name of the branch directory if the installation has been switched.
#     Returns none, if not a branch
#     the test 2frame branch. False otherwise
#     '''
#     if loc is None: loc = path2GSAS2
#     svn = whichsvn()
#     if not svn:
#         print('**** unable to load files: svn not found ****')
#         return ''
#     cmd = [svn, 'info', loc]
#     if proxycmds: cmd += proxycmds
#     p = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
#     res,err = MakeByte2str(p.communicate())
#     for l in res.split('\n'):
#         if "Relative URL:" in l: break
#     if "/branch/" in l:
#         return l[l.find("/branch/")+8:].strip()
#     else:
#         return None
    
def svnSwitch2branch(branch=None,loc=None,svnHome=None):
    '''Switch to a subversion branch if specified. Switches to trunk otherwise.
    '''
    if svnHome is None: svnHome = g2home
    svnURL = svnHome + '/trunk'
    if branch:
        if svnHome.endswith('/'):
            svnURL = svnHome[:-1]
        else:
            svnURL = svnHome
        if branch.startswith('/'):
            svnURL += branch
        else:
            svnURL += '/' + branch
    svnSwitchDir('','',svnURL,loadpath=loc)
    

def IPyBreak_base(userMsg=None):
    '''A routine that invokes an IPython session at the calling location
    This routine is only used when debug=True is set in config.py
    '''
    savehook = sys.excepthook # save the exception hook
    try: 
        from IPython.terminal.embed import InteractiveShellEmbed
    except ImportError:
        try:
            # try the IPython 0.12 approach
            from IPython.frontend.terminal.embed import InteractiveShellEmbed
        except ImportError:
            print ('IPython InteractiveShellEmbed not found')
            return
    import inspect
    ipshell = InteractiveShellEmbed()

    frame = inspect.currentframe().f_back
    msg   = 'Entering IPython console inside {0.f_code.co_filename} at line {0.f_lineno}\n'.format(frame)
    if userMsg: msg += userMsg
    ipshell(msg,stack_depth=2) # Go up one level, to see the calling routine
    sys.excepthook = savehook # reset IPython's change to the exception hook

try:
    from IPython.core import ultratb
except:
    pass
def exceptHook(*args):
    '''A routine to be called when an exception occurs. It prints the traceback
    with fancy formatting and then calls an IPython shell with the environment
    of the exception location.
    
    This routine is only used when debug=True is set in config.py    
    '''
    import IPython.core
    if sys.platform.startswith('win'):
        IPython.core.ultratb.FormattedTB(call_pdb=False,color_scheme='NoColor')(*args)
    else:
        IPython.core.ultratb.FormattedTB(call_pdb=False,color_scheme='LightBG')(*args)

    try: 
        from IPython.terminal.embed import InteractiveShellEmbed
    except ImportError:
        try:
            # try the IPython 0.12 approach
            from IPython.frontend.terminal.embed import InteractiveShellEmbed
        except ImportError:
            print ('IPython InteractiveShellEmbed not found')
            return
    import inspect
    frame = inspect.getinnerframes(args[2])[-1][0]
    msg   = 'Entering IPython console at {0.f_code.co_filename} at line {0.f_lineno}\n'.format(frame)
    savehook = sys.excepthook # save the exception hook
    try:
        InteractiveShellEmbed(banner1=msg)(local_ns=frame.f_locals,global_ns=frame.f_globals)
    except: # use a different call for IPython 5
        class c(object): pass
        pseudomod = c() # create something that acts like a module
        pseudomod.__dict__ = frame.f_locals
        InteractiveShellEmbed(banner1=msg)(module=pseudomod,global_ns=frame.f_globals)
    sys.excepthook = savehook # reset IPython's change to the exception hook

def DoNothing():
    '''A routine that does nothing. This is called in place of IPyBreak and pdbBreak
    except when the debug option is set True in config.py
    '''
    pass 

IPyBreak = DoNothing
pdbBreak = DoNothing
def InvokeDebugOpts():
    'Called in GSASII.py to set up debug options'
    if GetConfigValue('debug'):
        print ('Debug on: IPython: Exceptions and G2path.IPyBreak(); pdb: G2path.pdbBreak()')
        sys.excepthook = exceptHook
        import pdb
        global pdbBreak
        pdbBreak = pdb.set_trace
        global IPyBreak
        IPyBreak = IPyBreak_base

def TestSPG(fpth):
    '''Test if pyspg.[so,.pyd] can be run from a location in the path
    '''
    if not os.path.exists(fpth): return False
    if not glob.glob(os.path.join(fpth,'pyspg.*')): return False
    savpath = sys.path[:]
    sys.path = [fpth]
    # test to see if a shared library can be used
    try:
        import pyspg
        pyspg.sgforpy('P -1')
    except Exception as err:
        print(70*'=')
        print('Failed to run pyspg in {}\nerror: {}'.format(fpth,err))
        print(70*'=')
        sys.path = savpath
        return False
    sys.path = savpath
    return True
    
# see if a directory for local modifications is defined. If so, stick that in the path
if os.path.exists(os.path.expanduser('~/.G2local/')):
    sys.path.insert(0,os.path.expanduser('~/.G2local/'))
    import glob
    fl = glob.glob(os.path.expanduser('~/.G2local/GSASII*.py*'))
    files = ""
    prev = None
    for f in sorted(fl): # make a list of files, dropping .pyc files where a .py exists
        f = os.path.split(f)[1]
        if os.path.splitext(f)[0] == prev: continue
        prev = os.path.splitext(f)[0]
        if files: files += ", "
        files += f
    if files:
        print("*"*75)
        print("Warning: the following source files are locally overridden in "+os.path.expanduser('~/.G2local/'))
        print("  "+files)
        print("*"*75)

BinaryPathLoaded = False
def SetBinaryPath(printInfo=True):
    '''
    Add location of GSAS-II shared libraries (binaries: .so or .pyd files) to path
    
    This routine must be executed after GSASIIpath is imported and before any other
    GSAS-II imports are done.
    '''
    # do this only once no matter how many times it is called
    global BinaryPathLoaded
    if BinaryPathLoaded: return
    try:
        inpver = intver(np.__version__)
    except AttributeError: # happens on building docs
        return
    binpath = None
    binprfx = GetBinaryPrefix()
    for loc in os.path.abspath(sys.path[0]),os.path.abspath(os.path.split(__file__)[0]):
        # Look at bin directory (created by a local compile) before looking for standard dist files
        searchpathlist = [os.path.join(loc,'bin')]
        # also look for matching binary dist in loc/AllBinaries
        versions = {}
        for d in glob.glob(os.path.join(loc,'AllBinaries',binprfx+'*')):
            v = intver(d.rstrip('/').split('_')[3].lstrip('n'))
            versions[v] = d
        searchpathlist = [os.path.join(loc,'bin')]
        vmin = None
        vmax = None
        for v in sorted(versions.keys()):
            if v <= inpver:
                vmin = v
            elif v > inpver:
                vmax = v
                break
        if vmin in versions:
            searchpathlist.append(versions[vmin])
        if vmax in versions:
            searchpathlist.append(versions[vmax])
        searchpathlist.append(os.path.join(loc,'bindist'))
        for fpth in searchpathlist:
            if TestSPG(fpth):
                binpath = fpth
                break        
        if binpath: break
    if binpath:                                            # were GSAS-II binaries found
        sys.path.insert(0,binpath)
        if printInfo:
            print('GSAS-II binary directory: {}'.format(binpath))
        BinaryPathLoaded = True
    else:                                                  # try loading them 
        if printInfo:
            print('Attempting to download GSAS-II binary files...')
        try:
            binpath = DownloadG2Binaries(g2home)
        except AttributeError:   # this happens when building in Read The Docs
            if printInfo:
                print('Problem with download')
        if binpath and TestSPG(binpath):
            if printInfo:
                print('GSAS-II binary directory: {}'.format(binpath))
            sys.path.insert(0,binpath)
            BinaryPathLoaded = True
        # this must be imported before anything that imports any .pyd/.so file for GSASII
        else:
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # patch: use old location based on the host OS and the python version,  
            # path is relative to location of the script that is called as well as this file
            BinaryPathLoaded = True
            bindir = None
            if sys.platform == "win32":
                if platform.architecture()[0] == '64bit':
                    bindir = 'binwin64-%d.%d' % sys.version_info[0:2]
                else:
                    bindir = 'binwin%d.%d' % sys.version_info[0:2]
            elif sys.platform == "darwin":
                if platform.architecture()[0] == '64bit':
                    bindir = 'binmac64-%d.%d' % sys.version_info[0:2]
                else:
                    bindir = 'binmac%d.%d' % sys.version_info[0:2]
                #if platform.mac_ver()[0].startswith('10.5.'):
                #    bindir += '_10.5'
            elif sys.platform.startswith("linux"):
                if platform.architecture()[0] == '64bit':
                    bindir = 'binlinux64-%d.%d' % sys.version_info[0:2]
                else:
                    bindir = 'binlinux%d.%d' % sys.version_info[0:2]
            for loc in os.path.abspath(sys.path[0]),os.path.abspath(os.path.split(__file__)[0]):
            # Look at bin directory (created by a local compile) before standard dist
            # that at the top of the path
                fpth = os.path.join(loc,bindir)
                binpath = fpth
                if TestSPG(fpth):
                    sys.path.insert(0,binpath)
                    if printInfo:
                        print('\n'+75*'*')
                        print('  Warning. Using an old-style GSAS-II binary library. This is unexpected')
                        print('  and will break in future GSAS-II versions. Please contact toby@anl.gov')
                        print('  so we can learn what is not working on your installation.')
                        print('GSAS-II binary directory: {}'.format(binpath))
                        print(75*'*')
                    break
            else:
            # end patch
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                if printInfo:
                    print(75*'*')
                    print('Use of GSAS-II binary directory {} failed!'.format(binpath))
                    print(75*'*')
                raise Exception("**** ERROR GSAS-II binary libraries not found, GSAS-II cannot run ****")

    # add the data import and export directory to the search path
    newpath = os.path.join(path2GSAS2,'imports')
    if newpath not in sys.path: sys.path.append(newpath)
    newpath = os.path.join(path2GSAS2,'exports')
    if newpath not in sys.path: sys.path.append(newpath)

    # setup read of config.py, if present
    global configDict
    try:
        import config
        configDict = config.__dict__
        import inspect
        vals = [True for i in inspect.getmembers(config) if '__' not in i[0]]
        if printInfo:
            print (str(len(vals))+' values read from config file '+os.path.abspath(config.__file__))
    except ImportError:
        configDict = {'Clip_on':True}
    except Exception as err:
        if printInfo:
            print("Error importing config.py file: "+str(err))
        configDict = {'Clip_on':True}

if __name__ == '__main__':
    '''What follows is called to update (or downdate) GSAS-II in a separate process. 
    '''
    import time
    time.sleep(1) # delay to give the main process a chance to exit
    # perform an update and restart GSAS-II
    project,version = sys.argv[1:3]
    loc = os.path.dirname(__file__)
    if version == 'trunk':
        svnSwitch2branch('')
    elif '/' in version:
        svnSwitch2branch(version)
    elif version:
        print("Regress to version "+str(version))
        svnUpdateDir(loc,version=version)
    else:
        print("Update to current version")
        svnUpdateDir(loc)
    ex = sys.executable
    if sys.platform == "darwin": # mac requires pythonw which is not always reported as sys.executable
        if os.path.exists(ex+'w'): ex += 'w'
    if project:
        print("Restart GSAS-II with project file "+str(project))
        subprocess.Popen([ex,os.path.join(loc,'GSASII.py'),project])
    else:
        print("Restart GSAS-II without a project file ")
        subprocess.Popen([ex,os.path.join(loc,'GSASII.py')])
    print ('exiting update process')
    sys.exit()
