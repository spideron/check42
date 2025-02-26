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
        basic_missing_tags_text = open(f'{templates_location}basic_missing_tags.txt')
        basic_missing_tags_html = open(f'{templates_location}basic_missing_tags.html')
        basic_missing_tags_item_text = open(f'{templates_location}basic_missing_tags_item.txt')
        basic_missing_tags_item_html = open(f'{templates_location}basic_missing_tags_item.html')
        basic_missing_mfa_on_root_text = open(f'{templates_location}basic_no_mfa_on_root.txt')
        basic_missing_mfa_on_root_html = open(f'{templates_location}basic_no_mfa_on_root.html')
        basic_no_password_policy_text = open(f'{templates_location}basic_no_password_policy.txt')
        basic_no_password_policy_html = open(f'{templates_location}basic_no_password_policy.html')
        
        
        self.MAIN_TEXT = main_text_file.read()
        self.MAIN_HTML = main_html_file.read()
        self.BASIC_MISSING_TAGS_TEXT = basic_missing_tags_text.read()
        self.BASIC_MISSING_TAGS_HTML = basic_missing_tags_html.read()
        self.BASIC_MISSING_TAGS_ITEM_TEXT = basic_missing_tags_item_text.read()
        self.BASIC_MISSING_TAGS_ITEM_HTML = basic_missing_tags_item_html.read()
        self.BASIC_MISSING_MFA_ON_ROOT_TEXT = basic_missing_mfa_on_root_text.read()
        self.BASIC_MISSING_MFA_ON_ROOT_HTML = basic_missing_mfa_on_root_html.read()
        self.BASIC_NO_PASSWORD_POLICY_TEXT = basic_no_password_policy_text.read()
        self.BASIC_NO_PASSWORD_POLICY_HTML = basic_no_password_policy_html.read()
        
        

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
    
    
    def send_message_from_checks(self, processed_checks: list) -> Message:
        """
        Compile an email message from AWS Best practices checks
        """
        
        findings_text = ''
        findings_html = ''
        required_tags = ''
        
        # Get the required tags from the checks configuration
        for c in self.checks:
            match c['name']:
                case 'MISSING_TAGS':
                    missing_tags_config = json.loads(c['config'])
                    required_tags = ','.join(missing_tags_config['requiredTags'])
        
        
        # Go through the processed checkes
        for c in processed_checks:
            if c['pass'] is False:
                message = None
                match c['check']:
                    case 'MISSING_TAGS':
                        message = self.compile_missing_tags_message(required_tags, c['info'])
                    case 'NO_MFA_ON_ROOT':
                        message = self.compile_missing_mfa_on_root_message()
                    case 'NO_PASSWORD_POLICY':
                        message = self.compile_no_password_policy_message()
                
                if message is not None:
                    findings_text += message.message_text
                    findings_html += message.message_html
                
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
        
        
    def compile_missing_mfa_on_root_message(self) -> Message:
        """
        Compile missing MFA on Root email section
        """
        
        message = Message(self.templates.BASIC_MISSING_MFA_ON_ROOT_HTML, self.templates.BASIC_MISSING_MFA_ON_ROOT_TEXT)
        return message
    
    
    def compile_no_password_policy_message(self) -> Message:
        """
        Compile no password policy email section
        """
        
        message = Message(self.templates.BASIC_NO_PASSWORD_POLICY_HTML, self.templates.BASIC_NO_PASSWORD_POLICY_TEXT)
        return message