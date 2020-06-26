import subprocess

def create_container():
    shell =  "docker run -d -p 9100:9100   -v \"/proc:/host/proc\"   -v \"/sys:/host/sys\"   -v \"/:/rootfs\"   --privileged=true  --name=node-exporter  --net=host   prom/node-exporter   --path.procfs /host/proc   --path.sysfs /host/sys   --collector.filesystem.ignored-mount-points \"^/(sys|proc|dev|host|etc)($|/)\" \n" + \
    "docker run --volume=/:/rootfs:ro --volume=/var/run:/var/run:rw --volume=/sys:/sys:ro --volume=/var/lib/docker/:/var/lib/docker:ro --publish=8081:8080 --detach=true --name=cadvisor google/cadvisor:latest \n" + \
    "docker run -d -p 9090:9090 -v /home/monitor/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml --name prometheus --net=host prom/prometheus \n" + \
    "docker run -d -i -p 3000:3000 --privileged=true -e \"GF_SERVER_ROOT_URL=http://grafana.server.name\" -e \"GF_SECURITY_ADMIN_PASSWORD=secret\" --net=host --name=grafana grafana/grafana \n" + \
    "docker run -d --name=sflow_pro -p 8008:8008 -p 6343:6343/udp sflow/prometheus -Dsnmp.ifname=yes"
    print(shell)
    _, result = subprocess.getstatusoutput(shell)
    print(result)

def start_container():
    shell = "docker start node-exporter && docker start sflow_pro && docker start cadvisor && docker start prometheus && docker start grafana"
    print(shell)
    exitcode, result = subprocess.getstatusoutput(shell)
    print("result:",result,"exitcode:",exitcode)

def stop_container():
    shell = "docker stop prometheus && docker stop grafana && docker stop sflow_pro && docker stop cadvisor && docker stop node-exporter"
    print(shell)
    exitcode, result = subprocess.getstatusoutput(shell)
    print("result:",result,"exitcode:",exitcode)

def deploy_sflow():
    name = input("input ovs_name:")
    ip = input("input ip:")
    shell_ori = "sudo ifconfig <ovs_name> <ovs_ip> \n" + \
                "sudo ovs-vsctl -- --id=@sflow create sFlow agent=<ovs_name> target=\\\"172.24.1.181:6343\\\"  header=128  sampling=10 polling=1 -- set bridge <ovs_name> sflow=@sflow \n"
    shell = shell_ori.replace("<ovs_name>",name).replace("<ovs_ip>", ip)
    print(shell)
    _, result = subprocess.getstatusoutput(shell)
    print(result)

def clear_sflow():
    name = input("input ovs_name:")
    shell = "sudo ovs-vsctl -- clear Bridge <ovs_name> sflow".replace("<ovs_name>", name)
    print(shell)
    _, result = subprocess.getstatusoutput(shell)
    print(result)

def run():
    start_words = """please choose a number：
                    1. create
                    2. start 
                    3. stop
                    4. deploy_sflow
                    5. clear_sflow
                """
    # print(start_words)
    while True:
        choice = input(start_words)
        if choice == 'exit':
            break
        elif choice == '1':
            create_container()
        elif choice == '2':
            start_container()
        elif choice == '3':
            stop_container()
        elif choice == "4":
            deploy_sflow()
        elif choice == "5":
            clear_sflow()
        else:
            print('unknown choice,retry again!')

if __name__ == '__main__':
    run()
