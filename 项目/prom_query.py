import requests
import time
import pprint
import json


# 查询语句字典,每一个列表本可以写多个表达式以实现多个表达式同时查询。但为了查询和绘制便利，暂且仅写一个。
query_dict = {
    # TODO: 丰富查询？
    # 服务器节点查询
    'node_cpu':['1 - avg(irate(node_cpu_seconds_total{mode="idle"}[1m]))by (instance)', ],
    'node_mem':['node_memory_MemAvailable_bytes{ } / (1024 * 1024)', ],
    'node_load':['node_load1{ }', ],  # 'node_load5{ }', 'node_load15{ }'],
    'node_disk':['1-(node_filesystem_free_bytes{fstype=~"ext4|xfs"} / node_filesystem_size_bytes{fstype=~"ext4|xfs"})', ],
    # docker
    'docker_sent_traffic':['irate(container_network_transmit_bytes_total{name!="",name!~"gra.*",name!~"prom.*",name!~"sflow.*",name!~"cad.*",name!~"node.*"}[1m])*8', ],
    'docker_recv_traffic':['irate(container_network_receive_bytes_total{name!="",name!~"gra.*",name!~"prom.*",name!~"sflow.*",name!~"cad.*",name!~"node.*"}[1m])*8', ],
    # sflow
    'sflow_ifinoctets':['sflow_ifinoctets{ifname!~"s.*"} * 8', ],
    'sflow_ifoutoctets':['sflow_ifoutoctets{ifname!~"s.*"} * 8', ],
}
# 从Prometheus HTTP API获取范围数据
def get_range_metric_data(config, metric_dict, start_time, end_time, step):
    
    metric_datas = []

    # end_time = time.time()
    # start_time = end_time - float(history_len) # 300s数据

    for m in metric_dict:
        try:
            params = {
                "query": m,
                "start": start_time,
                "end": end_time,
                "step": step + 's', # 数据步长
            }
            url = config["PROMETHEUS_URL"] + "/api/v1/query_range"
            response = requests.get(url, params=params)
            if response.status_code == 200:
                res = response.json()
                if res and res.get('status') == 'success':
                    datas = res.get('data', {}).get('result', [])
                    metric_datas.extend(datas)
        except Exception as e:
            print(e)

    return metric_datas

# 从Prometheus HTTP API获取瞬时数据
# 是否设置可修改时刻？但是时刻的值用户不好确定
def get_instant_metric_data(config, metric_dict):
    metric_datas = []
    query_time = time.time()

    for m in metric_dict:
        try:
            params = {
                "query": m,
                "time":query_time
            }
            url = config["PROMETHEUS_URL"] + "/api/v1/query"
            response = requests.get(url, params=params)
            if response.status_code == 200:
                res = response.json()
                if res and res.get('status') == 'success':
                    datas = res.get('data', {}).get('result', [])
                    metric_datas.extend(datas)
        except Exception as e:
            print(e)

    return metric_datas

def date_to_timestamp(date, format_string="%Y-%m-%d %H:%M:%S"):
    time_array = time.strptime(date, format_string)
    time_stamp = int(time.mktime(time_array))
    return time_stamp

def timestamp_to_date(time_stamp, format_string="%Y-%m-%d %H:%M:%S"):
    time_array = time.localtime(time_stamp)
    str_date = time.strftime(format_string, time_array)
    return str_date

def range_ori_data_to_kv(metric_datas, type_name):
    metric_dict = {}
    # instance = ''
    # name = ''
    for m in metric_datas:
        ori_values = m.get('values', [])
        values = []
        data_time = []
        for val in ori_values:
            # TODO:加入时间轴和数据，为绘制图像做准备
            # data_time.append(timestamp_to_date(val[0]))
            values.append(val[1])
        # print(data_time)
        instance = m.get('metric', {}).get('instance', {})
        if type_name == 'node':
            metric_dict[instance] = values
        elif type_name == 'docker':
            name = m.get('metric', {}).get('name', {})
            interface = m.get('metric', {}).get('interface', {})
            metric_dict.setdefault(instance, {})
            if interface != dict():
                metric_dict[instance].setdefault(name, {}).setdefault(interface, []).extend(values)
            else:
                metric_dict[instance].setdefault(name, []).extend(values)
        elif type_name == 'sflow':
            agent = m.get('metric', {}).get('agent', {})
            ifname = m.get('metric', {}).get('ifname', {})
            metric_dict.setdefault(agent, {})
            metric_dict[agent].setdefault(ifname, []).extend(values)

    return metric_dict

def instant_ori_data_to_kv(metric_datas, type_name):
    metric_dict = {}
    for m in metric_datas:
        instance = m.get('metric', {}).get('instance', {})
        values = m.get('value', [])
        if type_name == 'node':
            metric_dict[instance] = values[1]
        elif type_name == 'docker':
            metric_dict.setdefault(instance, {})
            name = m.get('metric', {}).get('name', {})
            interface = m.get('metric', {}).get('interface', {})
            if interface != dict():
                metric_dict[instance].setdefault(name, {}).setdefault(interface, 0)
                metric_dict[instance][name][interface] = values[1]
            else:
                metric_dict[instance].setdefault(name, 0)
                metric_dict[instance][name] = values[1]
        elif type_name == 'sflow':
            agent = m.get('metric', {}).get('agent', {})
            ifname = m.get('metric', {}).get('ifname', {})
            metric_dict.setdefault(agent, {})
            metric_dict[agent].setdefault(ifname, 0)
            metric_dict[agent][ifname] = values[1]
    return metric_dict

# def cpu_query():
#     # mode:Total/user/system/iowait
#     # history_len:the history_len of metrics

#     # mode = input("输入CPU模式：")
#     # history_len = 10 
#     # step = 1
#     query_expr_list = ['1 - avg(irate(node_cpu_seconds_total{mode="idle"}[1m]))by (instance)', ] # 可以添加多个表达式
#     range_or_instant = input("选择数据输出类型：range or instant：")
#     if range_or_instant == "range":
#         history_len = input("输入数据跨度（单位：s）: ") # 数据跨度（单位：s）
#         step = input("输入数据点的时间间隔（单位：s）:") # 每个数据点之间的间隔（单位：s）
#         metric_datas = get_range_metric_data({"PROMETHEUS_URL": "http://localhost:9090/"}, query_expr_list, history_len, step)
#         pprint.pprint(range_ori_data_to_kv(metric_datas))
#     elif range_or_instant == "instant":
#         metric_datas = get_instant_metric_data({"PROMETHEUS_URL": "http://localhost:9090/"}, query_expr_list)
#         pprint.pprint(instant_ori_data_to_kv(metric_datas))


def query(query_choice):
    # 查询类型判断，决定输出类型
    if "docker" in query_choice:
        type_name = 'docker'
    elif "node" in query_choice:
        type_name = 'node'
    elif "sflow" in query_choice:
        type_name = 'sflow'
    if 'other' in query_choice:
        query_expr_list = []
        type_name = 'other'
        query_expr_list.append(input("输入查询数据的Prometheus表达式："))
    else:
        query_expr_list = query_dict[query_choice]
    range_or_instant = input("选择数据输出类型：range or instant：")
    if range_or_instant == "range":
        # history_len = input("输入数据跨度（单位：s）: ") # 数据跨度（单位：s）
        start_time = date_to_timestamp(input("输入数据的起始时间,格式为\"%Y-%m-%d %H:%M:%S\",eg:2020-06-01 13:37:04:"))
        end_time = date_to_timestamp(input("输入数据的结束时间,格式为\"%Y-%m-%d %H:%M:%S\",eg:2020-06-01 13:45:04:"))
        # print(start_time, end_time)
        step = input("输入数据点的时间间隔（单位：s）:") # 每个数据点之间的间隔（单位：s）
        metric_datas = get_range_metric_data({"PROMETHEUS_URL": "http://localhost:9090/"}, query_expr_list, start_time, end_time, step)
        pprint.pprint(metric_datas)
        if 'other' not in query_choice:
            range_data = range_ori_data_to_kv(metric_datas, type_name)
            # pprint.pprint(range_data)
        # 存储
        # filename = range_or_instant + '_' + query_choice + '_' +  str(start_time) + '_to_' + str(end_time) + "_" + "_step_" + step
        # with open(filename + ".json", 'w') as f:
        #     json.dump(metric_datas, f, indent=4)  # 原始数据
        #     f.write("\n")
        #     json.dump(range_data, f, indent=4)  # 整理为一定格式的数据
    elif range_or_instant == "instant":
        metric_datas = get_instant_metric_data({"PROMETHEUS_URL": "http://localhost:9090/"}, query_expr_list)
        pprint.pprint(metric_datas)
        instant_data = instant_ori_data_to_kv(metric_datas, type_name)
        # pprint.pprint(instant_data)
        # 存储
        # filename = range_or_instant + '_' + query_choice 
        # with open(filename + ".json", 'w') as f:
        #     json.dump(metric_datas, f, indent=4)  # 原始数据
        #     f.write("\n")
        #     json.dump(instant_data, f, indent=4)  # 整理为一定格式的数据
    else:
        print('unknown choice,retry again!')

def run_query():
    start_words = """please choose a number：
                    1. Other metrics
                    2. CPU Utilization
                    3. Memory
                    4. Disk Utilization
                    5. Average Load
                    6. Docker Sent Traffic
                    7. Docker Receive Traffic
                    8. sFlow In throughput
                """
    while True:
        choice = input(start_words)
        if choice == 'exit':
            break
        elif choice == '1':
            query('other_metric')
        elif choice == '2':
            query('node_cpu')
        elif choice == '3':
            query('node_mem')
        elif choice == '4':
            query('node_disk')
        elif choice == '5':
            query('node_load')
        elif choice == '6':
            query('docker_sent_traffic')
        elif choice == '7':
            query('docker_recv_traffic')
        elif choice == '8':
            query('sflow_ifinoctets')
        else:
            print('unknown choice,retry again!')

if __name__ == "__main__":
    run_query()
            
   
