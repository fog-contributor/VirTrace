from napalm import get_network_driver
from pprint import pprint
from tabulate import tabulate
import ipaddress
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import textfsm
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

def get_route_to_ip(dest_ip,node,vendor='huawei'):
    '''
    This function get ip route output from cli (for some vendor)
    :param dest_ip:
    :param node:
    :param vendor:
    :return:
    '''
    if vendor=='huawei':
        driver = get_network_driver('huawei_vrp')
        try:
            with driver(hostname=node['IP-mgmt'],password='huawei',username='huawei') as device:
                #Gather ip information from interfaces
                ip_route = device.cli([f'display ip rout {dest_ip} verbose'])
                print(ip_route)
                ######vrrp_output = device.cli(f'display ip routing table {dest_ip} verbose')
            #parse output information with TextFSM
            with open('textfsm_huawei_routing_verbose.template') as template:
                fsm = textfsm.TextFSM(template)
                result = fsm.ParseText(list(ip_route.values())[0])
            print(result)
            print(tabulate(result,headers=fsm.header))
            return result
        except Exception as err:
            print('Some unexpected error ocurred:\n', err)
            return None


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
    :return: list of dictionaries [ {'name':'...','interface':'...'} ]
    '''
    #verify, that user input was correct (IP-address)
    try:
        ip = ipaddress.ip_address(ip_address)
    except ValueError as err:
        print('Incorrect input for IP-address:\n'+str(err))
        return None
    success_search_flag = False
    list_of_success = []
    for node in equipment_list_modified:
        if node.get('IP_interfaces'):
            for interface, ipv4interface in node['IP_interfaces'].items():
                for subnet in ipv4interface:
                    if ip in subnet.network:
                        success_search_flag = True
                        print(f'Gotcha! This address {ip} belong to network {subnet.network}\n'
                              f'This is subnet on interface of Router {node["Hostname"]} and interface is {interface}')
                        list_of_success.append({'name':f'{node["Hostname"]}','interface':interface})
        else:
            print(f'Node {node["Hostname"]} is skipped, because there is no IP-interfaces in current snapshot 🙅‍♂️')
    if not success_search_flag:
        print('Sorry, but nothing was fing ... ')
        return []
    return list_of_success

def create_json_to_visualize(source_ip,destination_ip,snapshot_data):
    '''
    This function create graph.json file - that will be used for visualization of traceroute.
    Should be notice, that traceroute in visualization - is not simmetrical. Can be assimetrical paths in back direction.
    :param source_ip[str]: source_ip (from which)
    :param destination_ip[str]: destination_ip  (to which)
    :param snapshot_data[Object]:
    :return: file graph.json
    '''
    source = where_is_ip(source_ip,snapshot_data) #[ {'name':'...','interface':'...'},{} ]
    destination = where_is_ip(destination_ip, snapshot_data)
    nodes = [{'name': f'{source_ip}'}]
    if (source and destination):
        if len(source)==1:
            nodes.extend(source)
        else:
            print(f'Найдено более чем одно совпадение по {source_ip} --> {source}\n'
                  f'Граф не будет построен (пока что демо)')
            return False
        if len(destination)==1:
            nodes.extend(destination)
        else:
            print(f'Найдено более чем одно совпадение по {destination_ip} --> {destination}\n'
                  f'Граф не будет построен (пока что демо)')
            return False
        nodes.append({'name':f'{destination_ip}'})
    elif not source:
        print('В снапшоте не найден Source IP')
        return False
    elif not destination:
        print('В снапшоте не найден Destination IP')
        return False
    data_to_json = {
        'nodes': nodes,
        'links': [
            {
                "source": 0,
                "target": 1
            },
            {
                "source": 1,
                "target": 2
            },
            {
                "source": 2,
                "target": 3
            }
        ]
    }
    try:
        with open(r'flaskr/static/graph.json', 'w') as f:
            json.dump(data_to_json, f)
    except Exception as err:
        print(' Some error occured while write graph.json file\n',err)
        return False
    return True

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
            print(path)
            with open(fr'{path}','r+') as file:
                equipment_list = yaml.load(file,Loader=yaml.Loader)
            return equipment_list
    except Exception as err:
        print(' Some error occurred while opening snapshot!\n',err)
        return []

def find_interface(ipv4_interface,equipment_list):
    '''
    This function find matches in snapshot for particular IP-interface.
    :param ipv4_interface: IPv4address object
    :param equipment_list: Enriched snapshot of network state
    :return: next-hop item (node object)
    '''
    node = {}
    for item in equipment_list:
        for address in item['IP_interfaces'].values():
            for _item in address:
                if ipv4_interface == _item.ip:
                    print('Find interface!')
                    node.update(item)
    return node

def query_next_router(destination_ip,next_router):
    '''
    This function find matches in snapshot for particular IP-interface.
    :param destination_ip: destination ip
    :param next_router: node object
    :return: list of next-hop_ips
    '''
    next_hop_ips = []
    result_of_query_routing_table = get_route_to_ip(destination_ip,next_router)
    print(result_of_query_routing_table)
    for route in result_of_query_routing_table:
        if route[2].lower() != 'direct':
            next_hop_ips.append(ipaddress.ip_interface(route[3]))
        else:
            print(f'End router was finded!\n'
                  f'End router that terminate subnet for destination IP is {next_router["Hostname"]}')
            #  Should Do adding to graph.json
            to_graph_json["nodes"].extend([{"name":next_router["Hostname"]}, {"name":f"{destination_ip}"}])
            to_graph_json["links"].extend([{"source": source_id, "target": target_id}, {"source": source_id+1, "target": target_id+1}])
            try:
                with open(r'flaskr/static/graph.json', 'w') as f:
                    json.dump(to_graph_json, f)
                exit(-1)
            except Exception as err:
                print(' Some error occured while write graph.json file\n',err)
                exit(-1)
    return next_hop_ips



if __name__=='__main__':


    equipment_list = [{'Hostname': 'AR1',
               'IP-mgmt': '192.168.1.1'},
              {'Hostname': 'AR2',
               'IP-mgmt': '192.168.2.2'},
              {'Hostname': 'AR3',
               'IP-mgmt': '192.168.3.3'}]
    


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

    #pprint(create_json_to_visualize('5.5.5.5','1.1.1.1',equipment_list))
    #####################################
    source_ip = '11.1.1.1'
    destination_ip = '6.6.6.6'
    source_id = 0
    target_id = 1
    #Define graph.json
    to_graph_json = {
        "nodes":
            [
                {"name": f"{source_ip}"}
            ],
        "links":
            [
            ]
    }
    #Find source IP
    list_of_source_routers = where_is_ip(source_ip,equipment_list)
    pprint(list_of_source_routers)
    #variant A
    next_router = {}
    node = {}
    if len(list_of_source_routers)==1:
        for item in equipment_list:
            if item['Hostname'] == list_of_source_routers[0]['name']:
                next_router.update(item)
        #Go to the next router and see route to the destination
        result_of_query_routing_table = get_route_to_ip(destination_ip,next_router)
        next_hop_ips = []
        print(result_of_query_routing_table)
        for route in result_of_query_routing_table:
            if route[2].lower() != 'direct':
                next_hop_ips.append(ipaddress.ip_address(route[3]))
            else:
                print(f'End router was finded!\n'
                      f'End router that terminate subnet for destination IP is {next_router["Hostname"]}')
                #  Should Do adding to graph.json
                to_graph_json["nodes"].extend([{"name":next_router["Hostname"]}, {"name":f"{destination_ip}"}])
                to_graph_json["links"].extend([{"source": source_id, "target": target_id}, {"source": source_id+1, "target": target_id+1}])
                try:
                    with open(r'flaskr/static/graph.json', 'w') as f:
                        json.dump(to_graph_json, f)
                    exit(-1)
                except Exception as err:
                    print(' Some error occured while write graph.json file\n',err)
                    exit(-1)
        print(next_hop_ips)
        # Find to which router belongs this interface (from snapshot)
        node = {}
        for ip in next_hop_ips:
            node = find_interface(ip,equipment_list)
        print(node)
        print(f' Next router is {node["Hostname"]}, mgmt-address is {node["IP-mgmt"]}')
        #Next - is adding this information to graph.json
        to_graph_json["nodes"].extend([{"name":node["Hostname"]}])
        to_graph_json["links"].extend([{"source": source_id+1, "target": target_id+1}])

    #Find other hops
    flag = True
    while flag:
        result_of_query_routing_table = get_route_to_ip(destination_ip,node)
        next_hop_ips = []
        print(result_of_query_routing_table)
        for route in result_of_query_routing_table:
            if route[2].lower() != 'direct':
                next_hop_ips.append(ipaddress.ip_interface(route[3]))
            else:
                print(f'End router was finded!\n'
                      f'End router that terminate subnet for destination IP is {next_router["Hostname"]}')
                #  Should Do adding to graph.json
                to_graph_json["nodes"].extend([{"name":next_router["Hostname"]}, {"name":f"{destination_ip}"}])
                to_graph_json["links"].extend([{"source": source_id, "target": target_id}, {"source": source_id+1, "target": target_id+1}])
                try:
                    with open(r'flaskr/static/graph.json', 'w') as f:
                        json.dump(to_graph_json, f)
                    exit(-1)
                except Exception as err:
                    print(' Some error occured while write graph.json file\n',err)
                    exit(-1)
        print(next_hop_ips)
        # Find to which router belongs this interface (from snapshot)
        node = {}
        for ip in next_hop_ips:
            node = find_interface(ip,equipment_list)
        print(f' Next router is {node["Hostname"]}, mgmt-address is {node["IP-mgmt"]}')
        #Next - is adding this information to graph.json
        to_graph_json["nodes"].extend([{"name":node["Hostname"]}])
        to_graph_json["links"].extend([{"source": source_id+1, "target": target_id+1}])



    
    







