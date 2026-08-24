import maya.cmds as cmds
import autoRigger.utils.config as config


def fkCreator(joints):
    fkLocs = []
    fkCtrls = []
    for count, joint in enumerate(joints): 
            fkLoc = cmds.spaceLocator(n = joint.replace(config.suffix['joint'], config.suffix['locator']))[0]
            fkLocs.append(fkLoc)

            fkCtrl = cmds.circle(n = joint.replace(config.suffix['joint'], config.suffix['control']), 
                                r = 5, 
                                nr = (1,0,0))[0]
            fkCtrls.append(fkCtrl)

            cmds.parent(fkCtrl, fkLoc)

            cmds.matchTransform(fkLoc, joint, pos = True, rot = True)

            cmds.orientConstraint(fkCtrl, joint, 
                                        n = joint.replace(config.suffix['joint'], config.suffix['orientCon']), 
                                        mo = False)

            if count > 0:
                cmds.parent(fkLocs[count], fkCtrls[count-1])

    return fkLocs, fkCtrls