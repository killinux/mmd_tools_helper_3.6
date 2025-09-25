import bpy
from . import model
from . import import_csv

# 全局变量：记录已注册的类和属性，确保反注册时精准清理
_registered_classes = []
_registered_scene_props = [
    "Origin_Armature_Type",
    "Destination_Armature_Type"
]


class BonesRenamerPanel_MTH(bpy.types.Panel):
    """Creates the Bones Renamer Panel in a VIEW_3D TOOLS tab"""
    bl_label = "Bones Renamer"
    bl_idname = "object_pt_bones_renamer_mth"  # 修复：Blender 3.6要求ID全小写（原大写混合可能导致识别问题）
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "mmd_tools_helper"
    bl_order = 4  # 新增：控制面板在UI中的显示顺序（优化多工具排列）

    def draw(self, context):
        layout = self.layout
        # 优化：减少冗余空行，统一布局间距
        col = layout.column(align=True)
        
        # 标题与图标
        col.label(text="Mass Rename Bones", icon="ARMATURE_DATA")
        col.separator(factor=1.0)  # 分隔线：提升UI可读性
        
        # 源骨骼类型选择
        col.prop(context.scene, "Origin_Armature_Type", text="From")
        # 目标骨骼类型选择
        col.prop(context.scene, "Destination_Armature_Type", text="To")
        col.separator(factor=1.0)
        
        # 主操作按钮（独占一行，突出显示）
        col.operator("object.bones_renamer", text="Mass Rename Bones", icon="RENAME_OBJECT")


# 使用国际字体并显示骨骼名称（增强兼容性检查）
def use_international_fonts_display_names_bones():
    # 修复：增加上下文检查，避免无激活对象时报错
    if not bpy.context.object:
        return
    
    # Blender 3.6用户偏好设置路径（稳定兼容）
    bpy.context.preferences.system.use_international_fonts = True
    if bpy.context.object.type == 'ARMATURE':
        bpy.context.object.data.show_names = True
        # 新增：显示骨骼中文名称（MMD工具常见需求）
        bpy.context.object.data.show_names_enum = 'NAME'


def unhide_all_armatures():
    # 修复：使用context.scene.objects时增加类型检查，避免无效对象
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE' and obj.hide_get():  # 3.6推荐用hide_get()检查隐藏状态
            obj.hide_set(False)  # 2.8+后标准隐藏控制方法


def print_missing_bone_names():
    missing_bone_names = []
    try:
        # 新增：捕获CSV读取异常（避免CSV文件缺失导致崩溃）
        BONE_NAMES_DICTIONARY = import_csv.use_csv_bones_dictionary()
        FINGER_BONE_NAMES_DICTIONARY = import_csv.use_csv_bones_fingers_dictionary()
    except Exception as e:
        print(f"Failed to load bone dictionary: {str(e)}")
        return
    
    SelectedBoneMap = bpy.context.scene.Destination_Armature_Type
    # 修复：检查目标骨骼映射是否存在于字典中
    if SelectedBoneMap not in BONE_NAMES_DICTIONARY[0] or SelectedBoneMap not in FINGER_BONE_NAMES_DICTIONARY[0]:
        print(f"Destination bone map '{SelectedBoneMap}' not found in dictionary!")
        return
    
    BoneMapIndex = BONE_NAMES_DICTIONARY[0].index(SelectedBoneMap)
    FingerBoneMapIndex = FINGER_BONE_NAMES_DICTIONARY[0].index(SelectedBoneMap)
    
    # 确保激活对象是骨架
    armature = model.findArmature(bpy.context.active_object)
    if not armature:
        print("No valid armature found for missing bone check!")
        return
    
    bpy.context.view_layer.objects.active = armature
    armature_bones = armature.data.bones.keys()  # 提前缓存骨骼名称，减少重复查询
    
    # 检查主体骨骼
    for bone_entry in BONE_NAMES_DICTIONARY[1:]:  # 优化：用enumerate替代index()，提升效率
        bone_name = bone_entry[BoneMapIndex]
        if (bone_name != '' 
            and bone_name not in ["upper body 2", "上半身2"] 
            and bone_name not in armature_bones):
            missing_bone_names.append(bone_name)
    
    # 检查手指骨骼
    for bone_entry in FINGER_BONE_NAMES_DICTIONARY[1:]:
        bone_name = bone_entry[FingerBoneMapIndex]
        if (bone_name != '' 
            and bone_name not in ["thumb0_L", "thumb0_R", "左親指0", "親指0.L", "右親指0", "親指0.R"] 
            and bone_name not in armature_bones):
            missing_bone_names.append(bone_name)
    
    # 输出结果（优化格式，便于阅读）
    print("\n" + "="*50)
    print(f"Destination Bone Map: {SelectedBoneMap}")
    print(f"Missing Bones ({len(missing_bone_names)}):")
    for bone in sorted(missing_bone_names):  # 排序输出，便于查找
        print(f"  - {bone}")
    print("="*50 + "\n")


def rename_bones(boneMap1, boneMap2, BONE_NAMES_DICTIONARY): 
    boneMaps = BONE_NAMES_DICTIONARY[0]
    # 修复：检查源/目标映射是否有效
    if boneMap1 not in boneMaps or boneMap2 not in boneMaps:
        raise ValueError(f"Invalid bone map: From '{boneMap1}' To '{boneMap2}'")
    
    boneMap1_index = boneMaps.index(boneMap1)
    boneMap2_index = boneMaps.index(boneMap2)
    
    # 切换到对象模式（骨骼重命名必须在对象模式）
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    armature = bpy.context.active_object
    if armature.type != 'ARMATURE':
        raise TypeError("Active object is not an armature!")
    
    # 优化：批量获取骨骼，减少API调用次数
    armature_bones = armature.data.bones
    for bone_entry in BONE_NAMES_DICTIONARY[1:]:
        src_bone = bone_entry[boneMap1_index]
        dst_bone = bone_entry[boneMap2_index]
        
        if src_bone in armature_bones and dst_bone != '' and src_bone != dst_bone:
            # 重命名骨骼（避免重复命名导致冲突）
            try:
                armature_bones[src_bone].name = dst_bone
            except RuntimeError as e:
                print(f"Failed to rename {src_bone} to {dst_bone}: {str(e)}")
                continue
            
            # 若目标是MMD日语骨骼，更新mmd_bone属性
            if boneMap2 in ['mmd_japanese', 'mmd_japaneseLR']:
                bpy.ops.object.mode_set(mode='POSE')
                pose_bone = armature.pose.bones.get(dst_bone)
                if pose_bone and hasattr(pose_bone, "mmd_bone"):
                    pose_bone.mmd_bone.name_e = bone_entry[0]  # 设置英文名称
                bpy.ops.object.mode_set(mode='OBJECT')


def rename_finger_bones(boneMap1, boneMap2, FINGER_BONE_NAMES_DICTIONARY):
    # 逻辑与主体骨骼重命名一致，复用检查逻辑
    boneMaps = FINGER_BONE_NAMES_DICTIONARY[0]
    if boneMap1 not in boneMaps or boneMap2 not in boneMaps:
        raise ValueError(f"Invalid finger bone map: From '{boneMap1}' To '{boneMap2}'")
    
    boneMap1_index = boneMaps.index(boneMap1)
    boneMap2_index = boneMaps.index(boneMap2)
    
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    armature = bpy.context.active_object
    if armature.type != 'ARMATURE':
        raise TypeError("Active object is not an armature!")
    
    armature_bones = armature.data.bones
    for bone_entry in FINGER_BONE_NAMES_DICTIONARY[1:]:
        src_bone = bone_entry[boneMap1_index]
        dst_bone = bone_entry[boneMap2_index]
        
        if src_bone in armature_bones and dst_bone != '' and src_bone != dst_bone:
            try:
                armature_bones[src_bone].name = dst_bone
            except RuntimeError as e:
                print(f"Failed to rename finger bone {src_bone} to {dst_bone}: {str(e)}")
                continue
            
            if boneMap2 in ['mmd_japanese', 'mmd_japaneseLR']:
                bpy.ops.object.mode_set(mode='POSE')
                pose_bone = armature.pose.bones.get(dst_bone)
                if pose_bone and hasattr(pose_bone, "mmd_bone"):
                    pose_bone.mmd_bone.name_e = bone_entry[0]
                bpy.ops.object.mode_set(mode='OBJECT')
    
    # 更新源骨骼类型为当前目标类型（便于后续二次重命名）
    bpy.context.scene.Origin_Armature_Type = boneMap2
    print_missing_bone_names()


def main(context):
    try:
        # 找到并激活骨架对象（增加异常捕获）
        armature = model.findArmature(context.active_object)
        if not armature:
            raise RuntimeError("No MMD armature found! Please select an MMD model.")
        
        context.view_layer.objects.active = armature
        initial_mode = context.mode  # 保存初始模式，操作后恢复
        
        # 执行核心逻辑
        use_international_fonts_display_names_bones()
        unhide_all_armatures()
        
        # 加载骨骼字典（增加异常处理）
        BONE_NAMES_DICTIONARY = import_csv.use_csv_bones_dictionary()
        FINGER_BONE_NAMES_DICTIONARY = import_csv.use_csv_bones_fingers_dictionary()
        
        # 重命名骨骼
        rename_bones(
            context.scene.Origin_Armature_Type,
            context.scene.Destination_Armature_Type,
            BONE_NAMES_DICTIONARY
        )
        rename_finger_bones(
            context.scene.Origin_Armature_Type,
            context.scene.Destination_Armature_Type,
            FINGER_BONE_NAMES_DICTIONARY
        )
        
        # 切换到姿态模式并全选骨骼（便于用户后续操作）
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='SELECT')
        
        # 恢复初始模式（优化用户体验）
        # bpy.ops.object.mode_set(mode=initial_mode)
        
    except Exception as e:
        # 错误提示（同时输出到控制台和Blender信息区）
        print(f"Bone rename failed: {str(e)}")
        context.active_operator.report({'ERROR'}, str(e))


class BonesRenamer(bpy.types.Operator):
    """Mass bones renamer for armature conversion (MMD compatible)"""
    bl_idname = "object.bones_renamer"
    bl_label = "Mass Rename Bones"
    bl_options = {'REGISTER', 'UNDO'}  # 3.6支持撤销，必须保留
    bl_description = "Rename bones between different armature standards (MMD/XNALara/Rigify etc.)"

    @classmethod
    def poll(cls, context):
        # 严格控制操作器可用性：必须选中骨架且在对象模式
        return (
            context.active_object is not None
            and context.active_object.type == 'ARMATURE'
            and context.mode == 'OBJECT'  # 骨骼重命名必须在对象模式，避免数据损坏
        )

    def execute(self, context):
        main(context)
        self.report({'INFO'}, "Bone renaming completed (check console for missing bones)")
        return {'FINISHED'}


# 定义骨骼类型枚举（单独提取，便于维护）
def get_armature_type_items():
    return [
        ('mmd_english', 'MMD English', 'MikuMikuDance standard English bone names'),
        ('mmd_japanese', 'MMD Japanese', 'MikuMikuDance standard Japanese bone names'),
        ('mmd_japaneseLR', 'MMD Japanese .L.R', 'MMD Japanese with .L/.R suffixes'),
        ('xna_lara', 'XNALara', 'XNALara/XPS bone naming convention'),
        ('daz_poser', 'DAZ/Poser', 'DAZ Studio / Poser / Second Life bone names'),
        ('blender_rigify', 'Blender Rigify', 'Blender Rigify base bone names (pre-rig)'),
        ('sims_2', 'Sims 2', 'The Sims 2 bone naming standard'),
        ('motion_builder', 'Motion Builder', 'Autodesk Motion Builder bone names'),
        ('3ds_max', '3ds Max', 'Autodesk 3ds Max default bone names'),
        ('bepu', 'Bepu IK', 'Bepu Full Body IK bone naming convention'),
        ('project_mirai', 'Project Mirai', 'Hatsune Miku Project Mirai bone names'),
        ('manuel_bastioni_lab', 'Manuel Bastioni', 'Manuel Bastioni Lab character bone names'),
        ('makehuman_mhx', 'MakeHuman MHX', 'MakeHuman MHX export bone names'),
        ('sims_3', 'Sims 3', 'The Sims 3 bone naming standard'),
        ('doa5lr', 'DOA5LR', 'Dead or Alive 5 Last Round bone names'),
        ('Bip_001', 'Bip001', 'Generic Bip001 bone naming (3ds Max/Unity)'),
        ('biped_3ds_max', '3DS Max Biped', '3ds Max Biped system bone names'),
        ('biped_sfm', 'SFM Biped', 'Source Film Maker Biped bone names'),
        ('valvebiped', 'ValveBiped', 'Valve Source Engine ValveBiped bone names'),
        ('iClone7', 'iClone7', 'Reallusion iClone7 default bone names')
    ]


# 注册场景属性（Blender 3.6标准：外部注册，避免类内属性问题）
def register_scene_properties():
    for prop_name in _registered_scene_props:
        if not hasattr(bpy.types.Scene, prop_name):  # 避免重复注册
            if prop_name == "Origin_Armature_Type":
                setattr(
                    bpy.types.Scene,
                    prop_name,
                    bpy.props.EnumProperty(
                        items=get_armature_type_items(),
                        name="Rename From",
                        default='mmd_japanese',
                        description="Original armature bone naming standard"
                    )
                )
            elif prop_name == "Destination_Armature_Type":
                setattr(
                    bpy.types.Scene,
                    prop_name,
                    bpy.props.EnumProperty(
                        items=get_armature_type_items(),
                        name="Rename To",
                        default='mmd_english',
                        description="Target armature bone naming standard"
                    )
                )


def register():
    global _registered_classes
    # 1. 注册场景属性
    register_scene_properties()
    
    # 2. 注册类（按依赖顺序：面板依赖操作器，先注册操作器）
    classes_to_register = [
        BonesRenamer,
        BonesRenamerPanel_MTH
    ]
    
    for cls in classes_to_register:
        if not hasattr(bpy.types, cls.bl_idname):  # 检查是否已注册，避免重复
            try:
                bpy.utils.register_class(cls)
                _registered_classes.append(cls)
                print(f"Registered: {cls.bl_idname}")
            except Exception as e:
                print(f"Failed to register {cls.bl_idname}: {str(e)}")


def unregister():
    global _registered_classes
    # 1. 反注册类（逆序：先注册的后反注册，避免依赖冲突）
    for cls in reversed(_registered_classes):
        if hasattr(bpy.types, cls.bl_idname):
            try:
                bpy.utils.unregister_class(cls)
                print(f"Unregistered: {cls.bl_idname}")
            except Exception as e:
                print(f"Failed to unregister {cls.bl_idname}: {str(e)}")
    _registered_classes.clear()
    
    # 2. 清理场景属性（避免残留数据）
    for prop_name in _registered_scene_props:
        if hasattr(bpy.types.Scene, prop_name):
            delattr(bpy.types.Scene, prop_name)
            print(f"Cleared scene property: {prop_name}")


if __name__ == "__main__":
    register()