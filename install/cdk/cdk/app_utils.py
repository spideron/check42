class AppUtils:
    def __init__(self, config: dict) -> None:
        """
        Initialize AppUtils
        
        Args:
            config (dict): App configuration
        """
        self.config = config
        self.prefix = config['prefix']


    def get_name_with_prefix(self, name: str, default_format='{}_{}') -> str:
        """
        Get a resource name with a predefined prefix
        
        Args:
            name (str): The resource name
            default_format (str): The string format to apply. Default: {}_{}
        
        Returns: A string with a prefix and a resource name
        """
        return default_format.format(self.prefix, name)
    
    
    def deployment_name(self, lambda_name: str) -> str:
        """
        Get a name of a zip file package
        
        Args:
            lambda_name (str): The name of the Lambda Function
        
        Returns (str): A name of a zip file package
        """
        
        return f'{lambda_name}.zip'
    
    
    def key_replacer(self, resources: list) -> list:
        """
        Replace known keys with vaules
        
        Args:
            resources (list): A list of string to replace the keys
            
        Returns (list): A list of the original strings after replacement
        """
        
        replaced_resources = []
        
        for resource in resources:
            r = resource.replace('***REGION***', self.config['region'])
            r = r.replace('***ACCOUNT_ID***', self.config['account'])
            r = r.replace('***PREFIX***', self.prefix)
            r = r.replace('***SENDER_EMAIL***', self.config['ses']['senderEmail'])
            
            replaced_resources.append(r)
        
        return replaced_resources