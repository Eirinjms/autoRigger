#QT IMPORTS 
from PySide6 import QtWidgets, QtGui # pyright: ignore[reportMissingImports]
from PySide6.QtCore import QFile # pyright: ignore[reportMissingImports]
from PySide6.QtUiTools import QUiLoader # pyright: ignore[reportMissingImports]
from PySide6.QtWidgets import QFileDialog # pyright: ignore[reportMissingImports]
from shiboken6 import wrapInstance # pyright: ignore[reportMissingImports]

#system
import string
import os
import json
import math

#maya improts 
import maya.cmds as cmds # pyright: ignore[reportMissingImports]
import maya.OpenMayaUI as omui # pyright: ignore[reportMissingImports]
#from maya.app.general.mayaMixin import MayaQWidgetDockableMixin as MQwidgetMixin # pyright: ignore[reportMissingImports]
import maya.api.OpenMaya as om # pyright: ignore[reportMissingImports]

#my own modules
from autoRigger.modules.builderModules import buildRig, locatorBasedFunctions as locFunc, jointGeneration as jointGen
from autoRigger.modules.rigModules.symmetrySetup import symmetry
from autoRigger.modules.builderModules import ProceduralSpineCreation
from autoRigger.utils import config, mirror, hierarchyModule as hier, proceduralLocatorChain as procLoc, rigSettings
import autoRigger.modules.rigModules.twistSetup as twistSetup





import importlib
importlib.reload(jointGen)
importlib.reload(locFunc)
importlib.reload(buildRig)
importlib.reload(twistSetup)
importlib.reload(ProceduralSpineCreation)
importlib.reload(hier)
importlib.reload(mirror)
importlib.reload(config)
importlib.reload(procLoc)

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

        self.revFeetSymmetry = symmetry(self.revFeetLocList)
        self.guideSymmetry = symmetry(self.locatorList)

        self.guideHier = hier.hierarchyManager(self.locatorList, False, 'transform')
        self.revFeetHier = hier.hierarchyManager(self.revFeetLocList, False, 'transform')
        self.jointHier = hier.hierarchyManager(self.jointsList, True, 'joint')

        self.procSpine = ProceduralSpineCreation.ProceduralSpine()
        self.spineJoints = []
        self.spineCustomizationState = False

        self.locGuidesCreated = False

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

        self.mirrorLocatorBtn = self.ui.findChild(QtWidgets.QPushButton, "MirrorSelLocators_Btn")

        self.pvVisualizer = self.ui.findChild(QtWidgets.QCheckBox, "pvViz_checkBox")

        self.spineSlider = self.ui.findChild(QtWidgets.QSlider,"SpineAmount_Slider")
        self.spineCustomization = self.ui.findChild(QtWidgets.QGroupBox,"CustomizableSpine_grp")

        self.curveMult = self.ui.findChild(QtWidgets.QSlider, "SpineCurve_Slider")

        self.spineAmntText = self.ui.findChild(QtWidgets.QLabel, "SpineAmnt_Number")
        self.spineCurveText = self.ui.findChild(QtWidgets.QLabel, "SpineCurve_text")


        #generative locator

        self.guideChainLength = self.ui.findChild(QtWidgets.QSlider, "GuideChainLength_Slider")
        self.generateLocChain = self.ui.findChild(QtWidgets.QPushButton, "generateLocatorChain_btn")
        self.prefixLocChain = self.ui.findChild(QtWidgets.QLineEdit, "prefix_locChain_text")
        self.baseNameLocChain = self.ui.findChild(QtWidgets.QLineEdit, "baseName_locChain_text")
        self.LocatorChainNumber = self.ui.findChild(QtWidgets.QLabel, "generateLocatorChainNumber_btn")
        self.locatorUpdater = self.ui.findChild(QtWidgets.QPushButton, "generateLocatorChainUpdate_btn")
        
        #-----------------------------------joint buttons -----------------------------------------------#

        generateJointsBtn = self.ui.findChild(QtWidgets.QPushButton, "GenerateJoints_Bipedal")
        unparentJointsBtn = self.ui.findChild(QtWidgets.QPushButton, "UnparentJointHierarchy_Bipedal")
        reparentJointsBtn = self.ui.findChild(QtWidgets.QPushButton, "ReparentJointHierarchy_Bipedal")

        importRevFeetLocsBtn = self.ui.findChild(QtWidgets.QPushButton, "ImportPreset_reverseFeet_Locators")

        exportJoints =  self.ui.findChild(QtWidgets.QPushButton, "ExportJoints_JSON_Bttn")
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

        revFeetSymmetryToggle = self.ui.findChild(QtWidgets.QCheckBox, "LocatorSymmetry_revFeet_Bipedal")

        unParentRevFeet = self.ui.findChild(QtWidgets.QPushButton, "UnparentRevFeet_bn")
        ParentRevFeet = self.ui.findChild(QtWidgets.QPushButton, "ParentRevFeet_bn")


        #-----------------------------------joint text areas -----------------------------------------------#
        self.importPresetText = self.ui.findChild(QtWidgets.QLineEdit, "ImportPreset_LineEdit")
        self.revFeetTextBox = self.ui.findChild(QtWidgets.QLineEdit, "reverseFeet_Locators_editLine")
        self.exportJointsFilename = self.ui.findChild(QtWidgets.QLineEdit, "exportJointsFilename_text")

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

        self.stretchyLegsCheck = self.ui.findChild(QtWidgets.QCheckBox, "StretchyLimbs_legs_checkBttn")
        self.stretchyArmsCheck = self.ui.findChild(QtWidgets.QCheckBox, "StretchyLimbs_arms_checkBttn")

        self.temp = self.ui.findChild(QtWidgets.QPushButton, "TEMP")
        self.twistLabel = self.ui.findChild(QtWidgets.QLabel, "TwistJoint_Number")

        #ribbon

        self.ribbonArmCheck = self.ui.findChild(QtWidgets.QCheckBox, "ArmsRibbon_CheckBttn")
        self.ribbonLegCheck = self.ui.findChild(QtWidgets.QCheckBox, "LegsRibbon_CheckBttn")
        self.ribbonDriversSlider = self.ui.findChild(QtWidgets.QSlider, "ribbonDrivers_Slider")
        self.ribbonBindsSlider = self.ui.findChild(QtWidgets.QSlider, "ribbonBinds_Slider")
        self.ribbonBindsLabel = self.ui.findChild(QtWidgets.QLabel, "ribbonBinds_Number")
        self.ribbonDriverLabel = self.ui.findChild(QtWidgets.QLabel, "ribbonDrivers_Number")

        #-----------------------------------connections -----------------------------------------------#

        if rigBuildBtn:
            rigBuildBtn.clicked.connect(self.buildRigButton)

        if exportJoints:
            exportJoints.clicked.connect(self.exportJointsjson)

        if self.twistSlider:
            self.twistSlider.valueChanged.connect(self.updateSizeLabelTwist)
        
        if self.ribbonBindsSlider:
            self.ribbonBindsSlider.valueChanged.connect(self.updateRibbonBindsLabel)

        if self.ribbonDriversSlider: 
            self.ribbonDriversSlider.valueChanged.connect(self.updateRibbonDriveLabel)

        #-----------------------------------Rig Connections-----------------------------------------------#  
        
        if self.twistCheckGrp:
            self.twistCheckGrp.toggled.connect(self.toggleRigOptions)

        if self.stretchyLimbsCheckGrp:
            self.stretchyLimbsCheckGrp.toggled.connect(self.toggleRigOptions)

        if self.ribbonCheckGrp:
            self.ribbonCheckGrp.toggled.connect(self.toggleRigOptions)


        #-----------------------------------Locator connections -----------------------------------------------#
        if self.generateLocChain:
            self.generateLocChain.clicked.connect(self.guideGenerator)

        if self.guideChainLength:
            self.guideChainLength.valueChanged.connect(self.generateLocs)
        
        if self.locatorUpdater:
            self.locatorUpdater.clicked.connect(self.generateLocs)

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
            self.spineSlider.valueChanged.connect(self.spineUpdate)

        if self.curveMult:
             self.curveMult.valueChanged.connect(self.procSpine.updateCurvature)    
             self.curveMult.valueChanged.connect(lambda value: self.spineCurveText.setText(f"{value}"))    

            
        if self.locatorSymmetry:
            self.locatorSymmetry.toggled.connect(lambda checked: self.symmetryToggle(checked, 
                                                                                      self.guideSymmetry, 
                                                                                      self.locatorSymmetry))

        
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
            unparentLocsBtn.clicked.connect(self.unparentClicked)


        if reparentLocsBtn:
            reparentLocsBtn.clicked.connect(self.reparentClicked)

        if self.pvVisualizer:
            self.pvVisualizer.blockSignals(True)
            self.pvVisualizer.setChecked(False)
            self.pvVisualizer.blockSignals(False)
            self.pvVisualizer.toggled.connect(self.previewPV)
        
        if self.mirrorLocatorBtn:
            self.mirrorLocatorBtn.clicked.connect(lambda: mirror.mirrorLocators())


        #-----------------------------------rev feet connections -----------------------------------------------#
        if self.MirrorRevFeet: 
            self.MirrorRevFeet.clicked.connect(lambda : mirror.mirrorLocators("L_backOfHeel_LOC"))

        if importRevFeetLocsBtn:
            importRevFeetLocsBtn.clicked.connect(self.build_reverseFeetLocators) 

        if revFeetSymmetryToggle:
            revFeetSymmetryToggle.toggled.connect(lambda checked: self.symmetryToggle(checked, 
                                                                                      self.revFeetSymmetry, 
                                                                                      revFeetSymmetryToggle))          

        if unParentRevFeet:
            unParentRevFeet.clicked.connect(self.revFeetHier.unparentHierarchy)

        if ParentRevFeet:
            ParentRevFeet.clicked.connect(self.revFeetHier.reparentHierarchy)      

        #-----------------------------------joint connections -----------------------------------------------
        if defineNewJointList:
            defineNewJointList.clicked.connect(self.defineJointListSel)

        if unparentJointsBtn:
            unparentJointsBtn.clicked.connect(self.jointHier.unparentHierarchy)

        if reparentJointsBtn:
            reparentJointsBtn.clicked.connect(self.jointHier.reparentHierarchy)

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

        cmds.undoInfo(openChunk=True)
        try:
            expected = {
                "outerSideFoot_LOC",
                "innerSideFoot_LOC",
                "frontFoot_LOC",
                "backOfHeel_LOC"}
            sides = [
                "L_",
                "R_"
            ]
            for side in sides: 
                for e in expected: 
                    if cmds.objExists(f"{side}{e}"):
                        continue
                    else:
                        return cmds.warning("Error retrieving the reverse feet generators, delete remainding locators and re-generate")

            if not self.jointsList:
                cmds.warning("No joints found, please generate joints first")
                return

            self.defineRotOrder()   
            self.stretchyArms = self.stretchyArmsCheck.isChecked()
            self.stretchyLegs = self.stretchyLegsCheck.isChecked()

            self.ribbonArms = self.ribbonArmCheck.isChecked()
            self.ribbonLegs = self.ribbonLegCheck.isChecked()
            self.ribbonDrivers =self.ribbonDriversSlider.value()
            self.ribbonBinds = self.ribbonBindsSlider.value()

            twistArms = self.twistArmCheck.isChecked()
            twistLegs = self.twistLegCheck.isChecked()
            twistAmount = self.twistSlider.value()

            buildRig.build(
                self.spineOrder,
                self.spineJoints,     
                self.armOrder,
                self.legOrder,
                self.handOrder,
                self.neckOrder,
                self.stretchyArms,
                self.stretchyLegs,
                twistAmount,
                twistArms,
                twistLegs,
                self.ribbonArms,
                self.ribbonLegs,
                self.ribbonDrivers,
                self.ribbonBinds
            )
            print("..Rig built!")
        finally:
            cmds.undoInfo(closeChunk=True)

    def spineValue(self):
        value = self.spineSlider.value()

        if value % 2 == 0:
            value += 1

        self.spineAmntText.setText(f"{value}")

        return value
    
    def spineUpdate(self):
        self.procSpine.updateSpine(self.spineValue())
        self.spineJoints.clear()
        for loc in self.procSpine.spineLocs:
            loc = loc.replace("GUIDE", "JNT")
            self.spineJoints.append(loc)

    def locatorValue(self):
        value = self.guideChainLength.value()
        self.LocatorChainNumber.setText(str(value))

        return value
    
    def updateRibbonDriveLabel(self, value):
        if self.ribbonDriverLabel:
            self.ribbonDriverLabel.setText(str(value))

    def updateRibbonBindsLabel(self, value):
        if self.ribbonBindsLabel:
            self.ribbonBindsLabel.setText(str(value))

    def createInstanceLocChain(self): 
        prefix = self.prefixLocChain.text()
        baseName = self.baseNameLocChain.text()
        sliderValue = self.locatorValue()

        instance = procLoc.procLocatorGenerator(sliderValue, baseName, prefix)
        
        return instance
    
    def guideGenerator(self):
        self.generator = self.createInstanceLocChain()
        self.generator.generateLocs()

        self.locGuidesCreated = True
    
    def generateLocs(self):
        cmds.undoInfo(openChunk = True)
        try:
            self.locatorValue()
            if not self.locGuidesCreated:
                return
            self.generator.updateJointAmount(self.locatorValue())
            self.generator.placementMath()

            self.locatorList[:] = [
                loc for loc in self.locatorList
                if cmds.objExists(loc)]

            for loc in self.generator.Locs:
                if loc not in self.locatorList:
                    self.locatorList.append(loc)
            
        finally: 
            cmds.undoInfo(closeChunk = True)

    def updateSizeLabelTwist(self, value):
        if self.twistLabel:
            self.twistLabel.setText(str(value))

    def defineRotOrder(self):
        self.armOrder = self.armRotOrdMenu.currentIndex()
        self.legOrder = self.legRotOrdMenu.currentIndex()
        self.spineOrder = self.spineRotOrdMenu.currentIndex()
        self.handOrder = self.handRotOrdMenu.currentIndex()
        self.neckOrder = self.neckRotOrdMenu.currentIndex()
    

    # ─────────────────────────────────────────────────────────────────────────
    # LOCATORS
    # ─────────────────────────────────────────────────────────────────────────
    def importPreset(self, textBox, storeLocators : bool, locatorList, filePath=None, allowReverseDispatch=True):
        """
        Imports a JSON preset and recreates the locator hierarchy.

        Parameters:
            textBox:
                UI text box containing the preset file path.

            storeLocators (bool):
                If True, append the imported locators to ``locatorList``.

            locatorList (list):
                List used to store the imported locator objects.
        
        """
        folder = config.find_file_path("presets")
        if not filePath:
            filePath, _ = QFileDialog.getOpenFileName(
                self,
                "Import Locator Preset",
                folder,
                "JSON Files (*.json)",)
        
        if allowReverseDispatch and "reverseFeet" in filePath:
            return self.build_reverseFeetLocators(filePath = filePath)

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
        try:
            for root_name, root_data in presetData.items():
                if cmds.objExists(root_name.replace('JNT', 'GUIDE')):
                    return cmds.warning("This preset has already been loaded")
                
                self.build_locator(root_name, root_data, locatorList, storeLocators)
            cmds.undoInfo(closeChunk = True)

            cmds.select(clear = True)
            cmds.makeIdentity(locatorList, apply = True, t = True)
        finally: 
            cmds.undoInfo(closeChunk = True)

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

    def build_reverseFeetLocators(self, filePath=None):
        """Recreates the locator hierarchy from the loaded JSON dict."""

        cmds.undoInfo(openChunk = True)
        try:

            if cmds.objExists("L_backOfHeel_LOC"):
                return cmds.warning("Reverse Feet locators already in scene,"
                                    "delete them before importing new ones.")
            
            self.importPreset(self.revFeetTextBox, storeLocators = False, locatorList = self.revFeetLocList, filePath = filePath, allowReverseDispatch=False)

            mirroredRevFeet = mirror.mirrorLocators("L_backOfHeel_LOC")

            self.revFeetLocList.extend(mirroredRevFeet)

            cmds.select(clear = True)
        finally: 
            cmds.undoInfo(closeChunk = True)

    def locatorSize(self, value):
        if self.allLocatorsRadio and self.allLocatorsRadio.isChecked():
            locators = cmds.ls("*_GUIDE", type = 'transform')
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
                
    def symmetryToggle(self, checked, symmetry, checkBox):
        if checked:
            if not symmetry.locatorList:
                checkBox.blockSignals(True)
                try:
                    checkBox.setChecked(False)
                finally: 
                    checkBox.blockSignals(False)
                
                return cmds.warning("No locators found, please generate these first")
            
            else:
                symmetry.locator_symmetry()
        else:
            symmetry.disconnectSymmetry()

    
    def unparentClicked(self): 
        guides = cmds.ls("*GUIDE", type='transform')
        for guide in guides: 
            if guide not in self.locatorList: 
                self.locatorList.append(guide)

        self.spineCustomizationState = self.spineCustomization.isChecked()
        self.guideHier.unparentHierarchy()
        self.spineCustomization.setChecked(False)
        self.spineCustomization.blockSignals(True)

    def reparentClicked(self):
        self.guideHier.reparentHierarchy()
        self.spineCustomization.setChecked(self.spineCustomizationState)
        self.spineCustomization.blockSignals(False)

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
            

            self.locatorList = cmds.ls("*GUIDE", type = 'transform')
                
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
            cmds.select(clear = True)   
            #skelGrp = cmds.group(roots[0].replace("GUIDE", "JNT"), n = "_Skeleton_GRP")
            cmds.hide(locGrp)

            cmds.select(clear = True)   
            
        finally:
            cmds.undoInfo(closeChunk=True)

    def exportJointsjson(self):
        folder = config.find_file_path("presets")
        filePath, _ = QFileDialog.getSaveFileName(
        self,
        "Export Joint JSON",
        folder,
        "JSON Files (*.json)")

        if not filePath:
            return

        exp = jointGen.jointGeneration()
        exp.jointExportJSON(filePath)

        self.exportJointsFilename.setText(filePath)

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
            return self.jointsList
        else: 
            cmds.warning("Joint chain already generated")


    def jointOrientation(self):
        """
        Sets a basis for joint orientation across the skeleton (FOR BIPEDAL ONLY SO FAR)

        """

        roots = config.findRoots(cmds.ls("*JNT", type='joint'))
        for jnt in roots: 
            cmds.joint(jnt,                 
                    e = True, 
                   oj = "xyz", 
                   sao = "yup", 
                   ch = True, 
                   zso = True)

        required = [
            "C_spineJA_JNT",
            "L_armJD_JNT",
            "R_armJD_JNT",
            "L_middleFngJEnd_JNT",
            "R_middleFngJEnd_JNT",
        ]
        
        missing = [j for j in required if not cmds.objExists(j)]
        if missing:
            return
        
        cmds.joint("C_spineJA_JNT", 
                   e = True, 
                   oj = "xyz", 
                   sao = "yup", 
                   ch = True, 
                   zso = True)
        
        #spinejoints
        centerJoints = cmds.ls("C_*",
                               type='joint')
        
        hipJoins = cmds.ls("*legJA", type = 'joint')
        
        feetJoints = cmds.ls("*legJC*", "*legJD*", type = 'joint')

        self.jointHier.unparentHierarchy()

        for joint in centerJoints + feetJoints:
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

        wristPairs = [
            ("L_armJD_JNT", "L_middleFngJEnd_JNT"),
            ("R_armJD_JNT", "R_middleFngJEnd_JNT")] 
            
        
        for joint, aim in wristPairs:
            cmds.delete(cmds.aimConstraint(aim, joint, 
                               aimVector = (1,0,0),
                               worldUpType = 'scene'))
        
        self.jointHier.reparentHierarchy()

        #endjoints
        for joint in self.jointsList:
            if not cmds.listRelatives(joint, c=True, type="joint"):
                cmds.joint(joint, e=True, zso=True, oj="none")
        
        self.mirrorJoints()

    def mirrorJoints(self):
        """
        Mirrors joints based on input from UI
        """

        cmds.undoInfo(openChunk = True)
        try: 
            if len(self.jointsList) == 0:
                return cmds.warning("No joints found, unable to mirror joints.")

            if cmds.listRelatives(self.jointsList[0], children = True) is None:
                self.jointHier.reparentHierarchy() #ensures ur hierarchy is combined again before mirror
            
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

            leftJoints = [j for j in leftJoints if "eye" not in j]
            rightJoints = [j for j in rightJoints if "eye" not in j] #rebuilds the list but removes the eyejoints

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
    
    def previewPV(self, checked):

        cmds.undoInfo(openChunk = True)
        try:
            if not checked:
                # delete the visualization if it exists
                if cmds.objExists("*_PV_Visualization"):
                    cmds.delete(cmds.ls("*_PV_Visualization"))
                return

            sel = cmds.ls(sl=True, type='transform')
            if len(sel) != 1:
                return cmds.warning("Select ONLY root joint of the chain you want to test")
            
            children = cmds.listRelatives(sel, ad=True, type='transform') or []
            children.reverse()
            chain = sel + children
            

            if len(chain) < 3:
                cmds.warning("Select the root of the limb chain")
                return
            for guide in chain[:3]:
                local, world = config.getGuidePos(guide)
                pos = config.addTuples(local, world)

            self.unparentClicked()

            for guide in chain[:3]:
                shape = cmds.listRelatives(guide, s=True, type="locator")[0]

                # current values
                translate = cmds.getAttr(f"{guide}.translate")[0]
                localPos = cmds.getAttr(f"{shape}.localPosition")[0]

                # bake translate into the shape
                baked = tuple(t + l for t, l in zip(translate, localPos))

                cmds.setAttr(f"{shape}.localPosition", *baked, type="double3")
                cmds.setAttr(f"{guide}.translate", 0, 0, 0, type="double3")

            for guide in chain[:3]:
                local, world = config.getGuidePos(guide)
                pos = config.addTuples(local, world)


                for guide in chain[:3]:
                    shape = cmds.listRelatives(guide, s=True, type="locator")[0]

            locFunc.poleVectorVisualization(chain[:3:], pvDistance=10)

        finally:
            self.reparentClicked()
            cmds.select(clear = True)
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

        if sender in (self.ribbonCheckGrp, self.stretchyLimbsCheckGrp) and checked:
            self.twistCheckGrp.setChecked(False)
            self.twistArmCheck.setChecked(False)
            self.twistLegCheck.setChecked(False)

        elif sender == self.twistCheckGrp and checked:
            self.ribbonCheckGrp.setChecked(False)
            self.ribbonArmCheck.setChecked(False)
            self.ribbonLegCheck.setChecked(False)
