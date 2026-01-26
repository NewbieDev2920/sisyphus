from datetime import datetime 
from hashlib import sha256

def hash_gen() -> str:
    instant = str(datetime.now()).encode('utf-8')
    return sha256(instant).hexdigest()

