# AWS Best Practices - basic checks

A list of checks in the basic module.


## Configuration

The configuration of the checks can be found in the [config.json](../../install/config.json)  
Each config section has the following properties:  
- **name (REQUIRED)**: The key name of the check. Corresponds to the [CheckType Enum](../../install/lambdas/lib/check_type.py)
- **emailTemplates**:
    - baseFileName: The file name (without extention) in the [lambdas/email_templates folder](../../install/lambdas/email_templates)
    - itemFileName: The file name for sub item for the template (if there's one) in the same folder as the baseFileName
- **config**: An optional configuration section to be used by the checker


## Checks

### MFA on Root Account

**Purpose**: Check if multi-factor authentication (MFA) is set on the root account. The checker will notify the 
subscriber if no MFA was found on the root account. 
https://docs.aws.amazon.com/IAM/latest/UserGuide/enable-mfa-for-root.html  
**Implemented in version**: 1.0  
**Config**:
```JavaScript
{
    "name": "NO_MFA_ON_ROOT",
    "emailTemplates":{
        "baseFileName": "basic_no_mfa_on_root"
    }
}
```


### Password Policy

**Purpose**: Check if the account has a password policy set. The checker will notify the subscriber if no password 
policy was found on the account. 
https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_passwords_account-policy.html  
**Implemented in version**: 1.0  
**Config**:
```JavaScript
{
    "name": "NO_PASSWORD_POLICY",
    "emailTemplates":{
        "baseFileName": "basic_no_password_policy"
    }
}
```


### Public S3 Buckets

**Purpose**: Check if there are any S3 buckets with public access to the internet. If any bucket has public access, 
the subscriber will be notified about them and the reason it found to make them public. 
https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html  
**Implemented in version**: 1.0  
**Config**:
```JavaScript
{
    "name": "PUBLIC_BUCKETS",
    "emailTemplates":{
        "baseFileName": "basic_s3_public_access",
        "itemFileName": "basic_s3_public_access_item"
    }
}
```


### Missing Tags on Resources

**Purpose**: Check if there are resources in the provided regions that are missing the pre-defined tags.  
**Implemented in version**: 1.0  
**Config**:
```JavaScript
{
    "name": "MISSING_TAGS",
    "emailTemplates":{
        "baseFileName": "basic_missing_tags",
        "itemFileName": "basic_missing_tags_item"
    },
    "config": {
        "regions": ["us-west-2"],
        "configRuleName": "required_tags_rule",
        "requiredTags": ["environment", "project"]
    }
}
```


### Business Support

**Purpose**: Check if the account has at least a business support level subscription.  
**Implemented in version**: 1.0  
**Config**:
```JavaScript
{
    "name": "NO_BUSINESS_SUPPORT",
    "emailTemplates":{
        "baseFileName": "basic_no_premium_support"
    }
}
```


### Budget

**Purpose**: Check if the account has at least one budget set up.  
**Implemented in version**: 1.0  
**Config**:
```JavaScript
{
    "name": "NO_BUDGET",
    "emailTemplates":{
        "baseFileName": "basic_no_budget"
    }
}
```