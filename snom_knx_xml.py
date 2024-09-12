from xknxproject.models import KNXProject
from xknxproject import XKNXProj
from snom_knx_xml_creator import SnomKnxXmlCreator

if __name__ == "__main__":
    knxproj: XKNXProj = XKNXProj("./example.knxproj")
    project: KNXProject = knxproj.parse()

    groupaddresses_data = project.get("group_addresses").values()

    snom_knx_xml_creator = SnomKnxXmlCreator(groupaddresses_data)
    snom_knx_xml_creator.write_knx_xml()

    rtx_knx_xml_creator = SnomKnxXmlCreator(groupaddresses_data, rtx_xml=True)
    rtx_knx_xml_creator.write_knx_xml()
