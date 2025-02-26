import boto3
import botocore
import json

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
                    case 'MISSING_TAGS':
                        missing_tags = self.check_tags(c)
                        if len(missing_tags) > 0:
                            result['pass'] = False
                            result['info'] = missing_tags
                    case 'NO_MFA_ON_ROOT':
                        has_mfa = self.has_mfa_on_root()
                        if not has_mfa:
                            result['pass'] = False
                            result['info'] = 'No MFA on Root'
                    case 'NO_PASSWORD_POLICY':
                        has_password_policy = self.has_password_policy()
                        if not has_password_policy:
                            result['pass'] = False
                            result['info'] = 'No Password Policy'
                            
                results.append(result)
                        
        return results


    def check_tags(self, check_info):
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
        
        
    def get_non_compliant_resources(self, config_response):
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