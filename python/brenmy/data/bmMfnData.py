"""
stuff
"""

MFN_TYPE_NAMES = {
    110: "kTransform",
    111: "kAimConstraint",
    121: "kJoint",
    240: "kPointConstraint",
    239: "kOrientConstraint",
    242: "kParentConstraint",
    244: "kScaleConstraint",
    267: "kNurbsCurve",
    294: "kNurbsSurface",
}


def get_mfn_type_name(enum_id):
    if enum_id not in MFN_TYPE_NAMES:
        return "unknown"

    return MFN_TYPE_NAMES[enum_id]
