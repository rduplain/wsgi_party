# -*- coding: utf-8 -*-
"""
    Partyline dispatcher for WSGI with good intentions.

    :copyright: (c) 2012 by Ron DuPlain.
    :license: BSD, see LICENSE for more details.
"""

from werkzeug.test import create_environ, run_wsgi_app


class WSGIParty(object):
    """Dispatcher for cross-application communication.

    Originally based on :class:`~werkzeug.wsgi.DispatcherMiddleware`.
    """

    #: URL path to the registration URL of participating applications.
    invite_path = '/__invite__/'

    #: Key in environ with reference to this dispatcher.
    partyline_key = 'partyline'

    #: Class to use as the partyline operator, for connecting listeners.
    operator_class = PartylineOperator

    def __init__(self, app, mounts=None, base_url=None):
        #: Application mounted at root.
        self.app = app

        #: Applications mounted at sub URLs, with sub-URL as the key.
        self.mounts = mounts or {}

        #: Base URL for use in environ. Defaults to None.
        self.base_url = base_url

        # A dict of service -> handler mappings.
        self.partyline = {}

        self.send_invitations()

    def __call__(self, environ, start_response):
        """Dispatch WSGI call to a mounted application, default to root app."""
        # TODO: Consider supporting multiple applications mounted at root URL.
        #       Then, consider providing priority of mounted applications.
        #       One application could explicitly override some routes of other.
        script = environ.get('PATH_INFO', '')
        path_info = ''
        while '/' in script:
            if script in self.mounts:
                app = self.mounts[script]
                break
            items = script.split('/')
            script = '/'.join(items[:-1])
            path_info = '/%s%s' % (items[-1], path_info)
        else:
            app = self.mounts.get(script, self.app)
        original_script_name = environ.get('SCRIPT_NAME', '')
        environ['SCRIPT_NAME'] = original_script_name + script
        environ['PATH_INFO'] = path_info
        return app(environ, start_response)

    def send_invitations(self):
        """Call each application via our partyline connection protocol."""
        environ = create_environ(path=self.invite_path, base_url=self.base_url)
        environ[self.partyline_key] = self.operator_class(self)
        for application in self.applications:
            # TODO: Verify/deal with 404 responses from the application.
            run_wsgi_app(application, environ)

    @property
    def applications(self):
        """A list of all mounted applications, matching our protocol or not."""
        return [self.app] + self.mounts.values()

    def connect(self, service, handler):
        """Register a handler for a given service."""
        self.partyline.set_default(service, []).append(handler)

    def send_all(self, service, payload):
        """Notify all listeners of a service and yield their results."""
        for handler in self.partyline[service]:
            # first response wins
            yield handler(payload)


class PartylineOperator(object):
    """Expose an API for connecting a listener to the WSGI partyline.

    The WSGI application uses this object to communicate with the party.
    """

    def __init__(self, dispatcher):
        self.dispatcher = dispatcher

    def connect(self, service, handler):
        self.dispatcher.register(service, handler)

    def send_all(self, service, payload):
        self.dispatcher.send_all(service, payload)


class PartylineException(Exception):
    """Base exception class for wsgi_party."""


class AlreadyJoinedParty(PartylineException):
    """For bootstrapping; join only once."""
