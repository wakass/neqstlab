#Parameterspace.py 
#Defines classes and functions to span and traverse a parameter space in the qtlab environment.


# from pylab import *
import numpy as np
from time import time,sleep
import os
import qt

curve = np.zeros((0,2))

class Bunch:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

def get_cell_value(cell):
    return type(lambda: 0)(
        (lambda x: lambda: x)(0).func_code, {}, None, None, (cell,)
    )()
    
def _estimate_time_recur(axes, sweepback):
	'''
	Helper function for estimating execution time in seconds
	Assumes rate_delay values to be in milliseconds
	'''
	mod = axes[0].module_options
	
	x=Bunch
	x = {}
	ax=axes[0]
	x['time']  = np.abs(ax.begin - ax.end) / (mod['rate_stepsize'] / (mod['rate_delay']/1000.))
	x['steps'] = np.abs(ax.begin - ax.end) / np.abs(ax.stepsize)
	x['label'] = ax.label
	x['range'] = np.abs(ax.begin - ax.end)
	x['speed'] = mod['rate_stepsize'] / (mod['rate_delay']/1000.)
	print 'For %(label)s one sweep %(time)g seconds with %(steps)d steps. Range %(range)g speed %(speed)g' % x

	# Lowest-level axis
	if len(axes) == 1:
		return 1e-3 * mod['rate_delay'] * np.abs(
				(axes[0].begin - axes[0].end) / mod['rate_stepsize'])
	# Not lowest-level axis
	else:
		delay_per_step = 1e-3 * mod['rate_delay'] * (
				float(axes[0].stepsize) / mod['rate_stepsize'])
		steps = int(np.ceil(np.abs(
				(axes[0].begin - axes[0].end) / axes[0].stepsize)))
		vals = steps + 1
		if not sweepback:
			vals = 2 * vals - 1
		lower_level_time = _estimate_time_recur(axes[1:], sweepback)
		return steps * delay_per_step + vals * lower_level_time

def _estimate_time_hilbert(axes, n):
	'''
	Helper function for hilbert execution time in seconds
	Assumes rate_delay values to be in milliseconds
	'''
	mod = axes[0].module_options
	raise 'not implemented yet'
	#euclidian length of the curve = 2^n - 1/2^n
	

#generator version of hilbert space function
def hilbert_it(x0, y0, xi, xj, yi, yj, n):
    if n <= 0:
        X = x0 + (xi + yi)/2
        Y = y0 + (xj + yj)/2
        
        # Output the coordinates of the cv
        yield {'dp':[X,Y]}

    else:
        for i in hilbert_it(x0,               y0,               yi/2, yj/2, xi/2, xj/2, n - 1):
            yield i
        for i in hilbert_it(x0 + xi/2,        y0 + xj/2,        xi/2, xj/2, yi/2, yj/2, n - 1):
            yield i
        for i in hilbert_it(x0 + xi/2 + yi/2, y0 + xj/2 + yj/2, xi/2, xj/2, yi/2, yj/2, n - 1):
            yield i
        for i in hilbert_it(x0 + xi/2 + yi,   y0 + xj/2 + yj,  -yi/2,-yj/2,-xi/2,-xj/2, n - 1):
            yield i

def hilbert_gen(xs, n=3,**lopts):
	return hilbert_it(xs[0].begin, xs[1].begin, xs[0].end-xs[0].begin, 0,0, xs[1].end-xs[1].begin, n)
	
def hilbert_mul(xs,n=3,**lopts):
	if len(xs) < 2:
		raise Exception('Only works on 2d or more')
	if len(xs) > 2:
		for i in sweep_gen(xs[:-2],**lopts):
			for j in hilbert_it(xs[-2].begin, xs[-1].begin, xs[-2].end-xs[-2].begin, 0,0, xs[-1].end-xs[-1].begin, n):
				yield {'dp': np.append(i['dp'],j['dp']), 'newblock':i['newblock']}
	else:
		for i in hilbert_gen(xs,**lopts):
			yield i

def sweep_gen(xs,**lopts):
	#options are sweepback and datablock bit
	#sets the datablock bit in the part of a dict
	#first part of the tuple is always the list datapoints to set
	
	lopts['flipbit']=0
	for a in sweep_gen_helper(xs,**lopts):
		yield a
		
def star_gen(xs,**lopts):
	#generates a 'star' in parspace by tracing each axis seperately.
	#one could call it traceaxes, but meh.
	for i,x in enumerate(xs):
		beginnings = map(lambda x: getattr(x,'begin'),xs)
		for a in sweep_gen_helper([x],**lopts):	
			beginnings[i] = a['dp'][0]
			a['dp'] = beginnings
			yield a
						
def sweep_gen_helper(xs,**lopts):
	x = xs[0]
	u = np.arange(x.begin,x.end,x.stepsize)
	
	u = np.linspace(x.begin,x.end,round(np.abs((x.end-x.begin)/x.stepsize) +1)) #round here because we need an integer and not a weird outcome like ((.5-.2)/.1)==2.99999996..wtf
	

	if 'flipbit' in lopts and lopts['flipbit'] == 1:
		u = np.flipud(u)
	if len(xs) > 1:
		for i in u:
			for a in sweep_gen_helper(xs[1:],**lopts):
				yield {'dp': np.hstack(([i],a['dp'])),'newblock':a['newblock']}
			if 'sweepback' in lopts and lopts['sweepback'] == 'on':
				lopts['flipbit'] ^= 1
	else:
		for i in u[:-1]:
			yield {'dp': [i], 'newblock':0}
		yield {'dp': [u[-1]],'newblock':1}
		#and for each 'real' sweep (end of xs)
		#add a new datablock bit at the end if the option is set	
# 		if 'datablock' in lopts and lopts['datablock' == 'on'

def createCombinedFromAxes(axes):
	if 'combined_parspace' in qt.instruments.get_instruments():
		combined = qt.instruments.get_instruments()['combined_parspace']
	else:
		combined = qt.instruments.create('combined_parspace','virtual_composite')
	tocombine=axes
	master=None
	master_gain = None
	res=[]
	for i,p in enumerate(tocombine):
		if i == 0:
			master = p
			master_gain = p.module_options['gain']
			a= {
				'instrument': qt.instruments.get_instruments()[p.instrument],
				'parameter': p.module_options['var'],
				'scale': 1.,
				'offset': 0}
			res.append(a)
		else:
			scale = np.abs((p.begin - p.end) / (master.begin - master.end))*master_gain/p.module_options['gain']
			
			#logical or to determine direction of sweep relative to master
			if (p.begin > p.end) ^ (master.begin > master.end): #xor
				scale = -1*scale

			offset = p.begin/p.module_options['gain'] - scale*master.begin/master_gain
			
			
			a= {
				'instrument': qt.instruments.get_instruments()[p.instrument],
				'parameter': p.module_options['var'],
				'scale': scale,
				'offset': -offset}
				
			res.append(a)
	
	value_name = ''.join([i.label for i in axes])
	combined.add_variable_combined(value_name,res)

	import copy
	p = copy.deepcopy(master)
	p.combined_parameters =res
	p.label = ', '.join([i.label for i in axes])
	p.instrument = 'combined_parspace' 
	p.module_options['var'] = value_name
	qt.msleep(1.5) #allow qt to process signal handlers

	return p

def createCompositeParametricFromAxes(value_name,axes):
	if 'combined_parametric' in qt.instruments.get_instruments():
		combined = qt.instruments.get_instruments()['combined_parametric']
	else:
		combined = qt.instruments.create('combined_parametric','virtual_composite_parametric')
	res=[]
	for i,p in enumerate(axes):
		a= {
			'instrument': qt.instruments.get_instruments()[p.instrument],
			'parameter': p.module_options['var'],
			'function': p.module_options['function'],
			'gain': p.module_options['gain']
			}
		res.append(a)	
	combined.add_variable_combined(value_name,res)

	import copy
	p = copy.deepcopy(axes[0])
	p.combined_parameters = res
	p.label = value_name
	p.module_options['gain'] = 1.0 #no gain for a parametric variable
	p.instrument = 'combined_parametric' 
	p.module_options['var'] = value_name
	qt.msleep(1.5) #allow qt to process signal handlers
	return p


class param(object):
	def __init__(self):
		self.begin = 0
		self.end = 0
		self.instrument = []
		self.instrument_opt = []
		self.module = []
		self.module_name = []
		self.module_options = {}
		self.steps = []
		self.stepsize = []
		self.rate_stepsize = []
		self.rate_delay = []
		self.label = ''
		self.unit = 'a.u.'
	
class parspace(object):
	def __init__(self):
		self.xmlfile = ''
		self.xs = [] #empty list of x1,x2 ..xn (param objects)
		self.zs = [] #empty list of parmaham space
		self.measurementname = 'Noname Measurement'
		self.user = None
		
	def load_xml(self,filename):
		raise Exception('not implemented yet. Filename: {:<30}'.format(filename))
	
	def add_param(self, param):
		self.xs.append(param)
		
	def add_paramz(self,param):
		self.zs.append(param)
		
	def set_name(self,name):
		self.measurementname = name
	
	def remove_param(self, param, label='Optional'):
# 		for i in range(len(self.xs)):
# 			i = self.xs[i]
# 			if i.__hash__() == param.__hash__():
		self.xs.remove(param)		
				
			
		raise Exception('not implemented yet')
	
	def replace_param(self, param, label='Optional'):
		pass
	
	def remove_all_param(self, label='Optional'):	
		self.xs = []
	
	def set_traversefunc(self, func):
		self.traverse_func = func
		
	def set_traversefuncbyname(self, name, *kwargs,**lopts):
# 		if isempty(self.xs):
# 			raise Exception('Define all your axes before choosing a traverse function')
		functions = {'hilbert':	 lambda xs: hilbert_mul(xs,*kwargs,**lopts),
					'sweep': lambda xs: sweep_gen(xs,*kwargs,**lopts),
					'star' : lambda xs: star_gen(xs,*kwargs,**lopts)
					}
		try:
			self.traverse_name = name
			self.traverse_gen = functions[name]
		except:
			raise Exception('Unknown traverse function specified')
	
	
	def taketime_interval(self):
		diff_time = time() - self.b_time
		self.b_time = time()
		return diff_time
	def taketime_reset(self):
		self.b_time = time()
	def taketime_passed_since_reset(self):
		diff_time = time() - self.b_time
		return diff_time

	def estimate_time(self, sweepback=False):
		'''
		Estimate execution time
		Assumes rate_delay values to be im milliseconds
		'''
		#get the arguments from the traverse_gen
		
		try:
			seconds = 0
			cellvalue = get_cell_value(self.traverse_gen.func_closure[1])
			if self.traverse_name == 'sweep':
				if hasattr(cellvalue,'sweepback'):
					sweepback = cellvalue['sweepback']
				seconds = _estimate_time_recur(self.xs, sweepback)
			if self.traverse_name == 'hilbert':
				if hasattr(cellvalue,'n'):
					n = cellvalue['n']
				seconds = _estimate_time_hilbert(self.xs, n)
			(minutes, seconds) = divmod(seconds, 60)
			(hours, minutes) = divmod(minutes, 60)
			(days, hours) = divmod(hours, 24)
			print('Total estimated time: {:.0f}d {:.0f}h {:.0f}m {:.0f}s'
					.format(days, hours, minutes, seconds))
		except Exception as e:
			print(e)
		

	def traverse(self):
		'''
		traverse the defined parameter space, using e.g. a space filling
		curve defined in self.traverse_func
		'''
		
		instruments = []
		beginSweep = True
		for x in self.xs:
			instr = qt.instruments.get_instruments()[x.instrument]
			
			
			rate_delay = x.module_options['rate_delay']
			rate_stepsize = x.module_options['rate_stepsize']
			variable = x.module_options['var']
			
			if 'name' not in x.module_options:
				x.module_options['name'] = ''
			
			if 'gain' not in x.module_options:
				x.module_options['gain'] =1.

			#transform here also according to chosen module?
			rate_stepsize = rate_stepsize / x.module_options['gain']
			instr.set_parameter_rate(variable,rate_stepsize,rate_delay)
			instr.module_options = x.module_options
			instruments  = np.append(instruments, instr)

		data = qt.Data(name=self.measurementname)
		
		qt.mstart()
		
		cnt=0
		for i in self.xs:
			cnt+=1
			data.add_coordinate('{%s} ({%s})' % (i.label,i.unit),
				size=abs((i.end - i.begin) / i.stepsize),
				start=i.begin,
				end=i.end
				)
		cnt=0
		for i in self.zs:
			cnt+=1
			data.add_value('{%s} ({%s})' % (i.label,i.unit))
# 			grp.add_value('Z%d' % cnt, label=i.label,unit=i.unit)
			
		data.create_file(user=self.user)


        #now copy the calling measurement file to the measurement folder
		meas_dir = data.get_dir()
		import shutil,inspect,traceback,re
		
		reg=re.compile('.*.traverse\(\)')
		for i in traceback.extract_stack():
			res = reg.match(i[3])
			if res is not None:
				script_file =  i[0]
				shutil.copy(script_file, meas_dir)		
		
		
		valdim = len(self.zs)
		coorddim = len(self.xs)
		plots_3d = []
		plots_2d = [] 
		for j,i in enumerate(np.array(range(valdim))+coorddim):
			if coorddim > 1:	
				plot3d = qt.Plot3D(data, name='measure3D_%d'%j, coorddims=(coorddim-2,coorddim-1), valdim=i, style='image')
				plots_3d.append(plot3d)
				
			plot2d = qt.Plot2D(data, name='measure2D_%d'%j, coorddim=coorddim-1, valdim=i, traceofs=.1,autoupdate=False)
			plots_2d.append(plot2d)

		cnt = 0
		#give an initial update to all 2d plots so one no longer has to push button manually
		for plot2d in plots_2d:
			plot2d.update()

		try:
			print self.traverse_gen(self.xs)
			for dp in self.traverse_gen(self.xs):
				#datapoint extraction
				i = dp['dp']

				try:
					for x in range(len(self.xs)):
						module_options = self.xs[x].module_options
						

						functocall = getattr(instruments[x],'set_%s' % module_options['var'])
						instr = instruments[x]
						value = i[x] / module_options['gain']

						if 'setalways' in module_options and module_options['setalways'] == 0:
							if beginSweep:
								beginSweep = False
								functocall(value)	
								#after setting of variable call another function
								#maybe check for a list of variables in the future? in the var option
								if 'postcall' in module_options:
									arg = module_options['postcall']
									if hasattr(arg, '__call__'):
										#this is a function
										arg(value)
									else:
										(var,value) = arg
										func = getattr(instr,'set_%s'%var)
										func(value)
										
								# wait for setpoint to be reached
								if 'readywhen' in module_options:
									checkvar = module_options['readywhen']
									(var,value) = checkvar
									func = getattr(instr,'get_%s'%var)
									
									#poll the value until it changes
									while func() != value:
										qt.msleep(0.5)	
							else:
								pass #do nothing						
						else:
							functocall(value)
							#after setting of variable call another function
							#maybe check for a list of variables in the future? in the var option
							if 'postcall' in module_options:
								arg = module_options['postcall']
								if hasattr(arg, '__call__'):
									#this is a function
									arg(value)
								else:
									(var,value) = arg
									func = getattr(instr,'set_%s'%var)
									func(value)
									
							# wait for setpoint to be reached
							if 'readywhen' in module_options:
								checkvar = module_options['readywhen']
								(var,value) = checkvar
								func = getattr(instr,'get_%s'%var)
								
								#poll the value until it changes
								while func() != value:
									qt.msleep(0.5)
							
							
						
						
				except Exception as e:
					print 'Exception caught while trying to set axes: ', e				
					print e
				if hasattr(self.zs[0],'module_options'):
					if 'measure_wait' in self.zs[0].module_options:
						mwait = self.zs[0].module_options['measure_wait']
						if mwait != 0:
							sleep(mwait)
				
				rs = []
				for z in self.zs:
					r = z.module()
					rs.append(r)
				
				allmeas = np.hstack((i,rs))
				print allmeas
								
				data.add_data_point(*allmeas)
				#read out the control bit if it exists..
				#only used for communicating to plot3d and gnuplot to start a new datablock
				try:
					#fixme
					if 'newblock' in dp and dp['newblock'] == 1:
						data.new_block()
						if qt.flow.get_live_plot():
							for plot2d in plots_2d:
								plot2d.update()
						beginSweep = True
						
				except Exception as e:
					print 'why is there ane xception???'					
					print e.__doc__
					print e.message
					
				
				qt.msleep(0.001)
		except (Exception,KeyboardInterrupt) as e:
			print 'excepted error:', e 			
			print 'Wrapped up the datafiles'
		finally:
			meas_dir = data.get_dir()
			data.close_file()

			from lib.file_support.spyview import SpyView
			SpyView(data).write_meta_file()
			qt.mend()
			import subprocess
			from lib.config import get_shared_config
			user= get_shared_config().get('user')
			
			subprocess.call(['c:/qtlab/rsync.bat',user])
			print 'measurement ended'
