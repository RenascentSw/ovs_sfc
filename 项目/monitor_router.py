from flask import Flask, request


app = Flask(__name__)

# def Run(monitor):
#     monitor = monitor

    
@app.route('/')
def hello_world():
    return request.args.__str__()

# @app.route('/startmonitor')
# def startmonitor():
#     result = monitor.start_monitor_container
#     return result

# @app.route('/stopmonitor')
# def startmonitor():
#     result = monitor.stop_monitor_container
#     return result

# @app.route('/prometheus')
# def startmonitor():
#     result = monitor.go_to_prometheus
#     return result

# @app.route('/grafana')
# def startmonitor():
#     result = monitor.go_to_grafana
#     return result

# @app.route('/sflow_rt')
# def startmonitor():
#     result = monitor.go_to_sflow_rt
#     return result
    
# app.run(host='0.0.0.0', debug=True)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)