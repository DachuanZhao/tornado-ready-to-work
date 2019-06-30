from elasticsearch import Elasticsearch
from elasticsearch_dsl import DocType, Date, Integer, Keyword, Text
from elasticsearch_dsl import Search
from elasticsearch_dsl import connections
import datetime
import json

import configparser,os

FILE_DIR = os.path.dirname(__file__)
config_ini = configparser.ConfigParser()
config_ini.read(os.path.join(FILE_DIR,"config.ini"))
config_ini_database = config_ini["database"]

ELASTICSEARCH_HOST = config_ini_database["ELASTICSEARCH_HOST"]
ELASTICSEARCH_PORT = int(config_ini_database["ELASTICSEARCH_PORT"])
ELASTICSEARCH_TIMEOUT = int(config_ini_database["ELASTICSEARCH_TIMEOUT"])

connections.create_connection(hosts=[{"host":ELASTICSEARCH_HOST,"port":ELASTICSEARCH_PORT}], timeout=ELASTICSEARCH_TIMEOUT)

class Smiles(DocType):

    #不能够分词
    smiles = Text(fields={'raw': Keyword()})
    id_list = Text(fields={'raw': Keyword()})
    fingerprint = Text(analyzer='standard')
    fingerprint_inverted = Text(analyzer='whitespace')
    create_time = Date()

    class Index:
        name = "smiles"

    def save(self,**kwargs):
        self.create_time = datetime.datetime.now()
        return super().save(**kwargs)

    @classmethod
    def indices_delete(cls):
        index=cls._default_index()
        print(cls._get_connection().indices.delete(index=index,ignore=404))

    @classmethod
    def indices_get_mapping(cls):
        index=cls._default_index()
        return cls._get_connection().indices.get_mapping(index="smiles")

    @classmethod
    def count(cls):
        return cls._get_connection().count()

if __name__ == "__main__":
    #Smiles.indices_delete()
    #"""
    Smiles.init()

    with open ("/home/zhaodachuan/elasticsearch_data.txt") as f:
        f.seek(0,0)
        line = f.readline()
        count_ = 0
        while(line):
            count_ = count_ + 1
            if count_ % 100 == 0:
                print(str(count_*100) )
            doc = json.loads(line.strip())
            #print(doc)
            smiles = Smiles(meta={"id":" ".join(doc["id_list"])},smiles=doc["smiles"],id_list=" ".join(doc["id_list"]),fingerprint=doc["fingerprint"],fingerprint_inverted=" ".join([str(v) for v in doc["fingerprint_inverted_list"]]))
            smiles.save()
            id_ = " ".join(doc["id_list"])
            line = f.readline()
        #fingerprint_inverted = "1 33 80 140 171 205 237 255 317 356 378 392 403 431 643 648 650 715 753 759 807 812 820 835 838 893 908 932 935 939 1017"
        #result_list = Smiles.search()[0:10].filter().query('match',fingerprint_inverted=fingerprint_inverted)
        #for post in result_list:
        #    print(post.meta.score,post.fingerprint_inverted)
    #"""
