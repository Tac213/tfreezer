#include "tfloader/tfloader.h"

namespace tfloader
{
PyDoc_STRVAR(g_doc_load_package,
             "Load a package frozen by tfreezer.");

static PyObject*
load_package(PyObject* self, PyObject* py_pkg_name)
{
    wchar_t* pkg_name = PyUnicode_AsWideCharString(py_pkg_name, nullptr);
    if (!pkg_name)
    {
        return nullptr;
    }
    Py_RETURN_TRUE;
}

PyDoc_STRVAR(g_doc_tfloader,
             "Low-level tfreezer package loader.");

static int
module_exec(PyObject* module)
{
    PyObject* version = PyUnicode_FromString(TFLOADER_VERSION);
    if (PyModule_Add(module, "__version__", version) < 0)
    {
        return -1;
    }

    return 0;
}

static PyMethodDef tfloader_methods[] = {
    {"load_package", static_cast<PyCFunction>(load_package), METH_O, g_doc_load_package},
    {nullptr, nullptr},
};

static PyModuleDef_Slot tfloader_slots[] = {
    {Py_mod_exec, reinterpret_cast<void*>(module_exec)},
#if PY_VERSION_HEX >= 0x030d0000 /* >= 3.13.0 */
    {Py_mod_multiple_interpreters, Py_MOD_PER_INTERPRETER_GIL_SUPPORTED},
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
#endif
    {0, nullptr}};

static struct PyModuleDef tfloader_module = {
    .m_base    = PyModuleDef_HEAD_INIT,
    .m_name    = "tfloader",     /* name of module */
    .m_doc     = g_doc_tfloader, /* module documentation, may be nullptr */
    .m_size    = 0,              /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
    .m_methods = tfloader_methods,
    .m_slots   = tfloader_slots,
};

PyMODINIT_FUNC PyInit_tfloader()
{
    return PyModuleDef_Init(&tfloader_module);
}
} // namespace tfloader
