#include "tfloader/tfloader.h"
#include "package_loader.h"
#include <marshal.h>
#include <unordered_map>
#include <string>

namespace tfloader
{
static std::unordered_map<std::string, _frozen*> g_pkg_frozen_module_infos = {};

using FrozenStatus = enum {
    kFrozenOkay,
    kFrozenBadName,  // The given module name wasn't valid.
    kFrozenNotFound, // It wasn't in PyImport_FrozenModules.
    kFrozenDisabled, // -X frozen_modules=off (and not essential)
    kFrozenExcluded, /* The PyImport_FrozenModules entry has NULL "code"
                           (module is present but marked as unimportable, stops search). */
    kFrozenInvalid,  /* The PyImport_FrozenModules entry is bogus
                           (eg. does not contain executable code). */
};

static inline void
set_frozen_error(FrozenStatus status, PyObject* modname)
{
    const char* err = nullptr;
    switch (status)
    {
        case kFrozenBadName:
        case kFrozenNotFound:
            err = "No such tfpackage frozen object named %R";
            break;
        case kFrozenDisabled:
            err = "Tfpacakge frozen modules are disabled and the tfpackage frozen object named %R is not essential";
            break;
        case kFrozenExcluded:
            err = "Excluded tfpackage frozen object named %R";
            break;
        case kFrozenInvalid:
            err = "Tfpackage frozen object named %R is invalid";
            break;
        case kFrozenOkay:
            // There was no error.
            break;
        default:
            Py_UNREACHABLE();
    }
    if (err != nullptr)
    {
        PyObject* msg = PyUnicode_FromFormat(err, modname);
        if (msg == nullptr)
        {
            PyErr_Clear();
        }
        PyErr_SetImportError(msg, modname, nullptr);
        Py_XDECREF(msg);
    }
}

struct FrozenInfo
{
    PyObject*   nameobj;
    const char* data;
    Py_ssize_t  size;
    bool        is_package;
    bool        is_alias;
    const char* origname;
};

static const _frozen*
look_up_frozen(const char* name)
{
    _frozen* p;
    for (auto& pair : g_pkg_frozen_module_infos)
    {
        for (p = pair.second;; p++)
        {
            if (p->name == nullptr)
            {
                break;
            }
            if (strcmp(name, p->name) == 0)
            {
                return p;
            }
        }
    }
    return nullptr;
}

static FrozenStatus
find_frozen(PyObject* nameobj, FrozenInfo* info)
{
    if (info != nullptr)
    {
        memset(info, 0, sizeof(*info));
    }

    if (nameobj == nullptr || nameobj == Py_None)
    {
        return kFrozenBadName;
    }
    const char* name = PyUnicode_AsUTF8(nameobj);
    if (name == nullptr)
    {
        // Note that this function previously used
        // _PyUnicode_EqualToASCIIString().  We clear the error here
        // (instead of propagating it) to match the earlier behavior
        // more closely.
        PyErr_Clear();
        return kFrozenBadName;
    }

    const struct _frozen* p = look_up_frozen(name);
    if (p == nullptr)
    {
        return kFrozenNotFound;
    }
    if (info != nullptr)
    {
        info->nameobj    = nameobj; // borrowed
        info->data       = reinterpret_cast<const char*>(p->code);
        info->size       = p->size;
        info->is_package = p->is_package;
        if (p->size < 0)
        {
            // backward compatibility with negative size values
            info->size       = -(p->size);
            info->is_package = true;
        }
        info->origname = name;
        info->is_alias = false;
    }
    if (p->code == nullptr)
    {
        /* It is frozen but marked as un-importable. */
        return kFrozenExcluded;
    }
    if (p->code[0] == '\0' || p->size == 0)
    {
        /* Does not contain executable code. */
        return kFrozenInvalid;
    }
    return kFrozenOkay;
}

static PyObject*
unmarshal_frozen_code(PyInterpreterState* interp, FrozenInfo* info)
{
    PyObject* co = PyMarshal_ReadObjectFromString(info->data, info->size);
    if (co == nullptr)
    {
        /* Does not contain executable code. */
        PyErr_Clear();
        set_frozen_error(kFrozenInvalid, info->nameobj);
        return nullptr;
    }
    if (!PyCode_Check(co))
    {
        // We stick with TypeError for backward compatibility.
        PyErr_Format(PyExc_TypeError,
                     "frozen object %R is not a code object",
                     info->nameobj);
        Py_DECREF(co);
        return nullptr;
    }
    return co;
}

PyDoc_STRVAR(g_doc_load_tfpackage,
             "Load a package frozen by tfreezer.");

static PyObject*
load_tfpackage(PyObject* module, PyObject* args)
{
#ifdef MS_WINDOWS
    const char* pkg_name;
    PyObject*   py_pkg_path;
    if (!PyArg_ParseTuple(args, "sO", &pkg_name, &py_pkg_path))
    {
        return nullptr;
    }
    wchar_t* pkg_path = PyUnicode_AsWideCharString(py_pkg_path, nullptr);
#else
    const char* pkg_name;
    const char* pkg_path;
    if (!PyArg_ParseTuple(args, "ss", &pkg_name, &pkg_path))
    {
        return nullptr;
    }
#endif
    if (!pkg_name || !pkg_path)
    {
        return nullptr;
    }
    if (g_pkg_frozen_module_infos.find(pkg_name) != g_pkg_frozen_module_infos.end())
    {
#ifdef MS_WINDOWS
        PyMem_Free(pkg_path);
#endif
        Py_RETURN_TRUE;
    }
    dl_funcptr func = find_package_shared_funcptr(pkg_name, pkg_path);
    if (!func)
    {
#ifdef MS_WINDOWS
        PyMem_Free(pkg_path);
#endif
        Py_RETURN_FALSE;
    }
#ifdef MS_WINDOWS
    PyMem_Free(pkg_path);
#endif
    TFPackageInitFunction init_func = reinterpret_cast<TFPackageInitFunction>(func);

    _frozen* frozen_module_info = init_func();
    g_pkg_frozen_module_infos.emplace(std::make_pair(pkg_name, frozen_module_info));
    Py_RETURN_TRUE;
}

PyDoc_STRVAR(g_doc_is_tfpackage_frozen,
             "Check if a module is inside a package frozen by tfreezer.");

static PyObject*
is_tfpackage_frozen(PyObject* module, PyObject* name)
{
    FrozenInfo   info;
    FrozenStatus status = find_frozen(name, &info);
    if (status != kFrozenOkay)
    {
        Py_RETURN_FALSE;
    }
    Py_RETURN_TRUE;
}

PyDoc_STRVAR(g_doc_is_tfpackage_frozen_package,
             "Check if the module inside a package frozen by tfreezer is a package (source name ends with __init__.py).");

static PyObject*
is_tfpackage_frozen_package(PyObject* module, PyObject* name)
{
    FrozenInfo   info;
    FrozenStatus status = find_frozen(name, &info);
    if (status != kFrozenOkay && status != kFrozenExcluded)
    {
        set_frozen_error(status, name);
        return nullptr;
    }
    return PyBool_FromLong(info.is_package);
}

PyDoc_STRVAR(g_doc_get_tfpackage_frozen_object,
             "Get the frozen code object of the module inside a package frozen by tfreezer.");

static PyObject*
get_tfpackage_frozen_object(PyObject* module, PyObject* name)
{
    FrozenInfo info = {nullptr};

    FrozenStatus status = find_frozen(name, &info);
    if (status != kFrozenOkay)
    {
        set_frozen_error(status, name);
        return nullptr;
    }

    if (info.nameobj == nullptr)
    {
        info.nameobj = name;
    }

    if (info.size == 0)
    {
        /* Does not contain executable code. */
        set_frozen_error(kFrozenInvalid, name);
        return nullptr;
    }

    PyInterpreterState* interp  = PyInterpreterState_Get();
    PyObject*           codeobj = unmarshal_frozen_code(interp, &info);
    return codeobj;
}

PyDoc_STRVAR(g_doc_find_tfpackage_frozen,
             "Find the frozen module information of the module inside a package frozen by tfreezer.");


static PyObject*
find_tfpackage_frozen(PyObject* module, PyObject* name)
{
    FrozenInfo   info;
    FrozenStatus status = find_frozen(name, &info);
    if (status == kFrozenNotFound || status == kFrozenDisabled)
    {
        Py_RETURN_NONE;
    }
    else if (status == kFrozenBadName)
    {
        Py_RETURN_NONE;
    }
    else if (status != kFrozenOkay)
    {
        set_frozen_error(status, name);
        return nullptr;
    }

    PyObject* origname = nullptr;
    if (info.origname != nullptr && info.origname[0] != '\0')
    {
        origname = PyUnicode_FromString(info.origname);
        if (origname == nullptr)
        {
            return nullptr;
        }
    }

    PyObject* result = PyTuple_Pack(
        2,
        info.is_package ? Py_True : Py_False,
        origname ? origname : Py_None);
    Py_XDECREF(origname);
    return result;
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
    {"load_tfpackage", static_cast<PyCFunction>(load_tfpackage), METH_VARARGS, g_doc_load_tfpackage},
    {"is_tfpackage_frozen", static_cast<PyCFunction>(is_tfpackage_frozen), METH_O, g_doc_is_tfpackage_frozen},
    {"is_tfpackage_frozen_package", static_cast<PyCFunction>(is_tfpackage_frozen_package), METH_O, g_doc_is_tfpackage_frozen_package},
    {"get_tfpackage_frozen_object", static_cast<PyCFunction>(get_tfpackage_frozen_object), METH_O, g_doc_get_tfpackage_frozen_object},
    {"find_tfpackage_frozen", static_cast<PyCFunction>(find_tfpackage_frozen), METH_O, g_doc_find_tfpackage_frozen},
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
