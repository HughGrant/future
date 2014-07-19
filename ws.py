from wsgiref.simple_server import make_server
from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler
from ws4py.server.wsgiutils import WebSocketWSGIApplication
from ws4py.websocket import WebSocket
from extract import Ali

class YASON(WebSocket):
    browser = None
    def received_message(self, message):
        action = str(message)
        print action
        if action.startswith('login'):
            info = action.split('<>')
            # use email to create a profile dir
            self.browser = Ali(info[1])
            status = self.browser.login(info[1], info[2])
            if status:
                self.send('login success')
        # up stands for upload product
        elif action.startswith('up ') and self.browser:
            product_id = action.replace('up ', '', 1)
            if product_id:
                self.browser.upload_product(product_id)
        # ck stands for collect keywords
        elif action.startswith('ck ') and self.browser:
            key_words = action.replace('ck ', '', 1)
            counter = self.browser.collect_key_words(key_words)
            self.send('keywords collected: %s' % counter)
        # cp stands for copy product
        elif action.startswith('cp<>') and self.browser:
            p = action.split('<>')
            re = self.browser.copy_to_new_product(p[1], p[2])
            if re:
                self.send('upload success')
        # id stands for get product alibaba id
        elif action.startswith('id<>') and self.browser:
            p = action.split('<>')
            iid = self.browser.get_product_id(p[1], p[2])
            if iid:
                self.send('iid:%s' % iid)
        # cn stands for collect names
        # elif action.startswith('cn<>') and self.browser:
        #     p = action.split('<>')
        #     count = self.browser.get_various_product_name(p[1])
        #     self.send('Collected %s names for %s' % (count, p[1]))
        elif action == 'get auth' and self.browser:
            self.browser.get_auth_code()
        elif action.isdigit() and self.browser:
            self.browser.input_auth_code(auth_code)
        elif action in ['quit', 'q'] and self.browser:
            self.browser.quit()

    def closed(self, code, reason=None):
        print 'code:', code
        print 'reason:', reason

    def opened(self):
        print 'web socket opened'


server = make_server('', 9000, server_class=WSGIServer,
                     handler_class=WebSocketWSGIRequestHandler,
                     app=WebSocketWSGIApplication(handler_cls=YASON))
server.initialize_websockets_manager()
server.serve_forever()
