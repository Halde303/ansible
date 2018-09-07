#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Andrew Saraceni <andrew.saraceni@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_group_membership
version_added: "2.4"
short_description: Manage Windows local group membership
description:
     - Allows the addition and removal of local, service and domain users,
       and domain groups from a local group.
options:
  name:
    description:
      - Name of the local group to manage membership on.
    required: yes
  members:
    description:
      - A list of members to ensure are present/absent from the group.
      - Accepts local users as .\username, and SERVERNAME\username.
      - Accepts domain users and groups as DOMAIN\username and username@DOMAIN.
      - Accepts service users as NT AUTHORITY\username.
      - Accepts all local, domain and service user types as username,
        favoring domain lookups when in a domain.
    required: yes
    type: list
  state:
    description:
      - Desired state of the members in the group.
    choices: [ absent, present ]
    default: present
author:
    - Andrew Saraceni (@andrewsaraceni)
'''

EXAMPLES = r'''
- name: Add a local and domain user to a local group
  win_group_membership:
    name: Remote Desktop Users
    members:
      - NewLocalAdmin
      - DOMAIN\TestUser
    state: present

- name: Remove a domain group and service user from a local group
  win_group_membership:
    name: Backup Operators
    members:
      - DOMAIN\TestGroup
      - NT AUTHORITY\SYSTEM
    state: absent
'''

RETURN = r'''
name:
    description: The name of the target local group.
    returned: always
    type: string
    sample: Administrators
added:
    description: A list of members added when C(state) is C(present); this is
      empty if no members are added.
    returned: success and C(state) is C(present)
    type: list
    sample: ["SERVERNAME\\NewLocalAdmin", "DOMAIN\\TestUser"]
removed:
    description: A list of members removed when C(state) is C(absent); this is
      empty if no members are removed.
    returned: success and C(state) is C(absent)
    type: list
    sample: ["DOMAIN\\TestGroup", "NT AUTHORITY\\SYSTEM"]
members:
    description: A list of all local group members at completion; this is empty
      if the group contains no members.
    returned: success
    type: list
    sample: ["DOMAIN\\TestUser", "SERVERNAME\\NewLocalAdmin"]
'''
