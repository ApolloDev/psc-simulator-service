configuration = { 
'local': {
        'scratchDir':'/home/stbrown/hold/scratch',
        'serviceDir':'/usr/local/packages/Simulator-WS-v2.0',
        'logFile':'./sim.log',
        'port':'8089',
        'version':'2_0_1'
	},
'machines':{
	'blacklight.psc.xsede.org':{
		'username':'stbrown',
		'password':'',
		'privateKeyFile':'/usr/local/packages/.k/id_rsa.psc',
		'queueType':'PBS',
		'remoteDir':'$SCRATCH',
		'submitCommand':'module load torque; qsub',
		'special':'source /usr/share/modules/init/csh; source /etc/csh.cshrc.psc\n',
        'qstatCommand':'qstat',
        'useModules':True,
        'big':'-l ncpus=64 -l walltime=10:00:00',
        'medium':'-l ncpus=32 -l walltime=5:00:00',
        'small':'-l ncpus=16 -l walltime=1:30:00',
        'debug':'-l ncpus=16 -l walltime=00:30:00 -q debug',
        'getID':"set words = `echo $PBS_JOBID | sed 's/\./ /g'`; set id = $words[1]"
		},
	'fe-sandbox.psc.edu':{
		'username':'stbrown',
		'password':'',
		'privateKeyFile':'/usr/local/packages/.k/id_rsa.sand',
		'queueType':'PBS',
		'remoteDir':'/data/fs/stbrown/apolloTemp',
		'submitCommand':'qsub',
		'special':'',
		'qstatCommand':'qstat',
		'useModules':False,
		'big':'-l nodes=4:ppn=16',
		'medium':'-l nodes=1:ppn=10',
		'small':'-l nodes=1:ppn=10',
		'debug':'-l nodes=1:ppn=10',
		'getID':"set words = `echo $PBS_JOBID | sed 's/\./ /g'`; set id = $words[1]"
		},
	'unicron.psc.edu':{
		'username':'stbrown',
		'password':'',
		'privateKeyFile': '/usr/local/packages/.k/id_rsa.unicron',
		'queueType':'Direct',
		'remoteDir':'/media/scratch2/apolloTemp',
		'useModules':False,
		'big':'',
		'medium':'',
		'small':'',
		'debug':'',
					}
	},
'simulators':{
        'mappings':{'UPitt,PSC,CMU_FRED_2.0.1_':'fred_V1',
	            'UPitt,PSC,CMU_FRED_2.0.1_i_':'fred_V1_i',
                    'Chao-FredHutchinsonCancerCenter_FluTE_1.15_':'flute_v1.15',
                    'test':'test',
                    'fred':'fred_V1'},
	'fred_V1':{
            'stagedMachines':['blacklight.psc.xsede.org'],
            'defaultMachine':['blacklight.psc.xsede.org'],
            'runDirPrefix':'fred.tmp',
            'moduleCommand':'module load fred; module load python',
            'runCommand':'fred_job -p config.txt -k apollo_<<ID>>$id',
            'dbCommand':'touch .dbloading\npython $FRED_HOME/bin/fred_to_apollo_parallel.py -k apollo_<<ID>>$id\nrm -rf .dbloading',
            'big':'-m 1 -n 2 -t 32',
            'medium':'-m 2 -n 4 -t 16',
            'small':'-m 8 -n 8 -t 2',
            'debug':'-m 8 -n 8 -t 2'
		},
        'fred_V1_i':{
	    'stagedMachines':['fe-sandbox.psc.edu'],
	    'defaultMachine':['fe-sandbox.psc.edu'],
            'runDirPrefix':'fred.tmp',
            'moduleCimmand':'',
	    'runCommand':'fred_job -p config.txt -k apollo_<<ID>>',
            'dbCommand':'touch .dbloading\npython $FRED_HOME/bin/fred_to_apollo_census.py -k apollo_<<ID>> -i <<ID>>\nrm -rf .dbloading',
            'big':'-m 1 -n 1 -t 16',
            'medium':'-m 2 -n 2 -t 4',
	    'small':'-m 8 -n 8 -t 2',
            'debug':'-m 8 -n 8 -t 2'
              },
	'test':{
            'stagedMachine':['blacklight.psc.xsede.org','unicron.psc.edu'],
            'defaultMachine':['unicron.psc.edu'],
            'runDirPrefix':'test.tmp',
            'moduleCommand':'module load fred',
            'runCommand':'echo Testing <<ID>>; sleep 10; echo Testing <<ID>>; sleep 10',
            'dbCommand':'',
            'big':'',
            'medium':'',
            'small':'',
            'debug':''
			}
	}
}

