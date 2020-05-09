#!/usr/bin/env python
# coding=utf-8
import logging
import tornado.web,tornado.options
import json
import os,sys
import uuid
import redis
import configparser
from tornado.ioloop import IOLoop

APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(APP_DIR)
config_ini = configparser.ConfigParser()
config_ini.read(os.path.join(APP_DIR,"config.ini"))

config_ini_identification = config_ini["identification"]
LOGIN_TOKEN = config_ini["identification"]["LOGIN_TOKEN"]

config_ini_error = config_ini["error"]
COMMON_ERROR = config_ini_error["COMMON_ERROR"]

from libs.common_function import HandlerTool,CustomTornadoHandler
from libs.common_error import InputError
#from models.data_access.redis_model import RedisLoginAuth
#from handlers.decorator import authenticated
from models.business_logic.common_login import SqlFunc


class LoginHandler(CustomTornadoHandler):


    async def get(self):
        #mobilephone_number = self.get_argument('mobilephone_number', '')
        username = self.get_argument('username', '')
        password = self.get_argument('password', '')
        try:
            #mobilephone_number = mobilephone_number.strip()
            username = username.strip()
            password = password.strip()
            result = await IOLoop.current().run_in_executor(None,SqlFunc.verify_user,*(
                self.db_session,
                "by_username",
                {
                    "username":username,
                    "password":password}))
            if result:
                #生成token并存储
                token = result["token"]
                #前端设置cookies
                self.set_secure_cookie(LOGIN_TOKEN,token,expires_days=1/24/60 * int(config_ini_identification["LOGIN_EXPIRES_MIN"]))
                #logging.info(result)
                self.write(HandlerTool.set_response("0","",
                    {
                        "data":result["data"]["children"],
                        "username":result["username"],
                        "realname":result["realname"],
                        "role_list":result["role_list"],
                    }))
            else:
                self.write(HandlerTool.set_response("A00003","用户名或密码错误",{}))
        except InputError as error:
            self.db_session.rollback()
            logging.exception(error,exc_info = True)
            self.write(HandlerTool.set_response("-1",str(error),{}))
        except Exception as error:
            self.db_session.rollback()
            logging.exception(error,exc_info = True)
            self.write(HandlerTool.set_response("-1",COMMON_ERROR,{}))
        finally:
            self.finish()

class LoginRedisHandler(CustomTornadoHandler):


    async def get(self):
        #mobilephone_number = self.get_argument('mobilephone_number', '')
        username = self.get_argument('username', '')
        password = self.get_argument('password', '')
        try:
            #mobilephone_number = mobilephone_number.strip()
            username = username.strip()
            password = password.strip()
            result = await IOLoop.current().run_in_executor(None,SqlFunc.verify_user,*(
                self.db_session,
                "by_username",
                {
                    "username":username,
                    "password":password}))
            if result:
                #生成token并存储
                token = str(uuid.uuid1())
                login_auth = RedisLoginAuth(token)
                #uid,rid,limit_count
                uid = result["uid"]
                rid_set = result["rid_set"]
                login_auth.login_init(uid,rid_set,3)
                #前端设置cookies
                self.set_secure_cookie(LOGIN_TOKEN,token,expires_days=1/24/60 * int(config_ini_identification["LOGIN_EXPIRES_MIN"]))
                #logging.info(result)
                self.write(HandlerTool.set_response("0","",{"data":result["data"]["children"],"username":result["username"],"realname":result["realname"],"CARD_TID2DESC_HEADER_DICT":CARD_TID2DESC_HEADER_DICT,"CARD_TID2DATA_TID_DICT":CARD_TID2DATA_TID_DICT,"DATA_TID2DESC_DICT":DATA_TID2DESC_DICT,"DETAIL_STAUTS_DICT":DETAIL_STAUTS_DICT,"SINGLE_CARD_TID2DESC_HEADER_DICT":SINGLE_CARD_TID2DESC_HEADER_DICT}))
            else:
                self.write(HandlerTool.set_response("A00003","用户名或密码错误",{}))
        except InputError as error:
            self.db_session.rollback()
            logging.exception(error,exc_info = True)
            self.write(HandlerTool.set_response("-1",str(error),{}))
        except Exception as error:
            self.db_session.rollback()
            logging.exception(error,exc_info = True)
            self.write(HandlerTool.set_response("-1",COMMON_ERROR,{}))
        finally:
            self.finish()


if __name__ == "__main__":
    pass
