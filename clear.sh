sudo ovs-vsctl del-br s1
sudo ovs-vsctl del-br s2
sudo ovs-vsctl del-br s3
sudo ovs-vsctl del-br s4
sudo ovs-vsctl del-br s5
sudo ovs-vsctl del-br s6
sudo ovs-vsctl del-br s7
sudo ovs-vsctl del-br s8
sudo ovs-vsctl del-br s9
sudo ovs-vsctl del-br s10
sudo ovs-vsctl del-br s11
sudo docker rm -f web1
sudo docker rm -f web2
sudo docker rm -f web3
sudo docker rm -f nginx1
sudo docker rm -f dhcp1
sudo docker rm -f dhcp2
sudo docker rm -f gw1
sudo docker rm -f gw2
sudo docker rm -f h1
sudo docker rm -f h2
sudo docker rm -f h3
sudo docker rm -f h4
sudo docker rm -f h5
sudo docker rm -f h6
sudo docker rm -f h7
sudo docker rm -f h8
sudo docker rm -f h9
sudo docker rm -f h10
sudo docker rm -f h11
sudo docker rm -f h12
sudo ip link del dhcp1
sudo ip link del dhcp2
sudo rm -rf ~/Code-of-container/development/configurations/




