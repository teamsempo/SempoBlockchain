import os
import json
import sys

APP_REPO_BASE_URL = '290492953667.dkr.ecr.ap-southeast-2.amazonaws.com/app:server_'
WORKER_REPO_BASE_URL = '290492953667.dkr.ecr.ap-southeast-2.amazonaws.com/eth_worker:eth_worker_'

def strip_def(definition):
    definition.pop('taskDefinitionArn')
    definition.pop('compatibilities')
    definition.pop('requiresAttributes')
    definition.pop('status')
    definition.pop('revision')

def replace_container_url(definition, new_url):
    for a in definition['containerDefinitions']:
        a['image'] = new_url

print(sys.argv)
stream = os.popen('aws ecs describe-task-definition --task-definition '+ sys.argv[1])
output = stream.read()
task_definition = json.loads(output)['taskDefinition']
strip_def(task_definition)
replace_container_url(task_definition, APP_REPO_BASE_URL+sys.argv[3])
app_file = open('ecs_app_task_config.json', 'w')
app_file.write(json.dumps(task_definition))

stream = os.popen('aws ecs describe-task-definition --task-definition '+ sys.argv[2])
output = stream.read()
task_definition = json.loads(output)['taskDefinition']
strip_def(task_definition)
replace_container_url(task_definition, WORKER_REPO_BASE_URL+sys.argv[3])
app_file = open('ecs_app_worker_config.json', 'w')
app_file.write(json.dumps(task_definition))

