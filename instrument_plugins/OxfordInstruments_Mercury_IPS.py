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
        self._visainstrument = visa.instrument(self._address,timeout=100)
        self._values = {}
        self._visainstrument.term_chars = '\r\n'

        self._x = 0.
        self._y = 0.
        self._z = 0.

        self._buffer_x = 0.
        self._buffer_y = 0.
        self._buffer_z = 0.
        
        self._rate_x = 0.2
        self._rate_y = 0.2
        self._rate_z = 0.2
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
            'CYL' : "Cylindrical",
            'CART' : "Cartesian",
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

        self.add_parameter('target_vectorXYZ', type=types.TupleType,
            #READ:SYS:VRM:TVEC
            flags=Instrument.FLAG_SET)

        self.add_parameter('target_vector_from_buffer', type=types.FloatType,
            #READ:SYS:VRM:TVEC
            flags=Instrument.FLAG_SET)

        self.add_parameter('buffer', type=types.FloatType,
            #READ:SYS:VRM:TVEC
            flags=Instrument.FLAG_GETSET,
            channels=('X', 'Y', 'Z'))

        
        self.add_parameter('rate', type=types.FloatType,
            #Internal rate of sweeping
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
        self.get_rateX()
        self.get_rateY()
        self.get_rateZ()
        #self.get_target_vectorXYZ()
        # self.get_vectorXYZ()
        self.get_vectorX()
        self.get_vectorY()
        self.get_vectorZ()
        self.get_sweep_mode()
        self.get_activity()
        # self.get_buffer_x()
        # self.get_buffer_y()
        # self.get_buffer_z()

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
        res = (result.replace('STAT:SYS:VRM:VECT:',''))
        found = None
        coordsys = self.do_get_coordinatesys()
        if coordsys == 'CART':
            tesla = re.compile(r'^\[(.*)T (.*)T (.*)T\]$')
            found = tesla.findall(res)
        elif coordsys == 'SPH':
            tesla = re.compile(r'^\[(.*)T (.*)rad (.*)rad\]$')
            found = tesla.findall(res)
        elif coordsys == 'CYL':
            tesla = re.compile(r'^\[(.*)T (.*)rad (.*)T\]$')
            found = tesla.findall(res)
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

    def do_get_target_vectorXYZ(self):
        logging.info(__name__ + ' : Read current coordinate system')
        result = self._execute('READ:SYS:VRM:TVEC')
        res = (result.replace('STAT:SYS:VRM:TVEC:',''))
        
        found = None
        
        print self.do_get_coordinatesys()
        print res
        coordsys = self.do_get_coordinatesys()
        if coordsys == 'CART':
            tesla = re.compile(r'^\[(.*)T (.*)T (.*)T\]$')
            found = tesla.findall(res)
        elif coordsys == 'SPH':
            tesla = re.compile(r'^\[(.*)T (.*)rad (.*)rad\]$')
            found = tesla.findall(res)
        elif coordsys == 'CYL':
            tesla = re.compile(r'^\[(.*)T (.*)rad (.*)T\]$')
            found = tesla.findall(res)
        else:
            logging.info(__name__ + ' : Other than cartesian not yet supported')
            return
        self._x = float(found[0][0])
        self._y = float(found[0][1])
        self._z = float(found[0][2])
        selfxyz = [self._x,self._y,self._z]
        print found
        return selfxyz

        
    def do_get_target_vector(self,channel):
        logging.info(__name__ + ' : Read current coordinate system')
        result = self._execute('READ:SYS:VRM:TVEC')
        res = (result.replace('STAT:SYS:VRM:TVEC:',''))
        
        found = None
        
        print self.do_get_coordinatesys()
        print res
        coordsys = self.do_get_coordinatesys()
        if coordsys == 'CART':
            tesla = re.compile(r'^\[(.*)T (.*)T (.*)T\]$')
            found = tesla.findall(res)
        elif coordsys == 'SPH':
            tesla = re.compile(r'^\[(.*)T (.*)rad (.*)rad\]$')
            found = tesla.findall(res)
        elif coordsys == 'CYL':
            tesla = re.compile(r'^\[(.*)T (.*)rad (.*)T\]$')
            found = tesla.findall(res)
        else:
            logging.info(__name__ + ' : Other than cartesian not yet supported')
            return
        #rho,theta,z, cyl
        #[0.0000T 0.00000rad 0.0000T]
        #r theta phi, spherical 
        #[0.0000T 0.00000rad 0.00000rad]
        self._x = float(found[0][0])
        self._y = float(found[0][1])
        self._z = float(found[0][2])

        print found
        if channel=='X':
            return self._x
        if channel=='Y':
            return self._y
        if channel=='Z':
            return self._z
        
    def do_get_max_field_sweep(self):
        logging.info(__name__ + ' : Read current coordinate system')
        result = self._execute('READ:SYS:VRM:RFMX')
        return (result.replace('STAT:SYS:VRM:RFMX:',''))
    def do_get_sweep_mode(self):
        logging.info(__name__ + ' : Read current coordinate system')
        result = self._execute('READ:SYS:VRM:RVST:MODE')
        return (result.replace('STAT:SYS:VRM:RVST:MODE:',''))
    # def do_get_setpoint(self):
        # logging.info(__name__ + ' : Read setpoint')
        # result = self._execute('READ:SYS:VRM:VSET')
        # return (result.replace('STAT:SYS:VRM:VSET:',''))        
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
    # def do_set_setpoint(self,val):
        # logging.info(__name__ + ' : Set ')
        # mode = 'RATE'
        # rate = 0.1
        # tesla = val
        # print tesla
        # command = 'SET:SYS:VRM:RVST:MODE:%s:RATE:%.6f:VSET:[0 0 %.3f]'%(mode,rate,tesla)

        # result = self._execute(command)
        # print result
        
        # return (result.replace('SET:SYS:VRM:VSET:',''))
    def do_set_activity(self,val):
        while self.get_activity() != 'IDLE':
            sleep(1.0)
        logging.info(__name__ + ' : Set ')
        result = self._execute('SET:SYS:VRM:ACTN:%s' % val)
        # while self.get_activity() != 'IDLE':
            # print 'Waiting for magnet to become IDLE'
            # sleep(1.0)
        return (result.replace('STAT:SET:SYS:VRM:ACTN:',''))

    def do_set_rate(self, val, channel):
        if channel =='X':
            self._rate_x = val
        if channel =='Y':
            self._rate_y = val
        if channel =='Z':
            self._rate_z = val
    def do_get_rate(self, channel):
        if channel =='X':
            return self._rate_x
        if channel =='Y':
            return self._rate_y
        if channel =='Z':
            return self._rate_z

    def do_set_buffer(self, val, channel):
        if channel =='X':
            self._buffer_x = val
        if channel =='Y':
            self._buffer_y = val
        if channel =='Z':
            self._buffer_z = val

    def do_get_buffer(self, channel):
        if channel =='X':
            return self._buffer_x
        if channel =='Y':
            return self._buffer_y
        if channel =='Z':
            return self._buffer_z

    def do_set_target_vectorXYZ(self,val):
        while self.get_activity() != 'IDLE':
            print 'Waiting for magnet to become IDLE'
            sleep(1.0)
        print val
        logging.info(__name__ + ' : Read current coordinate system')
        command=[]
        mode = 'RATE'
        rate =0.2
        coordsys = self.get_coordinatesys()
        if coordsys == 'CART':
            command = 'SET:SYS:VRM:RVST:MODE:%s:RATE:%.6f:VSET:[%.6f %.6f %.6f]'%(mode,self._rate_x,val[0],val[1],val[2])
        elif coordsys == 'SPH':
            command = 'SET:SYS:VRM:RVST:MODE:%s:RATE:%.6f:VSET:[%.6f %.6f %.6f]'%(mode,rate,val[0],val[1],val[2])
        result = self._execute(command)

    def do_set_target_vector_from_buffer(self,dummy):
        while self.get_activity() != 'IDLE':
            print 'Waiting for magnet to become IDLE'
            sleep(1.0)
        val = [0,0,0]
        print self.get_bufferX()
        val[0] = self.get_bufferX()
        val[1] = self.get_bufferY()
        val[2] = self.get_bufferZ()
        print val
        logging.info(__name__ + ' : Read current coordinate system')
        command=[]
        mode = 'RATE'
        rate =0.2
        coordsys = self.get_coordinatesys()
        if coordsys == 'CART':
            command = 'SET:SYS:VRM:RVST:MODE:%s:RATE:%.6f:VSET:[%.6f %.6f %.6f]'%(mode,self._rate_x,val[0],val[1],val[2])
        elif coordsys == 'SPH':
            command = 'SET:SYS:VRM:RVST:MODE:%s:RATE:%.6f:VSET:[%.6f %.6f %.6f]'%(mode,rate,val[0],val[1],val[2])
        result = self._execute(command)

    def do_set_target_vector(self,val,channel):
        while self.get_activity() != 'IDLE':
            print 'Waiting for magnet to become IDLE'
            sleep(1.0)
        logging.info(__name__ + ' : Read current coordinate system')
        
        
        command=[]
        mode = 'RATE'
        rate =0.1


        coordsys = self.get_coordinatesys()
        if coordsys == 'CART':
            if channel=='X':
                self._x = val
                command = 'SET:SYS:VRM:RVST:MODE:%s:RATE:%.6f:VSET:[%.6f %.6f %.6f]'%(mode,self._rate_x,val,self._y,self._z)
            if channel=='Y':
                self._y = val
                command = 'SET:SYS:VRM:RVST:MODE:%s:RATE:%.6f:VSET:[%.6f %.6f %.6f]'%(mode,self._rate_y,self._x,val,self._z)
            if channel=='Z':
                self._z = val
                command = 'SET:SYS:VRM:RVST:MODE:%s:RATE:%.6f:VSET:[%.6f %.6f %.6f]'%(mode,self._rate_z,self._x,self._y,val)
        elif coordsys == 'SPH':
            if channel=='X':
                command = 'SET:SYS:VRM:RVST:MODE:%s:RATE:%.6f:VSET:[%.6f %.6f %.6f]'%(mode,rate,val,y,z)
            if channel=='Y':
                command = 'SET:SYS:VRM:RVST:MODE:%s:RATE:%.6f:VSET:[%.6f %.6f %.6f]'%(mode,rate,x,val,z)
            if channel=='Z':
                command = 'SET:SYS:VRM:RVST:MODE:%s:RATE:%.6f:VSET:[%.6f %.6f %.6f]'%(mode,rate,x,y,val)
                 
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
