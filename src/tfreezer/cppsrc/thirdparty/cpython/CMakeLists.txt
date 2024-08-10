# Macro to get various python include / link flags.
macro(python_config option output_var)
    if(${ARGC} GREATER 2)
        set(is_list ${ARGV2})
    else()
        set(is_list "")
    endif()

    execute_process(
        COMMAND ${PYTHON_EXECUTABLE} "-m" "tfreezer.python_config"
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

python_config(--python-include-path PYTHON_INCLUDE_DIR)
python_config(--python-link-flags-cmake PYTHON_LINKING_DATA 0)
python_config(--python3-link-flags-cmake PYTHON3_LINKING_DATA 0)

if(${WIN32})
    python_config(--python-dll-path PYTHON_DLL)
    python_config(--python3-dll-path PYTHON3_DLL)
endif()

# Find and link to the python library.
list(GET PYTHON_LINKING_DATA 0 PYTHON_LIBDIR)
list(GET PYTHON_LINKING_DATA 1 PYTHON_LIB_BASENAME)
find_library(PYTHON_LIB ${PYTHON_LIB_BASENAME} PATHS ${PYTHON_LIBDIR} HINTS ${PYTHON_LIBDIR})
list(GET PYTHON3_LINKING_DATA 0 PYTHON3_LIBDIR)
list(GET PYTHON3_LINKING_DATA 1 PYTHON3_LIB_BASENAME)
find_library(PYTHON3_LIB ${PYTHON3_LIB_BASENAME} PATHS ${PYTHON3_LIBDIR} HINTS ${PYTHON3_LIBDIR})

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

target_include_directories(cpython::libpython
    INTERFACE
    ${PYTHON_INCLUDE_DIR}
)
