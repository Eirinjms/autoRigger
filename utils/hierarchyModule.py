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
    def __init__(self, nodeList : list, freezeTrans : bool):

        self.hierarchy = {}
        self.freezeTrans = freezeTrans
        self.nodeList = nodeList

    def saveHierarchy(self):
        """
        Saves the hierarchy locally, for temporary parenting
        """

        self.hierarchy = {}

        for node in self.nodeList: 
            parent = cmds.listRelatives(node, 
                                        parent = True,
                                        )
            self.hierarchy[node] = parent[0] if parent else None
    
            
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
            for node in self.nodeList:
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