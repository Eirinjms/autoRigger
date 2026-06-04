import maya.cmds as cmds
import maya.api.OpenMaya as om
import autoRigTool.shapes as shapes
import autoRigTool.handModule as handModule
import autoRigTool.sizes as sizes

import importlib
importlib.reload(sizes)

size = sizes.femaleSentinel

#Creating lists for later use
def ikfkBuild(side, pvDistance, hand):
    
    suffix = ['_JNT','_LOC', '_CTRL', '_CON', '_IKH', '_FKIK', '_BLND', '_GRP', '_REV', "_paCON", '_poCON', '_oCON', '_pvCON']
    prefix = ['L_', 'R_']
    joints = ['armJB', 'armJC', 'armJD']
    fkIK = ['_FK_JNT', '_IK_JNT']

    prefixSide = f"{side}_"

    fkJoints = []
    ikJoints = []

    count = 0

####################################################################

    #duplicating the joint chains

####################################################################

    for i in fkIK:
        for joint in joints:
            dup = cmds.duplicate(prefixSide + joint + suffix[0], po = True, n = prefixSide + joint + i)[0]


            if count == len(joints):
                count = 0 

            if dup.endswith(fkIK[0]):
                fkJoints.append(dup)
                if count > 0:
                    cmds.parent(fkJoints[count], fkJoints[count-1])

            else:
                ikJoints.append(dup)
                if count > 0:
                    cmds.parent(ikJoints[count], ikJoints[count-1])

            count = count + 1   



    #########################################################################

    #FK setup

    #########################################################################
    
    fkLocs = []
    fkCtrls = []

    fkCount = 0

    for joint in fkJoints: 
        fkLoc = cmds.spaceLocator(n = joint.replace(suffix[0], suffix[1]))
        fkLocs.append(fkLoc)

        if 'armJB' in joint:
            radius = size['FKarms']

        elif 'armJC' in joint:
            radius = size['FKarms'] - 5

        elif 'armJD' in joint:
            radius = size['FKarms'] - 10

        fkCtrl = cmds.circle(n = joint.replace(suffix[0], suffix[2]), r = radius, nr = (1,0,0))[0]
        fkCtrls.append(fkCtrl)
        
        cmds.parent(fkCtrl, fkLoc)
        cmds.delete(cmds.parentConstraint(joint, fkLoc, mo = False))

        cmds.orientConstraint(fkCtrl, joint, n = joint.replace(suffix[0], suffix[11]), mo = False)
        
        if fkCount > 0:
            cmds.parent(fkLocs[fkCount], fkCtrls[fkCount-1])

        fkCount =  fkCount + 1

    #########################################################################

    #IK setup

    #########################################################################

    ikHandle = cmds.ikHandle(n = ikJoints[0].replace(fkIK[1], suffix [4]), sj = ikJoints[0], ee = ikJoints[2])[0]
    ikLoc = cmds.spaceLocator(n = ikJoints[0].replace(suffix[0], suffix[1]))
    ikCtrl = shapes.cubeCtrl(name = ikJoints[0].replace(suffix[0], suffix[2]), X = size['IKarms'], Y = size['IKarms'], Z = size['IKarms'])

    cmds.parent(ikCtrl, ikLoc)
    cmds.delete(cmds.parentConstraint(ikJoints[2], ikLoc, mo = False))

    cmds.pointConstraint(ikCtrl, ikHandle, n = ikJoints[0].replace(suffix[0], suffix[10]), mo = False)
    cmds.orientConstraint(ikCtrl, ikJoints[2], n = ikJoints[0].replace(suffix[0], suffix[11]), mo = False)

    #########################################################################

    #Create switch

    #########################################################################

    ikBNDLoc = cmds.spaceLocator(n = ikJoints[0].replace(suffix[0], '_BND' +suffix[1] )) [0]
    switch = shapes.gearCtrl(name =  prefixSide + 'arm_FKIK_switch' + suffix[2], size = size['IKswitchArm'], side = prefixSide, limb = "arm")

    cmds.parent(switch, ikBNDLoc)
    cmds.parentConstraint(prefixSide + joints[2] + suffix[0], ikBNDLoc, n = prefixSide + joints[0] + '_BND' + suffix[9], mo = False)

    cmds.addAttr(switch, ln = 'FKIK_Switch', at = 'float', min = 0, max = 1, dv = 1, k = True)

    if 'L_' in switch:

        Transform=(0, 20, 0)
        
    else: 
        Transform=(0, -20, 0) 

    cmds.xform(switch, r = True, t = Transform, ro = (90, 0, 0))
    cmds.makeIdentity(switch, apply = True, t = True, r = True, s = True)

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
        cmds.connectAttr(rotBlend + '.output',  prefixSide + joint + suffix[0] + '.rotate')

        cmds.connectAttr(switch + '.FKIK_Switch', rotBlend + '.blender')

        blendCount = blendCount + 1

    blendCount = 0


    for joint in joints: 
        scaleBlend = cmds.shadingNode('blendColors', au = True, n = f"{joint}_rot{suffix[6]}")

        cmds.connectAttr(ikJoints[blendCount] + '.scale', scaleBlend + '.color1')
        cmds.connectAttr(fkJoints[blendCount] + '.scale', scaleBlend + '.color2')
        cmds.connectAttr(scaleBlend + '.output',  prefixSide + joint + suffix[0] + '.scale')

        cmds.connectAttr(switch + '.FKIK_Switch', scaleBlend + '.blender')

        blendCount = blendCount + 1


    #########################################################################

    fkGrp = cmds.group(n = prefixSide + 'arm' + fkIK[0].replace(suffix[0], suffix[7]), em = True)
    ikGrp = cmds.group(n = prefixSide + 'arm' + fkIK[1].replace(suffix[0], suffix[7]), em = True)

    cmds.parent(fkLocs[0], fkGrp)
    cmds.parent(ikHandle, ikLoc, ikGrp)

    #########################################################################

    cmds.connectAttr(switch + '.FKIK_Switch', ikGrp + '.visibility')

    fkikRev = cmds.shadingNode('reverse', au = True, n = prefixSide + joints[0] + suffix[8])

    cmds.connectAttr(switch + '.FKIK_Switch', fkikRev + '.inputX')
    cmds.connectAttr(fkikRev + '.outputX', fkGrp + '.visibility')

    #########################################################################

    #PoleVector

    #########################################################################

    H = om.MVector(cmds.xform(prefixSide + joints[0] + suffix[0], q = True, ws = True, t = True))
    K = om.MVector(cmds.xform(prefixSide + joints[1] + suffix[0], q = True, ws = True, t = True))
    A = om.MVector(cmds.xform(prefixSide + joints[2] + suffix[0], q = True, ws = True, t = True))

    HK = K - H
    HA = A - H

    dot = HK * HA

    proj = (dot/(HA.length()**2)) * HA

    projK = HK - proj

    pv = (projK * pvDistance) + K

    pvLoc = cmds.spaceLocator(p = pv, n = prefixSide  + 'Arm_PV_LOC')[0]
    cmds.xform(pvLoc, cp = True)

    pvCtrl = shapes.pyramidCtrl(name = (prefixSide + 'Arm_PV' + suffix[2]), size = size['PVarms'])
    cmds.parent(pvCtrl, pvLoc)

    cmds.delete(cmds.parentConstraint(pvLoc, pvCtrl))

    pvCon = cmds.poleVectorConstraint(pvCtrl, ikHandle, n = ikJoints[0].replace(suffix[0], suffix[12]))

    cmds.makeIdentity(pvCtrl, apply = True, t = True)

    
    cmds.parent(pvLoc, ikGrp)


    #########################################################################
    
    # clavicle controll

    #########################################################################

    clavJnt = (f"{prefixSide}armJA{suffix[0]}")
    clavCtrl = cmds.circle(n = f"{prefixSide}armJA{suffix[2]}", r = size ['clavs'], nr = (0,1,0))[0]
    clavLoc = cmds.spaceLocator(n = f"{prefixSide}armJA{suffix[1]}")

    cmds.parent(clavCtrl, clavLoc)
    
    cmds.delete(cmds.parentConstraint(clavJnt, clavLoc, mo = False))

    cmds.orientConstraint(clavCtrl, clavJnt, mo = True, n = f"{prefixSide}armJA{suffix[-2]}")

    cmds.makeIdentity(clavCtrl, apply = True, t = True, r = True)

    shape = cmds.listRelatives(clavCtrl, shapes=True, type="nurbsCurve")[0]

    cvs = cmds.ls(shape + ".cv[*]", fl=True)

    if shape.startswith("L_"):
        cmds.xform(cvs, t = (10, 20, 0), ro = (0, 0, -10), s = (2,2,2), r = True)

    elif shape.startswith("R_"):
        cmds.xform(cvs, t = (-10, -20, 0), ro = (0, 0, -10), s = (2,2,2), r = True)

    indices = [1,5]

    for i in indices:
        cv = cvs[i]

        if clavCtrl.startswith("L_"):
            cmds.xform(cv, t = (0, -5, 0), os = True, r = True)
        elif clavCtrl.startswith("R_"):
            cmds.xform(cv, t = (0, 5, 0), os = True, r = True)

    cmds.parent(fkGrp, clavCtrl)
    


    #########################################################################

    # Clean up outliner

    #########################################################################

    IkswitchCtrl = cmds.group(em = True, w = True,n = prefixSide + 'arm_IK_switch' + suffix[7]) 
    cmds.parent(ikBNDLoc, IkswitchCtrl)


    cmds.hide(fkJoints, ikJoints, ikHandle)

    if hand: 
        handModule.build(side = side)

    
    ##################################################################

    #spaceSwitching

    #################################################################
    #Make the locators
    worldLoc = cmds.spaceLocator(n =f"{prefixSide}arm_worldSpace{suffix[1]}" )[0]
    hipLoc = cmds.spaceLocator(n = f"{prefixSide}hipSpace{suffix[1]}")[0]
    clavSpaceLoc = cmds.spaceLocator(n = f"{prefixSide}arm_clavSpace{suffix[1]}")[0]
    localSpaceLoc = cmds.spaceLocator(n = f"{prefixSide}arm_localSpace{suffix[1]}")[0]

    cmds.parent(ikLoc, localSpaceLoc)
    cmds.parent(localSpaceLoc, ikGrp)
  
    spineJnt = "C_spineJA_JNT"
    spineLoc = "spineJA_BND_LOC"

    cmds.delete(cmds.parentConstraint(spineJnt, hipLoc, mo = 0))
    cmds.delete(cmds.parentConstraint(clavJnt, clavSpaceLoc, mo = 0))
    cmds.delete(cmds.parentConstraint(f"{prefixSide}{joints[2]}{suffix[0]}", worldLoc, mo = 0))

    cmds.parent(hipLoc, spineLoc)
    cmds.parent(clavSpaceLoc, clavCtrl)

    paCon = cmds.parentConstraint(worldLoc, clavSpaceLoc, hipLoc, ikLoc, mo = True, n = f"{prefixSide}spaceSwitch{suffix[9]}")[0]

    cmds.parent(worldLoc, ikGrp)

    #make the switch

    cmds.addAttr(switch, ln = 'SPACES', at = "enum", en = "____________", k = True)
 
    cmds.addAttr(switch, ln = "Hand_Follow", at = "enum", en = " World : Clavicle : Hip ", k = True)


    #should u have time make this a loop pls
    driver = f"{switch}.Hand_Follow"

    driven1 = f"{paCon}.{prefixSide}arm_worldSpace_LOCW0"

    driven2 = f"{paCon}.{prefixSide}arm_clavSpace_LOCW1"

    driven3 = f"{paCon}.{prefixSide}hipSpace_LOCW2"

    cmds.setDrivenKeyframe(driven1, cd = driver, dv = 0, v = 1)
    cmds.setDrivenKeyframe(driven1, cd = driver, dv = 1, v = 0)
    cmds.setDrivenKeyframe(driven1, cd = driver, dv = 2, v = 0)

    cmds.setDrivenKeyframe(driven2, cd = driver, dv = 0, v = 0)
    cmds.setDrivenKeyframe(driven2, cd = driver, dv = 1, v = 1)
    cmds.setDrivenKeyframe(driven2, cd = driver, dv = 2, v = 0)

    cmds.setDrivenKeyframe(driven3,  cd = driver, dv = 0, v = 0)
    cmds.setDrivenKeyframe(driven3,  cd = driver, dv = 1, v = 0)
    cmds.setDrivenKeyframe(driven3,  cd = driver, dv = 2, v = 1)


    #ELBOW
    
    pvSpaceLoc = cmds.spaceLocator(n = f"{prefixSide}arm_pv_Space{suffix[1]}")[0]
    
    cmds.delete(cmds.parentConstraint(pvLoc, pvSpaceLoc, mo = 0))
    
    cmds.parent(pvSpaceLoc, ikCtrl)

    poConPV = cmds.parentConstraint(pvSpaceLoc, pvLoc, mo = False, n = f"{prefixSide}pv_SpaceSwitch{suffix[10]}")[0]
    
    cmds.addAttr(switch, ln = "Pole_Vector_Follow", at = "enum", en = " World : Hand ", k = True)

    driverPV = f"{switch}.Pole_Vector_Follow"

    drivenPV = f"{poConPV}.{prefixSide}arm_pv_Space_LOCW0"

    cmds.setDrivenKeyframe(drivenPV, at = 'switchAttr', cd = driverPV, dv = 0, v = 0)
    cmds.setDrivenKeyframe(drivenPV, at = 'switchAttr', cd = driverPV, dv = 1, v = 1)




    #############################################################################

    #mittens visibilitity

    #############################################################################

    '''cmds.addAttr(switch, ln = 'Visibility', at = "enum", en = "____________", k = True)


    mittVis = cmds.addAttr(switch, at = "bool", ln = f"{prefixSide}mitten_VIS", k = True, dv = True)

    mitten = f"{prefixSide}mitten_GEO"
    hand = f"{prefixSide}hand_GEO"

    cmds.setDrivenKeyframe(f"{mitten}.visibility", cd = f"{switch}.{prefixSide}mitten_VIS", dv = 0, v = 0)
    cmds.setDrivenKeyframe(f"{mitten}.visibility", cd = f"{switch}.{prefixSide}mitten_VIS", dv = 1, v = 1)

    cmds.setDrivenKeyframe(f"{hand}.visibility", cd = f"{switch}.{prefixSide}mitten_VIS", dv = 0, v = 1)
    cmds.setDrivenKeyframe(f"{hand}.visibility", cd = f"{switch}.{prefixSide}mitten_VIS", dv = 1, v = 0)'''

    ##############################################################################

    #squash and stretch

    ##############################################################################
    startJnt = cmds.xform(ikJoints[0], q = True, ws = True, t = True)
    midJnt = cmds.xform(ikJoints[1], q = True, ws = True, t = True)
    endJnt = cmds.xform(ikJoints[2], q = True, ws = True, t = True)

    a1 = cmds.curve(d = 1, ep = [startJnt, midJnt], n = f"{prefixSide}arm_a1Curve")
    a2 = cmds.curve(d = 1, ep = [midJnt, endJnt], n = f"{prefixSide}arm_a2Curve")
    b =  cmds.curve(d = 1, ep = [startJnt, endJnt], n = f"{prefixSide}arm_bCurve")

    cmds.select(f"{b}.cv[1]")

    ikCluster = cmds.cluster(n = f"{prefixSide}ikStretch")

    cmds.setAttr(f"{ikCluster[0]}.relative", 1)

    a1ci = cmds.shadingNode('curveInfo', au = True)
    cmds.connectAttr(f"{a1}.worldSpace[0]", f"{a1ci}.inputCurve")
    a2ci = cmds.shadingNode('curveInfo', au = True)
    cmds.connectAttr(f"{a2}.worldSpace[0]", f"{a2ci}.inputCurve")
    bci = cmds.shadingNode('curveInfo', au = True)
    cmds.connectAttr(f"{b}.worldSpace[0]", f"{bci}.inputCurve")

    #nodeshti
    pma = cmds.shadingNode('plusMinusAverage', au = True, n = f"{prefixSide}Stretch_PMA")
    cmds.connectAttr(f"{a1ci}.arcLength", f"{pma}.input1D[0]")
    cmds.connectAttr(f"{a2ci}.arcLength", f"{pma}.input1D[1]")

    md = cmds.shadingNode('multiplyDivide', au = True, n = f"{prefixSide}Stretch_MD")
    cmds.setAttr(f"{md}.operation", 2)
    cmds.connectAttr(f"{bci}.arcLength", f"{md}.input1X")
    cmds.connectAttr(f"{pma}.output1D", f"{md}.input2X")

    cnd = cmds.shadingNode('condition', au = True, n = f"{prefixSide}Stretch_CND")
    cmds.setAttr(f"{cnd}.operation", 3) 
    cmds.setAttr (f"{cnd}.secondTerm", 1)
    cmds.setAttr (f"{cnd}.colorIfFalseR", 1)
    cmds.connectAttr(f"{md}.outputX", f"{cnd}.colorIfTrueR")
    cmds.connectAttr(f"{md}.outputX", f"{cnd}.firstTerm")

    cmds.connectAttr(f"{cnd}.outColorR", f"{ikJoints[0]}.scaleX")
    cmds.connectAttr(f"{cnd}.outColorR", f"{ikJoints[1]}.scaleX")

    cmds.parent(ikCluster, ikGrp)
    clusterpocon = cmds.pointConstraint(ikCtrl, ikCluster, mo = True, n = f"{prefixSide}ikCluster{suffix[10]}")[0]

    cmds.addAttr(switch, ln = 'IK_Stretch', at = "enum", en = "____________", k = True)

    stretch = cmds.addAttr(switch, at = 'bool', ln = f"{prefixSide}Stretch", k = True, dv = 1)

    
    cmds.setDrivenKeyframe(f"{clusterpocon}.{ikCtrl}W0", cd = f"{switch}.{prefixSide}Stretch", dv = 0, v = 0)
    cmds.setDrivenKeyframe(f"{clusterpocon}.{ikCtrl}W0", cd = f"{switch}.{prefixSide}Stretch", dv = 1, v = 1)

    curveGrp = cmds.group(a1, a2, b, n = f"{prefixSide}armScaleCurves{suffix[7]}", p = ikGrp)
    cmds.hide(curveGrp, ikCluster)