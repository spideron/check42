from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
    aws_lambda as _lambda,
)
from constructs import Construct
from cdk.app_utils import AppUtils

class ApiStack(Stack):
    def __init__(self, scope: Construct, id: str, config: dict, lambda_functions: dict, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        app_utils = AppUtils(config)
        api_name = app_utils.get_name_with_prefix(config['api']['name'])
        api_description = config['api']['description']

        # Create the API Gateway
        self.api = apigw.RestApi(
            self,
            api_name,
            rest_api_name=api_name,
            description=api_description,
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            )
        )

        api_config = config['api']
        for resource_name, resource_settings in api_config['resources'].items():
            lambda_function = lambda_functions[resource_settings['lambda_function']]
            resource = self.api.root.add_resource(resource_name)
            integration = apigw.LambdaIntegration(lambda_function)
            
            for method_type in resource_settings['methods']:
                resource.add_method(method_type, integration)
        