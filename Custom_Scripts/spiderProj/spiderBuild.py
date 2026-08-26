import maya.cmds as cmds
from autoRigger.Custom_Scripts.spiderProj import spiderLeg, spiderBody, cleanup
from autoRigger.utils import shapes, config 
import importlib as imp

imp.reload(spiderBody)
imp.reload(spiderLeg)
imp.reload(cleanup)

def build():
    globalCtrl, glblShape = shapes.fourWayArrowCtrl(name = "global_CTRL", size = 20)
    cleanup.cleanupData_spider['globalCtrl'].append(globalCtrl)

    cmds.setAttr(f"{glblShape}.overrideEnabled", 1)
    cmds.setAttr(f"{glblShape}.overrideColor", 31)

    spiderBody.abdomenBuild()
    spiderBody.prosomaBuild()
    spiderBody.cheliceraeBuild()
    spiderLeg.build()
    cleanup.cleanup()
    shapes.ctrlColour()
    