import glob
import subprocess
import os

try:
    os.chdir('./.sempoconfig')
except FileNotFoundError:
    pass

print('Attempting SOPS Confgif load')

for in_path in glob.glob('./*.ini'):
    head, filename = os.path.split(in_path)

    print('Found file:')
    print(filename)

    out_path = '../test_config_files/{}'.format(filename)

    with open(out_path, 'w') as f:
        subprocess.call(['sops', '-d', in_path], stdout=f)
