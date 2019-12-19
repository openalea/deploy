###############################################################################
# -*- python -*-
#
#       OpenAlea.Deploy : OpenAlea setuptools extension
#
#       Copyright 2006-2009 INRIA - CIRAD - INRA
#
#       File author(s): Samuel Dufour-Kowalski <samuel.dufour@sophia.inria.fr>
#                       Christophe Pradal <christophe.prada@cirad.fr>
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
#
#       OpenAlea WebSite : http://openalea.gforge.inria.fr
#
###############################################################################
""" Environment variable manipulation functions """

from __future__ import absolute_import
from __future__ import print_function
__license__ = "Cecill-C"
__revision__ = " $Id$"

import os
import sys
from os.path import join, exists
from os import makedirs

from openalea.deploy.util import is_conda_env, conda_prefix


def get_posix_activate_export_str(vars):
    # Build string
    exportstr = "############ Configuration ############\n\n"

    for newvar in vars:

        vname, value = newvar.split('=')

        # Exception
        lib_names = ['LD_LIBRARY_PATH', 'DYLD_FALLBACK_LIBRARY_PATH',
                     'DYLD_FRAMEWORK_PATH']
        if (vname in lib_names and
                (value in ["/usr/local/lib", "/opt/local/lib", "/usr/lib"])):
            continue

        if (((vname in lib_names) or (vname == "PATH")) and value):
            exportstr += 'if [ -z "$%s" ]; then\n' % (vname)
            exportstr += '  export %s=%s\n' % (vname, value,)
            exportstr += 'else\n'
            exportstr += '   export %s=%s:$%s\n' % (vname, value, vname,)
            exportstr += 'fi\n\n'

        elif (vname and value):
            exportstr += 'export %s=%s\n\n' % (vname, value)

    exportstr += "############ Configuration END ########"
    return exportstr


def get_posix_deactivate_export_str(vars):
    # Build string
    exportstr = "############ Configuration ############\n\n"

    for newvar in vars:

        vname, value = newvar.split('=')

        # Exception
        lib_names = ['LD_LIBRARY_PATH', 'DYLD_FALLBACK_LIBRARY_PATH',
                     'DYLD_FRAMEWORK_PATH', 'PATH']
        if (vname in lib_names):
            continue
        else:
            exportstr += 'unset  %s\n' % vname

    exportstr += "############ Configuration END ########"
    return exportstr


def get_win32_activate_export_str(vars):
    # Build string
    exportstr = "############ Configuration ############\n\n"

    for newvar in vars:

        vname, value = newvar.split('=')

        if ((vname == "PATH") and value):
            exportstr += 'if [ -z "$%s" ]; then\n' % (vname)
            exportstr += '  export %s=%s\n' % (vname, value,)
            exportstr += 'else\n'
            exportstr += '   export %s=%s:$%s\n' % (vname, value, vname,)
            exportstr += 'fi\n\n'

        elif (vname and value):
            exportstr += 'export %s=%s\n\n' % (vname, value)

    exportstr += "############ Configuration END ########"
    return exportstr


def get_win32_deactivate_export_str(vars):
    # Build string
    exportstr = "############ Configuration ############\n\n"

    for newvar in vars:

        vname, value = newvar.split('=')

        if (vname == "PATH"):
            continue
        else:
            exportstr += 'set  %s=\n' % vname

    exportstr += "############ Configuration END ########"
    return exportstr


def set_lsb_env(name, vars):
    """
    Write a sh script in /etc/profile.d which set some environment variable
    LIBRARY_PATH and PATH are processed in order to avoid overwriting

    :param name: file name string without extension
    :param vars: ['VAR1=VAL1', 'VAR2=VAL2', 'LIBRARY_PATH=SOMEPATH']
    """
    if is_conda_env():
        return set_conda_env(vars, name)

    if ('posix' not in os.name):
        return

    exportstr = get_posix_activate_export_str(vars)

    try:
        filename = '/etc/profile.d/' + name + '.sh'
        filehandle = open(filename, 'w')
    except:
        # On Mac, we set the /etc/profile file (there is not .bashrc file)
        if "darwin" in sys.platform.lower():
            filename = os.path.join(os.path.expanduser('~'), ".profile")
        else:
            filename = os.path.join(os.path.expanduser('~'), ".bashrc")

        print("Warning : Cannot create /etc/profile.d/%s.sh" % (name))
        print("Trying to setup environment in %s" % filename)

        # If profile.d directory is not writable, try to update $HOM/.bashrc
        try:
            script_name = ".%s.sh" % (name)

            filehandle = open(filename, 'r')
            bashrc = filehandle.read()
            filehandle.close()

            # create the string to look for : "source ~/.openalea.sh"
            bashrc_cmd = "source ~/%s" % (script_name,)

            # post processing: remove all commented lines to avoid to consider
            # these lines as valid; in particular :"#source ~/.bashrc
            bashrc_list = bashrc.split('\n')
            bashrc = []
            for line in bashrc_list:
                if not line.startswith('#'):
                    bashrc.append(line)

            # search for the "source ~/.openalea.sh" string
            if bashrc_cmd not in bashrc:
                filehandle = open(filename, 'a+')
                filehandle.write('\n' + bashrc_cmd)
                filehandle.close()

            # create the openalea shell script
            filename = os.path.join(os.path.expanduser('~'), script_name)
            filehandle = open(filename, 'w')

        except Exception as e:
            print(e)
            raise

    print("Creating %s" % (filename,))

    filehandle.write(exportstr)

    filehandle.close()
    # cmdstr = "(echo $SHELL|grep bash>/dev/null)&&. %s
    # ||source %s"%(filename,filename)
    cmdstr = ". %s" % (filename,)
    print("To enable new OpenAlea config, open a new shell or type")
    print('  $ %s' % (bashrc_cmd))


def set_win_env(vars):
    """
    Set Windows environment variable persistently by editing the registry

    :param vars: ['VAR1=VAL1', 'VAR2=VAL2', 'PATH=SOMEPATH']
    """
    if is_conda_env():
        return set_conda_env(vars)

    if ('win32' not in sys.platform):
        return

    for newvar in vars:
        try:
            if sys.version_info.major == 2:
                import six.moves.winreg as winreg
            else:
                import winreg
        except ImportError as e:
            print("!!ERROR: Can not access to Windows registry.")
            return

        def queryValue(qkey, qname):
            qvalue, type_id = winreg.QueryValueEx(qkey, qname)
            return qvalue

        name, value = newvar.split('=')

        regpath = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
        reg = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        try:
            key = winreg.OpenKey(reg, regpath, 0, winreg.KEY_ALL_ACCESS)
        except WindowsError as we:
            print("Cannot set " + repr(name) + " for all users. Set for current user.")
            winreg.CloseKey(reg)
            regpath = r'Environment'
            reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(reg, regpath, 0, winreg.KEY_ALL_ACCESS)

        # Specific treatment for PATH variable
        if name.upper() == 'PATH':
            value = os.path.normpath(value)
            try:
                actualpath = queryValue(key, name)
            except:
                print('No PATH variable found')
                actualpath = ''

            listpath = actualpath.split(';')
            if not (value in listpath):
                value = actualpath + ';' + value
                print("ADD %s to PATH" % (value,))
            else:
                value = actualpath

            # TEST SIZE
            if (len(value) >= 8191):
                print("!!ERROR!! : PATH variable cannot contain more than 8191 characters")
                print("!!ERROR!! : Please : remove unused value in your environement")
                value = actualpath

        if (name and value):

            expand = winreg.REG_SZ
            # Expand variable if necessary
            if ("%" in value):
                expand = winreg.REG_EXPAND_SZ

            winreg.SetValueEx(key, name, 0, expand, value)
            # os.environ[name] = value #not necessary

        winreg.CloseKey(key)
        winreg.CloseKey(reg)

    # Refresh Environment
    try:
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 0x0002
        sParam = "Environment"

        import win32gui
        res1, res2 = win32gui.SendMessageTimeout(HWND_BROADCAST,
                                                 WM_SETTINGCHANGE, 0, sParam,
                                                 SMTO_ABORTIFHUNG, 100)
        if not res1:
            print("result %s, %s from SendMessageTimeout" % (bool(res1), res2))

    except Exception as e:
        print(e)


def set_conda_env(vars, name='openalea'):
    """
    Set conda environment variable persistently.
    Use method proposed in https://conda.io/docs/user-guide/tasks/manage-environments.html#saving-environment-variables

    :param vars: ['VAR1=VAL1', 'VAR2=VAL2', 'PATH=SOMEPATH']

    """
    envprefix = conda_prefix()

    activate_env_vars_dir = join(envprefix, 'etc', 'conda', 'activate.d')
    deactivate_env_vars_dir = join(envprefix, 'etc', 'conda', 'deactivate.d')

    if not exists(activate_env_vars_dir):
        makedirs(activate_env_vars_dir)

    if not exists(activate_env_vars_dir):
        makedirs(deactivate_env_vars_dir)

    if ('posix' in os.name):
        filename = join(activate_env_vars_dir, name + '.sh')
        config = open(filename, 'w')
        config.write('#!/bin/sh\n\n')
        config.write(get_posix_activate_export_str(vars))
        config.close()

        filename2 = join(deactivate_env_vars_dir, name + '.sh')
        config = open(filename2, 'w')
        config.write('#!/bin/sh\n\n')
        config.write(get_posix_activate_export_str(vars))
        config.close()

    else:
        filename = join(activate_env_vars_dir, name + '.bat')
        config = open(filename, 'w')
        config.write(get_win32_activate_export_str(vars))
        config.close()

        filename2 = join(deactivate_env_vars_dir, name + '.bat')
        config = open(filename2, 'w')
        config.write(get_win32_deactivate_export_str(vars))
        config.close()

    print("Creating %s and %s" % (repr(filename), repr(filename2)))

    if ('posix' in os.name):
        bashrc_cmd = "source %s" % (filename,)
    else:
        bashrc_cmd = "call %s" % (filename,)

    print("To enable new OpenAlea config, open a new shell or type")
    print('  $ %s' % (bashrc_cmd))
