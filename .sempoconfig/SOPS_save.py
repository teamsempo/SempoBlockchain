import glob
import subprocess
import os

try:
    os.chdir('./.sempoconfig')
except FileNotFoundError:
    pass

for in_path in glob.glob('../test_config_files/*.ini'):
    head, filename = os.path.split(in_path)

    print('Found file:')
    print(filename)

    out_path = './{}'.format(filename)

    with open(out_path, 'w') as f:
        subprocess.call(['sops', '-e', in_path], stdout=f)
