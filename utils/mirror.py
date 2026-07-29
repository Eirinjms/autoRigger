import maya.cmds as cmds  # pyright: ignore[reportMissingImports]
from autoRigger.utils.hierarchyModule import hierarchyManager


import maya.cmds as cmds  # pyright: ignore[reportMissingImports]


def mirrorLocators(sel: str | list | None = None) -> list:
    """
    Mirrors locators by duplicating into a temp group, scaling -1 on X,
    freezing transforms, renaming, then ungrouping.

    Parameters:
        sel (str | list | None): Locator(s) to mirror. Uses scene selection if None.

    Returns:
        list: The mirrored locator transforms.
    """

    cmds.undoInfo(openChunk=True)
    try:
        if not sel:
            sel = cmds.ls(sl=True, long=False)

        if not sel:
            cmds.warning("Please select what you want to mirror")
            return []

        if isinstance(sel, str):
            sel = [sel]

        if len(sel) != 1:
            cmds.warning("please select root to mirror")
            return []

        cmds.select(clear=True)

        parent = cmds.listRelatives(sel, p = True, type='transform')

        print(sel)
        for obj in sel: 
            print(obj)
            if obj.startswith("L_"):
                mirror = obj.replace("L_", "R_")
            if obj.startswith("R_"):
                mirror = obj.replace("R_", "L_")    

            if cmds.objExists(mirror):
                cmds.delete(mirror)

        # group originals temporarily so we can duplicate the whole hierarchy at once
        originGrp = cmds.group(em=True, name="tempOrigin_GRP")
        cmds.parent(sel, originGrp)

        # duplicate and mirror
        duplicatedGrp = cmds.duplicate(originGrp, n="tempMirror_GRP")[0]
        cmds.setAttr(f"{duplicatedGrp}.scaleX", -1)
        cmds.makeIdentity(duplicatedGrp, a=True, s=True)

        # rename deepest first so parent renames dont invalidate child paths
        children = cmds.listRelatives(duplicatedGrp, allDescendents=True, type='transform', fullPath=True) or []

        mirroredLocs=[]
        for child in children:
            shortName = child.split("|")[-1]

            if shortName.startswith("L_"):
                newName = shortName.replace("L_", "R_")
            elif shortName.startswith("R_"):
                newName = shortName.replace("R_", "L_")
            else:
                newName = f"{child}_mirror"     
            child = cmds.rename(child, newName)
            mirroredLocs.append(child)
        
            
        # ungroup both — restore originals and extract mirrored locs to world
        cmds.parent(cmds.listRelatives(duplicatedGrp, children=True), w=True, relative=False)
        cmds.parent(cmds.listRelatives(originGrp, children=True), w=True, relative=False)
        cmds.delete(originGrp, duplicatedGrp)

        if parent: 
            cmds.parent(sel, mirror, parent)

        return mirroredLocs 
    finally: 
        cmds.undoInfo(closeChunk=True)
