from parser import parse_brief
from generator import generate_dxf
import json

def text_to_dxf(description):
    print("\n" + "="*50)
    print("STEP 1: Reading your description...")
    print("="*50)
    parsed = parse_brief(description)
    
    if "error" in parsed:
        print(f"Could not understand: {parsed['error']}")
        return None
    
    print("\nExtracted dimensions:")
    for space in parsed["spaces"]:
        print(f"  {space['name']}: {space['length_mm']}mm x {space['width_mm']}mm")
        print(f"  Walls: {space['wall_thickness_mm']}mm thick")
        print(f"  Doors: {len(space['doors'])}")
    
    print("\n" + "="*50)
    print("STEP 2: Drawing your floor plan...")
    print("="*50)
    dxf_path = generate_dxf(parsed)
    
    if dxf_path:
        print("\n" + "="*50)
        print("DONE! Your CAD file is ready.")
        print("="*50)
        print(f"File saved: {dxf_path}")
        print("\nOpen it at: https://app.autodeskformats.com")
    
    return dxf_path

# ── TYPE YOUR OWN DESCRIPTION HERE ──────────────────────
if __name__ == "__main__":
    my_description = """
    Create an exhibition booth for BEXCO Busan.
    Main hall: 20 metres long, 15 metres wide.
    Walls 200mm thick.
    Two doors on the south wall, each 1200mm wide,
    positioned 3 metres from each corner.
    Small storage room: 4 metres by 3 metres
    attached to the north wall on the right side.
    """
    
    text_to_dxf(my_description)