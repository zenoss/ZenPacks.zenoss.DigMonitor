###########################################################################
#
# This program is part of Zenoss Core, an open source monitoring platform.
# Copyright (C) 2010, Zenoss Inc.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 or (at your
# option) any later version as published by the Free Software Foundation.
#
# For complete information please visit: http://www.zenoss.com/oss/
#
###########################################################################
from Products.Zuul.infos import ProxyProperty
from zope.schema.vocabulary import SimpleVocabulary
from zope.interface import implements
from Products.Zuul.infos.template import RRDDataSourceInfo
from ZenPacks.zenoss.DigMonitor.interfaces import IDigMonitorDataSourceInfo
from ZenPacks.zenoss.DigMonitor.datasources.DigMonitorDataSource import DigMonitorDataSource

def recordTypeVocabulary(context):
    # somehow build items [(name, value)]
    return SimpleVocabulary.fromValues(DigMonitorDataSource.allRecordTypes)

class DigMonitorDataSourceInfo(RRDDataSourceInfo):
    implements(IDigMonitorDataSourceInfo)
    timeout = ProxyProperty('timeout')
    cycletime = ProxyProperty('cycletime')
    dnsServer = ProxyProperty('dnsServer')
    port = ProxyProperty('port')
    recordName = ProxyProperty('recordName')
    recordType = ProxyProperty('recordType')
    
    @property
    def testable(self):
        """
        We can NOT test this datsource against a specific device
        """
        return False
    


