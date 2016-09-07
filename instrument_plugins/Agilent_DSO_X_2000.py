# LeCroy_44Xi.py class, to perform the communication between the Wrapper and the device
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
import qtvisa as visa
import types
import logging
import numpy as np
import struct

class Agilent_DSO_X_2000(Instrument):
    '''
    This is the python driver for the Agilent DSOX 2000 Series
    Digital Oscilloscope

    Usage:
    Initialize with
    <name> = instruments.create('name', 'Agilent_DSO_X_2000', address='<USB address>')
    Read address from Utility Menu->IO
    '''

    def __init__(self, name, address):
        '''
        Initializes the DSO.

        Input:
            name (string)    : name of the instrument
            address (string) :  address

        Output:
            None
        '''
        logging.debug(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])


        self._address = address
        self._visainstrument = visa.instrument(self._address)
        self._values = {}

        # Add parameters
        self.add_parameter('timebase', type=types.FloatType,
            flags=Instrument.FLAG_GETSET)
        self.add_parameter('vertical', type=types.FloatType,
            flags=Instrument.FLAG_GETSET, channels=(1, 4),
            channel_prefix='ch%d_')


#        # Make Load/Delete Waveform functions for each channel
 #       for ch in range(1, 5):
  #          self._add_save_data_func(ch)

        self.get_all()
        self.set_save_pwd()
        self.set_save_filename()

    # Functions
    def get_all(self):
        '''
        Get all parameter values
        '''
        self.get_timebase()
        self.get_ch1_vertical()
        self.get_ch2_vertical()
        self.get_ch3_vertical()
        self.get_ch4_vertical()
        
    def set_trigger_single(self):
        '''
        Change the aquisition state to Single.

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Set trigger to single')
        self._visainstrument.write(':SINGLE')

    def set_trigger_run(self):
        '''
        Change the trigger mode to Run.

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Set trigger to normal')
        self._visainstrument.write(':RUN')

    def set_trigger_stop(self):
        '''
        Change the trigger mode to Stop

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Set trigger to auto')
        self._visainstrument.write(':STOP')
    def force_trigger(self):
        '''
        Force a triggering event.
        '''
        logging.info(__name__ + ' : Sending a trigger')
        self._visainstrument.write('*TRG')
    def auto_setup(self):
        '''
        Adjust vertical, timebase and trigger parameters automatically

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Auto setup of vertical, timebase and trigger')
        self._visainstrument.write(':AUTO')

    def do_set_timebase(self, value):
        '''
        Modify the timebase setting in Sec/div.

        Input:
            value (str) : Timebase in S. (NS (nanosec), US (microsec), MS (milisec),
                S (sec) or KS (kilosec))
                (Example: '50E-6', '50 MS')

        Output:
            None
        '''
        logging.info(__name__ + ' : Set timebase setting to %s' % value)
        self._visainstrument.write(':TIMEBASE:SCALE {:s}'.format(self.format_r3(value)))

    def do_get_timebase(self):
        '''
        Get the timebase setting in Sec/div.

        Input:
            None

        Output:
            value (str) : Timebase in S
        '''
        logging.info(__name__ + ' : Get timebase setting')
        result = self._visainstrument.ask(':TIMEBASE:SCALE?')

        return float(result)

    def do_set_vertical(self, value, channel):
        '''
        Set vertical sensitivity in Volts/div.

        Input:
            value (str) : Vertical base in V. (UV (microvolts), MV (milivolts),
                V (volts) or KV (kilovolts))
                (Example: '20E-3', '20 MV')
            channel (int) : channel (1,2,3,4)

        Output:
            None
        '''
        logging.info(__name__ + ' : Set vertical base setting of channel %s to %s' % (channel,value))
        self._visainstrument.write(':CHANNEL{:d}:SCALE {:s}V'.format(channel,self.format_r3(value)))

    def do_get_vertical(self, channel):
        '''
        Get vertical sensitivity in Volts/div.

        Input:
            channel (int) : channel (1,2,3,4)

        Output:
            value (str) : Vertical base in V.
        '''
        logging.info(__name__ + ' : Get vertical base setting of channel %s' % channel)
        result = self._visainstrument.ask(':CHANNEL%s:SCALE?' % channel)
        return float(result)

    def set_save_pwd(self,path='\"\\usb\"'):
        self._visainstrument.write(':SAVE:PWD {:s}'.format(path))

    def set_save_filename(self,filename='\"default\"'):
        self._visainstrument.write(':SAVE:FILENAME {:s}'.format(filename))
    def save_waveform(self):
        self._visainstrument.write(':SAVE:WAVEFORM:FORMAT CSV')
        self._visainstrument.write(':SAVE:WAVEFORM:START')
    def get_waveform(self):
        dev = self._visainstrument
        dev.write(':WAVEFORM:POINTS:MODE MAX')
        dev.write(':WAVEFORM:POINTS 5000')

        dev.write(':TIMEBASE:MODE MAIN')
        
        dev.write(':ACQUIRE:TYPE NORMAL')
       # dev.write(':ACQUIRE:COUNT 1')
        
        dev.write(':DIGITIZE CHAN1') #bam, this is a trigger
        while not bool(dev.ask('*OPC?')):
            continue
    
        dev.write(':WAVEFORM:FORMAT BYTE')
        dev.write(':WAVEFORM:BYTEORDER LSBFirst') #this means little-endian

        preamble_string = dev.ask(':WAVEFORM:PREAMBLE?')
        wav_form_dict = {
            0 : "BYTE",
            1 : "WORD",
            4 : "ASCii",
        }
        acq_type_dict = {
            0 : "NORMal",
            1 : "PEAK",
            2 : "AVERage",
            3 : "HRESolution",
        }
        preamble_dict =[np.int16,
                        np.int16,
                        np.int32,
                        np.int32,
                        np.float64,
                        np.float64,
                        np.int32,
                        np.float32,
                        np.float32,
                        np.int32]
        (wav_form, acq_type, wfmpts, avgcnt, x_increment, x_origin,  x_reference, y_increment, y_origin, y_reference) = [f(v) for f,v in zip(preamble_dict,preamble_string.split(','))]
       
        '''
        % The preamble block contains all of the current WAVEFORM settings.  
        It is returned in the form <preamble_block><NL> where <preamble_block> is:
    FORMAT        : int16 - 0 = BYTE, 1 = WORD, 2 = ASCII.
    TYPE          : int16 - 0 = NORMAL, 1 = PEAK DETECT, 2 = AVERAGE
    POINTS        : int32 - number of data points transferred.
    COUNT         : int32 - 1 and is always 1.
    XINCREMENT    : float64 - time difference between data points.
    XORIGIN       : float64 - always the first data point in memory.
    XREFERENCE    : int32 - specifies the data point associated with
                            x-origin.
    YINCREMENT    : float32 - voltage diff between data points.
    YORIGIN       : float32 - value is the voltage at center screen.
    YREFERENCE    : int32 - specifies the data point where y-origin
                            occurs.
'''
        print 'preamble {:s}'.format(preamble_string)
        try:
            dev.write_raw(':WAVEFORM:DATA?')
            r = dev.read_raw() #read out the data directly from the interface')
        except ValueError as e:
            print 'Had a value error'
            print e
        instrument_error = dev.ask(':SYSTEM:ERR?')
        if instrument_error != '+0, \"No error\"':
            print 'Device had an error'
            print instrument_error

        return self.process_datablock(r,x_increment,x_origin,y_increment,y_origin,y_reference)

    def process_datablock(self,data,xinc, xorg, yinc, yorg, yref):
        if data[0] != '#':
            raise ValueError('Invalid binary block format')
        n_databytes = int(data[1])
        len_data = int(data[2:2+n_databytes])
        data = data[2+n_databytes:2+n_databytes+len_data]

        values = struct.unpack('%dB'%len(data), data) #taken from agilent example..ugh(ly). Maybe use np for this?
        values = np.array(values)
        time   = np.linspace(xorg,xorg+len(values)*xinc,len(values))
        values = (values - yref)*yinc + yorg
        return (time,values)

    def process_preamble(self,preamble_string):
        # Display the waveform settings from preamble:


        return preamble_string
    
    def _do_save_data(self, channel):
        '''
        Store a trace in ASCII format in internal memory

        Input:
            channel(int) : channel

        Output:
            None
        '''
        logging.info(__name__ + ' : Save data for channel %s' % channel)
        self._visainstrument.write('STST C%s,HDD,AUTO,OFF,FORMAT,ASCII; STO' % channel)

    def _add_save_data_func(self, channel):
        '''
        Adds save_ch[n]_data functions, based on _do_save_data(channel).
        n = (1,2,3,4) for 4 channels.
        '''
        func = lambda: self._do_save_data(channel)
        setattr(self, 'save_ch%s_data' % channel, func)

    def sequence(self, segments, max_size):
        '''
        Set the sequence mode on and set number of segments, maximum memory size.
        Input:
            segments(int) : number of segments. max: 2000.
            max_size(float) : maximum memory length. Format: {10e3, 10.0e3, 11e+3, 25K, 10M (mili), 10MA (mega))

        Output:
            None
        '''
        logging.info(__name__ + ' : Set the sequence mode settings. Segments: %s, Maximum memory size: %s' % (segments, max_size))

    def format_r3(self,value):
        return '{:.3E}'.format(value)
