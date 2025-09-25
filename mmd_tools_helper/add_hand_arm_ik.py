import bpy
import math
from . import model  # 依赖外部model模块，需确保该模块存在且适配3.6

class Add_MMD_Hand_Arm_IK_Panel(bpy.types.Panel):
    """Add hand and arm IK bones and constraints to active MMD model"""
    bl_idname = "OBJECT_PT_mmd_add_hand_arm_ik"
    bl_label = "Add Hand Arm IK to MMD model"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"  # Blender 2.8+使用UI区域
    bl_category = "mmd_tools_helper"

    def draw(self, context):
        layout = self.layout
        row = layout.row()

        row.label(text="Add hand arm IK to MMD model", icon="ARMATURE_DATA")
        row = layout.row()
        row.operator("object.add_hand_arm_ik", text = "Add hand_arm IK to MMD model")
        row = layout.row()


def clear_IK(context):
    IK_target_bones = []
    IK_target_tip_bones = []
    armature = model.findArmature(context.active_object)
    context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    
    english = ["elbow_L", "elbow_R", "wrist_L", "wrist_R", "middle1_L", "middle1_R"]
    japanese = ["左ひじ", "右ひじ", "左手首", "右手首", "左中指１", "右中指１"]
    japanese_L_R = ["ひじ.L", "ひじ.R", "手首.L", "手首.R", "中指１.L", "中指１.R"]
    arm_hand_bones = english + japanese + japanese_L_R
    
    for b_name in arm_hand_bones:
        if b_name in armature.pose.bones:
            bone = armature.pose.bones[b_name]
            for constraint in bone.constraints[:]:
                if constraint.type == "IK":
                    print("c.target = ", constraint.target)
                    if constraint.target == armature:
                        if constraint.subtarget is not None:
                            print("c.subtarget = ", constraint.subtarget)
                            if constraint.subtarget not in IK_target_bones:
                                IK_target_bones.append(constraint.subtarget)
    
    for b_name in IK_target_bones:
        if b_name in armature.pose.bones:
            for child_bone in armature.pose.bones[b_name].children:
                if child_bone.name not in IK_target_tip_bones:
                    IK_target_tip_bones.append(child_bone.name)
    
    bones_to_be_deleted = set(IK_target_bones + IK_target_tip_bones)
    print("bones to be deleted = ", bones_to_be_deleted)
    
    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature.data.edit_bones
    for b_name in bones_to_be_deleted:
        if b_name in edit_bones:
            edit_bones.remove(edit_bones[b_name])
    
    bpy.ops.object.mode_set(mode='POSE')
    for b_name in arm_hand_bones:
        if b_name in armature.pose.bones:
            bone = armature.pose.bones[b_name]
            for constraint in bone.constraints[:]:
                bone.constraints.remove(constraint)


def armature_diagnostic(armature):
    ENGLISH_ARM_BONES = ["elbow_L", "elbow_R", "wrist_L", "wrist_R", "middle1_L", "middle1_R"]
    JAPANESE_ARM_BONES = ["左ひじ", "右ひじ", "左手首", "右手首", "左中指１", "右中指１"]
    IK_BONE_NAMES = ["elbow IK_L", "elbow IK_R", "middle1 IK_L", "middle1 IK_R"]
    ENGLISH_OK = True
    JAPANESE_OK = True

    print('\n\n\nThese English bones are needed to add hand IK:\n')
    print(ENGLISH_ARM_BONES, '\n')
    for b_name in ENGLISH_ARM_BONES:
        if b_name not in armature.data.bones:
            ENGLISH_OK = False
            print(f'This bone is not in this armature: {b_name}')
    if ENGLISH_OK:
        print('OK! All English-named bones are present')

    print('\nOR These Japanese bones are needed to add IK:\n')
    print(JAPANESE_ARM_BONES, '\n')
    for b_name in JAPANESE_ARM_BONES:
        if b_name not in armature.data.bones:
            JAPANESE_OK = False
            print(f'This bone is not in this armature: {b_name}')
    if JAPANESE_OK:
        print('OK! All Japanese-named bones are present\n')

    print('\nHand IK bones already in the armature:\n')
    for b_name in IK_BONE_NAMES:
        if b_name in armature.data.bones:
            print(f'This IK bone already exists: {b_name}')


def main(context):
    armature = model.findArmature(context.active_object)
    context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='OBJECT')

    ARM_LEFT_BONE = ["左ひじ", "ひじ.L", "elbow_L"]
    ARM_RIGHT_BONE = ["右ひじ", "ひじ.R", "elbow_R"]
    ELBOW_LEFT_BONE = ["左手首", "手首.L", "wrist_L"]
    ELBOW_RIGHT_BONE = ["右手首", "手首.R", "wrist_R"]
    WRIST_LEFT_BONE = ["左中指１", "中指１.L", "middle1_L"]
    WRIST_RIGHT_BONE = ["右中指１", "中指１.R", "middle1_R"]

    ARM_LEFT = ARM_RIGHT = ELBOW_LEFT = ELBOW_RIGHT = WRIST_LEFT = WRIST_RIGHT = None

    print('\nSearching for target bones...')
    for b in armature.data.bones:
        if b.name in ARM_LEFT_BONE:
            ARM_LEFT = b.name
            print(f'ARM_LEFT = {ARM_LEFT}')
        if b.name in ARM_RIGHT_BONE:
            ARM_RIGHT = b.name
            print(f'ARM_RIGHT = {ARM_RIGHT}')
        if b.name in ELBOW_LEFT_BONE:
            ELBOW_LEFT = b.name
            print(f'ELBOW_LEFT = {ELBOW_LEFT}')
        if b.name in ELBOW_RIGHT_BONE:
            ELBOW_RIGHT = b.name
            print(f'ELBOW_RIGHT = {ELBOW_RIGHT}')
        if b.name in WRIST_LEFT_BONE:
            WRIST_LEFT = b.name
            print(f'WRIST_LEFT = {WRIST_LEFT}')
        if b.name in WRIST_RIGHT_BONE:
            WRIST_RIGHT = b.name
            print(f'WRIST_RIGHT = {WRIST_RIGHT}')

    missing_bones = []
    if not ARM_LEFT: missing_bones.append("ARM_LEFT (elbow_L/左ひじ/ひじ.L)")
    if not ARM_RIGHT: missing_bones.append("ARM_RIGHT (elbow_R/右ひじ/ひじ.R)")
    if not ELBOW_LEFT: missing_bones.append("ELBOW_LEFT (wrist_L/左手首/手首.L)")
    if not ELBOW_RIGHT: missing_bones.append("ELBOW_RIGHT (wrist_R/右手首/手首.R)")
    if not WRIST_LEFT: missing_bones.append("WRIST_LEFT (middle1_L/左中指１/中指１.L)")
    if not WRIST_RIGHT: missing_bones.append("WRIST_RIGHT (middle1_R/右中指１/中指１.R)")
    
    if missing_bones:
        raise Exception(f"Missing required bones: {', '.join(missing_bones)}")

    elbow_length = armature.data.bones[ELBOW_LEFT].length
    DOUBLE_LENGTH_OF_ELBOW_BONE = elbow_length * 2
    TWENTIETH_LENGTH_OF_ELBOW_BONE = elbow_length * 0.05

    bpy.ops.object.mode_set(mode='EDIT')
    edit_bones = armature.data.edit_bones

    bone_elbow_ik_l = edit_bones.new("elbow_IK_L")
    bone_elbow_ik_l.head = edit_bones[ELBOW_LEFT].head
    bone_elbow_ik_l.tail = edit_bones[ELBOW_LEFT].head.copy()
    bone_elbow_ik_l.tail.z -= DOUBLE_LENGTH_OF_ELBOW_BONE

    bone_elbow_ik_r = edit_bones.new("elbow_IK_R")
    bone_elbow_ik_r.head = edit_bones[ELBOW_RIGHT].head
    bone_elbow_ik_r.tail = edit_bones[ELBOW_RIGHT].head.copy()
    bone_elbow_ik_r.tail.z -= DOUBLE_LENGTH_OF_ELBOW_BONE

    bone_mid1_ik_l = edit_bones.new("middle1_IK_L")
    bone_mid1_ik_l.head = edit_bones[WRIST_LEFT].head
    bone_mid1_ik_l.tail = edit_bones[WRIST_LEFT].head.copy()
    bone_mid1_ik_l.tail.z -= DOUBLE_LENGTH_OF_ELBOW_BONE
    bone_mid1_ik_l.parent = edit_bones["elbow_IK_L"]
    bone_mid1_ik_l.use_connect = False

    bone_mid1_ik_r = edit_bones.new("middle1_IK_R")
    bone_mid1_ik_r.head = edit_bones[WRIST_RIGHT].head
    bone_mid1_ik_r.tail = edit_bones[WRIST_RIGHT].head.copy()
    bone_mid1_ik_r.tail.z -= DOUBLE_LENGTH_OF_ELBOW_BONE
    bone_mid1_ik_r.parent = edit_bones["elbow_IK_R"]
    bone_mid1_ik_r.use_connect = False

    def create_tip_bone(parent_name, tip_name, offset_axis, offset_val):
        tip_bone = edit_bones.new(tip_name)
        parent_bone = edit_bones[parent_name]
        tip_bone.head = parent_bone.head
        tip_bone.tail = parent_bone.head.copy()
        setattr(tip_bone.tail, offset_axis, getattr(tip_bone.tail, offset_axis) + offset_val)
        tip_bone.parent = parent_bone
        tip_bone.use_connect = False
        bpy.ops.object.mode_set(mode='POSE')
        pose_bone = armature.pose.bones[tip_name]
        pose_bone.bone.hide = True
        if hasattr(pose_bone, "mmd_bone"):
            pose_bone.mmd_bone.is_visible = False
            pose_bone.mmd_bone.is_controllable = False
            pose_bone.mmd_bone.is_tip = True
        bpy.ops.object.mode_set(mode='EDIT')

    create_tip_bone("elbow_IK_L", "elbow_IK_L_t", "y", TWENTIETH_LENGTH_OF_ELBOW_BONE)
    create_tip_bone("elbow_IK_R", "elbow_IK_R_t", "y", TWENTIETH_LENGTH_OF_ELBOW_BONE)
    create_tip_bone("middle1_IK_L", "middle1_IK_L_t", "z", -TWENTIETH_LENGTH_OF_ELBOW_BONE)
    create_tip_bone("middle1_IK_R", "middle1_IK_R_t", "z", -TWENTIETH_LENGTH_OF_ELBOW_BONE)

    bpy.ops.object.mode_set(mode='POSE')

    def add_ik_constraint(bone_name, target_subtarget, chain_count, iterations=48):
        bone = armature.pose.bones[bone_name]
        ik_const = bone.constraints.new("IK")
        ik_const.target = armature
        ik_const.subtarget = target_subtarget
        ik_const.chain_count = chain_count
        ik_const.use_tail = True
        ik_const.iterations = iterations

    add_ik_constraint(ARM_LEFT, "elbow_IK_L", chain_count=2)
    add_ik_constraint(ARM_RIGHT, "elbow_IK_R", chain_count=2)
    add_ik_constraint(ELBOW_LEFT, "middle1_IK_L", chain_count=1, iterations=6)
    add_ik_constraint(ELBOW_RIGHT, "middle1_IK_R", chain_count=1, iterations=6)

    for bone_name in [ARM_LEFT, ARM_RIGHT, ELBOW_LEFT, ELBOW_RIGHT]:
        if hasattr(armature.pose.bones[bone_name], "mmd_bone"):
            if "elbow" in bone_name.lower():
                armature.pose.bones[bone_name].mmd_bone.ik_rotation_constraint = 4
            else:
                armature.pose.bones[bone_name].mmd_bone.ik_rotation_constraint = 2

    if 'IK' not in armature.pose.bone_groups:
        armature.pose.bone_groups.new(name="IK")
    ik_group = armature.pose.bone_groups['IK']

    ik_bone_names = [
        "elbow_IK_L", "elbow_IK_R", "middle1_IK_L", "middle1_IK_R",
        "elbow_IK_L_t", "elbow_IK_R_t", "middle1_IK_L_t", "middle1_IK_R_t"
    ]
    for b_name in ik_bone_names:
        if b_name in armature.pose.bones:
            armature.pose.bones[b_name].bone_group = ik_group


class Add_MMD_Hand_Arm_IK(bpy.types.Operator):
    """Add hand and arm IK bones and constraints to active MMD model"""
    bl_idname = "object.add_hand_arm_ik"
    bl_label = "Add Hand Arm IK to MMD model"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None 
                and model.findArmature(context.active_object) is not None)

    def execute(self, context):
        try:
            armature = model.findArmature(context.active_object)
            armature_diagnostic(armature)
            clear_IK(context)
            main(context)
            self.report({'INFO'}, "Successfully added hand/arm IK!")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to add IK: {str(e)}")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(Add_MMD_Hand_Arm_IK)
    bpy.utils.register_class(Add_MMD_Hand_Arm_IK_Panel)


def unregister():
    bpy.utils.unregister_class(Add_MMD_Hand_Arm_IK)
    bpy.utils.unregister_class(Add_MMD_Hand_Arm_IK_Panel)


if __name__ == "__main__":
    register()
