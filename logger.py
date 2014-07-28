import time
import os,sys

ServiceCodes = {
    'UNKNOWN':100,
    'STARTED':101,
    'CALLRECV':102,
    'RUNNING':103,
    'CONF_MACHINE_FIND_FAILED':104,
    'SSH_CONN_ESTABLISHED':105,
    'SSH_CONN_FAILED':106,
    'SFTP_CONN_ESTABLISHED':107,
    'SFTP_CONN_FAILED':108,
    'SSH_SCRATCH_DIR_SUCCESS':109,
    'SSH_SCRATCH_DIR_FAILED':110,
    'SSH_CONN_CLOSED':111,
    'SSH_CONN_CLOSE_FAILED':112,
    'SFTP_CONN_CLOSED':113,
    'SFTP_CONN_CLOSE_FAILED':114,
    'SSH_GETSCRATCH_SUCCESS':115,
    'SSH_GETSCRATCH_FAILED':116,
    'SSH_EXECUTE_SUCCESS':117,
    'SSH_EXECUTE_FAILED':118,
    'SSH_EXECUTE_BEFORE_ESTB':119,
    'SSH_MKDIR_BEFORE_ESTB':120,
    'SSH_MKDIR_SUCCESS':121,
    'SSH_MKDIR_FAILED':122,
    'SSH_SENDSTRTOFILE_BEFORE_ESTB':123,
    'SSH_SENDSTRTOFILE_SUCCESS':124,
    'SSH_SENDSTRTOFILE_FAILED':125,
    'SSH_SENDFILE_BEFORE_ESTB':126,
    'SSH_SENDFILE_SUCCESS':127,
    'SSH_SENDFILE_FAILED':128,
    'SSH_SUBMIT_JOB_SUCCESS':129,
    'SSH_SUBMIT_JOB_FAILED':130,
    'SSH_PBS_ID_SUCCESS':131,
    'SSH_PBS_ID_FAILED':132,
    'SSH_PBS_SUBMIT_FAILED':133,
    'SSH_PBS_SUBMIT_SUCCESS':134,
    'SSH_PBS_QSTAT_SUCCESS':135,
    'SSH_PBS_QSTAT_FAILED':136,
    'SUBMIT_SIM_CONF_FOUND':137,
    'SUBMIT_SIM_CONF_FAILED':138,
    'SSH_PBS_CREATE_SCRIPT_SUCCESS':139,
    'SSH_PBS_CREATE_FAILED':140,
    'SSH_CREATEPBSRUN_SUCCESS':141,
    'SSH_CREATEPBSRUN_FAILED':142,
    'SSH_CREATEDIRRUN_SUCCESS':143,
    'SSH_CREATEDIRRUN_FAILED':144,
    'SSH_CONN_TIMEOUT':145,
    'SSH_DIRECT_JOB_SUCCESS':146,
    'SSH_DIRECT_JOB_FAILED':147,
    'SVC_APL_RESQ_RECV':148,
    'SVC_APL_RESQ_RECV_FAILED':149,
    'SVC_APL_TRANS_RECV':150,
    'SVC_APL_TRANS_FAILED':151,
    'SRV_SSH_CONN_SUCCESS':152,
    'SVC_SSH_CONN_FAILED':153,
    'SVC_TMPDIR_SUCCESS':154,
    'SVC_TMPDIR_FAILED':155,
    'SVC_FILELIST_RECIEVED':156,
    'SVC_FILELIST_FAILED':157,
    'SVC_FILE_SEND_SUCCESS':167,
    'SVC_FILE_SEND_FAILED':168,
    'SVC_SUBMIT_JOB_SUCCESS':169,
    'SVC_SUBMIT_JOB_FAILED':170,
    'DB_SUCCESS':158,
    'DB_NOID_FOUND':159,
    'DB_CONNECT_SUCCESS':160,
    'DB_CONNECT_FAILED':161,
    'DUPLICATE_ID':162,
    'DB_POP_FAILED':163,
    'DB_POP_ZERO':164,
    'DB_QUERY_FAILED':165,
    'DB_QUERY_NO_RESULTS':166,
    'DB_QUERY_MORE_THAN_ONE':167,
    'DB_STATUS_ERROR':168
    }

ServiceDescriptions = {
    ServiceCodes['UNKNOWN']:'Unknown Status',
    ServiceCodes['STARTED']:'Started Logging',
    ServiceCodes['CALLRECV']:'Incoming Call recieved',
    ServiceCodes['RUNNING']:'The service is Running',
    ServiceCodes['CONF_MACHINE_FIND_FAILED']:'Getting Machine Configuration Failed',
    ServiceCodes['SSH_CONN_ESTABLISHED']:'Established SSH Connection',
    ServiceCodes['SSH_CONN_FAILED']:'SSH Connection Failed',
    ServiceCodes['SFTP_CONN_ESTABLISHED']:'Established SFTP Connection',
    ServiceCodes['SFTP_CONN_FAILED']:'SFTP Connection Failed',
    ServiceCodes['SSH_SCRATCH_DIR_SUCCESS']:'Getting Remote SCRATCH Directory through SSH Success',
    ServiceCodes['SSH_SCRATCH_DIR_FAILED']:'Getting Remote SCRATCH Directory through SSH Failed',
    ServiceCodes['SSH_CONN_CLOSED']:'SSH Connection Closed',
    ServiceCodes['SSH_CONN_CLOSE_FAILED']:'SSH Connection Close Failed',
    ServiceCodes['SFTP_CONN_CLOSED']:'SFTP Connection Closed',
    ServiceCodes['SSH_GETSCRATCH_SUCCESS']:'SSH getScratch Success',
    ServiceCodes['SSH_GETSCRATCH_FAILED']:'SSH getScratch Failed',
    ServiceCodes['SSH_EXECUTE_SUCCESS']:'SSH Execute Success',
    ServiceCodes['SSH_EXECUTE_FAILED']:'SSH Execute Failed', 
    ServiceCodes['SFTP_CONN_CLOSE_FAILED']:'SFTP Connection Close Failed',
    ServiceCodes['SSH_EXECUTE_BEFORE_ESTB']:'Trying to Execute over SSH before Connection Established',
    ServiceCodes['SSH_MKDIR_BEFORE_ESTB']:'Trying to mkdir over SSH before Connection Established',
    ServiceCodes['SSH_MKDIR_SUCCESS']:'SSH mkdir Success',
    ServiceCodes['SSH_MKDIR_FAILED']:'SSH mkdir Failed',
    ServiceCodes['SSH_SENDSTRTOFILE_BEFORE_ESTB']:'Sending String over SSH before Connection Established',
    ServiceCodes['SSH_SENDSTRTOFILE_SUCCESS']:'Sending String over SSH Success',
    ServiceCodes['SSH_SENDSTRTOFILE_FAILED']:'Sending String over SSH Failed',
    ServiceCodes['SSH_SENDFILE_BEFORE_ESTB']:'Sending File over SSH before Connection Established',
    ServiceCodes['SSH_SENDFILE_SUCCESS']:'Sending File Over SSH Success',
    ServiceCodes['SSH_SENDFILE_FAILED']:'Sending File Over SSH Failed',
    ServiceCodes['SSH_SUBMIT_JOB_SUCCESS']:'Submit Job Success',
    ServiceCodes['SSH_SUBMIT_JOB_FAILED']:'Submit Job Failed',
    ServiceCodes['SSH_PBS_ID_SUCCESS']:'PBS Submit ID Success',
    ServiceCodes['SSH_PBS_ID_FAILED']:'PBS Submit ID Failed',
    ServiceCodes['SSH_PBS_SUBMIT_FAILED']:'PBS Submit Failed',
    ServiceCodes['SSH_PBS_SUBMIT_SUCCESS']:'PBS Submit Success',
    ServiceCodes['SSH_PBS_QSTAT_SUCCESS']:'PBS Qstat Success',
    ServiceCodes['SSH_PBS_QSTAT_FAILED']:'PBS Qstat Failed',
    ServiceCodes['SUBMIT_SIM_CONF_FOUND']:'Simulation Configuration Found',
    ServiceCodes['SUBMIT_SIM_CONF_FAILED']:'Simulation Configuration Not Found',
    ServiceCodes['SSH_PBS_CREATE_SCRIPT_SUCCESS']:'Creating a PBS Script has been Successful',
    ServiceCodes['SSH_PBS_CREATE_FAILED']:'Creating a PBS Script has Failed',
    ServiceCodes['SSH_CREATEPBSRUN_SUCCESS']:'Successfully Created the PBS Run string',
    ServiceCodes['SSH_CREATEPBSRUN_FAILED']:'Failed to Create the PBS Run String',
    ServiceCodes['SSH_CREATEDIRRUN_SUCCESS']:'Successfully Created the Direct Run string',
    ServiceCodes['SSH_CREATEDIRRUN_FAILED']:'Failed to Create the Direct Run String',
    ServiceCodes['SSH_CONN_TIMEOUT']:'SSH Connection timedout trying to get established',    
    ServiceCodes['SSH_DIRECT_JOB_SUCCESS']:'Setting up Direct Job Successful',
    ServiceCodes['SSH_DIRECT_JOB_FAILED']:'Setting up Direct Job Failed',
    ServiceCodes["SVC_APL_RESQ_RECV"]:'Apollo response created and received',
    ServiceCodes["SVC_APL_RESQ_RECV_FAILED"]:'Apollo repsonse creation Failed',
    ServiceCodes["SVC_APL_TRANS_RECV"]:'Apollo Translation service message recieved',
    ServiceCodes["SVC_APL_TRANS_FAILED"]:'Failed to recieve and parse Apollo translation message',
    ServiceCodes["SRV_SSH_CONN_SUCCESS"]:'Service was successful in creating a SSH connection',
    ServiceCodes["SVC_SSH_CONN_FAILED"]:'Service failed at creating a SSH connection',
    ServiceCodes["SVC_TMPDIR_SUCCESS"]:'Service succeeded in creating a local temporary directory',
    ServiceCodes["SVC_TMPDIR_FAILED"]:'Service failed to create a local temprorary directory',
    ServiceCodes["SVC_FILELIST_RECIEVED"]:'Service successfully recieved a file list from translation service',
    ServiceCodes["SVC_FILELIST_FAILED"]:'Service failed at getting a file list from translation service',
    ServiceCodes["SVC_FILE_SEND_SUCCESS"]:'Service successfully sent the input files to remote machine',
    ServiceCodes["SVC_FILE_SEND_FAILED"]:'Service failed sending input files to remote machine',
    ServiceCodes["SVC_SUBMIT_JOB_SUCCESS"]:'Service successfully submitted job to remote machine',
    ServiceCodes["SVC_SUBMIT_JOB_FAILED"]:'Service failed submtting job to remote machine',
    ServiceCodes['DB_SUCCESS']:'Successfully obtained data from the ApolloDB',
    ServiceCodes['DB_NOID_FOUND']:'No ID found in ApolloDB',
    ServiceCodes['DB_CONNECT_SUCCESS']:'Successfully connected to the ApolloDB',
    ServiceCodes['DB_CONNECT_FAILED']:'Failed to connect to the ApolloDB',
    ServiceCodes['DUPLICATE_ID']:'Tried this request again while it is still running',
    ServiceCodes['DB_POP_FAILED']:'Failed getting the population from the ApolloDB',
    ServiceCodes['DB_POP_ZERO']:'ApolloDB query returned zero population',
    ServiceCodes['DB_QUERY_FAILED']:'ApolloDB query failed',
    ServiceCodes['DB_QUERY_NO_RESULTS']:'ApolloDB query produced no results',
    ServiceCodes['DB_QUERY_MORE_THAN_ONE']:'ApolloDB query produced more than one result, when it should be unique',
    ServiceCodes['DB_STATUS_ERROR']:'ApolloDB: Status not in the allowed status'
    }

ServiceTypes = {
    ServiceCodes['UNKNOWN']:'unknown',
    ServiceCodes['STARTED']:'running',
    ServiceCodes['CALLRECV']:'running',
    ServiceCodes['RUNNING']:'running',
    ServiceCodes['CONF_MACHINE_FIND_FAILED']:'failed',
    ServiceCodes['SSH_CONN_ESTABLISHED']:'running',
    ServiceCodes['SSH_CONN_FAILED']:'failed',
    ServiceCodes['SFTP_CONN_ESTABLISHED']:'running',
    ServiceCodes['SFTP_CONN_FAILED']:'failed',
    ServiceCodes['SSH_SCRATCH_DIR_SUCCESS']:'running',
    ServiceCodes['SSH_SCRATCH_DIR_FAILED']:'failed',
    ServiceCodes['SSH_CONN_CLOSED']:'running',
    ServiceCodes['SSH_CONN_CLOSE_FAILED']:'failed',
    ServiceCodes['SFTP_CONN_CLOSED']:'running',
    ServiceCodes['SFTP_CONN_CLOSE_FAILED']:'failed',
    ServiceCodes['SSH_GETSCRATCH_SUCCESS']:'running',
    ServiceCodes['SSH_GETSCRATCH_FAILED']:'failed',
    ServiceCodes['SSH_EXECUTE_SUCCESS']:'running',
    ServiceCodes['SSH_EXECUTE_FAILED']:'failed',
    ServiceCodes['SSH_EXECUTE_BEFORE_ESTB']:'failed',
    ServiceCodes['SSH_MKDIR_BEFORE_ESTB']:'failed',
    ServiceCodes['SSH_MKDIR_SUCCESS']:'running',
    ServiceCodes['SSH_MKDIR_FAILED']:'failed',
    ServiceCodes['SSH_SENDSTRTOFILE_BEFORE_ESTB']:'failed',
    ServiceCodes['SSH_SENDSTRTOFILE_SUCCESS']:'running',
    ServiceCodes['SSH_SENDSTRTOFILE_FAILED']:'running',
    ServiceCodes['SSH_SENDFILE_BEFORE_ESTB']:'failed',
    ServiceCodes['SSH_SENDFILE_SUCCESS']:'running',
    ServiceCodes['SSH_SENDFILE_FAILED']:'failed',
    ServiceCodes['SSH_SUBMIT_JOB_SUCCESS']:'running',
    ServiceCodes['SSH_SUBMIT_JOB_FAILED']:'failed',
    ServiceCodes['SSH_PBS_ID_SUCCESS']:'running',
    ServiceCodes['SSH_PBS_ID_FAILED']:'failed',
    ServiceCodes['SSH_PBS_SUBMIT_FAILED']:'failed',
    ServiceCodes['SSH_PBS_SUBMIT_SUCCESS']:'running',
    ServiceCodes['SSH_PBS_QSTAT_SUCCESS']:'running',
    ServiceCodes[ 'SSH_PBS_QSTAT_FAILED']:'failed',
    ServiceCodes['SUBMIT_SIM_CONF_FOUND']:'running',
    ServiceCodes['SUBMIT_SIM_CONF_FAILED']:'failed',
    ServiceCodes['SSH_PBS_CREATE_SCRIPT_SUCCESS']:'running',
    ServiceCodes['SSH_PBS_CREATE_FAILED']:'failed',
    ServiceCodes['SSH_CREATEPBSRUN_SUCCESS']:'running',
    ServiceCodes['SSH_CREATEPBSRUN_FAILED']:'failed',
    ServiceCodes['SSH_CREATEDIRRUN_SUCCESS']:'running',
    ServiceCodes['SSH_CREATEDIRRUN_FAILED']:'failed',
    ServiceCodes['SSH_CONN_TIMEOUT']:'failed',
    ServiceCodes['SSH_DIRECT_JOB_SUCCESS']:'running',
    ServiceCodes['SSH_DIRECT_JOB_FAILED']:'failed',
    ServiceCodes["SVC_APL_RESQ_RECV"]:'running',
    ServiceCodes["SVC_APL_RESQ_RECV_FAILED"]:'failed',
    ServiceCodes["SVC_APL_TRANS_RECV"]:'running',
    ServiceCodes["SVC_APL_TRANS_FAILED"]:'failed',
    ServiceCodes["SRV_SSH_CONN_SUCCESS"]:'running',
    ServiceCodes["SVC_SSH_CONN_FAILED"]:'failed',
    ServiceCodes["SVC_TMPDIR_SUCCESS"]:'running',
    ServiceCodes["SVC_TMPDIR_FAILED"]:'failed',
    ServiceCodes["SVC_FILELIST_RECIEVED"]:'running',
    ServiceCodes["SVC_FILELIST_FAILED"]:'failed',
    ServiceCodes["SVC_FILE_SEND_SUCCESS"]:'staging',
    ServiceCodes["SVC_FILE_SEND_FAILED"]:'failed',
    ServiceCodes["SVC_SUBMIT_JOB_SUCCESS"]:'queued',
    ServiceCodes["SVC_SUBMIT_JOB_FAILED"]:'failed',
    ServiceCodes['DB_SUCCESS']:'running',
    ServiceCodes['DB_NOID_FOUND']:'failed',
    ServiceCodes['DB_CONNECT_SUCCESS']:'running',
    ServiceCodes['DB_CONNECT_FAILED']:'failed',
    ServiceCodes['DUPLICATE_ID']:'running',
    ServiceCodes['DB_POP_FAILED']:'failed',
    ServiceCodes['DB_POP_ZERO']:'failed',
    ServiceCodes['DB_QUERY_FAILED']:'failed',
    ServiceCodes['DB_QUERY_NO_RESULTS']:'failed',
    ServiceCodes['DB_QUERY_MORE_THAN_ONE']:'failed',
    ServiceCodes['DB_STATUS_ERROR']:'failed'
    }

class Log:
    def __init__(self, logFileName_=None,logLevel_ = "Normal", buffered_=False,append_=False):

        self.logFile = None
        try:
            if append_:
                self.logFile = open(logFileName_,"ab")
            else:
                self.logFile = open(logFileName_,"wb")
        except IOError:
            ### This error will prevent the server from starting, as it should
            raise RuntimeError("Cannot open the specified log file %s"%self.logFile)
        
        self.logLevel = logLevel_
        self.buffered = buffered_
        self.moniker = "Service-Wide"
        self.lastMessage = None

    def start(self):
        startTime = time.strftime("%Y-%m-%d %H:%M:%S")
        self.update('STARTED')
    
    def __del__(self):
        self.logFile.close()

    def setMoniker(self,moniker):
        self.moniker = moniker
        
    def update(self,status = "NOTHING",  message = None):
        thisServiceCode = ServiceCodes['UNKNOWN']
        
        if ServiceCodes.has_key(status):
            thisServiceCode = ServiceCodes[status]
            
        if thisServiceCode == ServiceCodes['UNKNOWN']:
            print "UNKNOWN for %s"%status
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        thisMessage = ""
        
        if message is None:
            thisMessage = "%s %s Code: %d(%s), %s\n"%(timestamp,self.moniker,
                                                      thisServiceCode,
                                                      ServiceTypes[thisServiceCode],
                                                      ServiceDescriptions[thisServiceCode])
        else:
            thisMessage = "%s %s Code: %d(%s), %s message: %s\n"%(timestamp,self.moniker,
                                                                  thisServiceCode,
                                                                  ServiceTypes[thisServiceCode],
                                                                  ServiceDescriptions[thisServiceCode],
                                                                  message)
        self.logFile.write("%s"%thisMessage)
        self.lastMessage = (status,thisMessage)
        
        if not self.buffered: self.logFile.flush()

    def updateAndExit(self,status = "NOTHING"):
        self.update(status)
        sys.exit()

    def pollStatus(self):
        return self.lastMessage

    def pollStatusCode(self):
        return ServiceCodes[self.lastMessage[0]]

    def pollStatusType(self):
        return ServiceTypes[self.pollStatusCode()]
    
class ThreadLog(Log):
    def __init__(self,logFileName_=None,logLevel_="Normal",id_=None,buffered_=False):
        Log.__init__(self,logFileName_,logLevel_,buffered_,append_=True)
        self.moniker = str(id_)
