import os,configparser,logging,sys,json
import functools,redis,uuid
import logging

#数据库配置文件
APP_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(APP_DIR)
config_ini = configparser.ConfigParser()
config_ini.read(os.path.join(APP_DIR,"config.ini"))
config_ini_identification = config_ini["identification"]
LOGIN_TOKEN = config_ini["identification"]["LOGIN_TOKEN"]

from models.data_access.redis_model import RedisLoginAuth
from libs.common_function import HandlerTool

def authenticated(rid_set=None):
    if rid_set:
        if not isinstance(rid_set,set):
            rid_set = set([rid_set])
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            token = self.get_secure_cookie(LOGIN_TOKEN)
            #如果token在前端不存在，就重新登陆
            if token:
                login_auth = RedisLoginAuth(token)
                uid = login_auth.get_uid()
                #如果token在后端不存在，直接重新登陆
                if not uid:
                    self.write({"code":"A00004","desc":"登陆失效，请重新登陆","data":{}})
                    return
                else:
                    #如果计数器大于规定的值，直接重新登陆,重新登陆的时候也会判断这个值，所以相当于用户登陆不了
                    if not login_auth.is_count_lte_limit():
                        self.write({"code":"A00004","desc":"登陆失效，请重新登陆(用户登陆次数超限制)","data":{}})
                        return
                    else:
                        #计数器+1
                        #username_count.create_or_incr()
                        #如果有参数，继续检查参数
                        if rid_set:
                            #logging.info(rid_set)
                            #logging.info(login_auth.get_rid_set())
                            if not rid_set.issubset(login_auth.get_rid_set()):
                                self.write({"code":"A00009","desc":"没有权限","data":{}})
                                return
            else:
                self.write({"code":"A00004","desc":"登陆失效，请重新登陆","data":{}})
                return
            #全部通过的话，前端和后端都需要更新token时间
            #前端更新
            self.set_secure_cookie(LOGIN_TOKEN,token,expires_days=1/24/60 * int(config_ini_identification["LOGIN_EXPIRES_MIN"]) )
            #后端更新
            login_auth.update_expire_second()
            #logging.info(self.request.body)
            if self.request.body[0:3].decode() != "---":
                monitor_dict = {"uid":uid,"uri":self.request.uri,"body":json.loads(HandlerTool.request_body_bytes2str(self.request.body))}
            else:
                monitor_dict = {"uid":uid,"uri":self.request.uri,"body":self.request.body.decode()}
            logging.info("{}".format(json.dumps(monitor_dict,ensure_ascii=False)))
            return func(self, *args, **kwargs)
        return wrapper
    return decorator
