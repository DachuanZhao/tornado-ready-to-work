# -*- coding: utf-8 -*-
from sqlalchemy import Column,String,Integer,DECIMAL,DateTime,func,literal,desc,UniqueConstraint
from sqlalchemy import create_engine,event,exc,MetaData,Table
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import sessionmaker,scoped_session,mapper
from sqlalchemy.ext.declarative import declarative_base
import configparser,os,sys,logging,datetime
import hashlib
import string
import random
import decimal
import dataclasses
import copy

#数据库配置文件
APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(APP_DIR)
config_ini = configparser.ConfigParser()
config_ini.read(os.path.join(APP_DIR,"config.ini"))
config_ini_database = config_ini["database"]

#数据库连接
#SQLITE3_DB_URL = config_ini_database["SQLITE3_DB_URL"]

MYSQL_HOST = config_ini_database["MYSQL_HOST"]
MYSQL_PORT = config_ini_database["MYSQL_PORT"]
MYSQL_DATABASE = config_ini_database["MYSQL_DATABASE"]
MYSQL_USERNAME = config_ini_database["MYSQL_USERNAME"]
MYSQL_PASSWORD = config_ini_database["MYSQL_PASSWORD"]
MYSQL_DB_URL = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8'.format(MYSQL_USERNAME,MYSQL_PASSWORD,MYSQL_HOST,MYSQL_PORT,MYSQL_DATABASE)

Base = declarative_base()

# 初始化数据库连接:
#engine = create_engine(SQLITE3_DB_URL,connect_args={'check_same_thread':False})
#连接池大小，可上溢的连接池,连接池释放时间
engine = create_engine(MYSQL_DB_URL,pool_size=300,max_overflow=0,pool_recycle=1800,pool_pre_ping=True)

#多进程相关配置,Pool使用事件来检测自身，以便在子进程中自动使过期连接无效
@event.listens_for(engine, "connect")
def connect(dbapi_connection, connection_record):
    connection_record.info['pid'] = os.getpid()

@event.listens_for(engine, "checkout")
def checkout(dbapi_connection, connection_record, connection_proxy):
    pid = os.getpid()
    if connection_record.info['pid'] != pid:
        connection_record.connection = connection_proxy.connection = None
        raise exc.DisconnectionError(
                "Connection record belongs to pid %s, "
                "attempting to check out in pid %s" %
                (connection_record.info['pid'], pid)
        )

#metadata
metadata = MetaData()

# 创建DBSession类型:
DBSession = sessionmaker(bind=engine)
#确保同一个线程中用的是一个session
db_session = scoped_session(DBSession)

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer,primary_key=True,autoincrement=True)
    mobilephonenumber = Column(String(20),index=True,unique=True,nullable=False)
    username = Column(String(20),index=True,unique=True)
    password = Column(String(100),nullable=False)
    alipayaccount = Column(String(100))
    idcard = Column(String(100))
    bankaccount = Column(String(100))
    bankaddress = Column(String(400))
    realname = Column(String(20),index=True,nullable=False)
    status = Column(INTEGER(unsigned=True),index=True,nullable=False,default=0,server_default="0") #0为待审核，1为正常，2为锁定
    gmt_create = Column(DateTime(), default=datetime.datetime.now)
    gmt_modified = Column(DateTime(), default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def __repr__(self):
        return '<User %r>' % self.username

class Role(Base):
    __tablename__ = 'role'
    id = Column(Integer,primary_key=True,autoincrement=True)
    rolename = Column(String(100),index=True,unique=True)
    roledesc = Column(String(4000))
    gmt_create = Column(DateTime(), default=datetime.datetime.now)
    gmt_modified = Column(DateTime(), default=datetime.datetime.now, onupdate=datetime.datetime.now)

class Permission(Base):
    __tablename__ = 'permission'
    id = Column(Integer,primary_key=True,autoincrement=True)
    name = Column(String(100),index=True)
    fatherpid = Column(Integer,index=True)
    url = Column(String(100))
    desc = Column(String(4000))
    level = Column(Integer,index=True)
    gmt_create = Column(DateTime(), default=datetime.datetime.now)
    gmt_modified = Column(DateTime(), default=datetime.datetime.now, onupdate=datetime.datetime.now)

class UserRole(Base):
    __tablename__ = 'user_role'
    id = Column(Integer,primary_key=True,autoincrement=True)
    uid = Column(Integer,index=True,nullable=False)
    rid = Column(Integer,index=True,nullable=False)
    gmt_create = Column(DateTime(), default=datetime.datetime.now)
    gmt_modified = Column(DateTime(), default=datetime.datetime.now, onupdate=datetime.datetime.now)

class RolePermission(Base):
    __tablename__ = 'role_permission'
    id = Column(Integer,primary_key=True,autoincrement=True)
    rid = Column(Integer,index=True,nullable=False)
    pid = Column(Integer,index=True,nullable=False)
    is_permitted = Column(INTEGER(unsigned=True),index=True)
    gmt_create = Column(DateTime(), default=datetime.datetime.now)
    gmt_modified = Column(DateTime(), default=datetime.datetime.now, onupdate=datetime.datetime.now)



class CustomTable():
    """
    需要动态建表的类
    """
    def __init__(self,table_name,metadata=metadata):
        self.table = Table(table_name,metadata,
            Column('id',Integer,primary_key=True,autoincrement=True),
            extend_existing=True,
            )
        #建表
        self.initial(engine=engine)

    def initial(self,engine=engine):
        #self.drop_table(engine)
        self.create_table(engine=engine)

    def create_table(self,engine=engine):
        """
        建表
        """
        self.table.create(engine,checkfirst=True)

    def drop_table(self,engine=engine):
        """
        删表
        """
        self.table.drop(engine,checkfirst=True)

if __name__ == "__main__":
    logging.info(MYSQL_DB_URL)
    Base.metadata.create_all(engine)
