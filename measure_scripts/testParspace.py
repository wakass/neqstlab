#elMeasure
#eefje = qt.instruments.create('Eefje','IVVI',address='COM1')
#elKeef = qt.instruments.create('ElKeefLy','Keithley_2000',address='GPIB::17')

dsgen1 = qt.instruments.create('dsgen1', 'dummy_signal_generator')
dsgen2 = qt.instruments.create('dsgen2', 'dummy_signal_generator')
dsgen3 = qt.instruments.create('dsgen3', 'dummy_signal_generator')

import lib.parspace as ps
reload(ps)
from math import sin

ax1 = ps.param()
ax1.begin = 2.
ax1.end = 20.
ax1.stepsize = 1.
ax1.rate_stepsize = 1.
ax1.rate_delay = 40.
ax1.instrument = 'dsgen1'
ax1.label = 'x'
ax1.module_name = 's1f'#'dac','s1c'
ax1.module = lambda x: dsgen1.set_amplitude(x)

ax1.module_options = {'dac':5, 
						'rate_stepsize':1.,
						'rate_delay': 40.,
						'var':'amplitude',
						'amplification':'100M' }


ax2 = ps.param()
ax2.begin = 5.
ax2.end = 30.
ax2.stepsize = .1
ax2.label = 'y'
ax2.rate_stepsize = .5
ax2.rate_delay = 20.
ax2.instrument = 'dsgen2'
ax2.module_name = 's1f'#'dac','s1c'
ax2.module_options = {'dac':5, 
						'rate_stepsize':.05,
						'rate_delay': 20.,
						'var':'amplitude',
						'amplification':'100M' }
ax2.module = lambda x: dsgen2.set_amplitude(x)

import copy
ax3 = copy.deepcopy(ax2)
ax3.label = 'z'
ax3.instrument='dsgen3'
ax3.begin = 1.
ax3.end=4.
ax3.stepsize=1.

z = ps.param()
z.label = 'value'
z.module = lambda: dsgen1.get_amplitude() + dsgen2.get_amplitude() + dsgen3.get_amplitude()

import time
b_time = time.time()
def taketime():
	global b_time
	diff_time = time.time() - b_time
	b_time = time.time()
	return diff_time
timer = ps.param()
timer.label = 'time'
timer.module = lambda: taketime()

ping = ps.parspace()
ping.add_param(ax1)
ping.add_param(ax2)
# ping.add_param(ax3)

ping.add_paramz(timer)
# ping.add_paramz(z)

#ping.set_traversefunc(lambda axes,**lopts: ps.sweep_func_helper(axes,datablock='on',**lopts))
ping.set_traversefuncbyname('sweep',n=7,sweepback='off')
ping.traverse()

#references to objects are kept so updating them is possible without re-adding
# ax2.end=11
# ping.traverse()