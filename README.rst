WSGI Party: partyline middleware for WSGI with good intentions
==============================================================

wsgi_party's goals for Python web developers:

1. Refactor legacy projects one route at a time; graft instead of rewrite.
2. Try new ideas from meetups/conferences in isolation; increase velocity.
3. Integrate multiple web frameworks; use the right tool for the job.

wsgi_party is for WSGI framework developers. See individual frameworks and
extensions for support. The initial intent was to build URLs across independent
applications, but other exchanges are possible if they are supported by all
frameworks in use.

The wsgi_party module provides the WSGIParty middleware which allows all
mounted applications to hook in handlers for cross-application communication
within a single WSGI process. Mount individual applications in a dispatcher,
then wrap the dispatcher with WSGIParty. Applications can then ask each other
for information with simple in-process messages. Messages are synchronous and
namespaced, and must be explicitly supported by Python web frameworks or their
extensions.

BSD licensed. Install with::

    pip install wsgi_party

Read the docs at: http://readthedocs.org/docs/wsgi_party/

This project started as a collaboration between Michael Merickel & Chris
McDonough (Pyramid core developers) and Ron DuPlain (a Flask core developer).
See AUTHORS for a full list of contributors.
