import os
import shutil
import zipfile

class Lambdatils:
    def __init__(self, app_name: str) -> None:
        """
        LambdaUtils constructor
        """
        self.temp_path = f'/tmp/{app_name}/temp/'
        self.build_path = f'/tmp/{app_name}/build/'
        
    
    def create_deployment_package(self, file_name: str, file_location: str, include_folders: list, dependencies=[]):
        """
        Create a Lambda Function deployment package
        
        Args:
            lambda_name (str): The name of the Lambda Function
            file_location (str): The location of the Lambda Function code
            include_folders (list): A list of folder to include in the package
            dependencies (list): List of dependencies to install. Default: empty list
        """
        
        # Create a temporary directory for the deployment package
        if not os.path.exists(self.temp_path):
            os.makedirs(self.temp_path)
        
        if not os.path.exists(self.build_path):
            os.makedirs(self.build_path)

        # Copy the Lambda function to the temp directory
        shutil.copy('../{}'.format(file_location), self.temp_path)
        
        for f in include_folders:
            shutil.copytree(f'../lambdas/{f}', f'{self.temp_path}{f}')
        
        # Install dependencies (if there are any) and copy them to the temp directory
        if len(dependencies) > 0:
            for p in dependencies:
                os.system(f"/bin/sh -c 'python -m pip install {p} --target {self.build_path}'")
            shutil.copytree(self.build_path, self.temp_path, dirs_exist_ok = True)
        
        # Create the ZIP file
        with zipfile.ZipFile(file_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.temp_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.temp_path)
                    zipf.write(file_path, arcname)

        # Clean up temporary directory
        if os.path.exists(self.temp_path):
            shutil.rmtree(self.temp_path)
        
        if os.path.exists(self.build_path):
            shutil.rmtree(self.build_path)
    
    
    def role_name(self, function_name: str) -> str:
        """
        Get a role name for a lambda function
        
        Args:
            function_name (str): The Lambda Function name
        
        Returns (str): An IAM Role name
        """
        
        return f'{function_name}_role'
        