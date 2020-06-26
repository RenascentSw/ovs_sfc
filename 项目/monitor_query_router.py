from flask import Flask, request
import monitor_query
# import test_query
app = Flask(__name__)


query = monitor_query.Monitor_Query()
    
@app.route('/proquery')
def pro_query():
    choice = request.args.get('choice')
    query_expr_list = []
    if choice == '1':
        query_expr_list.append(request.args.get('query_expr_list'))
    range_or_instant = request.args.get('range_or_instant')
    if range_or_instant == "range":
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        step = request.args.get('step') # 每个数据点之间的间隔（单位：s）
        metric_datas = query.run_query(choice, range_or_instant, start_time, end_time, step, query_expr_list=query_expr_list)
    elif range_or_instant == "instant":
        metric_datas = query.run_query(choice, range_or_instant, query_expr_list=query_expr_list)
    return metric_datas


# @app.route('/test')
# def test():
#     choice = request.args.get('choice')
#     range_or_instant = request.args.get('range_or_instant')
#     return test_query.query(choice, range_or_instant)

if __name__ == '__main__':
    app.run('0.0.0.0',port=5001, debug=True)
# http://47.108.183.103:5003/proquery?choice=1&range_or_instant=range&start_time=2020-06-26 12:15:50&end_time=2020-06-26 12:16:50&step=10&query_expr_list=sum(rate(container_cpu_usage_seconds_total{name!=""}[5m])) by (name) * 100
# http://47.108.183.103:5003/proquery?choice=1&range_or_instant=instant&query_expr_list=sum(rate(container_cpu_usage_seconds_total{ }[5m])) by (name) * 100
# http://47.108.183.103:5003/proquery?choice=2&range_or_instant=range&start_time=2020-06-26 12:15:50&end_time=2020-06-26 12:16:50&step=10
# http://47.108.183.103:5003/proquery?choice=6&range_or_instant=instant