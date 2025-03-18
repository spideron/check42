import sys
import os
import boto3
import botocore
from botocore.exceptions import ClientError

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.resource_type import ResourceType

class TagChecker:
    def __init__(self, required_tags: list) -> None:
        """
        Initialize the TagChecker checks class
        
        Args:
            required_tags (list): A list of required tags
        """
        self.required_tags = required_tags
    
    def has_required_tags(self, tags: list) -> bool:
        """
        Check if the provided list has all the required tags
        
        Args: 
            tags (list): A list of tag keys to check against the required tags
        
        Returns (bool): True if all the required tags found and False otherwise
        """
        
        has_all_required_tags = True
        
        for rt in self.required_tags:
            if rt not in tags:
                has_all_required_tags = False
                break
        
        return has_all_required_tags
    
    def get_acm_missing_tags(self, region: str) -> list:
        """
        Get a list of ACM resources missing the required tags
        
        Args:
            region (str): An AWS region to check the resources
            
        Returns (list): A list of all ACM resources in a region missing the required tags or an empty list if there are
                        none
        """
        
        missing_tags_resources = []
        
        try:
            acm_client = boto3.client('acm', region_name=region)
            response = acm_client.list_certificates()
            certificates = response['CertificateSummaryList']
            
            for cert in certificates:
                cert_arn = cert['CertificateArn']
                cert_tags_response = acm_client.list_tags_for_certificate(CertificateArn=cert_arn)
                tags = cert_tags_response.get('Tags', [])
                tag_keys = [tag['Key'].lower() for tag in tags]
                
                if not self.has_required_tags(tag_keys):
                    missing_tags_resources.append({
                        'resource_type': ResourceType.ACM_CERTIFICATE.value,
                        'resource_arn': cert_arn
                    })
                
            
        except Exception as e:
            print(e)
            raise(e)
            
        
        return missing_tags_resources