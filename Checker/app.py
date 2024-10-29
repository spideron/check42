import json
from modules.basic.security import *
from modules.basic.operational_excellence import *

MESSAGE_NOT_MFA_ON_ROOT = "No MFA found on root account. Please set an MFA on the root account. https://docs.aws.amazon.com/IAM/latest/UserGuide/enable-mfa-for-root.html"
MESSAGE_NO_PASSWORD_POLICY = "The account doens't have password policy. Please set a password policy. https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_passwords_account-policy.html"
MESSAGE_PUBLIC_BUCKETS = "The following S3 buckets has some public access settings. Please review and remove public access as necessary. Buckets: $buckets"
MESSAGE_MISSING_TAGS = "One or more resources are missing tags. Please add tags to AWS resources. https://docs.aws.amazon.com/tag-editor/latest/userguide/tagging.html. TODO: add formated version of resources"
MESSAGE_NO_BUSINESS_SUPPORT = "Business support is not enables on this account. Please consider upgarding to business support. https://aws.amazon.com/premiumsupport/plans/"


config_file = open('app_config.json')
app_config = json.load(config_file)

def lambda_handler(event, context):
    findings = []
    
    if app_config["modules"]["basic"]["enable"]:
        if app_config["modules"]["basic"]["checks"]["hasMfaOnRoot"] and not has_root_mfa():
            findings.append(MESSAGE_NOT_MFA_ON_ROOT)
    
        if app_config["modules"]["basic"]["checks"]["hasPasswordPolicy"] and not has_password_policy():
            findings.append(MESSAGE_NO_PASSWORD_POLICY)
        
        
        if app_config["modules"]["basic"]["checks"]["bucketsWithPublicAccess"]:
            buckets = buckets_with_public_access();
            if len(buckets) > 0:
                findings.append(MESSAGE_PUBLIC_BUCKETS.format(buckets=buckets))
    
    
        if app_config["modules"]["basic"]["checks"]["missingTags"]:
            non_compliance_rules = missing_tags(app_config["regions"])
            if len(non_compliance_rules) > 0:
                findings.append(MESSAGE_MISSING_TAGS)
                
        if app_config["modules"]["basic"]["checks"]["hasBusinessSupport"] and not has_business_support():
            findings.append(MESSAGE_NO_BUSINESS_SUPPORT)

    return findings
