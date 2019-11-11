import glob
import subprocess
import os
import hashlib
import configparser


def shahash(fpath):
    hash_sha = hashlib.sha1()
    with open(fpath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha.update(chunk)
    return hash_sha.hexdigest()

try:
    os.chdir('./.sempoconfig')
except FileNotFoundError:
    pass

os.environ['AWS_PROFILE'] = "sempo"

for in_path in glob.glob('../config_files/*.ini'):
    head, filename = os.path.split(in_path)

    print('Found file:')
    print(filename)

    new_hash = shahash(in_path)

    out_path = './{}'.format(filename)

    skip = False
    try:
        pre_paser = configparser.ConfigParser()
        pre_paser.read(out_path)
        orginal_hash = pre_paser['META']['data_hash']

        if orginal_hash == new_hash:
            print('File contents are identical, skipping')
            skip = True
    except KeyError:
        pass

    if not skip:

        with open(out_path, 'w') as f:
            subprocess.call(['sops', '-e', in_path], stdout=f)

        post_paser = configparser.ConfigParser()
        post_paser.read(out_path)
        post_paser['META'] = {}
        post_paser['META']['data_hash'] = new_hash

        with open(out_path, 'w') as f:
            post_paser.write(f)
