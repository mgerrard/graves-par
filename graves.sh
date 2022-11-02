#!/bin/bash

# if --version, print and exit
if [[ $1 == *"--version"* ]]; then
    echo "1.0"
    exit 0
fi

# check args
if [ "$#" -ne 8 ]; then
    echo "oops, expecting eight parameters to this script"
    echo "  usage: ./graves.sh verifier-parallel-portfolio.cvt --cache-dir cache --no-cache-update --use-python-processes
<C_FILE> <SPEC> {ILP32,LP64}"
    exit 9
fi

# call graves selector
graves_result=`./predict/build/predict predict/dummy_model.pt`

# parse tool from selector (from {cpa-seq,symbiotic,esbmc-kind})
arr_result=(${graves_result//,/ })
tool1=${arr_result[0]}
tool2=${arr_result[1]}

# write selected tools to expected 'coverilang' file
sed -e "s/REPLACE1/$tool1/g" -e "s/REPLACE2/$tool2/g" graves-template.cvt > verifier-parallel-portfolio.cvt

# launch coveriteam harness
./bin/coveriteam $1 $2 $3 $4 $5 --input program_path=$6 --input specification_path=$7 --data-model=$8
