##############################################################################
# 
# Copyright (C) Zenoss, Inc. 2018, all rights reserved.
# 
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
# 
##############################################################################


from distutils.util import strtobool
import logging
import re
import time

import Products.ZenModel.RRDDataSource as RRDDataSource

from twisted.internet import defer
from twisted.names import client, dns, error

from Products.ZenEvents import ZenEventClasses

from ZenPacks.zenoss.PythonCollector.datasources.PythonDataSource \
    import PythonDataSource, PythonDataSourcePlugin

log = logging.getLogger('zen.DigMonitor')

RECORDS = {
    'A':        {'id': 1,  'message': 'messageA'},
    'AAAA':     {'id': 28, 'message': 'messageAaaa'},
    'CNAME':    {'id': 5,  'message': 'messageCnameNsPtr'},
    'MX':       {'id': 15, 'message': 'messageMx'},
    'NAPTR':    {'id': 35, 'message': 'messageNaptr'},
    'NS':       {'id': 2,  'message': 'messageCnameNsPtr'},
    'PTR':      {'id': 12, 'message': 'messageCnameNsPtr'},
    'SOA':      {'id': 6,  'message': 'messageSoa'},
    'SRV':      {'id': 33, 'message': 'messageSrv'},
    'TXT':      {'id': 16, 'message': 'messageTxt'},
    'SSHFP':    {'id': 44, 'message': 'messageSshfp'},
}


class DnsException(Exception):
    """
    Dns Exception.
    """


class DigMonitorDataSource(PythonDataSource):
    
    ZENPACKID = 'ZenPacks.zenoss.DigMonitor'
    DIG_MONITOR = 'DigMonitor'
    
    sourcetypes = (DIG_MONITOR,)
    sourcetype = DIG_MONITOR

    plugin_classname = (
        ZENPACKID + '.datasources.DigMonitorDataSource.DigMonitorDataSourcePlugin')

    eventClass = '/Status/DNS'
    allRecordTypes = ['A', 'AAAA', 'CNAME', 'MX', 'NAPTR', 'NS',
                      'PTR', 'SOA', 'SRV', 'TXT', 'SSHFP']
    
    dnsServer = '${dev/id}'
    port = 53
    recordName = 'zenoss.com' # todo
    recordType = 'A' #todo
    timeout = 60
    tcp = False

    _properties = RRDDataSource.RRDDataSource._properties + (
        {'id':'dnsServer', 'type':'string', 'mode':'w'},
        {'id':'port', 'type':'int', 'mode':'w'},
        {'id':'recordName', 'type':'string', 'mode':'w'},
        {'id':'recordType', 'type':'string', 'mode':'w'},
        {'id':'timeout', 'type':'int', 'mode':'w'},
        {'id':'tcp', 'type':'boolean', 'mode':'w'},
        )


class DigMonitorDataSourcePlugin(PythonDataSourcePlugin):

    @classmethod
    def params(cls, datasource, context):
        params = {}

        params['dnsServer'] = datasource.talesEval(
            datasource.dnsServer, context)

        params['port'] = datasource.talesEval(
            datasource.port, context)

        params['recordName'] = datasource.talesEval(
            datasource.recordName, context)

        params['recordType'] = datasource.talesEval(
            datasource.recordType, context)

        params['eventKey'] = datasource.talesEval(
            datasource.eventKey, context)

        params['component'] = datasource.talesEval(
            datasource.component, context)

        params['timeout'] = datasource.talesEval(
            datasource.timeout, context)

        params['useTCP'] = datasource.talesEval(
            datasource.tcp, context)        

        return params

    def collect(self, config):
        ds0 = config.datasources[0]

        dnsServer = ds0.params['dnsServer']
        port = ds0.params['port']

        if dnsServer:
            self.resolver = client.Resolver(servers=[(dnsServer, int(port))])
        else:
            self.resolver = client.Resolver('/etc/resolv.conf')
        self._startTime = time.time()
        
        query = self.resolver.queryUDP
        if strtobool(ds0.params.get('useTCP', 'False')):
            query = self.resolver.queryTCP

        d = query([dns.Query(ds0.params['recordName'],
            RECORDS.get(ds0.params['recordType'])['id'])])

        return d

    def onSuccess(self, result, config):
        respTime = time.time() - self._startTime
        data = self.new_data()
        perfData = {}
        perfData['time'] = respTime
        ds0 = config.datasources[0]

        if not result.answers:
            message = ("DNS CRITICAL - {:.3f} seconds response time "
                "(No ANSWER SECTION found)".format(
                respTime))
            raise DnsException(message)
        else:
            response = result.answers[0]        
        
        message = getattr(self,
            RECORDS.get(ds0.params['recordType'])['message'])(
            response, respTime)
        import pdb; pdb.set_trace()
        log.debug('{} {}'.format(config.id, message))

        for dp in ds0.points:
            if dp.id in perfData:
                data['values'][None][dp.id] = perfData[dp.id]

        eventKey = ds0.eventKey  or 'DnsMonitorWarning'

        data['events'].append({
            'eventClassKey': 'DigMonitorSuccess',
            'eventKey': eventKey,
            'summary': message,
            'message': message,
            'device': config.id,
            'eventClass': ds0.eventClass,
            'severity': ZenEventClasses.Clear
        })

        return data

    def onError(self, result, config):
        import pdb; pdb.set_trace()
        respTime = time.time() - self._startTime
        DNSNameError = False
        data = self.new_data()
        perfData = {}
        ds0 = config.datasources[0]
        if hasattr(result.value, 'subFailure'):
            if isinstance(result.value.subFailure.value, error.DNSNameError):
                message = ("DNS WARNING - "
                    "Server: {} - Domain name '{}' "
                    "not found".format(self.resolver.pickServer()[0],
                        ds0.params['recordName']))
                DNSNameError = True
            elif isinstance(result.value.subFailure.value, defer.TimeoutError):
                message = ("DNS WARNING - "
                    "Server: {}, Port: {} - "
                    "TimeoutError".format(
                        self.resolver.pickServer()[0],
                        self.resolver.pickServer()[1]))
            severity = ds0.severity
        else:
            message = '{}'.format(result.getErrorMessage())
            severity = ZenEventClasses.Error

        if not isinstance(result.value, DnsException) and not DNSNameError:
            respTime = None
        
        log.error('{} {}'.format(config.id, message))

        if respTime:
            perfData['time'] = respTime
            for dp in ds0.points:
                if dp.id in perfData:
                    data['values'][None][dp.id] = perfData[dp.id]

        eventKey = ds0.eventKey or 'DigMonitorWarning'
        data['events'].append({
            'eventClassKey': 'DigMonitorWarning',
            'eventKey': eventKey,
            'summary': message,
            'message': message,
            'device': config.id,
            'severity': severity,
            'eventClass': ds0.eventClass
        })

        return data

    def _getCommonValues(self, response, respTime):
        s = response.__str__()
        values = [respTime]
        for x in ('name', 'ttl', 'class', 'type',):
            pattern = r'(?<={}=)[^\s]+'.format(x)
            if x == 'ttl':
                pattern = r'(?<={}=)[^\s^s]+'.format(x)
            try:
                values.append(
                    re.search(re.compile(pattern), s).group())
            except AttributeError:
                values.append(None)
                
        return values       

    def messageA(self, response, respTime):
        values = self._getCommonValues(response, respTime)
        values.append(response.payload.dottedQuad())

        return ("DNS OK - {:.3f} seconds response time "
            "({}.  {} {} {} {})".format(*values))

    def messageAaaa(self, response, respTime):
        values = self._getCommonValues(response, respTime)
        values.append(response.payload._address)

        return ("DNS OK - {:.3f} seconds response time "
            "({}.  {} {} {} {})".format(*values))

    def messageCnameNsPtr(self, response, respTime):
        values = self._getCommonValues(response, respTime)
        s = response.payload.__str__()
        try:
            name = re.search(re.compile(r'(?<=name=)[^\s]+'), s).group()
        except AttributeError:
            name = None        
        values.append(name)

        return ("DNS OK - {:.3f} seconds response time "
            "({}. {} {} {} {}.)".format(*values))

    def messageMx(self, response, respTime):
        values = self._getCommonValues(response, respTime)
        s = response.payload.__str__()
        try:
            mxname = re.search(re.compile(r'(?<=name=)[^\s]+'), s).group()
        except AttributeError:
            mxname = None
        values.extend((response.payload.preference, mxname))

        return ("DNS OK - {:.3f} seconds response time "
           "({}.  {} {} {} {} {})".format(*values))

    def messageNaptr(self, response, respTime):
        values = self._getCommonValues(response, respTime)
        s = response.payload.__str__()
        for x in ('order', 'preference',):
            pattern = r'(?<={}=)[^\s]+'.format(x)
            try:
                values.append(
                    re.search(re.compile(pattern), s).group())
            except AttributeError:
                values.append(None)
        message = ("DNS OK - {:.3f} seconds response time "
            "({}. {} {} {} {} {}".format(*values))
        for x in ('flags', 'service', 'regexp', 'replacement',):
            pattern = r'(?<={}=)[^\s]+'.format(x)
            try:
                value = re.search(re.compile(pattern), s).group()
                message = message + ' "' + value + '"'
            except AttributeError:
                message+=" "
        message += ".)"

        return message

    def messageSoa(self, response, respTime):
        values = self._getCommonValues(response, respTime)
        s = response.payload.__str__()
        for x in ('mname', 'rname', 'serial', 'refresh',
            'retry', 'expire', 'minimum',):
            pattern = r'(?<={}=)[^\s]+'.format(x)
            try:
                values.append(
                    re.search(re.compile(pattern), s).group())
            except AttributeError:
                values.append(None)

        return ("DNS OK - {:.3f} seconds response time "
            "({}.  {} {} {} {}. {}. {} {} {} {} {})".format(*values))

    def messageSrv(self, response, respTime):
        values = self._getCommonValues(response, respTime)
        s = response.payload.__str__()
        for x in ('priority', 'weight', 'port', 'target',):
            pattern = r'(?<={}=)[^\s]+'.format(x)
            try:
                values.append(
                    re.search(re.compile(pattern), s).group())
            except AttributeError:
                values.append(None)

        return ("DNS OK - {:.3f} seconds response time "
            "({}.  {} {} {} {} {} {} {}.)".format(*values))

    def messageTxt(self, response, respTime):
        values = self._getCommonValues(response, respTime)
        message = ("DNS OK - {:.3f} seconds response time "
            "({}.  {} {} {} ".format(*values))
        for x in response.payload.data:
            message = message + '"' + x + '"'
        message += ")"

        return message

    def messageSshfp(self, response, respTime):
        values = self._getCommonValues(response, respTime)
        st = response.payload.__str__()
        for x in ('algorithm', 'fp_type', 'fingerprint',):
            pattern = r'(?<={}=)[^\s]+'.format(x)
            try:
                values.append(
                    re.search(re.compile(pattern), st).group())
            except AttributeError:
                values.append(None)
        if len(values[-1]) == 64:
            values[-1] = ' '.join((values[-1][:-8], values[-1][-8:]))
        return ("DNS OK - {:.3f} seconds response time "
            "({}. {} {} {} {} {} {})".format(*values))
