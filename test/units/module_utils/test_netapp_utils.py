''' unit tests for module_utils netapp.py '''
# import json

try:
    from netapp_lib.api.zapi import zapi
    HAS_NETAPP_ZAPI = True
except ImportError:
    HAS_NETAPP_ZAPI = False

from ansible.compat.tests import unittest
# from ansible.compat.tests.mock import patch
# from ansible.module_utils import basic
# from ansible.module_utils._text import to_bytes
import ansible.module_utils.netapp as my_module

HAS_NETAPP_ZAPI_MSG = "pip install netapp_lib is required"


class MockONTAPConnection(object):
    ''' mock a server connection to ONTAP host '''

    def __init__(self, kind=None, parm1=None):
        ''' save arguments '''
        self.type = kind
        self.parm1 = parm1
        self.xml_in = None
        self.xml_out = None

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if self.type == 'vserver':
            xml = self.build_vserver_info(self.parm1)
        self.xml_out = xml
        return xml

    @staticmethod
    def build_vserver_info(vserver):
        ''' build xml data for vserser-info '''
        xml = zapi.NaElement('xml')
        attributes = zapi.NaElement('attributes-list')
        attributes.add_node_with_children('vserver-info',
                                          **{'vserver-name': vserver})
        xml.add_child_elem(attributes)
        # print(xml.to_string())
        return xml


class TestEMSLogVersion(unittest.TestCase):
    ''' validate version is read successfully from ansible release.py '''

    def setUp(self):
        self.assertTrue(HAS_NETAPP_ZAPI, HAS_NETAPP_ZAPI_MSG)
        self.source = 'unittest'
        self.server = MockONTAPConnection()

    def test_ems_log_event_version(self):
        ''' validate Ansible version is correctly read '''
        my_module.ems_log_event(self.source, self.server)
        xml = self.server.xml_in
        version = xml.get_child_content('app-version')
        # print(xml.to_string())
        self.assertEquals(version, '2.7')


class TestGetCServer(unittest.TestCase):
    ''' validate cserver name is extracted correctly '''

    def setUp(self):
        self.assertTrue(HAS_NETAPP_ZAPI, HAS_NETAPP_ZAPI_MSG)
        self.svm_name = 'svm1'
        self.server = MockONTAPConnection('vserver', self.svm_name)

    def test_get_cserver(self):
        ''' validate cluster vserser name is correctly retrieved '''
        cserver = my_module.get_cserver(self.server)
        self.assertEquals(cserver, self.svm_name)


if __name__ == '__main__':
    unittest.main()
