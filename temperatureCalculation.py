

class TemperatureCalculation:

    """10340 Motor Parameters """

    SurfaceArea = .104758 #.02841*2.5 #0.005615 # Cooling surface m^2 .044884
    StatorResistance = 9.4585

    WeightActiveParts = 6 #kg  #No need for tuning
    SpecificHeat = 750
    SpecificHeatDisipation =540.00 #W/m^2/degree diff # 600
    TorqueConstant = 1.867 #Nm/A

    """13684 Motor Parameters"""
    #SurfaceArea = .02841 #0.005615 # Cooling surface m^2 .044884
    #StatorResistance = 3.71
    #TorqueRequiredForMotor = .257
    #WeightActiveParts = 1.42 #kg  #No need for tuning
    #SpecificHeat = 500
    ##SpecificHeatDisipation =540.00 #W/m^2/degree diff # 600
    #TorqueConstant = .71 #Nm/A

    currRise = 0

    ambientTemperature = 27
    currentTemperature = ambientTemperature


    currDeltaTemp = 0

    prevWattLoss = 0

    currWattLoss = 0

    isMotorOn = False
    isStillChanging = False # Check to see 

    timeConstant = 0
    maximumTemp = 0


    def __init__(self):
        
        pass



    def UpdateParameters(self, loss_watts, deltaTime ):


        if True:

            deltaTime = deltaTime  / 30
            self.currWattLoss = loss_watts * 1000
            self.timeConstant = self.WeightActiveParts * self.SpecificHeat / self.SurfaceArea * self.SpecificHeatDisipation  / 3600
            self.maximumTemp = loss_watts * 1000 / self.SurfaceArea / self.SpecificHeatDisipation

            deltaTempRise = ((self.currWattLoss - (self.SurfaceArea * self.SpecificHeatDisipation * (self.currDeltaTemp))) *  deltaTime) / (self.WeightActiveParts * self.SpecificHeat)

            if abs(deltaTempRise) < 1e-6:
                deltaTempRise = 0
                self.currDeltaTemp = 0 

            self.currDeltaTemp += deltaTempRise

            self.currentTemperature = self.ambientTemperature + self.currDeltaTemp
            #print(deltaTime, " ", deltaTempRise, " ", self.currentTemperature, " ", self.currWattLoss)


    def ifStateChanged(self):


        pass