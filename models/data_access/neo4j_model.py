import neomodel,concurrent.futures
import json,logging
import configparser,os
import numpy as np
import concurrent.futures
import sys
import neo4j

#数据库配置文件
APP_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
config_ini = configparser.ConfigParser()
config_ini.read(os.path.join(APP_DIR,"config.ini"))
config_ini_database = config_ini["database"]


#neo4j连接
NEO4J_USERNAME = config_ini_database["NEO4J_USERNAME"]
NEO4J_PASSWORD = config_ini_database["NEO4J_PASSWORD"]
NEO4J_HOST = config_ini_database["NEO4J_HOST"]
NEO4J_PORT = config_ini_database["NEO4J_PORT"]

NEO4J_URI = "bolt://{NEO4J_HOST}:{NEO4J_PORT}".format(NEO4J_HOST=NEO4J_HOST,NEO4J_PORT=NEO4J_PORT)

NEO4J_DRIVER = neo4j.GraphDatabase.driver(
    uri=NEO4J_URI,
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
    encrypted = False,
    max_connection_lifetime=30 * 60,
    max_connection_pool_size=150, #neo4j默认是400
    connection_acquisition_timeout=2 * 60,
    connection_timeout=3,
    max_retry_time=1,
    )

#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    session = NEO4J_DRIVER.session()
    logging.info(dir(session))
    with NEO4J_DRIVER.session() as session:
        res = session.run('match (entity) where entity.name="{name}" or entity.name="{name1}" return entity'.           format(name="tcf15",name1="tcf12"))
        logging.info(dir(res))
        for r in res:
            logging.info(r["entity"])
            logging.info(r["entity"]["name"])
            logging.info(dir(r))
    session.close()
