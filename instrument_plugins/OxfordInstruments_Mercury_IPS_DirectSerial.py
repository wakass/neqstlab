# OxfordInstruments_OxfordInstruments_Mercury_IPS.py class, to perform the communication between the Wrapper and the device
# based on IPS120

# Joost Riddderbos, 2017
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

class OxfordInstruments_Mercury_IPS_DirectSerial(Instrument):
    '''
    This is the python driver for the Oxford Instruments IPS 120 Magnet Power Supply

    Usage:
    Initialize with
    <name> = instruments.create('name', 'OxfordInstruments_Mercury_IPSDirectSerial', address='<Instrument address>')
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
            print 'Being deleted'
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
        self._visainstrument = visa.instrument(self._address,timeout=10)
        self._values = {}
        self._visainstrument.term_chars = '\r\n'

        self._waitforcompletion_x = 'Off' 
        self._waitforcompletion_y = 'Off' 
        self._waitforcompletion_z = 'Off' 
                
        self.add_parameter('vector', type=types.FloatType,
            flags=Instrument.FLAG_GET, format='%.6f',
            channels=('X', 'Y', 'Z'))

        self.add_parameter('vectorcurr', type=types.FloatType,
            flags=Instrument.FLAG_GET, format='%.6f',
            channels=('X', 'Y', 'Z'))

        self.add_parameter('target_vectorcurr', type=types.FloatType,
            flags=Instrument.FLAG_GETSET, format='%.6f',
            channels=('X', 'Y', 'Z'))

        self.add_parameter('target_vector', type=types.FloatType,
            flags=Instrument.FLAG_GETSET, format='%.6f',
            channels=('X', 'Y', 'Z'))

        self.add_parameter('rate', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            channels=('X', 'Y', 'Z'))

        self.add_parameter('ratecurr', type=types.FloatType,
            flags=Instrument.FLAG_GETSET,
            channels=('X', 'Y', 'Z'))

        self.add_parameter('switch_heater', type=types.StringType,
            flags=Instrument.FLAG_GETSET,
            format_map = {
            'ON' : "On",
            'OFF' : "Off",
            },
            channels=('Z'))

        self.add_parameter('waitforsweepcompletion', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            format_map = {
            'On' : "On",
            'Off' : "Off",
            },
            channels=('X', 'Y', 'Z'))

        self.add_parameter('activity', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            format_map = {
            'HOLD' : "Hold",
            'RTOS' : "Ramp to setpoint",
            'RTOZ' : "Ramp to zero",
            'CLMP' : "Clamp if current = 0",
            },
            channels=('X', 'Y', 'Z'))

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
        self.get_rateX()
        self.get_rateY()
        self.get_rateZ()
        self.get_ratecurrX()
        self.get_ratecurrY()
        self.get_ratecurrZ()
        self.get_vectorX()
        self.get_vectorY()
        self.get_vectorZ()
        self.get_vectorcurrX()
        self.get_vectorcurrY()
        self.get_vectorcurrZ()
        self.get_target_vectorcurrX()
        self.get_target_vectorcurrY()
        self.get_target_vectorcurrZ()
        self.get_activityX()
        self.get_activityY()
        self.get_activityZ()
        self.get_target_vectorX()
        self.get_target_vectorY()
        self.get_target_vectorZ()
        self.get_vectorX()
        self.get_vectorY()
        self.get_vectorZ()
        self.get_waitforsweepcompletionX()
        self.get_waitforsweepcompletionY()
        self.get_waitforsweepcompletionZ()
        # self.do_get_switch_heaterX()
        # self.do_get_switch_heaterY()
        self.get_switch_heaterZ()

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

        print 'Activity: '
        print self.get_activity()

    def do_get_vector(self,channel):
        SCPIstring = 'READ:DEV:GRP' + channel + ':PSU:SIG:FLD?'
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:DEV:GRP' + channel  + ':PSU:SIG:FLD:',''))
        res = res[:-1]
        return res

    def do_get_activity(self, channel):
        SCPIstring = 'READ:DEV:GRP' + channel + ':PSU:ACTN?'
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:DEV:GRP' + channel  + ':PSU:ACTN:',''))
        return res

    def do_set_activity(self, val, channel):
        SCPIstring = 'SET:DEV:GRP' + channel + ':PSU:ACTN:' + val
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:DEV:GRP' + channel  + ':PSU:ACTN:',''))
        print self._waitforcompletion_x

        if channel == 'X' and self._waitforcompletion_x == 'On':
            while self.get_activityX() != 'HOLD':
                sleep(0.1)
        if channel == 'Y' and self._waitforcompletion_y == 'On':
            while self.get_activityY() != 'HOLD':
                sleep(0.1)
        if channel == 'Z' and self._waitforcompletion_z == 'On':
            while self.get_activityZ() != 'HOLD':
                sleep(0.1)
        self.get_vectorX()
        self.get_vectorY()
        self.get_vectorZ()
        self.get_vectorcurrX()
        self.get_vectorcurrY()
        self.get_vectorcurrZ()
        return res

    def do_get_rate(self, channel):
        SCPIstring = 'READ:DEV:GRP' + channel + ':PSU:SIG:RFST?'
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:DEV:GRP' + channel  + ':PSU:SIG:RFST:',''))
        res = res[:-3]
        return res

    def do_set_rate(self, val, channel):
        SCPIstring = 'SET:DEV:GRP' + channel + ':PSU:SIG:RFST:' + str(val)
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:DEV:GRP' + channel  + ':PSU:SIG:RFST:',''))
        res = res[:-3]
        sleep(1.0)
        self.get_ratecurrX()
        self.get_ratecurrY()
        self.get_ratecurrZ()
        return res

    def do_get_ratecurr(self, channel):
        SCPIstring = 'READ:DEV:GRP' + channel + ':PSU:SIG:RCST?'
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:DEV:GRP' + channel  + ':PSU:SIG:RCST:',''))
        res = res[:-3]
        return res

    def do_get_vectorcurr(self,channel):
        SCPIstring = 'READ:DEV:GRP' + channel + ':PSU:SIG:CURR'
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:DEV:GRP' + channel  + ':PSU:SIG:CURR:',''))
        res = res[:-1]
        return res

    def do_set_ratecurr(self, val, channel):
        SCPIstring = 'SET:DEV:GRP' + channel + ':PSU:SIG:RCST:' + str(val)
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:DEV:GRP' + channel  + ':PSU:SIG:RCST:',''))
        res = res[:-3]
        sleep(1.0)
        self.get_rateX()
        self.get_rateY()
        self.get_rateZ()
        return res


    def do_get_target_vector(self,channel):
        SCPIstring = 'READ:DEV:GRP' + channel + ':PSU:SIG:FSET?'
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:DEV:GRP' + channel  + ':PSU:SIG:FSET:',''))
        res = res[:-1]
        return res

    def do_set_target_vector(self,val,channel):
        SCPIstring = 'SET:DEV:GRP' + channel + ':PSU:SIG:FSET:' + str(val)
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:DEV:GRP' + channel  + ':PSU:SIG:FSET:',''))
        if channel == 'X':
            while self.get_activityX() != 'HOLD':
                sleep(0.1)
        if channel == 'Y':
            while self.get_activityY() != 'HOLD':
                sleep(0.1)
        if channel == 'Z':
            while self.get_activityZ() != 'HOLD':
                sleep(0.1)
        sleep(1.0) #Important! Mercury iPS needs this time to process the new setpoint
        self.get_target_vectorcurrX()
        self.get_target_vectorcurrY()
        self.get_target_vectorcurrZ()
        return res

    def do_get_target_vectorcurr(self,channel):
        SCPIstring = 'READ:DEV:GRP' + channel + ':PSU:SIG:CSET?'
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:DEV:GRP' + channel  + ':PSU:SIG:CSET:',''))
        res = res[:-1]
        return res

    def do_set_target_vectorcurr(self,val,channel):
        SCPIstring = 'SET:DEV:GRP' + channel + ':PSU:SIG:CSET:' + str(val)
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:DEV:GRP' + channel  + ':PSU:SIG:CSET:',''))
        if channel == 'X':
            while self.get_activityX() != 'HOLD':
                sleep(0.1)
        if channel == 'Y':
            while self.get_activityY() != 'HOLD':
                sleep(0.1)
        if channel == 'Z':
            while self.get_activityZ() != 'HOLD':
                sleep(0.1)
        sleep(1.0) #Important! Mercury iPS needs this time to process the new setpoint
        self.get_target_vectorX()
        self.get_target_vectorY()
        self.get_target_vectorZ()
        return res

    def do_set_waitforsweepcompletion(self,val,channel):
        if channel == 'X':
            self._waitforcompletion_x = val
        if channel == 'Y':
            self._waitforcompletion_y = val
        if channel == 'Z':
            self._waitforcompletion_z = val
        return res

    def do_get_waitforsweepcompletion(self,channel):
        if channel == 'X':
            return self._waitforcompletion_x
        if channel == 'Y':
            return self._waitforcompletion_y
        if channel == 'Z':
            return self._waitforcompletion_z
        return res

    def do_get_switch_heater(self,channel):
        SCPIstring = 'READ:DEV:GRP' + channel + ':PSU:SIG:SWHT?'
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:DEV:GRP' + channel  + ':PSU:SIG:SWHT:',''))
        return res

    def do_set_switch_heater(self,val,channel):
        SCPIstring = 'SET:DEV:GRP' + channel + ':PSU:SIG:SWHT:' + str(val)
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:DEV:GRP' + channel  + ':PSU:SIG:SWHT:',''))
        sleep(1.0) #Important! Mercury iPS needs this time to process the new setpoint
        return res
