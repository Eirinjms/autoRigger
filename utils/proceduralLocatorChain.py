import maya.cmds as cmds
import maya.api.OpenMaya as om

import autoRigger.utils.config as config
import string

class procLocatorGenerator:
    def __init__(self, slider, naming, prefix):

        self.basename = naming 
        self.jointAmount = slider
        self.prefix = prefix
        self.suffix = config.suffix

        self.newlocators = []
        self.Locs = []
        self.positions = []

        
    def generateLocs(self):
        if not "_" in self.prefix: 
            self.prefix += "_"

        self.startGuide = cmds.spaceLocator(n = f"{self.prefix}{self.basename}JA_GUIDE")
        self.endGuide = cmds.spaceLocator(n = f"{self.prefix}{self.basename}JEnd_GUIDE")
        

        startShape = cmds.listRelatives(self.startGuide, shapes=True)[0]
        endShape = cmds.listRelatives(self.endGuide, shapes=True)[0]


        cmds.xform(self.endGuide, t  = (10,0,0), ws = True)

        colours = [14, 13]
        shapes = [startShape, endShape]

        for c, s in zip(colours, shapes):
            cmds.setAttr(f"{s}.overrideEnabled", 1)
            cmds.setAttr(f"{s}.overrideColor", c)


    def placementMath(self):
        
        if self.newlocators:
            self.deleteGuides(self.newlocators)
            
        self.newlocators.clear()
        self.Locs.clear()
        self.positions.clear()

        self.Locs.append(self.startGuide)
        self.rootLocalPos, self.rootWorldPos = config.getGuidePos(self.startGuide)
        self.endLocalPos, self.endWorldPos = config.getGuidePos(self.endGuide)

        self.rootFinalPos = tuple(a + b for a, b in zip(self.rootLocalPos, self.rootWorldPos)) #adds the local and world position together
        self.endFinalPos = tuple(a + b for a, b in zip(self.endLocalPos, self.endWorldPos))

        self.startVector = om.MVector(self.rootFinalPos)
        self.endVector = om.MVector(self.endFinalPos)

        distanceVector = self.endVector - self.startVector
        distanceBetweenJoints = distanceVector.length() / (self.jointAmount + 1)
        self.direction = distanceVector.normal()

        for i in range(1, self.jointAmount + 1):
            pos = self.startVector + self.direction * distanceBetweenJoints * i
            self.positions.append(pos)

        for index, (pos, letter) in enumerate(zip(self.positions, string.ascii_uppercase[1:])):
            spinename = f"{self.prefix}{self.basename}J{letter}_GUIDE"
            loc = cmds.spaceLocator(n=spinename)[0]
            cmds.xform(loc, t=pos, ws=True)
            self.newlocators.append(spinename)
            self.Locs.append(spinename)

            if index > 0:
                cmds.parent(loc, self.newlocators[index - 1])
        self.Locs.append(self.endGuide)

        cmds.parent(self.newlocators[0], self.startGuide)
        cmds.parent(self.endGuide, self.newlocators[-1])


    def deleteGuides(self, joints: list):

        cmds.parent(self.endGuide, w=True)

        cmds.delete(joints)

    def updateJointAmount(self, value):
        self.jointAmount = value



