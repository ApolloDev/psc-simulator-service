# Copyright 2012 University of Pittsburgh
# Copyright 2012 Pittsburgh Supercomputing Center
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License.  You may obtain a copy of
# the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations under
# the License.


'''
Created on Jun 2013 

@author: Shawn Brown
'''

configuration = { 
    'local': {
            'scratchDir':'/tmp',
            'serviceDir':'/usr/local/packages/Simulator-WS-v3.0.2',
            'templateDir':'/usr/local/packages/Simulator-WS-v3.0.2/templates',
            'logFile':'/usr/local/packages/Simulator-WS-v3.0.2/sim.log',
            'wsdlFile':'/usr/local/packages/Simulator-WS-v3.0.2/simulator_service_3.0.2.wsdl',
            'apolloPyDir':'/usr/local/packages/apollo-db-python-module',
            'port':'8099',
            'version':'3.0.2',
            'apolloDBName':'apollo_302_snapshot',
            'apolloDBHost':'pha-db.psc.edu',
            'apolloDBUser':',
            'apolloDBPword':''
    },
    # Private key files will have to be updated by the user
    'machines':{
        'pscss.olympus.psc.edu':{
                'hostname':'pscss.olympus.psc.edu',
                'username':'ows_simulator',
                'password':'',
                'privateKeyFile':'/usr/local/packages/.k/id_rsa.login.olympus',
                'queueType':'PBS',
                'priorityQueue':'batch',
                'remoteDir':'/mnt/beegfs/users/ows_simulator/apolloTemp',
                'submitCommand':'/opt/bin/qsub',
                'special':'source /opt/packages/virtualenvs/ows2.7/bin/activate.csh; module load gnu_parallel',
                'apolloPyLoc':'/mnt/beegfs/users/ows_simulator/apollo-db-files',
                'qstatCommand':'qstat',
                'useModules':True,
                'big':'-l nodes=4:ppn=16',
                'medium':'-l nodes=1:ppn=16 -l walltime=60:00:00',
                'small':'-l nodes=1:ppn=16',
                'debug':'-l nodes=1:ppn=8',
                'getID':"set words = `echo $PBS_JOBID | sed 's/\./ /g'`; set id = $words[1]",
                'ppn':8,
                'mediumBatch':144,
                'useParallel':True,
                'env':'/bin/env'
    	},
    },
    'simulators':{
        'mappings':{
            'UPitt,PSC,CMU_FRED_2.0.1_':'fred_V1',
            'UPitt,PSC,CMU_FRED_2.0.1_i_':'fred_V1_i',
            'Chao-FredHutchinsonCancerCenter_FluTE_1.15_':'flute_v1.15',
            'PSC_CLARA_0.5_':'clara_v0.5',
	        'UPitt_SEIR_3.0':'seir_30',
            'PSC_OpenMalaria_1.0_':'openmalaria_32',
	    'PSC_OpenMalaria_R0063_':'openmalaria_32',
            'test':'test',
            'fred':'fred_V1'
        },
    	'fred_V1':{
            'stagedMachines':['blacklight.psc.xsede.org'],
            'defaultMachine':['blacklight.psc.xsede.org'],
            'runDirPrefix':'fred.tmp',
            'preProcessCommand':'',
            'moduleCommand':['module load fred; module load python'],
            'runCommand':'fred_job -p config.txt -k apollo_<<ID>>$id',
            'dbCommand':'python $FRED_HOME/bin/fred_to_apollo_parallel.py -k apollo_<<ID>>$id',
            'big':'-m 1 -n 2 -t 32',
            'medium':'-m 2 -n 4 -t 8',
            'small':'-m 4 -n 4 -t 2',
            'debug':'-m 8 -n 4 -t 4'
    	},
        'fred_V1_i':{
    	    'stagedMachines':['fe-sandbox.psc.edu', 'pscss.olympus.psc.edu'],
    	    'defaultMachine':['pscss.olympus.psc.edu'],
            'runDirPrefix':'fred.tmp',
    	    'preProcessCommand':'',
            'moduleCommand':['module load fred-apollo','module load fred/pfred-0.0.3'],
            'moduleName':['fred-apollo','fred/pfred-0.0.3'],
    	    'runCommand':'run_fred_apollo.bash ',
            'dependencies':['fred_to_apollo.py','apollo.py','apollo_update_status.py','apollo_batch_update_status.py','logger.py'],
            'dbCommand':'python $APOLLO_HOME/fred_to_apollo.py -o OUT -i <<ID>>',
            'statusCommand':'python $APOLLO_HOME/apollo_update_status.py -r <<ID>>',
            'batchStatusCommand':'python $APOLLO_HOME/apollo_batch_update_status.py -b <<bID>>',
            'big':'-m 1 -n 1 -t 16',
            'medium':'-m 8 -n 8 -t 4',
    	    'small':'-m 8 -n 8 -t 2',
            'debug':'-m 8 -n 4 -t 4',
            'mediumPPR':1,
            'mediumTPR':2,
            'mediumReals':4,
            'singlePPR':4,
            'singleTPR':2,
            'singleReals':8
            
        },
    	'flute_v1.15':{
    	    'stagedMachines':['fe-sandbox.psc.edu','pscss.olympus.psc.edu'],
    	    'defaultMachine':['pscss.olympus.psc.edu'],
    	    'runDirPrefix':'flute.tmp',
    	    'preProcessCommand':'',
            'dependencies':['apollo.py','apollo_update_status.py','apollo_batch_update_status.py','logger.py'],
    	    'moduleCommand':['','module load flute/flute-1.15.1-psc'],
            'moduleName':['','flute/flute-1.15.1-psc'],
    	    'runCommand':'$FLUTE_HOME/run_flute_apollo.bash',
    	    'dbCommand':'python $APOLLO_HOME/flute_to_apollo-snap.py -o OUT -i <<ID>>',
    	    'statusCommand':'python $APOLLO_HOME/apollo_update_status.py -r <<ID>>',
    	    'big':'',
    	    'medium':'',
            'small':'',
            'debug':'',
            'mediumPPR':4,
            'mediumTPR':1,
            'mediumReals':4,
            'singlePPR':4,
            'singleTPR':1,
    	},
        'openmalaria_32':{
            'stagedMachines':['pscss.olympus.psc.edu'],
            'defaultMachine':['pscss.olympus.psc.edu'],
            'runDirPrefix':'om.tmp',
            'preProcessCommand':'module load openmalaria_resources',
            'dependencies':['apollo.py','apollo_update_status.py','apollo_batch_update_status.py','logger.py'],
            'moduleCommand':['module load openmalaria/32'],
            'moduleName':['openmalaria/32'],
            'runCommand':'$OM_HOME/run_om_apollo.bash',
            'dbCommand':'',
            #'dbCommand':'python $APOLLO_HOME/flute_to_apollo-snap.py -o OUT -i <<ID>>',
            'statusCommand':'python $APOLLO_HOME/apollo_update_status.py -r <<ID>>',
            'big':'',
            'medium':'',
            'small':'',
            'debug':'',
            'mediumPPR':4,
            'mediumTPR':1,
            'mediumReals':4,
            'singlePPR':4,
            'singleTPR':1,
        },          
    	'clara_v0.5':{
            'stagedMachines':['fe-sandbox.psc.edu'],
            'defaultMachine':['fe-sandbox.psc.edu'],
            'runDirPrefix':'clara.tmp',
            'preProcessCommand':'mkdir Apollo; ln -s /data/fs/packages/clara-netlogo/inputs .; ln -s /data/fs/packages/clara-netlogo/CLARA.* .; ln -s /data/fs/packages/clara-netlogo/*.dat .; ln -s /data/fs/packages/clara-netlogo/extensions .; setenv THREADS $PBS_NUM_PPN',
            'moduleCommand':['module load java'],
            'runCommand':'java -server -Xmx65536M -XX:+AggressiveOpts -XX:+AggressiveHeap -XX:+UseNUMA -XX:+UseParallelGC -cp .:/data/fs/packages/netlogo-5.0.4/NetLogo.jar org.nlogo.headless.Main --threads $THREADS --model CLARA.nlogo --experiment Apollo --spreadsheet Apollo.csv',
            'dbCommand':'python $APOLLO_HOME/clara_to_apollo.py -i <<ID>>',
            'statusCommand':'python $APOLLO_HOME/apollo_update_status.py -r <<ID>>',
            'big':'',
            'medium':'',
            'small':'',
            'debug':''
        },
	'seir_30':{
	    'stagedMachines':['pscss.olympus.psc.edu'],
            'defaultMachine':['pscss.olympus.psc.edu'],
            'runDirPrefix':'seir.tmp',
            'preProcessCommand':'',
            'moduleCommand':['module load pitt_seir/pitt_seir-3.0.0'],
	    'moduleName':['pitt_seir/pitt_seir-3.0.0'],
            'runCommand':'$SEIR_HOME/run_seir_apollo.bash',
            'dbCommand':'python $APOLLO_HOME/seir_to_apollo.py -o OUT -i <<ID>>',
            'statusCommand':'python $APOLLO_HOME/apollo_update_status.py -r <<ID>>',
            'big':'',
            'medium':'',
            'small':'',
            'debug':'',
	    'mediumPPR':1,
	    'mediumTPR':1,
        'mediumReals':1,
        'singlePPR':1,
        'singleTPR':1
	},
    	'test':{
            'stagedMachine':['olympus.psc.edu', 'blacklight.psc.xsede.org', 'unicron.psc.edu'],
            'defaultMachine':['olumpus.psc.edu'],
            'runDirPrefix':'test.tmp',
    	    'preProcessCommand':'',
            'moduleCommand':'module load fred',
            'runCommand':'echo Testing <<ID>>; sleep 10; echo Testing <<ID>>; sleep 10',
    	    'statusCommand':'echo "running"',
            'dbCommand':'echo "db"',
            'big':'',
            'medium':'',
            'small':'',
            'debug':''
		}
    }
}

