"""Sync all internal and external resources before start.

TODO: move file fetching from config.py in here
"""

# standard imports
import logging

# platform imports
import config
from files.s3 import S3

logg = logging.getLogger(__file__)


def init():
    """Initializes the system

    Raises
    ------
    Exception 
        Any exception raised should result in immediate termination
    """
    #if not config.AWS_HAVE_CREDENTIALS:
    #    raise(Exception('translation files are available on AWS S3 only for the moment, but no AWS credentials found'))

    locale_syncer = S3(config.RESOURCE_BUCKET, config.SYSTEM_LOCALE_PATH, key=config.AWS_ACCESS_KEY_ID, secret=config.AWS_SECRET_ACCESS_KEY)
    r = locale_syncer.sync([
        'general_sms.en.yml',
        'general_sms.sw.yml',
        'ussd.en.yml',
        'ussd.sw.yml',
        ])

    for f in r:
        logg.info('synced locale file: {}'.format(f))


# In certain cases, for example a docker invocation script,
# init may be called directly from the command line
if __name__ == "__main__":
    init()
