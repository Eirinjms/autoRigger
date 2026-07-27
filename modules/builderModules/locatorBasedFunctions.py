import os
import json

import maya.cmds as cmds # pyright: ignore[reportMissingImports]
import maya.mel as mel # pyright: ignore[reportMissingImports]
import maya.api.OpenMaya as om # pyright: ignore[reportMissingImports]
import autoRigger.modules.builderModules.buildRig as buildRig
import autoRigger.utils.config as config    


def mirrorLocators(self, sel):
        mirrorGrp = cmds.ls(sl = True, long = True)
        print(mirrorGrp)

        if not sel:
            sel = mirrorGrp

        duplicatedObj = cmds.duplicate(sel, rc = True)

        dupeGRP = cmds.group(duplicatedObj, n = "duplicatedgroup")

        cmds.xform(dupeGRP, ws = True, piv = (0, 0, 0), s = (-1, 1, 1))

        cmds.ungroup(dupeGRP)

        mel.eval('searchReplaceNames "L_" "R_" "hierarchy";')
        mel.eval('searchReplaceNames "LOC1" "LOC" "hierarchy";')

        cmds.parent("R_innerSideFoot_LOC", "R_outerSideFoot_LOC")
        cmds.parent("R_outerSideFoot_LOC", "R_frontFoot_LOC")
        cmds.parent("R_frontFoot_LOC", "R_backOfHeel_LOC")

        cmds.makeIdentity(a = True, t = True, s = True, r = True)



def locator_symmetry(self): 
    cmds.undoInfo(openChunk = True)
    self.leftAttrs = []
    self.rightAttrs = []
    self.reverseNodes = []
    for left in self.locatorList:
        cmds.delete(left, ch = True)
        if left.startswith("L_"):
            right = left.replace("L_", "R_")

            if cmds.objExists(right):
                mulDiv = cmds.createNode('multiplyDivide', name = f"{right.replace('R_', '')}_MD")
                self.reverseNodes.append(mulDiv)

                for transform in ["translate", "rotate"]:
                    if transform == "rotate": 
                        axes = ["Z", "X", "Y"]
                    else: 
                        axes = ["X", "Y", "Z"]
                    cmds.connectAttr(f"{left}.{transform}{axes[0]}", f"{mulDiv}.input1{axes[0]}")
                    cmds.setAttr(f"{mulDiv}.input2{axes[0]}", -1) 
                    cmds.connectAttr(f"{mulDiv}.output{axes[0]}", f"{right}.{transform}{axes[0]}")

                    for i in axes[1::]: 
                        leftAttr = f"{left}.{transform}{i}"
                        rightAttr = f"{right}.{transform}{i}"
                        cmds.connectAttr(leftAttr, rightAttr)
                        self.leftAttrs.append(leftAttr)
                        self.rightAttrs.append(rightAttr)
                    
            print(f"successfully connected {left} with {right}")
    cmds.undoInfo(closeChunk = True)

def disconnectSymmetry(self):
    cmds.undoInfo(openChunk = True)
    if self.leftAttrs and cmds.isConnected(self.leftAttrs[0], self.rightAttrs[0]):
        for leftNode, RightNode in zip(self.leftAttrs, self.rightAttrs):
            cmds.disconnectAttr(leftNode, RightNode)
        cmds.delete(self.reverseNodes)
        print("Successfully disconnected symmetry from all nodes")
    else:
        print("no connections found")
    cmds.undoInfo(closeChunk = True)

def symmetryToggle(self, checked):

    if checked:
        self.locator_symmetry()

    else:
        self.disconnectSymmetry()

import maya.cmds as cmds  # pyright: ignore[reportMissingImports]
import maya.api.OpenMaya as om  # pyright: ignore[reportMissingImports]


def getGuidePos(locator):
    '''
    Returns true world-space position of a locator, accounting for
    spaceLocator(p=...) storing the position on the shape's localPosition
    rather than the transform's translate.
    '''
    shape = cmds.listRelatives(locator, shapes=True, type="locator")
    transformPos = cmds.xform(locator, q=True, ws=True, t=True)

    if shape:
        localPos = cmds.getAttr(f"{shape[0]}.localPosition")[0]
        return [transformPos[i] + localPos[i] for i in range(3)]

    return transformPos


def poleVectorVisualization(sel, pvDistance):
    '''
    Enables a visualization of the polevector, creating a polygon.
    '''
    pv = findpoleVector(sel, pvDistance)

    joint_positions = []
    for joint in sel:
        pos, _ = config.getGuidePos(joint)
        joint_positions.append(tuple(pos))
    joint_positions.append((pv.x, pv.y, pv.z))

    pvVis = cmds.polyCreateFacet(
        p=joint_positions,
        n=f"{sel[0]}_PV_Visualization"
    )[0]

    cmds.setAttr(f"{pvVis}.displayTriangles", 1)
    cmds.setAttr("openPBR_shader1.baseColor", 1, 0, 0.7, type="double3")
    cmds.setAttr("openPBR_shader1.baseDiffuseRoughness", 1)

    return pvVis


def findpoleVector(sel, pvDistance):
    '''
    Calculates a pole vector position using the plane defined by
    the start, mid, and end joints. 
    '''

    local0, world0 = config.getGuidePos(sel[0])
    local1, world1 = config.getGuidePos(sel[1])
    local2, world2 = config.getGuidePos(sel[-1])

    pos0 = config.addTuples(local0, world0)
    pos1 = config.addTuples(local1, world1)
    pos2 = config.addTuples(local2, world2)

    H = om.MVector(*pos0)
    K = om.MVector(*pos1)
    A = om.MVector(*pos2)

    HK = K - H
    HA = A - H

    dot = HK * HA

    proj = (dot/(HA.length()**2)) * HA

    projK = HK - proj

    pv = (projK * pvDistance) + K

    return pv