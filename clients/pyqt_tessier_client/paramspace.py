#Parameterspace.py 
#Defines classes and functions to span and traverse a parameter space in the qtlab environment.


from pylab import *
from time import time,sleep
import os
import qt

curve = np.zeros((0,2))
curve = np.mat(curve.copy())
def hilbert(x0, y0, xi, xj, yi, yj, n):
    if n <= 0:
        X = x0 + (xi + yi)/2
        Y = y0 + (xj + yj)/2
        
        # Output the coordinates of the cv
        global curve
        curve=np.append(curve, [[X,Y]],axis=0)
        #print '%s %s 0' % (X, Y)
    else:
        hilbert(x0,               y0,               yi/2, yj/2, xi/2, xj/2, n - 1)
        hilbert(x0 + xi/2,        y0 + xj/2,        xi/2, xj/2, yi/2, yj/2, n - 1)
        hilbert(x0 + xi/2 + yi/2, y0 + xj/2 + yj/2, xi/2, xj/2, yi/2, yj/2, n - 1)
        hilbert(x0 + xi/2 + yi,   y0 + xj/2 + yj,  -yi/2,-yj/2,-xi/2,-xj/2, n - 1)

def param_hilb(xs, n=5,**lopts):
	hilbert(xs[0].begin, xs[1].begin, xs[0].end-xs[0].begin, 0,0, xs[1].end-xs[1].begin, n)
	return curve

def sweep_func_helper(xs, **lopts):
	z = np.array([])
	x = xs[0]
	u = np.arange(x.begin,x.end,x.stepsize)
	sb_bit = 0
	if len(xs[1:]) > 0:
		for uu in u:
			appendage = sweep_func_helper(xs[1:],**lopts)
			if 'sweepback' in lopts:
				if sb_bit:
					appendage = np.flipud(appendage)
					if 'datablock' in lopts:
						#reverse the flip of the datablock bit#hackyhackyTM
						appendage[:,-1] = np.flipud(appendage[:,-1]) 
					sb_bit = 0
				else:
					sb_bit = 1
			#if  appendage 1d then column stack
			if len(b.shape) == 1:

				z_t = np.column_stack((np.repeat(uu,appendage.shape[0]),appendage))
				if len(z) == 0:
					z = z_t
				else:
					z = np.vstack((z,z_t))
			else:
				z_t = np.concatenate( (np.repeat(uu,appendage.shape[0]),appendage),axis=1)
				if len(z) == 0:
					z = z_t
				else:
					z = np.vstack((z,z_t))
	else:
		#implement datablock bit
		if 'datablock' in lopts:
			z_t = np.zeros(len(u))
			z_t[-1] = 1
			z = np.column_stack((u,z_t)) 
		else:
			z = u 
	return z

class param(object):
	def __init__(self):
		self.begin = 0
		self.end = 0
		self.instrument = []
		self.instrument_opt = []
		self.module = []
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
	
	def remove_param(self, label='Optional'):
		raise Exception('not implemented yet')
		
	def set_traversefunc(self, func)
		traverse_func = func
		
	def data_gen(self):
		trav = self.lineartraverse
		cnt = 0
		while cnt < trav.shape[0]: 
			yield trav[cnt,0] #yield a single tuple including controls bits
			cnt += 1
	
	def traverse(self, func):
		#traverse the defined parameter space, using e.g. a space filling curve defined in func
		for x in self.xs:
			instr = qt.instruments.get_instruments()[x.instrument]
			instr.set_parameter_rate(x.opt,xs.stepsize,xs.delay)
		
		self.lineartraverse = self.traverse_func(self.xs)
		data = qt.Data(name=self.measurementname)

		qt.mstart()
		for i in self.xs:
			data.add_coordinate('{:<30} ({:<30})'.format(i.label,i.unit),
				size=abs((i.end - i.begin) / i.stepsize),
				start=i.begin,
				end=i.end
				)
		for i in self.zs:
			data.add_value('{:<30} ({:<30})'.format(i.label,i.unit))
		
		data.create_file()
        
		plot2d = qt.Plot2D(data, name='measure2D', coorddim=0, valdim=2, traceofs=10)
		plot3d = qt.Plot3D(data, name='measure3D', coorddims=(0,1), valdim=2, style='image')
		cnt = 0
		for i in self.data_gen():
			try:
				for x in range(len(self.xs))
					self.xs[x].module(i[x])
			except Exception as e:
				print e
				
			#t = lambda x,y: sin(x*2*pi)+sin(y*2*pi)
			if cnt == 0:
				qt.msleep(4) #wait 4 seconds to start measuring to allow for capacitive effects to dissipate
				cnt +=1
			r = self.zs[0].module()

			data.add_data_point(i[0],i[1],r)

			#read out the control bit if it exists..
			try:
				if i[-1]:
					data.new_block()
			qt.msleep(0.001),
			
		data.new_block()
		data.close_file()
		from lib.file_support.spyview import SpyView
		
		qt.mend()
		SpyView(data).write_meta_file()
		print 'measurement ended'

def start_test():
	s1f_gain = 5.0 	#s1f module
	i_gain = 100e6/1e9 	#volt to nA --> 100MV/A, nanoampere in a volt
	stepsize= 30/gates_gain
	delay = 20
	
	#create paramspace object with defined axes and define instruments etc.
	b1 = param() 
	b1.begin = -3200.0
	b1.end = -5000.0
	b1.stepsize = 1.0
	b1.steps = 4.0
	b1.label = 'B1'
	b1.unit = 'Voltage (mV)'
	b1.instrument = 'eefje'
	b1.instrument_opt = 'dac11'
	b1.rate_stepsize = 1.0
	b1.rate_delay = 20.0
	b1.module = lambda x: eefje.set_dac11(x/s1f_gain) #s1f module amp
	
	#duplicate previous axis
	import copy
	b2 = copy.deepcopy(b1)
	b2.label = 'B2'
	b2.instrument = 'eefje'
	b1.instrument_opt = 'dac12'
	b2.module = lambda x: eefje.set_dac12(x/s1f_gain)
	
	#measurement axis
	z = copy.deepcopy(b2)
	z.label = 'Current'
	z.unit = 'nA'
	z.module = lambda: elKeef.get_readlastval()/i_gain #100 MV/A
	
	#now define the parameter space
	pspace = parspace()
	pspace.add_param(b1)
	pspace.add_param(b2)
	pspace.add_paramz(z)
	
	pspace.set_name('Default measurement')
	pspace.set_traversefunc(lambda x,**lopts: paramhilb(x,lopts)
	pspace.set_traversefunc(lambda x,**lopts: sweep_func_helper(x,sweepback='on',datablock='on',lopts))

		
	#set vsd
	eefje.set_dac4(10) #1 mv
	eefje.set_dac10(-4500/5.0) #4.5 volt and gain for lead
	try:
		pspace.load_xml('filename')
	except Exception, e :
		print 'Caught:', e
	
	print 'Starting measurement'
	pspace.traverse()