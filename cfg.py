import matplotlib.pyplot as plt
import re
import dvg
import networkx as nx

#function that given a file or function returns a pdg
#if p == True prints the graph
def to_cfg(file, p = False):

    nodes = []
    depth = 0

    #For each line in the file or function
    for i in range(len(file)):

        #line contents
        line = file[i].rstrip()

        #label the line
        label = dvg.get_label(line, i)

        #the line is empty or contains only '{' or '}'
        x = re.search("^(}|{| )+$", line)

        #if the line is not empty 
        if len(line) > 0 and not x:

            #generates a node(line number, depth, return statment?, conditional statments?)
            nodes.append((i+1, depth, "return" in line, re.search("else|elif", line), label))

        #if contains '}'s reduces depth
        if "}" in line:
            depth -= line.count("}")

        #if contains '{'s increment depth
        if "{" in line:
            depth += line.count("{")

    #graph that will save the cfg
    g = nx.MultiDiGraph()

    #for each node
    for n in range(len(nodes)-1):

        #if the node depth is the same as the next
        if nodes[n][1] == nodes[n+1][1]:

            #add an edge between the nodes in the graph
            g.add_edge((nodes[n][0], nodes[n][4]), (nodes[n+1][0], nodes[n+1][4]), color = 'b')

        #otherwise it got inside a conditional statment or a cycle
        else:

            #x represents the forward nodes
            #it increase until the end of the file or if its depth is smaller than the current node
            x = n + 1
            
            keep = True
            
            keepIf = True

            #while x is not in the end of the file or if its depth is smaller than the current node
            while(x < len(nodes) and nodes[n][1]-1 <= nodes[x][1]):

                #if the current node is a return statment break
                if nodes[n][2]:
                    break

                #if the current node depth is -1 than the forward one it got inside the condition or the cycle
                elif (nodes[n][1] + 1 == nodes[x][1] and keep):

                        #add an edge between them 
                        if nodes[x][2]:
                            g.add_edge((nodes[n][0], nodes[n][4]), "return", color = 'b')
                        else:
                            g.add_edge((nodes[n][0], nodes[n][4]), (nodes[x][0], nodes[x][4]), color = 'b')

                        #dont add any more edges considering this criteria
                        keep = False

                #if the node is the same depth as the forward one it got outside the condition or the cycle
                elif (nodes[n][1] == nodes[x][1] and keepIf):

                        #add an edge between them 
                        if nodes[x][2]:
                            g.add_edge((nodes[n][0], nodes[n][4]), "return", color = 'b')
                        else:
                            g.add_edge((nodes[n][0], nodes[n][4]), (nodes[x][0], nodes[x][4]), color = 'b')

                        #dont create any more edges for the current node
                        break
                    
                #if the current node depth is +1 than the forward one it got outside the condition or the cycle
                #if the forward statment is not a conditional statment
                elif (nodes[n][1] == nodes[x][1] + 1 and not nodes[x][3]):

                        #add an edge between them 
                        if nodes[x][2]:
                            g.add_edge((nodes[n][0], nodes[n][4]), "return", color = 'b')
                        else:
                            g.add_edge((nodes[n][0], nodes[n][4]), (nodes[x][0], nodes[x][4]), color = 'b')

                        #dont create any more edges for the current node
                        break

                #if the forward statment is a conditional statment it breaks the conditional train
                #from now on it only links to nodes outside the train aka with -1 depth
                elif nodes[n][1] == nodes[x][1] + 1:
                    
                    keepIf = False

                #keeps travelling the forward nodes
                x += 1
                
    #if p then prints the graph
    if p:
        print(g)
        nx.draw(g, with_labels = True)
        plt.show()
                
    return g