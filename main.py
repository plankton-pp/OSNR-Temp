from time import sleep
import requests
import base64
from bs4 import BeautifulSoup
import json
from multiprocessing import Pool,freeze_support
import pandas as pd
import datetime
import time
import random
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from os import path
import re
# Custom Lib
import db
# config pandas 
pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)
pd.set_option('max_colwidth', None)

class Nfm_t():
    def __init__(self,domain,username,password,address) -> None:        
        self.domain = domain
        self.__username = username
        self.__password = password
        self.token = ""
        self.address = address
        self.session=requests.Session()
        self.ServerIP=f'https://{address}'
        self.count_links = ()

    def get_token(self):
        return self.token
    
    def set_token(self,token_string):
        # print("set: ", str(token_string))
        self.token = str(token_string)

    def get_server_token(self):
        url = f"https://{self.address}/rest-gateway/rest/api/v1/auth/token"
        credential = "{}:{}".format(self.__username, self.__password)
        credential_bytes = credential.encode('ascii')
        base64_bytes = base64.b64encode(credential_bytes)
        base64_credential = base64_bytes.decode('ascii')

        payload = json.dumps({
            "grant_type": "client_credentials"
        })
        headers = {
            'Authorization': 'Basic {}'.format(base64_credential),
            'Content-Type': 'application/json',
            'Host': f"{self.address}:8443"
        }

        response = requests.request(
            "POST", url, headers=headers, data=payload, verify=False)

        if "error" in response.json():
            # print("URL: ", url)
            # print("TOKEN: ERROR")
            return False
        else:
            # print("URL: ", url)
            # print("TOKEN: ",response.json())
            self.token = response.json()["access_token"]
            return response.json()

    def auth_19_2(self):
        url = f"https://{self.address}:8443/oms1350/data/npr/nodes"
        headers = {
            'Content-Type': 'application/json/*',
        }
        self.session.headers.update(headers)
        res = self.session.get( url, timeout=500, verify=False)
        try:
            soup = BeautifulSoup(res.text, "html.parser")
            dt = soup.find("div", id='execution')
            execution = dt['value']
            geolocation = ''
            url = f"https://{self.address}/cas/login?username={self.__username}&password={self.__password}&execution={execution}&_eventId=submit&geolocation={geolocation}"       
            res = self.session.post(url, timeout=500, verify=False)
        except:
            pass

        if res.ok:
            headers = {
            'Content-Type': 'application/json',
            }
            self.session.headers.update(headers)
            print(f"[{self.domain}]:[Auth_19.2] Pass")
            return 0
        else:
            headers = {
            'Authorization': 'Bearer {}'.format(self.token),
            'Content-Type': 'application/json/*',
            'Host': f"{self.address}:8443",
            'Connection': 'keep-alive'
            }
            self.session.headers.update(headers)
            
            print(f"[{self.domain}]:[Auth_19.2] Failed")
            return 1

    def auth_21_4(self):

        url = f"https://{self.address}/rest-gateway/rest/api/v1/location/services"
        headers = {
            'Authorization': 'Bearer {}'.format(self.token),
            'Content-Type': 'application/json',
            'Host': f"{self.address}:8443",
            'Connection': 'keep-alive'
        }
        self.session.headers.update(headers)
        res = self.session.get( url, timeout=500, verify=False)
        # print(res.json())
        if res.ok:
            headers = {
            'Content-Type': 'application/json',
            }
            self.session.headers.update(headers)
            print(f"[{self.domain}]:[Auth_21.4] Pass")
            print(self.session.headers)
            return 0
        else:
            headers = {
            'Authorization': 'Bearer {}'.format(self.token),
            'Content-Type': 'application/json/*',
            'Host': f"{self.address}:8443",
            'Connection': 'keep-alive'
            }
            self.session.headers.update(headers)
            print(f"[{self.domain}]:[Auth_21.4] Failed")
            return 1

    def get_physicalConns(self):
        url=f'{self.ServerIP}:8443/oms1350/data/npr/physicalConns/'
        res = self.session.get(url, timeout=500, verify=False)
        print("Physical Access: ", self.token)
        id_fibers={}
        if not res.ok:
            print("Physical Conn Status: Failed")
            return 1
        else:
            print("Physical Conn Status: Pass")
            for i in res.json():
                id=i['id']
                id_fibers[id]=i['guiLabel']
            self.id_fibers=id_fibers
            return id_fibers

    def get_trails_data(self,domain):
        url=f'{self.ServerIP}:8443/oms1350/data/npr/trails/'
        res = self.session.get(url, timeout=500, verify=False)
        result=[]
        if not res.ok:
            return 1
        else:
            self.trails = res.json()
            self.ids =[]
            self.endToEndOtnTrailIds = []
            self.endToEndOtnTrailLabel = []
            idx = 0
            for trail in self.trails[:]:
                self.ids.append( trail['id'])
                self.endToEndOtnTrailIds.append( trail['endToEndOtnTrailId'])
                self.endToEndOtnTrailLabel.append( trail['endToEndOtnTrailLabel'])
                print("ID:: ",idx,self.endToEndOtnTrailLabel[idx])
                result.append((self.endToEndOtnTrailIds[idx],self.ids[idx],self.endToEndOtnTrailLabel))
                idx += 1
            if len(self.endToEndOtnTrailIds):
                print(f"\n\n[{domain}]:[GET_trails] Pass")
                self.total_links=len(self.endToEndOtnTrailIds)
                return result
            else:
                print(f"[{domain}]:[GET_trails] Fail")
                return 1

    def get_nominalRoute(self,id):
        nom_route=[]
        url = f"{self.ServerIP}:8443/oms1350/data/npr/trails/{id}/nominalRoute"
        nominalRoute = self.session.get(url,  timeout=500,verify=False)
        for ele in nominalRoute.json():
            if  ele['type'] == 'RouteComponentType_omsLink':
                userLabel=ele['userLabel'][0:-2]
                for key, value in self.id_fibers.items():
                    if value==userLabel:
                        nom_route.append(key)   
        #print(nom_route) 
        return nom_route

    def get_currentRoute(self,id):
        curr_route=[]
        url = f"{self.ServerIP}:8443/oms1350/data/npr/trails/{id}/currentRoute"
        currentRoute = self.session.get(url , timeout=500,verify=False)
        for ele in currentRoute.json():
            if  ele['type'] == 'RouteComponentType_omsLink':
                userLabel=ele['userLabel'][0:-2]
                for key, value in self.id_fibers.items():
                    if value==userLabel:
                        curr_route.append(key)

        # Check Status this link   
        for path in currentRoute.json()[:-1]:
            if path["routeRole"] != "RouteRole_nominal":
                print(f'[{self.domain}][id:{id}] Re-Route StatusLable: {path["routeRole"]}')
                break

        return curr_route

    def get_layout(self,endToEndOtnTrailId):
        url = f"{self.ServerIP}:8443/oms1350/data/otn/connection/{endToEndOtnTrailId}/wlt2/layout"
        layout = self.session.get(url, timeout=500, verify=False)
        body_layout2 = layout.json()
        otuTrailId = []
        startingNe = []
        oduNcId = []
        IdList = []
        connectionName = body_layout2['connectionName']
        for Ne in body_layout2['serviceAZ']:
            if Ne['otu'] != None:
                otu_Layout = Ne['otu']
                otuTrailId.append(otu_Layout['otuTrailId'])
                startingNe.append(otu_Layout['otuStartingNe'])
                oduNcId.append(otu_Layout['oduNcId'])
                IdList.append(otu_Layout['currentRouteIdList'])

        return otuTrailId, startingNe, oduNcId, IdList, connectionName

    def get_layout_option(self,otuTrailId, startingNe, oduNcId, IdList):
        try:
            url = f'{self.ServerIP}:8443/oms1350/data/otn/connection/{otuTrailId}/wlt2/layout?startingNe={requests.utils.quote(startingNe)}&oduNcId={oduNcId}&currentRouteIdList={IdList}'
            # print("Layout Option URL: ", url)
            res = self.session.get(url,  timeout=1000, verify=False)
            return res.json()
        except:
            return "Failed"

    def find_name_regex(self,connName):
        connName = str(connName).replace(" ","")
        src_ne_regex = ''
        dst_ne_regex = ''
        try :
            # print(connName)
            #regular expression chopping text to short term
            _regex_src = re.findall(r'(CH\d{4}\D)(\w*\D*\d[\/|\#]|\w*\D*\-\d*|\w*\D{2}\w*_\d)',connName)
            src_ne_regex = str(_regex_src[0][1]).replace("/","").replace("#","")
            
            #regular expression chopping text to short term
            _regex_dst1 = re.findall(r'(\_TO\_\w*|L\d+[\)|\_]+\d{4}\w{3}\w*|L\d\_\w*\D\w*\D\d*|L\d\-CH\d\_\w*\-\w*\-\d*)',connName)
            _regex_dst2 = str(_regex_dst1[len(_regex_dst1)-1])

            #regular expression chopping text from short term to usable text
            _regex_dst3 = re.findall(r'(\_\d{4}\w*|\_[A-Z]{3}\_\d*|\_\w{3}\d*\-\w{3}\-\d{2}|\_[A-Z]{3}\d*\w[\_\d|\d])',_regex_dst2)
            dst_ne_regex = _regex_dst3[0][1:]

        except:
            print("error: ",connName)
        return src_ne_regex, dst_ne_regex
    
    def get_osnr_az(self,otuTrailId,current_layout):
        # https://172.29.176.8:8443/oms1350/data/otn/connection/XXXXX/wlt2/power
        # url = f'{self.ServerIP}:8443/oms1350/data/otn/connection/{otuTrailId}/wlt2/service/power/AZ'
        url = f'{self.ServerIP}:8443/oms1350/data/otn/connection/{otuTrailId}/wlt2/power'
        print("Power AZ: ",url)
        # az = self.session.post(url, json=current_layout, timeout=1000, verify=False)
        az = self.reload_API(url,json=current_layout,count=5)
        src_ne=''
        dst_ne=''

        src_card_az = ''
        src_osnr_az = 0
        dst_card_az = ''
        dst_osnr_az = 0

        rate = ''
        connectionName = ''

        if not az:
            return None , None, src_ne , dst_ne ,src_card_az , dst_card_az , src_osnr_az , dst_osnr_az
        # f = open("test.json", "w")
        # f.writelines(json.dumps(az,indent=4))
        # f.close()
        else:
            for index,item in enumerate(az["serviceAZ"]):

                if index==0:
                    src_ne=item['ne']['neName']
                else:
                    dst_ne=item['ne']['neName']

                for tp in item['ne']['tp']:

                    if src_card_az:
                        dst_card_az = tp['cardName']
                    else:
                        src_card_az = tp['cardName']

                    if tp['power']['osnrValue']:

                        if src_osnr_az:
                            dst_osnr_az = tp['power']['osnrValue']
                        else:
                            src_osnr_az = tp['power']['osnrValue']

                # fixbug don't value in Des_NE
                if az["serviceAZ"][0]==item and src_osnr_az==0 :
                    dst_osnr_az='N/A'
                    src_osnr_az='N/A'

            connectionName=az['connectionName']
            rate =az['rate']        
        # print('otuTrailId :',otuTrailId,' AZ', dst_card_az, " OSNR : ", dst_osnr_az)
        if dst_osnr_az==0 or not dst_osnr_az:
            dst_osnr_az='N/A'
            # print('otuTrailId :',otuTrailId,' AZ', dst_card_az, " OSNR : ", dst_osnr_az, "AZ Error")

        

        return connectionName ,rate, src_ne , dst_ne ,src_card_az , dst_card_az , src_osnr_az , dst_osnr_az
    
    def get_osnr_za(self,otuTrailId,current_layout):
        url = f'{self.ServerIP}:8443/oms1350/data/otn/connection/{otuTrailId}/wlt2/service/power/ZA'
        # za =  self.session.post(url, json=current_layout, timeout=1000, verify=False)
        za = self.reload_API(url,json=current_layout,count=5)
        # f = open("test1.json", "w")
        # f.writelines(json.dumps(za,indent=4))
        # f.close()
        src_card_za = ''
        src_osnr_za = 0
        dst_card_za = ''
        dst_osnr_za = 0
        if not za:
            return src_card_za, dst_card_za, src_osnr_za , src_osnr_za

        for item in za["serviceZA"]:
            for tp in item['ne']['tp']:

                if dst_card_za:
                    dst_card_za = tp['cardName']
                else:
                    src_card_za = tp['cardName']

                if tp['power']['osnrValue']:
                    if dst_osnr_za:
                        src_osnr_za = tp['power']['osnrValue']
                    else:
                        dst_osnr_za = tp['power']['osnrValue']                 
                
                if tp['power']['osnrValue']:
                    if dst_osnr_za:
                        src_osnr_za = tp['power']['osnrValue']
                    else:
                        dst_osnr_za = tp['power']['osnrValue'] 

            # fixbug don't value in Des_NE
            if za["serviceZA"][0]==item and dst_osnr_za==0 :
                dst_osnr_za='N/A'
                src_osnr_za='N/A'

        # print('otuTrailId :',otuTrailId,' ZA :', src_card_za, " OSNR : ", dst_osnr_za)

        return src_card_za, dst_card_za, src_osnr_za , dst_osnr_za

    def get_osnr_trails(self,param):
        endToEndOtnTrailId , id ,endToEndOtnTrailLabel = param
        try:
            nom_route=self.get_nominalRoute(id)
            curr_route=self.get_currentRoute(id)
        except:
            print("Route:: Error")
            return f"ERROR {id}"

        try:
            otuTrailId, startingNe, oduNcId, IdList, connectionName  = self.get_layout(endToEndOtnTrailId)
        except:
            print("Layout:: Error")
            return f"ERROR {id}"

        # try:
        #     print("endToEndOtnTrailId", endToEndOtnTrailId)
        #     print("id",id)
        #     print("hop_length: ", len(startingNe))
        #     print("otuTrailId,  ",  otuTrailId)
        #     print("startingNe,  ",  startingNe)
        #     print( "oduNcId,  ",  oduNcId)
        #     print("idList,  ",  IdList)
        #     print("nominal_route",  nom_route)
        #     print("current_route",  curr_route)
        # except:
        #     print("PrintLine:: Error")

        # try:
        #     current_layout = self.get_layout_option(otuTrailId[0], startingNe[0],oduNcId[0], IdList[0])
        #     print("Layout Option:: ", current_layout)
        # except:
        #     print("Layout Option:: Failed")
        #option 
        return_val = []
        return_rate = []
        return_src_ne = []
        return_dst_ne = []
        return_src_card_az = []
        return_dst_card_az = []
        return_osnr_src_az = []
        return_osnr_dst_az = []

        return_src_card_za = []
        return_dst_card_za = []
        return_osnr_src_za = []
        return_osnr_dst_za = []
        return_connection_name = ""


        for index in range(len(startingNe)):
            try:
                current_layout = self.get_layout_option(otuTrailId[index], startingNe[index],oduNcId[index], IdList[index])
                # print("Current Layout Option Index:: ",index+1)
                # print("Params: ", otuTrailId[index], startingNe[index],oduNcId[index], IdList[index])
                # print("current_layout: Pass")
                # print("Current Layout:: ",current_layout)
                src_ne_regex, dst_ne_regex = self.find_name_regex(current_layout['connectionName'])
                print("Src/Dst :: ", src_ne_regex," : ", dst_ne_regex)
            except:
                # print("Params: ", otuTrailId[index], startingNe[index],oduNcId[index], IdList[index])
                print("current_layout: Error")

            try:
                connectionName , rate ,src_ne , dst_ne ,src_card_az , dst_card_az , src_osnr_az , dst_osnr_az = self.get_osnr_az(otuTrailId[index], current_layout)
                return_connection_name = connectionName
                print("Power AZ: ",otuTrailId[index], connectionName , rate ,src_ne , dst_ne ,src_card_az , dst_card_az , src_osnr_az , dst_osnr_az)   
            except:
                print("Power AZ: Error")

            try:
                src_card_za, dst_card_za, src_osnr_za , dst_osnr_za = self.get_osnr_za(otuTrailId[index],current_layout)
                # print("Power ZA: ",src_card_za, dst_card_za, src_osnr_za , dst_osnr_za)
            except:
                print("Power ZA: Error")
            
            try:
                return_rate.append(rate)
            except:
                return_rate.append(None)
            return_src_ne.append(src_ne)
            return_dst_ne.append(dst_ne)

            return_src_card_az.append(src_card_az)
            return_dst_card_az.append(src_card_az)
            return_osnr_src_az.append(src_osnr_az)
            return_osnr_dst_az.append(dst_osnr_az)

            return_src_card_za.append(src_card_za)
            return_dst_card_za.append(dst_card_za)
            return_osnr_src_za.append(src_osnr_za)
            return_osnr_dst_za.append(dst_osnr_za)

        return_val = {
            'id':id,
            'domain':self.domain,
            'endToEndOtnTrailId':endToEndOtnTrailId,
            'endToEndOtnTrailLabel':endToEndOtnTrailLabel,
            'nom_route':nom_route,
            'curr_route' : curr_route,
            'connectionName':return_connection_name,

            'rate':join_array_to_string(return_rate),
            'src_ne':join_array_to_string(return_src_ne),
            'dst_ne':join_array_to_string(return_dst_ne),
            'src_card_az':join_array_to_string(return_src_card_az),
            'dst_card_az':join_array_to_string(return_dst_card_az),
            'src_osnr_az':join_array_to_string(return_osnr_src_az),
            'dst_osnr_az':join_array_to_string(return_osnr_dst_az),
            'src_card_za':join_array_to_string(return_src_card_za),
            'src_osnr_za':join_array_to_string(return_osnr_src_za),
            'dst_card_za':join_array_to_string(return_dst_card_za),
            'dst_osnr_za':join_array_to_string(return_osnr_dst_za),
            }
        #sleep for 10 seconds
        # print("return: ")
        # print(return_val)
        time.sleep(10)
        # print("\r\r\r--------------------------------------------------------------------------------------------")
        return return_val
                
    def reload_API(self,url,json=None,count=5):
        if count==0:
            return None
        else:
            try:
                r1 = random.randint(3, 10)
                sleep(r1)
                res = self.session.post(url, json=json, timeout=600, verify=False)
                if not res.ok:
                    raise Exception("Sorry, Data don't resposne")
                return res.json()
            except:
                self.reload_API(url,json,count-1)
    
# END CLASS

#Start token verification
def get_time_now():
 return int(time.time()) 

def cal_expired_time(exp_seconds):
    return get_time_now()+exp_seconds

def check_existing_file(filepath):
    return path.exists(filepath)

def write_token(domain,software_version,expired_time,nfmt_object):
    # token export
    token = nfmt_object.get_server_token()
    token_data = {
        "domain":domain,
        "software_version": software_version,
        "token": token['access_token'],
        "begin": expired_time-3600,
        "expired": expired_time
    }

    # Serializing to json object
    # ident is mean spacing 4 characters from left bound
    json_object = json.dumps(token_data, indent=4)

    # Writing to json file
    with open(domain+"_"+software_version+"_token_data.json", "w") as outfile:
        outfile.write(json_object)


def read_token(filepath):
    # Opening JSON file
    with open(filepath, 'r') as openfile:
    
        # Reading from json file
        return json.load(openfile)

def check_token_expired(filepath):
    token_json = read_token(filepath)
    token_exp = int(token_json['expired'])
    now = get_time_now()

    #compare between currentime and token expire time
    two_mins = 120 #seconds
    print("-> Token Status Expire: ",int(token_exp)<int(now-two_mins))
    return int(token_exp)<int(now-two_mins)
    

def verify_token(domain,software_version,nfmt_object):
    one_hour = 3600 #seconds
    filepath = domain+"_"+software_version+"_token_data.json"
    now = get_time_now()
    token_exp = 0
    # check existing token data file
    if not check_existing_file(filepath) or check_token_expired(filepath):  #read if file exist
        print("-> Status: Write New Token")
        token_exp = now+3600
        write_token(domain,software_version,cal_expired_time(one_hour),nfmt_object)
        # print("NFMT: ", nfmt_object.token)

    #create token data file
    else:
        print("-> Status: Read Token")
        token_json = read_token(filepath)
        nfmt_object.set_token(token_json['token'])
        token_exp = int(token_json['expired'])

    print("******************* Verify Exp **************************")
    print("Current Unix: ", now)
    print("Expire Unix: ",token_exp)
    print("Current Human: ",time.strftime("%D %H:%M", time.localtime(now)))
    print("Expire Human: ",time.strftime("%D %H:%M", time.localtime(token_exp)))
    print("Remain: ", "{:.2f}".format(abs(token_exp-now)/60)," mins")
    print("*********************************************************")
#End token verification

def find_result(domain,username, password, version,address):
    global Ex_osnr_id
    global Ex_osnr_record
    global Ex_osnr_card_received

    print("Connect to ", address)
    print("----------------------------------------------------------\r\r")
    nfm_t=Nfm_t(domain,username, password, address)
    verify_token(domain, version, nfm_t)
    # Authen 
    if version=='19.2':
        nfm_t.auth_19_2()
    if version=='21.4':
        nfm_t.auth_21_4()

    #Get Physical Connection
    id_fibers=nfm_t.get_physicalConns()
    if(id_fibers==1):
        raise ValueError("Physical Connections cannot retrieve from ", address)
    # else:
        # print(id_fibers)

    print(f"[{domain}]:[Get OSNR]")
    with Pool(processes=15) as pool:
        results = pool.map(nfm_t.get_osnr_trails, nfm_t.get_trails_data(domain))
    
    results = [x for x in results if x is not None]
    Ex_osnr_record.reset_index(drop=True)


    for ele in results:
        if ele['domain'] is not None and ele['id'] is not None and ele['dst_osnr_az'] is not None and ele['dst_osnr_za'] is not None and ele['curr_route'] is not None:
            # print([ ele['id'], ele['domain'], datetime.date.today(), ele['dst_osnr_az'], ele['dst_osnr_za'], str(ele['curr_route'])])
            try:
                Ex_osnr_record.loc[len(Ex_osnr_record)]=[ ele['id'], ele['domain'], datetime.date.today(), ele['dst_osnr_az'], ele['dst_osnr_za'], str(ele['curr_route'])]
            except Exception as e:
                print('Error Record Adding: Ex_osnr_record')
                print("Domain: ", ele['domain'])
                print("Error massage: ",e)
                continue

            try:
                Ex_osnr_id.loc[len(Ex_osnr_id)]=[ele['id'], ele['domain'], ele['endToEndOtnTrailId'], ele['connectionName'], ele['src_card_az'], ele['rate'] , ele['src_ne'] , ele['dst_ne'] , str(ele['nom_route']) ]
            except Exception as e:
                print('Error Record Adding: Ex_osnr_id')
                print("Domain: ", ele['domain'])
                print("Error massage: ",e)
                continue
        else:
            continue   

    Ex_osnr_id=Ex_osnr_id.drop_duplicates(['id','domain'],keep= 'last')
    Ex_osnr_id.reset_index(drop=True)
    Ex_osnr_record=Ex_osnr_record.drop_duplicates(['id','domain','date'],keep= 'last')

def join_array_to_string(data_array):
    return ','.join(str(x) for x in data_array)

if __name__=="__main__":
    freeze_support()
    global Ex_osnr_id
    global Ex_osnr_record
    global Ex_osnr_card_received

    try:
        Ex_osnr_id = pd.read_sql_table('ex_osnr_id', db.engine)
    except:
        cols_id= ['id','domain','endToEndOtnTrailId','endToEndOtnTrailLabel','card_type','rate','src_ne','dst_ne','nom_route']
        Ex_osnr_id=pd.DataFrame(columns=cols_id)

    try:
        Ex_osnr_record = pd.read_sql_table('ex_osnr_record', db.engine)
        Ex_osnr_record = Ex_osnr_record.set_index('index')
        # print('Pull database')
    except:        
        cols_id= ['id','domain','date','az_osnr_value','za_osnr_value','curr_route',]        
        Ex_osnr_record=pd.DataFrame(columns=cols_id)

    try:
        Ex_osnr_card_received = pd.read_sql_table('ex_osnr_card_received', db.engine)
        Ex_osnr_card_received=Ex_osnr_card_received.set_index('index')
    except:        
        cols_id= ['card_type','rate','received_osnr']
        Ex_osnr_card_received =pd.DataFrame(columns=cols_id)

    #profile config
    domain = ['upper','lower']
    username = 'osphachar'
    nfmt_password = 'Dtacequipment1150'
    address = ['10.13.51.8','172.29.176.8']
    software_version = ['19.2','21.4']
    write_to_db = False
    calling_data = True

    #start data collecting -------------------------------------------------------------------------   
    print("\t\t    {} | {}  | {} | {}".format("Domain","Username", "S -V","IP Address")) 
    for idx,sub_domain in enumerate(domain):
        if calling_data and sub_domain=='lower':
            try:
                print("Real calling from => {} | {} | {} | {}".format(sub_domain,username, software_version[idx],address[idx]))
                results = find_result(sub_domain, username, nfmt_password, software_version[idx], address[idx])
            except:
                raise 'Connection failed for {} :: {}'.format(sub_domain,address[idx])
        else:
            print("Demo calling from => {} | {} | {} | {}".format(sub_domain,username, software_version[idx],address[idx]))

    #end collecting -------------------------------------------------------------------------

    # # write DB
    if write_to_db:
        print("write to db:: writing . . .")
        Ex_osnr_id.to_sql('ex_osnr_id', db.engine, if_exists='replace', index = False)
    
        Ex_osnr_record=Ex_osnr_record.drop_duplicates(['domain','id','date'],keep= 'last')
        Ex_osnr_record=Ex_osnr_record.reset_index(drop=True)
        Ex_osnr_record.to_sql('ex_osnr_record', db.engine, if_exists='replace', index = True)

        Ex_osnr_card_received=Ex_osnr_card_received.drop_duplicates(['card_type','rate',],keep= 'last')
        Ex_osnr_card_received=Ex_osnr_card_received.reset_index(drop=True)
        Ex_osnr_card_received.to_sql('ex_osnr_card_received', db.engine, if_exists='replace', index = True)
        
        # # Re-Date Format
        Ex_osnr_record = pd.read_sql_table('ex_osnr_record', db.engine)
        Ex_osnr_record=Ex_osnr_record.drop_duplicates(['domain','id','date'],keep= 'last')
        Ex_osnr_record = Ex_osnr_record.set_index('index')
        Ex_osnr_record=Ex_osnr_record.reset_index(drop=True)
        Ex_osnr_record.to_sql('ex_osnr_record', db.engine, if_exists='replace', index = True)
        print("done!")
    else:
        print("write to db:: not available")

        # print(Ex_osnr_id)
        # print(Ex_osnr_record)
        # print(Ex_osnr_card_received)