import boto3


class IAMHandler:
    def __init__(self, region, account_id):
        """
        Initialize IAM handler
        
        Args:
            region (String): AWS region name
            account_id (String): 12 digits AWS account id
        """
        
        self.region = region
        self.account_id = account_id
        self.iam_client = boto3.client('iam')
        
    def create_iam_policy(self, policy_name, policy_document, description='') -> str:
        """
        Create an IAM policy
        
        Args:
            policy_name (String): The IAM policy name
            policy_document (string): A string of json document descibing a policy
            description (string): A description for the policy. Default ''
            
        Returns:
            str: The newly created policy arn
        """
        try:
            response = self.iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=policy_document,
                Description=description
            )
            policy_arn = response['Policy']['Arn']
            print('Created IAM policy: {}'.format(policy_arn))
            return policy_arn
        except Exception as e:
            print(e)
            raise
        
    def create_iam_role_and_attach_role(self, role_name, trusted_relationship_document, policy_arn, description='') -> str:
        """
        Create an IAM role and attach a policy to it
        
        Args:
            role_name (String): The IAM role name
            trusted_relationship_document (String): An IAM trusted relationship document
            policy_arn (String): An IAM policy arn to attach to the role
            description (String): A description for the role. Default ''
        """
        try:
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=trusted_relationship_document,
                Description=description
            )
            role_arn = response['Role']['Arn']
            print('Created IAM role: {}'.format(role_arn))
    
            # Attach the policy to the role
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            print('Attached policy {} to role {}'.format(policy_arn, role_arn))
            return role_arn
        except Exception as e:
            print(e)
            raise
        
    def attach_lambda_basic_policy(self, role_name):
        """
        Attach Lambda basic execution policy to a role 
        
        Args:
            role_name (String): The IAM role name
        """
        self.iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )
        print('Attached Lambda basic execution role policy to role {}'.format(role_name))