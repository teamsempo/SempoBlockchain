import os
import json
import sys

cluster = sys.argv[1]
region = sys.argv[2]
stream = os.popen(f'aws ecs list-tasks --cluster {cluster} --region {region}')
task_list = json.loads(stream.read())['taskArns']
for task in task_list:
    os.popen(f'aws ecs stop-task --task {task} --cluster {cluster} --region {region}')
    output = stream.read()
    print(output)