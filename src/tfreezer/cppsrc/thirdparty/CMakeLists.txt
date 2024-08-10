set(third_party_folder "${CMAKE_CURRENT_SOURCE_DIR}")

if(NOT TARGET cpython::libpython)
    add_subdirectory(cpython)
endif()
