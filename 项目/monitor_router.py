from flask import Flask, request


app = Flask(__name__)



    
@app.route('/')
def hello_world():
    return request.args.__str__()
# def Run(monitor):
#     monitor = monitor

# @app.route('/createmonitor')
# def createmonitor():
#     result = monitor.create_monitor_container()
#     return result

# @app.route('/startmonitor')
# def startmonitor():
#     result = monitor.start_monitor_container()
#     return result

# @app.route('/stopmonitor')
# def stopmonitor():
#     result = monitor.stop_monitor_container()
#     return result

# @app.route('/prometheus')
# def prometheus_url():
#     result = monitor.go_to_prometheus()
#     return result

# @app.route('/grafana')
# def grafana_url():
#     result = monitor.go_to_grafana()
#     return result

# @app.route('/sflow_rt')
# def sflow_rt_url():
#     result = monitor.go_to_sflow_rt()
#     return result

# @app.route('/createsflowrt')
# def create_sflowrt():
#     user=request.args.get('user')
#     # sflow_recv_port,sflow_front_end_port由前端输入
#     result = monitor.go_to_sflow_rt(user, sflow_recv_port, sflow_front_end_port)
#     return result

# @app.route('/deployonesflow')
# def deploy_one_sflow():
#     user=request.args.get('user')
#     # sflow_recv_port,sflow_front_end_port由前端输入
#     result = monitor.deploy_one_sflow(ovs_name, ovs_ip)
#     return result

# @app.route('/clearonesflow')
# def clear_one_sflow():
#     user=request.args.get('user')
#     # sflow_recv_port,sflow_front_end_port由前端输入
#     result = monitor.clear_one_sflow(ovs_name):
#     return result
    
# app.run(host='0.0.0.0', debug=True)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)