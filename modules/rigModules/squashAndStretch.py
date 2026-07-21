import maya.cmds as cmds 
import autoRigger.utils.config as config

class squashNStretch:
    def __init__(self, joints, side, limb, ikgrp, ikCtrl, switch, twistJoints):
            
            self.joints = joints
            self.side = side
            self.limbType = limb
            self.switch = switch
            self.ikGrp = ikgrp
            self.ikCtrl = ikCtrl
            self.twistJoints = twistJoints

            self.suffix = config.suffix

    def create(self):

            startJnt = cmds.xform(self.joints[0], q = True, ws = True, t = True)
            midJnt = cmds.xform(self.joints[1], q = True, ws = True, t = True)
            endJnt = cmds.xform(self.joints[2], q = True, ws = True, t = True)

            a1 = cmds.curve(d = 1, ep = [startJnt, midJnt], n = f"{self.side}{self.limbType}_a1Curve")
            a2 = cmds.curve(d = 1, ep = [midJnt, endJnt], n = f"{self.side}{self.limbType}_a2Curve")
            b =  cmds.curve(d = 1, ep = [startJnt, endJnt], n = f"{self.side}{self.limbType}_bCurve")


            ikCluster = cmds.cluster(f"{b}.cv[1]", n = f"{self.side}ikStretch")

            #turn on clusterrelative
            cmds.setAttr(f"{ikCluster[0]}.relative", 1)

            a1ci = cmds.shadingNode('curveInfo', au = True)
            cmds.connectAttr(f"{a1}.worldSpace[0]", f"{a1ci}.inputCurve")
            a2ci = cmds.shadingNode('curveInfo', au = True)
            cmds.connectAttr(f"{a2}.worldSpace[0]", f"{a2ci}.inputCurve")
            bci = cmds.shadingNode('curveInfo', au = True)
            cmds.connectAttr(f"{b}.worldSpace[0]", f"{bci}.inputCurve")

            #nodes
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

            
            scaleJoints = self.joints[:-1]
            if self.twistJoints: 
                  print(self.twistJoints)
                  scaleJoints.extend(self.twistJoints[:-1])

            for joint in scaleJoints:
                cmds.connectAttr(f"{cnd}.outColorR", f"{joint}.scaleX")

            cmds.parent(ikCluster[1], self.ikGrp)
            clusterpocon = cmds.pointConstraint(self.ikCtrl, ikCluster[1], mo = True, n = f"{self.side}ikCluster{self.suffix['pointCon']}")[0]

            cmds.addAttr(self.switch, ln = 'IK_Stretch', at = "enum", en = "____________", k = True)

            cmds.addAttr(self.switch, at = 'bool', ln = f"{self.side}Stretch", k = True, dv = 1)
            
            cmds.setDrivenKeyframe(f"{clusterpocon}.{self.ikCtrl}W0", cd = f"{self.switch}.{self.side}Stretch", dv = 0, v = 0)
            cmds.setDrivenKeyframe(f"{clusterpocon}.{self.ikCtrl}W0", cd = f"{self.switch}.{self.side}Stretch", dv = 1, v = 1)

            curveGrp = cmds.group(a1, a2, b, n = f"{self.side}{self.limbType}ScaleCurves{self.suffix['group']}", p = self.ikGrp)
            cmds.hide(curveGrp, ikCluster[1])