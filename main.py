from napalm import get_network_driver
from pprint import pprint
from tabulate import tabulate
import ipaddress
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import yaml,json
import easygui

logging.basicConfig(
    format = '%(threadName)s %(name)s %(levelname)s: %(message)s',
    level=logging.INFO)

######## Part with information from Esigth or another Source of True ######

#Define List of equipment, where is each object in list represent Network Node and its parameters
equipment_list = [{'Hostname':'AR1',
                   'IP-mgmt':'192.168.111.10'},
                  {'Hostname':'AR2',
                   'IP-mgmt':'192.168.111.20'},
                  {'Hostname':'AR3',
                  'IP-mgmt':'192.168.111.30'}]

######### Main bony ############

def enrichment_with_ip_interfaces(node):
    '''
    This function for enrichment current node object with additional keys(fields) - Ip Interfaces
    :param node: Node object (dictionary)
    :return: node (enriched) object with 'IP_interfaces' key if success. In failure - not enriched node and error description
    '''
    start_msg = '===> {} Connection: {}'
    received_msg = '<=== {} Received: {}'
    logging.info(start_msg.format(datetime.now().time(), node['IP-mgmt']))
    driver = get_network_driver('huawei_vrp')
    try:
        with driver(hostname=node['IP-mgmt'],password='huawei',username='huawei') as device:
            #Gather ip information from interfaces
            result = device.get_interfaces_ip()
            #Output information
            node['IP_interfaces'] = result
        node_modified(node)
        return node
    except Exception as err:
        print('Some unexpected error ocurred:\n', err)
        return node

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

def where_is_ip(ip_address,equipment_list_modified):
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
    success_search_flag = False
    for node in equipment_list_modified:
        if node.get('IP_interfaces'):
            for interface, ipv4interface in node['IP_interfaces'].items():
                for subnet in ipv4interface:
                    if ip in subnet.network:
                        success_search_flag = True
                        print(f'Gotcha! This address {ip} belong to network {subnet.network}\n'
                              f'This is subnet on interface of Router {node["Hostname"]} and interface is {interface}')
        else:
            print(f'Node {node["Hostname"]} is skipped, because there is no IP-interfaces in current snapshot 🙅‍♂️')
    if not success_search_flag:
        print('Sorry, but nothing was fing ... ')

def save_snapshot(nodes,mode='yaml'):
    '''
    This function save current state of network (nodes and their properties) as snapshot. Two variants of saving to file:
     YAML (by default) and JSON.
    :param nodes: List of equipment (nodes)
    :param mode: for future support of another struct data
    :return: File in current directory with extension - YAML or JSON
    '''
    try:
        if mode == 'yaml':
            with open(f'snapshot_{datetime.now().strftime("%d-%b-%Y_%H-%M-%S")}.yml','w') as file:
                yaml.dump(nodes,file)
                print(f'Snapshot was saved successfully!')
        if mode == 'json': # Error will be ocurred - cause we can't serialize IPv4Interface obj. Will use pickle in future releases
            with open(f'snapshot_{datetime.now().strftime("%d-%b-%Y_%H-%M-%S")}.json','w') as file:
                json.dump(nodes,file)
    except Exception as err:
        print(' Some error occurred while saving snapshot!\n',err)

def init_snapshot(mode='yaml'):
    '''
    This function help to initialize snapshot of network interfaces state
    :param mode: for future support of another struct data
    :return: List of nodes from snapshot
    '''
    try:
        if mode == 'yaml':
            path = easygui.fileopenbox()
            with open(path,'r+') as file:
                equipment_list = yaml.load(file,Loader=yaml.Loader)
            return equipment_list
    except Exception as err:
        print(' Some error occurred while opening snapshot!\n',err)
        return []



if __name__=='__main__':

    '''
    equipment_list = [{'Hostname': 'AR1',
               'IP-mgmt': '192.168.111.10'},
              {'Hostname': 'AR2',
               'IP-mgmt': '192.168.111.20'},
              {'Hostname': 'AR3',
               'IP-mgmt': '192.168.111.30'},
                {'Hostname': 'AR4',
                   'IP-mgmt': '192.168.111.40'},
                  {'Hostname': 'AR5',
                   'IP-mgmt': '192.168.111.50'},
                  {'Hostname': 'AR6',
                   'IP-mgmt': '192.168.111.60'}]
    
    '''

    begin = datetime.now()
    print(begin)

    equipment_list = init_snapshot()

    pprint(equipment_list)
    '''
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_list = []
        for node in equipment_list:
            future = executor.submit(enrichment_with_ip_interfaces,node)
            future_list.append(future)
    save_snapshot(equipment_list)
    '''

    where_is_ip('1.1.1.12',equipment_list)
    print(datetime.now()-begin)


    
    
    







