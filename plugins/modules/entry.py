#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Author: Tobias Karger und Marie Berger
# Contact: coding@thepatchwork.de
# License: The Unlicense, see LICENSE file.

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

PYKEEPASS_IMP_ERR = None
try:
    from pykeepass import PyKeePass
    import pykeepass.exceptions
except ImportError:
    PYKEEPASS_IMP_ERR = traceback.format_exc()
    pykeepass_found = False
else:
    pykeepass_found = True

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['release'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: keepass_entry
short_description: Manage entries in a KeePass (kdbx) database.
version_added: "1.0"
description:
    - "This module allows you to manage entries in a KeePass (kdbx) database."
requirements:
    - PyKeePass
options:
    database:
        description:
            - Path of the KeePass database.
        required: true
        type: str
    title:
        description:
            - Title, used for the title of the entry.
        required: false
        type: str
    keyfile:
        description:
            - Path of the KeePass keyfile. Either this or 'database_password' (or both) are required.
        required: false
        type: str
    username:
        description:
            - Username of the entry.
        required: true
        type: str
    database_password:
        description:
            - Database password. Either this or 'keyfile' (or both) are required.
        required: false
        type: str
    password_length:
        description:
            - The length of the generated passwords. Defaults to 30 characters.
        required: false
        type: int
    url:
        description:
            - URL to be added to the KeePass entry.
        required: false
        type: str
    group_name:
        description:
            - Group name in which to place the KeePass entry.
        required: false
        type: str
    icon_id:
        description:
            - Icon ID to be associated with the KeePass Icon IDs.
        required: false
        type: str
    action:
        description:
            - The action to perform (create, modify, delete).
        required: true
        type: str
author:
    - Tobias Karger und Marie Berger
'''

EXAMPLES = '''
- name: Create a new entry in KeePass
  keepass_entry:
    action: create
    database: /path/to/keepass.kdbx
    database_password: "your_database_password"
    title: MyNewEntry
    username: myusername
    password: mypassword
    url: https://example.com
    group_name: MyGroup
    icon_id: 49
  register: entry

- debug:
    var: entry

- name: Modify the url of an entry in KeePass
  keepass_entry:
    action: modify
    database: /path/to/keepass.kdbx
    database_password: "your_database_password"
    title: MyNewEntry
    url: https://example.com
  register: entry

- debug:
    var: entry

- name: Delete an entry in KeePass
  keepass_entry:
    action: delete
    database: /path/to/keepass.kdbx
    database_password: "your_database_password"
    title: MyNewEntry
  register: entry

- debug:
    var: entry
'''

RETURN = '''
title:
    description: The title of the entry created or modified.
    type: str
icon_id:
    description: The Icon ID associated with the entry.
    type: str
username:
    description: The username associated with the entry.
    type: str
password:
    description: The password associated with the entry.
    type: str
url:
    description: The URL associated with the KeePass entry.
    type: str
group_name:
    description: The Group Name associated with the KeePass entry.
    type: str
changed:
    description: Indicates whether a change was made to the entry.
    type: bool
'''


def main():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        database=dict(type='str', required=True),
        title=dict(type='str', required=False),
        keyfile=dict(type='str', required=False, default=None),
        database_password=dict(type='str', required=False, default=None, no_log=True),
        password=dict(type='str', required=False, default=None, no_log=True),
        password_length=dict(type='int', required=False, no_log=False),
        username=dict(type='str', required=True),
        url=dict(type='str', required=False),
        group_name=dict(type='str', required=False),
        icon_id=dict(type='str', required=False),
        action=dict(type='str', required=True),

    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        username='',
        password='',
        url=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if not pykeepass_found:
        module.fail_json(msg=missing_required_lib("pykeepass"), exception=PYKEEPASS_IMP_ERR)

    database                = module.params['database']
    title                   = module.params['title']
    keyfile                 = module.params['keyfile']
    database_password       = module.params['database_password']
    password                = module.params['password']
    password_length         = module.params['password_length']
    username                = module.params['username']
    url                     = module.params['url']
    group_name              = module.params['group_name']
    icon_id                 = module.params['icon_id']
    action                  = module.params['action']

    if password and password_length:
        module.fail_json(msg="'password' and 'password_length' are defined. Only one is allowed")

    if not database_password and not keyfile:
        module.fail_json(msg="Either 'database_password' or 'keyfile' (or both) are required.")

    try:
        kp = PyKeePass(database, password=database_password, keyfile=keyfile)
    except IOError:
        KEEPASS_OPEN_ERR = traceback.format_exc()
        module.fail_json(msg='Could not open the database or keyfile.')
    except pykeepass.exceptions.CredentialsError:
        KEEPASS_OPEN_ERR = traceback.format_exc()
        module.fail_json(msg='Could not open the database, as the credentials are wrong.')
    except (pykeepass.exceptions.HeaderChecksumError, pykeepass.exceptions.PayloadChecksumError):
        KEEPASS_OPEN_ERR = traceback.format_exc()
        module.fail_json(msg='Could not open the database, as the checksum of the database is wrong. This could be caused by a corrupt database.')

    if action.lower() == "create":
        # try to get the entry from the database
        entry = kp.find_entries(title=title, first=True)
        if entry:
            if entry.title == title:
                result['icon_id']   = entry.icon
                result['title']     = entry.title
                result['username']  = entry.username
                result['password']  = entry.password
                result['url']       = entry.url
                module.exit_json(**result)

        # if there is no matching entry, create a new one
        if not password:
            if password_length:
                password = generate_password(password_length)
            else:
                password = generate_password(20)

        if not module.check_mode:
            try:
                if group_name:
                    kp.add_entry(kp.find_groups(name=group_name, first=True), title, username, password, url=url, icon=icon_id or '58', notes='Generated by ansible.')
                else:
                    kp.add_entry(kp.root_group, title, username, password, url=url, icon=icon_id or '58', notes='Generated by ansible.')
                kp.save()
            except:
                KEEPASS_SAVE_ERR = traceback.format_exc()
                module.fail_json(msg='Could not add the entry or save the database.', exception=KEEPASS_SAVE_ERR)

        entry = kp.find_entries(title=title, first=True)

        result['group']     = entry.group.name
        result['icon_id']   = entry.icon
        result['username']  = entry.username
        result['password']  = entry.password
        result['url']       = entry.url
        result['changed']   = True

        # in the event of a successful module execution, you will want to
        # simple AnsibleModule.exit_json(), passing the key/value results
        module.exit_json(**result)

    elif action.lower() == "modify":
        # try to get the entry from the database
        entry = kp.find_entries(title=title)
        if len (entry) > 1:
            module.fail_json(msg='More then one entry found in Database', exception=traceback.format_exc())
        elif len (entry) == 0:
            module.fail_json(msg='No entry found in Database', exception=traceback.format_exc())
        else:
            entry = entry[0]
            entry.save_history()
            entry.touch(modify=True)
            kp.save()
            if not password:
                if password_length:
                    entry.password = generate_password(password_length)
            else:
                entry.password = password

            if username:
                entry.username = username

            if url:
                entry.url = url

            if icon_id:
                entry.icon = icon_id

            kp.save()

            result['group']     = entry.group.name
            result['icon_id']   = entry.icon
            result['username']  = entry.username
            result['password']  = entry.password
            result['url']       = entry.url
            result['changed']   = True

        # in the event of a successful module execution, you will want to
        # simple AnsibleModule.exit_json(), passing the key/value results
        module.exit_json(**result)

    elif action.lower() == "delete":
        entry = kp.find_entries(title=title)
        if len (entry) > 1:
            module.fail_json(msg='More then one entry found in Database', exception=traceback.format_exc())
        elif len (entry) == 0:
            module.fail_json(msg='No entry found in Database', exception=traceback.format_exc())
        else:
            kp.delete_entry(entry=entry[0])
            kp.save()
            module.exit_json(changed=True)

    else:
        module.fail_json(msg='No action matched', exception=traceback.format_exc())

def generate_password(length):
    import string
    alphabet = string.ascii_letters + string.digits
    try:
        import secrets as random
    except ImportError:
        import random

    gen_password = ''.join(random.choice(alphabet) for _ in range(length))
    return gen_password

if __name__ == '__main__':
    main()
