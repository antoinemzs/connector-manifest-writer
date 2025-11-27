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

        process = subprocess.run(tool_cmw.get("config-dump-command").split(), text=True, capture_output=True, cwd=dir)
        config_schema_str = process.stdout

        logo_str = None
        with(open("{}/{}".format(dir, tool_cmw.get("icon-path")), "rb") as f):
            bytes = f.read()
            logo_str = "data:image/png;base64,{}".format(base64.encodebytes(bytes))

        contract = {}
        contract["slug"] = tool_cmw.get("slug")
        contract["use_cases"] = tool_cmw.get("use_cases")
        contract["logo"] = logo_str
        contract["config_schema"] = ast.literal_eval(config_schema_str)

        contracts.append(contract)

    manifest = {"id": "filigran-catalog-id", "name": "OpenCTI Connectors contracts", "description": "",
                "version": "rolling", "contracts": contracts}

    print(json.dumps(manifest))


if __name__ == "__main__":
    main()