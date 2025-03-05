#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Author: Tobias Karger und Marie Berger
# Contact: coding@thepatchwork.de
# License: The Unlicense, see LICENSE file.
from __future__ import absolute_import, division, print_function

import re
import traceback

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from pykeepass.entry import Entry

PYKEEPASS_IMP_ERR = None
try:
    import pykeepass.exceptions
    from pykeepass import PyKeePass
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

- name: Find entries in a specific group 
  debug:
    msg: "{{ lookup('lookup', 'entry', database='/path/to/database.kdbx', database_password='secret', group_path='My Group'), recursive=False }}"

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
        self._display.vv("Starting lookup plugin with terms: {}".format(terms))

        if terms[0] == "entry":
            self.set_options(var_options=variables, direct=kwargs)
            database = self.get_option('database')
            self._display.vv("Database path: {}".format(database))
            database_password = self.get_option('database_password')
            keyfile = self.get_option('keyfile')
            title = self.get_option('title')
            group_path = self.get_option('group_path')
            regex = self.get_option('regex')
            recursive = self.get_option('recursive')
            if recursive is None:
                recursive = True  # Default to True for entry searches

            notes = self.get_option('notes')
            url = self.get_option('url')
            tags = self.get_option('tags')
            username = self.get_option('username')

            if not database_password and not keyfile:
                raise AnsibleError("Either 'database_password' or 'keyfile' (or both) are required.")

            self._display.vv("Attempting to open the database...")
            try:
                kp = PyKeePass(database, password=database_password, keyfile=keyfile)
                self._display.vv("Database opened successfully")
            except IOError as exc:
                self._display.vvv("Error opening the database or keyfile: {}".format(exc))
                raise AnsibleError('Could not open the database or keyfile.') from exc
            except pykeepass.exceptions.CredentialsError as exc:
                self._display.vvv("Invalid credentials: {}".format(exc))
                raise AnsibleError('Could not open the database, as the credentials are wrong.') from exc
            except (pykeepass.exceptions.HeaderChecksumError, pykeepass.exceptions.PayloadChecksumError) as exc:
                raise AnsibleError("Could not open the database, as the checksum of the database is wrong. This could be caused by a corrupt database.") from exc

            entries = []
            if not any([title, username, notes, url, tags]):
                if group_path and group_path != "/":
                    # Split the group_path into a list of group names
                    group_path_list = group_path.split('/')
                    self._display.vv("Searching for group path: {}".format(group_path_list))
                    group = kp.find_groups(path=group_path_list, first=True)
                    if not group:
                        raise AnsibleError(f"Group '{group_path}' not found in the database.")
                    self._display.vv("Group found: {}".format(group))
                    entries = group.entries  # Return all entries in this group
                else:
                    # Search in root group
                    # Alle Einträge in der Wurzelgruppe zurückgeben
                    self._display.vv("Returning all entries in the root group")
                    entries = kp.entries
            else:
                # Filtered search
                search_params = {
                    'recursive': recursive,
                    'regex': regex,
                }
                if title:
                    search_params['title'] = title
                if username:
                    search_params['username'] = username
                if notes:
                    search_params['notes'] = notes
                if url:
                    search_params['url'] = url
                if tags and tags != ['']:
                    search_params['tags'] = tags
                if group_path and group_path != "/":
                    group = kp.find_groups(name=group_path, first=True)
                    if not group:
                        raise AnsibleError(f"Group '{group_path}' not found in the database.")
                    search_params['group'] = group
                

                if not recursive and group_path in [None, "/"]:
                    # Explicit search in the root group if not recursive
                    self._display.vv("Performing non-recursive search in the root group")
                    root_group = kp.root_group
                    entries = [e for e in root_group.entries if self.match_entry(e, title, username, notes, url, tags, regex)]
                else:
                    self._display.vv("Search parameters: {}".format(search_params))
                    entries = kp.find_entries(**search_params)

            self._display.vv("Number of entries found: {}".format(len(entries)))

            # Filter only entry objects and process them
            for entry in entries:
                if isinstance(entry, Entry):
                    self._display.vvv(f"Entry found: Title={entry.title}, Group={entry.group.path}, Username={entry.username}")
                    result = self.set_result(entry)
                    self._display.vvv("Entry result: {}".format(result))
                    ret.append(result)
                else:
                    self._display.vvv(f"Skipping non-entry object: {entry}")

        self._display.v("Final search parameters used: {}".format(kwargs))
        return ret

    def match_entry(self, entry, title, username, notes, url, tags, regex):
        """Helper function to match entries against the search criteria."""
        if title and not (regex and re.search(title, entry.title) or entry.title == title):
            return False
        if username and entry.username != username:
            return False
        if notes and entry.notes != notes:
            return False
        if url and entry.url != url:
            return False
        if tags and entry.tags is not None:
            if not set(tags).issubset(set(entry.tags)):
                return False
        return True

    def set_result(self, entry):
        result = {}
        result['title'] = entry.title
        result['username'] = entry.username
        result['group_path'] = "/".join(entry.group.path)
        result['icon_id'] = entry.icon
        result['password'] = entry.password
        result['url'] = entry.url
        result['notes'] = entry.notes
        result['tags'] = entry.tags
        return result