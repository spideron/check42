import re
import hashlib

class Utils:
    def __init__(self) -> None:
        """
        Utils class constructor
        """
    
    def is_valid_uuid(self, uuid_string: str) -> bool:
        """
        Check if the provided inout is a valid uuid string
        
        Args:
            uuid_string (str): The uuid string to validate
        
        Returns (bool): True if the input is a valid uuid4 string and false otherwise
        """
        regex = re.compile('^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z', re.I)
        match = regex.match(uuid_string)
        return bool(match)
    
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password string
        
        Args:
            password (str): The password string to hash
            
        Returns (str): Hashed password value
        """
        hash_object = hashlib.sha256()
        hash_object.update(password.encode('utf-8'))
        return hash_object.hexdigest()