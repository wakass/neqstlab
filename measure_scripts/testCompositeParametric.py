#elMeasure
#eefje = qt.instruments.create('Eefje','IVVI',address='COM1')
#elKeef = qt.instruments.create('ElKeefLy','Keithley_2000',address='GPIB::17')

dsgen1 = qt.instruments.create('dsgen1', 'dummy_signal_generator')
dsgen2 = qt.instruments.create('dsgen2', 'dummy_signal_generator')
combined_arb = qt.instruments.create('arb', 'virtual_composite_parametric')



import lib.parspace as ps
reload(ps)
from math import sin,pi


#numbers not accounting for gain (i.e. real output)
f1 = lambda x: 50*sin(x+0.2*pi) + 200
f2 = lambda x: 50*sin(x+0.5*pi) + 200

a= {
	'instrument': dsgen1,
	'parameter': 'amplitude',
	'function': f1,
	'gain':5.
	}
b= {
	'instrument': dsgen2,
	'parameter': 'amplitude',
	'function': f2,
	'gain':5.
	}

combined_arb.add_variable_combined('phase',[a,b])
qt.msleep(1.5) #allow for instruments to be registered


#safety maximum sweeps when the instruments are ill-defined
dsgen1.set_parameter_rate('amplitude',20,10)
dsgen2.set_parameter_rate('amplitude',20,10)

ds1=ps.param()
ds1.label ='amplitude'
ds1.instrument = 'dsgen1'
ds1.module_options ={ 
						'rate_stepsize':.02,
						'rate_delay': 100.,
						'var':'amplitude',
						'gain': 5.,
						'function': f1
							}
							
ds2=ps.param()
ds2.label ='amplitude'
ds2.instrument = 'dsgen2'
ds2.module_options ={ 
						'rate_stepsize':.02,
						'rate_delay': 100.,
						'var':'amplitude',
						'gain': 1.,
						'function':f2
							}

phasebyAxes =  ps.createCompositeParametricFromAxes('phase',[ds1,ds2])
phasebyAxes.begin = 0.
phasebyAxes.end = 2*pi
phasebyAxes.stepsize = 2*pi /5

phase=ps.param()
phase.label ='phase'
phase.begin = 0
phase.end = 2*pi
phase.stepsize = pi/100.
phase.instrument = 'arb'
phase.module_options ={ 
						'rate_stepsize':.02,
						'rate_delay': 100.,
						'var':'phase',
							}


d1=ps.param()
d1.label = 'd1'
d1.module = lambda: dsgen1.get_amplitude()

d2=ps.param()
d2.label = 'd2'
d2.module = lambda: dsgen2.get_amplitude()

ping = ps.parspace()
ping.add_param(phase)
ping.add_paramz(d1)
ping.add_paramz(d2)

ping.set_traversefuncbyname('sweep')

ping.traverse()