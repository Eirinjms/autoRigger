import maya.cmds as cmds
from autoRigger.utils import config, rigUtils
import autoRigger.Custom_Scripts.spiderProj.cleanup as cleanup
import importlib as imp

imp.reload(cleanup)

prosomaJoints = [f"C_prosomaJ{i}{config.suffix['joint']}" for i in "ABC"]
abdomenJoints = [f"C_abdomenJ{i}{config.suffix['joint']}" for i in "ABCD"]

def abdomenBuild():
    abdomen_fkLocs, abdomen_fkCtrls = rigUtils.fkCreator(abdomenJoints, "orient")
    cleanup.cleanupData_spider['abdomen_FKs'].append(abdomen_fkLocs[0])

    return abdomen_fkLocs, abdomen_fkCtrls

def prosomaBuild():
    prosoma_fkLocs, prosoma_fkCtrls = rigUtils.fkCreator(prosomaJoints, "parent")
    prosomaSpace = cmds.spaceLocator(n = "prosomaSpace")[0]
    cmds.matchTransform(prosomaSpace, prosoma_fkLocs[0])
    cmds.parent(prosomaSpace, prosoma_fkCtrls[0])

    cleanup.cleanupData_spider['prosoma_FKs'].append(prosoma_fkLocs[0])
    cleanup.cleanupData_spider['prosomaSpace'] = prosomaSpace


def cheliceraeBuild():
    chelicerae_fkLocs = []
    chelicerae_fkCtrls = []
    for side in list(config.prefix.values())[:2]: 
        cheliceraeJoints = [f"{side}cheliceraeJ{i}{config.suffix['joint']}" for i in "AB"]
        fkLocs, fkCtrls = rigUtils.fkCreator(cheliceraeJoints, "orient")
        chelicerae_fkLocs.append(fkLocs)
        chelicerae_fkCtrls.append(fkCtrls)
        cleanup.cleanupData_spider['chelicerae_FKs'][side[0]].append(fkLocs[0])

def spaceswitches(): 
    "hi"