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
    if not sel:
        sel = cmds.ls(sl=True, long=True)

    if not sel:
        cmds.warning("Please select what you want to mirror")
        return []

    if isinstance(sel, str):
        sel = [sel]

    cmds.select(clear=True)

    # group originals temporarily so we can duplicate the whole hierarchy at once
    originGrp = cmds.group(em=True, name="tempOrigin_GRP")
    cmds.parent(sel, originGrp)

    # duplicate and mirror
    duplicatedGrp = cmds.duplicate(originGrp)[0]
    cmds.setAttr(f"{duplicatedGrp}.scaleX", -1)
    cmds.makeIdentity(duplicatedGrp, a=True, s=True)

    # rename deepest first so parent renames dont invalidate child paths
    children = cmds.listRelatives(duplicatedGrp, allDescendents=True, type='transform', fullPath=True) or []

    mirroredLocs = []
    for child in children:
        shortName = child.split("|")[-1]  # get the actual node name without the path
        if shortName.startswith("L_"):
            newName = shortName.replace("L_", "R_").replace("LOC1", "LOC")
        elif shortName.startswith("R_"):
            newName = shortName.replace("R_", "L_").replace("LOC1", "LOC")
        else:
            newName = f"{shortName}_mirror"
        
        child = cmds.rename(child, newName)
        mirroredLocs.append(child)
        
    # ungroup both — restore originals and extract mirrored locs to world
    cmds.parent(cmds.listRelatives(duplicatedGrp, children=True), w=True)
    cmds.parent(cmds.listRelatives(originGrp, children=True), w=True)
    cmds.delete(originGrp, duplicatedGrp)

    return mirroredLocs
