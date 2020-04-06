import re


class containers_ip():
    ip_dict = {}
    ip = ""
    name = ""

    def get_ip(self, dhcps):          # 传入所有dhcp的name
        for dhcp in dhcps:
            file_path = "configurations/dhcp/" + dhcp + "/dhcpd.leases"
            with open(file_path, 'r') as dhcp_info:
                lines = dhcp_info.readlines()
                for line in lines:
                    ip = re.search(r'(([01]{0,1}\d{0,1}\d|2[0-4]\d|25[0-5])\.){3}([01]{0,1}\d{0,1}\d|2[0-4]\d|25[0-5])', line)
                    if ip is None:
                        pass
                    else:
                        # print(ip.group())
                        self.ip = ip.group()
                        continue
                    name = re.findall(r'client-hostname "(.+?)";', line)
                    if len(name) == 0:
                        pass
                    else:
                        name = name[0]
                        # print(name, type(name))
                        self.name = name
                        self.ip_dict[self.name] = self.ip
                        continue
        # print(self.ip_dict)
        return self.ip_dict


if __name__ == '__main__':
    dhcps = ["dhcp1", "dhcp2"]
    ip_dict = containers_ip().get_ip(dhcps)
    print(ip_dict)