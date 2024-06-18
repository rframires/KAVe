import re
import dvg
import mlkg_assembler

# Global variables
global kg, functions
entry_points = [
    "$_GET", "$_POST", "$_COOKIE", "$_REQUEST",
    "$_HTTP_GET_VARS", "$_HTTP_POST_VARS",
    "$_HTTP_COOKIE_VARS", "$_HTTP_REQUEST_VARS",
    "$_FILES", "$_SERVER", "$_SESSION", "$_ENV",
    "$argv", "$argc", "$_HTTP_RAW_POST_DATA",
    "$HTTP_ENV_VARS", "$GLOBALS"
]

# Load MLKG (Machine Learning Knowledge Graph) variables
def load_mlkg():
    try:
        global kg, functions
        functions = mlkg_assembler.functions
        kg = mlkg_assembler.kg
        return functions, kg
    except ImportError as e:
        print("Error loading MLKG variables:", e)
        return None, None

# Represents an agent that receives and processes messages
class Agent:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.inbox = []

    def receive_message(self, message):
        self.inbox.append(message)

    def process_messages(self):
        for message in self.inbox:
            # Process received messages
            content = message.get('content', {})
            sender = message.get('sender')
            
            if 'path_request' in content:
                # Handle path requests
                path = content['path']
                print(f"Agent {self.agent_id} received a path request: {path} from {sender}")
            else:
                print(f"Agent {self.agent_id} received an unknown message from {sender}")

        self.inbox = []

    def send_message(self, recipient, content):
        # Send messages to other agents
        message = {'sender': self.agent_id, 'content': content}
        recipient.receive_message(message)

# Represents an agent that traverses the call graph
class TravelAgent(Agent):
    def __init__(self, agent_id, call_graph, knowledge_graph, entry):
        super().__init__(agent_id)
        self.call_graph = call_graph
        self.knowledge_graph = knowledge_graph
        self.entry = entry

    # Process messages specifically for path requests
    def process_messages(self):
        for message in self.inbox:
            if 'path_request' in message['content']:
                path = message['content']['path']
                sender = message['sender']
                results = self.start_traversal(path)
                self.send_message(sender, {'results': results})

    # Start traversal through the call graph
    def start_traversal(self, path):
        agent = TravelAgent(f"{self.agent_id}_sub", self.call_graph, self.knowledge_graph, self.entry)
        return agent.travel_path(path)
    
    # Method for traversing a path
    def travel_path(self, path):
        var = []
        if path[-1] in self.knowledge_graph.keys():
            var.append((
                self.entry + tuple([path[0]]),
                [x for x in self.knowledge_graph[path[-1]][1] if "sink" in x[0]],
                path.copy()
            ))

        last_node = path[-1]
        for n in list(self.call_graph.successors(last_node)):
            if n not in path:
                agent = TravelAgent(f"{self.agent_id}_{n}", self.call_graph, self.knowledge_graph, self.entry)
                var.extend(agent.travel_path(path + [n]))

        return var


# Represents an agent for verification
class VerificationAgent(Agent):
    def __init__(self, agent_id, entry, sink, pathprint):
        super().__init__(agent_id)
        self.entry = entry
        self.sink = sink
        self.pathprint = pathprint

    def process_messages(self):
        for message in self.inbox:
            if 'verification_request' in message['content']:
                path = message['content']['path']
                var = message['content'].get('var')
                sender = message['sender']
                results = self.start_verification(path, var)
                self.send_message(sender, {'results': results})

    def start_verification(self, path, var):
        agent = VerificationAgent(f"{self.agent_id}_sub", self.entry, self.sink, self.pathprint)
        return agent.verify_path(path, var)

    def verify_path(self, path, var):
        var_list = []
        if not path:
            return (False, self.entry, self.sink)

        if len(path) == 1:
            start_node, target_var = (
                (self.get_node(kg[path[0]][0], self.entry[2]), self.entry[1])
                if path[0] == self.entry[3] else
                (self.get_node(kg[path[0]][0], 0), var if var else "-")
            )

            pdg = kg[path[0]][0]
            data_agent = DataAgent(pdg, [target_var], self.sink, path[0])
            flow_agent = FlowAgent(pdg, self.sink)

            return (
                data_agent.data(start_node) == "vulnerable" and
                flow_agent.flow(start_node) == "vulnerable",
                self.entry, self.sink, path, self.pathprint
            )

        translation_agent = TranslationAgent()

        translations = (
            translation_agent.translate(kg[path[0]][0],
                                        self.get_node(kg[path[0]][0], self.entry[2]) if path[0] == self.entry[3] else
                                        self.get_node(kg[path[0]][0], 0), var, path[0], path[1])
        ) if path[0] == self.entry[3] else (
            translation_agent.translate(kg[path[0]][0], self.get_node(kg[path[0]][0], 0), var, path[0], path[1])
        )

        if not translations:
            translations.append("")

        for n in list(self.call_graph.successors(path[-1])):
            if n not in path:
                agent = VerificationAgent(f"{self.agent_id}_{n}", self.entry, self.sink, self.pathprint)
                var_list.extend(agent.verify_path(path + [n], translations[-1]))

        return var_list

    def get_node(self, graph, index):
        return [n for n in graph if n[0] == index + 1][0]


# Represents an agent for translation
class TranslationAgent(Agent):
    def __init__(self, agent_id):
        super().__init__(agent_id)
        self.trans = []
        self.visited = []

    def process_messages(self):
        for message in self.inbox:
            if 'translation_request' in message['content']:
                pdg = message['content']['pdg']
                node = message['content']['node']
                var = message['content']['var']
                func = message['content']['func']
                prox = message['content']['prox']
                sender = message['sender']
                results = self.translate(pdg, node, var, func, prox)
                self.send_message(sender, {'results': results})

    def translate(self, pdg, node, var, func, prox):
        if not pdg.successors(node):
            return [""]

        for n in [node] + [x for x in pdg.successors(node) if x != "return"]:
            line = functions[func][n[0] - 1]
            func_call = re.compile(r'\b' + prox + r'\b').search(line)

            if func_call and n not in self.visited:
                possible_vars = dvg.get_vars_func(line, prox)

                if var in possible_vars:
                    self.trans.append(dvg.get_vars_func(functions[prox][0], prox)[possible_vars.index(var)])
                elif var in entry_points and self.index_entry(line, var) != -1:
                    self.trans.append(dvg.get_vars_func(functions[prox][0], prox)[self.index_entry(line, var)])

                self.visited.append(n)

            if n != node:
                agent = TranslationAgent(f"{self.agent_id}_{n}")
                self.trans.extend(agent.translate(pdg, n, var, func, prox))

        return self.trans

    def index_entry(self, line, var):
        if "=" in line:
            line = line.split("=")[1]

        x = -1
        while var in line:
            x += 1
            line = line[line.index("$") + 1:]

        return x


# Represents an agent for handling data
class DataAgent:
    
    def __init__(self, current_pdg, target_vars, sink, func):
        self.current_pdg = current_pdg
        self.target_vars = target_vars
        self.sink = sink
        self.func = func
        self.visited = []

    # Method to handle data flow
    def data(self, current_node):
        successors = self.current_pdg.successors(current_node)

        if not successors:
            return ""

        for successor in [s for s in successors if s != "return"]:
            if successor[1] != '' and "sanitization" in successor[1][0] and successor[1][1][0] in self.target_vars:
                self.target_vars.remove(successor[1][1][0])

            self.update_dependents(self.target_vars, functions[self.func][successor[0] - 1])

            if (
                successor not in self.visited and
                self.get_edge_type(self.current_pdg, current_node, successor) != "b" and
                len([x for x in self.target_vars if x in self.get_edge_data(self.current_pdg, current_node, successor)]) > 0
            ):

                if successor[1] == self.sink:
                    return "vulnerable"

                self.visited.append(successor)

                value = self.data(successor)
                if value:
                    return value

        return ""

    # Update dependent variables
    def update_dependents(self, target_vars, line):
        for t in target_vars:
            dependents = self.get_dependent_variables(line, t)
            if dependents and dependents not in target_vars:
                target_vars.append(dependents)

    # Get dependent variables from a line
    def get_dependent_variables(self, line, right_variable):
        sides = line.split("=", 1)
        if len(sides) > 1:
            if right_variable in sides[1] and right_variable not in sides[0]:
                pattern = r'\$([^\s]+)'
                match = re.search(pattern, sides[0])

                if match:
                    return match.group(0).strip()

        return ''

    # Get edge data from the graph
    def get_edge_data(self, graph, n1, n2):
        labels = [
            x[2].get("label") for x in graph.edges(data=True)
            if x[0] == n1 and x[1] == n2
        ][0]

        if labels:
            return [x[2].get("label") for x in graph.edges(data=True) if x[0] == n1 and x[1] == n2][0].split(".")

        return []

    # Get edge type from the graph
    def get_edge_type(self, graph, n1, n2):
        return [x[2].get("color") for x in graph.edges(data=True) if x[0] == n1 and x[1] == n2][0]

# Represents an agent for handling flow
class FlowAgent:
    
    def __init__(self, current_pdg, sink):
        self.current_pdg = current_pdg
        self.sink = sink
        self.visited = []

    # Method to handle flow traversal
    def flow(self, current_node):
        successors = self.current_pdg.successors(current_node)

        if not successors:
            return ""

        for successor in [s for s in successors if s != "return"]:
            if (
                successor not in self.visited and
                self.get_edge_type(self.current_pdg, current_node, successor) != "r"
            ):
                if successor[1] == self.sink:
                    return "vulnerable"

                self.visited.append(successor)
                value = self.flow(successor)
                if value:
                    return value

        return ""

    # Get edge type from the graph
    def get_edge_type(self, graph, n1, n2):
        return [x[2].get("color") for x in graph.edges(data=True) if x[0] == n1 and x[1] == n2][0]
