import argparse
import toml
import subprocess
import json
import base64
import ast

def main():
    parser = argparse.ArgumentParser(
        prog='connector-manifest-writer',
        description='Generates and compiles XTM Composer manifests',
        epilog='Good luck')

    parser.add_argument("target", action='extend', nargs='+', default=[])
    args = parser.parse_args()

    contracts = []
    for dir in args.target:
        pyproject_path = "{}/pyproject.toml".format(dir)
        pyproject_contents = toml.load(pyproject_path)

        tool_cmw = pyproject_contents.get("tool").get("cmw")

        install_process = subprocess.run(tool_cmw.get("install-command").split(), text=True, capture_output=True, cwd=dir)
        out = install_process.stdout

        process = subprocess.run(tool_cmw.get("config-dump-command").split(), text=True, capture_output=True, cwd=dir)
        config_schema_str = process.stdout

        with open(f"{dir}/{tool_cmw.get('icon-path')}", "rb") as f:
            raw_bytes = f.read()
        logo_b64 = base64.b64encode(raw_bytes).decode("utf-8")
        logo_str = f"data:image/png;base64,{logo_b64}"

        contract = {}
        contract["title"] = tool_cmw.get("title")
        contract["slug"] = tool_cmw.get("slug")
        contract["short_description"] = tool_cmw.get("short_description", "")
        contract["use_cases"] = tool_cmw.get("use_cases")
        contract["logo"] = logo_str
        contract["verified"] = True
        contract["container_type"] = tool_cmw.get("container_type")
        contract["config_schema"] = ast.literal_eval(config_schema_str)

        contracts.append(contract)

    manifest = {"id": "filigran-catalog-id", "name": "OpenAEV Connectors contracts", "description": "",
                "version": "rolling", "contracts": contracts}

    print(json.dumps(manifest, indent=4))


if __name__ == "__main__":
    main()