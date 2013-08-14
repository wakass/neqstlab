#!/bin/python
import matplotlib
matplotlib.use('TkAgg')

import sys, math
from pylab import *
import matplotlib.animation as animation 

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

def plothilby():
    global curve
    plot(curve[:-500,0],curve[:-500,1])
    show(block=True)
    
def anim_data_gen():
	global curve
	cnt = 0
	while cnt < curve.shape[0]:
		cnt += 1
		yield curve[cnt,0], curve[cnt,1]

		
fig, ax = plt.subplots()
line, = ax.plot([], [], lw=2)
ax.set_ylim(0, 1.0)
ax.set_xlim(0, 1.0)
ax.grid()
xdata, ydata = [], []
def animhilby_func(data):
    # update the data
    x,y = data
    xdata.append(x)
    ydata.append(y)
    xmin, xmax = ax.get_xlim()

    if x >= xmax:
        ax.set_xlim(xmin, 2*xmax)
        ax.figure.canvas.draw()
    line.set_data(xdata, ydata)

    return line,


#define iterations
reps = 7
# Calculate the number of curve cv's
cvs = int(math.pow(4, reps))
        
# Create the curve
hilbert(0.0, 0.0, 1.0, 0, 0.0, 1.0, reps)
ani = animation.FuncAnimation(fig, animhilby_func, anim_data_gen, blit=True, interval=10, repeat=False)
show(block=False)