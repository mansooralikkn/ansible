#!/usr/bin/python
try:
	import boto3
        Has_boto3 = True
except ImportError:
        Has_boto3 = False
try:       
	import requests
        Has_request = True
except ImportError:
        Has_request = False
try:
	import re
        has_re = True
except ImportError:
        has_re = False
try:

	from bs4 import BeautifulSoup
        has_bs4 = True
except ImportError:
        has_bs4 = False
from ansible.module_utils.basic import AnsibleModule
 
region={ 'NO': 4, 'EU': 5, 'AU': 6, 'LA': 7 }
ec2 = boto3.resource('ec2')
class NodepingSgCompare:
    
	def __init__(self,noderegion,sgid):
           self.noderegion = noderegion
           self.sgid = sgid
           self.rmlist= []
            
        
    	def nodeRegionid(self):
           nregion=region[self.noderegion]
           return nregion
    	def ipExternal(self):
	   nregion=self.nodeRegionid()
	   page= requests.get('https://nodeping.com/faq')
           soup = BeautifulSoup(page.content, 'html.parser')
           s = soup.findAll('ul')[nregion].get_text()
           ip=re.findall( r'[0-9]+(?:\.[0-9]+){3}', s)

           return ip
    	def ipSg(self):
           sg = ec2.SecurityGroup(self.sgid)
           ip=[x['CidrIp'].split('/')[0] for x in sg.ip_permissions[0]['IpRanges']]
 	
           return ip
    
    	def ipCompare(self):
           self.rmlist=[]
           self.ipx=[x.encode("utf-8") for x in self.ipExternal()]
           self.ipsg=self.ipSg()
           for x in self.ipsg:
              if x in self.ipx:
              	pass 
              else:
              	self.rmlist.append(x+'/32')

           return self.rmlist
def main():
   module = AnsibleModule(
        # not checking because of daisy chain to file module
        argument_spec = dict(
            SgGrp               = dict(required=True, type='str'),
            FromPort = dict(required=False,type='int'),  # used to handle 'dest is a directory' via template, a slight hack
            Noderegion        = dict(required=True, type='str' ),
            toPort              = dict(required=False, type='int'),
            lists              = dict(required=False, type='list'),
        ),
        add_file_common_args=True,
        supports_check_mode=True,
        )

   SgGrp = module.params['SgGrp']
   FromPort= module.params['FromPort']
   Noderegion= module.params['Noderegion']
   toPort= module.params['toPort']

   nodepingip=[x.encode("utf-8") for x in NodepingSgCompare(Noderegion,SgGrp).ipExternal()]
   nodeips=[x+"/32" for x in nodepingip]
   ipcompare=NodepingSgCompare(Noderegion, SgGrp).ipCompare()
   lists=ipcompare
#removing unknown IPs
   sg = ec2.SecurityGroup(SgGrp)
   for ip in ipcompare:
   	sg.revoke_ingress(IpProtocol="tcp", CidrIp=ip, FromPort=FromPort, ToPort=toPort)
#adding nodepingIPs
   
   for ip in nodeips:
        sg.authorize_ingress(IpProtocol="tcp", CidrIp=ip, FromPort=FromPort, ToPort=toPort)
   module.exit_json(changed='changed')
if __name__ == '__main__':

   main()
#sgip= NodepingSgCompare('NO','sg-99ec01e0').ipSg()
#ipdiff= NodepingSgCompare('NO','sg-99ec01e0').ipCompare()

#print set(IPS).intersection(ipdiff)
                               

            
            

