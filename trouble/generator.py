import os
import shutil
import json
import subprocess
from datetime import datetime
from string import Template
from trouble.etude_core import EtudeRegistry
from trouble.daily_runner import execute_daily_etude_tasks
from .log_config import get_logger

logger = get_logger(__name__)

def run_generation(output_dir_base="docs/", git_hash: str = "N/A"):
    """
    Main function to handle the document generation process using the Etude framework.
    - Discovers etudes.
    - Generates content for each etude in its respective subdirectory.
    - Generates a main index.html with tabs linking to each etude.
    """
    logger.info(f"Generation process started. Base output directory: '{output_dir_base}'")

    # 1. Initialize and populate the EtudeRegistry
    registry = EtudeRegistry()
    try:
        registry.discover_etudes(package_name="trouble.etudes")
    except Exception as e:
        logger.critical(f"Critical error during etude discovery: {e}", exc_info=True)
        logger.critical("Aborting generation.")
        return

    etudes_list = registry.get_all_etudes()

    if not etudes_list:
        logger.warning("No etudes found or registered. Nothing to generate.")
        return

    # 2. Ensure base output directory exists and is clean
    os.makedirs(output_dir_base, exist_ok=True)
    logger.info(f"Ensured base output directory exists: {output_dir_base}")

    # 3. Copy JavaScript assets
    logger.info("Copying JavaScript assets...")
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Project root is parent of 'trouble'
    js_src_dir = os.path.join(project_root, "trouble", "js_src")
    js_dest_dir = os.path.join(output_dir_base, "assets", "js")

    # Copy core JS files
    core_js_src = os.path.join(js_src_dir, "core")
    core_js_dest = os.path.join(js_dest_dir, "core")
    if os.path.exists(core_js_src):
        shutil.copytree(core_js_src, core_js_dest, dirs_exist_ok=True)
        logger.info(f"Copied core JS files to {core_js_dest}")

    # Copy vendor JS files
    vendor_js_src = os.path.join(js_src_dir, "vendor")
    vendor_js_dest = os.path.join(js_dest_dir, "vendor")
    if os.path.exists(vendor_js_src):
        shutil.copytree(vendor_js_src, vendor_js_dest, dirs_exist_ok=True)
        logger.info(f"Copied vendor JS files to {vendor_js_dest}")

    # Copy etude-specific JS files and templates
    for etude in etudes_list:
        etude_js_src = os.path.join(project_root, "trouble", "etudes", etude.name, "js_src")
        if os.path.exists(etude_js_src):
            etude_js_dest = os.path.join(js_dest_dir, etude.name)
            shutil.copytree(etude_js_src, etude_js_dest, dirs_exist_ok=True)
            logger.info(f"Copied JS assets for etude '{etude.name}' to {etude_js_dest}")

    # Copy skin definitions and CSS
    skins_src_dir = os.path.join(js_src_dir, "skins")
    skins_dest_dir = os.path.join(output_dir_base, "assets", "skins")
    if os.path.exists(skins_src_dir):
        shutil.copytree(skins_src_dir, skins_dest_dir, dirs_exist_ok=True)
        logger.info(f"Copied skin assets to {skins_dest_dir}")


    # 4. Get Build Information
    logger.info("Gathering build information...")
    build_timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    build_info = {
        "git_hash": git_hash, # Use the hash passed in from the workflow
        "build_timestamp": build_timestamp
    }


    # 5. Run daily tasks to get fresh data
    logger.info("Executing daily etude tasks to fetch data...")
    daily_run_results = execute_daily_etude_tasks(registry)

    # Write the results to a JSON file in the root of the output directory
    daily_run_results_path = os.path.join(output_dir_base, "all_etudes_results.json")
    try:
        with open(daily_run_results_path, "w") as f:
            json.dump(daily_run_results, f, indent=4)
        logger.info(f"Successfully wrote daily run results to {daily_run_results_path}")
    except Exception as e:
        logger.error(f"Failed to write daily run results to JSON file: {e}", exc_info=True)


    # 6. Generate content for each etude
    logger.info("Generating HTML app shells for individual etudes...")
    for etude in etudes_list:
        etude_output_dir = os.path.join(output_dir_base, etude.name)
        logger.info(f"Processing etude: {etude.name} -> {etude_output_dir}")
        try:
            # Pass build info and now also the path to the daily data
            build_info["daily_data_path"] = "all_etudes_results.json" # Relative path for the JS to use
            etude.generate_content(etude_output_dir, registry, build_info)
        except Exception as e:
            logger.error(f"Error generating content for etude {etude.name}: {e}", exc_info=True)
            # Decide if one etude failing should stop everything. For now, continue.

    # 6. Generate the main index.html with tabs for etudes
    logger.info("Generating main index.html with tabs...")

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
        logger.error(f"Error reading main index template ({template_path}): {e}")
        # Fallback if template is missing
        main_output_content = "<h1>Error: Main index template missing.</h1>"
    else:
        main_tmpl = Template(main_template_str)
        main_output_content = main_tmpl.safe_substitute(main_index_template_data)

    main_index_file_path = os.path.join(output_dir_base, "index.html")
    try:
        with open(main_index_file_path, "w") as f:
            f.write(main_output_content)
        logger.info(f"Generated main index.html at: {main_index_file_path}")
    except IOError as e:
        logger.error(f"Error writing main index.html: {e}")

    logger.info("Generation process finished.")
