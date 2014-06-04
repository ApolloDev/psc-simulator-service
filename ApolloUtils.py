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
Created on Nov 29, 2012

@author: John Levander
'''

from SimulatorService_v2_0_1_services_types import *
import logging

class ApolloUtils:
    logger = logging.getLogger("apollo-type-logger")
    hdlr = logging.FileHandler('apollo-type-logger.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)
    
    
    def log_simulatorConfiguration(self, obj):
        self.logger.debug("-----epidemic_model_input-----")
        self.log_authentication(obj)
        self.log_simulatorTimeSpecification(obj)
        self.log_simulatorIdentification(obj)
        self.log_disease(obj)
        #self.log_antiviralControlMeasure(obj)
        #self.log_vaccinationControlMeasure(obj)
        self.log_simulatedPopulation(obj)
        self.logger.debug("-----end epidemic_model_input-----")
        return
    
    def log_authentication(self, obj):
        self.logger.debug("-----authentication")
        self.logger.debug("requesterId: %s", obj._authentication._requesterId)
        self.logger.debug("requesterPassword: %s", obj._authentication._requesterPassword)
        return
    
    def log_simulatorIdentification(self, obj):
        self.logger.debug("-----simulatorIdentification")
        self.logger.debug("softwareDeveloper: %s", obj._simulatorIdentification._softwareDeveloper)
        self.logger.debug("softwareName: %s", obj._simulatorIdentification._softwareName)
        self.logger.debug("softwareVersion: %s", obj._simulatorIdentification._softwareVersion)
	self.logger.debug("softwareType: %s",obj._simulatorIdentification._softwareType)
        return
    
    def log_simulatorTimeSpecification(self, obj):
        self.logger.debug("-----simulatorConfiguration")
        self.logger.debug("timeStepUnit: %s", obj._simulatorTimeSpecification._timeStepUnit)
        self.logger.debug("timeStepValue: %s", obj._simulatorTimeSpecification._timeStepValue)
        self.logger.debug("runLength: %s", obj._simulatorTimeSpecification._runLength)
        return
    
    def log_disease(self,obj):
        self.logger.debug("-----disease")
        self.logger.debug("diseaseName: %s", obj._disease._diseaseName)
        self.logger.debug("infectiousPeriod: %s", obj._disease._infectiousPeriod)
        self.logger.debug("latentPeriod: %s", obj._disease._latentPeriod)
        self.logger.debug("reproductionNumber: %s", obj._disease._reproductionNumber)
        self.logger.debug("asymptomaticInfectionFraction: %s", obj._disease._asymptomaticInfectionFraction)
        return
    
##    def log_antiviralControlMeasure(self, obj):
##        self.logger.debug("-----antiviralControlMeasure")
##        self.logger.debug("antiviralCmCompliance: %s", obj._antiviralControlMeasure._antiviralCmCompliance)
##        self.logger.debug("antiviralEfficacy: %s", obj._antiviralControlMeasure._antiviralEfficacy)
##        self.logger.debug("antiviralEfficacyDelay: %s", obj._antiviralControlMeasure._antiviralEfficacyDelay) 
##        self.logger.debug("antiviralSupplySchedule: %s", obj._antiviralControlMeasure._antiviralSupplySchedule)
##        self.logger.debug("antiviralAdminSchedule: %s", obj._antiviralControlMeasure._antiviralAdminSchedule)
##        return
        
##    def log_vaccinationControlMeasure(self, obj):
##        self.logger.debug("-----vaccinationControlMeasure")
##        self.logger.debug("vaccineCmCompliance: %s", obj._vaccinationControlMeasure._vaccineCmCompliance)
##        self.logger.debug("vaccineEfficacy: %s", obj._vaccinationControlMeasure._vaccineEfficacy)
##        self.logger.debug("vaccineEfficacy_delay: %s", obj._vaccinationControlMeasure._vaccineEfficacyDelay) 
##        self.logger.debug("vaccineSupplySchedule: %s", obj._vaccinationControlMeasure._vaccineSupplySchedule)
##        self.logger.debug("vaccinationAdminSchedule: %s", obj._vaccinationControlMeasure._vaccinationAdminSchedule)
##        return
   
    def log_simulatedPopulation(self, obj):
        self.logger.debug("-----populationInitialization")
        self.logger.debug("populationLocation: %s", obj._populationInitialization._populationLocation)
        self.logger.debug("gender: %s", obj._populationInitialization._gender)
        self.logger.debug("ageRange: %s", obj._populationInitialization._ageRange)
        dbg = ""
        for d in obj._populationInitialization._populationDiseaseState:
            dbg += "\tdiseaseState: " + d._diseaseState
            dbg += "\n\tfractionOfPopulation:" + str(d._fractionOfPopulation) + "\n"
        self.logger.debug("populationDiseaseState:\n %s", dbg)
        return

    def getPopFractionGivenLocationAndDiseaseState(self, obj, location, diseaseState):
        ds = obj._populationInitialization._populationDiseaseState
        for d in ds:
            if d._diseaseState.lower() == diseaseState:
                return d._fractionOfPopulation
	return 0;
    def getPopCountGivenLocationAndDiseaseState(self, obj, location, diseaseState):
        ds = obj._populationInitialization._populationDiseaseState
        for d in ds:
            if d._diseaseState.lower() == diseaseState:
                return d._popCount
        return 0;
    
    def getTotalPopCount(self, obj):
        total = 0
        ds = obj._populationInitialization._populationDiseaseState
        for d in ds:
            total += d._popCount
        return total
