import glob
import subprocess
import os

try:
    os.chdir('./.sempoconfig')
except FileNotFoundError:
    pass

os.environ['AWS_PROFILE'] = "sempo"

i = input('You are about to replace your LOCAL config files with those from git - are you sure? (y/n)')

if i == 'y':
    for in_path in glob.glob('./*.ini'):
        head, filename = os.path.split(in_path)

        print('Found file:')
        print(filename)

        out_path = '../config_files/{}'.format(filename)

        with open(out_path, 'w') as f:
            subprocess.call(['sops', '-d', in_path], stdout=f)
else:
    print('Aborting')
