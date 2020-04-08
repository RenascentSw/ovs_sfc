import subprocess
import docker
import json
# import sys


# docker module: https://docker-py.readthedocs.io/en/stable/containers.html
client = docker.from_env()


def create_hosts(hosts):
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
                                             oom_kill_disable=True, # 内存不足时，OOM killer 会杀掉某个进程以腾出内存留给系统用
                                             publish_all_ports=True,
                                             privileged=True,
                                             hostname=key
                                             # volumes={"/home/light-travelling/resolv.conf": {'bind': '/etc/resolv.conf','mode': 'rw'}}
                                             )
        print('create host: '+ key)
        hostDict[key] = hostsContainer
    print('create_hosts done!')
    return hostDict

def create_switches(switches):
    for switch in switches:
        # print(switch)
        shell = "sudo ovs-vsctl add-br " + switch
        print(shell)
        ovs_info = subprocess.Popen(shell, shell=True, stdout=subprocess.PIPE)
        ovs_info.wait()
    print('create_switches done!')


#  deploy net using create_hosts(),create_switches() and link_with_net()
def deploy_net(networks):
    print('start to deploy net……')
    for net in networks:
        create_hosts(networks[net]['hosts'])
        create_switches(networks[net]['switches'])
        link_with_net(networks[net], networks[net]['links'])


#  set and delete linux-htb
def qos_htb():
    print("# qos_htb function")
    add_or_del = input("please input 'add_qos' or 'del_qos':")
    interface = input("please input interface name first.\nIf you want to search for interface,use 'Enter' please:")
    if add_or_del == 'add_qos':
        if interface != '':
            max_rate = input('please input max_rate(bits/s) :')
            burst = input('please input burst(bits) :')
            shell = "sudo ovs-vsctl set port <interface> qos=@newqos -- ".replace("<interface>", interface) + \
                    "--id=@newqos create qos type=linux-htb queues=0=@q0 -- " + \
                    "--id=@q0 create queue other-config:max-rate=<max_rate> other-config:burst=<burst>".replace("<max_rate>", max_rate).replace("<burst>",burst)
            print(shell)
            subprocess.getstatusoutput(shell)
        else:
            search_for_interface()
    elif add_or_del == 'del_qos':
        if interface != '':
            shell = "sudo ovs-vsctl clear port <interface> qos\n".replace("<interface>", interface) + \
                    "sudo ovs-vsctl -- --all destroy QoS -- --all destroy Queue"
            print(shell)
            subprocess.getstatusoutput(shell)
        else:
            search_for_interface()
    else:
        print("unknown choice!")


#  set and delete ingress_policing
def ingress_limit():
    print("# ingress policing function")
    add_or_del = input("please input 'add_ingress' or 'del_ingress':")
    interface = input("please input interface name first.\nIf you want to search for interface,use 'Enter' please:")
    if add_or_del == 'add_ingress':
        if interface != '':
            max_rate = input('please input max_rate(kbits/s) :')
            burst = input('please input burst(kbits) :')
            shell = "sudo ovs-vsctl set interface <interface> ingress_policing_rate=<max_rate>".replace("<interface>", interface).replace("<max_rate>", max_rate) + \
                    " ingress_policing_burst=<burst>".replace("<burst>", burst)
            print(shell)
            subprocess.getstatusoutput(shell)
        else:
            search_for_interface()
    elif add_or_del == 'del_ingress':
        if interface != '':
            shell = "sudo ovs-vsctl set interface <interface> ingress_policing_rate=0 ingress_policing_burst=0".replace("<interface>", interface)
            print(shell)
            subprocess.getstatusoutput(shell)
        else:
            search_for_interface()
    else:
        print("unknown choice!")


#  set stateless farewall
def stateless_fw():
    print("# stateless firewall function")


#  set stateful firewall
def stateful_fw():
    print("# stateful firewall function")
    shell = "sudo ovs-ofctl add-flow s1 \"table=0,priority=100,icmp,ct_state=-trk,actions=ct(table=1)\" \n" + \
            "sudo ovs-ofctl add-flow s1 \"table=1,in_port=2,icmp,ct_state=+trk+est,actions=output:1\" \n" + \
            "sudo ovs-ofctl add-flow s1 \"table=1,in_port=1,icmp,ct_state=+trk+est,actions=output:2\" \n" + \
            "sudo ovs-ofctl add-flow s1 \"table=1,in_port=1,icmp,ct_state=+trk+new,actions=ct(commit),output:2\" \n" + \
            "sudo ovs-ofctl add-flow s1 \"table=1,in_port=2,icmp,ct_state=+trk+new,actions=drop\" \n"
    print(shell)
    subprocess.getstatusoutput(shell)

#  set and delete meter table limit
def meter_limit():
    print("# meter table limit function")
    add_or_del = input("please input 'add_meter' or 'del_meter':")
    if add_or_del == 'add_meter':
        # TODO choose port
        max_rate = input('please input max_rate(kbits/s) :')
        burst = input('please input burst(kbits) :')
        shell = "sudo ovs-vsctl set bridge s1 protocols=OpenFlow13 \n" + \
                "sudo ovs-ofctl add-meter s1 meter=1,kbps,burst,bands=type=drop,rate=<max_rate>,burst_size=<burst> -O OpenFlow13 \n".replace("<max_rate>", max_rate).replace("<burst>", burst) + \
                "sudo ovs-ofctl add-flow s1 in_port=1,actions=meter:1,output:2 -O Openflow13"
        print(shell)
        subprocess.getstatusoutput(shell)
    elif add_or_del == 'del_meter':
        shell = "sudo ovs-ofctl del-meters s1 meter=all -O openflow13"
        print(shell)
        subprocess.getstatusoutput(shell)
    else:
        print("unknown choice!")


#  set sflow monitoring
def deploy_sflow():
    print("# sflow monitoring")
    shell = "sudo ifconfig s1 10.0.0.3/24 \n" + \
            "sudo ovs-vsctl -- --id=@sflow create sFlow agent=s1 target=\\\"127.0.0.1:6343\\\"  header=128  sampling=64 polling=1 -- set bridge s1 sflow=@sflow"
    print(shell)
    subprocess.getstatusoutput(shell)


#  search for interface
def search_for_interface():
    shell = "sudo ovs-vsctl list interface | grep -E \"name|ofport|external_id\""
    print(shell)
    _, result = subprocess.getstatusoutput(shell)
    print("result:\n", result)


def ovs_link(net, source, sourceType, target, targetType):
    """link with ovs.
    Args:
        net:
        source:
        sourceType:
        target:
        targetType:
    
    Return:
        nothing
    
    Raise:
        say some error
    """
    # create interface name
    source_to_target = source + target
    target_to_source = target + source   
    if sourceType == 'switch/ovs' and targetType == 'switch/ovs':
        print('ovs '+ source + ' links with ovs '+ target)
        shell = 'sudo ovs-vsctl add-port ' + source + ' ' + source_to_target + '\n' + \
                'sudo ovs-vsctl add-port ' + target + ' ' + target_to_source + '\n' + \
                'sudo ovs-vsctl set interface '+ source_to_target + ' type=patch options:peer='+ target_to_source + '\n' + \
                'sudo ovs-vsctl set interface '+ target_to_source + ' type=patch options:peer='+ source_to_target
        print(shell)
        subprocess.getstatusoutput(shell)
    elif sourceType == 'host/ubuntu':  # for target ovs
        print('host '+ source + ' links with ovs ' + target)
        if net['hosts'][source]['interfaces'][0]['ip'] == "":  # don't have ip address
            shell = 'sudo ovs-docker add-port ' + target + " " + source_to_target + " " + source
            print(shell)
            subprocess.getstatusoutput(shell)
        else:  # have ip address
            shell = 'sudo ovs-docker add-port ' + target + " " + source_to_target + " " + source + \
            " --ipaddress=" + net['hosts'][source]['interfaces'][0]['ip']
            print(shell)
            subprocess.getstatusoutput(shell)
    else:  # for source ovs
        print('ovs '+ source + ' links with host'+ target)
        if net['hosts'][target]['interfaces'][0]['ip'] == "":
            shell = 'sudo ovs-docker add-port ' + source + " " + target_to_source + " " + target
            print(shell)
            subprocess.getstatusoutput(shell)
        else:
            shell = 'sudo ovs-docker add-port ' + source + " " + target_to_source + " " + target + \
            " --ipaddress=" + net['hosts'][target]['interfaces'][0]['ip']
            print(shell)
            subprocess.getstatusoutput(shell)

#  link ovs with other object by using ovs_link()
def link_with_net(net, links):
    for link in links:
        # if links[link]['sourceType'] == "switch/ovs" or links[link]['targetType'] == "switch/ovs":
        # print("与交换机相连的....")
        ovs_link(net,links[link]['source'],links[link]['sourceType'],links[link]['target'],links[link]['targetType'])
    print('link_with_net done!')


#  main func of simple_vnf
def run(networks):
    start_words = """please choose a number：
                    1. deploy network using json
                    2. qos-htb/del-qos
                    3. ingress limit/del ingress
                    4. stateless firewall
                    5. stateful firewall
                    6. meter limit/del meter
                    7. search for interface
                    8. deploy sflow
                """
    # print(start_words)
    while True:
        choice = input(start_words)
        if choice == 'exit':
            break
        elif choice == '1':
            deploy_net(networks=networks)
        elif choice == '2':
            qos_htb()
        elif choice == '3':
            ingress_limit()
        elif choice == '4':
            stateless_fw()
        elif choice == '5':
            stateful_fw()
        elif choice == '6':
            meter_limit()
        elif choice == '7':
            search_for_interface()
        elif choice == '8':
            deploy_sflow()
        else:
            print('unknown choice,retry again!')


if __name__ == '__main__':
    with open('simple_topo.json','r') as f:
        topo = json.load(f)
    run(topo['networks'])
