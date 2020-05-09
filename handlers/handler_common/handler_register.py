#!/usr/bin/env python
# coding=utf-8
import logging
import tornado.web,tornado.options
import json
import os,sys
import uuid
import redis
import configparser
import random


APP_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
config_ini = configparser.ConfigParser()
config_ini.read(os.path.join(APP_DIR,"config.ini"))
config_ini_identification = config_ini["identification"]
LOGIN_TOKEN = config_ini["identification"]["LOGIN_TOKEN"]


from libs.common_function import HandlerTool,CustomTornadoHandler
from models.data_access.redis_model import RedisRegister
#from handlers.decorator import authenticated
from models.business_logic.common_login import SqlFunc
from libs.sms_lib2 import CustomSms

def phonecheck(s):
    #号码前缀，如果运营商启用新的号段，只需要在此列表将新的号段加上即可。
    phoneprefix=['130','131','132','133','134','135','136','137','138','139','150','151','152','153','156','158','159','166','170','183','182','185','186','188','189']
    #检测号码是否长度是否合法。
    if len(s) != 11:
        return 0,"The length of phonenum is 11."
    else:
        #检测输入的号码是否全部是数字。
        if  s.isdigit():
            #检测前缀是否是正确。
            if s[:3] in phoneprefix:
                return 1,"The phone num is valid."
            else:
                return 0,"The phone num is invalid."
        else:
            return 0,"The phone num is made up of digits."

class RegisterHandler(CustomTornadoHandler):

    def get(self):
        random_number = "".join([chr(random.randrange(ord('0'), ord('9') + 1)) for _ in range(6)])
        mobilephone_number = str(self.get_argument("mobilephone_number", '')).strip()
        if phonecheck(mobilephone_number):
            try:
                sms_obj = CustomSms()
                result = sms_obj.send_id_code(mobilephone_number.strip(),random_number)
                #如果用户通过验证
                if result["Message"] == "OK":
                    redis_reg = RedisRegister(mobilephone_number)
                    redis_reg.set_id_code(random_number)
                    self.write(HandlerTool.set_response("0","success",{}))
                else:
                    self.write(HandlerTool.set_response("-1","网络繁忙，请稍后再试(red)",{}))
            except Exception as error:
                logging.exception(error,exc_info = True)
                self.write(HandlerTool.set_response("-1",str(error),{}))

    def post(self):
        request_body = HandlerTool.request_body_bytes2str(self.request.body)
        try:
            request_body = json.loads(request_body)
            mobilephone_number = request_body["mobilephone_number"].strip()
            password = request_body["password"].strip()
            #alipay_account = request_body["alipay_account"].strip()
            realname = request_body["realname"].strip()
            id_code = request_body["id_code"].strip()
            redis_reg = RedisRegister(mobilephone_number)
            if redis_reg.get_id_code() == id_code:
                SqlFunc.create_user(self.db_session,{"mobilephonenumber":mobilephone_number,"password":password,"realname":realname,"status":0,"rolename":"generaluser"})
                self.write(HandlerTool.set_response("0","",{}))
            else:
                self.write(HandlerTool.set_response("-1","验证码错误",{}))
        except Exception as error:
            self.db_session.rollback()
            logging.error(str(error),exc_info = True)
            self.write(HandlerTool.set_response("-1","没有访问权限",{}))

if __name__ == "__main__":
    pass
