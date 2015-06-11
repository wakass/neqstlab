# OxfordInstruments_OxfordInstruments_Mercury_IPS.py class, to perform the communication between the Wrapper and the device
# based on IPS120

# WakA WakA, 2012
# old class
# Guenevere Prawiroatmodjo <guen@vvtp.tudelft.nl>, 2009
# Pieter de Groot <pieterdegroot@gmail.com>, 2009
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from instrument import Instrument
from time import time, sleep
#import visa
import pyvisa.visa as visa
import types
import logging

import re

class OxfordInstruments_Mercury_IPS(Instrument):
    '''
    This is the python driver for the Oxford Instruments IPS 120 Magnet Power Supply

    Usage:
    Initialize with
    <name> = instruments.create('name', 'OxfordInstruments_Mercury_IPS', address='<Instrument address>')
    <Instrument address> = TCPIP::10.89.193.8::33576::SOCKET
    No ISOBUS, assumed VRM program running on specified ip addres

    Note: Since the ISOBUS allows for several instruments to be managed in parallel, the command
    which is sent to the device starts with '@n', where n is the ISOBUS instrument number.

    '''
#TODO: auto update script
#TODO: get doesn't always update the wrapper! (e.g. when input is an int and output is a string)
    def __del__(self):
        print 'indel'
        try:
            print 'being delled'
            self._visainstrument.close()
        except:
            pass
    def __exit__(self):
        self.__del__()
        
    def __reload__(self,dict):
        print dict._visainstrument
    def __init__(self, name, address):
        '''
        Initializes the Oxford Instruments IPS 120 Magnet Power Supply.

        Input:
            name (string)    : name of the instrument
            address (string) : instrument address
            number (int)     : ISOBUS instrument number

        Output:
            None
        '''
        logging.debug(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])


        self._address = address
        self._visainstrument = visa.instrument(self._address,timeout=20)
        self._values = {}
        self._visainstrument.term_chars = '\r\n'

        #Add parameters
        
        #x,y,z -> enter setpoint
        #coordinate system
        #sweep mode: rate overall,time to setpoint, fast as possible
        #to setpoint
        #hold
        #to zero
        
        
        self.add_parameter('coordinatesys', type=types.StringType,
            #READ:SYS:VRM:COO
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            format_map = {
            'CART' : "Cartresian",
            'CYL' : "Cyclindrical",
            'SPH' : "Spherical",
            })
            
        # # channels with prefix
        # self.add_parameter('magn', type=types.FloatType,
                # flags=Instrument.FLAG_GETSET,
                # channels=('X', 'Y', 'Z'))
                
        self.add_parameter('vector', type=types.StringType,
            #dependent on coordinate system
            #get current magnet vector
            #READ:SYS:VRM:VECT
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            channels=('X', 'Y', 'Z'))
        
        self.add_parameter('target_vector', type=types.FloatType,
            #READ:SYS:VRM:TVEC
            flags=Instrument.FLAG_GETSET,
            channels=('X', 'Y', 'Z'))
        
        self.add_parameter('max_field_sweep', type=types.StringType,
            #max field sweep
            #[dBx/dt dBy/dt dBz/dt], tesla/minute
            #READ:SYS:VRM:RFMX
            flags=Instrument.FLAG_GET)
        
        self.add_parameter('sweep_mode', type=types.StringType,
            #READ:SYS:VRM:RVST:MODE 
            #return string+ asap | time | rate
            flags=Instrument.FLAG_GET)
        
        
        
        #magnet setpoints
        #READ:SYS:VRM:VSET
        #self.add_parameter('setpoint', type=types.FloatType,
        #    flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET)
            

        self.add_parameter('activity', type=types.StringType,
            #READ:SYS:VRM:ACTN 
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            format_map = {
            'RTOS' : "Sweep to setpoint",
            'RTOZ' : "Sweep to zero",
            'HOLD' : "Hold",
            'IDLE' : 'Idle',
            'PERS' : 'Make persistent',
            'NPERS': 'Make non-persistent',
            'SAFE' : "Safe"})
            


        # Add functions
        self.add_function('get_all')
        self.get_all()

    def get_all(self):
        '''
        Reads all implemented parameters from the instrument,
        and updates the wrapper.

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : reading all settings from instrument')
        self.get_coordinatesys()
        #self.get_vector()
        self.get_target_vectorX()
        self.get_target_vectorY()
        self.get_target_vectorZ()
        self.get_vectorX()
        self.get_vectorY()
        self.get_vectorZ()
        
        
        # self.get_max_field_sweep()
        # self.get_sweep_mode()
        # self.get_setpoint()
        self.get_activity()
        # self.get_mode()
        # self.get_activity()


    # Functions
    def _execute(self, message):
        '''
        Write a command to the device

        Input:
            message (str) : write command for the device

        Output:
            None
        '''
        logging.info(__name__ + ' : Send the following command to the device: %s' % message)
        #print __name__ + ' : Send the following command to the device: %s' % message
        #self._visainstrument.write('@%s%s' % (self._number, message))
        #sleep(20e-3) # wait for the device to be able to respond
        #result = self._visainstrument.read()
        result = self._visainstrument.ask(message)
        if result.find('?') >= 0:
            print "Error: Command %s not recognized" % message
        else:
            return result

    def identify(self):
        '''
        Identify the device

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Identify the device')
        return self._execute('V')

    def examine(self):
        '''
        Examine the status of the device

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Examine status')

        #print 'System Status: '
        #print self.get_system_status()

        print 'Activity: '
        print self.get_activity()

        print 'Mode: '
        print self.get_sweep_mode()


    def remote(self):
        '''
        Set control to remote & locked

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Set control to remote & locked')
        self.set_remote_status(3)

    def local(self):
        '''
        Set control to local & locked

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Set control to local & locked')
        self.set_remote_status(0)

 
    def do_get_coordinatesys(self):
        '''
        Get current coor system

        Input:
            None

        Output:
            result (string) : Read current coordinate system
        '''
        logging.info(__name__ + ' : Read current coordinate system')
        result = self._execute('READ:SYS:VRM:COO')
        return (result.replace('STAT:SYS:VRM:COO:',''))
     
    def do_get_vector(self,channel):
        logging.info(__name__ + ' : Read current coordinate system')
        result = self._execute('READ:SYS:VRM:VECT')
        parsed = (result.replace('STAT:SYS:VRM:VECT:',''))
        found = None
        if self.do_get_coordinatesys() == 'CART':
            tesla = re.compile(r'^\[(.*)T (.*)T (.*)T\]$')
            found = tesla.findall(parsed)
        else:
            logging.info(__name__ + ' : Other than cartesian not yet supported')
        #rho,theta,z, cyl
        #[0.0000T 0.00000rad 0.0000T]
        #r theta phi, spherical 
        #[0.0000T 0.00000rad 0.00000rad]
        

        print found
        if channel=='X':
            return found[0][0]
        if channel=='Y':
            return found[0][1]
        if channel=='Z':
            return found[0][2]
        
    def do_get_target_vector(self,channel):
        logging.info(__name__ + ' : Read current coordinate system')
        result = self._execute('READ:SYS:VRM:TVEC')
        res = (result.replace('STAT:SYS:VRM:TVEC:',''))
        
        found = None
        if self.do_get_coordinatesys() == 'CART':
            tesla = re.compile(r'^\[(.*)T (.*)T (.*)T\]$')
            found = tesla.findall(res)
        else:
            logging.info(__name__ + ' : Other than cartesian not yet supported')
            return
        #rho,theta,z, cyl
        #[0.0000T 0.00000rad 0.0000T]
        #r theta phi, spherical 
        #[0.0000T 0.00000rad 0.00000rad]
        
        print found
        if channel=='X':
            return found[0][0]
        if channel=='Y':
            return found[0][1]
        if channel=='Z':
            return found[0][2]
        
    def do_get_max_field_sweep(self):
        logging.info(__name__ + ' : Read current coordinate system')
        result = self._execute('READ:SYS:VRM:RFMX')
        return (result.replace('STAT:SYS:VRM:RFMX:',''))
    def do_get_sweep_mode(self):
        logging.info(__name__ + ' : Read current coordinate system')
        result = self._execute('READ:SYS:VRM:RVST:MODE')
        return (result.replace('STAT:SYS:VRM:RVST:MODE:',''))
    def do_get_setpoint(self):
        logging.info(__name__ + ' : Read setpoint')
        result = self._execute('READ:SYS:VRM:VSET')
        return (result.replace('STAT:SYS:VRM:VSET:',''))        
    def do_get_activity(self):
        logging.info(__name__ + ' : Read activity of magnet')
        result = self._execute('READ:SYS:VRM:ACTN')
        return (result.replace('STAT:SYS:VRM:ACTN:',''))
    # def do_set_(self):
        # logging.info(__name__ + ' : Set ')
        # result = self._execute('')
        # return (result.replace('SET:SYS:VRM::',''))
    def do_set_coordinatesys(self,val):
        logging.info(__name__ + ' : Set ')
        result = self._execute('SET:SYS:VRM:COO:%s' % val)
        return (result.replace('STAT:SYS:VRM:COO:',''))
    def do_set_vector(self,val):
        logging.info(__name__ + ' : Set ')
        result = self._execute('SET:SYS:VRM:VECT:%s' % val)
        return (result.replace('SET:SYS:VRM:VECT:',''))
    def do_set_setpoint(self,val):
        logging.info(__name__ + ' : Set ')
        mode = 'RATE'
        rate = 0.2
        tesla = val
        print tesla
        command = 'SET:SYS:VRM:RVST:MODE:%s:RATE:%.6f:VSET:[0 0 %.3f]'%(mode,rate,tesla)

        result = self._execute(command)
        print result
        
        return (result.replace('SET:SYS:VRM:VSET:',''))
    def do_set_activity(self,val):
        logging.info(__name__ + ' : Set ')
        result = self._execute('SET:SYS:VRM:ACTN:%s' % val)
        return (result.replace('STAT:SET:SYS:VRM:ACTN:',''))
    
    def do_set_target_vector(self,val,channel):
        logging.info(__name__ + ' : Read current coordinate system')
        
        
        command=[]
        mode = 'RATE'
        rate =0.2

        #x = self.get_target_vectorX()
        #y = self.get_target_vectorY()
        #z = self.get_target_vectorZ()
        x=self._x
        y=self._y
        if channel=='X':
            command = 'SET:SYS:VRM:RVST:MODE:%s:RATE:%.6f:VSET:[%.3f %.3f %.3f]'%(mode,rate,val,y,z)
        if channel=='Y':
            command = 'SET:SYS:VRM:RVST:MODE:%s:RATE:%.6f:VSET:[%.3f %.3f %.3f]'%(mode,rate,x,val,z)
        if channel=='Z':
            command = 'SET:SYS:VRM:RVST:MODE:%s:RATE:%.6f:VSET:[%.3f %.3f %.3f]'%(mode,rate,x,y,val)
            
        result = self._execute(command)
       # print result
    
	# def get_changed(self):
        # print "Current: "
        # print self.get_current()
        # print "Field: "
        # print self.get_field()
        # print "Magnet current: "
        # print self.get_magnet_current()
        # print "Heater current: "
        # print self.get_heater_current()
        # print "Mode: "
        # print self.get_mode()
