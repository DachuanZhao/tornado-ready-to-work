#code:utf8
import json,os,sys
import tornado.web
import logging
import hashlib

from typing import Union

logging.basicConfig(level=logging.INFO)

APP_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from models.data_access.sql_model import db_session

class HandlerTool():

    @staticmethod
    def request_body_bytes2str(request_body)->str:
        if isinstance(request_body,bytes):
            request_body = request_body.decode("utf-8")
        if request_body:
            return request_body
        else:
            return json.dumps({})

    @staticmethod
    def set_response(status:int,desc:str,data:dict)->dict:
        return {
            "code":status,
            "desc":desc,
            "data":data}

class EncryptionTool():

    @staticmethod
    def md5(str_temp:str,salt:str=None)->str:
        md5 = hashlib.md5()
        md5.update(str_temp.encode())
        return md5.hexdigest()


class CustomTornadoHandler(tornado.web.RequestHandler):
    """
    自定义tornadoHandler，实现了数据库session的绑定
    """
    def set_default_headers(self):
        """
        解决强求getjson跨越的问题
        """
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with,application/x-www-form-urlencoded")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, PATCH, DELETE, PUT')

    def initialize(self, *args, **kwargs):
        self.db_session = db_session()

    def on_finish(self):
        db_session.remove()

    def write(self,chunk: Union[str, bytes, dict],uid=-1,*args,**kwargs):
        if isinstance(chunk,dict):
            monitor_dict = {"uid":uid,"uri":self.request.uri,"response":chunk}
            logging.info("{}".format(json.dumps(monitor_dict,ensure_ascii=False)))
        return super(CustomTornadoHandler, self).write(chunk,*args, **kwargs)

