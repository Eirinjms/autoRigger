import maya.cmds as cmds # pyright: ignore[reportMissingImports] 
import maya.api.OpenMaya as om # pyright: ignore[reportMissingImports] 
import autoRigger.utils.shapes as shapes
from autoRigger.modules.rigModules import handModule, reverseFoot, twistSetup as twist, squashAndStretch as stretch
import autoRigger.utils.config as config
import importlib

importlib.reload(config)
importlib.reload(handModule)
importlib.reload(reverseFoot)

class limbBuild:
    def __init__(self, side, 
                 limbType, 
                 legOrder, 
                 armOrder, 
                 handOrder, 
                 armStretch, 
                 legStretch, 
                 twistArm, 
                 twistLeg, 
                 twistJoints):
        '''
        Builds an IK/FK limb rig including:
            - IK/FK blending
            - polevector
            - clavicle for arm
            - endlimb: hand or reverse feet. 

        parameters: 
            side (str):'L' or 'R'
            limbType (str): 'leg' or 'arm'
        '''

        side = side.upper()
        limbType = limbType.lower()

        if side not in ['L', 'R']: 
            cmds.error('Please Choose either L or R')
        if limbType not in ['arm', 'leg']:
            cmds.error('Please Choose either arm or leg')

        self.stretchyArms = armStretch
        self.stretchyLegs = legStretch

        self.twistArm = twistArm
        self.twistLeg = twistLeg
        self.twistAmount = twistJoints

        self.twistJoints = []

        self.size = config.bipedal
        self.suffix = config.suffix

        if limbType == "arm":
            self.pvDistance = self.size['pvArmDistance']
            self.rotOrder = armOrder
            self.handOrder = handOrder
        else:
            self.pvDistance = self.size['pvLegDistance'] 
            self.rotOrder = legOrder       

        self.fkIK = config.fkik
        self.attrs = config.attrs
        self.prefix = config.prefix

        self.side = f"{side}_"

        self.limbType = limbType

        #makes a list of the joints depending on limb, will integrate "categories" later
        if self.limbType == 'arm':
            index = 'BCD'
        else: 
            index = 'ABC'

        self.jointBaseName = [f"{self.limbType}J{i}" for i in index]
        self.joints = []
        for joints in self.jointBaseName: 
            joint = f"{self.side}{joints}{config.suffix['joint']}"
            self.joints.append(joint)
        

    def dupeJoints(self):
        '''
        Duplicating the bind joint chain to create the
        IK and FK chains

        '''
        config.setRotationOrder(self.joints, self.rotOrder)
        self.fkJoints = []
        self.ikJoints = []

        count = 0

        for i in self.fkIK.values():
            for joint in self.jointBaseName:
                dup = cmds.duplicate(f"{self.side}{joint}{self.suffix['joint']}", 
                                     po = True, 
                                     n = f"{self.side}{joint}{i}{self.suffix['joint']}")[0]
                
                if count == len(self.jointBaseName):
                    count = 0 

                if dup.endswith(f"{self.fkIK['fk']}{self.suffix['joint']}"):
                    self.fkJoints.append(dup)
                    if count > 0:
                        cmds.parent(self.fkJoints[count], self.fkJoints[count-1])

                else:
                    self.ikJoints.append(dup)
                    if count > 0:
                        cmds.parent(self.ikJoints[count], self.ikJoints[count-1])

                count = count + 1   

    def fkSetup(self):
        '''
        The FK setup for selected limb, creates a parented chain
        '''

        self.fkLocs = []
        self.fkCtrls = []

        for fkCount, joint in enumerate(self.fkJoints): 
            fkLoc = cmds.spaceLocator(n = joint.replace(self.suffix['joint'], self.suffix['locator']))[0]
            self.fkLocs.append(fkLoc)

            if 'legJA' in joint:
                radius = self.size['FKlegs'] * 1.2 
                normal=(1, 0, 0)

            elif 'legJB' in joint:
                radius = self.size['FKlegs']
                normal=(1, 0, 0 )

            elif 'legJC' in joint:
                normal=(0, 1, 0 )
                radius = self.size['FKlegs'] * 0.8
            
            elif 'armJB' in joint: 
                normal = (1,0,0)
                radius = self.size['FKarms'] * 1.2
            
            else: 
                normal = (1,0,0)
                radius = self.size['FKarms']

            fkCtrl = cmds.circle(n = joint.replace(self.suffix['joint'], self.suffix['control']), 
                                 r = radius, 
                                 nr = normal)[0]

            config.setRotationOrder([fkLoc, fkCtrl], self.rotOrder)
            self.fkCtrls.append(fkCtrl)
            
            cmds.parent(fkCtrl, fkLoc)
 
            cmds.matchTransform(fkLoc, joint, pos = True, rot = True)

            cmds.orientConstraint(fkCtrl, joint, 
                                  n = joint.replace(self.suffix['joint'], self.suffix['orientCon']), 
                                  mo = False)
            
            if fkCount > 0:
                cmds.parent(self.fkLocs[fkCount], self.fkCtrls[fkCount-1])


    def ikSetup(self):
        '''
        The IK setup for selected limb, creates the solver + control
        '''

        self.ikHandle = cmds.ikHandle(n = self.ikJoints[0].replace(self.fkIK['ik'], self.suffix ['ikHandle']), 
                                 sj = self.ikJoints[0], 
                                 ee = self.ikJoints[-1])[0]
        
        self.ikLoc = cmds.spaceLocator(n = self.ikJoints[0].replace(self.suffix['joint'], self.suffix['locator']))[0]

        if self.limbType == "leg":
            size = self.size['IKlegs']
        if self.limbType == "arm":
            size = self.size['IKarms']


        self.ikCtrl = shapes.cubeCtrl(name = f"{self.side}{self.limbType}{self.fkIK['ik']}'{self.suffix['control']}", 
                                 X = size, 
                                 Y = size, 
                                 Z = size)

        shape = cmds.listRelatives(self.ikCtrl, type = 'nurbsCurve')

        config.setRotationOrder([self.ikLoc, self.ikCtrl], self.rotOrder)

        cmds.parent(self.ikCtrl, self.ikLoc)
        cmds.matchTransform(self.ikLoc, self.ikJoints[-1], pos = True, rot = True)

        cmds.pointConstraint(self.ikCtrl, self.ikHandle, 
                             n = self.ikJoints[0].replace(self.suffix['joint'], self.suffix['pointCon']), 
                             mo = False)
        cmds.orientConstraint(self.ikCtrl, self.ikJoints[-1], 
                              n = self.ikJoints[0].replace(self.suffix['joint'], self.suffix['orientCon']), 
                              mo = False)

    def ikFkSwitch(self):
        '''
        Creates the IKFK switch and connects it to the ankle/wrist
        '''
        
        if self.limbType == "leg":
            size = self.size['IKswitchLegs']
        if self.limbType == "arm":
            size = self.size['IKswitchArm']

        self.ikBNDLoc = cmds.spaceLocator(n = self.ikJoints[0].replace(self.suffix['joint'], '_BND' + self.suffix['locator'] )) [0]
        self.switch = shapes.gearCtrl(name = f"{self.side}{self.limbType}_FKIK_switch{self.suffix['control']}", 
                                 size = size, 
                                 side = self.side, 
                                 limb = self.limbType)
                                 
        cmds.matchTransform(self.ikBNDLoc, self.joints[-1])
        cmds.matchTransform(self.switch, self.joints[-1], pos = True)
        cmds.makeIdentity(self.switch, apply = True, t = True)

        if 'L_' in self.switch:
            Transform=(20, 0, 0)
            
        else: 
            Transform=(-20, 0, 0) 

        cmds.xform(self.switch, t = Transform, ro = (0, 0, 0))
        cmds.makeIdentity(self.switch, apply = True, t = True, r = True)

        cmds.pointConstraint(self.switch,self.switch, self.ikBNDLoc, n = self.switch + config.suffix['pointCon']) 

        cmds.parentConstraint(f"{self.side}{self.jointBaseName[2]}{self.suffix['joint']}", self.ikBNDLoc, 
                              n = f"{self.side}{self.jointBaseName[0]}_BND{self.suffix['parentCon']}", 
                              mo = True)

        cmds.addAttr(self.switch, 
                     ln = 'FKIK_Switch', 
                     at = 'float', 
                     min = 0, 
                     max = 1, 
                     dv = 1, 
                     k = True)


        for attr in self.attrs: 
            cmds.setAttr(f"{self.switch}.{attr}", 
                         l = True, 
                         k = False, 
                         cb = False)

    def ikfkBlends(self):
        '''
        Creates the IKFK blends, of selected variatiants
        e.g scale, rotate, translate
        '''

        value = ['rotate', 'scale']

        for v in value: 
            for joint, ikJoint, fkJoint in zip(self.jointBaseName, self.ikJoints, self.fkJoints): 
                blend = cmds.shadingNode('blendColors', 
                                            au = True, 
                                            n = f"{joint}_{v}{self.suffix['blendColor']}")

                cmds.connectAttr(f"{ikJoint}.{v}", f"{blend}.color1")
                cmds.connectAttr(f"{fkJoint}.{v}", f"{blend}.color2")
                cmds.connectAttr(f"{blend}.output",  f"{self.side}{joint}{self.suffix['joint']}.{v}")

                cmds.connectAttr(f"{self.switch}.FKIK_Switch", f"{blend}.blender")


    def ikfkGroups(self):
        '''
        Grouping the IK and FK into their own groups and setups up visibility
        '''

        #########################################################################
        self.fkGrp = cmds.group(n = f"{self.side}{self.limbType}{self.fkIK['fk']}{self.suffix['group']}", em = True)
        self.ikGrp = cmds.group(n = f"{self.side}{self.limbType}{self.fkIK['ik']}{self.suffix['group']}", em = True)

        cmds.parent(self.fkLocs[0], self.fkGrp)
        cmds.parent(self.ikHandle, self.ikLoc, self.ikGrp)

        #########################################################################

        cmds.connectAttr(f"{self.switch}.FKIK_Switch", f"{self.ikGrp}.visibility")

        fkikRev = cmds.shadingNode('reverse', 
                                   au = True, 
                                   n = f"{self.side}{self.jointBaseName[0]}{self.suffix['reverse']}")

        cmds.connectAttr(f"{self.switch}.FKIK_Switch", f"{fkikRev}.inputX")
        cmds.connectAttr(fkikRev + '.outputX', self.fkGrp + '.visibility')


    def findpoleVector(self):
        '''
        Calculates a pole vector position using the plane defined by
        the start, mid, and end joints. 
        '''
        self.H = om.MVector(cmds.xform(f"{self.side}{self.jointBaseName[0]}{self.suffix['joint']}", q = True, ws = True, t = True))
        self.K = om.MVector(cmds.xform(f"{self.side}{self.jointBaseName[1]}{self.suffix['joint']}", q = True, ws = True, t = True))
        self.A = om.MVector(cmds.xform(f"{self.side}{self.jointBaseName[2]}{self.suffix['joint']}", q = True, ws = True, t = True))

        HK = self.K - self.H
        HA = self.A - self.H

        dot = HK * HA

        proj = (dot/(HA.length()**2)) * HA

        projK = HK - proj

        self.pv = (projK * self.pvDistance) + self.K

    def createPoleVector(self):
        '''
        Creates the poleVector control and parents it  
        '''

        self.pvLoc = cmds.spaceLocator(p = self.pv, n = f"{self.side}{self.limbType}_PV_LOC")[0]
        cmds.xform(self.pvLoc, cp = True)

        if self.limbType == "arm": 
            size = self.size['PVarms']
        else:
            size = self.size['PVlegs']

        self.pvCtrl = shapes.pyramidCtrl(name = f"{self.side}{self.limbType}_PV{self.suffix['control']}", size = size)
        cmds.parent(self.pvCtrl, self.pvLoc)

        cmds.matchTransform(self.pvCtrl, self.pvLoc, pos = True, rot = True)

        pvCon = cmds.poleVectorConstraint(self.pvCtrl, self.ikHandle, n = self.ikJoints[0].replace(self.suffix['joint'], self.suffix['poleVectorCon']))

        cmds.makeIdentity(self.pvCtrl, apply = True, t = True)

        cmds.parent(self.pvLoc, self.ikGrp)


    def poleVectorVisualization(self):
        '''
        Enables a visualization of the polevector, creating a polygon 
        '''

        self.findpoleVector()
        joint_positions = []
        for joint in [self.H, 
                      self.pv,
                      self.A]: 
            joint_positions.append(tuple(joint))

        self.pvVis = cmds.polyCreateFacet(p = joint_positions,
                                          n = f"{self.side}{self.limbType}_PV_VIS")[0]

    def clavicle(self):
        '''
        Calculates a pole vector position using the plane defined by
        the start, mid, and end joints. 
        '''            

        self.clavJnt = f"{self.side}armJA{self.suffix['joint']}"

        self.clavCtrl = cmds.circle(
            n = f"{self.side}armJA{self.suffix['control']}",
            r = self.size['clavs'],
            nr = (0,1,0))[0]

        self.clavLoc = cmds.spaceLocator(
            n=f"{self.side}armJA{self.suffix['locator']}")[0]

        cmds.parent(self.clavCtrl, self.clavLoc)

        cmds.matchTransform(self.clavLoc, self.clavJnt, pos = True, rot = True)

        cmds.orientConstraint(
            self.clavCtrl,
            self.clavJnt,
            mo=True,
            n=f"{self.side}armJA{self.suffix['orientCon']}")

        cmds.makeIdentity(self.clavCtrl, apply=True, t=True, r=True)

        shape = cmds.listRelatives(self.clavCtrl, shapes=True, type="nurbsCurve")[0]
        cvs = cmds.ls(shape + ".cv[*]", fl=True)

        if self.side == 'L_':
            cmds.xform(cvs, t=(10,6,0), ro=(0,0,-20), r=True)
        else:
            cmds.xform(cvs, t=(-10,-6,0), ro=(0,0,-20), r=True)

        for i in [1,5]:
            cv = cvs[i]
            if self.side == 'L_':
                cmds.xform(cv, t=(0,-5,0), os=True, r=True)
            else:
                cmds.xform(cv, t=(0,5,0), os=True, r=True)


        # parent into FK chain
        cmds.parent(self.fkGrp, self.clavCtrl)

    def cleanup(self):
        '''
        Minor cleanup:
            - hides fk/ik joints + ik handle
            - creates a group for the ik switch to parent the bindlocator
        
        '''
        IkswitchCtrl = cmds.group(em = True, w = True,n = f"{self.side}{self.limbType}_IK_switch{self.suffix['group']}") 

        cmds.parent(self.ikBNDLoc, IkswitchCtrl)

        cmds.hide(self.fkJoints, self.ikJoints, self.ikHandle)

        
    def endlimb(self):  
        '''
        Creates the endlimb depending on limbType:
            'leg' creates reverseFoot
            'arm' creates hand

        '''
        if self.limbType == 'leg':
            reverseFoot.build(self.side, self.ikHandle, self.ikCtrl, self.switch, self.joints)
        if self.limbType == 'arm':
            handModule.build(self.side, self.handOrder)

    def hipSpace(self):
        spineJnt = "C_spineJA_JNT"


        hiploc_name = f"hipSpace{self.suffix['locator']}"
        if cmds.objExists(hiploc_name) == True:
            self.hipLoc = hiploc_name
        else: 
            self.hipLoc = cmds.spaceLocator(n = hiploc_name)[0]

        
        spinePos = cmds.xform(spineJnt, q = True, t = True, ws = True)

        cmds.xform(self.hipLoc, t = spinePos)

    def legSpaceSwitch(self):
        '''
        Creates the spaceswitches for legs
        
        Parameters: 
            spineJnt: passed on from the spine module
        returns: alot of things im gnna guess. 
        '''
        if self.limbType == 'leg':

            cmds.addAttr(self.switch, ln = 'SPACES', at = "enum", en = "____________", k = True)
            #cmds.matchTransform(hipLoc, spineJnt, pos = True, rot = True)
            
            poConPV = cmds.parentConstraint(self.hipLoc, self.ikLoc, mo = True, n = f"{self.side}legPV_SpaceSwitch{self.suffix['parentCon']}")[0]
            
            cmds.addAttr(self.switch, ln = "Foot_Follow", at = "enum", en = "World : Hip", k = True)

            driverPV = f"{self.switch}.Foot_Follow"

            drivenPV = f"{poConPV}.{self.hipLoc}W0"

            cmds.setDrivenKeyframe(drivenPV, at = 'switchAttr', cd = driverPV, dv = 0, v = 0)
            cmds.setDrivenKeyframe(drivenPV, at = 'switchAttr', cd = driverPV, dv = 1, v = 1)

    def armSpaceSwitch(self):
        '''
        Creates the spaceswitches for arms
        
        Parameters: 
            spineJnt: passed on from the spine module
        returns: alot of things im gnna guess. 
        '''

        #Make the locators
        worldLoc = cmds.spaceLocator(n =f"{self.side}arm_worldSpace{self.suffix['locator']}" )[0]
        clavSpaceLoc = cmds.spaceLocator(n = f"{self.side}arm_clavSpace{self.suffix['locator']}")[0]
        localSpaceLoc = cmds.spaceLocator(n = f"{self.side}arm_localSpace{self.suffix['locator']}")[0]

        cmds.parent(self.ikLoc, localSpaceLoc)
        cmds.parent(localSpaceLoc, self.ikGrp)

        cmds.matchTransform(clavSpaceLoc, self.clavJnt, pos = True, rot = True)
        cmds.matchTransform(worldLoc, f"{self.side}{self.jointBaseName[2]}{self.suffix['joint']}", pos = True, rot = True)

        #cmds.parent(hipLoc, spineLoc)
        cmds.parent(clavSpaceLoc, self.clavCtrl)

        paCon = cmds.parentConstraint(worldLoc, clavSpaceLoc, self.hipLoc, self.ikLoc, mo = True, n = f"{self.side}spaceSwitch{self.suffix['parentCon']}")[0]

        cmds.parent(worldLoc, self.ikGrp)

        #make the switch

        cmds.addAttr(self.switch, ln = 'SPACES', at = "enum", en = "____________", k = True)
    
        cmds.addAttr(self.switch, ln = "Hand_Follow", at = "enum", en = " World : Clavicle : Hip ", k = True)

        space_names = ["worldSpace", "clavSpace", "hipSpace"]
        spaces = []
        for space in space_names:
            if space == space_names[2]:
                name = f"{paCon}.{space}"
            else:
                name = f"{paCon}.{self.side}arm_{space}"
            spaces.append(name)

        driver = f"{self.switch}.Hand_Follow"

        for i, name in enumerate(spaces):
            driven = f"{name}_LOCW{i}"
            
            for dv in range(len(spaces)):
                v = 1 if dv == i else 0
                cmds.setDrivenKeyframe(driven, cd=driver, dv=dv, v=v)

    def poleVectorSpaceSwitch(self):
        '''
        Creates the spaceswitches for the polevector for specified limb
        
        Parameters: 
            spineJnt: passed on from the spine module
        returns: alot of things im gnna guess. 
        '''
        pvSpaceLoc = cmds.spaceLocator(n = f"{self.side}{self.limbType}_pv_Space{self.suffix['locator']}")[0]
        
        cmds.delete(cmds.parentConstraint(self.pvLoc, pvSpaceLoc, mo = 0))
        
        cmds.parent(pvSpaceLoc, self.ikCtrl)

        poConPV = cmds.parentConstraint(pvSpaceLoc, self.pvLoc, mo = False, n = f"{self.side}pv_SpaceSwitch{self.suffix['parentCon']}")[0]
        
        cmds.addAttr(self.switch, ln = f"{self.side}{self.limbType}Pole_Vector_Follow", at = "enum", en = "World : Leg", k = True)

        driverPV = f"{self.switch}.{self.side}{self.limbType}Pole_Vector_Follow"

        drivenPV = f"{poConPV}.{self.side}{self.limbType}_pv_Space_LOCW0"

        cmds.setDrivenKeyframe(drivenPV, at = 'switchAttr', cd = driverPV, dv = 0, v = 0)
        cmds.setDrivenKeyframe(drivenPV, at = 'switchAttr', cd = driverPV, dv = 1, v = 1)
    
    def twistSetup(self):
        startJoints = [self.joints[0], self.joints[1]]
        endJoints = [self.joints[1], self.joints[2]]

        axis = "X"

        for sj, ej in zip(startJoints, endJoints):
            twistSetup = twist.TwistJointsGeneration(axis, sj, ej, self.twistAmount, self.rotOrder)
            twistJoints = twistSetup.creation()
            self.twistJoints.extend(twistJoints)

    def squashNstretch(self):

        stretchLimb = stretch.squashNStretch(self.joints, 
                                             self.side, 
                                             self.limbType, 
                                             self.ikGrp, 
                                             self.ikCtrl, 
                                             self.switch, 
                                             self.twistJoints)
        stretchLimb.create()

    def buildLimb(self):
        self.dupeJoints()
        self.fkSetup()
        self.ikSetup()
        self.ikFkSwitch()
        self.ikfkBlends()
        self.ikfkGroups()
        self.findpoleVector()
        self.createPoleVector()
        self.hipSpace()
        
        self.endlimb()
        if self.limbType == 'arm':
            self.clavicle()
            self.armSpaceSwitch()

        else: 
            self.legSpaceSwitch()

        self.poleVectorSpaceSwitch()

        if self.limbType == 'leg':
            if self.twistLeg:
                self.twistSetup()
            if self.stretchyLegs: 
                self.squashNstretch()  

        if self.limbType == 'arm':
            if self.twistArm:
                self.twistSetup()
            if self.stretchyArms:
                self.squashNstretch()
            
        self.cleanup()
        shapes.ctrlColour()
        print("Building:", self.side, self.limbType)

def build_limb_set(legOrder, armOrder, handOrder, stretchyArms, stretchyLegs, twistAmount, twistArms, twistLegs, sides: list, limbs: list):   
    """
    Builds the requested limb types for the specified sides.

    Parameters:
        sides (list[str]): Side identifiers to build, typically ["L", "R"].
        limbs (list[str]): Limb types to build, typically ["arm", "leg"].
        legOrder (int) : the rotation order of the legs. 
        armOrder (int) : the rotation order of the arms. 
        handOrder (int) : the rotation order of the fingers. 
        stretchylegs (bool):
    """
    print(twistAmount, "ui")
    for side in sides:
        for limb in limbs:
            limbBuild(side, limb, legOrder, armOrder, handOrder, stretchyArms, stretchyLegs, twistArms, twistLegs, twistAmount).buildLimb()
    
    print("All Limbs built")

        
