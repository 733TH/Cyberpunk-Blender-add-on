import bpy
import os
from ..main.common import *

class MetalBaseUI:
    def __init__(self, BasePath,image_format, ProjPath):
        self.BasePath = BasePath
        self.ProjPath = ProjPath
        self.image_format = image_format

    def create(self,Data,Mat):
        CurMat = Mat.node_tree
        pBSDF=CurMat.nodes['Principled BSDF']
        sockets=bsdf_socket_names()
        pBSDF.inputs[sockets['Specular']].default_value = 0
        vers=bpy.app.version

        if "FixForVerticalSlide" in Data:
            fixForVerticalSlide = CreateShaderNodeValue(CurMat,Data["FixForVerticalSlide"],-2000, 450,
                                                        "FixForVerticalSlide") 
            
        if "RenderTextureScale" in Data:
            renderTextureScale_x = CreateShaderNodeValue(CurMat,Data["RenderTextureScale"]["X"],-2000, 400,
                                                        "RenderTextureScale.x") 
            renderTextureScale_y = CreateShaderNodeValue(CurMat,Data["RenderTextureScale"]["Y"],-2000, 350,
                                                        "RenderTextureScale.y") 
            renderTextureScale_z = CreateShaderNodeValue(CurMat,Data["RenderTextureScale"]["Z"],-2000, 300,
                                                        "RenderTextureScale.z") 
            renderTextureScale_w = CreateShaderNodeValue(CurMat,Data["RenderTextureScale"]["W"],-2000, 250,
                                                        "RenderTextureScale.w") 
            
        if "TexturePartUV" in Data:
            texturePartUV_x = CreateShaderNodeValue(CurMat,Data["TexturePartUV"]["X"],-2000, 200,
                                                        "TexturePartUV.x") 
            texturePartUV_y = CreateShaderNodeValue(CurMat,Data["TexturePartUV"]["Y"],-2000, 150,
                                                        "TexturePartUV.y") 
            texturePartUV_z = CreateShaderNodeValue(CurMat,Data["TexturePartUV"]["Z"],-2000, 100,
                                                        "TexturePartUV.z") 
            texturePartUV_w = CreateShaderNodeValue(CurMat,Data["TexturePartUV"]["W"],-2000, 50,
                                                        "TexturePartUV.w") 
            
        # tangent, geometry node, uv
        tangent = create_node(CurMat.nodes, "ShaderNodeTangent", (-2000,650))
        tangent.direction_type = "UV_MAP"
        geometry = create_node(CurMat.nodes, "ShaderNodeNewGeometry", (-2000,575))
        UVMap = create_node(CurMat.nodes,"ShaderNodeUVMap",(-2000, 500))

        # binormal
        vecCross = create_node(CurMat.nodes,"ShaderNodeVectorMath",(-1750,575), operation="CROSS_PRODUCT")
        CurMat.links.new(geometry.outputs[1], vecCross.inputs[0])
        CurMat.links.new(tangent.outputs[0], vecCross.inputs[1])

        # leftRightDot
        vecDot = create_node(CurMat.nodes,"ShaderNodeVectorMath",(-1500,600), operation= "DOT_PRODUCT")
        CurMat.links.new(geometry.outputs[4], vecDot.inputs[0])
        CurMat.links.new(tangent.outputs[0], vecDot.inputs[1])

        # topDownDot
        vecDot2 = create_node(CurMat.nodes,"ShaderNodeVectorMath",(-1500,550), operation= "DOT_PRODUCT")
        CurMat.links.new(geometry.outputs[4], vecDot2.inputs[0])
        CurMat.links.new(vecCross.outputs[0], vecDot2.inputs[1])

        # modUV
        mul = create_node(CurMat.nodes,"ShaderNodeMath",(-1350,550), operation= "MULTIPLY")
        combine = create_node(CurMat.nodes,"ShaderNodeCombineXYZ",(-1200,575))
        CurMat.links.new(vecDot2.outputs["Value"], mul.inputs[0])
        CurMat.links.new(fixForVerticalSlide.outputs[0], mul.inputs[1])
        CurMat.links.new(vecDot.outputs["Value"], combine.inputs[0])
        CurMat.links.new(mul.outputs[0], combine.inputs[1])

        # remoteImageScale RenderTextureScale.xy / RenderTextureScale.zw;
        combine2 = create_node(CurMat.nodes,"ShaderNodeCombineXYZ",(-1500,450))
        combine3 = create_node(CurMat.nodes,"ShaderNodeCombineXYZ",(-1500,400))
        vecDiv = create_node(CurMat.nodes,"ShaderNodeVectorMath",(-1350,425), operation= "DIVIDE")
        CurMat.links.new(renderTextureScale_x.outputs[0], combine2.inputs[0])
        CurMat.links.new(renderTextureScale_y.outputs[0], combine2.inputs[1])
        CurMat.links.new(renderTextureScale_z.outputs[0], combine3.inputs[0])
        CurMat.links.new(renderTextureScale_w.outputs[0], combine3.inputs[1])
        CurMat.links.new(combine2.outputs[0], vecDiv.inputs[0])
        CurMat.links.new(combine3.outputs[0], vecDiv.inputs[1])

        # #float2 textureUV = float2(data.UV.x,1-data.UV.y);
        # separate = create_node(CurMat.nodes,"ShaderNodeSeparateXYZ",(-1500,500))
        # sub = create_node(CurMat.nodes,"ShaderNodeMath",(-1350,500), operation= "SUBTRACT")
        # sub.inputs[0].default_value = 1
        # combine4 = create_node(CurMat.nodes,"ShaderNodeCombineXYZ",(-1200,500))
        # CurMat.links.new(UVMap.outputs[0], separate.inputs[0])
        # CurMat.links.new(separate.outputs[1], sub.inputs[1])
        # CurMat.links.new(separate.outputs[0], combine4.inputs[0])
        # CurMat.links.new(sub.outputs[0], combine4.inputs[1])
        
        # float2 partSize = float2(texturePartUV.z - texturePartUV.x, texturePartUV.w - texturePartUV.y );
        sub2 = create_node(CurMat.nodes,"ShaderNodeMath",(-1500,350), operation= "SUBTRACT")
        sub3 = create_node(CurMat.nodes,"ShaderNodeMath",(-1500,300), operation= "SUBTRACT")
        combine5 = create_node(CurMat.nodes,"ShaderNodeCombineXYZ",(-1350,325))
        CurMat.links.new(texturePartUV_z.outputs[0], sub2.inputs[0])
        CurMat.links.new(texturePartUV_x.outputs[0], sub2.inputs[1])
        CurMat.links.new(texturePartUV_w.outputs[0], sub3.inputs[0])
        CurMat.links.new(texturePartUV_y.outputs[0], sub3.inputs[1])
        CurMat.links.new(sub2.outputs[0], combine5.inputs[0])
        CurMat.links.new(sub3.outputs[0], combine5.inputs[1])
        
        # textureUV = textureUV * partSize + texturePartUV.xy;
        vecMul2 = create_node(CurMat.nodes,"ShaderNodeVectorMath",(-750,-125), operation= "MULTIPLY")
        combine6 = create_node(CurMat.nodes,"ShaderNodeCombineXYZ",(-750,-175))
        vecAdd = create_node(CurMat.nodes,"ShaderNodeVectorMath",(-600,-125))
        CurMat.links.new(UVMap.outputs[0], vecMul2.inputs[0])
        CurMat.links.new(combine5.outputs[0], vecMul2.inputs[1])
        CurMat.links.new(texturePartUV_x.outputs[0], combine6.inputs[0])
        CurMat.links.new(texturePartUV_y.outputs[0], combine6.inputs[1])
        CurMat.links.new(vecMul2.outputs[0], vecAdd.inputs[0])
        CurMat.links.new(combine6.outputs[0], vecAdd.inputs[1])
