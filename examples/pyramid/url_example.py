# pip install pyramid

from pyramid.config import Configurator

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

def view_base(request):
    party = get_party(request)
    response = request.response

    urls = party.send_all('url', {'name': 'home'})
    if not urls:
        body = 'I have no friends. :-('
    else:
        body = ''
        for url in urls:
            body += 'Please visit <a href="{0}">{0}</a><br/>'.format(url)
    response.body = body
    return response

def view_one(request):
    party = get_party(request)
    response = request.response

    urls = party.send_all('url', {'name': 'home'})
    if not urls:
        body = 'I have no friends. :-('
    else:
        url = list(urls)[0]
        body = 'Please visit <a href="{0}">App Two</a>'.format(url)
    response.body = BODY % {'app': 'One', 'body': body}
    return response

def view_two(request):
    party = get_party(request)
    response = request.response

    urls = party.send_all('url', {'name': 'home'})
    if not urls:
        body = 'I have no friends. :-('
    else:
        url = list(urls)[0]
        body = 'Please visit <a href="{0}">App One</a>'.format(url)
    response.body = BODY % {'app': 'Two', 'body': body}
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

def main_base(global_conf, **settings):
    config = Configurator(settings=settings)
    config.include('pyramid_party')
    config.add_view(view_base)
    return config.make_wsgi_app()

def main_one(global_conf, **settings):
    config = Configurator(settings=settings)
    config.include('pyramid_party')
    config.add_subscriber(party_invite, PartylineInvitation)
    config.add_route('home', '')
    config.add_view(view_one, route_name='home')

    return config.make_wsgi_app()

def main_two(global_conf, **settings):
    config = Configurator(settings=settings)
    config.include('pyramid_party')
    config.add_subscriber(party_invite, PartylineInvitation)
    config.add_route('home', '')
    config.add_view(view_two, route_name='home')

    return config.make_wsgi_app()

if __name__ == '__main__':
    import os
    from werkzeug.serving import run_simple
    from wsgi_party import WSGIParty

    base = main_base({})
    one = main_one({})
    two = main_two({})
    party = WSGIParty(base, mounts={
        '/one': one,
        '/two': two,
    })

    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    run_simple('0.0.0.0', port, party, use_reloader=True)
