from tornado import web, websocket, ioloop
from tornado.options import define, options
from extract import Ali

define("port", default=9000, help="run on the given port", type=int)

class StatusHandler(websocket.WebSocketHandler):
    browser = None
    def on_message(self, message):
        action = str(message)
        print action
        if action.startswith('login') and not self.browser:
            info = action.split('<>')
            # use email to create a profile dir
            self.browser = Ali(info[1])
            status = self.browser.login(info[1], info[2])
            if status:
                self.write_message('login success')
        # up stands for upload product
        elif action.startswith('up<>') and self.browser:
            product_id = action.replace('up<>', '', 1)
            self.browser.upload_product(product_id)
        # ck stands for collect keywords
        elif action.startswith('ck<>') and self.browser:
            key_words = action.replace('ck<>', '', 1)
            counter = self.browser.collect_key_words(key_words)
            self.write_message('keywords collected: %s' % counter)
        # cp stands for copy product
        elif action.startswith('cp<>') and self.browser:
            pid = action.replace('cp<>', '', 1)
            re = self.browser.copy_to_new_product(pid)
            if re:
                self.write_message('upload success')
        # gai stands for get alibaba id
        elif action.startswith('gai<>') and self.browser:
            pid = action.replace('gai<>', '', 1)
            iid = self.browser.get_product_id(pid)
            if iid:
                self.write_message('aid:%s' % iid)
        # elif action == 'get auth' and self.browser:
        #     self.browser.get_auth_code()
        # elif action.isdigit() and self.browser:
        #     self.browser.input_auth_code(auth_code)
        elif action == 'quit' and self.browser:
            self.browser.quit()
            self.browser = None

    def open(self):
        print 'websocket connected'

    def on_close(self):
        print 'wesocket colsed'


    def check_origin(self, origin):
        return True
        
if __name__ == '__main__':
    options.parse_command_line()
    app = web.Application(handlers=[(r'/', StatusHandler)])
    app.listen(options.port)
    ioloop.IOLoop.instance().start()
