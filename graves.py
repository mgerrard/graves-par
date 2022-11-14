#!/usr/bin/python3

import sys
import subprocess
import argparse

#################################################
## Command line check

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Graves-Par Verifier')

    parser.add_argument("--version", help="Version number", action='store_true')
    parser.add_argument("-p", "--program", help="The program to verify", type=str, required="--version" not in sys.argv)
    parser.add_argument("--spec", help="The program specification", type=str, required="--version" not in sys.argv)
    parser.add_argument("--data-model", help="The data model", type=str, required="--version" not in sys.argv, choices=['ILP32','LP64'])
    parser.add_argument("--cache-dir", help="Cache directory", type=str)
    parser.add_argument("--use-python-processes", help="Coveriteam Flag 1", action='store_true')
    parser.add_argument("--no-cache-update", help="Coveriteam Flag 2", action='store_true')
    parser.add_argument("--debug", help="Print Debug messages", action='store_true')

    args = parser.parse_args()
    if args.version:
        print("1.0")
        sys.exit(0)

    #################################################
    ## Call graves selector
    
    graves_result=subprocess.run(["./predict/build/predict", "--model-location", "predict/dummy_model.pt", args.program],capture_output=True)
    
    graves_out = graves_result.stdout.decode("UTF-8").strip().split(",")
    if args.debug:
        print("graves output:")
        print(graves_out)

    #################################################
    ## Write CoVeriTeam language file for given tools

    # parse list of tools from graves output
    tools=[]
    for i in range(0, len(graves_out), 2):
        tools.append(graves_out[i])

    if args.debug:
        print("tools:"); print(tools)

    def tool_string(i,tool):
        return "tool_"+str(i)+"=ActorFactory.create(ProgramVerifier, \"./actors/"+tool+"-parallel-portfolio-3.yml\", \"default\");\n"

    verifier_str="\n// Create verifier from external-actor definition file\n"
    for i,tool in enumerate(tools):
        verifier_str+=tool_string(i,tool)

    portfolio_substr=""
    for i in range(len(tools)):
        portfolio_substr+="tool_"+str(i)+","

    portfolio_str="\nportfolio = ParallelPortfolio("+portfolio_substr+"ELEMENTOF(verdict, {TRUE,FALSE}));"

    example_inputs="""

    // Prepare example inputs
    prog = ArtifactFactory.create(CProgram, program_path);
    spec = ArtifactFactory.create(BehaviorSpecification, specification_path);
    inputs = {'program':prog, 'spec':spec};"""

    footer="""

    print(portfolio);

    result = execute(portfolio, inputs);
    print(result);"""

    cvt_file_str=verifier_str+portfolio_str+example_inputs+footer
    with open("verifier-parallel-portfolio.cvt", "w") as f:
        f.write(cvt_file_str)

    ##############################################
    ## Write memory limits to file for given tools

    # parse list of (tool,memory_limit) pairs from graves output
    tool_mem_pairs=[]
    for i in range(0, len(graves_out), 2):
        tool_mem_pairs.append((graves_out[i], graves_out[i+1]))

    if args.debug:
        print("(tool,mem) pairs:"); print(tool_mem_pairs)

    for tool,mem_limit in tool_mem_pairs:
        f_name="./actors/"+tool+"-resource-limitations.yml"
        f_str="resourcelimits:\n  memlimit: \""+str(mem_limit)+" MB\"\n  timelimit: \"15 min\"\n"
        with open(f_name, "w") as f:
            f.write(f_str)
    ##############################################
    ## Launch coveriteam harness

    coveriteam_output = subprocess.run(args=["./bin/coveriteam", "--input", "program_path="+args.program, "--input", "specification_path="+args.spec, "--data-model="+args.data_model, "verifier-parallel-portfolio.cvt"], capture_output=True)

    print(coveriteam_output.stdout.decode("UTF-8"))
    # print(coveriteam_output.stderr.decode("UTF-8"))