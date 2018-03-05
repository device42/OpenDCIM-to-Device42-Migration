#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import re
import sys
import pymysql as sql
import codecs
import requests
import base64 
import random
import json


# ========================================================================
# IMPORTANT !!!
# Devices that are not based on device template are not going to be migrated
# * TemplateID (openDCIM) == Hardware Model (Device42)
# Racks without height, are not going to be migrated
# ========================================================================



# ====== MySQL Source (openDCIM) ====== #
DB_IP     = ''
DB_PORT   = ''
DB_NAME   = ''
DB_USER   = ''
DB_PWD    = ''
# ====== Log settings  ==================== #
LOGFILE    = 'migration.log'
DEBUG      = True
# ====== Device42 upload settings ========= #
D42_USER   = ''
D42_PWD    = ''
D42_URL    = 'https://'
DRY_RUN    = False


def is_valid_ip(ip):
    """Validates IP addresses.
    """
    return is_valid_ipv4(ip) or is_valid_ipv6(ip)


def is_valid_ipv4(ip):
    """Validates IPv4 addresses.
    """
    pattern = re.compile(r"""
        ^
        (?:
          # Dotted variants:
          (?:
            # Decimal 1-255 (no leading 0's)
            [3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}
          |
            0x0*[0-9a-f]{1,2}  # Hexadecimal 0x0 - 0xFF (possible leading 0's)
          |
            0+[1-3]?[0-7]{0,2} # Octal 0 - 0377 (possible leading 0's)
          )
          (?:                  # Repeat 0-3 times, separated by a dot
            \.
            (?:
              [3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}
            |
              0x0*[0-9a-f]{1,2}
            |
              0+[1-3]?[0-7]{0,2}
            )
          ){0,3}
        |
          0x0*[0-9a-f]{1,8}    # Hexadecimal notation, 0x0 - 0xffffffff
        |
          0+[0-3]?[0-7]{0,10}  # Octal notation, 0 - 037777777777
        |
          # Decimal notation, 1-4294967295:
          429496729[0-5]|42949672[0-8]\d|4294967[01]\d\d|429496[0-6]\d{3}|
          42949[0-5]\d{4}|4294[0-8]\d{5}|429[0-3]\d{6}|42[0-8]\d{7}|
          4[01]\d{8}|[1-3]\d{0,9}|[4-9]\d{0,8}
        )
        $
    """, re.VERBOSE | re.IGNORECASE)
    return pattern.match(ip) is not None


def is_valid_ipv6(ip):
    """Validates IPv6 addresses.
    """
    pattern = re.compile(r"""
        ^
        \s*                         # Leading whitespace
        (?!.*::.*::)                # Only a single whildcard allowed
        (?:(?!:)|:(?=:))            # Colon iff it would be part of a wildcard
        (?:                         # Repeat 6 times:
            [0-9a-f]{0,4}           #   A group of at most four hexadecimal digits
            (?:(?<=::)|(?<!::):)    #   Colon unless preceeded by wildcard
        ){6}                        #
        (?:                         # Either
            [0-9a-f]{0,4}           #   Another group
            (?:(?<=::)|(?<!::):)    #   Colon unless preceeded by wildcard
            [0-9a-f]{0,4}           #   Last group
            (?: (?<=::)             #   Colon iff preceeded by exacly one colon
             |  (?<!:)              #
             |  (?<=:) (?<!::) :    #
             )                      # OR
         |                          #   A v4 address with NO leading zeros
            (?:25[0-4]|2[0-4]\d|1\d\d|[1-9]?\d)
            (?: \.
                (?:25[0-4]|2[0-4]\d|1\d\d|[1-9]?\d)
            ){3}
        )
        \s*                         # Trailing whitespace
        $
    """, re.VERBOSE | re.IGNORECASE | re.DOTALL)
    return pattern.match(ip) is not None

class Logger():
    def __init__(self, logfile):
        self.logfile  = LOGFILE

    def writer(self, msg):  
        if LOGFILE and LOGFILE != '':
            with codecs.open(self.logfile, 'a', encoding = 'utf-8') as f:
                f.write(msg.strip()+'\r\n')  # \r\n for notepad
        try:
            print msg
        except:
            print msg.encode('ascii', 'ignore') + ' # < non-ASCII chars detected! >'


class REST():
    def __init__(self):
        self.password = D42_PWD
        self.username = D42_USER
        self.base_url = D42_URL
        
        self.racks = json.loads(self.get_racks())

    def uploader(self, data, url):
        payload = data
        headers = {
            'Authorization': 'Basic ' + base64.b64encode(self.username + ':' + self.password),
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        r = requests.post(url, data=payload, headers=headers, verify=False)
        msg = 'Status code: %s' % str(r.status_code)
        logger.writer(msg)
        if DEBUG:
            msg =  unicode(payload)
            logger.writer(msg)
            msg = str(r.text)
            logger.writer(msg)

    def fetcher(self, url):
        headers = {
            'Authorization': 'Basic ' + base64.b64encode(self.username + ':' + self.password),
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        r = requests.get(url, headers=headers, verify=False)
        msg = 'Status code: %s' % str(r.status_code)
        logger.writer(msg)
        if DEBUG:
            msg = str(r.text)
            logger.writer(msg)
        return r.text


    def post_ip(self, data):
        if DRY_RUN == False:
            url = self.base_url+'/api/ip/'
            msg =  '\r\nPosting IP data to %s ' % url
            logger.writer(msg)
            self.uploader(data, url)
            
    def post_device(self, data):
        if DRY_RUN == False:
            url = self.base_url+'/api/1.0/device/'
            msg =  '\r\nPosting device data to %s ' % url
            logger.writer(msg)
            self.uploader(data, url)
            
    def post_location(self, data):
        if DRY_RUN == False:
            url = self.base_url+'/api/1.0/buildings/'
            msg =  '\r\nPosting location data to %s ' % url
            logger.writer(msg)
            self.uploader(data, url)
            
    def post_room(self, data):
        if DRY_RUN == False:
            url = self.base_url+'/api/1.0/rooms/'
            msg =  '\r\nPosting room data to %s ' % url
            logger.writer(msg)
            self.uploader(data, url)
            
    def post_rack(self, data):
        if DRY_RUN == False:
            url = self.base_url+'/api/1.0/racks/'
            msg =  '\r\nPosting rack data to %s ' % url
            logger.writer(msg)
            self.uploader(data, url)
    
    def post_pdu(self, data):
        if DRY_RUN == False:
            url = self.base_url+'/api/1.0/pdus/'
            msg =  '\r\nPosting PDU data to %s ' % url
            logger.writer(msg)
            self.uploader(data, url)

    def post_pdu_update(self, data):
        if DRY_RUN == False:
            url = self.base_url+'/api/1.0/pdus/rack/'
            msg =  '\r\nUpdating PDU data to %s ' % url
            logger.writer(msg)
            self.uploader(data, url)

    def post_pdu_model(self, data):
        if DRY_RUN == False:
            url = self.base_url+'/api/1.0/pdu_models/'
            msg =  '\r\nPosting PDU models from %s ' % url
            logger.writer(msg)
            self.uploader(data, url)

    def get_pdu_models(self):
        if DRY_RUN == False:
            url = self.base_url+'/api/1.0/pdu_models/'
            msg =  '\r\nFetching PDU models from %s ' % url
            logger.writer(msg)
            self.fetcher(url)
        
    def get_racks(self):
        if DRY_RUN == False:
            url = self.base_url+'/api/1.0/racks/'
            msg =  '\r\nFetching racks from %s ' % url
            logger.writer(msg)
        data = self.fetcher(url)
        return data

    def get_rack_by_name(self, name):
        for rack in self.racks['racks']:
            if rack['name'] == name:
                return rack
        return None

    def get_devices(self):
        if DRY_RUN == False:
            url = self.base_url+'/api/1.0/devices/'
            msg =  '\r\nFetching devices from %s ' % url
            logger.writer(msg)
            data = self.fetcher(url)
            return data

    def get_buildings(self):
        if DRY_RUN == False:
            url = self.base_url+'/api/1.0/buildings/'
            msg =  '\r\nFetching buildings from %s ' % url
            logger.writer(msg)
            data = self.fetcher(url)
            return data
            
    def get_rooms(self):
        if DRY_RUN == False:
            url = self.base_url+'/api/1.0/rooms/'
            msg =  '\r\nFetching rooms from %s ' % url
            logger.writer(msg)
            data = self.fetcher(url)
            return data

    def post_hardware(self, data):
        if DRY_RUN == False:
            url = self.base_url+'/api/1.0/hardwares/'
            msg =  '\r\nAdding hardware data to %s ' % url
            logger.writer(msg)
            self.uploader(data, url)
            
    def post_device2rack(self, data):
        if DRY_RUN == False:
            url = self.base_url+'/api/1.0/device/rack/'
            msg =  '\r\nAdding device to rack at %s ' % url
            logger.writer(msg)
            self.uploader(data, url)
            

class DB():
    def __init__(self):
        self.con = None
        self.tables = []
        self.datacenters_dcim = {}
        self.rooms_dcim = {}
        self.racks_dcim = {}
        self.manufacturers = {}
        
    def connect(self):
        self.con = sql.connect(host=DB_IP,  port=int(DB_PORT),  db=DB_NAME, user=DB_USER, passwd=DB_PWD)
        
    def get_ips(self):
        net = {}
        adrese = []
        if not self.con:
            self.connect()
        with self.con:
            cur = self.con.cursor()
            q = "SELECT PrimaryIP FROM fac_Device" 
            cur.execute(q)
            ips = cur.fetchall()
        for line in ips:
            if line[0] != '':
                ip = line[0]
                if is_valid_ip(ip):
                    net.update({'ipaddress':ip})
                    rest.post_ip(net)
                
        with self.con:
            cur = self.con.cursor()
            q = "SELECT IPAddress FROM fac_PowerDistribution" 
            cur.execute(q)
            ips = cur.fetchall()
        for line in ips:
            if line[0] != '':
                ip = line[0]
                if is_valid_ip(ip):
                    net.update({'ipaddress':ip})
                    rest.post_ip(net)
                

    def get_locations(self):
        building = {}
        if not self.con:
            self.connect()
        with self.con:
            cur = self.con.cursor()
            q = 'SELECT DatacenterID,Name,DeliveryAddress,Administrator FROM fac_DataCenter'
            cur.execute(q)
        data = cur.fetchall()
        
        for row in data:
            #building.clear()
            id, name, address, contact = row
            building.update({'name':name})
            building.update({'address':address})
            building.update({'contact_name':contact})
            self.datacenters_dcim.update({id:name})
            rest.post_location(building)
            
    def get_rooms(self): 
        rooms = {}
        # get building IDs from D42
        building_map = {}
        buildings = json.loads(rest.get_buildings())
        for building in buildings['buildings']:
            building_map.update({building['name']:building['building_id']})
        
        if not self.con:
            self.connect()
        with self.con:
            cur = self.con.cursor()
            q = 'SELECT ZoneID,DataCenterID,Description FROM fac_Zone'
            cur.execute(q)
        data = cur.fetchall()
        for row in data:
            room_id = row[0]
            dc  = row[1]
            name = row[2]
            dc = self.datacenters_dcim[dc]
            dc_id = building_map[dc]
            rooms.update({'name':name})
            rooms.update({'building_id':dc_id})
            self.rooms_dcim.update({room_id:name})
            rest.post_room(rooms)
            
            
    def get_racks(self):
         # get room IDs from D42
        room_map = {}
        rooms = json.loads(rest.get_rooms())
        for room in rooms['rooms']:
            room_map.update({room['name']:room['room_id']})

        if not self.con:
            self.connect()
        with self.con:
            cur = self.con.cursor()
            q = 'SELECT CabinetID,DatacenterID,Location,CabinetHeight,ZoneID FROM fac_Cabinet'  
            cur.execute(q)
        data = cur.fetchall()
        for row in data:
            rack = {}
            cid, did, name, height, room = row
            dc = self.datacenters_dcim[did]

            if height != 0:
                if name == '':
                    rnd = str(random.randrange(101,9999))
                    name = 'Unknown'+rnd
                if room > 0:
                    room = self.rooms_dcim[room]
                    room_id = room_map[room]
                    rack.update({'room_id':room_id})
                d42_rack = rest.get_rack_by_name(name)
                if d42_rack:
                    rack.update({'rack_id':d42_rack['rack_id']})
                rack.update({'name':name})
                rack.update({'size':height})
                rack.update({'building':did})
                self.racks_dcim.update({cid:name})
                rest.post_rack(rack)
           
    
    def get_datacenter_from_id(self, id):
        if not self.con:
            self.connect()
        with self.con:
            cur = self.con.cursor()
            q = 'SELECT Name FROM fac_DataCenter where DataCenterID = %d' % id
            cur.execute(q)
        data = cur.fetchone()
        return data
        
      
                
    def get_room_from_cabinet(self, cabinetID):
        if not self.con:
            self.connect()
        with self.con:
            cur = self.con.cursor()
            q = 'SELECT DatacenterID,Location,Model FROM fac_Cabinet where CabinetID = %d' % cabinetID
            cur.execute(q)
        data = cur.fetchone()
        id, room, model = data
        datacenter = self.get_datacenter_from_id(id)[0]
        return datacenter, room, model
        
        
    def get_vendor_and_model(self, id):
        self.get_manufacturers()
        hardware = {}
        
        if not self.con:
            self.connect()
        with self.con:
            cur = self.con.cursor()
            q = 'SELECT ManufacturerID, Model FROM fac_DeviceTemplate WHERE TemplateID=%d' % id
            cur.execute(q)
        data = cur.fetchone()
        try:
            id, model = data
        except TypeError:
            return None, None
        vendor = self.manufacturers[id]
        return vendor, model


    def get_devices(self):

        device        = {}
        device2rack = {}
        hardware     = {}
        if not self.con:
            self.connect()
        with self.con:
            cur = self.con.cursor()
            q = 'SELECT Label, SerialNo, AssetTag, PrimaryIP, Cabinet,Position,Height,DeviceType,HalfDepth,BackSide, TemplateID FROM fac_Device'
            cur.execute(q)
        data = cur.fetchall()
        for row in data:
            name, serial_no, comment, ip, rackid, position, size, devicetype, halfdepth, backside, tid = row
            datacenter, room, rack_name = self.get_room_from_cabinet(rackid)
            vendor, model = self.get_vendor_and_model(tid)

            # post device
            device.update({'name':name})
            device.update({'manufacturer':vendor})
            device.update({'hardware':model})
            device.update({'notes':comment})

            if devicetype.lower() == 'cdu':
                rest.post_pdu(device)
            else:
                device.update({'serial_no':serial_no})
                if devicetype.lower() == 'switch':
                    device.update({'is_it_switch':'yes'})
                rest.post_device(device)
            
            if rackid:
                #post device 2 rack
                device2rack.update({'device':name})
                device2rack.update({'size':size})
                #device2rack.update({'building':datacenter})
                #device2rack.update({'room':room})
                device2rack.update({'rack': self.racks_dcim[rackid]})
                device2rack.update({'start_at':position-1})
                if backside == '1':
                    device2rack.update({'orientation':'back'})
                rest.post_device2rack(device2rack)
    
        
    def get_manufacturers(self):
        if not self.con:
            self.connect()
        with self.con:
            cur = self.con.cursor()
            q = 'SELECT ManufacturerID, Name from fac_Manufacturer'
            cur.execute(q)
        data = cur.fetchall()
        for row in data:
            id, vendor = row
            self.manufacturers.update({id:vendor})
            
    def get_depth(self, id):
        if not self.con:
            self.connect()
        with self.con:
            cur = self.con.cursor()
            q = 'SELECT HalfDepth FROM fac_Device WHERE TemplateID=%d' % id
            cur.execute(q)
        data = cur.fetchone()
        d = data[0]
        if d == 0:
            return 1
        elif d ==1:
            return 2
        
    def get_hardware(self):
        self.get_manufacturers()
        hardware = {}
        
        if not self.con:
            self.connect()
        with self.con:
            cur = self.con.cursor()
            q = 'SELECT TemplateID, ManufacturerID, Model, Height, Wattage, DeviceType, FrontPictureFile, RearPictureFile FROM fac_DeviceTemplate'
            cur.execute(q)
        data = cur.fetchall()
        for row in data:
            TemplateID, ManufacturerID, Model, Height, Wattage, DeviceType, FrontPictureFile, RearPictureFile = row
            
            try:
                depth = self.get_depth(TemplateID)
            except TypeError:
                continue

            vendor = self.manufacturers[ManufacturerID]


            hardware.update({'name':Model})
            hardware.update({'size':Height})
            hardware.update({'depth':depth})
            hardware.update({'manufacturer':vendor})
            hardware.update({'watts':Wattage})
            if DeviceType.lower() == 'cdu':
                rest.post_pdu_model(hardware)
            else:
                hardware.update({'type':1})
                ''' 
                # to do 
                if FrontPictureFile:
                hardware.update({'front_image':FrontPictureFile})
                if RearPictureFile:
                hardware.update({'back_image':RearPictureFile})
                '''
                rest.post_hardware(hardware)

def main():
    db = DB()
    
    db.get_ips()
    db.get_locations()
    db.get_rooms()
    db.get_racks()
    db.get_hardware()
    db.get_devices()
    
    
if __name__ == '__main__':
    logger = Logger(LOGFILE)
    rest = REST()
    main()
    print '\n[!] Done!'
    sys.exit()
