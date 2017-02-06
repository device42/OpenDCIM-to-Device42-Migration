# OpenDCIM to Device42 Migration

[Device42](http://www.device42.com/) is a comprehensive data center inventory management and IP Address management software 
that integrates centralized password management, impact charts and applications mappings with IT asset management.

This script migrates data (models:building, room, rack, hardware, device, ip) from OpenDCIM to Device42. 

### Requirements
-----------------------------

    * python 2.7.x
    * pymysql (you can install it with pip install pymysql)
    * requests (you can install it with pip install requests or apt-get install python-requests)
    * allow remote connections to OpenDCIM MySQL port


Any missing requirements should be able to be installed with pip (ie, pip install pymysql) or your package manager (ie, apt-get install python-pymysql)

### Usage
-----------------------------

In opendcim2d42.py, modify the MySQL Source and Device42 upload settings to fit your environment. 

```
# ====== MySQL Source (OpenDCIM) ====== #
DB_IP = 'OpenDCIM server IP'
DB_PORT = 'OpenDCIM MySQL PORT'
DB_NAME = 'OpenDCIM database name'
DB_USER = 'OpenDCIM database user'
DB_PWD = 'OpenDCIM database password'
# ====== Log settings  ==================== #
LOGFILE = 'migration.log'
DEBUG = True  # write debug log
# ====== Device42 upload settings ========= #
D42_USER = 'device42 user'
D42_PWD = 'device42 password'
D42_URL = 'https:// device42 server IP address'
DRY_RUN = False # if True we don't send any REST requests
```

Run the script and enjoy! (`python opendcim2d42.py`)
If you have any questions - feel free to reach out to us at support at device42.com


### Compatibility
-----------------------------
    * Script runs on Linux and Windows


### Gotchas
-----------------------------

    * Order of function calls in main() function is important. Do not change it!
      For example: subnets must be migrated before IP addresses in order for addresses to join appropriate subnets.
    * Devices that are not based on device template are not going to be migrated
    * TemplateID (openDCIM) == Hardware Model (Device42)
    * Racks without height, are not going to be migrated
