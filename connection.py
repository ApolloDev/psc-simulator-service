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
Created on Feb, 8, 2013

@author: Shawn Brown
'''
import os,sys
import paramiko
import select
import datetime,dateutil.parser
import time
import math
from multiprocessing import Process,Queue
import simWS
from logger import Log

class SSHConn:
    def __init__(self, logger_, machineName_="olympus.psc.edu", debug_=False):
        # Machine Parameters
        self.logger = logger_
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
            self.logger.update('SSH_CONN_FAILED', message="%s" % str(e))
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
            raise e
        
	return scratchString
        
    def _executeCommand(self,command):	
        stdin=None
        stdout=None
        stderr=None
        returnValue=None
        try:
            self._connect()
            if self.debug: print "Excecuting %s"%command
            stdin,stdout,stderr = self.ssh.exec_command(command)
            
            while not stdout.channel.exit_status_ready():
                if stdout.channel.recv_ready():
                    rl,wl,xl = select.select([stdout.channel],[],[],0.0)
                    if len(rl) > 0:
                        returnValue = stdout.channel.recv(1024)
            self._close()
            self.logger.update('SSH_EXECUTE_SUCCESS',message='Command = %s'%command)
        except Exception as e:
            self.logger.update('SSH_EXECUTE_FAILED',message='Command = %s,%s'%(command,str(e)))
    	    print "There was an error exectuting the command on connections %s:"%self.name
    	    print "%s"%command
    	    print "stderr returned: %s"%str(stderr) 
    	    raise e

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

def main():
    import random
    import time

    connections = {}
    #sys.exit()
    ### Test on Blacklight
    logger = Log(logFileName_='./test.log')
    for i in range(0,1):
        tempId = random.randint(0,100000)
        #if i < 2:
        connections[tempId] = SSHConn(logger,machineName_='fe-sandbox.psc.edu',debug_=True)
        connections[tempId]._mkdir(simWS.configuration['simulators']['test']['runDirPrefix']+"."+str(tempId))
        
### Main Hook

if __name__=="__main__":
    main()
