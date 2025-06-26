import asyncio
import aiohttp
import websockets
import json
import os

COMFYUI_WS_URL = "ws://127.0.0.1:8188/ws"
COMFYUI_HTTP_URL = "http://127.0.0.1:8188"
async def upload_image(filepath, session):
    url = f"{COMFYUI_HTTP_URL}/upload/image"
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        data = aiohttp.FormData()
        data.add_field('image', f, filename=filename, content_type='application/octet-stream')
        async with session.post(url, data=data) as resp:
            res = await resp.json()
            print(f"[UPLOAD] {filename} -> {res['name']}")
            return res["name"]

async def send_upload_image(person_path, cloth_path):
    async with aiohttp.ClientSession() as session:
        # 1. Upload images
        person_uploaded = await upload_image(person_path, session)
        cloth_uploaded = await upload_image(cloth_path, session)

        return person_uploaded, cloth_uploaded


async def send_workflow_to_comfyui_test(workflow):
    async with aiohttp.ClientSession() as session:
        # 1. Upload images
        # person_uploaded = await upload_image(person_path, session)
        # cloth_uploaded = await upload_image(cloth_path, session)
        # workflow["10"]["inputs"]["image"] = person_uploaded
        # workflow["11"]["inputs"]["image"] = cloth_uploaded

        # 2. Debug: логування workflow, який буде надіслано
        print("[DEBUG] Final workflow JSON to send:")
        print('person_path:', workflow["10"]["inputs"]["image"])
        print('cloth_path:', workflow["11"]["inputs"]["image"])
        # print(json.dumps(workflow, indent=2))  # красиво форматований JSON
        prompt_id = None
        done = False
        # 3. Надсилання prompt
        prompt_payload = {"prompt": workflow}
        async with session.post(f"{COMFYUI_HTTP_URL}/prompt", json=prompt_payload) as resp:
                resp_json = await resp.json()
                prompt_id = resp_json.get("prompt_id")
                print("Prompt sent, prompt_id:", prompt_id)
   

        while done is False:
            # wait for 10 seconds before checking history
            await asyncio.sleep(5)
            async with session.get(f"{COMFYUI_HTTP_URL}/api/history?max_items=64") as resp:
                resp_json_1 = await resp.json()
                print("History response:", len(resp_json_1.keys()), "items")
                if resp_json_1.get(prompt_id) is not None:
                    status = resp_json_1[prompt_id]['status']['completed']
                    print("status:", status)
                    if (status is True):
                        # print("Prompt completed in history:", resp_json_1[prompt_id])
                        image_name = resp_json_1[prompt_id]['outputs']['18']['images'][0]['filename']
                        type = resp_json_1[prompt_id]['outputs']['18']['images'][0]['type']
                        subfolder = resp_json_1[prompt_id]['outputs']['18']['images'][0]['subfolder']
                        print("Image name from history:", image_name)
                        img_url = f"{COMFYUI_HTTP_URL}/view?filename={image_name}&type={type}&subfolder={subfolder}"
                        async with session.get(img_url) as img_resp:
                            return await img_resp.read()
                        done = True
                    else:
                        done = True
                        print("Prompt not completed yet, checking again...")
                        res = await send_workflow_to_comfyui_test(workflow)
                        return res
        
            

        # # 4. WebSocket – очікування результатів
        # async with websockets.connect(COMFYUI_WS_URL, max_size=100*1024*1024) as ws:
        #     while True:
        #         msg = await ws.recv()
        #         try:
        #             data = json.loads(msg)
        #             print(f"[WS] Received message: {data}")
        #         except Exception:
        #             continue
        #         if data.get("type") == "executed" and data.get("prompt_id") == prompt_id:
        #             outputs = data.get("outputs", {})
        #             for node_id, node_data in outputs.items():
        #                 if node_data.get("class_type") == "PreviewImage":
        #                     images = node_data.get("images", [])
        #                     if images:
        #                         image_name = images[0]
        #                         img_url = f"{COMFYUI_HTTP_URL}/view?filename={image_name}"
        #                         async with session.get(img_url) as img_resp:
        #                             return await img_resp.read()


async def send_workflow_to_comfyui(workflow, person_path, cloth_path, person_filename, cloth_filename):
    async with aiohttp.ClientSession() as session:
        # 1. Upload images
        # person_uploaded = await upload_image(person_path, session)
        # cloth_uploaded = await upload_image(cloth_path, session)
        # workflow["10"]["inputs"]["image"] = person_uploaded
        # workflow["11"]["inputs"]["image"] = cloth_uploaded

        # 2. Debug: логування workflow, який буде надіслано
        print("[DEBUG] Final workflow JSON to send:")
        print(json.dumps(workflow, indent=2))  # красиво форматований JSON

        # 3. Надсилання prompt
        prompt_payload = {"prompt": workflow}
        async with session.post(f"{COMFYUI_HTTP_URL}/prompt", json=prompt_payload) as resp:
            resp_json = await resp.json()
            prompt_id = resp_json.get("prompt_id")
            print("Prompt sent, prompt_id:", prompt_id)

        # 4. WebSocket – очікування результатів
        async with websockets.connect(COMFYUI_WS_URL, max_size=100*1024*1024) as ws:
            while True:
                msg = await ws.recv()
                try:
                    data = json.loads(msg)
                    print(f"[WS] Received message: {data}")
                except Exception:
                    continue
                if data.get("type") == "executed" and data.get("prompt_id") == prompt_id:
                    outputs = data.get("outputs", {})
                    for node_id, node_data in outputs.items():
                        if node_data.get("class_type") == "PreviewImage":
                            images = node_data.get("images", [])
                            if images:
                                image_name = images[0]
                                img_url = f"{COMFYUI_HTTP_URL}/view?filename={image_name}"
                                async with session.get(img_url) as img_resp:
                                    return await img_resp.read()

async def send_workflow_to_comfyui_retry(workflow, person_path, cloth_path, person_filename, cloth_filename):
    async with aiohttp.ClientSession() as session:
        # 1. Upload images
        person_uploaded = await upload_image(person_path, session)
        cloth_uploaded = await upload_image(cloth_path, session)
        workflow["10"]["inputs"]["image"] = person_uploaded
        workflow["11"]["inputs"]["image"] = cloth_uploaded

        # 2. Debug: логування workflow, який буде надіслано
        print("[DEBUG] Final workflow JSON to send:")
        print(json.dumps(workflow, indent=2))  # красиво форматований JSON

        # 3. Надсилання prompt
        prompt_payload = {"prompt": workflow}
        async with session.post(f"{COMFYUI_HTTP_URL}/prompt", json=prompt_payload) as resp:
            resp_json = await resp.json()
            prompt_id = resp_json.get("prompt_id")
            print("Prompt sent, prompt_id:", prompt_id)

        # 4. WebSocket – очікування результатів
        async with websockets.connect(COMFYUI_WS_URL, max_size=100*1024*1024) as ws:
            while True:
                msg = await ws.recv()
                try:
                    data = json.loads(msg)
                except Exception:
                    continue
                if data.get("type") == "executed" and data.get("prompt_id") == prompt_id:
                    outputs = data.get("outputs", {})
                    for node_id, node_data in outputs.items():
                        if node_data.get("class_type") == "PreviewImage":
                            images = node_data.get("images", [])
                            if images:
                                image_name = images[0]
                                img_url = f"{COMFYUI_HTTP_URL}/view?filename={image_name}"
                                async with session.get(img_url) as img_resp:
                                    return await img_resp.read()
                                
# async def send_workflow_to_comfyui_retry(workflow, person_uploaded, cloth_uploaded, mask_uploaded):
#     async with aiohttp.ClientSession() as session:
#         workflow["16"]["inputs"]["target_image"] = person_uploaded
#         workflow["16"]["inputs"]["refer_image"] = cloth_uploaded
#         workflow["16"]["inputs"]["mask_image"] = mask_uploaded

#         prompt_payload = {"prompt": workflow}
#         async with session.post(f"{COMFYUI_HTTP_URL}/prompt", json=prompt_payload) as resp:
#             resp_json = await resp.json()
#             prompt_id = resp_json.get("prompt_id")

#         async with websockets.connect(COMFYUI_WS_URL, max_size=100*1024*1024) as ws:
#             while True:
#                 msg = await ws.recv()
#                 try:
#                     data = json.loads(msg)
#                 except Exception:
#                     continue
#                 if data.get("type") == "executed" and data.get("prompt_id") == prompt_id:
#                     outputs = data.get("outputs", {})
#                     for node_id, node_data in outputs.items():
#                         if node_data.get("class_type") == "PreviewImage":
#                             images = node_data.get("images", [])
#                             if images:
#                                 image_name = images[0]
#                                 img_url = f"{COMFYUI_HTTP_URL}/view?filename={image_name}"
#                                 async with session.get(img_url) as img_resp:
#                                     return await img_resp.read()


# {"client_id":"e719497b6f7c4adbba1ccf9ae798c800","prompt":{"10":{"inputs":{"image":"Знімок екрана 2025-06-03 165847.png"},"class_type":"LoadImage","_meta":{"title":"Target Person"}},"11":{"inputs":{"image":"Знімок екрана 2025-06-03 165925.png"},"class_type":"LoadImage","_meta":{"title":"Reference Garment"}},"12":{"inputs":{"catvton_path":"zhengchong/CatVTON"},"class_type":"LoadAutoMasker","_meta":{"title":"Load AutoMask Generator"}},"13":{"inputs":{"cloth_type":"upper","pipe":["12",0],"target_image":["10",0]},"class_type":"AutoMasker","_meta":{"title":"Auto Mask Generation"}},"14":{"inputs":{"images":["13",1]},"class_type":"PreviewImage","_meta":{"title":"Masked Target"}},"15":{"inputs":{"images":["13",0]},"class_type":"PreviewImage","_meta":{"title":"Binary Mask"}},"16":{"inputs":{"seed":24,"steps":50,"cfg":2.5,"pipe":["17",0],"target_image":["10",0],"refer_image":["11",0],"mask_image":["13",0]},"class_type":"CatVTON","_meta":{"title":"TryOn by CatVTON"}},"17":{"inputs":{"sd15_inpaint_path":"runwayml/stable-diffusion-inpainting","catvton_path":"zhengchong/CatVTON","mixed_precision":"bf16"},"class_type":"LoadCatVTONPipeline","_meta":{"title":"Load CatVTON Pipeline"}},"18":{"inputs":{"images":["16",0]},"class_type":"PreviewImage","_meta":{"title":"Preview Image"}}},"extra_data":{"extra_pnginfo":{"workflow":{"id":"881f01a5-8662-43ea-8e6f-52f83b719e0c","revision":0,"last_node_id":23,"last_link_id":27,"nodes":[{"id":14,"type":"PreviewImage","pos":[1042.3883056640625,104.53547668457031],"size":[160.99398803710938,246],"flags":{},"order":7,"mode":0,"inputs":[{"name":"images","type":"IMAGE","link":17}],"outputs":[],"title":"Masked Target","properties":{"cnr_id":"comfy-core","ver":"0.3.39","Node name for S&R":"PreviewImage"},"widgets_values":[]},{"id":18,"type":"PreviewImage","pos":[885.5392456054688,501.701416015625],"size":[313.9939880371094,341.0123291015625],"flags":{},"order":8,"mode":0,"inputs":[{"name":"images","type":"IMAGE","link":27}],"outputs":[],"properties":{"cnr_id":"comfy-core","ver":"0.3.39","Node name for S&R":"PreviewImage"},"widgets_values":[]},{"id":15,"type":"PreviewImage","pos":[859.3865356445312,105.53547668457031],"size":[160.1082305908203,246],"flags":{},"order":5,"mode":0,"inputs":[{"name":"images","type":"IMAGE","link":18}],"outputs":[],"title":"Binary Mask","properties":{"cnr_id":"comfy-core","ver":"0.3.39","Node name for S&R":"PreviewImage"},"widgets_values":[]},{"id":17,"type":"LoadCatVTONPipeline","pos":[101,223],"size":[431.00823974609375,106],"flags":{},"order":0,"mode":0,"inputs":[],"outputs":[{"name":"pipe","type":"MODEL","slot_index":0,"links":[20]}],"properties":{"cnr_id":"comfyui-catvton","ver":"6ffd4a491c4cfb8923f4dece7844b68f5c392a72","Node name for S&R":"LoadCatVTONPipeline","aux_id":"pzc163/Comfyui-CatVTON"},"widgets_values":["runwayml/stable-diffusion-inpainting","zhengchong/CatVTON","bf16"]},{"id":13,"type":"AutoMasker","pos":[607.3880004882812,105.53547668457031],"size":[227.4981231689453,240.48341369628906],"flags":{},"order":4,"mode":0,"inputs":[{"name":"pipe","type":"MODEL","link":11},{"name":"target_image","type":"IMAGE","link":10}],"outputs":[{"name":"image","type":"IMAGE","slot_index":0,"links":[18,19]},{"name":"image_masked","type":"IMAGE","slot_index":1,"links":[17]}],"properties":{"cnr_id":"comfyui-catvton","ver":"6ffd4a491c4cfb8923f4dece7844b68f5c392a72","Node name for S&R":"AutoMasker","aux_id":"pzc163/Comfyui-CatVTON"},"widgets_values":["upper"]},{"id":16,"type":"CatVTON","pos":[605.5397338867188,503.701416015625],"size":[242.99398803710938,338.0123291015625],"flags":{},"order":6,"mode":0,"inputs":[{"name":"pipe","type":"MODEL","link":20},{"name":"target_image","type":"IMAGE","link":14},{"name":"refer_image","type":"IMAGE","link":15},{"name":"mask_image","type":"IMAGE","link":19}],"outputs":[{"name":"image","type":"IMAGE","slot_index":0,"links":[27]}],"properties":{"cnr_id":"comfyui-catvton","ver":"6ffd4a491c4cfb8923f4dece7844b68f5c392a72","Node name for S&R":"CatVTON","aux_id":"pzc163/Comfyui-CatVTON"},"widgets_values":[24,"fixed",50,2.5]},{"id":12,"type":"LoadAutoMasker","pos":[98.47675323486328,95.84894561767578],"size":[436.1082458496094,58],"flags":{},"order":1,"mode":0,"inputs":[],"outputs":[{"name":"pipe","type":"MODEL","slot_index":0,"links":[11]}],"properties":{"cnr_id":"comfyui-catvton","ver":"6ffd4a491c4cfb8923f4dece7844b68f5c392a72","Node name for S&R":"LoadAutoMasker","aux_id":"pzc163/Comfyui-CatVTON"},"widgets_values":["zhengchong/CatVTON"]},{"id":10,"type":"LoadImage","pos":[93.77685546875,465.34710693359375],"size":[210,345.0123291015625],"flags":{"pinned":false},"order":2,"mode":0,"inputs":[],"outputs":[{"name":"IMAGE","type":"IMAGE","slot_index":0,"links":[10,14]},{"name":"MASK","type":"MASK","slot_index":1,"links":null}],"title":"Target Person","properties":{"cnr_id":"comfy-core","ver":"0.3.39","Node name for S&R":"LoadImage"},"widgets_values":["Знімок екрана 2025-06-03 165847.png","image"],"shape":2},{"id":11,"type":"LoadImage","pos":[319.77685546875,463.34710693359375],"size":[210,347.0123291015625],"flags":{},"order":3,"mode":0,"inputs":[],"outputs":[{"name":"IMAGE","type":"IMAGE","slot_index":0,"links":[15]},{"name":"MASK","type":"MASK","links":null}],"title":"Reference Garment","properties":{"cnr_id":"comfy-core","ver":"0.3.39","Node name for S&R":"LoadImage"},"widgets_values":["Знімок екрана 2025-06-03 165925.png","image"],"shape":2}],"links":[[10,10,0,13,1,"IMAGE"],[11,12,0,13,0,"MODEL"],[14,10,0,16,1,"IMAGE"],[15,11,0,16,2,"IMAGE"],[17,13,1,14,0,"IMAGE"],[18,13,0,15,0,"IMAGE"],[19,13,0,16,3,"IMAGE"],[20,17,0,16,0,"MODEL"],[27,16,0,18,0,"IMAGE"]],"groups":[{"id":1,"title":"Model Loading","bounding":[80,38,480,333],"color":"#b06634","font_size":24,"flags":{}},{"id":2,"title":"Auto Mask Generating","bounding":[593.3880004882812,26.535490036010742,630,339],"color":"#8AA","font_size":24,"flags":{}},{"id":3,"title":"Inputs Image","bounding":[80,384,483,443],"color":"#3f789e","font_size":24,"flags":{}},{"id":4,"title":"TryOn by CatVTON","bounding":[586.5397338867188,419.70135498046875,629,441],"color":"#b58b2a","font_size":24,"flags":{}}],"config":{},"extra":{"ds":{"scale":0.8954302432552391,"offset":[291.2229995721141,-32.98225081453819]},"frontendVersion":"1.21.6"},"version":0.4}}}}
# {"client_id":"e719497b6f7c4adbba1ccf9ae798c800","prompt":{"10":{"inputs":{"image":"Знімок екрана 2025-06-03 165847.png"},"class_type":"LoadImage","_meta":{"title":"Target Person"}},"11":{"inputs":{"image":"Знімок екрана 2025-06-03 165925.png"},"class_type":"LoadImage","_meta":{"title":"Reference Garment"}},"12":{"inputs":{"catvton_path":"zhengchong/CatVTON"},"class_type":"LoadAutoMasker","_meta":{"title":"Load AutoMask Generator"}},"13":{"inputs":{"cloth_type":"upper","pipe":["12",0],"target_image":["10",0]},"class_type":"AutoMasker","_meta":{"title":"Auto Mask Generation"}},"14":{"inputs":{"images":["13",1]},"class_type":"PreviewImage","_meta":{"title":"Masked Target"}},"15":{"inputs":{"images":["13",0]},"class_type":"PreviewImage","_meta":{"title":"Binary Mask"}},"16":{"inputs":{"seed":24,"steps":50,"cfg":2.5,"pipe":["17",0],"target_image":["10",0],"refer_image":["11",0],"mask_image":["13",0]},"class_type":"CatVTON","_meta":{"title":"TryOn by CatVTON"}},"17":{"inputs":{"sd15_inpaint_path":"runwayml/stable-diffusion-inpainting","catvton_path":"zhengchong/CatVTON","mixed_precision":"bf16"},"class_type":"LoadCatVTONPipeline","_meta":{"title":"Load CatVTON Pipeline"}},"18":{"inputs":{"images":["16",0]},"class_type":"PreviewImage","_meta":{"title":"Preview Image"}}},"extra_data":{"extra_pnginfo":{"workflow":{"id":"881f01a5-8662-43ea-8e6f-52f83b719e0c","revision":0,"last_node_id":23,"last_link_id":27,"nodes":[{"id":14,"type":"PreviewImage","pos":[1042.3883056640625,104.53547668457031],"size":[160.99398803710938,246],"flags":{},"order":7,"mode":0,"inputs":[{"name":"images","type":"IMAGE","link":17}],"outputs":[],"title":"Masked Target","properties":{"cnr_id":"comfy-core","ver":"0.3.39","Node name for S&R":"PreviewImage"},"widgets_values":[]},{"id":18,"type":"PreviewImage","pos":[885.5392456054688,501.701416015625],"size":[313.9939880371094,341.0123291015625],"flags":{},"order":8,"mode":0,"inputs":[{"name":"images","type":"IMAGE","link":27}],"outputs":[],"properties":{"cnr_id":"comfy-core","ver":"0.3.39","Node name for S&R":"PreviewImage"},"widgets_values":[]},{"id":15,"type":"PreviewImage","pos":[859.3865356445312,105.53547668457031],"size":[160.1082305908203,246],"flags":{},"order":5,"mode":0,"inputs":[{"name":"images","type":"IMAGE","link":18}],"outputs":[],"title":"Binary Mask","properties":{"cnr_id":"comfy-core","ver":"0.3.39","Node name for S&R":"PreviewImage"},"widgets_values":[]},{"id":17,"type":"LoadCatVTONPipeline","pos":[101,223],"size":[431.00823974609375,106],"flags":{},"order":0,"mode":0,"inputs":[],"outputs":[{"name":"pipe","type":"MODEL","slot_index":0,"links":[20]}],"properties":{"cnr_id":"comfyui-catvton","ver":"6ffd4a491c4cfb8923f4dece7844b68f5c392a72","Node name for S&R":"LoadCatVTONPipeline","aux_id":"pzc163/Comfyui-CatVTON"},"widgets_values":["runwayml/stable-diffusion-inpainting","zhengchong/CatVTON","bf16"]},{"id":13,"type":"AutoMasker","pos":[607.3880004882812,105.53547668457031],"size":[227.4981231689453,240.48341369628906],"flags":{},"order":4,"mode":0,"inputs":[{"name":"pipe","type":"MODEL","link":11},{"name":"target_image","type":"IMAGE","link":10}],"outputs":[{"name":"image","type":"IMAGE","slot_index":0,"links":[18,19]},{"name":"image_masked","type":"IMAGE","slot_index":1,"links":[17]}],"properties":{"cnr_id":"comfyui-catvton","ver":"6ffd4a491c4cfb8923f4dece7844b68f5c392a72","Node name for S&R":"AutoMasker","aux_id":"pzc163/Comfyui-CatVTON"},"widgets_values":["upper"]},{"id":16,"type":"CatVTON","pos":[605.5397338867188,503.701416015625],"size":[242.99398803710938,338.0123291015625],"flags":{},"order":6,"mode":0,"inputs":[{"name":"pipe","type":"MODEL","link":20},{"name":"target_image","type":"IMAGE","link":14},{"name":"refer_image","type":"IMAGE","link":15},{"name":"mask_image","type":"IMAGE","link":19}],"outputs":[{"name":"image","type":"IMAGE","slot_index":0,"links":[27]}],"properties":{"cnr_id":"comfyui-catvton","ver":"6ffd4a491c4cfb8923f4dece7844b68f5c392a72","Node name for S&R":"CatVTON","aux_id":"pzc163/Comfyui-CatVTON"},"widgets_values":[24,"fixed",50,2.5]},{"id":12,"type":"LoadAutoMasker","pos":[98.47675323486328,95.84894561767578],"size":[436.1082458496094,58],"flags":{},"order":1,"mode":0,"inputs":[],"outputs":[{"name":"pipe","type":"MODEL","slot_index":0,"links":[11]}],"properties":{"cnr_id":"comfyui-catvton","ver":"6ffd4a491c4cfb8923f4dece7844b68f5c392a72","Node name for S&R":"LoadAutoMasker","aux_id":"pzc163/Comfyui-CatVTON"},"widgets_values":["zhengchong/CatVTON"]},{"id":10,"type":"LoadImage","pos":[93.77685546875,465.34710693359375],"size":[210,345.0123291015625],"flags":{"pinned":false},"order":2,"mode":0,"inputs":[],"outputs":[{"name":"IMAGE","type":"IMAGE","slot_index":0,"links":[10,14]},{"name":"MASK","type":"MASK","slot_index":1,"links":null}],"title":"Target Person","properties":{"cnr_id":"comfy-core","ver":"0.3.39","Node name for S&R":"LoadImage"},"widgets_values":["Знімок екрана 2025-06-03 165847.png","image"],"shape":2},{"id":11,"type":"LoadImage","pos":[319.77685546875,463.34710693359375],"size":[210,347.0123291015625],"flags":{},"order":3,"mode":0,"inputs":[],"outputs":[{"name":"IMAGE","type":"IMAGE","slot_index":0,"links":[15]},{"name":"MASK","type":"MASK","links":null}],"title":"Reference Garment","properties":{"cnr_id":"comfy-core","ver":"0.3.39","Node name for S&R":"LoadImage"},"widgets_values":["Знімок екрана 2025-06-03 165925.png","image"],"shape":2}],"links":[[10,10,0,13,1,"IMAGE"],[11,12,0,13,0,"MODEL"],[14,10,0,16,1,"IMAGE"],[15,11,0,16,2,"IMAGE"],[17,13,1,14,0,"IMAGE"],[18,13,0,15,0,"IMAGE"],[19,13,0,16,3,"IMAGE"],[20,17,0,16,0,"MODEL"],[27,16,0,18,0,"IMAGE"]],"groups":[{"id":1,"title":"Model Loading","bounding":[80,38,480,333],"color":"#b06634","font_size":24,"flags":{}},{"id":2,"title":"Auto Mask Generating","bounding":[593.3880004882812,26.535490036010742,630,339],"color":"#8AA","font_size":24,"flags":{}},{"id":3,"title":"Inputs Image","bounding":[80,384,483,443],"color":"#3f789e","font_size":24,"flags":{}},{"id":4,"title":"TryOn by CatVTON","bounding":[586.5397338867188,419.70135498046875,629,441],"color":"#b58b2a","font_size":24,"flags":{}}],"config":{},"extra":{"ds":{"scale":0.8140274938683989,"offset":[-65.70038592200694,-17.570665038931736]},"frontendVersion":"1.21.6"},"version":0.4}}}}
# async def send_workflow_to_comfyui(workflow, person_path, cloth_path, person_filename, cloth_filename):
#     print("[DEBUG] here:")
#     async with aiohttp.ClientSession() as session:
#         print("[DEBUG] here qq:")
#         person_uploaded = await upload_image(person_path, session)
#         print("[DEBUG] here ww:")
#         cloth_uploaded = await upload_image(cloth_path, session)

#         workflow["10"]["inputs"]["image"] = person_uploaded
#         workflow["11"]["inputs"]["image"] = cloth_uploaded

#         print("[DEBUG] Final workflow to send:")
#         print(json.dumps(workflow, indent=2))

#         async with websockets.connect(COMFYUI_WS_URL, max_size=100*1024*1024) as ws:
#             import uuid
#             prompt_id = "tryon_" + str(uuid.uuid4())
#             await ws.send(json.dumps({
#                 "type": "queue_prompt",
#                 "prompt": workflow,
#                 "prompt_id": prompt_id
#             }))
#             print(f"[WS] Відправлено workflow з prompt_id = {prompt_id}")

#             while True:
#                 msg = await ws.recv()
#                 print(f'[WS] Отримано повідомлення: {msg}')
#                 try:
#                     data = json.loads(msg)
#                     print(f"[WS] Розібрано JSON: {data}")
#                 except:
#                     continue

#                 if data.get("type") == "executed" and data.get("prompt_id") == prompt_id:
#                     outputs = data.get("outputs", {})
#                     for node_id, node_data in outputs.items():
#                         if node_data.get("class_type") == "PreviewImage":
#                             images = node_data.get("images", [])
#                             if images:
#                                 image_name = images[0]
#                                 print(f"[WS] Знайдено зображення: {image_name}")
#                                 img_url = f"{COMFYUI_HTTP_URL}/view?filename={image_name}"
#                                 async with session.get(img_url) as img_resp:
#                                     return await img_resp.read()
#             print("[WS] Завершено з'єднання.")
