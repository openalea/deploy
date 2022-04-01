.. image:: https://img.shields.io/badge/License-CeCILL_C-blue.svg
   :target: http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html

.. image:: https://ci.appveyor.com/api/projects/status/8d3qs5f00wriryo2/branch/master?svg=true
   :target: https://ci.appveyor.com/project/fredboudon/deploy

========================
Openalea.Deploy
========================

.. {# pkglts, doc

.. #}

OpenAlea.Deploy support the installation of OpenAlea packages via the network and manage their dependencies. It is an extension of Setuptools. 

**Authors** : S. Dufour-Kowalski, C. Pradal

**Contributors** : OpenAlea Consortium

**Institutes** : INRIA/CIRAD/INRA

**Type** : Pure Python package

**Status** : Devel

**License** : CeCILL-C


About
------

OpenAlea.Deploy support the installation of OpenAlea packages via the network and manage
their dependencies .
It is an extension of Setuptools_.
The last version is only available for Python 3.


**Additional Features** :
   * Discover and manage packages in EGG format
   * Declare shared libraries directory and include directories
   * Call SCons scripts

It doesn't include any GUI interface (See [[packages:compilation_installation:deploygui:deploygui|OpenAlea.DeployGui]] for that).

Requirements
-------------

  * Python_ >= 3.7
  * Setuptools_

Download
---------

See the [[:download|Download page]].

Installation
-------------

  python setup.py install

.. note::

  OpenAlea.Deploy can be automatically installed with the *alea_setup.py* script.


.. _Setuptools: https://setuptools.pypa.io/
.. _Python: http://www.python.org


Developper Documentation
-------------------------

To distribute your package with OpenAlea.Deploy, you need to write a setup.py script
as you do with setuptools.

  * have a look to the Setuptools_ developer's guide.
  * OpenAlea.Deploy add a numerous of keywords and commands

Setup keywords
###############

  * scons_scripts = [list of Scons scripts] : if not empty, call scons to build extensions
  * scons_parameters = [list of Scons parameters] : such as ``build_prefix=...``
  * postinstall_scripts = [list of strings] : Each string corresponds to a python module to execute at installation time. The module may contain a install function ``def install():``.
  * inc_dirs = {dict of dest_dir:src_dir} : Dictionary to map the directory containing the header files.
  * lib_dirs = {dict of dest_dir:src_dir} : Dictionary to map the directory containing the dynamic libraries to share.
  * share_dirs = {dict of dest_dir:src_dir} : Dictionary to map the directory containing shared data.

Additional setup.py commands
#############################

   * *scons* : call scons scripts, usage : ``python setup.py scons``.

For more information see : ``python setup.py --help-commands``

Setup.py example
#################

::

    import sys
    import os
    from setuptools import setup, find_packages
    from os.path import join as pj

    build_prefix = "build-scons"

    # Setup function
    setup(
        name = "OpenAlea.FakePackage",
        version = "0.1",
        author = "Me",
        author_email = "me@example.com",
        description = "This is an Example Package",
        license = 'GPL',
        keywords = 'fake',
        url = 'http://myurl.com',

        # Scons
        scons_scripts = ["SConstruct"],
        scons_parameters = ["build_prefix=%s"%(build_prefix)],

        # Packages
        namespace_packages = ["openalea"],
        packages = ['openalea.fakepackage', ],

        package_dir = {
                    'openalea.fakepackage':  pj('src','fakepackage'),
                    '' : 'src',  # necessary to use develop command
                      },
        include_package_data = True,
        zip_safe= False,

        # Specific options of openalea.deploy
        lib_dirs = { 'lib' : pj(build_prefix, 'lib'), },
        inc_dirs = { 'include' : pj(build_prefix, 'include') },
        share_dirs = { 'share' : 'share' },

        # Scripts
        entry_points = { 'console_scripts': [
                               'fake_script = openalea.fakepackage.amodule:console_script', ],
                         'gui_scripts': [
                               'fake_gui = openalea.fakepackage.amodule:gui_script',]},

        # Dependencies
        setup_requires = ['openalea.deploy'],

    )




