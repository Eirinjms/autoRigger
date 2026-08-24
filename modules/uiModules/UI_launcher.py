import autoRigger.modules.uiModules.UIConnections as con
import autoRigger.utils.config as config
from PySide6 import QtWidgets
import maya.cmds as cmds 
import importlib

importlib.reload(con)

def run_autorigger():
    for widget in QtWidgets.QApplication.topLevelWidgets():
        if type(widget).__name__ == "AutoRiggerUI":
            widget.close()
            widget.deleteLater()

    UI_File = "AutoRigger_v02.ui"
    autoRiggerWindow = con.AutoRiggerUI(config.find_file_path("UI_Files", UI_File))
    autoRiggerWindow.adjustSize()
    autoRiggerWindow.show()

