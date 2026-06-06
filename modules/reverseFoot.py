import maya.cmds as cmds
import autoRigger.shapes as shapes
import autoRigger.naming as naming
import autoRigger.sizes as sizes
import importlib

importlib.reload(shapes)

def build(side, ikHandle, ikCtrl, switch, joints):
    size = sizes.bipedal
    suffix = naming.suffix
    prefix = naming.prefix
    locs = ['frontFoot', 'backOfHeel', 'innerSideFoot', 'outerSideFoot']
    con = ["_paCON", '_poCON', '_oCON', '_aimCon']

    toeJoints = ['legJD', 'legJEnd']
    for jnt in toeJoints:
        joints.append(jnt)

    print(joints)



#########################
#Reverse foot ctrl setup
#########################

    #pivot LOCS (alr existign in scene)
    frontLoc = f"{side}{locs[0]}{suffix['locator']}"
    backLoc = f"{side}{locs[1]}{suffix['locator']}"
    innerLoc = f"{side}{locs[2]}{suffix['locator']}"
    outerLoc = f"{side}{locs[3]}{suffix['locator']}"

    ankleJnt = f"{side}{joints[2]}{suffix['joint']}"
    ballJnt = f"{side}{joints[3]}{suffix['joint']}"
    toeJnt = f"{side}{joints[4]}{suffix['joint']}"

    ballLoc = cmds.spaceLocator(n = f"{side}{joints[3]}{suffix['locator']}")[0]
    toeLoc = cmds.spaceLocator(n = f"{side}{joints[4]}{suffix['locator']}")[0]

    cmds.matchTransform(ballLoc, ballJnt, pos = True, rot = True)
    cmds.matchTransform(toeLoc, ballJnt, pos = True, rot = True)
    
    #REMOVE WHEN USED FOR CHARACTERS WITH STRAIGHT FEET (ADD AS A CHECKBOX?)
    cmds.xform(ballLoc, toeLoc, ro = (0,10,0), os = True)

    #Delete rotation valeus from locs 
    cmds.makeIdentity(ballLoc, toeLoc, apply = True, r = True)

    #unparent the OG ikh from the chain
    cmds.parent(ikHandle,  w = True)
    cmds.delete(f"{side}{joints[0]}{naming.fkik[1]}{suffix['pointCon']}")

    #IKS
    ballIk = cmds.ikHandle(n = f"{side}{joints[3]}{suffix['ikHandle']}", sj = ankleJnt, ee = ballJnt)[0]
    toeIk = cmds.ikHandle(n = f"{side}{joints[4]}{suffix['ikHandle']}", sj = ballJnt, ee = toeJnt)[0]

    #Hierarchy
    cmds.parent(toeIk, toeLoc)
    cmds.parent(ikHandle, ballLoc)
    cmds.parent(ballIk, ballLoc, toeLoc, innerLoc)


#########################
#CTRLS
#########################

    sliderCtrl = shapes.squareCtrl(name = f"{side}foot{suffix['control']}", size = 1)
    borderCtrl = shapes.squareCtrl(name = f"{side}footBorder{suffix['control']}", size = 3)

    
    cmds.transformLimits(sliderCtrl, tz = (-2, 2), tx = (-2, 2))
    cmds.transformLimits(sliderCtrl, etz = (True, True), etx = (True, True))


    footCtrlGrp = cmds.group(sliderCtrl, borderCtrl, n = f"{side}foot{suffix['control']}{suffix['group']}")

    cmds.matchTransform(footCtrlGrp, frontLoc, pos = True, rot = True)    

    cmds.xform(footCtrlGrp, t = (1,0,7), r = True)


    #SDKs for "hiding iks"
    driver = f"{switch}.FKIK_Switch"


    cmds.setDrivenKeyframe(ballIk, toeIk, at = 'ikBlend', cd = driver, dv = 0, v = 0)
    cmds.setDrivenKeyframe(ballIk, toeIk, at = 'ikBlend', cd = driver, dv = 1, v = 1)  
        
    #SDKs for the lil ctrl guy
    driverX = f"{sliderCtrl}.translateX"
    driverZ = f"{sliderCtrl}.translateZ"
    
    if side.startswith("L"):
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



    revFootGrp = cmds.group(backLoc, n = f"{side}revFoot{suffix['group']}")
    cmds.parent(revFootGrp, footCtrlGrp, ikCtrl)
