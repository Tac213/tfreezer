#include "package_loader.h"
#include <string>

namespace tfloader
{
dl_funcptr find_package_shared_funcptr(const char* pkg_name, wchar_t* pkg_path)
{
    dl_funcptr p = nullptr;

    HINSTANCE h_dll = nullptr;
#if WINAPI_FAMILY_PARTITION(WINAPI_PARTITION_DESKTOP)
    /* Desktop OS. */
    unsigned int old_mode;

    /* Don't display a message box when we can't load a DLL */
    old_mode = SetErrorMode(SEM_FAILCRITICALERRORS);
#endif

    h_dll = LoadLibraryExW(
        pkg_path,
        nullptr,
        LOAD_LIBRARY_SEARCH_DEFAULT_DIRS | LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR);

#if WINAPI_FAMILY_PARTITION(WINAPI_PARTITION_DESKTOP)
    /* restore old error mode settings */
    SetErrorMode(old_mode);
#endif

    if (!h_dll)
    {
        return nullptr;
    }

    std::string funcname(TFLOADER_PKG_FUNC_PREFIX);
    funcname += pkg_name;
    p = GetProcAddress(h_dll, funcname.c_str());
    return p;
}
} // namespace tfloader
