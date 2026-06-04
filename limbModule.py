import maya.cmds as cmds
import maya.api.OpenMaya as om
import autoRigTool.shapes as shapes
import autoRigTool.reverseFoot as reverseFoot
import autoRigTool.handModule as handModule
import autoRigTool.naming as naming
import importlib

importlib.reload(naming)


class limbBuild:
    def __init__(self, side, limbType, pvDistance):
        if side not in ['L', 'R']: 
            cmds.error('Please Choose either L or R')
        if limbType not in ['arm', 'leg']:
            cmds.error('Please Choose either arm or leg')
        
        self.suffix = naming.suffix

        self.fkIK = naming.fkik
        self.attrs = naming.attrs

        self.side = f"{side}_"

        self.pvDistance = pvDistance

        self.limbType = limbType

        #makes a list of the joints depending on limb 
        if self.limbType == 'arm':
            index = 'BCD'
        if self.limbType == 'leg':
            index = 'ABC'

        self.joints = [f"{self.limbType}J{i}" for i in index]
        


    def dupeJoints(self):
        self.fkJoints = []
        self.ikJoints = []

        count = 0

        #########################################################################

        #duplicating the joint chains

        #########################################################################

        for i in self.fkIK:
            for joint in self.joints:
                dup = cmds.duplicate(f"{self.side}{joint}{self.suffix['joint']}", 
                                     po = True, 
                                     n = f"{self.side}{joint}{i}{self.suffix['joint']}")[0]

                if count == len(self.joints):
                    count = 0 

                if dup.endswith(f"{self.fkIK[0]}{self.suffix['joint']}"):
                    self.fkJoints.append(dup)
                    if count > 0:
                        cmds.parent(self.fkJoints[count], self.fkJoints[count-1])

                else:
                    self.ikJoints.append(dup)
                    if count > 0:
                        cmds.parent(self.ikJoints[count], self.ikJoints[count-1])

                count = count + 1    


    def fkSetup(self):
        #########################################################################

        #FK setup

        #########################################################################

        self.fkLocs = []
        self.fkCtrls = []

        fkCount = 0

        for joint in self.fkJoints: 
            fkLoc = cmds.spaceLocator(n = joint.replace(self.suffix['joint'], self.suffix['locator']))
            self.fkLocs.append(fkLoc)

            if 'legJA' in joint:
                radius = 13
                normal=(1, 0, 0)

            elif 'legJB' in joint:
                radius = 10
                normal=(1, 0, 0 )

            elif 'legJC' in joint:
                normal=(0, 1, 0 )
                radius = 7
            
            elif 'arm' in joint: 
                normal = (1,0,0)
                radius = 10

            fkCtrl = cmds.circle(n = joint.replace(self.suffix['joint'], self.suffix['control']), 
                                 r = radius, 
                                 nr = normal)[0]
            self.fkCtrls.append(fkCtrl)
            
            cmds.parent(fkCtrl, fkLoc)
            cmds.delete(cmds.parentConstraint(joint, fkLoc, mo = False))

            cmds.orientConstraint(fkCtrl, joint, 
                                  n = joint.replace(self.suffix['joint'], self.suffix['orientCon']), 
                                  mo = False)
            
            if fkCount > 0:
                cmds.parent(self.fkLocs[fkCount], self.fkCtrls[fkCount-1])

            fkCount =  fkCount + 1

    def ikSetup(self):
        #########################################################################

        #IK setup

        #########################################################################

        self.ikHandle = cmds.ikHandle(n = self.ikJoints[0].replace(self.fkIK[1], self.suffix ['ikHandle']), 
                                 sj = self.ikJoints[0], 
                                 ee = self.ikJoints[2])[0]
        
        self.ikLoc = cmds.spaceLocator(n = self.ikJoints[0].replace(self.suffix['joint'], self.suffix['locator']))

        self.ikCtrl = shapes.cubeCtrl(name = self.ikJoints[0].replace(self.suffix['joint'], self.suffix['control']), 
                                 X = 7, 
                                 Y = 7, 
                                 Z = 7)

        shape = cmds.listRelatives(self.ikCtrl, type = 'nurbsCurve')

        cmds.parent(self.ikCtrl, self.ikLoc)
        cmds.delete(cmds.parentConstraint(self.ikJoints[2], self.ikLoc, mo = False))

        cmds.pointConstraint(self.ikCtrl, self.ikHandle, 
                             n = self.ikJoints[0].replace(self.suffix['joint'], self.suffix['pointCon']), 
                             mo = False)
        cmds.orientConstraint(self.ikCtrl, self.ikJoints[2], 
                              n = self.ikJoints[0].replace(self.suffix['joint'], self.suffix['orientCon']), 
                              mo = False)

    def ikFkSwitch(self):
        #########################################################################

        #Create switch

        #########################################################################
        self.ikBNDLoc = cmds.spaceLocator(n = self.ikJoints[0].replace(self.suffix['joint'], '_BND' + self.suffix['locator'] )) [0]
        self.switch = shapes.gearCtrl(name = f"{self.side}{self.limbType}_FKIK_switch{self.suffix['control']}", 
                                 size = 3, 
                                 side = self.side, 
                                 limb = self.limbType)

        cmds.parent(self.switch, self.ikBNDLoc)
        cmds.parentConstraint(f"{self.side}{self.joints[2]}{self.suffix['joint']}", self.ikBNDLoc, 
                              n = f"{self.side}{self.joints[0]}_BND{self.suffix['parentCon']}", 
                              mo = False)

        cmds.addAttr(self.switch, 
                     ln = 'FKIK_Switch', 
                     at = 'float', 
                     min = 0, 
                     max = 1, 
                     dv = 1, 
                     k = True)

        if 'L_' in self.switch:
            Transform=(0, 0, -13)
            
        else: 
            Transform=(0, 0, 13) 

        cmds.xform(self.switch, r = True, 
                   t = Transform, 
                   ro = (-6, 0, 90))
        cmds.makeIdentity(self.switch, 
                          apply = True, 
                          t = True, 
                          r = True)

        for attr in self.attrs: 
            cmds.setAttr(f"{self.switch}.{attr}", 
                         l = True, 
                         k = False, 
                         cb = False)

    def ikfkBlends(self):
        #########################################################################

        #Blends

        #########################################################################

        blendCount = 0


        for joint in self.joints: 
            rotBlend = cmds.shadingNode('blendColors', 
                                        au = True, 
                                        n = f"{joint}_rot{self.suffix['blendColor']}")

            cmds.connectAttr(f"{self.ikJoints[blendCount]}.rotate", f"{rotBlend}.color1")
            cmds.connectAttr(f"{self.fkJoints[blendCount]}.rotate", f"{rotBlend}.color2")
            cmds.connectAttr(f"{rotBlend}.output",  f"{self.side}{joint}{self.suffix['joint']}.rotate")

            cmds.connectAttr(f"{self.switch}.FKIK_Switch", f"{rotBlend}.blender")
            blendCount = blendCount + 1


        blendCount = 0


        for joint in self.joints: 
            scaleBlend = cmds.shadingNode('blendColors', 
                                          au = True, 
                                          n = f"{joint}_scale{self.suffix['blendColor']}")

            cmds.connectAttr(f"{self.ikJoints[blendCount]}.scale", f"{scaleBlend}.color1")
            cmds.connectAttr(f"{self.fkJoints[blendCount]}.scale", f"{scaleBlend}.color2")
            cmds.connectAttr(f"{scaleBlend}.output",  f"{self.side}{joint}{self.suffix['joint']}.scale")

            cmds.connectAttr(f"{self.switch}.FKIK_Switch", f"{scaleBlend}.blender")

            blendCount = blendCount + 1

    def ikfkGroups(self):
        #########################################################################
        fkGrp = cmds.group(n = f"{self.side}{self.limbType}{self.fkIK[0]}{self.suffix['group']}", em = True)
        self.ikGrp = cmds.group(n = f"{self.side}{self.limbType}{self.fkIK[1]}{self.suffix['group']}", em = True)

        cmds.parent(self.fkLocs[0], fkGrp)
        cmds.parent(self.ikHandle, self.ikLoc, self.ikGrp)

        #########################################################################

        cmds.connectAttr(f"{self.switch}.FKIK_Switch", f"{self.ikGrp}.visibility")

        fkikRev = cmds.shadingNode('reverse', 
                                   au = True, 
                                   n = f"{self.side}{self.joints[0]}{self.suffix['reverse']}")

        cmds.connectAttr(f"{self.switch}.FKIK_Switch", f"{fkikRev}.inputX")
        cmds.connectAttr(fkikRev + '.outputX', fkGrp + '.visibility')


    def poleVector(self):
        #########################################################################

        #PoleVector

        #########################################################################

        H = om.MVector(cmds.xform(f"{self.side}{self.joints[0]}{self.suffix['joint']}", q = True, ws = True, t = True))
        K = om.MVector(cmds.xform(f"{self.side}{self.joints[1]}{self.suffix['joint']}", q = True, ws = True, t = True))
        A = om.MVector(cmds.xform(f"{self.side}{self.joints[2]}{self.suffix['joint']}", q = True, ws = True, t = True))

        HK = K - H
        HA = A - H

        dot = HK * HA

        proj = (dot/(HA.length()**2)) * HA

        projK = HK - proj

        pv = (projK * self.pvDistance) + K

        self.pvLoc = cmds.spaceLocator(p = pv, n = f"{self.side}{self.limbType}_PV_LOC")[0]
        cmds.xform(self.pvLoc, cp = True)

        self.pvCtrl = shapes.pyramidCtrl(name = f"{self.side}{self.limbType}_PV{self.suffix['control']}", size = -2)
        cmds.parent(self.pvCtrl, self.pvLoc)

        cmds.delete(cmds.parentConstraint(self.pvLoc, self.pvCtrl))

        pvCon = cmds.poleVectorConstraint(self.pvCtrl, self.ikHandle, n = self.ikJoints[0].replace(self.suffix['joint'], self.suffix['poleVectorCon']))

        cmds.makeIdentity(self.pvCtrl, apply = True, t = True)

        cmds.parent(self.pvLoc, self.ikGrp)
    
    def clavicle(self):
            self.clavJnt = f"{self.side}armJA{self.suffix['joint']}"

            self.clavCtrl = cmds.circle(
                n=f"{self.side}armJA{self.suffix['control']}",
                r=7,
                nr=(0,1,0))[0]

            self.clavLoc = cmds.spaceLocator(
                n=f"{self.side}armJA{self.suffix['locator']}")[0]

            cmds.parent(self.clavCtrl, self.clavLoc)

            cmds.delete(cmds.parentConstraint(self.clavJnt, self.clavLoc))

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
            cmds.parent(self.fkLocs[0], self.clavCtrl)

    def cleanup(self):
        #########################################################################

        # Clean up

        #########################################################################
        IkswitchCtrl = cmds.group(em = True, w = True,n = f"{self.side}{self.limbType}_IK_switch{self.suffix['group']}") 

        cmds.parent(self.ikBNDLoc, IkswitchCtrl)

        cmds.hide(self.fkJoints, self.ikJoints, self.ikHandle)

        
    def endlimb(self):
        if self.limbType == 'leg':
            reverseFoot.build(self.side, self.ikHandle, self.ikCtrl, self.switch)
        if self.limbType == 'arm':
            handModule.build(self.side)


    def spaceSwitch(self):

        if self.limbType == 'leg':
            #########################################################################

            #leg spaceswitch

            #########################################################################

            cmds.addAttr(self.switch, ln = 'SPACES', at = "enum", en = "____________", k = True)

            hipLoc = cmds.spaceLocator(p = cmds.xform('C_spineJA_JNT',q = True, t = True), n = f"{self.side}leg_hipSpace{self.suffix['locator']}")
            
            poConPV = cmds.parentConstraint(hipLoc, self.ikLoc, mo = True, n = f"{self.side}pv_SpaceSwitch{self.suffix['parentCon']}")[0]
            
            cmds.addAttr(self.switch, ln = "Foot_Follow", at = "enum", en = "World : Hip", k = True)

            driverPV = f"{self.switch}.Foot_Follow"

            drivenPV = f"{poConPV}.{self.side}hipSpace_LOCW0"

            cmds.setDrivenKeyframe(drivenPV, at = 'switchAttr', cd = driverPV, dv = 0, v = 0)
            cmds.setDrivenKeyframe(drivenPV, at = 'switchAttr', cd = driverPV, dv = 1, v = 1)

        if self.limbType == 'arm':
            
        #Make the locators
            worldLoc = cmds.spaceLocator(n =f"{self.side}arm_worldSpace{self.suffix['locator']}" )[0]
            hipLoc = cmds.spaceLocator(n = f"{self.side}arm_hipSpace{self.suffix['locator']}")[0]
            clavSpaceLoc = cmds.spaceLocator(n = f"{self.side}arm_clavSpace{self.suffix['locator']}")[0]
            localSpaceLoc = cmds.spaceLocator(n = f"{self.side}arm_localSpace{self.suffix['locator']}")[0]

            cmds.parent(self.ikLoc, localSpaceLoc)
            cmds.parent(localSpaceLoc, self.ikGrp)
        
            spineJnt = "C_spineJA_JNT"
            #spineLoc = "spineJA_BND_LOC"

            cmds.delete(cmds.parentConstraint(spineJnt, hipLoc, mo = 0))
            cmds.delete(cmds.parentConstraint(self.clavJnt, clavSpaceLoc, mo = 0))
            cmds.delete(cmds.parentConstraint(f"{self.side}{self.joints[2]}{self.suffix['joint']}", worldLoc, mo = 0))

            #cmds.parent(hipLoc, spineLoc)
            cmds.parent(clavSpaceLoc, self.clavCtrl)

            paCon = cmds.parentConstraint(worldLoc, clavSpaceLoc, hipLoc, self.ikLoc, mo = True, n = f"{self.side}spaceSwitch{self.suffix['parentCon']}")[0]

            cmds.parent(worldLoc, self.ikGrp)

            #make the switch

            cmds.addAttr(self.switch, ln = 'SPACES', at = "enum", en = "____________", k = True)
        
            cmds.addAttr(self.switch, ln = "Hand_Follow", at = "enum", en = " World : Clavicle : Hip ", k = True)


            #should u have time make this a loop pls
            driver = f"{self.switch}.Hand_Follow"

            driven1 = f"{paCon}.{self.side}arm_worldSpace_LOCW0"

            driven2 = f"{paCon}.{self.side}arm_clavSpace_LOCW1"

            driven3 = f"{paCon}.{self.side}arm_hipSpace_LOCW2"

            cmds.setDrivenKeyframe(driven1, cd = driver, dv = 0, v = 1)
            cmds.setDrivenKeyframe(driven1, cd = driver, dv = 1, v = 0)
            cmds.setDrivenKeyframe(driven1, cd = driver, dv = 2, v = 0)

            cmds.setDrivenKeyframe(driven2, cd = driver, dv = 0, v = 0)
            cmds.setDrivenKeyframe(driven2, cd = driver, dv = 1, v = 1)
            cmds.setDrivenKeyframe(driven2, cd = driver, dv = 2, v = 0)

            cmds.setDrivenKeyframe(driven3,  cd = driver, dv = 0, v = 0)
            cmds.setDrivenKeyframe(driven3,  cd = driver, dv = 1, v = 0)
            cmds.setDrivenKeyframe(driven3,  cd = driver, dv = 2, v = 1)

            spaces = ["worldSpace", "clavSpace", "hipSpace"]

            driver = f"{self.switch}.Hand_Follow"

            for i, name in enumerate(spaces):
                driven = f"{paCon}.{self.side}arm_{name}_LOCW{i}"
                
                for dv in range(len(spaces)):
                    v = 1 if dv == i else 0
                    cmds.setDrivenKeyframe(driven, cd=driver, dv=dv, v=v)

        #########################################################################

        #pv spaceswitch

        #########################################################################

        pvSpaceLoc = cmds.spaceLocator(n = f"{self.side}{self.limbType}_pv_Space{self.suffix['locator']}")[0]
        
        cmds.delete(cmds.parentConstraint(self.pvLoc, pvSpaceLoc, mo = 0))
        
        cmds.parent(pvSpaceLoc, self.ikCtrl)

        poConPV = cmds.parentConstraint(pvSpaceLoc, self.pvLoc, mo = False, n = f"{self.side}pv_SpaceSwitch{self.suffix['parentCon']}")[0]
        
        cmds.addAttr(self.switch, ln = f"{self.side}{self.limbType}Pole_Vector_Follow", at = "enum", en = "World : Leg", k = True)

        driverPV = f"{self.switch}.{self.side}{self.limbType}Pole_Vector_Follow"

        drivenPV = f"{poConPV}.{self.side}{self.limbType}_pv_Space_LOCW0"

        cmds.setDrivenKeyframe(drivenPV, at = 'switchAttr', cd = driverPV, dv = 0, v = 0)
        cmds.setDrivenKeyframe(drivenPV, at = 'switchAttr', cd = driverPV, dv = 1, v = 1)

    def squashNstretch(self):
        ##############################################################################

        #squash and stretch

        ##############################################################################
        startJnt = cmds.xform(self.ikJoints[0], q = True, ws = True, t = True)
        midJnt = cmds.xform(self.ikJoints[1], q = True, ws = True, t = True)
        endJnt = cmds.xform(self.ikJoints[2], q = True, ws = True, t = True)

        a1 = cmds.curve(d = 1, ep = [startJnt, midJnt], n = f"{self.side}leg_a1Curve")
        a2 = cmds.curve(d = 1, ep = [midJnt, endJnt], n = f"{self.side}leg_a2Curve")
        b =  cmds.curve(d = 1, ep = [startJnt, endJnt], n = f"{self.side}leg_bCurve")

        cmds.select(f"{b}.cv[1]")

        ikCluster = cmds.cluster(n = f"{self.side}ikStretch")
        #turn on clusterrelative
        cmds.setAttr(f"{ikCluster[0]}.relative", 1)

        a1ci = cmds.shadingNode('curveInfo', au = True)
        cmds.connectAttr(f"{a1}.worldSpace[0]", f"{a1ci}.inputCurve")
        a2ci = cmds.shadingNode('curveInfo', au = True)
        cmds.connectAttr(f"{a2}.worldSpace[0]", f"{a2ci}.inputCurve")
        bci = cmds.shadingNode('curveInfo', au = True)
        cmds.connectAttr(f"{b}.worldSpace[0]", f"{bci}.inputCurve")

        #nodeshti
        pma = cmds.shadingNode('plusMinusAverage', au = True, n = f"{self.side}Stretch_PMA")
        cmds.connectAttr(f"{a1ci}.arcLength", f"{pma}.input1D[0]")
        cmds.connectAttr(f"{a2ci}.arcLength", f"{pma}.input1D[1]")

        md = cmds.shadingNode('multiplyDivide', au = True, n = f"{self.side}Stretch_MD")
        cmds.setAttr(f"{md}.operation", 2)
        cmds.connectAttr(f"{bci}.arcLength", f"{md}.input1X")
        cmds.connectAttr(f"{pma}.output1D", f"{md}.input2X")

        cnd = cmds.shadingNode('condition', au = True, n = f"{self.side}Stretch_CND")
        cmds.setAttr(f"{cnd}.operation", 3) 
        cmds.setAttr (f"{cnd}.secondTerm", 1)
        cmds.setAttr (f"{cnd}.colorIfFalseR", 1)
        cmds.connectAttr(f"{md}.outputX", f"{cnd}.colorIfTrueR")
        cmds.connectAttr(f"{md}.outputX", f"{cnd}.firstTerm")


        cmds.connectAttr(f"{cnd}.outColorR", f"{self.ikJoints[0]}.scaleX")
        cmds.connectAttr(f"{cnd}.outColorR", f"{self.ikJoints[1]}.scaleX")

        cmds.parent(ikCluster, self.ikGrp)
        clusterpocon = cmds.pointConstraint(self.ikCtrl, ikCluster[1], mo = True, n = f"{self.side}ikCluster{self.suffix['pointCon']}")[0]

        cmds.addAttr(self.switch, ln = 'IK_Stretch', at = "enum", en = "____________", k = True)

        cmds.addAttr(self.switch, at = 'bool', ln = f"{self.side}Stretch", k = True, dv = 1)
        
        cmds.setDrivenKeyframe(f"{clusterpocon}.{self.ikCtrl}W0", cd = f"{self.switch}.{self.side}Stretch", dv = 0, v = 0)
        cmds.setDrivenKeyframe(f"{clusterpocon}.{self.ikCtrl}W0", cd = f"{self.switch}.{self.side}Stretch", dv = 1, v = 1)

        curveGrp = cmds.group(a1, a2, b, n = f"{self.side}{self.limbType}ScaleCurves{self.suffix['group']}", p = self.ikGrp)
        cmds.hide(curveGrp, ikCluster[1])

    def buildLimb(self):
        self.dupeJoints()
        self.fkSetup()
        self.ikSetup()
        self.ikFkSwitch()
        self.ikfkBlends()
        self.ikfkGroups()
        self.poleVector()

        if self.limbType == 'arm':
            self.clavicle()
        
        self.endlimb()
        self.spaceSwitch()
        self.squashNstretch()
        self.cleanup()
        shapes.ctrlColour()
        print("Building:", self.side, self.limbType)

def build_limb_set(sides, limbs, pv):   
    """Builds multiple limb combinations for a character.

    Useful for creating standard biped setups, such as
    left/right arms and legs, using a single function call.

    Args:
        sides (list): Character sides (e.g. ['L', 'R']).
        limbs (list): Limb types to build (e.g. ['arm', 'leg']).
        pv (int): Pole vector distance. Automatically adjusted
                for supported limb types."""

    for side in sides:
        for limb in limbs:
            if limb == 'arm':
                pv = 10
            elif limb == 'leg':
                pv = 15
            limbBuild(side, limb, pv).buildLimb()

        
