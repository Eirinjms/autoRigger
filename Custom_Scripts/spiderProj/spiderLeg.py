import maya.cmds as cmds
import maya.cmds as cmds # pyright: ignore[reportMissingImports] 
import maya.api.OpenMaya as om # pyright: ignore[reportMissingImports] 
import maya.mel as mel
import autoRigger.utils.shapes as shapes
from autoRigger.utils import config, rigUtils
import importlib

importlib.reload(config)

class spiderLegs: 
    def __init__(self, side, legIndex): 

        side = side.upper()
        self.limbType = "leg"
        self.legIndex = legIndex

        if side not in ['L', 'R']: 
            cmds.error('Please Choose either L or R')

        self.size = config.bipedal
        self.suffix = config.suffix

        self.fkIK = config.fkik
        self.attrs = config.attrs
        self.prefix = config.prefix

        self.side = f"{side}_"

        self.pvDistance = self.size['pvLegDistance']
        index = 'BCDE' 

        #makes a list of the joints depending on limb, will integrate "categories" later
        self.jointBaseName = [f"{self.limbType}{self.legIndex}_J{i}" for i in index]
        self.joints = []
        for joints in self.jointBaseName: 
            joint = f"{self.side}{joints}{config.suffix['joint']}"
            self.joints.append(joint)
        endjoint = f"{self.side}{self.limbType}{self.legIndex}_JEnd{config.suffix['joint']}"
        self.joints.append(endjoint)

    def dupeJoints(self):
        '''
        Duplicating the bind joint chain to create the
        IK and FK chains

        '''

        print(self.joints)
        self.fkJoints = []
        self.ikJoints = []

        count = 0

        for i in self.fkIK.values():
            for joint in self.joints:
                dup = cmds.duplicate(joint, 
                                     po = True, 
                                     n = f"{joint}{i}")[0]
                
                if count == len(self.joints):
                    count = 0 

                if dup.endswith(f"{self.fkIK['fk']}"):
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
        rigUtils.fkCreator

    def driverIK(self):
        self.driverJoints = []
        self.driverpositions = [cmds.xform(self.joints[0], q=True, ws=True, t=True), 
                     cmds.xform(self.joints[1], q=True, ws=True, t=True), 
                     cmds.xform(self.joints[-1], q=True, ws=True, t=True)]

        names = ["start",
                 "mid",
                 "end"]
        
        cmds.select(clear=True)

        for pos, name in zip(self.driverpositions, names):
            joint = cmds.joint(p = pos)
            joint = cmds.rename(joint, f"{self.side}{self.limbType}{self.legIndex}driver_IK_{name}")
            self.driverJoints.append(joint)

    def ikSetup(self):
        '''
        The IK setup for selected limb, creates the solver + control
        '''
        self.ikHandle = cmds.ikHandle(n = self.ikJoints[0].replace(self.fkIK['ik'], self.suffix ['ikHandle']), 
                                 sj = self.ikJoints[0], 
                                 ee = self.ikJoints[-2],
                                 sol = "ikRPsolver")[0]
        
        self.driverIKHandle = cmds.ikHandle(n = f"{self.driverJoints[0]}{config.suffix['ikHandle']}", 
                                 sj = self.driverJoints[0], 
                                 ee = self.driverJoints[-1],
                                 sol = "ikRPsolver")[0]

        self.ikLoc = cmds.spaceLocator(n = "Foot_IK_LOC")[0]
        self.ikCtrl = shapes.cubeCtrl(name = self.ikLoc.replace(config.suffix['locator'],
                                                      config.suffix['control']), 
                                                      X = 4, Y =2, Z = 4)
        cmds.parent(self.ikCtrl, self.ikLoc)
        cmds.matchTransform(self.ikLoc, self.joints[-1])
        

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

        cmds.xform(self.switch, t = Transform, ro = (90, 0, 0))
        cmds.makeIdentity(self.switch, apply = True, t = True, r = True, s = True)

        cmds.pointConstraint(self.ikBNDLoc, self.switch, n = self.switch + config.suffix['pointCon'], mo = True) 

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
        self.H = om.MVector(cmds.xform(self.ikJoints[0], q=True, ws=True, t=True))
        self.K = om.MVector(cmds.xform(self.ikJoints[1], q=True, ws=True, t=True))
        self.A = om.MVector(cmds.xform(self.ikJoints[-2], q=True, ws=True, t=True))

        HK = self.K - self.H
        HA = self.A - self.H
        KA = self.K - self.A

        dot = HK * HA

        proj = (dot/(HA.length()**2)) * HA

        projK = HK - proj

        limbLength = HK.length() + KA.length()
        pvDistance = limbLength * self.pvDistance

        self.pv = (projK.normal() * pvDistance) + self.K

    def createPoleVector(self):
        '''
        Creates the poleVector control and parents it  
        '''

        self.pvLoc = cmds.spaceLocator( n = f"{self.side}{self.limbType}_PV_LOC")[0]

        cmds.xform(self.pvLoc, t = self.pv)
        cmds.matchTransform(self.pvLoc, self.coxaJnt, rot = True)

        if self.limbType == "arm": 
            size = self.size['PVarms']
        else:
            size = self.size['PVlegs']

        self.pvCtrl = shapes.pyramidCtrl(name = f"{self.side}{self.limbType}_PV{self.suffix['control']}", size = size)
        cmds.parent(self.pvCtrl, self.pvLoc)

        #cmds.matchTransform(self.pvCtrl, self.pvLoc, pos = True, rot = True)

        pvCon = cmds.poleVectorConstraint(self.pvCtrl, self.ikHandle, n = self.ikJoints[0].replace(self.suffix['joint'], self.suffix['poleVectorCon']))

        cmds.makeIdentity(self.pvCtrl, apply = True, t = True)

        cmds.parent(self.pvLoc, self.ikGrp)

    def poleVectorLine(self):
        points = [cmds.xform(self.joints[0], q = True, t = True, ws = True), 
                  cmds.xform(self.joints[-1], q = True, t = True, ws = True), 
                  cmds.xform(f"{self.pvCtrl}.cv[6]", q=True, t=True, ws =True)]

        pointsStraightLine = [cmds.xform(self.joints[1], q = True, t = True, ws = True), cmds.xform(f"{self.pvCtrl}.cv[6]", q=True, t=True, ws =True)]
        
        pvVizCurve = cmds.curve(n = f"{self.side}{self.limbType}_PV_VIZ", p = points,  d = 1)
        pvVizStraightCurve = cmds.curve(n = f"{self.side}{self.limbType}_PV_straight_VIZ", p = pointsStraightLine,  d = 1)
        curves = [pvVizCurve, pvVizStraightCurve]

        cmds.addAttr(self.switch, ln = "PV_VIZ_Line", at = "enum", en = "None : Line : Triangle", dv = 1, k = True)

        for index, curve in enumerate([pvVizStraightCurve, pvVizCurve]):
            if index == 0:
                name =f"{self.side}{self.limbType}_PV_straight_VIS_COND"
            else: 
                name = f"{self.side}{self.limbType}_PV_VIS_COND"
            condition = cmds.shadingNode(
                "condition",
                asUtility=True,
                n=name)

            cmds.setAttr(f"{condition}.operation", 0)
            cmds.setAttr(f"{condition}.secondTerm", index +1)

            cmds.setAttr(f"{condition}.colorIfTrueR", 1)
            cmds.setAttr(f"{condition}.colorIfFalseR", 0)

            cmds.connectAttr(
                f"{self.switch}.PV_VIZ_Line",
                f"{condition}.firstTerm")

            cmds.connectAttr(
                f"{condition}.outColorR",
                f"{curve}.visibility")

        parents= [self.joints[0], self.pvCtrl, self.joints[-1]]
        parentsSL = [self.joints[1], self.pvCtrl]

        self.pvVizGRP = cmds.group(em = True, n= "PV_VIZ_GRP")
        cmds.parent(pvVizCurve, self.pvVizGRP)
        cmds.parent(pvVizStraightCurve, self.pvVizGRP)
        for curve in (curves):
            cmds.setAttr(f"{curve}.template", 1)
            cmds.setAttr(f"{curve}.inheritsTransform", 0)

        for parent, curve in zip([parents, parentsSL], [pvVizCurve, pvVizStraightCurve]):
            for i, p in enumerate(parent):
                cluster = cmds.cluster(f"{curve}.cv[{i}]", n=f"{curve}_{i}{config.suffix['cluster']}")[1]
                cmds.parentConstraint(p, cluster, mo=False, n= f"{cluster}{config.suffix['parentCon']}")
                cmds.setAttr(f"{cluster}.visibility", 0)
                cmds.parent(cluster, self.pvVizGRP)



    def coxa(self):
        '''
        cLAVICEL
        '''            

        self.coxaJnt = f"{self.side}leg{self.legIndex}_JA{self.suffix['joint']}"

        self.coxaCtrl = cmds.circle(
            n = self.coxaJnt.replace(config.suffix['joint'], config.suffix['control']),
            r = self.size['clavs'],
            nr = (0,1,0))[0]

        self.coxaLoc = cmds.spaceLocator(
            n=self.coxaJnt.replace(config.suffix['joint'], config.suffix['locator']))[0]

        cmds.parent(self.coxaCtrl, self.coxaLoc)

        cmds.matchTransform(self.coxaLoc, self.coxaJnt, pos = True, rot = True)

        cmds.orientConstraint(
            self.coxaCtrl,
            self.coxaJnt,
            mo=True,
            n=self.coxaJnt.replace(config.suffix['joint'], config.suffix['orientCon']))

        cmds.makeIdentity(self.coxaCtrl, apply=True, t=True, r=True)

        shape = cmds.listRelatives(self.coxaCtrl, shapes=True, type="nurbsCurve")[0]

        # parent into FK chain
        cmds.parent(self.fkGrp, self.coxaCtrl)

    def cleanup(self):
        '''
        Minor cleanup:
            - hides fk/ik joints + ik handle
            - creates a group for the ik switch to parent the bindlocator
        
        '''
        IkswitchCtrl = cmds.group(em = True, w = True,n = f"{self.side}{self.limbType}_FKIK_switch{self.suffix['group']}") 

        cmds.parent(self.ikBNDLoc,self.switch, IkswitchCtrl)

        cmds.hide(self.fkJoints, self.ikJoints, self.ikHandle)

        cmds.parent(self.pvVizGRP, self.ikGrp)

    def legSpaceSwitch(self):
        '''
        Creates the spaceswitches for legs
        
        Parameters: 
            spineJnt: passed on from the spine module
        returns: alot of things im gnna guess. 
        '''
        if self.limbType == 'leg':

            cmds.addAttr(self.switch, ln = 'SPACES', at = "enum", en = "____________", k = True)
            #cmds.matchTransform(hipLoc, spineJnt, pos = True, rot = True
            
            cmds.addAttr(self.switch, ln = "Foot_Follow", at = "enum", en = "World : Hip", k = True)



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
        
        cmds.addAttr(self.switch, ln = f"{self.side}{self.limbType}Pole_Vector_Follow", at = "enum", en = f"World : {self.limbType}", k = True)

        driverPV = f"{self.switch}.{self.side}{self.limbType}Pole_Vector_Follow"

        drivenPV = f"{poConPV}.{self.side}{self.limbType}_pv_Space_LOCW0"

        cmds.setDrivenKeyframe(drivenPV, at = 'switchAttr', cd = driverPV, dv = 0, v = 0)
        cmds.setDrivenKeyframe(drivenPV, at = 'switchAttr', cd = driverPV, dv = 1, v = 1)
    
    def buildLimb(self):
        self.dupeJoints()
        self.fkSetup()
        self.driverIK()
        self.ikSetup()
        self.ikFkSwitch()
        self.ikfkBlends()
        self.ikfkGroups()
        self.findpoleVector()
        self.createPoleVector()
        self.poleVectorLine()

        self.coxa()
        self.legSpaceSwitch()

        self.poleVectorSpaceSwitch()
            
        self.cleanup()
        shapes.ctrlColour()
        print("\n [SpiderLeg Builder] :", self.side, "Leg:", self.legIndex)

def build():   
    """
    Builds the requested limb types for the specified sides.
    """

    legIndex= "A"
    sides = "L"
    for side in sides:
        for index in legIndex:
            spiderLegs(side,
                       index).buildLimb()
    
    print("\n All Limbs built \n ")

        
