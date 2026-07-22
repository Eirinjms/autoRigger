import maya.cmds as cmds # pyright: ignore[reportMissingImports] 
import autoRigger.modules.rigModules.spineModule as spineModule
import autoRigger.modules.rigModules.limbModule as limbModule
import autoRigger.modules.rigModules.headModule as headModule
import autoRigger.modules.rigModules.cleanup as cleanup
import autoRigger.utils.shapes as shapes
import importlib

#importlib.reload(spineModule)
importlib.reload(shapes)
importlib.reload(headModule)
importlib.reload(limbModule)
importlib.reload(spineModule)

def build(spineOrder, spineJoints, armOrder, legOrder, handOrder, neckOrder, stretchyArms, stretchylegs, twistAmount, twistArm, twistLeg, ribbonArms, ribbonLegs, ribbonDrivers, ribbonBinds):
    """
    the wrapper builder calling upon the other modules.

        Parameters: 
            armOrder : defines the rotation order for the arm, and is a passed value from the UI. 
            (counts for the other orders too) 
    """
    try:
        print(twistAmount, "ui")
        if len(cmds.ls("*spine*", type='joint')) != 0:
            spineBuild = spineModule.spineBuilder(spineOrder, spineJoints)
            spineBuild.buildSpine()
        
        limbs=[]
        if len(cmds.ls("*arm*", type='joint')) != 0:
            limbs.append("arm")
        if len(cmds.ls("*leg*", type='joint')) != 0:
            limbs.append("leg")

        if limbs:
            limbModule.build_limb_set(legOrder, 
                                    armOrder, 
                                    handOrder,
                                    stretchylegs,
                                    stretchyArms,
                                    twistAmount,
                                    twistArm,
                                    twistLeg,
                                    ribbonArms,
                                    ribbonLegs,
                                    ribbonDrivers,
                                    ribbonBinds,
                                    sides = ["L", "R"], 
                                    limbs = limbs)
            
        if len(cmds.ls("*head*", type='joint')) != 0:
            headModule.headBuild(neckOrder)

    except Exception as e:
        print(e)
    finally:
        cleanup.cleanup()