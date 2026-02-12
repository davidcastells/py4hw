import os
import re
import nbformat
import shutil
from nbconvert import HTMLExporter

def convert_to_docs():
    html_exporter = HTMLExporter()
    html_exporter.template_name = 'lab'
    
    source_dir = '.'
    target_dir = '../docs'

    # Create docs folder if it doesn't exist
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    for root, dirs, files in os.walk(source_dir):
	
        # skip checkpoints dir
        if ('checkpoints' in root):
            continue
	
        # 1. Create corresponding subdirectories in /docs
        rel_path = os.path.relpath(root, source_dir)
        dest_path = os.path.join(target_dir, rel_path) if rel_path != "." else target_dir
        
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)

        for file in files:
            if file.endswith(".ipynb"):
                nb_path = os.path.join(root, file)
                
                with open(nb_path, 'r', encoding='utf-8') as f:
                    nb_content = nbformat.read(f, as_version=4)

                (body, resources) = html_exporter.from_notebook_node(nb_content)

                # Fix links: .ipynb -> .html
                fixed_body = re.sub(r'href="([^"]+)\.ipynb"', r'href="\1.html"', body)

                # Save to /docs/tutorial_subfolder/name.html
                html_name = file.replace(".ipynb", ".html")
                with open(os.path.join(dest_path, html_name), 'w', encoding='utf-8') as f:
                    f.write(fixed_body)
                
                print(f"Mapped: {nb_path} -> {dest_path}/{html_name}")

if __name__ == "__main__":
    convert_to_docs()