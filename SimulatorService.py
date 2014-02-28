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
from SimulatorService_v2_0_services import runSimulationRequest
'''
Created on Nov 27, 2012

This is an example GenericEpidemicModelService implementation.

@author: John Levander, Shawn Brown
'''

from ZSI.wstools import logging
from SimulatorService_v2_0_services_server import SimulatorService_v2_0
from ZSI.ServiceContainer import AsServer
from SimulatorService_v2_0_services_types import *
from ApolloFactory import *
from ApolloUtils import *
from SimulatorService_v2_0_services import *
import os,sys
import shutil
import random
import datetime
import paramiko
import simWS
from logger import Log
from commission import SSHConn
from TranslatorService_v2_0_services import *
import urllib2

connections = {} 

class SimulatorWebService(SimulatorService_v2_0):
        _wsdl = "".join(open("simulatorservice20.wsdl").readlines())
        
        factory = ApolloFactory()
        utils = ApolloUtils()
	logger = Log(simWS.configuration['local']['logFile'])
        logger.start()
	
        #def soap_getSupportedLocations(self, ps, **kw):
        #    response = SimulatorService_v2_0.soap_getSupportedLocations(self, ps, **kw)
        #    
        #    spl = self.factory.new_SupportedPopulationLocation()
        #    
        #    spl._populationLocation = "42003"
        #    spl._populationLocationDescription = "Allegheny County"
        #    
        #    response._supportedPopluationLocations.append(spl)
        #    return response
        
        #this method checks on the status of a job, indicated by the jobs runId
        def soap_getRunStatus(self, ps, **kw):
            response = SimulatorService_v2_0.soap_getRunStatus(self, ps, **kw)
            #get the run id of the job 
            request = ps.Parse(getRunStatusRequest.typecode)
            runId = request._runId
	    print "Looking up run status of %s"%runId
	    ### First, check the log file to see if this status has been logged
	    logs = {}
	    with open("./service_log.txt","rb") as f:
		for line in f:
		    lineSplit = line.strip().split(":")
		    logs[lineSplit[0]] = lineSplit[1]

	    if runId in logs.keys():
		status = logs[runId]
                message = "This was read from the service cache"
		print "Returning " + str(status) + " " + message
            else:	   	    
		if request._runId not in connections.keys():
			status = "failed"
			message = "Simulation Service doesn't know anything about runId %s"%str(request._runId)
		else:
                	status, message = connections[request._runId].getStatus(runId)
			if status == "COMPLETED" or status == "FAILED":
				with open('./service_log.txt','ab') as f:
					f.write('%s:%s\n'%(runId,status))

            response._runStatus = self.factory.new_MethodCallStatus()
            response._runStatus._status = status.lower()
            response._runStatus._message = message
            
            return response

        #this method runs an epidemic model
        def soap_runSimulation(self, ps, **kw):
            try:
                response = SimulatorService_v2_0.soap_runSimulation(self, ps, **kw)
                request = ps.Parse(runSimulationRequest.typecode)
                self.logger.update("SVC_APL_RESQ_RECV")
            except Exception as e:
                self.logger.update("SVC_APL_RESQ_RECV_FAILED",message="%s"%str(e))
                response._runId = self.logger.pollStatusCode()
                response._message = self.logger.pollStatus()[1]
                return response
            #extract the epidemic model input object from the request
	    
	    ## Parse and Translate the Apollo message First
            try:
                cfg = request._runSimulationMessage
                transService = TranslatorService_v2_0Locator().getTranslatorServiceEI(url="http://research.rods.pitt.edu"+\
                                                                                        "/translatorservice2.0/services/"+\
                                                                                        "translatorservice")	    
                transReq = translateRunSimulationMessage()
                transReq._runSimulationMessage = cfg
                transResp = transService.translateRunSimulationMessage(transReq)
            
            
                idPrefix = cfg._simulatorIdentification._softwareDeveloper +\
                       "_" + cfg._simulatorIdentification._softwareName +\
                       "_" + cfg._simulatorIdentification._softwareVersion + "_"
                
                self.logger.update("SVC_APL_TRANS_RECV",message="%s"%str(idPrefix))
            except Exception as e:
                self.logger.update("SVC_APL_TRANS_FAILED",message="%s"%str(e))
                response._runId = self.logger.pollStatusCode()
                response._message = self.logger.pollStatus()[1]
                return response
            
            try:
                confId = simWS.configuration['simulators']['mappings'][idPrefix]
		simConf = simWS.configuration['simulators'][confId]
                conn = SSHConn(self.logger,machineName_=simConf['defaultMachine'][0])
                self.logger.update("SRV_SSH_CONN_SUCCESS",message="%s"%str(idPrefix))
            except Exception as e:
                self.logger.update("SVC_SSH_CONN_FAILED",message="%s"%str(e))
                response._runId = self.logger.pollStatusCode()
                response._message = self.logger.pollStatus()[1]
                return response
            
            ### Make a random directory name so that multiple calls can be made
            
            try:
                    randID = random.randint(0,100000)
                    tempDirName = "%s/fred.tmp.%d"%(simWS.configuration["local"]["scratchDir"],randID)
                    os.mkdir(tempDirName)
                    self.logger.update("SVC_TMPDIR_SUCCESS",message="%s"%tempDirName)
            except Exception as e:
                    self.logger.update("SVC_TMPDIR_FAILED",message="%s"%str(e))
                    #print("Cannot make temporary simulation directory %s"%(tempDirName))
                    response._runId = self.logger.pollStatusCode()
                    response._message = self.logger.pollStatus()[1]
                    return response

	    ### Get a list of the files
	    try:
		    fileList = [x for x in urllib2.urlopen(transResp._methodCallStatus._message).read().split('\n') if x != '']
		    print str(fileList)
		    fileDict = {}
		    for fileName in fileList:
			    fileDict[fileName] = urllib2.urlopen(transResp._methodCallStatus._message + "/" + fileName).read()

		    self.logger.update("SVC_FILELIST_RECIEVED")
	    except Exception as e:
		    self.logger.update("SVC_FILELIST_FAILED",message="%s"%str(e))
		    response._runId = self.logger.pollStatusCode()
		    response._message = self.logger.pollStatus()[1]
		    return response
        
	    for fileName,content in fileDict.items():
		    with open(tempDirName+"/"+fileName,"wb") as f:
			    f.write("%s"%content)
        
	    remoteScr = 'fred.tmp.%s'%str(randID)
            conn._mkdir(remoteScr)

	    for fileName,content in fileDict.items():
		    conn.sendFile(tempDirName + "/" + fileName, remoteScr + "/" + fileName)
	    
	    ### we do not need temp directory anymore
	    shutil.rmtree(tempDirName)
	    

	    returnVal = conn.submitJob(randID,idPrefix,idPrefix)
            #print returnVal

	    ### parse the run ID
	    response._runId = idPrefix + str(returnVal)      
	    
	    ### Add this connection to the dictionary of connections
	    connections[response._runId] = conn
            return response

#run a webserver on 8087
AsServer(port=8094, services=[SimulatorWebService('fred'), ])

