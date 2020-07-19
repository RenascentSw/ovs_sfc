import requests
import time
import pprint
# import address_utils
import json


# 查询语句字典,每一个列表本可以写多个表达式以实现多个表达式同时查询。但为了查询和绘制便利，暂且仅写一个。
query_dict = {
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

def date_to_timestamp(date, format_string="%Y-%m-%d %H:%M:%S"):
    '''
    @description: 将日期“%Y-%m-%d %H:%M:%S”转换为格林威治时间戳
    @param:
    :param date: 日期
    :param format_string: 输入日期的格式
    @return: 格林威治时间戳
    '''
    time_array = time.strptime(date, format_string)
    time_stamp = int(time.mktime(time_array))
    return time_stamp

def findall(string, s):
    '''
    @description: 找到所有字符串中符合条件的子字符串，并返回索引元组
    @param:
    :param string: 用于查找的字符串
    :param format_string: 需要在字符串中查找的子字符串
    @return: 子字符串的索引元组
    '''
    ret = []
    index = 0
    while True:
        index = string.find(s, index)
        if index != -1:
            ret.append(index)
            index += len(s)
        else:
            break
    return tuple(ret)

def timestamp_to_date(time_stamp, format_string="%Y-%m-%d %H:%M:%S"):
    '''
    @description: 将格林威治时间戳转换为日期“%Y-%m-%d %H:%M:%S”
    @param:
    :param timestamp: 格林位置时间戳
    :param format_string: 输入日期的格式
    @return: 日期，格式为format_string中的格式
    '''
    time_array = time.localtime(time_stamp)
    str_date = time.strftime(format_string, time_array)
    return str_date

def get_range_metric_data(config, metric_dict, start_time, end_time, step):        
    '''
    @description: 利用Prometheus的HTTP API获取一个时间段内的时序数据
    @param:
    :param config: 访问prometheus服务器的配置
    :param metric_dict: 指标字典
    :param start_time: 时间段查询的开始时间
    :param end_time: 时间段查询的结束时间
    :param step: 时间段查询的步长
    @return: 未处理格式的指标数据
    '''    
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
    '''
    @description: 利用Prometheus的HTTP API获取当前时刻的时序数据
    @param:
    :param config: 访问prometheus服务器的配置
    :param metric_dict: 指标字典
    @return: 未处理格式的指标数据
    '''  
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
# 从Prometheus HTTP API获取范围数据的监控类
class Monitor_Query():
    '''
    @description: 从Prometheus HTTP API获取范围数据的监控类,主要作用是查询Prometheus
    数据库中的数据，并将其输出为json格式 
    '''
    def __init__(self, master_ip='localhost', prometheus_port='9090'):
        self.master_ip=master_ip
        # self.ip = address_utils.get_host_ip() 
        self.prometheus_port = prometheus_port

        
    def json_output(self, metric_datas, type_name, range_or_instant, query_choice):
        '''
        @description: 接收Prometheus返回的数据，利用json_change方法，对数据格式进行处理
        @param:
        :param metrics_datas: 未处理的指标
        :param type_name: 未处理的指标类型（docker or node or sflow）
        :param range_or_instant: 数据类型是时间段数据还是实时数据
        :param query_choice: Prometheus指标的名字
        @return: 处理后的数据格式
        '''  
        metric_dict = {}
        if "docker" in type_name:
            metric_dict['type'] = 'docker'
            metric_dict = self.json_change(metric_dict['type'], metric_dict, metric_datas, range_or_instant, query_choice)
        elif "node" in type_name:
            metric_dict['type'] = 'node'
            metric_dict = self.json_change(metric_dict['type'], metric_dict, metric_datas, range_or_instant, query_choice)
        elif "sflow" in type_name:
            metric_dict['type'] = 'sflow'
            metric_dict = self.json_change(metric_dict['type'], metric_dict, metric_datas, range_or_instant, query_choice)
        return metric_dict

    def json_change(self, type_name, metric_dict, metric_datas, range_or_instant, query_choice):
        '''
        @description: 对数据格式进行处理
        @param:
        :param metrics_datas: 未处理的指标
        :param type_name: 未处理的指标类型（docker or node or sflow）
        :param range_or_instant: 数据类型是时间段数据还是实时数据
        :param query_choice: Prometheus指标的名字
        @return: 处理后的数据格式
        '''  
        type_name_list = ['docker', 'node', 'sflow']
        for t in type_name_list:
            metric_dict[t] = {}
        # metric_dict[type_name]['type'] = type_name
        metric_dict[type_name]['metric_name'] = query_choice
        metric_dict[type_name]['metric_datas'] = {}
        for num , m in enumerate(metric_datas):
            # metric_dict[type_name].setdefault(query_choice, {}).setdefault('num_' + str(num), {}).setdefault('label', {}).setdefault(k, m['metric'][k])
            if range_or_instant == 'range':
                ori_values = m['values']
                data_time = []
                values = []
                for val in ori_values:
                    # 加入时间轴和数据，为绘制图像做准备
                    data_time.append(val[0])
                    values.append(val[1])
                metric_dict[type_name]['metric_datas'].setdefault('data' + str(num), {}).setdefault('name', 'data' + str(num))
                metric_dict[type_name]['metric_datas']['data' + str(num)]['time'] = data_time
                metric_dict[type_name]['metric_datas']['data' + str(num)]['value'] = values
                metric_dict[type_name]['metric_datas']['data' + str(num)]['label'] = m['metric']
            else:
                metric_dict[type_name]['metric_datas'].setdefault('data' + str(num), {}).setdefault('name', 'data' + str(num))
                metric_dict[type_name]['metric_datas']['data' + str(num)]['time'] = m['value'][0]
                metric_dict[type_name]['metric_datas']['data' + str(num)]['value'] = m['value'][1]
                metric_dict[type_name]['metric_datas']['data' + str(num)]['label'] = m['metric']
        return metric_dict
    
    def container_add_id(self, query_expr_list, container_id):
        '''
        @description: 通过添加id表达式，过滤特定的容器信息
        @param:
        :param query_expr_list: Prometheus原始表达式
        :param container_id: docker容器的ID号
        @return: Prometheus最终的表达式
        '''  
        index_tuple = findall(query_expr_list[0], '}')
        final_query_expr_list = []
        final_query_expr = ''
        for i in range(len(index_tuple)):
            # 根据大括号的个数以及子字符串的个数修改最终表达式的写法
            if i == 0 and len(index_tuple) > 1:
                final_query_expr += query_expr_list[0][:index_tuple[i]]
                final_query_expr = self.mod_expr(final_query_expr, query_expr_list, index_tuple[i])
                final_query_expr += "id=\"/docker/" + container_id + "\""
            elif i == 0 and len(index_tuple) == 1:
                # print(query_expr_list[0][t[i] - 1])
                final_query_expr += query_expr_list[0][:index_tuple[i]]
                final_query_expr = self.mod_expr(final_query_expr, query_expr_list, index_tuple[i])
                final_query_expr += "id=\"/docker/" + container_id + "\"" + query_expr_list[0][index_tuple[i]: ]
            elif i == len(index_tuple) - 1 and i != 0:
                final_query_expr += query_expr_list[0][index_tuple[i-1]:index_tuple[i]]
                final_query_expr = self.mod_expr(final_query_expr, query_expr_list, index_tuple[i])
                final_query_expr += "id=\"/docker/" + container_id + "\"" + query_expr_list[0][index_tuple[i]: ]
            else:
                final_query_expr += query_expr_list[0][index_tuple[i-1]:index_tuple[i]]
                final_query_expr = self.mod_expr(final_query_expr, query_expr_list, index_tuple[i])
                # if query_expr_list[0][t[i] - 1] == '\"':
                #     final_query_expr += "\","
                final_query_expr += "id=\"/docker/" + container_id + "\""
        final_query_expr_list.append(final_query_expr)
        return final_query_expr_list
    
    def mod_expr(self, final_query_expr, query_expr_list, index):
        '''
        @description: 修改表达式细节
        @param:
        :param final_query_expr: Prometheus最终表达式
        :param query_expr_list: Prometheus原始表达式
        :param index: findall()方法返回的匹配子字符串的位置索引
        @return: 最终的表达式
        ''' 
        if query_expr_list[0][index - 1] == '\"':
            final_query_expr += ","
        return final_query_expr


    def query(self, query_choice, range_or_instant, start_time, end_time, step, query_expr_list=[], container_id='0'):
        '''
        @description: 根据查询的指标类型输出内容和格式
        @param:
        :param query_choice: Prometheus指标的名字
        :param range_or_instant: 数据类型是时间段数据还是实时数据
        :param start_time: 时间段查询的开始时间
        :param end_time: 时间段查询的结束时间
        :param step: 时间段查询的步长
        :param query_expr_list: Prometheus原始表达式
        :param container_id: 容器ID
        @return: 处理后的查询数据
        '''
        # 查询类型判断，决定输出类型
        if 'other' in query_choice:
            # type_name = 'other'
            query_expr_list = query_expr_list
            if 'container' in query_expr_list[0]:
                query_choice = query_expr_list[0][query_expr_list[0].find('container'):].split('{')[0]
                type_name = 'other_docker'
                if container_id != '0':
                    query_expr_list = self.container_add_id(query_expr_list, container_id)
            elif 'node' in query_expr_list[0]:
                query_choice = query_expr_list[0][query_expr_list[0].find('node'):].split('{')[0]
                type_name = 'other_node'
            elif 'sflow' in query_expr_list[0]:
                query_choice = query_expr_list[0][query_expr_list[0].find('sflow'):].split('{')[0]
                type_name = 'other_sflow'
        else:
            query_expr_list = query_dict[query_choice]
        
        if "docker" in query_choice:
            type_name = 'docker'
            if container_id != '0':
                query_expr_list = self.container_add_id(query_expr_list, container_id)
        elif "node" in query_choice:
            type_name = 'node'
        elif "sflow" in query_choice:
            type_name = 'sflow'
        
        if start_time != '0' and end_time != '0':
            start_time = date_to_timestamp(start_time)
            end_time = date_to_timestamp(end_time)

        if range_or_instant == "range":
            metric_datas = get_range_metric_data({"PROMETHEUS_URL": 'http://' + self.master_ip + ':' + self.prometheus_port}, query_expr_list, start_time, end_time, step)
            # return json.dumps(self.json_output(metric_datas, type_name, range_or_instant, query_choice), sort_keys=True, indent=4)
            return self.json_output(metric_datas, type_name, range_or_instant, query_choice)

            # 存储
            # filename = range_or_instant + '_' + query_choice + '_' +  str(start_time) + '_to_' + str(end_time) + "_" + "_step_" + step
            # with open(filename + ".json", 'w') as f:
            #     json.dump(metric_datas, f, indent=4)  # 原始数据
            #     f.write("\n")
            #     json.dump(range_data, f, indent=4)  # 整理为一定格式的数据
        elif range_or_instant == "instant":
            metric_datas = get_instant_metric_data({"PROMETHEUS_URL": 'http://' + self.master_ip + ':' + self.prometheus_port}, query_expr_list)
            # return json.dumps(self.json_output(metric_datas, type_name, range_or_instant, query_choice), sort_keys=True, indent=4)
            return self.json_output(metric_datas, type_name, range_or_instant, query_choice)
            # return json.dumps({query_expr_list[0]:self.json_output(metric_datas, type_name, range_or_instant, query_choice)})

            # 存储
            # filename = range_or_instant + '_' + query_choice 
            # with open(filename + ".json", 'w') as f:
            #     json.dump(metric_datas, f, indent=4)  # 原始数据
            #     f.write("\n")
            #     json.dump(instant_data, f, indent=4)  # 整理为一定格式的数据
        else:
            # return json.dumps({self.master_ip:"Unknown choice!"})
            return {self.master_ip:"Unknown choice!"}


    def run_query(self, choice, range_or_instant, start_time="0", end_time="0", step="10", query_expr_list=[], container_id='0'):
        '''
        @description: 根据前端的输入查询特定指标
        @param:
        :param choice: 查询选项
        :param range_or_instant: 数据类型是时间段数据还是实时数据
        :param start_time: 时间段查询的开始时间
        :param end_time: 时间段查询的结束时间
        :param step: 时间段查询的步长
        :param query_expr_list: Prometheus原始表达式
        :param container_id: 容器ID
        @return: 处理后的查询数据
        '''
        if choice == '1':
            # return pprint.pprint(self.query('other_metric', range_or_instant, start_time, end_time, step, query_expr_list=query_expr_list))
            return self.query('other_metric', range_or_instant, start_time, end_time, step, query_expr_list=query_expr_list, container_id=container_id)
        elif choice == '2':
            # return pprint.pprint(self.query('node_cpu', range_or_instant, start_time, end_time, step))
            return self.query('node_cpu', range_or_instant, start_time, end_time, step)
        elif choice == '3':
            return self.query('node_mem', range_or_instant, start_time, end_time, step)
        elif choice == '4':
            return self.query('node_disk', range_or_instant, start_time, end_time, step)
        elif choice == '5':
            return self.query('node_load', range_or_instant, start_time, end_time, step)
        elif choice == '6':
            return self.query('docker_sent_traffic', range_or_instant, start_time, end_time, step, container_id=container_id)
        elif choice == '7':
            return self.query('docker_recv_traffic', range_or_instant, start_time, end_time, step, container_id=container_id)
        elif choice == '8':
            return self.query('sflow_ifinoctets', range_or_instant, start_time, end_time, step)
        else:
            # return json.dumps({self.master_ip:"Unknown choice!"})
            return {self.master_ip:"Unknown choice!"}

if __name__ == "__main__":
    # query = Monitor_Query()
    # start_words = """please choose a number：
    #                     1. Other metrics
    #                     2. CPU Utilization
    #                     3. Memory
    #                     4. Disk Utilization
    #                     5. Average Load
    #                     6. Docker Sent Traffic
    #                     7. Docker Receive Traffic
    #                     8. sFlow In throughput
    #                 """
    # choice = input(start_words)
    # query_expr_list = []
    # if choice == '1':
    #     query_expr_list.append(input("输入查询数据的Prometheus表达式："))
    # range_or_instant = input("选择数据输出类型：range or instant：")
    # if range_or_instant == "range":
    #     start_time = input("输入数据的起始时间,格式为\"%Y-%m-%d %H:%M:%S\",eg:2020-06-01 13:37:04:")
    #     end_time = input("输入数据的结束时间,格式为\"%Y-%m-%d %H:%M:%S\",eg:2020-06-01 13:45:04:")
    #     step = input("输入数据点的时间间隔（单位：s）:") # 每个数据点之间的间隔（单位：s）
    #     query.run_query(choice, range_or_instant, start_time, end_time, step, query_expr_list=query_expr_list)
    # elif range_or_instant == "instant":
    #     query.run_query(choice, range_or_instant, query_expr_list=query_expr_list)
    query = Monitor_Query()
    query.run_query(choice='2',range_or_instant='instant')
            
   
