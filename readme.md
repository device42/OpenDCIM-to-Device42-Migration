# OpenDCIM to Device42 Migration

[Device42](http://www.device42.com/) is a comprehensive data center inventory management and IP Address management software 
that integrates centralized password management, impact charts and applications mappings with IT asset management.

This script migrates data from OpenDCIM to Device42.

### Requirements
-----------------------------

    * pymysql
    * codecs
    * requests
    * base64 
    * random
    * json
Any missing requirements should be able to be installed with pip (ie, pip install pymysql) or your package manager (ie, apt-get install python-pymysql)

### Usage
-----------------------------

In opendcim2d42.py, modify the MySQL Source and Device42 upload settings to fit your environment. 

```
# ====== MySQL Source (openDCIM) ====== #
DB_IP       = ''
DB_NAME  = ''
DB_USER   = ''
DB_PWD    = ''
# ====== Log settings  ==================== #
LOGFILE    = 'migration.log'
DEBUG      = True
# ====== Device42 upload settings ========= #
D42_USER   = ''
D42_PWD    = '2'
D42_URL     = 'https://'
DRY_RUN     = False
```
