
# Hit the database to get the latest block number to which we're synced
def get_latest_block_number():
    pass

# Call webhook
def call_webhook():
    pass

# Basic 'update' function that gets everything since the database's latest block
def sync_app_to_blockchain():
    # Some logic to chunk up start_block->end_block range. 
    pass

# Do the above, but for every filter as well. This will be called by the celery_tasks task
def sync_all_filters_to_app():
    #for f in filters:
    #   sync_app_to_blockchain(f)