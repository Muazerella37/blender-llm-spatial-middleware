import bpy
import urllib.request
import urllib.parse
import json
from mathutils import Vector

# =====================================================================
# BÜYÜK/KÜÇÜK HARF DUYARLILIĞINI ÇÖZEN ARAMA FONKSİYONU
# =====================================================================
def get_object_case_insensitive(name):
    if not name or name.lower() == "none": 
        return None
    for obj in bpy.context.scene.objects:
        if obj.name.lower() == name.lower():
            return obj
    return None

# =====================================================================
# 1. MATEMATİK VE YARATILIŞ MOTORLARI (ARAÇLAR)
# =====================================================================

# ARAÇ 1: OBJE YARATMA
def create_object(obj_type, name):
    obj_type = obj_type.lower().strip()
    
    # Seçili objenin seçimini kaldır (Yeni objenin karışmaması için)
    bpy.ops.object.select_all(action='DESELECT')
    
    if obj_type == "cube":
        bpy.ops.mesh.primitive_cube_add()
    elif obj_type == "cone":
        bpy.ops.mesh.primitive_cone_add()
    elif obj_type == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add()
    elif obj_type == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add()
    elif obj_type == "plane":
        bpy.ops.mesh.primitive_plane_add()
    else:
        print(f"Hata: Desteklenmeyen obje türü '{obj_type}'.")
        return

    # Yaratılan aktif objeyi bul ve ismini değiştir
    obj = bpy.context.active_object
    if obj:
        obj.name = name
        print(f"İşlem Tamam: Sahnede '{name}' adında bir {obj_type} yaratıldı.")


# ARAÇ 2: OBJE HAREKET ETTİRME
def move_a_relative_to_b(obj_name, target_obj_name, direction, distance):
    if not hasattr(bpy.context, "space_data") or bpy.context.space_data.type != 'VIEW_3D':
        print("Hata: 3D Viewport ekranında değilsiniz.")
        return

    region_3d = bpy.context.space_data.region_3d
    view_matrix_inv = region_3d.view_matrix.inverted()
    rotation_matrix = view_matrix_inv.to_3x3()

    direction = direction.lower().strip()
    if direction == "right": view_vec = Vector((1.0, 0.0, 0.0))
    elif direction == "left": view_vec = Vector((-1.0, 0.0, 0.0))
    elif direction == "up": view_vec = Vector((0.0, 1.0, 0.0))
    elif direction == "down": view_vec = Vector((0.0, -1.0, 0.0))
    elif direction == "front": view_vec = Vector((0.0, 0.0, -1.0))
    elif direction == "behind": view_vec = Vector((0.0, 0.0, 1.0))
    else: return

    world_vec = rotation_matrix @ view_vec
    world_vec.normalize()

    obj = get_object_case_insensitive(obj_name)
    if not obj:
        print(f"Hata: '{obj_name}' sahnede bulunamadı.")
        return

    if target_obj_name and target_obj_name.lower() != "none":
        target_obj = get_object_case_insensitive(target_obj_name)
        if target_obj:
            obj.location = target_obj.location.copy()
        else:
            print(f"Hata: Referans obje '{target_obj_name}' bulunamadı.")
            return

    obj.location += world_vec * distance
    print(f"İşlem Tamam: {obj.name}, {direction} yönüne {distance} birim taşındı.")


# =====================================================================
# 2. YAPAY ZEKA İLETİŞİMİ VE SIKI KISITLAMALAR
# =====================================================================
def ask_deepseek_to_code(user_prompt):
    API_URL = "http://localhost:11434/api/generate" 
    
    system_prompt = """You are an AI assistant that controls Blender.
You have EXACTLY TWO tools available:

Tool 1: create_object(obj_type, name)
- Use this to create a new object.
- Valid obj_types are ONLY: "cube", "cone", "sphere", "cylinder", "plane".

Tool 2: move_a_relative_to_b(obj_name, target_obj_name, direction, distance)
- Use this to move an object.
- If there is NO second object mentioned, write "None" for target_obj_name.
- Valid directions are ONLY: "Right", "Left", "Up", "Down", "Front", "Behind".

Rules:
- DO NOT write any other python code.
- Output ONLY the correct function call on a single line.

Example 1: Create a sphere named ball
Output 1: create_object("sphere", "ball")

Example 2: Move the ball 3 meters right of the cube
Output 2: move_a_relative_to_b("ball", "cube", "Right", 3.0)"""

    data = {
        "model": "deepseek-coder:6.7b", 
        "prompt": f"{system_prompt}\n\nUser: {user_prompt}\nOutput:",
        "stream": False
    }

    try:
        req = urllib.request.Request(API_URL, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get("response", "").strip()
    except Exception as e:
        print(f"Bağlantı Hatası: {e}")
        return None

# =====================================================================
# 3. BLENDER ARAYÜZÜ (UI)
# =====================================================================
class OBJECT_OT_GenerateCode(bpy.types.Operator):
    bl_idname = "object.generate_code"
    bl_label = "Generate & Execute Code"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        user_prompt = context.scene.llm_prompt
        if not user_prompt:
            return {'CANCELLED'}

        generated_code = ask_deepseek_to_code(user_prompt)
        if not generated_code:
            return {'CANCELLED'}
            
        generated_code = generated_code.replace("```python", "").replace("```", "").strip()
        print(f"\nYapay Zeka Çıktısı: {generated_code}")
        
        exec_globals = {
            "create_object": create_object,
            "move_a_relative_to_b": move_a_relative_to_b,
            "bpy": bpy
        }
        
        try:
            exec(generated_code, exec_globals)
        except Exception as e:
            print(f"Çalıştırma Hatası: {e}")
            
        return {'FINISHED'}

class VIEW3D_PT_BlenderLLM(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LLM Agent'
    bl_label = "Relative Spatial AI"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "llm_prompt", text="")
        layout.operator("object.generate_code", text="Execute Command", icon='PLAY')

def register():
    bpy.utils.register_class(OBJECT_OT_GenerateCode)
    bpy.utils.register_class(VIEW3D_PT_BlenderLLM)
    bpy.types.Scene.llm_prompt = bpy.props.StringProperty(name="Prompt", default="")

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_GenerateCode)
    bpy.utils.unregister_class(VIEW3D_PT_BlenderLLM)
    del bpy.types.Scene.llm_prompt

if __name__ == "__main__":
    register()