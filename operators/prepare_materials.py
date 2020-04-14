import bpy

from .. import utils

class PrepareMaterials(bpy.types.Operator):
    bl_idname = "tivoli.prepare_materials"
    bl_label = "Tivoli: Prepare Materials"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        objects = scene.objects

        MATERIAL_PREFIX = "Tivoli_Lightmap"
        # RANDOM_STRING_LENGTH = 8

        def serializeName(obj, material):
            return (
                MATERIAL_PREFIX + "_" +
                obj.name + "_" +
                material.name
            )

        def deserializeName(obj, material):
            return material.name[
                len(MATERIAL_PREFIX + "_" + obj.name + "_")
                :
                99999
            ]

        materials_in_use = []
        images_in_use = []

        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        for obj in objects:
            if obj.visible_get() == False or obj.type != "MESH":
                continue

            print("Preparing materials for: " + obj.name)

            material_slots = obj.material_slots.values()

            # for each material slot
            for index in range(len(material_slots)):
                material_slot = material_slots[index]
                material = material_slot.material

                if material == None:
                    material = utils.findOrCreateDefaultMaterial()

                #  undo tivoli material
                if material.name.startswith(MATERIAL_PREFIX):
                    old_material_name = deserializeName(obj, material)
                    old_material = utils.findMaterial(old_material_name)

                    if old_material != None:
                        material = old_material
                    else:
                        # cant find old material so use default
                        material = utils.findOrCreateDefaultMaterial()

                # find or clone new material and replace
                new_material_name = serializeName(obj, material)
                new_material = utils.findMaterialOrCloneWithName(
                    new_material_name,
                    material
                )

                obj.material_slots[index].material = new_material
                materials_in_use.append(new_material)

            # if no material slots, use default material
            if len(material_slots) == 0:
                material = utils.findOrCreateDefaultMaterial()

                new_material_name = serializeName(obj, material)
                new_material = utils.findMaterialOrCloneWithName(
                    new_material_name,
                    material
                )

                obj.data.materials.append(new_material)
                materials_in_use.append(new_material)

            # add image for baking to the first material 
            material = obj.material_slots[0].material
            material.use_nodes = True
            nodes = material.node_tree.nodes

            for node in nodes:
                if node.name == MATERIAL_PREFIX:
                    nodes.remove(node)

            node = nodes.new("ShaderNodeTexImage")
            node.name = MATERIAL_PREFIX
            # node.show_preview = True
            # node.mute = True

            new_image_name = MATERIAL_PREFIX + "_" + obj.name

            for image in bpy.data.images:
                if image.name == new_image_name:
                    bpy.data.images.remove(image)

            new_image = bpy.data.images.new(
                name=MATERIAL_PREFIX + "_" + obj.name, 
                width=1024,
                height=1024,
                alpha=False,
                float_buffer=True, # TODO: neccessary?
                # is_data=True
            )
            new_image.file_format = "OPEN_EXR"

            node.image = new_image
            images_in_use.append(new_image)

            # just for testing
            # bsdf = nodes["Principled BSDF"]
            # material.node_tree.links.new(
            #     node.outputs["Color"],
            #     bsdf.inputs["Emission"]
            # )

        utils.deselectAll() # not being used
        
        # remove all unused lightmap materials and textures   
        for material in bpy.data.materials:
            if material.name.startswith(MATERIAL_PREFIX) == False:
                continue
            if material not in materials_in_use:
                print("Deleting unused material: " + material.name)
                bpy.data.materials.remove(material)

        for image in bpy.data.images:
            if image.name.startswith(MATERIAL_PREFIX) == False:
                continue
            if image not in images_in_use:
                print("Deleting unused image: " + image.name)
                bpy.data.images.remove(image)

                
        return {"FINISHED"}