import oss2
#session最大连接数
oss2.defaults.connection_pool_size = 40000
import requests
import io
import pandas as pd
import logging
import configparser,os,sys
logging.basicConfig(level=logging.INFO)

#数据库配置文件
APP_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
config_ini = configparser.ConfigParser()
config_ini.read(os.path.join(APP_DIR,"config.ini"))
config_ini_aliyun = config_ini["aliyun"]
# 阿里云主账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM账号进行API访问或日常运维，请登录 https://ram.console.aliyun.com 创建RAM账号。
#auth = oss2.Auth('AccessKeyId', 'AccessKeySecret')
# Endpoint以杭州为例，其它Region请按实际情况填写。
#external_bucket = oss2.Bucket(auth, 'http://oss-cn-huhehaote.aliyuncs.com', 'bucket_name')
#internal_bucket = oss2.Bucket(auth, 'http://oss-cn-huhehaote-internal.aliyuncs.com', 'bucket_name')


class CustomOss2():

    def __init__(self,internal_bucket = oss2.Bucket(oss2.Auth(config_ini_aliyun['AccessKeyID'],config_ini_aliyun['AccessKeySecret']), config_ini_aliyun['OSS_ENDPOINT_INTERNAL'], config_ini_aliyun["BUCKET_NAME"]),external_bucket = oss2.Bucket(oss2.Auth(config_ini_aliyun['AccessKeyID'],config_ini_aliyun['AccessKeySecret']), config_ini_aliyun['OSS_ENDPOINT'], config_ini_aliyun["BUCKET_NAME"])):
        self.internal_bucket = internal_bucket
        self.external_bucket = external_bucket

    def is_file_exist(self,file_path:str):
        """
        判断文件在oss上是否存在
        """
        oss_file_path = file_path
        #logging.info("oss_file_path : " + str(oss_file_path))
        #is_exist = self.internal_bucket.object_exists(oss_file_path)
        file_path_set = set()
        prefix = os.path.dirname(file_path)
        if prefix[-1] != "/":
            prefix += "/"
        for obj in oss2.ObjectIterator(self.internal_bucket,prefix=prefix,delimiter = "/"):
            # 通过is_prefix方法判断obj是否为文件夹。
            if obj.is_prefix():  # 文件夹
                pass
            else:
                file_path_set.add(obj.key)
        is_exist = oss_file_path in file_path_set
        return is_exist

    def set_acl(self,file_path,permission=oss2.OBJECT_ACL_PUBLIC_READ):
        """
        设置文件权限为公共读
        """
        oss_file_path = file_path
        self.internal_bucket.put_object_acl(oss_file_path,permission)


    def set_all_file_acl(self,folder_path,permission=oss2.OBJECT_ACL_PUBLIC_READ):
        """
        设置文件夹下所有图片为 公共读
        """
        prefix = folder_path
        if prefix[-1] != "/":
            prefix += "/"
            #prefix = prefix[:-1]
        logging.info(prefix)
        for obj in oss2.ObjectIterator(self.internal_bucket,prefix=prefix,delimiter = "/"):
            logging.info(obj)
            # 通过is_prefix方法判断obj是否为文件夹。
            if obj.is_prefix():  # 文件夹
                pass
            else:
                logging.info(obj.key)
                self.internal_bucket.put_object_acl(obj.key,permission)


    def upload2oss(self,file_path,binary,force=0):
        """
        上传binary到oss
        """
        if force:
            oss_file_path = file_path
            res_obj = self.internal_bucket.put_object(oss_file_path, binary)
            return {"code":res_obj.status==200,"data":{"oss_file_path":oss_file_path,"bucket_name":config_ini_aliyun["BUCKET_NAME"],"oss_endpoint_internal":config_ini_aliyun['OSS_ENDPOINT_INTERNAL'],"oss_endpoint":config_ini_aliyun['OSS_ENDPOINT']}}
        else:
            if not self.is_file_exist(file_path):
                self.upload2oss(file_path,binary,1)
            else:
                raise ValueError("文件已存在")

    def download_binary(self,file_path:str):
        """
        把文件从oss上下载下来并返回binary
        """
        oss_file_path = file_path
        object_stream = self.internal_bucket.get_object(oss_file_path)
        return object_stream

    def get_download_file_url_or_None(self,file_path,time_out=int(config_ini_aliyun["TIME_OUT_SECOND"]),protocol="http"):
        """
        检查文件是否在oss，并返回下载链接或者空值
        """
        if self.is_file_exist(file_path):
            oss_file_path = file_path
            #logging.info("oss_file_path : " + str(oss_file_path))
            url = self.external_bucket.sign_url('GET', oss_file_path , time_out)
            if protocol=="https":
                url = url.replace("http","https")
            return url
        else:
            return ""

    def upload_df2excel(self,file_path:str,df:pd.DataFrame,sheetname="sheet1"):
        """
        上传df文件到oss
        """
        oss_file_path = file_path
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        writer.book.filename = output
        df.to_excel(writer, sheet_name='Sheet1',index=False)
        writer.save()
        xlsx_data = output.getvalue()
        res_obj = self.internal_bucket.put_object(oss_file_path, xlsx_data)
        #logging.debug(str(dir(res_obj)))
        #logging.debug(res_obj.request_id)
        #logging.debug(res_obj.status)
        return res_obj.status==200

    def download_excel2df(self,file_path:str):
        """
        把excel文件从oss上下载下来并返回pandas.DataFrame
        """
        oss_file_path = file_path
        object_stream = self.internal_bucket.get_object(oss_file_path)
        df = pd.read_excel(object_stream)
        return df

    def download_csv2df(self,file_path:str):
        """
        把csv文件从oss上下载下来并返回pandas.DataFrame
        """
        object_stream = self.internal_bucket.get_object(oss_file_path)
        df = pd.read_csv(object_stream)
        return df

logging.basicConfig(level=logging.INFO)
if __name__ == "__main__":
    df = pd.DataFrame([[1,2],[3,4]])
    #folder_path = 'mid-data/kg_link_one/'
    #folder_path = 'dip-dev-hhht/data-label-plat/'
    #folder_path = 'dip-data-labeling-platform/dev/ocr-file/task-file/202/'
    #file_name = 'urticaria_pityriasis lichenoides.xlsx'
    #file_name = '3_en.pdf'
    #oss_obj = CustomOss2()
    #oss_obj.set_all_file_acl(folder_path)
    file_path = "check-platform/dev/ocr/2019_08_28_20_37_59_230_0.pdf"
    oss_obj = CustomOss2()
    logging.info(oss_obj.get_download_file_url_or_None(file_path,protocol="https"))
    logging.info("-----------------------------------------------------------------")
    #logging.info(oss_obj.is_file_exist(file_name))