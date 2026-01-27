#include "_parsing_prinitives.h"
#include "_comment_data.h"
#include <stdbool.h>

static bool _is_ignorable(unsigned char c) {
    return ((c == 0x20) || (c == 0x09) || (c == 0x0D)
            || (c == 0x0B) || (c == 0x0C));
}

void
_parse_buffer(unsigned char *buffer, size_t buffer_size,
    int minimum_characters, int *valid_characters,
    int *total, int *loc,
    struct CommentData *comment_data){
    for (size_t i = 0; i < buffer_size; i++){
            if (buffer[i] & 0b10000000){
                comment_data->singleline_pointer = 0;
                comment_data->multiline_start_pointer = 0;
                comment_data->multiline_end_pointer = 0;
                continue;
            }
            else if (_is_ignorable(buffer[i])){
                comment_data->singleline_pointer = 0;
                comment_data->multiline_start_pointer = 0;
                comment_data->multiline_end_pointer = 0;
                continue;
            }
    
            // Substring matching to determine parsing states
            if (!comment_data->singleline_commented){
                if (comment_data->multiline_start_symbol
                    && buffer[i] == comment_data->multiline_start_symbol[comment_data->multiline_start_pointer]){
                    comment_data->multiline_start_pointer++;
                    if (comment_data->multiline_start_pointer == comment_data->multiline_start_length){
                        comment_data->commented_block = true;
                        comment_data->multiline_start_pointer = 0;
                    }
                    continue;
                }
                else if (comment_data->singleline_symbol
                    && buffer[i] == comment_data->singleline_symbol[comment_data->singleline_pointer]){
                    comment_data->singleline_pointer++;
                    if (comment_data->singleline_pointer == comment_data->singleline_length){
                        comment_data->singleline_commented = true;
                        comment_data->singleline_pointer = 0;
                        for (;i < buffer && buffer[i] != '\n'; i++);
                    }
                    continue;
                }
            }
    
            else if (comment_data->commented_block
                && comment_data->multiline_start_symbol
                && buffer[i] == comment_data->multiline_end_symbol[comment_data->multiline_end_pointer]){
                    comment_data->multiline_end_pointer++;
                    if (comment_data->multiline_end_pointer == comment_data->multiline_end_length){
                        comment_data->commented_block = false;
                        comment_data->multiline_end_pointer = 0;
                    }
                    continue;
            }
    
            *valid_characters += !(comment_data->commented_block || comment_data->singleline_commented);
    
            comment_data->singleline_pointer = 0;
            comment_data->multiline_start_pointer = 0;
            comment_data->multiline_end_pointer = 0;
            
            if (buffer[i] == '\n'){
                *total++;
                if (*valid_characters > minimum_characters){
                    *loc++;
                }
                *valid_characters = 0;
                comment_data->singleline_commented = false;
            }
        }
}
