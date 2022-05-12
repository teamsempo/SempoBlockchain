import os
import json
import sys

cluster = sys.argv[1]

stream = os.popen('aws ecs list-tasks --cluster '+ cluster)
task_list = json.loads(stream.read())['taskArns']
for task in task_list:
    os.popen(f'aws ecs stop-task --task {task} --cluster {cluster}')
