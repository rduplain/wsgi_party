"""Partyline Dispatcher for WSGI with good intentions."""

from werkzeug.test import create_environ, run_wsgi_app
from werkzeug.urls import url_quote


class MC(DispatcherMiddleware):
    """DispatcherMiddleware which implements our bootstrapping hack."""

    def __init__(self, app, mounts=None, base_url=None):
        super(MC, self).__init__(app, mounts=mounts)
        self.base_url = base_url
        self.attendees = []
        environ = create_environ(path='/invite/', base_url=self.base_url)
        environ['mc_dispatcher'] = self
        for application in self.applications:
            run_wsgi_app(application, environ)

    @property
    def applications(self):
        """A list of all mounted applications, partiers or not."""
        return [self.app] + self.mounts.values()


class DrinkingBuddy(object):
    """Mixin for registration & message passing."""

    def party(self, request):
        """Mount this view function at '/invite/' script path."""
        if hasattr(self, 'on_party'):
            # Hook implementations here. Be sure to 404 to outside world.
            self.on_party(request.environ)
        # Dispatcher loads itself into the environ.
        self.dispatcher = request.environ.get('mc_dispatcher')
        # Every participating application adds itself.
        self.dispatcher.attendees.append(self)
        # Bind to a list of all participating applications.
        self.partiers = self.dispatcher.attendees
        # Return something.
        return repr(self)

    @property
    def buddies(self):
        """Provide a list binding all participating applications."""
        return self.sort_buddies([buddy for buddy in self.partiers
                                  if buddy is not self])

    def sort_buddies(self, buddies):
        """Hook to provide order of buddies used in passing messages."""
        return buddies

    def receive(self, sender, message):
        """Receive a message from another application.

        All applications are locally bound in the same Python process, and this
        message passing occurs in a blocking synchronous call.  This provides
        each application a means to get information from each other application
        bound in the same process.

        We could just expose methods, but a message passing scheme is more
        generic.  I have no particular opinions about messaging, and here model
        message as a key-value tuple -- that is, an item in a dictionary.  The
        key is a message type, and the value is a pack of arguments to pass
        downstream -- a dumb protocol.  The response is a key-value tuple with
        the same message key (to keep symmetric send/receive code) and the
        return value of the implementation's handler.

        This is a poor man's RPC, but in a local process.  Being local, there
        is no concern for serialization.  Should we structure this with an
        existing RPC?  Make suggestions.

        If we are keeping scope to a single WSGI process and have no intention
        of using remote objects, the most straightforward design would be to
        use Python objects exposing methods, either e.g. Flask instances or a
        proxy object (which would expose only selected methods).
        """
        if message == ('ping', None):
            # The "Hello, world!" of message passing.
            return ('pong', None)
        if hasattr(self, 'on_receive'):
            # Hook protocol implementations here.
            return self.on_receive(sender, message)
        # No handler, send a None response.
        return (message[0], None)

    def send(self, sender, message):
        """Send a message. Here, alias of receive."""
        if hasattr(self, 'on_send'):
            # Provide a separate hook on send.
            self.on_send(sender, message)
        # Just an alias. Could rid of this method entirely.
        return self.receive(sender, message)
