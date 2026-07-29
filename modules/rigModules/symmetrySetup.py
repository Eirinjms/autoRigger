import maya.cmds as cmds

class symmetry:
    def __init__(self, locatorList):

        self.locatorList = locatorList

        self.leftAttrs = []
        self.rightAttrs = []
        self.reverseNodes = []

    def locator_symmetry(self): 
        cmds.undoInfo(openChunk = True)
        try:
            for left in self.locatorList:
                cmds.delete(left, ch = True)
                if left.startswith("L_"):
                    right = left.replace("L_", "R_")
                    print(right)
                    print(cmds.listConnections(f"{right}.translateX",
                                            source=True,
                                            destination=False,
                                            plugs=True))
                    cmds.makeIdentity(right, apply = True, t = True, r = True)

                    if cmds.objExists(right):
                        for transform in ["translate", "rotate"]:
                            mulDiv = cmds.createNode('multiplyDivide', name = f"{right.replace('R_', '')}{transform}_MD")
                            self.reverseNodes.append(mulDiv)

                            allAxes = ["Z", "Y", "X"]

                            if transform == "rotate": 
                                negatedAxes = ["Z", "Y"]
                                copiedAxes = [axis for axis in allAxes if axis not in negatedAxes]

                            else: 
                                negatedAxes = ["X"]
                                copiedAxes = [axis for axis in allAxes if axis not in negatedAxes]

                            for axis in negatedAxes:
                                cmds.connectAttr(f"{left}.{transform}{axis}", f"{mulDiv}.input1{axis}")
                                cmds.setAttr(f"{mulDiv}.input2{axis}", -1) 
                                cmds.connectAttr(f"{mulDiv}.output{axis}", f"{right}.{transform}{axis}")

                            for axis in copiedAxes:
                                leftAttr = f"{left}.{transform}{axis}"
                                rightAttr = f"{right}.{transform}{axis}"
                                cmds.connectAttr(leftAttr, rightAttr)
                                self.leftAttrs.append(leftAttr)
                                self.rightAttrs.append(rightAttr)
                            
                    print(f"successfully connected {left} with {right}")
        except Exception as e:
            print(e)            
        finally:
            cmds.undoInfo(closeChunk = True)

    def disconnectSymmetry(self):
        """
        Disconnects the symmetry by removing nodes and disconnecting sides
        """

        cmds.undoInfo(openChunk = True)
        try:
            if self.leftAttrs and cmds.isConnected(self.leftAttrs[0], self.rightAttrs[0]):
                for leftNode, RightNode in zip(self.leftAttrs, self.rightAttrs):
                    cmds.disconnectAttr(leftNode, RightNode)
                cmds.delete(self.reverseNodes)
                print("Successfully disconnected symmetry from all nodes")
            else:
                print("no connections found")
        finally:
            self.leftAttrs.clear()
            self.rightAttrs.clear()
            self.reverseNodes.clear()

            cmds.undoInfo(closeChunk = True)