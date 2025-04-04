/*
 * Author: Tac
 * Contact: cookiezhx@163.com
 */
#pragma once

#include <Python.h>

namespace tfloader
{
using TFPackageInitFunction = _frozen* (*)();

PyMODINIT_FUNC PyInit_tfloader();
} // namespace tfloader
