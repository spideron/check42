import os
import json
from lib.install_utils import InstallUtils

cwd = os.getcwd()
install_config_file = open(cwd + '/config.json')
install_config = json.load(install_config_file)
install_utils = InstallUtils(install_config)

password = install_utils.generate_password()
hashed_password = install_utils.hash_password(password)

install_utils.update_password(hashed_password)
print(f'New password created: {password}')