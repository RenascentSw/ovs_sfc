'''
@Author: your name
@Date: 2020-06-24 12:10:51
@LastEditTime: 2020-07-15 10:29:36
@LastEditors: sw
@Description: In User Settings Edit
@FilePath: \ovs_sfc\项目\monitor_query_router.py
'''
from flask import Flask, request, jsonify
import monitor_query
from flask_cors import cross_origin
# import test_query
app = Flask(__name__)


query = monitor_query.Monitor_Query()
    
@app.route('/proquery')
@cross_origin()
def pro_query():
    choice = request.args.get('choice')
    container_id = request.args.get('container_id', '0')
    query_expr_list = []
    if choice == '1':    
        query_expr_list.append(request.args.get('query_expr_list'))
    range_or_instant = request.args.get('range_or_instant')
    if range_or_instant == "range":
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        step = request.args.get('step') # 每个数据点之间的间隔（单位：s）
        metric_datas = query.run_query(choice, range_or_instant, start_time, end_time, step, query_expr_list=query_expr_list, container_id=container_id)
    elif range_or_instant == "instant":
        metric_datas = query.run_query(choice, range_or_instant, query_expr_list=query_expr_list, container_id=container_id)
    # return metric_datas
    return jsonify(metric_datas)


# @app.route('/test')
# def test():
#     choice = request.args.get('choice')
#     range_or_instant = request.args.get('range_or_instant')
#     return test_query.query(choice, range_or_instant)

if __name__ == '__main__':
    app.run('0.0.0.0',port=5003, debug=True)
# http://47.108.183.103:5003/proquery?choice=1&range_or_instant=range&start_time=2020-06-26 12:15:50&end_time=2020-06-26 12:16:50&step=10&query_expr_list=sum(rate(container_cpu_usage_seconds_total{name!=""}[5m])) by (name) * 100
# http://47.108.183.103:5003/proquery?choice=1&range_or_instant=instant&query_expr_list=sum(rate(container_cpu_usage_seconds_total{ }[5m])) by (name) * 100&container_id=
# http://47.108.183.103:5003/proquery?choice=2&range_or_instant=range&start_time=2020-06-26 12:15:50&end_time=2020-06-26 12:16:50&step=10
# http://47.108.183.103:5003/proquery?choice=6&range_or_instant=instant
# http://47.108.183.103:5003/proquery?choice=1&range_or_instant=instant&query_expr_list=container_memory_rss{name!=""}&container_id=/docker/51917dad39429c06541c4fee978543594e438ad6e9b8aa14dd0e32b4f4acbd06
# 成功：
# http://47.108.183.103:5003/proquery?choice=1&range_or_instant=instant&query_expr_list=container_memory_rss{name!=""}&container_id=51917dad39429c06541c4fee978543594e438ad6e9b8aa14dd0e32b4f4acbd06


# http://47.110.80.166:5003/proquery?choice=3&range_or_instant=instant&query_expr_list=container_memory_rss{name!=""}
# http://47.110.80.166:5003/proquery?choice=3&range_or_instant=range&start_time=2020-07-15 10:20:50&end_time=2020-07-15 10:22:50&step=10
# http://47.110.80.166:5003/proquery?choice=1&range_or_instant=range&query_expr_list=container_memory_rss{name!=""}&start_time=2020-07-15 10:20:50&end_time=2020-07-15 10:22:50&step=10