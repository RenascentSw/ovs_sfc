import subprocess
import json
import docker
client = docker.from_env()
class Interface():  # define a class to describe Interface(interfaces which in RIPRouter contains Interface object)
    name=''
    ip=''
    netmask=''

class RIPRouter():  # define a calss to dercribe RIPRouter (it contain many funcations to config a router)
    name=''
    image_name=''
    type=''
    subtype=''
    virtualization=''
    interfaces=[]
    networks=[]
    def __init__(self):  # instantiate the router
        print("\033[32;1m" + 'router instantiate successfully'+ "\033[0m")
    # some functions are temporarily useless

    def create(self):  # create the router without running
        try:
            container=client.containers.create(image=self.image_name,
                                     name=self.name,
                                     command="/bin/bash",
                                     cpuset_cpus="0,1",
                                     cpu_shares=2,
                                     cpu_period=100000,
                                     mem_limit="512m",
                                     network_mode="none",
                                     user="root",
                                     detach=True,
                                     tty=True,
                                     stdin_open=True,
                                     oom_kill_disable=True,
                                     publish_all_ports=True,
                                     privileged=True)
        except BaseException:
            self.feedback(0, self.name, 'create','(maybe existed)')
        else:
            self.feedback(container.id,self.name,'create','')

    def run(self):  # create and run a router
        try:
            container=client.containers.run(image=self.image_name,
                                     name=self.name,
                                     command="/bin/bash",
                                     cpuset_cpus="0,1",
                                     cpu_shares=2,
                                     cpu_period=100000,
                                     mem_limit="512m",
                                     network_mode="none",
                                     user="root",
                                     detach=True,
                                     tty=True,
                                     stdin_open=True,
                                     oom_kill_disable=True,
                                     publish_all_ports=True,
                                     privileged=True)
        except BaseException:
            self.feedback(0, self.name, 'run'+'(maybe existed)')
        else:
            self.feedback(container.id, self.name, 'run'+'')

    def startswitch(self,bool):  # control the start and stop in a router
        if bool==True:
            client.containers.get(self.name).start()
            self.feedback(client.containers.get(self.name).status=='running', self.name, 'start','')
        else:
            client.containers.get(self.name).stop()
            self.feedback(client.containers.get(self.name).status == 'exited', self.name, 'stop','')

    def protocolswitch(self,bool):  # control the protocol enable and diable in a router
        if bool==True:
            client.containers.get(self.name).exec_run(cmd='zebra -d',detach=True)
            client.containers.get(self.name).exec_run(cmd='ripd -d', detach=True)
        else:
            #client.containers.get(self.name).exec_run(cmd='kill $(cat /run/quagga/ripd.pid)',detach=True)
            subprocess.getstatusoutput('sudo docker exec -itd ' + self.name + ' /bin/bash -c \'kill $(cat /run/quagga/ripd.pid)\'')

    def default_config(self):  # edit the default config information and send it to router
        content_1 = 'hostname ripd\npassword zebra\nrouter rip\n'
        content_2 = ''
        content_3 = 'version 2\nlog stdout\n'
        filepath='/home/'
        for interface in self.interfaces:
            str = json.dumps(interface)
            dict = json.loads(str)
            interface = Interface()
            interface.__dict__ = dict
            content_2 = content_2 + 'network ' + interface.name + '\n'
        content = content_1 + content_2 + content_3
        configfile = open(filepath+'ripd.conf', 'w+')
        configfile.write(content)
        configfile.close()
        status1=subprocess.getstatusoutput('sudo docker exec -itd '+self.name+' /bin/bash -c \'rm /etc/quagga/ripd.conf\'')
        status2=subprocess.getstatusoutput('sudo docker cp '+filepath+'ripd.conf '+self.name+':/etc/quagga/')
        status3=subprocess.getstatusoutput('sudo rm '+filepath+'ripd.conf')
        status=status1[0]&status2[0]&status3[0]
        self.executionresult(status, self.name + ' default config successfully', self.name + ' default config failed')

    def manual_config(self):  # edit the manual config information and send it to router
        content_1 = 'hostname ripd\npassword zebra\nrouter rip\n'
        content_2 = ''
        content_3 = 'version 2\nlog stdout\n'
        filepath = '/home/'
        for network in self.networks:
            content_2=content_2+ 'network ' + network + '\n'
        content =content_1+content_2+content_3
        configfile = open(filepath + 'ripd.conf', 'w+')
        configfile.write(content)
        configfile.close()
        status1=subprocess.getstatusoutput('sudo docker exec -itd ' + self.name + ' /bin/bash -c \'rm /etc/quagga/ripd.conf\'')
        status2=subprocess.getstatusoutput('sudo docker cp ' + filepath + 'ripd.conf ' + self.name + ':/etc/quagga/')
        status3=subprocess.getstatusoutput('sudo rm ' + filepath + 'ripd.conf')
        status = status1[0] & status2[0] & status3[0]
        self.executionresult(status, self.name + ' manual config successfully', self.name + ' manual config failed')

    def executionresult(self,status,success,failure):  # feedback information
        if status==0:
           print("\033[32;1m" + success + "\033[0m")
        else:
            print("\033[31;1m" + failure + "\033[0m")

    def feedback(self,result,container,fun,tail):  # feedback information
        if result:
            print("\033[32;1m" + container+' '+fun+' successfully'+tail + "\033[0m")
        else:
            print("\033[31;1m" +  container+' '+fun+' failure' + tail+"\033[0m")

class OSPFRouter():  # define a calss to dercribe OSPFRouter(unfinished)
    name=''

class BGPRouter():  # define a calss to dercribe BGPRouter(unfinished)
    name=''



# debug the class
# def createGateway(gateway):
#     router_dict = gateway
#     if router_dict['subtype'] == 'rip':  # judge the router's subtype(unfinished)
#         router = RIPRouter()  # initialize the router
#     router.__dict__ = router_dict  # turn the dictionary to object
#     router.create()  # create the router without start
#     router.startswitch(bool=True)
#     if len(router.networks):
#         router.manual_config()  # manual mode
#     else:
#         router.default_config()  # default mode
#     #router.enable()  # enable the protocol which the router support
#     router.protocolswitch(bool=True)
#
# if __name__=='__main__':
#     with open("testjson.json", 'r') as f:
#         topo = json.load(f)
#         f.close()
#     gateway=topo['gateway']
#     createGateway(gateway)
