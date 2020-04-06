import json
import docker
import subprocess
import os
import ipaddress
import sys
import time

sys.path.append('../')
from development.router import RIPRouter
from development.get_ipaddress import *

client = docker.from_env()

# create hosts
def createHosts(hosts):
    # print(hosts)
    hostDict = {}
    for key in hosts:
        hostsContainer = client.containers.run(image=hosts[key]['image_name'], name=key,
                                             command="/bin/bash",
                                             cpuset_cpus="0,1",
                                             cpu_shares=2,
                                             cpu_period=100000,
                                             mem_limit="512m",
                                             network_mode="none",
                                             user="root",
                                             detach=True,
                                             tty=True,
                                             stdin_open=True,
                                             oom_kill_disable=True,
                                             publish_all_ports=True,
                                             privileged=True,
                                             hostname=key
                                             # volumes={"/home/light-travelling/resolv.conf": {'bind': '/etc/resolv.conf','mode': 'rw'}}
                                             )
        hostDict[key] = hostsContainer
    return hostDict
# create switches
def createSwitch(switches):
    for switch in switches:
        # print(switch)
        shell = "sudo ovs-vsctl add-br " + switch
        print(shell)
        ovs_info = subprocess.Popen(shell, shell=True, stdout=subprocess.PIPE)
        ovs_info.wait()
        shell = "sudo ovs-vsctl set bridge " + switch + " stp_enable=true"
        print(shell)
        ovs_info = subprocess.Popen(shell, shell=True, stdout=subprocess.PIPE)
        ovs_info.wait()
# create servers
def createServer(servers):
    serversDict = {}
    for key in servers:
        # apache server
        if "apache" == key:
            for key2 in servers[key]:
                websContainer = client.containers.run(image=servers[key][key2]['image_name'], name=key2,
                                                         network_mode="none",
                                                         detach=True,
                                                         tty=True,
                                                         stdin_open=True,
                                                         oom_kill_disable=True,
                                                         privileged=True,
                                                         hostname=key2
                                                        )
                serversDict[key2] = websContainer
        # streams server
        if "stream" == key:
            print()
        # ftp server
        if "ftp" == key:
            for key2 in servers[key]:
                ftpsContainer = client.containers.run(image=servers[key][key2]['image_name'], name=key2,
                                                         network_mode="none",
                                                         detach=True,
                                                         privileged=True,
                                                         hostname=key2,
                                                         environment=["PASV_ADDRESS_ENABLE=YES"]
                                                      )
                serversDict[key2] = ftpsContainer
        # db server
        if "db" == key:
            for key2 in servers[key]:
                dbsContainer = client.containers.run(image=servers[key][key2]['image_name'], name=key2,
                                                         network_mode="none",
                                                         detach=True,
                                                         privileged=True,
                                                         hostname=key2,
                                                         environment=["MYSQL_ALLOW_EMPTY_PASSWORD=true","MYSQL_ROOT_HOST=%"]
                                                        )
                serversDict[key2] = dbsContainer
        # dnses server
        if "dns" == key:
            # create dnsmasq.conf
            #  get apache object
            webs = servers['apache']

            content = ""
            for web in webs:
                # print(servers['apache'][web]['domainName'])
                if servers['apache'][web]['interfaces'][0]['ip'] != "":
                    getInformation = "address=/" + servers['apache'][web]['domainName'] + "/" + str(servers['apache'][web]['interfaces'][0]['ip']).split('/')[0] + "\n"
                    content = content + getInformation
            # create dns container
            for key2 in servers[key]:
                  # create configure file for every dns server-----dnsmasq.conf
                  dataPath = path + '/dns/' + servers[key][key2]['name']
                  if not os.path.exists(dataPath):
                        os.makedirs(dataPath)
                  fp = open(dataPath + "/dnsmasq.conf", 'w')
                  fp.write(content)
                  dnsContainer = client.containers.run(image=servers[key][key2]['image_name'], name=key2,
                                                     network_mode="none",
                                                     user="root",
                                                     detach=True,
                                                     privileged=True,
                                                     volumes={dataPath + "/dnsmasq.conf":{'bind':'/etc/dnsmasq.conf','mode':'rw'}}
                                                     )
                  serversDict[key2] = dnsContainer
    return serversDict
# create nginx
def createNginxs(nginxs):
    for nginx in nginxs:
        try:
            container = client.containers.run(image="middle_box/nginx", detach=True, name=nginx,
                                              privileged=True,command='/bin/bash', hostname=nginx,
                                              network="none",stdin_open=True, tty=True, oom_kill_disable=True)
        except:
            print("Error to cteate " + nginx)

# create middle_boxes
def createMiddleboxes(middle_boxes):
    # print(middle_boxs)
    middle_boxesDict = {}
    for key in middle_boxes:
        if "nginx" == key:
            # createNginxs(middle_boxes['nginx'])
            for nginx in middle_boxes['nginx']:
                try:
                    container = client.containers.run(image="middle_box/nginx", detach=True, name=nginx,
                                                      privileged=True, command='/bin/bash', hostname=nginx,
                                                      network="none", stdin_open=True, tty=True, oom_kill_disable=True)
                    middle_boxesDict[nginx] = container
                except:
                    print("Error to cteate " + nginx)
    return middle_boxesDict
# create gateway
def createGateway(gateway):
    router_dict = gateway
    if router_dict['subtype'] == 'rip':  # judge the router's subtype(unfinished)
        router = RIPRouter()  # initialize the router
    router.__dict__ = router_dict  # turn the dictionary to object
    router.create()  # create the router without start
    router.startswitch(bool=True)
    if len(router.networks):
        router.manual_config()  # manual mode
    else:
        router.default_config()  # default mode
    # router.enable()  # enable the protocol which the router support
    router.protocolswitch(bool=True)

# ovs link
def ovsLink(net,source,sourceType,target,targetType):
    # source net card name
    fromMeToYou = source + target
    # target net card name
    fromYouToMe = target + source

    if "switch" == sourceType.split('/')[0] and "switch" == targetType.split('/')[0]:
        print("switch-switch")
        subprocess.getstatusoutput('sudo ovs-vsctl add-port ' + source + ' ' + fromMeToYou)
        subprocess.getstatusoutput('sudo ovs-vsctl add-port ' + target + ' ' + fromYouToMe)
        subprocess.getstatusoutput('sudo ovs-vsctl set interface '+fromMeToYou+' type=patch options:peer='+fromYouToMe)
        subprocess.getstatusoutput('sudo ovs-vsctl set interface '+fromYouToMe+' type=patch options:peer='+fromMeToYou)
    elif "host" == sourceType.split('/')[0]:
        if networks[net]['hosts'][source]['interfaces'][0]['ip'] == "":
            shell = 'sudo ovs-docker add-port ' + target + " " + networks[net]['hosts'][source]['interfaces'][0]['name'] + " " + source
            print(shell)
            subprocess.getstatusoutput(shell)
        else:
            shell = 'sudo ovs-docker add-port ' + target + " " + networks[net]['hosts'][source]['interfaces'][0]['name'] + " " + source + " --ipaddress=" + networks[net]['hosts'][source]['interfaces'][0]['ip'] + " --gateway=" + networks[net]['hosts'][source]['interfaces'][0]['gateway']
            print(shell)
            subprocess.getstatusoutput(shell)
    elif "host" == targetType.split('/')[0]:

        if networks[net]['hosts'][target]['interfaces'][0]['ip'] == "":
            shell = 'sudo ovs-docker add-port ' + source + " " + networks[net]['hosts'][target]['interfaces'][0]['name'] + " " + target
            subprocess.getstatusoutput(shell)
        else:
            shell = 'sudo ovs-docker add-port ' + source + " " + networks[net]['hosts'][target]['interfaces'][0]['name'] + " " + target + " --ipaddress=" + networks[net]['hosts'][target]['interfaces'][0]['ip'] + " --gateway=" + networks[net]['hosts'][target]['interfaces'][0]['gateway']
            subprocess.getstatusoutput(shell)
    elif "server" == sourceType.split('/')[0]:
        if "dhcp" == sourceType.split('/')[1]:
            subprocess.getstatusoutput('sudo ip link add ' + source + ' type veth peer name ' + fromYouToMe)
            subprocess.getstatusoutput('sudo ip link set dev ' + source + ' up')
            subprocess.getstatusoutput('sudo ip link set dev ' + fromYouToMe + ' up')
            subprocess.getstatusoutput('sudo ovs-vsctl add-port ' + target + " " + fromYouToMe)
            subprocess.getstatusoutput('sudo ifconfig ' + source + " " + networks[net]['servers']['dhcp'][source]['interfaces'][0]['ip'])
            # create dhcp server
            # create configure file for every dhcp server-----data
            dataPath = path + '/dhcp/' + networks[net]['servers']['dhcp'][source]['name']
            if not os.path.exists(dataPath):
                os.makedirs(dataPath)

            # create ./data/dhcpd.conf
            ip = networks[net]['servers']['dhcp'][source]['interfaces'][0]['ip']
            netmask = str(ipaddress.ip_network(ip,strict=False).netmask)
            subnet = str(ipaddress.ip_network(ip,strict=False)).split('/')[0]
            range = networks[net]['servers']['dhcp'][source]['range'][0] + " " + networks[net]['servers']['dhcp'][source]['range'][1]

            content = "subnet " + subnet + " netmask " + netmask + " {option routers " + \
                      networks[net]['servers']['dhcp'][source]['interfaces'][0][
                          'gateway'] + ";option subnet-mask " + netmask + ";range " + range + ";default-lease-time " + \
                      networks[net]['servers']['dhcp'][source]['default-lease-time'] + ";max-lease-time " + networks[net]['servers']['dhcp'][source][
                          'max-lease-time'] + ";}"

            fp = open(dataPath + "/dhcpd.conf", 'w')
            fp.write(content)
            fp.close()
            # create dhcp container
            dhcpsContainer = client.containers.create(image=networks[net]['servers']['dhcp'][source]['image_name'], name=source,
                                                   network_mode="host",
                                                   detach=True,
                                                   publish_all_ports=True,
                                                   privileged=True,
                                                   volumes={dataPath: {'bind': '/data', 'mode': 'rw'}},
                                                   command=source  # listen the name is "source" net card
                                                   )
            dhcpsContainer.start()
        # other server
        else:
            otherKind  = sourceType.split('/')[1]
            print(otherKind)
            if networks[net]['servers'][otherKind][source]['interfaces'][0]['ip'] == "":
                shell = 'sudo ovs-docker add-port ' + target + " " + networks[net]['servers'][otherKind][source]['interfaces'][0]['name'] + " " + source
                print(shell)
                subprocess.getstatusoutput(shell)
            else:
                shell = 'sudo ovs-docker add-port ' + target + " " + networks[net]['servers'][otherKind][source]['interfaces'][0]['name'] + " " + source + " --ipaddress=" + networks[net]['servers'][otherKind][source]['interfaces'][0]['ip'] + " --gateway=" + networks[net]['servers'][otherKind][source]['interfaces'][0]['gateway']
                print(shell)
                subprocess.getstatusoutput(shell)
    elif "server" == targetType.split('/')[0]:
        if "dhcp" == targetType.split('/')[1]:
            subprocess.getstatusoutput('sudo ip link add ' + target + ' type veth peer name ' + fromMeToYou)
            subprocess.getstatusoutput('sudo ip link set dev ' + target + ' up')
            subprocess.getstatusoutput('sudo ip link set dev ' + fromMeToYou + ' up')
            subprocess.getstatusoutput('sudo ovs-vsctl add-port ' + source + " " + fromMeToYou)
            subprocess.getstatusoutput('sudo ifconfig ' + target + " " + networks[net]['servers']['dhcp'][target]['interfaces'][0]['ip'])
            # create dhcp server
            # create configure file for every dhcp server-----data
            dataPath = path + '/dhcp/' + networks[net]['servers']['dhcp'][target]['name']
            if not os.path.exists(dataPath):
                os.makedirs(dataPath)

            # create ./data/dhcpd.conf
            ip = networks[net]['servers']['dhcp'][target]['interfaces'][0]['ip']
            netmask = str(ipaddress.ip_network(ip, strict=False).netmask)
            subnet = str(ipaddress.ip_network(ip, strict=False)).split('/')[0]
            range = networks[net]['servers']['dhcp'][target]['range'][0] + " " + networks[net]['servers']['dhcp'][target]['range'][1]

            content = "subnet " + subnet + " netmask " + netmask + " {option routers " + \
                      networks[net]['servers']['dhcp'][target]['interfaces'][0][
                          'gateway'] + ";option subnet-mask " + netmask + ";range " + range + ";default-lease-time " + \
                      networks[net]['servers']['dhcp'][target]['default-lease-time'] + ";max-lease-time " + networks[net]['servers']['dhcp'][target][
                          'max-lease-time'] + ";}"

            fp = open(dataPath + "/dhcpd.conf", 'w')
            fp.write(content)
            fp.close()
            # create dhcp container
            dhcpsContainer = client.containers.create(image=networks[net]['servers']['dhcp'][target]['image_name'], name=target,
                                                      network_mode="host",
                                                      user="root",
                                                      detach=True,
                                                      publish_all_ports=True,
                                                      privileged=True,
                                                      volumes={dataPath: {'bind': '/data', 'mode': 'rw'}},
                                                      command=target   # listen the name is "target" net card
                                                      )
            dhcpsContainer.start()
        # other server
        else:
            otherKind = targetType.split('/')[1]
            if networks[net]['servers'][otherKind][target]['interfaces'][0]['ip'] == "":
                shell = 'sudo ovs-docker add-port ' + source + " " + networks[net]['servers'][otherKind][target]['interfaces'][0]['name'] + " " + target
                print(shell)
                subprocess.getstatusoutput(shell)
            else:
                shell = 'sudo ovs-docker add-port ' + source + " " + networks[net]['servers'][otherKind][target]['interfaces'][0]['name'] + " " + target + " --ipaddress=" + networks[net]['servers'][otherKind][target]['interfaces'][0]['ip'] + " --gateway=" + networks[net]['servers'][otherKind][target]['interfaces'][0]['gateway']
                print(shell)
                subprocess.getstatusoutput(shell)
    elif "gateway" == sourceType.split('/')[0]:
        # router has not only one net card,find it place  ------ i
        i = 0;

        while i < len(networks[net]['gateway']["interfaces"]):
            if fromMeToYou == networks[net]['gateway']["interfaces"][i]['name']:
                break
            i = i + 1

        if networks[net]['gateway']["interfaces"][i]['ip'] == "":
            print("router net card need give me!!")
        else:
            shell = 'sudo ovs-docker add-port ' + target + " " + networks[net]['gateway']["interfaces"][i]['name'] + " " + source + " --ipaddress=" + networks[net]['gateway']["interfaces"][i]['ip']
            print(shell)
            subprocess.getstatusoutput(shell)
    elif "gateway" == targetType.split('/')[0]:
        # router has not only one net card,find it place  ------ i
        i = 0;
        while i < len(networks[net]['gateway']["interfaces"]):
            if fromYouToMe == networks[net]['gateway']["interfaces"][i]['name']:
                break
            i = i + 1

        if "" == networks[net]['gateway']["interfaces"][i]['ip']:
            print("nginx net card need give me!!")
        else:
            shell = 'sudo ovs-docker add-port ' + source + " " + networks[net]['gateway']["interfaces"][i]['name'] + " " + target + " --ipaddress=" + networks[net]['gateway']["interfaces"][i]['ip']
            print(shell)
            subprocess.getstatusoutput(shell)
    elif "middle_box" == sourceType.split('/')[0]:
        if "nginx" == sourceType.split('/')[1]:
            if networks[net]['middle_boxes']['nginx'][source]['interfaces'][0]['ip'] == "":
                shell = 'sudo ovs-docker add-port ' + target + " " + networks[net]['middle_boxes']['nginx'][source]['interfaces'][0]['name'] + " " + source
                print(shell)
                subprocess.getstatusoutput(shell)
            else:
                shell = 'sudo ovs-docker add-port ' + target + " " + networks[net]['middle_boxes']['nginx'][source]['interfaces'][0]['name'] + " " + source + " --ipaddress=" + networks[net]['middle_boxes']['nginx'][source]['interfaces'][0]['ip'] + " --gateway=" + networks[net]['middle_boxes']['nginx'][source]['interfaces'][0]['gateway']
                print(shell)
                subprocess.getstatusoutput(shell)
    elif "middle_box" == targetType.split('/')[0]:
        if "nginx" == targetType.split('/')[1]:
            if networks[net]['middle_boxes']['nginx'][target]['interfaces'][0]['ip'] == "":
                shell = 'sudo ovs-docker add-port ' + source + " " + networks[net]['middle_boxes']['nginx'][target]['interfaces'][0]['name'] + " " + target
                print(shell)
                subprocess.getstatusoutput(shell)
            else:
                shell = 'sudo ovs-docker add-port ' + source + " " + networks[net]['middle_boxes']['nginx'][target]['interfaces'][0]['name'] + " " + target + " --ipaddress=" + networks[net]['middle_boxes']['nginx'][target]['interfaces'][0]['ip'] + " --gateway=" + networks[net]['middle_boxes']['nginx'][target]['interfaces'][0]['gateway']
                print(shell)
                subprocess.getstatusoutput(shell)

def get_pid(container_name):              # 获得容器的pid
    pid = None
    try:
        client = docker.from_env()
        container_id = client.containers.get(container_name)
        container_id = str(container_id)[-11: -1]
        shell = "sudo docker inspect -f '{{.State.Pid}}' " + container_id
        pid = subprocess.Popen(shell, shell=True, stdout=subprocess.PIPE)
        pid.wait()
        pid = str(int(pid.stdout.read().decode()))
    except:
        pass
    return pid          # 返回str类型的pid号

def create_veth_pair(container_name, container_name2):        # 创建veth
    first_pid = get_pid(container_name)
    second_pid = get_pid(container_name2)
    print("first_pid:" + first_pid + "\n""second_pid:" + second_pid + "\n")   # 输出两个pid号
    try:
        create_file_shell = "sudo mkdir -p /var/run/netns"
        create_file = subprocess.Popen(create_file_shell, shell=True, stdout=subprocess.PIPE)
        create_file.wait()
        link_file_shell = "sudo ln -s /proc/" + first_pid + "/ns/net /var/run/netns/" + first_pid
        link_file = subprocess.Popen(link_file_shell, shell=True, stdout=subprocess.PIPE)
        link_file.wait()
        link_file_shell2 = "sudo ln -s /proc/" + second_pid + "/ns/net /var/run/netns/" + second_pid
        link_file2 = subprocess.Popen(link_file_shell2, shell=True, stdout=subprocess.PIPE)
        link_file2.wait()
    except:
        print("create error!")
    try:
        lable = 0
        eth1 = container_name + container_name2
        eth2 = container_name2 + container_name
        """if eth1 == eth2:
            old_eth2 = eth2
            eth2 = eth2 + "_c"
            print("the second net card: " + old_eth2 + " is renamed to: " + eth2)"""
        shell = "sudo ip link add " + eth1 + " type veth peer name " + eth2
        os.system(shell)
        shell = "sudo ip link set " + eth1 + " netns " + first_pid       # 分别将两个网卡加入namespace
        os.system(shell)
        shell = "sudo ip link set " + eth2 + " netns " + second_pid
        os.system(shell)
        shell = "sudo ip netns exec " + first_pid + " ip link set " + eth1 + " up"
        os.system(shell)
        shell = "sudo ip netns exec " + second_pid + " ip link set " + eth2 + " up"
        os.system(shell)
    except:
        print("error")

# container link in net
def ContainerLink(net,source,target,sourceType,targetType):
    # source net card name
    fromMeToYou = source + target
    # target net card name
    fromYouToMe = target + source

    if "router" == sourceType.split('/')[0] and "server" == targetType.split('/')[0]:
        print("source=" + source + " target=" + target)
        print(fromMeToYou + "  " + fromYouToMe)

        create_veth_pair(source, target)

        # find source router net card place ------- i
        i = 0
        while i < len(networks[net]['gateway']['interfaces']):
            if fromMeToYou == networks['gateway']['interfaces'][i]['name']:
                break
            i = i + 1

        shell = 'sudo ip netns exec ' + get_pid(source) + ' ip addr add ' + networks[net]['gateway']['interfaces'][i]['ip'] + ' dev ' + fromMeToYou
        print(shell)
        subprocess.getstatusoutput(shell)
        shell = 'sudo ip netns exec ' + get_pid(target) + ' ip addr add ' + networks[net]['servers'][targetType.split('/')[1]][target]['interfaces'][0]['ip'] + ' dev ' + fromYouToMe
        print(shell)
        subprocess.getstatusoutput(shell)
        shell = 'sudo ip netns exec ' + get_pid(target) + ' route add default gw ' + str(networks[net]['gateway']['interfaces'][i]['ip']).split('/')[0]
        print(shell)
        subprocess.getstatusoutput(shell)
    elif "router" == targetType.split('/')[0] and "server" == sourceType.split('/')[0]:
        print("source=" + source + " target=" + target)
        print(fromMeToYou + "  " + fromYouToMe)

        create_veth_pair(source, target)

        # find target router net card place ------- i
        i = 0
        while i < len(networks[net]['gateway']['interfaces']):
            if fromYouToMe == networks[net]['gateway']['interfaces'][i]['name']:
                break
            i = i + 1

        shell = 'sudo ip netns exec ' + get_pid(target) + ' ip addr add ' + networks[net]['gateway']['interfaces'][i]['ip'] + ' dev ' + fromYouToMe
        print(shell)
        subprocess.getstatusoutput(shell)
        shell = 'sudo ip netns exec ' + get_pid(source) + ' ip addr add ' + networks[net]['servers'][sourceType.split('/')[1]][source]['interfaces'][0]['ip'] + ' dev ' + fromMeToYou
        print(shell)
        subprocess.getstatusoutput(shell)
        shell = 'sudo ip netns exec ' + get_pid(source) + ' route add default gw ' + str(networks[net]['gateway']['interfaces'][i]['ip']).split('/')[0]
        print(shell)
        subprocess.getstatusoutput(shell)
    elif "router" == sourceType.split('/')[0] and "middle_box" == targetType.split('/')[0]:
        print("source=" + source + " target=" + target)
        print(fromMeToYou + "  " + fromYouToMe)

        create_veth_pair(source, target)

        # find source router net card place ------- i
        i = 0
        while i < len(networks[net]['gateway']['interfaces']):
            if fromMeToYou == networks[net]['gateway']['interfaces'][i]['name']:
                break
            i = i + 1

        if "nginx" == targetType.split('/')[1]:
            # find target nginx net card place ------- j
            j = 0
            while j < len(networks[net]['middle_boxes']['nginx'][target]['interfaces']):
                if fromYouToMe == networks[net]['middle_boxes'][target]['interfaces'][j]['name']:
                    break
                j = j + 1

            shell = 'sudo ip netns exec ' + get_pid(source) + ' ip addr add ' + networks[net]['gateway']['interfaces'][i]['ip'] + ' dev ' + fromMeToYou
            print(shell)
            subprocess.getstatusoutput(shell)
            shell = 'sudo ip netns exec ' + get_pid(target) + ' ip addr add ' + networks[net]['middle_boxes']['nginx'][target]['interfaces'][j]['ip'] + ' dev ' + fromYouToMe
            print(shell)
            subprocess.getstatusoutput(shell)
            shell = 'sudo ip netns exec ' + get_pid(target) + ' route add default gw ' + str(networks[net]['gateway']['interfaces'][i]['ip']).split('/')[0]
            print(shell)
            subprocess.getstatusoutput(shell)
    elif "router" == targetType.split('/')[0] and "middle_box" == sourceType.split('/')[0]:
        print("source=" + source + " target=" + target)
        print(fromMeToYou + "  " + fromYouToMe)

        create_veth_pair(source, target)

        # find target router net card place ------- i
        i = 0
        while i < len(networks[net]['gateway']['interfaces']):
            if fromYouToMe == networks[net]['gateway']['interfaces'][i]['name']:
                break
            i = i + 1

        if "nginx" == sourceType.split('/')[1]:
            # find target nginx net card place ------- j
            j = 0
            while j < len(networks[net]['middle_boxes']['nginx'][source]['interfaces']):
                if fromMeToYou == networks[net]['middle_boxes']['nginx'][source]['interfaces'][j]['name']:
                    break
                j = j + 1

            shell = 'sudo ip netns exec ' + get_pid(target) + ' ip addr add ' + networks[net]['gateway']['interfaces'][i]['ip'] + ' dev ' + fromYouToMe
            print(shell)
            subprocess.getstatusoutput(shell)
            shell = 'sudo ip netns exec ' + get_pid(source) + ' ip addr add ' + networks[net]['middle_boxes']['nginx'][source]['interfacs'][j]['ip'] + ' dev ' + fromMeToYou
            print(shell)
            subprocess.getstatusoutput(shell)
            shell = 'sudo ip netns exec ' + get_pid(source) + ' route add default gw ' + str(networks[net]['gateway']['interfaces'][i]['ip']).split('/')[0]
            print(shell)
            subprocess.getstatusoutput(shell)
# link line in net
def linkNetLine(net,links):
    for key in links:
        if "switch/ovs" == links[key]['sourceType'] or "switch/ovs" == links[key]['targetType']:
            print("与交换机相连的....")
            ovsLink(net,links[key]['source'],links[key]['sourceType'],links[key]['target'],links[key]['targetType'])

        else:
            print("容器之间相连的...")
            ContainerLink(net,links[key]['source'],links[key]['target'],links[key]['sourceType'],links[key]['targetType'])

# host apply to IP from dhcp
def hostApplyIp(hostsDict):
    for key in hostsDict:
            hostsDict[key].exec_run(cmd='dhclient', detach=True)

# server apply to IP from dhcp
def serverApplyIp(serversDict):
    for key in serversDict:
            serversDict[key].exec_run(cmd='dhclient', detach=True)

#middle_box apply to IP from dhcp
def middle_boxApplyIp(middle_boxDict):
    for key in middle_boxDict:
        middle_boxDict[key].exec_run(cmd='dhclient', detach=True)

# create net
def cretateNet(networks):
    # loop create net
    for key in networks:
        # create net device
        if "hosts" in networks[key]:
            hostsDict = createHosts(networks[key]['hosts'])
        if "servers" in networks[key]:
            serversDict = createServer(networks[key]['servers'])

        createSwitch(networks[key]['switches'])
        createGateway(networks[key]['gateway'])
        if "middle_boxes" in networks[key]:
            middle_boxDict = createMiddleboxes(networks[key]['middle_boxes'])
        #link line in net
        linkNetLine(key, networks[key]['links'])
        #host apply to IP from dhcp
        if "hosts" in networks[key]:
            hostApplyIp(hostsDict)
        #server apply to IP from dhcp
        if "servers" in networks[key]:
            serverApplyIp(serversDict)
        #middle_box apply to IP from dhcp
        if "middle_boxes" in networks[key]:
            middle_boxApplyIp(middle_boxDict)

#link line between net
def linkOtherLine(links):
    for link in links:
        # source net card name
        fromMeToYou = links[link]['source'] + links[link]['target']
        # target net card name
        fromYouToMe = links[link]['target'] + links[link]['source']

        if "gateway" == links[link]['sourceType'] and "gateway" == links[link]['targetType']:
            sourceNet = links[link]['sourceNet']
            targetNet = links[link]['targetNet']

            print("source=" + links[link]['source'] + " target=" + links[link]['target'])
            print(fromMeToYou + "  " + fromYouToMe)

            create_veth_pair(links[link]['source'],links[link]['target'])

            # find source router net card place ------- i
            i = 0
            while i < len(networks[sourceNet]['gateway']['interfaces']):
              if fromMeToYou == networks[sourceNet]['gateway']['interfaces'][i]['name']:
                 break
              i = i + 1
            # find target router net card place ------- j
            j = 0
            while j < len(networks[targetNet]['gateway']['interfaces']):
              if fromYouToMe == networks[targetNet]['gateway']['interfaces'][j]['name']:
                 break
              j = j + 1

            shell = 'sudo ip netns exec ' + get_pid(links[link]['source']) + ' ip addr add ' + networks[sourceNet]['gateway']['interfaces'][i]['ip'] + ' dev ' + fromMeToYou
            print(shell)
            subprocess.getstatusoutput(shell)
            shell = 'sudo ip netns exec ' + get_pid(links[link]['target']) + ' ip addr add ' + networks[targetNet]['gateway']['interfaces'][j]['ip'] + ' dev ' + fromYouToMe
            print(shell)
            subprocess.getstatusoutput(shell)

# link between getway and ovs_vxlan
def link_gateway_vxlan(link):
    switch = link['target']
    shell = "sudo ovs-vsctl add-br " + switch
    print(shell)
    ovs_info = subprocess.Popen(shell, shell=True, stdout=subprocess.PIPE)
    ovs_info.wait()
    shell = "sudo ovs-vsctl set bridge " + switch + " stp_enable=true"
    print(shell)
    ovs_info = subprocess.Popen(shell, shell=True, stdout=subprocess.PIPE)
    ovs_info.wait()
    ovsLink(link['sourceNet'], link['source'], link['sourceType'], link['target'], link['targetType'])
    # add port of vxlan
    # vemu2 --> vemu3
    #subprocess.getstatusoutput('sudo ovs-vsctl add-port ' + switch + ' ' + 'vxlan ' + '-- set Interface vxlan type=vxlan options:remote_ip=10.1.1.27')
    # vemu3 --> vemu2
    subprocess.getstatusoutput('sudo ovs-vsctl add-port ' + switch + ' ' + 'vxlan ' + '-- set Interface vxlan type=vxlan options:remote_ip=10.1.1.31')


def write_congratuation_file(ip, nginxs):  # 实例化的containers_ip()类,　topo["networks"]["net1"]["middle_boxes"]["nginx"]
    client = docker.from_env()
    start_nginx_cmd = ["nginx", "-c", "nginx.conf"]
    for nginx in nginxs:
        container = client.containers.get(nginx)
        for server in nginxs[nginx]["server"]:    # 只有一个，但是因为json格式原因,需要循环
            if len(server["server_name"]) == 0:         # server
                server_ip = ip[nginx]     #获取nginx的IP
            else:
                server_ip = server["server_name"]
            server_port = server["listen"]
            location = server["location"]
            break                     # exit loop
        nginx_pools = []                         # nginx_pools
        for web in nginxs[nginx]["nginx_pools"]:
            web_name = web["name"]
            print(web_name)
            if len(web["ip"]) == 0:
                web_ip = ip[web_name]
                print(web_name,web_ip)
            else:
                web_ip = web["ip"]
            web_port = web["port"]
            web_weight = web["weight"]
            info = "    server " + web_ip + ":" + web_port + " weight=" + web_weight + ";\n"
            nginx_pools.append(info)
        with open("default.conf", "at") as configuration_file:  # 根据获取的信息写当前服务器的配置文件
            configuration_file.writelines("upstream nginx_pools {\n")
            for nginx_pool in nginx_pools:
                configuration_file.write(nginx_pool)
            configuration_file.write("}\n")
            configuration_file.write("server {\n")
            configuration_file.write("    listen " + server_port + ";\n")
            configuration_file.write("    server_name " + server_ip + ";\n")
            configuration_file.write("    location / {\n")
            configuration_file.write("        " + location + ";\n")
            configuration_file.write("    }\n")
            configuration_file.write("}\n")
            configuration_file.close()
        time.sleep(3)
        shell = "sudo docker cp default.conf " + nginx + ":/etc/nginx/conf.d/"  # docker目前没有发现有关复制的API
        save_configuration_file = subprocess.Popen(shell, shell=True, stdout=subprocess.PIPE)
        save_configuration_file.wait()  # 复制配置文件到容器中
        shell = "sudo rm default.conf"
        save_configuration_file = subprocess.Popen(shell, shell=True, stdout=subprocess.PIPE)
        save_configuration_file.wait()  # 删除配置文件
        container.exec_run(cmd=start_nginx_cmd, detach=True)

# write configure file to nginx
def writeFileToNginx(networks):
    dhcps = []
    for net in networks:
        if "dhcp" in networks[net]['servers']:
            for key in networks[net]['servers']["dhcp"]:
                dhcps.append(key)
        else:
            break
    print(dhcps)
    # dhcps = ["dhcp1", "dhcp2"]
    ipDict = containers_ip().get_ip(dhcps)

    for net in networks:
        if "nginx" in networks[net]['middle_boxes']:
            write_congratuation_file(ipDict, networks[net]['middle_boxes']["nginx"])
        else:
            break



if __name__ == '__main__':
    # get topo
    with open("topo.json", 'r') as f:
        topo = json.load(f)
        f.close()


    networks = topo['networks']
    links_net = topo['links_net']



    # create configure file---------configurations
    path1 = "./configurations"
    path = os.path.abspath(path1)
    print(path)
    isExists = os.path.exists(path)
    if not isExists:
        os.makedirs(path)

    cretateNet(networks)
    linkOtherLine(links_net)
    link_gateway_vxlan(topo['link_vxlan'])

    time.sleep(60)
    # jude has nginx or not
    flag = False
    for net in networks:
        if "nginx" in networks[net]['middle_boxes']:
            flag = True

    print(flag)

    if flag:
        writeFileToNginx(networks)

