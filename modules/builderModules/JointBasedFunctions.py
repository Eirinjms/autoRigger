def build_joint(self, locator: str, parent=None):
        '''
        Recursively creates joints from a locator hierarchy, matching position
        and naming (GUIDE replaced with JNT).

        Parameters:
            locator (str): Locator transform to convert into a joint
            parent (str): Parent joint name, if any
        '''
            
        cmds.select(clear=True)

        pos = self.getGuidePos(locator)
        jointName = locator.replace('GUIDE', 'JNT')

        joint = cmds.joint(n=jointName)         
        cmds.xform(joint, ws=True, t=pos)       

        if parent:
            joint = cmds.parent(joint, parent)[0]  
            
            cmds.xform(joint, ws=True, t=pos)

        print(f"Created: {joint}")

        children = cmds.listRelatives(locator, children=True, type="transform") or []
        for child in children:
            self.build_joint(child, joint)

        return joint

    def generateJoints(self):
        '''
        Builds a joint skeleton from whatever locators currently exist in
        self.locatorList, using only the root-level (unparented) locators
        as starting points so each hierarchy is only walked once.
        '''
        cmds.undoInfo(openChunk=True)
        try:
            if self.locatorSymmetry.isChecked:
                self.locatorSymmetry.setChecked(False)
            cmds.hide(self.locatorList)
            for loc in self.locatorList:
                cmds.makeIdentity(loc, 
                                apply = True, 
                                t = True, 
                                r = True)
            
            roots = []
            for loc in self.locatorList:
                if not cmds.objExists(loc):
                    continue
                parent = cmds.listRelatives(loc, parent=True)
                if not parent:
                    roots.append(loc)

            for root in roots:
                self.build_joint(root)
            
            self.jointOrientation()
        finally:
            cmds.undoInfo(closeChunk=True)

    def saveJointHierarchy(self):
        self.jointList = cmds.ls("*_JNT", type = 'joint')
        self.joint_Hierarchy = {}

        for joint in self.jointList: 
            parent = cmds.listRelatives(joint, 
                                        parent = True,
                                        type = 'joint'
                                        )
            self.joint_Hierarchy[joint] = parent[0] if parent else None
        
    def unparentJointHierarchy(self): 
        self.saveJointHierarchy()
        cmds.parent(self.jointList, world = True)

    def reparentJointHierarchy(self):
        for child, parent in self.joint_Hierarchy.items():
            if parent:
                cmds.parent(child,parent)
