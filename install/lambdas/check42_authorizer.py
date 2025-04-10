import json

def handler(event, context):
    response = {
        "result": "ok"
    }
    
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(response)
    }