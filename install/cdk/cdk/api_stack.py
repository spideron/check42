from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration
)
from constructs import Construct
from cdk.app_utils import AppUtils
from cdk.lambda_utils import Lambdatils

class ApiStack(Stack):
    def __init__(self, scope: Construct, id: str, config: dict, lambda_functions: dict, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        self.app_utils = AppUtils(config)
        self.lambda_utils = Lambdatils(config['prefix'])
        
        api_config = config['api']
        authorizer_function = self.create_lambda_authorizer(api_config)
        authorizer_cache_ttl = Duration.seconds(api_config['authorizer']['ttl'])
        
        api_name = self.app_utils.get_name_with_prefix(api_config['name'])
        api_description = api_config['description']
        

        # Create the API Gateway
        self.api = apigw.RestApi(
            self,
            api_name,
            rest_api_name=api_name,
            description=api_description,
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key", 
                      "X-Amz-Security-Token", "X-Requested-With", "X-Amz-Invocation-Type"],
                allow_credentials=True
            )
        )
        
        for resource_name, resource_settings in api_config['resources'].items():
            lambda_function = lambda_functions[resource_settings['lambda_function']]
            resource = self.api.root.add_resource(resource_name)
            integration = apigw.LambdaIntegration(lambda_function)
            
            require_auth = resource_settings.get('authorizer', False)
            
            if require_auth:
                authorizer = apigw.TokenAuthorizer(
                    self,
                    f"{resource_name}-authorizer",
                    handler=authorizer_function,
                    results_cache_ttl=authorizer_cache_ttl,
                    identity_source='method.request.header.Authorization'
                )
            
            for method_type in resource_settings['methods']:
                 # Add method with authorizer if required
                if require_auth:
                    resource.add_method(
                        method_type, 
                        integration,
                        authorizer=authorizer,
                        authorization_type=apigw.AuthorizationType.CUSTOM
                    )
                else:
                    resource.add_method(method_type, integration)
     
     
    def create_lambda_authorizer(self, api_config: dict) -> _lambda.Function:
        """
        Create a Lambda function to act as the API Gateway Authorizer
        
        Args:
            api_config (dict): The API config section
        
        Returns (_lambda.Function): The authorizer Lambda Function
        """
        
        authorizer_config = api_config['authorizer']
        function_file_location = authorizer_config['fileLocation']
        function_name = self.app_utils.get_name_with_prefix(authorizer_config['functionName'])
        function_policies = []
        include_folders = []
        function_policies = authorizer_config['iamPolicies']
        file_name = self.app_utils.deployment_name(function_name)
        
        self.lambda_utils.create_deployment_package(file_name, function_file_location, include_folders)
        
        role_name = self.lambda_utils.role_name(function_name)
        lambda_role = iam.Role(
            self,
            role_name,
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        for function_policy in function_policies:
            resources = self.app_utils.key_replacer(function_policy['resources'])
            iam_policy = iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        effect=iam.Effect.ALLOW,
                        actions=function_policy['actions'],
                        resources=resources
                    )
                ]
            )
        
            policy = iam.ManagedPolicy(
                self,
                f'{role_name}_{function_policy["name"]}',
                document=iam_policy
            )
            
            lambda_role.add_managed_policy(policy)
        
        lambda_function = _lambda.Function(
            self, 
            function_name,
            function_name = function_name,
            runtime=_lambda.Runtime.PYTHON_3_10,
            handler=f'{function_name}.handler',
            code=_lambda.Code.from_asset(file_name),
            role=lambda_role
        )
        
        return lambda_function
