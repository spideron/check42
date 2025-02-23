import boto3
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