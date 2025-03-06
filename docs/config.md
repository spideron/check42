# AWS Best Practices - configuration

The AWS Best practices [configuration file](../../install/config.json) can be found under the install folder.

## Structure

```JavaScript
{
    "prefix": "",
    "tags": [],
    "dynamodb": {
        "tables": []
    },
    "iam": {
        "configRoleName": ""
    },
    "lambda": {
        "defaults": {
            "memory": 0,
            "timeout": 0
        },
        "includeFolders": [],
        "functions": {},
    "configRules": {
        "ruleName": "",
        "requiredTags": [],
        "resourcesToChecks": []
    },
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
        "modules": [{
            "name": "basic",
            "version": "1.0",
            "checks": []
        }]
    }
}

```

- **prefix**: A prefix for AWS resources, for example, a DyanmoDB table that holds the checks, can be named 
"prefix_checks". If the prefix name is `aws_best_practices` and the table name in the configuration is named 
`checks`, the actual table name will be `aws_best_practices_checks`

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
        "Value": "aws-best-practices-checks"
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

- **iam**: IAM configuration section.  
    - **configRoleName**: AWS Config role name.

```JavaScript
"iam": {
    "configRoleName": "config_role"
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
            - **includeFolders**: A list of additional folder to add for the specific Lambda Function.  
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
        "logItemName": {
            "functionName": "log_item",
            "fileLocation": "lambdas/aws_best_practices_log_item.py",
            "iamPolicies": [{
                "name": "dynamodb_access",
                "actions": [
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:Query",
                    "dynamodb:Scan",
                    "dynamodb:BatchGetItem",
                    "dynamodb:BatchWriteItem"
                ],
                "resources": [
                    "arn:aws:dynamodb:***REGION***:***ACCOUNT_ID***:table/***PREFIX***_log"
                ]
            }]
        },
        "run": {
            "timeout": 60,
            "functionName": "run",
            "fileLocation": "lambdas/aws_best_practices_run.py",
            "environment": {
                "senderEmail": "SET SENDER EMAIL ADDRESS HERE OR USE AWS_SENDER_EMAIL environment variable",
                "recipientEmail": "SET RECIPIENT EMAIL ADDRESS HERE OR USE AWS_RECIPIENT_EMAIL environment variable"
            },
            "includeFolders": ["email_templates"],
            "iamPolicies": [{
                    "name": "dynamodb_access",
                    "actions": [
                        "dynamodb:GetItem",
                        "dynamodb:Query",
                        "dynamodb:Scan",
                        "dynamodb:BatchGetItem"
                    ],
                    "resources": [
                        "arn:aws:dynamodb:***REGION***:***ACCOUNT_ID***:table/***PREFIX***_checks"
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
                    "name": "config_access",
                    "actions": [
                        "config:GetComplianceDetailsByConfigRule"
                    ],
                    "resources": ["*"]
                },
                {
                    "name": "s3_access",
                    "actions": [
                        "s3:ListAllMyBuckets",
                        "s3:GetBucketAcl",
                        "s3:GetBucketPolicy",
                        "s3:GetBucketPolicyStatus",
                        "s3:GetBucketPublicAccessBlock",
                        "s3:GetBucketLocation"
                    ],
                    "resources": ["*"]
                },
                {
                    "name": "support_access",
                    "actions": [
                        "support:DescribeSeverityLevels"
                    ],
                    "resources": ["*"]
                },
                {
                    "name": "budgets_access",
                    "actions": [
                        "budgets:DescribeBudgets",
                        "budgets:ViewBudget"
                    ],
                    "resources": ["*"]
                },
                {
                    "name": "ec2_access",
                    "actions": [
                        "ec2:DescribeRegions",
                        "ec2:DescribeAddresses"
                    ],
                    "resources": ["*"]
                },
                {
                    "name": "iam_access",
                    "actions": [
                        "iam:GetAccountPasswordPolicy",
                        "iam:GetAccountSummary"
                    ],
                    "resources": ["*"]
                }
            ]
        }
    }
}
```

- **configRules**: AWS Config Rules configuration section.  
    - **ruleName**: The config rule name.  
    - **requiredTags**: Required tags the Config Rule will check for against the provided resources.  
    - **resourcesToChecks**: A list of resources Config Rules will check the required tags against.  

```JavaScript
"configRules": {
    "ruleName": "required_tags_rule",
    "requiredTags": ["environment", "project"],
    "resourcesToChecks": [
        "ACM_CERTIFICATE",
        "AUTO_SCALING_GROUP",
        "CLOUDFORMATION_STACK",
        "CODEBUILD_PROJECT",
        "DYNAMODB_TABLE",
        "EC2_CUSTOMER_GATEWAY",
        "EC2_INSTANCE",
        "EC2_INTERNET_GATEWAY",
        "EC2_NETWORK_ACL",
        "EC2_NETWORK_INTERFACE",
        "EC2_ROUTE_TABLE",
        "EC2_SECURITY_GROUP",
        "EC2_SUBNET",
        "EBS_VOLUME",
        "EC2_VPC",
        "EC2_VPN_CONNECTION",
        "EC2_VPN_GATEWAY",
        "ELB_LOAD_BALANCER",
        "ELBV2_LOAD_BALANCER",
        "RDS_DB_INSTANCE",
        "RDS_DB_SECURITY_GROUP",
        "RDS_DB_SNAPSHOT",
        "RDS_DB_SUBNET_GROUP",
        "RDS_EVENT_SUBSCRIPTION",
        "REDSHIFT_CLUSTER",
        "REDSHIFT_CLUSTER_PARAMETER_GROUP",
        "REDSHIFT_CLUSTER_SECURITY_GROUP",
        "REDSHIFT_CLUSTER_SNAPSHOT",
        "REDSHIFT_CLUSTER_SUBNET_GROUP",
        "S3_BUCKET"
    ]
}
```

- **api**: API Gateway configuration section. TODO: NEED TO IMPLEMENT

```JavaScript
{
    
}
```

- **ses**: SES configuration section.  
    - **senderEmail**: The sender email address for the notification emails. Can be set directly here but preferred to be stored in an os environment variable named `AWS_SENDER_EMAIL`.  

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
    - **modules**: A list of checks modules.  
        - **name**: The module name.  
        - **version**: The module current version.  
        - **checks**: A list of checks for the module.  
            - **name**: The check name. This corresponds to the [CheckType](../install/lambdas/lib/check_type.py).  
            - **emailTemplates**: Email template configuration section.  
            - **baseFileName**: The base file name (without .html ot .txt) as it's located in the [email_templates folder](../install/lambdas/email_templates).  
            - **itemFileName**: An email template for a sub section in the base file.  
            - **config**: Extra configuration section to be used by the checker for the specific check.  

```JavaScript
"checks": {
    "modules": [{
        "name": "basic",
        "version": "1.0",
        "checks": [{
                "name": "NO_MFA_ON_ROOT",
                "emailTemplates": {
                    "baseFileName": "basic_no_mfa_on_root"
                }
            },
            {
                "name": "PUBLIC_BUCKETS",
                "emailTemplates": {
                    "baseFileName": "basic_s3_public_access",
                    "itemFileName": "basic_s3_public_access_item"
                }
            },
            {
                "name": "MISSING_TAGS",
                "emailTemplates": {
                    "baseFileName": "basic_missing_tags",
                    "itemFileName": "basic_missing_tags_item"
                },
                "config": {
                    "regions": ["us-west-2"],
                    "configRuleName": "required_tags_rule",
                    "requiredTags": ["environment", "project"]
                }
            },
            {
                "name": "UNUSED_EIP",
                "emailTemplates": {
                    "baseFileName": "basic_unused_eip",
                    "itemFileName": "basic_unused_eip_item"
                },
                "config": {
                    "regions": ["*"]
                }
            }
        ]
    }]
}
```