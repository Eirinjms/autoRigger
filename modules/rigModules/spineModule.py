import maya.cmds as cmds # pyright: ignore[reportMissingImports] 
import autoRigger.utils.shapes as shapes
import autoRigger.utils.config as config

import importlib
importlib.reload(shapes)

class spineBuilder:
    def __init__(self, spineOrder : int, spineJoints : list | None = None):
        size = config.bipedal
        self.rotOrder = spineOrder

        self.prefix = config.prefix['center']
        self.suffix = config.suffix

        self.spineJointsAmount = len(spineJoints)
        self.spineJoints = spineJoints

        if not spineJoints:
            joints = ['spineJA', 'spineJB', 'spineJC', 'spineJD', 'spineJE']
            spineJoints = []
            for joint in joints: 
                joint = f"{self.prefix}{joint}{self.suffix['joint']}"
                spineJoints.append(joint)


        jointsNEW = ['spineJA', 'spineJB', 'spineJEnd'] 

        self.startJoint = self.spineJoints[0]
        self.endJoint = self.spineJoints[-1]

        for i in range(self.spineJointsAmount):



    
    def duplicatingJoints(self):
        fkJoints = []
        ikJoints = []

        # duplicate joint chains
        for i in fkIK:
            for joint in joints:
                source = f"{prefix[0]}{joint}{suffix[0]}" 

                if not cmds.objExists(source):
                    cmds.warning(f"{source} does not exist, skipping")
                    continue

                dup = cmds.duplicate(source, po=True, n=joint + i)[0]

                if i == fkIK[0]:  # FK chain
                    fkJoints.append(dup)
                    if len(fkJoints) > 1:
                        cmds.parent(fkJoints[-1], fkJoints[-2])

                else:  # IK chain
                    ikJoints.append(dup)
                    if len(ikJoints) > 1:
                        cmds.parent(ikJoints[-1], ikJoints[-2])

    def build(spineOrder):
        suffix = ['_JNT','_LOC', '_CTRL', '_CON', '_IKH', '_FKIK', '_BLND', '_GRP', '_REV', '_CURVE']
        prefix = ['C_']
        joints = ['spineJA', 'spineJB', 'spineJC', 'spineJD', 'spineJE']
        con = ['_paCON', '_poCON', '_oCON']
        fkIK = ['_FK_JNT', '_IK_JNT']
        jointsNEW = ['spineJA', 'spineJB', 'spineJEnd']

        #########################################################################

        #duplicating the joint chains

        #########################################################################

        fkJoints = []
        ikJoints = []

        # duplicate joint chains
        for i in fkIK:
            for joint in joints:
                source = f"{prefix[0]}{joint}{suffix[0]}" 

                if not cmds.objExists(source):
                    cmds.warning(f"{source} does not exist, skipping")
                    continue

                dup = cmds.duplicate(source, po=True, n=joint + i)[0]

                if i == fkIK[0]:  # FK chain
                    fkJoints.append(dup)
                    if len(fkJoints) > 1:
                        cmds.parent(fkJoints[-1], fkJoints[-2])

                else:  # IK chain
                    ikJoints.append(dup)
                    if len(ikJoints) > 1:
                        cmds.parent(ikJoints[-1], ikJoints[-2])

        #########################################################################

        #FK setup

        #########################################################################

        fkLocs = []
        fkCtrls = []

        fkCount = 0

        for joint in fkJoints: 
            fkLoc = cmds.spaceLocator(n = prefix[0] + joint.replace(suffix[0], suffix[1]))
            fkLocs.append(fkLoc)

            fkCtrl = cmds.circle(n = prefix[0] + joint.replace(suffix[0], suffix[2]), r = size['FKspine'], nr = (1,0,0))[0]
            fkCtrls.append(fkCtrl)

            shape = cmds.listRelatives(fkCtrl, shapes=True, type="nurbsCurve")[0]

            cvs = cmds.ls(shape + ".cv[*]", fl=True)

            indices = [3,7]

            if 'spineJE' in joint:

                for i in indices:
                    cv = cvs[i]
                    cmds.xform(cv, t = (20, 0, 0), os = True, r = True)

            elif 'spineJD' in joint:

                for i in indices:
                    cv = cvs[i]
                    cmds.xform(cv, t = (-20, 0, 0), os = True, r = True)
            
            
            cmds.parent(fkCtrl, fkLoc)
            cmds.delete(cmds.parentConstraint(joint, fkLoc, mo = False))


            if 'spineJA' in joint:
                cmds.parentConstraint(fkCtrl,joint, n = joint + (con[0]), mo = False)
            else:
                cmds.orientConstraint(fkCtrl,joint, n = joint + (con[2]), mo = False)
            
            if fkCount > 0:
                cmds.parent(fkLocs[fkCount], fkCtrls[fkCount-1])

            fkCount =  fkCount + 1
        #########################################################################

        #IK setup

        #########################################################################
        curvepoints = []

        for joint in ikJoints: 
            pos = cmds.xform(joint, q = True, ws = True, t = True)
            curvepoints.append(pos)

            
        iKctrlCurve = cmds.curve(d = 3, ep = curvepoints, n = f"{joints[0].replace('JA', '')}{suffix[4]}{suffix[-1]}")

        cmds.setAttr(f"{iKctrlCurve}.inheritsTransform", 0)

        ikSpline = cmds.ikHandle(ccv = False, sol="ikSplineSolver", c = iKctrlCurve, sj = ikJoints[0], ee = ikJoints[-1], rtm = False, n = f"spine{suffix[4]}")
        curveJoints = ikJoints[0::2]

        jointName = ['hip_', 'middle_', 'shoulders_']    

        ctrlJoints = []

        for i, joint in enumerate(curveJoints):
            name = jointName[i]
            ctrlJoint = cmds.joint(n=f"{prefix[0]}{name}{joint.replace('JA','').replace('JC','').replace('JE','')}{suffix[2]}{suffix[0]}")
            cmds.delete(cmds.parentConstraint(joint, ctrlJoint))
            cmds.parent(w=True)

            ctrlJoints.append(ctrlJoint)

        ikLocs = []
        ikCtrls = []

        for joint in ctrlJoints:
            ikLoc = cmds.spaceLocator(n = joint.replace(suffix[0], suffix[1]))
            ikLocs.append(ikLoc)

            ikCtrl = shapes.cubeCtrl(name = joint.replace(suffix[0], suffix[2]), X = size['IKspineX'], Y = size['IKspineY'], Z  = size['IKspineZ'])
            ikCtrls.append(ikCtrl)

            cmds.parent(ikCtrl, ikLoc)
            cmds.delete(cmds.parentConstraint(joint, ikLoc, mo = False))

            cmds.parentConstraint(ikCtrl, joint, n = joint.replace(suffix[0], con[0]), mo = False)

        cmds.skinCluster(ctrlJoints, iKctrlCurve, tsb=True, n = "ikSpine_SKN")


        ########################################################

        #nodes

        ########################################################

        md = cmds.shadingNode('multiplyDivide', au = True)
        cmds.setAttr(f"{md}.input2X", -1)
        pma = cmds.shadingNode('plusMinusAverage', au = True)
        cmds.setAttr(f"{pma}.operation", 1)

        cmds.connectAttr(f"{ikCtrls[0]}.rotateX", f"{ikSpline[0]}.roll")
        cmds.connectAttr(f"{ikCtrls[0]}.rotateX", f"{md}.input1X")
        cmds.connectAttr(f"{md}.outputX", f"{pma}.input1D[0]")
        cmds.connectAttr(f"{ikCtrls[-1]}.rotateX", f"{pma}.input1D[1]")
        cmds.connectAttr(f"{pma}.output1D", f"{ikSpline[0]}.twist")


        #########################################################################

        #Create switch

        #########################################################################

        ikBNDLoc = cmds.spaceLocator(n = '_spine_FKIK_CTRL') [0]
        switch = shapes.gearCtrl(name = 'spine_FKIK_switch' + suffix[2], size = 7, limb = 'none', side = 'none')

        cmds.parent(switch, ikBNDLoc)
        cmds.parentConstraint(prefix[0] + joints[-1] + suffix[0], ikBNDLoc, n = joints[0] + '_BND' + con[0], mo = False)

        cmds.addAttr(switch, ln = 'FKIK_Switch', at = 'float', min = 0, max = 1, dv = 1, k = True)

        Transform=(40, 0, 30) 

        cmds.xform(switch, r = True, t = Transform, ro = (0, 0, 0))
        cmds.makeIdentity(switch, apply = True, t = True, r = True)

        attrs = ["tx","ty","tz","rx","ry","rz","sx","sy","sz"]

        for attr in attrs: 
            cmds.setAttr(switch + "." + attr, l = True, k = False, cb = False)

        #########################################################################

        #Blends

        #########################################################################

        blendCount = 0

        for joint in joints: 
            rotBlend = cmds.shadingNode('blendColors', au = True, n = f"{joint}_rot{suffix[6]}")

            cmds.connectAttr(ikJoints[blendCount] + '.rotate', rotBlend + '.color1')
            cmds.connectAttr(fkJoints[blendCount] + '.rotate', rotBlend + '.color2')
            cmds.connectAttr(rotBlend + '.output',  prefix[0] + joint + suffix[0] + '.rotate')

            cmds.connectAttr(switch + '.FKIK_Switch', rotBlend + '.blender')

            blendCount = blendCount + 1
            
        trnBlend =  cmds.shadingNode('blendColors', au = True, n = f"{joints[0]}_tran{suffix[6]}") 
        cmds.connectAttr(ikJoints[0] + '.translate', trnBlend + '.color1')
        cmds.connectAttr(fkJoints[0] + '.translate', trnBlend + '.color2')
        cmds.connectAttr(trnBlend + '.output', prefix[0] + joints[0] + suffix[0] + '.translate')

        cmds.connectAttr(switch + '.FKIK_Switch', trnBlend + '.blender')

        #########################################################################

        fkGrp = cmds.group(n = 'spine' + fkIK[0].replace(suffix[0], suffix[7]), em = True)
        ikGrp = cmds.group(n = 'spine' + fkIK[1].replace(suffix[0], suffix[7]), em = True)
        ikJointCtrlGrp = cmds.group(n = f"spineCtrlJoints_GRP", em = True)
        ikCtrlGrp = cmds.group(n = f"ik_CTRL_GRP", em = True)

        cmds.parent(ikLocs[0], ikLocs[1], ikLocs[2], ikCtrlGrp)
        cmds.parent(ctrlJoints, ikJointCtrlGrp)
        cmds.parent(fkLocs[0], fkGrp)
        cmds.parent(ikSpline[0], ikCtrlGrp, ikJointCtrlGrp, iKctrlCurve, ikGrp)

        topSpineLOC = cmds.spaceLocator(n = f"{joints[2]}_BND{suffix[1]}")
        bottomSpineLOC = cmds.spaceLocator(n = f"{joints[0]}_BND{suffix[1]}")

        cmds.delete(cmds.parentConstraint(f"{prefix[0]}{joints[2]}{suffix[0]}", topSpineLOC))
        cmds.delete(cmds.parentConstraint(f"{prefix[0]}{joints[0]}{suffix[0]}",bottomSpineLOC))

        cmds.parentConstraint(f"{prefix[0]}{joints[0]}{suffix[0]}", bottomSpineLOC, n = f"{joints[0]}_BND{con[0]}")
        cmds.parentConstraint(f"{prefix[0]}{joints[2]}{suffix[0]}", topSpineLOC, n = f"{joints[2]}_BND{con[0]}")

        #########################################################################

        cmds.connectAttr(switch + '.FKIK_Switch', ikGrp + '.visibility')

        fkikRev = cmds.shadingNode('reverse', au = True, n = joints[0] + suffix[8])

        cmds.connectAttr(switch + '.FKIK_Switch', fkikRev + '.inputX')
        cmds.connectAttr(fkikRev + '.outputX', fkGrp + '.visibility')


        IkswitchCtrl = cmds.group(em = True, w = True, n = 'spine_IK_switch' + suffix[7]) 
        cmds.parent(ikBNDLoc, IkswitchCtrl)

        cmds.hide(fkJoints, ikJoints, ikSpline, ikJointCtrlGrp, iKctrlCurve)

