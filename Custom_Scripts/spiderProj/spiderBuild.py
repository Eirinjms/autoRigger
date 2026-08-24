import maya.cmds as cmds
from autoRigger.Custom_Scripts.spiderProj import spiderLeg, spiderBody, cleanup
from autoRigger.utils import shapes, config 

def build():
    globalCtrl, glblShape = shapes.fourWayArrowCtrl(name = "global_CTRL", size = 20)
    cleanup.cleanupData_spider['globalCtrl'].append(globalCtrl)

    spiderLeg.build()
    spiderBody.abdomenBuild()
    spiderBody.prosomaBuild()
    spiderBody.cheliceraeBuild()
    shapes.ctrlColour()
    