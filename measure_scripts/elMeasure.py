#elMeasure
#eefje = qt.instruments.create('Eefje','IVVI',address='COM1')
#elKeef = qt.instruments.create('ElKeefLy','Keithley_2000',address='GPIB::17')

import SiQD
reload(SiQD)
DAC = arange(0,100,5)
SiQD.turnon(DAC)
