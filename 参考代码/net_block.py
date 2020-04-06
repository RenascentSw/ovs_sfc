import json
import random
import copy
from queue import Queue


def net_cut(topo):
    topo_1 = {"name":"topo1","status":"STATUS_SAVED","networks":{},"links_net":{}}
    topo_2 = {"name":"topo2","status":"STATUS_SAVED","networks":{},"links_net":{}}

    net = copy.deepcopy(topo['networks'])
    links_net = copy.deepcopy(topo['links_net'])
    # link deleted
    links_net_keys = links_net.keys()
    temp = random.sample(links_net_keys,1)
    link_cut_key = temp[0]
    link_cut_value = links_net[link_cut_key]
    net_1 = copy.deepcopy(link_cut_value['sourceNet'])
    net_2 = copy.deepcopy(link_cut_value['targetNet'])
    net1 = copy.deepcopy(net_1)
    net2 = copy.deepcopy(net_2)
    del topo['links_net'][link_cut_key]

    # queue process
    q1 = Queue(maxsize=len(net))
    q2 = Queue(maxsize=len(net))
    q1.put(net_1)
    q2.put(net_2)

    # net_1 part
    while q1.empty() == 0:
        links_net = topo['links_net']
        net_1 = q1.get()
        topo_1['networks'][net_1] = copy.deepcopy(topo['networks'][net_1])
        del topo['networks'][net_1]
        for key in links_net:
            if links_net[key]['sourceNet'] == net_1:
                net_key = copy.deepcopy(links_net['targetNet']) # net inqueue
                q1.put(net_key)
                topo_1['links_net'][key] = copy.deepcopy(links_net[key])
                del topo['links_net'][key]

            if links_net[key]['targetNet'] == net_1:
                net_key = copy.deepcopy(links_net['sourceNet'])
                q1.put(net_key)
                topo_1['links_net'][key] = copy.deepcopy(links_net[key])
                del topo['links_net'][key]
    # net_2 part
    while q2.empty() == 0:
        links_net = topo['links_net']
        net_2 = q2.get()
        topo_2['networks'][net_2] = copy.deepcopy(topo['networks'][net_2])
        del topo['networks'][net_2]
        for key in links_net:
            if links_net[key]['sourceNet'] == net_2:
                net_key = copy.deepcopy(links_net['targetNet'])
                q2.put(net_key)
                topo_2['links_net'][key] = copy.deepcopy(links_net[key])
                del topo['links_net'][key]
            if links_net[key]['targetNet'] == net_2:
                net_key = copy.deepcopy(links_net['sourceNet'])
                q2.put(net_key)
                topo_2['links_net'][key] = copy.deepcopy(links_net[key])
                del topo['links_net'][key]
    for key in topo_1['networks'][net1]['gateway']['interfaces']:
        if key['name'] == topo_1['networks'][net1]['gateway']['name']+topo_2['networks'][net2]['gateway']['name'] or key['name'] == topo_2['networks'][net2]['gateway']['name']+topo_1['networks'][net1]['gateway']['name']:
            key['name'] = topo_1['networks'][net1]['gateway']['name'] + "ovs_vxlan"
    for key in topo_2['networks'][net2]['gateway']['interfaces']:
        if key['name'] == topo_1['networks'][net1]['gateway']['name']+topo_2['networks'][net2]['gateway']['name'] or key['name'] == topo_2['networks'][net2]['gateway']['name']+topo_1['networks'][net1]['gateway']['name']:
            key['name'] = topo_2['networks'][net2]['gateway']['name'] + "ovs_vxlan"

    return topo_1, topo_2, net1, net2



# get topo
with open("topo.json", "r") as f:
    topo = json.load(f)
    f.close()

link_vxlan={
            "name": "l1",
            "source": "",
            "sourceType": "gateway",
            "sourceNet": "",
            "target": "ovs_vxlan",
            "targetType": "switch/ovs",

            "delay": "XX",
            "jitter": "XX",
            "loss": "XX%",
            "max_bandwidth": "XXXXkbit",
            "burst": "XXXX",
            "latency": "XXms"}

topo_1, topo_2, net1, net2 = net_cut(topo)

if net1 in topo_1['networks']:
    topo_1['link_vxlan'] = copy.deepcopy(link_vxlan)
    topo_1['link_vxlan']['source'] = copy.deepcopy(topo_1['networks'][net1]['gateway']['name'])
    topo_1['link_vxlan']['sourceNet'] = net1
    topo_2['link_vxlan'] = copy.deepcopy(link_vxlan)
    topo_2['link_vxlan']['source'] = copy.deepcopy(topo_2['networks'][net2]['gateway']['name'])
    topo_2['link_vxlan']['sourceNet'] = net2
else:
    topo_1['link_vxlan'] = copy.deepcopy(link_vxlan)
    topo_1['link_vxlan']['source'] = copy.deepcopy(topo_1['networks'][net2]['gateway']['name'])
    topo_1['link_vxlan']['sourceNet'] = net2
    topo_2['link_vxlan'] = copy.deepcopy(link_vxlan)
    topo_2['link_vxlan']['source'] = copy.deepcopy(topo_2['networks'][net1]['gateway']['name'])
    topo_2['link_vxlan']['sourceNet'] = net1


with open("topo_1.json","w") as f:
    json.dump(topo_1, f, indent=3, separators=(',', ': '))
    f.close()
with open("topo_2.json","w") as f:
    json.dump(topo_2, f, indent=3, separators=(',', ':'))
    f.close()
