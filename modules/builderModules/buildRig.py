import maya.cmds as cmds # pyright: ignore[reportMissingImports] 
import autoRigger.modules.rigModules.spineModule as spineModule
import autoRigger.modules.rigModules.limbModule as limbModule
import autoRigger.modules.rigModules.faceModule as faceModule
import autoRigger.utils.shapes as shapes
import importlib

importlib.reload(spineModule)
importlib.reload(shapes)
importlib.reload(faceModule)
importlib.reload(limbModule)


def build():
    spineModule.build()
    limbModule.build_limb_set(sides = ["L", "R"], 
                              limbs = ["leg", "arm"])
    faceModule.headBuild()

    #Create global ctrl

    globalCtrl = shapes.fourWayArrowCtrl(name = "C_global_CTRL", size = 20)

    #Automated color selection based on name
    shapes.ctrlColour()

    skeleton = cmds.ls('*Skeleton*')
    ikGrps = cmds.ls('*_IK_GRP')
    spineStart = cmds.ls("spineJA_BND_LOC")
    spineStartLoc = cmds.ls("spineJA_BND_LOC")
    spineEnd = cmds.ls("spineJE_BND_LOC")
    spineFK = cmds.ls("spine_FK_GRP")
    fistCtrl = cmds.group(cmds.ls("*fist_CTRL"), n = "fist_CTRL_GRP")
    handGrps = cmds.group(cmds.ls("*hand_LOC"), n = "handCTRL_GRP")
    neck = cmds.ls('C_neckJA_LOC')
    headGRP = cmds.ls('head_GRP')
    cmds.parent(ikGrps, spineStartLoc, spineEnd,spineFK, handGrps, headGRP, skeleton, globalCtrl)
    cmds.parent(fistCtrl, handGrps)

    legFKs = cmds.ls('*_leg_FK_GRP')
    armFKs = cmds.ls('*_armJA_LOC')
    legIks = cmds.ls('*_leg_IK_GRP')
    armIks = cmds.ls('*_arm_IK_GRP')
    fkikSwitch = cmds.ls('*_IK_switch_GRP')
    switchGrp = cmds.group(fkikSwitch, n = "FKIK_switch_GRP")


    iKGrp = cmds.group(armIks, legIks, ikGrps,  n = "IK_GRP")
    ikLegGrp = cmds.group(legIks, n = "leg_IK_GRP")
    ikArmGrp = cmds.group(armIks, n = "arm_IK_GRP")
    cmds.parent(switchGrp, iKGrp)

    cmds.parent(armFKs, neck, spineEnd)
    cmds.parent(legFKs, spineStart)

    locs = cmds.ls("*LOC*", s = True)
    for loc in locs:
        cmds.setAttr(f"{loc}.visibility", 0) 
