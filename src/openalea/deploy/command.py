# -*- python -*-
#
#       OpenAlea.Deploy: OpenAlea setuptools extension
#
#       Copyright 2006-2009 INRIA - CIRAD - INRA
#
#       File author(s): Samuel Dufour-Kowalski <samuel.dufour@sophia.inria.fr>
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
#
#       OpenAlea WebSite : http://openalea.gforge.inria.fr
#
"""Setuptools commands.

To extend setuptools, we have to replace setuptools function with our
own function.
"""
from __future__ import print_function


from __future__ import absolute_import

__license__ = "Cecill-C"
__revision__ = " $Id$ "

import os
import subprocess
import sys
import shutil
from distutils.errors import *
import stat
import glob
import shlex

from os.path import join as pj
from setuptools import Command
from setuptools.dist import assert_string_list, assert_bool

from distutils.command.build import build as old_build
from setuptools.command.install_lib import install_lib as old_install_lib
from setuptools.command.build_py import build_py as old_build_py
from setuptools.command.build_ext import build_ext as old_build_ext

from distutils.command.clean import clean as old_clean
import distutils.command.build
import setuptools.command.build_py
import setuptools.command.build_ext
import setuptools.command.install
import setuptools.command.install_lib

from distutils.dist import Distribution

import pkg_resources
from distutils.errors import DistutilsSetupError
# from distutils.util import convert_path
from distutils.dir_util import mkpath
import re

PY3K = False
# Python 3
import configparser
PY3K = True

from .util import get_all_lib_dirs, get_all_bin_dirs, DEV_DIST
from .install_lib import get_dyn_lib_dir
from .util import get_base_dir
from .util import is_virtual_env, is_conda_env, is_conda_build, conda_prefix
#from .environ_var import set_lsb_env, set_win_env
from . import install_lib


# Utility


def copy_data_tree(src, dst, exclude_pattern=['(RCS|CVS|\.svn|\.git)', '.*\~']):
    """
    Copy an entire directory tree 'src' to a new location 'dst'.

    :param exclude_pattern: a list of pattern to exclude.
    """
    names = os.listdir(src)
    mkpath(dst)
    outfiles = []

    for p in exclude_pattern:
        names = [x for x in names if not (re.match(p, x))]

    for n in names:
        src_name = os.path.join(src, n)
        dst_name = os.path.join(dst, n)

        if os.path.isdir(src_name):
            ret = copy_data_tree(src_name, dst_name, exclude_pattern)
            outfiles += ret
        else:
            shutil.copy2(src_name, dst_name)
            outfiles.append(dst_name)

    return outfiles


# Command overloading


def has_ext_modules(dist):
    """ Replacement function for has_ext_module """
    try:
        return (Distribution.has_ext_modules(dist) or
                (dist.scons_scripts or
                 dist.lib_dirs or dist.inc_dirs or
                 dist.bin_dirs) or
                dist.add_plat_name)
    except:
        return dist.has_ext_modules()


def set_has_ext_modules(dist):
    """ Set new function handler to dist object """
    from types import MethodType as instancemethod

    try:
        # Python 2
        m = instancemethod(has_ext_modules, dist, Distribution)
    except TypeError:
        # Python 3
        m = instancemethod(has_ext_modules, dist)

    dist.has_ext_modules = m


class build(old_build):
    """ Override sub command order in build command """

    # We change the order of distutils because scons will install
    # extension libraries inside python repository.

    sub_commands = [('build_ext', old_build.has_ext_modules),
                    ('build_py', old_build.has_pure_modules),
                    ('build_clib', old_build.has_c_libraries),
                    ('build_scripts', old_build.has_scripts),
                    ]


class build_py(old_build_py):
    """
    Enhanced 'build_py'
    """

    def initialize_options(self):
        old_build_py.initialize_options(self)
        self.scons_ext_param = ""  # None value are not accepted
        self.scons_path = None  # Scons path

    def run(self):

        # Add share_dirs
        share_dirs = self.distribution.share_dirs
        if share_dirs:

            """
            if is_conda_env():
                env_dir = os.path.abspath(os.environ['PREFIX'])
                share_dir = os.path.join(env_dir, 'share')

                # get the name of the package
                pkg_name = self.distribution.name.lower()

                for (name, dir) in share_dirs.items():
                    if name == 'share':
                        copy_data_tree(dir, pj(share_dir, pkg_name))

            else:
            """
            if (not os.path.exists(self.build_lib)):
                self.mkpath(self.build_lib)

            for (name, dir) in share_dirs.items():
                copy_data_tree(dir, pj(self.build_lib, name))

        ret = old_build_py.run(self)
        return ret


class build_ext(old_build_ext):
    """
    Enhanced 'build_ext'
    Add lib_dirs and inc_dirs parameters to package parameter
    """

    # User options
    user_options = []
    user_options.extend(old_build_ext.user_options)
    user_options.append(('scons-ext-param=',
                         None,
                         'External parameters to pass to scons.'))
    user_options.append(('scons-path=',
                         None,
                         'Optional scons executable path.'
                         'eg : C:\Python27\scons.bat for windows.'))

    def initialize_options(self):
        old_build_ext.initialize_options(self)
        self.scons_ext_param = ""  # None value are not accepted
        self.scons_path = None  # Scons path

    def run(self):
        # Run others commands

        self.run_command("scons")
        #self.run_command("cmake")

        # Add lib_dirs and include_dirs in packages
        # Copy the directories containing the files generated
        # by scons and the like.
        if is_conda_build():
            print('Building directly with conda. Skip the bin, include and lib dirs.')
            return old_build_ext.run(self)

        for d in (self.distribution.lib_dirs,
                  self.distribution.inc_dirs,
                  self.distribution.bin_dirs,
                  # self.distribution.share_dirs,
                  ):

            if (not d or self.inplace == 1):
                continue

            if (not os.path.exists(self.build_lib)):
                self.mkpath(self.build_lib)

            for (name, dir) in d.items():
                copy_data_tree(dir, pj(self.build_lib, name))

        return old_build_ext.run(self)


class cmd_install_lib(old_install_lib):
    """ Overide install_lib command (execute build_ext before build_py)"""

    def build(self):
        if not self.skip_build:
            if self.distribution.has_ext_modules():
                self.run_command('build_ext')

            if self.distribution.has_pure_modules():
                self.run_command('build_py')

# Validation functions


def validate_scons_scripts(dist, attr, value):
    """ Validation for scons_scripts keyword """
    assert_string_list(dist, attr, value)
    if (value):
        setuptools.command.build_ext.build_ext = build_ext
        distutils.command.build.build = build
        setuptools.command.install_lib.install_lib = cmd_install_lib
        set_has_ext_modules(dist)


def validate_cmake_scripts(dist, attr, value):
    """ Validation for cmake_scripts keyword """
    assert_string_list(dist, attr, value)
    if (value):
        setuptools.command.build_ext.build_ext = build_ext
        distutils.command.build.build = build
        setuptools.command.install_lib.install_lib = cmd_install_lib
        set_has_ext_modules(dist)


def validate_pylint_options(dist, attr, value):
    try:
        assert type(value[0]) == str
    except ValueError:
        raise ValueError("""options %s in the setup.py must be a  such as
            --disable-msg=C0103 that can be used as pylint options""" % attr)


def validate_pylint_packages(dist, attr, value):
    if isinstance(value, list):
        pass
    else:
        raise ValueError("""options %s in the setup.py must be a list of path
             where to find the python source files """ % attr)


def validate_bin_dirs(dist, attr, value):
    """ Validation for shared directories keywords"""

    try:
        assert_string_list(dist, attr, list(value.keys()))
        assert_string_list(dist, attr, list(value.values()))

        if (value):
            # Change commands
            setuptools.command.build_ext.build_ext = build_ext
            setuptools.command.install_lib.install_lib = cmd_install_lib
            #setuptools.command.develop.develop = develop
            set_has_ext_modules(dist)

    except (TypeError, ValueError, AttributeError, AssertionError):
        raise DistutilsSetupError(
            "%r must be a dict of strings (got %r)" % (attr, value))


def validate_share_dirs(dist, attr, value):
    """ Validation for shared directories keywords"""
    try:
        assert_string_list(dist, attr, list(value.keys()))
        assert_string_list(dist, attr, list(value.values()))

        if (value):
            # Change commands
            setuptools.command.build_py.build_py = build_py
            #setuptools.command.install.install = install
            set_has_ext_modules(dist)

    except (TypeError, ValueError, AttributeError, AssertionError):
        raise DistutilsSetupError(
            "%r must be a dict of strings (got %r)" % (attr, value))


def validate_add_plat_name(dist, attr, value):
    """ Validation for add_plat_name keyword"""
    try:
        assert_bool(dist, attr, value)

        if (value):
            # Change commands
            set_has_ext_modules(dist)

    except (TypeError, ValueError, AttributeError, AssertionError):
        raise DistutilsSetupError(
            "%r must be a boolean (got %r)" % (attr, value))


def write_keys_arg(cmd, basename, filename, force=False):
    """ Egg-info writer """

    argname = os.path.splitext(basename)[0]
    value = getattr(cmd.distribution, argname, None)
    if value is not None:
        value = '\n'.join(list(value.keys())) + '\n'
    cmd.write_or_delete_file(argname, filename, value, force)
    if is_conda_env():
        #print('CONDA EGG WRITER: ', cmd, basename, filename, value)
        pass

# SCons Management

class SconsError(Exception):
    """Scons subprocess Exception"""

    def __str__(self):
        return "Scons subprocess has failed."


class scons(Command):
    """
    Call SCons in an external process.
    """

    description = "Run SCons"

    user_options = [('scons-ext-param=',
                     None,
                     'External parameters to pass to scons.'),
                    ('scons-path=',
                     None,
                     'Optional scons executable path. eg : C:\Python27\scons.bat for windows.'),]

    def initialize_options(self):
        self.outfiles = None
        self.scons_scripts = []  # scons directory
        self.scons_parameters = []  # scons parameters
        self.build_dir = None  # build directory
        self.scons_ext_param = None  # scons external parameters
        self.scons_path = None
        self.scons_install = None # install in conda env

    def finalize_options(self):

        # Set default values
        try:
            self.scons_scripts = self.distribution.scons_scripts
            self.scons_parameters = self.distribution.scons_parameters
        except:
            pass

        if (not self.scons_parameters):
            self.scons_parameters = ""

        if not self.scons_install:
            if is_conda_env():
                self.scons_install = True



        self.set_undefined_options('build_ext',
                                   ('build_lib', 'build_dir'),
                                   ('scons_ext_param', 'scons_ext_param'),
                                   ('scons_path', 'scons_path'))

    def get_source_files(self):
        return []

    def run(self):
        """
        Run scons command with subprocess module if available.
        """
        if (not self.scons_scripts):
            return

        # try to import subprocess package
        import subprocess
        subprocess_enabled = True


        # run each scons script from setup.py
        for s in self.scons_scripts:
            try:
                # Join all the SCons parameters.
                file_param = '-f %s' % (s,)

                # Join all parameters strings from setup.py scons_parameters list
                param = ' '.join(self.scons_parameters)

                # Integrated Build parameter
                build_param = 'python_build_dir=%s ' % (self.build_dir,)
                build_param += 'py_pkg_name=%s ' % (
                    self.distribution.metadata.get_name(),)

                # External parameters (from the command line)
                externp = self.scons_ext_param

                if (self.scons_path):
                    command = self.scons_path
                else:
                    command = 'scons'

                command_param = ' '.join([file_param, build_param,
                                          param, externp])
                commandstr = command + ' ' + command_param

                # Run scons install
                # To correctly dispatch the dll in the conda prefix bin dir
                if self.scons_install:

                    commandstr += ' install'

                print(commandstr)

                # Run SCons
                # Fix issue 57 : Martin and Christophe

                command_line = shlex.split(commandstr)
                result = subprocess.run(command_line, shell=True, timeout=None)
                retval = result.returncode

                # Test if command success with return value
                if (retval != 0):
                    raise SconsError()


            except SconsError as i:
                print(i, " Failure...")
                sys.exit(1)

            except Exception as i:
                print("!! Error : Cannot execute scons command:", i, " Failure...")
                sys.exit(1)


# CMake Management

class CMakeError(Exception):
    """CMake subprocess Exception"""

    def __str__(self):
        return "CMake subprocess has failed."


class cmake(Command):
    """
    Call CMake in an external process.
    """

    description = "Run CMake"

    def initialize_options(self):
        self.cmake_scripts = []  # cmake directory
        self.build_dir = None  # build directory

    def finalize_options(self):

        # Set default values
        try:
            self.cmake_scripts = self.distribution.cmake_scripts
        except:
            pass

        self.set_undefined_options('build_ext',
                                   ('build_lib', 'build_dir'),
                                   )

    def run(self):
        """
        Run Cmake command with subprocess module if available.
        """
        if (not self.cmake_scripts):
            return

        # try to import subprocess package
        try:
            import subprocess
            subprocess_enabled = True
        except ImportError:
            subprocess_enabled = False

        # run each CMake script from setup.py
        for s in self.cmake_scripts:
            try:
                # Join all the SCons parameters.
                # file_param = s
                file_param = '../src'

                cmake_cmd = 'cmake'

                cmake_cmd_param = file_param
                commandstr = cmake_cmd + ' ' + cmake_cmd_param

                print(commandstr)

                if not os.path.isdir('build-cmake'):
                    os.mkdir('build-cmake')

                os.chdir('build-cmake')

                # Run CMake
                if (subprocess_enabled):
                    retval = subprocess.call(commandstr, shell=True)
                else:
                    retval = os.system(commandstr)

                # Test if command success with return value
                if (retval != 0):
                    raise CMakeError()

                make_cmd = 'make'
                commandstr = make_cmd

                # Run Make
                if (subprocess_enabled):
                    retval = subprocess.call(commandstr, shell=True)
                else:
                    retval = os.system(commandstr)

                # Test if command success with return value
                if (retval != 0):
                    raise CMakeError()

                os.chdir(os.pardir)

            except CMakeError as i:
                print(i, " Failure...")
                sys.exit(1)

            except Exception as i:
                print("!! Error : Cannot execute cmake command:", i, " Failure...")
                sys.exit(1)

