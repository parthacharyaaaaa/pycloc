
#ifndef _PARSING_PRIMITIVES_H
#define _PARSING_PRIMITIVES_H
#include <stdlib.h>

struct CommentData;

extern void
_parse_buffer(unsigned char *buffer, size_t buffer_size,
    int minimum_characters, int *valid_characters,
    int *total, int *loc,
    struct CommentData *comment_data);

#endif