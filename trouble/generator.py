import os
import shutil
from string import Template
from trouble.etude_core import EtudeRegistry

def run_generation(output_dir_base="docs/"):
    """
    Main function to handle the document generation process using the Etude framework.
    - Discovers etudes.
    - Generates content for each etude in its respective subdirectory.
    - Generates a main index.html with tabs linking to each etude.
    """
    print(f"Generation process started. Base output directory: '{output_dir_base}'")

    # 1. Initialize and populate the EtudeRegistry
    registry = EtudeRegistry()
    try:
        # Discover etudes from the 'trouble.etudes' package path
        # The actual Python package path is 'trouble.etudes'
        registry.discover_etudes(package_name="trouble.etudes")
    except Exception as e:
        print(f"Critical error during etude discovery: {e}")
        print("Aborting generation.")
        return

    etudes_list = registry.get_all_etudes()

    if not etudes_list:
        print("No etudes found or registered. Nothing to generate.")
        # Optionally, still create a basic main index page
        # For now, just exiting.
        return

    # 2. Ensure base output directory exists and is clean
    if os.path.exists(output_dir_base):
        # Be careful with this in a real project, but for a clean build it's useful
        # shutil.rmtree(output_dir_base)
        pass # For now, we'll just overwrite
    os.makedirs(output_dir_base, exist_ok=True)
    print(f"Ensured base output directory exists: {output_dir_base}")

    # 3. Copy JavaScript assets
    print("\nCopying JavaScript assets...")
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Project root is parent of 'trouble'
    js_src_dir = os.path.join(project_root, "trouble", "js_src")
    js_dest_dir = os.path.join(output_dir_base, "assets", "js")

    # Copy core JS files
    core_js_src = os.path.join(js_src_dir, "core")
    core_js_dest = os.path.join(js_dest_dir, "core")
    if os.path.exists(core_js_src):
        shutil.copytree(core_js_src, core_js_dest, dirs_exist_ok=True)
        print(f"  Copied core JS files to {core_js_dest}")

    # Copy vendor JS files
    vendor_js_src = os.path.join(js_src_dir, "vendor")
    vendor_js_dest = os.path.join(js_dest_dir, "vendor")
    if os.path.exists(vendor_js_src):
        shutil.copytree(vendor_js_src, vendor_js_dest, dirs_exist_ok=True)
        print(f"  Copied vendor JS files to {vendor_js_dest}")

    # Copy etude-specific JS files and templates
    for etude in etudes_list:
        etude_js_src = os.path.join(project_root, "trouble", "etudes", etude.name, "js_src")
        if os.path.exists(etude_js_src):
            etude_js_dest = os.path.join(js_dest_dir, etude.name)
            shutil.copytree(etude_js_src, etude_js_dest, dirs_exist_ok=True)
            print(f"  Copied JS files for etude '{etude.name}' to {etude_js_dest}")


    # 4. Generate content for each etude
    print("\nGenerating HTML app shells for individual etudes...")
    for etude in etudes_list:
        etude_output_dir = os.path.join(output_dir_base, etude.name)
        print(f"  Processing etude: {etude.name} -> {etude_output_dir}")
        try:
            # The generate_content method of each etude is responsible for
            # creating its own directory and index.html file within etude_output_dir
            etude.generate_content(etude_output_dir, registry)
        except Exception as e:
            print(f"    Error generating content for etude {etude.name}: {e}")
            # Decide if one etude failing should stop everything. For now, continue.

    # 5. Generate the main index.html with tabs for etudes
    print("\nGenerating main index.html with tabs...")

    # Prepare data for the main index template
    tabs_html_list = []
    iframes_html_list = [] # Using iframes for simplicity to embed etude content

    # Determine default active etude (e.g., 'zero' or the first one)
    active_etude_name = "zero" if registry.get_etude("zero") else (etudes_list[0].name if etudes_list else None)

    for i, etude in enumerate(etudes_list):
        is_active = etude.name == active_etude_name
        tab_id = f"tab-{etude.name}"
        iframe_id = f"iframe-{etude.name}"

        # For tabs:
        # Using simple button-like divs for tabs for now.
        # A real tab implementation would use more robust HTML/CSS/JS.
        tabs_html_list.append(
            f"""<button class="tablinks {'active' if is_active else ''}" onclick="openEtude(event, '{etude.name}')">{etude.name.capitalize()}</button>"""
        )

        # For iframes (tab content):
        # The src will be like "zero/index.html" or "one/index.html"
        iframe_src = f"{etude.name}/index.html"
        iframes_html_list.append(
            f"""<div id="{etude.name}" class="tabcontent" style="display: {'block' if is_active else 'none'};">
    <h3>{etude.name.capitalize()}: {etude.description}</h3>
    <iframe src="{iframe_src}" style="width:100%; height:600px; border:1px solid #ccc;" title="{etude.name} content"></iframe>
</div>"""
        )

    tabs_html = "\n".join(tabs_html_list)
    iframes_html = "\n".join(iframes_html_list)

    main_index_template_data = {
        "project_title": "Trouble Project Etudes",
        "tabs_navigation": tabs_html,
        "tab_iframes_content": iframes_html,
        "default_active_etude_name": active_etude_name or ""
    }

    # Load the main_index.html.template
    # Path is relative to this file's location (trouble/generator.py -> trouble/templates/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(current_dir, "templates", "main_index.html.template")

    try:
        with open(template_path, "r") as f_template:
            main_template_str = f_template.read()
    except IOError as e:
        print(f"  Error reading main index template ({template_path}): {e}")
        # Fallback if template is missing
        main_output_content = "<h1>Error: Main index template missing.</h1>"
    else:
        main_tmpl = Template(main_template_str)
        # Use safe_substitute for robustness
        main_output_content = main_tmpl.safe_substitute(main_index_template_data)

    main_index_file_path = os.path.join(output_dir_base, "index.html")
    try:
        with open(main_index_file_path, "w") as f:
            f.write(main_output_content)
        print(f"  Generated main index.html at: {main_index_file_path}")
    except IOError as e:
        print(f"  Error writing main index.html: {e}")

    print("\nGeneration process finished.")

if __name__ == "__main__":
    # This allows testing generator.py directly.
    # It will generate files into a 'docs' directory in the current working directory.
    print("Running generator.py directly for testing...")

    # To ensure etudes are found, we need to be in a context where 'trouble.etudes' is importable.
    # Typically, this means running from the project root or having the project in PYTHONPATH.
    # For direct execution from `trouble/` directory:
    # Add project root to sys.path if not already there (e.g. if running `python generator.py` from `trouble/`)
    import sys
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Up two levels to project root
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"Added {project_root} to sys.path for module discovery.")

    # Now 'trouble.etudes' should be discoverable by EtudeRegistry
    run_generation()
    print("Direct test run complete. Check the 'docs' directory.")
