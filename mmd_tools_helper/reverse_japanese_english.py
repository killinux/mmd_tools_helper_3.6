import bpy

class ReverseJapaneseEnglishPanel(bpy.types.Panel):
    """Sets up nodes in Blender node editor for rendering toon textures"""
    bl_idname = "OBJECT_PT_reverse_japanese_english"
    bl_label = "Reverse Japanese English names"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"  # 改为Blender默认支持的"Tool"分类

    def draw(self, context):
        layout = self.layout
        row = layout.row()

        row.label(text="Reverse Japanese English names", icon="TEXT")
        row = layout.row()
        row.operator("mmd_tools_helper.reverse_japanese_english", text = "Reverse Japanese English names")
        row = layout.row()

def main(context):
    # 处理材质名称
    for m in bpy.data.materials:
        if hasattr(m, 'mmd_material'):
            name_j = m.mmd_material.name_j
            name_e = m.mmd_material.name_e
            if name_e != '':
                m.mmd_material.name_e = name_j
                m.mmd_material.name_j = name_e
                m.mmd_material.name = name_e

    # 更新材质名称
    for m in bpy.data.materials:
        if hasattr(m, 'mmd_material'):
            m.name = m.mmd_material.name

    # 处理骨骼名称
    for o in bpy.context.scene.objects:
        if o.type == 'ARMATURE':
            o.data.show_names = True
            bpy.context.view_layer.objects.active = o
            bpy.ops.object.mode_set(mode='POSE')
            for b in bpy.context.active_object.pose.bones:
                if hasattr(b, 'mmd_bone'):
                    name_j = b.mmd_bone.name_j
                    name_e = b.mmd_bone.name_e
                    if name_e != '':
                        b.mmd_bone.name_j = name_e
                        b.mmd_bone.name_e = name_j
                        b.name = name_e

    bpy.ops.object.mode_set(mode='OBJECT')

    # 处理顶点变形名称
    for o in bpy.context.scene.objects:
        if hasattr(o, 'mmd_type') and o.mmd_type == 'ROOT':
            for vm in o.mmd_root.vertex_morphs:
                name_j = vm.name
                name_e = vm.name_e
                if name_e != '':
                    vm.name = name_e
                    vm.name_e = name_j


class ReverseJapaneseEnglish(bpy.types.Operator):
    """Reverses Japanese and English names of shape keys, materials, bones"""
    bl_idname = "mmd_tools_helper.reverse_japanese_english"
    bl_label = "Reverse Japanese English names of MMD model"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        main(context)
        self.report({'INFO'}, "Successfully reversed Japanese and English names")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(ReverseJapaneseEnglish)
    bpy.utils.register_class(ReverseJapaneseEnglishPanel)


def unregister():
    bpy.utils.unregister_class(ReverseJapaneseEnglish)
    bpy.utils.unregister_class(ReverseJapaneseEnglishPanel)


if __name__ == "__main__":
    register()
    