import json

class Settings:
    def __init__(self) -> None:
        self.settings_id = None
        self.schedule = None
        self.sender = None
        self.subscriber = None
        self.defaults = {}
    
    @staticmethod
    def from_query(query_object: dict):
        """
        Get a settings object from database results
        
        Args:
            settings (dict): A database query response with the settings
            
        Returns (Settings): A Settings object
        """
        
        settings = Settings()

        if 'id' in query_object:
            settings.settings_id = query_object['id']
        
        if 'subscriber' in query_object:
            settings.subscriber = query_object['subscriber']

        if 'sender' in query_object:
            settings.sender = query_object['sender']
            
        if 'schedule' in query_object:
            settings.schedule = query_object['schedule']
        
        if 'defaults' in query_object:
            settings.defaults = json.loads(query_object['defaults'])
        
        return settings