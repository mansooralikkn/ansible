#!/usr/bin/python
import boto3
import requests
import re
from bs4 import BeautifulSoup

from ansible.module_utils.basic import AnsibleModule
    
ec2 = boto3.resource('ec2')
def ipExternal():
           
    nregion=4
    page= requests.get('https://nodeping.com/faq')
    soup = BeautifulSoup(page.content, 'html.parser')
    s= soup.findAll('ul')[nregion].get_text()
    ip=re.findall( r'[0-9]+(?:\.[0-9]+){3}', s)
    return ip

def ipSg(sgid):
            
    sg = ec2.SecurityGroup(sgid)
    ip=[x['CidrIp'].split('/')[0] for x in sg.ip_permissions[0]['IpRanges']]
    return ip
    
def ipCompare(ip1,ip2):
    rmlist=[]
    havelist=[]
    for x in ip1:
       if x in ip2:
           havelist.append(x+'/32')
       else:
           rmlist.append(x+'/32')

    return (rmlist,havelist)

#IPS=[x.encode("utf-8") for x in NodepingSgCompare('NO',21321).ipExternal()]
#sgip= NodepingSgCompare('NO','sg-99ec01e0').ipSg()
#ipdiff= NodepingSgCompare('NO','sg-99ec01e0').ipCompare()

#print sgip,IPS,ipdiff
#print set(IPS).intersection(ipdiff)
                               

            
            
def main():
    module = AnsibleModule(
        # not checking because of daisy chain to file module
        argument_spec = dict(
            sgip               = dict(required=True, type='str'),
            FromPort = dict(required=False, type='int', force = dict(type='int', default=80)),  
            toPort              = dict(required=False, type='int', force = dict(type='int', default=80)),
        ),
        add_file_common_args=True,
        supports_check_mode=True,
        )
    sgip = module.params['sgip']
    FromPort= module.params['FromPort']
    toPort= module.params['toPort']
    ec2 = boto3.resource('ec2')
    sg = ec2.SecurityGroup(sgip)
    ipsg=ipSg(sgip)
    ndip=[x.encode("utf-8") for x in ipExternal()]
    rmiplist=ipCompare(ipsg,ndip)
    addip=ipCompare(ndip,ipsg)
    rmvlist=rmiplist[0]
    addipv=addip[0]
#Removing old nodepingIPs
    for ip in rmvlist:
   	sg.revoke_ingress(IpProtocol="tcp", CidrIp=ip, FromPort=FromPort, ToPort=toPort)
#adding new nodeping IPs
    for ip in addipv:
   	sg.authorize_ingress(IpProtocol="tcp", CidrIp=ip, FromPort=FromPort, ToPort=toPort)

    module.exit_json(changed='changed')
if __name__ == '__main__':
    main()


