#-*- coding:utf-8 -*-
import tornado.ioloop
import tornado.web
import tornado.options
import tornado.httpserver
import tornado.process
import tornado.netutil
import logging

from config import *
from models.data_access.sql_model import DBSession
#from models.data_access.neo4j_model import NEO4J_DRIVER

from handlers.common.hello_world import HelloWorldHandler
#from handlers.common.login import LoginHandler
#from handlers.common.register import RegisterHandler

def tornado_app():
    app = tornado.web.Application([
        (URL_PREFIX + r"/", HelloWorldHandler),
        #(URL_PREFIX + r"/register",RegisterHandler),
    ],**setting)
    app.DBSession = DBSession
    #app.NEO4J_DRIVER = NEO4J_DRIVER
    return app

if __name__ == "__main__":
    #读取命令行参数
    tornado.options.parse_command_line()

    #多进程启动
    #tornado_sockets = tornado.netutil.bind_sockets(tornado.options.options.port)
    ##tornado.process.fork_processes(0)
    #tornado_server = tornado.httpserver.HTTPServer(tornado_app(),max_buffer_size=MAX_BUFFER_SIZE)#2G
    #tornado_server.add_sockets(tornado_sockets)

    #单进程启动
    tornado_server = tornado.httpserver.HTTPServer(tornado_app(),max_buffer_size=MAX_BUFFER_SIZE,xheaders = True)#2G
    tornado_server.listen(tornado.options.options.port)
    logging.info("tornado即将启动，端口为{}".format(tornado.options.options.port))
    tornado.ioloop.IOLoop.current().start()