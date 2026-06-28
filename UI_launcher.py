import autoRigger.config as config
import maya.cmds as cmds
import os
import importlib

importlib.reload(con)

try:
    autoRiggerWindow.close()  # close previous instance if it exists
    autoRiggerWindow.deleteLater()
except (NameError, RuntimeError):
    pass

UI_File = "AutoRiggerAlternatepart2.ui"
autoRiggerWindow = con.AutoRiggerUI(config.find_file_path("UI_Files", UI_File))
autoRiggerWindow.adjustSize()
autoRiggerWindow.show()