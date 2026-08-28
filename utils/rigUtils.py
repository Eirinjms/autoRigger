import maya.cmds as cmds
import autoRigger.utils.config as config


def fkCreator(joints, constraint, size):
    fkLocs = []
    fkCtrls = []
    for count, joint in enumerate(joints): 
            fkLoc = cmds.spaceLocator(n = joint.replace(config.suffix['joint'], config.suffix['locator']))[0]
            fkLocs.append(fkLoc)

            fkCtrl = cmds.circle(n = joint.replace(config.suffix['joint'], config.suffix['control']), 
                                r = size, 
                                nr = (1,0,0))[0]
            fkCtrls.append(fkCtrl)

            cmds.parent(fkCtrl, fkLoc)

            cmds.matchTransform(fkLoc, joint, pos = True, rot = True)

            if constraint == "parent":
                constraintFunc = cmds.parentConstraint
            elif constraint == "orient":
                 constraintFunc = cmds.orientConstraint

            constraintFunc(fkCtrl, joint, 
                                        n = joint.replace(config.suffix['joint'], config.suffix['orientCon']), 
                                        mo = False)

            if count > 0:
                cmds.parent(fkLocs[count], fkCtrls[count-1])

    return fkLocs, fkCtrls


def spaceSwitchConstraint(weights, driver):
    """
    Creates the driven keys for a space switch.

    Takes the constraint weights and sets them so only one
    space is active at a time, based on the driver enum.

    Args:
        weights (list): List of constraint weight attributes.
        driver (str): Attribute driving the space switch.
    """
    for i, weight in enumerate(weights):
        for dv in range(len(weights)):
            v = 1 if dv == i else 0
            cmds.setDrivenKeyframe(weight, cd = driver, dv = dv, v = v)