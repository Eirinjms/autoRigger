import maya.cmds as cmds # pyright: ignore[reportMissingImports] 
import maya.mel as mel
import autoRigger.modules.rigModules.spineModule as spineModule
import autoRigger.modules.rigModules.limbModule as limbModule
import autoRigger.modules.rigModules.headModule as headModule
import autoRigger.modules.rigModules.cleanup as cleanup
from autoRigger.utils import shapes, config
import importlib

#importlib.reload(spineModule)
importlib.reload(shapes)
importlib.reload(headModule)
importlib.reload(limbModule)
importlib.reload(spineModule)
importlib.reload(cleanup)

def build(spineOrder, 
          spineJoints,
           armOrder, 
           legOrder, 
           handOrder, 
           neckOrder, 
           stretchyArms, 
           stretchylegs, 
           twistAmount, 
           twistArm, 
           twistLeg, 
           ribbonArms, 
           ribbonLegs, 
           ribbonDrivers, 
           ribbonBinds,
           digigradeLegs
           ):
    """
    the wrapper builder calling upon the other modules.

        Parameters: 
            armOrder : defines the rotation order for the arm, and is a passed value from the UI. 
            (counts for the other orders too) 
    """

    if not cmds.pluginInfo("ikSpringSolver", q=True,loaded=True):
        cmds.loadPlugin("ikSpringSolver")
        print("[Plugin Loaded]: ikSpringSolver")
    mel.eval("ikSpringSolver;")    

    if not cmds.pluginInfo("quatNodes", q=True, loaded=True):
        cmds.loadPlugin("quatNodes")
        print("[Plugin Loaded]: quatNodes")

    globalCtrl, glblShape = shapes.fourWayArrowCtrl(name = "global_CTRL", size = 20)
    cleanup.cleanupData['globalCtrl'].append(globalCtrl)

    cmds.setAttr(f"{glblShape}.overrideEnabled", 1)
    cmds.setAttr(f"{glblShape}.overrideColor", 31)

    righelper = cmds.group(n = config.RIG_HELPER_GRP , em = True)
    cleanup.cleanupData['rig_helper_GRP'].append(righelper)


    if len(cmds.ls("*spine*", type='joint')) != 0:
        spineBuild = spineModule.spineBuilder(spineOrder, spineJoints)
        spineBuild.buildSpine()
    else: 
        return cmds.warning("Spine does not exist.")
    
    limbs=[]
    if len(cmds.ls("*arm*", type='joint')) != 0:
        limbs.append("arm")
    if len(cmds.ls("*leg*", type='joint')) != 0:
        limbs.append("leg")

    if limbs:
        limbModule.build_limb_set(legOrder, 
                                armOrder, 
                                handOrder,
                                stretchyArms,
                                stretchylegs,
                                twistAmount,
                                twistArm,
                                twistLeg,
                                ribbonArms,
                                ribbonLegs,
                                ribbonDrivers,
                                ribbonBinds,
                                digigradeLegs,
                                sides = ["L", "R"], 
                                limbs = limbs)
        
    if len(cmds.ls("*head*", type='joint')) != 0:
        headModule.headBuild(neckOrder)

    cleanup.cleanup()
    cmds.select(clear = True)