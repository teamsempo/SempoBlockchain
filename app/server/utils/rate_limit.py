from server import red
from flask import current_app

def rate_limit(key, rate):
    """Function to impose ratelimits on an API. Pass it a key, and it'll only allow that key `rate` times per hour
    key: Key on which to rate limit (like a username)
    rate: Number of allowed requests per hour
    
    Returns True if rate limited
    """

    # Don't ratelimit our unit tests!
    if current_app.config['IS_TEST']:
        return False

    # Check if the key has been tried recently
    if red.exists(key):
        attempts = int(red.get(key))
        if attempts > rate:
            # If rate limited, return how long (minutes) until you can try again
            ttl = int(red.ttl(key)/60)
            return ttl
        red.set(key, attempts+1, keepttl=True)
        return False
    # Add key to redis to start tracking rates
    red.setex(key, 
        3600, # 1 Hour
        value=1)
    return False
