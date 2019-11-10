import glob
import subprocess
import os

for in_path in glob.glob('./test_config_files/*.ini'):
    head, filename = os.path.split(in_path)
    out_path = './.sempoconfig/{}'.format(filename)

    with open(out_path, 'w') as f:
        subprocess.call(['sops', '-e', in_path], stdout=f)
