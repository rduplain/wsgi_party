# pip install pyramid>1.3b3
#
# A bug was fixed in pyramid's 2b41345e815c2e584fd51bbe534ba35e222f3b80 commit.

from pyramid.config import Configurator
from pyramid.wsgi import wsgiapp2

from pyramid_party import (
    get_party,
    PartylineInvitation,
)

def party_invite(event):
    request = event.request
    party = event.party
    def _gen_url(payload):
        name = payload['name']
        kwargs = payload.get('kwargs', {})
        query = payload.get('query', ())
        return request.route_path(name, _query=query, **kwargs)
    party.connect('url', _gen_url)

def view(request):
    party = get_party(request)
    response = request.response

    urls = party.ask_around('url', {'name': 'home'})
    if not urls:
        body = 'I have no friends. :-('
    else:
        body = ''
        for url in urls:
            body += 'Please visit <a href="{0}">{0}</a><br/>'.format(url)
    response.body = body
    return response

BODY = """
<html>
    <head>
        <title>Welcome to Application %(app)s</title>
    </head>
    <body>
        %(body)s
    </body>
</html>
"""

def appinclude(config):
    config.include('pyramid_party')
    config.add_subscriber(party_invite, PartylineInvitation)
    config.add_route('home', '')
    config.add_view(view, route_name='home')

def app():
    config = Configurator()
    config.include(appinclude)
    return config.make_wsgi_app()

if __name__ == '__main__':
    import os
    from werkzeug.serving import run_simple
    from wsgi_party import WSGIParty
    config = Configurator()
    config.include(appinclude)
    config.add_route('one', '/one*subpath')
    config.add_route('two', '/two*subpath')
    config.add_view(wsgiapp2(app()), route_name='one')
    config.add_view(wsgiapp2(app()), route_name='two')
    base = config.make_wsgi_app()
    party = WSGIParty(
        base, ('/__invite__', '/one/__invite__', '/two/__invite__')
        )
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    run_simple('0.0.0.0', port, party, use_reloader=True)
