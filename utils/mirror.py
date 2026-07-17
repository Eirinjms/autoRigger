import maya.cmds as cmds

def mirrorLocators(sel : str | list | None = None) -> list:
        """
        Mirrors locators from a provided list or the current Maya selection.

            Parameters:
                sel (list): List of locators to duplicate.
                    
            Returns:
                list: A list of the mirrored locators
        """

        selection = cmds.ls(sl = True, long = True)

        mirroredLocs = []

        if not sel:
            sel = selection

        if not sel:
            cmds.warning("Please select what you want to mirror")
            return []
        
        cmds.select(clear = True)

        originGrp = cmds.group(em=True, name="tempMirror_GRP")
        cmds.parent(sel, originGrp)

        duplicatedGrp = cmds.duplicate(originGrp)[0]

        cmds.setAttr(f"{duplicatedGrp}.scaleX", -1)

        #cmds.makeIdentity(duplicatedGrp, a = True, s = True)

        children = cmds.listRelatives(duplicatedGrp, allDescendents = True, type = 'transform') or []
        
        for child in children:

            if child.startswith("L_"):
                child = cmds.rename(child, child.replace("L_", "R_")
                            .replace("LOC1", "LOC"))
            elif child.startswith("R_"):
                child = cmds.rename(child, child.replace("R_", "L_")
                            .replace("LOC1", "LOC"))
            else: 
                child = cmds.rename(child, f"{child}_mirror")
            
            mirroredLocs.append(child)

        cmds.parent(cmds.listRelatives(duplicatedGrp, children = True), w = True)

        cmds.parent(cmds.listRelatives(originGrp, children = True), w = True)

        cmds.delete(originGrp, duplicatedGrp)

        return mirroredLocs

def mirrorJoints():
     print("hello")