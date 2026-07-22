import maya.cmds as cmds # pyright: ignore[reportMissingImports] 
import autoRigger.utils.shapes as shapes
import importlib

importlib.reload(shapes)

def cleanup():
    globalCtrl = shapes.fourWayArrowCtrl(name = "C_global_CTRL", size = 20)

    #Automated color selection based on name
    shapes.ctrlColour()

    skeleton = cmds.ls('*Skeleton*')
    ikGrps = cmds.ls('*_IK_GRP')
    spineStart = cmds.ls("spineJA_BND_LOC")
    spineEnd = cmds.ls("spineJEnd_BND_LOC")
    spineFK = cmds.ls("spine_FK_GRP")
    fistCtrl = cmds.group(cmds.ls("*fist_CTRL"), n = "fist_CTRL_GRP")
    handGrps = cmds.group(cmds.ls("*hand_LOC"), n = "handCTRL_GRP")
    neck = cmds.ls('C_neckJA_LOC')
    headGRP = cmds.ls('head_GRP')

    ribbonGrps = cmds.ls("*Ribbon*GRP", type='transform')
    cmds.group(ribbonGrps, n = "Ribbons_GRP")


    cmds.parent(ikGrps, spineEnd, spineStart, spineFK, handGrps, headGRP, skeleton, globalCtrl)
    cmds.parent(fistCtrl, handGrps)

    legFKs = cmds.ls('*_leg_FK_GRP')
    armFKs = cmds.ls('*_armJA_LOC')
    legIks = cmds.ls('*_leg_IK_GRP')
    armIks = cmds.ls('*_arm_IK_GRP')
    fkikSwitch = cmds.ls('*_switch_GRP')
    switchGrp = cmds.group(fkikSwitch, n = "FKIK_switch_GRP")

    ribbonGrps = cmds.ls("*Ribbon*GRP", type='transform')

    cmds.group(ribbonGrps, n = "Ribbons_GRP")


    iKGrp = cmds.group(armIks, legIks, ikGrps,  n = "IK_GRP")
    ikLegGrp = cmds.group(legIks, n = "leg_IK_GRP")
    ikArmGrp = cmds.group(armIks, n = "arm_IK_GRP")
    cmds.parent(switchGrp, iKGrp)

    cmds.parent(armFKs, neck, spineEnd)
    cmds.parent(legFKs, spineStart)

    locs = cmds.ls("*LOC*", s = True)
    for loc in locs:
        cmds.setAttr(f"{loc}.visibility", 0) 
