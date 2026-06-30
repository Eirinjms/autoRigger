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
