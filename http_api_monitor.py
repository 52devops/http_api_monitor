from elasticsearch import Elasticsearch
import datetime,time,os,yaml,requests,json,logging,socket
config_file=os.path.join(os.path.dirname(__file__),"http_api_monitor.yml")
year=str(datetime.datetime.now().year)
month=str(datetime.datetime.now().month).zfill(2)
day=str(datetime.datetime.now().day).zfill(2)
log = logging.getLogger()
logging.basicConfig(level=logging.ERROR)
ts=int(time.time())
with open(config_file,'r') as f:
    r=yaml.load(f.read())
    hosts=r.get("es_cluster_host")
    max_request_time=r.get("max_request_time")
    exclude_fields=r.get("exclude_fields")
    max_response_time=r.get("max_response_time")
    index_list=r.get("index")
    falcon_endpoint=r.get("falcon_endpoint")
    statuses=r.get("statuses")


query={
    "query" : {
        "bool" :{
        "filter" : {
        "range" : {
          "@timestamp" : {
            "gte" : "now-1m",
            "lte" : "now"
            }
          }
        }
      }
    }
}
setting_body={
    "index" : {
        "max_result_window" : 100000
    }
}
def analyse_data(doc_list):
    doc_dict={}
    for doc in doc_list:
        doc_dict[doc]=doc_list.count(doc)
    return doc_dict



class ElasticSearchClass(object):
    def __init__(self,index,query):
        self.hosts = hosts
        self.index=index
        self.query=query
        self.es = Elasticsearch(hosts=self.hosts)
    def increase_max_result_window(self):
        if  self.es.indices.get_settings(index=self.index).get(self.index).get('settings').get('index').get('max_result_window')  != 100000:
            r = self.es.indices.put_settings(index=self.index,body=setting_body)
            return r
    def get_docs(self):
        docs = self.es.search(body=self.query, index=self.index, _source_exclude=exclude_fields, size=20000)
        self.docs=docs
        return self.docs

    @property
    def get_request_time(self):
        path_list=[]
        try:
            r = self.docs.get("_shards").get('failed')
            if r != 0:
                print("connect to elasticsearch failed")
            else:
                R = self.docs.get('hits').get('hits')
                for doc in R:
                    request_time=doc.get('_source').get('request_time')
                    path=doc.get('_source').get("path")
                    if request_time != "-" and request_time != None and  path != "-" and path  != None and path != "":
                        request_time=float(request_time)
                        if request_time >= max_request_time:
                            path_list.append(path)
            return analyse_data(path_list)
        except Exception as  e:
            print(e)

    @property
    def get_response_time(self):
        path_list=[]
        try:
            r = self.docs.get("_shards").get('failed')
            if r != 0:
                print("connect to elasticsearch failed")
            else:
                R = self.docs.get('hits').get('hits')
                for doc in R:
                    response_time=doc.get('_source').get('response_time')
                    path=doc.get('_source').get("path")
                    if response_time != "-" and response_time !=None and  path != "-" and path  != None and path != "" :
                        response_time=float(response_time)
                        if response_time >= max_response_time:
                            path_list.append(path)
            return analyse_data(path_list)
        except Exception as  e:
            print(e)
    @property
    def get_status(self):
        path_list_404 = ["404"]
        path_list_408 = ["408"]
        path_list_499 = ["499"]
        path_list_500 = ["500"]
        path_list_502 = ["502"]
        path_list_504 = ["504"]
        try:
            R = self.docs.get("_shards").get('failed')
            if R != 0:
                print("connect to elasticsearch failed")
            else:
                R = self.docs.get('hits').get('hits')
                for doc in R:
                    path=doc.get('_source').get('path')
                    status=doc.get('_source').get('status')
                    status=int(status)
                    if status != "-" and status  != None and status != "" and  path != "-" and path  != None and path != "" :
                        if status == 404:
                            path_list_404.append(path)
                        elif status== 408:
                            path_list_408.append(path)
                        elif status == 499:
                            path_list_499.append(path)
                        elif status == 500:
                            path_list_500.append(path)
                        elif status == 502:
                            path_list_502.append(path)
                        elif status == 504:
                            path_list_504.append(path)
                        else:
                            continue
            return analyse_data(path_list_404),analyse_data(path_list_408),analyse_data(path_list_499),analyse_data(path_list_500),analyse_data(path_list_502),analyse_data(path_list_504)
        except Exception as  e:
             print(e)

class Falcon_Class(object):
   def push_to_falcon(self,url,payload):
            r=requests.post(url=url,data=json.dumps(payload))
            log.info("Push mertic successfully")
            print(r.text)


def get_playload():
    playload_list = []
    for index in index_list:
        A = ElasticSearchClass(index=index + "-" + year + "." + month + "." + day, query=query)
        A.increase_max_result_window()
        A.get_docs()
        res_request_time = A.get_request_time
        res_response_time = A.get_response_time
        res_status = A.get_status
        for k,v in res_request_time.items():
            tag="api=%s"%k
            playload_list.append({"endpoint": falcon_endpoint,"metric": "api_request_time","timestamp": ts,"step": 60,"value": v,"counterType": "GAUGE","tags": tag})
        for k,v in res_response_time.items():
            tag = "api=%s"%k
            playload_list.append({"endpoint":falcon_endpoint,"metric": "api_response_time","timestamp": ts,"step": 60,"value": v,"counterType": "GAUGE","tags": tag})
        for R in res_status:
            for s in statuses:
                if str(s)  in list(R.keys()):
                    for k,v in R.items():
                        if  str(k) != str(s):
                            tag = "api=%s"%k
                            playload_list.append({"endpoint":falcon_endpoint,"metric": "http_code_"+str(s),"timestamp": ts,"step": 60,"value": v,"counterType": "GAUGE","tags": tag})
    return playload_list

if __name__ == '__main__':
    r=get_playload()
    f=Falcon_Class()
    #hostname=socket.gethostname()
    hostname = "p-awsbj-sqe-kafka-manager-1512296070"
    url = "http://{0}{1}:1988/v1/push".format(hostname, ".mynextev.net")
    f.push_to_falcon(url=url, payload=r)
