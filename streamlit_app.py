import streamlit as st
import os
import shutil
import base64
import streamlit.components.v1 as components

from app.pipeline.orchastrator import (
    generate_cad_from_text,
    refine_existing_design
)
from app.config.settings import JSON_DIR, STL_DIR, CADQUERY_DIR

# ==========================================================
# STL VIEWER
# ==========================================================
def render_stl_viewer(stl_path, height=200):
    with open(stl_path, "rb") as f:
        stl_bytes = f.read()

    b64 = base64.b64encode(stl_bytes).decode()

    html = f"""
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
            scene.background = new THREE.Color(0xf4f4f4);

            const camera = new THREE.PerspectiveCamera(60, window.innerWidth/{height}, 0.1, 1000);
            camera.position.set(0, 0, 100);

            const renderer = new THREE.WebGLRenderer({{antialias:true}});
            renderer.setSize(window.innerWidth, {height});
            document.getElementById("viewer").appendChild(renderer.domElement);

            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;

            scene.add(new THREE.AmbientLight(0x404040));
            const light = new THREE.DirectionalLight(0xffffff, 1);
            light.position.set(1,1,1);
            scene.add(light);

            const loader = new THREE.STLLoader();
            const geometry = loader.parse(
                Uint8Array.from(atob("{b64}"), c => c.charCodeAt(0)).buffer
            );
            geometry.center();

            const material = new THREE.MeshStandardMaterial({{
                color: 0x0077be,
                roughness: 0.6,
                metalness: 0.2
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
# SESSION STATE
# ==========================================================
if "stage" not in st.session_state:
    st.session_state.stage = "initial"

if "design" not in st.session_state:
    st.session_state.design = None

if "terminate_popup" not in st.session_state:
    st.session_state.terminate_popup = False


# ==========================================================
# PAGE CONFIG
# ==========================================================
st.set_page_config("Text to CAD Generator", layout="centered")
st.title("🧱 Text → CAD Generator")


# ==========================================================
# STAGE 1 — INITIAL INPUT
# ==========================================================
if st.session_state.stage == "initial":

    st.subheader("Initial Design Description")

    description = st.text_area(
        "Describe your CAD design",
        placeholder="Example: Square plate with a circular hole in the center"
    )

    if st.button("Generate Design"):
        if not description.strip():
            st.warning("Please enter a valid description.")
        else:
            with st.spinner("Generating design..."):
                try:
                    result = generate_cad_from_text(description)
                    st.session_state.design = {
                        **result,
                        "description": description
                    }
                    st.session_state.stage = "active"
                    st.rerun()
                except Exception as e:
                    st.error(f"Generation failed: {e}")


# ==========================================================
# STAGE 2 — ACTIVE DESIGN (PREVIEW + MODIFY)
# ==========================================================
if "last_action" not in st.session_state:
    st.session_state.last_action = None

if "last_message" not in st.session_state:
    st.session_state.last_message = None

if st.session_state.stage == "active":

    design = st.session_state.design

    st.markdown("### 📝 Original Design Description")
    st.info(design["description"])
    st.markdown("---")
    
    if st.session_state.last_action == "modify":
        st.success(st.session_state.last_message)
        st.session_state.last_action = None
        st.session_state.last_message = None

    elif st.session_state.last_action == "error":
        st.error(st.session_state.last_message)
        st.session_state.last_action = None
        st.session_state.last_message = None


    # ---- Load latest STL
    stl_files = [
        f for f in os.listdir(design["stl_dir"])
        if f.lower().endswith(".stl")
    ]

    if not stl_files:
        st.error("No STL generated yet.")
        st.stop()

    stl_files.sort(key=lambda f: os.path.getmtime(os.path.join(design["stl_dir"], f)))
    stl_path = os.path.join(design["stl_dir"], stl_files[-1])

    st.subheader("🔍 Design Preview")
    render_stl_viewer(stl_path)

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
                st.warning("Enter a modification.")
            else:
                with st.spinner("Applying modification..."):
                    try:
                        refine_existing_design(design["json_path"], modification)

                        # Persist success across rerun
                        st.session_state.last_action = "modify"
                        st.session_state.last_message = "✅ Modification applied successfully."

                    except Exception as e:
                        st.session_state.last_action = "error"
                        st.session_state.last_message = f"❌ Modification failed: {e}"
                        st.session_state.stage = "terminate"
                        st.session_state.terminate_popup = True

                st.rerun()


    with col2:
        if st.button("Terminate Design"):
            st.session_state.stage = "terminate"
            st.session_state.terminate_popup = True
            st.rerun()


# ==========================================================
# STAGE 3 — TERMINATION POPUP
# ==========================================================
# ==========================================================
# STAGE 3 — TERMINATION POPUP (COMPATIBLE VERSION)
# ==========================================================
if st.session_state.stage == "terminate" and st.session_state.terminate_popup:

    st.markdown("---")
    st.markdown("## 🔚 Finalize Design")

    design = st.session_state.design

    # ---- Load latest STL
    stl_files = sorted(
        [f for f in os.listdir(design["stl_dir"]) if f.endswith(".stl")],
        key=lambda f: os.path.getmtime(os.path.join(design["stl_dir"], f))
    )

    stl_path = os.path.join(design["stl_dir"], stl_files[-1])

    st.subheader("🔍 Final Design Preview")
    render_stl_viewer(stl_path, height=200)

    st.divider()

    # ---- Downloads
    with open(stl_path, "rb") as f:
        st.download_button(
            "⬇️ Download Final STL",
            f,
            file_name=os.path.basename(stl_path),
            mime="application/sla"
        )

    cad_files = sorted(
        [f for f in os.listdir(design["cadquery_dir"]) if f.endswith(".py")],
        key=lambda f: os.path.getmtime(os.path.join(design["cadquery_dir"], f))
    )

    cad_path = os.path.join(design["cadquery_dir"], cad_files[-1])

    with open(cad_path, "rb") as f:
        st.download_button(
            "⬇️ Download CADQuery Script",
            f,
            file_name=os.path.basename(cad_path),
            mime="text/plain"
        )

    st.divider()

    # ---- Cleanup + Reset
    if st.button("🧹 Clear Workspace & Start New Design"):
        for folder in [JSON_DIR, CADQUERY_DIR, STL_DIR]:
            if os.path.exists(folder):
                shutil.rmtree(folder)
                os.makedirs(folder, exist_ok=True)

        st.session_state.stage = "initial"
        st.session_state.design = None
        st.session_state.terminate_popup = False
        st.success("Workspace cleared. Ready for a new design.")
        st.rerun()