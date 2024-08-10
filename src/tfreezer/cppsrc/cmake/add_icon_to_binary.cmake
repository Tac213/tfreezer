include(CMakeParseArguments)

function(add_icon_to_binary appsources)
    set(options)
    set(oneValueArgs OUTFILE_BASENAME)
    set(multiValueArgs ICONS)
    cmake_parse_arguments(ARG "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

    if(NOT ARG_ICONS)
        message(FATAL_ERROR "No ICONS argument given to add_icon_to_binary")
    endif()

    if(ARG_UNPARSED_ARGUMENTS)
        message(FATAL_ERROR "Unexpected arguments to ecm_add_app_icon: ${ARG_UNPARSED_ARGUMENTS}")
    endif()

    foreach(icon ${ARG_ICONS})
        get_filename_component(icon_full ${icon} ABSOLUTE)
        get_filename_component(icon_type ${icon_full} EXT)
        get_filename_component(icon_name ${icon_full} NAME_WE)

        if(${CMAKE_SYSTEM_NAME} STREQUAL "Darwin")
            if(${icon_type} STREQUAL ".icns")
                set(icon_full_output ${CMAKE_CURRENT_BINARY_DIR}/${icon_name}.icns)
                configure_file(${icon_full} ${icon_full_output} COPYONLY)
                set(MACOSX_BUNDLE_ICON_FILE ${icon_name}.icns PARENT_SCOPE)
                set(${appsources} "${${appsources}};${icon_full_output}" PARENT_SCOPE)
                set_source_files_properties(${icon_full_output} PROPERTIES MACOSX_PACKAGE_LOCATION Resources)
                return()
            endif()
        endif()

        if(${CMAKE_SYSTEM_NAME} STREQUAL "Windows")
            if(${icon_type} STREQUAL ".ico")
                set(icon_full_output ${CMAKE_CURRENT_BINARY_DIR}/${icon_name}.ico)
                configure_file(${icon_full} ${icon_full_output} COPYONLY)
                file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/${icon_name}.rc.in" "#pragma code_page(1252)
IDI_ICON1        ICON        DISCARDABLE    \"${icon_name}.ico\"
VS_VERSION_INFO VERSIONINFO
 FILEVERSION 1, 0, 0, 0
 PRODUCTVERSION 1, 0, 0, 0
 FILEFLAGSMASK 0x3fL
 FILEFLAGS 0x0L
 FILEOS 0x4L
 FILETYPE 0x1L
 FILESUBTYPE 0x0L
BEGIN
    BLOCK \"StringFileInfo\"
    BEGIN
        BLOCK \"000004b0\"
        BEGIN
            VALUE \"CompanyName\", \"Unknown Company\\0\"
            VALUE \"FileDescription\", \"${PROJECT_NAME}\\0\"
            VALUE \"FileVersion\", \"${PROJECT_VERSION}\\0\"
            VALUE \"InternalName\", \"${PROJECT_NAME}\\0\"
            VALUE \"LegalCopyright\", \"Copyright (c) 2024 Unknown Company.\\0\"
            VALUE \"OriginalFilename\", \"${PROJECT_NAME}.exe\\0\"
            VALUE \"ProductName\", \"${PROJECT_NAME}\\0\"
            VALUE \"ProductVersion\", \"${PROJECT_VERSION}\\0\"
        END
    END
    BLOCK \"VarFileInfo\"
    BEGIN
        VALUE \"Translation\", 0x0, 1200
    END
END
")
                add_custom_command(
                    OUTPUT "${icon_name}.rc"
                    COMMAND ${CMAKE_COMMAND}
                    ARGS -E copy "${icon_name}.rc.in" "${icon_name}.rc"
                    DEPENDS "${icon_name}.ico"
                    WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}")
                set(${appsources} "${${appsources}};${icon_name}.rc" PARENT_SCOPE)
                return()
            endif()
        endif()
    endforeach()

    return()
endfunction()
