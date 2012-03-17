================================================================
 WSGI Party: partyline middleware for WSGI with good intentions
================================================================

This is a collaboration between Ron DuPlain (a Flask core developer) and Chris
McDonough & Michael Merickel (Pyramid core developers).

Primary use cases:

1. I have a legacy WSGI application, and I would like to refactor it one route
   at a time to a fresh clean project which makes hacking fun again.  Avoid the
   great rewrite; graft applications instead.
2. I just attended a Python meetup or conference where I was introduced to
   advanced patterns, and would like to try new techniques in isolation from
   the rest of my project.
3. I enjoy using multiple frameworks in my project, and would like to integrate
   them at WSGI level without painful/awkward URL-building across applications.

Non-opinionated frameworks (such as Pyramid or Flask) encourage you to make
explicit design decisions, and sometimes you are stuck with design decisions
you made a long time ago.  Instead of rewriting everything all of the time, you
can mix applications at the WSGI level and put emergent insights into
production faster.  To date, the primary obstacle is building URLs across
applications for links and redirects.  Yes, you can come up with various URL
rewrite hacks, but this requires shared ownership of an application's routes,
and I'd prefer to let the application maintain its own routes (and after some
evaluation, I think you'll agree).

This project investigates message-passing within a WSGI process, with intent to
build URLs between applications, but potentially allows for more.

Connecting applications, an observation.  WSGI allows for arbitrary
middleware.  If we connect multiple applications with a dispatcher middleware,
we have no guarantee that the Python objects implementing the applications
exposing any API beyond the core WSGI spec.

The hack: every participating WSGI application can provide a route which a
middleware can use to register the application into a message-passing scheme.
Essentially, we need to bootstrap the middleware to discover and register
without any bolt-ons to the WSGI spec and while allowing arbitrary middleware
to be provided.  If every WSGI application registers a special route or fails
gracefully (404), the middleware can call this route on every mounted
application to bootstrap (credit to Chris McDonough for this technique).

Development philosophy: routes are typically a name or endpoint encoded as a
string and a collection of view function arguments.  We can normalize to one
routing framework, and have participating web frameworks build adapters for
it.  The endpoint names are up to the developer, and in my opinion, should not
be standardized.  The developer should know the endpoint in each application in
the WSGI process, and use that information when requesting URLs to be built.
