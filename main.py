from pyvis.network import Network
import subprocess
import argparse
import yaml

'''
run using "python main.py -v [variable_name]
'''


YEAR = 2024

EXCLUDE_VARS = {
    "employment_income_before_lsr",
    "employment_income_behavioral_response",
    "spm_unit_size",
}

year_str = f"<{YEAR},"  # String to match the year in the output


def create_yaml_file(variable_name):
    data = [
        {
            "name": "Scenario",
            "period": YEAR,
            "input": {},
            "output": {variable_name: 0},
        }
    ]

    with open("test.yaml", "w") as file:
        yaml.dump(data, file)


def run_policy_engine():
    command = "policyengine-core test test.yaml -c policyengine_us -v"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else result.stderr


def nodes_and_edges(output: str):
    lines = output.split("\n")
    nodes = set()
    leaf_nodes = set()
    non_leaf_nodes = set()
    edges = []
    parent_stack = []

    for i in range(len(lines) - 1):
        line = lines[i]
        if "=" not in line or f"<{YEAR}," not in line:
            continue

        variable = line.split("=")[0].strip()
        # Remove the year and default tag
        variable = variable.replace(year_str, "").replace("(default)>", "").strip()

        if variable in EXCLUDE_VARS:
            continue

        current_indent = get_indent(line)

        # Determine if the next line is more indented
        next_line = lines[i + 1]
        next_indent = get_indent(next_line)

        nodes.add(variable)

        if len(parent_stack):
            edges.append((parent_stack[-1], variable))

        if current_indent > next_indent:
            parent_stack = parent_stack[: next_indent - 2]
        elif current_indent < next_indent:
            parent_stack.append(variable)

        if current_indent >= next_indent:
            leaf_nodes.add(variable)
        else:
            non_leaf_nodes.add(variable)

    leaf_nodes.difference_update(non_leaf_nodes)
    return nodes, edges, leaf_nodes


def get_indent(line: str):
    return int((len(line) - len(line.lstrip())) / 2)


parser = argparse.ArgumentParser()

parser.add_argument("-v", "--variable", help="variable name")

args = parser.parse_args()

create_yaml_file(args.variable)
output = run_policy_engine()

# Extract and display unique leaf nodes
nodes, edges, leaf_nodes = nodes_and_edges(output)

net = Network(
    height="100vh", directed=True, select_menu=True, neighborhood_highlight=True
)
Network.set_options(
    net,
    '''
    const options = {
        "physics": {
            "barnesHut": {
                "theta": 1,
                "centralGravity": 0,
                "springLength": 255,
                "springConstant": 0.06,
                "damping": 1,
                "avoidOverlap": 1
            },
            "minVelocity": 0.75
        }
    }
    '''
)

for node in nodes:
    if node in leaf_nodes:
        net.add_node(node, color="red")
    else:
        net.add_node(node)

for edge in edges:
    net.add_edge(edge[0], edge[1])

net.write_html("nx.html")
