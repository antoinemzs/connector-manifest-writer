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

## Reasons for not plugging the OpenCTI connectors scripts

Mostly, there are a number of assumptions regarding the internal organisation of the code
which create frictions with using against the OpenAEV components:

Expects specific files and directories which don't exist in most OpenAEV components:
```shell
# Search for directory name - but only connector roots
# Look for directories with requirements.txt, src/, or __metadata__/
find . -type d -iname "*$search_term*" 2>/dev/null \
  | while read dir; do
      # Check if it's likely a connector root
      if [ -f "$dir/requirements.txt" ] || [ -d "$dir/src" ] || [ -d "$dir/__metadata__" ]; then
        echo "$dir"
      fi
```

Expects requirements.txt to exist and install with pip:
```shell
# -qq: Hides both informational and warning messages, showing only errors.
python -m pip install -qq -r "$requirements_file"
```

Writes to a file directly instead of stdout
```python
with open(filepath, "w") as file:
    connector_config_json_schema_json = json.dumps(
        connector_config_json_schema, indent=2
    )
    file.write(connector_config_json_schema_json)

print(f"✅ Connector config JSON schema written to {filepath}")
```

Fragile maintenance of both bash and powershell wrapper scripts along with a python script
which does not install its own dependencies (expects them to exist globally)

The locality of these scripts is also problematic as they are embedded into the
OpenCTI connectors repository.

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

## Example

### Invocation

```shell
python -m connector-manifest-writer ../collectors/crowdstrike
```

### Relevant contents of collector-specific pyproject.toml
```toml
[tool.cmw]
config-dump-command = "poetry run python -m crowdstrike.openaev_crowdstrike --dump-config-schema"
icon-path = "crowdstrike/img/icon-crowdstrike.png"
slug = "openaev_crowdstrike"
use_cases = ["cti", "vuln-hunting"]
```

### Output
Note: the binary file encoding is not quite right at the moment, sorry
```json
{
  "id": "filigran-catalog-id",
  "name": "OpenCTI Connectors contracts",
  "description": "",
  "version": "rolling",
  "contracts": [
    {
      "slug": "openaev_crowdstrike",
      "use_cases": [
        "cti",
        "vuln-hunting"
      ],
      "logo": "data:image/png;base64,b'iVBORw0KGgoAAAANSUhEUgAAAV4AAAFeCAYAAADNK3caAAABhWlDQ1BJQ0MgcHJvZmlsZQAAKJF9\\nkT1Iw1AUhU9TpSLVDnYQcchQxcGCqIijVLEIFkpboVUHk5f+QZOGJMXFUXAtOPizWHVwcdbVwVUQ\\nBH9A3AUnRRcp8b6k0CLGC4/3cd49h/fuA4RGhalm1wSgapaRisfEbG5VDLzCBwEhjKFfYqaeSC9m\\n4Flf99RNdRflWd59f1afkjcZ4BOJ55huWMQbxDObls55nzjMSpJCfE48btAFiR+5Lrv8xrnosMAz\\nw0YmNU8cJhaLHSx3MCsZKvE0cURRNcoXsi4rnLc4q5Uaa92TvzCY11bSXKc1jDiWkEASImTUUEYF\\nFqK0a6SYSNF5zMM/5PiT5JLJVQYjxwKqUCE5fvA/+D1bszA16SYFY0D3i21/jACBXaBZt+3vY9tu\\nngD+Z+BKa/urDWD2k/R6W4scAaFt4OK6rcl7wOUOMPikS4bkSH5aQqEAvJ/RN+WAgVugd82dW+sc\\npw9Ahma1fAMcHAKjRcpe93h3T+fc/u1pze8HSptylzurTW0AAAAGYktHRAAPALwA/5pVxFcAAAAJ\\ncEhZcwAALiMAAC4jAXilP3YAAAAHdElNRQfpAQIPLgkTcfdkAAAgAElEQVR42u3df2zU953n8dd3\\nvl/PmFqH72p5jQJWLJFBiV3MxaWBgqI1JLngRFUWts6JhUi3XHLKJeRS0TYtQRWHoiTdbJNNVNJt\\nL0CEGi8ibEhBKvhE+aWiOAHELnHkcDWIVtZdZY1gWatK7PF8v3N/jMdrwOBfM9/v5zPzfPzVJQvz\\n+zXv+Xzfn/fHuTLvrqwAAKGJ8RQAAMELAAQvAIDgBQCCFwBA8AIAwQsAIHgBgOAFAIIXAEDwAgDB\\nCwAgeAGA4AUAELwAQPACAMELACB4AYDgBQAQvABA8AIAQg9eZ1GjnEWNPOMACN6wbih7vkeVP3+b\\n8AVA8IZ5Y9nBQcIXAMEb5o35n3YrVlurxJuv88wDIHhDCd7TZyRJbn29Evv38OwDIHiLLejYp+zA\\ngCTJa15I+AIgeEOpen//h9H/7TUvVLxjF68CAIK3qMF75sx1/3fFkvvkvbKVVwJA2XCuzLsrG/aN\\nfqXnnJx4/Lo/G3p/nzIvbuMVAUDFW5Sq98L/uenPEo+3U/kCIHiLJXPs2Lh/nni8Xd7mTbwqAAje\\ngle8298Z7W64UfyJ9Yqta+eVAUDwFrzq/fzCuH/uxOOq3LKZ8AVA8Bba8C/fu+V/I3wBELxFkO08\\nJr+vj/AFQPCGKdP18W3/ez58nVUreaUAlIxI+njHGq+n90ZBKqXBp59V9nwPrxgAKt4ZV70ffTTx\\nnaytZZwkAIK3UIb/cf/k7ijhC4DgLYxs5zFlPu0mfAEQvGFK/693Jn+HCV8ABG9hqt7btZYRvgAI\\n3iIY/mD/1O444QvAUpG3k41Vefyw3Pr6Kf0dv69PgyvaeCUBUPGGUfVKnN8GgOCdEX/7O1Na683j\\n/DYABG/IVS/hC4DgjaDqJXwBELwRVL2ELwCCdwZV72R3sxG+AAjeApnKbjbCFwDBWwDZzmMa/uQ0\\n4QuA4A3T8Gs/UTadJnwBELyhVb3nezR85Dcz/ncIXwAmMWrL8K3M6jquWG3tjP+dzKfdGlqzllcd\\nABXvRNId/1CQf8drXqjK44cZrAOA4J3ITNvLxnLr65lqBoDgnVTVu+2lGV9oG33QjJQEQPBOrFAX\\n2ghfAFGz4uLaWNOZ2Xs7HB0PgIp3Aukduwr7BFD5AiB4J6hQO/Zp+MQJwhcAwRtq1fvkRgWpVFHC\\nN7aunXcFAIJ3PEPbf1b4J6O2VpVbNhO+AAje8RRjyUGSnHic8AVA8N5KMZYcCF8ABO8EirHkQPgC\\nKCb3B7O/+j9tfgDZ7h5pfoPcBcnCh6/rqmJFq7JzahUcPcm7BUBhssW2DRS3UuiNFTdV1u/vU+bF\\nbbxjAMxYrFQeyNB3vluwWQ7jSTzeLu+VrbxjABC8ednzPUr/8r2i3kbi8XbFd2znXQOA4M3LvPrG\\njM9pm0hFayunWQAgeMdKr9tQlBazsThKCADBe4PBAs7uvV34Vh7+kPkOAAheKXc0fLHXeyXJTSYZ\\nrgOA4M0LY71XYrIZAIL3OmGs9+bDd9ae99jlBoDglZQ7XaLI670SW4wBTJ71W4Yn1J9S4ATyli4t\\nfvi6rrzly5SdO4ctxgDKOHglZU+fK9o8h3HDt6mJ+Q4Abp0TpTKrYTIS+/fIa14Y2u0Nnzih9JMb\\neZcBKN/glaRZXccVq60N7fYyn3ZraM1a3mkARsXK7QGHdbEtz2teqMrjh2k3A1C+wZs936PBl18N\\nNXzd+np6fQGUb/BKufPa0r86EO4TXVurWe/uoN0MQHl0NYwbvkdPymlulNvQENptOomEvOXL5F+7\\nmjs5A0BZKruLazcKu9MhjxMtAIK3rIXd6ZBHuxlQnmI8BblOhzBmOtyIoeoAwVu2sud7QpnhOx6v\\neaFmdR2n4wEoI2V7ce0mFy/Lv3ZV3vJlclw31Jt2qqrkrmxVMPgFF90AgrfMKt/untAG6owXvnQ8\\nAARveYbv6XPKzqmV19QUfvi6ripWtDJgByhxrPGOI/PiNg29vy+y20883q54xy5eCIDgLb/wDePo\\noFupWHKfEvv3cNENIHjLS3rdBmU+7Y7s9r3mhcx4AAje8jO0Zm2k4ct5bkDpYefaJFUe/lBuMhnp\\nfWCbMUDFW16V7w+3RLK7bSwuugEEb1nJnu+JbGvxWBVL7lPl4Q9Z9wUIXsI3TG4yqcqfv826L2Ap\\nNlBMVX9K/tkzcle2yqmqiuxu5He6BU6QO0UZgDW4uDbdJ25RY67qjGCc5I3Svz6k4edf4EUBLMFS\\nwzSZsuwgSfFHH2GzBUDwEr5hG91ssWolLwxA8BK+ob2YtbWa9cZP5G58ihcGMBhrvIV6Ig1a85VY\\n9wWoeKl8Qxd/9BH6fQGCl/ANG/2+gJno4y00Q/p88/L9vtnZVQpOdfH6AAZgjbdYT6xha76SNPzJ\\naaXXbeDFASLGUkOR5Jcd/N5eY+5TxZL7VHn8MOu+ABVv6Uvs3yOveaE5XwrptIZ+9vfyt7/DiwMQ\\nvDMs30cuIgUd+4y7b6aFr0TLGRBZVpXSgwk69qlyy2Yjr+JHfZLFeGg5AwjewoRvf7/R4Zv+9SGj\\n7pObTGrWuztoOQPC/NyVWjuZ07JI3j13y1u+TP61q8p295j1xdB5RNk5tfKamsx5zhIJVaxoleY3\\nKOg8wqcCIHinJitfFY+0yXFdc8P36EnjwleS3AVJuW0Pyf+sW+pP8ekAilXslGJXw6yu46P9s9l0\\nWl+uXa/s+R7j7mdsXbsqt2yWE4+b9eU1MKDB1//OyIuUABWvqd8mzU1yF+ROBHZcV+7KVvlnzxhX\\nxWW7e+Rfuypv+TI5rsvSA1AmSnIDReZw5/UPsrY2N6vWwKv3Qcc+fbnpe8bMdxiLrgeApYYpqTx+\\nWG59/fUhl0pp8OlnjVx2MHGL8dilh6Fd77LhAqDinaDq7fr45gdrcOWb32JsWq+vJDmzZ6vyO88r\\nvmM7nxiAivf2vtJzbtwLVyZXvpKZu9zy/L4+DX3nu8Y+dwAVb9RV70cfjf+gDa58pdxGi6H3zewo\\ncOvrNWvPe/I2b+LTA0z3c1TK83iD9KAqHmkbv9SvqjK220Ea6fWtqpT7tSajOh6kXKeI13KvnCWL\\nFVzqpecXIHjHuHhZsdb7FaurszN8T3UZ2W42+uaZN1fuylYFg18Yt0kFIHijDK9//ZdbVr02hG+2\\nu0eZU7815kSL8Z4/en6BqSn5QejZzmMTdgrEams1a897xg6KMXGo+o3ijz7CkHWAinfyVa8ko2c7\\nSJL6U8p07JWzZLHceXPN/Bavrpa3+jHOdwMIXk241mtN+Ery9x8wcsDOdc8hF94AgneyVa8t4Rsc\\nPSn/SsrYi25S7sKb1/aw/D8NcOENKNfgnWzVa0v4Zrt7lLnUK/cbi4286Cb927Adp7lR/sFDfNqA\\nsgteScGFz+WtfmxSVWI+fLNz5yg4etLYLxP/7BnFWv6jYjU15r7JGhrkrW2n7Qwox+BVf0rOvQvl\\nNjRMrmJzXXlNTcrOqTU3fPMX3ZobJ/24Iql+q6rkLV8mLZhP2xnKXlke7/6Vcx/JmT17Sn9n6P19\\nyry4zejH5W3epPgT640brH4jv69PQ3/zt8p2HuMTCCresllyqIjJW7p0aqHW1CRnyWL5+w+Y+7hG\\ndrq5X2sydt1XGmk7e/ABs5dxACrewqs8/KHcZHLKfy/zabeG1qw1+0Vd1KjEj1+e1uMLvfrt7dXQ\\nD7cw7QxlJVauD3zoh1uUTaen/nO+eaES+/cY/diy53s02LZawydOmP+TK5lk2hkI3nKRPd+j4SO/\\nmdbf9ZoXalbXceO3x6af3Kihnbum9QUTaoUejyvxXzdwzBBYaiibJYdxjgiaLNMHqo9+u65rV2Lj\\nM0YeK3TTF2I6rfQv31Pm1Tf4dKJkleXFtbH8/j/Ke/CBae0Ac6qq5K1+zOiNFtLIacZnz8i55+5J\\nbSCJtBIY2XLstj0k/7NuthyD4C1JFy9LC+aPHgc/raAwfJebJKk/JX/vB9L8hmk/1lCr9JoaBu6A\\npYaSX3KYZpfDWDb0+uaXHiq3bDa+33f0VwmdD6DiLdElh8+6J72d+Fa8piYrBoLnh6vHli1VrLqa\\n6hcI+z3NUzASRud7NPSzv5/xvxN/9BHj283yj3dwRZsVLWcSnQ+g4i3d8D19riCDxmN1dXJXf0v+\\nP/+T8ReH/IOHFATDcltajB0xSfWLUsMa7zhmdR0vSOtVkEppcNtLVswkcBY1KvHm69NurYvkS4O1\\nX1Dxlg7///ZNu8XsujCrqpL34APmdzxIuSlnuzuMn3I2bvXLzAcQvCXg4mUFTjDlQTrjhq8Nc30t\\nXnrIj+50V39Lfv8fc+2BAEsN9orv2K6K1taC/XvDJ04o/eRGO94YFi49ZNNpDR/5jYaff4E3L8z+\\ntcZTcGvpJzcW9Ej1itZWJfbvseKqvG1dD1Ku82H0mPlVK3kDg6UGW/mfdctd2Vqw+baxujq5K1vl\\nnz1jxXbY0aWHxkY5iYQd1UR1tSoeaeOsNxC81upPFexi22hlZsmMh9Hq9/Q5ZT7uMv5st5ve3AU+\\n681Z1MjsCBC8obl4Wf61q6pY0Vq4n8Wuq4oVrWaf53bDF1CmY680v0GxhjutuPCW/5LLn3Qc/OH3\\nMwtOQhcEb8hVX3ePsnNqc9uCC8iGI4XGCjqPWHG80LjVb9vDCipiyp4+xxsaBK8tgqMnC7Kz7aYX\\nYd5ca3a65b+E/LNnpIY7C/5cFLX6TSTkLV0qZ8liBZd6qWBB8NrC339Asdb7Cz7XNlZdLa/tYfl/\\nGrBi3Vf9Kfn7DyhbVZmrfi1Zesh/0bHtGJEWAfTxTk+hthXfVE2m00r/6oAV4yVH30QWHa550xcp\\n245B8Fr0xC1qVOXP3y7acTo2nGZ8o4q3XlPFQw9aM+d37JcdGy/AUoMN+lPyz54paI/vdUsPdXXy\\n1rZb0+8r2XvhzXFduQuSbDsGwWtL+AaDX8hbvqwoa5z5ft/ACay5Ep/t7lFm526rhu2MftlVV8t7\\n8AFpwXzjh9mD4C1r2e4e+deuFi98XTc3rMeCky3G8g8ekn8lJe/rLdbseBtb/RZy4wVA8FoYvpJy\\nP4UtO3k3292jzMdd1rWd5X9t5DdesO0YBG8Zh2+spsauljNptO3MtnkPox+QAm87BgjeIoRvoeb4\\n3rISSyRyW5ctW3qwdd7DddUvGy9A8JobMMXYWlwKSw/5eQ82brqQRjZesO0YBK+ZgqMnQwlfK5ce\\nJAWnunLHy9tY/bLtGAQv4Wvr0kOpVL/Zr1az7RgEbzmGr7VLD6VQ/bbca+XzDoK35MM3rMMj80sP\\n1q1BWl79jp52zNAdELzmyJ4+V/RWs+uqsKVLrew/tbr6dd1c9cu2YxC8BoVvCH2+172wDQ12hoDt\\n1S/bjkHwlnf45kPAxp/Atle/DN0BwWti+IY0wyD/EzjWer+CC5/bdQFobPV713zrdr1R/YLgNSx8\\nMx93FW2k5LghUFdnbfN/cKrL3pkPVL8Y733BIPQIn/wiD1O/leETJ5R+cqOdlcLGp5TY8NdyZs+2\\n7wuXgeug4jXjp7R/9oyce+4u+Blut33RLR78kp/5oLpa6+b9Uv2Citcwif175DUvpAKbgti6diU2\\nPhP6L4ZCPffpX76nzKtv8OYneBGlirdeU/zRR0K/Xb+vT0N/87fKdh6z9nmz8aw3icM2WWpA5ILO\\nI6FtMb6ucsy3nc2do+DoSSuft8ylXsUWfk2x6mq7qnZ2vRG8MCBEjp7MHZkTUq/v6E8f15XX1GTv\\n3IGLl5XZ3WHlxot8yx8TzwheRCjf6xvFab22V2D5jRc2tp7lJ57ZNuYT0/iyZY3X4BcnonazPNvX\\nH21uPbO55Q8Eb0mIouNhtPq2/Oq7s6hRFS98TxVL7rPuvtt+0RMsNVjN3/uBNL9B7oJk+MGVn7pl\\n69qvxYdt2n7REwSv9YLOI5FeOLJ97Xd044Vla7/5i55WztoAwVsS4XuqK7KLbtdVv7buvBqpfv0r\\nqciew2l/8Y3M2uDCW2lgjdfGF21RoxI/flluMhnZfSiFuQPxHdvlLVtm3caL9K8PMe+B4EWUwVHR\\n2hrpfbD9ApCzaqUSP/i+3Pp6q+6339enoe98lx1vLDUg9A/fwUORbxiIVVer4pE2K48aknT9xguL\\nZv7GqqvlrX5MgRNYN+YTBK/1ol73HX0jjUw8y86KWxkENs78dVzX2vP1CF6C13rZ7h75Z89EfkyO\\nU1WVCwJbt76OufgWu2u+NXMfRs/X++d/ouuB4EXYoZHp2BtZv+91b6p5c+1uPevuyS0/zKmVW19v\\nxfIDSw8EL6L8ydx5JJIhO+P+DLb8uPPg6Emrhq7nlx40v4Ez3kx/rehqKNEXdlGjEm++bsTV+mw6\\nrcxHH1k9e8C27gfm/FLxIqqlh90dcpobI6/WHNeV29Cgiv+y3srDNiWNdj/YsvU4VlMjd2Wrlcc7\\nEbywnn/wUC4sWloin1HrJBLyli6Vzdtfs6fPafgXO+U0Nyp2xx1Gz/11qqrkLV/GrAeWGhDp0kPE\\nu91uXH6wfeebs6hR8a0/imxy3FQMf3Ja6XUb+CAQvIhCVOe63UqQSind8Q/yt79j7XMaW9eu+JMb\\njF//ZbcbSw2IKujyXQ9fbzFinTLf+2v18kO+/czw3W+x6moG7VDxgp/Jpbf8IJk/fCebTiv9qwPK\\nvLiNDwLBiyh4mzcp/sR6o0KiFJYfbFj/Zd2XpQZEFXKnuow7Gv265Yd//RcrN1+oPyV/7wfK/O6C\\nscfOu/Pm2nuyCBUvSoUJYybH+1ls++YLyeyDN4NUSoPbXuJsNypeRME/eMi40xnGbr7IfrXaytkP\\n0r/1/2p+g2INdxrV/+tUVcl78AH5165y0Y2KF5FWvx27jDyZtxRO3jX55OOh9/dx0Y2KF5EFnKEn\\n844OXrd19KQ0On4y87sLiiXvinSU5428pibm+1LxgursNj/fS6T9zN34lOLr/kqx2lpj7lPm024N\\nrVnLB4CKF1FWZ6bMe7juS8F15S5I2j18RyNHz+/cnZv/m0wa8RzH6uoYrk7FC1OqX5PmPdyoZNZ/\\nn3vGmO6SIJXS4NPPss2YihdRVr+Zjr2RH7B5yyqtVNZ/Dx4ypv/XqaqSt/oxOh4IXkReBZ3qUubU\\nb+Xcc7didXXmvalHjh5y7l1o70Uig+b/Oq4rb/kywpelBhgTcgZvDJCk7MCA0vv+UZlX37D6ea54\\n6zVVPPRgpFu7mfFAxQtTgu30OaOPRXcSidGz37L/7ivWXoALOo9E/ivDcV15TU3KzqllsDrBi8iN\\n7Xww9FicWHV1ycx/CIJhxebPj2x3IeHLUgMMZOLMhxsNnzih4Z/+zOqr9d4rWxX/i8ciW34YPnHC\\n+hkaBC9Kig2nMpTK8UNRbnBhowXBCwOZcFFowgAugQtwUe5+I3wJXpj4Jlu1UonnnzN240We39en\\n4Q/2Wz2APaovOsKX4IWhvM2bFG//trGtZ6MB3Nurobd+au0OuKh2GBK+BC8MDgVTh+7caPiT0xp+\\n7SfWXoCLosea8CV4YTBbjkS3/QSMKGY/EL4EL0xffoi4JWrSATwwoHTn/7Z211ZsXbsSG58J7eIb\\n4UvwguWHgrH9AlyYR88TvgQvLGDiQPDbBbCtIyidVSuV+MH3Q1nmIXwJXrD8UHA2X4ALq/WM8B2n\\nyGBWA0wTHD2pzKnfGjt457oP0JgRlMEffm/VDOCg84gyl3qLPvc3VlcnzW9Q0HmENzfBC6ONDN7x\\nr6QUu2t+5APBb/uzceQIeq/tYWXvnGfX8JiRub/FPnbeXZBksA7BC1tku3uU2d2RO4+svt7IyWej\\nAZxIyGtqsvIMuHz1635jcdGmnjHVjOCFjcsPH3dJdbVyGxqMvq9OIiFv6VL7ZgBfvKzMzt1ymhuL\\n9hx7TU3yr6TK/iQLghd2LT/kzyNL3qVYTY3Rd9fWGcD+wUPyr6Tkfb2lKL8wOEaI4IWNLl5WpmNv\\n5APBJx3AdXW5QzibG625AJft7lHm466inHiRP8Mtc+q3ZXt0PO1ksJ5N7Wc2zgD2Nm9S/In1BX9+\\ny/noeIIXpfFGjmAmwYwC2LIZwM6qlarc+qOCb27x+/o0uKKN4AWsfkOvWqn4f3tKXvNCK+6v39en\\n9I5dCjr2WXF/i3GsUzlusGCNF6Xl4uXRAyGduXON7v+VchfgKla0KtZ6v4ILnxu/5ukfPJQ71LSl\\npWA9v7G6urJrMyN4UZKyp8/l+n+rKuXeNd/o/t98+OR3wPkHD5n/3Ba459dralIQDFvV+8xSAzAB\\nG85+Gw22gQEN7XrXiglo8Y5dBZsql02n9eWm71l78gcVL3CDoPNIrn2prlaxO+4o2tbYglRDYzZg\\n+P1/NLr/199/ILerMJmc8XPquK7cbyyWf/ZMybeZEbwoH/kNGJd65cybV/D+1IIvP1RXW9H/Gxw9\\nKf/a1YJsuHCqquTcc7f8vR8QvEBJGbkAl/ndhaJP5irIh9SCATz5DRexZUtn/HyWw8U2ghdlHcCZ\\n3R1WdEDkB/C4q7+lIJM2c7ttf0qZ3R1yliye8ThPN5ks6W3FBC/KXr4DIgiG5TY2Gt0BkW8/c5Ys\\nVnCp18jlh/y6r9fUNP0vGteV9/WW3GCkElzvJXiBMQE8/IudVoygdOfNzS0/fLVawaku4+5fcPRk\\nbtDO8mXTvujmJBIlu95L8ALjhMbwL3bKaW40ugPCSSTktdxrbPdDtrtnxv2+pbreS/ACt/rJfPCQ\\nFS1osepqeQ8+YObmi4uX5Z89M6OLbm4yqcylXmvGak7qS5MNFMAkPigjQ3jCOhp92lWmwZsvEvv3\\nTHuGRqkN06HiBSbDkh7g/OYLEy+++Xs/mPbpFrHqajnNjcZvpyZ4gWL9dB7pATY5gPOnH2dnVxl1\\n8c0/eGjaHQ9uQ0PJHBvEUgNQ4ksQfm+vht76qVEzEKY7vD5IpfTlN1dQ8QIsQZh9ES5WUyPvwQek\\nBfMVdB4x4j6NbjOeYruZU1VVEksOBC9QBgHsuK7cBUmjWs+y3T3TCl+3oUGZ312wusuBpQagSEsQ\\n7n9uV3zVw3Jmzzbqvpl27ltsXbsqt2ye0rKD7V0OVLxAkSrg/EYM03bCmVb9TmejRay62uqNFVS8\\nQEi8zZvk/aeH5NbXU/3e4ldC5c/fnvSBmtl0Wl+uXW/lKcVUvEBIglNdxk1DM6r67U/JP3tG7srW\\nSVW+jutKDXfK33+A4AUwQaU2Mg3Nv5KSU1NjRC9wfttx5H2/Uwxfd95cK3t7WWoAov4QGnYkvd/b\\nq6Efbon0J/xUlh1svNBGxQtELb8b7uQJI1rRYjU18lY/psAJojv1dwqVb6y62roTiql4AdM+lAbt\\nhhv+5LTS6zZE+lzMenfHhC152YEBfdGyjIoXwAyqvYOHNPz2LyJvRXPnzZW3tl3B4BfRrKP2p+T/\\naWDCTRZOImFVexkVL2AB75WtkW7GiLrtbDKbLGyqeql4AQuM3YwR+7M/m/aJDtOu0PJtZ20Pyf+s\\nO/Rxk5PZXuwkEtbMcSB4AcsCOLNzd2S9wLGaGnltD8v/00DoSw/Z7h4FTiBv6dJb37877sjNyzD8\\ngEyCF7DQ2JORww5gJ5FQxYpWaX5D6NPOsqfP3Xaer+O6Ul2t8VUva7xACXA3PqWKv1wT+nbkqHp+\\nvVe2KvF4+/jhnE7ri8YWKl4ApVkBR7X0EBw9qVjr/ePu+nNc1/gOBypegAp45sGfTiv9qwPKvLgt\\n1Md5qwM0Te9woOIFqIBnXsG5rrymJjlLFoc6tCa48Pm4u9tM7+ul4gXKpAKOr/urSY9cnFEYplIa\\nfPrZ0NZ9nUWNmrXnvZt6fE0+n42KFyiXCnjn7lB2wjlVVfJWPyb/2tVw1n37U+P2+DpVVcbOcCB4\\ngTIS1qkYjuvKW75M2blzQvm5n+3uUXbunJvazJyaGmU69hK8AMwI4MzHXUWdhhb2um9w9KSc5ka5\\nDQ2jfxarqTHyYMwYb0GgTJcfzvco/eRGfbl2vYY/OV2026lYcp8qD38oZ1Fj0R9T+smN8nt7r7/9\\nb68x7rnn4hqAXBisWqnE88/JTSaLU5GGdNHtxiHqJm6oYKkBQM7Fy8p07C1aC1poF936UwoGvxi9\\n2GbihgqCF8D1SxAjPcDFuACXv+hW7NMtst09ys6uktdyb+5243GjLrIRvADGXxoYcwFu7AWrgoTv\\n0qVFr0KDU11yliyWO2+ucRfZuLgG4NaV48gFuC82/g/5fX0F/bcTj7fLe2VrUe9/et0GBanciEiT\\nLrIRvAAmDuDOYxpc0aahnbuUHRgoaPgm9u8p6n0f3PaSsum0vBZzLrCx1ABgSj/fC738EKurU6z1\\nfvl7PyjOnb54Obfe+82l8q+kojk77ga0kwGYXnisWqnED75fsAlomU+7NbRmbdHub7xjl5xZs4p6\\nGyw1AAhn+eH9fcqm0zP+97zmhUXdaDH82k/k/Id/b8aXFhUvgBkHyaJGJX78ckE2XxRzo0VsXe7U\\niqBjH8ELoDR4mzcp3v7tGR9DH/ZoSYIXgPXVb8UL31PFkvsIX4IXQJjcjU8pseGvZ1T9lmr4ErwA\\nilr9znTt1+/t1WDb6pJ6XuhqAFA02fM9Gmxbndt4Mc3OBzeZLPomCypeAKVb/b75+rT7fovd50vF\\nC6A0q98VbUr/+tC0/r7XvLBkKl+2DAMIVdB5RP6VlNyvNd10LPuElWJdndHHthO8AMytfrt75J89\\nI+eeuxWrq5ta5dvUZH34stQAIJrwPd+joTVrp7XlOP4Xj43uQqPiBYApCo6elH/t6pSWHvInWWQu\\n9Rp3gjAVLwA7wrdjnwaffvamE4JvG77xuCq3/iiU04sJXgAlKd/zO5Wuh1htrRI/fpngBYCZGH7+\\nBQ2++dak133dZFLxHduteoys8QIwr/o9fU6ZS71yv7F4Uuu+bkODslWVCk51UfECwLTDt/PYlNZ9\\n40+sl7NqpRWPjS3DAIwX79g1qTGTQSqlL7+5gglkWVgAAAHISURBVIoXAGYqvW6Dht6f+NSIWG2t\\n4h27jH88rPECsEJw9KSCYFhuS4sc1711qM2bqyAYVvb0OSpeAJgpf/s7Gnz51Qk7HhLP/Hej+3sJ\\nXgB2Vb4d+/Tl2vUKUqlb/v848bjR/b0ELwDrZM/3aPDpZ28bvm4yKW/zJoIXAAodvrdrN4s/sd7I\\nJQfayQBYL7F/j7zmheP+NxPPbKPiBWC9oTVrlfm0e9z/ZuKSA8ELoOTDN97+baOWHAheACUfvs7s\\n2ap47hmCFwDCDN+K1lZjZjkQvADKJnwTzz9H8AJAmOHrJpNyNz5F8AJAmOFb8ZdrCF4ACDN83fp6\\nea9sJXgBIMzwja96mOAFgGJLb3tpdLaDM3t2pFUvwQugLNw4WCfKqpfgBVB24ZsdGIi06iV4AZRf\\n+L7+d8qm05FVvRz9A6D8wre7R4ETqOLP/zySY4KoeAGUJX/7Oxp6f18kfb0EL4CylXlxm4L/90fF\\n1rUTvAAQlvS6DaHfJidQAEDIqHgBgOAFAIIXAEDwAgDBCwAgeAGA4AUAELwAQPACAMELACB4AYDg\\nBQAQvABA8AIACF4AIHgBgOAFABC8AEDwAgAIXgAgeAEAo/4/kyoZz9IUBKIAAAAASUVORK5CYII=\\n'",
      "config_schema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "config.schema.json",
        "type": "object",
        "properties": {
          "OPENAEV_URL": {
            "description": "The OpenAEV platform URL.",
            "format": "uri",
            "maxLength": 2083,
            "minLength": 1,
            "type": "string"
          },
          "OPENAEV_TOKEN": {
            "description": "The token for the OpenAEV platform.",
            "type": "string"
          },
          "COLLECTOR_ID": {
            "description": "ID of the collector.",
            "type": "string"
          },
          "COLLECTOR_NAME": {
            "description": "Name of the collector",
            "type": "string"
          },
          "COLLECTOR_PLATFORM": {
            "default": "SIEM",
            "description": "Platform type for the collector (e.g., EDR, SIEM, etc.).",
            "type": "string"
          },
          "COLLECTOR_LOG_LEVEL": {
            "default": "error",
            "description": "Determines the verbosity of the logs.",
            "enum": [
              "debug",
              "info",
              "warn",
              "error"
            ],
            "type": "string"
          },
          "COLLECTOR_PERIOD": {
            "default": "PT1M",
            "description": "Duration between two scheduled runs of the collector (ISO 8601 format).",
            "format": "duration",
            "type": "string"
          },
          "COLLECTOR_ICON_FILEPATH": {
            "default": "crowdstrike/img/icon-crowdstrike.png",
            "description": "Path to the icon file",
            "type": "string"
          },
          "CROWDSTRIKE_CLIENT_ID": {
            "description": "The CrowdStrike API client ID.",
            "type": "string"
          },
          "CROWDSTRIKE_CLIENT_SECRET": {
            "description": "The CrowdStrike API client secret.",
            "format": "password",
            "type": "string",
            "writeOnly": true
          },
          "CROWDSTRIKE_API_BASE_URL": {
            "description": "The base URL for the CrowdStrike APIs. ",
            "type": "string"
          },
          "CROWDSTRIKE_UI_BASE_URL": {
            "default": "https://falcon.us-2.crowdstrike.com",
            "description": "The base URL for the CrowdStrike UI you use to see your alerts.",
            "type": "string"
          }
        },
        "required": [
          "OPENAEV_URL",
          "OPENAEV_TOKEN",
          "COLLECTOR_ID",
          "COLLECTOR_NAME",
          "CROWDSTRIKE_CLIENT_ID",
          "CROWDSTRIKE_CLIENT_SECRET",
          "CROWDSTRIKE_API_BASE_URL"
        ],
        "additionalProperties": true
      }
    }
  ]
}
```