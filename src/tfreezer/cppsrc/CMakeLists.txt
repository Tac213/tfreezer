cmake_minimum_required(VERSION 3.4...3.18)
project(${TF_APP_NAME})

set(CMAKE_CXX_STANDARD 20)

option(NEED_CONSOLE "Whether to build a console application." ON)
option(FREEZE_APPLICATION "Whether to freeze the python application." OFF)

if(NOT DEFINED PYTHON_EXECUTABLE)
    message(FATAL_ERROR "PYTHON_EXECUTABLE is not set.")
endif()

add_subdirectory(thirdparty)

set(SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/main.cpp
)

if(FREEZE_APPLICATION)
    if(NOT DEFINED TF_BUILD_DIR)
        message(FATAL_ERROR "TF_BUILD_DIR is not defined")
    endif()

    if(NOT DEFINED ENTRY_MODULE_NAME)
        if(NOT EXISTS ${TF_BUILD_DIR}/entry_module)
            message(FATAL_ERROR "Neither ENTRY_MODULE_NAME nor ${TF_BUILD_DIR}/entry_module is set.")
        endif()

        set(ENTRY_MODULE_NAME "${TF_BUILD_DIR}/entry_module")
    endif()

    if(NOT DEFINED HIDDEN_IMPORTS)
        if(NOT EXISTS ${TF_BUILD_DIR}/hidden_imports)
            message(FATAL_ERROR "Neither HIDDEN_IMPORTS nor ${TF_BUILD_DIR}/hidden_imports is set.")
        endif()

        set(HIDDEN_IMPORTS "${TF_BUILD_DIR}/hidden_imports")
    endif()

    if(NOT DEFINED EXCLUDES)
        if(NOT EXISTS ${TF_BUILD_DIR}/excludes)
            message(FATAL_ERROR "Neither EXCLUDES nor ${TF_BUILD_DIR}/excludes is set.")
        endif()

        set(EXCLUDES "${TF_BUILD_DIR}/excludes")
    endif()

    if(NOT DEFINED TF_APPROOT_DIR)
        message(FATAL_ERROR "TF_APPROOT_DIR is not defined")
    endif()

    # Get frozen header file names
    execute_process(
        COMMAND ${PYTHON_EXECUTABLE} "-m" "tfreezer.generate_frozen_modules" "--get-frozen-header-file-names"
        "${TF_BUILD_DIR}"
        "${ENTRY_MODULE_NAME}" "--hidden-imports=${HIDDEN_IMPORTS}" "--excludes=${EXCLUDES}"
        RESULT_VARIABLE _resullt
        WORKING_DIRECTORY ${TF_APPROOT_DIR}
    )

    if(${_resullt})
        message(FATAL_ERROR "Failed to get frozen header file names.")
    endif()

    if(NOT EXISTS ${TF_BUILD_DIR}/frozen_headers)
        message(FATAL_ERROR "File '${TF_BUILD_DIR}/frozen_headers' was not generated.")
    endif()

    file(READ ${TF_BUILD_DIR}/frozen_headers _frozen_headers)
    string(STRIP "${_frozen_headers}" _frozen_headers)

    add_custom_command(
        OUTPUT ${_frozen_headers}
        COMMAND
        ${CMAKE_CROSSCOMPILING_EMULATOR} ${PYTHON_EXECUTABLE} "-m" "tfreezer.generate_frozen_modules" "--make-freeze"
        "${TF_BUILD_DIR}"
        "${ENTRY_MODULE_NAME}"
        WORKING_DIRECTORY
        ${TF_APPROOT_DIR}
        COMMENT
        "Generating frozen module headers"
    )

    set(SOURCES
        ${SOURCES}
        ${_frozen_headers}
    )
endif()

# Add icons
if(DEFINED PROJECT_ICON AND NOT ${PROJECT_ICON} STREQUAL "")
    include(${CMAKE_CURRENT_SOURCE_DIR}/cmake/add_icon_to_binary.cmake)
    add_icon_to_binary(SOURCES ICONS
        ${PROJECT_ICON}

        # Add MacOS icns file if you have one
        # ${CMAKE_CURRENT_SOURCE_DIR}/resource/icon.icns
    )
endif()

add_executable(${PROJECT_NAME}
    ${SOURCES}
)

if(NOT DEFINED TF_GENERATED_HEADERS_DIR)
    message(FATAL_ERROR "TF_GENERATED_HEADERS_DIR needs to be set.")
endif()

target_include_directories(${PROJECT_NAME}
    PRIVATE
    ${TF_GENERATED_HEADERS_DIR}
)

if(NEED_CONSOLE)
    target_compile_definitions(${PROJECT_NAME}
        PRIVATE
        NEED_CONSOLE
    )
endif()

if(FREEZE_APPLICATION)
    target_compile_definitions(${PROJECT_NAME}
        PRIVATE
        FREEZE_APPLICATION
    )
endif()

target_link_libraries(${PROJECT_NAME}
    PRIVATE
    cpython::libpython
)

if(${WIN32})
    add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_RUNTIME_DLLS:${PROJECT_NAME}> $<TARGET_FILE_DIR:${PROJECT_NAME}>
        COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:cpython::libpython3> $<TARGET_FILE_DIR:${PROJECT_NAME}>
        COMMAND_EXPAND_LISTS
    )
    set(PYTHON_VERSIONS_LIST 3 311 312)
    set(PYTHON_ADDITIONAL_LINK_FLAGS "")

    foreach(VER ${PYTHON_VERSIONS_LIST})
        set(PYTHON_ADDITIONAL_LINK_FLAGS
            "${PYTHON_ADDITIONAL_LINK_FLAGS} /NODEFAULTLIB:\"python${VER}_d.lib\"")
        set(PYTHON_ADDITIONAL_LINK_FLAGS
            "${PYTHON_ADDITIONAL_LINK_FLAGS} /NODEFAULTLIB:\"python${VER}.lib\"")
    endforeach()

    set_target_properties(${PROJECT_NAME} PROPERTIES LINK_FLAGS "${PYTHON_ADDITIONAL_LINK_FLAGS}")

    if(NOT NEED_CONSOLE)
        set_target_properties(${PROJECT_NAME} PROPERTIES WIN32_EXECUTABLE 1)
    endif()

    if(FREEZE_APPLICATION)
        if(NOT DEFINED TF_DEPLOY_DIR)
            message(FATAL_ERROR "TF_DEPLOY_DIR is not defined")
        endif()

        if(NOT DEFINED DATAS)
            if(NOT EXISTS ${TF_BUILD_DIR}/datas)
                message(FATAL_ERROR "Neither DATAS nor ${TF_BUILD_DIR}/datas is set.")
            endif()

            set(DATAS "${TF_BUILD_DIR}/datas")
        endif()

        add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
            COMMAND ${PYTHON_EXECUTABLE} "-m" "tfreezer.assemble_application" "${TF_BUILD_DIR}"
            "${ENTRY_MODULE_NAME}" "--hidden-imports=${HIDDEN_IMPORTS}" "--excludes=${EXCLUDES}" "--binaries=$<TARGET_FILE:${PROJECT_NAME}>,$<TARGET_FILE:cpython::libpython3>"
            "--datas=${DATAS}"
            COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:cpython::libpython3> ${TF_DEPLOY_DIR}
            WORKING_DIRECTORY ${TF_APPROOT_DIR}
        )
    endif()
endif()
