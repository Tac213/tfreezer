cmake_minimum_required(VERSION 3.4...3.18)
project(tfreezer)

if(${WIN32})
    set(PYTHON_EXECUTABLE
        ${CMAKE_CURRENT_SOURCE_DIR}/.venv/Scripts/python.exe
    )
else()
    set(PYTHON_EXECUTABLE
        ${CMAKE_CURRENT_SOURCE_DIR}/.venv/bin/python
    )
endif()

set(ENTRY_MODULE_NAME "${CMAKE_CURRENT_SOURCE_DIR}/examples/basic_check/basic_check.py")
set(HIDDEN_IMPORTS "")
set(EXCLUDES "")
set(DATAS "")
set(TF_APP_NAME "basic_check")
set(TF_APPROOT_DIR "${CMAKE_CURRENT_SOURCE_DIR}")
set(TF_BUILD_DIR "${CMAKE_CURRENT_BINARY_DIR}")
set(TF_DEPLOY_DIR "${CMAKE_CURRENT_SOURCE_DIR}/dist")
set(TF_GENERATED_HEADERS_DIR "${TF_BUILD_DIR}/generated")
set(PROJECT_VERSION "1.0.0")

file(WRITE ${TF_BUILD_DIR}/paths "APPROOT = r\"${TF_APPROOT_DIR}\"
BUILD_DIR = r\"${TF_BUILD_DIR}\"
DEPLOY_DIR = r\"${TF_DEPLOY_DIR}\"
CPP_SRC = r\"${CMAKE_CURRENT_SOURCE_DIR}/src/tfreezer/cppsrc\"
GENERATED_HEADERS_DIR = r\"${TF_GENERATED_HEADERS_DIR}\"
FROZEN_MODULE_DIR = r\"${TF_GENERATED_HEADERS_DIR}/frozen_modules\"
FROZEN_MODULES_HEADER = r\"${TF_GENERATED_HEADERS_DIR}/frozen_modules/frozen_modules.h\"
PYTHON_EXE = r\"${PYTHON_EXECUTABLE}\"
CMAKE_EXE = r\"\"
")

add_subdirectory(src/tfreezer/cppsrc)
