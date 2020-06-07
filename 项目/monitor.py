import subprocess
import address_utils
import json

class Monitor():
    def __init__(self, master_ip, prometheus_port=9090, grafana_port=3000, sflow_rt_port=8008):
        self.master_ip=master_ip
        self.ip = address_utils.get_host_ip() #判断是否在master服务器
        self.prometheus_port = prometheus_port
        self.grafana_port = grafana_port
        self.sflow_rt_port = sflow_rt_port
    

    # TODO: 创建容器？import docker?
    def create_container(self):
        if self.ip == self.master_ip:
            shell =  "docker run -d -p 9100:9100   -v \"/proc:/host/proc\"   -v \"/sys:/host/sys\"   -v \"/:/rootfs\"   --privileged=true  --name=node-exporter  --net=host   weis88/node-exporter:v1   --path.procfs /host/proc   --path.sysfs /host/sys   --collector.filesystem.ignored-mount-points \"^/(sys|proc|dev|host|etc)($|/)\" \n" + \
            "docker run --volume=/:/rootfs:ro --volume=/var/run:/var/run:rw --volume=/sys:/sys:ro --volume=/var/lib/docker/:/var/lib/docker:ro --publish=8081:8080 --detach=true --name=cadvisor google/cadvisor:latest \n" + \
            "docker run -d -p 9090:9090 -v /home/monitor/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml --name prometheus --net=host weis88/prometheus:v1 \n" + \
            "docker run -d -i -p 3000:3000 -e \"GF_SERVER_ROOT_URL=http://grafana.server.name\" -e \"GF_SECURITY_ADMIN_PASSWORD=secret\" --net=host --name=grafana weis88/grafana:v1 \n" + \
            "docker run -d --name=sflow_pro -p 8008:8008 -p 6343:6343/udp weis88/sflow_pro:v1 -Dsnmp.ifname=yes"
            
        else:
            shell =  "docker run -d -p 9100:9100   -v \"/proc:/host/proc\"   -v \"/sys:/host/sys\"   -v \"/:/rootfs\"   --privileged=true  --name=node-exporter  --net=host   weis88/node-exporter:v1   --path.procfs /host/proc   --path.sysfs /host/sys   --collector.filesystem.ignored-mount-points \"^/(sys|proc|dev|host|etc)($|/)\" \n" + \
            "docker run --volume=/:/rootfs:ro --volume=/var/run:/var/run:rw --volume=/sys:/sys:ro --volume=/var/lib/docker/:/var/lib/docker:ro --publish=8080:8080 --detach=true --name=cadvisor google/cadvisor:latest \n" 
        print(shell)
        exitcode, result = subprocess.getstatusoutput(shell)
        if exitcode == "0":
            print(result)
            return json.dumps({self.ip:"Create monitor containers successfully!"})
        else:
            print(result)
            return json.dumps({self.ip:"Some Error!"})

    # 启动监控容器
    def start_monitor_container(self):
        if self.ip == self.master_ip:
            shell = "docker start node-exporter && docker start cadvisor && docker start prometheus && docker start grafana && docker start sflow_pro" 
        else:
            shell = "docker start node-exporter && docker start cadvisor"
        exitcode, result = subprocess.getstatusoutput(shell)
        if exitcode == "0":
            print(result)
            return json.dumps({self.ip:"Start to monitor successfully!"})
        else:
            print(result)
            return json.dumps({self.ip:"Some Error!"})
    
    # 停止监控容器
    def stop_monitor_container(self):
        if self.ip == self.master_ip:
            shell = "docker stop prometheus && docker stop grafana && docker stop cadvisor && docker stop node-exporter && docker stop sflow_pro"
        else:
            shell = "docker stop cadvisor && docker stop node-exporter"
        exitcode, result = subprocess.getstatusoutput(shell)
        if exitcode == "0":
            print(result)
            return json.dumps({self.ip:"Stop to monitor successfully!"})
        else:
            print(result)
            return json.dumps({self.ip:"Some Error!"})
    
    # 给出Prometheus容器的运行url，希望前端跳转此链接
    def go_to_prometheus(self):
        if self.ip == self.master_ip:
            prometheus_url = 'http://%s:%s' % (self.ip, self.prometheus_port)
            result = {'Prometheus':prometheus_url}
            return json.dumps(result)
    
    # 给出Grafana容器的运行url，希望前端跳转此链接
    def go_to_grafana(self):
        if self.ip == self.master_ip:
            grafana_url = 'http://%s:%s' % (self.ip, self.grafana_port)
            result = {'Grafana':grafana_url}
            return json.dumps(result)
    
    # 给出sFlow-RT容器的运行url，希望前端跳转此链接
    def go_to_sflow_rt(self):
        if self.ip == self.master_ip:
            sflow_rt_url = 'http://%s:%s' % (self.ip, self.sflow_rt_port)
            result = {'sFlow-RT':sflow_rt_url}
            return json.dumps(result)
    
    # 为user创建sFlow-RT，暂且认为在master上运行
    def create_sflow_rt(self, user, sflow_recv_port, sflow_front_end_port):
        sflow_rt_name = str(user) + "_sflow_rt"
        shell_ori = "sudo docker run -d --name=<name> -p <front>:8008 -p <recv>:6343/udp weis88/sflow_pro:v1 -Dsnmp.ifname=yes"
        shell = shell_ori.replace("<name>", sflow_rt_name).replace("<front>", sflow_front_end_port).replace("<recv>", sflow_recv_port)
        exitcode, result = subprocess.getstatusoutput(shell)
        if exitcode == "0":
            print(result)
            return json.dumps({str(user):"Create sFlow-RT successfully!"})
        else:
            print(result)
            return json.dumps({str(user):"Some Error!"})
    
    # 部署一个sflow项
    def deploy_one_sflow(self, ovs_name, ovs_ip):
        shell_ori = "sudo ifconfig <ovs_name> <ovs_ip> \n" + \
                "sudo ovs-vsctl -- --id=@sflow create sFlow agent=<ovs_name> target=\\\"172.24.1.181:6343\\\"  header=128  sampling=64 polling=1 -- set bridge <ovs_name> sflow=@sflow \n"
        shell = shell_ori.replace("<ovs_name>",ovs_name).replace("<ovs_ip>", ovs_ip)
        print(shell)
        exitcode, result = subprocess.getstatusoutput(shell)
        if exitcode == "0":
            print(result)
            return json.dumps({self.ip:"Deploy one sflow successfully!"})
        else:
            print(result)
            return json.dumps({self.ip:"Some Error!"})
    
    # 清楚一个sflow项
    def clear_one_sflow(self, ovs_name):
        shell = "sudo ovs-vsctl -- clear Bridge <ovs_name> sflow".replace("<ovs_name>", ovs_name)
        print(shell)
        exitcode, result = subprocess.getstatusoutput(shell)
        if exitcode == "0":
            print(result)
            return json.dumps({self.ip:"Clear one sflow successfully!"})
        else:
            print(result)
            return json.dumps({self.ip:"Some Error!"})
    
    # 输入参数OVS的ip列表、要发往的sflow_rt的IP地址、LAN 
    def deploy_sflow(self, ovs_ip_list, lan):
        # TODO:1)OVS 的名字是之前建立好的，应该要从数据库中获取，如何获取某个用户下的OVS的名字列表？; 2)sflow_recv_ip_port应该从哪获取？前端？数据库？
        sflow_recv_ip_port = "" # 根据LAN确定
        ovs_name = [] # 根据LAN确定

        # 设置sflow
        for name, ip in zip(ovs_name, ovs_ip_list):
            shell_ori = "sudo ifconfig <ovs_name> <ovs_ip> \n" + \
                    "sudo ovs-vsctl -- --id=@sflow create sFlow agent=<ovs_name> target=\\\"<sflow_recv_ip_port>\\\"  header=128  sampling=64 polling=1 -- set bridge <ovs_name> sflow=@sflow \n"
            shell = shell_ori.replace("<ovs_name>",name).replace("<sflow_recv_ip_port>",sflow_recv_ip_port).replace("<ovs_ip>", ip)
            subprocess.getstatusoutput(shell)
        return json.dumps({lan: 'sFlow deploy success!'})
    
    # 清除LAN的sflow
    def clear_sflow(self, lan):
        # TODO:
        ovs_name = [] # 根据LAN确定
        for name in ovs_name:
            shell = "sudo ovs-vsctl -- clear Bridge <ovs_name> sflow \n".replace("<ovs_name>",name)
            subprocess.getstatusoutput(shell)
        return json.dumps({lan: 'sFlow clear success!'})
        
    
    #TODO: 监控的细节？比如监控那个OVS？似乎没必要——直接通过url访问就可以