#!/usr/bin/env python 
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
Created on Nov 27, 2012

@author: John Levander, Shawn Brown
'''

import paths
from SimulatorService_v3_1_0_server import SimulatorService_v3_1_0
from ZSI import *
from ZSI.ServiceContainer import AsServer
from SimulatorService_v3_1_0_types import *
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
from pbsBatch import PBSBatch

connections = {} 
print sys.getrecursionlimit()
def generate_message(statsDict):
    return "{0} completed, {1} running, {2} failed, {3} queued of {4} total jobs".format(statsDict['completed'],
                                                                                        statsDict['running'],
                                                                                        statsDict['failed'],
                                                                                        statsDict['queued'],
                                                                                        statsDict['total'])

def monitorBatchStatus(batchId,apolloDB):
    while True:
        runsToCheck = apolloDB.getRunsFromRunId(batchId)
        runStatus = {}
        overallStatus = "queued"
        message = "batch of runs is queued"

        for runId in runsToCheck:
            runStatus[runId] = apolloDB.getRunStatus(runId)
        statsDict = {'total':0,'completed':0,'running':0,'queued':0,'failed':0}

        for runId,status in runStatus.items():
            if status[0] not in statsDict.keys():
                statsDict['queued'] += 1
            else:
                statsDict[status[0]] += 1
            statsDict['total'] += 1

        if statsDict['queued'] != statsDict['total']:
            # this means that something has already happened
            if (statsDict['completed'] + statsDict['failed'])== statsDict['total']:
                if statsDict['failed']:
                    overallStatus = "failed"
                else:
                    overallStatus = "completed"
            else:
                overallStatus = "running"

            message = generate_message(statsDict)
    
            apolloDB.setRunStatus(batchId,overallStatus,message)
            if overallStatus == "completed":
                break
            #if overallStatus == "failed":
            #    break
        time.sleep(5)
        
class SimulatorWebService(SimulatorService_v3_1_0):
    _wsdl = "".join(open(simWS.configuration['local']['wsdlFile']).readlines())
        
    factory = ApolloFactory()
    utils = ApolloUtils()
    logger = Log(simWS.configuration['local']['logFile'])
    logger.start()
    
    def soap_runSimulations(self,ps, **kw):
        
        
        try:
            ### Connect to the Apollo Database
            apolloDB = ApolloDB(dbname_=simWS.configuration['local']['apolloDBName'],
                                host_=simWS.configuration['local']['apolloDBHost'],
                                user_=simWS.configuration['local']['apolloDBUser'],
                                password_=simWS.configuration['local']['apolloDBPword'])
            apolloDB.connect()
            
            #initialize the return information
            response = SimulatorService_v3_1_0.soap_runSimulations(self, ps, **kw)
            response[1]._runSimulationsResult = self.factory.new_RunResult()
            response[1]._runSimulationsResult._runId = response[0]._simulationRunId
            response[1]._runSimulationsResult._methodCallStatus = self.factory.new_MethodCallStatus()
            
            response[1]._runSimulationsResult._methodCallStatus._status = "staging"
            response[1]._runSimulationsResult._methodCallStatus._message = "This is the starting message"
            #get the runId for this message
            init_runId = response[0]._simulationRunId
            apolloDB.setRunStatus(init_runId,'initializing',"Received message from Apollo")
            self.logger.update("SVC_APL_RESQ_RECV")

        except Exception as e:
            print str(e)
            self.logger.update("SVC_APL_RESQ_RECV_FAILED", message="%s" % str(e))
            raise e
    
        try:
            ### get the software information from the message
	    print "Entering"
	    print apolloDB.getBatchAware_SoftwareIdentificationForRunId(init_runId)
            (name,dev,ver) = apolloDB.getBatchAware_SoftwareIdentificationForRunId(init_runId)
            idPrefix = "%s_%s_%s_"%(dev,name,ver)
        
            self.logger.update("SVC_APL_TRANS_RECV",message="%s"%str(idPrefix))
        
        except Exception as e:
            self.logger.update("SVC_APL_TRANS_FAILED",message="%s"%str(e))
            apolloDB.setRunStatus(init_runId,"failed",self.logger.pollStatus()[1])
            response[1]._runSimulationsResult._methodCallStatus._status = "failed"
            response[1]._runSimulationsResult._methodCallStatus._message = str(e)
            return response
        
        # Get the pertinent user information from the runSimulation message from the database
        try:
            transId = apolloDB.getSoftwareIdentificationId("Translator","1.0")
            endId = apolloDB.getSoftwareIdentificationId("any","any")
            print "Attempting to call here"
            jsonStr = apolloDB.getRunDataContentFromRunIdAndLabel(init_runId,"run_simulations_message.json",
                                                                  endId,transId,"TEXT","RUN_SIMULATIONS_MESSAGE")
            jsonDict = json.loads(jsonStr)
            user = "shawn" #jsonDict['authentication']['requesterId']
            
        except Exception as e:
            apolloDB.setRunStatus(init_runId,"failed",str(e))
            response[1]._runSimulationsResult._methodCallStatus._status = 'failed'
            response[1]._runSimulationsResult._methodCallStatus._message = str(e)
            print str(e)
            raise e
        
        try:
            confId = simWS.configuration['simulators']['mappings'][idPrefix]
            simConf = simWS.configuration['simulators'][confId]
            conn = SSHConn(self.logger,machineName_=simConf['defaultMachine'][0])
            self.logger.update("SRV_SSH_CONN_SUCCESS",message="%s"%str(idPrefix))
            apolloDB.setRunStatus(init_runId,"staging",message="ssh connection established")
        except Exception as e:
            print str(e)
            self.logger.update("SVC_SSH_CONN_FAILED",message="%s"%str(e))
            apolloDB.setRunStatus(init_runId,"failed",message="%s"%self.logger.pollStatus()[1])
            response[1]._runSimulationsResult._methodCallStatus._status = 'failed'
            response[1]._runSimulationsResult._methodCallStatus._message = str(e)
            return response

        
        # Make a random directory name so that multiple calls can be made     
        try:
            randID = random.randint(0,1000000000)
            tempDirName = "%s/%s.%d"%(simWS.configuration["local"]["scratchDir"],
                      simConf['runDirPrefix'],
                      randID)
            os.mkdir(tempDirName)
            self.logger.update("SVC_TMPDIR_SUCCESS",message="%s"%tempDirName)
            apolloDB.setRunStatus(init_runId,"staging","temporary directory created on local system")
        except Exception as e:
            self.logger.update("SVC_TMPDIR_FAILED",message="%s"%str(e))
            apolloDB.setRunStatus(init_runId,"failed",message="%s"%self.logger.pollStatus()[1])
            response[1]._runSimulationsResult._methodCallStatus._status = 'failed'
            response[1]._runSimulationsResult._methodCallStatus._message = str(e)
            return response

        # Create a PBS Batch object from the runId
        try:
            pbsBatch = PBSBatch(init_runId,
                                nodes_=conn._configuration['mediumBatch'],
                                ppn_=conn._configuration['ppn'],
                                procsPerRun_=simConf['mediumPPR'],
                                threadsPerRun_=simConf['mediumTPR'],
                                apollodb_=apolloDB,
                                localCnf_=simWS.configuration['local'],
                                machineCnf_=conn._configuration,
                                simulatorCnf_=simConf)
            pbsBatch.populate_from_apollo_runId()
            pbsBatch.create_zipFile("{0}/job_{1}.zip".format(tempDirName,init_runId))
            pbsBatch.createRunScript("{0}/batch_run{1}.py".format(tempDirName,init_runId))
            self.logger.update("SVC_FILELIST_RECIEVED")
            apolloDB.setRunStatus(init_runId,"staging","run files successfully retrieved from the database")
        except Exception as e:
            self.logger.update("SVC_FILELIST_FAILED",message="%s"%str(e))
            apolloDB.setRunStatus(init_runId,"failed","%s"%self.logger.pollStatus()[1])
            response[1]._runSimulationsResult._methodCallStatus._status = 'failed'
            response[1]._runSimulationsResult._methodCallStatus._message = str(e)
            return response
        
        # Send file to remote machine
        try:
            remoteScr = '%s.%s'%(simConf['runDirPrefix'],str(randID))
            conn._mkdir(remoteScr)
            conn.sendFile('{0}/job_{1}.zip'.format(tempDirName,init_runId),'{0}/job_packet.zip'.format(remoteScr))
            conn.sendFile('{0}/batch_run{1}.py'.format(tempDirName,init_runId),'{0}/batch_run.py'.format(remoteScr))
            shutil.rmtree(tempDirName)
            
            self.logger.update("SVC_FILE_SEND_SUCCESS",message="%s"%tempDirName)
            apolloDB.setRunStatus(init_runId,"staging","run files successfully retrieved from the databae")
        except Exception as e:
            self.logger.update("SVC_FILE_SEND_FAILED",message="%s"%e)
            apolloDB.setRunStatus(init_runId,"failed",self.logger.pollStatus()[1])
            response[1]._runSimulationsResult._methodCallStatus._status = 'failed'
            response[1]._runSimulationsResult._methodCallStatus._message = str(e)            
            return response
        
        # unzip and run the job on the remote machine
        try:
            apolloDB.setRunStatus(init_runId,"staging","executing on the remote system")
            returnVal = conn._executeCommand("cd {0}/{1}; chmod a+x batch_run.py; nohup ./batch_run.py >& out &".format(conn._remoteDir,
                                                                                                                  remoteScr))                                                                                                                
            self.logger.update("SVC_SUBMIT_JOB_SUCCESS",message="%s"%returnVal)
            
            conn._close()
            t = Thread(target=monitorBatchStatus,args=(init_runId,apolloDB))
            t.start()
        except Exception as e:
            self.logger.update("SVC_SUBMIT_JOB_FAILED",message="%s"%str(e))
            apolloDB.setRunStatus(init_runId,"failed",self.logger.pollStatus()[1])
            response[1]._runSimulationsResult._methodCallStatus._status = 'failed'
            response[1]._runSimulationsResult._methodCallStatus._message = str(e)
            return response
        
        response[1]._runSimulationsResult._methodCallStatus._status = "staging"
        response[1]._runSimulationsResult._methodCallStatus._message = 'runSimulation call completed successfully'
        return response
    
    # this method runs an epidemic model
    def soap_runSimulation(self, ps, **kw):
        try:
            apolloDB = ApolloDB(dbname_=simWS.configuration['local']['apolloDBName'],
                                host_=simWS.configuration['local']['apolloDBHost'],
                                user_=simWS.configuration['local']['apolloDBUser'],
                                password_=simWS.configuration['local']['apolloDBPword'])
            apolloDB.connect()
            response = SimulatorService_v3_1_0.soap_runSimulation(self, ps, **kw)

            #initialize the return information
            response[1]._methodCallStatus = self.factory.new_MethodCallStatus()
            response[1]._methodCallStatus._status = "staging"
            response[1]._methodCallStatus._message = "This is the starting message"

            #get the runId for this message
            init_runId = response[0]._simulationRunId
            runIds = apolloDB.getRunsFromRunId(init_runId)
            runId = init_runId
            apolloDB.setRunStatus(init_runId,'initializing',"Recieved message from Apollo")
            self.logger.update("SVC_APL_RESQ_RECV")

        except Exception as e:
            print str(e)
            self.logger.update("SVC_APL_RESQ_RECV_FAILED", message="%s" % str(e))
            raise e
        
        # Parse and Translate the Apollo message First
        try:
            # Get the information about the simulator
	    print "neter"
            (name,dev,ver) = apolloDB.getBatchAware_SoftwareIdentificationForRunId(runId)
	    print "name"
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
            transId = apolloDB.getSoftwareIdentificationId("Translator","1.0")
            endId = apolloDB.getSoftwareIdentificationId("any","any")
            jsonStr = apolloDB.getRunDataContentFromRunIdAndLabel(runId,"run_message.json",
                                                                  endId,transId,"TEXT","RUN_MESSAGE")
            jsonDict = json.loads(jsonStr)
            user = "Shawn" #jsonDict['authentication']['requesterId']
            
        except Exception as e:
            apolloDB.setRunStatus(runId,"failed",str(e))
            response[1]._methodCallStatus._status = 'failed'
            response[1]._methodCallStatus._message = str(e)
            print str(e)
            raise e

        try:
            confId = simWS.configuration['simulators']['mappings'][idPrefix]
            simConf = simWS.configuration['simulators'][confId]
            conn = SSHConn(self.logger,machineName_=simConf['defaultMachine'][0])
            self.logger.update("SRV_SSH_CONN_SUCCESS",message="%s"%str(idPrefix))
            apolloDB.setRunStatus(init_runId,"staging",message="ssh connection established")
        except Exception as e:
            self.logger.update("SVC_SSH_CONN_FAILED",message="%s"%str(e))
            apolloDB.setRunStatus(runId,"failed",str(e))
            response[1]._methodCallStatus._status = 'failed'
            response[1]._methodCallStatus._message = str(e)
            print str(e)
            raise e
        
        # Make a random directory name so that multiple calls can be made     
        try:
            randID = random.randint(0,1000000000)
            tempDirName = "%s/%s.%d"%(simWS.configuration["local"]["scratchDir"],
                      simConf['runDirPrefix'],
                      randID)
            os.mkdir(tempDirName)
            self.logger.update("SVC_TMPDIR_SUCCESS",message="%s"%tempDirName)
            apolloDB.setRunStatus(init_runId,"staging","temporary directory created on local system")
        except Exception as e:
            self.logger.update("SVC_TMPDIR_FAILED",message="%s"%str(e))
            apolloDB.setRunStatus(init_runId,"failed",message="%s"%self.logger.pollStatus()[1])
            response[1]._methodCallStatus._status = 'failed'
            response[1]._methodCallStatus._message = str(e)
            return response
        
        try:
            pbsBatch = PBSBatch(init_runId,
                                nodes_=conn._configuration['mediumBatch'],
                                ppn_=conn._configuration['ppn'],
                                procsPerRun_=simConf['singlePPR'],
                                threadsPerRun_=simConf['singleTPR'],
                                apollodb_=apolloDB,
                                localCnf_=simWS.configuration['local'],
                                machineCnf_=conn._configuration,
                                simulatorCnf_=simConf)
            pbsBatch.populate_from_apollo_runId()
            pbsBatch.create_zipFile("{0}/job_{1}.zip".format(tempDirName,init_runId))
            pbsBatch.createRunScript("{0}/batch_run{1}.py".format(tempDirName,init_runId))
            self.logger.update("SVC_FILELIST_RECIEVED")
            apolloDB.setRunStatus(init_runId,"staging","run files successfully retrieved from the database")
        except Exception as e:
            self.logger.update("SVC_FILELIST_FAILED",message="%s"%str(e))
            apolloDB.setRunStatus(init_runId,"failed","%s"%self.logger.pollStatus()[1])
            response[1]._methodCallStatus._status = 'failed'
            response[1]._methodCallStatus._message = str(e)
            return response
        
        # Send file to remote machine
        try:
            remoteScr = '%s.%s'%(simConf['runDirPrefix'],str(randID))
            conn._mkdir(remoteScr)
            conn.sendFile('{0}/job_{1}.zip'.format(tempDirName,init_runId),'{0}/job_packet.zip'.format(remoteScr))
            conn.sendFile('{0}/batch_run{1}.py'.format(tempDirName,init_runId),'{0}/batch_run.py'.format(remoteScr))
            shutil.rmtree(tempDirName)
            
            self.logger.update("SVC_FILE_SEND_SUCCESS",message="%s"%tempDirName)
            apolloDB.setRunStatus(init_runId,"staging","run files successfully retrieved from the database")
        except Exception as e:
            self.logger.update("SVC_FILE_SEND_FAILED",message="%s"%e)
            apolloDB.setRunStatus(init_runId,"failed",self.logger.pollStatus()[1])
            response[1]._methodCallStatus._status = 'failed'
            response[1]._methodCallStatus._message = str(e)            
            return response
        
        # unzip and run the job on the remote machine
        try:
            apolloDB.setRunStatus(init_runId,"staging","executing on the remote system")
            returnVal = conn._executeCommand("cd {0}/{1}; chmod a+x batch_run.py; nohup ./batch_run.py >& out &".format(conn._remoteDir,
                                                                                                                  remoteScr))                                                                                                                
            self.logger.update("SVC_SUBMIT_JOB_SUCCESS",message="%s"%returnVal)
            
            conn._close()
            t = Thread(target=monitorBatchStatus,args=(init_runId,apolloDB))
            t.start()
        except Exception as e:
            self.logger.update("SVC_SUBMIT_JOB_FAILED",message="%s"%str(e))
            apolloDB.setRunStatus(init_runId,"failed",self.logger.pollStatus()[1])
            response[1]._methodCallStatus._status = 'failed'
            response[1]._methodCallStatus._message = str(e)
            return response

        response[1]._methodCallStatus._status = 'staging'
        response[1]._methodCallStatus._message = 'runSimulation call completed successfully'
        return response

#run a webserver 
AsServer(port=int(simWS.configuration['local']['port']), services=[SimulatorWebService('pscsimu'), ])

