wsdl2py --complexType --lazy -f simulatorservice201.wsdl
wsdl2dispatch -f simulatorservice201.wsdl
ln -sf SimulatorService.py SimulatorService-2.0.1.py
