import autoRigger.modules.uiModules.UIConnections as con
import autoRigger.utils.config as config
from PySide6 import QtWidgets
import maya.cmds as cmds 
import importlib
import sys

importlib.reload(con)

def run_autorigger():
    for widget in QtWidgets.QApplication.topLevelWidgets():
        if type(widget).__name__ == "AutoRiggerUI":

            print(type(widget))
            print(con.AutoRiggerUI)
            print(type(widget) is con.AutoRiggerUI)
            print(isinstance(widget, con.AutoRiggerUI))
            print(widget.__class__.__mro__)
            print(id(type(widget)))
            print(id(con.AutoRiggerUI))
            print(widget.__class__.__module__)
            print(con.AutoRiggerUI.__module__)
            print(sys.modules.keys())

            widget.close()
            widget.deleteLater()

    UI_File = "AutoRigger_v01.ui"
    autoRiggerWindow = con.AutoRiggerUI(config.find_file_path("UI_Files", UI_File))
    autoRiggerWindow.adjustSize()
    autoRiggerWindow.show()

