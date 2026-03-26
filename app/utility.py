from passlib.context import CryptContext


pwd_context = CryptContext(schemes=['argon2'], deprecated='auto') # this tells crpto class how to or which algo to use for hashing



# hash pass 
def hashPassword(password: str)-> str :
   """ this takes password and return hashed password"""
   return pwd_context.hash(password)

# verfify 
def verifyPassword(plain_password: str, hashed_password: str)-> bool:
   """ takes plain and hashed password"""
   return pwd_context.verify(plain_password,hashed_password)


