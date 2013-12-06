# OxfordInstruments_ILM200.py class, to perform the communication between the Wrapper and the device
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
import pyvisa.visa as visa
import types
import logging

class OxfordInstruments_ITC503S(Instrument):
    '''
    This is the python driver for the Oxford Instruments ITC 503 Temperature Contorller.

    Usage:
    Initialize with
    <name> = instruments.create('name', 'OxfordInstruments_ITC503S', address='<Instrument address>')
    <Instrument address> = ASRL1::INSTR

    Note: Since the ISOBUS allows for several instruments to be managed in parallel, the command
    which is sent to the device starts with '@n', where n is the ISOBUS instrument number.

    '''
#TODO: auto update script
#TODO: get doesn't always update the wrapper! (e.g. when input is an int and output is a string)

    def __init__(self, name, address, number=1):
        '''
        Initializes the Oxford Instruments ITC 503 Temperature Controller.

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
        self._number = number
        self._visainstrument = visa.SerialInstrument(self._address)
        self._values = {}
        self._visainstrument.stop_bits = 2
        print 'jadoei'

        #Add parameters
        self.add_parameter('T1', type=types.FloatType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('T2', type=types.FloatType,
            flags=Instrument.FLAG_GET)
        self.add_parameter('T3', type=types.FloatType,
            flags=Instrument.FLAG_GET)

        self.add_parameter('status', type=types.StringType,
            flags=Instrument.FLAG_GET)
 
        self.add_parameter('p', type=types.FloatType,
             flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,minval=0, maxval=50)
        self.add_parameter('i', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,minval=0, maxval=10)
        self.add_parameter('d', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,minval=0, maxval=1)

        self.add_parameter('T_setpoint', type=types.FloatType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,minval=0, maxval=50)
        self.add_parameter('remote_status', type=types.IntType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            format_map = {
            0 : "Local and locked",
            1 : "Remote and locked",
            2 : "Local and unlocked",
            3 : "Remote and unlocked",})
        self.add_parameter('heater', type=types.IntType,
            flags=Instrument.FLAG_GETSET | Instrument.FLAG_GET_AFTER_SET,
            format_map = {
			    0 : "Heater Manual, Gas manual",
				1 : "heater auto, gas manual",
				2 : "heater manual, gas auto",
				3 : "heater auto, gas auto"})
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
        self.get_T1()
        self.get_T2()
        self.get_T3()
        self.get_heater()
        self.get_status()

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
        self._visainstrument.write('@%s%s' %(self._number, message))
        sleep(20e-3) # wait for the device to be able to respond
        result = self._visainstrument.read()
        if result.find('?') >= 0:
            print "Error: Command %s not recognized" %message
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

    def remote(self):
        '''
        Set control to remote & locked

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Set control to remote & locked')
        self.set_remote_status(1)

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

    def set_remote_status(self, mode):
        '''
        Set remote control status.

        Input:
            mode(int) :
            0 : "Local and locked",
            1 : "Remote and locked",
            2 : "Local and unlocked",
            3 : "Remote and unlocked",

        Output:
            None
        '''
        status = {
        0 : "Local and locked",
        1 : "Remote and locked",
        2 : "Local and unlocked",
        3 : "Remote and unlocked",
        }
        logging.info(__name__ + ' : Setting remote control status to %s' %status.get(mode,"Unknown"))
        self._execute('C%s' %mode)
    def do_set_heater(self, mode):
        '''
        Set the switch heater Off or On. Note: After issuing a command it is necessary to wait
        several seconds for the switch to respond.
        Input:
            mode (int) :
            0 : "Off",
            1 : "On, if PSU = Magnet",

            2 : "On, No checks" (not available)

        Output:
            None
        '''
        status = {
        0 : "Heater Manual, Gas manual",
        1 : "heater auto, gas manual",
		2 : "heater manual, gas auto",
		3 : "heater auto, gas auto"
        }
        if status.__contains__(mode):
            logging.info(__name__ + ' : Setting heater to %s' % status.get(mode, "Unknown"))
            self._execute('A%s' % mode)
        else:
            print 'Invalid mode inserted.'
			
    def do_set_p(self, p):
        self._execute('P%s' % p)
    def do_set_i(self, i):
        self._execute('I%s' % i)
    def do_set_d(self, d):
        self._execute('D%s' % d)
    def do_set_T_setpoint(self, T):
        self._execute('T%s' % T)
		
    def do_get_p(self):
        logging.info(__name__ + ' : Read Proportional')
        result = self._execute('R8')
        return float(result.replace('R',''))
    def do_get_i(self):
        logging.info(__name__ + ' : Read Proportional')
        result = self._execute('R9')
        return float(result.replace('R',''))
    def do_get_d(self):
        logging.info(__name__ + ' : Read Proportional')
        result = self._execute('R10')
        return float(result.replace('R',''))
    def do_get_T_setpoint(self):
        logging.info(__name__ + ' : Read Proportional')
        result = self._execute('R0')
        return float(result.replace('R',''))
    def do_get_heater(self):
        '''
        Get the switch heater status.
        Input:
            None

        Output:
            result(str) : "Off magnet at zero", "On (switch open)", "Off magnet at field (switch closed)",
            "Heater fault (heater is on but current is low)" or "No switch fitted".
        '''
        logging.info(__name__ + ' : Get switch heater status')
        result = self._execute('X')
        return int(result[3])
    def do_get_T1(self):
        '''
        Get temperature on channel 1.
        Input:
            None

        Output:
            result (float) : Temperature
        '''
        logging.info(__name__ + ' : Read level of channel 1')
        result = self._execute('R1')
        return float(result.replace('R',''))
    def do_get_T2(self):
        '''
        Get temperature on channel 2.
        Input:
            None

        Output:
            result (float) : Temperature
        '''
        logging.info(__name__ + ' : Read level of channel 2')
        result = self._execute('R2')
        return float(result.replace('R',''))
    def do_get_T3(self):
        '''
        Get temperature on channel 3.
        Input:
            None

        Output:
            result (float) : Temperature
        '''
        logging.info(__name__ + ' : Read level of channel 3')
        result = self._execute('R3')
        return float(result.replace('R',''))

    def do_get_status(self):
        '''
        Get status of the device.
        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Get status of the device.')
        result = self._execute('X')
        status = {
        0 : "Channel not in use",
        1 : "Channel used for Nitrogen level",
        2 : "Channel used for Helium Level (Normal pulsed operation)",
        3 : "Channel used for Helium Level (Continuous measurement)",
        9 : "Error on channel (Usually means probe unplugged)"
        }
        return status.get(int(result[1]), "Unknown")
    def do_get_remote_status(self):
        '''
        Get remote control status

        Input:
            None

        Output:
            result(str) :
            "Local & locked",
            "Remote & locked",
            "Local & unlocked",
            "Remote & unlocked",
        '''
        logging.info(__name__ + ' : Get remote control status')
        result = self._execute('X')
        return int(result[5])
    def do_set_remote_status(self, mode):
        '''
        Set remote control status.

        Input:
            mode(int) :
            0 : "Local and locked",
            1 : "Remote and locked",
            2 : "Local and unlocked",
            3 : "Remote and unlocked",

        Output:
            None
        '''
        status = {
        0 : "Local and locked",
        1 : "Remote and locked",
        2 : "Local and unlocked",
        3 : "Remote and unlocked",
        }
        if status.__contains__(mode):
            logging.info(__name__ + ' : Setting remote control status to %s' % status.get(mode,"Unknown"))
            self._execute('C%s' % mode)
        else:
            print 'Invalid mode inserted: %s' % mode
