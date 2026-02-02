#ifndef _COMMENT_DATA_H
#define _COMMENT_DATA_H

#include <stdbool.h>
struct CommentData {
    const char *singleline_symbol;
    const char *multiline_start_symbol;
    const char *multiline_end_symbol;

    unsigned int singleline_length;
    unsigned int multiline_start_length;
    unsigned int multiline_end_length;

    unsigned int singleline_pointer;
    unsigned int multiline_start_pointer;
    unsigned int multiline_end_pointer;
    
    bool in_singleline, in_multiline;
};

extern void initialize_comment_data(struct CommentData *comment_data,
    const char *singleline_symbol, const char *multiline_start_symbol, const char *multiline_end_symbol,
    unsigned int singleline_length, unsigned int multiline_start_length, unsigned int multiline_end_length);

#endif