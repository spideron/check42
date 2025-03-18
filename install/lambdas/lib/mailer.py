import os
import boto3
import json
from .check_type import CheckType 
from botocore.exceptions import ClientError

    
class Template:
    def __init__(self, txt = None, html = None, item_txt = None, item_html = None) -> None:
        self.txt = txt
        self.html = html
        self.item_txt = item_txt
        self.item_html = item_html

class Templates:
    def __init__(self, checks: list) -> None:
        """
        Templates class constructor
        
        Args:
            checks (list): A list of checks settings
        """
        self.email_templates = {}
        cwd = os.getcwd()
        templates_location = f'{cwd}/email_templates/'
        main_text_file = open(f'{templates_location}main.txt')
        main_html_file = open(f'{templates_location}main.html')
        template = Template(txt=main_text_file.read(), html=main_html_file.read())
        
        self.email_templates['main'] = template
        
        for check in checks:
            if 'email_templates' in check:
                email_template = json.loads(check['email_templates'])
                template = Template()
                if 'baseFileName' in email_template:
                    file_txt_path = f'{templates_location}{email_template["baseFileName"]}.txt'
                    file_html_path = f'{templates_location}{email_template["baseFileName"]}.html'
                    
                    if os.path.exists(file_txt_path):
                        template.txt = open(file_txt_path).read()
                    
                    if os.path.exists(file_html_path):
                        template.html = open(file_html_path).read()
                
                if 'itemFileName' in email_template:
                    file_txt_path = f'{templates_location}{email_template["itemFileName"]}.txt'
                    file_html_path = f'{templates_location}{email_template["itemFileName"]}.html'
                    
                    if os.path.exists(file_txt_path):
                        template.item_txt = open(file_txt_path).read()
                    
                    if os.path.exists(file_html_path):
                        template.item_html = open(file_html_path).read()
                
                self.email_templates[check['name']] = template
    
        
    def get_template(self, check_type: str) -> Template:
        """
        Get an email template by the provided check type
        
        Args:
            check_type (str): The Check Type
        """
        
        template = Template()
        if check_type in self.email_templates:
            template = self.email_templates[check_type]
            
        return template
        

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
        self.email_templates = Templates(checks)

    
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
        
        Args:
            processed_checks(list): A list of items from the checker
            
        Returns (Message): A Message object containig the email text and html sections
        """
        
        findings_text = ''
        findings_html = ''
        required_tags = ''
        
        # Get the required tags from the checks configuration
        for c in self.checks:
            match c['name']:
                case CheckType.MISSING_TAGS.value:
                    missing_tags_config = json.loads(c['config'])
                    required_tags = ' | '.join(missing_tags_config['requiredTags'])
        
        
        # Go through the processed checks
        for c in processed_checks:
            if c['pass'] is False:
                message = None
                match c['check']:
                    case CheckType.MISSING_TAGS.value:
                        message = self.compile_missing_tags_message(required_tags, c['info'])
                    case CheckType.NO_MFA_ON_ROOT.value:
                        message = self.compile_simple_message(CheckType.NO_MFA_ON_ROOT.value)
                    case CheckType.NO_PASSWORD_POLICY.value:
                        message = self.compile_simple_message(CheckType.NO_PASSWORD_POLICY.value)
                    case CheckType.PUBLIC_BUCKETS.value:
                        message = self.compile_s3_public_buckets_access(c['info'])
                    case CheckType.NO_BUSINESS_SUPPORT.value:
                        message = self.compile_simple_message(CheckType.NO_BUSINESS_SUPPORT.value)
                    case CheckType.NO_BUDGET.value:
                        message = self.compile_simple_message(CheckType.NO_BUDGET.value)
                    case CheckType.UNUSED_EIP.value:
                        message = self.compile_unused_eips(c['info'])
                
                if message is not None:
                    findings_text += message.message_text
                    findings_html += message.message_html
         
        main_template = self.email_templates.get_template('main')
        main_text = ''
        main_html = ''
        
        if main_template.txt is not None:
            main_text = main_template.txt.replace('***FINDINGS***', findings_text)
        if main_template.html is not None:
            main_html = main_template.html.replace('***FINDINGS***', findings_html)
        
        message = Message(main_html, main_text, subject='AWS Best Practices Checks') #TODO: Move subject to configuration
        self.send(message)
    
    
    def compile_simple_message(self, check_type: str) -> Message:
        """
        Compile a simple message where there's no specific string replacement needed
        
        Args:
            check_type (str): The check type
        """
        
        template = self.email_templates.get_template(check_type)
        html = ''
        txt = ''
        
        if template.html is not None:
            html = template.html
        if template.txt is not None:
            txt = template.txt
            
        message = Message(html, txt)
        return message
        
    
    def compile_missing_tags_message(self, required_tags: str, missing_tags_resource: list) -> Message:
        """
        Compile missing tags email section
        
        Args:
            required_tags (list): A string representing a list of required tags
            missing_tags_resource (str): A list of missing tags resources recorded by AWS Config
        
        Returns (Message): A Message object containig the email text and html sections
        """
        
        item_text = ''
        item_html = ''
        missing_tags_text = ''
        missing_tags_html = ''
        template = self.email_templates.get_template(CheckType.MISSING_TAGS.value)
        
        for key, value in missing_tags_resource.items():
            if value:  # Check if the array is not empty
                for t in value:
                    template_text = ''
                    template_html = ''
                
                    if template.item_txt is not None:
                        template_text = template.item_txt.replace(
                            '***RESOURCE_TYPE***', t['resource_type']).replace('***RESOURCE_ID***', t['resource_arn'])
                    
                    if template.item_html is not None:
                        template_html = template.item_html.replace(
                        '***RESOURCE_TYPE***', t['resource_type']).replace('***RESOURCE_ID***', t['resource_arn']).replace(
                            '***RESOURCE_URL***', '')
                
                    item_text += template_text
                    item_html += template_html
        
        if template.txt is not None:
            missing_tags_text = template.txt.replace(
                '***MISSING_TAGS_LIST***', item_text).replace('***TAGS***', required_tags)
          
        if template.html is not None: 
            missing_tags_html = template.html.replace(
                '***MISSING_TAGS_LIST***', item_html).replace('***TAGS***', required_tags)
        
        message = Message(missing_tags_html, missing_tags_text)
        return message
        
    
    def compile_s3_public_buckets_access(self, processed_checks: list) -> Message:
        """
        Compile S3 public buckets access email section
        
        Args:
            processed_checks(list): A list of items from the checker
        
        Returns (Message): A Message object containing the email text and html sections
        """
        bucket_list_text = ''
        bucket_list_html = ''
        findings_text = ''
        findings_html = ''
        template = self.email_templates.get_template(CheckType.PUBLIC_BUCKETS.value)
        
        for bucket_info in processed_checks:
            bucket_name = bucket_info['bucket_name']
            reasons = bucket_info['reasons']
            
            if template.item_txt is not None:
                bucket_list_text += template.item_txt.replace(
                    '***BUCKET_NAME***', bucket_name).replace('***REASON***', '\n'.join(reasons))
            
            if template.item_html is not None:    
                bucket_list_html += template.item_html.replace(
                    '***BUCKET_NAME***', bucket_name).replace('***REASON***', '<br/>'.join(reasons))
        
        if template.txt is not None:
            findings_text = template.txt.replace('***S3_BUCKETS_LIST***', bucket_list_text)
        if template.html is not None:
            findings_html = template.html.replace('***S3_BUCKETS_LIST***', bucket_list_html)
        
        message = Message(findings_html, findings_text)
        return message
        
    
    def compile_unused_eips(self, processed_checks: list) -> Message:
        """
        Compile unused elastic ips email section
        
        Args:
            processed_checks(list): A list of items from the checker
        
        Returns (Message): A Message object containig the email text and html sections
        """
        
        eip_list_text = ''
        eip_list_html = ''
        findings_text = ''
        findings_html = ''
        template = self.email_templates.get_template(CheckType.UNUSED_EIP.value)
        
        for eip in processed_checks:
            region = eip['region']
            allocation_id = eip['allocationId']
            public_ip = eip['publicIp']
            tags = ' | '.join(eip['tags'])
            
            if template.item_txt is not None:
                eip_list_text += template.item_txt.replace(
                    '***REGION***', region).replace('***IP_ADDRESS***', public_ip).replace(
                        '***TAGS***', tags)
            
            if template.item_html is not None:    
                eip_list_html += template.item_html.replace(
                    '***REGION***', region).replace('***IP_ADDRESS***', public_ip).replace(
                        '***TAGS***', tags)
        
        if template.txt is not None:
            findings_text = template.txt.replace('***UNUSED_EIPS***', eip_list_text)
        if template.html is not None:
            findings_html = template.html.replace('***UNUSED_EIPS***', eip_list_html)
        
        message = Message(findings_html, findings_text)
        return message