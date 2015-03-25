# Keithley_236.py driver for Keithley 236 SMU
# Zeust the Unoobian <2noob2banoob@gmail.com>
# Based on:
#   Keithley_199.py driver for Keithley 199 DMM
#   Reinier Heeres <reinier@heeres.eu>, 2009
#
# Most stuff also works for Keithley 237 and 238 but there are some
# slight differences, this is indicated with comments. Refer to the
# Keithley 236,237,238 User Manual for further details:
# http://www.download-service-manuals.com/download.php?file=Keithley-3526.pdf&SID=fp799cqduhurj3gh6rgsjr1ac5
# Section 3.6 of that document is of particular interest.
#
# The following commands are not implemented:
# * Modify Sweep List (A)
# * Calibration (C)
# * Display (D)
# * IEEE Immediate Trigger (H0X)
#   (although this one is used in read() under certain conditions)
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

import types
import visa
import re
import warnings
from instrument import Instrument

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

# Multi-use option maps
OPTMAP_RANGE = {
	0: 'auto',
	1: '1.1V / 1nA', # 1.5V for Keithley 238
	2: '11V / 10nA', # 15V for Keithley 238
	3: '110V / 100nA',
	4: '1uA', # Also 1.1kV for Keithley 237
	5: '10uA',
	6: '100uA',
	7: '1mA',
	8: '10mA',
	9: '100mA' }
	# 10 = 1A for Keithley 238

ERRORS = {
	25: 'Trigger Overrun '
		'(ignored trigger because still processing previous trigger)',
	24: 'IDDC (illegal command)',
	23: 'IDDCO (command with illegal option)',
	22: 'Interlock Present '
		'(Failed to set operate/standby or went to standby because '
		'of interlock condition)',
	21: 'Illegal Measure Range',
	20: 'Illegal Source Range',
	19: 'Invalid Sweep Mix (tried to mix pulsed and non-pulsed sweeps)',
	18: 'Log Cannot Cross Zero '
		'(tried to create logarithmic sweep that passes zero)',
	17: 'Autoranging Source with Pulse Sweep',
	16: 'In Calibration '
		'(tried to send non-calibration command while in calibration mode)',
	15: 'In Standby (tried to send calibration command while in standby mode)',
	14: 'Unit is a 236 (Tried 1.1kV calibration command on Keithley 236)',
	13: 'IOU DPRAM Failed (dual-port RAM in I/O controller failed)',
	12: 'IOU EEROM Failed (EEROM in I/O controller failed)',
	11: 'IOU Cal. Checksum Error '
		'(checksum of calibration constants does not match)',
	10: 'DPRAM Lockup '
		'(ROM/RAM failure in source/measure controller which consequentially '
		'does not respond to the I/O controller)',
	 9: 'DPRAM Link Error '
		'(Communication error in dual-port RAM between I/O controller and '
		'source/measure controller',
	 8: 'Cal. ADC Zero Error (Calibration constant outside expected range)',
	 7: 'Cal. ADC Gain Error (Calibration constant outside expected range)',
	 6: 'Cal. SRC Zero Error (Calibration constant outside expected range)',
	 5: 'Cal. SRC Gain Error (Calibration constant outside expected range)',
	 4: 'Cal. Common Mode Error (error calibrating common mode adjustment)',
	 3: 'Cal. Compliance Error (compliance during calibration procedure)',
	 2: 'Cal. Value Error '
		'(Entered calibration constant outside '
		'expected range for current step)',
	 1: 'Cal. Constants Error '
		'(Calibration constants outside limits during power-up)',
	 0: 'Cal. Invalid Error '
		'(compliance error during power-up, '
		'factory initialisation DCL or SDC)' }

WARNINGS = {
	9: 'Uncalibrated (illegal calibration constants stored in EEROM)',
	8: 'Temporary Cal '
		'(enter or exit calibration mode when CAL LOCK is LOCKED)',
	7: 'Value Out of Range '
		'(bias, compliance or step size incompatible with range)',
	6: 'Sweep buffer Filled',
	5: 'No Sweep Points; Must Create sweep (try to modify non-existent sweep)',
	4: 'Pulse Times Not Met',
	3: 'Not in Remote',
	2: 'Measurement Range Changed Due to 1kV/100mA or 110V/1A Range Select',
	1: 'Measurement Overflow (OFLO) / Sweep Aborted',
	0: 'Pending Trigger (trigger sent while processing other command)' }

# Regular expressions
#####################
_REGEX_STATUS1 = re.compile('ERS([01]{26})')
_REGEX_STATUS3 = re.compile('MSTG(0\d|1[1-5]),([0-4]),([0-2])'
		'K([0-3])M([01]\d{2}),([01])N([01])R([01])'
		'T([0-4]),([0-8]),([0-8]),([01])V([01])Y([0-4])')
_REGEX_STATUS4 = re.compile('[IV]MPL,(0\d|10)F([01]),([01])'
		'O([01])P([0-5])S([0-3])W([01])Z([01])')
_REGEX_STATUS9 = re.compile('ERS([01]{10})')

def _interpret_status3(s):
	'''((G1,G2,G3), K, (M1,M2), N, R, (T1,T2,T3,T4), V, Y)'''
	try:
		m = tuple([int(i) for i in re.match(_REGEX_STATUS3, s).groups()])
		return (m[:3], m[3], m[4:6], m[6], m[7], m[8:12], m[12], m[13])
	except Exception as e:
		e.args = ('Got invalid status(3) string \'{:s}\''.format(s),) + e.args
		raise

def _interpret_status4(s):
	'''(L2, (F1,F2), O, P, S, W, Z)'''
	try:
		m = tuple([int(i) for i in re.match(_REGEX_STATUS4, s).groups()])
		return (m[0], m[1:3], m[3], m[4], m[5], m[6], m[7])
	except Exception as e:
		e.args = ('Got invalid status(4) string \'{:s}\''.format(s),) + e.args
		raise

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
		return '' if val is None else str(val)

def _print(s):
	pass

# Some command generators, all excluding the trailing X that would lead
# to immediate execution
#######################################################################

def _set_bias_range_delay_cmd(bias=None, rng=None, delay=None):
	'''Generate command to set bias, range and delay'''
	return 'B{:s},{:s},{:s}'.format(_opt(bias), _opt(rng), _opt(delay))

def _set_data_format_cmd(items=None, fmt=None, lines=None):
	'''Generate command to set data format.'''
	if type(items) is list:
		items = sum([(OUTPUT_ITEMS[i] if i in OUTPUT_ITEMS else i) for i in items])
	return 'G{:s},{:s},{:s}'.format(_opt(items, OUTPUT_ITEMS),
			_opt(fmt, OUTPUT_FORMATS), _opt(lines, OUTPUT_LINES))

# Exception classes
###################

class _Keithley236BaseException:
	'''
	Base class to generate exception from error and warning flags.
	Should not be directly instantiated but rather extended into
	separate error and warning classes which also has to derive from
	BaseException or one of its subclasses.
	'''
	def __init__(self, err, warn):
		for i in ERRORS:
			if err & 2**i:
				self.args += ('ERROR: {:s}'.format(ERRORS[i]),)
		for i in WARNINGS:
			if warn & 2**i:
				self.args += ('WARNING: {:s}'.format(WARNINGS[i]),)

class Keithley236Error(RuntimeError, _Keithley236BaseException):
	'''Keithley 236 error exception class'''
	def __init__(self, err, warn):
		RuntimeError.__init__(self)
		_Keithley236BaseException.__init__(self, err, warn)

class Keithley236Warning(RuntimeWarning, _Keithley236BaseException):
	'''Keithley 236 warning exception class'''
	def __init__(self, warn):
		RuntimeWarning.__init__(self)
		_Keithley236BaseException.__init__(self, 0, warn)

# The actual class
##################

class Keithley_236(Instrument):

	def __init__(self, name, address=None):
		Instrument.__init__(self, name, tags=['measure', 'sweep'])

		self._address = address
		self._visains = visa.instrument(address)

		self._buffered_cmd = ''

		self.add_parameter('function', type=types.TupleType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_GET,
				option_map={
					(0,0): 'DC_Vsrc_Imeas',
					(0,1): 'Sweep_Vsrc_Imeas',
					(1,0): 'DC_Isrc_Vmeas',
					(1,1): 'Sweep_Isrc_Vmeas'
				})

		self.add_parameter('bias', type=types.FloatType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET)

		self.add_parameter('bias_range', type=types.IntType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
				minval=0, maxval=9, #maxval=10 for Keithley 238
				option_map=OPTMAP_RANGE)

		self.add_parameter('meas_range', type=types.IntType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_GET,
				minval=0, maxval=9, #maxval=10 for Keithley 238
				option_map=OPTMAP_RANGE)

		self.add_parameter('compliance', type=types.FloatType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_GET)

		self.add_parameter('filter', type=types.IntType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_GET,
				option_map={
					0: 'No filter',
					1: '2-reading filter',
					2: '4-reading filter',
					3: '8-reading filter',
					4: '16-reading filter',
					5: '32-reading filter'
				})

		self.add_parameter('trigger_origin', type=types.IntType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_GET,
				option_map={
					0: 'IEEE X',
					1: 'IEEE GET',
					2: 'IEEE Talk',
					3: 'External',
					4: 'Immediate (Front panel or command)'
				})

		self.add_parameter('trigger_timing', type=types.IntType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_GET,
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

		self.add_parameter('trig_out_timing', type=types.IntType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_GET,
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

		self.add_parameter('trig_out_sweepend', type=types.BooleanType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_GET)

		self.add_parameter('delay', type=types.IntType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_SOFTGET,
				minval=0, maxval=65000, units='msec')

		self.add_parameter('error', type=types.IntType,
				flags=Instrument.FLAG_GET)

		self.add_parameter('warning', type=types.IntType,
				flags=Instrument.FLAG_GET)

		self.add_parameter('value', type=types.FloatType,
				flags=Instrument.FLAG_GET,
				tags=['measure'])

		self.add_parameter('output_items', type=types.IntType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_GET,
				minval=0, maxval=15,
				option_map=_multiopts({OUTPUT_ITEMS[i]: i for i in OUTPUT_ITEMS}))

		self.add_parameter('output_format', type=types.IntType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_GET,
				minval=0, maxval=4,
				option_map={OUTPUT_FORMATS[i]: i for i in OUTPUT_FORMATS})

		self.add_parameter('output_lines', type=types.IntType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_GET,
				minval=0, maxval=2,
				option_map={OUTPUT_LINES[i]: i for i in OUTPUT_LINES})

		self.add_parameter('operate', type=types.BooleanType,
				flags=Instrument.FLAG_SET | Instrument.FLAG_GET)

		self.add_parameter('hit_compliance', type=types.BooleanType,
				flags=Instrument.FLAG_GET)

		self.add_function('set_defaults')
		self.add_function('self_test')
		self.add_function('read')

	def _get_errwarn(self, whichword, regex):
		'''Get error or warning condition as int representing flags'''
		errword = self.get_status(whichword)
		try: 
			err = [int(i) for i in re.match(regex, errword).group(1)]
			return sum([2**i * err[-i-1] for i in range(len(err))])
		except AttributeError:
			print('Got invalid status word {:d}: {:s}'
					.format(whichword, errword))

	def check_error(self):
		'''Check for any errors and warnings and report them'''
		(err, warn) = (self.get_error(), self.get_warning)
		if err:
			raise Keithley236Error(err, warn)
		elif warn:
			warnings.warn(Keithley236Warning(warn))

	def test_check_error(self, err, warn):
		'''
		Test case for check_error() where you specify the error and
		warning flag ints yourself
		'''
		if err:
			raise Keithley236Error(err, warn)
		elif warn:
			warnings.warn(Keithley236Warning(warn))

	def get_serial_poll_byte(self):
		'''
		Acquire the instrument's serial poll byte and reset it by
		writing 0 to  the SRQ mask.
		TODO: read the actual value of the mask and write it back
		instead of writing a default value.
		'''
		spb = self._visains._GpibInstrument__get_stb()
		self.write('M0,X')
		return spb

	def write(self, cmd):
		_print(cmd)
		self._visains.write(cmd)

	def ask(self, cmd):
		ret = self._visains.ask(cmd)
		_print('{:s} -> {:s}'.format(cmd, ret))
		return ret

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
		#self.self_test([0])

		# Set our preferred defaults for as far as they differ from the
		# factory defaults
		self.set_output_items(4)
		self.set_output_format(2)
		self.set_output_lines(0)
		self.set_bias_range(2)
		self.set_bias(0)
		self.set_meas_range(2)
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
		self.write(cmd)

	def do_set_bias(self, bias):
		'''Set bias'''
		self.write('{:s}X'.format(_set_bias_range_delay_cmd(bias=bias)))

	def do_set_output_items(self, items):
		'''Set output items'''
		self.write(_set_data_format_cmd(items, None, None) + 'X')

	def do_set_output_format(self, fmt):
		'''Set output format'''
		self.write(_set_data_format_cmd(None, fmt, None) + 'X')

	def do_set_output_lines(self, lines):
		'''Set output format lines'''
		self.write(_set_data_format_cmd(None, None, lines) + 'X')

	def do_set_function(self, func):
		'''Set the source and measurement function.'''
		self.write('F{:d},{:d}X'.format(*func))
		return True

	def do_set_bias_range(self, rng):
		'''
		Set the bias range.
		Note that this may or may not also affect the measurement range.
		'''
		self.write('{:s}X'.format(_set_bias_range_delay_cmd(rng=rng)))
		return True

	def do_set_meas_range(self, rng):
		'''
		Set the measurement range.
		Note that this may or may not also affect the bias range.
		'''
		self.write('L,{:d}X'.format(rng))
		return True

	def do_set_filter(self, val):
		'''Set filter type.'''
		self.write('P{:d}X'.format(val))
		return True

	def _set_trigger(self, trig):
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
		self.write('T{:s},{:s},{:s},{:s}X'.format(
				_opt(src), _opt(t_in), _opt(t_out), _opt(end)))
		return True

	def do_set_trigger_origin(self, orig):
		'''Set the trigger origin'''
		self._set_trigger((orig, None, None, None))

	def do_set_trigger_timing(self, t_in):
		'''Set the input trigger timing'''
		self._set_trigger((None, t_in, None, None))

	def do_set_trig_out_timing(self, t_out):
		'''Set the output trigger timing'''
		self._set_trigger((None, None, t_out, None))

	def do_set_trig_out_sweepend(self, end):
		'''Set whether to generate output trigger on sweep end'''
		self._set_trigger((None, None, None, end))

	def do_set_delay(self, val):
		'''Set delay after trigger before taking a measurement.'''
		self.write('{:s}X'.format(
				_set_bias_range_delay_cmd(delay=val)))
		return True

	def do_set_compliance(self, compliance):
		self.write('L{:.2E},X'.format(compliance))

	def do_get_error(self):
		'''Read the error condition and return as int representing flags.'''
		return self._get_errwarn(1, _REGEX_STATUS1)
	
	def do_get_warning(self):
		'''Read the warning condition and return as int representing flags.'''
		return self._get_errwarn(9, _REGEX_STATUS9)

	def do_set_operate(self, operate):
		'''Set the SMU in operate or standby mode'''
		self.write('N{:d}X'.format(operate))

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
			return [self.get_status(i) for i in whichstatus]
		else:
			return self.ask('U{:d}X'.format(whichstatus))

	def read(self):
		'''Read a value if not in external trigger mode.'''
		if self.get_trigger_timing() == 0:
			strval = self._visains.read()
			_print('<empty> -> {:s}'.format(strval))
		else:
			strval = self.ask('H0X')
		try:
			return float(strval)
		except:
			print('read failed')
			return self.read()

	def do_get_value(self):
		'''Get measurement value'''
		return self.read()

	def do_get_compliance(self):
		'''Get compliance value'''
		cplstr = self.get_status(5)
		if cplstr[:3] in ('ICP', 'VCP'):
			return float(cplstr[3:])
		else:
			raise RuntimeError(
					'Keithley 236: read invalid compliance '
					'status string \'{:s}\''.format(cplstr))

	def do_get_output_items(self):
		'''Get output items in flag-int format'''
		return _interpret_status3(self.get_status(3))[0][0]

	def do_get_output_format(self):
		'''Get output format'''
		return _interpret_status3(self.get_status(3))[0][1]

	def do_get_output_lines(self):
		'''Get output lines'''
		return _interpret_status3(self.get_status(3))[0][2]

	def do_get_eoi_and_bus_holdoff(self):
		'''Get EOI and bus hold-off (not implemented as parameter)'''
		return _interpret_status3(self.get_status(3))[1]

	def do_get_srq_mask(self):
		'''Get SRQ (Service ReQuest) mask (not implemented as parameter)'''
		return _interpret_status3(self.get_status(3))[2][0]

	def do_get_hit_compliance(self):
		'''
		Check if measured value hits compliance value.
		Note that the returned value may represent a histirocal state;
		it will be True if the compliance has been hit at any moment
		since the last time the serial poll byte was reset.
		Also note that this function will reset the serial poll byte.
		'''
		return bool(self.get_serial_poll_byte() & 128)

	def do_get_operate(self):
		'''Check whether operating or in standby'''
		return bool(_interpret_status3(self.get_status(3))[3])

	def do_get_trigger_enable(self):
		'''See if triggers are enabled (not implemented as parameter)'''
		return bool(_interpret_status3(self.get_status(3))[4])

	def do_get_trigger_origin(self):
		'''Get input trigger origin'''
		return _interpret_status3(self.get_status(3))[5][0]

	def do_get_trigger_timing(self):
		'''Get input trigger timing'''
		return _interpret_status3(self.get_status(3))[5][1]

	def do_get_trig_out_timing(self):
		'''Get output trigger timing'''
		return _interpret_status3(self.get_status(3))[5][2]

	def do_get_trig_out_sweepend(self):
		'''See if there's an output trigger at the end of a sweep'''
		return _interpret_status3(self.get_status(3))[5][3]

	def do_get_1100V_range(self):
		'''
		See if 1100 Volt range is enabled (not implemented as parameter)
		(Keithley 237 only)
		'''
		return bool(_interpret_status3(self.get_status(3))[6])

	def do_get_terminator(self):
		'''Check output line terminator (not implemented as parameter)'''
		return _interpret_status3(self.get_status(3))[7]

	def do_get_meas_range(self):
		'''Get measurement range'''
		return _interpret_status4(self.get_status(4))[0]

	def do_get_function(self):
		'''Get measurement range'''
		return _interpret_status4(self.get_status(4))[1]

	def do_get_sense(self):
		'''Get output sense (local/remote) (not implemented as parameter)'''
		return _interpret_status4(self.get_status(4))[2]

	def do_get_filter(self):
		'''Get filter specification'''
		return _interpret_status4(self.get_status(4))[3]

	def do_get_integration_time(self):
		'''Get integration time specification (not implemented as parameter)'''
		return _interpret_status4(self.get_status(4))[4]

	def do_get_default_delay(self):
		'''Check if default delay is enabled (not implemented as parameter)'''
		return bool(_interpret_status4(self.get_status(4))[5])

	def do_get_suppression(self):
		'''Check if suppression is enabled (not implemented as parameter)'''
		return bool(_interpret_status4(self.get_status(4))[6])
