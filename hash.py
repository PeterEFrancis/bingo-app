import hashlib


def SHA1(string):
    return hashlib.sha1(string.encode()).hexdigest()

print(SHA1('a7he9J08ghw9hr'))
print(SHA1('b9f7Jge5jr6jSRj'))
print(SHA1('TorChamele0n123Kg63KSRjsr5js'))
