import sys

from scrapy.utils.misc import load_object
from twisted.application.service import Application
from twisted.application.internet import TimerService, TCPServer
from twisted.web import server
from twisted.python import log
from twisted.cred.portal import Portal
from twisted.web.guard import HTTPAuthSessionWrapper, BasicCredentialFactory

from scrapy.utils.misc import load_object

from scrapyd.interfaces import IEggStorage, IJobStorage, IPoller, ISpiderScheduler, IEnvironment
from scrapyd.scheduler import SpiderScheduler
from scrapyd.poller import QueuePoller
from scrapyd.environ import Environment
from scrapyd.basicauth import PublicHTMLRealm, StringCredentialsChecker
import os

def create_wrapped_resource(webcls, config, app):
    username = config.get('username', '')
    password = config.get('password', '')
    if ':' in username:
        sys.exit("The `username` option contains illegal character ':', "
                 "check and update the configuration file of Scrapyd")
    resource = webcls(config, app)
    if username and password:
        log.msg("Basic authentication enabled")
        portal = Portal(PublicHTMLRealm(resource),
                        [StringCredentialsChecker(username, password)])
        credential_factory = BasicCredentialFactory("Auth")
        return HTTPAuthSessionWrapper(portal, [credential_factory])
    else:
        log.msg("Basic authentication disabled as either `username` or `password` is unset")
        return resource


def application(config):
    app = Application("Scrapyd")
    http_port = config.getint('http_port', 6800)
    
    if 'PORT' in os.environ:
        http_port = int(os.environ.get('PORT'))

    bind_address = '0.0.0.0' if 'PORT' in os.environ else config.get('bind_address', '127.0.0.1')

    poll_interval = config.getfloat('poll_interval', 5)

    poller = QueuePoller(config)
    scheduler = SpiderScheduler(config)
    environment = Environment(config)

    app.setComponent(IPoller, poller)
    app.setComponent(ISpiderScheduler, scheduler)
    app.setComponent(IEnvironment, environment)

    jspath = config.get('jobstorage', 'scrapyd.jobstorage.MemoryJobStorage')
    jscls = load_object(jspath)
    jobstorage = jscls(config)
    app.setComponent(IJobStorage, jobstorage)
    eggstorage = config.get('eggstorage', 'scrapyd.eggstorage.FilesystemEggStorage')
    eggstoragecls = load_object(eggstorage)
    app.setComponent(IEggStorage, eggstoragecls(config))

    laupath = config.get('launcher', 'scrapyd.launcher.Launcher')
    laucls = load_object(laupath)
    launcher = laucls(config, app)

    timer = TimerService(poll_interval, poller.poll)

    webpath = config.get('webroot', 'scrapyd.website.Root')
    webcls = load_object(webpath)
    resource = create_wrapped_resource(webcls, config, app)
    webservice = TCPServer(http_port, server.Site(resource), interface=bind_address)
    log.msg(format="Scrapyd web console available at http://%(bind_address)s:%(http_port)s/",
            bind_address=bind_address, http_port=http_port)

    launcher.setServiceParent(app)
    timer.setServiceParent(app)
    webservice.setServiceParent(app)

    return app
