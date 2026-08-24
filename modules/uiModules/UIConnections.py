#QT IMPORTS 
from PySide6 import QtWidgets, QtGui, QtCore # pyright: ignore[reportMissingImports]
from PySide6.QtCore import QFile # pyright: ignore[reportMissingImports]
from PySide6.QtUiTools import QUiLoader # pyright: ignore[reportMissingImports]
from PySide6.QtWidgets import QFileDialog # pyright: ignore[reportMissingImports]
from shiboken6 import wrapInstance # pyright: ignore[reportMissingImports]

#system
import string
import os
import json
import math
import cProfile
import pstats

#maya improts 
import maya.cmds as cmds # pyright: ignore[reportMissingImports]
import maya.OpenMayaUI as omui # pyright: ignore[reportMissingImports]
#from maya.app.general.mayaMixin import MayaQWidgetDockableMixin as MQwidgetMixin # pyright: ignore[reportMissingImports]
import maya.api.OpenMaya as om # pyright: ignore[reportMissingImports]
import maya.mel as mel

#my own modules
from autoRigger.modules.builderModules import buildRig, locatorBasedFunctions as locFunc, jointGeneration as jointGen
from autoRigger.modules.rigModules.symmetrySetup import symmetry
from autoRigger.modules.builderModules import ProceduralSpineCreation
from autoRigger.utils import config, mirror, hierarchyModule as hier, proceduralLocatorChain as procLoc, jointOrientation as jointOrient
import autoRigger.modules.rigModules.twistSetup as twistSetup





import importlib
import importlib.util
importlib.reload(jointGen)
importlib.reload(jointOrient)
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
        if not self.locatorList:
            self.locatorList[:] = cmds.ls("*GUIDE", type="transform") or []
        self.revFeetLocList = []
        if not self.revFeetLocList:
            self.revFeetLocList = cmds.ls("*revLOC", type = "transform")
        self.jointsList = []
        if not self.jointsList:
            self.jointsList[:] = cmds.ls(type = 'joint')
        self.ui = None
        self.oldSpinelocators = []
        self.newSpinelocators = []
        
        self.revFeetSymmetry = symmetry(self.revFeetLocList)
        self.guideSymmetry = symmetry(cmds.ls("*_GUIDE", type='transform'))

        self.locatorHier = hier.hierarchyManager(self.locatorList, False, 'transform')
        self.revFeetHier = hier.hierarchyManager(self.revFeetLocList, False, 'transform')
        self.jointHier = hier.hierarchyManager(self.jointsList, True, 'joint')
        self.jointOrient = jointOrient

        self.procSpine = ProceduralSpineCreation.ProceduralSpine()
        self.spineJoints = []
        self.spineCustomizationState = False

        self.locsParentedState = True

        self.locGuidesCreated = False

        self.prefix = [config.prefix['left'], config.prefix['right']]

        self.setWindowIcon(QtGui.QIcon(config.find_file_path("logo.png")))
        self.setWindowTitle("AutoRigger V.1.0")
        self.setObjectName("AutoRiggerV01")

        self._loadUi(ui_file_path)
        self._connectWidgets()

        self.infoWindow = None

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

        self.spineChecker = self.ui.findChild(QtWidgets.QGroupBox, "")

        self.spineSlider = self.ui.findChild(QtWidgets.QSlider,"SpineAmount_Slider")
        self.spineCustomization = self.ui.findChild(QtWidgets.QGroupBox,"CustomizableSpine_grp")

        self.curveMult = self.ui.findChild(QtWidgets.QSlider, "SpineCurve_Slider")

        self.spineAmntText = self.ui.findChild(QtWidgets.QLabel, "SpineAmnt_Number")
        self.spineCurveText = self.ui.findChild(QtWidgets.QLabel, "SpineCurve_text")

        self.orientJointsBtn = self.ui.findChild(QtWidgets.QPushButton, "autoOrientJoints_btn")


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

        self.allOrientJoints = self.ui.findChild(QtWidgets.QRadioButton, "orientJoint_all_radio")
        self.selectedOrientJoints = self.ui.findChild(QtWidgets.QRadioButton, "orientJoint_selected_radio")
        self.endJntOrientsJoints = self.ui.findChild(QtWidgets.QRadioButton, "OnlyEndJoints_radio")

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

        self.digigradeCheck = self.ui.findChild(QtWidgets.QCheckBox, "DigiGradeLegs_btn")
        self.digigradeCheck2 = self.ui.findChild(QtWidgets.QCheckBox, "DigiGradeLegs_btn_2")
        self.digigradeCheck3 = self.ui.findChild(QtWidgets.QCheckBox, "DigiGradeLegs_btn_3")


        #-----------------------------------advancec -----------------------------------------------
        self.scriptsList = self.ui.findChild(QtWidgets.QListWidget, "scriptLists_list")
        self.advancedBuild = self.ui.findChild(QtWidgets.QPushButton, "advancedRig_btn")
        self.addScript = self.ui.findChild(QtWidgets.QPushButton, "AddScript_btn")
        self.removeScript = self.ui.findChild(QtWidgets.QPushButton, "removeScript_btn")
        self.overrideBase = self.ui.findChild(QtWidgets.QCheckBox, "overrideRig_btn")

        self.infobutton = self.ui.findChild(QtWidgets.QPushButton, "aboutMe_btn")

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

        if self.digigradeCheck:
            self.digigradeCheck.toggled.connect(self.digigradeCheck2.setChecked)
            self.digigradeCheck.toggled.connect(self.digigradeCheck3.setChecked)

        if self.digigradeCheck2:
            self.digigradeCheck2.toggled.connect(self.digigradeCheck.setChecked)
            self.digigradeCheck2.toggled.connect(self.digigradeCheck3.setChecked)

        if self.digigradeCheck3:
            self.digigradeCheck3.toggled.connect(self.digigradeCheck.setChecked)
            self.digigradeCheck3.toggled.connect(self.digigradeCheck2.setChecked)

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

        if self.spineCustomization:
            self.spineCustomization.toggled.connect(self.spineUpdate)
                
            
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
            self.mirrorLocatorBtn.clicked.connect(self.mirrorLocs)


        #-----------------------------------rev feet connections -----------------------------------------------#
        if self.MirrorRevFeet: 
            self.MirrorRevFeet.clicked.connect(lambda : mirror.mirrorLocators("L_backOfHeel_revLOC"))

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

        if self.orientJointsBtn:
            self.orientJointsBtn.clicked.connect(self.jointOrientRadio)


        #-----------------------------------Advanced -----------------------------------------------

        if self.advancedBuild:
            self.advancedBuild.clicked.connect(self.advancedBuildRig)
        if self.addScript:
            self.addScript.clicked.connect(self.addScriptFunc)
        if self.removeScript:
            self.removeScript.clicked.connect(self.removeScriptFunc)    

        if self.infobutton:
            self.infobutton.clicked.connect(self.openInfoWindow)


    def openInfoWindow(self):
        if self.infoWindow:
            self.infoWindow.close()
            self.infoWindow.deleteLater()

        UI_File = "customScripts_info.ui"
        infoPath = config.find_file_path("UI_Files", UI_File)

        file = QFile(infoPath)
        file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.infoWindow = loader.load(file, self)
        self.infoWindow.setWindowIcon(QtGui.QIcon(config.find_file_path("logo.png")))

        file.close()

        self.infoWindow.adjustSize()
        self.infoWindow.show()



    def closeEvent(self, event):
        if getattr(self, "selectionJob", None):
            cmds.scriptJob(kill=self.selectionJob, force=True)
        self.locatorSymmetry.setChecked(False)
        if not self.locsParentedState:
            self.locatorHier.reparentHierarchy()
        if self.localRotationAxesToggle.isChecked():
            self.localRotationAxesToggle.setChecked(False)
        super().closeEvent(event)

    # ─────────────────────────────────────────────────────────────────────────
    # RIG BUILD
    # ─────────────────────────────────────────────────────────────────────────

    def buildRigButton(self):
        """
        Validates the scene state and fires the full rig build.
        Checks reverse feet locators exist on both sides before proceeding.
        """

        with config.mayaUndo():
            expected = {
                "outerSideFoot_revLOC",
                "innerSideFoot_revLOC",
                "frontFoot_revLOC",
                "backOfHeel_revLOC"}
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
            self.digigradeLeg = self.digigradeCheck.isChecked()

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
                self.ribbonBinds,
                self.digigradeLeg
            )
            print("\n ^^^^^^^^^^^^^^^^^^^^^^^^ \n ..Rig built!") 

    def spineValue(self):
        value = self.spineSlider.value()

        if value % 2 == 0:
            value += 1

        text = value + 2
        self.spineAmntText.setText(f"{text}")

        return value
    
    def spineUpdate(self, checked):

        """
        Runs the procedural spine when the customization group is toggled.
        Blocks if guides are unparented or the spine guides don't exist yet.

            Parameters:
                checked (bool): State of the CustomizableSpine group box.
        """

        required = ["C_spineJA_GUIDE", 
                    "C_spineJEnd_GUIDE"]

        if not all(cmds.objExists(guide) for guide in required):
            if checked:
                self.spineCustomization.setChecked(False)
                return cmds.warning("Spine does not exist. Generate using prefix C and basename spine")
        
        if not self.locsParentedState: 
            if checked:
                self.spineCustomization.setChecked(False)
                return cmds.warning("Guides are unparented, spine customization currently unavailable")
            
        if checked: 
            self.procSpine.updateSpine(self.spineValue(), self.slider.value())
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
        """
        Reads the prefix, base name and slider value from the UI
        and creates a procLocatorGenerator instance from them.

            Returns:
                procLocatorGenerator: Configured instance ready to generate.
        """

        prefix = self.prefixLocChain.text()
        baseName = self.baseNameLocChain.text()
        sliderValue = self.locatorValue()

        instance = procLoc.procLocatorGenerator(sliderValue, baseName, prefix)
        
        return instance
    
    def guideGenerator(self):
        """
        Creates a new procedural locator chain from the current UI values.
        Sets self.locGuidesCreated so the slider update knows its safe to run.
        """

        self.generator = self.createInstanceLocChain()
        self.generator.generateLocs()

        self.locGuidesCreated = True
    
    def generateLocs(self):
        """
        Updates the procedural locator chain when the slider changes.
        Only runs if a chain has already been generated this session.
        """

        with config.mayaUndo():
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

    def updateSizeLabelTwist(self, value):
        if self.twistLabel:
            self.twistLabel.setText(str(value))

    def defineRotOrder(self):
        """
        Reads all rotation order dropdowns from the UI and stores
        them on self for use during the rig build.
        """     

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
        Opens a file dialog, loads a JSON preset and recreates the locator hierarchy.
        If the selected file contains 'reverseFeet' in the path, dispatches to
        build_reverseFeetLocators instead unless allowReverseDispatch is False.

            Parameters:
                textBox: UI line edit to update with the chosen file path.
                storeLocators (bool): Whether to append created locators to locatorList.
                locatorList (list): Target list to store imported locators.
                filePath (str): Skip the dialog and use this path directly.
                allowReverseDispatch (bool): Whether reverse feet detection is active.
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
        """
        Recreates a locator hierarchy from a loaded JSON dict.
        Creates a root_GUIDE if none exists and parents the first locator under it.

            Parameters:
                presetData (dict): The loaded JSON hierarchy data.
                storeLocators (bool): Whether to append locators to locatorList.
                locatorList (list): Target list to store created locators.
        """
        
        with config.mayaUndo():
            for root_name, root_data in presetData.items():
                if cmds.objExists(root_name.replace('JNT', 'GUIDE')):
                    return cmds.warning("This preset has already been loaded")
                
                self.build_locator(root_name, root_data, locatorList, storeLocators)

                if locatorList is not self.revFeetLocList:
                    root = cmds.ls("root_*", type = 'transform') 

                    if not root: 
                        print("no root")
                        rootguide = cmds.spaceLocator(n = "root_GUIDE")[0]
                        cmds.setAttr(f"{rootguide}.overrideEnabled", 1)
                        cmds.setAttr(f"{rootguide}.overrideColor", 17) 
                    
                        if rootguide:
                            cmds.parent(locatorList[0], rootguide)

            cmds.select(clear = True)
            cmds.makeIdentity(locatorList, apply = True, t = True)

    def build_locator(self, locator_name: str, joint_data: dict, locatorList, storeLocators, parent=None):
        """
        Recursively creates locators from a joint hierarchy dict.
        Colour codes by joint type — JA is green, JEnd is red, everything else white.

            Parameters:
                locator_name (str): Name for the locator, JNT is replaced with GUIDE.
                joint_data (dict): Dict containing pos and children.
                locatorList (list): List to append created locators to.
                storeLocators (bool): Whether to actually append.
                parent (str): Parent locator name, if any.
        """

        cmds.select(clear=True)

        loc = cmds.spaceLocator(
            n=locator_name.replace('JNT', 'GUIDE'))[0]

        cmds.setAttr(f"{loc}.overrideEnabled", 1)
        if "JA" in loc:
            colour = 14
        elif "JEnd" in loc:
            colour = 13
        else: 
            colour = 17
            
        cmds.setAttr(f"{loc}.overrideColor", colour)        
        
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
        """
        Imports the reverse feet preset and mirrors it to the right side.
        Blocks if locators already exist in the scene.

            Parameters:
                filePath (str): Path to the preset. Opens a dialog if None.
        """

        with config.mayaUndo():
            self.revFeetLocList.clear()
            if cmds.objExists("L_backOfHeel_revLOC"):
                return cmds.warning("Reverse Feet locators already in scene,"
                                    "delete them before importing new ones.")
            
            self.importPreset(self.revFeetTextBox, storeLocators = False, locatorList = self.revFeetLocList, filePath = filePath, allowReverseDispatch=False)

            mirroredRevFeet = mirror.mirrorLocators("L_backOfHeel_revLOC")

            self.revFeetLocList.extend(mirroredRevFeet)

            cmds.select(clear = True)

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
        """
        When a locator is selected, set the slider/label to its current scale.
        """

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

    def mirrorLocs(self):
        """
        Mirrors selected locators and deduplicates the locator list afterwards.
        """

        mirror.mirrorLocators()
        self.locatorList[:] = list(dict.fromkeys(self.locatorList))
                
    def symmetryToggle(self, checked, symmetry, checkBox):
        """
        Connects or disconnects live symmetry for the given locator set.
        Freezes transforms before connecting so offsets don't contaminate the connection.
        Unchecks and warns if no locators are found.

            Parameters:
                checked (bool): Whether symmetry is being enabled or disabled.
                symmetry: The symmetry instance to toggle.
                checkBox: The checkbox that triggered the toggle, used for blockSignals.
        """
        with config.mayaUndo():
            if checked:
                locs = cmds.ls("*_GUIDE", type='transform')
                cmds.makeIdentity(locs, a = True, t = True, r = True)

            if not self.locatorList:
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
        """
        Unparents the full locator hierarchy for individual editing.
        Disables symmetry and spine customization while guides are separated.
        Tracks parented state so closeEvent can restore if needed.
        """

        self.locsParentedState = False
        if self.locatorSymmetry.isChecked():
            self.locatorSymmetry.setChecked(False)
        guides = cmds.ls("*GUIDE", type='transform')
        for guide in guides: 
            if guide not in self.locatorList: 
                self.locatorList.append(guide)

        self.spineCustomizationState = self.spineCustomization.isChecked()
        self.spineCustomization.setChecked(False)
        self.locatorHier.unparentHierarchy()

    def reparentClicked(self):
        """
        Restores the locator hierarchy and re-enables spine customization
        to whatever state it was in before unparenting.
        """

        self.locsParentedState = True
        self.locatorHier.reparentHierarchy()
        self.spineCustomization.setChecked(self.spineCustomizationState)



    def discoverGuides(self):
        """
        Scans the scene for anything ending in _GUIDE and repopulates
        self.locatorList. Resets override colours to white.
        """

        self.locatorList.clear()

        locators = cmds.ls("*_GUIDE", type='transform') or []
        if not locators: 
            return cmds.warning("No guides within the scene")

        for loc in locators: 
            cmds.setAttr(f"{loc}.overrideEnabled", 1)
            cmds.setAttr(f"{loc}.overrideColor", 17)
            self.locatorList.append(loc)

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
        with config.mayaUndo():
            self.jointsList.clear()

            if self.locatorSymmetry.isChecked():
                self.locatorSymmetry.setChecked(False)

            if not self.locsParentedState: 
                self.locatorHier.reparentHierarchy()  

        
            self.locatorList[:] = cmds.ls("*GUIDE", type="transform") or []
                
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

            self.allOrientJoints.setChecked(True)
            self.jointOrientRadio()

            cmds.select(clear = True)   
            #locGrp = cmds.group(roots, n = "Guide_Locator_GRP")
            cmds.select(clear = True)   
            #skelGrp = cmds.group(roots[0].replace("GUIDE", "JNT"), n = "_Skeleton_GRP")
            cmds.hide(roots)

            cmds.select(clear = True)   

    def exportJointsjson(self):

        selected = cmds.ls(sl = True, type = 'joint')

        if len(selected) != 1:
            cmds.warning("Please select only the root of the chain you want to export")
            return
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

    def jointOrientRadio(self):
        with config.mayaUndo():
            if self.allOrientJoints.isChecked():
                self.jointOrient.jointOrientation(self.digigradeCheck.isChecked())
            elif self.selectedOrientJoints.isChecked():
                self.jointOrient.orientSelectedJoints(self.digigradeCheck.isChecked())
            elif self.endJntOrientsJoints.isChecked():
                self.jointOrient.orientOnlyEndJoints()


    def mirrorJoints(self):
        """
        Mirrors joints based on input from UI
        """

        with config.mayaUndo(): 
            self.jointsList[:] = cmds.ls("*_JNT", type="joint") or []

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

            leftJoints = [j for j in leftJoints if "eye" not in j and "Ear" not in j]
            rightJoints = [j for j in rightJoints if "eye" not in j and "Ear" not in j]  #rebuilds the list but removes the eyejoints


            if self.leftToRight.isChecked():
                sourceJoints = leftJoints
                targetJoints = rightJoints
                prefix = left
                mirror = right
                side = "Left to right"

            elif self.rightToLeft.isChecked():
                sourceJoints = rightJoints
                targetJoints = leftJoints
                prefix = right
                mirror = left
                side = "Right to left"

            cmds.delete(targetJoints)

            mirrorRoots = []

            for joint in sourceJoints:
                parent = cmds.listRelatives(joint, parent=True)

                if parent and parent[0].startswith("C_"):
                    mirrorRoots.append(joint)

            for joint in mirrorRoots:
                cmds.mirrorJoint(joint, 
                                mirrorBehavior = True,
                                mirrorYZ = True,
                                searchReplace = (prefix, mirror))
            
            cmds.select(cl = True)
            print(f"Joints mirrored {side}")

    def showLocalRotationAxes(self):
        """
            Toggles the visibility of local rotation axes on joints.
        """
        with config.mayaUndo():
            if len(self.jointsList) == 0:
                try:
                    self.localRotationAxesToggle.blockSignals(True)
                    self.localRotationAxesToggle.setChecked(False)
                finally: 
                    self.localRotationAxesToggle.blockSignals(False)

                return cmds.warning("No joints found, unable to enable local rotation axes")
            
            selectedJoints = cmds.ls(sl = True, 
                                    type = 'joint')
            self.jointsList[:] = cmds.ls(type='joint')
            if self.allLRA.isChecked():
                for joint in self.jointsList:
                    cmds.setAttr(f"{joint}.displayLocalAxis", 1)
            
            elif self.selectedLRA.isChecked():
                for joint in selectedJoints:
                    cmds.setAttr(f"{joint}.displayLocalAxis", 1)

            if not self.localRotationAxesToggle.isChecked():
                for joint in self.jointsList:
                    cmds.setAttr(f"{joint}.displayLocalAxis", 0)

    
    def previewPV(self, checked):
        """
        Creates a polygon face showing where the pole vector
        will land for the selected limb chain.
        Supports digigrade legs with a longer chain length.

            Parameters:
                checked (bool): Whether the visualizer is being turned on or off.
        """

        with config.mayaUndo():
            if not checked:
                if cmds.objExists("*_PV_Visualization"):
                    cmds.delete(cmds.ls("*_PV_Visualization"))
                return

            sel = cmds.ls(sl=True, type='transform')
            if len(sel) != 1:
                self.pvVisualizer.setChecked(False)
                return cmds.warning("Please select exactly one root joint.")

            children = cmds.listRelatives(sel, ad=True, type='transform') or []
            children.reverse()
            chain = sel + children

            isLeg = "leg" in chain[0].lower()
            chainlength = 4 if (self.digigradeCheck.isChecked() and isLeg) else 3

            if len(chain) < chainlength:
                self.pvVisualizer.setChecked(False)
                cmds.warning("Not enough joints to create a visualiser")
                return

            locFunc.poleVectorVisualization(chain[:chainlength], pvDistance=10)
        cmds.select(clear=True)

            
    # ─────────────────────────────────────────────────────────────────────────
    # Rig options
    # ─────────────────────────────────────────────────────────────────────────

    def toggleRigOptions(self, checked):
        """
        Enforces mutual exclusivity between rig option groups.
        Twist and ribbons/stretchy can't be active at the same time.
        Clears the relevant checkboxes when a conflicting group is enabled.

            Parameters:
                checked (bool): Whether the sending group box was just enabled.
        """

        sender = self.sender() #returns the widget that sent the signal to run the function

        if sender == self.ribbonCheckGrp and checked:
            self.twistCheckGrp.setChecked(False)
            self.twistArmCheck.setChecked(False)
            self.twistLegCheck.setChecked(False)

        elif sender == self.twistCheckGrp and checked:
            self.ribbonCheckGrp.setChecked(False)
            self.ribbonArmCheck.setChecked(False)
            self.ribbonLegCheck.setChecked(False)

    # ─────────────────────────────────────────────────────────────────────────
    # script import
    # ─────────────────────────────────────────────────────────────────────────

    def addScriptFunc(self):
        folder = config.find_file_path("Custom_Scripts")
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(self.ui,
                                                            "Load Script",
                                                            folder,
                                                            "Python Files (*.py)"
                                                            )
        if filePath:
            fileName = os.path.basename(filePath)

        """if fileName in self.scriptsList:
            self.scriptsList.removeItem(fileName)"""

        if not filePath:
            return
            
        item = QtWidgets.QListWidgetItem(fileName)
        item.setData(QtCore.Qt.UserRole, filePath)
        self.scriptsList.addItem(item)


    def removeScriptFunc(self):
        selection = self.scriptsList.currentRow()

        if selection >= 0:
            self.scriptsList.takeItem(selection)

    def advancedBuildRig(self):
        with config.mayaUndo():
            if not self.overrideBase.isChecked():
                self.buildRigButton()

            for i in range(self.scriptsList.count()):
                item = self.scriptsList.item(i)
                filePath = item.data(QtCore.Qt.UserRole)

                spec = importlib.util.spec_from_file_location("customScript", filePath)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                module.build()