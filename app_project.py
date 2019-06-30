#-*- coding:utf-8 -*-
import tornado.ioloop
import tornado.web
import tornado.options
import tornado.httpserver
import tornado.process
import tornado.netutil
import logging

from config import *

from handlers.handler_hello_world import HelloWorldHandler
from handlers.handler_login import LoginHandler
#from handlers.handler_register import RegisterHandler

def tornado_app():
    return tornado.web.Application([
        (URL_PREFIX + r"/", HelloWorldHandler),
        (URL_PREFIX + r"/login/", LoginHandler),
        #(URL_PREFIX + r"/register/",RegisterHandler),
    ],**setting)

if __name__ == "__main__":
    #读取命令行参数
    tornado.options.parse_command_line()

    tornado_sockets = tornado.netutil.bind_sockets(tornado.options.options.port)
    tornado.process.fork_processes(0)
    tornado_server = tornado.httpserver.HTTPServer(tornado_app(),max_buffer_size=MAX_BUFFER_SIZE)#2G
    tornado_server.add_sockets(tornado_sockets)

    tornado.ioloop.IOLoop.current().start()
