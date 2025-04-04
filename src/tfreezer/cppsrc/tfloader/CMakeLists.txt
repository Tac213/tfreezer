cmake_minimum_required(VERSION 3.4...3.18)
project(tfloader VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 20)

option(TFLOADER_BUILTIN "Whether to build tfloader as a builtin python module." OFF)

if(NOT DEFINED PYTHON_EXECUTABLE)
    message(FATAL_ERROR "PYTHON_EXECUTABLE is not set.")
endif()

if(NOT TARGET cpython::libpython)
    add_subdirectory(cpython)
endif()

set(_tfloader_sources
    ${CMAKE_CURRENT_SOURCE_DIR}/include/tfloader/tfloader.h
    ${CMAKE_CURRENT_SOURCE_DIR}/src/tfloader.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/package_loader.h
)
if(${WIN32})
    list(APPEND _tfloader_sources
        ${CMAKE_CURRENT_SOURCE_DIR}/src/package_loader_win32.cpp
    )
endif()

if(TFLOADER_BUILTIN)
    add_library(tfloader STATIC ${_tfloader_sources})
else()
    add_library(tfloader SHARED ${_tfloader_sources})
    set_target_properties(
        tfloader
        PROPERTIES
        SUFFIX "${PYTHON_EXTENSION_SUFFIX}"
    )
    add_custom_command(TARGET tfloader POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:tfloader> ${CMAKE_LIBRARY_OUTPUT_DIRECTORY}
        COMMAND_EXPAND_LISTS
    )
endif()


target_include_directories(
    tfloader
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
)
target_link_libraries(
    tfloader
    PRIVATE
        cpython::libpython
)
target_compile_definitions(
    tfloader
    PRIVATE
        TFLOADER_VERSION="${PROJECT_VERSION}"
)
