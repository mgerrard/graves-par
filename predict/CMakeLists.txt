cmake_minimum_required(VERSION 3.10)
project(predict)

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
	PRIVATE ${TorchScatter_INCLUDE_DIR}
	PRIVATE ${TorchSparse_INCLUDE_DIR}
)

target_link_libraries(predict
    TorchScatter::TorchScatter TorchSparse::TorchSparse
)


set_property(TARGET predict PROPERTY CXX_STANDARD 14)