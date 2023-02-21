"""Help functions for iot project"""
import socket
import os
import shutil
import logging
from enum import Enum

class StringEnum(Enum):
    def __repr__(self):
        return f"<{ self.__class__.__name__ }.{ self.name }>"


def get_local_ip():
    local_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        local_socket.connect(('10.255.255.255', 1))
        local_ip = local_socket.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        local_socket.close()
    return local_ip

def remove_file_if_exists(file):
    if os.path.exists(file):
        os.remove(file)
        logging.warning(f"Existing file {file} deleted")

def update_directory(directory) -> None:
    """
    Creates directory for snom xml. Removes it if exits.
    """
    if os.path.exists(directory):
        shutil.rmtree(directory)
        logging.warning(f"Existing directory {directory} removed recursively")

    os.makedirs(directory)
    logging.warning(f"Directory {directory} created")


import csv
import logging
import os
import xml.etree.ElementTree as ET


GATEWAY_IP = get_local_ip()
XML_TARGET_DIRECTORY='/srv/http/knx_xml/'
KNX_ROOT = f"http://{ GATEWAY_IP }:1234/"

SEPERATOR = '_'
XML_HTTP_ROOT = f'http://{GATEWAY_IP}/knx_xml/'
XML_PHYSICAL_ROOT = XML_TARGET_DIRECTORY
MAIN_XML_FILE_NAME = "knx_multi.xml"
ENCODING = 'iso-8859-10'
DATAPOINT_TYPES = {
    "binary": 1,
    "step_code": 3,
    "unsigned_value": 5,
}
DATAPOINT_SUBTYPES = {
    "binary": {
        "on_off": 1,
        "false_true": 2,
        "enable_disable": 3,
        "alarm_no_alarm": 5,
        "increase_decrease": 7,
        "up_down": 8,
        "open_close": 9,
        "start_stop": 10,
        "state": 11,
        "window_door": 19
    },
    "step_code": {},
    "unsigned_value": {}
}
DATAPOINT_VALUES = {
    1: {"on": "-an", "off": "-aus"},
    3: {"increase": "-plus", "decrease": "-minus"},
}


def remove_file_if_exists(file):
    if os.path.exists(file):
        os.remove(file)
        logging.warning(f"Existing file {file} deleted")


class SnomXMLFactory:
    def __init__(self, data):
        self.data = data
        update_directory(XML_PHYSICAL_ROOT)

    def create_multi_xml(self):
        main_xml_path = f'{XML_PHYSICAL_ROOT}{MAIN_XML_FILE_NAME}'
        remove_file_if_exists(main_xml_path)

        with open(main_xml_path, 'w', encoding=ENCODING) as main_xml:
            open_xml_phone_menu(main_xml)
            

            for groupaddress_info in self.data:
                groupaddress = groupaddress_info.get("address")
                groupaddress_items = groupaddress.split("/")
                main_address = groupaddress_items[0]
                mid_address = groupaddress_items[1]
                is_main_address = '/-/-' in groupaddress
                main_address_xml = f"{main_address}-_-_.xml"
                mid_address_xml = f"{main_address}-{mid_address}-_.xml"

                if not os.path.exists(f"{XML_PHYSICAL_ROOT}{main_address_xml}"):
                    main_address_name = groupaddress_info.get("main_name")
                    main_xml_file_name = f"{main_address}-_-_.xml"
                    #mid_xml_file_name = f"{main_address}-{mid_address}-_.xml"
                    create_xml_menu_item(main_xml, main_address_name, main_xml_file_name)
                    mid_address_name = groupaddress_info.get("middle_name")
                    self.create_main_group_xml(main_address_name, main_xml_file_name)
                    
            
            close_xml_phone_menu(main_xml)

    def create_main_group_xml(self, main_address_name, mid_xml_file_name):
        mid_xml_path = f"{XML_PHYSICAL_ROOT}{mid_xml_file_name}"
        remove_file_if_exists(mid_xml_path)

        with open(mid_xml_path, 'w', encoding=ENCODING) as mid_xml:
            open_xml_phone_menu(mid_xml, title=main_address_name)
            # address_xml_file_name = f"{main_address}-{main_address}-_.xml"
            # create_xml_menu_item(mid_xml, mid_address_name, address_xml_file_name)


            close_xml_phone_menu(mid_xml)

def create_xml_menu_item(xml_file, menu_name, xml_subfile):
    xml_file.write(f"""
        <MenuItem>
            <Name>{menu_name}</Name>
            <URL>{XML_HTTP_ROOT}{xml_subfile}</URL>
        </MenuItem>
    """)

def get_datapoint_type(datapointtype_items):
    return int(datapointtype_items[1])

def get_datapoint_subtype(datapointtype_items):
    try:
        datapoint_subtype = int(datapointtype_items[2])
    except IndexError:
        datapoint_subtype = None
    except Exception:
        logging.exception("Uncaught exception:")

    return datapoint_subtype

def create_xml_menu_item_action(xml_file, groupaddress, datapointtype):
    for label, value in DATAPOINT_VALUES.get(datapointtype).items():
        xml_file.write(f"""
            <MenuItem>
                <Name>{label}</Name>
                <URL>{ KNX_ROOT }{groupaddress}{value}</URL>
            </MenuItem>"""
        )

def create_xml_menu_item_read_value(xml_file, groupaddress):
    xml_file.write(f"""
        <MenuItem>
            <Name>Show {groupaddress} value</Name>
            <URL>Fetch {groupaddress} value</URL>
        </MenuItem>"""
    )

def open_xml_phone_menu(xml_file, title="KNX"):
    xml_file.write(f"""<?xml version="1.0" encoding="{ENCODING}"?>
        <SnomIPPhoneMenu>
        <Title>{title}</Title>""")

def close_xml_phone_menu(xml_file):
    xml_file.write("</SnomIPPhoneMenu>")


from xknxproject.models import KNXProject
from xknxproject import XKNXProj

MAIN_XML_PATH = f"{XML_PHYSICAL_ROOT}{MAIN_XML_FILE_NAME}"

class SnomElement:
    ROOT = "SnomIPPhoneMenu"
    TITLE = "Title"
    MENU_ITEM = "MenuItem"
    NAME = "Name"
    URL = "URL"

def write_master_xml(groupaddresses_data):
    main_addresses_root = ET.Element(SnomElement.ROOT)
    title = ET.SubElement(main_addresses_root, SnomElement.TITLE)
    title.text = "KNX"

    main_addresses = {}

    for groupaddress_data in groupaddresses_data:
        main_address = get_main_groupaddress(groupaddress_data)
        main_addresses.update(main_address)

    for address, address_name in main_addresses.items():
        menu_item = ET.SubElement(main_addresses_root, SnomElement.MENU_ITEM)
        item_name = ET.SubElement(menu_item, SnomElement.NAME)
        item_name.text = address_name
        item_url = ET.SubElement(menu_item, SnomElement.URL)
        main_file = f"{address}-_-_.xml"
        item_url.text = f"{XML_HTTP_ROOT}{main_file}"
        write_main_address_xml(main_file, groupaddresses_data, address, address_name)

    master_file_path = f"{XML_PHYSICAL_ROOT}knx_multi.xml"
    main_addresses_tree = ET.ElementTree(main_addresses_root)
    main_addresses_tree.write(master_file_path, encoding="utf-8", xml_declaration=True)

def write_main_address_xml(main_file, groupaddresses_data, main_address, main_address_name):
    midd_addresses_root = ET.Element(SnomElement.ROOT)
    title = ET.SubElement(midd_addresses_root, SnomElement.TITLE)
    title.text = main_address_name

    midd_addresses = {}

    for groupaddress_data in groupaddresses_data:
        main_groupaddress = get_main_groupaddress(groupaddress_data)

        if {main_address: main_address_name} == main_groupaddress:
            midd_address = get_midd_groupaddress(groupaddress_data)
            midd_addresses.update(midd_address)

    for address, address_name in midd_addresses.items():
        menu_item = ET.SubElement(midd_addresses_root, SnomElement.MENU_ITEM)
        item_name = ET.SubElement(menu_item, SnomElement.NAME)
        item_name.text = address_name
        item_url = ET.SubElement(menu_item, SnomElement.URL)
        midd_file = f"{main_address}-{address}-_.xml"
        item_url.text = f"{XML_HTTP_ROOT}{midd_file}"
        write_midd_addresses_xml(midd_file, groupaddresses_data, main_address, address, address_name)

    main_file_path = f"{XML_PHYSICAL_ROOT}{main_file}"
    midd_addresses_tree = ET.ElementTree(midd_addresses_root)
    midd_addresses_tree.write(main_file_path, encoding="utf-8", xml_declaration=True)

def write_midd_addresses_xml(midd_file, groupaddresses_data, main_address, midd_address, midd_address_name):
    sub_addresses_root = ET.Element(SnomElement.ROOT)
    title = ET.SubElement(sub_addresses_root, SnomElement.TITLE)
    title.text = midd_address_name

    sub_addresses = {}

    for groupaddress_data in groupaddresses_data:
        midd_groupaddress = get_midd_groupaddress(groupaddress_data)

        if {midd_address: midd_address_name} == midd_groupaddress:
            sub_address = get_sub_groupaddress(groupaddress_data)
            sub_addresses.update(sub_address)

    for address, address_name in sub_addresses.items():
        menu_item = ET.SubElement(sub_addresses_root, SnomElement.MENU_ITEM)
        item_name = ET.SubElement(menu_item, SnomElement.NAME)
        item_name.text = address_name
        item_url = ET.SubElement(menu_item, SnomElement.URL)
        sub_file = f"{main_address}-{midd_address}-{address}.xml"
        item_url.text = f"{XML_HTTP_ROOT}{sub_file}"
        write_sub_addresses_xml(sub_file, groupaddresses_data, main_address, midd_address, address, address_name)

    midd_file_path = f"{XML_PHYSICAL_ROOT}{midd_file}"
    sub_addresses_tree = ET.ElementTree(sub_addresses_root)
    sub_addresses_tree.write(midd_file_path, encoding="utf-8", xml_declaration=True)

def write_sub_addresses_xml(sub_file, groupaddresses_data, main_address, midd_address, sub_address, sub_address_name):
    groupaddress_actions = {}

    for groupaddress_data in groupaddresses_data:
        sub_groupaddress = get_sub_groupaddress(groupaddress_data)

        if {sub_address: sub_address_name} == sub_groupaddress:
            dpt = groupaddress_data.get("dpt_type")
            if dpt:
                dpt_type = dpt.get("main")
                actions = DATAPOINT_VALUES.get(dpt_type)
                if actions:
                    groupaddress_actions.update(actions)
                else:
                    return

    if groupaddress_actions:
        actions_root = ET.Element(SnomElement.ROOT)
        title = ET.SubElement(actions_root, SnomElement.TITLE)
        title.text = sub_address_name

        for label, action in groupaddress_actions.items():
            menu_item = ET.SubElement(actions_root, SnomElement.MENU_ITEM)
            item_name = ET.SubElement(menu_item, SnomElement.NAME)
            item_name.text = label
            item_url = ET.SubElement(menu_item, SnomElement.URL)
            item_url.text = f"{KNX_ROOT}{main_address}/{midd_address}/{sub_address}{action}"

        sub_file_path = f"{XML_PHYSICAL_ROOT}{sub_file}"
        actions_tree = ET.ElementTree(actions_root)
        actions_tree.write(sub_file_path, encoding="utf-8", xml_declaration=True)

def get_main_groupaddress(groupaddress_data) -> dict[str, str]:
    groupaddress = groupaddress_data.get("address")
    main_name = groupaddress_data.get("main_name")
    items = groupaddress.split("/")

    return  {items[0]: main_name}

def get_midd_groupaddress(groupaddress_data) -> dict[str, str]:
    groupaddress = groupaddress_data.get("address")
    main_name = groupaddress_data.get("middle_name")
    items = groupaddress.split("/")

    return  {items[1]: main_name}

def get_sub_groupaddress(groupaddress_data) -> dict[str, str]:
    groupaddress = groupaddress_data.get("address")
    main_name = groupaddress_data.get("name")
    items = groupaddress.split("/")

    return  {items[2]: main_name}

if __name__ == "__main__":
    knxproj: XKNXProj = XKNXProj("/home/golpe/knx/ISE_2023_20230213.knxproj")
    project: KNXProject = knxproj.parse()

    groupaddresses_data = project.get("group_addresses").values()

    update_directory(XML_PHYSICAL_ROOT)
    remove_file_if_exists(MAIN_XML_PATH)

    write_master_xml(groupaddresses_data)
