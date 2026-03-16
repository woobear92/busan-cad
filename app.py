# app.py
# This is your web server.
# It receives text from a browser, generates a DXF floor plan,
# and sends it back as a download.
# Run it with: py app.py
# Then open your browser to: http://localhost:5000

from flask import Flask, request, send_file, render_template, jsonify
from flask_cors import CORS
from parser import parse_brief
from generator import generate_dxf, generate_svg, generate_section_view, generate_elevation_view, generate_top_view, generate_electrical_plan, generate_water_plan, generate_rigging_plan
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import requests
import base64

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

os.makedirs("output", exist_ok=True)

STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify({"status": "running", "message": "Busan CAD API is online"})

@app.route('/preview', methods=['POST'])
def preview():
    try:
        data = request.get_json()
        description = data.get('description', '')
        view_type = data.get('view_type', 'floor_plan')

        parsed = parse_brief(description)

        if view_type == 'section':
            svg = generate_section_view(parsed)
        elif view_type == 'elevation':
            svg = generate_elevation_view(parsed)
        elif view_type == 'top':
            svg = generate_top_view(parsed)
        elif view_type == 'electrical':
            svg = generate_electrical_plan(parsed)
        elif view_type == 'water':
            svg = generate_water_plan(parsed)
        elif view_type == 'rigging':
            svg = generate_rigging_plan(parsed)
        else:
            svg = generate_svg(parsed)

        spaces = parsed.get('spaces', [])
        space_info = []
        for s in spaces:
            space_info.append({
                'name': s.get('name', 'Space'),
                'length_mm': s.get('length_mm', 0),
                'width_mm': s.get('width_mm', 0),
                'wall_thickness_mm': s.get('wall_thickness_mm', 200),
                'ceiling_height_mm': s.get('ceiling_height_mm', 4000),
                'doors': s.get('doors', [])
            })

        return jsonify({
            'svg': svg,
            'spaces': space_info,
            'view_type': view_type
        })

    except Exception as e:
        print(f"Preview error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()
        description = data.get('description', '')
        parsed = parse_brief(description)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"floorplan_{timestamp}.dxf"
        filepath = os.path.join("output", filename)
        generate_dxf(parsed, filepath)
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        print(f"Generate error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/render3d', methods=['POST'])
def render3d():
    try:
        data = request.get_json()
        description = data.get('description', '')
        spaces = data.get('spaces', [])

        if not STABILITY_API_KEY:
            return jsonify({'error': 'Stability API key not configured'}), 500

        space_info = "exhibition booth"
        if spaces:
            s = spaces[0]
            length = s.get('length_mm', 10000) / 1000
            width = s.get('width_mm', 8000) / 1000
            space_info = f"a {length} metre by {width} metre booth"

        prompt = f"Professional architectural 3D rendering of {space_info}, modern exhibition booth interior design, clean white walls, professional lighting, photorealistic, high quality render"

        response = requests.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
            headers={
                "Authorization": f"Bearer {STABILITY_API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json={
                "text_prompts": [{"text": prompt, "weight": 1}],
                "cfg_scale": 7,
                "height": 1024,
                "width": 1024,
                "samples": 1,
                "steps": 30
            },
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            image_base64 = result["artifacts"][0]["base64"]
            print("3D render generated successfully")
            return jsonify({
                "image_base64": image_base64,
                "space_info": space_info
            })
        else:
            return jsonify({'error': f'Render failed: {response.status_code} {response.text}'}), 500

    except requests.exceptions.Timeout:
        return jsonify({"error": "Render timed out - please try again"}), 500
    except Exception as e:
        print(f"Render error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("=" * 50)
    print("Busan CAD Server starting...")
    print("Open your browser and go to:")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)