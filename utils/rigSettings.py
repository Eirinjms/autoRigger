class RigSettings:
    """
    Stores all build options for the autorigger.
    """

    def __init__(self, 
                 armOrder, 
                 legOrder, 
                 handOrder, 
                 spineOrder, 
                 neckOrder, 
                 stretchyArms, 
                 stretchyLegs, 
                 twistArms, 
                 twistLegs, 
                 twistAmount, 
                 twistJoints, 
                 ribbons, 
                 spineJoints, 
                 sides, 
                 limbs):

        # Rotation Orders
        self.armOrder = armOrder
        self.legOrder = legOrder
        self.handOrder = handOrder
        self.spineOrder = spineOrder
        self.neckOrder = neckOrder

        # Features
        self.stretchyArms = stretchyArms
        self.stretchyLegs = stretchyLegs

        self.twistArms = twistArms
        self.twistLegs = twistLegs
        self.twistAmount = twistAmount
        self.twistJoints = twistJoints

        self.ribbons = ribbons

        # Skeleton
        self.spineJoints = spineJoints

        # Build options
        self.sides = sides
        self.limbs = limbs