import maya.cmds as cmds
import autoRigTool.shapes as shapes
import autoRigTool.naming as naming
import autoRigTool.sizes as sizes
import importlib

importlib.reload(shapes)

def build(side, ikHandle, ikCtrl, switch):
    suffix = naming.suffix
    prefix = naming.prefix
    joints = ['legJC', 'legJD', 'legJEnd', 'ball', 'toe']
    locs = ['frontFoot', 'backOfHeel', 'innerSideFoot', 'outerSideFoot']
    con = ["_paCON", '_poCON', '_oCON', '_aimCon']

    prefixSide = f"{side}_"

#########################
#Reverse foot ctrl setup
#########################

    #pivot LOCS (alr existign in scene)
    frontLoc = f"{prefixSide}{locs[0]}{suffix['locator']}"
    backLoc = f"{prefixSide}{locs[1]}{suffix['locator']}"
    innerLoc = f"{prefixSide}{locs[2]}{suffix['locator']}"
    outerLoc = f"{prefixSide}{locs[3]}{suffix['locator']}"

    ankleJnt = f"{prefixSide}{joints[0]}{suffix['joint']}"
    ballJnt = f"{prefixSide}{joints[1]}{suffix['joint']}"
    toeJnt = f"{prefixSide}{joints[2]}{suffix['joint']}"

    ballLoc = cmds.spaceLocator(n = f"{prefixSide}{joints[3]}{suffix['locator']}")[0]
    toeLoc = cmds.spaceLocator(n = f"{prefixSide}{joints[4]}{suffix['locator']}")[0]
    cmds.delete(cmds.parentConstraint(ballJnt, ballLoc, mo = False))
    cmds.delete(cmds.parentConstraint(ballJnt, toeLoc, mo = False))
    
    #REMOVE WHEN USED FOR CHARACTERS WITH STRAIGHT FEET
    #cmds.xform(ballLoc, toeLoc, ro = (0,10,0), os = True)

    #Delete rotation valeus from locs 
    cmds.makeIdentity(ballLoc, toeLoc, apply = True, r = True)

    #unparent the OG ikh from the chain
    cmds.parent(ikHandle,  w = True)
    cmds.delete(f"{ikHandle.replace('IKH', 'IK')}{con[1]}")

    #IKS
    ballIk = cmds.ikHandle(n = f"{prefixSide}{joints[3]}{suffix['ikHandle']}", sj = ankleJnt, ee = ballJnt)[0]
    toeIk = cmds.ikHandle(n = f"{prefixSide}{joints[4]}{suffix['ikHandle']}", sj = ballJnt, ee = toeJnt)[0]

    #Hierarchy
    cmds.parent(toeIk, toeLoc)
    cmds.parent(ikHandle, ballLoc)
    cmds.parent(ballIk, ballLoc, toeLoc, innerLoc)


#########################
#CTRLS
#########################

    sliderCtrl = shapes.squareCtrl(name = f"{prefixSide}foot{suffix['control']}", size = 1)
    borderCtrl = shapes.squareCtrl(name = f"{prefixSide}footBorder{suffix['control']}", size = 3)

    
    cmds.transformLimits(sliderCtrl, tz = (-2, 2), tx = (-2, 2))
    cmds.transformLimits(sliderCtrl, etz = (True, True), etx = (True, True))


    footCtrlGrp = cmds.group(sliderCtrl, borderCtrl, n = f"{prefixSide}foot{suffix['control']}{suffix['group']}")

    cmds.delete(cmds.parentConstraint(frontLoc,footCtrlGrp, mo = False))

    cmds.xform(footCtrlGrp, t = (1,0,7), r = True)


    #SDKs for "hiding iks"
    driver = f"{switch}.FKIK_Switch"


    cmds.setDrivenKeyframe(ballIk, toeIk, at = 'ikBlend', cd = driver, dv = 0, v = 0)
    cmds.setDrivenKeyframe(ballIk, toeIk, at = 'ikBlend', cd = driver, dv = 1, v = 1)  
        
    #SDKs for the lil ctrl guy
    driverX = f"{sliderCtrl}.translateX"
    driverZ = f"{sliderCtrl}.translateZ"
    
    if side == 'L':
        cmds.setDrivenKeyframe(frontLoc, at = 'rotateX', cd = driverZ, dv = 2, v = 70)
        cmds.setDrivenKeyframe(frontLoc, at = 'rotateX', cd = driverZ, dv = 0, v = 0)
        cmds.setDrivenKeyframe(backLoc, at = 'rotateX', cd = driverZ, dv = -2, v = -70)
        cmds.setDrivenKeyframe(backLoc, at = 'rotateX', cd = driverZ, dv = 0, v = 0)

        cmds.setDrivenKeyframe(innerLoc, at = 'rotateZ', cd = driverX, dv = -2, v =70)
        cmds.setDrivenKeyframe(innerLoc, at = 'rotateZ', cd = driverX, dv = 0, v = 0)
        cmds.setDrivenKeyframe(outerLoc, at = 'rotateZ', cd = driverX, dv = 2, v = -70)  
        cmds.setDrivenKeyframe(outerLoc, at = 'rotateZ', cd = driverX, dv = 0, v = 0)  

    else: 
        cmds.setDrivenKeyframe(frontLoc, at = 'rotateX', cd = driverZ, dv = 2, v = 70)
        cmds.setDrivenKeyframe(frontLoc, at = 'rotateX', cd = driverZ, dv = 0, v = 0)
        cmds.setDrivenKeyframe(backLoc, at = 'rotateX', cd = driverZ, dv = -2, v = -70)
        cmds.setDrivenKeyframe(backLoc, at = 'rotateX', cd = driverZ, dv = 0, v = 0)

        cmds.setDrivenKeyframe(innerLoc, at = 'rotateZ', cd = driverX, dv = 2, v = -70)
        cmds.setDrivenKeyframe(innerLoc, at = 'rotateZ', cd = driverX, dv = 0, v = 0)
        cmds.setDrivenKeyframe(outerLoc, at = 'rotateZ', cd = driverX, dv = -2, v = 70)  
        cmds.setDrivenKeyframe(outerLoc, at = 'rotateZ', cd = driverX, dv = 0, v = 0)  

    #roll attr on the ik ctrl

    cmds.addAttr(ikCtrl, ln = 'FOOT_CTRLS', at = "enum", en = "____________", k = True)

    cmds.addAttr(ikCtrl, ln = "Heel_Lift", at = "float", min = 0, max = 1, dv = 0, k = True)
    cmds.addAttr(ikCtrl, ln = "Toe_Lift", at = "float", min = 0, max = 1, dv = 0, k = True)

    driverToe = f"{ikCtrl}.Toe_Lift"
    driverHeel = f"{ikCtrl}.Heel_Lift"

    cmds.setDrivenKeyframe(ballLoc, at = 'rotateX', cd = driverHeel, dv = 0, v = 0)
    cmds.setDrivenKeyframe(ballLoc, at = 'rotateX', cd = driverHeel, dv = 1, v = 60)

    cmds.setDrivenKeyframe(toeLoc, at = 'rotateX', cd = driverToe, dv = 0, v = 0)
    cmds.setDrivenKeyframe(toeLoc, at = 'rotateX', cd = driverToe, dv = 1, v = -60)




#########################
#cleanup
#########################

    cmds.hide(ballIk, toeIk)

    attrs = ["tx", "tz", "ty","rx","ry","rz","sx","sy","sz"]

    for attr in attrs: 
        cmds.setAttr(f"{borderCtrl}.{attr}", l = True, k = False, cb = False)

    attrsX = ["ty","rx","ry","rz","sx","sy","sz"]

    for attr in attrsX: 
        cmds.setAttr(f"{sliderCtrl}.{attr}", l = True, k = False, cb = False)



    revFootGrp = cmds.group(backLoc, n = f"{prefixSide}revFoot{suffix['group']}")
    cmds.parent(revFootGrp, footCtrlGrp, ikCtrl)
