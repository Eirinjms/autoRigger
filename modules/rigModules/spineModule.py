import maya.cmds as cmds # pyright: ignore[reportMissingImports] 
import autoRigger.utils.shapes as shapes
import autoRigger.utils.config as config
import autoRigger.utils.hierarchyModule as hier

import importlib
importlib.reload(shapes)

class spineBuilder:
    def __init__(self, spineOrder : int, spineJoints : list):
        self.size = config.bipedal
        self.rotOrder = spineOrder

        self.prefix = config.prefix['center']
        self.suffix = config.suffix
        self.attrs = config.attrs

        if not spineJoints: 
            spineJoints = cmds.ls("*spine*", type = 'joint')
            spineJoints.sort()

        if not spineJoints:
            raise RuntimeError("No spine joints found.")
        
        self.spineJoints = spineJoints

        self.spineJointsAmount = len(spineJoints)
        
        self.spineRoot = spineJoints[0]
        self.spineMiddle = spineJoints[len(spineJoints)//2] #ty stack overflow
        self.spineEnd = spineJoints[-1]

        self.fkJoints = []
        self.ikJoints = []

        self.fkLocs = []
        self.fkCtrls = []

        self.ctrlJoints = []
        self.ikLocs = []
        self.ikCtrls = []
        
        self.spineHier = hier.hierarchyManager([self.spineRoot], False, "transform") 
    
    def duplicatingJoints(self):
        # duplicate joint chains
        for i in config.fkik.values():
            for joint in self.spineJoints:
                source = f"{joint}" 

                if not cmds.objExists(source):
                    cmds.warning(f"{source} does not exist, skipping")
                    continue
                
                config.setRotationOrder(self.spineJoints, self.rotOrder)

                dup = cmds.duplicate(source, po=True, n=joint + i)[0]

                if i == config.fkik['fk']:  # FK chain
                    self.fkJoints.append(dup)
                    if len(self.fkJoints) > 1:
                        cmds.parent(self.fkJoints[-1], self.fkJoints[-2])

                else:  # IK chain
                    self.ikJoints.append(dup)
                    if len(self.ikJoints) > 1:
                        cmds.parent(self.ikJoints[-1], self.ikJoints[-2])


    def fkSetup(self):
        for count, joint in enumerate(self.fkJoints):
            name = joint.replace(self.suffix['joint'], "") 
            fkLoc = cmds.spaceLocator(n = f"{name}{self.suffix['locator']}")[0]
            self.fkLocs.append(fkLoc)

            config.setRotationOrder([fkLoc], self.rotOrder)


            fkCtrl = cmds.circle(n =f"{name}{self.suffix['control']}", 
                                 r = self.size['FKspine'], 
                                 nr = (1,0,0))[0]
            config.setRotationOrder([fkCtrl], self.rotOrder)
            
            self.fkCtrls.append(fkCtrl)
  
            cmds.parent(fkCtrl, fkLoc)
            cmds.delete(cmds.parentConstraint(joint, fkLoc, mo = False))


            if 'spineJA' in joint:
                cmds.parentConstraint(fkCtrl, joint, n = f"{joint}{self.suffix['parentCon']}", mo = False)
            else:
                cmds.orientConstraint(fkCtrl, joint, n = f"{joint}{self.suffix['orientCon']}", mo = False)
            
            if count > 0:
                cmds.parent(self.fkLocs[count], self.fkCtrls[count-1])

    def ikSetup(self):     

        curvepoints = []
        for joint in self.ikJoints: 
            pos = cmds.xform(joint, q = True, ws = True, t = True)
            curvepoints.append(pos)

           
        self.iKctrlCurve = cmds.curve(d = 3, 
                                 ep = curvepoints, 
                                 n = f"{self.prefix}spine{self.suffix['control']}{self.suffix['curve']}")

        cmds.setAttr(f"{self.iKctrlCurve}.inheritsTransform", 0)

        self.ikSpline, _ = cmds.ikHandle(ccv = False, 
                                 sol="ikSplineSolver", 
                                 c = self.iKctrlCurve, 
                                 sj = self.spineRoot, 
                                 ee = self.spineEnd, 
                                 rtm = False, 
                                 n = f"spine{self.suffix['ikspline']}")
        
        if self.spineJointsAmount <= 3:
            curveJoints = self.spineJoints
        else:
            curveJoints = [self.spineRoot, 
                           self.spineMiddle, 
                           self.spineEnd]

        controlNames = ['hip', 
                     'middle', 
                     'shoulders']    

        for joint, name in zip(curveJoints, controlNames):
            cmds.select(clear=True)
            ctrlJoint = cmds.joint(n=f"{self.prefix}spine_{name}{self.suffix['joint']}")
            config.setRotationOrder([ctrlJoint], self.rotOrder)

            cmds.delete(cmds.parentConstraint(joint, ctrlJoint))

            self.ctrlJoints.append(ctrlJoint)

        for joint in self.ctrlJoints:
            ikLoc = cmds.spaceLocator(n = joint.replace(self.suffix['joint'], self.suffix['locator']))[0]
            config.setRotationOrder([ikLoc], self.rotOrder)
            self.ikLocs.append(ikLoc)

            ikCtrl = shapes.cubeCtrl(name = joint.replace(self.suffix['joint'], self.suffix['control']), 
                                     X = self.size['IKspineX'], 
                                     Y = self.size['IKspineY'], 
                                     Z  = self.size['IKspineZ'])
            config.setRotationOrder([ikCtrl], self.rotOrder)
            
            self.ikCtrls.append(ikCtrl)

            cmds.parent(ikCtrl, ikLoc)
            cmds.delete(cmds.parentConstraint(joint, ikLoc, mo = False))

            cmds.parentConstraint(ikCtrl, joint, n = joint.replace(self.suffix['joint'], self.suffix['parentCon']), mo = False)

        cmds.skinCluster(self.ctrlJoints, self.iKctrlCurve, 
                         tsb=True, 
                         n = f"{self.prefix}ikSpine_{self.suffix['skinCluster']}")

    def nodeSetup(self):

        md = cmds.shadingNode('multiplyDivide', au = True)
        cmds.setAttr(f"{md}.input2X", -1)
        pma = cmds.shadingNode('plusMinusAverage', au = True)
        cmds.setAttr(f"{pma}.operation", 1)

        cmds.connectAttr(f"{self.ikCtrls[0]}.rotateX", f"{self.ikSpline}.roll")
        cmds.connectAttr(f"{self.ikCtrls[0]}.rotateX", f"{md}.input1X")
        cmds.connectAttr(f"{md}.outputX", f"{pma}.input1D[0]")
        cmds.connectAttr(f"{self.ikCtrls[-1]}.rotateX", f"{pma}.input1D[1]")
        cmds.connectAttr(f"{pma}.output1D", f"{self.ikSpline}.twist")

    def ikfkSwitch(self):
        baseName = f"{self.prefix}spine_FKIK_switch{config.suffix['control']}"
        self.ikBNDLoc = cmds.spaceLocator(n = f"{baseName}{self.suffix['locator']}") [0]
        self.switch = shapes.gearCtrl(name = f"{baseName}{self.suffix['control']}", 
                                 size = 7, 
                                 limb = 'spine', 
                                 side = 'spine')

        cmds.parent(self.switch, self.ikBNDLoc)
        cmds.parentConstraint(self.spineEnd, self.ikBNDLoc, 
                              n = f"{baseName}{self.suffix['parentCon']}", 
                              mo = False) 

        cmds.addAttr(self.switch, ln = 'FKIK_Switch', at = 'float', min = 0, max = 1, dv = 1, k = True)

        transform=(40, 0, 30) 

        cmds.xform(self.switch, r = True, t = transform, ro = (0, 0, 0))
        cmds.makeIdentity(self.switch, apply = True, t = True, r = True)

        for attr in self.attrs: 
            cmds.setAttr(f"{self.switch}.{attr}", l = True, k = False, cb = False)

    def blends(self):

        for blendCount, joint in enumerate(self.spineJoints): 
            rotBlend = cmds.shadingNode('blendColors', au = True, n = f"{joint}_rot{self.suffix['blendColor']}")

            cmds.connectAttr(f"{self.ikJoints[blendCount]}.rotate", f"{rotBlend}.color1")
            cmds.connectAttr(f"{self.fkJoints[blendCount]}.rotate", f"{rotBlend}.color2")
            cmds.connectAttr(f"{rotBlend}.output", f"{joint}.rotate")

            cmds.connectAttr(f"{self.switch}.FKIK_Switch", f"{rotBlend}.blender")
            
        trnBlend =  cmds.shadingNode('blendColors', au = True, n = f"{self.spineJoints[0]}_tran{self.suffix['blendColor']}") 
        cmds.connectAttr(f"{self.ikJoints[0]}.translate", f"{trnBlend}.color1")
        cmds.connectAttr(f"{self.fkJoints[0]}.translate", f"{trnBlend}.color2")
        cmds.connectAttr(f"{trnBlend}.output", f"{self.spineRoot}.translate")

        cmds.connectAttr(f"{self.switch}.FKIK_Switch", f"{trnBlend}.blender")

    def cleanup(self):

        fkGrp = cmds.group(n = f"spine{config.fkik['fk']}{config.suffix['group']}", em = True)
        ikGrp = cmds.group(n = f"spine{config.fkik['ik']}{config.suffix['group']}", em = True)

        ikJointCtrlGrp = cmds.group(n = f"spineCtrlJoints_GRP", em = True)
        ikCtrlGrp = cmds.group(n = f"ik_CTRL_GRP", em = True)

        cmds.parent(*self.ikLocs, ikCtrlGrp)
        cmds.parent(self.ctrlJoints, ikJointCtrlGrp)
        cmds.parent(self.fkLocs[0], fkGrp)
        cmds.parent(self.ikSpline, ikCtrlGrp, ikJointCtrlGrp, self.iKctrlCurve, ikGrp)

        topSpineLOC = cmds.spaceLocator(n = f"{self.spineJoints[-1]}_BND{self.suffix['locator']}")
        bottomSpineLOC = cmds.spaceLocator(n = f"{self.spineJoints[0]}_BND{self.suffix['locator']}")

        cmds.parentConstraint(self.spineRoot, bottomSpineLOC, n = f"{self.spineJoints[0]}_BND{self.suffix['parentCon']}")
        cmds.parentConstraint(self.spineEnd, topSpineLOC, n = f"{self.spineJoints[2]}_BND{self.suffix['parentCon']}")
        

        cmds.connectAttr(self.switch + '.FKIK_Switch', ikGrp + '.visibility')

        fkikRev = cmds.shadingNode('reverse', au = True, n = self.spineJoints[0] + self.suffix['reverse'])

        cmds.connectAttr(f"{self.switch}.FKIK_Switch", f"{fkikRev}.inputX")
        cmds.connectAttr(f"{fkikRev}.outputX", f"{fkGrp}.visibility")

        globalSpineCtrl = cmds.circle(n = f"{self.prefix}spine_global{self.suffix['control']}", r = 10)[0]
        cmds.matchTransform(globalSpineCtrl, bottomSpineLOC)
        cmds.makeIdentity(globalSpineCtrl, a = True, t = True, r = True, s = True)
        cmds.parent(ikCtrlGrp, globalSpineCtrl)
        cmds.parent(globalSpineCtrl, ikGrp)


        IkswitchCtrl = cmds.group(em = True, w = True, n = f"spine_IK_switch{self.suffix['group']}")
        cmds.parent(self.ikBNDLoc, IkswitchCtrl)

        cmds.hide(self.fkJoints, self.ikJoints, self.ikSpline, ikJointCtrlGrp, self.iKctrlCurve)

    def buildSpine(self):
            self.duplicatingJoints()
            self.fkSetup()
            self.ikSetup()
            self.nodeSetup()
            self.ikfkSwitch()
            self.blends()
            self.cleanup()

            print(f"[SpineBuilder] : Spine built")

