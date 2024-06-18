# KAVe

The KAVe tool is a Knowledge-based Multi-Agent System designed for web vulnerability detection. It operates by employing a multi-layer knowledge graph (MLKG) combined with a multi-agent system (MAS) to effectively and efficiently identify vulnerabilities in web applications. This approach allows KAVe to analyze the interconnected representations of the application's source code, including lexical and semantic features, data and control flows, and function calls, while integrating security properties associated with vulnerabilities. The MAS component enables dynamic and autonomous vulnerability detection through static taint analysis, leveraging the MLKG to pinpoint potential security issues. The tool has demonstrated high precision and efficiency in detecting vulnerabilities, notably in PHP web applications, by reducing false positives and optimizing the detection process.

# Installation

Download the code into your desired location.

# Execution

Before trying to execute the tool make sure all the dependencies listed below are installed in your system.

To execute KAVe, open a terminal inside the folder where the code is located and execute the main.py file with the file/folder you wish to verify as parameter. Examples:

To examine a folder:
> python3 main.py /folder1 <br>

To examine a file:
> python3 main.py /folder1/file1.php <br>

There is the option to only look for a specific type of vulnerability either xss or sqli, the default is both. Examples:

To search for both:
> python3 main.py /folder1/file1.php <br>

To search for only sqli:
> python3 main.py /folder1/file1.php sqli <br>

To search for only xss:
> python3 main.py /folder1/file1.php xss <br>

### Dependencies
- python3
- matplotlib
- networkx
