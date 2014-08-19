#Parameterspace.py 
#Defines classes and functions to span and traverse a parameter space in the qtlab environment.


# from pylab import *
import numpy as np
from time import time,sleep
import os
import qt
import hdf5_data as h5

curve = np.zeros((0,2))

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
						
def sweep_gen_helper(xs,**lopts):
	x = xs[0]
	u = np.arange(x.begin,x.end,x.stepsize)
	
	u = np.linspace(x.begin,x.end,np.abs((x.end-x.begin)/x.stepsize) +1)
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
		if name == 'hilbert':
			self.traverse_gen = lambda xs: hilbert_mul(xs,*kwargs,**lopts)
		elif name == 'sweep':
			self.traverse_gen = lambda xs: sweep_gen(xs,*kwargs,**lopts)
		else:
			raise Exception('Unknown traverse function specified')
	
	def estimate_time(self):
		#calculate time, try at least
		#assume no sweepback measure2D
		try:
			#'loop' axis
			ax0_time = np.abs(self.xs[-2].begin - self.xs[-2].end) / (self.xs[-2].rate_stepsize / (self.xs[-2].rate_delay/1000.))
			ax0_steps = np.abs(self.xs[-2].begin - self.xs[-2].end) / np.abs(self.xs[-2].stepsize)
			label= self.xs[-2].label
			range= np.abs(self.xs[-2].begin - self.xs[-2].end)
			speed= self.xs[-2].rate_stepsize / (self.xs[-2].rate_delay/1000.)
			print 'For %(label)s one sweep %(time)g seconds with %(steps)d steps. Range %(range)g speed %(speed)g' % {'label':label,'time':ax0_time,'steps':ax0_steps,'range':range,'speed':speed}

			
			#'sweep' axis
			ax1_time = np.abs(self.xs[-1].begin - self.xs[-1].end) / (self.xs[-1].rate_stepsize / (self.xs[-1].rate_delay/1000.))
			ax1_steps = np.abs(self.xs[-1].begin - self.xs[-1].end) / np.abs(self.xs[-1].stepsize)
			label= self.xs[-1].label
			range= np.abs(self.xs[-1].begin - self.xs[-1].end)
			speed= self.xs[-1].rate_stepsize / (self.xs[-1].rate_delay/1000.)
			print 'For %(label)s one sweep %(time)g seconds with %(steps)d steps. Range %(range)g speed %(speed)g' % {'label':label,'time':ax1_time,'steps':ax1_steps,'range':range,'speed':speed}
			
			time = ax1_time*ax0_steps*2 + ax0_time
			import datetime
			print time
			print 'Total time will probably be: %s' % datetime.timedelta(seconds=time)
		except Exception as e:
			print e
	def traverse(self):
		#traverse the defined parameter space, using e.g. a space filling curve defined in self.traverse_func
		instruments = []
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
		dat = h5.HDF5Data(name=self.measurementname)
		grp = h5.DataGroup('my_data', dat, description='pretty wise',
			greets_from='WakA') # arbitrary metadata as kw

		qt.mstart()
		
		cnt=0
		for i in self.xs:
			cnt+=1
			data.add_coordinate('{%s} ({%s})' % (i.label,i.unit),
				size=abs((i.end - i.begin) / i.stepsize),
				start=i.begin,
				end=i.end
				)
			grp.add_coordinate('X%d' % cnt, #keep track of the nth coordinate
				label=i.label,
				unit=i.unit,
				size=abs((i.end - i.begin) / i.stepsize),
				start=i.begin,
				end=i.end
				)
		cnt=0
		for i in self.zs:
			cnt+=1
			data.add_value('{%s} ({%s})' % (i.label,i.unit))
			grp.add_value('Z%d' % cnt, label=i.label,unit=i.unit)
			
		data.create_file()
        
		plotvaldim =2
		if len(self.xs) > 1:
			plotvaldim = len(self.xs)
			plot3d = qt.Plot3D(data, name='measure3D', coorddims=(plotvaldim-2,plotvaldim-1), valdim=plotvaldim, style='image')
		plot2d = qt.Plot2D(data, name='measure2D', coorddim=plotvaldim-1, valdim=plotvaldim, traceofs=10,autoupdate=False)
		cnt = 0

		

			
		try:
			print self.traverse_gen(self.xs)
			for dp in self.traverse_gen(self.xs):
				#datapoint extraction
# 				print dp
				i = dp['dp']

				try:
					for x in range(len(self.xs)):				
						module_options = self.xs[x].module_options
						functocall = getattr(instruments[x],'set_%s' % module_options['var'])
						
						value = i[x] / module_options['gain']
						functocall(value)
				except Exception as e:
					print 'Exception caught while trying to set axes: ', e				
				
				if hasattr(self.zs[0],'module_options'):
					if 'measure_wait' in self.zs[0].module_options:
						mwait = self.zs[0].module_options['measure_wait']
						if mwait != 0:
							sleep(mwait)
				r = self.zs[0].module()
	
				allmeas = np.hstack((i,r))
				print allmeas
				
				#get keys for all dimensions
				kz = grp.group.keys()
				#write to them
				##todo: check if dataset exceeded
				##expand dataset every time with 100?
				#temporarily stop writing hdf5
				#for i in range(len(kz)):
				#	grp[kz[i]] = np.append(grp[kz[i]], allmeas[i])
				
				data.add_data_point(*allmeas)
				#read out the control bit if it exists..
				#only used for communicating to plot3d and gnuplot to start a new datablock
				try:
					#fixme
					if 'newblock' in dp and dp['newblock'] == 1:
						data.new_block()
						if qt.flow.get_live_update():
							plot2d.update()
				except Exception as e:
					print e
				
				qt.msleep(0.001)
		except (Exception,KeyboardInterrupt) as e:
			print 'excepted error:', e 
			#handle an abort with some grace for hdf5 et.al.
			dat.close()
			from lib.file_support.spyview import SpyView
			SpyView(data).write_meta_file()
			print 'Wrapped up the datafiles'
			raise


		data.close_file()
		dat.close()
		from lib.file_support.spyview import SpyView
		SpyView(data).write_meta_file()
		
		qt.mend()
		print 'measurement ended'
