import os
import uuid
import json
from lib.install_utils import InstallUtils

recipient_email = os.getenv('AWS_RECIPIENT_EMAIL')
sender_email = os.getenv('AWS_SENDER_EMAIL')
cwd = os.getcwd()
install_config_file = open(cwd + '/config.json')
install_config = json.load(install_config_file)
install_utils = InstallUtils(install_config)
checks_config = install_config['checks']

amplify_stack_name = install_utils.get_cdk_exports_value(install_config['deploymentExports']['amplifyStackNameKey']) 
amplify_web_url =  install_utils.get_cloud_formation_output(amplify_stack_name, ['url'])

checks_table_name = install_utils.get_name_with_prefix('checks')
settings_table_name = install_utils.get_name_with_prefix('settings')

# Clear the checks and settings tables
install_utils.delete_table_contents(checks_table_name)
install_utils.delete_table_contents(settings_table_name)

# Populate the checks table
items_added = 0
for m in checks_config['modules']:
    item_module = m['name']
    item_version = m['version']
    
    for c in m['checks']:
        item_uuid = uuid.uuid4()
        item_id = str(item_uuid)
        item_name = c['name']
        item_title = c['title']
        item_description = c['description'] 
        
        item={
                "id": {'S': item_id},
                "name": {'S': item_name},
                "title": {'S': item_title},
                "description": {'S': item_description},
                "version": {'S': item_version},
                "module": {'S': item_module},
                "enabled": {'BOOL' : True},
                "muted": {'BOOL': False}
            }
        
        if 'config' in c:
            item['config'] = {'S': json.dumps(c['config'])}
        
        if 'emailTemplates' in c:
            item['email_templates'] = {'S': json.dumps(c['emailTemplates'])}
        
        install_utils.put_item(checks_table_name, item)
        items_added += 1

print(f'Added {items_added} checks to the checks table')
        

# Populate the settings table
item_uuid = uuid.uuid4()
item_id = str(item_uuid)
password = install_utils.generate_password()
hashed_password = install_utils.hash_password(password)
item = {
    "id": {'S': item_id},
    "subscriber": {'S': recipient_email},
    "sender": {'S': sender_email},
    "password": {'S': hashed_password},
    "session_token": {'S' : ''},
    "schedule": {'S': ''}
    }

if checks_config['defaults']:
    item['defaults'] = {'S': json.dumps(checks_config['defaults'])}
    
install_utils.put_item(settings_table_name, item)
print(f'The configuration url can be found at {amplify_web_url}. Use email: {recipient_email} and password: {password} to log in')