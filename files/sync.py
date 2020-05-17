"""External file retrieval
"""

# standard imports
import os
import logging

logg = logging.getLogger(__file__)


class FileSyncer:
    """Parent class to be overloaded by component providing access to
    external file resources.

    A function is passed to the constructor by the implementer, which _must_ 
    fulfull the following interface:
        * accept a single string as argument for the filename to retrieve
        * return an object implementing a read(blocksize=int) method

    Attributes
    ----------
    blocksize : int
        byte count used as argument for read from remote source
    source_path : str
        implementation-dependent source file identifier
    destination_path : str
        path used for output of retrieved files
    getfunc : function
        implementer file callback function

    Args
    ----
    source_path : str
        implementation-dependent source file identifier
    destination_path : str
        path used for output of retrieved files
    getfunc : function
        implementer file callback function
    """

    blocksize = 1024

    def source_is_newer(self, filepath: str) -> bool:
        """Abstract method called by sync to determine whether a file should be
        retrieved.

        This default implementation will always return False.
        """

        return False


    def sync(self, files: list) -> list:
        """Retrieves the given list of files from the implemented remote source.

        Parameters
        ----------
        files : list
            list of files to retrieve

        Returns
        -------
        retrieved_files : list
        """

        updated_files = []
        os.makedirs(self.destination_path, 0o777, exist_ok=True)
        for f in files:
            if self.source_is_newer(f):
                fo = open(self.destination_path + '/' + f, 'wb')
                r = self.getfunc(f)
                while 1:
                    data = r.read(self.blocksize)
                    if not data:
                        break
                    fo.write(data)
                r.close()
                fo.close()
                updated_files.append(f)

        return updated_files


    def __init__(self, source_path, destination_path, getfunc):
        self.source_path = source_path
        self.destination_path = destination_path
        self.getfunc = getfunc
