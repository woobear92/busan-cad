import ezdxf
import os
from datetime import datetime

def generate_dxf(parsed_data, output_filename=None):
    if "error" in parsed_data:
        print(f"Cannot generate: {parsed_data['error']}")
        return None
    
    doc = ezdxf.new(dxfversion='R2010')
    msp = doc.modelspace()
    
    # Create layers
    doc.layers.add(name="WALLS", color=1)
    doc.layers.add(name="DIMENSIONS", color=5)
    doc.layers.add(name="TEXT", color=7)
    doc.layers.add(name="DOORS", color=3)
    
    x_offset = 0
    
    for space in parsed_data["spaces"]:
        name      = space.get("name", "space")
        length    = space.get("length_mm", 5000)
        width     = space.get("width_mm", 5000)
        thickness = space.get("wall_thickness_mm", 200)
        doors     = space.get("doors", [])
        
        ox = x_offset
        oy = 0
        
        print(f"Drawing: '{name}' — {length}mm x {width}mm, walls {thickness}mm")
        
        # Draw 4 walls as filled rectangles
        # South wall
        msp.add_lwpolyline(
            [(ox, oy), (ox+length, oy), (ox+length, oy+thickness), (ox, oy+thickness)],
            close=True, dxfattribs={"layer": "WALLS"})
        
        # North wall
        msp.add_lwpolyline(
            [(ox, oy+width-thickness), (ox+length, oy+width-thickness),
             (ox+length, oy+width), (ox, oy+width)],
            close=True, dxfattribs={"layer": "WALLS"})
        
        # West wall
        msp.add_lwpolyline(
            [(ox, oy+thickness), (ox+thickness, oy+thickness),
             (ox+thickness, oy+width-thickness), (ox, oy+width-thickness)],
            close=True, dxfattribs={"layer": "WALLS"})
        
        # East wall
        msp.add_lwpolyline(
            [(ox+length-thickness, oy+thickness), (ox+length, oy+thickness),
             (ox+length, oy+width-thickness), (ox+length-thickness, oy+width-thickness)],
            close=True, dxfattribs={"layer": "WALLS"})
        
        # Draw doors
        for door in doors:
            wall     = door.get("wall", "south").lower()
            pos      = door.get("position_from_left_mm", 1000)
            dw       = door.get("width_mm", 900)
            
            if wall == "south":
                msp.add_line((ox+pos, oy+thickness), (ox+pos+dw, oy+thickness),
                             dxfattribs={"layer": "DOORS"})
                msp.add_arc(center=(ox+pos, oy+thickness),
                            radius=dw, start_angle=0, end_angle=90,
                            dxfattribs={"layer": "DOORS"})
            elif wall == "north":
                msp.add_line((ox+pos, oy+width-thickness), (ox+pos+dw, oy+width-thickness),
                             dxfattribs={"layer": "DOORS"})
                msp.add_arc(center=(ox+pos, oy+width-thickness),
                            radius=dw, start_angle=270, end_angle=360,
                            dxfattribs={"layer": "DOORS"})
            elif wall == "west":
                msp.add_line((ox+thickness, oy+pos), (ox+thickness, oy+pos+dw),
                             dxfattribs={"layer": "DOORS"})
                msp.add_arc(center=(ox+thickness, oy+pos),
                            radius=dw, start_angle=0, end_angle=90,
                            dxfattribs={"layer": "DOORS"})
            elif wall == "east":
                msp.add_line((ox+length-thickness, oy+pos),
                             (ox+length-thickness, oy+pos+dw),
                             dxfattribs={"layer": "DOORS"})
                msp.add_arc(center=(ox+length-thickness, oy+pos),
                            radius=dw, start_angle=90, end_angle=180,
                            dxfattribs={"layer": "DOORS"})
        
        # Add dimension lines
        dim_offset = 1000
        if "BUSAN_DIM" not in doc.dimstyles:
            ds = doc.dimstyles.new("BUSAN_DIM")
            ds.dxf.dimtxt = 200
            ds.dxf.dimasz = 150
        
        msp.add_linear_dim(
            base=(ox + length/2, oy - dim_offset),
            p1=(ox, oy), p2=(ox+length, oy),
            dimstyle="BUSAN_DIM",
            dxfattribs={"layer": "DIMENSIONS"}
        ).render()
        
        msp.add_linear_dim(
            base=(ox - dim_offset, oy + width/2),
            p1=(ox, oy), p2=(ox, oy+width),
            angle=90,
            dimstyle="BUSAN_DIM",
            dxfattribs={"layer": "DIMENSIONS"}
        ).render()
        
        # Room label in centre
        cx = ox + length/2
        cy = oy + width/2
        msp.add_text(
            name.upper(),
            dxfattribs={"layer": "TEXT",
                        "height": min(length, width) * 0.04,
                        "insert": (cx, cy)}
        )
        
        x_offset += length + 2000
    
    # Save file
    os.makedirs("output", exist_ok=True)
    if output_filename is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"output/floorplan_{ts}.dxf"
    
    doc.saveas(output_filename)
    print(f"DXF saved: {output_filename}")
    return output_filename


if __name__ == "__main__":
    test_data = {
        "spaces": [{
            "name": "Exhibition Booth",
            "length_mm": 10000,
            "width_mm": 8000,
            "height_mm": 3000,
            "wall_thickness_mm": 200,
            "doors": [{
                "wall": "south",
                "position_from_left_mm": 4550,
                "width_mm": 900,
                "height_mm": 2100
            }],
            "windows": [],
            "notes": ""
        }],
        "assumptions": [],
        "warnings": []
    }
    
    result = generate_dxf(test_data)
    print(f"\nOpen this file to see your floor plan:")
    print(f"  {result}")

def generate_svg(parsed_data):
    """
    Creates an SVG image of the floor plan.
    SVG displays directly in browsers — no download needed.
    Returns the SVG as a text string.
    """
    if "error" in parsed_data:
        return None

    spaces = parsed_data.get("spaces", [])
    if not spaces:
        return None

    # Find total drawing size for SVG viewbox
    total_width = sum(s.get("length_mm", 5000) for s in spaces)
    total_width += (len(spaces) - 1) * 2000  # gaps between rooms
    max_height = max(s.get("width_mm", 5000) for s in spaces)

    # Add padding for dimension lines
    padding = 2000
    svg_w = total_width + padding * 2
    svg_h = max_height + padding * 2

    # Scale: fit into 800px wide display
    scale = 800 / svg_w
    display_w = int(svg_w * scale)
    display_h = int(svg_h * scale)

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{display_w}" height="{display_h}" viewBox="0 0 {svg_w} {svg_h}">')
    lines.append('<rect width="100%" height="100%" fill="#0f0f0f"/>')

    x_offset = padding

    for space in spaces:
        name = space.get("name", "space")
        length = space.get("length_mm", 5000)
        width = space.get("width_mm", 5000)
        thick = space.get("wall_thickness_mm", 200)
        doors = space.get("doors", [])

        ox = x_offset
        oy = padding

        # Outer wall rectangle
        lines.append(f'<rect x="{ox}" y="{oy}" width="{length}" height="{width}" fill="none" stroke="#e05555" stroke-width="{thick}"/>')

        # Inner space (fill)
        lines.append(f'<rect x="{ox+thick}" y="{oy+thick}" width="{length-thick*2}" height="{width-thick*2}" fill="#1a1a2e" opacity="0.8"/>')

        # Room name label
        cx = ox + length / 2
        cy = oy + width / 2
        font_size = min(length, width) * 0.06
        lines.append(f'<text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="middle" fill="#ffffff" font-size="{font_size}" font-family="monospace" font-weight="bold">{name.upper()}</text>')

        # Dimension labels
        dim_font = min(length, width) * 0.04
        lines.append(f'<text x="{cx}" y="{oy+width+400}" text-anchor="middle" fill="#4a9eff" font-size="{dim_font}" font-family="monospace">{length}mm</text>')
        lines.append(f'<text x="{ox-400}" y="{oy+width/2}" text-anchor="middle" fill="#4a9eff" font-size="{dim_font}" font-family="monospace" transform="rotate(-90,{ox-400},{oy+width/2})">{width}mm</text>')

        # Dimension lines
        lines.append(f'<line x1="{ox}" y1="{oy+width+250}" x2="{ox+length}" y2="{oy+width+250}" stroke="#4a9eff" stroke-width="30" marker-end="url(#arrow)" marker-start="url(#arrow)"/>')

        # Draw doors
        for door in doors:
            wall = door.get("wall", "south").lower()
            pos = door.get("position_from_left_mm", 1000)
            dw = door.get("width_mm", 900)

            if wall == "south":
                dx = ox + pos
                dy = oy + width - thick
                # Door gap (white gap in wall)
                lines.append(f'<rect x="{dx}" y="{dy}" width="{dw}" height="{thick+2}" fill="#0f0f0f"/>')
                # Door swing arc
                lines.append(f'<path d="M{dx},{dy} A{dw},{dw} 0 0,1 {dx+dw},{dy}" fill="none" stroke="#4adf4a" stroke-width="60" stroke-dasharray="100,100"/>')
            elif wall == "north":
                dx = ox + pos
                dy = oy
                lines.append(f'<rect x="{dx}" y="{dy-2}" width="{dw}" height="{thick+2}" fill="#0f0f0f"/>')
                lines.append(f'<path d="M{dx},{dy+thick} A{dw},{dw} 0 0,0 {dx+dw},{dy+thick}" fill="none" stroke="#4adf4a" stroke-width="60" stroke-dasharray="100,100"/>')
            elif wall == "west":
                dx = ox
                dy = oy + pos
                lines.append(f'<rect x="{dx-2}" y="{dy}" width="{thick+2}" height="{dw}" fill="#0f0f0f"/>')
                lines.append(f'<path d="M{dx+thick},{dy} A{dw},{dw} 0 0,0 {dx+thick},{dy+dw}" fill="none" stroke="#4adf4a" stroke-width="60" stroke-dasharray="100,100"/>')
            elif wall == "east":
                dx = ox + length - thick
                dy = oy + pos
                lines.append(f'<rect x="{dx-2}" y="{dy}" width="{thick+2}" height="{dw}" fill="#0f0f0f"/>')
                lines.append(f'<path d="M{dx},{dy} A{dw},{dw} 0 0,1 {dx},{dy+dw}" fill="none" stroke="#4adf4a" stroke-width="60" stroke-dasharray="100,100"/>')

        x_offset += length + 2000

    lines.append('</svg>')
    return "\n".join(lines)

    # ============================================================
# SECTION VIEW - vertical cut showing wall heights
# ============================================================
def generate_section_view(parsed_data):
    spaces = parsed_data.get("spaces", [])
    if not spaces:
        return "<svg><text x='50' y='50' fill='white'>No data</text></svg>"

    space = spaces[0]
    length = space.get("length_mm", 10000)
    width = space.get("width_mm", 8000)
    thick = space.get("wall_thickness_mm", 200)
    height_mm = space.get("ceiling_height_mm", 4000)
    name = space.get("name", "Space")

    scale = 0.06
    sw = int(length * scale)
    sh = int(height_mm * scale)
    pad = 80
    svg_w = sw + pad * 2
    svg_h = sh + pad * 2

    lines = []
    lines.append(f'<svg width="{svg_w}" height="{svg_h}" xmlns="http://www.w3.org/2000/svg" style="background:#0a0a0a">')
    lines.append(f'<text x="{svg_w//2}" y="20" fill="#888" font-size="12" text-anchor="middle" font-family="monospace">SECTION VIEW — {name.upper()}</text>')

    ox = pad
    oy = pad

    # Floor
    lines.append(f'<rect x="{ox}" y="{oy+sh}" width="{sw}" height="{int(thick*scale)+4}" fill="#444" stroke="#666" stroke-width="1"/>')
    # Left wall
    lines.append(f'<rect x="{ox}" y="{oy}" width="{int(thick*scale)+4}" height="{sh}" fill="#555" stroke="#888" stroke-width="1"/>')
    # Right wall
    lines.append(f'<rect x="{ox+sw-int(thick*scale)-4}" y="{oy}" width="{int(thick*scale)+4}" height="{sh}" fill="#555" stroke="#888" stroke-width="1"/>')
    # Ceiling
    lines.append(f'<rect x="{ox}" y="{oy}" width="{sw}" height="{int(thick*scale)+4}" fill="#444" stroke="#666" stroke-width="1"/>')

    # Interior space fill
    ix = ox + int(thick*scale) + 4
    iy = oy + int(thick*scale) + 4
    iw = sw - 2*(int(thick*scale)+4)
    ih = sh - 2*(int(thick*scale)+4)
    lines.append(f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" fill="#111" stroke="none"/>')

    # Height dimension line
    lines.append(f'<line x1="{ox+sw+20}" y1="{oy}" x2="{ox+sw+20}" y2="{oy+sh}" stroke="#0af" stroke-width="1" stroke-dasharray="4,2"/>')
    lines.append(f'<text x="{ox+sw+35}" y="{oy+sh//2}" fill="#0af" font-size="11" font-family="monospace" dominant-baseline="middle">{height_mm}mm</text>')

    # Width dimension line
    lines.append(f'<line x1="{ox}" y1="{oy+sh+30}" x2="{ox+sw}" y2="{oy+sh+30}" stroke="#0af" stroke-width="1" stroke-dasharray="4,2"/>')
    lines.append(f'<text x="{ox+sw//2}" y="{oy+sh+45}" fill="#0af" font-size="11" font-family="monospace" text-anchor="middle">{length_mm}mm</text>')

    # Floor label
    lines.append(f'<text x="{ox+sw//2}" y="{oy+sh+int(thick*scale)+18}" fill="#666" font-size="10" text-anchor="middle" font-family="monospace">FLOOR LEVEL ±0</text>')
    # Ceiling label
    lines.append(f'<text x="{ox+sw//2}" y="{oy-8}" fill="#666" font-size="10" text-anchor="middle" font-family="monospace">CEILING +{height_mm}mm</text>')

    # Grid lines inside for scale reference
    for i in range(1, 4):
        gx = ox + int((sw/4)*i)
        lines.append(f'<line x1="{gx}" y1="{iy}" x2="{gx}" y2="{iy+ih}" stroke="#1a1a1a" stroke-width="1"/>')

    lines.append('</svg>')
    return "\n".join(lines)


# ============================================================
# ELEVATION VIEW - flat wall face drawings
# ============================================================
def generate_elevation_view(parsed_data):
    spaces = parsed_data.get("spaces", [])
    if not spaces:
        return "<svg><text x='50' y='50' fill='white'>No data</text></svg>"

    space = spaces[0]
    length = space.get("length_mm", 10000)
    width = space.get("width_mm", 8000)
    thick = space.get("wall_thickness_mm", 200)
    height_mm = space.get("ceiling_height_mm", 4000)
    doors = space.get("doors", [])
    name = space.get("name", "Space")

    scale = 0.05
    pad = 60
    door_w = 1200
    door_h = 2100

    walls = [
        ("NORTH ELEVATION", length),
        ("SOUTH ELEVATION", length),
        ("EAST ELEVATION", width),
        ("WEST ELEVATION", width),
    ]

    cols = 2
    cell_w = 420
    cell_h = 280
    svg_w = cols * cell_w + pad
    svg_h = (len(walls) // cols + 1) * cell_h + pad

    lines = []
    lines.append(f'<svg width="{svg_w}" height="{svg_h}" xmlns="http://www.w3.org/2000/svg" style="background:#0a0a0a">')
    lines.append(f'<text x="{svg_w//2}" y="20" fill="#888" font-size="12" text-anchor="middle" font-family="monospace">ELEVATION VIEWS — {name.upper()}</text>')

    for i, (label, wall_len) in enumerate(walls):
        col = i % cols
        row = i // cols
        ox = col * cell_w + 40
        oy = row * cell_h + 40

        ww = int(wall_len * scale)
        wh = int(height_mm * scale)

        # Wall outline
        lines.append(f'<rect x="{ox}" y="{oy+20}" width="{ww}" height="{wh}" fill="#1a1a1a" stroke="#555" stroke-width="1.5"/>')

        # Door opening on south wall
        if "SOUTH" in label and doors:
            dw = int(door_w * scale)
            dh = int(door_h * scale)
            dx = ox + ww//2 - dw//2
            dy = oy + 20 + wh - dh
            lines.append(f'<rect x="{dx}" y="{dy}" width="{dw}" height="{dh}" fill="#0a0a0a" stroke="#888" stroke-width="1"/>')
            lines.append(f'<text x="{dx+dw//2}" y="{dy+dh//2}" fill="#555" font-size="9" text-anchor="middle" font-family="monospace">DOOR</text>')

        # Dimension — width
        lines.append(f'<line x1="{ox}" y1="{oy+20+wh+15}" x2="{ox+ww}" y2="{oy+20+wh+15}" stroke="#0af" stroke-width="1"/>')
        lines.append(f'<text x="{ox+ww//2}" y="{oy+20+wh+28}" fill="#0af" font-size="9" text-anchor="middle" font-family="monospace">{wall_len}mm</text>')

        # Dimension — height
        lines.append(f'<line x1="{ox+ww+10}" y1="{oy+20}" x2="{ox+ww+10}" y2="{oy+20+wh}" stroke="#0af" stroke-width="1"/>')
        lines.append(f'<text x="{ox+ww+22}" y="{oy+20+wh//2}" fill="#0af" font-size="9" font-family="monospace" dominant-baseline="middle">{height_mm}mm</text>')

        # Label
        lines.append(f'<text x="{ox+ww//2}" y="{oy+14}" fill="#aaa" font-size="10" text-anchor="middle" font-family="monospace">{label}</text>')

    lines.append('</svg>')
    return "\n".join(lines)


# ============================================================
# TOP VIEW - clean overhead outline, no dimensions
# ============================================================
def generate_top_view(parsed_data):
    spaces = parsed_data.get("spaces", [])
    if not spaces:
        return "<svg><text x='50' y='50' fill='white'>No data</text></svg>"

    pad = 60
    scale = 0.06
    cols = 2
    x_offset = pad

    lines = []
    total_w = sum(int(s.get("length_mm",8000)*scale) for s in spaces) + pad*(len(spaces)+1)
    max_h = max(int(s.get("width_mm",6000)*scale) for s in spaces) + pad*2 + 40
    lines.append(f'<svg width="{total_w}" height="{max_h}" xmlns="http://www.w3.org/2000/svg" style="background:#0a0a0a">')
    lines.append(f'<text x="{total_w//2}" y="20" fill="#888" font-size="12" text-anchor="middle" font-family="monospace">TOP VIEW — LAYOUT OVERVIEW</text>')

    for space in spaces:
        length = space.get("length_mm", 8000)
        width = space.get("width_mm", 6000)
        thick = space.get("wall_thickness_mm", 200)
        name = space.get("name", "Space")
        sw = int(length * scale)
        sh = int(width * scale)
        ox = x_offset
        oy = 40

        # Outer wall
        lines.append(f'<rect x="{ox}" y="{oy}" width="{sw}" height="{sh}" fill="#222" stroke="#888" stroke-width="3"/>')
        # Inner space
        ti = int(thick * scale)
        lines.append(f'<rect x="{ox+ti}" y="{oy+ti}" width="{sw-ti*2}" height="{sh-ti*2}" fill="#111" stroke="#333" stroke-width="1"/>')

        # Compass rose
        cx = ox + sw - 20
        cy = oy + 20
        lines.append(f'<circle cx="{cx}" cy="{cy}" r="12" fill="none" stroke="#444" stroke-width="1"/>')
        lines.append(f'<text x="{cx}" y="{cy-3}" fill="#aaa" font-size="9" text-anchor="middle" font-family="monospace">N</text>')
        lines.append(f'<line x1="{cx}" y1="{cy+2}" x2="{cx}" y2="{cy-10}" stroke="#aaa" stroke-width="1"/>')

        # Space name
        lines.append(f'<text x="{ox+sw//2}" y="{oy+sh//2}" fill="#555" font-size="14" text-anchor="middle" font-family="monospace" dominant-baseline="middle">{name.upper()}</text>')
        lines.append(f'<text x="{ox+sw//2}" y="{oy+sh//2+18}" fill="#333" font-size="10" text-anchor="middle" font-family="monospace">{length}×{width}mm</text>')

        x_offset += sw + pad

    lines.append('</svg>')
    return "\n".join(lines)


# ============================================================
# ELECTRICAL PLAN - power outlets and lighting
# ============================================================
def generate_electrical_plan(parsed_data):
    spaces = parsed_data.get("spaces", [])
    if not spaces:
        return "<svg><text x='50' y='50' fill='white'>No data</text></svg>"

    pad = 80
    scale = 0.06
    x_offset = pad

    lines = []
    total_w = sum(int(s.get("length_mm",8000)*scale) for s in spaces) + pad*(len(spaces)+1)
    max_h = max(int(s.get("width_mm",6000)*scale) for s in spaces) + pad*2 + 60
    lines.append(f'<svg width="{total_w}" height="{max_h}" xmlns="http://www.w3.org/2000/svg" style="background:#0a0a0a">')
    lines.append(f'<text x="{total_w//2}" y="20" fill="#ffaa00" font-size="12" text-anchor="middle" font-family="monospace">ELECTRICAL PLAN — POWER & LIGHTING</text>')

    for space in spaces:
        length = space.get("length_mm", 8000)
        width = space.get("width_mm", 6000)
        thick = space.get("wall_thickness_mm", 200)
        name = space.get("name", "Space")
        sw = int(length * scale)
        sh = int(width * scale)
        ox = x_offset
        oy = 40
        ti = int(thick * scale)

        # Base floor plan (grey, faded)
        lines.append(f'<rect x="{ox}" y="{oy}" width="{sw}" height="{sh}" fill="none" stroke="#333" stroke-width="2"/>')
        lines.append(f'<rect x="{ox+ti}" y="{oy+ti}" width="{sw-ti*2}" height="{sh-ti*2}" fill="#0d0d0d" stroke="#222" stroke-width="1"/>')

        # Distribution board — top left corner
        dbx = ox + ti + 10
        dby = oy + ti + 10
        lines.append(f'<rect x="{dbx}" y="{dby}" width="20" height="14" fill="none" stroke="#ffaa00" stroke-width="1.5"/>')
        lines.append(f'<text x="{dbx+10}" y="{dby+10}" fill="#ffaa00" font-size="7" text-anchor="middle" font-family="monospace">DB</text>')

        # Power outlets — evenly spaced along south wall
        num_outlets = max(2, length // 2500)
        spacing = (sw - ti*2) // (num_outlets + 1)
        for j in range(1, num_outlets + 1):
            px = ox + ti + spacing * j
            py = oy + sh - ti - 8
            # Outlet symbol: circle with horizontal line
            lines.append(f'<circle cx="{px}" cy="{py}" r="6" fill="none" stroke="#ffaa00" stroke-width="1.5"/>')
            lines.append(f'<line x1="{px-4}" y1="{py}" x2="{px+4}" y2="{py}" stroke="#ffaa00" stroke-width="1"/>')
            lines.append(f'<text x="{px}" y="{py+14}" fill="#ffaa00" font-size="7" text-anchor="middle" font-family="monospace">13A</text>')

        # Cable route from DB to outlets (dashed line)
        lines.append(f'<line x1="{dbx+10}" y1="{dby+14}" x2="{ox+ti+spacing}" y2="{oy+sh-ti-8}" stroke="#ffaa00" stroke-width="0.8" stroke-dasharray="4,3" opacity="0.5"/>')

        # Ceiling lights — grid pattern
        light_rows = max(1, width // 3000)
        light_cols = max(2, length // 2500)
        lr_spacing = (sh - ti*2) // (light_rows + 1)
        lc_spacing = (sw - ti*2) // (light_cols + 1)
        for r in range(1, light_rows + 1):
            for c in range(1, light_cols + 1):
                lx = ox + ti + lc_spacing * c
                ly = oy + ti + lr_spacing * r
                # Light symbol: X in circle
                lines.append(f'<circle cx="{lx}" cy="{ly}" r="7" fill="none" stroke="#ffe066" stroke-width="1"/>')
                lines.append(f'<line x1="{lx-4}" y1="{ly-4}" x2="{lx+4}" y2="{ly+4}" stroke="#ffe066" stroke-width="1"/>')
                lines.append(f'<line x1="{lx+4}" y1="{ly-4}" x2="{lx-4}" y2="{ly+4}" stroke="#ffe066" stroke-width="1"/>')

        # Space label
        lines.append(f'<text x="{ox+sw//2}" y="{oy+sh+18}" fill="#555" font-size="10" text-anchor="middle" font-family="monospace">{name.upper()} — ELECTRICAL</text>')

        # Legend
        lx = ox + ti + 5
        ly = oy + ti + 35
        lines.append(f'<circle cx="{lx+6}" cy="{ly}" r="5" fill="none" stroke="#ffaa00" stroke-width="1.2"/>')
        lines.append(f'<line x1="{lx+2}" y1="{ly}" x2="{lx+10}" y2="{ly}" stroke="#ffaa00" stroke-width="1"/>')
        lines.append(f'<text x="{lx+16}" y="{ly+4}" fill="#888" font-size="8" font-family="monospace">Power outlet 13A</text>')
        lines.append(f'<circle cx="{lx+6}" cy="{ly+16}" r="5" fill="none" stroke="#ffe066" stroke-width="1"/>')
        lines.append(f'<text x="{lx+16}" y="{ly+20}" fill="#888" font-size="8" font-family="monospace">Ceiling light</text>')
        lines.append(f'<rect x="{lx+2}" y="{ly+29}" width="10" height="7" fill="none" stroke="#ffaa00" stroke-width="1"/>')
        lines.append(f'<text x="{lx+16}" y="{ly+36}" fill="#888" font-size="8" font-family="monospace">Distribution board</text>')

        x_offset += sw + pad

    lines.append('</svg>')
    return "\n".join(lines)


# ============================================================
# WATER PLAN - plumbing and drainage
# ============================================================
def generate_water_plan(parsed_data):
    spaces = parsed_data.get("spaces", [])
    if not spaces:
        return "<svg><text x='50' y='50' fill='white'>No data</text></svg>"

    pad = 80
    scale = 0.06
    x_offset = pad

    lines = []
    total_w = sum(int(s.get("length_mm",8000)*scale) for s in spaces) + pad*(len(spaces)+1)
    max_h = max(int(s.get("width_mm",6000)*scale) for s in spaces) + pad*2 + 60
    lines.append(f'<svg width="{total_w}" height="{max_h}" xmlns="http://www.w3.org/2000/svg" style="background:#0a0a0a">')
    lines.append(f'<text x="{total_w//2}" y="20" fill="#00aaff" font-size="12" text-anchor="middle" font-family="monospace">WATER / PLUMBING PLAN</text>')

    for space in spaces:
        length = space.get("length_mm", 8000)
        width = space.get("width_mm", 6000)
        thick = space.get("wall_thickness_mm", 200)
        name = space.get("name", "Space")
        sw = int(length * scale)
        sh = int(width * scale)
        ox = x_offset
        oy = 40
        ti = int(thick * scale)

        # Base floor plan
        lines.append(f'<rect x="{ox}" y="{oy}" width="{sw}" height="{sh}" fill="none" stroke="#333" stroke-width="2"/>')
        lines.append(f'<rect x="{ox+ti}" y="{oy+ti}" width="{sw-ti*2}" height="{sh-ti*2}" fill="#0d0d0d" stroke="#222" stroke-width="1"/>')

        # Water inlet point — bottom left
        wx = ox + ti + 20
        wy = oy + sh - ti - 20
        lines.append(f'<circle cx="{wx}" cy="{wy}" r="8" fill="none" stroke="#00aaff" stroke-width="2"/>')
        lines.append(f'<text x="{wx}" y="{wy+4}" fill="#00aaff" font-size="7" text-anchor="middle" font-family="monospace">W</text>')
        lines.append(f'<text x="{wx}" y="{wy+18}" fill="#00aaff" font-size="7" text-anchor="middle" font-family="monospace">INLET</text>')

        # Drain point — centre
        dx = ox + sw // 2
        dy = oy + sh - ti - 20
        lines.append(f'<circle cx="{dx}" cy="{dy}" r="8" fill="none" stroke="#00ffaa" stroke-width="2"/>')
        lines.append(f'<line x1="{dx-5}" y1="{dy-5}" x2="{dx+5}" y2="{dy+5}" stroke="#00ffaa" stroke-width="1.5"/>')
        lines.append(f'<line x1="{dx+5}" y1="{dy-5}" x2="{dx-5}" y2="{dy+5}" stroke="#00ffaa" stroke-width="1.5"/>')
        lines.append(f'<text x="{dx}" y="{dy+18}" fill="#00ffaa" font-size="7" text-anchor="middle" font-family="monospace">DRAIN</text>')

        # Sink unit — top right area
        sx = ox + sw - ti - 40
        sy = oy + ti + 20
        lines.append(f'<rect x="{sx}" y="{sy}" width="30" height="20" fill="none" stroke="#00aaff" stroke-width="1.5"/>')
        lines.append(f'<circle cx="{sx+15}" cy="{sy+10}" r="5" fill="none" stroke="#00aaff" stroke-width="1"/>')
        lines.append(f'<text x="{sx+15}" y="{sy+30}" fill="#00aaff" font-size="7" text-anchor="middle" font-family="monospace">SINK</text>')

        # Supply pipe — blue dashed
        lines.append(f'<line x1="{wx}" y1="{wy}" x2="{sx+15}" y2="{sy+20}" stroke="#00aaff" stroke-width="1.5" stroke-dasharray="5,3"/>')
        # Drain pipe — green dashed
        lines.append(f'<line x1="{dx}" y1="{dy}" x2="{sx+15}" y2="{sy+20}" stroke="#00ffaa" stroke-width="1.5" stroke-dasharray="5,3"/>')

        # Legend
        lx = ox + ti + 5
        ly = oy + ti + 10
        lines.append(f'<circle cx="{lx+6}" cy="{ly}" r="5" fill="none" stroke="#00aaff" stroke-width="1.5"/>')
        lines.append(f'<text x="{lx+16}" y="{ly+4}" fill="#888" font-size="8" font-family="monospace">Water inlet</text>')
        lines.append(f'<circle cx="{lx+6}" cy="{ly+14}" r="5" fill="none" stroke="#00ffaa" stroke-width="1.5"/>')
        lines.append(f'<text x="{lx+16}" y="{ly+18}" fill="#888" font-size="8" font-family="monospace">Drain point</text>')
        lines.append(f'<line x1="{lx+2}" y1="{ly+28}" x2="{lx+12}" y2="{ly+28}" stroke="#00aaff" stroke-width="1.5" stroke-dasharray="3,2"/>')
        lines.append(f'<text x="{lx+16}" y="{ly+32}" fill="#888" font-size="8" font-family="monospace">Supply pipe</text>')
        lines.append(f'<line x1="{lx+2}" y1="{ly+42}" x2="{lx+12}" y2="{ly+42}" stroke="#00ffaa" stroke-width="1.5" stroke-dasharray="3,2"/>')
        lines.append(f'<text x="{lx+16}" y="{ly+46}" fill="#888" font-size="8" font-family="monospace">Drain pipe</text>')

        lines.append(f'<text x="{ox+sw//2}" y="{oy+sh+18}" fill="#555" font-size="10" text-anchor="middle" font-family="monospace">{name.upper()} — PLUMBING</text>')
        x_offset += sw + pad

    lines.append('</svg>')
    return "\n".join(lines)


# ============================================================
# RIGGING PLAN - ceiling suspension points and loads
# ============================================================
def generate_rigging_plan(parsed_data):
    spaces = parsed_data.get("spaces", [])
    if not spaces:
        return "<svg><text x='50' y='50' fill='white'>No data</text></svg>"

    pad = 80
    scale = 0.06
    x_offset = pad

    lines = []
    total_w = sum(int(s.get("length_mm",8000)*scale) for s in spaces) + pad*(len(spaces)+1)
    max_h = max(int(s.get("width_mm",6000)*scale) for s in spaces) + pad*2 + 100
    lines.append(f'<svg width="{total_w}" height="{max_h}" xmlns="http://www.w3.org/2000/svg" style="background:#0a0a0a">')
    lines.append(f'<text x="{total_w//2}" y="16" fill="#ff6600" font-size="12" text-anchor="middle" font-family="monospace">RIGGING PLAN — SUSPENSION POINTS & LOADS</text>')
    lines.append(f'<text x="{total_w//2}" y="30" fill="#ff3300" font-size="9" text-anchor="middle" font-family="monospace">⚠ FOR PLANNING ONLY — ALL RIGGING MUST BE APPROVED BY VENUE TECHNICAL MANAGER</text>')

    for space in spaces:
        length = space.get("length_mm", 8000)
        width = space.get("width_mm", 6000)
        thick = space.get("wall_thickness_mm", 200)
        name = space.get("name", "Space")
        sw = int(length * scale)
        sh = int(width * scale)
        ox = x_offset
        oy = 45
        ti = int(thick * scale)

        # Base floor plan
        lines.append(f'<rect x="{ox}" y="{oy}" width="{sw}" height="{sh}" fill="none" stroke="#333" stroke-width="2"/>')
        lines.append(f'<rect x="{ox+ti}" y="{oy+ti}" width="{sw-ti*2}" height="{sh-ti*2}" fill="#0d0d0d" stroke="#222" stroke-width="1"/>')

        # Ceiling grid lines — 3000mm spacing
        grid_mm = 3000
        grid_px = int(grid_mm * scale)
        gx = ox + ti
        while gx < ox + sw - ti:
            lines.append(f'<line x1="{gx}" y1="{oy+ti}" x2="{gx}" y2="{oy+sh-ti}" stroke="#1a1a1a" stroke-width="1" stroke-dasharray="3,3"/>')
            gx += grid_px
        gy = oy + ti
        while gy < oy + sh - ti:
            lines.append(f'<line x1="{ox+ti}" y1="{gy}" x2="{ox+sw-ti}" y2="{gy}" stroke="#1a1a1a" stroke-width="1" stroke-dasharray="3,3"/>')
            gy += grid_px

        # Rigging points — at grid intersections
        rigging_points = []
        cols_r = max(2, length // 3000)
        rows_r = max(2, width // 3000)
        col_sp = (sw - ti*2) // (cols_r + 1)
        row_sp = (sh - ti*2) // (rows_r + 1)
        load_per_point = 150

        point_num = 1
        for r in range(1, rows_r + 1):
            for c in range(1, cols_r + 1):
                rpx = ox + ti + col_sp * c
                rpy = oy + ti + row_sp * r
                rigging_points.append((rpx, rpy, point_num, load_per_point))

                # Rigging symbol: X inside circle
                lines.append(f'<circle cx="{rpx}" cy="{rpy}" r="9" fill="none" stroke="#ff6600" stroke-width="2"/>')
                lines.append(f'<line x1="{rpx-6}" y1="{rpy-6}" x2="{rpx+6}" y2="{rpy+6}" stroke="#ff6600" stroke-width="1.5"/>')
                lines.append(f'<line x1="{rpx+6}" y1="{rpy-6}" x2="{rpx-6}" y2="{rpy+6}" stroke="#ff6600" stroke-width="1.5"/>')
                lines.append(f'<text x="{rpx+12}" y="{rpy-6}" fill="#ff6600" font-size="8" font-family="monospace">R{point_num}</text>')
                lines.append(f'<text x="{rpx+12}" y="{rpy+6}" fill="#888" font-size="7" font-family="monospace">{load_per_point}kg</text>')
                point_num += 1

        # Load table below drawing
        total_load = len(rigging_points) * load_per_point
        ty = oy + sh + 18
        lines.append(f'<text x="{ox}" y="{ty}" fill="#ff6600" font-size="9" font-family="monospace">RIGGING SCHEDULE — {name.upper()}</text>')
        lines.append(f'<text x="{ox}" y="{ty+14}" fill="#666" font-size="8" font-family="monospace">Points: {len(rigging_points)}   Load per point: {load_per_point}kg   Total: {total_load}kg   Grid: {grid_mm}mm</text>')
        lines.append(f'<text x="{ox}" y="{ty+26}" fill="#ff3300" font-size="8" font-family="monospace">Max permitted: 300kg/point (COEX) / 500kg/point (BEXCO)</text>')

        # Legend
        lx = ox + sw - 100
        ly = oy + ti + 10
        lines.append(f'<circle cx="{lx+6}" cy="{ly}" r="6" fill="none" stroke="#ff6600" stroke-width="1.5"/>')
        lines.append(f'<line x1="{lx+2}" y1="{ly-4}" x2="{lx+10}" y2="{ly+4}" stroke="#ff6600" stroke-width="1"/>')
        lines.append(f'<line x1="{lx+10}" y1="{ly-4}" x2="{lx+2}" y2="{ly+4}" stroke="#ff6600" stroke-width="1"/>')
        lines.append(f'<text x="{lx+16}" y="{ly+4}" fill="#888" font-size="7" font-family="monospace">Rigging point</text>')

        x_offset += sw + pad
    


    lines.append('</svg>')
    return "\n".join(lines)

