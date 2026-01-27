#include <stdbool.h>
#include "_comment_data.h"

void initialize_comment_data(struct CommentData *comment_data,
    const char *singleline_symbol, const char *multiline_start_symbol, const char *multiline_end_symbol,
    unsigned int singleline_length, unsigned int multiline_start_length, unsigned int multiline_end_length){
    comment_data->commented_block = false;
    comment_data->singleline_commented = false;

    comment_data->singleline_length = singleline_length;
    comment_data->multiline_start_length = multiline_start_length;
    comment_data->multiline_end_length = multiline_end_length;

    comment_data->singleline_symbol = singleline_symbol;
    comment_data->multiline_start_symbol = multiline_start_symbol;
    comment_data->multiline_end_symbol = multiline_end_symbol;

    comment_data->multiline_start_pointer = 0;
    comment_data->multiline_end_pointer = 0;
    comment_data->singleline_pointer = 0;
}