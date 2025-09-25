import bpy
from . import model

# 全局变量：跟踪已注册的类和属性，确保安全清理
_registered_classes = []
_registered_props = [
    "find_bone_string",
    "replace_bone_string",
    "bones_all_or_selected"
]


class ReplaceBonesRenamingPanel(bpy.types.Panel):
    """Replace Bones Renaming panel"""
    bl_label = "Bone Name Replacer"
    bl_idname = "object_pt_replace_bones_renaming"  # 修正：使用全小写ID符合Blender 3.6规范
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "mmd_tools_helper"
    bl_order = 5  # 控制面板显示顺序

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)  # 使用列布局提升UI紧凑性
        
        # 标题与说明
        col.label(text="Batch Replace Bone Names", icon="RENAME_OBJECT")
        col.separator(factor=0.5)
        
        # 查找字符串输入
        col.label(text="Find:")
        col.prop(context.scene, "find_bone_string", text="")
        
        # 替换字符串输入
        col.label(text="Replace with:")
        col.prop(context.scene, "replace_bone_string", text="")
        
        # 选择范围选项
        col.separator(factor=1.0)
        col.prop(context.scene, "bones_all_or_selected")
        
        # 操作按钮
        col.separator(factor=1.0)
        col.operator(
            "mmd_tools_helper.replace_bones_renaming",
            text="Apply Replacement",
            icon="CHECKMARK"
        )


def main(context):
    try:
        # 找到并激活骨架对象
        armature = model.findArmature(context.active_object)
        if not armature:
            raise RuntimeError("No armature found! Please select an armature or a linked object.")
        
        context.view_layer.objects.active = armature
        initial_mode = context.mode  # 保存初始模式
        
        # 切换到对象模式以安全修改骨骼名称
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        find_str = context.scene.find_bone_string
        replace_str = context.scene.replace_bone_string
        selected_only = context.scene.bones_all_or_selected
        modified_count = 0
        
        # 遍历骨骼并替换名称
        for bone in armature.data.bones:
            # 过滤条件：排除含"dummy"或"shadow"的骨骼
            if 'dummy' in bone.name.lower() or 'shadow' in bone.name.lower():
                continue
            
            # 根据选择状态过滤
            if selected_only and not bone.select:
                continue
            
            # 执行替换
            if find_str in bone.name:
                original_name = bone.name
                bone.name = original_name.replace(find_str, replace_str)
                modified_count += 1
                print(f"Renamed: {original_name} -> {bone.name}")
        
        # 恢复初始模式
        if context.mode != initial_mode:
            bpy.ops.object.mode_set(mode=initial_mode)
        
        # 操作反馈
        context.active_operator.report(
            {'INFO'},
            f"Replaced {modified_count} bone(s) containing '{find_str}'"
        )
        
    except Exception as e:
        # 错误处理
        error_msg = f"Failed to replace bone names: {str(e)}"
        print(error_msg)
        context.active_operator.report({'ERROR'}, error_msg)


class ReplaceBonesRenaming(bpy.types.Operator):
    """Find and replace mass renaming of bones"""
    bl_idname = "mmd_tools_helper.replace_bones_renaming"
    bl_label = "Batch Replace Bone Names"
    bl_options = {'REGISTER', 'UNDO'}  # 支持撤销操作
    bl_description = "Find and replace specific strings in bone names (supports selected bones only)"

    @classmethod
    def poll(cls, context):
        """仅在选中骨架时启用操作"""
        return (context.active_object is not None and 
                (context.active_object.type == 'ARMATURE' or 
                 model.findArmature(context.active_object) is not None))

    def execute(self, context):
        main(context)
        return {'FINISHED'}


# 注册场景属性（Blender 3.6标准方式）
def register_properties():
    for prop in _registered_props:
        if not hasattr(bpy.types.Scene, prop):
            if prop == "find_bone_string":
                bpy.types.Scene.find_bone_string = bpy.props.StringProperty(
                    name="Find String",
                    description="String to find in bone names",
                    default=""
                )
            elif prop == "replace_bone_string":
                bpy.types.Scene.replace_bone_string = bpy.props.StringProperty(
                    name="Replace String",
                    description="String to replace with",
                    default=""
                )
            elif prop == "bones_all_or_selected":
                bpy.types.Scene.bones_all_or_selected = bpy.props.BoolProperty(
                    name="Affect Selected Bones Only",
                    description="Only modify names of selected bones",
                    default=False
                )


def register():
    global _registered_classes
    # 注册属性
    register_properties()
    
    # 注册类
    classes = [
        ReplaceBonesRenamingPanel,
        ReplaceBonesRenaming
    ]
    
    for cls in classes:
        if not hasattr(bpy.types, cls.bl_idname):
            try:
                bpy.utils.register_class(cls)
                _registered_classes.append(cls)
            except Exception as e:
                print(f"Failed to register {cls.__name__}: {e}")


def unregister():
    global _registered_classes
    # 反注册类
    for cls in reversed(_registered_classes):
        if hasattr(bpy.types, cls.bl_idname):
            try:
                bpy.utils.unregister_class(cls)
            except Exception as e:
                print(f"Failed to unregister {cls.__name__}: {e}")
    _registered_classes.clear()
    
    # 清理属性
    for prop in _registered_props:
        if hasattr(bpy.types.Scene, prop):
            delattr(bpy.types.Scene, prop)


if __name__ == "__main__":
    register()
