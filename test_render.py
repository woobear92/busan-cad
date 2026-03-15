# test_render.py
# This tests your 3D render route properly
import requests
import json
import base64
import os

print("Testing 3D render route...")

# Send request to your Flask server
response = requests.post(
    "http://localhost:5000/render3d",
    json={
        "description": "exhibition booth 10m x 8m",
        "spaces": [
            {
                "name": "booth",
                "length_mm": 10000,
                "width_mm": 8000
            }
        ]
    }
)

print(f"Status code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    
    if "image_base64" in data:
        print("SUCCESS! 3D render generated")
        print(f"Space: {data.get('space_info')}")
        
        # Save the image so you can see it
        image_data = base64.b64decode(data["image_base64"])
        output_path = "output/test_render.png"
        os.makedirs("output", exist_ok=True)
        
        with open(output_path, "wb") as f:
            f.write(image_data)
        
        print(f"Image saved to: {output_path}")
        print("Open that file to see your 3D render!")
        
    elif "error" in data:
        print(f"Error from server: {data['error']}")
else:
    print(f"Failed: {response.text}")