import requests
import time
import pprint

query_dict = {
    'cpu':['1 - avg(irate(node_cpu_seconds_total{mode="idle"}[1m]))by (instance)', ],
    'mem':['1 - node_memory_MemAvailable_bytes{ } / node_memory_MemTotal_bytes{ }', ],
}
# 从Prometheus HTTP API获取范围数据
def get_range_metric_data(config, metric_dict, history_len, step):
    
    metric_datas = []
    end_time = time.time()
    start_time = end_time - float(history_len) # 300s数据

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

def range_ori_data_to_kv(metric_datas):
    metric_dict = {}
    for m in metric_datas:
            instance = m.get('metric', {}).get('instance', {})
            ori_values = m.get('values', [])
            values = []
            for val in ori_values:
                values.append(val[1])
            metric_dict[instance] = values
    return metric_dict

def instant_ori_data_to_kv(metric_datas):
    metric_dict = {}
    for m in metric_datas:
        instance = m.get('metric', {}).get('instance', {})
        values = m.get('value', [])
        metric_dict[instance] = values[1]
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


def query(query_expr_list):
    range_or_instant = input("选择数据输出类型：range or instant：")
    if range_or_instant == "range":
        history_len = input("输入数据跨度（单位：s）: ") # 数据跨度（单位：s）
        step = input("输入数据点的时间间隔（单位：s）:") # 每个数据点之间的间隔（单位：s）
        metric_datas = get_range_metric_data({"PROMETHEUS_URL": "http://localhost:9090/"}, query_expr_list, history_len, step)
        pprint.pprint(range_ori_data_to_kv(metric_datas))
    elif range_or_instant == "instant":
        metric_datas = get_instant_metric_data({"PROMETHEUS_URL": "http://localhost:9090/"}, query_expr_list)
        pprint.pprint(instant_ori_data_to_kv(metric_datas))
    else:
        print('unknown choice,retry again!')

def run_query():
    start_words = """please choose a number：
                    1. CPU Utilization
                    2. Memory Utilization
                """
    while True:
        choice = input(start_words)
        if choice == 'exit':
            break
        elif choice == '1':
            query(query_dict['cpu'])
        elif choice == '2':
            query(query_dict['mem'])
        else:
            print('unknown choice,retry again!')

if __name__ == "__main__":
    run_query()
            
   
