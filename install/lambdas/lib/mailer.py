import os
import boto3
import json
from botocore.exceptions import ClientError

class Templates:
    def __init__(self) -> None:
        cwd = os.getcwd()
        templates_location = f'{cwd}/email_templates/'
        main_text_file = open(f'{templates_location}main.txt')
        main_html_file = open(f'{templates_location}main.html')
        basic_missing_tags_text = open(f'{templates_location}basic_missing_tags.html')
        basic_missing_tags_html = open(f'{templates_location}basic_missing_tags.html')
        basic_missing_tags_item_text = open(f'{templates_location}basic_missing_tags_item.html')
        basic_missing_tags_item_html = open(f'{templates_location}basic_missing_tags_item.html')
        
        
        self.MAIN_TEXT = main_text_file.read()
        self.MAIN_HTML = main_html_file.read()
        self.BASIC_MISSING_TAGS_TEXT = basic_missing_tags_text.read()
        self.BASIC_MISSING_TAGS_HTML = basic_missing_tags_html.read()
        self.BASIC_MISSING_TAGS_ITEM_TEXT = basic_missing_tags_item_text.read()
        self.BASIC_MISSING_TAGS_ITEM_HTML = basic_missing_tags_item_html.read()
        
        

class Message:
     def __init__(self, message_html: str, message_text:str, subject = '') -> None:
         self.subject = subject
         self.message_html = message_html
         self.message_text = message_text


class Mailer:
    def __init__(self, checks: list, sender: str, recipient: str) -> None:
        """
        Initialize the Mailer class
        
        Args:
            checks (list): A list of checks settings
            sender (str): The sender email address
            recipient (str): The recipient email address
        """
        self.checks = checks
        self.sender = sender
        self.recipient = recipient
        self.ses_client = boto3.client('ses')
        self.templates = Templates()

    
    def send(self, message: Message) -> None:
        """
        Send an email using SES
        
        Args:
            message(Message): A message object
        """
        
        try:
            email_message = {
                'Source': self.sender,
                'Destination': {
                    'ToAddresses': [
                        self.recipient
                    ]
                },
                'Message': {
                    'Subject': {
                        'Data': message.subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': message.message_text,
                            'Charset': 'UTF-8'
                        },
                        'Html': {
                            'Data': message.message_html,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            }
            
            # Send the email
            response = self.ses_client.send_email(**email_message)
            
        except Exception as e:
            print(str(e))
            raise(e)
    
    
    def send_message(self) -> Message:
        """
        Compile an email message from AWS Best practices checks
        """
        
        findings_text = ''
        findings_html = ''
        
        for c in self.checks:
            match c['check']:
                case 'MISSING_TAGS':
                    missing_tags_checks = None
                    for check in self.checks:
                        if check["name"] == "MISSING_TAGS":
                            missing_tags_checks = check
                            break
                        
                    required_tags = ''
                    if missing_tags_checks is not None:
                        missing_tags_checks_config = json.loads(missing_tags_checks['config'])
                        required_tags = ','.join(missing_tags_checks_config['requiredTags'])
                    
                    message = self.compile_missing_tags_message(required_tags, c['info'])
                    findings_text += message.message_text
                    findings_html ++ message.message_html
                    
        main_text = self.templates.MAIN_TEXT.replace('***FINDINGS***', findings_text)
        main_html = self.templates.MAIN_HTML.replace('***FINDINGS***', findings_html)
        
        message = Message(main_html, main_text, subject='AWS Best Practices Checks') #TODO: Move subject to configuration
        self.send(message)
    
    
    def compile_missing_tags_message(self, required_tags: str, missing_tags_resource: list) -> Message:
        """
        Compile missing tags email section
        
        Args:
            required_tags (list): A string representing a list of required tags
            missing_tags_resource (str): A list of missing tags resources recorded by AWS Config
        """
        
        item_text = ''
        item_html = ''
        for t in missing_tags_resource:
            template_text = self.templates.BASIC_MISSING_TAGS_ITEM_TEXT.replace(
                '***RESOURCE_TYPE***', t['ResourceType']).replace('***RESOURCE_ID***', t['ResourceId'])
                
            template_html = self.templates.BASIC_MISSING_TAGS_ITEM_HTML.replace(
                '***RESOURCE_TYPE***', t['ResourceType']).replace('***RESOURCE_ID***', t['ResourceId']).replace(
                    '***RESOURCE_URL***', '') # TODO: compile link to the resource
            
            item_text += template_text
            item_html += template_html
        
        missing_tags_text = self.templates.BASIC_MISSING_TAGS_TEXT.replace(
            '***MISSING_TAGS_LIST***', item_text).replace('***TAGS***', required_tags)
            
        missing_tags_html = self.templates.BASIC_MISSING_TAGS_HTML.replace(
            '***MISSING_TAGS_LIST***', item_html).replace('***TAGS***', required_tags)
        
        message = Message(missing_tags_html, missing_tags_text)
        
        return message
        
    
        