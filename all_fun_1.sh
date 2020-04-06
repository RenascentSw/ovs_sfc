#!/bin/bash
# 各种功能合集
# del_ingress
ovs-vsctl set interface ${intercase1} ingress_policing_rate=0 ingress_policing_burst=0
# del_meter
ovs-ofctl del-meters s1 meter=all -O openflow13
# del_qos
ovs-vsctl clear port ${interface1} qos
ovs-vsctl -- --all destroy QoS -- --all destroy Queue
# deploy_sflow
ifconfig s1 10.0.0.3/24
ovs-vsctl -- --id=@sflow create sFlow agent=s1 target=\"127.0.0.1:6343\"  header=128  sampling=64 polling=1 -- set bridge s1 sflow=@sflow
# ingress_limit
ovs-vsctl set interface ${interface1} ingress_policing_rate=5000 ingress_policing_burst=4000
# meter_limit
ovs-vsctl set bridge s1 protocols=OpenFlow13
ovs-ofctl add-meter s1 meter=1,kbps,burst,bands=type=drop,rate=5000,burst_size=4000 -O OpenFlow13
ovs-ofctl add-flow s1 in_port=1,actions=meter:1,output:2 -O Openflow13

# qos_htb
ovs-vsctl set port ${interface1} qos=@newqos -- --id=@newqos create qos type=linux-htb queues=0=@q0 -- --id=@q0 create queue other-config:max-rate=5000000 other-config:burst=4000000
# search_interface
ovs-vsctl list interface | grep -E "name|ofport|external_id" 
# simple_net
echo "begin to delete old bridge"
ovs-vsctl del-br s1
echo "begin to initial host"
docker start host1
docker start host2
echo "begin to build new bridge"
ovs-vsctl add-br s1
ovs-docker add-port s1 eth0 host1
ovs-docker add-port s1 eth0 host2
echo "done!"
# simple_st_fw
ovs-ofctl add-flow s1 "table=0,priority=100,icmp,ct_state=-trk,actions=ct(table=1)"
ovs-ofctl add-flow s1 "table=1,in_port=2,icmp,ct_state=+trk+est,actions=output:1"
ovs-ofctl add-flow s1 "table=1,in_port=1,icmp,ct_state=+trk+est,actions=output:2"
ovs-ofctl add-flow s1 "table=1,in_port=1,icmp,ct_state=+trk+new,actions=ct(commit),output:2"
ovs-ofctl add-flow s1 "table=1,in_port=2,icmp,ct_state=+trk+new,actions=drop"

