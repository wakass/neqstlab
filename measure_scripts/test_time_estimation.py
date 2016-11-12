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
ax1.begin = 0.
ax1.end = 10.
ax1.stepsize = 1.
ax1.instrument = 'dsgen1'
ax1.label = 'x'
ax1.module_options = {'dac':5, 
						'name':'s1f',
						'rate_stepsize':.5,
						'rate_delay': 10.,
						'var':'amplitude',
						'setalways':1,
# 						'postcall': some_function,
						'gain':1. }


import copy

ax2 = copy.deepcopy(ax1)
ax2.label = 'y'
ax2.instrument='dsgen2'

ax3 = copy.deepcopy(ax1)
ax3.label = 'z'
ax3.instrument='dsgen3'


z = ps.param()
z.label = 'z_one'
z.module = lambda: dsgen1.get_amplitude()

z_set = ps.param()
z_set.label = 'z_two'
z_set.module = lambda: dsgen3.get_amplitude()


import time
global b_time
b_time = time.time()
def taketime():
	global b_time
	diff_time = time.time() - b_time
	b_time = time.time()
	return diff_time*1000
timer = ps.param()
timer.label = 'time (ms)'
timer.module = lambda: taketime()



ping = ps.parspace()

ping.add_param(ax1)
ping.add_param(ax2)
ping.add_param(ax3)


ping.add_paramz(timer)
ping.add_paramz(z)
ping.add_paramz(z_set)

ping.set_traversefuncbyname('sweep',n=7,sweepback=False)
ping.set_name('time_estimation')

#set initial starting values to check time estimation algorithm
dsgen1.set_amplitude(ax1.begin)
dsgen2.set_amplitude(ax2.begin)
dsgen3.set_amplitude(ax3.begin)


ping.estimate_time()
#reset the timer
b_time = time.time()
ping.traverse()

#references to objects are kept so updating them is possible without re-adding

#ax2.end=11
#ping.estimate_time()
# ping.traverse()

