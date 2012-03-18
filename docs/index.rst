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

:ref:`genindex`
