#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdbool.h>

static bool _is_ignorable(unsigned char c) {
    return ((c == 0x20) || (c == 0x09) || (c == 0x0D)
            || (c == 0x0B) || (c == 0x0C));
}

static PyObject *_parse_complete_buffer(PyObject *self, PyObject *args){
    Py_buffer mapped_buffer;

    const char *singleline_character,
    *multiline_start_character, *multiline_end_character;
    
    Py_ssize_t singleline_length,
    multiline_start_length, multiline_end_length,
    minimum_characters;

    if (!PyArg_ParseTuple(args,
        "y*z#z#z#n",
        &mapped_buffer,
        &singleline_character, &singleline_length,
        &multiline_start_character, &multiline_start_length,
        &multiline_end_character, &multiline_end_length,
        &minimum_characters)){
            return NULL;
    }

    bool commented_block = false, singleline_comment = false;
    int multiline_start_pointer = 0, multiline_end_pointer = 0,
    singleline_pointer = 0;
    int total_lines = 0, loc = 0, valid_symbols = 0;

    const unsigned char *view = (const unsigned char *) mapped_buffer.buf;
    Py_ssize_t i = 0;
    for (;i < mapped_buffer.len; i++){
        if (view[i] & 0b10000000){
            multiline_start_pointer = 0;
            multiline_end_pointer = 0;
            singleline_pointer = 0;
            continue;
        }
        else if (_is_ignorable(view[i])){
            multiline_start_pointer = 0;
            multiline_end_pointer = 0;
            singleline_pointer = 0;
            continue;
        }

        // Substring matching to determine parsing states
        if (!commented_block){
            if (multiline_start_character
                && view[i] == multiline_start_character[multiline_start_pointer]){
                multiline_start_pointer++;
                if (multiline_start_pointer == multiline_start_length){
                    commented_block = true;
                    multiline_start_pointer = 0;
                }
                continue;
            }
            else if (singleline_character
                && view[i] == singleline_character[singleline_pointer]){
                singleline_pointer++;
                if (singleline_pointer == singleline_length){
                    singleline_comment = true;
                    singleline_pointer = 0;
                    for (;i < mapped_buffer.len && view[i] != '\n'; i++);
                }
                continue;
            }
        }

        else if (commented_block
            && multiline_start_character
            && view[i] == multiline_end_character[multiline_end_pointer]){
                multiline_end_pointer++;
                if (multiline_end_pointer == multiline_end_length){
                    commented_block = false;
                    multiline_end_pointer = 0;
                }
                continue;
        }

        valid_symbols += !(commented_block || singleline_comment);

        multiline_start_pointer = 0;
        multiline_end_pointer = 0;
        singleline_pointer = 0;
        
        if (view[i] == '\n'){
            total_lines++;
            if (valid_symbols > minimum_characters){
                loc++;
            }
            valid_symbols = 0;
            singleline_comment = false;
        }
    }
    // Files not terminating with newline
    if (view[i-1] != '\n'){
        total_lines++;
        if (valid_symbols > minimum_characters){
            loc++;
        }
    }
    PyBuffer_Release(&mapped_buffer);

    return Py_BuildValue("ii", total_lines, loc);
}

static PyObject *_parse_file(PyObject *self, PyObject *args){
    const char *filename,
    *singleline_character,
    *multiline_start_character, *multiline_end_character;
    
    Py_ssize_t singleline_length,
    multiline_start_length,
    multiline_end_length,
    minimum_characters;

    if (!PyArg_ParseTuple(args,
        "sz#z#z#n",
        &filename,
        &singleline_character, &singleline_length,
        &multiline_start_character, &multiline_start_length,
        &multiline_end_character, &multiline_end_length,
        &minimum_characters)){
            return NULL;
    }

    bool commented_block = false, singleline_comment = false;
    int multiline_start_pointer = 0, multiline_end_pointer = 0,
    singleline_pointer = 0;
    int total_lines = 0, loc = 0, valid_symbols = 0;
    FILE *file = fopen(filename, "rb");
    Py_ssize_t i;

    const unsigned int buffer_size = 4 * 1024 * 1024;
    unsigned char buffer[buffer_size];

    size_t chunk_size;
    while ((chunk_size = fread(buffer, 1, buffer_size, file)) > 0){
        for (i = 0; i < chunk_size; i++){
            if (buffer[i] & 0b10000000){
                multiline_start_pointer = 0;
                multiline_end_pointer = 0;
                singleline_pointer = 0;
                continue;
            }
            else if (_is_ignorable(buffer[i])){
                multiline_start_pointer = 0;
                multiline_end_pointer = 0;
                singleline_pointer = 0;
                continue;
            }
    
            // Substring matching to determine parsing states
            if (!commented_block){
                if (multiline_start_character
                    && buffer[i] == multiline_start_character[multiline_start_pointer]){
                    multiline_start_pointer++;
                    if (multiline_start_pointer == multiline_start_length){
                        commented_block = true;
                        multiline_start_pointer = 0;
                    }
                    continue;
                }
                else if (singleline_character
                    && buffer[i] == singleline_character[singleline_pointer]){
                    singleline_pointer++;
                    if (singleline_pointer == singleline_length){
                        singleline_comment = true;
                        singleline_pointer = 0;
                        for (;i < chunk_size && buffer[i] != '\n'; i++);
                    }
                    continue;
                }
            }
    
            else if (commented_block
                && multiline_start_character
                && buffer[i] == multiline_end_character[multiline_end_pointer]){
                    multiline_end_pointer++;
                    if (multiline_end_pointer == multiline_end_length){
                        commented_block = false;
                        multiline_end_pointer = 0;
                    }
                    continue;
            }
    
            valid_symbols += !(commented_block || singleline_comment);
    
            multiline_start_pointer = 0;
            multiline_end_pointer = 0;
            singleline_pointer = 0;
            
            if (buffer[i] == '\n'){
                total_lines++;
                if (valid_symbols > minimum_characters){
                    loc++;
                }
                valid_symbols = 0;
                singleline_comment = false;
            }
        }
    }
    // Files not terminating with newline
    if (buffer[i-1] != '\n'){
        total_lines++;
        if (valid_symbols > minimum_characters){
            loc++;
        }
    }
    fclose(file);
    return Py_BuildValue("ii", total_lines, loc);
}

PyDoc_STRVAR(_parse_complete_buffer_doc, "Parse a UTF-8 byte stream to count total lines and lines of code (LOC)");
PyDoc_STRVAR(_parse_file_doc, "Parse a UTF-8 encoded file to count total lines and lines of code (LOC)");
static PyMethodDef methods[] = {
    {
        .ml_name = "_parse_complete_buffer",
        .ml_doc = _parse_complete_buffer_doc,
        .ml_flags = METH_VARARGS,
        .ml_meth = _parse_complete_buffer,
    },
    {
        .ml_name = "_parse_file",
        .ml_doc = _parse_file_doc,
        .ml_flags = METH_VARARGS,
        .ml_meth = _parse_file,
    },
    {NULL, NULL, 0, NULL}
};

PyDoc_STRVAR(module_doc, "Internal module for parsing files");
static PyModuleDef module = {
    .m_base = PyModuleDef_HEAD_INIT,
    .m_name = "_parsing",
    .m_doc = module_doc,
    .m_size = -1,
    .m_methods = methods
};

PyMODINIT_FUNC
PyInit__parsing(void){
    return PyModule_Create(&module);
}