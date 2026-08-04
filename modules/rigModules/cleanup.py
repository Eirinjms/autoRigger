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

    #Automated color selection based on name
    shapes.ctrlColour()

    skeleton = cmds.ls('root_JNT')
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
       ribbongrp = cmds.group(ribbonGrps, n = "Ribbons_GRP")
    else:
        ribbongrp = []

    righelpergrp = "rig_helpers_GRP"
    if cmds.objExists(righelpergrp):
        children = cmds.listRelatives(righelpergrp, children = True)
        if not children:
            cmds.delete(righelpergrp)
        if children: 
            cmds.parent(righelpergrp, globalCtrl)

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

    cmds.parent(fistCtrl, handGrps)
    cmds.parent(fkikSwitch, ikGrp)
    cmds.parent(armFKs, neck, spineEnd)
    cmds.parent(legFKs, spineStart)
    cmds.parent(ribbongrp, spineFK, spineStart, spineEnd, ikGrp, handGrps, headGRP, hipSpace, skeleton, globalCtrl)

    locs = cmds.ls("*LOC*", s = True)
    for loc in locs:
        cmds.setAttr(f"{loc}.visibility", 0) 


"""    cleanup = {
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

    for p, c in cleanup.items():
        cmds.parent(c, p)
#headgrp under neck, """