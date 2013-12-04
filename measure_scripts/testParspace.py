#elMeasure
#eefje = qt.instruments.create('Eefje','IVVI',address='COM1')
#elKeef = qt.instruments.create('ElKeefLy','Keithley_2000',address='GPIB::17')

dsgen1 = qt.instruments.create('dsgen1', 'dummy_signal_generator')
dsgen2 = qt.instruments.create('dsgen2', 'dummy_signal_generator')

import lib.parspace as ps
reload(ps)
from math import sin

ax1 = ps.param()
ax1.begin = 2.
ax1.end = 10.
ax1.stepsize = 1.
ax1.rate_stepsize = .5
ax1.rate_delay = 55
ax1.instrument = 'dsgen1'
ax1.instrument_opt = 'amplitude'
ax1.module = lambda x: dsgen1.set_amplitude(x)


ax2 = ps.param()
ax2.begin = 5.
ax2.end = 10.
ax2.stepsize = 1.
ax2.rate_stepsize = .5
ax2.rate_delay = 55
ax2.instrument = 'dsgen2'
ax2.instrument_opt = 'amplitude'
ax2.module = lambda x: dsgen2.set_amplitude(x)

z = ps.param()
z.module = lambda: dsgen1.get_amplitude() + dsgen2.get_amplitude()


ping = ps.parspace()
ping.add_param(ax1)
ping.add_param(ax2)
# ping.add_param(ax2)
ping.add_paramz(z)

ping.set_traversefunc(lambda axes,**lopts: ps.sweep_func_helper(axes,datablock='on',**lopts))
ping.set_traversefuncbyname('sweep',n=3,sweepback='off')
ping.traverse()