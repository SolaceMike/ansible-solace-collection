#!/usr/bin/env bash
# Copyright (c) 2020, Solace Corporation, Ricardo Gomez-Ulmke, <ricardo.gomez-ulmke@solace.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

scriptDir=$(cd $(dirname "$0") && pwd);
scriptName=$(basename $(test -L "$0" && readlink "$0" || echo "$0"));
testTarget=${scriptDir##*/}
scriptLogName="$testTargetGroup.$testTarget.$scriptName"
if [ -z "$PROJECT_HOME" ]; then echo ">>> ERROR: - $scriptLogName - missing env var: PROJECT_HOME"; exit 1; fi
source $PROJECT_HOME/.lib/functions.sh

############################################################################################################################
# Environment Variables

  if [ -z "$LOG_DIR" ]; then echo ">>> ERROR: - $scriptLogName - missing env var: LOG_DIR"; exit 1; fi
  if [ -z "$WORKING_DIR" ]; then echo ">>> ERROR: - $scriptLogName - missing env var: WORKING_DIR"; exit 1; fi
  if [ -z "$SOLACE_CLOUD_API_TOKEN_ALL_PERMISSIONS" ]; then echo ">>> ERROR: - $scriptLogName - missing env var: SOLACE_CLOUD_API_TOKEN_ALL_PERMISSIONS"; exit 1; fi
  if [ -z "$SOLACE_CLOUD_INVENTORY_FILE_NAME" ]; then echo ">>> ERROR: - $scriptLogName - missing env var: SOLACE_CLOUD_INVENTORY_FILE_NAME"; exit 1; fi
  if [ -z "$TEARDOWN_SOLACE_CLOUD" ]; then export TEARDOWN_SOLACE_CLOUD=True; fi

##############################################################################################################################
# Settings

  export ANSIBLE_SOLACE_LOG_PATH="$LOG_DIR/$scriptLogName.ansible-solace.log"
  export ANSIBLE_LOG_PATH="$LOG_DIR/$scriptLogName.ansible.log"

##############################################################################################################################
# Run

  solaceCloudInventory=$(assertFile $scriptLogName "$WORKING_DIR/$SOLACE_CLOUD_INVENTORY_FILE_NAME") || exit

  playbooks=(
    "$scriptDir/main.playbook.yml"
  )

  for playbook in ${playbooks[@]}; do

    playbook=$(assertFile $scriptLogName $playbook) || exit
    ansible-playbook \
                    -i $solaceCloudInventory \
                    $playbook \
                    --extra-vars "WORKING_DIR=$WORKING_DIR" \
                    --extra-vars "SOLACE_CLOUD_API_TOKEN=$SOLACE_CLOUD_API_TOKEN_ALL_PERMISSIONS" \
                    --extra-vars "SOLACE_CLOUD_INVENTORY_FILE_NAME=$SOLACE_CLOUD_INVENTORY_FILE_NAME" \
                    --extra-vars "TEARDOWN_SOLACE_CLOUD=$TEARDOWN_SOLACE_CLOUD"
    code=$?; if [[ $code != 0 ]]; then echo ">>> ERROR - $code - script:$scriptLogName, playbook:$playbook"; exit 1; fi

  done

echo ">>> SUCCESS: $scriptLogName"

###
# The End.
