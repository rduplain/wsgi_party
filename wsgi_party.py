# -*- coding: utf-8 -*-
"""
    Partyline middleware for WSGI with good intentions.

    :copyright: (c) 2012 by Ron DuPlain.
    :license: BSD, see LICENSE for more details.
"""

from werkzeug.test import create_environ, run_wsgi_app


class PartylineException(Exception):
    """Base exception class for wsgi_party."""


class HighAndDry(PartylineException):
    """Handler does not have a response; skip it."""


class PartylineOperator(object):
    """Expose an API for connecting a listener to the WSGI partyline.

    The WSGI application uses this object to communicate with the party.
    """

    def __init__(self, partyline):
        self.partyline = partyline

    def connect(self, service, handler):
        return self.partyline.connect(service, handler)

    def send_all(self, service, payload):
        return self.partyline.send_all(service, payload)


class WSGIParty(object):
    """Partyline middleware WSGI object."""

    #: Key in environ with reference to the partyline operator.
    partyline_key = 'partyline'

    #: Class to use as the partyline operator, for connecting listeners.
    operator_class = PartylineOperator

    def __init__(self, application, invites=()):
        #: Wrapped WSGI application.
        self.application = application
        self.send_invitations(invites)

    def __call__(self, environ, start_response):
        """Call wrapped application."""
        self.applications(environ, start_response)

    def send_invitations(self, invites):
        """Call each invite route to establish a partyline."""
        self.operator = self.operator_class(self)
        for invite in invites:
            self.send_invitation(invite)

    def send_invitation(self, invite):
        """Call individual route to add an application to the partyline."""
        environ = create_environ(path=invite)
        environ[self.partyline_key] = operator
        run_wsgi_app(application, environ)

    def connect(self, service, handler):
        """Register a handler for a given service."""
        self.partyline.setdefault(service, []).append(handler)

    def send_all(self, service, payload):
        """Notify all listeners of a service and yield their results."""
        for handler in self.partyline[service]:
            try:
                yield handler(payload)
            except HighAndDry:
                pass
