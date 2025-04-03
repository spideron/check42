# Check42

This repository provides an automated solution that periodically checks your AWS account against best practices and 
sends the findings via email.

## Overview

The Check42 solution performs regular audits of your AWS account configuration to ensure compliance with recommended 
security and operational practices. The solution runs on a schedule and emails the results to specified recipients.

## Installation

### Prerequisites

- An AWS account
- Access to AWS Cloud Shell
- Permissions to create AWS resources (Lambda, EventBridge, SES, etc.)

### Installation Steps

1. Open AWS Cloud Shell in your AWS account

2. Clone this repository:
   ```bash
   git clone https://github.com/spideron/check42
   ```

3. Navigate to the install directory:
   ```bash
   cd check42/install
   ```

4. Make the install script executable:
   ```bash
   chmod +x install.sh
   ```

5. Edit the install script to update required environment variables:
   ```bash
   nano install.sh
   ```

6. Update the following environment variables in the file:
   ```bash
   export AWS_DEFAULT_REGION=''      # e.g., 'us-east-1'
   export AWS_DEFAULT_ACCOUNT=''     # Your AWS account ID
   export AWS_SENDER_EMAIL=''        # Email address that will send reports
   export AWS_RECIPIENT_EMAIL=''     # Email address that will receive reports
   ```

7. Save the file (in nano: Ctrl+O, then Enter, then Ctrl+X)

8. Run the installation script:
   ```bash
   ./install.sh
   ```

9. **Important**: After running the installation script, you will receive an email from 
AWS SES to verify the sender email identity. You must click the verification link in this 
email to complete the installation.

## Usage

The Check42 solution will run automatically at 12:00 AM UTC every day.

### Manual Testing

To manually test the solution:

1. Log in to the AWS Console
2. Navigate to AWS Lambda
3. Find and select the `check42_run` Lambda function
4. Click the "Test" tab
5. Create a new test event with an empty JSON object `{}`
6. Click "Test" to run the function

You should receive an email with the AWS Best Practices check results shortly after 
the function completes execution.

## Troubleshooting

- If you're not receiving emails, verify that the sender email was confirmed through the SES verification process
- Check the Lambda function logs in CloudWatch for any execution errors
- Ensure your SES account is out of sandbox mode if sending to non-verified recipients


## Configuration

Check the [configuration doc](docs/config.md)
