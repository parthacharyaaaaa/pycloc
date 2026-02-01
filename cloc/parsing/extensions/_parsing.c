#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdbool.h>
#include "_parsing_prinitives.h"
#include "_comment_data.h"

#define uchar_sentinel '0'

#ifdef _WIN32

#include <windows.h>
static PyObject *
_parse_file_vm_map(PyObject *self, PyObject *args){
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

    const HANDLE file_handle = CreateFile(filename, GENERIC_READ, FILE_SHARE_READ, NULL,
        OPEN_EXISTING, FILE_ATTRIBUTE_READONLY, NULL);

    if (file_handle == INVALID_HANDLE_VALUE){
        PyErr_SetFromWindowsErrWithFilename(0, filename);
        return NULL;
    }

    LARGE_INTEGER filesize;
    GetFileSizeEx(file_handle, &filesize);

    if (filesize.QuadPart == 0){
        CloseHandle(file_handle);
        return Py_BuildValue("ii", 0, 0);
    } 
    
    const HANDLE mapping_handle = CreateFileMapping(file_handle, NULL, PAGE_READONLY, 0, 0, NULL);
    if (!mapping_handle){
        CloseHandle(file_handle);
        PyErr_SetFromWindowsErrWithFilename(0, filename);
        return NULL;
    }

    void *mapped_region = MapViewOfFile(mapping_handle, FILE_MAP_READ, 0, 0, 0);
    if (!mapped_region){
        CloseHandle(file_handle);
        CloseHandle(mapping_handle);
        PyErr_SetFromWindowsErrWithFilename(0, filename);
        return NULL;
    }

    const unsigned char *view = (unsigned char *) mapped_region;
    int total_lines = 0, loc = 0, valid_symbols = 0;
    
    struct CommentData comment_data;
    initialize_comment_data(
        &comment_data,
        singleline_character,
        multiline_start_character,
        multiline_end_character,
        singleline_length,
        multiline_start_length,
        multiline_end_length
    );

    _parse_buffer(view, filesize.QuadPart, minimum_characters, &valid_symbols, &total_lines, &loc, &comment_data);

    // Files not terminating with newline
    if (view[filesize.QuadPart-1] != '\n'){
        total_lines++;
        loc += (valid_symbols >= minimum_characters);
    }

    UnmapViewOfFile(mapped_region);
    CloseHandle(mapping_handle);
    CloseHandle(file_handle);
    return Py_BuildValue("ii", total_lines, loc);
}

#else

#include <sys/mman.h>
static PyObject *
_parse_file_vm_map(PyObject *self, PyObject *args){
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

    FILE *file = fopen(filename, "rb");
    if (!file){
        PyErr_SetFromErrnoWithFilename(PyExc_OSError, filename);
        return NULL;
    }

    struct stat st;
    if (fstat(fileno(file), &st) == -1){
        fclose(file);
        PyErr_SetFromErrnoWithFilename(PyExc_OSError, filename);
        return NULL;
    }

    if (st.st_size == 0){
        fclose(file);
        return Py_BuildValue("ii", 0, 0);
    }
    void *mapped_region = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, fileno(file), 0);
    if (mapped_region == MAP_FAILED){
        fclose(file);
        PyErr_SetFromErrnoWithFilename(PyExc_OSError, filename);
        return NULL;
    }

    const unsigned char *view = (unsigned char *) mapped_region;
    int total_lines = 0, loc = 0, valid_symbols = 0;
    
    struct CommentData comment_data;
    initialize_comment_data(
        &comment_data,
        singleline_character,
        multiline_start_character,
        multiline_end_character,
        singleline_length,
        multiline_start_length,
        multiline_end_length
    );

    _parse_buffer(view, st.st_size, minimum_characters, &valid_symbols, &total_lines, &loc, &comment_data);

    // Files not terminating with newline
    if (view[st.st_size-1] != '\n'){
        total_lines++;
        loc += (valid_symbols >= minimum_characters);
    }

    fclose(file);
    munmap(mapped_region, st.st_size);
    return Py_BuildValue("ii", total_lines, loc);
}


#endif

static PyObject *
_parse_file(PyObject *self, PyObject *args){
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

    FILE *file = fopen(filename, "rb");
    if (!file){
        PyErr_SetFromErrnoWithFilename(PyExc_OSError, filename);
        return NULL;
    }

    int total_lines = 0, loc = 0, valid_symbols = 0;
    const size_t buffer_size = 4 * 1024 * 1024;
    unsigned char buffer[buffer_size];
    unsigned char last_byte = uchar_sentinel;
    size_t chunk_size;

    struct CommentData comment_data;
    initialize_comment_data(
        &comment_data,
        singleline_character,
        multiline_start_character,
        multiline_end_character,
        singleline_length,
        multiline_start_length,
        multiline_end_length
    );

    while ((chunk_size = fread(buffer, 1, buffer_size, file)) > 0){
        last_byte = buffer[chunk_size-1];
        _parse_buffer(buffer, chunk_size, minimum_characters, &valid_symbols, &total_lines, &loc, &comment_data);
    }
    // Files not terminating with newline
    if (last_byte != '\n' 
        && last_byte != uchar_sentinel){
        total_lines++;
        loc += (valid_symbols >= minimum_characters);
    }
    fclose(file);
    return Py_BuildValue("ii", total_lines, loc);
}

static PyObject *
_parse_file_no_chunk(PyObject *self, PyObject *args){
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

    FILE *file = fopen(filename, "rb");
    if (!file){
        PyErr_SetFromErrnoWithFilename(PyExc_OSError, filename);
        return NULL;
    }

    struct stat st;
    if (fstat(fileno(file), &st) == -1){
        fclose(file);
        PyErr_SetFromErrnoWithFilename(PyExc_OSError, filename);
        return NULL;
    }

    if (st.st_size == 0){
        fclose(file);
        return Py_BuildValue("ii", 0, 0);
    }

    unsigned char *buffer = malloc(st.st_size);
    if (!buffer){
        PyErr_Format(PyExc_MemoryError,
            "Failed to open file %s of size %d bytes",
            filename, st.st_size);
        return NULL;
    }
    fread(buffer, 1, st.st_size, file);
    
    int total_lines = 0, loc = 0, valid_symbols = 0;
    struct CommentData comment_data;
    initialize_comment_data(
        &comment_data,
        singleline_character,
        multiline_start_character,
        multiline_end_character,
        singleline_length,
        multiline_start_length,
        multiline_end_length
    );

    _parse_buffer(buffer, st.st_size, minimum_characters, &valid_symbols, &total_lines, &loc, &comment_data);
    // Files not terminating with newline
    if (buffer[st.st_size-1] != '\n'){
        total_lines++;
        loc += (valid_symbols >= minimum_characters);
    }
    fclose(file);
    return Py_BuildValue("ii", total_lines, loc);
}

PyDoc_STRVAR(_parse_file_vm_map_doc, "Parse a UTF-8 byte stream to count total lines and lines of code (LOC)");
PyDoc_STRVAR(_parse_file_doc, "Parse a UTF-8 encoded file to count total lines and lines of code (LOC)");
PyDoc_STRVAR(_parse_file_no_chunk_doc,
    "Parse a UTF-8 encoded file to count total lines and lines of code (LOC), reading the entire file at once");

static PyMethodDef methods[] = {
    {
        .ml_name = "_parse_file_vm_map",
        .ml_doc = _parse_file_vm_map_doc,
        .ml_flags = METH_VARARGS,
        .ml_meth = _parse_file_vm_map,
    },
    {
        .ml_name = "_parse_file",
        .ml_doc = _parse_file_doc,
        .ml_flags = METH_VARARGS,
        .ml_meth = _parse_file,
    },
    {
        .ml_name = "_parse_file_no_chunk",
        .ml_doc = _parse_file_no_chunk_doc,
        .ml_flags = METH_VARARGS,
        .ml_meth = _parse_file_no_chunk,
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