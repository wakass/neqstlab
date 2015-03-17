'''
cv.py: measurement script for C-V measurements
Author: Zeust the Unoobian <2noob2banoob@gmail.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
'''

import numpy
import time
import qt

class CVStepTimeout(Exception):
	def __init__(self, *args, **kwargs):
		args = ('CV-measurement step timed out',) + args
		Exception.__init__(self, *args, **kwargs)

class CVStepReadyChecker:
	'''
	Base class for checking if a C-V measurement is ready for the next
	source voltage step. This class has to be extended.
	'''
	def __init__(self, minwait, maxwait, waitafter,
			exceptontimeout, Vsrc, Vold):
		'''
		Constructor.
		You might want to override this to add more properties, although
		this is optional.
		'''
		self.minwait = minwait
		self.maxwait = maxwait
		self.waitafter = waitafter
		self.tout_except = exceptontimeout
		self.Vsrc = Vold
		self.restart(Vsrc)

	def restart(self, Vsrc):
		'''
		Reset the starttime and completetime properties after a voltage
		step.
		'''
		self.starttime = time.time()
		self.completetime = None
		self.Vold = self.Vsrc
		self.Vsrc = Vsrc

	def check_ready_crit(self, Vmeas):
		'''
		Check if some criterion for being ready for the next source
		voltage step is being met.
		This function has to be overridden in a subclass.
		'''
		raise NotImplementedError()

	def check_ready(self, t_now, Vmeas):
		'''
		Check if the measurement is ready for the next source voltage
		step. This function works by means of a check_ready_crit()
		function that is implemented in a subclass, while governing the
		minimum and maximum times between two source voltage steps.
		Overriding this function is not recommended, override
		check_ready_crit() instead.
		'''
		if self.completetime is not None:
			return t_now > self.completetime + self.waitafter
		else:
			t_rel = t_now - self.starttime
			if t_rel > self.minwait and self.check_ready_crit(t_now, Vmeas):
				self.completetime = t_now
				return self.waitafter == 0.
			elif t_rel > self.maxwait:
				if self.tout_except:
					raise CVStepTimeout()
				else:
					self.completetime = t_now
					return self.waitafter == 0.
			return False

class CVDefaultStepReadyChecker(CVStepReadyChecker):
	'''Default instrument-independent CVStepReadyChecker'''
	def __init__(self, Vsrc, Vold, wait_stepfrac=.95, minwait=5.,
			maxwait=60., waitafter=0., exceptontimeout=False):
		CVStepReadyChecker.__init__(self, minwait, maxwait, waitafter,
				exceptontimeout, Vsrc, Vold)
		self.wait_stepfrac = wait_stepfrac

	def check_ready_crit(self, Vmeas):
		return ((Vmeas - self.Vold) / (self.Vsrc - self.Vold) >
				self.wait_stepfrac)

class CVSMUStepReadyChecker(CVStepReadyChecker):
	'''Instrument-specific CVStepReadyChecker for Keithley236 SMU'''
	def __init__(self, ins, minwait=5., maxwait=60., waitafter=5.):
		CVStepReadyChecker.__init__(self, minwait, maxwait, waitafter,
				True, None, None)
		if isinstance(ins, str):
			ins = qt.get_instruments()[ins]
		self.ins = ins

	def check_ready_crit(self, Vmeas):
		return not self.ins.get_hit_compliance()

def CV(
		devicename,
		Vstart,
		Vend,
		Vstep,
		smu_ins,
		vmeas_ins,
		imeas_ins=None,       # Use SMU by default
		sweepback=True,       # Go back and forth to check hysteresis
		smu_var='bias',
		smu_gain=1.,
		imeas_var='value',
		imeas_gain=1.,
		vmeas_var='readlastval',
		vmeas_gain=1.,
		rate_delay=19.,       # in ms
		rate_stepsize=0.001,  # in Volts for Keithley
		measname_fmt='cv_{:s}',
		readychecker=None,
		tmeas=100e-3
		):
	'''C-V measurement'''
	# Some constants and initial values
	measname = measname_fmt.format(devicename)
	Vmeas = 0.
	(vmeas_gain, imeas_gain) = (float(vmeas_gain), float(imeas_gain))
	if imeas_ins is None:
		imeas_ins = smu_ins
	# Set ramp rate
	smu_ins.set_parameter_rate(smu_var, rate_stepsize, rate_delay)
	# Create data structure
	data = qt.Data(name=measname)
	data.add_coordinate('time (s)')
	data.add_coordinate('Vsrc (V)',
			size=abs((Vend - Vstart) / Vstep), start=Vstart, end=Vend)
	data.add_value('Vmeas (V)')
	data.add_value('Imeas (nA)')
	# Create array of source values
	Vsrcvals = numpy.arange(Vstart, Vend+Vstep/2., Vstep)
	if sweepback:
		Vsrcvals = numpy.append(Vsrcvals, Vsrcvals[-2::-1])
	# Start measurement
	qt.mstart()
	qt.Plot2D(data, name='C-V measurement', coorddim=0, valdim=3,
			traceofs=10, autoupdate=False)
	if readychecker is None:
		readychecker = CVDefaultStepReadyChecker(0., 0.)
	try:
		for Vsrc in Vsrcvals:
			Vmeas = None
			readychecker.restart(Vsrc)
			t = time.time()
			smu_ins.set(smu_var, Vsrc)
			while not readychecker.check_ready(t, Vmeas):
				(t, Vmeas, Imeas) = (
						time.time(),
						vmeas_ins.get(vmeas_var) / vmeas_gain,
						imeas_ins.get(imeas_var) / imeas_gain)
				data.add_data_point(t, Vsrc, Vmeas, Imeas)
				qt.msleep(tmeas)
	except KeyboardInterrupt:
		print('Measurement interrupted, will save data so far')
	except CVStepTimeout:
		print('Source value {:f} not reached, aborting measurement'
				.format(Vsrc))
	qt.mend()
	data.close_file()
	print('Measurement finished')

def CV_default():
	smuperioret = qt.get_instruments()['SMUperioret']
	elKeef = qt.get_instruments()['elKeefly']
	smuperioret.set_function((0, 0))
	smuperioret.set_bias_range(2)
	smuperioret.set_meas_range(2)
	smuperioret.set_compliance(8e-9)
	smuperioret.set_operate(True)
	CV('dummy', 0., 2., .1, smuperioret, elKeef)

CV_default()

