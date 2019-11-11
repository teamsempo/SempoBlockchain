import glob
import subprocess
import os
import hashlib
import configparser

def shahash(fpath):
    hash_sha = hashlib.sha1()

    try:
        hash_parser = configparser.ConfigParser()
        hash_parser.read(fpath)
        for each_section in hash_parser.sections():
            for (each_key, each_val) in hash_parser.items(each_section):
                hash_sha.update('{}{}'.format(each_key, each_val).encode())
        return hash_sha.hexdigest()
    except FileNotFoundError:
        return None

try:
    os.chdir('./.sempoconfig')
except FileNotFoundError:
    pass

os.environ['AWS_PROFILE'] = "sempo"

for in_path in glob.glob('../config_files/*.ini'):
    head, filename = os.path.split(in_path)
    print('---Found file: {}'.format(filename))

    out_path = './{}'.format(filename)
    meta_path = './meta.ini'

    new_hash = shahash(in_path)

    skip = False

    try:
        meta_parser = configparser.ConfigParser()
        meta_parser.read(meta_path)
        orginal_hash = meta_parser['HASHES'][filename]

        if orginal_hash == new_hash:
            print('File contents are identical, skipping')
            skip = True
    except KeyError:
        pass

    if not skip:
        print('encrypting')
        with open(out_path, 'w') as f:
            subprocess.call(['sops', '-e', in_path], stdout=f)

        meta_parser = configparser.ConfigParser()
        meta_parser.read(meta_path)
        try:
            meta_parser['HASHES']
        except KeyError:
            meta_parser['HASHES'] = {}

        meta_parser['HASHES'][filename] = new_hash

        with open(meta_path, 'w') as f:
            meta_parser.write(f)

