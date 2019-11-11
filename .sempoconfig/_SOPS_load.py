import glob
import subprocess
import os
import configparser
import hashlib

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

i = input('You are about to replace your LOCAL config files with those from git - are you sure? (y/n)')

if i == 'y':
    for in_path in glob.glob('./*.ini'):
        head, filename = os.path.split(in_path)
        if filename != 'meta.ini':
            print('---Found file: {}---'.format(filename))

            out_path = '../config_files/{}'.format(filename)
            meta_path = './meta.ini'

            new_hash = shahash(out_path)

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
                print('decrypting')
                with open(out_path, 'w') as f:
                    subprocess.call(['sops', '-d', in_path], stdout=f)
else:
    print('Aborting')
