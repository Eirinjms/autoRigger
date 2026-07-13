import string
import maya.cmds as cmds  # pyright: ignore[reportMissingImports]
import maya.api.OpenMaya as om  # pyright: ignore[reportMissingImports]
from autoRigger.utils import config, hierarchyModule


class ProceduralSpine:
    def __init__(self):
        self.jointAmount = 0
        self.curvature = 0

        self.oldSpinelocators = []
        self.newSpinelocators = []
        self.positions = []
    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC
    # ─────────────────────────────────────────────────────────────────────────

    def updateSpine(self, jointAmount):
        self.jointAmount = jointAmount
        self.spineFunc()

    def updateCurvature(self, curvatureAmount):
        self.curvature  = curvatureAmount
        self.curveSpineMath()

    def spineFunc(self):
        cmds.undoInfo(openChunk=True)
        try:
            self.spineJointNumber = self.jointAmount
            self.spineLocators(self.spineJointNumber)

            if self.oldSpinelocators:
                self.deletingSpine(self.oldSpinelocators)
            elif self.newSpinelocators:
                self.deletingSpine(self.newSpinelocators)

            self.spineLocMath()

            if self.jointAmount != 0:
                self.curveSpineMath()
            
            cmds.parent(self.spineEnd, self.newSpinelocators[-1])
            cmds.parent(self.newSpinelocators[0], self.spineRoot)

        finally:
            cmds.undoInfo(closeChunk=True)

    # ─────────────────────────────────────────────────────────────────────────
    # LOCATOR SETUP
    # ─────────────────────────────────────────────────────────────────────────

    def spineLocators(self, spineJointNumber):
        self.jointAmount = spineJointNumber

        self.spineRoot = cmds.listRelatives("root_JA_GUIDE", children=True, type='transform')[0]
        print(self.spineRoot)

        self.spineEnd = "C_spineJEnd_GUIDE"

        if self.spineEnd is None:
            return print("No spine End locator found")
        elif self.spineRoot is None:
            return print("No spine root was found")

        self.oldSpinelocators = cmds.ls("*spine*", type='transform')

        if self.spineRoot in self.oldSpinelocators:
            self.oldSpinelocators.remove(self.spineRoot)

        if self.spineEnd in self.oldSpinelocators:
            self.oldSpinelocators.remove(self.spineEnd)

    def spineLocMath(self):

        self.newSpinelocators.clear()
        self.positions.clear()

        self.rootLocalPos, _ = config.getGuidePos(self.spineRoot)
        self.endLocalPos, _ = config.getGuidePos(self.spineEnd)

        self.SRVECTOR = om.MVector(self.rootLocalPos)
        self.SEVECTOR = om.MVector(self.endLocalPos)

        distanceVector = self.SEVECTOR - self.SRVECTOR
        distanceBetweenJoints = distanceVector.length() / (self.jointAmount + 1)
        self.direction = distanceVector.normal()

        self.positions = []
        for i in range(1, self.jointAmount + 1):
            pos = self.SRVECTOR + self.direction * distanceBetweenJoints * i
            self.positions.append(pos)

        for index, (pos, letter) in enumerate(zip(self.positions, string.ascii_uppercase[1:])):
            spinename = f"C_spineJ{letter}_GUIDE"
            loc = cmds.spaceLocator(n=spinename)[0]
            cmds.xform(loc, t=pos, ws=True)
            self.newSpinelocators.append(spinename)

            if index > 0:
                cmds.parent(loc, self.newSpinelocators[index - 1])

    # ─────────────────────────────────────────────────────────────────────────
    # CURVE OFFSET
    # ─────────────────────────────────────────────────────────────────────────

    def curveSpineMath(self):
        cmds.undoInfo(openChunk=True)
        try:
            worldUp = om.MVector(0, 0, 1)

            perpendicular = self.direction ^ worldUp
            perpendicular.normalize()

            middle = (self.SRVECTOR + self.SEVECTOR) * 0.5
            curvatureMultiplier = self.curvature
            controlPos = middle + om.MVector(0, 0, curvatureMultiplier)

            curveloc = cmds.spaceLocator(n="spineCurvature_GUIDE")[0]
            cmds.xform(curveloc, t=controlPos, ws=True)
            cmds.makeIdentity(curveloc, a=True, t=True)

            curvepoints = []
            for loc in [self.spineRoot, curveloc, self.spineEnd]:
                pos, _ = config.getGuidePos(loc)
                curvepoints.append(pos)

            curve = cmds.curve(d=3, ep=curvepoints, n="temp_curve")
            cmds.rebuildCurve(curve, d=3,
                              rpo=True,
                              kep=True,
                              s=self.spineJointNumber + 1,
                              n="tempCurve_rebuilt",
                              rt=0)

            cvs = cmds.ls(f"{curve}.ep[*]", fl=True)

            for cv, jnt in zip(cvs[1:-1], self.newSpinelocators):
                position = cmds.xform(cv, q=True, t=True, ws=True)
                cmds.xform(jnt, t=position, ws=True)

            cmds.delete(curve)
            cmds.delete(curveloc)
            curvepoints.clear()
            
        finally:
            cmds.undoInfo(closeChunk=True)

    # ─────────────────────────────────────────────────────────────────────────
    # CLEANUP
    # ─────────────────────────────────────────────────────────────────────────

    def deletingSpine(self, joints: list):

        cmds.parent(self.spineEnd, w=True)

        cmds.delete(joints)
