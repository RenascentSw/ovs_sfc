import sys
import pprint
import numpy as np
import matplotlib.pyplot as plt
from putil import mkAXS


agent_dict = {
    '10.0.0.3':'s1',
    '10.0.0.101':'s1',
    '10.0.0.102':'s2',
    '10.0.0.103':'s3',
    '10.0.0.104':'s4'
}
# 在我的 notebook 里，要设置下面两行才能显示中文
# plt.rcParams['font.family'] = ['sans-serif']
# 如果是在 PyCharm 里，只要下面一行，上面的一行可以删除
# plt.rcParams['font.sans-serif'] = ['SimHei']
def run_log():
    monitor_data = dict(agent={})
    with open('monitor_ori.log', 'r') as f:
        for line in f:
            if line.startswith('s'):
                continue
            line = line.split(',')
            monitor_data['agent'].setdefault(line[1], {})
            if (len(line[2]) >= 4):
                monitor_data['agent'][line[1]].setdefault(line[2], {})
                monitor_data['agent'][line[1]][line[2]].setdefault('In', []).append(int(line[4]))
                monitor_data['agent'][line[1]][line[2]].setdefault('Out', []).append(int(line[5]))
    # pprint.pprint(monitor_data)
    cal_sflow_bw(monitor_data['agent'])


#  calculate difference value
def cal_bw_delta_data(list_data):
    delta_data = []
    length = len(list_data)
    for i in range(length-1):
        delta_data.append((list_data[i+1] - list_data[i]) * 8 / 1e6)
    
    return delta_data


# calculate bandwidth
def cal_sflow_bw(agent_data):
    plot_data = {}
    lss = ['-', '--', '-.', ':', ]
    filled_markers = ('x', '*', 'o', 'v', '^', '<', '>', '8', 's', 'p', 'h', 'H', 'D', 'd', 'P', )
    for agent in agent_data:
        ax1 = mkAXS()
        plot_data.setdefault(agent, {})
        for interface in agent_data[agent]:
            plot_data[agent].setdefault(interface, {})
            for i, param in enumerate(agent_data[agent][interface]):
                plot_data[agent][interface].setdefault(param, []).extend(cal_bw_delta_data(agent_data[agent][interface][param]))
                ax1.errorbar(x=range(len(plot_data[agent][interface][param])), y=plot_data[agent][interface][param], label=u'端口：'+interface[:3]+u' 参数: '+param,
                ls=lss[i % len(lss)], marker=filled_markers[i], markersize=5)
                # plt.plot(range(len(plot_data[agent][interface][param])), plot_data[agent][interface][param], label=u'端口：'+interface[:3]+u' 参数: '+param,
                # ls=lss[i % len(lss)], marker=filled_markers[i], markersize=5)
        ax1.set(title='交换机' + agent_dict[agent] + '：端口吞吐量', xlabel=u'时间 (s)', ylabel=u'吞吐量 '+'(Mbits/s)')
        ax1.legend(loc='best')
    # plt.xlabel(u'时间 (s)')
    # plt.ylabel(u'吞吐量 '+'(Mbits/s)')
    # plt.legend(loc='best')
    # plt.title('交换机s1：端口吞吐量')
    plt.show()
    pprint.pprint(plot_data)
    # return plot_data

if __name__ == '__main__':
    run_log()
    # print(data)
    
    
    # plot_graph(plot_data)
    


