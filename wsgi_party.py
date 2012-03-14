from flask import Flask, request
from werkzeug.wsgi import DispatcherMiddleware
from werkzeug.test import create_environ, run_wsgi_app


class FlaskDrunk(Flask):
    def __init__(self, import_name, *args, **kwargs):
        super(FlaskDrunk, self).__init__(import_name, *args, **kwargs)
        self.add_url_rule('/invite/', endpoint='party', view_func=self.party)
        self.dispatcher = None
        self.drunks = []

    def party(self):
        self.dispatcher = request.environ.get('mc_dispatcher')
        self.dispatcher.attendees.append(self)
        self.drunks = self.dispatcher.attendees
        return repr(self)

    @property
    def buddies(self):
        return [buddy for buddy in self.drunks if buddy is not self]

    def receive(self, sender, message):
        if message == ('ping', None):
            return ('pong', None)


class MC(DispatcherMiddleware):
    def __init__(self, app, mounts=None, base_url=None):
        super(MC, self).__init__(app, mounts=mounts)
        self.base_url = None
        self.attendees = []
        environ = create_environ(path='/invite/', base_url=self.base_url)
        environ['mc_dispatcher'] = self
        for application in [app] + mounts.values():
            run_wsgi_app(application, environ)


# Demonstrate.
root = FlaskDrunk(__name__)
one = FlaskDrunk(__name__)
two = FlaskDrunk(__name__)

root.debug = True
one.debug = True
two.debug = True

@root.route('/', endpoint='index')
def root_index():
    if not root.buddies:
        return 'I have no friends.'
    buddy = root.buddies[0]
    received = buddy.receive(root, ('ping', None))
    return 'received %r from %r' % (received, buddy)

application = MC(root, {
    '/one': one,
    '/two': two,
})


if __name__ == '__main__':
    from werkzeug.serving import run_simple
    run_simple('localhost', 5000, application, use_reloader=True)
