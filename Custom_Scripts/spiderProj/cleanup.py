import maya.cmds as cmds # pyright: ignore[reportMissingImports] 
from autoRigger.utils import shapes, config
import importlib

importlib.reload(shapes)

##refactor this so that the modules fill in this dict instead of finding everything w maya cmds
cleanupData_spider = {
        "globalCtrl"        : [],

        "leg_IK_GRP"        :  {
                "L" : [],
                "R" : [] 
                }, 

        "leg_FK_GRP"       : {
                "L" : [],
                "R" : []
                },

        "leg_Driver_JNT"    : {
                "L" : [],
                "R" : []
                },
        
        "FKIK_switches"     : {
                "L" : [],
                "R" : []
                },

        "prosoma_FKs"       : [],
        "coxa"              : [],
        "coxaFollows"       : [],
        "chelicerae_FKs"    : {
                "L" : [],
                "R" : []
                },

        "abdomen_FKs"       : [],

        "prosomaSpace"      : None,
        "prosomaRoll"       : None,

        "rig_helper_GRP"    : [],
        "textShapes"        : [],
        "cog"               : None,

        }

def cleanup():
        #Automated color selection based on name
        shapes.ctrlColour()

        skeleton = cmds.ls('*root*JNT', type='joint')[0]
        skeletonGrp = cmds.group(skeleton, n = "skeleton_GRP")
        deformersGrp = cmds.group(em = True, n = "deformers")
        cmds.select(clear=True)
        #dntGrp = cmds.group(em = True, n = "DO_NOT_TOUCH")

        prosomaFKs = cleanupData_spider['prosoma_FKs']
        prosomaConnection = cleanupData_spider['prosoma_FKs'][0]
        prosomaMid = cleanupData_spider['prosoma_FKs'][1]
        abdomenFks = cleanupData_spider['abdomen_FKs'][0]

        l_chel = cmds.group(cleanupData_spider['chelicerae_FKs']['L'], n = "L_Chelicerae_GRP")
        r_chel = cmds.group(cleanupData_spider['chelicerae_FKs']['R'], n = "R_Chelicerae_GRP")
        cheliceraeFK_Grp = cmds.group(r_chel, l_chel, n = "Chelicerae_GRP")

        coxaGrp = cmds.group(*cleanupData_spider['coxaFollows'], n = "coxa_Follows_GRP")
        cog = cleanupData_spider['cog']
        cogLoc = cleanupData_spider['cog'].replace('CTRL', 'LOC')

        l_drivers = cmds.group(cleanupData_spider['leg_Driver_JNT']['L'], n = "L_drivers_GRP")
        r_drivers = cmds.group(cleanupData_spider['leg_Driver_JNT']['R'], n = "R_drivers_GRP")
        driver_Grp = cmds.group(r_drivers, l_drivers, n = "Driver_JNTs_GRP")

        L_leg_GRP = cmds.group(cleanupData_spider['leg_FK_GRP']['L'], n = "L_leg_FK_GRP")
        R_leg_GRP = cmds.group(cleanupData_spider['leg_FK_GRP']['R'], n = "R_leg_FK_GRP")
        fkGrp = cmds.group(L_leg_GRP, R_leg_GRP, n = "Leg_FK_GRP")

        L_leg_switches_GRP = cmds.group(cleanupData_spider['FKIK_switches']['L'], n = "L_leg_FKIK_switch_GRP")
        R_leg_switches_GRP = cmds.group(cleanupData_spider['FKIK_switches']['R'], n = "R_leg_FKIK_switch_GRP")

        L_legIK_GRP = cmds.group(cleanupData_spider['leg_IK_GRP']['L'], n = "L_leg_IK_GRP")
        R_legIK_GRP = cmds.group(cleanupData_spider['leg_IK_GRP']['R'], n = "R_leg_IK_GRP")
        ikGrp = cmds.group(L_legIK_GRP, R_legIK_GRP, n = "Legs_IK_GRP")


        globalCtrl = "global_CTRL"

        fkikSwitch = cmds.group(R_leg_switches_GRP, L_leg_switches_GRP, n = "FKIK_Switches")


        cmds.scaleConstraint(cleanupData_spider["globalCtrl"], skeletonGrp, n = f"{skeletonGrp}{config.suffix['scaleCon']}")
        prosomaEnd = cleanupData_spider["prosoma_FKs"][-1].replace('LOC', 'CTRL')

        locs = cmds.ls("*LOC*", s = True)
        for loc in locs:
                cmds.setAttr(f"{loc}.visibility", 0) 

        cmds.hide(driver_Grp)
        
        cleanup = {
                prosomaConnection : [coxaGrp],

                cog               : [abdomenFks,
                                     fkGrp],

                prosomaEnd        : [cheliceraeFK_Grp],

                ikGrp             : [fkikSwitch],
                
                deformersGrp      : [skeletonGrp, 
                                      driver_Grp],

                globalCtrl        : [ikGrp,
                                        deformersGrp,
                                        prosomaConnection,
                                        cogLoc],
                }

        for parent, child in cleanup.items():
                print(f"[{child}] parented to [{parent}]")
                cmds.parent(child, parent)

        shapes.shapeColour(cleanupData_spider["textShapes"])