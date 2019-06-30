import neomodel,concurrent.futures
import json,logging
import configparser,os
import numpy as np
import concurrent.futures
import sys

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

NEO4J_URL = "bolt://{NEO4J_USERNAME}:{NEO4J_PASSWORD}@{NEO4J_HOST}:{NEO4J_PORT}".format(NEO4J_USERNAME=NEO4J_USERNAME,NEO4J_PASSWORD=NEO4J_PASSWORD,NEO4J_HOST=NEO4J_HOST,NEO4J_PORT=NEO4J_PORT)
neomodel.config.DATABASE_URL = NEO4J_URL
neomodel.db.set_connection(NEO4J_URL)


#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)




class CustomMedicalEntity():

    @staticmethod
    def get_all_name_from_neo4j():
        cypher = "match (entity) return {name:entity.name}"
        #logging.info(cypher)
        data_row_list,column_name_list = neomodel.db.cypher_query(cypher)
        data_row_list = CustomMedicalEntity.to_list(data_row_list)
        return data_row_list


    @staticmethod
    def get_node_obj_by_name(name:str):
        main_node = neomodel.db.cypher_query('match (entity) where entity.name="{name}" return entity'.format(name=name))[0][0][0]
        return main_node

    @staticmethod
    def to_list(data_row_list):
        return [v[0] for v in data_row_list]

    @staticmethod
    def list2frontend_data(res_data_row_list):
        node_list = []
        node_name_set = set()
        link_list = []
        link_source_target_set = set()
        #为空的情况
        if not res_data_row_list:
            return {"node_list":[{}],"link_list":[]}
        for i,v in enumerate(res_data_row_list):
            #添加节点
            if not v["source"] in node_name_set:
                node_name_set.add(v["source"])
                node_list.append({"id":v["source"],"category":v["source_category"]})
            if not v["target"] in node_name_set:
                node_name_set.add(v["target"])
                node_list.append({"id":v["target"],"category":v["target_category"]})
            #添加边
            if (not v["source"]+v["target"] in link_source_target_set) and (not v["target"]+v["source"] in link_source_target_set):
                link_list.append({"source":v["source"],"target":v["target"],"confidence":v["confidence"]})
                link_source_target_set.add(v["source"]+v["target"])
        return {"node_list":node_list,"link_list":link_list}

    @staticmethod
    def cypher_filter_entity_labels(entity_name:str,category_list:list)->str:
        """
        这样子搜索不是最好的办法，会扫描所有的节点，但相信neo4j以后会改好的，参见：
        https://stackoverflow.com/questions/20003769/neo4j-match-multiple-labels-2-or-more
        https://github.com/neo4j/neo4j/issues/5002
        """
        front2backend_dict = {
            "drugs": "DrugsEntity",
            "compound": "CompoundEntity",
            "gene": "GeneEntity",
            "protein": "ProteinEntity",
            "disease": "DiseaseEntity",
            "symptom": "SymptomEntity",
            "organism": "OrganismEntity",
            "anatomy": "AnatomyEntity",
            "equipment": "EquipmentEntity",
            "phenomenon": "PhenomenonEntity"}
        res = []
        for v in category_list:
            res.append(entity_name + ":" + front2backend_dict[v])
        return " OR ".join(res)

    @staticmethod
    def traversal_one_degree(node_name,category_list,top_n=300):
        node_id = CustomMedicalEntity.get_node_obj_by_name(node_name).id
        if len(category_list) < 10:
            cypher = \
                '''
                    MATCH (entity0) WHERE id(entity0)={_id}
                    MATCH (entity0)-[r01]-(entity1)
                    Where ({category_cypher})
                    RETURN {{source:entity0.name,source_category:entity0.category,confidence:r01.confidence,target:entity1.name,target_category:entity1.category}}
                '''.format(_id=node_id,category_cypher=CustomMedicalEntity.cypher_filter_entity_labels("entity1",category_list))
        else:
            cypher = \
                '''
                    MATCH (entity0) WHERE id(entity0)={_id}
                    MATCH (entity0)-[r01]-(entity1)
                    RETURN {{source:entity0.name,source_category:entity0.category,confidence:r01.confidence,target:entity1.name,target_category:entity1.category}}
                '''.format(_id=node_id)
        #logging.info("cypher \n"+cypher )
        data_row_list,column_name_list = neomodel.db.cypher_query(cypher)
        data_row_list = CustomMedicalEntity.to_list(data_row_list)
        logging.debug(data_row_list)
        #为空的情况
        if not data_row_list: return
        confidence_nparray = np.array([v["confidence"] for v in data_row_list],dtype=np.float32)
        if len(confidence_nparray) > top_n:
            top_n_index_nparray = np.argpartition(confidence_nparray, -top_n)[-top_n:]
            res_data_row_list = [data_row_list[i] for i in top_n_index_nparray]
        else:
            res_data_row_list = data_row_list
        return res_data_row_list


    def __init__(self,node_name,category_list,relationship_list,top_n,confidence_list=[0,1]):
        self.node_name = node_name
        self.category_list = category_list
        self.relationship_list = relationship_list
        self.top_n = top_n
        self.confidence_list = confidence_list
        self.executor = concurrent.futures.ThreadPoolExecutor(top_n)


    def get_one_degree_category(self):
        node_name = self.node_name
        cypher = 'match (entity0)-[]-(entity1) where entity0.name="{}" return DISTINCT entity1.category'.format(node_name)
        #logging.info("cypher")
        #logging.info(cypher)
        data_row_list,column_name_list = neomodel.db.cypher_query(cypher)
        #logging.info(data_row_list[0:10])
        data_row_list = CustomMedicalEntity.to_list(data_row_list)
        #logging.info(data_row_list[0:10])
        return data_row_list

    def traversal_by_relationship_list(self):
        node_name = self.node_name
        category_list = self.category_list
        relationship_list = self.relationship_list
        top_n = self.top_n
        if int(relationship_list[1]) == 2:
            one_degree_result = CustomMedicalEntity.traversal_one_degree(node_name,category_list,top_n)
            #one_degree_result为空
            if not one_degree_result:
                node_obj = CustomMedicalEntity.get_node_obj_by_name(node_name)
                return {"node_list":[{"id":node_name,"category":dict(node_obj)["category"]}],"link_list":[]}
            two_degree_result = [self.executor.submit(CustomMedicalEntity.traversal_one_degree,v["target"],category_list,top_n) for v in one_degree_result]
            #第一个0是拿one_degree_result，第二个0是拿一度节点
            two_degree_result = [v.result() for v in two_degree_result]
            for v in two_degree_result:
                one_degree_result.extend(v)
        elif int(relationship_list[1]) == 1:
            one_degree_result = CustomMedicalEntity.traversal_one_degree(node_name,category_list,top_n)

        else:
            return
        #接下来需要处理one_degree_result为空的情况
        if one_degree_result:
            return CustomMedicalEntity.list2frontend_data(one_degree_result)
        else:
            node_obj = CustomMedicalEntity.get_node_obj_by_name(node_name)
            return {"node_list":[{"id":node_name,"category":dict(node_obj)["category"]}],"link_list":[]}

