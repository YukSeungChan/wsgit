#!/usr/bin/python
import threading
import bson
from SocketServer import ThreadingMixIn, TCPServer, BaseRequestHandler

from wsgi import WSGIHandler, Environ

class Server(ThreadingMixIn, TCPServer):
    def __init__(self, addr, handler, app):
        self.app = app
        self.connected_handlers = []
        TCPServer.__init__(self, addr, handler)

    @classmethod
    def run_server(cls, addr, app):
        bson.patch_socket()
        server = cls(addr, WSGITRequestHandler, app)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        return server, thread

class WSGITRequestHandler(BaseRequestHandler):
    def setup(self):
        self.conn = self.request
        self.server.connected_handlers.append(self)

    def handle(self):
        while True:
            try:
                obj = self.conn.recvobj()
            except Exception:
                logger.debug('Bad Request. Not bson protocol.')
            if obj == None:
                break
            environ = Environ(obj)
            wsgi_handler = WSGIHandler()
            obj = wsgi_handler.call_application(self.server.app, 
                                                environ.get_dict())
            self.conn.send(obj)


    def finish(self):
        self.conn.close()

if __name__ == '__main__':
    import sys, os, time
    sys.path.append(os.getcwd())
    if len(sys.argv) != 3:
        print 'Usage : %s BIND_IP:PORT MODULENAME.APPLICATION_NAME'%sys.argv[0]
        sys.exit(1)
    path = sys.argv[2].split('.')
    name = path[-1]
    module = __import__('.'.join(path[:-1]), fromlist=[name])
    ip,port = sys.argv[1].split(':')
    try:
        server, thread= Server.run_server((ip,int(port)), getattr(module, name))
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.shutdown()