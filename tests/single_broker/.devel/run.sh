#!/usr/bin/env bash
# Copyright (c) 2020, Solace Corporation, Ricardo Gomez-Ulmke, <ricardo.gomez-ulmke@solace.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

scriptDir=$(cd $(dirname "$0") && pwd);
scriptName=$(basename $(test -L "$0" && readlink "$0" || echo "$0"));
projectHome=${scriptDir%/ansible-solace-collection/*}
if [[ ! $projectHome =~ "ansible-solace-collection" ]]; then
  projectHome=$projectHome/ansible-solace-collection
fi
export PROJECT_HOME=$projectHome


ansibleSolaceTests=(
  # "setup"
  # "solace_get_available"
  # "solace_facts"
  # "solace_acl_profile"
  # "solace_client_profile"
  "solace_rdp"
  # "solace_mqtt"
  # "solace_queue"
  # "solace_topic_endpoint"
  # "solace_client_username"
  # "solace_get_vpn_clients"
  # "solace_vpn"
  # "solace_cert_authority"
  # "teardown"
)
export ANSIBLE_SOLACE_TESTS="${ansibleSolaceTests[*]}"

# local broker
  export BROKER_DOCKER_IMAGE="solace/solace-pubsub-standard:latest"
  # export BROKER_DOCKER_IMAGE="solace/solace-pubsub-standard:9.7.0.29"
  # export BROKER_DOCKER_IMAGE="solace/solace-pubsub-standard:9.3.1.28"
  export BROKER_TYPE="local"
  export LOCAL_BROKER_INVENTORY_FILE="$projectHome/test-runner/files/local.broker.inventory.yml"
  export BROKER_DOCKER_COMPOSE_FILE="$projectHome/test-runner/files/PubSubStandard_singleNode.yml"
  export INVENTORY_FILE=$LOCAL_BROKER_INVENTORY_FILE

# # solace cloud broker
#   export BROKER_TYPE="solace_cloud"
#   export INVENTORY_FILE="$projectHome/test-runner/files/solace-cloud-account.inventory.yml"
#   export SOLACE_CLOUD_API_TOKEN=$SOLACE_CLOUD_API_TOKEN_ALL_PERMISSIONS

export CLEAN_WORKING_DIR=False

export LOG_DIR=$scriptDir/logs
mkdir -p $LOG_DIR
rm -rf $LOG_DIR/*

export ANSIBLE_LOG_PATH="$LOG_DIR/ansible.log"
export ANSIBLE_DEBUG=False
export ANSIBLE_VERBOSITY=3
# logging: ansible-solace
export ANSIBLE_SOLACE_LOG_PATH="$LOG_DIR/ansible-solace.log"
export ANSIBLE_SOLACE_ENABLE_LOGGING=True

export RUN_FG=true
# export RUN_FG=false

../_run.sh

###
# The End.
