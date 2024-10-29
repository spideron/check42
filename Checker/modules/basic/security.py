import boto3
import botocore

iam_client = boto3.client('iam')
s3_client = boto3.client('s3')

def has_root_mfa():
    mfa_on_root = False

    try:
        account_summary = iam_client.get_account_summary()

        if account_summary['SummaryMap']['AccountMFAEnabled']:
            mfa_on_root = True
            
    except botocore.exceptions.ClientError as e:
        print(f"Error checking root MFA: {e}")
    
    return mfa_on_root
    


def has_password_policy():
    
    sufficient_password_policy = True
    
    try:
        iam_client.get_account_password_policy()
    except iam_client.exceptions.NoSuchEntityException:
        sufficient_password_policy = False
    except botocore.exceptions.ClientError as e:
        print(f"Error checking account password policy: {e}")
    
    return sufficient_password_policy


def buckets_with_public_access():
    public_buckets = []
    buckets = s3_client.list_buckets()
    
    for bucket in buckets['Buckets']:
        try:
            access = s3_client.get_public_access_block(Bucket=bucket['Name'])
            if not all(access['PublicAccessBlockConfiguration'].values()):
                public_buckets.append(bucket['Name'])
        except botocore.exceptions.ClientError as e:
            print(f"Error checking bucket {bucket['Name']}: {e}")
    
    return public_buckets
    