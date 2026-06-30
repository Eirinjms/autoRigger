import maya.cmds as cmds # pyright: ignore[reportMissingImports] 
import autoRigger.utils.shapes as shapes

#Creating lists for later use
def headBuild():
    
    suffix = ['_JNT','_LOC', '_CTRL', '_GRP', "_paCON", '_poCON', '_oCON', '_aimCON']
    prefix = ['L_', 'R_', 'C_']
    joints = ['neckJA', 'headJA',]
    eyes = ['eyeJA']

    #head + neck + Jaw fk setup
    fkLocs = []
    fkCtrls = []

    fkCount = 0

    for joint in joints: 
        fkLoc = cmds.spaceLocator(n = (prefix[2]) + joint + (suffix[1]))
        fkLocs.append(fkLoc)
        

        ctrlName = f"{prefix[2]}{joint}{suffix[2]}"

        if "jaw" in joint:
            fkCtrl = shapes.oneWayArrowCtrl(name=ctrlName, size=0.75)
            shape = cmds.listRelatives(fkCtrl, shapes=True, type="nurbsCurve")[0]
            cvs = cmds.ls(shape + ".cv[*]", fl=True)
            cmds.xform(cvs, t=(0, 10, -4), r=True, os=True)
            cmds.xform(cvs, ro=(90, 90, -30), r=True, os=True)
            

        elif "head" in joint:
            fkCtrl = cmds.circle(n=ctrlName, r=10, nr=(1,0,0))[0]
            shape = cmds.listRelatives(fkCtrl, shapes=True, type="nurbsCurve")[0]
            cvs = cmds.ls(shape + ".cv[*]", fl=True)
            cmds.xform(cvs, t=(20,0,0), r=True, os=True)

        else:
            fkCtrl = cmds.circle(n=ctrlName, r=10, nr=(1,0,0))[0]
            shape = cmds.listRelatives(fkCtrl, shapes=True, type="nurbsCurve")[0]
            cvs = cmds.ls(shape + ".cv[*]", fl=True)
            cmds.xform(cvs, t=(3,0,0), r=True, os=True)

        fkCtrls.append(fkCtrl)

        cmds.parent(fkCtrl, fkLoc)
        cmds.delete(cmds.parentConstraint((f"{prefix[2]}{joint}{suffix[0]}"), fkLoc, mo = False))

        if 'neck' in joint:
            cmds.parentConstraint(fkCtrl,(f"{prefix[2]}{joint}{suffix[0]}"), n = joint + (suffix[4]), mo = True)
        else: 
            cmds.orientConstraint(fkCtrl,(f"{prefix[2]}{joint}{suffix[0]}"), n = joint + (suffix[-2]), mo = True)
        
        if fkCount > 0:
            cmds.parent(fkLocs[fkCount], fkCtrls[fkCount-1])

        fkCount =  fkCount + 1

    #Eye setup

    '''lEyeJnt = f"{prefix[0]}{eyes[0]}{suffix[0]}"
    rEyeJnt = f"{prefix[1]}{eyes[0]}{suffix[0]}"

    
    lEyeCtrl = cmds.circle(n = f"{prefix[0]}eyeJA{suffix[2]}", r = 2, nr = (1,0,0))[0]
    rEyeCtrl = cmds.circle(n = f"{prefix[1]}eyeJA{suffix[2]}", r = 2, nr = (1,0,0))[0]
    eyectrl = shapes.eyeCtrl(name = f"{prefix[2]}eyes{suffix[2]}", size = 6)

    cmds.delete(cmds.parentConstraint(lEyeJnt, lEyeCtrl, mo = False))
    cmds.delete(cmds.parentConstraint(rEyeJnt, rEyeCtrl, mo = False))

    cmds.xform(lEyeCtrl, t = (0, 0, 15), r = True)
    cmds.xform(rEyeCtrl, t = (0, 0, 15), r = True)

    cmds.delete(cmds.parentConstraint(rEyeCtrl, eyectrl, mo = False))

    cmds.setAttr(f"{eyectrl}.translateX", 0)

    cmds.makeIdentity(lEyeCtrl, rEyeCtrl, apply = True, t = True, r = True)

    cmds.parent(lEyeCtrl, rEyeCtrl, eyectrl)

    cmds.aimConstraint(lEyeCtrl, lEyeJnt, n = f"{prefix[0]}{eyes[0]}{suffix[-1]}", mo = True)
    cmds.aimConstraint(rEyeCtrl, rEyeJnt, n = f"{prefix[0]}{eyes[0]}{suffix[-1]}", mo = True)
    #parents to the headctrl

    cmds.makeIdentity(eyectrl, apply = True, t = True, r = True)'''

###############################
#spaceswitching eyes
###############################

    head = f"{prefix[2]}{joints[1]}{suffix[1]}"
    headCtrl = f"{prefix[2]}{joints[1]}{suffix[2]}"
    neckCtrl = f"{prefix[2]}{joints[0]}{suffix[2]}"

    '''eyesWS = cmds.spaceLocator(n = f"{eyes[0]}_worldSpace{suffix[1]}")
    cmds.delete(cmds.parentConstraint(eyectrl, eyesWS, mo = False))

    eyesLS = cmds.duplicate(eyesWS, n =  f"{eyes[0]}_localSpace{suffix[1]}")

    eyesLoc = cmds.duplicate(eyesWS, n =  f"{eyes[0]}{suffix[1]}")

    cmds.parent(eyectrl, eyesLoc)

    cmds.parent(eyesLS, headCtrl)

    cmds.addAttr(eyectrl, at = "enum", en = "Local Space: World Space", k = True, ln = "Space_Switch")

    paCon = cmds.parentConstraint(eyesLS, eyesWS, eyesLoc, mo = False, n = f"{eyectrl}{suffix[4]}")[0]

    cmds.makeIdentity(eyectrl, a = True, t = True)

    #SDKs 
    driver = f"{eyectrl}.Space_Switch"

    drivenWS = f"{paCon}.{eyesWS[0]}W1"
    drivenLS = f"{paCon}.{eyesLS[0]}W0"

    cmds.setDrivenKeyframe(drivenLS, at = 'switchAttr', cd = driver, dv = 0, v = 1)
    cmds.setDrivenKeyframe(drivenLS, at = 'switchAttr', cd = driver, dv = 1, v = 0)
    cmds.setDrivenKeyframe(drivenWS, at = 'switchAttr', cd = driver, dv = 0, v = 0)
    cmds.setDrivenKeyframe(drivenWS, at = 'switchAttr', cd = driver, dv = 1, v = 1)'''


###############################
#spaceswitching head
###############################

    #removeHead

    #unparent from the neck
    cmds.parent(head, w = True)

    #duplicate the headLoc n delete the children x2
    dupeWS = cmds.ls(cmds.duplicate(head, n = f"{prefix[2]}{joints[1]}_worldSpace{suffix[1]}"))
    cmds.delete(dupeWS[1])
    dupeLS =  cmds.ls(cmds.duplicate(head, n = f"{prefix[2]}{joints[1]}_localSpace{suffix[1]}"))
    cmds.delete(dupeLS[1])
    
    #Attribute under OG head

    cmds.addAttr(headCtrl, ln = 'Spaces', at = 'enum', en = "__________ ", k = True)

    cmds.addAttr(headCtrl, at = "enum", en = "Local Space: World Space", k = True, ln = "Space_Switch" )

    cmds.parent(dupeLS[0], neckCtrl)

    oCon = cmds.orientConstraint(dupeLS[0], dupeWS[0], head, mo = False, n = f"{head}{suffix[-2]}")[0]

    #SET DRIVEN KEYYYSS

    driver = f"{headCtrl}.Space_Switch"

    drivenWS = f"{oCon}.{dupeWS[0]}W1"
    drivenLS = f"{oCon}.{dupeLS[0]}W0"

    cmds.setDrivenKeyframe(drivenLS, at = 'switchAttr', cd = driver, dv = 0, v = 1)
    cmds.setDrivenKeyframe(drivenLS, at = 'switchAttr', cd = driver, dv = 1, v = 0)
    cmds.setDrivenKeyframe(drivenWS, at = 'switchAttr', cd = driver, dv = 0, v = 0)
    cmds.setDrivenKeyframe(drivenWS, at = 'switchAttr', cd = driver, dv = 1, v = 1)


    #parent the head jnt to the og loc

    cmds.pointConstraint(f"{prefix[2]}{joints[1]}{suffix[0]}", head, mo = True, n = f"{joints[0]}{suffix[5]}") 

    '''cmds.group(head, eyesLoc, dupeWS[0], eyesWS[0], n = f"head{suffix[3]}")
    cmds.group(eyesLoc, eyesWS[0], n = "eyes_GRP")'''


    #Face
    '''eyebrowJnts = ['face_eyebrowJA_tweak','face_eyebrowJB_tweak','face_eyebrowJC_tweak','face_eyebrowJD_tweak', 'face_eyebrowJEnd_tweak', 'face_eyebrowMiddle_tweak']
    eyelidJnts = ['face_eyelidUpperJA', 'face_eyelidLowerJA', 'face_eyeInnerCorner_tweak', 'face_eyeOuterCorner_tweak']
    cheekJnts = ['face_upperCheekJA','face_upperCheekJB','face_midCheekJA']
    noseJnts = ['face_noseTip', 'face_noseCorner', 'face_noseUnder' ]
    lipsufx = ['_tweak', '_root']
    lipRoot = ['face_lipTopJA', 'face_lipTopJB', 'face_lipTopJC', 'face_lipBottomJA', 'face_lipBottomJB', 'face_lipBottomJC', 'face_lipCorner']
    suffix = ['_JNT','_LOC', '_CTRL', '_GRP', "_paCON", '_poCON', '_oCON', '_aimCON']
    prefix = ['L_', 'R_', 'C_']

    facegrp = cmds.group(em = True, n = "face_CTRL_GRP")

    cheekGRP = []
    noseGRP = []  


    for p in prefix:
        
        for jnt in cheekJnts: 
        
            if p == 'C_':
                continue
                
            jnt = f"{p}{jnt}{suffix[0]}"
            ctrl = jnt.replace(suffix[0],suffix[2])

            OffsetGrp = cmds.group(n = jnt.replace(suffix[0], '_pose' + suffix[3]), em = True)
            loc = cmds.spaceLocator(n = jnt.replace(suffix[0], suffix[1]))[0]

            cmds.parent(OffsetGrp, loc)

            cmds.delete(cmds.parentConstraint(jnt, loc, mo = False))
            
            cmds.parent(ctrl, OffsetGrp)        

            cmds.makeIdentity(ctrl, apply = True, t = True, r = True, s = True)

            cmds.pointConstraint(ctrl, jnt, mo = True, n = jnt.replace(suffix[0], suffix[5]))

            cheekGRP.append(loc)

        eyebrowGRP = []
        for jnt in eyebrowJnts: 

            #skip middle eyebrow for L_ and R_
            if jnt == 'face_eyebrowMiddle_tweak' and p != 'C_':
                continue
                
            if jnt not in 'face_eyebrowMiddle_tweak' and p == 'C_':
                continue

            jnt = f"{p}{jnt}{suffix[0]}"
            ctrl = jnt.replace(suffix[0],suffix[2])

            OffsetGrp = cmds.group(n = jnt.replace(suffix[0], '_pose' + suffix[3]), em = True)
            loc = cmds.spaceLocator(n = jnt.replace(suffix[0], suffix[1]))[0]

            cmds.parent(OffsetGrp, loc)

            cmds.delete(cmds.parentConstraint(jnt, loc, mo = False))
            
            cmds.parent(ctrl, OffsetGrp)

            cmds.makeIdentity(ctrl, apply = True, t = True, r = True, s = True)

            cmds.pointConstraint(ctrl, jnt, mo = True, n = jnt.replace(suffix[0], suffix[5]))

            eyebrowGRP.append(loc)
            
            if loc == 'C_face_eyebrowMiddle_tweak_LOC': 
                cmds.parent(loc, facegrp)
        
        if not 'C_' in p:
            meyebrowGRP = cmds.group(eyebrowGRP, n = f"{p}eyebrow_GRP")
            masterctrl = f"{p}masterEyebrow_CTRL"
            cmds.parent(masterctrl, facegrp)

        cmds.parent(meyebrowGRP, masterctrl)

        tweak = []
        root = []
        lipGRP = []

        for ls in lipsufx: 

            for jnt in lipRoot: 

                if jnt in ['face_lipTopJA', 'face_lipBottomJA'] and p != 'C_':
                    continue

                if jnt not in ['face_lipTopJA', 'face_lipBottomJA'] and p == 'C_':
                    continue
                    
                jnt = f"{p}{jnt}{ls}{suffix[0]}"
                ctrl = jnt.replace(suffix[0],suffix[2])

                OffsetGrp = cmds.group(n = jnt.replace(suffix[0], '_pose' + suffix[3]), em = True)
                loc = cmds.spaceLocator(n = jnt.replace(suffix[0], suffix[1]))[0]

                cmds.parent(OffsetGrp, loc)

                cmds.delete(cmds.parentConstraint(jnt, loc, mo = False))
                
                cmds.parent(ctrl, OffsetGrp)

                cmds.makeIdentity(ctrl, apply = True, t = True, r = True, s = True)
                
                if ls == '_tweak':
                    cmds.pointConstraint(ctrl, jnt, mo = True, n = jnt.replace(suffix[0], suffix[5]))
                    tweak.append(loc)

                elif ls == '_root':
                    cmds.orientConstraint(ctrl, jnt, mo = True, n = jnt.replace(suffix[0], suffix[6]))
                    root.append(loc)

        for twk, rt in zip(tweak, root):
            cmds.parent(twk, rt)

        lipGRP.append(root)
        lipGRP.append(tweak)
        
        mGRP = cmds.group(em = True, n = f"{p}lip_GRP")
        for grp in lipGRP:
            cmds.parent(grp, mGRP) 
        cmds.parent(mGRP, facegrp)

        for jnt in noseJnts: 

                #skip middle eyebrow for L_ and R_
            if jnt in ['face_noseTip', 'face_noseUnder'] and p != 'C_':
                continue
                
            if jnt not in ['face_noseTip', 'face_noseUnder'] and p == 'C_':
                continue

            jnt = f"{p}{jnt}{suffix[0]}"
            ctrl = jnt.replace(suffix[0],suffix[2])

            OffsetGrp = cmds.group(n = jnt.replace(suffix[0], '_pose' + suffix[3]), em = True)
            loc = cmds.spaceLocator(n = jnt.replace(suffix[0], suffix[1]))[0]

            cmds.parent(OffsetGrp, loc)

            cmds.delete(cmds.parentConstraint(jnt, loc, mo = False))
            
            cmds.parent(ctrl, OffsetGrp)

            cmds.makeIdentity(ctrl, apply = True, t = True, r = True, s = True)

            cmds.pointConstraint(ctrl, jnt, mo = True, n = jnt.replace(suffix[0], suffix[5]))

            noseGRP.append(loc)
        



        eyelidGRP = []
        for jnt in eyelidJnts: 
                        
            if p == 'C_':
                continue

            jnt = f"{p}{jnt}{suffix[0]}"
            ctrl = jnt.replace(suffix[0],suffix[2])

            OffsetGrp = cmds.group(n = jnt.replace(suffix[0], '_pose' + suffix[3]), em = True)
            loc = cmds.spaceLocator(n = jnt.replace(suffix[0], suffix[1]))[0]

            cmds.parent(OffsetGrp, loc)

            cmds.delete(cmds.parentConstraint(jnt, loc, mo = False))
            
            cmds.parent(ctrl, OffsetGrp)

            cmds.makeIdentity(ctrl, apply = True, t = True, r = True, s = True)

            if '*tweak*' in jnt: 
                cmds.pointConstraint(ctrl, jnt, mo = True, n = jnt.replace(suffix[0], suffix[5]))
            else: 
                cmds.orientConstraint(ctrl, jnt, mo = True, n = jnt.replace(suffix[0], suffix[6]))

            eyelidGRP.append(loc)
        if p == 'C_':
            continue    
        meyelidGRP = cmds.group(em = True, n = f"{p}eyelid_GRP")    
        for obj in eyelidGRP:     
            cmds.parent(obj, meyelidGRP)
        cmds.parent(meyelidGRP, facegrp)

    mnoseGRP = cmds.group(em = True, n = "nose_GRP")      
    for obj in noseGRP: 
        cmds.parent(obj, mnoseGRP)

    mcheekGRP = cmds.group(em = True, n = "cheek_GRP")
    for obj in cheekGRP: 
        cmds.parent(obj, mcheekGRP)
        
    mtoplip = 'C_masterLipTop_CTRL'
    mbottomlip = 'C_masterLipBottom_CTRL'  
        
    cmds.parent(mnoseGRP, mcheekGRP, mGRP, mtoplip, mbottomlip, facegrp)


    #sdk for tweak vis

    cmds.addAttr(headCtrl, ln = 'Tweak_CTRL_Visibility', at = 'enum', en = "__________ ", k = True)

    cmds.addAttr(headCtrl, at = "bool", ln = "Eyebrow_Tweak_CTRL_VIS", k = True, dv = False )
    cmds.addAttr(headCtrl, at = "bool", ln = "Eyelid_Tweak_CTRL_VIS", k = True, dv = False )
    cmds.addAttr(headCtrl, at = "bool", ln = "Lip_secondary_Tweak_CTRL_VIS", k = True, dv = False )
    cmds.addAttr(headCtrl, at = "bool", ln = "Lip_Tertiary_Tweak_CTRL_VIS", k = True, dv = False )

    #SET DRIVEN KEYYYSS

    driver = f"{headCtrl}.Tweak_CTRL_VIS"

    eyebrowtweakCTRLS = cmds.ls('*eyebrow*tweak*CTRL')
    eyelidtweakCTRLS = cmds.ls('*eye*Corner*tweak*CTRL')
    liptweakCTRLS = cmds.ls('*lip*tweak*CTRL')
    liprootCTRLS = cmds.ls('*lip*root*CTRL')

    liprootCTRLS.remove('L_face_lipCorner_root_CTRL')
    liprootCTRLS.remove('R_face_lipCorner_root_CTRL')

    for ctrl in eyebrowtweakCTRLS: 
        driver = f"{headCtrl}.Eyebrow_Tweak_CTRL_VIS"
        driven = f"{ctrl}.visibility"
        cmds.setDrivenKeyframe(driven, cd = driver, dv = 0, v = 0)
        cmds.setDrivenKeyframe(driven, cd = driver, dv = 1, v = 1)

    for ctrl in liptweakCTRLS: 
        driver = f"{headCtrl}.Lip_Tertiary_Tweak_CTRL_VIS"
        driven = f"{ctrl}.visibility"
        cmds.setDrivenKeyframe(driven, cd = driver, dv = 0, v = 0)
        cmds.setDrivenKeyframe(driven, cd = driver, dv = 1, v = 1)

    for ctrl in liprootCTRLS: 
        driver = f"{headCtrl}.Lip_secondary_Tweak_CTRL_VIS"
        driven = f"{ctrl}.visibility"
        cmds.setDrivenKeyframe(driven, cd = driver, dv = 0, v = 0)
        cmds.setDrivenKeyframe(driven, cd = driver, dv = 1, v = 1)

    for ctrl in eyelidtweakCTRLS: 
        driver = f"{headCtrl}.Eyelid_Tweak_CTRL_VIS"
        driven = f"{ctrl}.visibility"
        cmds.setDrivenKeyframe(driven, cd = driver, dv = 0, v = 0)
        cmds.setDrivenKeyframe(driven, cd = driver, dv = 1, v = 1)

    #rotational joints doing the big movements and transform on the tiny joints for smaller movements.
    # 2 sets of ctrls. the tweak ones need to be parented underneath the big 
    #naming con would be JNT and tweak_JNT + volume jnts '''
