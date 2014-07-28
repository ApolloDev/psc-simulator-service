import sys,os,os.path
import simWS

try:
	sys.path.append(simWS.configuration['local']['apolloPyDir'])

except Exception as e:
	print 'The Directory for apolloPyDir '\
	    + '%s is not available, please check '%(simWS.configuration['local']['apolloPyDir'])\
	    + 'the path in simWS.py again'
	raise e


