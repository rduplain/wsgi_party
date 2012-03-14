from flask import Flask
from werkzeug.wsgi import DispatcherMiddleware

application = DispatcherMiddleware(Flask(__name__), {
    '/one': Flask(__name__),
    '/two': Flask(__name__),
})


if __name__ == '__main__':
    from werkzeug.serving import run_simple
    run_simple('localhost', 5000, application, use_reloader=True)
