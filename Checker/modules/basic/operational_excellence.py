import boto3
import botocore

def missing_tags(regions):
    
    non_compliance_list = []
    
    if len(regions) > 0:
        try:
            for region in regions:
                config_client = boto3.client('config', region_name=region)
                compliance_details = config_client.get_compliance_details_by_config_rule(
                    ConfigRuleName='required-tags',
                    ComplianceTypes=['NON_COMPLIANT'])
                    
                evaluation_results = compliance_details['EvaluationResults']
                
                while "NextToken" in compliance_details:
                    compliance_details = config_client.get_compliance_details_by_config_rule(
                    ConfigRuleName='required-tags',
                    ComplianceTypes=['NON_COMPLIANT'],
                    NextToken=compliance_details["NextToken"])
                    
                    evaluation_results.extend(compliance_details['EvaluationResults'])
                
                
                if len(evaluation_results) > 0:
                    for result in evaluation_results:
                        resource_type = result['EvaluationResultIdentifier']['EvaluationResultQualifier']['ResourceType']
                        resource_id = result['EvaluationResultIdentifier']['EvaluationResultQualifier']['ResourceId']
                        non_compliance_list.append({"region": region, "type": resource_type, "id": resource_id})
                    
        except botocore.exceptions.ClientError as e:
            print(f"Error checking config rules - reuired tags: {e}")
            
    return non_compliance_list

def has_business_support():
    support_client = boto3.client('support')
    has_support = True
    
    try:
        support_client.describe_severity_levels()
    
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "SubscriptionRequiredException":
            has_support = False
        else:
            print(f"Error checking for business support: {e}")
    return has_support
