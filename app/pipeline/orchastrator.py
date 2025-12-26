
import json
import uuid
import os
from app.config.settings import JSON_DIR, CADQUERY_DIR, STL_DIR
from app.cad.json_to_cadquery import process_all_json_files
from app.cad.cadquery_to_stl import process_all_cadquery_files
from app.LLM.modifications import modify_design_json
from app.LLM.text_to_json import text_to_json

def generate_cad_from_text(user_description: str):
    """
    Full pipeline:
    Text → JSON → CADQuery → STL

    Returns:
        dict with paths to generated artifacts
    """

    design_id = str(uuid.uuid4())[:8]

    # -------------------------------
    # 1. Text → JSON
    # -------------------------------
    cad_json = text_to_json(user_description)

    json_path = os.path.join(JSON_DIR, f"{design_id}.json")
    with open(json_path, "w") as f:
        json.dump(cad_json, f, indent=2)

    # -------------------------------
    # 2. JSON → CADQuery
    # -------------------------------
    process_all_json_files(
        JSON_DIR,
        CADQUERY_DIR,
        simulate=False,
        limit=1
    )

    # -------------------------------
    # 3. CADQuery → STL
    # -------------------------------
    process_all_cadquery_files(
        CADQUERY_DIR,
        STL_DIR
    )

    return {
        "design_id": design_id,
        "json_path": json_path,
        "cadquery_dir": CADQUERY_DIR,
        "stl_dir": STL_DIR
    }

#result = generate_cad_from_text(input("\n\n Give Description for the Design you want"))
#result


def refine_existing_design(
    existing_json_path: str,
    modification_text: str
):
    with open(existing_json_path) as f:
        design_json = json.load(f)

    updated_json = modify_design_json(design_json, modification_text)

    with open(existing_json_path, "w") as f:
        json.dump(updated_json, f, indent=2)

    process_all_json_files(JSON_DIR, CADQUERY_DIR, limit=1)
    process_all_cadquery_files(CADQUERY_DIR, STL_DIR)

"""add a half circle on top of the square plate.

"""

#json_path = result["json_path"]
#refine_existing_design("/content/drive/MyDrive/CQ_llm_project/json/a69fe245.json", input("Enter the Modifications.\n\n"))