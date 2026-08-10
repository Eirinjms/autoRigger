import maya.cmds as cmds # pyright: ignore[reportMissingImports] 
import autoRigger.utils.shapes as shapes
import importlib

importlib.reload(shapes)

##refactor this so that the modules fill in this dict instead of finding everything w maya cmds
cleanupData = {
        "globalCtrl": [],

        "arm_IK_GRP": [],
        "leg_IK_GRP": [],
        "FKIK_switches": [],

        "headGRP": [],
        "neckLoc": [],

        "handCTRL_GRP": [],
        "fist_CTRL_GRP": [],

        "spine_FK_GRP": [],
        "spineStart": [],
        "spineEnd": [],
        "hipSpace" : [],

        "arm_FK_GRP": [],
        "leg_FK_GRP": [],

        "Ribbons_GRP": [],

        "rig_helper_GRP": [],
        }

def cleanup():
    print(cleanupData)
    #Automated color selection based on name
    shapes.ctrlColour()

    skeleton = 'root_JNT'
    skeletonGrp = cmds.group(skeleton, n = "skeleton_GRP")
    deformersGrp = cmds.group(em = True, n = "deformers")
    dntGrp = cmds.group(em = True, n = "DO_NOT_TOUCH")



    ikGrps = cmds.ls('*_IK_GRP')
    spineStart = cmds.ls("*spineJA_BND_LOC")[0]
    spineEnd = cmds.ls("*spineJEnd_BND_LOC")[0]
    spineFK = cmds.ls("spine_FK_GRP")[0]
    fistCtrl = cmds.group(cmds.ls("*fist_CTRL"), n = "fist_CTRL_GRP")
    handGrps = cmds.group(cmds.ls("*hand_LOC"), n = "handCTRL_GRP")
    neck = cmds.ls('C_neckJA_LOC')[0]
    headGRP = cmds.ls('head_GRP')[0]
    globalCtrl = "global_CTRL"
    hipSpace = "hipSpace_LOC"

    ribbonGrps = cmds.ls("*RIBBONS*GRP", type='transform') or []
    if ribbonGrps: 
       ribbongGrp = cmds.group(ribbonGrps, n = "Ribbons_GRP")
    else:
        ribbonGrp = []

    righelpergrp = "rig_helpers_GRP"
    if cmds.objExists(righelpergrp):
        children = cmds.listRelatives(righelpergrp, children = True)
        if not children:
            cmds.delete(righelpergrp)
        if children: 
            cmds.parent(righelpergrp, deformersGrp)

    legFKs = cmds.ls('*_leg_FK_GRP')
    armFKs = cmds.ls('*_armJA_LOC')
    fkikSwitch = cmds.group(cmds.ls('*_switch_GRP'), n = "FKIK_switches")

    ikGrp = cmds.group(ikGrps,  n = "IK_GRP")
    armIKs = cmds.group(em = True, n = "arm_IK_GRP")
    legIKs = cmds.group(em = True, n = "leg_IK_GRP")
    cmds.parent(armIKs, legIKs, ikGrp)

    for grp in ikGrps:
        if "arm" in grp: 
            cmds.parent(grp, armIKs)
        if "leg" in grp:
            cmds.parent(grp, legIKs)
        else: 
            continue 


    cmds.parent(skeletonGrp, dntGrp, deformersGrp)
    cmds.parent(ribbonGrp, dntGrp)
    cmds.parent(fistCtrl, handGrps)
    cmds.parent(fkikSwitch, ikGrp)
    cmds.parent(armFKs, neck, spineEnd)
    cmds.parent(legFKs, spineStart)
    cmds.parent(spineFK, spineStart, spineEnd, ikGrp, handGrps, headGRP, hipSpace, skeleton, globalCtrl)

    locs = cmds.ls("*LOC*", s = True)
    for loc in locs:
        cmds.setAttr(f"{loc}.visibility", 0) 


"""    
ikGrps = cleanupData['ikGrps']
spineEnd =  cleanupData['spineEnd']
spineStart =  cleanupData['spineStart']
spineFK = cleanupData['spine_FK_GRP']
armFKs = cleanupData['spine_FK_GRP']
legFKs = cleanupData['spine_FK_GRP']
neck = cleanupData['neckLoc']
handGrps = cmds.group(cleanupData['handCTRL_GRP'] + cleanupData['fist_CTRL_GRP'], n = "handGrp")   ## this seems wrong
headGRP = cleanupData['headGRP']
hipSpace = cleanupData['spine_FK_GRP']
ribbonsGrp = cleanupData['spine_FK_GRP']
rigHelperGrp = cleanupData['spine_FK_GRP']

        "globalCtrl": [],

        "arm_IK_GRP": [],
        "leg_IK_GRP": [],
        "FKIK_switches": [],

        "headGRP": [],
        "neckLoc": [],

        "handCTRL_GRP": [],
        "fist_CTRL_GRP": [],

        "spine_FK_GRP": [],
        "spineStart": [],
        "spineEnd": [],
        "hipSpace" : [],

        "arm_FK_GRP": [],
        "leg_FK_GRP": [],

        "Ribbons_GRP": [],

        "rig_helper_GRP": [],
        }
cleanup = {
        globalCtrl : [ikGrps,
                    spineEnd,
                    spineStart,
                    spineFK,
                    handGrps,
                    headGRP],

        spineEnd : [armFKs,
                    neck],

        spineStart : [legFKs],

        ikGrp : [fkikSwitch],
        }

        deformers : skeletonGrp,
                    dntGrp,

    for parent, child in cleanup.items():
        cmds.parent(child, parent)
#headgrp under neck, """