import glob
import subprocess
import os

for path in glob.glob('./.sempoconfig/*.ini'):
    head, filename = os.path.split(path)
    subprocess.Popen(['sops', '-d', path, '>', f'./test_config_files/{filename}'])

# Making a random changes