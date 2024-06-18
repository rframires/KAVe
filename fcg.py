import re
import matplotlib.pyplot as plt
import networkx as nx

def to_fcg(file_path, p = False):
    # Create an empty directed graph
    graph = nx.MultiDiGraph()
    graph.add_node("_main")

    # Read PHP code from a file or any other source
    with open(file_path, 'r') as file:
        php_code = file.read()

    # Extract user-defined function names using regular expressions
    function_definitions = re.findall(r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', php_code)

    main_calls = re.findall(r'(?<!function\s)([a-zA-Z_\x7f-\xff][a-zA-Z0-9_\x7f-\xff]*)\s*\(', php_code)
    main_calls = [x for x in main_calls if x in function_definitions]

    # Helper function to find function calls within a given function definition
    def find_function_calls(function_definition):
        function_code = re.search(r'function\s+' + re.escape(function_definition) + r'\s*\((.*?)\)\s*{(.+?)}', php_code, re.DOTALL)
        if function_code:
            function_body = function_code.group(2)
            function_calls = re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', function_body)
            function_calls = [x for x in function_calls if x in function_definitions]
            return function_calls
        return []

    # Build the graph
    for function in function_definitions:
        graph.add_node(function)

    # Find function calls and create edges in the graph
    for calling_function in function_definitions:
        function_calls = find_function_calls(calling_function)
        for called_function in function_calls:
            graph.add_edge(calling_function, called_function)

    for called_function in main_calls:
        graph.add_edge("_main", called_function)

    #if p then prints the graph
    if p:
        print(graph)
        nx.draw(graph, with_labels = True)
        plt.show()
                
    return graph