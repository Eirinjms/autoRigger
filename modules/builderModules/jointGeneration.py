import maya.cmds as cmds  # pyright: ignore[reportMissingImports]
import maya.api.OpenMaya as om  # pyright: ignore[reportMissingImports]
import autoRigger.config as config
import json
import os
import importlib

importlib.reload(config)


class jointGeneration():
    def __init__(self, prefix, preset, moduleType):
        prefix = prefix.upper()
        preset = preset.lower()

        if prefix not in ['L', 'R', 'C']:
            cmds.error('Please Choose either L, R, C')
        if preset not in ['bipedal', 'quadraped', 'creature']:
            cmds.error('Please choose existing preset')

        self.suffix = config.suffix
        self.attrs = config.attrs
        self.side = f"{prefix}_"
        self.preset = preset
        self.moduleType = moduleType

        mayaDir = cmds.internalVar(userAppDir=True)
        self.json_file_path = os.path.join(
            mayaDir,
            "scripts",
            "autoRigger",
            "presets",
            "hierarchy.json"
        )

    # -------------------------------------------------------------------------
    # JSON Save
    # -------------------------------------------------------------------------

    def get_joint_hierarchy(self, joint: str) -> dict:
        '''
        Recursively builds a dictionary for a joint and all its children.

        Parameters:
            joint (str): Name of the joint

        Returns:
            dict: Position, orientation, rotation order, parent, children
        '''
        joint_pos = cmds.xform(joint, q=True, ws=True, t=True)
        children = cmds.listRelatives(joint, children=True, type='joint')
        parents = cmds.listRelatives(joint, parent=True, type='joint')
        joint_orientation = cmds.getAttr(f"{joint}.jointOrient")[0]
        rotationOrder = cmds.getAttr(f"{joint}.rotateOrder")

        joint_data = {
            "pos": joint_pos,
            "orientation": joint_orientation,
            "rotationOrder": rotationOrder,
            "parent": parents[0] if parents else None,
            "children": {}
        }

        if children:
            for child in children:
                joint_data['children'][child] = self.get_joint_hierarchy(child)

        return joint_data

    def build_skeleton_dict(self, rootJoint: str) -> dict:
        '''Builds the full skeleton dictionary from a root joint.'''
        return {rootJoint: self.get_joint_hierarchy(rootJoint)}

    def skeleton_dict_result(self, rootJoint: str = 'root_JA_JNT'):
        '''Stores the skeleton dict on self for use by build_json.'''
        self.result = self.build_skeleton_dict(rootJoint)

    def build_json(self):
        '''Writes self.result to the json file path and prints the result.'''
        with open(self.json_file_path, "w") as f:
            json.dump(self.result, f, indent=4)

        with open(self.json_file_path, "r") as f:
            loaded = json.load(f)

        print(loaded)

    # -------------------------------------------------------------------------
    # JSON Load → Locators
    # -------------------------------------------------------------------------

    def build_locator(self, joint_name: str, joint_data: dict, parent=None):
        '''
        Recursively creates locators from a joint hierarchy dict.

        Parameters:
            joint_name (str): Name to give the locator (JNT replaced with GUIDE)
            joint_data (dict): Dictionary of joint data including children
            parent (str): Parent locator name, if any
        '''
        cmds.select(clear=True)

        loc = cmds.spaceLocator(
            n=joint_name.replace('JNT', 'GUIDE'),
            p=joint_data["pos"]
        )[0]

        if parent:
            cmds.parent(loc, parent)

        print(f"Created: {loc}")

        for child_name, child_data in joint_data["children"].items():
            self.build_locator(child_name, child_data, loc)

    def import_json_locators(self):
        '''Loads the hierarchy JSON and recreates the locator hierarchy.'''
        with open(self.json_file_path, "r") as f:
            data = json.load(f)

        for root_name, root_data in data.items():
            self.build_locator(root_name, root_data)

    # -------------------------------------------------------------------------
    # Joint Generation from Locators
    # -------------------------------------------------------------------------

    def generateJoints(self):
        '''
        Finds all GUIDE locators in the scene and creates a joint at each one,
        grouped under a Skeleton_GRP.
        '''
        guides = cmds.ls("*GUIDE", type="locator")

        joints = []
        for loc in guides:
            loc_pos = cmds.xform(loc, q=True, ws=True, t=True)
            jnt = cmds.joint(p=loc_pos, n=loc.replace("GUIDE", "JNT"))[0]
            joints.append(jnt)

        cmds.group(joints, n="Skeleton_GRP")


    def separate_module_from_hierarchy(self, data: dict, root_joint: str) -> dict:
        '''
        Extracts a subtree from the full skeleton dictionary
        starting at root_joint.

        Parameters:
            data (dict): The full skeleton dictionary
            root_joint (str): The joint name to extract from

        Returns:
            dict: Subtree rooted at root_joint, or empty dict if not found
        '''
        for joint_name, joint_data in data.items():
            if joint_name == root_joint:
                return {joint_name: joint_data}
            
            # recurse into children
            if joint_data["children"]:
                result = self.separate_module_from_hierarchy(
                    joint_data["children"], 
                    root_joint
                )
                if result:
                    return result
        
        return {}
        


    