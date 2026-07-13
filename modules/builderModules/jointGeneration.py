import os
import json
import maya.cmds as cmds
import autoRigger.utils.config as config


class jointGeneration():
    def __init__(self):
        self.suffix = config.suffix
        self.attrs = config.attrs

        mayaDir = cmds.internalVar(userAppDir=True)
        self.json_file_path = os.path.join(
            mayaDir,
            "scripts",
            "autoRigger",
            "presets",
            "hierarchy.json"
        )


    # JSON Export
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

        joint_data = {
            "pos": joint_pos,
            "parent": parents[0] if parents else None,
            "children": {}
        }

        if children:
            for child in children:
                joint_data['children'][child] = self.get_joint_hierarchy(child)

        return joint_data

    def skeleton_dict_result(self, rootJoint: str = 'root_JA_JNT'):
        '''Builds and stores the full skeleton dict from rootJoint on self.'''
        self.result = {rootJoint: self.get_joint_hierarchy(rootJoint)}

    def build_json(self, file_name: str):
        '''Writes self.result to the preset file path.'''
        file_path = config.find_file_path("presets", f"{file_name}.json")
        with open(file_path, "w") as f:
            json.dump(self.result, f, indent=4)
        print(f"Saved {file_name} at: {file_path}")

    def jointExportJSON(self, file_name: str):
        '''Entry point for exporting. Select the root joint, then call this.
            
            Parameter: 
                file_name(str) : whatever you want the file to be named'''
        
        selected = cmds.ls(sl=True)
        if len(selected) != 1:
            cmds.warning("Please select only the root of the chain you want to export")
            return

        self.skeleton_dict_result(rootJoint=selected[0])
        self.build_json(file_name)


    # JSON Import → Locators

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


    # Joint Generation from Locators

    def generateJoints(self):
        '''
        Finds all GUIDE locators in the scene and creates a joint at each one.
        '''
        guides = cmds.ls("*GUIDE", type="locator")

        joints = []
        for loc in guides:
            loc_pos = cmds.xform(loc, q=True, ws=True, t=True)
            jnt = cmds.joint(p=loc_pos, n=loc.replace("GUIDE", "JNT"))
            joints.append(jnt)

        cmds.group(joints, n="Skeleton_GRP")


    # Hierarchy Utilities
  
    def separate_module_from_hierarchy(self, data: dict, root_joint: str) -> dict:
        '''
        Extracts a subtree from the full skeleton dictionary starting at root_joint.

        Parameters:
            data (dict): The full skeleton dictionary
            root_joint (str): The joint name to extract from

        Returns:
            dict: Subtree rooted at root_joint, or empty dict if not found
        '''
        for joint_name, joint_data in data.items():
            if joint_name == root_joint:
                return {joint_name: joint_data}

            if joint_data["children"]:
                result = self.separate_module_from_hierarchy(
                    joint_data["children"],
                    root_joint
                )
                if result:
                    return result

        return {}

    


'''
DEVELOPER NOTE — Export/Import call chains
==========================================

EXPORT (joints → JSON):
    jointExportJSON(file_name)
        └── skeleton_dict_result(rootJoint)
                └── get_joint_hierarchy(joint)   ← recurses through children
        └── build_json(file_name)                ← writes self.result to disk

    skeleton_dict_result builds and stores the dict on self.result.
    build_json just writes whatever is on self.result.
    You only need these two calls because get_joint_hierarchy and
    build_skeleton_dict are internal steps — jointExportJSON is the
    only public entry point you should call from outside the class.

IMPORT (JSON → locators):
    import_json_locators()
        └── build_locator(joint_name, joint_data, parent)  ← recurses through children

    import_json_locators reads the file and kicks off the recursion.
    build_locator handles both creation and parenting in one pass.
    Again, one public entry point — import_json_locators — is all you need.
'''