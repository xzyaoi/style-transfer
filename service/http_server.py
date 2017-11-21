from __future__ import print_function
from flask import Flask
from flask import request
import sys
import Queue
import threading
import time
import uuid
from werkzeug.wsgi import LimitedStream
from optparse import OptionParser

import inference

app = Flask(__name__)

input_queue = None
result_dict = {}
cond_var = None

class StreamConsumingMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if 'CONTENT_LENGTH' not in environ:
            environ['CONTENT_LENGTH'] = 0
        stream = LimitedStream(environ['wsgi.input'],
                               int(environ['CONTENT_LENGTH'] or 0))
        environ['wsgi.input'] = stream
        app_iter = self.app(environ, start_response)
        try:
            stream.exhaust()
            for event in app_iter:
                yield event
        finally:
            if hasattr(app_iter, 'close'):
                app_iter.close()

def check_auth(username, password):
    return True
    # return username == 'song' and password == 'pass'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return ('Could not verify your access level for that URL.\n', 401, '')

def do_post(data):
    return 'Does not support POST now\n'

def do_get(data):
    global input_queue
    global result_dict
    global cond_var
 
    if input_queue.full():
        return ('Server is busy', 501, '')

    key = uuid.uuid4()

    start = time.time()
    try: 
        input_queue.put_nowait([key, data])
    except Queue.Full:
        return ('Server is busy', 501, '')
    except:
        return ('Internal error', 500, '')

    cond_var.acquire()
    while not (key in result_dict):
        cond_var.wait()

    #set None to ensure pop will not through exception
    result = result_dict.pop(key, None)
    cond_var.release()

    print ('Time cost {0}'.format(time.time() - start))
    return result

def start_service(config):
    global input_queue
    global result_dict
    global cond_var
 
    max_bufsize = 20
    input_queue = Queue.Queue(maxsize=max_bufsize)
    cond_var = threading.Condition()

    inference.start_service(input_queue, result_dict, cond_var, config)

@app.route("/", methods=['GET'])
def hello():
    return 'hello_world!'

@app.route("/initialized", methods=['GET'])
def do_initialized():
    if inference.initialized == True:
        return 'YES'
    else:
        return 'NO'

@app.route("/service", methods=['POST'])
def do_service():
    return do_get(request.stream)

@app.route("/udl", methods=['GET', 'POST'])
def do_udl():
    if request.method == 'GET':
        return do_get(request.stream)

    if request.method == 'POST':
        return do_get(request.stream)

def http_server_run(config, port):
    start_service(config)
    app.wsgi_app = StreamConsumingMiddleware(app.wsgi_app)
    app.run(host='0.0.0.0', port=port, threaded=True)
