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
import sqlalchemy

#数据库配置文件
APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(APP_DIR)
config_ini = configparser.ConfigParser()
config_ini.read(os.path.join(APP_DIR,"config.ini"))
LOGIN_TOKEN = config_ini["identification"]["LOGIN_TOKEN"]
COMMON_ERROR = config_ini["error"]["COMMON_ERROR"]

from libs.common_function import HandlerTool,CustomTornadoHandler
from libs.common_error import InputError
#from models.data_access.redis_model import RedisRegister
from libs.decorator import authenticated
from models.business_logic.common_login import SqlFunc
from libs.sms_lib2 import CustomSms
#from models.data_access.redis_model import RedisLoginAuth
from libs.common_function import CommonFunc

class UserInformationHandler(CustomTornadoHandler):

    @authenticated({2})
    def get(self):
        token = self.get_secure_cookie(LOGIN_TOKEN)
        try:
            action = self.get_argument("action")
            #login_auth = RedisLoginAuth(token)
            #uid = login_auth.get_uid()
            if action == "get_user_list":
                page_num = self.get_argument('pageNum')
                page_size = self.get_argument('pageSize')
                limit = int(page_size)
                offset = (int(page_num)) * limit
                order_by = self.get_argument("order_by","gmt_create")
                filter_dict = json.loads(self.get_argument("filter_dict","{}"))

                data = SqlFunc.get_user_information(
                    self.db_session,
                    action,
                    {
                        "limit":limit,
                        "offset":offset,
                        "order_by_list":[order_by],
                        "filter_dict":filter_dict
                    }
                )
                self.write(HandlerTool.set_response(0,"",data))
        except Exception as error:
            self.db_session.rollback()
            logging.error(str(error),exc_info = True)
            self.write(HandlerTool.set_response(-1,COMMON_ERROR,{}))

    def post(self):
        request_body = HandlerTool.request_body_bytes2str(self.request.body)
        request_body_dict = json.loads(request_body)
        try:
            action = request_body_dict["action"]
            if action == "insert_user":
                if not CommonFunc.check_is_chinese(request_body_dict["real_name"]):
                    raise InputError("真实姓名必须全部为中文，请检查")
                SqlFunc.create_user(
                    self.db_session,
                    {
                        "username":request_body_dict["username"],
                        "password":request_body_dict["password"],
                        "real_name":request_body_dict["real_name"],
                        "status":int(request_body_dict["status"]),
                        "rid":int(request_body_dict["role"])
                    })
                self.write(HandlerTool.set_response("0","",{}))
        except InputError as error:
            self.db_session.rollback()
            logging.error(str(error),exc_info = True)
            self.write(HandlerTool.set_response("-1",str(error),{}))
        except sqlalchemy.exc.IntegrityError as error:
            self.db_session.rollback()
            logging.error(str(error),exc_info = True)
            self.write(HandlerTool.set_response("-1","账号已存在",{}))
        except Exception as error:
            self.db_session.rollback()
            logging.error(str(error),exc_info = True)
            self.write(HandlerTool.set_response("-1",COMMON_ERROR,{}))

    def patch(self):
        request_body = HandlerTool.request_body_bytes2str(self.request.body)
        request_body_dict = json.loads(request_body)
        token = self.get_secure_cookie(LOGIN_TOKEN)
        try:
            action = request_body_dict["action"]
            if action == "update_user_information":
                if not CommonFunc.check_is_chinese(request_body_dict["real_name"]):
                    raise InputError("真实姓名必须全部为中文，请检查")
                SqlFunc.update_user(
                    self.db_session,
                    action,
                    {
                        "status":request_body_dict["status"],
                        "real_name":request_body_dict["real_name"],
                        "uid":request_body_dict["id"]
                    })
                self.write(HandlerTool.set_response("0","success",{}))
            elif action == "update_user_password":
                SqlFunc.update_user(
                    self.db_session,
                    action,
                    {
                        "uid":self.get_uid(token),
                        "old_password":request_body_dict["old_password"].strip(),
                        "new_password":request_body_dict["new_password"].strip()
                    })
                self.write(HandlerTool.set_response("0","success",{}))
            else:
                raise InputError("action错误")
        except InputError as error:
            self.db_session.rollback()
            logging.error(str(error),exc_info = True)
            self.write(HandlerTool.set_response("-1",str(error),{}))
        except Exception as error:
            self.db_session.rollback()
            logging.exception(error,exc_info = True)
            self.write(HandlerTool.set_response("-1",COMMON_ERROR,{}))

if __name__ == "__main__":
    pass
