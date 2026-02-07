#ifndef _COMMENT_DATA_H
#define _COMMENT_DATA_H
#include "_locstat.h"
#include <stdbool.h>
struct CommentData {
    const char *singleline_symbol;
    const char *multiline_start_symbol;
    const char *multiline_end_symbol;

    Py_ssize_t singleline_length;
    Py_ssize_t multiline_start_length;
    Py_ssize_t multiline_end_length;

    Py_ssize_t singleline_pointer;
    Py_ssize_t multiline_start_pointer;
    Py_ssize_t multiline_end_pointer;
    
    bool in_singleline, in_multiline;
};

extern void initialize_comment_data(struct CommentData *comment_data,
    const char *singleline_symbol, const char *multiline_start_symbol, const char *multiline_end_symbol,
    Py_ssize_t singleline_length, Py_ssize_t multiline_start_length, Py_ssize_t multiline_end_length);

#endif