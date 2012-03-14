import copy

from flask import Flask, abort, request
from werkzeug.routing import BuildError
from werkzeug.test import create_environ, run_wsgi_app
from werkzeug.urls import url_quote
from werkzeug.wsgi import DispatcherMiddleware


class DrinkingBuddy(object):
    def party(self, request):
        if hasattr(self, 'on_party'):
            self.on_party(request.environ)
        self.dispatcher = request.environ.get('mc_dispatcher')
        self.dispatcher.attendees.append(self)
        self.partiers = self.dispatcher.attendees
        return repr(self)

    @property
    def buddies(self):
        return [buddy for buddy in self.partiers if buddy is not self]

    def receive(self, sender, message):
        if message == ('ping', None):
            return ('pong', None)
        if hasattr(self, 'on_receive'):
            return self.on_receive(sender, message)
        return (message[0], None)

    def send(self, sender, message):
        if hasattr(self, 'on_send'):
            self.on_send(sender, message)
        return self.receive(sender, message)


class FlaskDrunk(Flask, DrinkingBuddy):
    def __init__(self, import_name, *args, **kwargs):
        super(FlaskDrunk, self).__init__(import_name, *args, **kwargs)
        self.pregame = True
        self.add_url_rule('/invite/', endpoint='party', view_func=self.join_party)
        self.dispatcher = None
        self.partiers = []

    def on_party(self, environ):
        if not self.pregame:
            # This route does not exist at the HTTP level.
            abort(404)
        self.pregame = False

    def join_party(self, request=request):
        return self.party(request)

    def on_receive(self, sender, message):
        if message[0] == 'url':
            try:
                endpoint, values = message[1]
                return ('url', self.my_url_for(endpoint, **values))
            except BuildError:
                return ('url', None)

    def url_for(self, endpoint, use_buddies=True, **values):
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
        message = 'url', (endpoint, values)
        return buddy.receive(self, message)[1]


class MC(DispatcherMiddleware):
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
  <p>You are in the root application.
  <ul>
    <li><a href="%s">Go to application one</a></li>
    <li><a href="%s">Go to application two</a></li>
  </ul>
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
    from werkzeug.serving import run_simple
    run_simple('localhost', 5000, application, use_reloader=True)
