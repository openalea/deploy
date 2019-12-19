# -*- python -*-
#
#       openalea.deploy.deploy_system
#
#       Copyright 2006-2011 INRIA - CIRAD - INRA
#
#       File author(s): Daniel Barbeau
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
#
#       OpenAlea WebSite : http://openalea.gforge.inria.fr
#
#############################################################################

############################################################
# THIS MODULE IS DEPRECATED, USE DEPLOY_SYSTEM2.PY INSTEAD #
############################################################

from __future__ import absolute_import
from __future__ import print_function
from six.moves import input
__license__ = "Cecill-C"
__revision__ = " $Id$"

from . import distributions, dependency
import sys
from functools import reduce

def install_dependencies(software, osname=None, fake=False):
    if osname is None:
        osname = dependency.get_platform()
    theOs = dependency.OsInterfaceFactory().create(osname)
    dependencies = dependency.DependencySolver(software, osname)

    vrun = False
    vdev = False
    voth = False

    rpkgs = dependencies.runtime_distribution_packages()
    if len(rpkgs):
        print("Do you wish to install the required runtime packages:\n")
        rpkgs = map(str, rpkgs)
        print(" ".join(rpkgs) + " (y/n)?")
        vrun = eval(input())

    dpkgs = dependencies.development_distribution_packages()

    if len(dpkgs):
        print("Do you wish to install the development packages:\n")
        print(" ".join(dpkgs) + " (y/n)?")
        vdev = eval(input())

    opkgs = dependencies.other_packages()
    if len(opkgs:
        print("Do you wish to install the other packages:\n")
        print(" ".join(opkgs) + " (y/n)?")
        voth = eval(input())

    if vrun == "y":
        theOs.install_packages(dependencies.runtime_distribution_packages(), fake)
    if vdev == "y":
        theOs.install_packages(dependencies.development_distribution_packages(), fake)
    if voth == "y":
        theOs.install_packages(dependencies.other_packages(), fake)

usage = """
Usage:
deploy_system sofware_name [os_name=Fedora] [dry_run=True]
* software_name can be any from :
%s

* os_name can be a distribution name (eg. Fedora, Ubuntu)
or more specifically, a release name (eg. "Ubuntu Karmic").
If not specified deploy_system will choose the dependencies
for the one it is running on.

* dry_run can be True or False. Defaults to False
"""

def main():

    print("""
############################################################
# THIS MODULE IS DEPRECATED, USE DEPLOY_SYSTEM2.PY INSTEAD #
############################################################
""")
    if len(sys.argv)==1:
        print(usage%( reduce( lambda x, y: x+" "+y, iter(distributions.canonical_dependencies.keys()) ), ))
        sys.exit(-1)

    software = sys.argv[1]

    args   = dict( arg.split("=") for arg in sys.argv[2:] )
    osname   = args.get("os_name", None)
    fake     = bool(args.get("dry_run", False))

    install_dependencies(software, osname, fake)


if __name__=="__main__":
    main()
