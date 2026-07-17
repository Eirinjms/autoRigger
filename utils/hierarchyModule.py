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
        for child in children: 
            self.hierarchy[child] = root
            self.climbHierarchy(child)

    def unparentHierarchy(self): 
        """
        unparents the hierarchy

        """
        cmds.undoInfo(openChunk = True)
        try:
            if not self.nodeList:
                return cmds.warning("No Hierarchy found")
            if len(self.hierarchy) != 0: 
                return cmds.warning("Hierarchy already saved, please reparent first!")            

            self.saveHierarchy()
            print(self.hierarchy)
            for node in self.hierarchy:
                if cmds.listRelatives(node, parent = True) is not None:  
                    cmds.parent(node, world = True)
        finally: 
            cmds.undoInfo(closeChunk = True)


    def reparentHierarchy(self):
        """
        Reparents based on prior saved hierarchy

        """
        cmds.undoInfo(openChunk = True)
        try:
            if self.freezeTrans:
                for node in self.hierarchy:
                    cmds.makeIdentity(node, apply = True, r = True)
            for child, parent in self.hierarchy.items():
                if parent:
                    cmds.parent(child,parent)
            
            self.hierarchy.clear()
            
        finally: 
            cmds.undoInfo(closeChunk = True)