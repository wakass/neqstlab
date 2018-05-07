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

class OxfordInstruments_Triton200_Temperature(Instrument):
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

        self.add_parameter('temperature', type=types.FloatType,
            flags=Instrument.FLAG_GET, format='%.6f',
            channels=('1', '2', '3', '4', '5', '6', '13'))

        self.add_parameter('mixingchamber_setpoint', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET, format='%.6f'
            )

        self.add_parameter('mixingchamber_temp', type=types.FloatType,
            flags=Instrument.FLAG_GET, format='%.6f'
            )

        self.add_parameter('autotempcontrol', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET, format='%.6f'
            )

        self.add_parameter('closedPID', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            format_map = {
            'ON' : "On",
            'OFF' : "Off",
            })

        self.add_parameter('heater_power', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET, format='%.4f'
            )

        self.add_parameter('turbo', type=types.StringType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            format_map = {
            'ON' : "On",
            'OFF' : "Off",
            })

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
        # self.get_rateX()
        # self.get_rateY()
        # self.get_rateZ()
        # self.get_ratecurrX()
        # self.get_ratecurrY()
        # self.get_ratecurrZ()
        # self.get_vectorX()
        # self.get_vectorY()
        # self.get_vectorZ()
        # self.get_vectorcurrX()
        # self.get_vectorcurrY()
        # self.get_vectorcurrZ()
        # self.get_target_vectorcurrX()
        # self.get_target_vectorcurrY()
        # self.get_target_vectorcurrZ()
        # self.get_activityX()
        # self.get_activityY()
        # self.get_activityZ()
        # self.get_target_vectorX()
        # self.get_target_vectorY()
        # self.get_target_vectorZ()
        # self.get_vectorX()
        # self.get_vectorY()
        # self.get_vectorZ()
        # self.get_waitforsweepcompletionX()
        # self.get_waitforsweepcompletionY()
        # self.get_waitforsweepcompletionZ()
        # self.do_get_switch_heaterX()
        # self.do_get_switch_heaterY()
        # self.get_switch_heaterZ()

        self.get_temperature1()
        self.get_temperature2()
        self.get_temperature3()
        self.get_temperature4()
        self.get_temperature5()
        self.get_temperature6()
        self.get_temperature13()
        self.get_closedPID()
        self.get_heater_power()
        self.get_mixingchamber_setpoint()
        self.get_mixingchamber_temp()
        self.get_turbo()
        

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

    def do_get_temperature(self,channel):
        SCPIstring = 'READ:DEV:T' + str(channel) + ':TEMP:SIG:TEMP'
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:DEV:T' + channel  + ':TEMP:SIG:TEMP:',''))
        res = res[:-1]
        return res

    def do_get_mixingchamber_setpoint(self):
        SCPIstring = 'READ:DEV:T5:TEMP:LOOP:TSET'
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:DEV:T5:TEMP:LOOP:TSET:',''))
        res = res[:-1]
        return res

    def do_get_mixingchamber_temp(self):
        SCPIstring = 'READ:DEV:T5:TEMP:SIG:TEMP'
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:DEV:T5:TEMP:SIG:TEMP:',''))
        res = res[:-1]
        return res

    def do_set_mixingchamber_setpoint(self, val):
        SCPIstring = 'SET:DEV:T5:TEMP:LOOP:TSET:' +str(val)
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:SET:DEV:T5:TEMP:LOOP:TSET:0.1:',''))
        return res

    def do_get_closedPID(self):
        SCPIstring = 'READ:DEV:T5:TEMP:LOOP:MODE'
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:DEV:T5:TEMP:LOOP:MODE:',''))
        return res

    def do_set_closedPID(self, val):
        SCPIstring = 'SET:DEV:T5:TEMP:LOOP:MODE:'+str(val)
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:DEV:T5:LOOP:MODE',''))
        self.get_heater_power()
        return res

    def do_get_turbo(self):
        SCPIstring = 'READ:DEV:TURB1:PUMP:SIG:STATE'
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:DEV:TURB1:PUMP:SIG:STATE:',''))
        return res

    def do_set_turbo(self, val):
        SCPIstring = 'SET:DEV:TURB1:PUMP:SIG:STATE:'+str(val)
        result = self._execute(SCPIstring)
        sleep(3)
        res = (result.replace('STAT:SET:DEV:TURB1:PUMP:SIG:STATE',''))
        return res

    def do_get_heater_power(self):
        SCPIstring = 'READ:DEV:T5:TEMP:LOOP:RANGE'
        result = self._execute(SCPIstring)
        res = (result.replace('STAT:DEV:T5:TEMP:LOOP:RANGE:',''))
        res = res[:-2]
        return res

    def do_set_heater_power(self, val):
        #Allowed values: 0.0316, 0.1, 0.316, 1, 3.16, 10, 31.6, 100
        if self.get_closedPID() == 'ON':
            SCPIstring = 'SET:DEV:T5:TEMP:LOOP:RANGE:'+str(val)
            result = self._execute(SCPIstring)
            res = (result.replace('STAT:SET:DEV:T5:TEMP:LOOP:RANGE:1:',''))
            return res
        else:
            SCPIstring = 'SET:DEV:T5:TEMP:LOOP:RANGE:0.'
            result = self._execute(SCPIstring)
            res = (result.replace('STAT:SET:DEV:T5:TEMP:LOOP:RANGE:1:',''))
            return res

    def istempreached(self,val):
        thighperc = val*1.015
        tlowperc = val/1.015
        thighabs = val+0.001
        tlowabs = val-0.001
        if thighperc<thighabs:
            thigh = thighabs
            tlow = tlowabs
        else:
            thigh = thighperc
            tlow = tlowperc

        print 'thigh:' + str(thigh) + ' tlow:' + str(tlow)
        stability_samples_limit = 5
        stability_samples = 0
        tlow_samples_limit = 10
        tlow_samples = 0
        tick = 30 #polling interval
        while stability_samples != stability_samples_limit:
            actualtemp = self.get_mixingchamber_temp()
            if actualtemp > tlow and actualtemp < thigh:
                print 'Waiting for temp to stabilise. Samples:' + str(stability_samples)
                stability_samples = stability_samples + 1
            if actualtemp < tlow:
                stability_samples = 0
                tlow_samples = tlow_samples + 1
                print 'Waiting to reach temp, temp = ' + str(actualtemp) + ' Tlow_samples:' + str(tlow_samples)
            if actualtemp > thigh:
                stability_samples = 0
                tlow_samples = 0
                print 'Temp higher than setpoint: '+ str(actualtemp) +', waiting...'
            if tlow_samples == tlow_samples_limit:
                hp = 2*self.get_heater_power()+0.0316
                self.set_heater_power(hp)
                timeout = 0
                tlow_samples = 0
            sleep(tick)

    def do_set_autotempcontrol(self,val):
        #PID: 6 11 4
        print 'temptoset'+ str(val)
        self.set_heater_power(0.)
        sleep(1)
        self.set_closedPID('ON')
        sleep(1)
        self.set_mixingchamber_setpoint(val)
        sleep(1)
        if val <= 0.015:
            if self.get_turbo() == 'OFF':
                self.set_turbo('ON')
            self.set_closedPID('OFF')
        if val > 0.015 and val <= 0.075:
            if self.get_turbo() == 'OFF':
                self.set_turbo('ON')
            self.set_heater_power(0.316)
        if val > 0.075 and val <= 0.7:
            if self.get_turbo() == 'OFF':
                self.set_turbo('ON')
            self.set_heater_power(1.)
        if val > 0.7 and val <= 1.0:
            self.set_heater_power(3.16)
            if self.get_turbo() == 'OFF':
                self.set_turbo('ON')
        if val > 1.0 and val <= 1.5:
            self.set_heater_power(3.16)
            if self.get_turbo() == 'ON':
                self.set_turbo('OFF')
        if val > 1.5 and val <= 2.:
            self.set_heater_power(10.)
            if self.get_turbo() == 'ON':
                self.set_turbo('OFF')
        if val > 2.:
            self.set_heater_power(31.6)
            if self.get_turbo() == 'ON':
                self.set_turbo('OFF')
        self.istempreached(val)

    def do_get_autotempcontrol(self):
        return self.get_mixingchamber_setpoint()
