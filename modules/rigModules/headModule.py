import maya.cmds as cmds # pyright: ignore[reportMissingImports] 
from autoRigger.utils import shapes, config

#Creating lists for later use
def headBuild(neckOrder):

    prefix = config.prefix
    suffix = config.suffix
    
    joints = ['neckJA', 'headJA', 'jawJA']
    eyes = ['eyeJA']

    #head + neck + Jaw fk setup
    fkLocs = []
    fkCtrls = []

    fkCount = 0
    alljoints =[]

    for joint in joints: 
        jnt = f"{prefix['center']}{joint}{suffix['joint']}"
        alljoints.append(jnt)

    config.setRotationOrder(alljoints, neckOrder)

    for joint in joints: 
        fkLoc = cmds.spaceLocator(n = f"{prefix['center']}{joint}{suffix['locator']}")[0]
        fkLocs.append(fkLoc)
        config.setRotationOrder([fkLoc], neckOrder)
        

        ctrlName = f"{prefix['center']}{joint}{suffix['control']}"

        if "jaw" in joint:
            jawCtrl = shapes.oneWayArrowCtrl(name=ctrlName, size=0.75)
            fkCtrl = jawCtrl
            shape = cmds.listRelatives(fkCtrl, shapes=True, type="nurbsCurve")[0]
            cvs = cmds.ls(shape + ".cv[*]", fl=True)
            cmds.xform(cvs, t=(0, 10, -4), r=True, os=True)
            cmds.xform(cvs, ro=(90, 90, -30), r=True, os=True)
            

        elif "head" in joint:
            headCtrl = cmds.circle(n=ctrlName, r=10, nr=(1,0,0))[0]
            fkCtrl = headCtrl
            shape = cmds.listRelatives(fkCtrl, shapes=True, type="nurbsCurve")[0]
            cvs = cmds.ls(shape + ".cv[*]", fl=True)
            cmds.xform(cvs, t=(20,0,0), r=True, os=True)

        elif "neck" in joint:
            neckCtrl = cmds.circle(n=ctrlName, r=10, nr=(1,0,0))[0]
            fkCtrl = neckCtrl
            shape = cmds.listRelatives(fkCtrl, shapes=True, type="nurbsCurve")[0]
            cvs = cmds.ls(shape + ".cv[*]", fl=True)
            cmds.xform(cvs, t=(3,0,0), r=True, os=True)
        
        config.setRotationOrder([fkCtrl], neckOrder)

        fkCtrls.append(fkCtrl)

        cmds.parent(fkCtrl, fkLoc)
        cmds.delete(cmds.parentConstraint((f"{prefix['center']}{joint}{suffix['joint']}"), fkLoc, mo = False))

        if 'neck' in joint:
            cmds.parentConstraint(fkCtrl,(f"{prefix['center']}{joint}{suffix['joint']}"), n = f"{joint}{suffix['parentCon']}", mo = True)

        else: 
            cmds.orientConstraint(fkCtrl,(f"{prefix['center']}{joint}{suffix['joint']}"), n = f"{joint}{suffix['orientCon']}", mo = True)
        
        if fkCount > 0:
            cmds.parent(fkLocs[fkCount], fkCtrls[fkCount-1])

        fkCount =  fkCount + 1

    #Eye setup

    lEyeJnt = f"{prefix['left']}{eyes[0]}{suffix['joint']}"
    rEyeJnt = f"{prefix['right']}{eyes[0]}{suffix['joint']}"

    
    lEyeCtrl = cmds.circle(n = lEyeJnt.replace('JNT', 'CTRL'), r = 2, nr = (1,0,0))[0]
    rEyeCtrl = cmds.circle(n = rEyeJnt.replace('JNT', 'CTRL'), r = 2, nr = (1,0,0))[0]
    eyectrl = shapes.eyeCtrl(name = f"{prefix['center']}eyes{suffix['control']}", size = 6)

    cmds.delete(cmds.parentConstraint(lEyeJnt, lEyeCtrl, mo = False))
    cmds.delete(cmds.parentConstraint(rEyeJnt, rEyeCtrl, mo = False))

    cmds.xform(lEyeCtrl, t = (0, 0, 15), r = True)
    cmds.xform(rEyeCtrl, t = (0, 0, 15), r = True)

    cmds.delete(cmds.parentConstraint(rEyeCtrl, eyectrl, mo = False))

    cmds.setAttr(f"{eyectrl}.translateX", 0)

    cmds.makeIdentity(lEyeCtrl, rEyeCtrl, apply = True, t = True, r = True)

    cmds.parent(lEyeCtrl, rEyeCtrl, eyectrl)

    cmds.aimConstraint(lEyeCtrl, lEyeJnt, n = f"{prefix['left']}{eyes[0]}{suffix['aimCon']}", mo = True)
    cmds.aimConstraint(rEyeCtrl, rEyeJnt, n = f"{prefix['right']}{eyes[0]}{suffix['aimCon']}", mo = True)

    #parents to the headctrl
    
    cmds.parent(eyectrl, headCtrl)

    cmds.makeIdentity(eyectrl, apply = True, t = True, r = True)

###############################
#spaceswitching eyes
###############################

    headJoint = headCtrl.replace('CTRL', 'JNT')
    headLoc = headCtrl.replace('CTRL', 'LOC')

    eyesWS = cmds.spaceLocator(n = f"{eyes[0]}_worldSpace{suffix['locator']}")
    cmds.delete(cmds.parentConstraint(eyectrl, eyesWS, mo = False))

    eyesLS = cmds.duplicate(eyesWS, n =  f"{eyes[0]}_localSpace{suffix['locator']}")

    eyesLoc = cmds.duplicate(eyesWS, n =  f"{eyes[0]}{suffix['locator']}")

    cmds.parent(eyectrl, eyesLoc)

    cmds.parent(eyesLS, headCtrl)

    cmds.addAttr(eyectrl, at = "enum", en = "Local Space: World Space", k = True, ln = "Space_Switch")

    paCon = cmds.parentConstraint(eyesLS, eyesWS, eyesLoc, mo = False, n = f"{eyectrl}{suffix['parentCon']}")[0]

    cmds.makeIdentity(eyectrl, a = True, t = True)

    #SDKs 
    driver = f"{eyectrl}.Space_Switch"

    drivenWS = f"{paCon}.{eyesWS[0]}W1"
    drivenLS = f"{paCon}.{eyesLS[0]}W0"

    cmds.setDrivenKeyframe(drivenLS, at = 'switchAttr', cd = driver, dv = 0, v = 1)
    cmds.setDrivenKeyframe(drivenLS, at = 'switchAttr', cd = driver, dv = 1, v = 0)
    cmds.setDrivenKeyframe(drivenWS, at = 'switchAttr', cd = driver, dv = 0, v = 0)
    cmds.setDrivenKeyframe(drivenWS, at = 'switchAttr', cd = driver, dv = 1, v = 1)

#spaceswitching head

    #removeHead

    #unparent from the neck
    cmds.parent(headLoc, w = True)

    #duplicate the headLoc n delete the children x2
    dupeWS = cmds.spaceLocator(
        n=f"{prefix['center']}{joints[1]}_worldSpace{suffix['locator']}"
    )[0]

    cmds.matchTransform(dupeWS, headLoc, pos=True, rot=True)

    dupeLS = cmds.spaceLocator(
        n=f"{prefix['center']}{joints[1]}_localSpace{suffix['locator']}"
    )[0]
    cmds.matchTransform(dupeLS, headLoc, pos=True, rot=True)
    
    #Attribute under OG head

    cmds.addAttr(headCtrl, ln = 'Spaces', at = 'enum', en = "__________ ", k = True)

    cmds.addAttr(headCtrl, at = "enum", en = "Local Space: World Space", k = True, ln = "Space_Switch" )

    cmds.parent(dupeLS, neckCtrl)

    oCon = cmds.orientConstraint(dupeLS, dupeWS, headLoc, mo = False, n = f"{headLoc}{suffix['orientCon']}")[0]

    #SET DRIVEN KEYYYSS

    driver = f"{headCtrl}.Space_Switch"

    drivenWS = f"{oCon}.{dupeWS}W1"
    drivenLS = f"{oCon}.{dupeLS}W0"

    cmds.setDrivenKeyframe(drivenLS, at = 'switchAttr', cd = driver, dv = 0, v = 1)
    cmds.setDrivenKeyframe(drivenLS, at = 'switchAttr', cd = driver, dv = 1, v = 0)
    cmds.setDrivenKeyframe(drivenWS, at = 'switchAttr', cd = driver, dv = 0, v = 0)
    cmds.setDrivenKeyframe(drivenWS, at = 'switchAttr', cd = driver, dv = 1, v = 1)


    #parent the head jnt to the og loc

    cmds.pointConstraint(headLoc, headJoint, mo = True, n = f"{joints[0]}{suffix['pointCon']}") 

    neckLoc = cmds.listRelatives(neckCtrl, parent = True)

    cmds.parent(headLoc, neckLoc)

    eyegrp = cmds.group(eyesLoc, eyesWS[0], n = "eyes_GRP")
    cmds.group(headLoc,dupeWS, eyegrp, n = f"head{suffix['group']}")

    print(f"[Head Builder] : built head")
