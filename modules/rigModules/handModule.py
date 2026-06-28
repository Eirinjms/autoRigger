import maya.cmds as cmds # pyright: ignore[reportMissingImports] 
import autoRigger.config as config
import string


import importlib
importlib.reload(config)

def rotationOrder(item):
    cmds.setAttr(f"{item}.rotateOrder", config.rotationOrder.ZYX.value) 

def build(side):
    size = config.bipedal
    suffix = config.suffix
    attrs = config.attrs
    fingers = ['indexFng', 'middleFng', 'pinkyFng', 'thumb']
    
    wristJoint = f"{side}armJD_JNT"
    wrist = cmds.spaceLocator(n = f"{side}hand{suffix['locator']}")
    cmds.parentConstraint(wristJoint, wrist, mo = False, n = f"{side}hand{suffix['parentCon']}")

    for fng in fingers:
        index = string.ascii_uppercase[:3]
        fingerjoints = [f"{side}{fng}J{i}{suffix['joint']}" for i in index]

        fkLocs = []
        fkGrps = []
        fkCtrls = []

        for count, joint in enumerate(fingerjoints):
            fkLoc = cmds.spaceLocator(n = joint.replace(suffix['joint'], suffix['locator']))[0]
            rotationOrder(fkLoc)
            fkLocs.append(fkLoc)

            OffsetGrp = cmds.group(n = joint.replace(suffix['joint'], suffix['offsetGrp']), em = True)
            rotationOrder(OffsetGrp)
            fkGrps.append(OffsetGrp)

            if 'thumbJA' in joint:
                fkCtrl = cmds.circle(n = joint.replace(suffix['joint'], suffix['control']), r = size['fingers'] + 1, nr = (1,0,0))[0]
                rotationOrder(fkCtrl)
                fkCtrls.append(fkCtrl)
            else: 
                fkCtrl = cmds.circle(n = joint.replace(suffix['joint'], suffix['control']), r = size['fingers'], nr = (1,0,0))[0]
                rotationOrder(fkCtrl)
                fkCtrls.append(fkCtrl)
                
            cmds.parent(fkCtrl, OffsetGrp)
            cmds.parent(OffsetGrp, fkLoc)
            cmds.delete(cmds.parentConstraint(joint, fkLoc, mo = False))

            cmds.orientConstraint(fkCtrl, joint, n = joint.replace(suffix['joint'], suffix['orientCon']), mo = False)
                
            if count >0:
                cmds.parent(fkLocs[count], fkCtrls[count-1])

            if 'JA' in fkLoc: 
                cmds.parent(fkLoc, wrist)
            else: 
                continue

    ##################################################################

    #set driven keys

    ##################################################################

    fistCtrl = cmds.circle(n = f"{side}fist{suffix['control']}", r = 5, nr = (0,1,0))[0]
    cmds.delete(cmds.parentConstraint(f"{side}{fingers[1]}JA{suffix['joint']}", fistCtrl, mo = False))
    cmds.addAttr(fistCtrl, ln = 'FIST', at = 'enum', en = "__________ ", k = True)


    if side == 'L':
        cmds.xform(fistCtrl, t = (5,0,0), ws = True, r = True)

    else:
        cmds.xform(fistCtrl, t = (-5,0,0), ws = True, r = True)


    #fist ctrl
    cmds.makeIdentity(fistCtrl, a = True, t = True, r = True, s = True)

    cmds.addAttr(fistCtrl, ln = 'Fist_Curl', at = 'float', min = -1, max = 1, dv = 0, k = True)

    curlOffsetGrp = cmds.ls(f"{side}*{suffix['offsetGrp']}")

    driver = f"{fistCtrl}.Fist_Curl"


    for grp in curlOffsetGrp:
        cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = 0, v = 0)

        if "thumbJA" in grp: 
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = 1, v = 20) 
            cmds.setDrivenKeyframe(grp, at = 'rotateY', cd = driver, dv = 1, v = 20)   
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = -1, v = -30)
            cmds.setDrivenKeyframe(grp, at = 'rotateY', cd = driver, dv = 0, v = 0) 

        elif "thumbJB" in grp: 
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = 1, v = 50) 
            cmds.setDrivenKeyframe(grp, at = 'rotateY', cd = driver, dv = 1, v = 10)   
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = -1, v = -30)
            cmds.setDrivenKeyframe(grp, at = 'rotateY', cd = driver, dv = 0, v = 0) 

        elif "thumbJC" in grp: 
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = 1, v = 60) 
            cmds.setDrivenKeyframe(grp, at = 'rotateY', cd = driver, dv = 1, v = -20)   
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = -1, v = -30)
            cmds.setDrivenKeyframe(grp, at = 'rotateY', cd = driver, dv = 0, v = 0) 

        else:
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = 1, v = 80)    
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = -1, v = -40)    


    #SPLAYED FINGERS
    ##################################################################


    cmds.addAttr(fistCtrl, ln = 'Splayed_Fingers', at = 'float', min = -1, max = 1, dv = 0, k = True)

    curlOffsetGrp = cmds.ls(f"{side}*{suffix['offsetGrp']}")

    driver = f"{fistCtrl}.Splayed_Fingers"


    for grp in curlOffsetGrp:
        cmds.setDrivenKeyframe(grp, at = 'rotateY', cd = driver, dv = 0, v = 0)
        cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = 0, v = 0)

        if "thumbJA" in grp: 
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = 1, v = -20)  
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = -1, v = 20)
        elif "indexFngJA" in grp:
            cmds.setDrivenKeyframe(grp, at = 'rotateY', cd = driver, dv = 1, v = 20) 
            cmds.setDrivenKeyframe(grp, at = 'rotateY', cd = driver, dv = -1, v = -22)     

        elif "middleFngJA" in grp:
            cmds.setDrivenKeyframe(grp, at = 'rotateY', cd = driver, dv = 1, v = 10)
            cmds.setDrivenKeyframe(grp, at = 'rotateY', cd = driver, dv = -1, v = -10)
        
        elif "ringFngJA" in grp:
            cmds.setDrivenKeyframe(grp, at = 'rotateY', cd = driver, dv = 1, v = -10)
            cmds.setDrivenKeyframe(grp, at = 'rotateY', cd = driver, dv = -1, v = 0)

        elif "pinkyFngJA" in grp:
            cmds.setDrivenKeyframe(grp, at = 'rotateY', cd = driver, dv = 1, v = -20)
            cmds.setDrivenKeyframe(grp, at = 'rotateY', cd = driver, dv = -1, v = 12)  

    ##################################################################
    #inbetweener

    ##################################################################

    cmds.addAttr(fistCtrl, ln = 'INDIV_FINGERS', at = 'enum', en = "__________ ", k = True)

    ##################################################################

    #individual fingers

    ##################################################################
    #finger 5 also known as thumb
    cmds.addAttr(fistCtrl, ln = 'Thumb_Bend', at = 'float', min = -1, max = 1, dv = 0, k = True)

    curlOffsetGrp = cmds.ls(f"{side}*{suffix['offsetGrp']}")

    driver = f"{fistCtrl}.Thumb_Bend"


    for grp in curlOffsetGrp:
        if "thumb" in grp:
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = 0, v = 0)
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = 1, v = 20)
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = -1, v = -40)   


    #individual finger bend 1

    cmds.addAttr(fistCtrl, ln = 'Index_Finger_Bend', at = 'float', min = -1, max = 1, dv = 0, k = True)

    curlOffsetGrp = cmds.ls(f"{side}*{suffix['offsetGrp']}")

    driver = f"{fistCtrl}.Index_Finger_Bend"


    for grp in curlOffsetGrp:
        if "indexFng" in grp:
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = 0, v = 0)
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = 1, v = 50)
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = -1, v = -20)    


    #individual finger bend 2

    cmds.addAttr(fistCtrl, ln = 'Middle_Finger_Bend', at = 'float', min = -1, max = 1, dv = 0, k = True)

    curlOffsetGrp = cmds.ls(f"{side}*{suffix['offsetGrp']}")

    driver = f"{fistCtrl}.Middle_Finger_Bend"


    for grp in curlOffsetGrp:
        if "middleFng" in grp:
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = 0, v = 0)
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = 1, v = 50)
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = -1, v = -20)
            

    #individual finger bend 3

    cmds.addAttr(fistCtrl, ln = 'Ring_Finger_Bend', at = 'float', min = -1, max = 1, dv = 0, k = True)

    curlOffsetGrp = cmds.ls(f"{side}*{suffix['offsetGrp']}")

    driver = f"{fistCtrl}.Ring_Finger_Bend"


    for grp in curlOffsetGrp:
        if "ringFng" in grp:
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = 0, v = 0)
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = 1, v = 50)
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = -1, v = -20)    

    #individual finger bend 4

    cmds.addAttr(fistCtrl, ln = 'Pinky_Finger_Bend', at = 'float', min = -1, max = 1, dv = 0, k = True)

    curlOffsetGrp = cmds.ls(f"{side}*{suffix['offsetGrp']}")

    driver = f"{fistCtrl}.Pinky_Finger_Bend"


    for grp in curlOffsetGrp:
        if "pinkyFng" in grp:
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = 0, v = 0)
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = 1, v = 50)
            cmds.setDrivenKeyframe(grp, at = 'rotateZ', cd = driver, dv = -1, v = -20)    

                
                

    #finalCleanup

    cmds.parentConstraint(wrist[0], fistCtrl, mo=True, n = f"{side}fist{suffix['parentCon']}")

    for attr in attrs: 
        cmds.setAttr(f"{fistCtrl}.{attr}", l = True, k = False, cb = False)








