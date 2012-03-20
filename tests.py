import unittest


class TestPartylineOperator(unittest.TestCase):
    def _makeOne(self, partyline):
        from wsgi_party import PartylineOperator
        return PartylineOperator(partyline)

    def test_connect(self):
        partyline = DummyPartyline(connect_response='123')
        inst = self._makeOne(partyline)
        result = inst.connect('name', 'handler')
        self.assertEqual(partyline.connections, [('name', 'handler')])
        self.assertEqual(inst.handlers, set(['handler']))
        self.assertEqual(result, '123')

    def test_ask_around(self):
        partyline = DummyPartyline(ask_response=['abc'])
        inst = self._makeOne(partyline)
        result = inst.ask_around('name', 'payload')
        self.assertEqual(partyline.asked, [('name', 'payload', inst)])
        self.assertEqual(result, ['abc'])


class TestWSGIParty(unittest.TestCase):
    def _makeOne(self, app, invites=(), ignore_missing_services=False):
        from wsgi_party import WSGIParty
        return WSGIParty(app, invites, ignore_missing_services)

    def test_ctor_calls_send_invitations(self):
        app = DummyWSGIApp()
        self._makeOne(app, ('/__invite__', '/another/__invite__'))
        self.assertEqual(len(app.environs), 2)

    def test___call__(self):
        app = DummyWSGIApp()
        inst = self._makeOne(app)
        environ = {}
        def start_response(status, headers=()):
            environ['start_response_called'] = True
        inst(environ, start_response)
        self.assertEqual(app.environs, [environ])
        self.assertEqual(environ['start_response_called'], True)

    def test_send_invitations(self):
        app = DummyWSGIApp()
        inst = self._makeOne(app)
        inst.send_invitations(('/__invite__', '/another/__invite__'))
        self.assertEqual(len(app.environs), 2)
        environ1, environ2 = app.environs
        self.assertEqual(environ1['PATH_INFO'], '/__invite__')
        self.assertEqual(environ1[inst.partyline_key].__class__,
                         inst.operator_class)
        self.assertEqual(environ2['PATH_INFO'], '/another/__invite__')
        self.assertEqual(environ2[inst.partyline_key].__class__,
                         inst.operator_class)

    def test_connect_to_nonexisting(self):
        app = DummyWSGIApp()
        inst = self._makeOne(app)
        inst.connect('service_name', 'handler')
        self.assertEqual(inst.handlers['service_name'], ['handler'])

    def test_connect_to_existing(self):
        app = DummyWSGIApp()
        inst = self._makeOne(app)
        inst.handlers['service_name'] = ['abc']
        inst.connect('service_name', 'handler')
        self.assertEqual(inst.handlers['service_name'], ['abc', 'handler'])

    def test_ask_around_other_operator(self):
        operator = DummyOperator()
        app = DummyWSGIApp()
        inst = self._makeOne(app)
        L = []
        def handler1(payload):
            L.append(payload)
            return 'result'
        def handler2(payload):
            L.append(payload)
            return 'result2'
        inst.handlers['service_name'] = [handler1, handler2]
        result = inst.ask_around('service_name', 'payload', operator=operator)
        self.assertEqual(L, ['payload', 'payload'])
        self.assertEqual(result, ['result', 'result2'])

    def test_ask_around_other_operator_handler_raises_HighAndDry(self):
        from wsgi_party import HighAndDry
        operator = DummyOperator()
        app = DummyWSGIApp()
        inst = self._makeOne(app)
        L = []
        def handler1(payload):
            L.append(payload)
            return 'result'
        def handler2(payload):
            L.append(payload)
            raise HighAndDry()
        inst.handlers['service_name'] = [handler1, handler2]
        result = inst.ask_around('service_name', 'payload', operator=operator)
        self.assertEqual(L, ['payload', 'payload'])
        self.assertEqual(result, ['result'])

    def test_ask_around_same_operator(self):
        app = DummyWSGIApp()
        inst = self._makeOne(app)
        L = []
        def handler1(payload):
            L.append(payload)
            return 'result'
        def handler2(payload):
            L.append(payload)
            return 'result2'
        operator = DummyOperator((handler1, handler2))
        inst.handlers['service_name'] = [handler1, handler2]
        result = inst.ask_around('service_name', 'payload', operator=operator)
        self.assertEqual(L, [])
        self.assertEqual(result, [])

    def test_ask_around_no_operator(self):
        from wsgi_party import HighAndDry
        app = DummyWSGIApp()
        inst = self._makeOne(app)
        L = []
        def handler1(payload):
            L.append(payload)
            return 'result'
        def handler2(payload):
            L.append(payload)
            raise HighAndDry()
        inst.handlers['service_name'] = [handler1, handler2]
        result = inst.ask_around('service_name', 'payload')
        self.assertEqual(L, ['payload', 'payload'])
        self.assertEqual(result, ['result'])

    def test_ask_around_no_handler(self):
        from wsgi_party import NoSuchServiceName
        app = DummyWSGIApp()
        inst = self._makeOne(app)
        self.assertRaises(NoSuchServiceName, inst.ask_around, 'unlucky', None)

    def test_ask_around_no_handler_ignored(self):
        from wsgi_party import NoSuchServiceName
        app = DummyWSGIApp()
        inst = self._makeOne(app, ignore_missing_services=True)
        try:
            self.assertEqual(inst.ask_around('who_cares', None), [])
        except NoSuchServiceName:
            self.fail('NoSuchServiceName was not suppressed as requested.')


class DummyOperator(object):
    def __init__(self, handlers=()):
        self.handlers = handlers


class DummyPartyline(object):
    def __init__(self, connect_response=None, ask_response=None):
        self.connections = []
        self.asked = []
        self.ask_response = ask_response
        self.connect_response = connect_response

    def connect(self, name, handler):
        self.connections.append((name, handler))
        return self.connect_response

    def ask_around(self, service_name, payload, operator=None):
        self.asked.append((service_name, payload, operator))
        return self.ask_response


class DummyWSGIApp(object):
    def __init__(self, response=()):
        self.response = response
        self.environs = []

    def __call__(self, environ, start_response):
        self.environs.append(environ)
        start_response('200 OK', [])
        return self.response
