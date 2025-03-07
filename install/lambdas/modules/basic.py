import sys
import os
import boto3
import botocore
import json
from botocore.exceptions import ClientError

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.check_type import CheckType

class Basic:
    def __init__(self, checks: list) -> None:
        """
        Initialize the Basic checks module
        
        Args:
            checks (list): A list of checks to run
        """
        self.checks = checks
    
    def run_checks(self) -> list:
        """
        Run the module checks and return a list of results
        """
        
        results = []
        for c in self.checks:
            if c['enabled'] == True:
                
                result = {
                    'check': c['name'],
                    'pass': True,
                    'info': ''
                }
                
                match c['name']:
                    case CheckType.MISSING_TAGS.value:
                        missing_tags = self.check_tags(c)
                        if len(missing_tags) > 0:
                            result['pass'] = False
                            result['info'] = missing_tags
                    case CheckType.NO_MFA_ON_ROOT.value:
                        has_mfa = self.has_mfa_on_root()
                        if not has_mfa:
                            result['pass'] = False
                            result['info'] = 'No MFA on Root'
                    case CheckType.NO_PASSWORD_POLICY.value:
                        has_password_policy = self.has_password_policy()
                        if not has_password_policy:
                            result['pass'] = False
                            result['info'] = 'No Password Policy'
                    case CheckType.PUBLIC_BUCKETS.value:
                        public_buckets = self.check_s3_public_buckets()
                        if len(public_buckets) > 0:
                            result['pass'] = False
                            result['info'] = public_buckets
                    case CheckType.NO_BUSINESS_SUPPORT.value:
                        has_premium_supprt = self.has_premuim_support()
                        if not has_premium_supprt:
                            result['pass'] = False
                            result['info'] = 'No premium support found'
                    case CheckType.NO_BUDGET.value:
                        has_budget = self.has_budget()
                        if not has_budget:
                            result['pass'] = False
                            result['info'] = 'No budget found'
                    case CheckType.UNUSED_EIP.value:
                        unused_eips = self.check_unused_eip(c)
                        if len(unused_eips) > 0:
                            result['pass'] = False
                            result['info'] = unused_eips
                            
                results.append(result)
                        
        return results


    def check_tags(self, check_info) -> list:
        """
        Check if tags are set correctly
        """
        
        missing_tags_resources = []
        check_info_config = json.loads(check_info['config'])
        
        try:
            config_client = boto3.client('config')
            rule_name = check_info_config['configRuleName']
            
            response = config_client.get_compliance_details_by_config_rule(
                ConfigRuleName=rule_name,
                ComplianceTypes=['NON_COMPLIANT'],
                Limit=100
            )
            
            non_compliant_resources = self.get_non_compliant_resources(response)
           
            # Handle pagination if there are more results
            while 'NextToken' in response:
                response = config_client.get_compliance_details_by_config_rule(
                    ConfigRuleName=rule_name,
                    ComplianceTypes=['NON_COMPLIANT'],
                    NextToken=response['NextToken'],
                    Limit=100
                )
                
                non_compliant_resources.extend(self.get_non_compliant_resources(response))
            
            missing_tags_resources.extend(non_compliant_resources)
        except Exception as e:
            print(e)
            raise(e)
        
        return missing_tags_resources
        
        
    def get_non_compliant_resources(self, config_response) -> list:
        # Process the non-compliant resources
        non_compliant_resources = []
        
        for evaluation in config_response['EvaluationResults']:
            resource_info = {
                'ResourceId': evaluation['EvaluationResultIdentifier']['EvaluationResultQualifier']['ResourceId'],
                'ResourceType': evaluation['EvaluationResultIdentifier']['EvaluationResultQualifier']['ResourceType'],
                'ComplianceType': evaluation['ComplianceType'],
                'LastResultRecordedTime': evaluation['ResultRecordedTime'].strftime('%Y-%m-%d %H:%M:%S')
            }
            
            non_compliant_resources.append(resource_info)
        
        return non_compliant_resources
        
    
    def has_mfa_on_root(self) -> bool:
        """
        Check if the account has MFA on root
        
        Returns (bool): True if the account has MFA on root and False otherwise
        """
        
        try:
            iam_client = boto3.client('iam')
            account_summary = iam_client.get_account_summary()
            root_mfa_enabled = bool(account_summary['SummaryMap'].get('AccountMFAEnabled', 0))
            
            return root_mfa_enabled
        except Exception as e:
            print(e)
            raise(e)
    
    
    def has_password_policy(self) -> bool:
        """
        Check if the account has password policy
        
        Returns (bool): True if the account has password policy and False otherwise
        """
        
        try:
            iam = boto3.client('iam')
            response = iam.get_account_password_policy()
            
            # If we get here, a password policy exists
            policy = response['PasswordPolicy']
            
            return True
                
        except botocore.exceptions.ClientError as error:
            if error.response['Error']['Code'] == 'NoSuchEntity':
                return False
            else:
                print(error)
                raise(error)
        except Exception as e:
            print(e)
            raise(e)
    
    
    def check_s3_public_buckets(self) -> list:
        """
        Search for S3 public access
        
        Returns (list): A list of S3 buckets with public access. Empty list if there are none
        """
        
        s3_client = boto3.client('s3')
        public_buckets = []
        buckets = []
        
        try:
            buckets = s3_client.list_buckets()['Buckets']
        except Exception as e:
            print(e)
            raise(e)
        
        if len(buckets) > 0:
            for bucket in buckets:
                bucket_name = bucket['Name']
                public_access = False
                public_reason = []
                
                # Check bucket public access block settings
                try:
                    public_access_block = s3_client.get_public_access_block(Bucket=bucket_name)
                    block_config = public_access_block['PublicAccessBlockConfiguration']
                    
                    # If any of these are False, the bucket might allow public access
                    if not block_config.get('BlockPublicAcls', True):
                        public_reason.append("BlockPublicAcls disabled")
                        public_access = True
                    if not block_config.get('BlockPublicPolicy', True):
                        public_reason.append("BlockPublicPolicy disabled")
                        public_access = True
                    if not block_config.get('IgnorePublicAcls', True):
                        public_reason.append("IgnorePublicAcls disabled")
                        public_access = True
                    if not block_config.get('RestrictPublicBuckets', True):
                        public_reason.append("RestrictPublicBuckets disabled")
                        public_access = True
                        
                except ClientError as e:
                    public_access = True
                    if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                        # No public access block configured - potential risk
                        public_reason.append("The bucket might be public. No public access block configuration found")
                    else:
                        public_reason.append(f'The bucket might be public. Getting an error when trying to get the bucket access block configuration. {str(e)}')
                
                
                # Check bucket ACL
                try:
                    acl = s3_client.get_bucket_acl(Bucket=bucket_name)
                    for grant in acl.get('Grants', []):
                        grantee = grant.get('Grantee', {})
                        if grantee.get('URI') == 'http://acs.amazonaws.com/groups/global/AllUsers':
                            public_reason.append(f"Public ACL: {grant.get('Permission')}")
                            public_access = True
                        elif grantee.get('URI') == 'http://acs.amazonaws.com/groups/global/AuthenticatedUsers':
                            public_reason.append(f"ACL grants access to any AWS authenticated user: {grant.get('Permission')}")
                            public_access = True
                except ClientError:
                    public_access = True
                    public_reason.append("The bucket could potentially be public. Could not check ACL")
                    
                
                # Check bucket policy
                try:
                    policy = s3_client.get_bucket_policy(Bucket=bucket_name)
                    policy_str = policy.get('Policy', '')
                    policy_json = json.loads(policy_str)
                    
                    # Simple check for public policy - look for Principal: "*" or Principal: {"AWS": "*"}
                    for statement in policy_json.get('Statement', []):
                        principal = statement.get('Principal', {})
                        effect = statement.get('Effect', '')
                        
                        if effect == 'Allow' and (principal == '*' or principal == {"AWS": "*"} or 
                                                  (isinstance(principal, dict) and principal.get('AWS') == '*')):
                            public_reason.append("Bucket policy allows public access")
                            public_access = True
                            break
                            
                except ClientError as e:
                    if e.response['Error']['Code'] != 'NoSuchBucketPolicy':
                        public_reason.append(f"The bucket could potentially be public. Error checking policy: {str(e)}")
                        public_access = True
                
                if public_access:
                    public_buckets.append({'bucket_name': bucket_name, 'reasons': public_reason})
        
        return public_buckets
    
    
    def has_premuim_support(self) -> bool:
        """
        Check is the account has premium support
        
        Returns (bool): True if the account has premuim support and False otherwise
        """
        support_client = boto3.client('support')
        has_premium_support = True
        
        try:
             response = support_client.describe_severity_levels()
        except Exception as e:
            if "subscription" in str(e).lower() or "not subscribed" in str(e).lower():
                has_premium_support = False
            else:
                print(str(e))
                raise(e)
        
        return has_premium_support


    def has_budget(self) -> bool:
        """
        Check if the account has at least one budget set
        
        Returns (bool): True if the account has at least one budget and False otherwise
        """
        has_budgets = False
        
        try:
            account_id = boto3.client('sts').get_caller_identity().get('Account')
            budget_client = boto3.client('budgets')
            response = budget_client.describe_budgets(
                AccountId=account_id
            )
            
            budgets = response.get('Budgets', [])
            has_budgets = len(budgets) > 0
        except Exception as e:
            print(str(e))
            raise(e)
            
        return has_budgets
    
    
    def check_unused_eip(self, check_info: dict) -> list:
        """
        Check for unused elastic ips
        
        Args:
            check_info (dict): A check information
        
        Returns (list): A list of unused elastic ips. Empty list if there are non
        """
        unused_eips = []
        regions = []
        
        try:
            if 'config' in check_info:
                check_config = json.loads(check_info['config'])
                if 'regions' in check_config:
                    if len(check_config['regions']) == 1 and check_config['regions'][0] == "*":
                        ec2_client = boto3.client('ec2')
                        regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
                    else:
                        regions = check_info['config']['regions']
            
            for region in regions:
                regional_ec2 = boto3.client('ec2', region_name=region)
                addresses = regional_ec2.describe_addresses()['Addresses']
                
                for address in addresses:
                    if 'InstanceId' not in address and 'NetworkInterfaceId' not in address:
                        eip_info = {
                            'region': region,
                            'allocationId': address.get('AllocationId', 'N/A'),
                            'publicIp': address.get('PublicIp', 'N/A'),
                            'tags': address.get('Tags', [])
                        }
                        unused_eips.append(eip_info)
            
        except Exception as e:
            print(f"Error checking region {str(e)}")
            raise(e)
        
        return unused_eips