import bpy
import sys

# 全局变量：记录已注册的类和属性，确保精准清理
_registered_classes = []
_registered_scene_props = ["BackgroundColor"]


class MMDBackgroundColorPicker_Panel(bpy.types.Panel):
    """Selects world background color and a contrasting text color"""
    bl_idname = "object_pt_mmd_background_color_picker"  # 修复：Blender 3.6要求ID全小写（避免识别异常）
    bl_label = "MMD Background Color Picker"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "mmd_tools_helper"
    bl_order = 8  # 控制面板显示顺序（与其他MMD工具错开）

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)  # 优化：用column统一布局，提升可读性
        
        # 标题与说明
        col.label(text="MMD Background Settings", icon="WORLD")
        col.separator(factor=0.5)
        
        # 背景色选择器（独占一列，便于操作）
        col.prop(context.scene, "BackgroundColor", text="Background Color")
        col.separator(factor=0.5)
        
        # 应用按钮（突出显示，避免误触）
        col.operator(
            "mmd_tools_helper.background_color_picker",
            text="Apply Background & Text Color",
            icon="COLOR"
        )


def main(context):
    try:
        # 1. 启用3D视图的世界显示（兼容Blender 3.6多窗口场景）
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    # 用override_context临时切换上下文（3.6安全方式，避免直接遍历spaces报错）
                    with context.temp_override_window(window, area=area):
                        for space in area.spaces:
                            if space.type == 'VIEW_3D':
                                space.show_world = True  # 启用世界背景显示
                                break  # 每个3D视图只处理一次，提升效率
        
        # 2. 确保世界环境存在且节点树完整（3.6新增：避免默认世界无节点树报错）
        if not context.scene.world:
            # 创建新世界并启用节点
            new_world = bpy.data.worlds.new(name="MMD_Background_World")
            new_world.use_nodes = True  # 强制启用节点（Blender 3.6默认世界可能关闭节点）
            context.scene.world = new_world
        
        # 获取世界节点树（容错处理：防止节点树被删除）
        world_node_tree = context.scene.world.node_tree
        if not world_node_tree or "Background" not in world_node_tree.nodes:
            # 重建默认世界节点（3.6标准节点结构）
            world_node_tree.nodes.clear()  # 清空无效节点
            output_node = world_node_tree.nodes.new(type='ShaderNodeOutputWorld')
            background_node = world_node_tree.nodes.new(type='ShaderNodeBackground')
            # 连接节点
            world_node_tree.links.new(background_node.outputs["Background"], output_node.inputs["Surface"])
            # 调整节点位置（提升用户可编辑性）
            background_node.location = (-300, 0)
            output_node.location = (0, 0)
        
        # 3. 设置背景色（添加alpha通道，兼容3.6节点输入格式）
        background_node = world_node_tree.nodes["Background"]
        bg_color = context.scene.BackgroundColor
        # 转换为4通道（RGBA），alpha固定为1.0（世界背景不透明）
        background_node.inputs["Color"].default_value = (bg_color[0], bg_color[1], bg_color[2], 1.0)
        
        # 4. 设置对比色文本（适配Blender 3.6主题系统，避免索引错误）
        theme = context.preferences.themes.get("Default")  # 3.6推荐用get()获取默认主题，避免索引0报错
        if theme:
            # 计算对比色（亮度反转，确保文本清晰）
            text_color = (1.0 - bg_color[0], 1.0 - bg_color[1], 1.0 - bg_color[2], 1.0)
            # 设置3D视图文本高亮色（影响UI文字，如骨骼名称、坐标轴）
            theme.view_3d.space.text_hi = text_color
            # 额外优化：设置3D视图文本普通色（提升整体对比度）
            theme.view_3d.space.text = (text_color[0] * 0.8, text_color[1] * 0.8, text_color[2] * 0.8, 1.0)
        
        # 提示成功（输出到信息区）
        context.active_operator.report({'INFO'}, f"Background color applied: RGB({bg_color[0]:.2f}, {bg_color[1]:.2f}, {bg_color[2]:.2f})")

    except Exception as e:
        # 错误捕获（避免工具崩溃Blender）
        error_msg = f"Failed to apply background color: {str(e)}"
        print(error_msg)
        context.active_operator.report({'ERROR'}, error_msg)


class MMDBackgroundColorPicker(bpy.types.Operator):
    """Selects world background color and a contrasting text color (MMD compatible)"""
    bl_idname = "mmd_tools_helper.background_color_picker"
    bl_label = "Apply MMD Background Color"
    bl_options = {'REGISTER', 'UNDO'}  # 3.6支持撤销，提升用户体验
    bl_description = "Set world background color and auto-adjust 3D view text color for contrast"

    @classmethod
    def poll(cls, context):
        """控制操作器可用性：确保有场景上下文"""
        return context.scene is not None

    def execute(self, context):
        main(context)
        return {'FINISHED'}


# 注册场景属性（Blender 3.6标准：外部注册，避免类内属性问题）
def register_scene_properties():
    for prop_name in _registered_scene_props:
        if not hasattr(bpy.types.Scene, prop_name):  # 避免重复注册，防止属性冲突
            setattr(
                bpy.types.Scene,
                prop_name,
                bpy.props.FloatVectorProperty(
                    name="Background Color",
                    description="Set MMD world background color (auto-adjusts text contrast)",
                    default=(1.0, 1.0, 1.0),  # 默认白色背景
                    min=0.0, max=1.0,
                    soft_min=0.0, soft_max=1.0,
                    precision=3,  # 提升颜色精度，支持细腻调节
                    options={'ANIMATABLE'},  # 允许关键帧动画（如背景色渐变）
                    subtype='COLOR',  # 显示为颜色选择器UI（3.6标准）
                    size=3  # RGB三通道
                )
            )


def register():
    global _registered_classes
    # 1. 注册场景属性
    register_scene_properties()
    
    # 2. 注册类（按依赖顺序：先注册操作器，再注册面板）
    classes_to_register = [
        MMDBackgroundColorPicker,
        MMDBackgroundColorPicker_Panel
    ]
    
    for cls in classes_to_register:
        if not hasattr(bpy.types, cls.bl_idname):  # 检查是否已注册，避免重复报错
            try:
                bpy.utils.register_class(cls)
                _registered_classes.append(cls)
                print(f"Registered MMD Background Tool: {cls.bl_idname}")
            except Exception as e:
                print(f"Failed to register {cls.bl_idname}: {str(e)}")


def unregister():
    global _registered_classes
    # 1. 反注册类（逆序：先注册的后反注册，避免依赖冲突）
    for cls in reversed(_registered_classes):
        if hasattr(bpy.types, cls.bl_idname):
            try:
                bpy.utils.unregister_class(cls)
                print(f"Unregistered MMD Background Tool: {cls.bl_idname}")
            except Exception as e:
                print(f"Failed to unregister {cls.bl_idname}: {str(e)}")
    _registered_classes.clear()
    
    # 2. 清理场景属性（避免残留数据，防止Blender启动警告）
    for prop_name in _registered_scene_props:
        if hasattr(bpy.types.Scene, prop_name):
            delattr(bpy.types.Scene, prop_name)
            print(f"Cleared MMD Background Tool property: {prop_name}")


if __name__ == "__main__":
    register()