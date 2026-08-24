import maya.cmds as cmds
from autoRigger.utils import config, rigUtils

prosomaJoints = [f"C_prosomaJ{i}{config.suffix['joint']}" for i in "ABC"]
abdomenJoints = [f"C_abdomenJ{i}{config.suffix['joint']}" for i in "ABCD"]

print(prosomaJoints, abdomenJoints)

def abdomenBuild():
    abdomen_fkLocs, abdomen_fkCtrls = rigUtils.fkCreator(abdomenJoints)

    return abdomen_fkLocs, abdomen_fkCtrls

def prosomaBuild():
    prosoma_fkLocs, prosoma_fkCtrls = rigUtils.fkCreator(prosomaJoints)

def cheliceraeBuild():
    chelicerae_fkLocs = []
    chelicerae_fkCtrls = []
    for side in config.prefix: 
        cheliceraeJoints = [f"{side}cheliceraeJ{i}{config.suffix['joint']}" for i in "AB"]
        fkLocs, fkCtrls = rigUtils.fkCreator(cheliceraeJoints)
        chelicerae_fkLocs.append(fkLocs)
        chelicerae_fkCtrls.append(fkCtrls)
