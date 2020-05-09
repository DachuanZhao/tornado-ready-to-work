import os,sys,logging,json
import bisect,uuid,redis
import configparser,os
#数据库配置文件
APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(APP_DIR)
config_ini = configparser.ConfigParser()
config_ini.read(os.path.join(APP_DIR,"config.ini"))
config_ini_database = config_ini["database"]
config_ini_identification = config_ini["identification"]

REDIS_HOST = config_ini_database["REDIS_HOST"]
REDIS_PORT = int(config_ini_database["REDIS_PORT"])
REDIS_PASSWORD = config_ini_database["REDIS_PASSWORD"]
REDIS_DATABASE = int(config_ini_database["REDIS_DATABASE"])
#sortset,利用默认排序实现搜索推荐
#redis_entity_name_search_suggestion_pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=2,password=REDIS_PASSWORD)


#key,value连接池

redis_key_value_pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DATABASE,password=REDIS_PASSWORD)

class RedisSmsVerify():

    #短信验证的相关模块
    @staticmethod
    def bytes2str(token):
        if isinstance(token,bytes):
            token=token.decode("utf8")
        return token


    def __init__(self,mobilephone_number:str,conn=redis.StrictRedis(connection_pool=redis_key_value_pool),
            prefix=config_ini_identification["PREFIX"]+"_"+"RGT"+"_"):
        self.mobilephone_number = RedisSmsVerify.bytes2str(mobilephone_number)
        self.conn=conn
        self.prefix=prefix

    def set_id_code(self,id_code:str):
        self.conn.set(self.prefix+self.mobilephone_number,id_code)
        self.conn.expire(self.prefix+self.mobilephone_number,300) #五分钟

    def get_id_code(self):
        id_code = self.conn.get(self.prefix+self.mobilephone_number)
        return RedisSmsVerify.bytes2str(id_code)

class RedisRegister(RedisSmsVerify):

    #注册的模块
    def __init__(self,mobilephone_number:str,conn=redis.StrictRedis(connection_pool=redis_key_value_pool),
            prefix=config_ini_identification["PREFIX"]+"_"+"RGT"+"_"):
        super(RedisRegister, self).__init__(mobilephone_number,conn,prefix)

class RedisChangePassword(RedisSmsVerify):

    #修改密码的模块
    def __init__(self,mobilephone_number:str,conn=redis.StrictRedis(connection_pool=redis_key_value_pool),
            prefix=config_ini_identification["PREFIX"]+"_"+"RCPW"+"_"):
        super(RedisChangePassword, self).__init__(mobilephone_number,conn,prefix)


class RedisLoginAuth():

    @staticmethod
    def bytes_str(token):
        if isinstance(token,bytes):
            token=token.decode("utf8")
        return token

    def __init__(self,token,conn=redis.StrictRedis(connection_pool=redis_key_value_pool),
            token_prefix=config_ini_identification["PREFIX"]+"_"+"UT"+"_",
            count_prefix=config_ini_identification["PREFIX"]+"_"+"UC"+"_",
            sql_rid_prefix=config_ini_identification["PREFIX"]+"_"+"SRD"+"_",
            sql_count_prefix=config_ini_identification["PREFIX"]+"_"+"SC"+"_"):
        self.token=RedisLoginAuth.bytes_str(token)
        self.conn=conn
        self.token_prefix=token_prefix
        self.count_prefix=count_prefix
        self.sql_rid_prefix=sql_rid_prefix
        self.sql_count_prefix=sql_count_prefix

    def get_uid(self)->int:
        #sql查询权限时需要
        uid = RedisLoginAuth.bytes_str(self.conn.get(self.token_prefix+self.token))
        if uid:
            return int(uid)
        else:
            return 0

    def get_rid_set(self)->set:
        #sql查询权限时需要
        uid = self.get_uid()
        if uid:
            uid = str(uid)
            rid_set = {int(RedisLoginAuth.bytes_str(v)) for v in self.conn.smembers(self.sql_rid_prefix+uid)}
            return rid_set
        else:
            return 0


    def is_count_lte_limit(self)->int:
        uid = str(self.get_uid())
        if uid:
            uid = str(uid)
            _count = RedisLoginAuth.bytes_str(self.conn.get(self.count_prefix+uid))
            limit_count = RedisLoginAuth.bytes_str(self.conn.get(self.sql_count_prefix+uid))
            return int(_count)<=int(limit_count)
        else:
            return 0

    def update_expire_second(self,expire_second=60 * int(config_ini_identification["LOGIN_EXPIRES_MIN"])):
        #更新时间，每次打接口都需要
        self.conn.expire(self.token_prefix+self.token,expire_second)
        uid = RedisLoginAuth.bytes_str(self.conn.get(self.token_prefix+self.token))
        self.conn.expire(self.token_prefix+uid,expire_second)
        #self.conn.incr(self.count_prefix+uid,expire_second)
        self.conn.expire(self.count_prefix+uid,expire_second)
        self.conn.expire(self.sql_rid_prefix+uid,expire_second)
        self.conn.expire(self.sql_count_prefix+uid,expire_second)

    def login_init(self,uid:str,rid_set:set,limit_count:str,expire_second=60 * int(config_ini_identification["LOGIN_EXPIRES_MIN"])):
        """
        #登陆成功初始化，需要初始化：
        #token->uid
        #uid->token
        #uid->count
        #先删除已有的token,这一步实现了登陆互踢
        """
        if isinstance(uid,int):
            uid = str(uid)
        if isinstance(limit_count,int):
            limit_count = str(limit_count)
        old_token = self.conn.get(self.token_prefix+uid)
        if old_token:
            old_token = RedisLoginAuth.bytes_str(old_token)
            if self.conn.get(self.token_prefix+old_token):
                self.conn.delete(self.token_prefix+old_token)
        #再更新
        #token->uid
        self.conn.set(self.token_prefix+self.token,uid)
        self.conn.expire(self.token_prefix+self.token,expire_second)
        #uid->token
        self.conn.set(self.token_prefix+uid,self.token)
        self.conn.expire(self.token_prefix+uid,expire_second)
        #uid->action count
        self.conn.set(self.count_prefix+uid,0)
        self.conn.expire(self.count_prefix+uid,expire_second)
        #uid->rid_set
        for v in rid_set:
            self.conn.sadd(self.sql_rid_prefix+uid,v)
        self.conn.expire(self.sql_rid_prefix+uid,expire_second)
        #uid->count_limit
        self.conn.set(self.sql_count_prefix+uid,limit_count)
        self.conn.expire(self.sql_count_prefix+uid,expire_second)

class RedisTaskQueue():

    @staticmethod
    def bytes_str(token):
        if isinstance(token,bytes):
            token=token.decode("utf8")
        return token


    def __init__(self,task_name:str,conn=redis.StrictRedis(connection_pool=redis_key_value_pool),prefix=config_ini_identification["PREFIX"]+"_"+"TQ"+"_"):
        self.task_name = task_name.upper()
        self.conn = conn
        self.prefix = prefix

    def send_task2queue(self,dict1:dict):
        self.conn.rpush(self.prefix+self.task_name,json.dumps(dict1))

    def get_task(self,callback_func=None):
        #<=30s内等待任务返回
        result = self.conn.blpop(self.prefix+self.task_name,30)
        if result:
            key,task = result
            logging.info(task)
            task = self.bytes_str(task)
            task_dict = json.loads(task)
        else:
            task_dict = {}
        return task_dict

    def get_task_from_queue(self,callback_func=None):
        #返回指定位置任务
        task = self.conn.lindex(self.prefix+self.task_name,0)
        if task:
            logging.info(task)
            task = self.bytes_str(task)
            task_dict = json.loads(task)
        else:
            task_dict = {}
        return task_dict


class RedisRequestBody2Data():

    def __init__(self,request_body_str,conn=redis.StrictRedis(connection_pool=redis_key_value_pool),prefix=config_ini_identification["PREFIX"]+"_"+"RBD"+"_"):
        self.request_body_str=request_body_str if not isinstance(request_body_str,dict) else json.dumps(request_body_str)
        self.conn = conn
        self.prefix = prefix

    def is_cached_or_get(self,expire_second=60 * int(config_ini_identification["LOGIN_EXPIRES_MIN"]))->dict:
        data_dict_str = self.conn.get(self.prefix+self.request_body_str)
        if isinstance(data_dict_str,bytes):
            data_dict_str = data_dict_str.decode()
        if data_dict_str:
            #更新有效时间
            self.conn.expire(self.prefix+self.request_body_str,expire_second)
            data_dict = json.loads(data_dict_str)
        else:
            data_dict = {}
        return data_dict

    def add(self,data_dict_str,expire_second=60 * int(config_ini_identification["LOGIN_EXPIRES_MIN"])):
        if isinstance(data_dict_str,dict):
            data_dict_str = json.dumps(data_dict_str)
        self.conn.set(self.prefix+self.request_body_str,data_dict_str)
        self.conn.expire(self.prefix+self.request_body_str,expire_second)
        return


class RedisForwardBackward():

    def __init__(self,token,conn=redis.StrictRedis(connection_pool=redis_key_value_pool),prefix=config_ini_identification["PREFIX"]):
        self.token = token if not isinstance(token,bytes) else token.decode()
        self.conn = conn
        self.prefix = prefix

    def get_backward(self):
        backward_data_dict_str = self.conn.lindex(self.prefix+self.token+"_backward",0)
        if isinstance(backward_data_dict_str,bytes):
            backward_data_dict_str = backward_data_dict_str.decode()
        if backward_data_dict_str:
            return  json.loads(backward_data_dict_str)
        else:
            return {}

    def add_backward(self,str1):
        self.conn.lpush(self.prefix+self.token+"_backward",str1)

    def add_backward_and_delete_forward(self,str1):
        self.conn.lpush(self.prefix+self.token+"_backward",str1)
        self.conn.delete(self.prefix+self.token+"_backward")

    def add_forward(self,str1):
        self.conn.lpush(self.prefix+self.token+"_forward",str1)

    def delete_forward(self):
        self.conn.ltrim(self.prefix+self.token+"_forward",1,0)

    def is_forward_and_return_data_dict(self):
        if len(self.conn.lrange(self.prefix+self.token+"_backward",0,-1))>0:
            forward = self.conn.lpop(self.prefix+self.token+"_forward",0,0)
            self.add_backward(forward)
            return json.loads(forward)
        else:
            return 0

    def is_backward_and_return_data_dict(self):
        if len(self.conn.lrange(self.prefix+self.token+"_backward",0,-1))>1:
            now = self.conn.lpop(self.prefix+self.token+"_backward")
            self.add_forward(now)
            backward = self.conn.lpop(self.prefix+self.token+"_backward")
            return json.loads(backward)
        else:
            return 0

class Maintenance():

    @staticmethod
    def init_entity_name_search_suggestion_db(conn,entity_name_list:list,key:str):
        #清空所有数据
        conn.flushdb()
        if isinstance(entity_name_list,list) and isinstance(key,str):\
            #加入数据
            with conn.pipeline(transaction=True) as pipeline:
                for i,name in enumerate(entity_name_list):
                    if i%1000==0:logging.info({i:name})
                    pipeline.zadd(key,{name:0})
                pipeline.execute()
        else:
            raise TypeError("Invalid type")

    @staticmethod
    def remove_except_redis_entity_name_search_suggestion_pool():
        conn = redis.StrictRedis(connection_pool=redis_key_value_pool)
        conn.flushdb()



def autocomplete_on_prefix(key:str,prefix:str):
    """
    二分查找字符串
    """
    def find_prefix_range(prefix:str)->tuple:
        """
        输入字符，按照valid_characters输出应该返回的字符范围
        ascii编码里，顺序就是这样：a前面是`，z后面是{
        找abc其实就是找abb{--abc{
        """
        valid_characters = "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{~"
        valid_characters = chr(ord(valid_characters[0]) - 1) + valid_characters + chr(ord(valid_characters[-1]) + 1)
        last_str = valid_characters[-1]
        #写成[-1:]是为了避免index_out_of_range，计算最后一个字符左侧的字符
        posn = bisect.bisect_left(valid_characters,prefix[-1:])
        suffix = valid_characters[(posn or 1) - 1]
        start_str = prefix[:-1] + suffix + last_str
        end_str = prefix + last_str
        return start_str,end_str,last_str

    conn = redis.StrictRedis(connection_pool=redis_entity_name_search_suggestion_pool)
    start_str,end_str,last_str = find_prefix_range(prefix)
    #print(start_str,end_str)
    #因为要插入，所以生成一个独一无二的字符串放在后面
    id_ = str(uuid.uuid4())
    start_str += id_
    end_str += id_
    zset_name = key
    #范围开始和结束的元素插入有序集合里面
    #print(zset_name,start_str,end_str)
    #print(type(zset_name),type(start_str),type(end_str))
    conn.zadd(zset_name,{start_str:0,end_str:0})
    pipeline = conn.pipeline(transaction=True)
    while True:
        try:
            # watch库存键, multi后如果该key被其他客户端改变, 事务操作会抛出WatchError异常
            pipeline.watch(zset_name)
            start_index = pipeline.zrank(zset_name,start_str)
            end_index = pipeline.zrank(zset_name,end_str)
            end_range = min(start_index + 10,end_index)
            #logging.info(" start " + str(start_index) + " end " + str(end_index) + " end_range " + str(end_range))
            pipeline.multi()
            pipeline.zrem(zset_name,start_str,end_str)
            pipeline.zrange(zset_name,start_index,end_range)
            item_list = pipeline.execute()[-1]
            #print(item_list)
            break
        except redis.exceptions.WatchError:
            continue
    return [item.decode() for item in item_list if last_str not in item.decode()]

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    Maintenance.remove_except_redis_entity_name_search_suggestion_pool()
    #from models.neo4j_model import CustomMedicalEntity
    #conn = redis.StrictRedis(connection_pool=redis_entity_name_search_suggestion_pool)
    #print(conn.zscore(key,"(+)-3-(Trifluoroacetyl)camphor"))
    #print(autocomplete_on_prefix(conn,key,"(+)"))
    #print([entity.name for entity in MedicalEntityDict.objects() if entity.name][0:10])
    #logging.info(RedisTaskQueue().get_task_from_queue())
    #logging.info(RedisTaskQueue().get_task())
