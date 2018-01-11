
import Globals
import glob
import platform
import os.path

from Products.ZenModel.ZenPack import ZenPackBase
from Products.ZenUtils.Utils import zenPath

import logging
log = logging.getLogger("zen.DigMonitor")

skinsDir = os.path.join(os.path.dirname(__file__), 'skins')
from Products.CMFCore.DirectoryView import registerDirectory
if os.path.isdir(skinsDir):
    registerDirectory(skinsDir, globals())

def onCollectorInstalled(ob, event):
    zpFriendly = 'DigMonitor'
    errormsg = '{0} binary cannot be found on {1}. This is part of the nagios-plugins ' + \
               'dependency, and must be installed before {2} can function.'
    
    verifyBin = 'check_dig'
    code, output = ob.executeCommand('zenbincheck %s' % verifyBin, 'zenoss', needsZenHome=True)
    if code:
       	log.warn(errormsg.format(verifyBin, ob.hostname, zpFriendly))


class ZenPack(ZenPackBase):

    products = ('twisted',)
    
    def install(self, app):
        self.patchProducts()
        ZenPackBase.install(self, app)

    def upgrade(self, app):
        ZenPackBase.upgrade(self, app)
        self.patchProducts()

    def patchProducts(self):
        for product in self.products:
            relevant_patches = sorted(glob.glob(os.path.join(self.path('src'), product + '.all.patch[0-9]*')))
            for patch in relevant_patches:
                if os.path.isfile(patch):
                    log.info("Patching %s with %s" % (product, patch))
                    log.info(" patch -p0 -d %s -i %s" %
                        (zenPath(), patch))
                    #import pdb; pdb.set_trace()
                    os.system("patch -p0 -d %s -i %s" % (
                        zenPath(), patch))
                else:
                    log.warn("Patch file %s does not exist" % patch)
                    log.warn("Skipping patch -p0 -d %s -i %s" %
                        (zenPath(), patch))
