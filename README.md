# COMPP | Mattia Metry
Official repo of my compp module project. It requires [this hugging-face space](https://huggingface.co/spaces/hslu-di/PIFu-Clothed-Human-Digitization) to be up and running!
## Installation Blender Add-on

1. Download the **humanImageTo3D.py** from this repo.
2. In Blender, go to **Edit → Preferences → Add-ons → Install**
3. Select the **humanImageTo3D.py** file you previously downloaded.
4. Enable the add-on by checking its checkbox

 You should now see the **Create human AI** tab on the right hand side of the 3D view port, if not, press **N** to see the side-bar it.

## Usage

You can now search your machine for any **.png** or **.jpeg** files. Please note that the AI was trained for images of clothed humans from the front!

Once you have chosen your image, press the **Generate** button. This will block Blender until the 3D model is done and imported. This may take up to 3 minutes.

After the processing is done, you will have a 3D model of your image inside of Blender.

## Process

### Ideation
My fisrt idea was to find some sort of AI to create audio. I didn't find any good AI I wanted to use. But then, randomly while being on reddit, I stumbled upon [this](https://www.reddit.com/r/blender/comments/11jedrn/using_pifuhd_ai_to_generate_a_3d_model_from_a/?utm_source=share&utm_medium=ios_app&utm_name=iossmf) post. This got me really intersted in AI systems that can create 3D models. So after reading the research paper of the PIFu model, I installed it locally on my PC. But to get it all up and running, it took me quiet some time and fixing some bugs etc. But once it was up and running, I really liked the performance and the output of this AI system.

So I got the idea to maybe take this AI, but make it much easier to use. I then found a [hugging-face space](https://huggingface.co/spaces/radames/PIFu-Clothed-Human-Digitization) that was running this excat model. Here, you can simply upload an image, and then download the 3D model. This already was much more user friendly. But I wanted to make it even more simple. So I decided to create a Blender-Addon, so you can use the AI without ever leaving the Blender software.

### AI
As mentioned before, getting the AI to run on the local machine can be tricky, so its not really suitable for a Bledner Add-on. This is why I needed some sort of API now. So, I duplicated the hugging-face space. Then I tried to enable the API, but it didn't seem to work. To my surprise, there wasn't much helpful documentation on why this didn't work. i then by accident saw on another space that someone once made a commit called `enable API`. There, the person also updated the gradio-version. So I did the same, and the API became available!

### Blender Addon
To create a Blender Add-on, you can open the **scripting** window. From there, you can create a new script. Then, to have some sort of grounds to base your add-on on, you can go to **Templates** and then open any of those examples. (I used the **addon_add_object.py**) Here, we can see the main structre of a Belder Add-on.
The first section contains the infos of your Add-on. Those get shown when the users install the add-on in the preferences-window.

```python
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
```
After this, you have to declare all the imports needed.
```python
import bpy
import requests
import json
import os
import base64
```

Then, you can define any needed functions. I needed to define 2 functions. The first one is used to downlaod the 3D object file and save it to a temporary folder.
```python
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
```
The second function removes the camera of the imported 3D object. This was only needed because the API returns a GLB file which not only inclued the 3D object, but also a camera.
```python
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
```
Now, we have to decale an operation-class. This is used by Blender to declare any functionallity. (In my case, this is used to define the behaviour of a button-press)
It needs certain class-variables like the `bl_idname` which is later used to refer to this operator. The most important part of this class will be the `execute` function. This contains all the code that gets executed once the operation is called. (In this case, once the button will be pressed)
The function reads in the image, converts it to Base64, sends it to the API, then downloads the 3D object, imports it, and finally, removes the temporary files from the system to not create any waste.
```python
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
```
The second class that is needed will define how the UI looks like and what elements this contains. I added 2 lines of text, then one text input field for the image path, and lastly the button to execute. (Note how in the button, the operations class gets referenced via its `bl_idname`)
```python
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
```

The final part of the add-on script is fairly standard again. It just registers and unregisters all the classes.
```python
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
```