# Check42 - configuration

The [configuration file](../install/config.json) can be found under the install folder.

## Structure

```JavaScript
{
    "prefix": "",
    "tags": [],
    "dynamodb": {
        "tables": []
    },
    "lambda": {
        "defaults": {
            "memory": 0,
            "timeout": 0
        },
        "includeFolders": [],
        "functions": {},
    "api": {

    },
    "ses": {
        "senderEmail": ""
    },
    "schedule": {
        "ruleNmae": "",
        "defaultSchedule": {
            "minute": "",
            "hour": "",
            "day": "",
            "month": "",
            "year": ""
        }
    },
    "checks": {
        "defaults": {
            "regions": []
        },
        "modules": [{
            "name": "",
            "version": "",
            "checks": []
        }]
    }
}

```

- **prefix**: A prefix for AWS resources, for example, a DynamoDB table that holds the checks, can be named 
"prefix_checks". If the prefix name is `check42` and the table name in the configuration is named `checks`, 
the actual table name will be `check42_checks`

```JavaScript
"prefix": "aws_best_practices"
```


- **tags**: A list of Key and Value tags to attach to the resources created by the installer. For example:

```JavaScript
"tags": [{
        "Key": "environment",
        "Value": "monitoring"
    },
    {
        "Key": "project",
        "Value": "check42"
    }
]
```


- **dynamodb**: DynamoDB configuration section.  
    - **tables**: List of tables to create. The prefix will be added to the table name.

```JavaScript
"dynamodb": {
    "tables": ["checks", "settings", "log"]
}
```


- **lambda**: Lambda Functions configuration section.  
    - **defaults**: Default values section.  
        - **memory**: The default memory use for the Lambda Functions.  
        - **timeout**: The default timeout in seconds for the Lambda Functions.  
    - **includeFolders**: Local folders to include in the Lambda Functions package.  
    - **functions**: Lambda Functions and their specific configuration.  
        - **Key:Function_Name**: The key for reference to a specific Lambda Function configuration.
            - **functionName**: The name of the Lambda Function. The prefix will be added to the function name.  
            - **fileLocation**: A local file location with the Lambda Function code.  
            - **environment**: (optional), a set of environment variables to add to the Lambda Function.  
            - **includeFolders**: (optional) A list of additional folder to add for the specific Lambda Function.  
            - **iamPolicies**: List of IAM policies configuration needed for the Lambda Function.  
                - **name**: The Name of the IAM policy.  
                - **actions**: A list of IAM actions to allow.  
                - **resources**: A list of resources to apply the policy to. Some known keys will be replaced automatically. 
                    - Some of the known keys are
                        - `***REGION***` - The AWS region
                        - `***ACCOUNT_ID***` - The AWS Account Id
                        - `***PREFIX***` - The application prefix
                        - `***SENDER_EMAIL***` - The sender email as set in the 'ses' section.  

```JavaScript
"lambda": {
        "defaults": {
            "memory": 128,
            "timeout": 5
        },
        "includeFolders": ["lib", "modules"],
        "functions": {
            "settings": {
                "functionName": "settings",
                "fileLocation": "lambdas/check42_settings.py",
                "iamPolicies": [{
                        "name": "dynamodb_access",
                        "actions": [
                            "dynamodb:GetItem",
                            "dynamodb:PutItem",
                            "dynamodb:UpdateItem",
                            "dynamodb:DeleteItem",
                            "dynamodb:Query",
                            "dynamodb:Scan",
                            "dynamodb:BatchGetItem",
                            "dynamodb:BatchWriteItem"
                        ],
                        "resources": [
                            "arn:aws:dynamodb:***REGION***:***ACCOUNT_ID***:table/***PREFIX***_settings"
                        ]
                    },
                    {
                        "name": "event_bridge_access",
                        "actions": [
                            "events:DescribeRule",
                            "events:PutRule"
                        ],
                        "resources": ["*"]
                    }
                ]
            },
            "checks": {
                "functionName": "checks",
                "fileLocation": "lambdas/check42_checks.py",
                "iamPolicies": [{
                    "name": "dynamodb_access",
                    "actions": [
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:Query",
                        "dynamodb:Scan",
                        "dynamodb:BatchGetItem",
                        "dynamodb:BatchWriteItem"
                    ],
                    "resources": [
                        "arn:aws:dynamodb:***REGION***:***ACCOUNT_ID***:table/***PREFIX***_checks"
                    ]
                }]
            },
            "run": {
                "timeout": 60,
                "functionName": "run",
                "fileLocation": "lambdas/check42_run.py",
                "includeFolders": ["email_templates"],
                "iamPolicies": [{
                        "name": "dynamodb_access",
                        "actions": [
                            "dynamodb:GetItem",
                            "dynamodb:PutItem",
                            "dynamodb:UpdateItem",
                            "dynamodb:DeleteItem",
                            "dynamodb:Query",
                            "dynamodb:Scan",
                            "dynamodb:BatchGetItem",
                            "dynamodb:BatchWriteItem"
                        ],
                        "resources": [
                            "arn:aws:dynamodb:***REGION***:***ACCOUNT_ID***:table/***PREFIX***_checks",
                            "arn:aws:dynamodb:***REGION***:***ACCOUNT_ID***:table/***PREFIX***_log",
                            "arn:aws:dynamodb:***REGION***:***ACCOUNT_ID***:table/***PREFIX***_settings"
                        ]
                    },
                    {
                        "name": "ses_access",
                        "actions": [
                            "ses:SendEmail",
                            "ses:SendRawEmail"
                        ],
                        "resources": ["arn:aws:ses:***REGION***:***ACCOUNT_ID***:identity/***SENDER_EMAIL***"]
                    },
                    {
                        "name": "general_access",
                        "actions": [
                            "s3:ListAllMyBuckets",
                            "s3:GetBucketAcl",
                            "s3:GetBucketPolicy",
                            "s3:GetBucketPolicyStatus",
                            "s3:GetBucketPublicAccessBlock",
                            "s3:GetBucketLocation",
                            "support:DescribeSeverityLevels",
                            "budgets:DescribeBudgets",
                            "budgets:ViewBudget",
                            "ec2:DescribeRegions",
                            "ec2:DescribeAddresses",
                            "ec2:DescribeVolumes",
                            "ec2:DescribeVpcs",
                            "ec2:DescribeInstances",
                            "ec2:DescribeSecurityGroups",
                            "ec2:DescribeSubnets",
                            "ec2:DescribeNetworkInterfaces",
                            "ec2:DescribeRouteTables",
                            "rds:DescribeDBInstances",
                            "elasticloadbalancing:DescribeLoadBalancers",
                            "iam:GetAccountPasswordPolicy",
                            "iam:GetAccountSummary",
                            "iam:ListUsers",
                            "tag:GetResources",
                            "ce:GetCostAndUsage"
                        ],
                        "resources": ["*"]
                    }
                ]
            },
            "schedule": {
                "functionName": "schedule",
                "fileLocation": "lambdas/check42_schedule.py"
            }
        }
    }
```


- **api**: API Gateway configuration section. TODO: NEED TO IMPLEMENT

```JavaScript
{
    
}
```

- **ses**: SES configuration section.  
    - **senderEmail**: The sender email address for the notification emails. Can be set directly here but preferred to be stored in an OS environment variable named `AWS_SENDER_EMAIL`.  

```JavaScript
"ses": {
    "senderEmail": "SET SENDER EMAIL ADDRESS HERE OR USE AWS_SENDER_EMAIL environment variable"
}
```

- **schedule**: An EventBridge schedule configuration. This will be used to invoke the checker.  
    - **ruleNmae**: The name of the rule. The prefix will be added to it.  
    - **defaultSchedule**: The default schedule to run the checker. The time is in UTC.  

```JavaScript
"schedule": {
    "ruleNmae": "schedule",
    "defaultSchedule": {
        "minute": "0",
        "hour": "0",
        "day": "*",
        "month": "*",
        "year": "*"
    }
}
```

- **checks**: A list of checks configuration. These checks will be saved in the checks DynamoDB table.   
    - **defaults**: A section for default values
        - **regions**: A list of default regions to use for the checks
    - **modules**: A list of checks modules.  
        - **name**: The module name.  
        - **version**: The module current version.  
        - **checks**: A list of checks for the module.  
            - **name**: The check name. This corresponds to the [CheckType](../install/lambdas/lib/check_type.py).  
            - **title**: A title with short description for the check  
            - **description**: A longer description of the check  
            - **emailTemplates**: (optional) Email template configuration section. More information in the [templates doc](./templates.md)
            - **config**: Extra configuration section to be used by the checker for the specific check.  

```JavaScript
"checks": {
        "defaults": {
            "regions": ["us-west-2", "us-east-1"]
        },
        "modules": [{
            "name": "basic",
            "version": "1.0",
            "checks": [{
                    "name": "NO_MFA_ON_ROOT",
                    "title": "No MFA on Root",
                    "description": "Check if multi-factor authentication (MFA) was set on the root account. As a security best practice, enable MFA for AWS account access, especially for long-term credentials such as the account root user and IAM users."
                },
                {
                    "name": "NO_PASSWORD_POLICY",
                    "title": "Password policy is not configured",
                    "description": "Check if a password policy was set for the account. Require that passwords adhere to a strong password policy to help prevent discovery through brute force or social engineering."
                },
                {
                    "name": "PUBLIC_BUCKETS",
                    "title": "Public S3 Buckets",
                    "description": "Check if any of the S3 buckets on the account are set for a public access. It is recommended to keep private access to S3 buckets unless it's necessary",
                    "emailTemplates": {
                        "itemFileName": "basic_s3_public_access_item"
                    }
                },
                {
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
                },
                {
                    "name": "NO_BUSINESS_SUPPORT",
                    "title": "No Premium Support",
                    "description": "Check if the account is enrolled in premium support (business, enterprise, or enterprise on-ramp). It is recommended to enroll in premium support for any account with workloads in production"
                },
                {
                    "name": "NO_BUDGET",
                    "title": "No Budget Set",
                    "description": "Check if there's at least one budget set on the account. It is recommended to have a budget set in order o monitor and control costs"
                },
                {
                    "name": "UNUSED_EIP",
                    "title": "Unused Elastic IPs",
                    "description": "Check if there are unused Elastic IPs (EIPs). It is recommended to release any unused EIPs",
                    "emailTemplates": {
                        "itemFileName": "basic_unused_eip_item"
                    }
                },
                {
                    "name": "UNATTACHED_EBS_VOLUMES",
                    "title": "Unattached EBS Volumes",
                    "description": "Check if there are EBS volumes not attached to an instance. It is recommended to delete EBS volumes if they have no use anymore",
                    "emailTemplates": {
                        "itemFileName": "basic_unattached_ebs_volume_item"
                    }
                },
                {
                    "name": "USING_DEFAULT_VPC",
                    "title": "Default VPC Is In Use",
                    "description": "Check if the default VPC exists and if there are any resources in it. It is recommended to create a custom VPC and control the network configuration"
                },
                {
                    "name": "EC2_IN_PUBLIC_SUBNET",
                    "title": "EC2 Running In Public Subnet",
                    "description": "Check if EC2 instances are running in a public subnet. It is recommended to run resources such as EC2 in private subnet when possible"
                },
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
                },
                {
                    "name": "RDS_PUBLIC_ACCESS",
                    "title": "RDS instance is set for public access",
                    "description": "Check if RDS instance(s) are set for public access. It is recommended to keep RDS instances with private access when possible"
                },
                {
                    "name": "RDS_IN_PUBLIC_SUBNET",
                    "title": "RDS Running In Public Subnet",
                    "description": "Check if RDS instances are running in a public subnet. It is recommended to run resources such as RDS in private subnet when possible"
                },
                {
                    "name": "HAS_IAM_USRES",
                    "title": "The Account Has IAM Users",
                    "description": "Check if the account has IAM users. It is recommended to use IAM Identity Center for users management instead of account bound IAM users",
                    "emailTemplates": {
                        "itemFileName": "basic_has_iam_users_item"
                    }
                }
            ]
        }]
    }
```