# connector-manifest-writer
Writes a XTM Composer compatible manifest for connectors leveraging PEP621 metadata

## Design goals

* Full python program with an aim of being cross-platform: Windows, most Linux, macOS
* Runs on CLI
* Support python 3.12+
* Can be invoked anywhere: paths (if any) are provided as CLI arguments
* Parse main metadata from pyproject.toml in each component's main dir path
* Load targeted python modules in virtual env; support poetry and pip+venv

## Non goals

* Be responsible for implementing the code to output the configuration JSON Schema

## Proposed architecture

### CLI

```shell
cmw [-h] path [path ...]
```

### Process outline

For each `path` argument, the program:

1. parses the found pyproject.toml and collects metadata

This fulfills the manifest entries for: title, slug, description, short_description,
use_cases, verified, last_verified_date, playbook_supported, max_confidence_level,
support_version, subscription_link, source_code, manager_supported, container_version,
container_image, container_type

2. triggers the output of the config schema

Make use of a special CLI argument in a python subprocess. Each component must parse this argument.
It's useful for this behaviour to be implemented in a shared library, e.g. `pyoaev`

Example:
```python
python -m collector_module --output-config-schema
```

Should support invoking via poetry or python in a venv; find this hint in the pyproject.toml file
under the **build-system** collection.

This outputs to stdin.

This fulfills the config_schema manifest property

3. output the base64-encoded icon file binary

Possibly based on the output config, locate the icon file and output the base64-encoded binary data

Falling back to browsing to a known directory (often an img/ directory)

This outputs to stdin

This fulfills the logo manifest property.

4. consolidate this data into a single manifest entry
5. compile all manifest entries into a manifest object and output to stdin

Invokers should take care to redirect all output to the desired location e.g. a file.

### Compatibility requirements

Components (connectors, collectors, injectors...) compatible with this scheme must:

* Have a complete pyproject.toml file (can coexist with requirements.txt)
* Parse an argument that switches off executing the component and triggers an output of the configuration schema

### pyproject.toml contents

To satisfy the metadata needs, a compatible pyproject.toml file should include a special tool section for this present program,
ase per https://packaging.python.org/en/latest/specifications/pyproject-toml/#arbitrary-tool-configuration-the-tool-table.

e.g.
```toml
[tool.connector-manifest-writer]
title=...
slug=...
use_cases...
source_code=...
```

Some metadata should come from the standard tables, e.g.
```toml
[project]
description=...
version=...
```