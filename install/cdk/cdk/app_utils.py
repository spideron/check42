class AppUtils:
    def __init__(self, config: dict, default_format='{}_{}') -> None:
        """
        Initialize AppUtils
        
        Args:
            config (dict): App configuration
            default_format (str): The format to use. Default: {}_{}
        """
        self.config = config
        self.default_format = default_format

    def get_name_with_prefix(self, name):
        return self.default_format.format(self.config['prefix'], name)