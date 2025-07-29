
import random
import string

class TokenGenerator:
    @staticmethod
    def generate_referral_code(length: int = 8) -> str:
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choice(characters) for _ in range(length))
    
    @staticmethod
    def generate_secure_token(length: int = 16) -> str:
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))
