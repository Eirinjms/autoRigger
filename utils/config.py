import enum
from dataclasses import dataclass
import maya.cmds as cmds # pyright: ignore[reportMissingImports]
import os
from contextlib import contextmanager


suffix = {
    "joint"        : "_JNT",
    "locator"      : "_LOC",
    "rvlocator"    : "_revLOC",
    "control"      : "_CTRL",
    "ikHandle"     : "_IKH",
    "fkik"         : "_FKIK",
    "blendColor"   : "_BLND",
    "group"        : "_GRP",
    "reverse"      : "_REV",
    "parentCon"    : "_paCON",
    "pointCon"     : "_poCON",
    "orientCon"    : "_oCON",
    "aimCon"       : "_aimCON",
    "scaleCon"     : "_scaleCON",
    "poleVectorCon": "_pvCON",
    "offsetGrp"    : "_OFFSET_GRP",
    "skinCluster"  : "_SKN",
    "switch"       : "_SWITCH",
    "curve"        : "_CURVE",
    "ikspline"     : "_IKSpline",
    "cluster"      : "_CLS",
}

prefix = {
    "left"    : "L_",
    "right"   : "R_",
    "center" : "C_"
}

attrs = ["tx","ty","tz","rx","ry","rz","sx","sy","sz"]

fkik = {
    'fk' : '_FK',
    'ik' : '_IK'}


RIG_HELPER_GRP = "rig_helpers_GRP"


class RotationOrder(enum.Enum):
    XYZ = 0
    YZX = 1
    ZXY = 2
    XZY = 3
    YXZ = 4
    ZYX = 5


limbRotationOrder = {
    "Arm"   : RotationOrder.XYZ,
    "Leg"   : RotationOrder.XYZ,
    "Spine" : RotationOrder.ZXY
}

bipedal = {
    "FKlegs"       : 10,
    "IKlegs"       : 7,
    "IKswitchLegs" : 6,
    "PVlegs"       : -3,
    "pvLegDistance": 0.75,
    "pvArmDistance": 0.75,
    "FKarms"       : 10,
    "IKarms"       : 5,
    "IKswitchArm"  : 5,
    "PVarms"       : 2,
    "clavs"        : 7,
    "IKspineX"     : 6,
    "IKspineY"     : 15,
    "IKspineZ"     : 15,
    "FKspine"      : 20,
    "fingers"      : 2,
}


def find_file_path(*destination: str) -> str :
    """
    Return the absolute path inside the autoRigger folder.

    Parameters:
        *destination: One or more path components inside the
            autoRigger directory. 
            mayadir/scripts/autoRigger/*destination

    Returns:
        str : The file path.
    """
    mayaDir = cmds.internalVar(userAppDir = True)
    file_path = os.path.join(mayaDir,
                        "scripts",
                        "autoRigger",
                        *destination
                        )

    return file_path



def setRotationOrder(itemList, rotOrderIndex):
    """
    Sets the rotation for the specified list.
        Parameters: 
            itemList (list): a list of objects you want to set order on
            rotOrderIndex (int): 
    
    """
    for item in itemList: 
        cmds.setAttr(f"{item}.rotateOrder", rotOrderIndex) 


def getGuidePos(locator):
    """
    Finds the local and world position of the specified node.

        Parameters: 
            locator (str): name of specified locator
        
        Returns: 
            localPos (tuple[float, float, float]): Local-space translation.
            worldPos (tuple[float, float, float]): World-space translation.
    
    """
    shape = cmds.listRelatives(locator, shapes=True, type="locator")[0]
    transformPos = cmds.xform(locator, q=True, ws=True, t=True)
    localPos = cmds.getAttr(f"{shape}.localPosition")[0]

    return localPos, transformPos

def addTuples(tuple1, tuple2):
    return tuple(x + y for x, y in zip(tuple1, tuple2))

def addedGuidePos(locator):
    lp, wp = getGuidePos(locator)
    finalpos = addTuples(lp, wp)

    return finalpos

     

def findRoots(nodes):
    """
    Returns all root nodes from a list of transforms.
    """

    roots = []

    for node in nodes:
        if not cmds.objExists(node):
            continue

        if not cmds.listRelatives(node, parent=True):
            roots.append(node)

    return roots[0]


def setConstraintWeights(constraintType : str, con, values=None, query = False) -> list:
    """
    Queries and optionally sets a constraint's weight aliases.

    Args:
        constraintType (str): Constraint type ("point", "orient", or "parent").
        con (str): Constraint node.
        values (list, optional): Weight values to assign. Order must match the
            constraint's weight aliases.
        query (bool, optional): If True, only returns the weight aliases.

    Returns:
        list: The constraint's weight aliases.
    """
    constraintType = constraintType.lower()

    if "orient" in constraintType:
        constraint = cmds.orientConstraint
    elif "parent" in constraintType:
        constraint = cmds.parentConstraint
    elif "point" in constraintType:
        constraint = cmds.pointConstraint
    else:
        raise ValueError(f"Unsupported constraint type: {constraintType}")
    
    if isinstance(con, list):
        con = con[0]

    conWeights = constraint(con, q = True, wal = True)
    weights = [f"{con}.{weight}" for weight in conWeights]

    if not query and values is not None:
        for weight, value in zip(weights, values):
            cmds.setAttr(weight, value)


    return weights

@contextmanager
def mayaUndo():
    cmds.undoInfo(openChunk=True)
    try:
        yield
    finally:
        cmds.undoInfo(closeChunk=True)


def shapeSwap(shape, newshape):
    newshapeShape = cmds.listRelatives(newshape, shapes=True, noIntermediate=True)[0]
    cmds.parent(newshapeShape, shape, r=True, s=True)
    cmds.delete(newshape)