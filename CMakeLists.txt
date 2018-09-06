cmake_minimum_required(VERSION 2.8.12)

project(cmake_wrapper)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup(KEEP_RPATHS)
set(CMAKE_MACOSX_RPATH ON)

include(CMakeLists_original.txt)
