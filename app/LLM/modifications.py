
import json, os
from typing import Dict
from datetime import datetime
from app.cad.json_to_cadquery import process_all_json_files
from app.cad.cadquery_to_stl import process_all_cadquery_files
from app.LLM.client import client
JSON_REFINER_SYSTEM_PROMPT = """
You are a AutoCAD JSON editor.

Your task:
- Modify the given CAD JSON to reflect the user's requested change.
- Preserve the original schema and structure.
- Change ONLY what is necessary.
- Do NOT invent new fields.
- Do NOT remove unrelated geometry.
- Units are millimeters.
- Follow operation order:
  Sketch → Extrude → Solid modification

Targeting rules:
- Every modification MUST identify a specific target:
  - sketch
  - extrude
  - or one feature inside "features"
- Feature targets MUST be matched by type, shape, and key dimensions.
- If multiple matches exist, modify the closest match.

Modification rules:
- If a shape type changes, REPLACE the shape.
- If only dimensions change, MODIFY dimensions only.
- Do NOT explain or justify changes.

Output rules (CRITICAL):
- Output ONLY ONE JSON object.
- The output MUST start with '{' and end with '}'.
- Do NOT include explanations, comments, or text.
- Do NOT include markdown.
- If the target is ambiguous, choose the closest match and still output JSON.

Here is an Example Modified JSON:
{
  "existing_design": {
    "sketch": {
      "type": "square",
      "size": 20
    },
    "extrude": {
      "height": 2
    },
    "features": [
      {
        "type": "cut",
        "shape": "circle",
        "dimensions": {
          "radius": 0.5,
          "position_x": 10,
          "position_y": 10,
          "height": 2
        }
      },
      {
        "type": "add",
        "shape": "cube",
        "dimensions": {
          "size": 1,
          "position_x": 0,
          "position_y": 0,
          "position_z": 2
        }
      }
    ],
    "export_format": "stl"
  }
}

"""



def modify_design_json(
    existing_json: Dict,
    modification_text: str
) -> Dict:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": JSON_REFINER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps({
                    "existing_design": existing_json,
                    "requested_modification": modification_text
                })
            }
        ],
        temperature=0
    )

    refined_json_str = response.choices[0].message.content.strip()
    return json.loads(refined_json_str)

def refine_existing_design(
    existing_json_path: str,
    modification_text: str,
    JSON_ROOT: str,
    CQ_CODE_DIR: str,
    STL_DIR: str,
    client
):
    # 1. Load existing design
    with open(existing_json_path, "r") as f:
        design_json = json.load(f)

    # 2. Modify JSON using LLM
    updated_json = modify_design_json(
        existing_json=design_json,
        modification_text=modification_text,
        client=client
    )

    # 3. Overwrite JSON (or save versioned copy if you prefer)
    with open(existing_json_path, "w") as f:
        json.dump(updated_json, f, indent=2)

    # 4. Regenerate CADQuery code from updated JSON
    process_all_json_files(
        JSON_ROOT=JSON_ROOT,
        OUTPUT_ROOT=CQ_CODE_DIR,
        limit=1
    )

    # 5. Regenerate STL
    process_all_cadquery_files(
        CQ_CODE_DIR=CQ_CODE_DIR,
        STL_DIR=STL_DIR
    )

def save_versioned_json(json_data, original_path):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_path = original_path.replace(".json", f"_v{ts}.json")
    with open(new_path, "w") as f:
        json.dump(json_data, f, indent=2)
    return new_path