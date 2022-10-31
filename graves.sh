#!/bin/bash

# if --version, print and exit
if [[ $1 == *"--version"* ]]; then
    echo "1.0"
    exit 0
fi

# check args
if [ "$#" -ne 3 ]; then
    echo "oops, there should be three parameters to this script"
    echo "  usage: ./graves.sh <SPEC> <FILE> {ILP32,LP64}"
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
./bin/coveriteam --use-python-processes --input specification_path=$1 --input program_path=$2 --data-model=$3 verifier-parallel-portfolio.cvt
