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
module: solace_rdp_queue_binding

short_description: queue bindining for rdp

description:
    - "Allows addition, removal and configuration of Queue Binding objeccts for a Rest Delivery Point(RDP). "
    - "Reference documentation: https://docs.solace.com/API-Developer-Online-Ref-Documentation/swagger-ui/config/index.html#/restDeliveryPoint/getMsgVpnRestDeliveryPointQueueBindings."

seealso:
- module: solace_rdp
- module: solace_queue

options:
  queue_name:
    description: Name of the queue. Maps to 'queueBindingName' in the API.
    required: true
    type: str
    aliases: [name]
  rdp_name:
    description: Name of the RDP. Maps to 'restDeliveryPointName' in the API.
    required: true
    type: str

extends_documentation_fragment:
- solace.pubsub_plus.solace.broker
- solace.pubsub_plus.solace.vpn
- solace.pubsub_plus.solace.settings
- solace.pubsub_plus.solace.state

author:
  - Ricardo Gomez-Ulmke (@rjgu)
'''

EXAMPLES = '''
hosts: all
gather_facts: no
any_errors_fatal: true
collections:
- solace.pubsub_plus
module_defaults:
  solace_rdp:
    host: "{{ sempv2_host }}"
    port: "{{ sempv2_port }}"
    secure_connection: "{{ sempv2_is_secure_connection }}"
    username: "{{ sempv2_username }}"
    password: "{{ sempv2_password }}"
    timeout: "{{ sempv2_timeout }}"
    msg_vpn: "{{ vpn }}"
  solace_queue:
    host: "{{ sempv2_host }}"
    port: "{{ sempv2_port }}"
    secure_connection: "{{ sempv2_is_secure_connection }}"
    username: "{{ sempv2_username }}"
    password: "{{ sempv2_password }}"
    timeout: "{{ sempv2_timeout }}"
    msg_vpn: "{{ vpn }}"
  solace_rdp_queue_binding:
    host: "{{ sempv2_host }}"
    port: "{{ sempv2_port }}"
    secure_connection: "{{ sempv2_is_secure_connection }}"
    username: "{{ sempv2_username }}"
    password: "{{ sempv2_password }}"
    timeout: "{{ sempv2_timeout }}"
    msg_vpn: "{{ vpn }}"
tasks:
  - name: Create RDP
    solace_rdp:
      name: "rdp"
      state: present

  - name: Create Queue
    solace_queue:
      name: "rdp-queue"
      state: present

  - name: Create a Queue Binding
    solace_rdp_queue_binding:
      rdp_name: "rdp"
      queue_name: "rdp-queue"
      settings:
        postRequestTarget: "{host}:{port}"
      state: present
'''

RETURN = '''
response:
    description: The response from the Solace Sempv2 request.
    type: dict
    returned: success
'''

import ansible_collections.solace.pubsub_plus.plugins.module_utils.solace_common as sc
import ansible_collections.solace.pubsub_plus.plugins.module_utils.solace_utils as su
from ansible.module_utils.basic import AnsibleModule


class SolaceRdpQueueBindingTask(su.SolaceTask):

    LOOKUP_ITEM_KEY = 'queueBindingName'

    def __init__(self, module):
        su.SolaceTask.__init__(self, module)

    def lookup_item(self):
        return self.module.params['queue_name']

    def get_args(self):
        return [self.module.params['msg_vpn'], self.module.params['rdp_name']]

    def get_func(self, solace_config, vpn, rdp_name, lookup_item_value):
        # GET /msgVpns/{msgVpnName}/restDeliveryPoints/{restDeliveryPointName}/queueBindings/{queueBindingName}
        path_array = [su.SEMP_V2_CONFIG, su.MSG_VPNS, vpn, su.RDP_REST_DELIVERY_POINTS, rdp_name, su.RDP_QUEUE_BINDINGS, lookup_item_value]
        return su.get_configuration(solace_config, path_array, self.LOOKUP_ITEM_KEY)

    def create_func(self, solace_config, vpn, rdp_name, name, settings=None):
        # POST /msgVpns/{msgVpnName}/restDeliveryPoints/{restDeliveryPointName}/queueBindings
        defaults = {}
        mandatory = {
            'msgVpnName': vpn,
            'restDeliveryPointName': rdp_name,
            'queueBindingName': name
        }
        data = su.merge_dicts(defaults, mandatory, settings)
        path_array = [su.SEMP_V2_CONFIG, su.MSG_VPNS, vpn, su.RDP_REST_DELIVERY_POINTS, rdp_name, su.RDP_QUEUE_BINDINGS]
        return su.make_post_request(solace_config, path_array, data)

    def update_func(self, solace_config, vpn, rdp_name, lookup_item_value, settings):
        # PATCH /msgVpns/{msgVpnName}/restDeliveryPoints/{restDeliveryPointName}/queueBindings/{queueBindingName}
        path_array = [su.SEMP_V2_CONFIG, su.MSG_VPNS, vpn, su.RDP_REST_DELIVERY_POINTS, rdp_name, su.RDP_QUEUE_BINDINGS, lookup_item_value]
        return su.make_patch_request(solace_config, path_array, settings)

    def delete_func(self, solace_config, vpn, rdp_name, lookup_item_value):
        # DELETE /msgVpns/{msgVpnName}/restDeliveryPoints/{restDeliveryPointName}/queueBindings/{queueBindingName}
        path_array = [su.SEMP_V2_CONFIG, su.MSG_VPNS, vpn, su.RDP_REST_DELIVERY_POINTS, rdp_name, su.RDP_QUEUE_BINDINGS, lookup_item_value]
        return su.make_delete_request(solace_config, path_array)


def run_module():
    module_args = dict(
        rdp_name=dict(type='str', required=True),
        queue_name=dict(type='str', required=True, aliases=['name'])
    )
    arg_spec = su.arg_spec_broker()
    arg_spec.update(su.arg_spec_vpn())
    arg_spec.update(su.arg_spec_settings())
    arg_spec.update(su.arg_spec_state())
    # module_args override standard arg_specs
    arg_spec.update(module_args)

    module = AnsibleModule(
        argument_spec=arg_spec,
        supports_check_mode=True
    )

    solace_task = SolaceRdpQueueBindingTask(module)
    result = solace_task.do_task()

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
