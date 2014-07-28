#!/usr/bin/env python 
# Copyright 2012 University of Pittsburgh
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
#from SimulatorService_v2_0_2_services import runSimulationRequest
'''
Created on Nov 27, 2012

This is an example GenericEpidemicModelService implementation.

@author: John Levander, Shawn Brown
'''

import paths
from SimulatorService_v2_0_2_server import SimulatorService_v2_0_2
from ZSI import *
from ZSI.ServiceContainer import AsServer
from SimulatorService_v2_0_2_types import *
from ApolloFactory import *
from ApolloUtils import *
import os,sys
import shutil
import random
import datetime
import paramiko
import simWS
import time
from threading import Thread
from logger import Log
from commission import SSHConn
import json
from apollo import ApolloDB

connections = {} 

def monitorConnectionForFailedOrCompleted(connection,remoteScratch,runId,apolloDB):
    ### This function is run in a thread for each job that is submitted so that we can see
    ### if there are errors occuring from the run on the remote machine.
    while True:
        failCommand = 'echo -n "X"; if ( -e %s/%s/.failed ) echo "yes"'%(connection._remoteDir,remoteScratch)
        compCommand = 'echo -n "X"; if ( -e %s/%s/.completed ) echo "yes"'%(connection._remoteDir,remoteScratch)
        failVal = connection._executeCommand(failCommand)
        compVal = connection._executeCommand(compCommand)
        if failVal != "X":
            errCommand = 'cat %s/%s/run.stderr'%(connection._remoteDir,remoteScratch)
            failOutput = connection._executeCommand(errCommand)
            apolloDB.setRunStatus(runId,'failed',str(failOutput.replace('\"','')))
            break
        if compVal != "X":
            break
        time.sleep(3)
        
        
class SimulatorWebService(SimulatorService_v2_0_2):
    _wsdl = "".join(open(simWS.configuration['local']['wsdlFile']).readlines())
        
    factory = ApolloFactory()
    utils = ApolloUtils()
    logger = Log(simWS.configuration['local']['logFile'])
    logger.start()
    
    # this method runs an epidemic model
    def soap_runSimulation(self, ps, **kw):
        try:
            apolloDB = ApolloDB(dbname_="test")
            apolloDB.connect()
            response = SimulatorService_v2_0_2.soap_runSimulation(self, ps, **kw)

            #initialize the return information
	    response[1]._methodCallStatus = self.factory.new_MethodCallStatus()
            response[1]._methodCallStatus._status = "staging"
            response[1]._methodCallStatus._message = "This is the starting message"

            #get the runId for this message
            runId = response[0]._simulationRunId
            apolloDB.setRunStatus(runId,'initializing',"Recieved message from Apollo")
            self.logger.update("SVC_APL_RESQ_RECV")

        except Exception as e:
            self.logger.update("SVC_APL_RESQ_RECV_FAILED", message="%s" % str(e))
	    raise e
        
        # Parse and Translate the Apollo message First
        try:
            # Get the information about the simulator
            (name,dev,ver) = apolloDB.getSoftwareIdentificationForRunId(runId)
            idPrefix = "%s_%s_%s_"%(dev,name,ver)
	    
            self.logger.update("SVC_APL_TRANS_RECV",message="%s"%str(idPrefix))
        except Exception as e:
            self.logger.update("SVC_APL_TRANS_FAILED",message="%s"%str(e))
            apolloDB.setRunStatus(runId,"failed",self.logger.pollStatus()[1])
            response[1]._methodCallStatus._status = "failed"
            response[1]._methodCallStatus._message = str(e)
            return response

        # Get the pertinent user information from the runSimulation message from the database
        try:
            jsonStr = apolloDB.getRunDataContentFromRunIdAndLabel(runId,"run_simulation_message.json",
                                                                  0,1,"TEXT","RUN_SIMULATION_MESSAGE")
            jsonDict = json.loads(jsonStr)
            user = jsonDict['authentication']['requesterId']
            
        except Exception as e:
            apolloDB.setRunStatus(runId,"failed",str(e))
            response[1]._methodCallStatus._status = 'failed'
            response[1]._methodCallStatus._message = str(e)
            print str(e)
            raise e

        # Create the current connector
        
        try:
            confId = simWS.configuration['simulators']['mappings'][idPrefix]
            simConf = simWS.configuration['simulators'][confId]
            conn = SSHConn(self.logger,machineName_=simConf['defaultMachine'][0])
            connections[str(runId)] = conn
            self.logger.update("SRV_SSH_CONN_SUCCESS",message="%s"%str(idPrefix))
            apolloDB.setRunStatus(runId,"staging",message="ssh connection established")
        except Exception as e:
	    print str(e)
            self.logger.update("SVC_SSH_CONN_FAILED",message="%s"%str(e))
            apolloDB.setRunStatus(runId,"failed",message="%s"%self.logger.pollStatus()[1])
            response[1]._methodCallStatus._status = 'failed'
            response[1]._methodCallStatus._message = str(e)
            return response

        
        # Make a random directory name so that multiple calls can be made
             
        try:
            randID = random.randint(0,100000)
            tempDirName = "%s/fred.tmp.%d"%(simWS.configuration["local"]["scratchDir"],randID)
            os.mkdir(tempDirName)
            self.logger.update("SVC_TMPDIR_SUCCESS",message="%s"%tempDirName)
            apolloDB.setRunStatus(runId,"staging","temporary directory created on remote system")
        except Exception as e:
            self.logger.update("SVC_TMPDIR_FAILED",message="%s"%str(e))
            apolloDB.setRunStatus(runId,"failed",message="%s"%self.logger.pollStatus()[1])
            response[1]._methodCallStatus._status = 'failed'
            response[1]._methodCallStatus._message = str(e)
            return response

        # Get the files from the Apollo DB
        try:
            translatorServiceId = apolloDB.getTranslatorServiceKey()
            simulatorServiceId = apolloDB.getSimulatorServiceKey(dev,name,ver)
            
            simulatorInputFileDict = apolloDB.getSimulationInputFilesForRunId(runId,translatorServiceId,simulatorServiceId)
            for fileName,content in simulatorInputFileDict.items():
                with open(tempDirName+"/"+fileName,"wb") as f:
                    f.write("%s"%content)

            self.logger.update("SVC_FILELIST_RECIEVED")
            apolloDB.setRunStatus(runId,"staging","run files successfully retrieved from the database")
        except Exception as e:
            self.logger.update("SVC_FILELIST_FAILED",message="%s"%str(e))
            apolloDB.setRunStatus(runId,"failed","%s"%self.logger.pollStatus()[1])
            response[1]._methodCallStatus._status = 'failed'
            response[1]._methodCallStatus._message = str(e)
            return response

        try:
            remoteScr = 'fred.tmp.%s'%str(randID)
            conn._mkdir(remoteScr)
 
            for fileName,content in simulatorInputFileDict.items():
                conn.sendFile(tempDirName + "/" + fileName, remoteScr + "/" + fileName)

            ### we do not need temp directory anymore
            shutil.rmtree(tempDirName)
            
            self.logger.update("SVC_FILE_SEND_SUCCESS",message="%s"%tempDirName)
            apolloDB.setRunStatus(runId,"staging","run files successfully retrieved from the databae")
        except Exception as e:
            self.logger.update("SVC_FILE_SEND_FAILED",message="%s"%e)
            apolloDB.setRunStatus(runId,"failed",self.logger.pollStatus()[1])
            response[1]._methodCallStatus._status = 'failed'
            response[1]._methodCallStatus._message = str(e)            
            return response

        try:
            (jobType,returnVal) = conn.submitJob(randID,runId,idPrefix,user=user)
            self.logger.update("SVC_SUBMIT_JOB_SUCCESS",message="%s"%returnVal)
            apolloDB.setRunStatus(runId,"queued","run is queued on remote system")
            t = Thread(target=monitorConnectionForFailedOrCompleted,args=(conn,remoteScr,runId,apolloDB))
            t.start()
        except Exception as e:
            self.logger.update("SVC_SUBMIT_JOB_FAILED",message="%s"%str(e))
            apolloDB.setRunStatus(runId,"failed",self.logger.pollStatus()[1])
            response[1]._methodCallStatus._status = 'failed'
            response[1]._methodCallStatus._message = str(e)
            return response

        response[1]._methodCallStatus._status = 'success'
        response[1]._methodCallStatus._message = 'runSimulation call completed successfully'
        return response

#run a webserver 
AsServer(port=int(simWS.configuration['local']['port']), services=[SimulatorWebService('pscsimu'), ])

