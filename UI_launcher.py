import autoRigger.modules.uiModules.UIConnections as con
import autoRigger.utils.config as config
import maya.cmds as cmds 
import os
import importlib


importlib.reload(con)
def run_autorigger():
    try:
        autoRiggerWindow.close()  # close previous instance if it exists
        autoRiggerWindow.deleteLater()
    except (NameError, RuntimeError):
        pass

    UI_File = "AutoRigger_v01.ui"
    autoRiggerWindow = con.AutoRiggerUI(config.find_file_path("UI_Files", UI_File))
    autoRiggerWindow.adjustSize()
    autoRiggerWindow.show()