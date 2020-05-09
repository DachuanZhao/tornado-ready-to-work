import configparser,os,sys,logging,datetime
import hashlib
import string
import random
import decimal
import logging
import anytree
import anytree.exporter
import json
import copy

APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(APP_DIR)
config_ini = configparser.ConfigParser()
config_ini.read(os.path.join(APP_DIR,"config.ini"))

from models.data_access.sql_model import db_session,User,Role,Permission,UserRole,RolePermission
#from libs.oss2_libs import CustomOss2


class SqlFunc():
    """
    定义一些需要使用的函数
    """
    @staticmethod
    def create_user(session,update_dict):
        username = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        mobilephone_number = update_dict["mobilephonenumber"]
        password = update_dict["password"]
        realname = update_dict["realname"]
        status = update_dict["status"]
        rolename = update_dict["rolename"]
        user = User(mobilephonenumber=mobilephone_number,password=password,realname=realname,status=status)
        session.add(user)
        #增加user的role
        uid = session.query(User.id).filter(User.mobilephonenumber==mobilephone_number).first()[0]
        rid = db_session.query(Role.id).filter(Role.rolename==rolename).first()[0]
        user_role = UserRole(uid=uid,rid=rid)
        session.add(user_role)
        session.commit()

    @staticmethod
    def verify_user(session,action,param_dict):
        """
        检查账号密码
        """
        if action == "by_username":
            username = param_dict["username"]
            password = param_dict["password"]
            #query_result = session.query(User).filter(User.mobilephonenumber == mobilephone_number,User.password ==  password).first()
            query_result = session.query(User).filter(User.username == username,User.password ==  password).first()
            if query_result:
                uid = query_result.id
                username = query_result.username
                realname = query_result.realname
                status = query_result.status
                if status:
                    query = session.query(UserRole,RolePermission,Permission).filter(UserRole.uid==uid,UserRole.rid==RolePermission.rid,RolePermission.pid==Permission.id).order_by()
                    root = anytree.AnyNode(name="root")
                    id2dict = {}
                    rid_set = set()
                    pid_set = set()
                    permission_dict_list = []
                    exporter = anytree.exporter.JsonExporter(indent=2, sort_keys=True)
                    for v in query:
                        #print([v.UserRole.rid,v.RolePermission.pid,v.Permission.id,v.Permission.fatherpid,v.Permission.name])
                        rid_set.add(v.UserRole.rid)
                        if not v.Permission.id in pid_set:
                            pid_set.add(v.Permission.id)
                            permission_dict_list.append({"id":v.Permission.id,"name":v.Permission.name,"fatherpid":v.Permission.fatherpid})
                    for v in permission_dict_list:
                        if v["fatherpid"] == -1:
                            id2dict[v["id"]] = anytree.AnyNode(id=v["id"],name=v["name"],parent=root)
                    #二层结构的特别写法
                    for v in permission_dict_list:
                        if v["fatherpid"] != -1:
                            id2dict[v["id"]] = anytree.AnyNode(id=v["id"],name=v["name"],parent=id2dict[v["fatherpid"]])
                    return {"data":json.loads(exporter.export(root)),"username":username,"uid":uid,"rid_set":rid_set,"realname":realname}
                else:
                    raise ValueError("等待用户审核")
            else:
                raise ValueError("用户名密码错误")

