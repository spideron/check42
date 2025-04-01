import sys
import os
import boto3
import botocore
import json
import datetime
from datetime import timedelta
from botocore.exceptions import ClientError

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.check_type import CheckType
from lib.settings import Settings

class Basic:
    def __init__(self, checks: list, settings: Settings) -> None:
        """
        Initialize the Basic checks module
        
        Args:
            checks (list): A list of checks to run
        """
        self.checks = checks
        self.settings = settings
    
    def get_all_regions(self) -> list:
        """
        Get a list of all regions
        
        Returns (list): A list of regions
        """
        ec2_client = boto3.client('ec2')
        regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]
        
        return regions
        
        
    def get_region_list(self, check_info: dict) -> list:
        """
        Get a list of regions from a config section
        
        Args:
            check_info (dict): check_info (dict): The check information as stored in the DB
        
        Returns (list): A list of regions
        """
        
        region_response = []
        regions = []
        
        # Use the default regions and override if the regions are explicitly configured
        if 'regions' in self.settings.defaults:
            regions = self.settings.defaults['regions']
        
        if 'config' in check_info:
            config = json.loads(check_info['config'])
            
            if 'regions' in config:
                regions = config['regions']
            
        if len(regions) == 1 and regions[0] == "*":
            region_response = self.get_all_regions()
        else:
            region_response = regions
        
        return region_response
    
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
                            result['info'] = c['title']
                    case CheckType.NO_PASSWORD_POLICY.value:
                        has_password_policy = self.has_password_policy()
                        if not has_password_policy:
                            result['pass'] = False
                            result['info'] = c['title']
                    case CheckType.PUBLIC_BUCKETS.value:
                        public_buckets = self.check_s3_public_buckets()
                        if len(public_buckets) > 0:
                            result['pass'] = False
                            result['info'] = public_buckets
                    case CheckType.NO_BUSINESS_SUPPORT.value:
                        has_premium_supprt = self.has_premuim_support()
                        if not has_premium_supprt:
                            result['pass'] = False
                            result['info'] = c['title']
                    case CheckType.NO_BUDGET.value:
                        has_budget = self.has_budget()
                        if not has_budget:
                            result['pass'] = False
                            result['info'] = c['title']
                    case CheckType.UNUSED_EIP.value:
                        unused_eips = self.check_unused_eip(c)
                        if len(unused_eips) > 0:
                            result['pass'] = False
                            result['info'] = unused_eips
                    case CheckType.UNATTACHED_EBS_VOLUMES.value:
                        unattached_ebs_volumes = self.check_unattached_ebs_volumes(c)
                        if len(unattached_ebs_volumes) > 0:
                            result['pass'] = False
                            result['info'] = unattached_ebs_volumes
                    case CheckType.USING_DEFAULT_VPC.value:
                        default_vpc_resources = self.check_using_default_vpc(c)
                        if len(default_vpc_resources) > 0:
                            result['pass'] = False
                            result['info'] = default_vpc_resources
                    case CheckType.EC2_IN_PUBLIC_SUBNET.value:
                        ec2_in_public_subnets = self.check_ec2_in_public_subnet(c)
                        if len(ec2_in_public_subnets) > 0:
                            result['pass'] = False
                            result['info'] = ec2_in_public_subnets
                    case CheckType.RESOURCES_IN_OTHER_REGIONS.value:        
                        resources = self.check_for_resources_in_other_regions(c)
                        if len(resources) > 0:
                            result['pass'] = False
                            result['info'] = resources
                    case CheckType.RDS_PUBLIC_ACCESS.value:        
                        resources = self.check_for_public_rds(c)
                        if len(resources) > 0:
                            result['pass'] = False
                            result['info'] = resources
                            
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
        regions = self.get_region_list(check_info)
        check_config = json.loads(check_info['config'])
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
        regions = self.get_region_list(check_info)
        
        try:
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
    
    def check_unattached_ebs_volumes(self, check_info: dict) -> list:
        """
        Check for unattached EBS volumes
        
        Args:
            check_info (dict): A check information
        
        Returns (list): A list of unattached EBS volumes. Empty list if there are none
        """
        
        unattached_ebs_volumes = []
        regions = self.get_region_list(check_info)
        
        try:
            for region in regions:
                ec2 = boto3.resource('ec2', region_name=region)
                
                # Filter for available (unattached) volumes
                volumes = ec2.volumes.filter(
                    Filters=[{'Name': 'status', 'Values': ['available']}]
                )
                
                for volume in volumes:
                    volume_info = {
                        'region': region,
                        'volume_id': volume.id,
                        'size': f"{volume.size} GB"
                    }
                    
                    unattached_ebs_volumes.append(volume_info)
            
        except Exception as e:
            print(f"Error checking region {str(e)}")
            raise(e)
        
        return unattached_ebs_volumes
        
    
    def check_using_default_vpc(self, check_info: dict) -> list:
        """
        Check for default VPC usage
        
        Args:
            check_info (dict): A check information
        
        Returns (list): A list of resources in a default vpc. Empty list if there's no default vpc
        """
        
        default_vpc_resources = []
        regions = self.get_region_list(check_info)
        
        try:
            for region in regions:
                ec2 = boto3.client('ec2', region_name=region)
                response = ec2.describe_vpcs()
                
                default_vpc = None
                for vpc in response['Vpcs']:
                    if vpc.get('IsDefault', False):
                        default_vpc = vpc
                        break
                
                if default_vpc:
                    vpc_id = default_vpc['VpcId']
                    
                    # Collect EC2 Instances details
                    instances = ec2.describe_instances(
                        Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
                    )
                    for reservation in instances['Reservations']:
                        for instance in reservation['Instances']:
                            instance_id = instance['InstanceId']
                            instance_name = instance.get('KeyName', '')
                            
                            default_vpc_resources.append({
                                'region': region,
                                'resource': f'EC2 ({instance_name} - {instance_id})'
                            })
                    
                    # Collect security groups details
                    security_groups = ec2.describe_security_groups(
                        Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
                    )
                    for sg in security_groups['SecurityGroups']:
                        group_name = sg['GroupName']
                        group_id = sg['GroupId']
                        
                        default_vpc_resources.append({
                                'region': region,
                                'resource': f'Security Group ({group_name} - {group_id})'
                            })
                    
                    # Collect subnets details
                    subnets = ec2.describe_subnets(
                        Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
                    )
                    for subnet in subnets['Subnets']:
                        subnet_id = subnet['SubnetId']
                        cidr_block = subnet['CidrBlock']
                        
                        default_vpc_resources.append({
                                'region': region,
                                'resource': f'Subnet ({cidr_block} - {subnet_id})'
                            })
                    
                    # Collect network interfaces details
                    network_interfaces = ec2.describe_network_interfaces(
                        Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
                    )
                    for ni in network_interfaces['NetworkInterfaces']:
                        network_interface_id = ni['NetworkInterfaceId']
                        
                        default_vpc_resources.append({
                                'region': region,
                                'resource': f'Network Interface ({network_interface_id})'
                            })
                    
                    # Collect elastic load balancers details
                    elb = boto3.client('elbv2')
                    load_balancers = elb.describe_load_balancers()
                    for lb in load_balancers['LoadBalancers']:
                        if lb.get('VpcId') == vpc_id:
                            load_balancer_name = lb['LoadBalancerName']
                            load_balancer_type = lb['Type']
                            
                            default_vpc_resources.append({
                                'region': region,
                                'resource': f'Load Balancer ({load_balancer_name} - {load_balancer_type})'
                            })
                            
        except Exception as e:
            print(f"Error checking region {str(e)}")
            raise(e)
        
        return default_vpc_resources
    
    
    def check_ec2_in_public_subnet(self, check_info: dict) -> list:
        """
        Check for EC2 instances running in public subnets
        
        Args:
            check_info (dict): A check information
        
        Returns (list): A list of EC2 instances running in a public subnet. Empty list if there are non
        """
        instances_in_public_subnets = []
        regions = self.get_region_list(check_info)
        
        try:
            for region in regions:
                ec2_client = boto3.client('ec2', region_name=region)
                instances_response = ec2_client.describe_instances()
                subnets_response = ec2_client.describe_subnets()
                
                # Create a dictionary of subnet IDs to their public/private status
                public_subnets = {}
                for subnet in subnets_response['Subnets']:
                    subnet_id = subnet['SubnetId']
                    
                    # A subnet is public if it has a route to an Internet Gateway
                    is_public = False
                    
                    # Get the route table associated with this subnet
                    route_tables = ec2_client.describe_route_tables(
                        Filters=[{'Name': 'association.subnet-id', 'Values': [subnet_id]}]
                    )
                    
                    # If no explicit association, check the main route table for the VPC
                    if not route_tables['RouteTables']:
                        vpc_id = subnet['VpcId']
                        route_tables = ec2_client.describe_route_tables(
                            Filters=[
                                {'Name': 'vpc-id', 'Values': [vpc_id]},
                                {'Name': 'association.main', 'Values': ['true']}
                            ]
                        )
                    
                    # Check routes for an internet gateway
                    for rt in route_tables.get('RouteTables', []):
                        for route in rt.get('Routes', []):
                            if route.get('GatewayId', '').startswith('igw-'):
                                is_public = True
                                break
                    
                    public_subnets[subnet_id] = is_public
                    
                # Find instances in public subnets
                for reservation in instances_response['Reservations']:
                    for instance in reservation['Instances']:
                        instance_id = instance['InstanceId']
                        subnet_id = instance['SubnetId']
                        
                        if public_subnets.get(subnet_id, False):
                            instance_id = instance['InstanceId']
                            instance_name = instance.get('KeyName', 'N/A')
                            
                            instances_in_public_subnets.append({
                                'region': region,
                                'instance': f'{instance_name} - {instance_id}'
                            })
        
        except Exception as e:
            print(f"Error checking region {str(e)}")
            raise(e)
        
        
        return instances_in_public_subnets
    
    
    def check_for_resources_in_other_regions(self, check_info: dict) -> list:
        """
        Check if there are resources in other regions than the intended ones
        
        Args:
            check_info (dict): A check information
        
        Returns (list): A list of resources running in unintended regions. Empty list if there are non
        """
        resources_in_other_regions = []
        
        all_regions = self.get_all_regions()
        intended_regions = self.get_region_list(check_info)
        intended_regions.extend(['global', 'noregion'])
        
        # Get today's date and first day of the month
        end_date = datetime.datetime.now().date()
        start_date = end_date.replace(day=1)
        
        # Format dates as strings (YYYY-MM-DD)
        start_date_str = start_date.strftime('%Y-%m-%d')
        
        # The end date can't be the same as the start date, in case of the 1st of the month.
        if end_date.strftime('%d') == '01':
            end_date_str = end_date.strftime('%Y-%m-02')
        else:
            end_date_str = end_date.strftime('%Y-%m-%d')
                
        try:
            client = boto3.client('ce')
            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date_str,
                    'End': end_date_str
                },
                Granularity='MONTHLY',
                Metrics=['BlendedCost', 'UsageQuantity'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    },
                    {
                        'Type': 'DIMENSION',
                        'Key': 'REGION'
                    }
                ]
            )   
        
            for group in response['ResultsByTime'][0]['Groups']:
                service_region = group['Keys']
                service = service_region[0]
                region = service_region[1] if service_region[1] != '' else 'global'
                
                if region.lower() not in intended_regions:
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    
                    if cost > 0:
                        resources_in_other_regions.append({
                            'region': region,
                            'service': service,
                            'cost': f'${round(cost, 2)}'
                        })
        
        except Exception as e:
            print(f"Error checking region {str(e)}")
            raise(e)
        
        return resources_in_other_regions
    
    
    def check_for_public_rds(self, check_info: dict) -> list:
        """
        Check if there are any RDS instances set for public access
        
        Args:
            check_info (dict): A check information
        
        Returns (list): A list of RDS instances with public access. Empty list if there are non
        """
        
        public_rds_instances = []
        regions = self.get_region_list(check_info)
        
        try:
            for region in regions:
                rds_client = boto3.client('rds', region_name=region)
                response = rds_client.describe_db_instances()
                
                for instance in response.get('DBInstances', []):
                    if instance.get('PubliclyAccessible'):
                        rds_id = instance.get('DBInstanceIdentifier')
                        rds_engine = instance.get('Engine')
                        
                        public_rds_instances.append({
                            'region': region,
                            'resource': f'RDS Id: {rds_id}. Engine: {rds_engine}'
                        })
        
        except Exception as e:
            print(f"Error checking region {str(e)}")
            raise(e)
        
        return public_rds_instances