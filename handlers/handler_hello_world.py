# coding=utf-8
import tornado.web
import sys,os
import time
import json
import logging
from tornado.concurrent import run_on_executor
import concurrent.futures

APP_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(APP_DIR)
from libs.common_function import HandlerTool

class HelloWorldHandler(tornado.web.RequestHandler):

    executor = concurrent.futures.ThreadPoolExecutor()

    def set_default_headers(self):
        """
        解决强求getjson跨越的问题
        """
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with,application/x-www-form-urlencoded")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    @run_on_executor
    def post(self):
        """

        """
        request_body = HandlerTool.request_body_bytes2str(self.request.body)
        try:
            request_body_dict = json.loads(request_body)
            self.write(HandlerTool.set_response(0,"",{"hi":"Hello, world","request_body":request_body_dict,"test":test}))
        except Exception as error:
            logging.error(str(error),exc_info = True)
            self.write(HandlerTool.set_response(-1,str(error),{}))

    @run_on_executor
    def put(self):
        request_body = HandlerTool.request_body_bytes2str(self.request.body)
        try:
            request_body_dict = json.loads(request_body)
            self.write(HandlerTool.set_response(0,"",{"hi":"Hello, world","request_body":request_body_dict}))
        except Exception as error:
            logging.error(str(error),exc_info = True)
            self.write(HandlerTool.set_response(-1,str(error),{}))

    @run_on_executor
    def patch(self):
        request_body = HandlerTool.request_body_bytes2str(self.request.body)
        try:
            request_body_dict = json.loads(request_body)
            self.write(HandlerTool.set_response(0,"",{"hi":"Hello, world","request_body":request_body_dict}))
        except Exception as error:
            logging.error(str(error),exc_info = True)
            self.write(HandlerTool.set_response(-1,str(error),{}))

    @run_on_executor
    def delete(self):
        try:
            username = self.get_argument('username', 'you can guess it')
            password = self.get_argument('password', 'you can guess it')
            self.write(HandlerTool.set_response(0,"",{"hi":"Hello, world","request_body":{"username":username,"password":password}}))
        except Exception as error:
            logging.error(str(error),exc_info = True)
            self.write(HandlerTool.set_response(-1,str(error),{}))

    @run_on_executor
    def get(self):
        try:
            username = self.get_argument('username', 'you can guess it')
            password = self.get_argument('password', 'you can guess it')
            self.write(HandlerTool.set_response(0,"",{"hi":"Hello, world","request_body":{"username":username,"password":password}}))
        except Exception as error:
            logging.error(str(error),exc_info = True)
            self.write(HandlerTool.set_response(-1,str(error),{}))
