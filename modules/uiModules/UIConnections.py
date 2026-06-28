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
import autoRigger.buildRig as buildRig
import autoRigger.utils.config as config
import autoRigger.modules.builderModules.jointGeneration as jointGen


def getMayaWindow():
    return wrapInstance(int(om.MQtUtil.mainWindow()), QtWidgets.QWidget)


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

        #locator buttons
        createLocBtn = self.ui.findChild(QtWidgets.QPushButton, "GenerateLocators_Bipedal")
        importPresetBtn = self.ui.findChild(QtWidgets.QPushButton, "ImportPreset_Locators")
        slider = self.ui.findChild(QtWidgets.QSlider, "horizontalSlider_7")
        self.sizeLabel = self.ui.findChild(QtWidgets.QLabel, "TwistJoint_Number_2")
        self.locatorSymmetry = self.ui.findChild(QtWidgets.QCheckBox, "LocatorSymmetry_Bipedal")
        
        #joint Buttons
        generateJointsBtn = self.ui.findChild(QtWidgets.QPushButton, "GenerateJoints_Bipedal")
        unparentJointsBtn = self.ui.findChild(QtWidgets.QPushButton, "UnparentJointHierarchy_Bipedal")
        reparentJointsBtn = self.ui.findChild(QtWidgets.QPushButton, "ReparentJointHierarchy_Bipedal")

        importRevFeetLocsBtn = self.ui.findChild(QtWidgets.QPushButton, "ImportPreset_reverseFeet_Locators")

        exportJoints =  self.ui.findChild(QtWidgets.QPushButton, "ImportPreset_reverseFeet_Locators")

        #joint text areas
        self.importPresetText = self.ui.findChild(QtWidgets.QLineEdit, "ImportPreset_LineEdit")
        self.revFeetTextBox = self.ui.findChild(QtWidgets.QLineEdit, "reverseFeet_Locators_editLine")

        self.revFeetSymmetry = self.ui.findChild(QtWidgets.QCheckBox, "LocatorSymmetry_ReverseFeet")
        self.MirrorRevFeet = self.ui.findChild(QtWidgets.QPushButton, "MirrorReverseFeet")

        if rigBuildBtn:
            rigBuildBtn.clicked.connect(self.buildRigButton)
        
        #locator buttons
        if createLocBtn:
            createLocBtn.clicked.connect(self.buildLocators)
        if importPresetBtn:
            importPresetBtn.clicked.connect(lambda : self.importPreset(self.importPresetText))
        if generateJointsBtn:
            generateJointsBtn.clicked.connect(self.generateJoints)

        self.slider = slider
        if slider:
            slider.valueChanged.connect(self.locatorSize)
            slider.valueChanged.connect(self.updateSizeLabel)
            
        if self.locatorSymmetry:
            self.locatorSymmetry.toggled.connect(self.symmetryToggle)

        
        #Rev feet
        if self.MirrorRevFeet: 
            self.MirrorRevFeet.clicked.connect(lambda : self.mirrorLocators("L_backOfHeel_LOC"))

        if self.revFeetSymmetry: 
            self.MirrorRevFeet.toggled.connect(self.symmetryToggle)

        if importRevFeetLocsBtn:
            importRevFeetLocsBtn.clicked.connect(lambda: self.importPreset(self.revFeetTextBox))            

        #joint buttons
        if unparentJointsBtn:
            unparentJointsBtn.clicked.connect(self.unparentJointHierarchy)

        if reparentJointsBtn:
            reparentJointsBtn.clicked.connect(self.reparentJointHierarchy)
            


        # keep slider/label in sync with whatever locator is selected in the scene
        self.selectionJob = cmds.scriptJob(
            event=["SelectionChanged", self.syncSliderToSelection],
            protected=True,
        )

    def importPreset(self, textBox):
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
        self.applyPreset(presetData)
    
    def applyPreset(self, presetData):
        """Recreates the locator hierarchy from the loaded JSON dict.
        
            Parameters: 
                presetData : JSON file
        """
        

        cmds.undoInfo(openChunk = True)
        for root_name, root_data in presetData.items():
            self.build_locator(root_name, root_data, self.locatorList)
        cmds.undoInfo(closeChunk = True)

        cmds.select(self.locatorList, r = True)
        cmds.makeIdentity(apply = True, t = True)

    def getGuidePos(self, locator):
        shape = cmds.listRelatives(locator, shapes=True, type="locator")[0]
        transformPos = cmds.xform(locator, q=True, ws=True, t=True)
        localPos = cmds.getAttr(f"{shape}.localPosition")[0]

        return localPos
    
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

    def build_locator(self, joint_name: str, joint_data: dict, locatorList, parent=None):
        '''
        Recursively creates locators from a joint hierarchy dict.

        Parameters:
            joint_name (str): Name to give the locator (JNT replaced with GUIDE)
            joint_data (dict): Dictionary of joint data including children
            parent (str): Parent locator name, if any
        '''
        cmds.select(clear=True)

        loc = cmds.spaceLocator(
            n=joint_name.replace('JNT', 'GUIDE'))[0]
        
        cmds.xform(loc,
                   ws=True,
                   t=joint_data["pos"]
                    )
    
        if parent:
            cmds.parent(loc, parent)

        locatorList.append(loc)
        print(f"Created: {loc}")

        for child_name, child_data in joint_data["children"].items():
            self.build_locator(child_name, child_data, locatorList, loc)

        
    
    def build_reverseFeetLocators(self, presetData):
        """Recreates the locator hierarchy from the loaded JSON dict."""

        for root_name, root_data in presetData.items():
            self.build_locator(root_name, root_data, self.revFeetLocatorList)

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

    def jointOrientation(self):
        cmds.joint("root_JA_JNT", e = True, oj = "xyz", sao = "yup", ch = True, zso = True)

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

#################### joint based funcs #######################################

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

