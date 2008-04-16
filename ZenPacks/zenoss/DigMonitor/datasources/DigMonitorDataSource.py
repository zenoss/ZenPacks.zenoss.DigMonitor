###########################################################################
#
# This program is part of Zenoss Core, an open source monitoring platform.
# Copyright (C) 2007, Zenoss Inc.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# For complete information please visit: http://www.zenoss.com/oss/
#
###########################################################################


import Products.ZenModel.RRDDataSource as RRDDataSource
from AccessControl import ClassSecurityInfo, Permissions
from Products.ZenUtils.ZenTales import talesCompile, getEngine


class DigMonitorDataSource(RRDDataSource.RRDDataSource):
    
    DIG_MONITOR = 'DigMonitor'
    
    sourcetypes = (DIG_MONITOR,)
    sourcetype = DIG_MONITOR

    eventClass = '/Status/DNS'
        
    dnsServer = '${dev/id}'
    port = 53
    recordName = 'zenoss.com' # todo
    recordType = 'A' #todo
    timeout = 60

    _properties = RRDDataSource.RRDDataSource._properties + (
        {'id':'dnsServer', 'type':'string', 'mode':'w'},
        {'id':'port', 'type':'int', 'mode':'w'},
        {'id':'recordName', 'type':'string', 'mode':'w'},
        {'id':'recordType', 'type':'string', 'mode':'w'},
        {'id':'timeout', 'type':'int', 'mode':'w'},
        )
        
    _relations = RRDDataSource.RRDDataSource._relations + (
        )


    factory_type_information = ( 
    { 
        'immediate_view' : 'editDigMonitorDataSource',
        'actions'        :
        ( 
            { 'id'            : 'edit',
              'name'          : 'Data Source',
              'action'        : 'editDigMonitorDataSource',
              'permissions'   : ( Permissions.view, ),
            },
        )
    },
    )

    security = ClassSecurityInfo()


    def __init__(self, id, title=None, buildRelations=True):
        RRDDataSource.RRDDataSource.__init__(self, id, title, buildRelations)
        #self.addDataPoints()


    def getDescription(self):
        if self.sourcetype == self.DIG_MONITOR:
            return self.ipAddress + self.hostname
        return RRDDataSource.RRDDataSource.getDescription(self)


    def useZenCommand(self):
        return True


    def getCommand(self, context):
        parts = ['check_dig']
        if self.dnsServer:
            parts.append('-H %s' % self.dnsServer)
        if self.port:
            parts.append('-p %d' % self.port)
        if self.recordName:
            parts.append('-l %s' % self.recordName)
        if self.recordType:
            parts.append('-T %s' % self.recordType)
        if self.timeout:
            parts.append('-t %d' % self.timeout)

        cmd = ' '.join(parts)
        cmd = '$ZENHOME/libexec/' + \
                    RRDDataSource.RRDDataSource.getCommand(self, context, cmd)
        return cmd


    def checkCommandPrefix(self, context, cmd):
        return cmd


    def addDataPoints(self):
        if not hasattr(self.datapoints, 'time'):
            self.manage_addRRDDataPoint('time')


    def zmanage_editProperties(self, REQUEST=None):
        '''validation, etc'''
        if REQUEST:
            # ensure default datapoint didn't go away
            self.addDataPoints()
            # and eventClass
            if not REQUEST.form.get('eventClass', None):
                REQUEST.form['eventClass'] = self.__class__.eventClass
        return RRDDataSource.RRDDataSource.zmanage_editProperties(self, REQUEST)


