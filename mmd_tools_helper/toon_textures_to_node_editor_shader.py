import bpy
from . import model


# Each image is a list of numbers(floats): R,G,B,A,R,G,B,A etc.
# So the length of the list of pixels is 4 X number of pixels
# pixels are in left-to-right rows from bottom left to top right of image

class MMDToonTexturesToNodeEditorShaderPanel(bpy.types.Panel):
	"""Sets up nodes in Blender node editor for rendering toon textures"""
	bl_idname = "OBJECT_PT_mmd_toon_render_node_editor"
	bl_label = "MMD Toon Texture Node Setup"
	bl_space_type = "VIEW_3D"
	bl_region_type = "UI"  # Blender 2.8+ 后 TOOLS 区域合并为 UI
	bl_category = "mmd_tools_helper"  # 侧边栏标签页名称

	def draw(self, context):
		layout = self.layout
		row = layout.row()

		row.label(text="MMD Render Toon Textures", icon="MATERIAL")
		row = layout.row()
		row.operator("mmd_tools_helper.mmd_toon_render_node_editor", text="Create Toon Material Nodes")
		row = layout.row()


def toon_image_to_color_ramp(toon_texture_color_ramp, toon_image):
	"""将TOON纹理图像转换为颜色渐变节点"""
	pixels_width = toon_image.size[0]
	pixels_height = toon_image.size[1]
	toon_image_pixels = []
	toon_image_gradient = []

	# 提取像素RGBA数据
	for f in range(0, len(toon_image.pixels), 4):
		pixel_rgba = toon_image.pixels[f:f+4]
		toon_image_pixels.append(pixel_rgba)

	# 采样生成渐变（避免像素过多导致节点异常）
	sample_step = max(1, int(len(toon_image_pixels) / 32))  # 最多32个采样点
	for p in range(0, len(toon_image_pixels), sample_step):
		toon_image_gradient.append(toon_image_pixels[p])

	# 设置渐变首尾颜色
	if len(toon_image_gradient) >= 2:
		toon_texture_color_ramp.color_ramp.elements[0].color = toon_image_gradient[0]
		toon_texture_color_ramp.color_ramp.elements[-1].color = toon_image_gradient[-1]

	# 添加中间渐变点
	for i in range(1, len(toon_image_gradient)-1):
		# 计算渐变位置（0-1范围）
		position = i / (len(toon_image_gradient) - 1)
		elem = toon_texture_color_ramp.color_ramp.elements.new(position)
		elem.color = toon_image_gradient[i]
		# 后半段渐变设为透明（MMD TOON纹理特性）
		if i > len(toon_image_gradient) / 2:
			elem.color[3] = 0.0  # Alpha通道设为0
	return


def clear_material_nodes(context):
	"""清空材质中的现有节点（保留基础输出节点）"""
	obj = context.active_object
	if not (obj and obj.type == 'MESH'):
		return
	for mat in obj.data.materials:
		if mat and mat.use_nodes:
			# 保留输出节点（避免删除后无法重建连接）
			output_nodes = [n for n in mat.node_tree.nodes if isinstance(n, bpy.types.ShaderNodeOutputMaterial)]
			# 反向删除非输出节点（避免索引错乱）
			for node in reversed(mat.node_tree.nodes):
				if node not in output_nodes:
					mat.node_tree.nodes.remove(node)


def main(context):
	"""主逻辑：为选中物体创建TOON材质节点树"""
	obj = context.active_object
	if not (obj and obj.type == 'MESH'):
		return

	# 确保场景中有太阳灯（若没有则创建）
	sun_lamp = None
	for lamp in bpy.data.lights:
		if lamp.type == 'SUN':
			sun_lamp = lamp
			break
	if not sun_lamp:
		sun_lamp = bpy.data.lights.new("MMD_Toon_Sun", type='SUN')
		lamp_obj = bpy.data.objects.new("MMD_Toon_Sun_Obj", sun_lamp)
		context.scene.collection.objects.link(lamp_obj)
		context.scene.view_layers[0].objects.active = obj  # 恢复选中物体为活跃

	# 遍历物体的所有材质
	for mat in obj.data.materials:
		if not mat:
			continue
		mat.use_nodes = True
		node_tree = mat.node_tree
		nodes = node_tree.nodes
		links = node_tree.links

		# 1. 获取/创建基础节点
		# 输出节点（Blender 2.8+ 节点类型为 ShaderNodeOutputMaterial）
		output_node = next((n for n in nodes if isinstance(n, bpy.types.ShaderNodeOutputMaterial)), None)
		if not output_node:
			output_node = nodes.new(type='ShaderNodeOutputMaterial')
		output_node.location = (1450, 800)

		# 原理化BSDF节点（替代旧版Material节点，Blender 2.8+ 标准材质节点）
		principled_node = next((n for n in nodes if isinstance(n, bpy.types.ShaderNodeBsdfPrincipled)), None)
		if not principled_node:
			principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
		principled_node.location = (-800, 800)
		principled_node.inputs['Base Color'].default_value = (*mat.diffuse_color, 1.0)  # 同步漫反射色

		# 2. 创建TOON效果所需节点
		# 灯光数据节点（获取灯光方向和阴影信息）
		lamp_node = nodes.new(type='ShaderNodeLightData')
		lamp_node.light_object = bpy.data.objects[sun_lamp.name]  # 关联太阳灯物体
		lamp_node.location = (-530, -50)

		# RGB转灰度节点（处理阴影）
		rgb_to_bw = nodes.new(type='ShaderNodeRGBToBW')
		rgb_to_bw.location = (-90, -50)

		# 向量点积节点（计算法线与灯光方向夹角）
		vector_math_dot = nodes.new(type='ShaderNodeVectorMath')
		vector_math_dot.operation = 'DOT_PRODUCT'
		vector_math_dot.location = (-520, 470)

		# 数学节点（调整点积结果范围）
		math_add = nodes.new(type='ShaderNodeMath')
		math_add.operation = 'ADD'
		math_add.inputs[1].default_value = 1.0
		math_add.location = (-325, 470)

		math_mul1 = nodes.new(type='ShaderNodeMath')
		math_mul1.operation = 'MULTIPLY'
		math_mul1.inputs[1].default_value = 0.5
		math_mul1.location = (-90, 470)

		math_mul2 = nodes.new(type='ShaderNodeMath')
		math_mul2.operation = 'MULTIPLY'
		math_mul2.location = (120, 470)

		# 颜色渐变节点（TOON核心效果）
		toon_color_ramp = nodes.new(type='ShaderNodeValToRGB')
		toon_color_ramp.location = (340, 470)

		# 混合RGB节点（TOON颜色叠加）
		mix_rgb_toon = nodes.new(type='ShaderNodeMixRGB')
		mix_rgb_toon.blend_type = 'MULTIPLY'
		mix_rgb_toon.inputs['Fac'].default_value = 1.0
		mix_rgb_toon.inputs['Color2'].default_value = (1.0, 1.0, 1.0, 1.0)
		mix_rgb_toon.location = (690, 470)
		mix_rgb_toon.label = "Toon Modifier"

		# 混合RGB节点（漫反射色混合）
		mix_rgb_diffuse = nodes.new(type='ShaderNodeMixRGB')
		mix_rgb_diffuse.blend_type = 'MULTIPLY'
		mix_rgb_diffuse.inputs['Fac'].default_value = 1.0
		mix_rgb_diffuse.location = (1000, 470)

		# 混合RGB节点（球面纹理叠加）
		mix_rgb_sphere = nodes.new(type='ShaderNodeMixRGB')
		mix_rgb_sphere.blend_type = 'ADD'
		mix_rgb_sphere.inputs['Fac'].default_value = 1.0
		mix_rgb_sphere.location = (1240, 470)

		# 几何节点（获取UV和法线）
		geo_uv = nodes.new(type='ShaderNodeGeometry')
		geo_uv.location = (620, 250)

		geo_normal = nodes.new(type='ShaderNodeGeometry')
		geo_normal.location = (620, -50)

		# 图像纹理节点（漫反射和球面纹理）
		diffuse_tex = nodes.new(type='ShaderNodeTexImage')
		diffuse_tex.location = (820, 250)

		sphere_tex = nodes.new(type='ShaderNodeTexImage')
		sphere_tex.location = (820, -50)

		# 3. 连接节点链路
		# 基础链路：原理化BSDF -> 输出节点
		links.new(output_node.inputs['Surface'], principled_node.outputs['BSDF'])

		# TOON灯光计算链路
		links.new(vector_math_dot.inputs[0], principled_node.outputs['Normal'])  # 物体法线
		links.new(vector_math_dot.inputs[1], lamp_node.outputs['Light Direction'])  # 灯光方向
		links.new(math_add.inputs[0], vector_math_dot.outputs['Value'])  # 点积结果+1
		links.new(math_mul1.inputs[0], math_add.outputs['Value'])  # 结果*0.5（范围缩至0-1）

		# 阴影处理链路
		links.new(rgb_to_bw.inputs['Color'], lamp_node.outputs['Shadow'])  # 阴影转灰度
		links.new(math_mul2.inputs[0], math_mul1.outputs['Value'])  # 灯光因子 * 阴影因子
		links.new(math_mul2.inputs[1], rgb_to_bw.outputs['Value'])

		# TOON渐变链路
		links.new(toon_color_ramp.inputs['Fac'], math_mul2.outputs['Value'])  # 因子控制渐变
		links.new(mix_rgb_toon.inputs['Color1'], toon_color_ramp.outputs['Color'])  # 渐变颜色
		links.new(mix_rgb_toon.inputs['Fac'], toon_color_ramp.outputs['Alpha'])  # 渐变透明度

		# 漫反射纹理链路
		links.new(diffuse_tex.inputs['Vector'], geo_uv.outputs['UV'])  # UV控制纹理坐标
		links.new(mix_rgb_diffuse.inputs['Color1'], mix_rgb_toon.outputs['Color'])  # TOON色
		links.new(mix_rgb_diffuse.inputs['Color2'], diffuse_tex.outputs['Color'])  # 漫反射纹理

		# 球面纹理链路
		links.new(sphere_tex.inputs['Vector'], geo_normal.outputs['Normal'])  # 法线控制球面纹理
		links.new(mix_rgb_sphere.inputs['Color1'], mix_rgb_diffuse.outputs['Color'])  # 漫反射+TOON
		links.new(mix_rgb_sphere.inputs['Color2'], sphere_tex.outputs['Color'])  # 球面纹理

		# 最终输出链路
		links.new(principled_node.inputs['Base Color'], mix_rgb_sphere.outputs['Color'])  # 最终颜色输入

		# 4. 读取材质纹理槽（适配Blender 2.8+ 纹理系统：材质使用节点，纹理通过图像纹理节点加载）
		# 注意：Blender 2.8+ 移除了 texture_slots，需通过旧版数据或手动关联纹理
		# 此处兼容旧版MMD材质的纹理索引（0=漫反射，1=TOON，2=球面）
		# 实际使用时建议直接在图像纹理节点中加载纹理，或通过自定义属性关联
		if hasattr(mat, 'mmd_texture_slots'):  # 若材质有自定义MMD纹理槽属性
			texture_slots = mat.mmd_texture_slots
			for idx, tex in enumerate(texture_slots):
				if not tex or not tex.texture:
					continue
				tex_obj = tex.texture
				if idx == 0 and tex_obj.type == 'IMAGE' and tex_obj.image:
					# 漫反射纹理
					diffuse_tex.image = tex_obj.image
				elif idx == 1 and tex_obj.type == 'IMAGE' and tex_obj.image:
					# TOON纹理：生成渐变
					toon_image_to_color_ramp(toon_color_ramp, tex_obj.image)
				elif idx == 2 and tex_obj.type == 'IMAGE' and tex_obj.image:
					# 球面纹理
					sphere_tex.image = tex_obj.image
					# 同步混合模式
					if hasattr(tex, 'blend_type'):
						mix_rgb_sphere.blend_type = tex.blend_type

		# 若无漫反射纹理，使用材质基础色
		if not diffuse_tex.image:
			# 移除原有Color2连接，连接材质基础色
			if mix_rgb_diffuse.inputs['Color2'].links:
				links.remove(mix_rgb_diffuse.inputs['Color2'].links[0])
			links.new(mix_rgb_diffuse.inputs['Color2'], principled_node.inputs['Base Color'])


class MMDToonTexturesToNodeEditorShader(bpy.types.Operator):
	"""Sets up nodes in Blender node editor for rendering toon textures"""
	bl_idname = "mmd_tools_helper.mmd_toon_render_node_editor"
	bl_label = "Create MMD Toon Material Nodes"
	bl_options = {'REGISTER', 'UNDO'}  # 支持撤销

	@classmethod
	def poll(cls, context):
		"""仅当活跃物体存在且为网格时可用"""
		return context.active_object is not None and context.active_object.type == 'MESH'

	def execute(self, context):
		try:
			# 获取MMD网格列表（依赖model模块的find_MMD_MeshesList方法）
			mesh_objects_list = model.find_MMD_MeshesList(context.active_object)
			if not mesh_objects_list:
				self.report({'ERROR'}, "Active object is not an MMD model.")
				return {'CANCELLED'}

			# 为每个网格物体创建节点
			for obj in mesh_objects_list:
				context.view_layer.objects.active = obj  # 切换活跃物体
				clear_material_nodes(context)  # 清空旧节点
				main(context)  # 创建新节点

			self.report({'INFO'}, "MMD Toon nodes created successfully!")
			return {'FINISHED'}
		except Exception as e:
			self.report({'ERROR'}, f"Failed to create nodes: {str(e)}")
			return {'CANCELLED'}


def register():
	"""注册面板和操作器"""
	bpy.utils.register_class(MMDToonTexturesToNodeEditorShader)
	bpy.utils.register_class(MMDToonTexturesToNodeEditorShaderPanel)


def unregister():
	"""注销面板和操作器"""
	bpy.utils.unregister_class(MMDToonTexturesToNodeEditorShader)
	bpy.utils.unregister_class(MMDToonTexturesToNodeEditorShaderPanel)


if __name__ == "__main__":
	register()