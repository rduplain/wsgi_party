"""A hack with good intentions: build URLs across WSGI applications."""

import copy

from flask import Flask, abort, request
from werkzeug.routing import BuildError
from werkzeug.test import create_environ, run_wsgi_app
from werkzeug.urls import url_quote
from werkzeug.wsgi import DispatcherMiddleware


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


class FlaskDrunk(Flask, DrinkingBuddy):
    """Subclass of Flask which builds URLs across instances via the party."""

    def __init__(self, import_name, *args, **kwargs):
        super(FlaskDrunk, self).__init__(import_name, *args, **kwargs)
        # Bootstrap, turn the view function into a 404 after registering.
        self.pregame = True
        self.add_url_rule('/invite/', endpoint='party', view_func=self.join_party)
        # This dispatcher hook is not currently used, but is potentially useful.
        self.dispatcher = None
        # The list of neighbors for sending/receiving messages.
        self.partiers = []

    def on_party(self, environ):
        """Hook to expose party registration only once, to dispatcher."""
        if not self.pregame:
            # This route does not exist at the HTTP level.
            abort(404)
        self.pregame = False

    def join_party(self, request=request):
        """A simple wrapper to support Flask's request pattern."""
        return self.party(request)

    def on_receive(self, sender, message):
        """Message receive hook to request URLs across instances."""
        if message[0] == 'url':
            try:
                endpoint, values = message[1]
                return ('url', self.my_url_for(endpoint, **values))
            except BuildError:
                return ('url', None)

    def url_for(self, endpoint, use_buddies=True, **values):
        """Build a URL, asking other applications if BuildError occurs locally.

        This implementation is a fork of :func:`~flask.helpers.url_for`, where
        the implementation you see here works around Flask's context-locals to
        provide URL routing specific to ``self``.  Then it implements the
        wsgi_party url_for requests across Flask applications loaded into the
        dispatcher.
        """
        # Some values are popped; keep an original copy for re-requesting URL.
        original_values = copy.deepcopy(values)
        blueprint_name = request.blueprint
        if endpoint[:1] == '.':
            if blueprint_name is not None:
                endpoint = blueprint_name + endpoint
            else:
                endpoint = endpoint[1:]
        external = values.pop('_external', False)
        anchor = values.pop('_anchor', None)
        method = values.pop('_method', None)
        self.inject_url_defaults(endpoint, values)
        url_adapter = self.create_url_adapter(request)
        try:
            rv = url_adapter.build(endpoint, values, method=method,
                                   force_external=external)
        except BuildError:
            # We do not have this URL, ask our buddies.
            if not use_buddies:
                raise
            for buddy in self.buddies:
                rv = self.buddy_url_for(buddy, endpoint, **original_values)
                if rv is not None:
                    return rv
        if anchor is not None:
            rv += '#' + url_quote(anchor)
        return rv

    def my_url_for(self, endpoint, use_buddies=False, **values):
        """Context-locals hurt."""
        with self.test_request_context():
            return self.url_for(endpoint, use_buddies=use_buddies, **values)

    def buddy_url_for(self, buddy, endpoint, **values):
        """Ask a drinking buddy for a URL matching this endpoint."""
        message = 'url', (endpoint, values)
        return buddy.send(self, message)[1]


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


# Demonstrate.
root = FlaskDrunk(__name__)
one = FlaskDrunk(__name__)
two = FlaskDrunk(__name__)

root.debug = True
one.debug = True
two.debug = True

one.config['APPLICATION_ROOT'] = '/one'
two.config['APPLICATION_ROOT'] = '/two'

template = """
<html>
<head>
  <title>Demo: Cross-application URL building in Flask.</title>
</head>
<body>
  <p>You are in the root application.</p>
  <ul>
    <li><a href="%s">Go to application one</a></li>
    <li><a href="%s">Go to application two</a></li>
  </ul>
  <p>Source code is <a href="http://github.com/rduplain/wsgi_party">here</a>.</p>
</body>
</html>
"""

@root.route('/', endpoint='index')
def root_index():
    if not root.buddies:
        return 'I have no friends.'
    return template % (root.url_for('one:index'), root.url_for('two:index'))

@one.route('/', endpoint='one:index')
def one_index():
    url = one.url_for('two:index')
    return 'This is app one. <a href="%s">Go to two.</a>' % url

@two.route('/', endpoint='two:index')
def two_index():
    url = two.url_for('one:index')
    return 'This is app two. <a href="%s">Go to one.</a>' % url

application = MC(root, {
    '/one': one,
    '/two': two,
})


if __name__ == '__main__':
    import os
    from werkzeug.serving import run_simple
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    run_simple('0.0.0.0', port, application, use_reloader=True)
