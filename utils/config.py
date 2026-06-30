import enum
from dataclasses import dataclass
import maya.cmds as cmds # pyright: ignore[reportMissingImports]
import os


suffix = {
    "joint"        : "_JNT",
    "locator"      : "_LOC",
    "control"      : "_CTRL",
    "ikHandle"     : "_IKH",
    "fkik"         : "_FKIK",
    "blendColor"   : "_BLND",
    "group"        : "_GRP",
    "reverse"      : "_REV",
    "parentCon"    : "_paCON",
    "pointCon"     : "_poCON",
    "orientCon"    : "_oCON",
    "poleVectorCon": "_pvCON",
    "offsetGrp"    : "_OFFSET_GRP",
    "skinCluster"  : "_SKN"
}

prefix = {
    "left"    : "L_",
    "right"   : "R_",
    "central" : "C_"
}

attrs = ["tx","ty","tz","rx","ry","rz","sx","sy","sz"]

fkik = ['_FK', '_IK']


class rotationOrder(enum.Enum):
    XYZ = 0
    YZX = 1
    ZXY = 2
    XZY = 3
    YXZ = 4
    ZYX = 5


limbRotationOrder = {
    "Arm"   : rotationOrder.XYZ,
    "Leg"   : rotationOrder.XYZ,
    "Spine" : rotationOrder.ZXY
}

bipedal = {
    "FKlegs"       : 10,
    "IKlegs"       : 7,
    "IKswitchLegs" : 6,
    "PVlegs"       : -3,
    "pvLegDistance": 15,
    "pvArmDistance": 10,
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
