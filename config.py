import tornado.web
import tornado.options
import tornado.log
from handlers import *
import logging
import os,configparser

FILE_DIR = os.path.dirname(os.path.realpath(__file__))
config_ini = configparser.ConfigParser()
config_ini.read(os.path.join(FILE_DIR,"config.ini"))
config_ini_identification = config_ini["identification"]

#2gb
MAX_BUFFER_SIZE = 2097152000

setting = {
        "cookie_secret":config_ini_identification["SECURE_KEY"],
        'gzip': True,
        'debug':False,
        "static_path": os.path.join(os.path.dirname(os.path.realpath(__file__)), "static"),
        "xsrf_cookies": False
        }
logging.info("setting is " + str(setting))

#前缀
URL_PREFIX = r"/" + config_ini_identification["PREFIX"]

#调整端口
tornado.options.define("port", default=9000, help="run on the given port", type=int)

#自定义日志等级
tornado.options.options.logging = "INFO"

#开启日志的颜色
tornado.log.enable_pretty_logging()


#自定义日志类

class LogFormatter(tornado.log.LogFormatter):

    def __init__(self):
        super(LogFormatter, self).__init__(
            fmt='%(color)s%(asctime)s | [%(process)d:%(threadName)s:%(thread)d] | [%(filename)s:%(funcName)s:%(lineno)d] | %(levelname)s%(end_color)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

for i in logging.getLogger().handlers:
    #logging.info(i)
    i.setFormatter(LogFormatter())


#读取命令行参数
tornado.options.parse_command_line()

