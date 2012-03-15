from flask import Flask, request
from wsgi_party import WSGIParty, PartylineConnector


class PartylineFlask(Flask, PartylineConnector):
    def __init__(self, import_name, *args, **kwargs):
        super(PartylineFlask, self).__init__(import_name, *args, **kwargs)
        self.add_url_rule(WSGIParty.invite_path, endpoint='partyline',
                          view_func=self.join_party_wrapper)

    def join_party_wrapper(self, request=request):
        """A simple wrapper to support Flask's request pattern."""
        return self.join_party(request)


# Demonstrate.
root = PartylineFlask(__name__)
one = PartylineFlask(__name__)
two = PartylineFlask(__name__)

root.debug = True
one.debug = True
two.debug = True

one.config['APPLICATION_ROOT'] = '/one'
two.config['APPLICATION_ROOT'] = '/two'

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
