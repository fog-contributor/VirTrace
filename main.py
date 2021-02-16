from napalm import get_network_driver
from pprint import pprint
from tabulate import tabulate
import ipaddress


######## Part with information from Esigth or another Source of True ######

#Define List of equipment, where is each object in list represent Network Node and its parameters
equipment_list = [{'Hostname':'AR1',
                   'IP-mgmt':'192.168.1.1'},
                  {'Hostname':'AR2',
                   'IP-mgmt':'192.168.2.2'},
                  {'Hostname':'AR3',
                  'IP-mgmt':'192.168.3.3'}]

######### Main bony ############


def enrichment_with_ip_interfaces(node):
    '''
    This function for enrichment current node object with additional keys(fields) - Ip Interfaces
    :param node: Node object (dictionary)
    :return: node (enriched) object with 'IP_interfaces' key if succes. In failure - not enriched node and error description
    '''
    driver = get_network_driver('huawei_vrp')
    try:
        with driver(hostname=node['IP-mgmt'],password='huawei',username='huawei') as device:
            #Gather ip information from interfaces
            result = device.get_interfaces_ip()
            #Output information
            node['IP_interfaces'] = result
        return node
    except Exception as err:
        print('Some unexpected error ocurred:\n', err)
        return node


def node_list_of_interfaces(node):
    '''
    This function see if we have 'IP_interfaces' key and can obtain list of interfaces in ipaddress.ip_int
    object notation
    :param node: Object node
    :return: List of  objects - ipaddress.ip_int if node have it. Empty list - overwise.
    '''

    if node.get('IP_interfaces'):
        list_of_interfaces = []
        for interface in node['IP_interfaces'].values():
            for ip_int in list(interface['ipv4'].keys()):
                list_of_interfaces.append((ip_int + '/' + str(interface['ipv4'][ip_int]['prefix_length'])))
        ip_int_obj_list = [ipaddress.ip_interface(i) for i in list_of_interfaces]
        return ip_int_obj_list
    else:
        print('No such key\parameter in Node object')
        return []

def node_modified(node):
    '''
    This function will be modified node dictionary - with IP-interfaces as IP_interface objects of ipadress module

    'IP_interfaces': {'GigabitEthernet0/0/0': [IPv4Interface('10.0.23.3/24'), IPv4Interface('10.0.13.3/24')],
                        'LoopBack0': {'ipv4': {'3.3.3.3': {'prefix_length': 32}}},
                        'LoopBack1': {'ipv4': {'192.168.3.3': {'prefix_length': 32}}},
                        'Vlanif10': {'ipv4': {'192.168.12.10': {'prefix_length': 24}}}}}]

    :param node:
    :return: modified node
    '''
    if node.get('IP_interfaces'):
        for name_interface, ipv4_addresses in node['IP_interfaces'].items():
            li_ipv4 = []
            for prefix, prefix_lenght in ipv4_addresses['ipv4'].items():
                ipv4_interface = ipaddress.ip_interface((prefix + '/' + str(prefix_lenght['prefix_length'])))
                li_ipv4.append(ipv4_interface)
            node['IP_interfaces'][name_interface] = li_ipv4
        return node
    else:
        print('No such key\parameter in Node object')
        return node



def where_is_ip(ip_address):
    '''
    This function for understanding - to which interface belong ip_address.
    ip_address - string.
    If we find match - return Name of router (and interface) in tuple - ('R1':'GigabitEthernet0/1') (without VRF reffering :(()
    If we don't find any matches - return  None (empty tuple)
    :param ip_address:
    :return:
    '''
    #verify, that user input was correct (IP-address)
    try:
        ip = ipaddress.ip_address(ip_address)
    except ValueError as err:
        print('Incorrect input for IP-address:\n'+str(err))
        return None




if __name__=='__main__':
    '''
    equipment_list = [{'Hostname': 'AR1',
                   'IP-mgmt': '192.168.1.1'},
                  {'Hostname': 'AR2',
                   'IP-mgmt': '192.168.2.2'},
                  {'Hostname': 'AR3',
                   'IP-mgmt': '192.168.3.3'}]  
    '''
    equipment_list = [{'Hostname': 'AR1',
      'IP-mgmt': '192.168.1.1',
      'IP_interfaces': {'GigabitEthernet0/0/0': {'ipv4': {'10.0.12.1': {'prefix_length': 24}}},
                        'GigabitEthernet0/0/1': {'ipv4': {'10.0.13.1': {'prefix_length': 24}}},
                        'LoopBack0': {'ipv4': {'1.1.1.1': {'prefix_length': 32}}},
                        'LoopBack1': {'ipv4': {'192.168.1.1': {'prefix_length': 32}}},
                        'LoopBack222': {'ipv4': {'111.111.111.111': {'prefix_length': 32},
                                                 '12.12.12.12': {'prefix_length': 32}}}}},
     {'Hostname': 'AR2',
      'IP-mgmt': '192.168.2.2',
      'IP_interfaces': {'GigabitEthernet0/0/0': {'ipv4': {'10.0.12.2': {'prefix_length': 24}}},
                        'GigabitEthernet0/0/1': {'ipv4': {'10.0.23.2': {'prefix_length': 24}}},
                        'LoopBack0': {'ipv4': {'2.2.2.2': {'prefix_length': 32}}},
                        'LoopBack1': {'ipv4': {'192.168.2.2': {'prefix_length': 32}}}}},
     {'Hostname': 'AR3',
      'IP-mgmt': '192.168.3.3',
      'IP_interfaces': {'GigabitEthernet0/0/0': {'ipv4': {'10.0.23.3': {'prefix_length': 24}}},
                        'GigabitEthernet0/0/1': {'ipv4': {'10.0.13.3': {'prefix_length': 24}}},
                        'LoopBack0': {'ipv4': {'3.3.3.3': {'prefix_length': 32}}},
                        'LoopBack1': {'ipv4': {'192.168.3.3': {'prefix_length': 32}}},
                        'Vlanif10': {'ipv4': {'192.168.12.10': {'prefix_length': 24}}}}}]
    #At first - enrich nodes with IP_interfaces
    #for node in equipment_list:
        #enrichment_with_ip_interfaces(node)
    #pprint(equipment_list)
    #At second - translate IP_interfaces into IP_int object

    for node in equipment_list:
        node_modified(node)
    pprint(equipment_list)

    '''
        dict_of_ip_int ={}
    for node in equipment_list:
        dict_of_ip_int[node['Hostname']] = node_list_of_interfaces(node)
    pprint(dict_of_ip_int)
    ip_address = input('Input IP-address')
    try:
        ip = ipaddress.ip_address(ip_address)
    except ValueError as err:
        print('Incorrect input for IP-address:\n'+str(err))
        exit(-1)
    success_search_flag = False
    for node,interfaces in dict_of_ip_int.items():
        for interface in interfaces:
            if ip in interface.network:
                success_search_flag = True
                print(f'Gotcha! This address {ip} belong to network {interface.network}\n'
                      f'This is subnet on interface of Router {node}')
    if not success_search_flag:
        print('Sorry, but nothing was fing ... ')

    
    
    
    '''






