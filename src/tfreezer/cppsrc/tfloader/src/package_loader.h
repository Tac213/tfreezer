/*
 * Author: Tac
 * Contact: cookiezhx@163.com
 */
#pragma once

#ifdef _MSC_VER
#    ifndef NOMINMAX
#        define NOMINMAX
#    endif
#    ifndef WIN32_LEAN_AND_MEAN
#        define WIN32_LEAN_AND_MEAN // Exclude rarely-used stuff from Windows headers
#    endif
#    include <Windows.h>
#endif

namespace tfloader
{
#define TFLOADER_PKG_FUNC_PREFIX "TFPackage_"

#ifdef _MSC_VER
using dl_funcptr = FARPROC;
#else
using dl_funcptr = void (*)();
#endif

#ifdef _MSC_VER
dl_funcptr find_package_shared_funcptr(const char* pkg_name, wchar_t* pkg_path);
#else
dl_funcptr find_package_shared_funcptr(const char* pkg_name, const char* pkg_path);
#endif
} // namespace tfloader
