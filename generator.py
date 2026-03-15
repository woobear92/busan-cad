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