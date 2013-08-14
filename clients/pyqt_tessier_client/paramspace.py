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

def param_hilb(xs, n):
	hilbert(xs[0].begin, xs[1].begin, xs[0].end-xs[0].begin, 0,0, xs[1].end-xs[1].begin, n)

def data_gen():
	global curve
	cnt = 0
	while cnt < curve.shape[0]: 
		yield curve[cnt,0], curve[cnt,1]
		cnt += 1

class param(object):
	def __init__(self):
		self.begin = 0
		self.end = 0
		self.module = []
		self.steps = []
		self.stepsize = []
		self.label = ''
		self.unit = 'a.u.'
	
class parspace(object):
	def __init__(self):
		self.xmlfile = ''
		self.xs = [] #empty list of x1,x2 ..xn (param objects)
		self.zs = [] #empty list of parmaham space
		
	def load_xml(self,filename):
		raise Exception('not implemented yet. Filename: {:<30}'.format(filename))
	
	def add_param(self, param):
		self.xs.append(param)
		
	def add_paramz(self,param):
		self.zs.append(param)
	
	def remove_param(self, label='Optional'):
		raise Exception('not implemented yet')
	
	def traverse(self, func):
		#traverse the defined parameter space, using e.g. a space filling curve defined in func
		param_hilb(self.xs,5)
		data = qt.Data(name='testmeasurement')

		qt.mstart()
		data.add_coordinate('{:<30} ({:<30})'.format(self.xs[0].label,self.xs[0].unit))
		data.add_coordinate('{:<30} ({:<30})'.format(self.xs[1].label,self.xs[1].unit))
		data.add_value('{:<30} ({:<30})'.format(self.zs[0].label,self.zs[0].unit))
		
		data.create_file()
        
		plot2d = qt.Plot2D(data, name='measure2D', coorddim=0, valdim=2, traceofs=10)
		plot3d = qt.Plot3D(data, name='measure3D', coorddims=(0,1), valdim=2, style='image')

		for i in func():
# 			print i,
			#xs[0].module('set_dac',value)
			
			t = lambda x,y: sin(x*2*pi)+sin(y*2*pi)
			val = t(i[0],i[1])
			data.add_data_point(i[0],i[1],val)
			qt.msleep(0.001),
			
		print 'done'
		data.new_block()
		data.close_file()
		qt.mend()

def start_test():
	a = param()
	a.begin = 1.0
	a.end = 2.0
	a.steps = 4.0
	a.label = 'Gate Frequency'
	a.unit = 'GHz'
	import copy
	b = copy.deepcopy(a)
	b.label = 'Gate2 frequency'
	z = copy.deepcopy(b)
	z.label = 'Current'
	z.unit = 'mA'
		
	pspace = parspace()
	pspace.add_param(a)
	pspace.add_param(b)
	pspace.add_paramz(z)
	
	try:
		pspace.load_xml('filename')
	except Exception, e :
		print 'Caught:', e
	
	print 'trying hilby'
	pspace.traverse(data_gen)