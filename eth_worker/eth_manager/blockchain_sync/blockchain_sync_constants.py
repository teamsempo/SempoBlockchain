BLOCKS_PER_REQUEST = 500
# How long a blockchain_sync lock can last.
# The lock gets renewed with every synchronized chunk, so the lock will continue to 
# function in long-running jobs
LOCK_TIMEOUT = 120
