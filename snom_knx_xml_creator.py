"""Creates a snom xml for controlling knx installations"""
import socket
import os
import shutil
import logging
from enum import Enum
import xml.etree.ElementTree as ET

#ENCODING = 'iso-8859-10'
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

class SnomXmlElement:
    ROOT = "SnomIPPhoneMenu"
    TITLE = "Title"
    MENU_ITEM = "MenuItem"
    NAME = "Name"
    URL = "URL"

class SnomKnxXmlCreator:
    def __init__(self, groupaddresses_data, rtx_xml=False):
        self.groupaddresses_data = groupaddresses_data
        self.local_ip = self._get_local_ip()
        self.knx_http_root = f"http://{self.local_ip}:1234/"

        if rtx_xml:
            xml_root_dir = "knx_xml_rtx/"
            self.encoding = "iso-8859-10"
        else:
            xml_root_dir = "knx_xml/"
            self.encoding = "utf-8"

        self.xml_physical_root = f"/srv/http/{xml_root_dir}"
        self.http_root = f"http://{self.local_ip}/{xml_root_dir}"
        self.master_file = "knx_multi.xml"
        self.master_file_path = f"{self.xml_physical_root}{self.master_file}"

        self._update_directory()
        self._remove_file_if_exists()

    def _update_directory(self) -> None:
        """
        Creates directory for snom xml. Removes it if exits.
        """
        directory = self.xml_physical_root

        if os.path.exists(directory):
            shutil.rmtree(directory)
            logging.warning(f"Existing directory {directory} removed recursively")

        os.makedirs(directory)
        logging.warning(f"Directory {directory} created")

    def _remove_file_if_exists(self):
        file = self.master_file_path

        if os.path.exists(file):
            os.remove(file)
            logging.warning(f"Existing file {file} deleted")

    def _get_local_ip(self):
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

    def write_knx_xml(self):
        main_addresses_root = ET.Element(SnomXmlElement.ROOT)
        title = ET.SubElement(main_addresses_root, SnomXmlElement.TITLE)
        title.text = "KNX"

        main_addresses = {}

        for groupaddress_data in self.groupaddresses_data:
            main_address = self.get_main_groupaddress(groupaddress_data)
            main_addresses.update(main_address)

        for address, address_name in main_addresses.items():
            menu_item = ET.SubElement(main_addresses_root, SnomXmlElement.MENU_ITEM)
            item_name = ET.SubElement(menu_item, SnomXmlElement.NAME)
            item_name.text = address_name
            item_url = ET.SubElement(menu_item, SnomXmlElement.URL)
            main_file = f"{address}-_-_.xml"
            item_url.text = f"{self.http_root}{main_file}"
            self.write_main_address_xml(main_file, address, address_name)

        main_addresses_tree = ET.ElementTree(main_addresses_root)
        main_addresses_tree.write(self.master_file_path, encoding=self.encoding, xml_declaration=True)

    def write_main_address_xml(self, main_file, main_address, main_address_name):
        midd_addresses_root = ET.Element(SnomXmlElement.ROOT)
        title = ET.SubElement(midd_addresses_root, SnomXmlElement.TITLE)
        title.text = main_address_name

        midd_addresses = {}

        for groupaddress_data in self.groupaddresses_data:
            main_groupaddress = self.get_main_groupaddress(groupaddress_data)

            if {main_address: main_address_name} == main_groupaddress:
                midd_address = self.get_midd_groupaddress(groupaddress_data)
                midd_addresses.update(midd_address)

        for address, address_name in midd_addresses.items():
            menu_item = ET.SubElement(midd_addresses_root, SnomXmlElement.MENU_ITEM)
            item_name = ET.SubElement(menu_item, SnomXmlElement.NAME)
            item_name.text = address_name
            item_url = ET.SubElement(menu_item, SnomXmlElement.URL)
            midd_file = f"{main_address}-{address}-_.xml"
            item_url.text = f"{self.http_root}{midd_file}"
            self.write_midd_addresses_xml(midd_file, main_address, address, address_name)

        main_file_path = f"{self.xml_physical_root}{main_file}"
        midd_addresses_tree = ET.ElementTree(midd_addresses_root)
        midd_addresses_tree.write(main_file_path, encoding=self.encoding, xml_declaration=True)

    def write_midd_addresses_xml(self, midd_file, main_address, midd_address, midd_address_name):
        sub_addresses_root = ET.Element(SnomXmlElement.ROOT)
        title = ET.SubElement(sub_addresses_root, SnomXmlElement.TITLE)
        title.text = midd_address_name

        sub_addresses = {}

        for groupaddress_data in self.groupaddresses_data:
            midd_groupaddress = self.get_midd_groupaddress(groupaddress_data)

            if {midd_address: midd_address_name} == midd_groupaddress:
                sub_address = self.get_sub_groupaddress(groupaddress_data)
                sub_addresses.update(sub_address)

        for address, address_name in sub_addresses.items():
            menu_item = ET.SubElement(sub_addresses_root, SnomXmlElement.MENU_ITEM)
            item_name = ET.SubElement(menu_item, SnomXmlElement.NAME)
            item_name.text = address_name
            item_url = ET.SubElement(menu_item, SnomXmlElement.URL)
            sub_file = f"{main_address}-{midd_address}-{address}.xml"
            item_url.text = f"{self.http_root}{sub_file}"
            self.write_sub_addresses_xml(sub_file, main_address, midd_address, address, address_name)

        midd_file_path = f"{self.xml_physical_root}{midd_file}"
        sub_addresses_tree = ET.ElementTree(sub_addresses_root)
        sub_addresses_tree.write(midd_file_path, encoding=self.encoding, xml_declaration=True)

    def write_sub_addresses_xml(self, sub_file, main_address, midd_address, sub_address, sub_address_name):
        groupaddress_actions = {}

        for groupaddress_data in self.groupaddresses_data:
            sub_groupaddress = self.get_sub_groupaddress(groupaddress_data)

            if {sub_address: sub_address_name} == sub_groupaddress:
                if dpt := groupaddress_data.get("dpt_type"):
                    dpt_type = dpt.get("main")
                    if actions := DATAPOINT_VALUES.get(dpt_type):
                        groupaddress_actions.update(actions)
                    else:
                        return

        if groupaddress_actions:
            actions_root = ET.Element(SnomXmlElement.ROOT)
            title = ET.SubElement(actions_root, SnomXmlElement.TITLE)
            title.text = sub_address_name

            for label, action in groupaddress_actions.items():
                menu_item = ET.SubElement(actions_root, SnomXmlElement.MENU_ITEM)
                item_name = ET.SubElement(menu_item, SnomXmlElement.NAME)
                item_name.text = label
                item_url = ET.SubElement(menu_item, SnomXmlElement.URL)
                item_url.text = f"{self.knx_http_root}{main_address}/{midd_address}/{sub_address}{action}"

            sub_file_path = f"{self.xml_physical_root}{sub_file}"
            actions_tree = ET.ElementTree(actions_root)
            actions_tree.write(sub_file_path, encoding=self.encoding, xml_declaration=True)

    def get_main_groupaddress(self, groupaddress_data) -> dict[str, str]:
        groupaddress = groupaddress_data.get("address")
        main_name = groupaddress_data.get("main_name")
        items = groupaddress.split("/")

        return  {items[0]: main_name}

    def get_midd_groupaddress(self, groupaddress_data) -> dict[str, str]:
        groupaddress = groupaddress_data.get("address")
        main_name = groupaddress_data.get("middle_name")
        items = groupaddress.split("/")

        return  {items[1]: main_name}

    def get_sub_groupaddress(self, groupaddress_data) -> dict[str, str]:
        groupaddress = groupaddress_data.get("address")
        main_name = groupaddress_data.get("name")
        items = groupaddress.split("/")

        return  {items[2]: main_name}
