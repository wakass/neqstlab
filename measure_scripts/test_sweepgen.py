import lib.parspace as ps
reload(ps)

ax1 = ps.param()
ax1.begin = 1.
ax1.end = 3.
ax1.stepsize = 1.
						
xs = [ax1,ax1,ax1]

for dp in ps.sweep_gen(xs,**{'sweepback':'on'}):
	print dp

def bin2str(b):
	return '{:#008b}'.format(b)