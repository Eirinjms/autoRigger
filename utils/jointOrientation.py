import maya.cmds as cmds
from autoRigger.utils import config, hierarchyModule as hier

def jointOrientation(digigrade):    ##to do; move out of UI. 
    """
    Orients the full skeleton. Centre joints aim along X, wrists toward the middle finger,
    feet depend on digigrade. Skips jaw.

        Parameters:
            digigrade (bool): Whether the leg is digigrade.
    """
    jointList = cmds.ls(type='joint')
    jointHier = hier.hierarchyManager(jointList, True, 'joint')

    joints = cmds.ls(type='joint')
    cmds.makeIdentity(joints, a = True, r = True)
    roots = config.findRoots(cmds.ls("*JNT", type='joint'))
    children = cmds.listRelatives(roots, children = True)
    for jnt in children: 
        cmds.joint(jnt,                 
                e = True, 
            oj = "xyz", 
            sao = "yup", 
            ch = True, 
            zso = True)


    required = [
        "C_spineJA_JNT",
        "L_armJD_JNT",
        "R_armJD_JNT",
        "L_middleFngJEnd_JNT",
        "R_middleFngJEnd_JNT",
    ]
    
    missing = [j for j in required if not cmds.objExists(j)]
    if missing:
        return cmds.warning("Automatic orientation not done due to missing", missing)
    
    cmds.joint("C_spineJA_JNT", 
            e = True, 
            oj = "xyz", 
            sao = "yup", 
            ch = True, 
            zso = True)
    
    #spinejoints
    centerJoints = cmds.ls("C_*",
                        type='joint')

    jointHier.unparentHierarchy()

    for joint in centerJoints:
        if "jaw" in joint:
            continue
        
        pos = cmds.xform(joint, q = True, t = True, ws = True)
        loc = cmds.spaceLocator(n = f"{joint}_temp")[0]
        cmds.xform(loc, ws=True, t=(pos[0], pos[1] + 10, pos[2]))
        cmds.delete(cmds.aimConstraint(loc, joint, 
                                    offset = (90,0,0), 
                                    aimVector = (1,0,0), 
                                    upVector = (0,0,-1), 
                                    worldUpType = 'scene'))
        cmds.delete(loc) 

    wristPairs = [
        ("L_armJD_JNT", "L_middleFngJEnd_JNT"),
        ("R_armJD_JNT", "R_middleFngJEnd_JNT")] 
        
    
    for joint, aim in wristPairs:
        cmds.delete(cmds.aimConstraint(aim, joint, 
                        aimVector = (1,0,0),
                        worldUpType = 'scene'))
    
    jointHier.reparentHierarchy()
    orientFeetJoints(digigrade)

    #endjoints
    orientOnlyEndJoints()
    print("All joints in scene has been oriented")
def orientOnlyEndJoints():
    """
    Zeroes orientation on all joints with no joint children.
    """

    jointList = cmds.ls(type='joint')

    for joint in jointList:
        if not cmds.objExists(joint):
            cmds.warning(f"{joint} does not exist, check your scene")
            continue
        if not cmds.listRelatives(joint, c=True, type="joint"):
            cmds.makeIdentity(joint, a = True, r = True)
            cmds.joint(joint, 
                        e=True, 
                        zso=True, 
                        oj="none")
    print("[Endjoints] have been oriented")

def orientFeetJoints(digigrade):
    """
    Orients foot/ankle joints. Extends further down the chain if digigrade.

        Parameters:
            digigrade (bool): Whether to go further down the leg.
    """
    feetJoints = cmds.ls("*legJC*", "*legJD*", type = 'joint')
    jointList = cmds.ls(type='joint')
    jointHier = hier.hierarchyManager(jointList, True, 'joint')
    
    if digigrade:
        feetJoints = cmds.ls("*legJD*", type = 'joint')
        children = cmds.listRelatives(feetJoints, children = True, type = 'joint')
        feetJoints.extend(children)

    jointHier.unparentHierarchy()
    for joint in feetJoints:
        pos = cmds.xform(joint, q = True, t = True, ws = True)
        loc = cmds.spaceLocator(n = f"{joint}_temp")[0]
        cmds.xform(loc, ws=True, t=(pos[0], pos[1] + 10, pos[2]))
        cmds.delete(cmds.aimConstraint(loc, joint, 
                                    offset = (0,-90,0), 
                                    aimVector = (0,1,0), 
                                    upVector = (0,0,-1), 
                                    worldUpType = 'scene'))
        cmds.delete(loc) 
    jointHier.reparentHierarchy()

def orientSelectedJoints(digigrade):
    """
    Re-orients selected joints. Foot joints unparent/reparent first,
    everything else orients in place without affecting children.

        Parameters:
            digigrade (bool): Passed to orientFeetJoints if needed.
    """

    joints = cmds.ls(sl=True, type='joint')
    if not joints: 
        return cmds.warning("Nothing selected")
    for jnt in joints: 
        if "legJD" in jnt or "legJE" in jnt or "legJC" in jnt: 
            orientFeetJoints(digigrade)
        else: 
            cmds.joint(jnt,                 
                    e = True, 
                    oj = "xyz", 
                    sao = "yup", 
                    ch = False, 
                    zso = True)
    print(f"[selected Joints]: {joints} have been oriented")
