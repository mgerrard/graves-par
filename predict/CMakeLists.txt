cmake_minimum_required(VERSION 3.10)
project(predict)

set(LLVM_LINK_COMPONENTS
  Support
)

add_subdirectory(graph-builder)

# LLVM.
find_package(LLVM 11.1 REQUIRED CONFIG)
include_directories(${LLVM_INCLUDE_DIRS})
add_definitions(${LLVM_DEFINITIONS})
llvm_map_components_to_libnames(llvm_libs Support Core Passes)

#Clang
find_package(Clang REQUIRED)
include_directories(${CLANG_INCLUDE_DIRS})
add_definitions(${CLANG_DEFINITIONS})

find_package(Python3 COMPONENTS Development)
find_package(Torch REQUIRED)
find_package(TorchScatter REQUIRED)
find_package(TorchSparse REQUIRED)

message(STATUS ${TorchScatter_INCLUDE_DIR})
message(STATUS ${TorchSparse_INCLUDE_DIR})

add_executable(predict main.cpp)

# We now need to link the TorchScatter and TorchSparse libraries
# to our executable. We can do that by using the
# TorchScatter::TorchScatter and TorchSparse::TorchSparse targets,
# which also adds all the necessary torch dependencies.
target_compile_features(predict PUBLIC cxx_range_for)

target_include_directories(predict
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}
    PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/graph-builder/src/c
	PRIVATE ${TorchScatter_INCLUDE_DIR}
	PRIVATE ${TorchSparse_INCLUDE_DIR}
)

target_link_libraries(predict
    PRIVATE
    TorchScatter::TorchScatter TorchSparse::TorchSparse
    clangAST
    clangBasic
    clangFrontend
    clangSerialization
    clangTooling
    clangASTMatchers
    utils
    ast
    icfg
    call
    data
    graph-builder
)


set_property(TARGET predict PROPERTY CXX_STANDARD 14)