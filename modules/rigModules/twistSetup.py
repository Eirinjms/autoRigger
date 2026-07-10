import maya.cmds as cmds  # pyright: ignore[reportMissingImports]
import maya.api.OpenMaya as om  # pyright: ignore[reportMissingImports]
import autoRigger.utils.config as config


class TwistJointsGeneration:
    def __init__(self, axisInput, startJoint, endJoint, twistInput, armOrder, legOrder):
        """
        Creates an instance of the twist setup, can be used on any limb. 
        
        """
        self.axis = axisInput

        self.startJoint = startJoint
        self.endJoint = endJoint

        self.twistJointsList = []
        self.mdNodes = []

        self.twistInput = twistInput

        self.legOrder = legOrder
        self.armOrder = armOrder

    def twistCreation(self):
        """
        creates Twist
        """
        jointName = self.startJoint.replace('_JNT', '')

        # vector lerp between start and end
        A = om.MVector(cmds.xform(self.startJoint, q=True, ws=True, t=True))
        B = om.MVector(cmds.xform(self.endJoint, q=True, ws=True, t=True))

        step = (B - A) / (self.twistInput + 1)

        # create twist joints evenly spaced between start and end
        cmds.select(clear=True)

        for i in range(self.twistInput):
            cmds.select(clear=True)

            pos = A + step * (i + 1)
            jnt = cmds.joint(
                n=f"{jointName}_{i:02d}_TWIST_JNT",
                p= pos,
                rad=1)
            self.twistJointsList.append(jnt)

            if 'leg' in jointName:
                cmds.matchTransform(jnt, self.startJoint, rot=True, pos=False, scl=False)
                config.setRotationOrder([jnt], self.legOrder)
                print(self.legOrder)

            if 'arm' in jointName:
                cmds.matchTransform(jnt, self.startJoint, rot=True, pos=False, scl=False)
                config.setRotationOrder([jnt], self.armOrder)
                print(self.armOrder)


        # parent into a chain under startJoint
        cmds.select(clear=True)
        for i in range(len(self.twistJointsList) - 1, 0, -1):
            cmds.parent(self.twistJointsList[i], self.twistJointsList[i - 1])
        cmds.parent(self.twistJointsList[0], self.startJoint)

        cmds.makeIdentity(self.twistJointsList[0], apply=True, t=False, r=True, s=False)

        # distribute twist percentages evenly
        percentStep = 1 / (len(self.twistJointsList) + 1)
        for i, twst in enumerate(self.twistJointsList):
            percent = percentStep * (i + 1)
            md = cmds.createNode('multiplyDivide', n=f"{twst}_MD")
            self.mdNodes.append(md)

            cmds.setAttr(f"{md}.input2{self.axis}", percent)
        print(self.mdNodes)
        return self.twistJointsList
    
    def matrixTwistSetup(self):
        locatorStart = cmds.spaceLocator(n = self.startJoint.replace("JNT", "MTX_LOC"))[0]
        locatorEnd = cmds.spaceLocator(n = self.endJoint.replace("JNT", "MTX_LOC"))[0]
        

        cmds.matchTransform(locatorStart, self.startJoint, pos = True, rot = True)
        cmds.matchTransform(locatorEnd, self.endJoint, pos = True, rot = True)

        cmds.parentConstraint(self.startJoint, locatorStart)
        cmds.parentConstraint(self.endJoint, locatorEnd)
        
        multMtx = cmds.createNode('multMatrix', name = self.startJoint.replace("JNT", "MM"))
        decomposeMtx = cmds.createNode('decomposeMatrix', name = self.startJoint.replace("JNT", "DM"))
        quatEuler = cmds.createNode('quatToEuler', name = self.startJoint.replace("JNT", "QTE") )

        cmds.connectAttr(f"{locatorEnd}.worldMatrix[0]", f"{multMtx}.matrixIn[0]")
        cmds.connectAttr(f"{locatorStart}.worldInverseMatrix[0]", f"{multMtx}.matrixIn[1]")

        cmds.connectAttr(f"{multMtx}.matrixSum", f"{decomposeMtx}.inputMatrix")
        cmds.connectAttr(f"{decomposeMtx}.outputQuatX", f"{quatEuler}.inputQuatX")
        cmds.connectAttr(f"{decomposeMtx}.outputQuatW", f"{quatEuler}.inputQuatW")

        for jnt, md in zip(self.twistJointsList, self.mdNodes):
            cmds.connectAttr(f"{quatEuler}.outputRotateX", f"{md}.input1X")
            cmds.connectAttr(f"{md}.outputX", f"{jnt}.rotateX")

    def creation(self):
        self.twistCreation()
        self.matrixTwistSetup()

        return self.twistJointsList
            
