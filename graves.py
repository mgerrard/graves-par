#!/usr/bin/python3

import sys
import subprocess

#################################################
## Command line check

if "--version" in sys.argv:
    print("1.0")
    sys.exit(0)

three_args=False
if len(sys.argv) == 3:
    three_args=True
elif len(sys.argv) != 8:
    print("oops, expecting either three or eight parameters to this script")
    print("  basic usage: ./graves.py <C_FILE> <SPEC> {ILP32,LP64}")
    print("  sv-comp usage: ./graves.py verifier-parallel-portfolio.cvt --cache-dir cache --no-cache-update --use-python-processes
<C_FILE> <SPEC> {ILP32,LP64}")
    sys.exit(9)

#################################################
## Call graves selector
#if three_args:
#    graves_result=subprocess.check_output(["./predict/build/predict", "--model-location", "predict/dummy_model.pt", sys.argv[1]])
#else:
#    graves_result=subprocess.check_output(["./predict/build/predict", "--model-location", "predict/dummy_model.pt", sys.argv[6]])
    
debug=True
raw_str="cpa-seq,500,symbiotic,200"
graves_out=raw_str.split(",")
if(debug):
    print("graves output:"); print(graves_out)

#################################################
## Write CoVeriTeam language file for given tools

# parse list of tools from graves output
tools=[]
for i in range(0, len(graves_out), 2):
    tools.append(graves_out[i])

if(debug):
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

if(debug):
    print("(tool,mem) pairs:"); print(tool_mem_pairs)

for tool,mem_limit in tool_mem_pairs:
    print(tool); print(mem_limit);
    f_name=tool+"-resource-limitations.yml"
    f_str="resourcelimits:\n  memlimit: \""+str(mem_limit)+" MB\"\n  timelimit: \"15 min\"\n"
    with open(f_name, "w") as f:
        f.write(f_str)

##############################################
## Launch coveriteam harness

if three_args:
    print(subprocess.check_output(["./bin/coveriteam", "--input", "program_path="+sys.argv[1], "--input", "specification_path="+sys.argv[2], "--data-model="+sys.argv[3], "verifier-parallel-portfolio.cvt"]))
else:
    print(subprocess.check_output(["./bin/coveriteam", sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], "--input", "program_path="+sys.argv[6], "--input", "specification_path="+sys.argv[7], "--data-model="+sys.argv[8]]))
