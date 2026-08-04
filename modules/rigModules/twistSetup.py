import maya.cmds as cmds  # pyright: ignore[reportMissingImports]
import maya.api.OpenMaya as om  # pyright: ignore[reportMissingImports]
import autoRigger.utils.config as config


class TwistJointsGeneration:
    def __init__(self, axisInput, startJoint, endJoint, twistInput, rotOrder, name):
        """
        Creates an instance of the twist setup, can be used on any chain hopefully. 
        
        """
        self.axis = axisInput

        self.startJoint = startJoint
        self.endJoint = endJoint

        self.twistJointsList = []
        self.mdNodes = []

        self.twistInput = twistInput

        self.rotOrder = rotOrder

        self.jointName = None
        self.name = name

    

    def twistCreation(self):
        """
        creates Twist
        """
        self.jointName = self.startJoint.replace('_JNT', '')
        if "leg" in self.jointName: 
            limb = "leg"
        elif "arm" in self.jointName:
            limb = "arm"
        side = self.startJoint[0]
        self.jointName = f"{side}_{limb}_{self.name}"

        # vector lerp between start and end
        A = om.MVector(cmds.xform(self.startJoint, q=True, ws=True, t=True))
        B = om.MVector(cmds.xform(self.endJoint, q=True, ws=True, t=True))

        step = (B - A) / (self.twistInput + 1)

        # create twist joints evenly
        cmds.select(clear=True)

        for i in range(self.twistInput):
            cmds.select(clear=True)

            pos = A + step * (i + 1)
            jnt = cmds.joint(
                n=f"{self.jointName}_{i:02d}_TWIST_JNT",
                p= pos,
                rad=1)
            self.twistJointsList.append(jnt)

            if 'leg' in self.jointName:
                cmds.matchTransform(jnt, self.startJoint, rot=True, pos=False, scl=False)
                config.setRotationOrder([jnt], self.rotOrder)
                

            elif 'arm' in self.jointName:
                cmds.matchTransform(jnt, self.startJoint, rot=True, pos=False, scl=False)
                config.setRotationOrder([jnt], self.rotOrder)
            
            else:
                cmds.matchTransform(jnt, self.startJoint, rot=True, pos=False, scl=False)
                config.setRotationOrder([jnt], 0)
            
            cmds.makeIdentity(jnt, apply = True, r = True)
            

        cmds.select(clear=True)
        for jnt in self.twistJointsList:
            cmds.parent(jnt, self.startJoint)

        cmds.makeIdentity(self.twistJointsList[0], apply=True, t=False, r=True, s=False)

        # distribute twist percentages evenly
        percentStep = 1 / (len(self.twistJointsList) + 1)
        for i, twst in enumerate(self.twistJointsList):
            percent = percentStep * (i + 1)
            md = cmds.createNode('multiplyDivide', n=f"{twst}_MD")
            self.mdNodes.append(md)

            cmds.setAttr(f"{md}.input2{self.axis}", percent)
        return self.twistJointsList
    
    def matrixTwistSetup(self):
        locatorStart = cmds.spaceLocator(n = f"{self.jointName}_start_MTX{config.suffix['locator']}")[0]
        locatorEnd = cmds.spaceLocator(n = f"{self.jointName}_end_MTX{config.suffix['locator']}")[0]
        
        cmds.matchTransform(locatorEnd, self.endJoint, pos = True)
        cmds.matchTransform(locatorStart, self.startJoint, rot = True)
        cmds.matchTransform(locatorEnd, self.startJoint, rot = True)

        cmds.parentConstraint(self.startJoint, locatorStart)
        cmds.parentConstraint(self.endJoint, locatorEnd)
        
        multMtx = cmds.createNode('multMatrix', name = self.startJoint.replace("JNT", "MM"))
        decomposeMtx = cmds.createNode('decomposeMatrix', name = self.startJoint.replace("JNT", "DM"))
        quatEuler = cmds.createNode('quatToEuler', name = self.startJoint.replace("JNT", "QTE") )
        cmds.setAttr(f"{quatEuler}.inputRotateOrder", self.rotOrder)

        cmds.connectAttr(f"{locatorEnd}.worldMatrix[0]", f"{multMtx}.matrixIn[0]")
        cmds.connectAttr(f"{locatorStart}.worldInverseMatrix[0]", f"{multMtx}.matrixIn[1]")

        cmds.connectAttr(f"{multMtx}.matrixSum", f"{decomposeMtx}.inputMatrix")
        cmds.connectAttr(f"{decomposeMtx}.outputQuatX", f"{quatEuler}.inputQuatX")
        cmds.connectAttr(f"{decomposeMtx}.outputQuatW", f"{quatEuler}.inputQuatW")

        for jnt, md in zip(self.twistJointsList, self.mdNodes):
            cmds.connectAttr(f"{quatEuler}.outputRotateX", f"{md}.input1X")
            cmds.connectAttr(f"{md}.outputX", f"{jnt}.rotateX")

        group = cmds.group(locatorStart,locatorEnd, n = f"{self.jointName}{config.suffix['group']}")

        cmds.parent(group, config.RIG_HELPER_GRP)

    def creation(self):
        self.twistCreation()
        self.matrixTwistSetup()

        print(f"[Twist joints] : built {self.jointName}")

        return self.twistJointsList
            
