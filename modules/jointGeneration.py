import maya.cmds as cmds
import maya.api.OpenMaya as om
import autoRigger.naming as naming
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


joints = cmds.ls(sl = True)

locs = []
for jnt in joints:
    jnt_pos = cmds.xform(jnt, q = True, ws = True, t = True)
    print(jnt_pos)
    loc = cmds.spaceLocator(p = jnt_pos, n = jnt.replace("JNT", "GUIDE"))[0]
    locs.append(loc)

cmds.group(locs) 

joints = cmds.ls(sl = True)
savedHierarchy = {}

for joint in joints:

    parent = cmds.listRelatives(
        joint,
        parent=True,
        type='joint'
    )

    savedHierarchy[joint] = parent[0] if parent else None
print(savedHierarchy)

cmds.parent(joints, w = True) 

for child, parent in savedHierarchy.items():

    if parent:
        cmds.parent(child, parent)





joints = cmds.ls(sl = True)
savedHierarchy = {}

for joint in joints:

    parent = cmds.listRelatives(
        joint,
        parent=True,
        type='joint'
    )

    savedHierarchy[joint] = parent[0] if parent else None


cmds.parent(joints, w = True) 
locs = []
for jnt in joints:
    jnt_pos = cmds.xform(jnt, q = True, ws = True, t = True)
    loc = cmds.spaceLocator(p = jnt_pos, n = jnt.replace("JNT", "GUIDE"))[0]
    locs.append(loc)

for child, parent in savedHierarchy.items():
    childeGuide = child.replace("JNT", "GUIDE")
    if parent:
        parentGuide = parent.replace("JNT", "GUIDE")
        cmds.parent(childeGuide, parentGuide)