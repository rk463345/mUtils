class MediaObject:
    def __init__(self, location, name):
        self.location = location
        self.name = name
        self.finalLocation = None
        self.finalname = None

    def getFinalLocation(self):
        return self.finalLocation

    def getName(self):
        return self.name

    def getFinalName(self):
        return self.finalname

    def getLocation(self):
        return self.location

    def setFinalLocation(self, newLocation):
        self.finalLocation = newLocation

    def setFinalName(self, newName):
        self.finalname = newName
