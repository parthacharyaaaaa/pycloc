
#ifndef _PARSING_PRIMITIVES_H
#define _PARSING_PRIMITIVES_H
#include "_locstat.h"
#include <stdlib.h>

struct CommentData;
extern void
_parse_buffer(unsigned char *buffer, size_t buffer_size,
    Py_ssize_t minimum_characters, int *valid_characters,
    int *total, int *loc,
    struct CommentData *comment_data);

#endif