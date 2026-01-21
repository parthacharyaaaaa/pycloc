#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdbool.h>

static PyObject *_parse_memoryview(PyObject *self, PyObject *args){
    Py_buffer mapped_buffer;

    const char *singleline_character,
    *multiline_start_character, *multiline_end_character;
    
    Py_ssize_t singleline_length,
    multiline_start_length, multiline_end_length,
    minimum_characters;

    if (!PyArg_ParseTuple(args,
        "w*y#y#y#n",
        &mapped_buffer,
        &singleline_character, &singleline_length,
        &multiline_start_character, &multiline_start_length,
        &multiline_end_character, &multiline_end_length,
        &minimum_characters)){
            PyBuffer_Release(&mapped_buffer);
            return NULL;
    }

    bool commented_block = false;
    int total_lines = 0, loc = 0, valid_chars = 0;

    // Parsing logic here >:3
    const char *view = (const char *) mapped_buffer.buf;
    for (Py_ssize_t i = 0; i < mapped_buffer.len; i++){
        
    }

    PyBuffer_Release(&mapped_buffer);

    return Py_BuildValue("ii", total_lines, loc);
}

static PyMethodDef methods[] = {
    {
        .ml_name = "_parse_memoryview",
        .ml_doc = "Parse a UTF-8 byte stream to count total lines and lines of code (LOC)",
        .ml_flags = METH_VARARGS,
        .ml_meth = _parse_memoryview
    },
    {NULL, NULL, 0, NULL}
};

PyDoc_STRVAR(module_doc, "Internal module for parsing files");
static PyModuleDef module = {
    .m_base = PyModuleDef_HEAD_INIT,
    .m_name = "parse_file",
    .m_doc = module_doc,
    .m_size = -1,
    .m_methods = methods
};

PyMODINIT_FUNC
PyInit__parse_file(void){
    return PyModule_Create(&module);
}