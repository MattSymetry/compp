bl_info = {
    "name": "HuggingFaceAPI - Human",
    "author": "Mattia Metry",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh > New Object",
    "description": "Adds a new Mesh Object",
    "warning": "",
    "doc_url": "",
    "category": "Add Human ",
}

import bpy
import requests
import json
import os
import base64

def download(url: str, dest_folder: str):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)  # create folder if it does not exist

    filename = url.split('/')[-1].replace(" ", "_")  # be careful with file names
    file_path = os.path.join(dest_folder, filename)

    r = requests.get(url, stream=True)
    if r.ok:
        print("saving to", os.path.abspath(file_path))
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 8):
                if chunk:
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
    else:  # HTTP status code 4XX/5XX
        print("Download failed: status code {}\n{}".format(r.status_code, r.text))
        
def remove_latest_camera():
    # Get all the cameras in the scene
    cameras = [obj for obj in bpy.context.scene.objects if obj.type == 'CAMERA']

    # If there are no cameras, return
    if not cameras:
        return

    # Get the latest added camera by sorting them based on their creation time
    latest_camera = sorted(cameras, key=lambda obj: obj.name)[-1]

    # Remove the camera
    bpy.data.objects.remove(latest_camera, do_unlink=True)

class AddImagePlaneOperator(bpy.types.Operator):
    bl_idname = "object.add_image_plane"
    bl_label = "Create 3D model"
    bl_description = "Uploads the image to the AI, generates the 3D model and imports it."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Load the image texture
        img = bpy.data.images.load(context.scene.my_image_path)
        ext     = context.scene.my_image_path.split('.')[-1]
        
        if ext == "png" or ext == "jpg":
        
            binary_fc       = open(context.scene.my_image_path, 'rb').read()  # fc aka file_content
            base64_utf8_str = base64.b64encode(binary_fc).decode('utf-8')

            
            dataurl = f'data:image/{ext};base64,{base64_utf8_str}'
            
            response = requests.post("https://hslu-di-pifu-clothed-human-digitization.hf.space/run/predict", json={
                "data": [
                    dataurl,
                ]
            }).json()

            data = response["data"]

            json_object = data
            urlPre = "https://hslu-di-pifu-clothed-human-digitization.hf.space/file="
            urlSuf = json_object[0]["name"]
            
            url = urlPre + urlSuf

            download(url, "tmp")
            
            filename = url.split('/')[-1].replace(" ", "_")
            file_path = os.path.join("tmp", filename)
            
            bpy.ops.import_scene.gltf(filepath=file_path, files=[{"name":filename, "name":filename}], loglevel=50)
            
            remove_latest_camera()
            
            os.remove(file_path)
        else:
            message = "Please only use .png or .jpg files!"
            self.report({'ERROR'}, message)

        return {'FINISHED'}

class AddImagePlanePanel(bpy.types.Panel):
    bl_idname = "OBJECT_PT_add_image_plane_panel"
    bl_label = "Image to human 3D model"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Create Human AI"

    def draw(self, context):

        layout = self.layout
        scene = context.scene
        
        row = layout.row()
        row.label(text="Only use .png or .jpg image-files!")
        
        row = layout.row()
        row.label(text="This process might take up to 3 minutes. During this time, Blender won't respond!")
        
        row = layout.row()
        row.prop(scene, "my_image_path", text="Image Path")

        row = layout.row()
        row.operator("object.add_image_plane", text="Create Model")

def register():
    bpy.utils.register_class(AddImagePlaneOperator)
    bpy.utils.register_class(AddImagePlanePanel)
    bpy.types.Scene.my_image_path = bpy.props.StringProperty(
        name="Image Path",
        subtype="FILE_PATH"
    )

def unregister():
    bpy.utils.unregister_class(AddImagePlaneOperator)
    bpy.utils.unregister_class(AddImagePlanePanel)
    del bpy.types.Scene.my_image_path

if __name__ == "__main__":
    register()