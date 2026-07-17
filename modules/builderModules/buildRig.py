import maya.cmds as cmds # pyright: ignore[reportMissingImports] 
import autoRigger.modules.rigModules.spineModule as spineModule
import autoRigger.modules.rigModules.limbModule as limbModule
import autoRigger.modules.rigModules.faceModule as faceModule
import autoRigger.modules.rigModules.cleanup as cleanup
import autoRigger.utils.shapes as shapes
import importlib

#importlib.reload(spineModule)
importlib.reload(shapes)
importlib.reload(faceModule)
importlib.reload(limbModule)


def build(spineOrder, spineJoints, armOrder, legOrder, handOrder, neckOrder, stretchyArms, stretchylegs):
    """
    the wrapper builder calling upon the other modules.

        Parameters: 
            armOrder : defines the rotation order for the arm, and is a passed value from the UI. 
            (counts for the other orders too) 
    """
    spineBuild = spineModule.spineBuilder(spineOrder, spineJoints)
    spineBuild.buildSpine()
    limbModule.build_limb_set(legOrder, 
                              armOrder, 
                              handOrder,
                              stretchylegs,
                              stretchyArms,
                              sides = ["L", "R"], 
                              limbs = ["leg", "arm"])
    faceModule.headBuild(neckOrder)
    cleanup.cleanup()