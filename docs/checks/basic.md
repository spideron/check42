# Check42 - basic checks

A list of checks in the basic module.


## Creating or updating a check

Each check has a section in the [config.json file](../../install/config.json) which will be stored in the database 
during the installation. Each check required the `name`, `title`, and `description` properties. There are also 2 
optional properties, `emailTemplates` which include email message construction details and `config` for adding more 
details to be used by the checker.

When creating a new check, add a new section to the [config.json file](../../install/config.json) with the necessary 
information for the check. If needed, the default email temaplates can be overriden. Check the 
[templates doc](../temaplates.md) for more information.

The same `name` value used in the config file need to be reflected in the 
[check_type.py](../../install/lambdas/lib/check_type.py) file. For example, if the name of the new check is 
`MY_CHECK`, the same need to be added to the enum in the [check_type.py](../../install/lambdas/lib/check_type.py) file. 
as `MY_CHECK = 'MY_CHECK'`.

In the [basic module](../../install/lambdas/modules/basic.py) add a code that runs the check and add the type of it to 
the switch case in the `run_checks` method.

To log the results in the databse, add the same type to the [logger](../../install/lambdas/lib/logger.py) switch case 
under the `log_checks` method.

To create an email section for the check, either use the default behavior or override is as described in the 
[templates doc](../temaplates.md). To override the default behavior, create a new method in the 
[mailer.py](../../install/lambdas/lib/mailer.py) file. Add the new check type to the switch case under the 
`send_message_from_checks` method and reference either one of the default behavior methods or the custom on created 
for the new check.


## Checks

### No MFA on Root

**Purpose**: Check if multi-factor authentication (MFA) is set on the root account. The checker will notify the 
subscriber if no MFA was found on the root account. 
https://docs.aws.amazon.com/IAM/latest/UserGuide/enable-mfa-for-root.html  
**Implemented in version**: 1.0  
**Config**:
```JavaScript
{
    "name": "NO_MFA_ON_ROOT",
    "title": "No MFA on Root",
    "description": "Check if multi-factor authentication (MFA) was set on the root account. As a security best practice, enable MFA for AWS account access, especially for long-term credentials such as the account root user and IAM users."
}
```


### Password policy is not configured

**Purpose**: Check if the account has a password policy set. The checker will notify the subscriber if no password 
policy was found on the account. 
https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_passwords_account-policy.html  
**Implemented in version**: 1.0  
**Config**:
```JavaScript
{
    "name": "NO_PASSWORD_POLICY",
    "title": "Password policy is not configured",
    "description": "Check if a password policy was set for the account. Require that passwords adhere to a strong password policy to help prevent discovery through brute force or social engineering."
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
    "title": "Public S3 Buckets",
    "description": "Check if any of the S3 buckets on the account are set for a public access. It is recommended to keep private access to S3 buckets unless it's necessary",
    "emailTemplates": {
        "itemFileName": "basic_s3_public_access_item"
    }
}
```


### Missing Tags

**Purpose**: Check if there are resources in the provided regions that are missing the pre-defined tags.  
**Implemented in version**: 1.0  
**Config**:
```JavaScript
    "name": "MISSING_TAGS",
    "title": "Missing Tags",
    "description": "Check if the configured resources are set with the required tags. It is recommended to tag resources to help manage workloads and costs",
    "emailTemplates": {
        "itemFileName": "basic_missing_tags_item"
    },
    "config": {
        "requiredTags": ["environment", "project"],
        "resources": [
            "ec2",
            "acm",
            "s3",
            "rds",
            "lambda",
            "dynamodb",
            "cloudwatch",
            "elasticfilesystem",
            "sagemaker",
            "redshift"
        ]
    }
```


### No Premium Support

**Purpose**: Check if the account has at least a business support level subscription.  
**Implemented in version**: 1.0  
**Config**:
```JavaScript
{
    "name": "NO_PREMIUM_SUPPORT",
    "title": "No Premium Support",
    "description": "Check if the account is enrolled in premium support (business, enterprise, or enterprise on-ramp). It is recommended to enroll in premium support for any account with workloads in production"
}
```


### No Budget Set

**Purpose**: Check if the account has at least one budget set up.  
**Implemented in version**: 1.0  
**Config**:
```JavaScript
{
    "name": "NO_BUDGET",
    "title": "No Budget Set",
    "description": "Check if there's at least one budget set on the account. It is recommended to have a budget set in order o monitor and control costs"
}
```


### Unused Elastic IPs

**Purpose**: Check if there are unused Elastic IPs (EIPs).  
**Implemented in version**: 1.0  
**Config**:
```JavaScript
{
    "name": "UNUSED_EIP",
    "title": "Unused Elastic IPs",
    "description": "Check if there are unused Elastic IPs (EIPs). It is recommended to release any unused EIPs",
    "emailTemplates": {
        "itemFileName": "basic_unused_eip_item"
    }
}
```


### Unattached EBS Volumes

**Purpose**: Check if there are EBS volumes not attached to an instance.  
**Implemented in version**: 1.0  
**Config**:
```JavaScript
{
    "name": "UNATTACHED_EBS_VOLUMES",
    "title": "Unattached EBS Volumes",
    "description": "Check if there are EBS volumes not attached to an instance. It is recommended to delete EBS volumes if they have no use anymore",
    "emailTemplates": {
        "itemFileName": "basic_unattached_ebs_volume_item"
    }
}
```


### Default VPC Is In Use

**Purpose**: Check if the default VPC exists and if there are any resources in it.  
**Implemented in version**: 1.0  
**Config**:
```JavaScript
{
    "name": "USING_DEFAULT_VPC",
    "title": "Default VPC Is In Use",
    "description": "Check if the default VPC exists and if there are any resources in it. It is recommended to create a custom VPC and control the network configuration"
}
```


### EC2 Running In Public Subnet

**Purpose**: Check if EC2 instances are running in a public subnet.  
**Implemented in version**: 1.0  
**Config**:
```JavaScript
{
    "name": "EC2_IN_PUBLIC_SUBNET",
    "title": "EC2 Running In Public Subnet",
    "description": "Check if EC2 instances are running in a public subnet. It is recommended to run resources such as EC2 in private subnet when possible"
}
```


### There are resources running in unintended regions

**Purpose**: Check if there are resources in other regions than the intended ones.  
**Implemented in version**: 1.0  
**Config**:
```JavaScript
{
    "name": "RESOURCES_IN_OTHER_REGIONS",
    "title": "There are resources running in unintended regions",
    "description": "Check if there are resources in other regions than the intended ones",
    "emailTemplates": {
        "itemFileName": "basic_resources_in_other_regions_item"
    },
    "config":{
        "regions": ["us-west-2", "us-east-1"]
    }
}
```


### RDS instance is set for public access

**Purpose**: Check if RDS instance(s) are set for public access.  
**Implemented in version**: 1.0  
**Config**:
```JavaScript
{
    "name": "RDS_PUBLIC_ACCESS",
    "title": "RDS instance is set for public access",
    "description": "Check if RDS instance(s) are set for public access. It is recommended to keep RDS instances with private access when possible"
}
```


### RDS Running In Public Subnet

**Purpose**: Check if RDS instances are running in a public subnet.  
**Implemented in version**: 1.0  
**Config**:
```JavaScript
{
    "name": "RDS_IN_PUBLIC_SUBNET",
    "title": "RDS Running In Public Subnet",
    "description": "Check if RDS instances are running in a public subnet. It is recommended to run resources such as RDS in private subnet when possible"
}
```


### The Account Has IAM Users

**Purpose**: Check if the account has IAM users.  
**Implemented in version**: 1.0  
**Config**:
```JavaScript
{
    "name": "HAS_IAM_USRES",
    "title": "The Account Has IAM Users",
    "description": "Check if the account has IAM users. It is recommended to use IAM Identity Center for users management instead of account bound IAM users",
    "emailTemplates": {
        "itemFileName": "basic_has_iam_users_item"
    }
}
```