#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Author: Tobias Karger und Marie Berger
# Contact: coding@thepatchwork.de
# License: The Unlicense, see LICENSE file.
from __future__ import (absolute_import, division, print_function)
import traceback
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
PYKEEPASS_IMP_ERR = None
try:
    from pykeepass import PyKeePass
    import pykeepass.exceptions
except ImportError:
    PYKEEPASS_IMP_ERR = traceback.format_exc()
    PYKEEPASS_FOUND = False
else:
    PYKEEPASS_FOUND = True
__metaclass__ = type

DOCUMENTATION = '''
---
name: lookup
short_description: Search for Entries in a KeePass Database
version_added: "1.2.0"
description:
  - Uses pykeepass to search for Entries in a KeePass Database
requirements:
  - pykeepass

options:
    _terms:
      description: For what you are looking for
      required: True
      type: str
    database:
      description: Path to the KeePass database file
      type: str
      required: True
    database_password:
      description: Password to unlock the KeePass database
      type: str
      required: False
    keyfile:
      description: Path to the keyfile to unlock the KeePass database
      type: str
      required: False
    title:
      description: Filter entries by title
      type: str
      required: False
    group_path:
      description: Filter entries by group path
      type: str
      required: False
      default: '/'
    regex:
      description: Whether to use regular expressions for filtering
      type: bool, str
      required: False
      default: False
    recursive:
      description: Whether to search recursively in groups
      type: bool, str
      required: False
      default: True
    notes:
      description: Filter entries by notes
      type: str
      required: False
      default: Null
    url:
      description: Filter entries by URL
      type: str
      required: False
      default: Null
    tags:
      description: Filter entries by tags
      type: list
      elements: str
      required: False
      default: ['']
    username:
      description: Filter entries by username
      type: str
      required: False
      default: Null
'''


EXAMPLES = """
- name: Find an entry by title in KeePass database
  debug:
    msg: "{{ lookup('lookup', 'entry', database='/path/to/database.kdbx', database_password='secret', title='My Entry') }}"

- name: Find entries in a specific group and 
  debug:
    msg: "{{ lookup('lookup', 'entry', database='/path/to/database.kdbx', database_password='secret', group='My Group'), recursive=False }}"

- name: Find entries with a specific tag
  debug:
    msg: "{{ lookup('lookup', 'entry', database='/path/to/database.kdbx', database_password='secret', tags=['important']) }}"
"""

RETURN = """
entries:
    description: List of KeePass entries matching the search criteria
    type: list
    elements: dict
    returned: always
    sample: [
        {
            "title": "My Entry",
            "username": "myusername",
            "group_path": "Root/Group/",
            "icon_id": 1,
            "password": "mypassword",
            "url": "http://example.com",
            "notes": "Some notes",
            "tags": ["tag1", "tag2"]
        }
    ]
"""

class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        ret = []
        if terms[0] == "entry":
            self.set_options(var_options=variables, direct=kwargs)
            database          = self.get_option('database')
            database_password = self.get_option('database_password')
            keyfile           = self.get_option('keyfile')
            title             = self.get_option('title')
            group_path        = self.get_option('group_path')
            regex             = self.get_option('regex')
            if not isinstance(regex, bool):
                raise AnsibleError(f"The option 'regex' must be of type 'bool', got {type(regex)}")
            recursive         = self.get_option('recursive')
            if not isinstance(recursive, bool):
                raise AnsibleError(f"The option 'recursive' must be of type 'bool', got {type(recursive)}")
            notes             = self.get_option('notes')
            url               = self.get_option('url')
            tags              = self.get_option('tags')
            username          = self.get_option('username')

            for option in kwargs:
                if option not in self._options:
                    raise AnsibleError(
                        f"'{option}' is not a valid option. Use one of these options instead: database, database_password, keyfile, title, group_path, regex, recursive, notes, url, tags, username"
                    )
                try:
                    self.get_option(option)
                except KeyError as exc:
                    raise AnsibleError(
                        f"Requested entry (plugin_type: lookup plugin: ansible_collections.torie_coding.keepass.plugins.lookup.lookup setting: {option} ) was not defined in configuration."
                    ) from exc

            if not database_password and not keyfile:
                raise AnsibleError("Either 'database_password' or 'keyfile' (or both) are required.")
            try:
                kp = PyKeePass(database, password=database_password, keyfile=keyfile)
            except IOError as exc:
                raise AnsibleError('Could not open the database or keyfile.') from exc
            except pykeepass.exceptions.CredentialsError as exc:
                raise AnsibleError('Could not open the database, as the credentials are wrong.') from exc
            except (pykeepass.exceptions.HeaderChecksumError, pykeepass.exceptions.PayloadChecksumError) as exc:
                raise AnsibleError('Could not open the database, as the checksum of the database is wrong. This could be caused by a corrupt database.') from exc
        directory_list = group_path.split("/")
        for idx, dir in enumerate(directory_list):
            if dir == "":
                directory_list.pop(idx)
        group = kp.find_groups(path=directory_list, first=True)

        entries = kp.find_entries(title=title, group=group, regex=regex, recursive=recursive, notes=notes, url=url, tags=tags, username=username)
        for entry in entries:
            ret.append(set_result(entry))

        return ret
    
def set_result(entry):
    result = {}
    result['title']             = entry.title
    result['username']          = entry.username
    result['group_path']        = ""
    for path in entry.group.path:
        result['group_path'] += path + "/"
    result['icon_id']           = entry.icon
    result['username']          = entry.username
    result['password']          = entry.password
    result['url']               = entry.url
    result['notes']             = entry.notes
    result['tags']              = entry.tags
    return result
