import boto3
from botocore.exceptions import ClientError

def get_checks():
    """
    Get the check items from DynamoDB
    
    Returns (list): List of check items. None in case of an error
    """
    try:
        # Create a DynamoDB resource
        dynamodb = boto3.resource('dynamodb')
        
        # Get the table
        table = dynamodb.Table('aws_best_practices_checks')
        
        # Perform a simple scan
        response = table.scan()
        
        # Get the items from the response
        items = response.get('Items', [])
        
        return items
    
    except ClientError as e:
        print("Error: {}".format(e.response['Error']['Message']))
        return None
    except Exception as e:
        print("Error: {}".format(str(e)))
        return None


def handler(event, context):
    errors=[]
    statusCode = 200
    headers = {
        "Content-Type": "application/json"
    }
    
    checks = get_checks()
    if checks is not None:
        for c in checks:
            print(c)
