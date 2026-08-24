self.scriptsList = self.ui.findChild(QtWidget.QListWidget, "scriptLists_list")
self.advancedBuild = self.ui.findChild(QtWidget.QPushButton, "advancedRig_btn")
self.addScript = self.ui.findChild(QtWidget.QPushButton, "AddScript_btn")
self.removeScript = self.ui.findChild(QtWidget.QPushButton, "removeScript_btn")
self.overrideBase = self.ui.findChild(QtWidget.QCheckBox, "overrideRig_btn")


if self.advancedBuild:
    self.advancedBuild.clicked.Connect(self.advancedBuildRig)
if self.addScript:
    self.addScript.clicked.Connect(self.addScriptFunc)
if self.removeScript:
    self.removeScript.clicked.connect(self.removeScriptFunc)


def addScriptFunc(self):
    filePath, _ = QtWidgets.QFileDialog.getOpenFileName(self.ui,
                                                        "Load Script",
                                                        "",
                                                        "Python Files (*.py)"
                                                        )
    if filePath:
        fileName = os.path.basename(filePath)
        
    item = QtWidgets.QListWidgetItem(fileName)
    item.setData(QtCore.Qt.UserRole, filePath)
    self.scriptsList.addItem(item)

def removeScriptFunc(self):
    selection = self.scriptsList.currentRow()

    if selection >= 0:
        self.scriptsList.takeItem(selection)

def overrideBase(self):
    """tbf this would just be to say "dont run build script" """

def advancedBuildRig(self):
    with config.mayaUndo:
        if not self.overrideBase.isChecked():
            self.buildRig()

        for i in range(self.scriptsList.count()):
            item = self.scriptsList.item(i)
            filePath = item.data(QtCore.Qt.UserRole)

            spec = importlib.util.spec_from_file_location("customScript", filePath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            module.build()