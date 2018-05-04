#!/usr/bin/python
''' this is cifs_server module 

 (c) 2018, NetApp, Inc
 # GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
'''
 
ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: na_ontap_cifs_server
short_description: cifs server configuration
extends_documentation_fragment:
    - netapp.ontap
version_added: '2.4'
author: chhaya gunawat (chhayag@netapp.com)

description:
    - Creating / deleting and modifying the CIF server .

options:

  state:
    description:
    - Whether the specified cifs_server should exist or not. Values: present/absent
    required: false
    default: present

  service_state:
    description:
    - CIFS Server Administrative Status. Values: started/stopped
    required: true

  cifs_server_name:
    description:
    - Specifies the cifs_server name.
    required: true

  admin_user_name:
    description:
    - Specifies the LIF's home node.
    required: false

  admin_password:
    description:
    - Specifies the role of the LIF.
    required: false

  domain:
    description:
    - The Fully Qualified Domain Name of the Windows Active Directory this CIFS server belongs to.
    required: false

  workgroup:
    description:
    -  The NetBIOS name of the domain or workgroup this CIFS server belongs to.
    required: false

  vserver:
    description:
    - The name of the vserver to use.
    required: true
   
'''

EXAMPLES = '''
    - name: Create cifs_server
      na_ontap_cifs_server:
        state: present
        vserver: svm1
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

    - name: Delete cifs_server
      na_ontap_cifs_server:
        state: absent
        cifs_server_name: data2
        vserver: svm1
        hostname: "{{ netapp_hostname }}"
        username: "{{ netapp_username }}"
        password: "{{ netapp_password }}"

'''

RETURN = '''
    changed: True/False 
'''

import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native
import ansible.module_utils.netapp as netapp_utils

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()


class NetAppOntapcifs_server(object):
    ''' object to describe  cifs_server info '''

    def __init__(self):

        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(required=False, choices=['present', 'absent'], default='present'),
            service_state=dict(required=False, choices=['stopped', 'started']),
            cifs_server_name=dict(required=False, type='str'),
            workgroup=dict(required=False, type='str', default=None),
            domain=dict(required=False, type='str'),
            admin_user_name=dict(required=False, type='str'),
            admin_password=dict(required=False, type='str'),

            vserver=dict(required=True, type='str', default=None),
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        params = self.module.params

        # set up state variables
        self.state = params['state']
        self.cifs_server_name = params['cifs_server_name']
        self.workgroup = params['workgroup']
        self.domain= params['domain']
        self.vserver = params['vserver']
        self.service_state = params['service_state']
        self.admin_user_name = params['admin_user_name']
        self.admin_password = params['admin_password']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json(msg="the python NetApp-Lib module is required")
        else:
            self.server = netapp_utils.setup_ontap_zapi(module=self.module, vserver=self.vserver)

    def get_cifs_server(self):
        """
        Return details about the CIFS-server
        :param:
            name : Name of the name of the cifs_server

        :return: Details about the cifs_server. None if not found.
        :rtype: dict
        """
        cifs_server_info = netapp_utils.zapi.NaElement('cifs-server-get-iter')
        cifs_server_attributes = netapp_utils.zapi.NaElement('cifs-server-config')
        cifs_server_attributes.add_new_child('cifs-server', self.cifs_server_name)
        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(cifs_server_attributes)
        cifs_server_info.add_child_elem(query)
        result = self.server.invoke_successfully(cifs_server_info, True)
        return_value = None

        if result.get_child_by_name('num-records') and \
                int(result.get_child_content('num-records')) >= 1:

            cifs_server_attributes = result.get_child_by_name('attributes-list').\
                get_child_by_name('cifs-server-config')
            return_value = {
                'cifs_server_name': self.cifs_server_name,
                'administrative-status': cifs_server_attributes.get_child_content('administrative-status')
            }

        return return_value

   
    def create_cifs_server(self):
        ''' calling zapi to create cifs_server '''

        options ={'cifs-server': self.cifs_server_name, 'administrative-status': 'up' if self.service_state == 'started' else 'down'}
        if self.workgroup is not None:
            options['workgroup'] = self.workgroup
        if self.domain is not None:
            options['domain'] = self.domain
        if self.admin_user_name is not None:
            options['admin-username'] = self.admin_user_name
        if self.admin_password is not None:
            options['admin-password'] = self.admin_password

        cifs_server_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'cifs-server-create', **options)

        try:
            self.server.invoke_successfully(cifs_server_create,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as exc:
            self.module.fail_json(msg='Error Creating cifs_server %s: %s' %
                (self.cifs_server_name, to_native(exc)), exception=traceback.format_exc())

    def delete_cifs_server(self):
        ''' calling zapi to delete cifs_server '''
        if self.cifs_server_name == 'up':
          self.modify_cifs_server(admin_status='down')

        cifs_server_delete = netapp_utils.zapi.NaElement.create_node_with_children('cifs-server-delete')

        try:
            self.server.invoke_successfully(cifs_server_delete,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as exc:
            self.module.fail_json(msg='Error deleting cifs_server %s: %s' % (self.cifs_server_name, to_native(exc)),
                                  exception=traceback.format_exc())

    def modify_cifs_server(self, admin_status):
        """
        RModify the cifs_server.
        """    
        cifs_server_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'cifs-server-modify', **{'cifs-server': self.cifs_server_name,
             'administrative-status': admin_status, 'vserver': self.vserver})
        try:
            self.server.invoke_successfully(cifs_server_modify,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error modifying cifs_server %s: %s' % (self.cifs_server_name, to_native(e)),
                                  exception=traceback.format_exc())

    def start_cifs_server(self):
        """
        RModify the cifs_server.
        """    
        cifs_server_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'cifs-server-start')
        try:
            self.server.invoke_successfully(cifs_server_modify,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error modifying cifs_server %s: %s' % (self.cifs_server_name, to_native(e)),
                                  exception=traceback.format_exc())

    def stop_cifs_server(self):
        """
        RModify the cifs_server.
        """    
        cifs_server_modify = netapp_utils.zapi.NaElement.create_node_with_children(
            'cifs-server-stop')
        try:
            self.server.invoke_successfully(cifs_server_modify,
                                            enable_tunneling=True)
        except netapp_utils.zapi.NaApiError as e:
            self.module.fail_json(msg='Error modifying cifs_server %s: %s' % (self.cifs_server_name, to_native(e)),
                                  exception=traceback.format_exc())



    def apply(self):
        ''' calling all cifs_server features '''
        
        changed = False
        cifs_server_exists = False
        netapp_utils.ems_log_event("na_ontap_cifs_server", self.server)
        cifs_server_detail = self.get_cifs_server()

        if cifs_server_detail:
            cifs_server_exists = True

            if self.state == 'present':
                administrative_status = cifs_server_detail['administrative-status']
                if self.service_state == 'started' and administrative_status == 'down':
                    changed = True
                if self.service_state == 'stopped' and administrative_status == 'up':
                    changed = True  
            else:
                # we will delete the CIFs server 
                changed = True
        else:
            if self.state == 'present':
                changed = True

        if changed:
            if self.module.check_mode:
                pass
            else:
                if self.state == 'present':
                    if not cifs_server_exists:
                        self.create_cifs_server()

                    elif self.service_state == 'stopped':
                        self.stop_cifs_server()

                    elif self.service_state == 'started':
                        self.start_cifs_server()

                elif self.state == 'absent':
                    self.delete_cifs_server()

        self.module.exit_json(changed=changed)



def main():
    cifs_server = NetAppOntapcifs_server()
    cifs_server.apply()

if __name__ == '__main__':
    main()