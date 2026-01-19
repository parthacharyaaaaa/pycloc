#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdbool.h>

static const int NEWLINE_INTEGER = 10;

static PyObject *_parse_file(PyObject *self, PyObject *args){
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
    int total_lines = 0, loc = 0;

    // Parsing logic here >:3
    for (Py_ssize_t i = 0; i < mapped_buffer.len; i++){
        
    }

    PyBuffer_Release(&mapped_buffer);

    return Py_BuildValue("ii", total_lines, loc);
}