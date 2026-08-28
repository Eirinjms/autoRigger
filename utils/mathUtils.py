import config
import string
import maya.cmds as cmds
import maya.openMaya.api as om

def interpolatePositions(startGuide, endGuide, amount):
    positions = []

    startLocalPos, startWorldPos = config.getGuidePos(startGuide)
    endLocalPos, endWorldPos = config.getGuidePos(endGuide)

    startPos = tuple(a + b for a, b in zip(startLocalPos, startWorldPos))
    endPos = tuple(a + b for a, b in zip(endLocalPos, endWorldPos))

    startVector = om.MVector(startPos)
    endVector = om.MVector(endPos)

    distanceVector = endVector - startVector
    distanceBetweenPoints = distanceVector.length() / (amount + 1)
    direction = distanceVector.normal()

    for i in range(1, amount + 1):
        pos = startVector + direction * distanceBetweenPoints * i
        positions.append(pos)

    return positions