import os
import json
import boto3
import re
from botocore.exceptions import ClientError
from lib.utils import Utils

utils = Utils()

table_name = os.environ.get('checks_table_name')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(table_name)


def handler(event, context):
    errors=[]
    statusCode = 200
    response_body = {
        'status': 'success',
        'message': ''
    }

    try:
        if event.get('httpMethod') == 'GET':
            checks = utils.get_checks()

            if checks is None:
                status_code = 500
                errors.append('Could not retrieve check items')
            else:
                status_code = 200
                response_body['message'] = checks

        elif event.get('httpMethod') == 'PUT':
            request_body = event['body']
            checks = json.loads(request_body)["checks"]
            validation_errors = utils.validate_checks(checks)
            
            if len(validation_errors) > 0:
                status_code = 400
                errors = validation_errors
            else:
                update_errors = utils.update_checks(checks)
                if len(update_errors) > 0:
                    status_code = 500
                    print(json.dumps(update_errors))
                    errors.append('Failed updating one or more checks. Check the logs')
                else:
                    status_code = 200
                    response_body['message'] = "Update completed successfully"
        else:
            status_code = 400
            errors.append('Unsupported HTTP method')
    except Exception as e:
        print(e)
        status_code = 500
        errors.append('Internal server error. Check the logs')

    if len(errors) > 0:
        response_body['status'] = 'error'
        response_body['message'] = errors

    response = utils.lambda_response(response_body, status_code)
    return response