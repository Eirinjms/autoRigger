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
        jointOrientation = cmds.getAttr(f"{joint}.jointOrient")[0]

        joint_data = {
            "pos": joint_pos,
            "parent": parents[0] if parents else None,
            "jointOrientation" : jointOrientation,
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

        file_path = config.find_file_path("presets", f"{file_name}")

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

