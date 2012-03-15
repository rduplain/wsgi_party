from flask import Flask, abort, request
from wsgi_party import WSGIParty


class PartylineFlask(Flask):
    def __init__(self, import_name, *args, **kwargs):
        super(PartylineFlask, self).__init__(import_name, *args, **kwargs)
        self.add_url_rule(WSGIParty.invite_path, endpoint='partyline',
                          view_func=self.join_party)
        self.partyline = None
        self.connected = False

    def join_party(self, request=request):
        # Bootstrap, turn the view function into a 404 after registering.
        if self.connected:
            # This route does not exist at the HTTP level.
            abort(404)
        self.partyline = request.environ.get(WSGIParty.partyline_key)
        self.partyline.connect('ping', lambda x: 'pong')
        self.connected = True
        return 'ok'


# Demonstrate.
root = PartylineFlask(__name__)
one = PartylineFlask(__name__)
two = PartylineFlask(__name__)

root.debug = True
one.debug = True
two.debug = True

one.config['APPLICATION_ROOT'] = '/one'
two.config['APPLICATION_ROOT'] = '/two'

@root.route('/', endpoint='index')
def root_index():
    if root.partyline is None:
        return 'I have no friends.'
    # Note: This is a synchronous call.
    pongs = root.partyline.send_all('ping', None)
    # Simply show responses.
    return repr(list(pongs))

application = WSGIParty(root, {
    '/one': one,
    '/two': two,
})


if __name__ == '__main__':
    import os
    from werkzeug.serving import run_simple
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    run_simple('0.0.0.0', port, application, use_reloader=True)
