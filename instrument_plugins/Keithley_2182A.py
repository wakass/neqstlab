# Keithley_2182A.py driver for Keithley 2182A nanovoltmeter
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


from timeit import default_timer as timer

import qt

def bool_to_str(val):
    '''
    Function to convert boolean to 'ON' or 'OFF'
    '''
    if val == True:
        return "ON"
    else:
        return "OFF"

class Keithley_2182A(Instrument):
    '''
    This is the driver for the Keithley 2182A current source

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Keithley_2182A',
        address='<GBIP address>',
        reset=<bool>,
        change_display=<bool>,
        change_autozero=<bool>)
    '''

    def __init__(self, name, address, reset=False,
            change_display=True):
        '''
        Initializes the Keithley_2182A, and communicates with the wrapper.

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
        logging.info('Initializing instrument Keithley_2182A')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._change_display = change_display

        # Add parameters to wrapper
        self.add_parameter('reading',
            flags=Instrument.FLAG_GET,
            units='V',
            type=types.FloatType,
            tags=['measure'])
        self.add_parameter('range',
            flags=Instrument.FLAG_GETSET,
            units='V', 
            minval=0.0, 
            maxval=120.0, 
            type=types.FloatType)
        self.add_parameter('autorange',
            flags=Instrument.FLAG_GETSET,
            units='',
            type=types.BooleanType)
        self.add_parameter('display', 
            flags=Instrument.FLAG_GETSET,
            type=types.BooleanType)
        self.add_parameter('nplc',
            flags=Instrument.FLAG_GETSET,
            units='#',
            minval=0.001,
            maxval=50,
            type=types.FloatType)
        self.add_parameter('aperture',
            flags=Instrument.FLAG_GETSET,
            units='s',
            minval=200e-6,
            maxval=1.0,
            type=types.FloatType)
        self.add_parameter('analog_filter', 
            flags=Instrument.FLAG_GETSET,
            type=types.BooleanType)
        self.add_parameter('digital_filter', 
            flags=Instrument.FLAG_GETSET,
            type=types.BooleanType)
        self.add_parameter('digital_filter_count', 
            flags=Instrument.FLAG_GETSET,
            units='#', 
            minval=1, 
            maxval=100, 
            type=types.IntType)
        self.add_parameter('digital_filter_window', 
            flags=Instrument.FLAG_GETSET,
            units='%', 
            minval=0, 
            maxval=10, 
            type=types.FloatType)
        self.add_parameter('digital_filter_type', 
            flags=Instrument.FLAG_GETSET,
            format_map = {
                'MOV' : "Moving average filter",
                'REP' : "Repeating filter"},
            type=types.StringType)
        self.add_parameter('autozero', 
            flags=Instrument.FLAG_GETSET,
            type=types.BooleanType)
        self.add_parameter('front_autozero', 
            flags=Instrument.FLAG_GETSET,
            type=types.BooleanType)
        self.add_parameter('line_frequency', 
            flags=Instrument.FLAG_GET,
            type=types.FloatType)
        self.add_parameter('lsync', 
            flags=Instrument.FLAG_GETSET,
            type=types.BooleanType)
     

        # Add functions to wrapper
        self.add_function('reset')
        self.add_function('get_all')
        self.add_function('enable_fast_mode')

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
        self._write('SENS:CHAN 1')
        self._write('CONF:VOLT')
        self._write('TRIG:DEL:AUTO ON')
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
        self.get_range()
        self.get_autorange()
        self.get_display()
        self.get_nplc()
        self.get_aperture()
        self.get_analog_filter()
        self.get_digital_filter()
        self.get_digital_filter_count()
        self.get_digital_filter_window()
        self.get_digital_filter_type()

    def enable_fast_mode(self):
        self.set_analog_filter(False)
        self.set_digital_filter(False)
        self.set_autozero(False)
        self.set_front_autozero(False)
        self.set_lsync(False)

# --------------------------------------
#           parameters
# --------------------------------------

    def do_get_reading(self):
        logging.debug('Get measurement reading')
        reply = self._ask(':READ?')
        return float(reply)

    def do_get_range(self):
        logging.debug('Get measurement range')
        reply = self._ask('SENS:VOLT:RANG?')
        return float(reply)

    def do_set_range(self, val):
        logging.debug('Set measurement range to %s' % val)
        self._write('SENS:VOLT:RANG %s' % val)

    def do_get_autorange(self):
        logging.debug('Get autorange setting')
        reply = self._ask('SENS:VOLT:RANG:AUTO?')
        return bool(int(reply))

    def do_set_autorange(self, val):
        logging.debug('Set autorange to %s' % val)
        self._write('SENS:VOLT:RANG:AUTO %s' % bool_to_str(val))

    def do_get_display(self):
        logging.debug('Get state of front display')
        reply = self._ask('DISP:ENAB?')
        return bool(int(reply))

    def do_set_display(self, val):
        logging.debug('Set state of front display to %s' % val)
        self._write('DISP:ENAB %s' % bool_to_str(val))

    def do_get_nplc(self):
        logging.debug('Get integration rate in line cycles')
        reply = self._ask('SENS:VOLT:NPLC?')
        return float(reply)

    def do_set_nplc(self, val):
        logging.debug('Set integration rate in line cycles to %s' % val)
        self._write('SENS:VOLT:NPLC %s' % val)

    def do_get_aperture(self):
        logging.debug('Get integration rate in seconds')
        reply = self._ask('SENS:VOLT:APER?')
        return float(reply)

    def do_set_aperture(self, val):
        logging.debug('Set integration rate in seconds %s' % val)
        self._write('SENS:VOLT:APER %s' % val)

    def do_get_analog_filter(self):
        logging.debug('Get state of analog filter')
        reply = self._ask('SENS:VOLT:LPAS?')
        return bool(int(reply))

    def do_set_analog_filter(self, val):
        logging.debug('Set state of analog filter to %s' % val)
        self._write('SENS:VOLT:LPAS %s' % bool_to_str(val))

    def do_get_digital_filter(self):
        logging.debug('Get state of digital filter')
        reply = self._ask('SENS:VOLT:DFIL?')
        return bool(int(reply))

    def do_set_digital_filter(self, val):
        logging.debug('Set state of digital filter to %s' % val)
        self._write('SENS:VOLT:DFIL %s' % bool_to_str(val))

    def do_get_digital_filter_count(self):
        logging.debug('Get filter count of digital filter')
        reply = self._ask('SENS:VOLT:DFIL:COUN?')
        return int(reply)

    def do_set_digital_filter_count(self, val):
        logging.debug('Set filter count of digital filter to %s' % val)
        self._write('SENS:VOLT:DFIL:COUN %s' % val)

    def do_get_digital_filter_window(self):
        logging.debug('Get window size of digital filter')
        reply = self._ask('SENS:VOLT:DFIL:WIND?')
        return float(reply)

    def do_set_digital_filter_window(self, val):
        logging.debug('Set window size of digital filter to %s' % val)
        self._write('SENS:VOLT:DFIL:WIND %s' % val)

    def do_get_digital_filter_type(self):
        logging.debug('Get filter type of digital filter')
        reply = self._ask('SENS:VOLT:DFIL:TCON?')
        return str(reply).strip()

    def do_set_digital_filter_type(self, val):
        logging.debug('Set filter type of digital filter to %s' % val)
        self._write('SENS:VOLT:DFIL:TCON %s' % val)

    def do_get_autozero(self):
        logging.debug('Get state of autozero filter')
        reply = self._ask('SYST:AZER?')
        return bool(int(reply))

    def do_set_autozero(self, val):
        logging.debug('Set state of autozero filter to %s' % val)
        self._write('SYST:AZER %s' % bool_to_str(val))

    def do_get_front_autozero(self):
        logging.debug('Get state of front autozero filter')
        reply = self._ask('SYST:FAZ?')
        return bool(int(reply))

    def do_set_front_autozero(self, val):
        logging.debug('Set state of front autozero filter to %s' % val)
        self._write('SYST:FAZ %s' % bool_to_str(val))

    def do_get_line_frequency(self):
        logging.debug('Get detected line frequency value')
        reply = self._ask('SYST:LFR?')
        return float(reply)

    def do_get_lsync(self):
        logging.debug('Get state of line cycle synchronization')
        reply = self._ask('SYST:LSYN?')
        return bool(int(reply))

    def do_set_lsync(self, val):
        logging.debug('Set state of line cycle synchronization to %s' % val)
        self._write('SYST:LSYN %s' % bool_to_str(val))

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


