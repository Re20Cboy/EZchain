import hashlib

def sha256_hash(val):
    if type(val) == str:
        return hashlib.sha256(val.encode("utf-8")).hexdigest()
    else:
        return hashlib.sha256(val).hexdigest()