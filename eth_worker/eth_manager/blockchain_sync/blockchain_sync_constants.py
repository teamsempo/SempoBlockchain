BLOCKS_PER_REQUEST = 5000
# How long a blockchain_sync lock can last.
# This is set to 2 days, longer than any `synchronize_third_party_transactions` should last.
# The reason for this is just in case the app terminates mid-operation and the lock is never
# freed, this removes the need to go in manually and remove the lock from the redis server.
LOCK_TIMEOUT = 172800 
