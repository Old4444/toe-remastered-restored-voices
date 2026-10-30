import hashlib, sys
print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())
