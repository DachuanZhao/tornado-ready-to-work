from mongoengine import *
import json,sys
import urllib.parse
import configparser,os
import logging
import datetime
import concurrent.futures

#数据库配置文件
APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(APP_DIR)
config_ini = configparser.ConfigParser()
config_ini.read(os.path.join(APP_DIR,"config.ini"))
config_ini_database = config_ini["database"]

MONGODB_HOST1 = config_ini_database["MONGODB_HOST1"]
MONGODB_HOST2 = config_ini_database["MONGODB_HOST2"]
MONGODB_PORT = config_ini_database["MONGODB_PORT"]
MONGODB_DATABASE = config_ini_database["MONGODB_DATABASE"]
MONGODB_USERNAME = config_ini_database["MONGODB_USERNAME"]
MONGODB_PASSWORD = config_ini_database["MONGODB_PASSWORD"]


connect(
    db = MONGODB_DATABASE,
    host = "mongodb://{}:{}@{}:{},{}:{}/{}".format(MONGODB_USERNAME,urllib.parse.quote_plus(MONGODB_PASSWORD),MONGODB_HOST1,MONGODB_PORT,MONGODB_HOST2,MONGODB_PORT,MONGODB_DATABASE),
    maxPoolSize = 50,
    waitQueueMultiple = 10,
    connect = False)

class OrmAttritudeClass(EmbeddedDocument):
    id = IntField(min_value=-1,required=True)#序号
    text = StringField(required=True, default="")

class OrmClass(Document):
    meta = {'collection':'example',
            'index':[
                'tid',
                'textlist.id',
                ]}

    _id = StringField(required=True)
    gmt_create = DateTimeField()
    gmt_modified = DateTimeField(default=datetime.datetime.now)
    tid = IntField(min_value=1,required=True)
    textlist = ListField(EmbeddedDocumentField(OrmAttritudeClass),required=True)

    def clean(self, *args, **kwargs):
        if not self.gmt_create:
            self.gmt_create = datetime.datetime.now()
        self.gmt_modified = datetime.datetime.now()
        return super(OrmClass, self).clean(*args, **kwargs)
