#!/usr/local/packages/bin/python 
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
from SimulatorService_v2_0_1_services import runSimulationRequest
'''
Created on Nov 27, 2012

This is an example GenericEpidemicModelService implementation.

@author: John Levander, Shawn Brown
'''

from ZSI.wstools import logging
from SimulatorService_v2_0_1_services_server import SimulatorService_v2_0_1
from ZSI.ServiceContainer import AsServer
from SimulatorService_v2_0_1_services_types import *
from ApolloFactory import *
from ApolloUtils import *
from SimulatorService_v2_0_1_services import *
import os,sys
import shutil
import random
import datetime
import paramiko
import simWS
from logger import Log
from commission import SSHConn
from statusDB import StatusDB
from apollo import ApolloDB

#from TranslatorService_v2_0_1_services import *
#import urllib2

connections = {} 
statusDB = StatusDB()
class SimulatorWebService(SimulatorService_v2_0_1):
    _wsdl = "".join(open("simulatorservice201.wsdl").readlines())
        
    factory = ApolloFactory()
    utils = ApolloUtils()
    logger = Log(simWS.configuration['local']['logFile'])
    logger.start()

    #statusDB = StatusDB()

   #this method checks on the status of a job, indicated by the jobs runId
    def soap_getRunStatus(self, ps, **kw):
        response = SimulatorService_v2_0_1.soap_getRunStatus(self, ps, **kw)
            #get the run id of the job 
        request = ps.Parse(getRunStatusRequest.typecode)
        runId = str(request._runId)
        print "Looking up run status of %s"%runId
	status,message = statusDB.getEntry(runId)
        print "Status for %s is %s"%(runId,status)
	goCheckList = ["queued","running","unknown","logfilewritten"]
        errorList = ['LOGERROR']
        	
        ### First, check the log file to see if this status has been logged
        if status in goCheckList:
            print "checking "+ str(connections.keys())
            if str(request._runId) not in connections.keys():
                status = "failed"
                message = "Simulation Service doesn't know anything about runId %s"%str(request._runId)
                statusDB.updateEntry(runId,status,message)
            else:
		pbsId = statusDB.getPBSId(runId)
                status, message = connections[runId].getStatus(runId,pbsId)
                print "Parsing status of %s"%status
                if status in errorList: status = 'failed'
                statusDB.updateEntry(runId,status.lower(),message)

        response._runStatus = self.factory.new_MethodCallStatus()
        response._runStatus._status = status.lower()
        response._runStatus._message = message
            
        return response

        # this method runs an epidemic model
    def soap_runSimulation(self, ps, **kw):
        try:
            response = SimulatorService_v2_0_1.soap_runSimulation(self, ps, **kw)
            request = ps.Parse(runSimulationRequest.typecode)
            runId = request._simulationRunId
            statusDB.updateEntry(runId,'staging')
            self.logger.update("SVC_APL_RESQ_RECV")
        except Exception as e:
            self.logger.update("SVC_APL_RESQ_RECV_FAILED", message="%s" % str(e))
            #response._runId = self.logger.pollStatusCode()
            response._message = self.logger.pollStatus()[1]
            return response
 
        # Parse and Translate the Apollo message First
        try:
            cfg = request._runSimulationMessage
            idPrefix = cfg._simulatorIdentification._softwareDeveloper +\
                       "_" + cfg._simulatorIdentification._softwareName +\
                       "_" + cfg._simulatorIdentification._softwareVersion + "_"
                 
            
            self.logger.update("SVC_APL_TRANS_RECV",message="%s"%str(idPrefix))
        except Exception as e:
            self.logger.update("SVC_APL_TRANS_FAILED",message="%s"%str(e))
            response._runId = self.logger.pollStatusCode()
            response._message = self.logger.pollStatus()[1]
            statusDB.updateEntry(runId,"ERROR",str(self.logger.pollStatusCode()) + ":"\
                                 + str(self.logger.pollStatus()[1]))
            return response

        # Create the current connector
        
        try:
            confId = simWS.configuration['simulators']['mappings'][idPrefix]
            simConf = simWS.configuration['simulators'][confId]
            conn = SSHConn(self.logger,machineName_=simConf['defaultMachine'][0])
            connections[str(runId)] = conn
            self.logger.update("SRV_SSH_CONN_SUCCESS",message="%s"%str(idPrefix))
        except Exception as e:
            self.logger.update("SVC_SSH_CONN_FAILED",message="%s"%str(e))
            response._runId = self.logger.pollStatusCode()
            response._message = self.logger.pollStatus()[1]
            return response

        
        # Make a random directory name so that multiple calls can be made
             
        try:
            randID = random.randint(0,100000)
            tempDirName = "%s/fred.tmp.%d"%(simWS.configuration["local"]["scratchDir"],randID)
            os.mkdir(tempDirName)
            self.logger.update("SVC_TMPDIR_SUCCESS",message="%s"%tempDirName)
        except Exception as e:
            self.logger.update("SVC_TMPDIR_FAILED",message="%s"%str(e))
            #print("Cannot make temporary simulation directory %s"%(tempDirName))
            #response._runId = self.logger.pollStatusCode()
            response._message = self.logger.pollStatus()[1]
            return response

        # Get the files from the Apollo DB
        try:
            apolloDB = ApolloDB(logger_=self.logger)
            apolloDB.connect()
            translatorServiceId = apolloDB.getTranslatorServiceKey()
            simulatorServiceId = apolloDB.getSimulatorServiceKey(cfg._simulatorIdentification._softwareDeveloper,
                                                                 cfg._simulatorIdentification._softwareName,
                                                                 cfg._simulatorIdentification._softwareVersion)

            
            simulatorInputFileDict = apolloDB.getSimulationInputFilesForRunId(runId,translatorServiceId,simulatorServiceId)
            apolloDB.close()
            for fileName,content in simulatorInputFileDict.items():
                print fileName
                with open(tempDirName+"/"+fileName,"wb") as f:
                    f.write("%s"%content)

            self.logger.update("SVC_FILELIST_RECIEVED")
        except Exception as e:
            self.logger.update("SVC_FILELIST_FAILED",message="%s"%str(e))
            response._runId = self.logger.pollStatusCode()
            response._message = self.logger.pollStatus()[1]
            return response

        try:
            remoteScr = 'fred.tmp.%s'%str(randID)
            conn._mkdir(remoteScr)
 
            for fileName,content in simulatorInputFileDict.items():
                conn.sendFile(tempDirName + "/" + fileName, remoteScr + "/" + fileName)

            ### we do not need temp directory anymore
            shutil.rmtree(tempDirName)
            
            self.logger.update("SVC_FILE_SEND_SUCCESS",message="%s"%tempDirName)
        except Exception as e:
            self.logger.update("SVC_FILE_SEND_FAILED",message="%s"%e)
            response._runId = self.logger.pollStatusCode()
            response._message = self.logger.pollStatus()[1]
            return response

        try:
            (jobType,returnVal) = conn.submitJob(randID,runId,idPrefix)
	    print "JobType = %s returnVal = %s"%(jobType,str(returnVal))
	    if jobType == "pbs":
		statusDB.updatePBSId(runId,"pbs",returnVal) 
            statusDB.updateEntry(runId,'queued',"%s"%returnVal)
            self.logger.update("SVC_SUBMIT_JOB_SUCCESS",message="%s"%returnVal)
        except Exception as e:
            self.logger.update("SVC_SUBMIT_JOB_FAILED",message="%s"%str(e))
            response._runId = self.logger.pollStatusCode()
            response._message = self.logger.pollStatus()[1]
            return response

        
        response._runId = str(idPrefix) + str(runId)
        response._message = "%s has successfully been processed by runSimulation"%str(runId)
        return response

#run a webserver on 8087
AsServer(port=8045, services=[SimulatorWebService('fred'), ])

