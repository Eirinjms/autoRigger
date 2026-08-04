import maya.cmds as cmds # pyright: ignore[reportMissingImports] 
import autoRigger.utils.shapes as shapes
import autoRigger.utils.config as config
import importlib

importlib.reload(shapes)

def build(side, ikHandle, ikCtrl, switch, joints):
    '''
    Builds a reverse foot system based on existing locators.
        
    Parameters: 
        passed in from limbModule
    
    '''
    size = config.bipedal
    attrs = config.attrs
    suffix = config.suffix
    prefix = config.prefix
    locs = ['frontFoot', 'backOfHeel', 'innerSideFoot', 'outerSideFoot']
    
    #pivot LOCS (alr existign in scene)
    frontLoc = f"{side}{locs[0]}{suffix['locator']}"
    backLoc = f"{side}{locs[1]}{suffix['locator']}"
    innerLoc = f"{side}{locs[2]}{suffix['locator']}"
    outerLoc = f"{side}{locs[3]}{suffix['locator']}"

    ankleJnt = joints[-1]
    ballJnt = cmds.listRelatives(ankleJnt, children = True)[0]
    toeJnt = cmds.listRelatives(ballJnt, children = True)[0]


    ballLoc = cmds.spaceLocator(n = ballJnt.replace(suffix["joint"], suffix["locator"]))[0]
    toeLoc = cmds.spaceLocator(n = toeJnt.replace(suffix["joint"], suffix["locator"]))[0]

    cmds.matchTransform(ballLoc, ballJnt, pos = True, rot = True)
    cmds.matchTransform(toeLoc, ballJnt, pos = True, rot = True)
    
    #REMOVE WHEN USED FOR CHARACTERS WITH STRAIGHT FEET (ADD AS A CHECKBOX?)
    #cmds.xform(ballLoc, toeLoc, ro = (0,10,0), os = True)

    #Delete rotation valeus from locs 
    cmds.makeIdentity(ballLoc, toeLoc, apply = True, r = True)

    #unparent the OG ikh from the chain
    cmds.parent(ikHandle,  w = True)
    pointCon = joints[0].replace(
                suffix["joint"],
                f"{config.fkik['ik']}{suffix['pointCon']}")
    cmds.delete(pointCon)

    #IKS
    ballIk = cmds.ikHandle(n = ballJnt.replace(suffix["joint"], suffix["ikHandle"]), sj = ankleJnt, ee = ballJnt)[0]
    toeIk = cmds.ikHandle(n = toeJnt.replace(suffix["joint"], suffix["ikHandle"]), sj = ballJnt, ee = toeJnt)[0]

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

    #cmds.xform(footCtrlGrp, t = (1,0,7), r = True)


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

    for attr in attrs: 
        cmds.setAttr(f"{borderCtrl}.{attr}", l = True, k = False, cb = False)

    attrsNew = attrs[:]
    attrsX = ['tx', 'tz']
    for obj in attrsX:
        attrsNew.remove(obj)

    for attr in attrsNew: 
        cmds.setAttr(f"{sliderCtrl}.{attr}", l = True, k = False, cb = False)



    revFootGrp = cmds.group(backLoc, n = f"{side}revFoot{suffix['group']}")
    cmds.parent(revFootGrp, footCtrlGrp, ikCtrl)

    print(f"\n [ReverseFeet Builder] : built for {side} side \n ")
