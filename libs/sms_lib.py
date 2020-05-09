#coding=utf-8

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
import logging,datetime
import configparser,os,sys,json
logging.basicConfig(level=logging.INFO)

#数据库配置文件
APP_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
config_ini = configparser.ConfigParser()
config_ini.read(os.path.join(APP_DIR,"config.ini"))
config_ini_aliyun = config_ini["aliyun"]

#说明文档https://help.aliyun.com/document_detail/55491.html?spm=a2c4g.11186623.6.651.5b6651cd3zVeQm

class CustomSms():

    def __init__(self,client = AcsClient("AccessKeyID", "AccessKeySecret", 'cn-hangzhou'),request = CommonRequest()):
        self.client = client
        self.request = request

    def send_id_code(self,mobilephone_number:str,id_code:str):
        self.request.set_accept_format('json')
        self.request.set_domain('dysmsapi.aliyuncs.com')
        self.request.set_method('POST')
        self.request.set_protocol_type('https') # https | http
        self.request.set_version('2017-05-25')
        self.request.set_action_name('SendSms')

        #短信接收号码
        self.request.add_query_param('PhoneNumbers', mobilephone_number)
        #短信签名
        #self.request.add_query_param('SignName', '阿里云短信测试专用')
        self.request.add_query_param('SignName', 'dipoa')
        #短信模板ID
        self.request.add_query_param('TemplateCode', 'SMS_135000014')

        self.request.add_query_param("TemplateParam",json.dumps({"code":id_code}))
        response = json.loads(str(self.client.do_action(self.request),encoding = 'utf-8'))
        logging.info(response)
        return response
        #return response["Message"] == "OK"

if __name__ == "__main__":
    sms_obj = CustomSms()
    print(sms_obj.send_id_code("18811436160","123456"))