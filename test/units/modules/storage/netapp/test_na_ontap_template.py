''' unit test template for ONTAP Ansible module '''

from __future__ import print_function
import json

try:
    from netapp_lib.api.zapi import zapi
    HAS_NETAPP_ZAPI = True
except ImportError:
    HAS_NETAPP_ZAPI = False

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes

# TODO: change filename and module name
from ansible.modules.storage.netapp.na_ontap_cg_snapshot \
   import NetAppONTAPCGSnapshot as my_module  # module under test

HAS_NETAPP_ZAPI_MSG = "pip install netapp_lib is required"


def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)  # pylint: disable=protected-access


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


def exit_json(*args, **kwargs):  # pylint: disable=unused-argument
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):  # pylint: disable=unused-argument
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


class MockONTAPConnection(object):
    ''' mock server connection to ONTAP host '''

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


class TestMyModule(unittest.TestCase):
    ''' a group of related Unit Tests '''

    def setUp(self):
        self.assertTrue(HAS_NETAPP_ZAPI, HAS_NETAPP_ZAPI_MSG)
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)
        self.server = MockONTAPConnection()

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with self.assertRaises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.exception[0]['msg'])

    def test_ensure_command_called(self):
        ''' a more interesting test '''
# TODO: change argument names/values
        set_module_args({
            'vserver': 'vserver',
            'volumes': 'volumes',
            'snapshot': 'snapshot',
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password',
        })
        my_obj = my_module()
        my_obj.server = self.server
        with self.assertRaises(AnsibleFailJson) as exc:
            # It may not be a good idea to start with apply
            # More atomic methods can be easier to mock
            my_obj.apply()
# TODO: change message, and maybe test contents
        msg = 'Error fetching CG ID for CG commit snapshot'
        self.assertEquals(exc.exception[0]['msg'], msg)


if __name__ == '__main__':
    unittest.main()
