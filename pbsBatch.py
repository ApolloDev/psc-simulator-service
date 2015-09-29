import paths
from apollo import ApolloDB

class PBSBatch:
    def __init__(self,batchId_,nodes_=None,ppn_=None,procsPerRun_=None,threadsPerRun_=None,
                 apollodb_=None,localCnf_=None,machineCnf_=None,simulatorCnf_=None):
        self.batchId = batchId_
        
        ### check to make sure we have required parameters
        if nodes_ is None: raise RuntimeError("PBSBatch creation: nodes_ needs to be defined")
        if ppn_ is None: raise RuntimeError("PBSBatch creation: ppn_ needs to be defined")
        if procsPerRun_ is None: raise RuntimeError("PBSBatch creation: procsPerRun_ needs to be defined")
        if threadsPerRun_ is None: raise RuntimeError("PBSBatch creation: threadsPerRun_ needs to be defined")
        if apollodb_ is None: raise RuntimeError("PBSBatch creation: apollodb_ needs to be defined")
        if localCnf_ is None: raise RuntimeError("PBSBatch creation: localCnf_ needs to be defined")
        if machineCnf_ is None: raise RuntimeError("PBSBatch creation: machineCnf_ needs to be defined")
        if simulatorCnf_ is None: raise RuntimeError("PBSBatch creation: simulatorCnf_ needs to be defined")
        
        self._apolloDB = apollodb_
        self._dirName = "apollo_run_{0}".format(batchId_)
        
        self._jobs = {}
        self._localConf = localCnf_
        self._machineConf = machineCnf_
        self._simConf = simulatorCnf_
        
        self._nodes = nodes_
        self._ppn = ppn_
        self._procsPerRun = procsPerRun_
        self._threadsPerRun = threadsPerRun_
        self._runScriptString = None
    
    def add_job(self,jobId):
        self._jobs[jobId] = {}
    
    def add_file_to_job(self,jobId_,fileName_,fileString_):
        if jobId_ not in self._jobs.keys():
            self._jobs[jobId_] = {}
        
        self._jobs[jobId_][fileName_] = fileString_
    
    def populate_from_apollo_runId(self):
        if self._apolloDB is None:
            raise RuntimeError("PBSBatch class:: population_from_apollo_runId: cannot use this member if apolloDB is not set in constructor")
        
        self._apolloDB.connect()
        runsToPopulateWith = self._apolloDB.getRunsFromRunId(self.batchId)
        print "RunToPopulate = {0}".format(runsToPopulateWith)
        if len(runsToPopulateWith) == 0:
            raise RuntimeError("PBSBatch class:: population_from_apollo_runId: no runs in the database with simulation_group_id:{0}".format(self.batchId))
        
        for runId in runsToPopulateWith:
            (name,dev,ver) = self._apolloDB.getSoftwareIdentificationForRunId(runId)
            idPrefix = "{0}_{1}_{2}".format(dev,name,ver)
            
            #jsonStr = self._apolloDB.getRunDataContentFromRunIdAndLabel(runId,"run_simulation_message.json",0,1,"TEXT","")
            translatorServiceId = self._apolloDB.getTranslatorServiceKey()
            simulatorServiceId = self._apolloDB.getSimulatorServiceKey(dev,name,ver)
            simulatorInputFileDict = self._apolloDB.getSimulationInputFilesForRunId(runId,translatorServiceId,simulatorServiceId)
            if isinstance(simulatorInputFileDict,dict):
                #if "config.txt" not in simulatorInputFileDict.keys():
#         			raise
                for filename,content in simulatorInputFileDict.items():
                    if filename != "verbose.html":
                        self.add_file_to_job(runId,filename,content)
            
                self.add_file_to_job(runId,'apollo_run.csh',self._createIndividualRunScript(runId))
    
           
    def create_zipFile(self,zipFileName_):
        import zipfile
        from StringIO import StringIO
        
        if zipFileName_[-4:] != ".zip":
            zipFileName_ += ".zip"
        
        zipFile = zipfile.ZipFile(zipFileName_,"w")
        for job in self._jobs.keys():
            jobDirName = "run_{0}".format(job)
            for fileName,fileString in self._jobs[job].items():
                zipFile.writestr("{0}/{1}".format(jobDirName,fileName),fileString,zipfile.ZIP_DEFLATED)
        ### put the python dependences in this 
        for depFile in self._simConf['dependencies']:
            with open("{0}/{1}".format(self._localConf['apolloPyDir'],depFile),"rb") as f:
                zipFile.writestr('{0}'.format(depFile),f.read(),zipfile.ZIP_DEFLATED)
        
        #zipFile.writestr("{0}/{1}".format(self._dirName,'batch_run.py'),self._createRunScript(),zipfile.ZIP_DEFLATED)
        zipFile.close()
        
    def createRunScript(self,outfileName_):
        pbsList = []
        with open('{0}/pbsBatch.py.template'.format(self._localConf['templateDir']),'rb') as f:
            for line in f.readlines(): 
                pbsList.append(line.replace('<<env>>',str(self._machineConf['env']))\
                                  .replace('<<bID>>',str(self.batchId))\
                                  .replace('<<nodes>>',str(self._nodes))\
                                  .replace('<<ppn>>',str(self._ppn))\
                                  .replace('<<walltime>>','30:00:00')\
                                  .replace('<<threadsPerRun>>',str(self._threadsPerRun))\
                                  .replace('<<procsPerRun>>',str(self._procsPerRun))\
                                  .replace('<<dbname>>',self._localConf['apolloDBName'])\
                                  .replace('<<dbhost>>',self._localConf['apolloDBHost'])\
                                  .replace('<<dbuser>>',self._localConf['apolloDBUser'])\
                                  .replace('<<dbpass>>',self._localConf['apolloDBPword'])\
                                  .replace('<<runCommand>>',self._simConf['runCommand'])
                                  .replace('<<apBatchUpdate>>',self._machineConf['apolloPyLoc']+"/apollo_batch_update_status.py")
                                  .replace('<<use_parallel>>',str(self._machineConf['useParallel']))\
                                  .replace('<<special>>',str(self._machineConf['special']))\
                                  .replace('<<submitCommand>>',str(self._machineConf['submitCommand'])))
        with open(outfileName_,"wb") as f:
            f.write("{0}".format(''.join(pbsList)))
           
    def _createIndividualRunScript(self,id):
        import random
        dbString = "-H {0} -D {1} -U {2} -P {3} ".format(self._localConf['apolloDBHost'],
                                                         self._localConf['apolloDBName'],
                                                         self._localConf['apolloDBUser'],
                                                         self._localConf['apolloDBPword'])
        tempId = random.randint(0, 100000)

        scriptList = []
        scriptList.append("#!/bin/csh\n")  
        scriptList.append('%s\n\n' % self._machineConf['special'])
        if self._machineConf['useModules']:
            moduleCMD = self._simConf['moduleCommand'][self._simConf['stagedMachines'].index(self._machineConf['hostname'])]
            print self._simConf['stagedMachines']
            scriptList.append('{0}\n'.format(moduleCMD))
        scriptList.append('setenv APOLLO_HOME {0} \n'.format(self._machineConf['apolloPyLoc']))
        scriptList.append('%s %s -t ../ -s running -m "simulation started" >& out.db\n' % (self._simConf['statusCommand'].replace("<<ID>>", str(id)).replace("<<bID>>",str(self.batchId)), dbString))
        scriptList.append('if ($status) then\n')
        scriptList.append('   echo "There 1 was a problem updating the status of job %s to the database" > out.err\n' % (str(id)))
        scriptList.append('   touch .failed\n')
        scriptList.append('   exit 1\n')
        scriptList.append('endif\n')
        scriptList.append('%s\n' % self._simConf['preProcessCommand'])
        scriptList.append('({0} {1} config.txt {2} {3} {4} {5} > run.exe.stdout) >& run.exe.stderr\n'.format(self._simConf['runCommand'],
                                                                                                             self._simConf['moduleName'][self._simConf['stagedMachines'].index(self._machineConf['hostname'])],
                                                                                                             self._threadsPerRun,
                                                                                                             self._simConf['mediumReals'],
                                                                                                             self._procsPerRun,
                                                                                                             id))
        scriptList.append('set errCont = `stat -c %s run.exe.stderr`\n')
        scriptList.append('if ($status || $errCont != "0") then\n')
        scriptList.append('   %s %s -t../ -s failed -m "The simulation failed during running"  >& out.db\n' % (self._simConf['statusCommand'].replace("<<ID>>", str(id)).replace("<<bID>>",str(self.batchId)), dbString))
        scriptList.append('   if ($status) then\n')
        scriptList.append('       echo "There 3 was a problem updating the status of job %s to the database" > out.err\n' % (str(id)))
        scriptList.append('       touch .failed\n')
        scriptList.append('      exit 1\n')
        scriptList.append('   endif\n')
        scriptList.append('else\n')           
        scriptList.append("   %s %s -t ../ -s running -m 'populating Apollo Database' >& out.db\n" % (self._simConf['statusCommand'].replace("<<ID>>", str(id)).replace("<<bID>>",str(self.batchId)), dbString))
        scriptList.append('   if ($status) then\n')
        scriptList.append('       echo "There 5 was a problem updating the status of job %s to the database" > out.err\n' % (str(id)))
        scriptList.append('       touch .failed\n')
        scriptList.append('      exit 1\n')
        scriptList.append('   endif\n')
        scriptList.append('endif\n')
        scriptList.append('(%s %s> run.db.stdout) > & run.db.stderr\n' % (self._simConf['dbCommand'].replace("<<tID>>", "%s_%s" % (str(tempId), str(id))).replace('<<ID>>', str(id)).replace("<<bID>>",str(self.batchId)), dbString))
        scriptList.append('set errCont = `stat -c %s run.db.stderr`\n')
        scriptList.append('if ($status || $errCont != "0") then\n')
        scriptList.append('   %s %s -t ../ -s failed -m "Database upload failed" >& out.db\n' % (self._simConf['statusCommand'].replace("<<ID>>", str(id)).replace("<<bID>>",str(self.batchId)), dbString))
        scriptList.append('   if ($status) then\n')
        scriptList.append('       echo "There 7 was a problem updating the status of job %s to the database" > out.err\n' % (str(id)))
        scriptList.append('       touch .failed\n')
        scriptList.append('      exit 1\n')
        scriptList.append('   endif\n')
        scriptList.append('   touch .failed\n')
        scriptList.append('   exit 1\n')
        scriptList.append('else\n')           
        scriptList.append("   %s %s -t ../ -s completed -m 'simulation completed' >& out.db\n" % (self._simConf['statusCommand'].replace("<<ID>>", str(id)).replace("<<bID>>",str(self.batchId)), dbString))
        scriptList.append('   if ($status) then\n')
        scriptList.append('       echo "There 1 was a problem updating the status of job %s to the database"\n > out.err' % (str(id)))
        scriptList.append('       touch .failed\n')
        scriptList.append('      exit 1\n')
        scriptList.append('   endif\n')
        scriptList.append('endif\n')
        scriptList.append('touch .completed')  
        
        return "".join(scriptList)
    
def main():
    import simWS
    
    print "Running Unit Test for PBSBatch Class"
    apolloDB =ApolloDB(dbname_=simWS.configuration['local']['apolloDBName'],
                                host_=simWS.configuration['local']['apolloDBHost'],
                                user_=simWS.configuration['local']['apolloDBUser'],
                                password_=simWS.configuration['local']['apolloDBPword'])
    
    pbsBatchJob = PBSBatch(209598,apollodb_=apolloDB,
                           nodes_=1,
                           ppn_=8,
                           procsPerRun_=4,
                           threadsPerRun_=1,
                           localCnf_=simWS.configuration['local'],
                           machineCnf_=simWS.configuration['machines']['pscss.olympus.psc.edu'],
                           simulatorCnf_=simWS.configuration['simulators']['fred_V1_i'])
    
    pbsBatchJob.populate_from_apollo_runId()
    pbsBatchJob.createRunScript("tmp/batch_run.py")
    pbsBatchJob.create_zipFile("tmp/text.zip")
    
    apolloDB.connect()
    apolloDB.close()
    
### Main Hook

if __name__=="__main__":
    main()
