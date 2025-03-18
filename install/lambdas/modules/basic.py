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
    
    def get_region_list(self, regions: list) -> list:
        """
        Get a list of regions from a config section
        
        Args:
            regions (list): A list of region names or ['*'] for all available regions
        
        Returns (list): A list of regions
        """
        
        region_list = []
        
        if len(regions) == 1 and regions[0] == "*":
            ec2_client = boto3.client('ec2')
            region_list = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
        else:
            region_list = regions
        
        return region_list
    
    def has_required_tags(self, tags, required_tags):
        """
        Check if all required tags are present in the tags list.
        
        Args:
            tags (list): List of tag dictionaries with 'Key' and 'Value'
            required_tags (list): List of required tag keys
            
        Returns:
            bool: True if all required tags are present, False otherwise
        """
        # Convert list of tag dictionaries to a set of lowercase tag keys
        tag_keys = {tag['Key'].lower() for tag in tags}
        
        # Check if all required tags are present
        for tag in required_tags:
            if tag.lower() not in tag_keys:
                return False
    
        return True
    
    
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


    def check_tags(self, check_info: dict) -> list:
        """
        Check if the rquired tags are set for the services set in the congfig
        
        Args:
            check_info (dict): The check information as stored in the DB
            
        Returns (list): A list of resources with missing tags
        """
        
        non_compliant_resources = {}
        check_config = json.loads(check_info['config'])
        regions = self.get_region_list(check_config['regions'])
        required_resources = check_config['resources']
        required_tags = check_config['requiredTags']
        
        try:
            for region in regions:
                tagging_client = boto3.client('resourcegroupstaggingapi', region_name=region)
                
                paginator = tagging_client.get_paginator('get_resources')
                for page in paginator.paginate():
                    for resource in page['ResourceTagMappingList']:
                        resource_arn = resource['ResourceARN']
                        tags = resource['Tags']
                        
                        # Extract service name from ARN
                        service_name = resource_arn.split(':')[2]
                        
                        if service_name not in non_compliant_resources:
                            non_compliant_resources[service_name] = []
                        
                        # Check if required tags are present
                        if service_name in required_resources and not self.has_required_tags(tags, required_tags):
                            non_compliant_resources[service_name].append({
                                'resource_arn': resource_arn,
                                'resource_type': service_name
                            })
                                
        except Exception as e:
            print(e)
            raise(e)
        
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
        
        Returns (bool): True if the account has premium support and False otherwise
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
        
        Returns (list): A list of unused elastic ips. Empty list if there are none
        """
        unused_eips = []
        regions = []
        
        try:
            if 'config' in check_info:
                check_config = json.loads(check_info['config'])
                if 'regions' in check_config:
                    regions = self.get_region_list(check_config['regions'])
            
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