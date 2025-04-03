# Check42 - templates

The Check42 uses templates to send emails in both html and text formats. The templates are splitted into 3 sections:
- main
- specific check section
- list of items for a sepcific check

All the email template can be found under the [email_templates folder](../install/lambdas/email_templates/).  

## Template sections

### Main

The main email template section holds the structure of the email message.  
[main.html](../install/lambdas/email_templates/main.html)  
[main.txt](../install/lambdas/email_templates/main.txt)  


### Specific check section

Each check will create its own html and text formatted section which will be added to the main section. The default 
behavior will extract the title and description from the check configuration stored in the database and will inject 
them into the check section. The default check section can be found in 
[default_section.html](../install/lambdas/email_templates/default_section.html) and 
[default_section.txt](../install/lambdas/email_templates/default_section.txt).

To override the default behavior, create html and text templates in the 
[templates folder](../install/lambdas/email_templates/) and reference it in the check configuration. Notice that the 
`baseFileName` property does not include the file extension. If the `baseFileName` is set as `my_file_name`, then 
create the files `my_file_name.html` and `my_file_name.txt` inside the email_templates folder.
```JavaScript
{
    "name": "MY_CHECK",
    "title": "Short description of the check",
    "description": "Short description of the check",
    "emailTemplates": {
        "baseFileName": "my_file_name"
    }
}
```


### List of items for a sepcific check

If there's a list of items to add to the check, the default behavior will try to extract if from the checker results. 
Currently it will expect a list of objects with a `region` and `resource` fields to automatically inject it to the 
email message. For examples:
```JavaScript
[
{"region": "us-west-2", "resource": "my resource 1"},
{"region": "us-east-1", "resource": "my resource 2"}
]
```

To override the default behavior, create html and text templates in the 
[templates folder](../install/lambdas/email_templates/) and reference it in the check configuration. Notice that the 
`itemFileName` property does not include the file extension. If the `itemFileName` is set as `my_item_file_name`, then 
create the files `my_item_file_name.html` and `my_item_file_name.txt` inside the email_templates folder.
```JavaScript
{
    "name": "MY_CHECK",
    "title": "Short description of the check",
    "description": "Short description of the check",
    "emailTemplates": {
        "itemFileName": "my_item_file_name"
    }
}
```