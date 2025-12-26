import os
import cadquery as cq
from app.config.settings import CADQUERY_DIR, STL_DIR

def process_single_cadquery_file(file_path, stl_path):
    """Processes a single CadQuery Python file, executes it, and exports the resulting model to an STL file."""
    print(f"Processing: {os.path.basename(file_path)}")

    # Execution namespace
    exec_globals = {
        "__file__": file_path,
        "cq": cq
    }

    try:
        # Execute the CadQuery code
        with open(file_path, "r") as f:
            exec(f.read(), exec_globals)

        # Retrieve the CAD object
        model = None
        if "assembly" in exec_globals:
            model = exec_globals["assembly"]
        elif "solid" in exec_globals:
            model = exec_globals["solid"]

        if model is None:
            raise ValueError("No 'assembly' or 'solid' variable found in the CadQuery script.")

        # Export STL
        cq.exporters.export(model, stl_path)
        print(f" STL saved \u2192 {stl_path}")

    except Exception as e:
        print(f" Failed for {os.path.basename(file_path)}: {e}")

def process_all_cadquery_files(cq_code_dir, stl_dir):
    """Iterates through CadQuery Python files in a directory and processes each one.

    Args:
        cq_code_dir (str): Path to the directory containing CadQuery Python files.
        stl_dir (str): Path to the directory where output STL files should be saved.
    """
    print(f"\nProcessing CadQuery files from: {cq_code_dir}")
    for file_name in os.listdir(cq_code_dir):
        if not file_name.endswith(".py"):
            continue

        file_path = os.path.join(cq_code_dir, file_name)
        base_name = os.path.splitext(file_name)[0]
        stl_path = os.path.join(stl_dir, f"{base_name}.stl")
        process_single_cadquery_file(file_path, stl_path)
        
# Process all CadQuery files using the new functions
#process_all_cadquery_files(CADQUERY_DIR, STL_DIR)