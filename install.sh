#!/bin/bash

pushd depends

if [ ! -d depends/libtorch ]; then
    echo "Collecting Pytorch"
    wget https://download.pytorch.org/libtorch/cpu/libtorch-cxx11-abi-shared-with-deps-1.12.1%2Bcpu.zip
    echo

    echo "Extracting Pytorch"
    if unzip libtorch-cxx11-abi-shared-with-deps-1.12.1+cpu.zip ; then
        echo
    else
        echo "Couldn't extract libtorch; Exiting"
        exit 1
    fi
fi

if [ ! -d depends/torch-scatter-install ]; then
    echo "Building torch-scatter"
    mkdir pytorch_scatter/build
    pushd pytorch_scatter/build
    cmake -DTorch_DIR="$PWD/../../libtorch/share/cmake/Torch/" -DCMAKE_INSTALL_PREFIX="$PWD/../../torch-scatter-install"  ..
    if make install -j4; then
        echo "Built torch-scatter"
        popd
        echo
    else   
        echo "Failed to build torch-sscatter; exiting"
        exit 1
    fi
fi

if [ ! -d depends/torch-sparse-install ]; then
    echo "Building torch-sparse"
    mkdir pytorch_sparse/build
    pushd pytorch_sparse/build
    cmake -DTorch_DIR="$PWD/../../libtorch/share/cmake/Torch/" -DCMAKE_INSTALL_PREFIX="$PWD/../../torch-sparse-install"  ..
    if make install -j4; then
        echo "Built torch-sparse"
        popd
        echo
    else   
        echo "Failed to build torch-sparse; exiting"
        exit 1
    fi
fi 

popd

if [ ! -d predict/build ]; then
    mkdir predict/build
fi

pushd predict/build

if [ ! -f predict ]
    echo "Building predictor"
    cmake .. -DTorchScatter_DIR="$PWD/../../depends/torch-scatter-install/share/cmake/TorchScatter" -DTorchSparse_DIR="$PWD/../../depends/torch-sparse-install/share/cmake/TorchSparse" -DTorch_DIR="$PWD/../../depends/libtorch/share/cmake/Torch"
    if make -j4; then
        echo "Built predictor"
        popd
        echo
    else   
        echo "Failed to build predict; exiting"
        exit 1
    fi
fi