# app.py
# This is your web server.
# It receives text from a browser, generates a DXF floor plan,
# and sends it back as a download.
# Run it with: py app.py
# Then open your browser to: http://localhost:5000

from flask import Flask, request, send_file, render_template, jsonify
from flask_cors import CORS
from parser import parse_brief
from generator import generate_dxf, generate_svg
from dotenv import load_dotenv
import os
import json
from datetime import datetime

# Load your API key from .env file
load_dotenv()

# Create the Flask web application
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Make sure the output folder exists
os.makedirs("output", exist_ok=True)


# ── ROUTE 1: Show the main web page ─────────────────────────
# When someone visits your website, they see index.html
@app.route("/")
def home():
    return render_template("index.html")


# ── ROUTE 2: Generate floor plan ────────────────────────────
# When someone clicks Generate, the browser sends the text here.
# This route parses it, generates the DXF, and returns the file.
@app.route("/generate", methods=["POST"])
def generate():
    try:
        # Get the text the user typed
        data = request.get_json()
        description = data.get("description", "")

        if not description.strip():
            return jsonify({"error": "Please enter a description"}), 400

        # Step 1: Parse the text into dimensions
        print(f"Received: {description[:50]}...")
        parsed = parse_brief(description)

        if "error" in parsed:
            return jsonify({"error": parsed["error"]}), 400

        # Step 2: Generate the DXF file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output/floorplan_{timestamp}.dxf"
        generate_dxf(parsed, filename)

        # Step 3: Send the DXF file back to the browser as a download
        return send_file(
            filename,
            as_attachment=True,
            download_name=f"floorplan_{timestamp}.dxf",
            mimetype="application/dxf"
        )

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": f"Something went wrong: {str(e)}"}), 500


# ── ROUTE 3: Health check ────────────────────────────────────
# A simple check to confirm the server is running
@app.route("/health")
def health():
    return jsonify({"status": "running", "message": "Busan CAD API is online"})
@app.route("/preview", methods=["POST"])
def preview():
    """Returns an SVG preview of the floor plan for display in browser."""
    try:
        data = request.get_json()
        description = data.get("description", "")
        if not description.strip():
            return jsonify({"error": "No description"}), 400

        parsed = parse_brief(description)
        if "error" in parsed:
            return jsonify({"error": parsed["error"]}), 400

        svg = generate_svg(parsed)
        spaces_summary = []
        for s in parsed.get("spaces", []):
            spaces_summary.append({
                "name": s.get("name"),
                "length_mm": s.get("length_mm"),
                "width_mm": s.get("width_mm"),
                "wall_thickness_mm": s.get("wall_thickness_mm"),
                "doors": len(s.get("doors", []))
            })

        return jsonify({
            "svg": svg,
            "spaces": spaces_summary,
            "assumptions": parsed.get("assumptions", []),
            "warnings": parsed.get("warnings", [])
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/render3d", methods=["POST"])
def render3d():
    """Generates a photorealistic 3D render image of the space."""
    import requests as req
    import base64

    try:
        data = request.get_json()
        description = data.get("description", "")
        spaces = data.get("spaces", [])

        # Build a detailed render prompt from the space data
        space_info = ""
        if spaces:
            s = spaces[0]
            length_m = s.get("length_mm", 5000) // 1000
            width_m = s.get("width_mm", 5000) // 1000
            name = s.get("name", "exhibition booth")
            space_info = f"a {length_m} metre by {width_m} metre {name}"
        else:
            space_info = "an exhibition booth"

        render_prompt = f"""Professional architectural interior 3D render of {space_info}.
Modern exhibition design, clean minimalist space.
Empty room showing walls, polished concrete floor, recessed ceiling lights.
Photorealistic architectural visualization, ray traced lighting.
High quality render, sharp details, professional photography style.
Wide angle view showing the full space."""

        negative_prompt = "people, furniture, blurry, low quality, dark, cartoon, drawing, sketch"

        stability_key = os.getenv("STABILITY_API_KEY")
        if not stability_key:
            return jsonify({"error": "Stability API key not configured"}), 500

        print(f"Generating 3D render for: {space_info}")

        response = req.post(
            "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
            headers={
                "Authorization": f"Bearer {stability_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            json={
                "text_prompts": [
                    {"text": render_prompt, "weight": 1.0},
                    {"text": negative_prompt, "weight": -1.0}
                ],
                "cfg_scale": 7,
                "height": 768,
                "width": 1344,
                "samples": 1,
                "steps": 30,
                "style_preset": "photographic"
            },
            timeout=60
        )

        if response.status_code != 200:
            print(f"Stability API error: {response.status_code} — {response.text}")
            return jsonify({"error": f"Render failed: {response.status_code}"}), 500

        result = response.json()
        image_base64 = result["artifacts"][0]["base64"]

        print("3D render generated successfully")
        return jsonify({
            "image_base64": image_base64,
            "space_info": space_info
        })

    except req.exceptions.Timeout:
        return jsonify({"error": "Render timed out — please try again"}), 500
    except Exception as e:
        print(f"Render error: {e}")
        return jsonify({"error": str(e)}), 500
    
# ── START THE SERVER ─────────────────────────────────────────
# This runs when you type: py app.py
if __name__ == "__main__":
    print("="*50)
    print("Busan CAD Server starting...")
    print("Open your browser and go to:")
    print("  http://localhost:5000")
    print("="*50)
    app.run(debug=True, host="0.0.0.0", port=5000)
    