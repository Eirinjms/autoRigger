from unicodedata import name
import maya.cmds as cmds # pyright: ignore[reportMissingImports]
import maya.mel as mel # pyright: ignore[reportMissingImports]

# ------------------------------
# ARROW
# ------------------------------
def fourWayArrowCtrl(name, size):
    ctrl = cmds.curve(
        d=1,
        p=[
            (-1,0,-1), (-1,0,-3), (-2,0,-3), (0,0,-5), (2,0,-3), (1,0,-3), (1,0,-1),
            (3,0,-1), (3,0,-2), (5,0,0), (3,0,2), (3,0,1), (1,0,1), (1,0,3),
            (2,0,3), (0,0,5), (-2,0,3), (-1,0,3), (-1,0,1), (-3,0,1),
            (-3,0,2), (-5,0,0), (-3,0,-2), (-3,0,-1), (-1,0,-1)
        ],
        k=list(range(25)),
        name=name
    )

    curve = cmds.ls(sl=True)[0]
    
    shape = cmds.listRelatives(curve, shapes=True, type="nurbsCurve")[0]
    
    cvs = cmds.ls(shape + ".cv[*]", fl=True)

    indices = [0, 6, 12, 18, 24]

    for i in indices:
        cv = cvs[i]
        cmds.xform(cv, s=(1.5, 1.5, 1.5))

    cmds.xform(ctrl, s=(size, size, size))
    cmds.makeIdentity(ctrl, apply=True, t=True, r=True, s=True)

    return ctrl
# ------------------------------
# CUBE
# ------------------------------

def cubeCtrl(name, X, Y, Z):
    ctrl = cmds.curve(
    d=1,
    p=[
    (1,1,1),(1,-1,1),(1,-1,-1),(1,1,-1),(1,1,1),
    (-1,1,1),(-1,-1,1),(1,-1,1),(1,1,1),
    (1,1,-1),(-1,1,-1),(-1,-1,-1),(1,-1,-1),
    (-1,-1,-1),(-1,-1,1),(-1,1,1),(-1,1,-1)
    ],
    k=list(range(17)),
    name=name
    )


    cmds.xform(ctrl, s=(X, Y, Z))
    cmds.makeIdentity(ctrl, apply=True, t=True, r=True, s=True)


    return ctrl

# ------------------------------
# PYRAMID
# ------------------------------
def pyramidCtrl(name, size):
    ctrl = cmds.curve(
        d=1,
        p=[
            ( 1.72909, -1.72909, -1.72909), 
            ( 0.0,      1.72909,  0.0     ), 
            (-1.72909, -1.72909, -1.72909),
            ( 1.72909, -1.72909, -1.72909),
            (-1.72909, -1.72909, -1.72909),
            (-1.72909, -1.72909,  1.72909),
            ( 0.0,      1.72909,  0.0     ),
            (-1.72909, -1.72909,  1.72909),
            ( 1.72909, -1.72909,  1.72909),
            ( 0.0,      1.72909,  0.0     ),
            ( 1.72909, -1.72909, -1.72909),
            ( 1.72909, -1.72909,  1.72909)
        ],
        k=list(range(12)),
        name=name
    )

    cmds.xform(ctrl, ro = (90,0,0))
    cmds.xform(ctrl, s=(size, size, size))
    cmds.makeIdentity(ctrl, apply=True, t=True, r=True, s=True)

    return ctrl


# ------------------------------
# ONEWAY ARROW
# ------------------------------


def oneWayArrowCtrl(name, size):
    ctrl = cmds.curve(
        d=1,
        p=[
            (-1, 0,  2),
            (-1, 0,  0),
            (-2, 0,  0),
            ( 0, 0, -3),
            ( 2, 0,  0),
            ( 1, 0,  0),
            ( 1, 0,  2),
            (-1, 0,  2)
        ],
        k=list(range(8)),
        name=name
    )

    cmds.xform(ctrl, s=(size, size, size))
    cmds.makeIdentity(ctrl, apply=True, t=True, r=True, s=True)

    return ctrl

# ------------------------------
# TWO WAY ARROW
# ------------------------------

def twoWayArrowCtrl(name, size):
    ctrl = cmds.curve(
        d=1,
        p=[
            ( 1, 0, -2),
            ( 1, 0,  2),
            ( 2, 0,  2),
            ( 0, 0,  5),
            (-2, 0,  2),
            (-1, 0,  2),
            (-1, 0, -2),
            (-2, 0, -2),
            ( 0, 0, -5),
            ( 2, 0, -2),
            ( 1, 0, -2)
        ],
        k=list(range(11)),
        name=name
    )

    cmds.xform(ctrl, s=(size, size, size))
    cmds.makeIdentity(ctrl, apply=True, t=True, r=True, s=True)

    return ctrl

# ------------------------------
# Text Curve CTRL
# ------------------------------

def txtCTRL(name, size):
    txtCurve = cmds.textCurves(f = "Lucida Sans Unicode", o = True, t = name)

    curves = cmds.ls('curve*')
    charGrp = cmds.ls('Char*')

    cmds.parent(curves, world = True)

    cmds.delete(txtCurve)

    curves = cmds.ls(selection=True, long=True)


    if len(curves) < 2:
        cmds.error("Please select at least 2 curves. First selected = master.")

    master = curves[0]
    donors = curves[1:]

    cmds.makeIdentity(curves, apply=True, t=True, r=True, s=True, n=False)

    shapes = []

    for donor in donors:
        donor_shapes = cmds.listRelatives(donor, shapes=True, fullPath=True) or []
        shapes.extend(donor_shapes)

    cmds.select(clear=True)
    cmds.select(shapes, add=True)
    cmds.select(master, add=True)

    cmds.parent(r=True, s=True)

    cmds.delete(curves[1:])
    cmds.select(master)
    cmds.rename(master, name +"_CTRL")
    cmds.CenterPivot()
    cmds.xform(s = (size, size, size))


# ------------------------------
# Diamond CTRL / Pole Vector CTRL
# ------------------------------

def pvCtrl(name, size):
    circleCurve = cmds.circle(r = size, name = name, nr = (0,0,1))[0]
    
    curve = cmds.ls(sl=True)[0]
    
    shape = cmds.listRelatives(curve, shapes=True, type="nurbsCurve")[0]
    
    cvs = cmds.ls(shape + ".cv[*]", fl=True)
    
    cmds.xform(cvs[1::2], s = (3, 3, 3))

    cmds.makeIdentity(circleCurve, t = 1, s = 1, r = 1)

    return circleCurve 


# ------------------------------
# Eye CTRL
# ------------------------------

def eyeCtrl(name, size):
    ctrl = cmds.circle(n = name, r = size, nr = (1,0,0))[0]

    shape = cmds.listRelatives(ctrl, shapes=True, type="nurbsCurve")[0]

    cvs = cmds.ls(shape + ".cv[*]", fl=True)

    indices = [1,5]

    for i in indices:
        cv = cvs[i]
        cmds.xform(cv, s = (0.2, 0.2, 0.2))

    indexes = [3,7]

    for i in indexes:
        cv = cvs[i]
        cmds.xform(cv, s = (1, 1, 1.3))

    cmds.makeIdentity(ctrl, apply = True, t = True, r = True, s = True)

    return ctrl

# ------------------------------
# Gear CTRL 
# ------------------------------

def gearCtrl(name, size, side, limb):
    ctrl = cmds.curve(
        d = 1, p = [
    (-0.923879, 0,  0.22961),
    (-1.123879, 0,  0.229611),
    (-1.12388,  0, -0.22961),
    (-0.92388,  0, -0.22961),
    (-0.81564,  0, -0.490923),
    (-0.957062, 0, -0.632344),
    (-0.632344, 0, -0.957062),
    (-0.490923, 0, -0.81564),
    (-0.22961,  0, -0.923879),
    (-0.22961,  0, -1.123879),
    ( 0.22961,  0, -1.12388),
    ( 0.22961,  0, -0.92388),
    ( 0.490923, 0, -0.81564),
    ( 0.632344, 0, -0.957062),
    ( 0.957062, 0, -0.632344),
    ( 0.81564,  0, -0.490923),
    ( 0.92388,  0, -0.22961),
    ( 1.12388,  0, -0.22961),
    ( 1.12388,  0,  0.22961),
    ( 0.92388,  0,  0.22961),
    ( 0.81564,  0,  0.490923),
    ( 0.957062, 0,  0.632344),
    ( 0.632344, 0,  0.957062),
    ( 0.490923, 0,  0.81564),
    ( 0.22961,  0,  0.92388),
    ( 0.22961,  0,  1.12388),
    (-0.22961,  0,  1.12388),
    (-0.22961,  0,  0.92388),
    (-0.490923, 0,  0.81564),
    (-0.632344, 0,  0.957062),
    (-0.957061, 0,  0.632344),
    (-0.81564,  0,  0.490923),
    (-0.923879, 0,  0.22961),]
    , n = name)

    if side == "L_":
        if limb == "leg":
            innerCircle = cmds.circle(r = 0.7, n = "L_legInnerCircle", nr = (0,1,0))[0]
        elif limb == "arm":
            innerCircle = cmds.circle(r = 0.7, n = "L_armInnerCircle", nr = (0,1,0))[0]
            
    elif side == "R_":
        if limb == "leg":
            innerCircle = cmds.circle(r = 0.7, n = "R_legInnerCircle", nr = (0,1,0))[0]
        elif limb == "arm":
            innerCircle = cmds.circle(r = 0.7, n = "R_armInnerCircle", nr = (0,1,0))[0]

    else: 
     innerCircle = cmds.circle(r = 0.7, n = "InnerCircle", nr = (0,1,0))[0]   
       
    innerShape = cmds.listRelatives(innerCircle, s=True)[0]

    cmds.parent(innerShape, ctrl, r=True, s=True)

    cmds.xform(ctrl, s = (size, size, size))

    cmds.delete(innerCircle)

    return ctrl


def squareCtrl(name, size):
    ctrl = cmds.curve(
        d = 1, p=[
        ( 1, 0,  1),
        ( 1, 0, -1),
        (-1, 0, -1),
        (-1, 0,  1),
        ( 1, 0,  1)],

        k=[0, 1, 2, 3, 4], 
        n = name)

    cmds.xform(ctrl, s=(size, size, size))
    cmds.makeIdentity(ctrl, apply=True, t=True, r=True, s=True)

    return ctrl


# ------------------------------
# ctrl colour
# ------------------------------

def ctrlColour():
    ctrls = cmds.ls("*_CTRL", type="transform")

    for ctrl in ctrls:
        shapes = cmds.listRelatives(ctrl, s=True, f=True)

        if not shapes:
            continue

        for shape in shapes:
            cmds.setAttr(shape + ".overrideEnabled", 1)

            if ctrl.startswith("C_"):
                cmds.setAttr(shape + ".overrideColor", 17)

            elif ctrl.startswith("L_"):
                cmds.setAttr(shape + ".overrideColor", 6)

            elif ctrl.startswith("R_"):
                cmds.setAttr(shape + ".overrideColor", 13)

        
    switches = cmds.ls("*switch*", type = "transform")
    for switch in switches:
        shapes = cmds.listRelatives(switch, s=True, f=True)

        if not shapes:
            continue

        for shape in shapes:
            cmds.setAttr(f"{shape}.overrideEnabled", 1)
            cmds.setAttr(f"{shape}.overrideColor", 16)

