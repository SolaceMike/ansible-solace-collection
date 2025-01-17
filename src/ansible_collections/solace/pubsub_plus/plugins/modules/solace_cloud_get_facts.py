#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2020, Solace Corporation, Ricardo Gomez-Ulmke, <ricardo.gomez-ulmke@solace.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: solace_cloud_get_facts

short_description: access solace facts from M(solace_cloud_account_gather_facts)

description: >
    Provides convenience functions to access Solace Cloud service facts gathered with M(solace_cloud_account_gather_facts).
    Call M(solace_cloud_account_gather_facts) first.

options:
    from_dict:
        description: The JSON object (dict) which holds the facts. This is direct result from the GET {service} call.
        required: True
        type: dict
    field_funcs:
        description: List of pre-built field functions that retrieve values from the 'from_dict'.
        required: false
        type: list
        default: []
        elements: str
        suboptions:
            get_serviceSEMPManagementEndpoints:
                description: Retrieves the SEMP management endpoint.
                type: str
                required: no
    get_formattedHostInventory:
        description: >
            Get the facts formatted as a JSON host inventory.
            Retrieve the inventory field by field or
            save to file and use in subsequent playbooks as an inventory.
        type: dict
        required: no
        suboptions:
            host_entry:
                description: The entry for this broker / service in the hosts file. Must be a valid JSON key.
                type: str
                required: true
            api_token:
                description: The API token to access the Solace Cloud Service API.
                type: str
                required: true
            meta:
                description: Additional meta data describing the service instance.
                type: dict
                required: true

seealso:
- module: solace_cloud_account_gather_facts
- module: solace_cloud_get_service

author: Ricardo Gomez-Ulmke (@rjgu)
'''

EXAMPLES = '''

  hosts: all
  gather_facts: no
  any_errors_fatal: true
  collections:
    - solace.pubsub_plus
  tasks:
    - name: "Get Service"
      solace_cloud_get_service:
        api_token: "{{ api_token }}"
        service_id: "{{ serviceId }}"
      register: result

    - name: "Set Fact: Solace Service Details"
      set_fact:
        sc_service_details: "{{ result.response }}"

    - name: "Get Semp Management Endpoints"
      solace_cloud_get_facts:
        from_dict: "{{ sc_service_details }}"
        field_funcs:
            - get_serviceSEMPManagementEndpoints
        register: semp_enpoints_facts

    - name: "Save Solace Cloud Service SEMP Management Endpoints to File"
      copy:
        content: "{{ semp_enpoints_facts | to_nice_json }}"
        dest: "./tmp/facts.solace_cloud_service.semp.json"
      delegate_to: localhost

    - name: "Set Fact: Solace Service SEMP"
      set_fact:
        sempv2_host: "{{ semp_enpoints_facts.facts.serviceManagementEndpoints.SEMP.SecuredSEMP.uriComponents.host }}"
        sempv2_port: "{{ semp_enpoints_facts.facts.serviceManagementEndpoints.SEMP.SecuredSEMP.uriComponents.port }}"
        sempv2_is_secure_connection: True
        sempv2_username: "{{ semp_enpoints_facts.facts.serviceManagementEndpoints.SEMP.username }}"
        sempv2_password: "{{ semp_enpoints_facts.facts.serviceManagementEndpoints.SEMP.password }}"
        sempv2_timeout: 60

    - name: "Gather Solace Facts from Service"
      solace_gather_facts:
        host: "{{ sempv2_host }}"
        port: "{{ sempv2_port }}"
        secure_connection: "{{ sempv2_is_secure_connection }}"
        username: "{{ sempv2_username }}"
        password: "{{ sempv2_password }}"
        timeout: "{{ sempv2_timeout }}"
        solace_cloud_api_token: "{{ api_token }}"
        solace_cloud_service_id: "{{ serviceId }}"

    - name: "Save Solace Cloud Service Facts to File"
      copy:
        content: "{{ ansible_facts.solace | to_nice_json }}"
        dest: "./tmp/solace_facts.solace_cloud_service.json"
      delegate_to: localhost

    - name: "Get Host Inventory"
      solace_cloud_get_facts:
        from_dict: "{{ sc_service_details }}"
        get_formattedHostInventory:
          host_entry: "{{ sc_service_name }}"
          api_token: "{{ api_token }}"
          meta:
            service_name: "{{ sc_service_details.name }}"
            service_id: "{{ sc_service_details.serviceId }}"
            datacenterId: "{{ sc_service_details.datacenterId }}"
            serviceTypeId: "{{ sc_service_details.serviceTypeId}}"
            serviceClassId: "{{ sc_service_details.serviceClassId }}"
            serviceClassDisplayedAttributes: "{{ sc_service_details.serviceClassDisplayedAttributes }}"
      register: inv_results

    - name: "Save Solace Cloud Service inventory to File"
      copy:
        content: "{{ inv_results.facts.formattedHostInventory | to_nice_json }}"
        dest: "./tmp/inventory.{{ sc_service_name }}.json"
      delegate_to: localhost
'''

RETURN = '''

    rc:
        description: return code, either 0 (ok), 1 (not ok)
        type: int
        returned: always
        sample:
            rc: 0
    msg:
        description: error message if not ok
        type: str
        returned: error
    facts:
        description: The facts retrieved from the input.
        type: dict
        returned: success

'''
from ansible_collections.solace.pubsub_plus.plugins.module_utils.solace_error import SolaceError
import ansible_collections.solace.pubsub_plus.plugins.module_utils.solace_common as sc
from ansible.module_utils.basic import AnsibleModule
from urllib.parse import urlparse
import json
from json.decoder import JSONDecodeError
import traceback


class SolaceCloudGetFactsTask():

    def __init__(self, module):
        sc.module_fail_on_import_error(module, sc.HAS_IMPORT_ERROR, sc.IMPORT_ERR_TRACEBACK)
        self.module = module
        return

    FIELD_FUNCS = [
        "get_serviceSEMPManagementEndpoints"
    ]

# check:
# at least one field_func or get_formattedHostInventory needs to be specified
# could be both or multiple
    def validate_args(self):
        field_funcs = self.module.params['field_funcs']
        has_get_funcs = False
        if field_funcs is not None and len(field_funcs) > 0:
            for field_func in field_funcs:
                exists = (True if field_func in self.FIELD_FUNCS else False)
                if not exists:
                    return False, f"Unknown field_func='{field_func}'. Valid field functions are: {self.FIELD_FUNCS}."
            has_get_funcs = True

        param_get_formattedHostInventory = self.module.params['get_formattedHostInventory']
        if param_get_formattedHostInventory is not None:
            has_get_funcs = True
        if not has_get_funcs:
            return False, "no get functions found. Specify at least one."
        return True, ''

    def get_facts(self):
        ok, msg = self.validate_args()
        if not ok:
            return False, msg
        # return facts['formattedHostInventory']
        from_dict = self.module.params['from_dict']
        search_object = from_dict
        facts = dict()
        field_funcs = self.module.params['field_funcs']
        if field_funcs and len(field_funcs) > 0:
            try:
                for field_func in field_funcs:
                    field, value = globals()[field_func](search_object)
                    facts[field] = value
            except SolaceError as e:
                ex_msg_list = [f"field_func:'{field_func}'"] + e.to_list()
                raise SolaceError(ex_msg_list) from e

        try:
            param_get_formattedHostInventory = self.module.params['get_formattedHostInventory']
            if param_get_formattedHostInventory:
                field, value = get_formattedHostInventory(search_object,
                                                          param_get_formattedHostInventory['host_entry'],
                                                          param_get_formattedHostInventory['api_token'],
                                                          param_get_formattedHostInventory['meta'])
        except SolaceError as e:
            ex_msg_list = ["get_formattedHostInventory():"] + e.to_list()
            raise SolaceError(ex_msg_list) from e

        facts[field] = value

        return True, facts

#
# field funcs
#


def get_formattedHostInventory(search_dict, host_entry, api_token, meta):
    if not isinstance(search_dict, dict):
        raise SolaceError(f"input is not of type 'dict', but type='{type(search_dict)}'.")

    _eps_field, eps_val = get_serviceSEMPManagementEndpoints(search_dict)
    inv = dict(
        all=dict()
    )
    hosts = dict()
    hosts[host_entry] = {
        'meta': meta,
        'ansible_connection': 'local',
        'broker_type': 'solace_cloud',
        'solace_cloud_api_token': api_token,
        'solace_cloud_service_id': search_dict['serviceId'],
        'sempv2_host': eps_val['SEMP']['SecuredSEMP']['uriComponents']['host'],
        "sempv2_port": eps_val['SEMP']['SecuredSEMP']['uriComponents']['port'],
        "sempv2_is_secure_connection": True,
        "sempv2_username": eps_val['SEMP']['username'],
        "sempv2_password": eps_val['SEMP']['password'],
        "sempv2_timeout": "60",
        "vpn": search_dict['msgVpnName'],
        "virtual_router": "primary"

    }
    inv['all']['hosts'] = hosts
    return 'formattedHostInventory', inv


def get_serviceSEMPManagementEndpoints(search_dict):
    if not isinstance(search_dict, dict):
        raise SolaceError(f"input is not of type 'dict', but type='{type(search_dict)}'.")
    eps = dict(
        SEMP=dict(
            SecuredSEMP=dict()
        )
    )
    mgmt_protocols_dict = _get_field(search_dict, 'managementProtocols')
    if mgmt_protocols_dict is None:
        raise SolaceError("Could not find 'managementProtocols' in 'from_dict'.")
    semp_dict = _find_nested_dict(mgmt_protocols_dict, field="name", value='SEMP')
    if semp_dict is None:
        raise SolaceError("Could not find 'name=SEMP' in 'managementProtocols' in 'from_dict'.")
    sec_semp_end_point_dict = _get_protocol_endpoint(semp_dict, field='name', value='Secured SEMP Config')
    sec_semp_uri = _get_protocol_endpoint_uri(sec_semp_end_point_dict)
    t = urlparse(sec_semp_uri)
    sec_semp_protocol = t.scheme
    sec_semp_host = t.hostname
    sec_semp_port = t.port
    # put the dict together
    sec_semp = dict()
    sec_semp_ucs = dict()
    sec_semp_ucs['protocol'] = sec_semp_protocol
    sec_semp_ucs['host'] = sec_semp_host
    sec_semp_ucs['port'] = sec_semp_port
    sec_semp['uriComponents'] = sec_semp_ucs
    sec_semp['uri'] = sec_semp_uri
    eps['SEMP']['SecuredSEMP'] = sec_semp
    eps['SEMP']['username'] = semp_dict['username']
    eps['SEMP']['password'] = semp_dict['password']
    return 'serviceManagementEndpoints', eps

#
# field func helpers
#


def _get_protocol_endpoint(search_dict, field, value):
    element = 'endPoints'
    if element not in search_dict:
        raise SolaceError(f"Could not find '{element}' in dict:{search_dict}.")
    end_points = search_dict[element]
    if len(end_points) == 0:
        raise SolaceError(f"Empty list:'{element}' in dict:{search_dict}.")
    end_point_dict = _find_nested_dict(end_points, field, value)
    if end_point_dict is None:
        raise SolaceError(f"Could not find end point with '{field}={value}'.")
    return end_point_dict


def _get_protocol_endpoint_uri(search_dict):
    element = 'uris'
    if element not in search_dict:
        errs = [
            f"Could not find '{element}' in end point:",
            f"{json.dumps(search_dict)}"
        ]
        raise SolaceError(errs)
    if len(search_dict['uris']) != 1:
        errs = [
            f"'{element}' list contains != 1 elements in end point:",
            f"{json.dumps(search_dict)}"
        ]
        raise SolaceError(errs)
    return search_dict['uris'][0]


def _find_nested_dict(search_dict, field, value):
    if isinstance(search_dict, dict):
        if field in search_dict and search_dict[field] == value:
            return search_dict
        for key in search_dict:
            item = _find_nested_dict(search_dict[key], field, value)
            if item is not None:
                return item
    elif isinstance(search_dict, list):
        for element in search_dict:
            item = _find_nested_dict(element, field, value)
            if item is not None:
                return item
    return None


def _get_field(search_dict, field):
    if isinstance(search_dict, dict):
        if field in search_dict:
            return search_dict[field]
        for key in search_dict:
            item = _get_field(search_dict[key], field)
            if item is not None:
                return item
    elif isinstance(search_dict, list):
        for element in search_dict:
            item = _get_field(element, field)
            if item is not None:
                return item
    return None


def run_module():
    module_args = dict(
        from_dict=dict(type='dict', required=True),
        field_funcs=dict(type='list', required=False, elements='str'),
        get_formattedHostInventory=dict(type='dict',
                                        required=False,
                                        default=None,
                                        options=dict(
                                            host_entry=dict(type='str', required=True),
                                            api_token=dict(type='str', required=True),
                                            meta=dict(type='dict', required=True)
                                        ))
    )
    arg_spec = dict()
    arg_spec.update(module_args)

    module = AnsibleModule(
        argument_spec=arg_spec,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        facts=dict(),
        rc=0
    )

    solace_task = SolaceCloudGetFactsTask(module)
    try:
        ok, resp = solace_task.get_facts()
        if not ok:
            result['rc'] = 1
            module.fail_json(msg=resp, **result)
    except SolaceError as e:
        ex = traceback.format_exc()
        ex_msg_list = e.to_list()
        msg = ["Pls raise an issue including the full traceback. (hint: use -vvv)"] + ex_msg_list + ex.split('\n')
        module.fail_json(msg=msg, exception=ex)

    result['facts'] = resp
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
