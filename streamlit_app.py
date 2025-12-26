import streamlit as st
import os
import shutil

from app.pipeline.orchastrator import (
    generate_cad_from_text,
    refine_existing_design
)
from app.config.settings import JSON_DIR, STL_DIR, CADQUERY_DIR
import streamlit.components.v1 as components
import base64

def render_stl_viewer(stl_path, height=500):
    """
    Renders an interactive 3D STL viewer inside Streamlit
    """
    with open(stl_path, "rb") as f:
        stl_bytes = f.read()

    b64 = base64.b64encode(stl_bytes).decode()

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://unpkg.com/three@0.128.0/build/three.min.js"></script>
        <script src="https://unpkg.com/three@0.128.0/examples/js/loaders/STLLoader.js"></script>
        <script src="https://unpkg.com/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    </head>
    <body style="margin:0">
        <div id="viewer"></div>
        <script>
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0xf0f0f0);

            const camera = new THREE.PerspectiveCamera(
                60, window.innerWidth / {height}, 0.1, 1000
            );
            camera.position.set(0, 0, 100);

            const renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(window.innerWidth, {height});
            document.getElementById("viewer").appendChild(renderer.domElement);

            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;

            const light1 = new THREE.DirectionalLight(0xffffff, 1);
            light1.position.set(1, 1, 1).normalize();
            scene.add(light1);

            const light2 = new THREE.AmbientLight(0x404040);
            scene.add(light2);

            const loader = new THREE.STLLoader();
            const geometry = loader.parse(
                Uint8Array.from(atob("{b64}"), c => c.charCodeAt(0)).buffer
            );

            geometry.center();

            const material = new THREE.MeshStandardMaterial({{
                color: 0x0077be,
                metalness: 0.2,
                roughness: 0.6
            }});

            const mesh = new THREE.Mesh(geometry, material);
            scene.add(mesh);

            function animate() {{
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
            }}

            animate();
        </script>
    </body>
    </html>
    """

    components.html(html, height=height)


# ==========================================================
# Session State
# ==========================================================
if "active_design" not in st.session_state:
    st.session_state.active_design = None  # dict with paths

if "stage" not in st.session_state:
    st.session_state.stage = "initial"  # initial | modify | terminate


# ==========================================================
# Page Setup
# ==========================================================
st.set_page_config(page_title="Text to CAD Generator", layout="centered")
st.title("🧱 Text → CAD → STL Generator")


# ==========================================================
# STAGE 1 — INITIAL DESIGN CREATION
# ==========================================================
if st.session_state.stage == "initial":

    st.header("Create Your CAD Design")

    description = st.text_area(
        "Design description",
        placeholder="Example: Create a square plate with a circular hole in the center"
    )

    if st.button("Generate Design"):
        if not description.strip():
            st.warning("Please enter a design description.")
        else:
            with st.spinner("Generating CAD design..."):
                result = generate_cad_from_text(description)

            st.session_state.active_design = result
            st.session_state.stage = "modify"
            st.success("Design generated successfully!")
          


# ==========================================================
# STAGE 2 — MODIFY + REVIEW
# ==========================================================
if st.session_state.stage == "modify":

    st.header("Review Current Design")

    stl_dir = st.session_state.active_design["stl_dir"]
    stl_files = [
        f for f in os.listdir(stl_dir)
        if f.lower().endswith(".stl")
    ]

    if not stl_files:
        st.warning("No STL file found yet.")
        st.stop()

    stl_files.sort(key=lambda f: os.path.getmtime(os.path.join(stl_dir, f)))
    stl_path = os.path.join(stl_dir, stl_files[-1])
    
    # ---- 3D STL Preview (ADD HERE)
    st.subheader("🔍 3D Preview (Interactive)")
    render_stl_viewer(stl_path, height=500)


    cadquery_dir = st.session_state.active_design.get("cadquery_dir")

    if not cadquery_dir or not os.path.isdir(cadquery_dir):
        st.error("CADQuery directory not found.")
        st.stop()

    cad_files = [
        f for f in os.listdir(cadquery_dir)
        if f.endswith(".py")
    ]

    if not cad_files:
        st.warning("No CADQuery file generated yet.")
        st.stop()

    cad_files.sort(key=lambda f: os.path.getmtime(os.path.join(cadquery_dir, f)))
    cad_path = os.path.join(cadquery_dir, cad_files[-1])


    # ---- STL Preview (downloadable)
    if os.path.exists(stl_path):
        with open(stl_path, "rb") as f:
            st.download_button(
                "⬇️ Download Current STL",
                data=f,
                file_name=os.path.basename(stl_path),
                mime="application/sla"
            )

    if os.path.exists(cad_path):
        with open(cad_path, "rb") as f:
            st.download_button(
                "⬇️ Download CADQuery Script",
                data=f,
                file_name=os.path.basename(cad_path),
                mime="text/plain"
            )

    st.divider()

    # ---- Modification
    st.subheader("Modify Design")

    modification = st.text_area(
        "Modification instruction",
        placeholder="Example: Add a semicircular cut on the top edge"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Apply Modification"):
            if not modification.strip():
                st.warning("Please enter a modification instruction.")
            else:
                with st.spinner("Applying modification..."):
                    refine_existing_design(
                        st.session_state.active_design["json_path"],
                        modification   
                    )
                    
                st.success("Modification applied!")
            #st.rerun()

    with col2:
        if st.button("Terminate Design"):
            st.session_state.stage = "terminate"


# ==========================================================
# STAGE 3 — FINALIZE + CLEANUP
# ==========================================================
if st.session_state.stage == "terminate":

    st.header("Finalize Design")

    design = st.session_state.active_design

    # ---- Final Downloads
    if os.path.exists(design["stl_dir"]):
        stl_dir = design["stl_dir"]
        stl_files = [
            f for f in os.listdir(stl_dir)
            if f.lower().endswith(".stl")
        ]

        if not stl_files:
            st.error("No STL file found.")
            st.stop()

        # pick latest STL
        stl_files.sort(key=lambda f: os.path.getmtime(os.path.join(stl_dir, f)))
        stl_path = os.path.join(stl_dir, stl_files[-1])

        st.subheader("🔍 Final Design Preview")
        render_stl_viewer(stl_path, height=500)

        with open(stl_path, "rb") as f:
            st.download_button(
                "Download STL",
                data=f,
                file_name=os.path.basename(stl_path),
                mime="application/sla"
            )


    if os.path.exists(design["cadquery_dir"]):
        cadquery_dir = design["cadquery_dir"]

        cad_files = [
            f for f in os.listdir(cadquery_dir)
            if f.lower().endswith(".py")
        ]

        if not cad_files:
            st.error("No CADQuery file found.")
            st.stop()

        # Pick the latest generated CADQuery file
        cad_files.sort(key=lambda f: os.path.getmtime(os.path.join(cadquery_dir, f)))
        cadquery_path = os.path.join(cadquery_dir, cad_files[-1])

        with open(cadquery_path, "rb") as f:
            st.download_button(
                "Download CADQuery Script",
                data=f,
                file_name=os.path.basename(cadquery_path),
                mime="text/plain"
            )


    st.divider()

    # ---- Cleanup
    if st.button("Start New Design (Clean Workspace)"):

        for folder in [JSON_DIR, CADQUERY_DIR, STL_DIR]:
            if os.path.exists(folder):
                shutil.rmtree(folder)
                os.makedirs(folder, exist_ok=True)

        st.session_state.active_design = None
        st.session_state.stage = "initial"

        st.success("Workspace cleared. Ready for a new design.")
        st.rerun()