# Macro to get various python include / link flags.
macro(python_config option output_var)
    if(${ARGC} GREATER 2)
        set(is_list ${ARGV2})
    else()
        set(is_list "")
    endif()

    execute_process(
        COMMAND ${PYTHON_EXECUTABLE} "${CMAKE_CURRENT_SOURCE_DIR}/cpython_config.py"
        ${option}
        OUTPUT_VARIABLE ${output_var}
        OUTPUT_STRIP_TRAILING_WHITESPACE)

    if("${${output_var}}" STREQUAL "")
        message(FATAL_ERROR "Error: Calling tfreezer.python_config ${option} returned no output.")
    endif()

    if(is_list)
        string(REPLACE " " ";" ${output_var} "${${output_var}}")
    endif()
endmacro()

execute_process(
    COMMAND ${PYTHON_EXECUTABLE} "-c" "import sys;print('{}.{}.{}'.format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro))"
    OUTPUT_VARIABLE PYTHON_VERSION
    OUTPUT_STRIP_TRAILING_WHITESPACE)
string(REGEX MATCHALL "[0-9]+" _PYTHON_VERSION_LIST ${PYTHON_VERSION})
list(GET _PYTHON_VERSION_LIST 0 PYTHON_VERSION_MAJOR)
list(GET _PYTHON_VERSION_LIST 1 PYTHON_VERSION_MINOR)
list(GET _PYTHON_VERSION_LIST 2 PYTHON_VERSION_MICRO)
python_config(--extension-suffix PYTHON_EXTENSION_SUFFIX)
set(PYTHON_EXTENSION_SUFFIX "${PYTHON_EXTENSION_SUFFIX}" PARENT_SCOPE)
python_config(--python-include-path PYTHON_INCLUDE_DIR)
python_config(--python-link-flags-cmake PYTHON_LINKING_DATA 0)
if(PYTHON_VERSION VERSION_GREATER_EQUAL "3.0.0")
    python_config(--python3-link-flags-cmake PYTHON3_LINKING_DATA 0)
endif()

if(${WIN32})
    python_config(--python-dll-path PYTHON_DLL)
    if(PYTHON_VERSION VERSION_GREATER_EQUAL "3.0.0")
        python_config(--python3-dll-path PYTHON3_DLL)
    endif()
endif()

# Find and link to the python library.
list(GET PYTHON_LINKING_DATA 0 PYTHON_LIBDIR)
list(GET PYTHON_LINKING_DATA 1 PYTHON_LIB_BASENAME)
find_library(PYTHON_LIB ${PYTHON_LIB_BASENAME} PATHS ${PYTHON_LIBDIR} HINTS ${PYTHON_LIBDIR})
if(PYTHON_VERSION VERSION_GREATER_EQUAL "3.0.0")
    list(GET PYTHON3_LINKING_DATA 0 PYTHON3_LIBDIR)
    list(GET PYTHON3_LINKING_DATA 1 PYTHON3_LIB_BASENAME)
    find_library(PYTHON3_LIB ${PYTHON3_LIB_BASENAME} PATHS ${PYTHON3_LIBDIR} HINTS ${PYTHON3_LIBDIR})
endif()

add_library(cpython::libpython SHARED IMPORTED GLOBAL)

if(${WIN32})
    set_target_properties(cpython::libpython PROPERTIES
        IMPORTED_LOCATION ${PYTHON_DLL}
        IMPORTED_IMPLIB ${PYTHON_LIB}
    )
else()
    set_target_properties(cpython::libpython PROPERTIES
        IMPORTED_LOCATION ${PYTHON_LIB}
    )
endif()

if(NOT(${CMAKE_SYSTEM_NAME} STREQUAL "Darwin"))
    if(PYTHON_VERSION VERSION_GREATER_EQUAL "3.0.0")
        add_library(cpython::libpython3 SHARED IMPORTED GLOBAL)

        if(${WIN32})
            set_target_properties(cpython::libpython3 PROPERTIES
                IMPORTED_LOCATION ${PYTHON3_DLL}
                IMPORTED_IMPLIB ${PYTHON3_LIB}
            )
        else()
            set_target_properties(cpython::libpython3 PROPERTIES
                IMPORTED_LOCATION ${PYTHON3_LIB}
            )
        endif()
    endif()
endif()

target_include_directories(cpython::libpython
    INTERFACE
    ${PYTHON_INCLUDE_DIR}
)

