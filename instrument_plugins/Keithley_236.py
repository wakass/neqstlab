# Keithley_236.py driver for Keithley 236 SMU
# Zeust the Unoobian <2noob2banoob@gmail.com>
# Based on:
#   Keithley_199.py driver for Keithley 199 DMM
#   Reinier Heeres <reinier@heeres.eu>, 2009
#
# Most stuff also works for Keithley 237 and 238 but some parameter
# values represent slightly different numerical values for real
# parameters, this is indicated with comments. Refer to the Keithley
# 236,237,238 User Manual for further details:
# http://www.download-service-manuals.com/download.php?file=Keithley-3526.pdf&SID=fp799cqduhurj3gh6rgsjr1ac5
# Section 3.6 of that document is of particular interest.
#
# The following commands are not implemented:
# * Modify Sweep List (A)
# * Calibration (C)
# * Display (D)
# * IEEE Immediate Trigger (H0X)
# * EOI and Bus Hold-off (K)
# * SRQ (service request) Mask and Serial Poll Byte (M)
# * Output Sense (local or remote sensing) (O)
# * Create/Append Sweep List (Q)
# * Trigger Control (enable/disable) (R)
# * Integration Time (S)
# * 1100V Range Control (Keithley 237 only) (V)
# * Default Delay (W)
# * Execute Terminator (Y)
# * Suppress (Z)
#
# Note that the set_defaults() method reflects the author's group's
# preferences and that other groups may want to modify this method
# for their own implementation of QTLab.
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
import types
import visa

# Some ENUMs
############

OUTPUT_ITEMS = { 'source': 1, 'delay': 2, 'measure': 4, 'time': 8 }
OUTPUT_FORMATS = {
	'ASCII_prefix_suffix': 0,
	'ASCII_prefix_nosuffix': 1,
	'ASCII_noprefix_nosuffix': 2,
	'binary_HP': 3,
	'binary_IBM': 4 }
OUTPUT_LINES = { 'onesample': 0, 'onesweep': 1, 'allsweeps': 2 }

# Some functions for internal use
#################################

def _multiopts(unprocessed, filled=None, totalsofar=0, strsofar=''):
	'''
	Populate option map with combined options when fundamental options
	are to be treated like flags. This function was written assuming an
	integer datatype and may produce unexpected results for other types.
	
	Also note that this function will affect the original dict, which
	will resemble the return value after this function is done. You may
	want to manually do a copy.copy() if this is undesirable.
	'''
	if filled is None:
		filled = unprocessed
	idx = list(unprocessed)
	for i in range(len(idx)):
		if i != len(idx) - 1:
			filled = _multiopts(
					{j: unprocessed[j] for j in idx[i+1:]}, filled,
					totalsofar + idx[i],
					'{:s}{:s}, '.format(strsofar, unprocessed[idx[i]]))
		if totalsofar:
			filled[totalsofar + idx[i]] = '{:s}{:s}'.format(
					strsofar, unprocessed[idx[i]])
	return filled

def _opt(val, enum=None):
	'''Format an optional parameter as a string'''
	if enum is not None and val in enum:
		return str(enum[val])
	else:
		return None if val is None else str(val)

# Some command generators, all excluding the trailing X that would lead
# to immediate execution
#######################################################################

def _set_bias_range_delay_cmd(self, bias=None, rng=None, delay=None):
	'''Generate command to set bias, range and delay'''
	return 'B{:s},{:s},{:s}'.format(_opt(bias), _opt(rng), _opt(delay))

def _set_data_format_cmd(self, items=None, fmt=None, lines=None):
	'''Generate command to set data format.'''
	if type(items) is list:
		items = sum([(OUTPUT_ITEMS[i] if i in OUTPUT_ITEMS else i) for i in items])
	return 'G{:s},{:s},{:s}'.format(_opt(items, OUTPUT_ITEMS),
			_opt(fmt, OUTPUT_FORMATS), _opt(lines, OUTPUT_LINES))

# The actual class
##################

class Keithley_236(Instrument):

	def __init__(self, name, address=None):
		Instrument.__init__(self, name, tags=['measure', 'sweep'])

		self._address = address
		self._visains = visa.instrument(address)

		self.add_parameter('function', type=types.IntType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
				option_map={
					(0,0): 'DC_Vsrc_Imeas',
					(0,1): 'Sweep_Vsrc_Imeas',
					(1,0): 'DC_Isrc_Vmeas',
					(1,1): 'Sweep_Isrc_Vmeas'
				})

		self.add_parameter('range', type=types.FloatType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
				minval=0, maxval=9, #maxval=10 for Keithley 238
				option_map={
					0: 'auto',
					1: '1.1V / 1nA', # 1.5V for Keithley 238
					2: '11V / 10nA', # 15V for Keithley 238
					3: '110V / 100nA',
					4: '1uA', # Also 1.1kV for Keithley 237
					5: '10uA',
					6: '100uA',
					7: '1mA',
					8: '10mA',
					9: '100mA'
					# 10 = 1A for Keithley 238
				})

		self.add_parameter('compliance', type=types.FloatType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET)
		
		self.add_parameter('zero', type=types.IntType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
				option_map={
					0: 'Disabled',
					1: 'Enabled',
					2: 'Value',
				})

		self.add_parameter('zero_value', type=types.FloatType,
				flags=Instrument.FLAG_GETSET)

		#self.add_parameter('rate', type=types.IntType,
		#		flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
		#		option_map={
		#			0: '4.5 digit',
		#			1: '5.5 digit',
		#		})

		self.add_parameter('filter', type=types.IntType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
				option_map={
					0: 'No filter',
					1: '2-reading filter',
					2: '4-reading filter',
					3: '8-reading filter',
					4: '16-reading filter',
					5: '32-reading filter'
				})

		self.add_parameter('trigger-origin', type=types.IntType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
				option_map={
					0: 'IEEE X',
					1: 'IEEE GET',
					2: 'IEEE Talk',
					3: 'External',
					4: 'Immediate (Front panel or command)'
				})

		self.add_parameter('trigger-timing', type=types.IntType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
				option_map={
					0: 'Continuous (no trigger needed)',
					1: 'TRIG-source-delay-measure',
					2: 'source-TRIG-delay-measure',
					3: 'TRIG-source-TRIG-delay-measure',
					4: 'source-delay-TRIG-measure',
					5: 'TRIG-source-delay-TRIG-measure',
					6: 'source-TRIG-delay-TRIG-measure',
					7: 'TRIG-source-TRIG-delay-TRIG-measure',
					8: 'Single pulse'
				})

		self.add_parameter('trig-out-timing', type=types.IntType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
				option_map={
					0: 'None',
					1: 'source-TRIG-delay-measure',
					2: 'source-delay-TRIG-measure',
					3: 'source-TRIG-delay-TRIG-measure',
					4: 'source-delay-measure-TRIG',
					5: 'source-TRIG-delay-measure-TRIG',
					6: 'source-delay-TRIG-measure-TRIG',
					7: 'source-TRIG-delay-TRIG-measure-TRIG',
					8: 'Pulse end'
				})

		self.add_parameter('trig-out-sweepend', type=types.BooleanType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET)

		self.add_parameter('delay', type=types.IntType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
				minval=0, maxval=65000, units='msec')

		#self.add_parameter('interval', type=types.IntType,
		#		flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
		#		minval=15, maxval=999999, units='msec')

		self.add_parameter('error', type=types.IntType,
				flags=Instrument.FLAG_GET)

		self.add_parameter('value', type=types.FloatType,
				flags=Instrument.FLAG_GET,
				tags=['measure'])

		self.add_parameter('output_items', type=types.IntType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
				minval=0, maxval=15,
				option_map=_multiopts({OUTPUT_ITEMS[i]: i for i in OUTPUT_ITEMS})
		
		self.add_parameter('output_format', type=types.IntType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
				minval=0, maxval=4,
				option_map={OUTPUT_FORMATS[i]: i for i in OUTPUT_FORMATS}
		
		self.add_parameter('output_lines', type=types.IntType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
				minval=0, maxval=2,
				option_map={OUTPUT_LINES[i]: i for i in OUTPUT_LINES}
		
		self.add_function('set_defaults')
		self.add_function('self_test')
		self.add_function('read')
		self.set_defaults()
	
	def set_defaults(self):
		'''
		Set default parameters.
		
		This is done by first restoring factory default values, and then
		changing anything the author of this code likes to have different
		by default. Note that this function reflects the author's group's
		preferences and that other groups may want to modify this method
		for their own implementation of QTLab.
		'''
		# Restore factory defaults
		self.self_test([0])

		# Set our preferred defaults for as far as they differ from the
		# factory defaults
		self._visains.write(_set_data_format_cmd(
					'measure', 'ASCII_noprefix_nosuffix', 'onesample'))
		self.set_compliance(8e-9)

	def self_test(self, whichtest=[1,2]):
		'''
		Perform one or more self tests and/or restore factory defaults.
		Available tests:
			0: Restore factory defaults
			1: Memory test
			2: Display test
		Default: memory test and display test
		'''
		if type(whichtest) is int:
			whichtest = [whichtest]
		cmd = ''.join(['J{:d}X'.format(i) for i in whichtest])
		self._visains.write(cmd)

	def do_set_function(self, func):
		'''Set the source and measurement function.'''
		self._visains.write('F{:d},{:d}X'.format(*func))
		return True

	def do_set_range(self, rng):
		'''Set the measurement range.'''
		self._visains.write('{:s}X'.format(_set_bias_range_delay_cmd(rng=rng)))
		return True

	def do_set_zero(self, zero):
		'''Set whether to use zero calibration.'''
		#self._visains.write('Z%dX' % zero)
		#return True
		raise NotImplementedError(
				'This instrument does not appear to have a command'
				'for automatic offset nulling.')

	def do_get_zero_value(self):
		raise NotImplementedError(
				'This instrument does not appear to have a command'
				'for reading the offset null.')
		#return self._visains.ask('U4')

	def do_set_zero_value(self, val):
		'''Set the zero calibration value.'''
		#self._visains.write('V%EX' % val)
		raise NotImplementedError(
				'This instrument does not appear to have a command'
				'for manual offset nulling.')

	def do_set_rate(self, rate):
		'''Set the rate and precision.'''
		#self._visains.write('R%dX' % rate)
		#return True
		raise NotImplementedError(
				'This instrument does not appear to have a command'
				'for setting the rate.')

	def do_set_filter(self, val):
		'''Set filter type.'''
		self._visains.write('P{:d}X'.format(val))
		return True

	def do_set_trigger(self, trig):
		'''
		Set trigger source, input trigger timing, output trigger timing
		and whether to generate a trigger pulse at the end of a sweep.
		Arguments (all optional):
			src:   input trigger source
			t_in:  input trigger timing
			t_out: output trigger timing
			end:   whether or not to generate an output trigger at the
			       end of a sweep
		Arguments must be tupled, and None values must be inserted at
		the positions of any arguments you do not want to provide.
		'''
		(src, t_in, t_out, end) = trig
		if type(end) is bool:
			end = int(end)
		self._visains.write('T{:s},{:s},{:s},{:s}X'.format(
				_opt(src), _opt(t_in), _opt(t_out), _opt(end)))
		return True

	def do_set_delay(self, val):
		'''Set delay after trigger before taking a measurement.'''
		self._visains.write('{:s}X'.format(
				_set_bias_range_delay_cmd(delay=val)))
		return True

	def do_set_interval(self, val):
		'''Set trigger interval.'''
		raise NotImplementedError(
				'This instrument does not appear to have a command'
				'for setting the trigger interval.')
		#self._visains.write('Q%d' % val)
		#return True

	def do_set_compliance(self, compliance):
		self._visains.write('L{:.2E},X'.format(compliance))
	
	def do_get_error(self):
		'''Read the error condition.'''
		return self.get_status(1)

	def get_status(self, whichstatus='all'):
		'''
		Read one of the instrument's statuses.
		The following statuses are available:
			 0: Model no. and revision
			 1: Error status word
			 2: Stored ASCII string
			 3: Machine status word
			 4: Measurement parameters
			 5: Compliance value
			 6: Suppression value
			 7: Calibration status word
			 8: Defined sweep size
			 9: Warning status word
			10: First sweep point in compliance
			11: Sweep measure size
		Multiple statuses can be read by providing a list or
		'all' as the status specifyer.
		'''
		if whichstatus is 'all':
			whichstatus = list(range(12))
		if isinstance(whichstatus, list):
			return [get_status(i) for i in whichstatus]
		else:
			return self._visains.ask('U{:d}X'.format(whichstatus))
	
	def read(self):
		'''Read a value if not in external trigger mode.'''
		mode = self.get_trigger(query=False)
		if mode in (0, 1):
			ret = self._visains.ask('')
		elif mode in (2, 3):
			ret = self._visains.ask('X')
		elif mode in (4, 5):
			ret = self._visains.ask('GET')
		return float(ret)

	def do_get_value(self):
		return self.read()

