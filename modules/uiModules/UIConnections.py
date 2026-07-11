#QT IMPORTS 
from PySide6 import QtWidgets, QtGui # pyright: ignore[reportMissingImports]
from PySide6.QtCore import QFile # pyright: ignore[reportMissingImports]
from PySide6.QtUiTools import QUiLoader # pyright: ignore[reportMissingImports]
from PySide6.QtWidgets import QFileDialog # pyright: ignore[reportMissingImports]
from shiboken6 import wrapInstance # pyright: ignore[reportMissingImports]
import os
import json

#maya improts 
import maya.cmds as cmds # pyright: ignore[reportMissingImports]
import maya.OpenMayaUI as omui # pyright: ignore[reportMissingImports]
#from maya.app.general.mayaMixin import MayaQWidgetDockableMixin as MQwidgetMixin # pyright: ignore[reportMissingImports]
import maya.api.OpenMaya as om # pyright: ignore[reportMissingImports]

#my own modules
from autoRigger.modules.builderModules import buildRig, locatorBasedFunctions as locFunc, jointGeneration as jointGen
import autoRigger.utils.config as config
import autoRigger.modules.rigModules.twistSetup as twistSetup

import importlib
importlib.reload(jointGen)
importlib.reload(locFunc)
importlib.reload(buildRig)
importlib.reload(twistSetup)


def getMayaWindow():
    """
    Retrieves Maya's main window as a PySide6 QWidget.

    Uses Maya's OpenMayaUI API to get a pointer to the native Maya main
    window, then wraps that pointer with shiboken6 so it can be used as
    a proper Qt widget within PySide6 code.

    This is primarily used to parent custom PySide6 dialogs (such as
    AutoRiggerUI) to Maya's main window, ensuring that:
        - The tool window stays on top of Maya rather than getting lost
          behind it.
        - The tool closes automatically when Maya closes.
        - The window behaves consistently with other Maya-native UI panels.

    Returns:
        QtWidgets.QWidget: The Maya main window wrapped as a Qt widget,
        suitable for use as a `parent` argument when constructing
        QDialog/QWidget-based tools.

    Notes:
        - Relies on `maya.OpenMayaUI.MQtUtil.mainWindow()` to fetch the
          raw C++ pointer to Maya's main window.
        - `shiboken6.wrapInstance()` converts that pointer into a usable
          Python/Qt object; the pointer must be cast to `int` first since
          `MQtUtil.mainWindow()` returns a SIP/void pointer type.
        - Must be run within Maya's Python environment, since it depends
          on `maya.OpenMayaUI` and an active Maya session with a
          initialized UI (i.e. not in `mayapy` batch mode without a UI).
    """
    mayaWindow = wrapInstance(int(omui.MQtUtil.mainWindow()), QtWidgets.QWidget)
    return mayaWindow


class AutoRiggerUI(QtWidgets.QDialog):
    def __init__(self, ui_file_path, parent=None):
        super().__init__(parent or getMayaWindow())

        self.locator = None
        self.locatorList = []
        self.revFeetLocList = []
        self.jointsList = []
        self.ui = None
        self.oldSpinelocators = []
        self.newSpinelocators = []

        self.hierarchy = {}

        self.prefix = [config.prefix['left'], config.prefix['right']]

        self.setWindowIcon(QtGui.QIcon(config.find_file_path("logo.png")))
        self.setWindowTitle("AutoRigger V01")
        self.setObjectName("AutoRiggerV01")


        self._loadUi(ui_file_path)
        self._connectWidgets()

    # ─────────────────────────────────────────────────────────────────────────
    # UI SETUP
    # ─────────────────────────────────────────────────────────────────────────

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
        self.slider = self.ui.findChild(QtWidgets.QSlider, "horizontalSlider_7")
        self.sizeLabel = self.ui.findChild(QtWidgets.QLabel, "TwistJoint_Number_2")
        self.locatorSymmetry = self.ui.findChild(QtWidgets.QCheckBox, "LocatorSymmetry_Bipedal")

        unparentLocsBtn = self.ui.findChild(QtWidgets.QPushButton, "UnparentLocHierarchy_Bipedal")
        reparentLocsBtn = self.ui.findChild(QtWidgets.QPushButton, "ReparentLocHierarchy_Bipedal")

        mirrorLocatorBtn = self.ui.findChild(QtWidgets.QPushButton, "ReparentLocHierarchy_Bipedal")

        self.revFeetSymmetry = self.ui.findChild(QtWidgets.QCheckBox, "LocatorSymmetry_ReverseFeet")
        self.MirrorRevFeet = self.ui.findChild(QtWidgets.QPushButton, "MirrorReverseFeet")

        self.pvVisualizer = self.ui.findChild(QtWidgets.QCheckBox, "pvViz_checkBox")

        self.spineSlider = self.ui.findChild(QtWidgets.QSlider,"SpineAmount_Slider")
        self.spineCustomization = self.ui.findChild(QtWidgets.QGroupBox,"CustomizableSpine_grp")
        
        #-----------------------------------joint buttons -----------------------------------------------#

        generateJointsBtn = self.ui.findChild(QtWidgets.QPushButton, "GenerateJoints_Bipedal")
        unparentJointsBtn = self.ui.findChild(QtWidgets.QPushButton, "UnparentJointHierarchy_Bipedal")
        reparentJointsBtn = self.ui.findChild(QtWidgets.QPushButton, "ReparentJointHierarchy_Bipedal")

        importRevFeetLocsBtn = self.ui.findChild(QtWidgets.QPushButton, "ImportPreset_reverseFeet_Locators")

        exportJoints =  self.ui.findChild(QtWidgets.QPushButton, "ExportJoints_JSON_Bttn")
        self.exportJointsFilename = self.ui.findChild(QtWidgets.QLineEdit, "exportJointsFilename_text")
        importJoints = self.ui.findChild(QtWidgets.QPushButton, "ImportJoints_Bttn")
        self.importJointsFilename =self.ui.findChild(QtWidgets.QLineEdit, "importJointsFilename_text")

        mirrorOrientationBtn = self.ui.findChild(QtWidgets.QPushButton, "mirrorJointOrientation_Btn")
        self.leftToRight = self.ui.findChild(QtWidgets.QRadioButton, "jointMirror_leftToRight_radio")
        self.rightToLeft = self.ui.findChild(QtWidgets.QRadioButton, "jointMirror_rightToLeft_radio")

        self.localRotationAxesToggle = self.ui.findChild(QtWidgets.QCheckBox, "LRA_checkBox")
        self.allLRA = self.ui.findChild(QtWidgets.QRadioButton, "LRA_all_radio")
        self.selectedLRA = self.ui.findChild(QtWidgets.QRadioButton, "LRA_selected_radio")

        defineNewJointList = self.ui.findChild(QtWidgets.QPushButton, "UseSelectedRoot_btn")
        self.newJointListText = self.ui.findChild(QtWidgets.QLineEdit, "selectedrootchain_text")


        #-----------------------------------joint text areas -----------------------------------------------#
        self.importPresetText = self.ui.findChild(QtWidgets.QLineEdit, "ImportPreset_LineEdit")
        self.revFeetTextBox = self.ui.findChild(QtWidgets.QLineEdit, "reverseFeet_Locators_editLine")

        self.MirrorRevFeet = self.ui.findChild(QtWidgets.QPushButton, "MirrorReverseFeet")


        #-----------------------------------Rig Option buttons -----------------------------------------------#

        self.armRotOrdMenu = self.ui.findChild(QtWidgets.QComboBox, "armRotationOrder_comboBox")
        self.legRotOrdMenu = self.ui.findChild(QtWidgets.QComboBox, "legRotationOrder_comboBox")
        self.spineRotOrdMenu = self.ui.findChild(QtWidgets.QComboBox, "spineRotationOrder_comboBox")
        self.handRotOrdMenu = self.ui.findChild(QtWidgets.QComboBox, "fingersRotationOrder_comboBox")
        self.neckRotOrdMenu = self.ui.findChild(QtWidgets.QComboBox, "neckRotationOrder_comboBox")


        self.twistCheckGrp = self.ui.findChild(QtWidgets.QGroupBox, "TwistJoints_Grpbox")
        self.stretchyLimbsCheckGrp = self.ui.findChild(QtWidgets.QGroupBox, "StretchyLimbs_Grpbox")
        self.ribbonCheckGrp = self.ui.findChild(QtWidgets.QGroupBox, "ribbons_Grpbox")

        self.twistArmCheck = self.ui.findChild(QtWidgets.QCheckBox, "twistJoints_arm_checkbtn")
        self.twistLegCheck = self.ui.findChild(QtWidgets.QCheckBox, "twistJoints_legs_checkbtn")
        self.twistSlider = self.ui.findChild(QtWidgets.QSlider, "twistJoint_Slider")

        self.temp = self.ui.findChild(QtWidgets.QPushButton, "TEMP")
        self.twistLabel = self.ui.findChild(QtWidgets.QLabel, "TwistJoint_Number")


        #-----------------------------------connections -----------------------------------------------#

        if rigBuildBtn:
            rigBuildBtn.clicked.connect(self.buildRigButton)

        if exportJoints:
            exportJoints.clicked.connect(self.exportJointsjson)

        if self.temp:
            self.temp.clicked.connect(self.twistCreation)

        if self.twistSlider:
            self.twistSlider.valueChanged.connect(self.updateSizeLabelTwist)

        #-----------------------------------Rig Connections-----------------------------------------------#  
        
        if self.twistCheckGrp:
            self.twistCheckGrp.toggled.connect(self.toggleRigOptions)

        if self.stretchyLimbsCheckGrp:
            self.stretchyLimbsCheckGrp.toggled.connect(self.toggleRigOptions)

        if self.ribbonCheckGrp:
            self.ribbonCheckGrp.toggled.connect(self.toggleRigOptions)


        #-----------------------------------Locator connections -----------------------------------------------#
        if createLocBtn:
            createLocBtn.clicked.connect(self.buildLocators)
            
        if importPresetBtn:
            importPresetBtn.clicked.connect(lambda : self.importPreset(self.importPresetText, True, self.locatorList))

        if generateJointsBtn:
            generateJointsBtn.clicked.connect(self.generateJoints)

        if self.slider:
            self.slider.valueChanged.connect(self.locatorSize)
            self.slider.valueChanged.connect(self.updateSizeLabel)

        if self.spineSlider:
            self.spineSlider.valueChanged.connect(self.spineFunc)

            
        if self.locatorSymmetry:
            self.locatorSymmetry.toggled.connect(self.symmetryToggle)

        
        # keep slider/label in sync with whatever locator is selected in the scene
        existing = cmds.scriptJob(listJobs=True)
        for job in existing:
            if "syncSliderToSelection" in job:
                jobNum = int(job.split(":")[0])
                cmds.scriptJob(kill=jobNum, force=True)

        self.selectionJob = cmds.scriptJob(
            event=["SelectionChanged", self.syncSliderToSelection],
            protected=False,
        )

        if unparentLocsBtn:
            unparentLocsBtn.clicked.connect(lambda : self.unparentHierarchy(self.locatorList))

        if reparentLocsBtn:
            reparentLocsBtn.clicked.connect(lambda : self.reparentHierarchy(False))

        if self.pvVisualizer:
            self.pvVisualizer.blockSignals(True)
            self.pvVisualizer.setChecked(False)
            self.pvVisualizer.blockSignals(False)
            self.pvVisualizer.toggled.connect(self.previewPV)

        if self.spineCustomization:
            if self.spineCustomization.isChecked():
                self.spineFunc()


        #-----------------------------------rev feet connections -----------------------------------------------#
        if self.MirrorRevFeet: 
            self.MirrorRevFeet.clicked.connect(lambda : self.mirrorLocators("L_backOfHeel_LOC"))

        if importRevFeetLocsBtn:
            importRevFeetLocsBtn.clicked.connect(lambda: self.importPreset(self.revFeetTextBox, storeLocators = False, locatorList = self.revFeetLocList))            


        #-----------------------------------joint connections -----------------------------------------------
        if defineNewJointList:
            defineNewJointList.clicked.connect(self.defineJointListSel)

        if unparentJointsBtn:
            unparentJointsBtn.clicked.connect(lambda: self.unparentHierarchy(self.jointsList))

        if reparentJointsBtn:
            reparentJointsBtn.clicked.connect(lambda: self.reparentHierarchy(True))

        if mirrorOrientationBtn:
            mirrorOrientationBtn.clicked.connect(self.mirrorJoints)

        if self.localRotationAxesToggle:
            self.localRotationAxesToggle.toggled.connect(self.showLocalRotationAxes)

    def closeEvent(self, event):
        if getattr(self, "selectionJob", None):
            cmds.scriptJob(kill=self.selectionJob, force=True)
        super().closeEvent(event)

    # ─────────────────────────────────────────────────────────────────────────
    # RIG BUILD
    # ─────────────────────────────────────────────────────────────────────────

    def buildRigButton(self):
        """ Builds the rig :D """

        self.twistCreation()

        cmds.undoInfo(openChunk=True)
        try:
            if not self.revFeetLocList:
                cmds.warning("Please generate reverse feet before building rig")
                return
            
            if len(self.revFeetLocList) == 4: 
                print("only one side of rev feet found, generating the other side")
                rightSideLocs = self.mirrorLocators("L_backOfHeel_LOC")
                self.revFeetLocList.extend(rightSideLocs)
                print("Right side created..")

            if not self.jointsList:
                cmds.warning("No joints found, please generate joints first")
                return

            self.armOrder = self.armRotOrdMenu.currentIndex()
            self.legOrder = self.legRotOrdMenu.currentIndex()
            self.spineOrder = self.spineRotOrdMenu.currentIndex()
            self.handOrder = self.handRotOrdMenu.currentIndex()
            self.neckOrder = self.neckRotOrdMenu.currentIndex()

            buildRig.build(
                self.armOrder,
                self.legOrder,
                self.handOrder,
                self.spineOrder,
                self.neckOrder,
            )
            print("..Rig built!")
        finally:
            cmds.undoInfo(closeChunk=True)


    def twistCreation(self):
        cmds.undoInfo(openChunk = True)
        try: 
            self.twistInput = self.twistSlider.value()
            startJoints = []
            endJoints = []
            axisInput = "X"
            if self.twistArmCheck.isChecked():
                for side in self.prefix:
                    startJoints.extend([f"{side}armJB_JNT", f"{side}armJC_JNT"])
                    endJoints.extend([f"{side}armJC_JNT", f"{side}armJD_JNT"])

            if self.twistLegCheck.isChecked():
                for side in self.prefix:
                    startJoints.extend([f"{side}legJA_JNT", f"{side}legJB_JNT"])
                    endJoints.extend([f"{side}legJB_JNT", f"{side}legJC_JNT"])

            for sj, ej in zip(startJoints, endJoints):
                twist = twistSetup.TwistJointsGeneration(axisInput, sj, ej, self.twistInput, self.armOrder, self.legOrder)
                print(self.legOrder)
                self.jointsList.extend(twist.creation())
        finally: 
            cmds.undoInfo(closeChunk = True)
            print(self.jointsList)

    
    def updateSizeLabelTwist(self, value):
        if self.twistLabel:
            self.twistLabel.setText(str(value))

    # ─────────────────────────────────────────────────────────────────────────
    # LOCATORS
    # ─────────────────────────────────────────────────────────────────────────

    def buildLocators(self):
        "Builds a Locator? "
        cmds.undoInfo(openChunk=True)
        try:
            self.locator = cmds.spaceLocator()[0]
            self.locatorList.append(self.locator)
            print(self.locator)
        finally:
            cmds.undoInfo(closeChunk=True)

    def importPreset(self, textBox, storeLocators : bool, locatorList):
        """
        the function doing thangs

            Parameters: 
                textBox : which UI box you wanna fill
                storeLocators(bool) : if you want to append to the loc list
        
        """
        folder = config.find_file_path("presets")

        filePath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Locator Preset",
            folder,
            "JSON Files (*.json)",)

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
        self.applyPreset(presetData, storeLocators, locatorList)
    
    def applyPreset(self, presetData, storeLocators, locatorList):
        """Recreates the locator hierarchy from the loaded JSON dict.
        
            Parameters: 
                presetData : JSON file
        """
        
        cmds.undoInfo(openChunk = True)
        for root_name, root_data in presetData.items():
            self.build_locator(root_name, root_data, locatorList, storeLocators)
        cmds.undoInfo(closeChunk = True)

        cmds.select(self.locatorList, r = True)
        cmds.makeIdentity(apply = True, t = True)

    def build_locator(self, locator_name: str, joint_data: dict, locatorList, storeLocators, parent=None):
        '''
        Recursively creates locators from a joint hierarchy dict.

        Parameters:
            locator_name (str): Name to give the locator (JNT replaced with GUIDE )
            joint_data (dict): Dictionary of joint data including children
            parent (str): Parent locator name, if any
            storeLocators (bool) : if you want to save to the lovator list. 
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

        locatorList.append(loc)
        print(f"Created: {loc}")

        for child_name, child_data in joint_data["children"].items():
            self.build_locator(child_name, child_data, locatorList, storeLocators, loc)

    def build_reverseFeetLocators(self, presetData, storeLocators):
        """Recreates the locator hierarchy from the loaded JSON dict."""

        for root_name, root_data in presetData.items():
            self.build_locator(root_name, root_data, self.revFeetLocatorList, storeLocators)

        cmds.select(self.locatorList, r = True)
        cmds.makeIdentity(apply = True, t = True)      

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

    def updateSizeLabel(self, value):
        if self.sizeLabel:
            self.sizeLabel.setText(str(value))

    def syncSliderToSelection(self):
        """When a locator is selected, set the slider/label to its current scale."""
        if not self.isVisible():
            return
        
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

    def mirrorLocators(self, sel : str | list | None = None) -> list:
        """
        Mirrors locators from a provided list or the current Maya selection.

            Parameters:
                sel (list): List of locators to duplicate.
                    
            Returns:
                list: A list of the mirrored locators
        """

        selection = cmds.ls(sl = True, long = True)

        mirroredLocs = []

        if not sel:
            sel = selection

        if not sel:
            cmds.warning("Please select what you want to mirror")
            return []

        originGrp = cmds.group(sel)

        duplicatedGrp = cmds.duplicate(originGrp, rc = True)[0]
        cmds.makeIdentity(duplicatedGrp, a = True, s = True)

        cmds.xform(duplicatedGrp, ws = True, piv = (0, 0, 0), s = (-1, 1, 1))

        children = cmds.listRelatives(duplicatedGrp, allDescendents = True) or []
        
        for child in children:

            if child.startswith("L_"):
                child = cmds.rename(child, child.replace("L_", "R_")
                            .replace("LOC1", "LOC"))
            elif child.startswith("R_"):
                child = cmds.rename(child, child.replace("R_", "L_")
                            .replace("LOC1", "LOC"))
            else: 
                child = cmds.rename(child, f"{child}_mirror")
            
            mirroredLocs.append(child)
            
        cmds.parent(cmds.listRelatives(duplicatedGrp, children = True), w = True)

        cmds.parent(cmds.listRelatives(originGrp, children = True), w = True)

        cmds.delete(originGrp, duplicatedGrp)

        return mirroredLocs
    
    def locator_symmetry(self): 
        cmds.undoInfo(openChunk = True)
        try:
            self.leftAttrs = []
            self.rightAttrs = []
            self.reverseNodes = []
            for left in self.locatorList:
                cmds.delete(left, ch = True)
                if left.startswith("L_"):
                    right = left.replace("L_", "R_")

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
            cmds.undoInfo(closeChunk = True)
            

    def symmetryToggle(self, checked):
        if checked:
            if not self.locatorList:
                self.locatorSymmetry.blockSignals(True)
                try:
                    self.locatorSymmetry.setChecked(False)
                finally: 
                    self.locatorSymmetry.blockSignals(False)
                   
                return cmds.warning("No locators found, please generate these first")
            
            else:
                self.locator_symmetry()
        else:
            self.disconnectSymmetry()

    # ─────────────────────────────────────────────────────────────────────────
    # JOINTS
    # ─────────────────────────────────────────────────────────────────────────

    def build_joint(self, locator: str, parent=None) -> str:
        '''
        Creates a joint per given locator. 

        Parameters:
            locator (str): Locator transform to convert into a joint
            parent (str): Parent joint name, if any

        Returns:
            str: Name of the joint created for the supplied locator. 
        '''
            
        cmds.select(clear=True)

        pos, _ = config.getGuidePos(locator)
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
                
            if len(self.locatorList)== 0:
                return cmds.warning("No guide Locators found, please generate these before generating joints!")
            
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

            cmds.select(clear = True)   
            locGrp = cmds.group(roots, n = "Guide_Locator_GRP")
            cmds.hide(locGrp)
            
        finally:
            cmds.undoInfo(closeChunk=True)

    def exportJointsjson(self):
        folder = config.find_file_path("presets")
        filePath, _ = QFileDialog.getSaveFileName(
        self,
        "Export Joint JSON",
        folder,
        "JSON Files (*.json)")

        exp = jointGen.jointGeneration()
        exp.jointExportJSON(filePath)

    def defineJointListSel(self):
        if not self.jointsList:
            selected = cmds.ls(sl = True)
            if len(selected) != 1:
                cmds.warning("More than one root joint chosen, select ONE and try again")
                return
            
            rootJoint = selected[0]
            print(f"{rootJoint}selected")

            self.jointsList.append(rootJoint)
            jointChain = cmds.listRelatives(rootJoint, ad = True)
            self.jointsList.extend(jointChain)

            self.newJointListText.setText(rootJoint)
            print(f"{rootJoint} chain set as new Joint List")

            print(self.jointsList)
        
            return self.jointsList
        else: 
            cmds.warning("Joint chain already generated")


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
        centerJoints = cmds.ls("C_*",
                               type='joint')
        
        
        feetJoints = cmds.ls("*legJC*", "*legJD*", type = 'joint')

        print(centerJoints)

        self.unparentHierarchy(self.jointsList)

        for joint in centerJoints:
            if "jaw" in joint:
                continue
            
            pos = cmds.xform(joint, q = True, t = True, ws = True)
            loc = cmds.spaceLocator(n = f"{joint}_temp")[0]
            cmds.xform(loc, ws=True, t=(pos[0], pos[1] + 10, pos[2]))
            cmds.delete(cmds.aimConstraint(loc, joint, 
                                           offset = (90,0,0), 
                                           aimVector = (1,0,0), 
                                           upVector = (0,0,-1), 
                                           worldUpType = 'scene'))
            cmds.delete(loc)

        for joint in feetJoints:
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
        
        self.reparentHierarchy(True)

        #endjoints
        for joint in self.jointsList:
            if not cmds.listRelatives(joint, c=True, type="joint"):
                cmds.joint(joint, e=True, zso=True, oj="none")

    def mirrorJoints(self):
        """
        Mirrors joints based on input from UI
        """

        cmds.undoInfo(openChunk = True)
        try: 
            if len(self.jointsList) == 0:
                return cmds.warning("No joints found, unable to mirror joints.")
            
            leftJoints = []
            rightJoints = []
            for joint in self.jointsList: 
                if joint.startswith("L_"):
                    leftJoints.append(joint)
                elif joint.startswith("R_"):
                    rightJoints.append(joint)
                else:
                    continue
            
            print(leftJoints + rightJoints)
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
            
            cmds.select(cl = True)
        finally: 
            cmds.undoInfo(closeChunk = True)

    def showLocalRotationAxes(self):
        """
            Toggles the visibility of local rotation axes on joints.
        """
        cmds.undoInfo(openChunk = True)
        try:
            if len(self.jointsList) == 0:
                try:
                    self.localRotationAxesToggle.blockSignals(True)
                    self.localRotationAxesToggle.setChecked(False)
                finally: 
                    self.localRotationAxesToggle.blockSignals(False)

                return cmds.warning("No joints found, unable to enable local rotation axes")
            
            selectedJoints = cmds.ls(sl = True, 
                                    type = 'joint')

            if self.allLRA.isChecked():
                for joint in self.jointsList:
                    cmds.setAttr(f"{joint}.displayLocalAxis", 1)
            
            elif self.selectedLRA.isChecked():
                for joint in selectedJoints:
                    cmds.setAttr(f"{joint}.displayLocalAxis", 1)

            if not self.localRotationAxesToggle.isChecked():
                for joint in self.jointsList:
                    cmds.setAttr(f"{joint}.displayLocalAxis", 0)
        finally:
            cmds.undoInfo(closeChunk=True)
    
    def previewPV(self, sel):
        """
        Enables a preview version of where the PoleVector will be located.

            Parameters: 
                sel (str) : a selected root for the chain you want to visualize.
        """

        if not sel:
            sel = cmds.ls(sl = True, 
                        type='transform')
            
            children = cmds.listRelatives(sel, 
                                    ad = True)
            
            sel = cmds.ls(sel + children)

            locFunc.poleVectorVisualization(sel, pvDistance = 10)


        # AND ALSO ADD IN THAT HEN THE THANG IS UNCHECKED U DELETE THE plane

    # ─────────────────────────────────────────────────────────────────────────
    # GENERAL
    # ─────────────────────────────────────────────────────────────────────────

    def saveHierarchy(self, nodeList):
        """
        Saves the hierarchy locally, for temporary parenting

        """

        self.hierarchy = {}

        for node in nodeList: 
            parent = cmds.listRelatives(node, 
                                        parent = True,
                                        )
            self.hierarchy[node] = parent[0] if parent else None
    
            
    def unparentHierarchy(self, nodeList): 
        """
        unparents the hierarchy

        """
        cmds.undoInfo(openChunk = True)
        try:    
            if len(self.hierarchy) != 0: 
                return cmds.warning("Hierarchy already saved, please reparent first!")            

            self.saveHierarchy(nodeList)
            for node in nodeList:
                if cmds.listRelatives(node, parent = True) is not None:  
                    cmds.parent(node, world = True)
        finally: 
            cmds.undoInfo(closeChunk = True)

    def reparentHierarchy(self, freezeTrans : bool):
        """
        Reparents based on prior saved hierarchy

        """
        cmds.undoInfo(openChunk = True)
        try:
            if freezeTrans:
                for node in self.hierarchy:
                    cmds.makeIdentity(node, apply = True, r = True)
            for child, parent in self.hierarchy.items():
                if parent:
                    cmds.parent(child,parent)

            self.hierarchy = {}  #resets the dict to empty
            
        finally: 
            cmds.undoInfo(closeChunk = True)


    # ─────────────────────────────────────────────────────────────────────────
    # Rig options
    # ─────────────────────────────────────────────────────────────────────────

    def toggleRigOptions(self, checked):
        """
            Enables or disables UI elements based on the state of the button.

            Parameters:
                checked (bool): Whether the button is checked.
        """

        sender = self.sender() #returns the widget that sent the signal to run the function

        if sender == self.ribbonCheckGrp and checked:
            self.twistCheckGrp.setChecked(False)
            self.stretchyLimbsCheckGrp.setChecked(False)

        elif sender in (self.twistCheckGrp, self.stretchyLimbsCheckGrp) and checked:
            self.ribbonCheckGrp.setChecked(False)

# ─────────────────────────────────────────────────────────────────────────
    # procedural spine locator creation
    # ─────────────────────────────────────────────────────────────────────────
    def spineLocators(self, spineJointNumber):

        self.jointAmount = spineJointNumber

        self.spineRoot = cmds.listRelatives("root_JA_GUIDE", children = True, type='transform')[0]
        print(self.spineRoot)

        self.spineEnd = next(loc for loc in cmds.listRelatives(self.spineRoot, ad = True, type='transform') if "JEnd" in loc)
        print(self.spineEnd)

        if self.spineEnd is None:
            return print("No spine End locator found")
        elif self.spineRoot is None:
            return print("No spine root was found")
        
        self.oldSpinelocators = cmds.ls("*spine*", type='transform')

        if self.spineRoot in self.oldSpinelocators:
            self.oldSpinelocators.remove(self.spineRoot)

        if self.spineEnd in self.oldSpinelocators:
            self.oldSpinelocators.remove(self.spineEnd)
    
    def spineLocMath(self):
        
        rootLocalPos, _ = config.getGuidePos(self.spineRoot)
        endLocalPos, _ = config.getGuidePos(self.spineEnd)

        SRVECTOR = om.MVector(rootLocalPos)
        SEVECTOR = om.MVector(endLocalPos)

        distanceVector = SEVECTOR - SRVECTOR

        distanceBetweenJoints = distanceVector.length() / (self.jointAmount - 1 )

        direction = distanceVector.normal()

        positions = []
        print(positions)

        for i in range(self.jointAmount):
            pos = SRVECTOR + direction * distanceBetweenJoints * i
            positions.append(pos)

        for pos in positions:
            loc = cmds.spaceLocator(n = "spine#")[0]
            cmds.xform(loc, t = (pos), ws = True)
            self.newSpinelocators.append(loc)
        print(positions)

    def spineFunc(self):
        if self.oldSpinelocators:
            self.deletingSpine(self.oldSpinelocators)
        elif self.newSpinelocators:
            self.deletingSpine(self.newSpinelocators)

        spineJointNumber = self.spineSlider.value()

        self.spineLocators(spineJointNumber)
        self.spineLocMath()

    def deletingSpine(self, joints: list):
        childrenEnd = cmds.listRelatives(self.spineEnd, children = True)
        childrenRoot = cmds.listRelatives(self.spineRoot, children = True)

        cmds.parent(self.spineEnd, w = True)

        cmds.delete(joints)

        cmds.parent(self.spineEnd, self.newSpinelocators[-1])

        
        
"""Generate Spine
    ↓
Unparent:
- L_armJA_GUIDE
- R_armJA_GUIDE
- L_legJA_GUIDE
- R_legJA_GUIDE
- neck_GUIDE
    ↓
Delete old procedural spine
    ↓
Generate new spine chain
    ↓
Parent spineEnd → neck
Parent spineRoot → arms/legs

That's much simpler than trying to thread new locators into an existing chain.

Even better, your Generate Joints function can just assume the hierarchy is already correct. It doesn't need to know how the spine was rebuilt—it just recursively walks whatever hierarchy exists."


Save root attachments
Save end attachments
↓
Unparent attachments
↓
Delete procedural spine
↓
Generate new procedural spine
↓
Parent:
spineRoot
    ↓
new spine chain
    ↓
spineEnd
↓
Reattach saved root attachments
Reattach saved end attachments"""