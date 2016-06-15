# Keithley_2661.py driver for Keithley 2661 current source
# adapted from:
# Keithley_2400.py driver for Keithley 2400 DMM
# Pieter de Groot <pieterdegroot@gmail.com>, 2008
# Martijn Schaafsma <qtlab@mcschaafsma.nl>, 2008
# Reinier Heeres <reinier@heeres.eu>, 2008 - 2010
#
# Update december 2009:
# Michiel Jol <jelle@michieljol.nl>
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
import qtvisa as visa
import types
import logging
import numpy

import qt

def bool_to_str(val):
    '''
    Function to convert boolean to 'ON' or 'OFF'
    '''
    if val == True:
        return "ON"
    else:
        return "OFF"

class Keithley_6221(Instrument):
    '''
    This is the driver for the Keithley 6221 current source

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Keithley_6221',
        address='<GBIP address>',
        reset=<bool>,
        change_display=<bool>,
        change_autozero=<bool>)
    '''

    def __init__(self, name, address, reset=False,
            change_display=True):
        '''
        Initializes the Keithley_6221, and communicates with the wrapper.

        Input:
            name (string)           : name of the instrument
            address (string)        : GPIB address
            reset (bool)            : resets to default values
            change_display (bool)   : If True (default), automatically turn off
                                        display during measurements.
            change_autozero (bool)  : If True (default), automatically turn off
                                        autozero during measurements.
        Output:
            None
        '''
        # Initialize wrapper functions
        logging.info('Initializing instrument Keithley_6221')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._change_display = change_display

        # Add parameters to wrapper
        self.add_parameter('current',
            flags=Instrument.FLAG_GETSET,
            units='A', 
            minval=-0.105, 
            maxval=0.105, 
            type=types.FloatType)
        self.add_parameter('range',
            flags=Instrument.FLAG_GETSET,
            units='A', 
            minval=0.0, 
            maxval=0.105, 
            type=types.FloatType)
        self.add_parameter('autorange',
            flags=Instrument.FLAG_GETSET,
            units='',
            type=types.BooleanType)
        self.add_parameter('compliance',
            flags=Instrument.FLAG_GETSET,
            units='V',
            minval=0.1,
            maxval=105,
            type=types.FloatType)    
        self.add_parameter('output_response',
            flags=Instrument.FLAG_GETSET,
            format_map = {
                'SLOW' : "Slow output response",
                'FAST' : "Fast output response"},
            type=types.StringType)
        self.add_parameter('output',
            flags=Instrument.FLAG_GETSET,
            type=types.BooleanType) 
        self.add_parameter('display', 
            flags=Instrument.FLAG_GETSET,
            type=types.BooleanType)
     

        # Add functions to wrapper
        self.add_function('reset')
        self.add_function('get_all')
        self.add_function('clear')

        # Connect to measurement flow to detect start and stop of measurement
        qt.flow.connect('measurement-start', self._measurement_start_cb)
        qt.flow.connect('measurement-end', self._measurement_end_cb)

        if reset:
            self.reset()
        else:
            self.get_all()
            self.set_defaults()

# --------------------------------------
#           functions
# --------------------------------------

    def reset(self):
        '''
        Resets instrument to default values

        Input:
            None

        Output:
            None
        '''
        logging.debug('Resetting instrument')
        self._write('*RST')
        self.get_all()

    def set_defaults(self):
        '''
        Set to driver defaults:
        '''
        self.set_autorange(True)

    def get_all(self):
        '''
        Reads all relevant parameters from instrument

        Input:
            None

        Output:
            None
        '''
        logging.info('Get all relevant data from device')
        self.get_current()
        self.get_range()
        self.get_autorange()
        self.get_compliance()
        self.get_output_response()
        self.get_output()
        self.get_display()

    def clear(self):
        logging.debug('Clear the current source')
        self._write('SOUR:CLE')

# --------------------------------------
#           parameters
# --------------------------------------


    def do_get_current(self):
        logging.debug('Get current setpoint')
        reply = self._ask('SOUR:CURR?')
        return float(reply)

    def do_set_current(self, val):
        logging.debug('Set current setpoint to %s' % val)
        self._write('SOUR:CURR %s' % val)
        
    def do_get_range(self):
        logging.debug('Get current range')
        reply = self._ask('SOUR:CURR:RANG?')
        return float(reply)

    def do_set_range(self, val):
        logging.debug('Set current range to %s' % val)
        self._write('SOUR:CURR:RANG %s' % val)

    def do_get_autorange(self):
        logging.debug('Get autorange setting')
        reply = self._ask('SOUR:CURR:RANG:AUTO?')
        return bool(int(reply))

    def do_set_autorange(self, val):
        logging.debug('Set autorange to %s' % val)
        self._write('SOUR:CURR:RANG:AUTO %s' % bool_to_str(val))

    def do_get_compliance(self):
        logging.debug('Get compliance setting')
        reply = self._ask('SOUR:CURR:COMP?')
        return float(reply)

    def do_set_compliance(self, val):
        logging.debug('Set compliance to %s' % val)   
        self._write('SOUR:CURR:COMP %s' % val)

    def do_get_output_response(self):
        logging.debug('Get output response')
        reply = self._ask('OUTP:RESP?')
        return str(reply).strip()

    def do_set_output_response(self, val):
        logging.debug('Set output response to %s' % val)
        self._write('OUTP:RESP %s' % val)

    def do_get_output(self):
        logging.debug('Get state of output (on/off)')
        reply = self._ask('OUTP?')
        return bool(int(reply))

    def do_set_output(self, val):
        logging.debug('Set state of output to %s' % val)
        self._write('OUTP %s' % bool_to_str(val))

    def do_get_display(self):
        logging.debug('Get state of front display')
        reply = self._ask('DISP:ENAB?')
        return bool(int(reply))

    def do_set_display(self, val):
        logging.debug('Set state of front display to %s' % val)
        self._write('DISP:ENAB %s' % bool_to_str(val))


# --------------------------------------
#           Internal Routines
# --------------------------------------

    def _ask(self, query):
        '''
        Ask instrument <query> and return the reply.
        '''
        logging.debug('Asking instrument for \'%s\'' % query)
        reply = self._visainstrument.ask(query)
        logging.debug('Instrument replied \'%s\'' % reply)
        return reply

    def _write(self, query):
        '''
        Write <query> to instrument.
        '''
        logging.debug('Sending \'%s\' to instrument' % query)
        self._visainstrument.write(query)

    def _measurement_start_cb(self, sender):
        '''
        Things to do at starting of measurement
        '''
        if self._change_display:
            self.set_display(False)
            #Switch off display to get stable timing

    def _measurement_end_cb(self, sender):
        '''
        Things to do after the measurement
        '''
        if self._change_display:
            self.set_display(True)


