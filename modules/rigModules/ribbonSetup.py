import maya.cmds as cmds  # pyright: ignore[reportMissingImports]
import maya.api.OpenMaya as om # pyright: ignore[reportMissingImports]
import autoRigger.utils.config as config  # pyright: ignore[reportMissingImports]


# RIBBON MAKER

"""parente the follicle bind joints to the bind skeleton, parent constrain to the follicles
add func for blendshapes: 
sine, wave. """

class RibbonMaker:
    def __init__(self, startJoint, endJoint, limb, side, numDrivers, numFollicles):
        self.suffix = config.suffix
        self.prefix = config.prefix

        self.startJoint = startJoint
        self.endJoint = endJoint

        self.jointPlacements = []
        for joint in [startJoint, endJoint]:
            jointPlacement = cmds.xform(joint, q=True, ws=True, t=True)
            self.jointPlacements.append(jointPlacement)
        self.limbName = limb
        self.side = f"{side}_"

        self.numDrivers = numDrivers

        self.numFollicles = numFollicles

        self.name = f"{self.side}{self.limbName}_Ribbon"

    def lengthOfRibbon(self):
        """Calculates the distance between the chosen joints."""
        A = om.MVector(self.jointPlacements[0])
        B = om.MVector(self.jointPlacements[1])
        self.RibbonLength = (B - A).length()

    def creatingNurbsPlane(self):
        """
        Creates the NURBS plane and orients/positions it between the two joints.

        Stores:
            self.RibbonPlane (str) transform node name
            self.RibbonPlaneShape (str)shape node name
        """
        self.planeWidth = 3
        plane = cmds.nurbsPlane(
            axis=(0, 0, 1),
            degree=3,
            patchesU=8,
            patchesV=1,
            width=self.RibbonLength,          # length runs along U
            lengthRatio=self.planeWidth / self.RibbonLength,
            name=self.name,
        )
        self.RibbonPlane = plane[0]           # keep the transform string, not the list
        self.RibbonPlaneShape = cmds.listRelatives(self.RibbonPlane, shapes=True)[0]

        self.positionRibbonPlane()

    def positionRibbonPlane(self):
        """
        Moves and orients the ribbon so its U axis runs from joint[0] to joint[1],
        centred between them.
        """
        A = om.MVector(self.jointPlacements[0])
        B = om.MVector(self.jointPlacements[1])

        mid = (A + B) / 2.0
        cmds.xform(self.RibbonPlane, ws=True, t=(mid.x, mid.y, mid.z))

        # aim the plane so its local X points from a to b
        aimVec = (B - A).normalize()

        # build a stable up vectorprefer world-Y, fall back to world-Z
        worldUp = om.MVector(0, 1, 0)
        if abs(aimVec * worldUp) > 0.99:
            worldUp = om.MVector(0, 0, 1)

        sideVec = (aimVec ^ worldUp).normalize()   # right
        upVec   = (sideVec ^ aimVec).normalize()   # recalculated up

        mtx = [
            aimVec.x,  aimVec.y,  aimVec.z,  0,
            upVec.x,   upVec.y,   upVec.z,   0,
            sideVec.x, sideVec.y, sideVec.z, 0,
            mid.x,     mid.y,     mid.z,     1,
        ]
        cmds.xform(self.RibbonPlane, ws=True, matrix=mtx)

    def createFollicles(self):
        """
        Creates follicles evenly distributed along the ribbon (U direction).

        Stores:
            self.ribbonFollicles (list) follicle transform names
        """
        self.ribbonFollicles = []

        for index in range(self.numFollicles):
            follicleShape = cmds.createNode("follicle")
            follicleTransform = cmds.listRelatives(follicleShape, parent=True)[0]
            follicleTransform = cmds.rename(
                follicleTransform,
                f"{self.name}_follicle{index + 1:02d}",
            )
            follicleShape = cmds.listRelatives(follicleTransform, children = True, type='follicle')[0]
            self.ribbonFollicles.append(follicleTransform)

            #surface connections 
            cmds.connectAttr(
                f"{self.RibbonPlaneShape}.local",
                f"{follicleShape}.inputSurface",
            )
            cmds.connectAttr(
                f"{self.RibbonPlaneShape}.worldMatrix[0]",
                f"{follicleShape}.inputWorldMatrix",
            )
            cmds.connectAttr(f"{follicleShape}.outRotate",    f"{follicleTransform}.rotate")
            cmds.connectAttr(f"{follicleShape}.outTranslate", f"{follicleTransform}.translate")

            u = index / (self.numFollicles - 1) if self.numFollicles > 1 else 0.5
            cmds.setAttr(f"{follicleShape}.parameterU", u)
            cmds.setAttr(f"{follicleShape}.parameterV", 0.5)

    def createBindJoints(self):
        """
        Creates one bind joint per follicle, parented under startjoint and constrained to the follicle .

        Stores:
            self.BindJoints (list) joint names
        """
        self.BindJoints = []
        for index, follicle in enumerate(self.ribbonFollicles):
            cmds.select(clear=True)
            joint = cmds.joint(
                name=f"{self.name}_follicle{index + 1:02d}_BIND{self.suffix['joint']}"
            )
            cmds.matchTransform(joint, follicle, pos=True, rot=True)
            cmds.parent(joint, self.startJoint)
            self.BindJoints.append(joint)
        
        for j, f in zip(self.BindJoints, self.ribbonFollicles):
            cmds.parentConstraint(f, j, mo = False)

    def createDriverJoints(self):
        """
        Creates driver joints evenly spaced in world space along the ribbon.
        Fixed: positions are now proper (x,y,z) tuples in world space.

        Stores:
            self.DriverJoints (list) joint names
        """
        self.DriverJoints = []

        A = om.MVector(self.jointPlacements[0])
        B = om.MVector(self.jointPlacements[1])

        for index in range(self.numDrivers):
            cmds.select(clear=True)
            t = index / (self.numDrivers - 1) if self.numDrivers > 1 else 0.5
            pos = A + (B - A) * t                 # lerp along ribbon direction

            joint = cmds.joint(
                name=f"{self.name}_Driver{index:02d}{self.suffix['joint']}"
            )
            cmds.xform(joint, ws=True, t=(pos.x, pos.y, pos.z))
            self.DriverJoints.append(joint)

    def bindRibbon(self):
        """Binds the driver joints to the NURBS plane via a skin cluster."""
        cmds.skinCluster(
            self.DriverJoints,
            self.RibbonPlane,                 
            toSelectedBones=True,
            bindMethod=0,                  
            skinMethod=0,                         
            normalizeWeights=1,
            name=f"{self.name}{self.suffix['skinCluster']}",
        )

    def groupAndClean(self):
        """
        Organises ribbon nodes into a tidy hierarchy:
        """
        self.ribbonGrp = cmds.group(em=True, name=f"{self.name}_RBN_GRP")
        self.geoGrp = cmds.group(em=True, name=f"{self.name}_geo_GRP",parent=self.ribbonGrp)
        self.folliclesGrp = cmds.group(em=True, name=f"{self.name}_follicles_GRP", parent=self.ribbonGrp)
        self.driversGrp = cmds.group(em=True, name=f"{self.name}_drivers_GRP", parent=self.ribbonGrp)

        cmds.parent(self.RibbonPlane, self.geoGrp)
        cmds.parent(self.ribbonFollicles,self.folliclesGrp)
        cmds.parent(self.DriverJoints, self.driversGrp)

        cmds.setAttr(f"{self.geoGrp}.visibility",       0)
        cmds.setAttr(f"{self.folliclesGrp}.visibility", 0)

    def build(self):
        """Runs every step in the correct order."""

        self.lengthOfRibbon()
        self.creatingNurbsPlane()
        self.createFollicles()
        self.createBindJoints()
        self.createDriverJoints()
        self.bindRibbon()
        self.groupAndClean()
        print(f"[ribbonMaker] '{self.name}' built successfully.")
        return {
            "ribbonGrp":    self.ribbonGrp,
            "bindJoints":   self.BindJoints,
            "driverJoints": self.DriverJoints,
            "follicles":    self.ribbonFollicles,
        }