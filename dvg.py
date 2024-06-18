import matplotlib.pyplot as plt
import re
import networkx as nx

def to_dvg(file, p = False):
    variables = {}
    braco = [0]*3 #ramifications
    camada = 0    #layer
    down = False
    down2 = False
    for i in range(len(file)):
        line = file[i].rstrip()
        if "}" in line:
            camada -= line.count("}")

        if "else" in line or "elseif" in line or "if" in line or "case" in line:
            braco[camada] += 1
            if not "{" in line:
                down = True
        if "$" in line:
            if abs(camada) + 1 >= len(braco) - 1:
                braco += [0]*abs(camada)
            index = line[line.index('$'):]
            varss = get_vars(line)
            label = get_label(line, i)
            for var in varss:
                if str(var) not in variables:
                    variables[str(var)] = [(i+1, 0, camada, braco[camada-1], label)]
                else:
                    eq = index.find("=")
                    versao = variables[str(var)][-1][1]

                    if eq != -1 and index[eq-1] not in "><!=" and line[0:eq+1].count(var) == 1 and line.count(var) == 1:
                        variables[str(var)].append((i+1, versao + 1, camada, braco[camada-1], label, True))
                    else:
                        variables[str(var)].append((i+1, versao, camada, braco[camada-1], label, False))

        if "{" in line:
            camada += line.count("{")
        if down2:
            camada -= 1
            down2 = False
        if down:
            camada += 1
            down = False
            down2 = True

    graphs = []

    
    for var in variables:
        repeated = [x[0] for x in variables[var]]
        g = nx.MultiDiGraph()
        nodes = variables[var]

        for n in range(len(nodes)-1):
            for k in range(n+1, len(nodes)):


                if (not(nodes[n][2] == nodes[k][2] and nodes[n][3] != nodes[k][3]) and
                    not (nodes[n][2] == nodes[k][2] and nodes[n][1] != nodes[k][1])):

                    if nodes[n][2] > nodes[k][2] and not nodes[k][5]:

                        g.add_edge((nodes[n][0], nodes[n][4]), (nodes[k][0], nodes[k][4]))
                        break
                        
                    if ((not nodes[n][1] != nodes[k][1] or repeated.count(nodes[k][0]) >= 2) and
                        not nodes[n][0] == nodes[k][0]):
                            g.add_edge((nodes[n][0], nodes[n][4]), (nodes[k][0], nodes[k][4]))
        
        if p and var == "$tainted":
            plt.clf()
            nx.draw(g, with_labels = True)
            plt.show()
        graphs.append((var,g))

    return graphs

def get_label(line, i):
    
    label = ""

    entry_point = ["$_GET", "$_POST", "$_COOKIE", "$_REQUEST",
        "$_HTTP_GET_VARS", "$_HTTP_POST_VARS",
        "$_HTTP_COOKIE_VARS", "$_HTTP_REQUEST_VARS",
        "$_FILES", "$_SERVER", "$_SESSION", "$_ENV" "$argv", "$argc",
        "$_HTTP_RAW_POST_DATA", "$HTTP_ENV_VARS", "$GLOBALS"]
    
    sqli_sanitization = ["mysql_escape_string", "mysql_real_escape_string",
        "mysqli_escape_string", "mysqli_real_escape_string",
        "mysqli_stmt_bind_param", "mysqli::escape_string",
        "mysqli::real_escape_string", "mysqli_stmt::bind_param", "floatval", "intval", "preg_replace"]

    xss_sanitization = ["htmlentities", "htmlspecialchars", "strip_tags", "urlencode"]

    sqli_sink = ["mysql_query", "mysql_unbuffered_query", "mysql_db_query",
        "mysqli_query", "mysqli_real_query", "mysqli_master_query",
        "mysqli_multi_query", "mysqli_stmt_execute", "mysqli_execute",
        "mysqli::query", "mysqli::multi_query", "mysqli::real_query",
        "mysqli_stmt::execute"]

    xss_sink = ["echo", "print", "printf", "sprintf", "vprintf", "die", "exit",
        "file_put_contents", "file_get_contents", "vfprintf", "fprintf", "fscanf"]

    func = [x for x in sqli_sanitization if x in line]
    if func:
        label = ("sqli_sanitization", tuple(get_vars_func(line, func[0])), i, label)
        if func[0] == "(int)" or func[0] == "(float)":
            label = ("sqli_sanitization", tuple(get_var_casted(line, func[0][1:-1])), i, label)

    func = [x for x in xss_sanitization if x in line]
    if func:
        label = ("xss_sanitization", tuple(get_vars_func(line, func[0])), i, label) 

    func = [x for x in sqli_sink if x in line]
    if func:
        label = ("sqli_sink", tuple(get_vars_func(line, func[0])), i, label)

    func = [x for x in xss_sink if x in line]
    if func:
        label = ("xss_sink", tuple(get_vars_func(line, func[0])), i, label)

    func = [x for x in entry_point if x in line]
    if func:
        label = ("entry_point", get_entry(line), i, label)

    if "(int)" in line:
        label = ("cast_sanitization", tuple(get_var_casted(line, "int")), i, label)

    if "(float)" in line:
        label = ("cast_sanitization", tuple(get_var_casted(line, "float")), i, label)

    return label


def get_entry(line):

    newline = line
    var = newline[newline.index('$'):]
    
    match = re.search(r'\W', var[1:])

    if match:
        end = match.start()
    else:
        end = len(var[1:]) - 1
    end = var[0:end+1]
    return end

def get_vars(line):

    pattern = r'\$(?!_)\w+'  
    return re.findall(pattern, line)


def get_vars_func(line, func):

    newline = line[line.find(func)+len(func):]

    if func != "print":
        newline = newline[:newline.find(")")+1]

    ret = get_vars(newline)
    return ret

def get_var_casted(php_code, casting_type):
    # Define a regular expression pattern to match casting operations
    pattern = r'\(\s*' + casting_type + r'\s*\)\s*\$([a-zA-Z_\x7f-\xff][a-zA-Z0-9_\x7f-\xff]*)\s*;'

    # Search for the pattern in the PHP code
    match = re.search(pattern, php_code)

    # If a match is found, return the variable name
    if match:
        return ["$" + match.group(1)]
    else:
        return None