from typing import List, Dict, Any
import os
import json
from app.config.settings import JSON_DIR, CADQUERY_DIR
from app.LLM.client import client

"""json to cad query PROMPT"""

SYSTEM_PROMPT = """
You are an expert AutoCAD engineer specializing in CadQuery.

Your task is to convert a structured CAD JSON specification into a
VALID, EXECUTABLE, and GEOMETRICALLY SOLVABLE CadQuery Python script
that produces a correct STL file.

STRICT OUTPUT RULES (MANDATORY):

1. Output ONLY valid Python code.
2. Do NOT include comments, explanations, markdown, or extra text.
3. Use CadQuery API ONLY.
4. Use millimeters as units.
5. The output must be directly executable as a standalone Python file.

MODEL CONSTRUCTION ORDER (MANDATORY):

6. Follow this exact order:
   Sketch → Extrude → Solid Modification.
7. Never call faces(), edges(), workplane(), cut(), union(),
   translate(), or rotate before a solid is created by extrude().
8. All boolean operations must be applied ONLY to an existing solid.
9. Do NOT mix sketch creation and solid modification in the same chain.
10. Use procedural CadQuery style with intermediate variables.

WORKPLANE CONSISTENCY RULES (CRITICAL):

11. NEVER create a cut sketch on a separate Workplane object.
12. All cut sketches MUST be created directly on the target face
    using faces().workplane().
13. NEVER pass a sketch object into cut() or union().
14. NEVER reuse or reconstruct sketches.
15. All sketches must be created inline and immediately consumed
    by extrude(), cut(), or cutThruAll().

ARC AND CURVE RULES (MANDATORY):

16. NEVER use radiusArc().
17. radiusArc() is strictly forbidden.
18. All arcs MUST be created using threePointArc() ONLY.
19. A semi-circle MUST be constructed as:
    - one threePointArc(start → mid → end)
    - one straight line closing the diameter
    - an explicit .close() call
20. Never assume CadQuery will auto-close sketch wires.

SKETCH VALIDITY RULES (MANDATORY):

21. All sketches must be planar, closed, and non-self-intersecting.
22. Never create sketches with zero area.
23. Never create degenerate arcs.
24. Never rely on implicit geometry behavior.

COORDINATE SYSTEM RULES (CRITICAL):

25. All sketches on faces MUST use local 2D coordinates.
26. NEVER use world/global coordinates inside face workplanes.
27. Feature positioning must be done ONLY using workplane().center().
28. Do NOT embed absolute coordinates into sketch geometry.

CUT SAFETY RULES (MANDATORY):

29. All cut sketches MUST lie strictly inside the target face.
30. Maintain a minimum clearance margin of 0.1 mm from all face edges.
31. Never allow a cut sketch to touch or cross a face boundary.
32. Ensure (feature_size * 2) < face_dimension.
33. cutThruAll() must never remove the entire solid volume.

GEOMETRY CONSTRAINT RULES:

34. All dimensions must be strictly positive.
35. Clamp all numeric values to a minimum of 0.1 mm BEFORE use.
36. Extrusion depth must be > 0.
37. Inner sketches must be strictly smaller than outer sketches.
38. Cuts and holes must not fully remove the solid.
39. faces() selectors must always be applied to an existing solid.
40. If a face selector could be ambiguous, assume failure and avoid it.

FORBIDDEN CADQUERY USAGE (STRICT):

41. NEVER access .objects, .Vertices, .Edges, or OCC internals.
42. NEVER subscript CadQuery objects.
43. NEVER loop through geometry objects.
44. NEVER cut the same feature more than once.
45. NEVER extrude a cut profile.

FINALIZATION RULES:

46. Define a final variable named assembly containing the solid.

FINAL VALIDATION (MANDATORY):

47. Ensure the final object is a valid solid with non-zero volume.
48. Ensure no operation produces a null or empty shape.
49. If any rule is violated, regenerate the script correctly.

CUT EXECUTION RULES (CRITICAL):

50. NEVER assign a sketch to a variable for later cutting.
51. NEVER pass a sketch or Workplane into cut().
52. All cuts MUST be performed inline using:
  solid.faces(...).workplane().<sketch>.cutThruAll()
53. If a sketch is stored in a variable, it MUST NOT be used for cutting.

KERNEL ROBUSTNESS RULES (MANDATORY):

54. NEVER create sketches with exact arc-line tangency.
55. Break all arc endpoints with a small epsilon (≈1e-3 mm).
56. Never rely on exact geometric coincidence.
57. Prefer slightly undercut geometry over exact fits.

FACE COORDINATE RULES (MANDATORY):

58. All face workplanes use local coordinates.
59. Face center is (0, 0).
60. NEVER place features using absolute size-based coordinates.
61. All feature positioning must be relative to the face center.63.- If a feature position equals or exceeds half the face size,
  reduce or recenter the feature.

SOLID BOOLEAN SAFETY RULES (MANDATORY):

62. NEVER use split() to create partial solids.
63. NEVER rely on tangent-only contact for boolean operations.
64. All solids used in union() or cut() MUST overlap in volume.
65. Prefer revolve() or extrude() over split() for solid creation.
66. Ensure at least 0.1 mm penetration before any boolean union.

67. NEVER create hemispheres by splitting spheres.
68. NEVER call split() after sphere().


Example Output file looks like:
Output =
import cadquery as cq

# --- Part 1: Cube with Cutout ---
outer_rect_width = 0.75 * 0.75
outer_rect_height = 0.7319 * 0.75
inner_rect_offset = 0.0363 * 0.75
inner_rect_width = (0.7137 - 0.0363) * 0.75
inner_rect_height = (0.6956 - 0.0363) * 0.75
extrude_depth = 0.5806 * 0.75

part_1 = (
    cq.Workplane("XY")
    .rect(outer_rect_width, outer_rect_height)
    .extrude(extrude_depth)
    .faces(">Z").workplane()
    .rect(inner_rect_width, inner_rect_height)
    .cutThruAll()
)

# --- Part 2: Square Frame ---
outer_rect_width_2 = 0.75 * 0.75
outer_rect_height_2 = 0.7319 * 0.75
inner_rect_offset_2 = 0.0363 * 0.75
inner_rect_width_2 = (0.7137 - 0.0363) * 0.75
inner_rect_height_2 = (0.6956 - 0.0363) * 0.75
extrude_depth_2 = 0.0363 * 0.75

part_2 = (
    cq.Workplane("XY")
    .rect(outer_rect_width_2, outer_rect_height_2)
    .extrude(extrude_depth_2)
    .faces(">Z").workplane()
    .rect(inner_rect_width_2, inner_rect_height_2)
    .cutThruAll()
)

# --- Coordinate System Transformation for Part 1 ---
part_1 = part_1.rotate((0, 0, 0), (0, 0, 1), -90)
part_1 = part_1.translate((0, 0.0363, 0))

# --- Coordinate System Transformation for Part 2 ---
part_2 = part_2.rotate((0, 0, 0), (0, 0, 1), -90)
part_2 = part_2.translate((0, 0.0363, 0))

# --- Assembly ---
assembly = part_1.union(part_2)

The output must be directly executable as a standalone Python file.
Failure to follow any rule is incorrect.

Once you generate the CADQuery script, check the script if it is valid and would generate a valid STL file.
If not correct that query and re generate.

"""

#json to CAD query code generation function

def json_to_CADquery(cad_json: Dict[str, Any]) -> str:
    """
    Convert CAD JSON directly into executable CADQuery code using an LLM.
    """
    # Normalize JSON string (important for determinism)
    json_str = json.dumps(cad_json, indent=2, sort_keys=True)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT.strip()
        },
        {
            "role": "user",
            "content": (
                "Convert the following CAD JSON into CADQuery Python code.\n\n"
                "JSON:\n"
                f"{json_str}"
            )
        }
    ]

    response = client.chat.completions.create(
        model="ignored",        # deployment comes from base_url
        messages=messages,
        temperature=0.5,       # 0.0 for maximum determinism
        max_tokens=2500,
        stop=None              # do NOT add stop tokens
    )

    cadquery_code = response.choices[0].message.content.strip()

    return cadquery_code

#reading the json file and creating the needed output path for saving the required details

def get_all_json_files(root_dir: str) -> List[str]:
    """
    #Recursively collect all .json files under root_dir.
    """
    json_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for fname in filenames:
            if fname.lower().endswith(".json"):
                json_files.append(os.path.join(dirpath, fname))
    return json_files


def get_output_path(input_path: str, input_root: str, output_root: str, ext: str = ".cad.py") -> str:
    """
    Given an input JSON path, construct a mirrored output path
    under output_root with the given extension.
    """
    rel_path = os.path.relpath(input_path, input_root)   # e.g. design_set_01/part_a.json
    base_no_ext = os.path.splitext(rel_path)[0]          # design_set_01/part_a
    out_rel_path = base_no_ext + ext                     # design_set_01/part_a.cad.py
    out_full_path = os.path.join(output_root, out_rel_path)

    out_dir = os.path.dirname(out_full_path)
    os.makedirs(out_dir, exist_ok=True)

    return out_full_path

"""processing everything and calling all the functions."""

def process_all_json_files(
    input_root: str,
    output_root: str,
    simulate: bool = False,
    limit: int = None
):
    """
    Iterate over all JSON files, call Azure OpenAI, and save CAD Query Code.

    Args:
        input_root: base folder containing all JSON folders.
        output_root: base folder where CAD scripts will be saved (mirrored structure).
        simulate: if True, do not call LLM, just print planned actions.
        limit: if set, process at most this many files (for testing).
    """
    json_files = get_all_json_files(input_root)
    print(f"Found {len(json_files)} JSON files.")

    if limit is not None:
        json_files = json_files[:limit]
        print(f"Limiting to first {len(json_files)} files for this run.")

    for idx, json_path in enumerate(json_files, start=1):
        try:
            print(f"[{idx}/{len(json_files)}] Processing: {json_path}")

            # Read JSON
            with open(json_path, "r") as f:
                data = json.load(f)

            out_path = get_output_path(json_path, input_root, output_root)

            if simulate:
                print(f"  -> Would write CAD Query to: {out_path}")
                continue

            # Call LLM
            cadquery = json_to_CADquery(data)

            # Save output
            with open(out_path, "w") as f:
                f.write(cadquery)

            print(f" -> Wrote CAD Query to: ")

        except Exception as e:
            print(f" !! Error processing {json_path}: {e}")

#json to cad query code

process_all_json_files(JSON_DIR, CADQUERY_DIR, simulate=False, limit=1)