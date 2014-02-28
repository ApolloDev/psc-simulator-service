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


'''
Created on Feb, 8, 2013

@author: Shawn Brown
'''
import os,sys
import paramiko
import select
import datetime,dateutil.parser
import time
import math
#from threading import Thread
from multiprocessing import Process,Queue
#from ApolloUtils import *
import simWS
from logger import Log

class SSHConn:
    def __init__(self, logger_, machineName_="blacklight.psc.xsede.org", debug_=False):
        # Machine Parameters
        self.logger = logger_
        print simWS.configuration['machines'].keys()
        if machineName_ not in simWS.configuration['machines'].keys():
            self.logger.update('CONF_MACHINE_FIND_FAILED')
           
        
	self._machine = machineName_
	self._configuration = simWS.configuration['machines'][self._machine]
        self._simConfigs = simWS.configuration['simulators']

        self._username = self._configuration['username']
        self._password = self._configuration['password']
        self._privateKeyFile = self._configuration['privateKeyFile']
        
	self._localConfiguration = simWS.configuration['local']

	self._ssh = None
	self._transport = None
	self._sftp = None

	self.isConnectedSSH = False
	self.isConnectedSFTP = False
	
        self.name = "SSH Connection: %s"%self._machine
	self.debug = debug_	
        ### Flags for internals
        self._runPBS = False
	self._numUNKNOWN = 0

        if self._configuration['queueType'] == 'PBS':
            self._runPBS = True
        
        #self._getScratch = False
        #if self.configuration['remoteDir'] == '$SCRATCH':
        #    self._getScrath = True

	self._remoteDir = self._configuration['remoteDir']
        if self._remoteDir == "$SCRATCH":
            try:
                if self.debug: print 'On connection %s getting scratch directory'%self.name
                self._remoteDir = self._getScratchDir()
                if self.debug: print 'Got %s as scratch directory on connection %s'%(self._remoteDir,self.name)
                self.logger.update('SSH_SCRATCH_DIR_SUCCESS')
            except Exception as e:
                self.logger.update('SSH_SCRATCH_DIR_FAILED',message="%s"%str(e))
                raise e

	#self._statusFileDir = self._localConfiguration['statusFileDir']
	#self._statusFile = None
	self._remoteTmpDir = None
	self._runScript = None
	self._runScriptName = None
        self._directRunDirectory = None
        self._startTiming = False
            
	    
    def _connect(self,blocking=True):
	### open SSH connection
        timeout = 3000
        count = 0
        while True:
            if (self.isConnectedSSH is False and self.isConnectedSFTP is False):
                break
            if count > timeout:
                self.logger.update("SSH_CONN_TIMEOUT")
                self._close()
            time.sleep(0.5)
            count += 1

	self.ssh = paramiko.SSHClient()
	self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

	if self.debug: 
            print 'Establishing SSH connection %s'%(self.name)

	try:
            self.ssh.connect(self._machine,
                             username=self._username,
                             password=self._password,
                             key_filename=self._privateKeyFile)

            self.isConnectedSSH = True
            self.logger.update('SSH_CONN_ESTABLISHED')

        except Exception as e:
            self.logger.update('SSH_CONN_FAILED',message = "%s"%str(e))
            raise e

       
	if self.debug: print 'SSH connection %s established'%(self.name)
	
	### open SFTP connection
	if self.debug: print 'Establishing SFTP connection %s'%(self.name)
	
        try:
            self.transport = paramiko.Transport((self._machine,22))
            if self._privateKeyFile:
                privateKey = paramiko.RSAKey.from_private_key_file(self._privateKeyFile)
                self.transport.connect(username=self._username,
                                       pkey = privateKey)
            else:
                self.transport.connect(username=self._username,
                                       password=self._password)

            self.sftp = paramiko.SFTPClient.from_transport(self.transport)
            self.isConnectedSFTP = True
            self.logger.update('SFTP_CONN_ESTABLISHED')
        
        except Exception as e:
            self.logger.update('SFTP_CONN_FAILED',message="%s"%str(e))
            raise e
        

	if self.debug: print 'SFTP connection %s established'%self.name
	
    def _close(self):
        try:
            self.ssh.close()
            self.isConnectedSSH = False
            self.logger.update("SSH_CONN_CLOSED")
        except:
            self.logger.update("SSH_CONN_CLOSE_FAILED")
            raise
        
        try:
            self.sftp.close()
            self.transport.close()
            self.isConnectedSFTP = False
            self.logger.update("SFTP_CONN_CLOSED")
        except:
            self.logger.update("SFTP_CONN_CLOSE_FAILED")
            raise

    def _getScratchDir(self):
	remote_command = 'echo $SCRATCH'
        try:
            returnVal = None
            while returnVal is None:
                returnVal = self._executeCommand(remote_command)
            scratchString = ""
	    scratchString = returnVal.strip()
            self.logger.update("SSH_GETSCRATCH_SUCCESS",message="%s"%scratchString)
	except Exception as e:
            self.logger.update("SSH_GETSCRATCH_FAILED",message="%s"%str(e))
            raise
	    #raise RuntimeError("Error in getting SCRATCH directory through connection %s"%self.name)
        
	return scratchString
        
    def _executeCommand(self,command):	
        stdin=None
	stdout=None
	stderr=None
        returnValue=None
	try:
            self._connect()
            print "Excecuting %s"%command
	    stdin,stdout,stderr = self.ssh.exec_command(command)
            
            while not stdout.channel.exit_status_ready():
                if stdout.channel.recv_ready():
                    rl,wl,xl = select.select([stdout.channel],[],[],0.0)
                    if len(rl) > 0:
                        returnValue = stdout.channel.recv(1024)
                        print "Status: " + str(stdout.channel.recv(1024))
            self._close()
            self.logger.update('SSH_EXECUTE_SUCCESS',message='Command = %s'%command)
	except Exception as e:
            self.logger.update('SSH_EXECUTE_FAILED',message='Command = %s,%s'%(command,str(e)))
	    print "There was an error exectuting the command on connections %s:"%self.name
	    print "%s"%command
	    print "stderr returned: %s"%str(stderr) 
	    raise e
#RuntimeError('Error with executing "%s" over %s'%(command,self.name))
        
        print "RETURNING " + str(returnValue)
	return returnValue

    def _mkdir(self,remoteDirectoryName):
        if self.debug: print "Making %s directory on %s"%(remoteDirectoryName,self.name)
        if self._remoteDir is not None:
            remoteDirectoryName = self._remoteDir + "/" + remoteDirectoryName
        if self.debug: print "Parsed remote directory is %s"%remoteDirectoryName
        try:
            self._connect()
            self.sftp.mkdir(remoteDirectoryName)
            self.logger.update('SSH_MKDIR_SUCCESS',message='%s'%remoteDirectoryName)
            self._close()
        except Exception as e:
            print e
            self.logger.update('SSH_MKDIR_FAILED',message='%s'%remoteDirectoryName)
            raise e 

#     def _sendStringToFile(self,content,remoteFileName=None):
# 
#         if remoteFileName is None:
#             remoteFileName = localFileName
# 
#         if self._remoteDir is not None:
#             remoteFileName = self._remoteDir + "/" + remoteFileName
# 
#         if self.isConnectedSSH is False:
#             self.logger.update("SSH_SENDSTRTOFILE_BEFORE_ESTB")
#             raise RuntimeError("Trying to send a string to a file through %s before openning the SSH connection"\
#                                %self.name)
# 
#         try:
#             command = "echo \"%s\" > %s"%(content,remoteFileName)
#             #command = "echo \"%s\""%(content)
#             print "command = " + command
#             self._executeCommand(command)
#             self.logger.update("SSH_SENDSTRTOFILE_SUCCESS",message="STRING->%s"%(remoteFileName))
#         except Exception as e:
#             self.logger.update("SSH_SENDSTRTOFILE_FAILED",message="STRING->%s: %s"%(remoteFileName,str(e)))
#             raise
        
    def sendFile(self,localFileName,remoteFileName=None):
        if remoteFileName is None:
            remoteFileName = localFileName
        if self._remoteDir is not None:
            remoteFileName = self._remoteDir + "/" + remoteFileName
        try:
            self._connect()
            self.sftp.put(localFileName,remoteFileName)
            self.logger.update("SSH_SENDFILE_SUCCESS",message="%s->%s"%(localFileName,remoteFileName))
            self._close()
        except Exception as e:
            self.logger.update("SSH_SENDFILE_FAILED",message="%s->%s: %s"%(localFileName,remoteFileName,str(e)))
            raise 

    def submitJob(self,tmpId,simId,simulator="fred",size="medium"):
        
        idString = "BAD"
        
        try:
            simKey = self._simConfigs['mappings'][simulator]
            simulatorConf = self._simConfigs[simKey]
            self.logger.update("SUBMIT_SIM_CONF_FOUND",message="%s"%simulator)
        except:
            self.logger.update("SUBMIT_SIM_CONF_FAILED",message="%s"%simulator)
            raise
        
        try:
            if self._runPBS:
                
                idString = self._submitPBSJob(tmpId,simId,simulatorConf,size)

            else:
                ### Generate the runID here and pass it into submit Job for threading
                timeStamp = int(time.time())
                idSuffix = str(simId)+str(timeStamp)
                idPrefix = simId
                #t = Process(target=self._submitDirectJob,args=(tmpId,idSuffix,simulatorConf,size))
                #t.start()
                self._submitDirectJob(tmpId,idSuffix,simulatorConf,size)
                idString = str(timeStamp)
            self._startTiming = True
            self.logger.update("SSH_SUBMIT_JOB_SUCCESS")
        except Exception as e:
            self.logger.update("SSH_SUBMIT_JOB_FAILED",message='%s'%str(e))
        
	if idString == "BAD":
	    raise RuntimeError("There was a problem submitting the job through connection %s"%self.name)

	return idString
	
    def _submitDirectJob(self,tmpId,simId,simConf,size="small"):
        ### set and update the status file
        try:
            ## Create the run script 
            with open("%s/apollorun.%s.csh"%(self._localConfiguration['scratchDir'],str(tmpId)),"wb") as f:
                f.write("%s"%self._createDirectRunScript(simConf,simId,size=size))
            self._directRunDirectory = "%s.%s"%(simConf['runDirPrefix'],str(tmpId))
            self.sendFile("%s/apollorun.%s.csh"%(self._localConfiguration['scratchDir'],str(tmpId)),"%s/apollorun.csh"%self._directRunDirectory)
            self.sendFile("./templates/starttime","%s/starttime"%self._directRunDirectory)

            remote_command = 'cd %s/%s.%s;'%(self._remoteDir,simConf['runDirPrefix'],str(tmpId)) 
            remote_command += 'setenv id ' + simId + '; '
            remote_command += 'chmod a+x ./apollorun.csh; ./apollorun.csh'
            
            t = Process(target=self._executeCommand,args=(remote_command,))
            t.start()
            
            #retVal = self._executeCommand(remote_command)
            self.logger.update("SSH_DIRECT_JOB_SUCCESS")
        except Exception as e:
            self.logger.update("SSH_DIRECT_JOB_FAILED",message="%s"%str(e))
            raise e
         
        return 1
    def _submitPBSJob(self,tmpId,simId,simConf,size="small"):
        ## Create starttime file
        try:
            with open(self._localConfiguration['scratchDir'] + "/submit.pbs.%s"%str(tmpId),"wb") as f:
                f.write("%s"%self.createPBSRunScript(simConf,simId,size=size))
            self.sendFile(self._localConfiguration['scratchDir'] + "/submit.pbs.%s"%str(tmpId),simConf['runDirPrefix']+"."+str(tmpId)+"/submit.pbs")
            self.sendFile('./templates/starttime',simConf['runDirPrefix']+"."+str(tmpId) + '/starttime')
            self._startTiming = True
            self.logger.update("SSH_PBS_CREATE_SCRIPT_SUCCESS")
        except Exception as e:
            self.logger.update("SSH_PBS_CREATE_FAILED",message="%s"%str(e))
            raise e
        
        remote_command = ""
        try:
            if self._remoteDir is not None:
                remote_command += 'cd %s/%s.%s; '%(self._remoteDir,simConf['runDirPrefix'],str(tmpId))
            else:
                remote_command += 'cd %s.%s;'%(simConf['runDirPrefix'],str(tmpId))

            remote_command += self._configuration['submitCommand'] + " submit.pbs"
            
            returnVal = self._executeCommand(remote_command)
            idString = ""
            
            try:
                idString = returnVal.split('.')[0]
                self.logger.update("SSH_PBS_ID_SUCCESS")
            except Exception as e:
                self.logger.update("SSH_PBS_ID_FAILED",message="%s"%str(e))
                raise e#RuntimeError("Error in getting PBS ID through connection %s"%self.name)
            self.logger.update("SSH_PBS_SUBMIT_SUCCESS",message="%s"%str(idString))
        except Exception as e:
            self.logger.update("SSH_PBS_SUBMIT_FAILED",message="%s"%str(e))
            raise e
	### Set PBSPBS directory
	self.pbsWorkDir = "%s/%s.%s"%(self._remoteDir,simConf['runDirPrefix'],str(tmpId))

	return idString
		
    def _getPBSQueueStatus(self,pbsID):
        try:
            remote_command = "%s %s"%(self._configuration['qstatCommand'],str(pbsID))
            pbsStatus = "U"
            
            unkFlag = False
            returnVal = None
            
            returnVal = self._executeCommand(remote_command)
            if returnVal is None:
                return "U"
            else:
                statusList = returnVal.split("\n")
                #print "StatusList = " + str(statusList)
                pbsString = statusList[len(statusList)-2]
                if self.debug: print "PBSString = " + str(pbsString)
                pbsStatus = pbsString.split()[4]
            self.logger.update("SSH_PBS_QSTAT_SUCCESS",message="%s"%(str(pbsID)))
        except Exception as e:
            unkFlag = True
            self.logger.update("SSH_PBS_QSTAT_FAILED",message="%s: %s"%(str(pbsID),str(e)))
            raise
        
        return pbsStatus
    
    def _getPBSTimeContents(self):
        if not self._startTiming:
            print "StartTiming is false"
            return ("QUEUED","0",0.0)
        print "Timing is true"
        remoteCommand = "tail -1 %s/starttime"%(self.pbsWorkDir)
        returnVal = None
        while returnVal is None:
            returnVal = self._executeCommand(remoteCommand)
        
        returnVal = returnVal.strip()
        if returnVal == "Nothing":
            secondsRunning = -1.0
            status = "Nothing"
            date = "Nothing"
        else:
            status = returnVal.split()[0]
            date = " ".join(returnVal.split()[1:])
            timeValTZ = dateutil.parser.parse(date)
            timeVal = timeValTZ.replace(tzinfo=None)
            now = datetime.datetime.now()
            secondsRunning = (now-timeVal).seconds
            
        return (status,date,secondsRunning)
    
    def _getDirectTimeContents(self):
        if not self._startTiming:
            return ("QUEUED","0",0.0)
        remoteCommand = "tail -1 %s/%s/starttime"%(self._remoteDir,self._directRunDirectory)
        print remoteCommand
        returnVal = None
        while returnVal is None:
            returnVal = self._executeCommand(remoteCommand)
        print "DirTim: " + str(returnVal) + " " + str(returnVal is None)
        
        returnVal = returnVal.strip()
        if returnVal == "Nothing":
            secondsRunning = -1.0
            status = "Nothing"
            date = "Nothing"
        else:
            status = returnVal.split()[0]
            date = " ".join(returnVal.split()[1:])
            timeValTZ = dateutil.parser.parse(date)
            timeVal = timeValTZ.replace(tzinfo=None)
            now = datetime.datetime.now()
            secondsRunning = (now-timeVal).seconds
            
        return (status,date,secondsRunning)
    
    def getStatus(self,key):
	pbsStatus = None
	status = "UNKNOWN"
	response = "Empty Response"
	if self._runPBS:
	    pbsSplit = str(key).split("_")
	    pbsID = pbsSplit[len(pbsSplit)-1]
	    pbsStatus = self._getPBSQueueStatus(pbsID)
	    if pbsStatus == "U":
                rstat,date,secondsRunning = self._getPBSTimeContents()
                if rstat == "COMPLETED":
                    status = "COMPLETED"
                    response = 'The run completed successfully at %s'%(date)
                else:
		    self._numUNKNOWN +=1
		    if self._numUNKNOWN > 50:
			status = "ERROR"
			response = "Too Many Failures in Get Status"
		    else:
			status = "UKNOWN"
                    	response = "The service was unable to determine the status of the jobs (time#: %d)"%self._numUNKNOWN
			
            
	    elif pbsStatus == "Q":
		status = "QUEUED"
		response = 'The run is queued on ' + self._machine +\
			   ' at ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
	    elif pbsStatus == "R":
		status = "RUNNING"
                rstat,date,secondsRunning = self._getPBSTimeContents()
                print "Running Date: " + str(rstat) + " " + str(date) + " " + str(secondsRunning)
                if rstat == "Nothing":
                    response = "The run is running on " + self._machine +\
                        ' at ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M") 
                else:
                    response = "The run has been running for %g seconds on %s at %s"\
                        		   %(secondsRunning,self._machine,date)
            
	    else:
		status = "UNKNOWN"
		response = "getStatus on connection %s returned an unknown response"\
			   %self.name		
		
	    return (status,response)
	else:
#            print "Direct Running not supported yet"
            status,date,secondsRunning = self._getDirectTimeContents()
            print "Status, Date, seconds Running: ,%s,%s,%s"%(status,str(date),str(secondsRunning))
            
            ## make this more robust
            if status == "RUNNING":
                response = "The run has been running for %g seconds on %s at %s"\
                        		   %(secondsRunning,self._machine,date)
                
            elif status == "QUEUED":
                response = 'The run is queued on ' + self._machine +\
                    ' at ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

            elif status == "COMPLETED":
                response = 'The run completed successfully at %s'%(date)
	return (status,response)

    def createPBSRunScript(self,simConf,id,size="debug"):
        try:
            PBSList = []
            PBSList.append("#!/bin/csh\n")
            PBSList.append("#PBS %s"%(self._configuration[size]))
            PBSList.append("\n")
            PBSList.append("%s\n\n"%self._configuration['special'])
            if self._configuration['useModules']:
                PBSList.append("%s\n"%simConf['moduleCommand'])
            PBSList.append("cd $PBS_O_WORKDIR\n")
            PBSList.append("echo RUNNING `date` > starttime\n")
            PBSList.append("%s\n"%self._configuration['getID'])

            PBSList.append("%s %s\n"%(simConf['runCommand'].replace("<<ID>>",str(id)),simConf[size]))
            PBSList.append("%s\n"%(simConf['dbCommand'].replace('<<ID>>',str(id))))
            PBSList.append("echo COMPLETED `date` > starttime\n")
            self.logger.update("SSH_CREATEPBSRUN_SUCCESS")
        except Exception as e:
            self.logger.update("SSH_CREATEPBSRUN_FAILED",message=str(e))
            raise e
        
        return ("").join(PBSList)
    
    def _createDirectRunScript(self,simConf,id,size="small"):
        try:
            LocalList = []
            ### This is language to only allow one run to go at a time.
            LocalList.append('#!/bin/csh\n')
            LocalList.append("echo QUEUED `date` > starttime\n")
            LocalList.append('while ( -e /tmp/.lock1 && -e /tmp/.lock2)\n')
            LocalList.append('sleep 1\n')
            LocalList.append('end\n')

            LocalList.append('set lockfile = ""\n')
            LocalList.append('if( ! -e /tmp/.lock1 ) then\n')
            LocalList.append('   touch /tmp/.lock1\n')
            LocalList.append('   set lockfile = /tmp/.lock1\n')
            LocalList.append('else if ( ! -e /tmp/.lock2 ) then\n')
            LocalList.append('   touch /tmp/.lock2\n')
            LocalList.append('  set lockfile = /tmp/.lock2\n')
            LocalList.append('endif\n')

            LocalList.append('echo RUNNING `date` > starttime\n')
            LocalList.append('### Generate Timestamp for ID\n')
            LocalList.append("%s %s\n"%(simConf['runCommand'].replace("<<ID>>",str(id)),simConf[size]))
            LocalList.append("%s\n"%(simConf['dbCommand'].replace("<<ID>>",str(id))))
            LocalList.append("echo COMPLETED `date` > starttime\n")
            LocalList.append("rm -rf $lockfile\n")
            self.logger.update("SSH_CREATEDIRRUN_SUCCESS")
        except Exception as e:
            self.logger.update("SSH_CREATEDIRRUN_FAILED",message=str(e))
            raise e

        return ("").join(LocalList)
        
            
def jsonDict2Obj(d):
    if isinstance(d, list):
	d = [jsonDict2Obj(x) for x in d]
    if not isinstance(d, dict):
	return d
    class C(object):
	pass
    o = C()
    for k in d:
	o.__dict__['_'+k] = jsonDict2Obj(d[k])
    return o

def main():
    import random
    import time

    ### STB to do: Unit test parsings
    ## Test the FREDInputBatch
    #fredBatch = FredBatchInputs()
    #fredBatch.setupFromJsonListFile("sample_json_simulator_configuration.txt")
    
    connections = {}
    #sys.exit()
    ### Test on Blacklight
    logger = Log(logFileName_='./test.log')
    for i in range(0,10):
        tempId = random.randint(0,100000)
        if i < 2:
            connections[tempId] = SSHConn(logger,machineName_='blacklight.psc.xsede.org',debug_=True)
        else:
            connections[tempId] = SSHConn(logger,machineName_='unicron.psc.edu',debug_=True)
        
        connections[tempId]._mkdir(simWS.configuration['simulators']['test']['runDirPrefix']+"."+str(tempId))
        pbsId = connections[tempId].submitJob(tempId,simId="Test_ID",simulator="test",size="debug")

    while True: 
        completed = True
        for id,conn in connections.items():
            status,response = conn.getStatus(pbsId)
            print "For Conn %s Status,Response: %s,%s"%(str(id),status,response)
            if status != "COMPLETED":
                completed = False
        if completed is True:
            break
        print "For ----------"
        time.sleep(1)

### Main Hook

if __name__=="__main__":
    main()
