import bcrypt
def hash_password(password):
    salt = bcrypt.gensalt(10)
    hashed_password = bcrypt.hashpw(password.encode(), salt)
    return hashed_password

def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode(), hashed_password)

