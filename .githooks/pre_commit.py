import glob
import subprocess
import os

for path in glob.glob('./test_config_files/*.ini'):
    head, filename = os.path.split(path)
    subprocess.Popen(['sops', '-e', path, '>', f'./.sempoconfig/{filename}'])
