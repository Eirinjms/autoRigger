import maya.cmds as cmds # pyright: ignore[reportMissingImports] 
import maya.api.OpenMaya as om # pyright: ignore[reportMissingImports] 
import autoRigger.naming as naming
import json
import os
import importlib

importlib.reload(naming)

class jointGeneration():
    def __init__(self, prefix, preset, moduleType):
        prefix = prefix.upper()
        preset = preset.lower()

        if prefix not in ['L', 'R', 'C']: 
            cmds.error('Please Choose either L, R, C')
        if preset not in ['bipedal', 'quadraped', 'creature']:
            cmds.error('Please choose existing preset')
        
        self.suffix = naming.suffix
        self.attrs = naming.attrs

        self.side = f"{prefix}_"

        self.preset = preset
        self.moduleType = moduleType

    def armModule(self):
    
    def legModule(self):

    def spineModule(self):

    def faceModule(self):
    
    def handModule(self):
    
    def generateJoints(self):
        guides = cmds.ls("*GUIDE", type = "locator")

        joints = []
        for loc in guides:
            loc_pos = cmds.xform(loc, q = True, ws = True, t = True)
            jnt = cmds.joint(p = loc_pos, n = loc.replace("GUIDE", "JNT"))[0]
            joints.append(jnt)

        cmds.group(joints, n = "Skeleton_GRP") 


    def seperate_module_from_hierarchy(self, joint: str) -> dict:
        '''
        This function creates a dictionary harvesting 
        modules from the overall joint one.

        Parameters:
        Joint - name of joint

        Returns: 
            Hierarchy dictionary
        '''    


def get_joint_hierarchy(joint: str) -> dict:
    '''
    This function creates a dictionary containing: 
        - Position
        - Orientation
        - Parent
        - Child

    Parameters:
    Joint - name of joint

    Returns: 
        Hierarchy dictionary
    '''
    joint_pos = cmds.xform(joint, q = True, ws = True, t = True)

    children = cmds.listRelatives(
    joint,
    children =True,
    type='joint')

    parents = cmds.listRelatives(
    joint,
    parent =True,
    type='joint')

    joint_orientation = cmds.getAttr(f"{joint}.jointOrient")[0]

    joint_data = {
        "pos" : joint_pos,
        "orientation" : joint_orientation,
        "parent" : parents[0] if parents else None,
        "children" : {}
    }

    if children: 
        for c in children:
            joint_data['children'][c] = get_joint_hierarchy(c)
    return joint_data

def build_skeleton_dict(rootjoint: str):
    return {rootjoint : get_joint_hierarchy(rootjoint)}

result = build_skeleton_dict('root_JA_JNT')
print(result)

def build_json(filepath):
#build JSON
    filepath = r"C:\Users\Eirso\OneDrive\Dokumenter\Escape_MA\Module_5\Specialization\scripts\hierarchy.json"
    with open(filepath, "w") as fil:
        json.dump(result, fil, indent = 4)
    with open(filepath, "r") as fil:
        smth = json.load(fil)
    print(smth) 

"insert something that allows you to select file placement in the final UI oen. "


#allows u to save the hierarchy to the users preset folder :3 
mayaDir = cmds.internalVar(userAppDir=True)

presetDir = os.path.join(
    mayaDir,
    "scripts",
    "autoRigger",
    "presets"
)