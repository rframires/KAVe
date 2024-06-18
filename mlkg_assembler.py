import pdg
import re
import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing import nx_agraph
import fcg
import agents

kg = {}
functions = []
count_sqli = 0
count_xss = 0

def removeComments(file_path):
    with open(file_path, 'r') as file:
        contents = file.read()

    comment_pattern = r"(?s)//.*?\n|/\*.*?\*/"

    no_comments = re.sub(comment_pattern, '\n', contents)

    no_empty_lines = [line.strip() for line in no_comments.splitlines() if line.strip()]

    return no_empty_lines

def remove_html_comments(lines):
    in_comment = False
    cleaned_lines = []

    for line in lines:
        if '<!--' in line:
            in_comment = True
            continue
        elif '-->' in line:
            in_comment = False
            continue
        
        if not in_comment:
            cleaned_lines.append(line)

    return cleaned_lines

def is_sanitized(node):

    if "sanitization" in node[0]:
        return True
    elif node[3] != '':
        return is_sanitized(node[3])
    return False

def find_vuls(path, type = False):

    g = fcg.to_fcg(path + ".php", False)
    file = remove_html_comments(removeComments(path + ".php"))

    global kg
    global functions
    global count_sqli
    global count_xss
    
    kg = {}
    functions = {}
    main = []

    nodes = [x[0] for x in list(g.nodes.data())]

    pilha = -1
    rem = False
    for l in file:
        x = re.search("^function", l)
        if x:
            if l.count("{") == 0:
                rem = True
            pilha = 1
        elif pilha > 0:
            if rem:
                rem = False
                pilha -= 1
            pilha += l.count("{")
            pilha -= l.count("}")
        if pilha == 0:
            pilha = -1
        elif pilha == -1:
            main.append(l) 

    functions["_main"] = main
    kg["_main"] = pdg.to_pdg(main, False)

    for n in nodes[1:]:

        pilha = -1
        function = []
        for l in file:
            x = re.search("^function.*"+ n, l)
            if x:
                pilha = 1
                function.append(l)
            elif pilha > 0:
                pilha += l.count("{")
                pilha -= l.count("}")
                function.append(l)
            if pilha == 0:
                functions[n] = function
                p = pdg.to_pdg(function)
                kg[n] = p
                if len(p[1]) == 0 and not p[2]:
                    g.remove_node(n)
                elif len(p[1]) == 0:
                    kg[n] = p + "connector"
                else:
                    kg[n] = p
                break

    grafos = sum([x[3] + 2 for x in kg.values()]) + 1
    funcoes = len(functions)
    variaveis = sum([x[3] for x in kg.values()])
    nos = sum([len(x[0].nodes()) for x in kg.values()]) +len(g.nodes())
    edges = sum([len(x[0].edges()) for x in kg.values()]) + len(g.edges())

    possible_vulnerabilities = []
    vulnerabilities = []

    agents.load_mlkg()

    for func in kg:
        colors = nx.get_edge_attributes(kg[func][0],'color').values()
        nx.draw(kg[func][0], with_labels = True, edge_color=colors)
        if len(kg[func][1]) > 0:
            for y in [z for z in kg[func][1] if z[0] == "entry_point"]:
                    if not is_sanitized(y):
                        travel_agent = agents.TravelAgent("Travel Agent", g, kg, y[:3])
                        possible_vulnerabilities += travel_agent.start_traversal([func])
                        if y[3] and "sink" in y[3][0] and (not type or y[3] and type in y[3][0]):
                            vulnerabilities.append((True, y, y, func))
                            if "xss" in y[3][0]:
                                count_xss+=1
                            if "sqli" in y[3][0]:
                                count_sqli+=1

    for trial in possible_vulnerabilities:
        for sink in trial[1]:
            if not type or type in sink[0]:
                if not is_sanitized(sink):
                    verification_agent = agents.VerificationAgent(0, trial[0], sink, trial[2])
                    vulnerabilities.append(verification_agent.start_verification(trial[2], trial[0][1]))
                    

    vuls = len([x for x in vulnerabilities if x[0]])
    print("Number of vulnerabilities:", len([x for x in vulnerabilities if x[0]]))
    i = 1
    for vul in vulnerabilities:
        if vul[0]:
            print(i, ":", vul[1:3])
            if "xss" in vul[2][0]:
                count_xss+=1
            if "sqli" in vul[2][0]:
                count_sqli+=1
            i+=1

    print("\n")

    return (grafos, funcoes, variaveis, nos, edges, vuls > 0) 
