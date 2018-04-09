# -*- coding: utf-8 -*-
import os
import traceback

from util import shell_call, get_version_and_build, change_first_line, install_pip, install_pip_deps

__author__ = "Mike Belov"
__copyright__ = "Copyright (C) Nginx, Inc. All rights reserved."
__license__ = ""
__maintainer__ = "Mike Belov"
__email__ = "dedm@nginx.com"


def build(package=None):
    """
    Builds a deb package

    :param package: str full package name
    """
    pkg_root = os.path.expanduser('~') + '/agent-pkg-root'
    pkg_final = os.path.expanduser('~') + '/agent-package'

    # get version and build
    version, bld = get_version_and_build()

    # get architecture
    arch = shell_call("dpkg-architecture -c 'echo ${DEB_BUILD_ARCH}'").split('\n')[0]

    # get codename
    shell_call("lsb_release -c")  # checks that lsb_release is installed
    codename = shell_call("lsb_release -c | awk '{print $2}'").split('\n')[0]

    # install pip
    install_pip()

    try:
        # delete previous build
        shell_call('rm -rf %s' % pkg_root)
        shell_call('rm -rf %s && mkdir %s' % (pkg_final, pkg_final))

        # install all dependencies
        install_pip_deps(package=package)

        # sed build to control
        shell_call(
            "sed -i 's/^Version: .*$/Version: %s-%s~%s/' packages/%s/deb/DEBIAN/control" % (
                version, bld, codename, package
            )
        )
        shell_call(
            "sed -i 's/^Architecture: .*$/Architecture: %s/' packages/%s/deb/DEBIAN/control" % (
                arch, package
            )
        )

        # sed first line of changelog
        changelog_first_line = '%s (%s-%s~%s) unstable; urgency=low' % (package, version, bld, codename)
        change_first_line('packages/%s/deb/DEBIAN/changelog' % package, changelog_first_line)

        # create python package
        shell_call('cp packages/%s/setup.py ./' % package)
        shell_call('python setup.py install --install-layout=deb --prefix=/usr --root=%s' % pkg_root)

        # copy debian files to pkg-root
        shell_call('cp -r packages/%s/deb/DEBIAN %s/' % (package, pkg_root))

        # create deb package
        package_file = '%s_%s-%s~%s_%s.deb' % (package, version, bld, codename, arch)
        shell_call('fakeroot dpkg --build %s %s/%s' % (pkg_root, pkg_final, package_file))

        # clean
        shell_call('rm -r build', important=False)
        shell_call('rm -r *.egg-*', important=False)
        shell_call('rm setup.py', important=False)
    except:
        print(traceback.format_exc())
