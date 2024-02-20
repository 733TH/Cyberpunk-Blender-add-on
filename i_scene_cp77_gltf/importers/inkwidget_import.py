import json
import os
import bpy
import blf
import gpu
import glob
from collections import defaultdict
from mathutils import Matrix
from ..main.common import *




def find_font(filepath, fontfpath, fontstyle):
    before,mid,after=filepath.partition('source\\raw\\')
    fontfpath = before+mid+fontfpath+".json"

    with open(fontfpath,"r") as f:
        j=json.load(f)

    l = j["Data"]["RootChunk"]["fontStyles"]

    for id,v in enumerate(l):
        if fontstyle in l[id]["styleName"]["$value"]:
            path = before+mid+l[id]["font"]["DepotPath"]["$value"][:-4]+".ttf"

    return path

def draw_text(font_path, size, text, x, y, color):
    font_id = blf.load(font_path)
    blf.enable(font_id, blf.WORD_WRAP)
    blf.position(font_id, x,y  ,1)
    blf.word_wrap(font_id, 800)
    blf.size(font_id, size)
    blf.color(font_id, color["Red"],color["Green"],color["Blue"],color["Alpha"])
    blf.draw(font_id, text)

def get_pos(anchor, margin, width, height):
    
    if "TopLeft" in anchor:
        x = -(width/2) + margin['left']
        y = (height/2) - margin['top']

    elif "Centered" in anchor:
        x = margin['left']
        y = margin['top']

    elif "TopRight" in anchor:
        x = (width/2) - margin['right']
        y = (height/2) - margin['top']

    elif "BottomLeft" in anchor:
        x = -(width/2) + margin['left']
        y = -(height/2) + margin['bottom']
    
    return x,y

                
def recursive_parser(entry: dict, data_dict: dict) -> dict:
    ''' data_dict = {inkTextWidget: [name, fontPath, fontStyle fontSize, 
                                     text, anchor, margin, visible, tintColor],
                    inkImageWidget: [name],
                    inkCanvasWidget: [name, size_x, size_y, margin]} '''
    if isinstance(entry, dict):
        for key, val in entry.items():
            if isinstance(val, dict):
                if "$type" in val and val["$type"] == "inkTextWidget":
                    data_dict["inkTextWidget"].append([val["name"]["$value"]])
                    id=len(data_dict["inkTextWidget"])-1
                    data_dict["inkTextWidget"][id].append(val["fontFamily"]["DepotPath"]["$value"])
                    data_dict["inkTextWidget"][id].append(val["fontStyle"]["$value"])
                    data_dict["inkTextWidget"][id].append(val["fontSize"])
                    data_dict["inkTextWidget"][id].append(val["text"])
                    data_dict["inkTextWidget"][id].append(val["layout"]["anchor"])
                    data_dict["inkTextWidget"][id].append(val["layout"]["margin"])
                    data_dict["inkTextWidget"][id].append(val["visible"])
                    data_dict["inkTextWidget"][id].append(val["tintColor"])
                    
                elif "$type" in val and val["$type"] == "inkImageWidget":
                    data_dict["inkImageWidget"].append([val["name"]["$value"]])

                elif "$type" in val and val["$type"] == "inkCanvasWidget":
                    data_dict["inkCanvasWidget"].append([val["name"]["$value"]])
                    id=len(data_dict["inkCanvasWidget"])-1
                    data_dict["inkCanvasWidget"][id].append(val["size"]["X"])
                    data_dict["inkCanvasWidget"][id].append(val["size"]["Y"])
                    data_dict["inkCanvasWidget"][id].append(val["layout"]["margin"])
            recursive_parser(entry[key], data_dict)
            # if isinstance(val, (str,int,float)):
            #     print(key, val)
    elif isinstance(entry, list):
        for i, val in enumerate(entry):
            # if isinstance(val, (str,int,float)):
            #     print(i, val)
            recursive_parser(entry[i], data_dict)

def generate_inkwidget_texture(data, filepath):
    for key,val in data.items():
        for v in val:
            if (key == "inkCanvasWidget"
                and data["name"][0] in v[0]):
                    width = v[1]
                    height = v[2]
    offscreen = gpu.types.GPUOffScreen(width, height)
    with offscreen.bind():
        fb = gpu.state.active_framebuffer_get()
        fb.clear(color=(0.0, 0.0, 0.0, 0.0))
        with gpu.matrix.push_pop():
            projection_matrix = Matrix.Diagonal( (2/width, 2/height, .0) )
            projection_matrix = Matrix.Translation( (.0,.0,1) ) @ projection_matrix.to_4x4()
            gpu.matrix.load_projection_matrix(projection_matrix)

            #print(data)
            for key,val in data.items():
                for v in val:
                    #print(v[0])
                    if key == "inkTextWidget" and v[7]:
                        x, y = get_pos(v[5],v[6],width,height)
                        draw_text(
                            find_font(filepath, v[1], v[2]),
                            v[3], v[4], 
                            x, y, v[8]
                            )



        buffer = fb.read_color(0, 0, width, height, 4, 0, 'UBYTE')

    offscreen.free()

    if data["name"][0] not in bpy.data.images:
        bpy.data.images.new(data["name"][0], width, height)
    image = bpy.data.images[data["name"][0]]
    image.scale(width, height)

    buffer.dimensions = width * height * 4
    image.pixels = [v / 255 for v in buffer]
    return image


def import_inkwidget(filepath):

    ink_name=os.path.basename(filepath)[:-15]
    print('Importing inkwidget', ink_name)
    with open(filepath,'r') as f: 
        j=json.load(f)
    l = j["Data"]["RootChunk"]["libraryItems"][0]["packageData"]
    parsed_data = defaultdict(list)
    name = os.path.basename(j["Header"]["ArchiveFileName"])[:-10]
    parsed_data["name"].append(name)
    for entry in l:
        recursive_parser(l[entry], parsed_data)
    
    data = dict(parsed_data)
    image = generate_inkwidget_texture(data, filepath)
    ob = bpy.context.active_object
    mat = ob.active_material.node_tree
    imgnode = create_node(mat.nodes,"ShaderNodeTexImage",(-1500,0))
    imgnode.image = image




if __name__ == "__main__":
    path = 'E:\\WolvenKit\\materials\\source\\raw'
    ink_name = 'radio_ui.inkwidget'
    jsonpath = glob.glob(path+"\**\*.inkwidget.json", recursive = True)

    if len(jsonpath)==0:
        print('No jsons found')
    

    for i,e in enumerate(jsonpath):
        if os.path.basename(e)== ink_name+'.json' :
            filepath=e
    import_inkwidget(filepath)
