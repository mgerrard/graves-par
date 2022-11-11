#!/bin/bash

# if --version, print and exit
if [[ $1 == *"--version"* ]]; then
    echo "1.0"
    exit 0
fi

THREE_ARGS=false;
# check args
if [ "$#" -eq 3 ]; then
    THREE_ARGS=true;
elif [ "$#" -ne 8 ]; then
    echo "oops, expecting either three or eight parameters to this script"
    echo "  basic usage: ./graves.sh <C_FILE> <SPEC> {ILP32,LP64}"
    echo "  sv-comp usage: ./graves.sh verifier-parallel-portfolio.cvt --cache-dir cache --no-cache-update --use-python-processes
<C_FILE> <SPEC> {ILP32,LP64}"
    exit 9
fi

# call graves selector
if [ "$THREE_ARGS"=true ]; then
    graves_result=`./predict/build/predict --model-location predict/dummy_model.pt $1`
else
    graves_result=`./predict/build/predict --model-location predict/dummy_model.pt $6`
fi

# parse tool from selector (from {cpa-seq,symbiotic,esbmc-kind})
arr_result=(${graves_result//,/ })
tool1=${arr_result[0]}
tool2=${arr_result[1]}
tool3=${arr_result[2]}

# write selected tools to expected 'coverilang' file
sed -e "s/REPLACE1/$tool1/g" -e "s/REPLACE2/$tool2/g" -e "s/REPLACE3/$tool3/g" graves-template.cvt > verifier-parallel-portfolio.cvt

# launch coveriteam harness
if [ "$THREE_ARGS"=true ]; then
    ./bin/coveriteam --input program_path=$1 --input specification_path=$2 --data-model=$3 verifier-parallel-portfolio.cvt
else
    ./bin/coveriteam $1 $2 $3 $4 $5 --input program_path=$6 --input specification_path=$7 --data-model=$8
fi
