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
from Products.Zuul.interfaces import IRRDDataSourceInfo
from Products.Zuul.form import schema
from Products.Zuul.utils import ZuulMessageFactory as _t


class IDigMonitorDataSourceInfo(IRRDDataSourceInfo):
    timeout = schema.Int(title=_t(u'Timeout (seconds)'))
    cycletime = schema.Int(title=_t(u'Cycle Time (seconds)'))
    dnsServer = schema.Text(title=_t(u'DNS Server'))
    recordName = schema.Text(title=_t(u'Record Name'))
    port = schema.Int(title=_t(u'Port'))
    recordType = schema.Choice(title=_t(u'Record Type'),
                               vocabulary="dnsMonitorRecordTypeVocabulary")
                      
    
    
    

