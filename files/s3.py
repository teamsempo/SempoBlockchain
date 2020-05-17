"""Use AWS S3 as file retrieval backend 
"""

# standard imports
import logging

# third party imports
import boto3

# platform imports
from files.sync import FileSyncer

logg = logging.getLogger(__file__)


class S3(FileSyncer):
    """Provides S3 access through FileSyncer interface

    Attributes
    ----------
    session : boto3.Session
        authenticated S3 session

    Args
    ----
    source_path : str
        bucket name
    destination_path : str
        local path for file output
    key : str
        aws session key id
    secret : str
        aws session secret
    """

    def source_is_newer(self, filepath):
        return True

    def _getfunc(self, item):
        """File callback used by FileSyncer.sync

        Attributes
        ----------
        item : str
            file name to retrieve
        
        Returns
        -------
        reader
            object implementing read(readsize=int) method 
        """

        logg.debug('s3 file sync callback get {} from {}'.format(item, self.source_path))
        reader = None
        try:
            response = self.session.get_object(
                    Bucket=self.source_path,
                    Key=item
                    )
            reader = response['Body']
        # TODO: cannot determine the correct exception; is an "errorfactory instance"
        except Exception as e:
            raise KeyError(e)
        return reader

    def __init__(self, source_path, destination_path, key=None, secret=None):
        super(S3, self).__init__(source_path, destination_path, self._getfunc)
        session = boto3.Session(
            aws_access_key_id       = key,
            aws_secret_access_key   = secret,
        )
        self.session = session.client('s3')
