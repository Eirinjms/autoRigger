import maya.cmds as cmds

class hierarchyManager:
    """
    Stores the hierarchy of a list of nodes, allowing them to be
    temporarily unparented and later restored.

    The original hierarchy is automatically cached when
    `unparentHierarchy()` is called.

        Parameters: 
            nodeList (list[str]): Nodes whose hierarchy will be managed.
            freezeTrans (bool): If True, freeze the nodes' transforms
                                before restoring the hierarchy. Primarily intended for joint
                                workflows.
    """
    def __init__(self, nodeList : list, freezeTrans : bool, typeOfNode : str):

        self.hierarchy = {}
        self.freezeTrans = freezeTrans
        self.nodeList = nodeList
        self.type = typeOfNode

    def saveHierarchy(self):

        self.hierarchy = {}
        roots = []
        for node in self.nodeList:
            if not cmds.objExists(node):
                continue
            parent = cmds.listRelatives(node, 
                                        parent = True)
            
            if parent is None: 
                root = node
                roots.append(root)
            
        for root in roots:
            self.hierarchy[root] = None
            self.climbHierarchy(root)
    
    def climbHierarchy(self, root):
        children = cmds.listRelatives(root, children = True, type = self.type) or []
        hierarchy = []
        for child in children: 
            self.hierarchy[child] = root
            hierarchy.append(child)
            hierarchy.extend(self.climbHierarchy(child))
        
        return hierarchy

    def unparentHierarchy(self): 
        """
        unparents the hierarchy

        """
        cmds.undoInfo(openChunk = True)
        try:
            if not self.nodeList:
                return cmds.warning("No Hierarchy found")
            if len(self.hierarchy) != 0: 
                return cmds.warning("Hierarchy already unparented, please reparent first!")            

            self.saveHierarchy()
            for node in self.hierarchy:
                if cmds.listRelatives(node, parent = True) is not None:  
                    cmds.parent(node, world = True)
        finally: 
            cmds.select(clear = True)
            cmds.undoInfo(closeChunk = True)


    def reparentHierarchy(self):
        """
        Reparents based on prior saved hierarchy

        """
        cmds.undoInfo(openChunk = True)
        try:
            if self.freezeTrans:
                for node in self.hierarchy:
                    if cmds.objExists(node):
                        cmds.makeIdentity(node, apply = True, r = True)
                    else: 
                        continue
            for child, parent in self.hierarchy.items():
                if parent:
                    if not cmds.objExists(parent):
                        cmds.warning(f"{parent} not found, moving to next joint")
                        continue
                    if not cmds.objExists(child):
                        cmds.warning(f"{child} not found, moving to next joint")
                        continue
                    cmds.parent(child,parent)
            
            self.hierarchy.clear()
            
        finally: 
            cmds.select(clear = True)
            cmds.undoInfo(closeChunk = True)