#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Setup.py file generated by PkgLTS."""

# {# pkglts, pysetup.kwds
# format setup arguments

from setuptools import setup, find_packages


short_descr = "OpenAlea.Deploy support the installation of OpenAlea packages via the network and manage their dependencies. It is an extension of Setuptools."
readme = open('README.rst').read()
history = open('HISTORY.rst').read()


# find version number in src/openalea/deploy/version.py
version = {}
with open("src/openalea/deploy/version.py") as fp:
    exec(fp.read(), version)


setup_kwds = dict(
    name='openalea.deploy',
    version=version["__version__"],
    description=short_descr,
    long_description=readme + '\n\n' + history,
    author="openalea",
    author_email="openalea@inria.fr",
    url='https://openalea.gforge.inria.fr',
    license='cecill-c',
    zip_safe=False,

    packages=find_packages('src'),
    namespace_packages=['openalea'],
    package_dir={'': 'src'},
    entry_points={},
    keywords='setuptools, openalea',
    )
# #}
# change setup_kwds below before the next pkglts tag

entry_points = {
    "distutils.setup_keywords": [
        "lib_dirs = openalea.deploy.command:validate_bin_dirs",
        "inc_dirs = openalea.deploy.command:validate_bin_dirs",
        "bin_dirs = openalea.deploy.command:validate_bin_dirs",
        "share_dirs = openalea.deploy.command:validate_share_dirs",
        "cmake_scripts = openalea.deploy.command:validate_cmake_scripts",
        "scons_scripts = openalea.deploy.command:validate_scons_scripts",
        "scons_parameters = setuptools.dist:assert_string_list",
        "add_plat_name = openalea.deploy.command:validate_add_plat_name",
    ],

    "egg_info.writers": [
        "lib_dirs.txt = openalea.deploy.command:write_keys_arg",
        "inc_dirs.txt = openalea.deploy.command:write_keys_arg",
        "bin_dirs.txt = openalea.deploy.command:write_keys_arg",
    ],

    "distutils.commands": [
        "cmake = openalea.deploy.command:cmake",
        "scons = openalea.deploy.command:scons",
    ],
}
setup_kwds["entry_points"] = entry_points
setup_kwds["include_package_data"] = True

# do not change things below
# {# pkglts, pysetup.call
setup(**setup_kwds)
# #}
