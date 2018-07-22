# this should install all these modules into ../../sitepackages/uqd
# make a uqd.pth file
# the extra_path make a .pth file - careful here the manual says
# i should used install_path

from distutils.core import setup

# print dir(install)
setup(name="uqdbuffer", packages=[""], extra_path=["uqdbuffer"])
