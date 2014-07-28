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

@author: John Levander and Shawn Brown
'''

from SimulatorService_v2_0_2_types import *
import inspect


class ApolloFactory:
    def new_RunSimulationMessage(self):
        mess = ns1.RunSimulationMessage_Def(None).pyclass()
        mess._authentication = ns1.Authentication_Def(None).pyclass()
        mess._simulatorIdentification = ns1.SoftwareIdentification_Def(None).pyclass()
        mess._simulatorTimeSpecification = ns1.SimulatorTimeSpecification_Def(None).pyclass()
        mess._infectiousDiseaseScenario = ns1.InfectiousDiseaseScenario_Def(None).pyclass()
        return mess

    def new_InfectiousDiseaseScenario(self):
        ifdscen = ns1.InfectiousDiseaseScenario_Def(None).pyclass()
        ifdscen._location = ns1.Location_Def(None).pyclass()
        ifdscen._infections = []
        #ns1.Infection_Def(None).pyclass()
        ifdscen._diseases = []
        #ns1.InfectiousDisease_Def(None).pyclass()
        #ifdscen._contaminations = []
        #ns1.Contamination_Def(None).pyclass()
        #ifdscen._infectious
        return ifdscen
    
    #def new_Location(self):
    #    loc = ns1.Location_Def(None).pyclass()
    
    def new_Infection(self):
        inf = ns1.Infection_Def(None).pyclass()
        inf._infectionAquisitions = [ns1.InfectionAcquisition_Def(None).pyclass()]
        
        return inf
    
    def new_SimulatorConfiguration(self):
        cfg = ns1.SimulatorConfiguration_Def(None).pyclass()
        cfg._authentication = ns1.Authentication_Def(None).pyclass()
        cfg._simulatorIdentification = ns1.SoftwareIdentification_Def(None).pyclass()
        cfg._populationInitialization = ns1.SimulatedPopulation_Def(None).pyclass()
        cfg._simulatorTimeSpecification= ns1.SimulatorTimeSpecification_Def(None).pyclass()
        cfg._disease = ns1.Disease_Def(None).pyclass()
        cfg._controlMeasures = ns1.ControlMeasures_Def(None).pyclass()
        return cfg
    
    def new_Vaccination(self):
        vacc = ns1.Vaccination_Def(None).pyclass()
        vacc._vaccinationEfficacy = ns1.TreatmentEfficacyOverTime_Def(None).pyclass()
        return vacc
    
    
    def new_VaccinationControlMeasure(self):
        vcm = ns1.VaccinationControlMeasure_Def(None).pyclass()
        for name,obj in inspect.getmembers(vcm):
            if name[0:11] == "set_element":
                #print name
                obj(None)
        return vcm
    
    def new_AntiviralControlMeasure(self):
        avcm = ns1.AntiviralTreatmentControlMeasure_Def(None).pyclass()
        for name,obj in inspect.getmembers(avcm):
            if name[0:11] == "set_element":
                #print name
                obj(None)
        return avcm
    
    
    def new_Vaccine(self):
        return ns1.Vaccine_Def(None).pyclass()    
    
    def new_Antiviral(self):
        return ns1.Antiviral_Def(None).pyclass()
    
    def new_AntiviralTreatment(self):
        avt = ns1.AntiviralTreatment_Def(None).pyclass()
        avt._antiviralTreatmentEfficacy = ns1.TreatmentEfficacyOverTime_Def(None).pyclass()
        return avt
                
    def new_FixedStartTimeControlMeasure(self):
        cm = ns1.FixedStartTimeControlMeasure_Def(None).pyclass()
        cm._controlMeasureFixedStartTime = ns1.FixedStartTime_Def(None).pyclass()
        return cm;
    
    def new_TreatmentEfficacyOverTime(self):
        eff = ns1.TreatmentEfficacyOverTime_Def(None).pyclass()
        return eff
        
    def new_TargetPriorityPopulation(self):
        tpp = ns1.TargetPriorityPopulation_Def(None).pyclass()        
        return tpp

    def new_ReactiveControlMeasure(self):
        rcm = ns1.ReactiveControlMeasure_Def(None).pyclass()
        #rcm._controlMeasureReactiveTriggersDefinition = self.new_ReactiveTriggersDefinition()
        for name,obj in inspect.getmembers(rcm):
            if name[0:11] == "set_element":
                print name
                obj(None)
        return rcm
    
    def new_ReactiveTriggersDefinition(self):
        rtd = ns1.ReactiveTriggersDefinition_Def(None).pyclass()
        for name,obj in inspect.getmembers(rtd):
            if name[0:11] == "set_element":
                obj(None)
        return rtd
    
    def new_SchoolClosureControlMeasure(self):
        sc = ns1.SchoolClosureControlMeasure_Def(None).pyclass()
        for name,obj in inspect.getmembers(sc):
            if name[0:11] == "set_element":
                #print name
                obj(None)
        return sc
    
    def new_PopulationStrataDefinition(self):
        psd = ns1.PopulationStrataDefinition_Def(None).pyclass()
               
        for name,obj in inspect.getmembers(psd):
            if name[0:11] == "set_element":
                #print name
                obj(None)
        return psd

    def new_MethodCallStatus(self):
        run_status = ns1.MethodCallStatus_Def(None).pyclass()
        run_status._status = ns1.MethodCallStatusEnum_Def(None).pyclass()
	run_status._status = "unknown"
        return run_status
    
    def new_SupportedPopulationLocation(self):
        spl = ns1.SupportedPopulationLocation_Def(None).pyclass()
        return spl

    
    def new_PopulationDiseaseState(self):
        return ns1.PopulationDiseaseState_Def(None).pyclass()
        
        
        
