.. _overview:

WSGI Party: partyline middleware for WSGI
=========================================

wsgi_party provides a partyline middleware for Python WSGI applications, which
lets multiple applications communication which each other within the same WSGI
process.  Use cases:

1. Refactor legacy projects one route at a time; graft instead of rewrite.
2. Try new ideas from meetups/conferences in isolation; increase velocity.
3. Integrate multiple web frameworks; use the right tool for the job.

This project targets developers familiar with WSGI, and Python web framework
developers who would like to support interoperability between WSGI
applications.

Get the source: http://github.com/rduplain/wsgi_party

BSD licensed. Install with::

    pip install wsgi_party


.. _quickstart-users:

Quickstart
----------

wsgi_party intends for Python web frameworks to provide an extension or plugin
so that applications built in those frameworks can join the partyline with a
simple wrapper.  Create the extension or use the partyline directly; see the
:ref:`quickstart-diy`.


.. _quickstart-diy:

Quickstart for DIY Developers
-----------------------------

Mount multiple applications into a WSGI dispatcher (the example here uses
:class:`~werkzeug.wsgi.DispatcherMiddleware`); wrap it with WSGIParty::

    # pip install wsgi_party werkzeug
    # Using werkzeug's DispatcherMiddleware as example; any dispatcher will do.
    from werkzeug.wsgi import DispatcherMiddleware
    from wsgi_party import WSGIParty

    # Import independent WSGI applications.
    from my_project import app0, app1, app2

    # Mount applications into the dispatcher, producing standalone application.
    dispatcher = DispatcherMiddleware(app0, {
        '/path1': app1,
        '/path2': app2,
    })

    # Collect routes which applications will use to join the partyline.
    invites=('/__invite__/', '/path1/__invite__/', '/path2/__invite__/')

    # Wrap the dispatcher with the partyline middleware. Serve this over HTTP.
    application = WSGIParty(dispatcher, invites=invites)

:class:`wsgi_party.WSGIParty` will invite each application to join the
partyline during initialization by sending a request to each path given in
``invites``.  This is a special bootstrapping request which includes a
partyline hook in the WSGI environ at the key ``partyline``, an instance of
:class:`wsgi_party.PartylineOperator` which the application can keep around to
ask for information from the partyline.

Configure a route on each application to hook into the partyline::

    # ... inside the route handler, environ is passed in on WSGI request.
    partyline = environ.get('partyline')

    # Connect some handlers.
    partyline.connect('ping', lambda x: 'pong')

By connecting a handler -- here a 'ping' handler, each of the other
participating applications in the partyline can get information from the
others, through the ``ask_around`` method::

    partyline.ask_around('ping', None)

Handlers connected by :meth:`wsgi_party.PartlineOperator.connect` should either
return a value or raise :class:`wsgi_party.HighAndDry` if they should be
skipped.  See :ref:`building_handlers` and :ref:`handler_limitations`.


.. _building_handlers:

Building Handlers
-----------------

A handler connected to WSGIParty is just a callable which accepts a single
argument, which could be a single value or a tuple-packed set of arguments
(that's up to the handler).  If a handler does not have a meaningful result, it
should raise :class:`wsgi_party.HighAndDry`. To illustrate::

    from __future__ import print_function
    from wsgi_party import WSGIParty, HighAndDry

    def even(number):
        "A trivial handler, returns number if it is even."
        if number % 2 == 0:
            return number
        raise HighAndDry()

    def odd(number):
        "A trivial handler, returns number if it is odd."
        if number % 2 == 1:
            return number
        raise HighAndDry()

    def multiple_of_four(number):
        "A trivial handler, returns number if it is a multiple of 4."
        if number % 4 == 0:
            return number
        raise HighAndDry()

    def application(environ, start_response):
        "The simplest WSGI application, to initialize a WSGIParty instance."
        start_response('200 OK', [('Content-Type', 'text/plain')])
        yield 'Hello, world!\n'

    # Connect the handlers defined above.
    partyline = WSGIParty(application)
    partyline.connect('number', even)
    partyline.connect('number', odd)
    partyline.connect('number', multiple_of_four)

    if __name__ == '__main__':
        print(repr(partyline.ask_around('number', 1))) # [1]
        print(repr(partyline.ask_around('number', 2))) # [2]
        print(repr(partyline.ask_around('number', 4))) # [4, 4]

Running this example produces the lists ``[1]``, ``[2]``, and ``[4, 4]``.  This
illustration works outside of WSGI just to show wsgi_party's behavior with
handlers; don't use WSGIParty outside WSGI.


.. _handler_limitations:

Handler Limitations
-------------------

Handlers on the partyline are connected in the same WSGI process and are called
synchronously one at a time on :meth:`wsgi_party.PartylineOperator.ask_around`.
The partyline simply connects handlers; it's up to the handlers to decide on
message namespaces and what information to pass.

Calling :meth:`wsgi_party.PartylineOperator.ask_around` returns a list of all
available handler responses; the partyline itself makes no guarantee on order.
Note that each web framework has its own limitations on how to work with
requests and request contexts.  Some frameworks require a request context to
perform certain actions; keep the request context from the invitation around
for handlers which require a request context.

wsgi_party's original intent is to build URLs across applications, but supports
a general-purpose handler scheme for handlers which can work across all
participating frameworks.


.. _partyline_design:

Partyline Design
----------------

Dispatchers allow for mounting multiple applications in WSGI, but do not
provide a means for mounted applications to exchange details with each other
directly.  Note that WSGI allows for arbitrary middleware.  Connecting multiple
applications with a dispatcher middleware gives no guarantee that the mounted
Python objects expose any API beyond the core WSGI spec, as they could be
wrapped.

The key: instead of requiring middleware participation or changing the WSGI
spec, every partyline WSGI application can provide a route which a middleware
can use to register the application into a message-passing scheme. If every
WSGI application registers a special route or fails gracefully (404), a
unifying middleware can call this route on every mounted application to
bootstrap a partyline.

In the current design, this route is only sensible at the WSGI level, not at
HTTP, since all applications bind to each other within a single process.
Invitation handlers should respond with a 404 not-found response for all
requests after the first, as :class:`wsgi_party.WSGIParty` only calls this
handler once on initialization.


.. _partyline_philosophy:

Partyline Philosophy
--------------------

Non-opinionated frameworks (such as Pyramid or Flask) encourage explicit design
decisions, and sometimes developers are stuck with design decisions made a long
time ago.  Instead of rewriting everything all of the time, a partyline can mix
applications at the WSGI level and help developers put emergent insights into
production faster.  To date, the primary obstacle is building URLs across
applications for links and redirects.  Various URL rewrite tricks can work
around this obstacle, but that puts an application's routes into shared
ownership.  A partyline let's an application maintain its own routes.

For building URLs across applications, routes are typically a name or endpoint
encoded as a string and a collection of view function arguments.  Participating
frameworks can normalize to one routing framework, then build adapters for it.
The endpoint names are up to the application developer.  The developer should
know the endpoint in each application in the WSGI process, and use that
information when requesting URLs to be built.  The partyline just provides the
connection to make this possible.


.. _api:

API
===

.. module:: wsgi_party

.. autoclass:: WSGIParty
   :members:
   :inherited-members:

.. autoclass:: PartylineOperator
   :members:
   :inherited-members:

.. autoclass:: PartylineException
   :members:
   :inherited-members:

.. autoclass:: HighAndDry
   :members:
   :inherited-members:

.. autoclass:: NoSuchServiceName
   :members:
   :inherited-members:

:ref:`genindex`
