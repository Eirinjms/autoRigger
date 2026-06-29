from PySide6 import QtWidgets # pyright: ignore[reportMissingImports]
from PySide6.QtCore import QFile # pyright: ignore[reportMissingImports]
from PySide6.QtUiTools import QUiLoader # pyright: ignore[reportMissingImports]
from PySide6.QtWidgets import QFileDialog # pyright: ignore[reportMissingImports]
from shiboken6 import wrapInstance # pyright: ignore[reportMissingImports]
import os
import json

import maya.cmds as cmds # pyright: ignore[reportMissingImports]
import maya.mel as mel # pyright: ignore[reportMissingImports]
import maya.OpenMayaUI as om # pyright: ignore[reportMissingImports]
import autoRigger.modules.builderModules.buildRig as buildRig
import autoRigger.utils.config as config
import autoRigger.modules.builderModules.jointGeneration as jointGen
import importlib

importlib.reload(jointGen)


def getMayaWindow():
    mayaWindow = wrapInstance(int(om.MQtUtil.mainWindow()), QtWidgets.QWidget)
    return mayaWindow


class AutoRiggerUI(QtWidgets.QDialog):
    def __init__(self, ui_file_path, parent=None):
        super().__init__(parent or getMayaWindow())

        self.locator = None
        self.locatorList = []
        self.jointsList = []
        self.ui = None


        self._loadUi(ui_file_path)
        self._connectWidgets()

    def _loadUi(self, ui_file_path):
        if not os.path.exists(ui_file_path):
            print("File not found.")
            return

        file = QFile(ui_file_path)
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.ui = loader.load(file, parentWidget=self)
        file.close()

        # put the loaded UI into this dialog
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.ui)
        

    def _connectWidgets(self):
        if self.ui is None:
            return

        self.allLocatorsRadio = self.ui.findChild(QtWidgets.QRadioButton, "radioButton_3")
        self.selectedLocatorsRadio = self.ui.findChild(QtWidgets.QRadioButton, "radioButton_4")

        rigBuildBtn = self.ui.findChild(QtWidgets.QPushButton, "buildRigButton")


        #-----------------------------------locator buttons -----------------------------------------------#
        createLocBtn = self.ui.findChild(QtWidgets.QPushButton, "GenerateLocators_Bipedal")
        importPresetBtn = self.ui.findChild(QtWidgets.QPushButton, "ImportPreset_Locators")
        slider = self.ui.findChild(QtWidgets.QSlider, "horizontalSlider_7")
        self.sizeLabel = self.ui.findChild(QtWidgets.QLabel, "TwistJoint_Number_2")
        self.locatorSymmetry = self.ui.findChild(QtWidgets.QCheckBox, "LocatorSymmetry_Bipedal")
        
        #-----------------------------------joint buttons -----------------------------------------------#
        generateJointsBtn = self.ui.findChild(QtWidgets.QPushButton, "GenerateJoints_Bipedal")
        unparentJointsBtn = self.ui.findChild(QtWidgets.QPushButton, "UnparentJointHierarchy_Bipedal")
        reparentJointsBtn = self.ui.findChild(QtWidgets.QPushButton, "ReparentJointHierarchy_Bipedal")

        importRevFeetLocsBtn = self.ui.findChild(QtWidgets.QPushButton, "ImportPreset_reverseFeet_Locators")

        exportJoints =  self.ui.findChild(QtWidgets.QPushButton, "ExportJoints_JSON_Bttn")
        self.exportJointsFilename = self.ui.findChild(QtWidgets.QLineEdit, "exportJointsFilename_text")

        mirrorOrientationBtn = self.ui.findChild(QtWidgets.QPushButton, "mirrorJointOrientation_Btn")
        self.leftToRight = self.ui.findChild(QtWidgets.QRadioButton, "jointMirror_leftToRight_radio")
        self.rightToLeft = self.ui.findChild(QtWidgets.QRadioButton, "jointMirror_rightToLeft_radio")

        #-----------------------------------joint text areas -----------------------------------------------#
        self.importPresetText = self.ui.findChild(QtWidgets.QLineEdit, "ImportPreset_LineEdit")
        self.revFeetTextBox = self.ui.findChild(QtWidgets.QLineEdit, "reverseFeet_Locators_editLine")

        self.revFeetSymmetry = self.ui.findChild(QtWidgets.QCheckBox, "LocatorSymmetry_ReverseFeet")
        self.MirrorRevFeet = self.ui.findChild(QtWidgets.QPushButton, "MirrorReverseFeet")


        #-----------------------------------connections -----------------------------------------------#

        if rigBuildBtn:
            rigBuildBtn.clicked.connect(self.buildRigButton)

        if exportJoints:
            exportJoints.clicked.connect(self.exportJointsjson)
        
        #-----------------------------------Locator connections -----------------------------------------------#
        if createLocBtn:
            createLocBtn.clicked.connect(self.buildLocators)
        if importPresetBtn:
            importPresetBtn.clicked.connect(lambda : self.importPreset(self.importPresetText, True))
        if generateJointsBtn:
            generateJointsBtn.clicked.connect(self.generateJoints)

        self.slider = slider
        if slider:
            slider.valueChanged.connect(self.locatorSize)
            slider.valueChanged.connect(self.updateSizeLabel)
            
        if self.locatorSymmetry:
            self.locatorSymmetry.toggled.connect(self.symmetryToggle)

        

        #-----------------------------------rev feet connections -----------------------------------------------#
        if self.MirrorRevFeet: 
            self.MirrorRevFeet.clicked.connect(lambda : self.mirrorLocators("L_backOfHeel_LOC"))

        if self.revFeetSymmetry: 
            self.MirrorRevFeet.toggled.connect(self.symmetryToggle)

        if importRevFeetLocsBtn:
            importRevFeetLocsBtn.clicked.connect(lambda: self.importPreset(self.revFeetTextBox, storeLocators = False))            


        #-----------------------------------joint connections -----------------------------------------------
        if unparentJointsBtn:
            unparentJointsBtn.clicked.connect(self.unparentJointHierarchy)

        if reparentJointsBtn:
            reparentJointsBtn.clicked.connect(self.reparentJointHierarchy)

        if mirrorOrientationBtn:
            mirrorOrientationBtn.clicked.connect(self.mirrorOrientation)
            


        # keep slider/label in sync with whatever locator is selected in the scene
        self.selectionJob = cmds.scriptJob(
            event=["SelectionChanged", self.syncSliderToSelection],
            protected=True,
        )

    def exportJointsjson(self):
        file_name = self.exportJointsFilename.text()
        exp = jointGen.jointGeneration()
        exp.jointExportJSON(file_name)
    

    def importPreset(self, textBox, storeLocators : bool):
        """
        the function doing thangs

            Parameters: 
                textBox : which UI box you wanna fill
                storeLocators(bool) : if you want to append to the loc list
        
        """
        folder = config.find_file_path("presets")
        print(folder)
        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Locator Preset",
            folder,
            "JSON Files (*.json)",
        )

        if textBox:
            textBox.setText(filePath)

        if not filePath:
            return  # user cancelled

        try:
            with open(filePath, "r") as f:
                presetData = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Failed to load preset: {e}")
            return

        print(f"Loaded preset: {filePath}")
        self.applyPreset(presetData, storeLocators)
    
    def applyPreset(self, presetData, storeLocators):
        """Recreates the locator hierarchy from the loaded JSON dict.
        
            Parameters: 
                presetData : JSON file
        """
        
        cmds.undoInfo(openChunk = True)
        for root_name, root_data in presetData.items():
            self.build_locator(root_name, root_data, self.locatorList, storeLocators)
        cmds.undoInfo(closeChunk = True)

        cmds.select(self.locatorList, r = True)
        cmds.makeIdentity(apply = True, t = True)
    
    def build_joint(self, locator: str, parent=None):
        '''
        Creates a joint per given locator. 

        Parameters:
            locator (str): Locator transform to convert into a joint
            parent (str): Parent joint name, if any

        Returns:
            str: Name of the joint created for the supplied locator. 
        '''
            
        cmds.select(clear=True)

        pos = self.getGuidePos(locator)
        jointName = locator.replace('GUIDE', 'JNT')

        joint = cmds.joint(n=jointName)   
        self.jointsList.append(joint)      
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
        Recursively recreates a joint hierarchy from a locator hierarchy.

        This function traverses the locator hierarchy depth-first, creating one
        joint per locator while preserving naming, positions, and parenting.

        It is intended to be called once for each root locator. Child hierarchies
        are processed automatically through recursion.
        '''
        cmds.undoInfo(openChunk=True)
        try:
            if self.locatorSymmetry.isChecked():
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

    def build_locator(self, locator_name: str, joint_data: dict, locatorList, storeLocators, parent=None):
        '''
        Recursively creates locators from a joint hierarchy dict.

        Parameters:
            locator_name (str): Name to give the locator (JNT replaced with GUIDE )
            joint_data (dict): Dictionary of joint data including children
            parent (str): Parent locator name, if any
        '''
        cmds.select(clear=True)

        loc = cmds.spaceLocator(
            n=locator_name.replace('JNT', 'GUIDE'))[0]
        
        cmds.xform(loc,
                   ws=True,
                   t=joint_data["pos"]
                    )
    
        if parent:
            cmds.parent(loc, parent)

        if storeLocators == True:
            locatorList.append(loc)
        print(f"Created: {loc}")

        for child_name, child_data in joint_data["children"].items():
            self.build_locator(child_name, child_data, locatorList, storeLocators, loc)
            

    def getGuidePos(self, locator):
        shape = cmds.listRelatives(locator, shapes=True, type="locator")[0]
        transformPos = cmds.xform(locator, q=True, ws=True, t=True)
        localPos = cmds.getAttr(f"{shape}.localPosition")[0]

        return localPos        
    

    def build_reverseFeetLocators(self, presetData, storeLocators):
        """Recreates the locator hierarchy from the loaded JSON dict."""

        for root_name, root_data in presetData.items():
            self.build_locator(root_name, root_data, self.revFeetLocatorList, storeLocators)

        cmds.select(self.locatorList, r = True)
        cmds.makeIdentity(apply = True, t = True)

    def buildRigButton(self):
        """ Builds the rig :D """
        cmds.undoInfo(openChunk=True)
        try:
            buildRig.build()
        finally:
            cmds.undoInfo(closeChunk=True)

    def buildLocators(self):
        "Builds a Locator? "
        cmds.undoInfo(openChunk=True)
        try:
            self.locator = cmds.spaceLocator()[0]
            self.locatorList.append(self.locator)
            print(self.locator)
        finally:
            cmds.undoInfo(closeChunk=True)

    def syncSliderToSelection(self):
        """When a locator is selected, set the slider/label to its current scale."""
        selected = cmds.ls(sl=True) or []
        for obj in selected:
            shapes = cmds.listRelatives(obj, s=True) or []
            if shapes and cmds.nodeType(shapes[0]) == "locator":
                value = cmds.getAttr(f"{obj}.localScaleX")
                if self.slider:
                    self.slider.blockSignals(True)   # avoid re-triggering setAttr on every locator
                    self.slider.setValue(int(value))
                    self.slider.blockSignals(False)
                if self.sizeLabel:
                    self.sizeLabel.setText(str(value))
                return  # just sync to the first locator found
                

    def closeEvent(self, event):
        if getattr(self, "selectionJob", None):
            cmds.scriptJob(kill=self.selectionJob, force=True)
        super().closeEvent(event)

    def updateSizeLabel(self, value):
        if self.sizeLabel:
            self.sizeLabel.setText(str(value))

    def locatorSize(self, value):
        if self.allLocatorsRadio and self.allLocatorsRadio.isChecked():
            locators = self.locatorList
        else:
            selected = cmds.ls(sl=True)
            locators = []
            for obj in selected:
                shapes = cmds.listRelatives(obj, s=True) or []
                if shapes and cmds.nodeType(shapes[0]) == "locator":
                    locators.append(obj)

        cmds.undoInfo(openChunk = True)
        for locator in locators:
            for index in ['X', 'Y', 'Z']:
                cmds.setAttr(f"{locator}.localScale{index}", value)
        cmds.undoInfo(closeChunk = True)

    def mirrorLocators(self, sel):
        selection = cmds.ls(sl = True, long = True)

        if not sel:
            sel = selection
            if not selection:
                cmds.error("Please select what you want to mirror")

        originGrp = cmds.group(sel)

        duplicatedGrp = cmds.duplicate(originGrp, rc = True)[0]
        cmds.makeIdentity(duplicatedGrp, a = True, s = True)

        cmds.xform(duplicatedGrp, ws = True, piv = (0, 0, 0), s = (-1, 1, 1))

        children = cmds.listRelatives(duplicatedGrp, allDescendents = True)
        
        for child in children:
            if child.startswith("L_"):
                cmds.rename(child, child.replace("L_", "R_")
                            .replace("LOC1", "LOC"))
            elif child.startswith("R_"):
                cmds.rename(child, child.replace("R_", "L_")
                            .replace("LOC1", "LOC"))
            else: 
                cmds.rename(child, f"{child}_mirror")
            
        cmds.parent(cmds.listRelatives(duplicatedGrp, children = True), w = True)

        cmds.parent(cmds.listRelatives(originGrp, children = True), w = True)

        cmds.delete(originGrp, duplicatedGrp)


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

#################### joint based funcs #######################################

    def saveJointHierarchy(self):
        """
        Saves the hierarchy locally, for temporary parenting

        """
        self.joint_Hierarchy = {}

        for joint in self.jointsList: 
            parent = cmds.listRelatives(joint, 
                                        parent = True,
                                        type = 'joint'
                                        )
            self.joint_Hierarchy[joint] = parent[0] if parent else None
        
    def unparentJointHierarchy(self): 
        """
        unparents the hierarchy

        """
        cmds.undoInfo(openChunk = True)
        try:
            self.saveJointHierarchy()
            for joint in self.jointsList:
                if not "root_JA_JNT" in joint:
                    cmds.parent(joint, world = True)
        finally: 
            cmds.undoInfo(closeChunk = True)

    def reparentJointHierarchy(self):
        """
        Reparents based on prior saved hierarchy

        """
        cmds.undoInfo(openChunk = True)
        try:
            for joint in self.joint_Hierarchy:
                cmds.makeIdentity(joint, apply = True, r = True)
            for child, parent in self.joint_Hierarchy.items():
                if parent:
                    cmds.parent(child,parent)
        finally: 
            cmds.undoInfo(closeChunk = True)

    def jointOrientation(self):
        """
        Sets a basis for joint orientation across the skeleton (FOR BIPEDAL ONLY SO FAR)

        """
        cmds.joint("C_spineJA_JNT", 
                   e = True, 
                   oj = "xyz", 
                   sao = "yup", 
                   ch = True, 
                   zso = True)
        
        #spinejoints
        joints = cmds.ls("C_spine*",
                              "C_head*",
                              "C_neck*",
                              "*legJD*",
                              "*legJC*",
                               type='joint')

        self.unparentJointHierarchy()

        for joint in joints:
            pos = cmds.xform(joint, q = True, t = True, ws = True)
            loc = cmds.spaceLocator(n = f"{joint}_temp")[0]
            cmds.xform(loc, ws=True, t=(pos[0], pos[1] + 10, pos[2]))
            cmds.delete(cmds.aimConstraint(loc, joint, 
                                           offset = (90,0,0), 
                                           aimVector = (1,0,0), 
                                           upVector = (0,0,-1), 
                                           worldUpType = 'scene'))
            cmds.delete(loc)

        wristPairs = [
            ("L_armJD_JNT", "L_middleFngJEnd_JNT"),
            ("R_armJD_JNT", "R_middleFngJEnd_JNT")] 
        
        for joint, aim in wristPairs:
            cmds.delete(cmds.aimConstraint(aim, joint, 
                               aimVector = (1,0,0),
                               worldUpType = 'scene'))
        
        self.reparentJointHierarchy()

        #endjoints
        endjoints = cmds.ls("*End_JNT", type = 'joint')
        for joint in endjoints:
            cmds.joint(joint, e = True, zso = True, oj = 'none')

    
    def mirrorOrientation(self):
        """
        Mirrors joints based on input from UI
        """

        cmds.undoInfo(openChunk = True)
        try: 
            leftJoints = []
            rightJoints = []
            for joint in self.jointsList: 
                if joint.startswith("L_"):
                    leftJoints.append(joint)
                elif joint.startswith("R_"):
                    rightJoints.append(joint)
                else:
                    continue

            left = config.prefix['left']
            right = config.prefix['right']
            if self.leftToRight.isChecked():
                prefix = left
                mirror = right
                cmds.delete(rightJoints)

            elif self.rightToLeft.isChecked():
                prefix = right
                mirror = left
                cmds.delete(leftJoints)

            clavJoint = f"{prefix}armJA_JNT"
            hipJoint = f"{prefix}legJA_JNT"

            for joint in [clavJoint, hipJoint]:
                cmds.mirrorJoint(joint, 
                                mirrorBehavior = True,
                                mirrorYZ = True,
                                searchReplace = (prefix, mirror))
            
            cmds.selection(cl = True)
        finally: 
            cmds.undoInfo(closeChunk = True)

    #def showLocalRotationAxis(self): 


        

                    