===================================
Torie\_Coding.Keepass Release Notes
===================================

.. contents:: Topics

v1.2.1
======

Release Summary
---------------

| Release Date: 2024-06-12
| Added group - fixed modify action. 

Minor Changes
-------------

- group - fixed modify action.

v1.2.0
======

Release Summary
---------------

| Release Date: 2024-06-11
| Added lookup plugin for entries and fixed docs

Major Changes
-------------

- added lookup plugin for entries

Minor Changes
-------------

- entry and group examples added 'keyfile' example
- modifed README.md to include changes

New Plugins
-----------

Lookup
~~~~~~

- torie_coding.keepass.lookup - Search for Entries in a KeePass Database

v1.1.5
======

Release Summary
---------------

| Release Date: 2024-02-04
| Fixed behavior when no icon_id provided

Bugfixes
--------

- entry - None value for icon_id did result in a database error. None values are possible now. Thanks to @kism
- group - None value for icon_id did result in a database error. None values are possible now. Thanks to @kism

v1.1.4
======

Release Summary
---------------

| Release Date: 2023-10-25
| Fixed creating group unter root group and added feature in entry to create custom notes

Minor Changes
-------------

- entry - added feature to create custom notes

Bugfixes
--------

- group - creating a group under root directory results in nontype value

v1.1.3
======

Release Summary
---------------

| Release Date: 2023-10-24
| Fixed wrong var type in the add_group and add_entry calls

Bugfixes
--------

- entry - icon_id var was called as 'id' but has to be 'str'
- group - icon_id var was called as 'id' but has to be 'str'

v1.1.2
======

Release Summary
---------------

| Release Date: 2023-10-24
| Fixed docs and wrong var type

Minor Changes
-------------

- entry,group, README - fixed

Bugfixes
--------

- entry - icon_id var was defined as 'str' but has to be 'int'

v1.1.1
======

Release Summary
---------------

| Release Date: 2023-10-24
| Due to problems with Ansible Galaxy-NG we have to create a no Version to be able to upload to Galaxy-NG

v1.1.0
======

Release Summary
---------------

| Release Date: 2023-10-19
| Added Feature nested group creation, added some code optimizations

Major Changes
-------------

- group - nested group creation is possible, if create_path was set to true

Minor Changes
-------------

- entry - range for icon_id was specified
- entry - updated documetation
- group - updated documetation

Breaking Changes / Porting Guide
--------------------------------

- entry - Changed some keys of the return object from the Ansible module. Please check README.md
- entry - The module entry requires the parameter group_path if entry is not located under the root directory. That way the module can make sure which entry should be touched, even if duplicate entries in different directories exist
- group - Changed some keys of the return object from the Ansible module. Please check README.md
- group - The module group requires the parameter path if group is not located under the root directory. When creating a new group the parameter create_path must be set.

v1.0.3
======

Release Summary
---------------

updated repo and hompage in galaxy.yml

Minor Changes
-------------

- galaxy.yml - repo and hompage (iam sorry i really forgot everything)

v1.0.2
======

Release Summary
---------------

updated tags in galaxy.yml

Minor Changes
-------------

- galaxy.yml - updated tags

v1.0.1
======

Release Summary
---------------

Added some Documentation for requirements and defaults

Minor Changes
-------------

- entry.py - Added defaults and corrected Documentation
- group.py - Added defaults and corrected Documentation
- runtime.yml - Added requirert Ansible Version

New Modules
-----------

Torie Coding
~~~~~~~~~~~~

- torie_coding.keepass.torie_coding.entry - Manage entries in a KeePass (kdbx) database.
- torie_coding.keepass.torie_coding.group - Manage groups in a KeePass (kdbx) database.
