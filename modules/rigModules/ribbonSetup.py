import maya.cmds as cmds  # pyright: ignore[reportMissingImports]
import maya.api.OpenMaya as om # pyright: ignore[reportMissingImports]
import maya.mel as mel
import autoRigger.utils.config as config  # pyright: ignore[reportMissingImports]


# RIBBON MAKER

"""
add func for blendshapes: 
sine, wave. """

class RibbonMaker:
    def __init__(self, limb, side, numDrivers, numFollicles, startJoint, endJoint, switch):
        self.suffix = config.suffix
        self.prefix = config.prefix

        self.startJoint = startJoint
        self.endJoint = endJoint

        self.jointPlacements = []
        for joint in [startJoint, endJoint]:
            jointPlacement = cmds.xform(joint, q=True, ws=True, t=True)
            self.jointPlacements.append(jointPlacement)
        self.limbName = limb
        self.side = side

        self.numDrivers = numDrivers
        self.locs = []
        self.ctrls =[]
        self.numFollicles = numFollicles
        
        self.switch = switch

        self.name = f"{self.side}{self.limbName}_RBN"

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
            patchesU= self.numFollicles + 2,
            patchesV=1,
            width=self.RibbonLength,          # length runs along U
            lengthRatio=self.planeWidth / self.RibbonLength,
            name=self.name,
        )

        self.RibbonPlane = plane[0]      

            # keep the transform string, not the list
        self.RibbonPlaneShape = cmds.listRelatives(self.RibbonPlane, shapes=True)[0]

        sinePlane, sineHandle = self.addSineBlendshape()
        twistPlane, twistHandle = self.addTwistDeformer()

        handles = [twistHandle, sineHandle]

        cmds.xform(handles, ro=(0, 0, -90))
        cmds.makeIdentity(handles, a=True, r=True)

        cmds.parent(sinePlane, sineHandle, twistPlane, twistHandle, self.RibbonPlane) #temp parenting to the plane

        self.positionRibbonPlane() 
 
        cmds.parent(sinePlane, sineHandle, twistPlane, twistHandle, w = True)
        self.ribbonDeformerGrp = cmds.group(sinePlane, 
                                            sineHandle, 
                                            twistPlane, 
                                            twistHandle, 
                                            n = f"{self.name}ribbon_deformers_GRP")

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

        self.ribbonMtx = [
            aimVec.x,  aimVec.y,  aimVec.z,  0,
            upVec.x,   upVec.y,   upVec.z,   0,
            sideVec.x, sideVec.y, sideVec.z, 0,
            mid.x,     mid.y,     mid.z,     1,
        ]
        cmds.xform(self.RibbonPlane, ws=True, matrix=self.ribbonMtx)

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
            cmds.setAttr(f"{joint}.drawStyle", 3)
        
        for j, f in zip(self.BindJoints, self.ribbonFollicles):
            cmds.parentConstraint(f, j, mo = False)
        
        cmds.hide(self.BindJoints)

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

        count = self.numDrivers +2
        for index in range(count):
            cmds.select(clear=True)
            t = index / (count - 1) if self.numDrivers > 1 else 0.5
            pos = A + (B - A) * t                                                    # lerp along ribbon direction

            joint = cmds.joint(
                name=f"{self.name}_Driver{index:02d}{self.suffix['joint']}"
            )
            cmds.xform(joint, ws=True, t=(pos.x, pos.y, pos.z))
            cmds.matchTransform(joint, self.startJoint, rot = True)
            cmds.makeIdentity(joint, a = True, r = True)
            self.DriverJoints.append(joint)

            cmds.parentConstraint(self.startJoint, joint, n = joint.replace(self.suffix['joint'], self.suffix['parentCon']), mo = True)
    
    def createDriverJointsControls(self):
        self.startLoc = cmds.spaceLocator(n = f"{self.name}{config.suffix['control']}{config.suffix['locator']}")[0]
        cmds.matchTransform(self.startLoc, self.startJoint, pos = True, rot = True)

        for i, joint in enumerate(self.DriverJoints):

            if i == 0 or i == len(self.DriverJoints) -1: 
                continue
            loc = cmds.spaceLocator(n = f"{joint}{config.suffix['locator']}")[0]
            self.locs.append(loc)
            cmds.parent(loc, self.startLoc)

            cmds.matchTransform(loc, joint, pos = True, rot = True)
            ctrl = cmds.circle(n = f"{joint}{config.suffix['control']}", r = 4, nr = (1,0,0))[0]
            self.ctrls.append(ctrl)
            
            cmds.matchTransform(ctrl, joint, rot = True, pos = True)    
            cmds.parent(ctrl, loc)
            cmds.makeIdentity(ctrl, a = True, t = True, r = True)
            
            cmds.parentConstraint(ctrl, joint, name = f"{joint}{self.suffix['parentCon']}", mo = True)
        


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

        self.ribbonGrp = cmds.group(em=True, name=f"{self.name}_RIBBONS_GRP")
        ctrlGrp = cmds.group(em = True, n = f"{self.name}_CTRL_GRP", parent = self.ribbonGrp)
        self.geoGrp = cmds.group(em=True, name=f"{self.name}_geo_GRP", parent=self.ribbonGrp)
        self.folliclesGrp = cmds.group(em=True, name=f"{self.name}_follicles_GRP", parent=self.ribbonGrp)
        self.driversGrp = cmds.group(em=True, name=f"{self.name}_drivers_GRP", parent=self.ribbonGrp)

        cmds.parentConstraint(self.startJoint, ctrlGrp, 
                              n= f"{self.name}{config.suffix['parentCon']}", 
                              mo = False)
        cmds.parent(self.startLoc, ctrlGrp)

        cmds.parent(self.RibbonPlane, self.geoGrp)
        cmds.parent(self.ribbonFollicles,self.folliclesGrp)
        cmds.parent(self.DriverJoints, self.driversGrp)
        cmds.parent(self.ribbonDeformerGrp, self.ribbonGrp)

        cmds.setAttr(f"{self.ribbonGrp}.inheritsTransform", 0)

        cmds.setAttr(f"{self.geoGrp}.visibility", 0)
        cmds.setAttr(f"{self.folliclesGrp}.visibility", 0)
        cmds.setAttr(f"{self.ribbonDeformerGrp}.visibility", 0)

        if not cmds.isConnected(f"{self.switch}.Ribbon_Ctrls", 
                                f"{self.startLoc}.visibility"):
            cmds.connectAttr(
                f"{self.switch}.Ribbon_Ctrls",
                f"{self.startLoc}.visibility")
    
    def addSineBlendshape(self):

        self.sineBSplane = cmds.duplicate(self.RibbonPlane, n = f"{self.name}_sine_blendshape")
        cmds.xform(self.sineBSplane, t = [0, 0, -10], r = True, ws = True)
        self.sineDef, sineHandle = cmds.nonLinear(self.sineBSplane, type='sine', n = f"{self.name}_sine")
        cmds.matchTransform(sineHandle, self.sineBSplane, pos=True, rot=True)

        return self.sineBSplane, sineHandle
    
    def addTwistDeformer(self):
        self.twistBSplane = cmds.duplicate(self.RibbonPlane, n = f"{self.name}_twist_blendshape")
        cmds.xform(self.twistBSplane, t = [0, 0, -10], r = True, ws = True)
        self.twistDef, twistHandle = cmds.nonLinear(self.twistBSplane, type='twist', n = f"{self.name}_twist")
        cmds.matchTransform(twistHandle, self.twistBSplane, pos=True, rot=True)

        return self.twistBSplane, twistHandle

    def addBlendshapeControls(self):
        sineBs = cmds.blendShape(self.sineBSplane, self.RibbonPlane, n = f"{self.name}_sine_BS" )
        twistBs = cmds.blendShape(self.twistBSplane, self.RibbonPlane, n = f"{self.name}_twist_BS" )

        if not cmds.attributeQuery("Ribbon_Deformers", node=self.switch, exists=True):  
            cmds.addAttr(self.switch, ln = "Ribbon_Deformers", at = "enum", en = "____________", k = True)

        if not cmds.attributeQuery("Ribbon_Ctrls", node=self.switch, exists=True):
            cmds.addAttr(
                        self.switch,
                        ln="Ribbon_Ctrls",
                        at="bool",
                        dv=0,
                        k=True)

        cmds.connectAttr(
            f"{self.switch}.Ribbon_Ctrls",
            f"{self.startLoc}.visibility",
            force=True)
            
        """        cmds.addAttr(self.switch, ln = "Twist_controls", at = "enum", en = "____________", k = True)
                cmds.addAttr(self.switch, ln = f"{self.side}{self.limbName}Twist_Upper", at = "double", dv = 0, k = True)
                cmds.addAttr(self.switch, ln = f"{self.side}{self.limbName}Twist_Lower", at = "double", dv = 0, k = True)
        """
        #cmds.connectAttr(f"{self.endJoint}.rotateX", f"{self.twistDef}.endAngle")
        #cmds.connectAttr(f"{self.startJoint}.rotateX", f"{self.twistDef}.startAngle")
        #print(cmds.connectAttr(f"{self.endJoint}.rotateX", f"{self.twistDef}.endAngle"))

        for suffix in ["Upper", "Lower"]:
            cmds.addAttr(self.switch, 
                     ln = f"{self.side}{self.limbName}{suffix}_Sine", 
                     at = "enum", 
                     en = "____________", 
                     k = True)
            
            longname = [f"{self.limbName}SineOffset_{suffix}",
                        f"{self.limbName}SineAmplitude_{suffix}", 
                        f"{self.limbName}SineWavelength_{suffix}"]
            
            nicename = ["Offset",
                        "Amplitude",
                        "Wavelength"]

            for ln, nn in zip(longname, nicename):
                cmds.addAttr(self.switch, 
                        ln = ln, 
                        nn = nn, 
                        at = "double", 
                        dv = 0, 
                        k = True)

        


    def build(self):
        """Runs every step in the correct order."""

        self.lengthOfRibbon()
        self.creatingNurbsPlane()
        self.createFollicles()
        self.createBindJoints()
        self.createDriverJoints()
        self.createDriverJointsControls()
        self.bindRibbon()
        self.addBlendshapeControls()
        self.groupAndClean()

        print(f"\n [ribbonMaker] '{self.name}' built successfully. \n ")
        return {
            "ribbonGrp":    self.ribbonGrp,
            "bindJoints":   self.BindJoints,
            "driverJoints": self.DriverJoints,
            "follicles":    self.ribbonFollicles,
        }