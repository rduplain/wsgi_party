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
    """A handler raises this when it does not have a response; skip it."""


class NoSuchServiceName(PartylineException):
    """Raised when no handlers are registered for a requested service name."""


class PartylineOperator(object):
    """Expose an API for connecting a handler to the WSGI partyline.

    The WSGI application uses this object to communicate with the party, with
    one operator per invitation, and typically one invitation per WSGI
    application.  One operator per application prevents an application from
    handling a request from itself.
    """

    def __init__(self, partyline):
        #: Instance of :class:`WSGIParty`, required argument.
        self.partyline = partyline

        #: Set of handlers added through :meth:`connect`.
        self.handlers = set()

    def connect(self, service_name, handler):
        """Connect a handler :meth:`ask_around` calls for service_name."""
        self.handlers.add(handler)
        return self.partyline.connect(service_name, handler)

    def ask_around(self, service_name, payload):
        """Ask all handlers of a given service name, return list of answers.

        Handlers connected through this instance are skipped, so that
        applications do not call themselves.
        """
        return self.partyline.ask_around(service_name, payload, operator=self)


class WSGIParty(object):
    """Partyline middleware WSGI object."""

    #: Key in environ with reference to the partyline operator.
    partyline_key = 'partyline'

    #: Class to use as the partyline operator, for connecting handlers.
    operator_class = PartylineOperator

    def __init__(self, application, invites=(), ignore_missing_services=False):
        #: WSGIParty's wrapped WSGI application.
        self.application = application

        #: A dict of service name => handler mappings.
        self.handlers = {}

        #: If True, suppress :class:`NoSuchServiceName` errors. Default: False.
        self.ignore_missing_services = ignore_missing_services

        self.send_invitations(invites)

    def __call__(self, environ, start_response):
        """Call WSGIParty's wrapped application."""
        return self.application(environ, start_response)

    def send_invitations(self, invites):
        """Call each invite route to establish a partyline. Called on init."""
        for invite in invites:
            environ = create_environ(path=invite)
            environ[self.partyline_key] = self.operator_class(self)
            run_wsgi_app(self.application, environ)

    def connect(self, service_name, handler):
        """Register a handler for a given service name."""
        self.handlers.setdefault(service_name, []).append(handler)

    def ask_around(self, service_name, payload, operator=None):
        """Ask all handlers of a given service name, return list of answers.

        Handlers connected through the optionally given operator are skipped,
        so that partyline applications do not call themselves.
        """
        answers = []
        try:
            service_handlers = self.handlers[service_name]
        except KeyError:
            if not self.ignore_missing_services:
                raise NoSuchServiceName('No handler is registered for %r.' %
                                        repr(service_name))
            service_handlers = []
        for handler in service_handlers:
            if operator is not None and handler in operator.handlers:
                # Skip handlers on the same operator, ask *others* for answer.
                continue
            try:
                answers.append(handler(payload))
            except HighAndDry:
                continue
        return answers
