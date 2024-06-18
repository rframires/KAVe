# main.py

import os
import sys
import time
import mlkg_assembler

global count_xss
global count_sqli
statistics = []

def main(path, type = False):

    start = time.perf_counter()

    # Checking if the path is a file or a directory
    if os.path.isfile(path):
        # If it's a file
        if path.endswith('.php'):
            # Process the single PHP file
            print(path)
            try:
                statistics.append(mlkg_assembler.find_vuls(path[:-4], type))
            except Exception as e:
                print("Number of vulnerabilities: 0\n\n")
        else:
            print("The provided file is not a PHP file.")

    elif os.path.isdir(path):
        # If it's a directory
        # Recursively search for PHP files
        files = [os.path.join(root, filename)
                 for root, dirs, files in os.walk(path)
                 for filename in files
                 if filename.endswith('.php')]
        files.sort()

        for file in files:
            print(file)
            try:
                statistics.append(mlkg_assembler.find_vuls(file[:-4], type))
            except Exception as e:
                print("Number of vulnerabilities: 0\n\n")
    else:
        print("The provided path does not exist.")

    load_vulstats()

    print("Total vulnerabilities found:\nXSS:", count_xss, "\nSQLi:", count_sqli)

    print_graphstats()

    end = time.perf_counter()
    elapsed = end - start
    print("\nElapsed time:", "{:.2f}".format(elapsed), "seconds")


def load_vulstats():
    try:
        global count_xss
        global count_sqli
        
        # Access the functions or variables from mlkg_assembler
        count_xss = mlkg_assembler.count_xss
        count_sqli = mlkg_assembler.count_sqli

        # Return the loaded variables
        return count_xss, count_sqli
    except ImportError as e:
        print("Error loading MLKG variables:", e)
        return None, None
    
def print_graphstats():
    
    print("\nGraph stats:")
    print("N grafos:", sum([x[0] for x in statistics]))
    print("N funcoes:", sum([x[1] for x in statistics]))
    print("N variaveis:", sum([x[2] for x in statistics]))
    print("N nós:", sum([x[3] for x in statistics]))
    print("N edges:", sum([x[4] for x in statistics]))

if __name__ == "__main__":
    if len(sys.argv) > 3:
        print("Usage: python main.py <path>")
    elif len(sys.argv) == 3:
        path = sys.argv[1]
        type = sys.argv[2]
        main(path, type)
    else:
        path = sys.argv[1]
        main(path)
 