import bpy

class MMDCameraToBlenderCameraPanel(bpy.types.Panel):
    """Convert MMD cameras back to Blender cameras"""
    bl_idname = "OBJECT_PT_mmd_camera_to_blender_camera"
    bl_label = "Convert MMD Cameras to Blender cameras"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "mmd_tools_helper"

    def draw(self, context):
        layout = self.layout
        row = layout.row()

        row = layout.row()
        row.operator("mmd_tools_helper.mmd_camera_to_blender_camera", text="Convert MMD cameras to Blender cameras")
        row = layout.row()

def main(context):
    # 遍历场景中的所有相机
    for o in bpy.context.scene.objects:
        if o.type == 'CAMERA':
            camera = o
            # 解锁所有变换
            camera.lock_location = (False, False, False)
            camera.lock_rotation = (False, False, False)
            camera.lock_scale = (False, False, False)

            # 静音所有驱动
            if o.animation_data is not None:
                for d in o.animation_data.drivers:
                    d.mute = True

            # 处理MMD相机父对象
            if camera.parent is not None:
                # 检查父对象是否是MMD相机控制器
                if hasattr(camera.parent, 'mmd_type') and camera.parent.mmd_type == 'CAMERA':
                    # 移除MMD相机控制器
                    bpy.context.scene.collection.objects.unlink(camera.parent)
                    # 清除父关系但保持变换
                    bpy.context.view_layer.objects.active = camera
                    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

class MMDCameraToBlenderCamera(bpy.types.Operator):
    """Convert MMD cameras back to Blender cameras"""
    bl_idname = "mmd_tools_helper.mmd_camera_to_blender_camera"
    bl_label = "Convert MMD Cameras to Blender cameras"
    bl_options = {'REGISTER', 'UNDO'}  # 添加UNDO支持，提升用户体验

    def execute(self, context):
        main(context)
        self.report({'INFO'}, "MMD cameras converted to Blender cameras")
        return {'FINISHED'}


def register():
    # 修正类名，使用正确的MMDCameraToBlenderCamera
    bpy.utils.register_class(MMDCameraToBlenderCamera)
    bpy.utils.register_class(MMDCameraToBlenderCameraPanel)


def unregister():
    # 同样修正注销时的类名
    bpy.utils.unregister_class(MMDCameraToBlenderCamera)
    bpy.utils.unregister_class(MMDCameraToBlenderCameraPanel)


if __name__ == "__main__":
    register()
