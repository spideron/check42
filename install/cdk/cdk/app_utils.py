class AppUtils:
    def __init__(self, config: dict) -> None:
        """
        Initialize AppUtils
        
        Args:
            config (dict): App configuration
        """
        self.config = config


    def get_name_with_prefix(self, name: str, default_format='{}_{}') -> str:
        """
        Get a resource name with a predefined prefix
        
        Args:
            name (str): The resource name
            default_format (str): The string format to apply. Default: {}_{}
        
        Returns: A string with a prefix and a resource name
        """
        return default_format.format(self.config['prefix'], name)
    
    
    def deployment_name(self, lambda_name: str) -> str:
        """
        Get a name of a zip file package
        
        Args:
            lambda_name (str): The name of the Lambda Function
        
        Returns (str): A name of a zip file package
        """
        
        return '{}.zip'.format(lambda_name)