import config
import subprocess
import os

if config.IS_USING_BITCOIN:
    DIR = os.path.abspath(os.path.dirname(__file__))
    script = os.path.join(DIR,'_beat_starter.sh')
    subprocess.call(['ls'])
    subprocess.call([script])
