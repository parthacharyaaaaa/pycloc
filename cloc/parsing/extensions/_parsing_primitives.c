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
        // Skip continuation bytes
        if ((buffer[i] & 0b11000000) == 0b10000000){
            continue;
        }

        // Skip whitespace characters
        else if (_is_ignorable(buffer[i])){
            comment_data->singleline_pointer = 0;
            comment_data->multiline_start_pointer = 0;
            comment_data->multiline_end_pointer = 0;
            continue;
        }
        
        // Singleline comments
        if (comment_data->singleline_symbol
            && buffer[i] == comment_data->singleline_symbol[comment_data->singleline_pointer]){
            (comment_data->singleline_pointer)++;
            if (comment_data->singleline_pointer == comment_data->singleline_length){
                /*
                  Singleline comment matched
                  Progress until EOF or newline
                */
                for(; i < buffer_size && buffer[i] != '\n'; i++);
                i -= (buffer[i] == '\n'); // Let outer loop handle newline
                continue;
            }
            comment_data->partial_matches |= 0b10000000;
        }

        // Multiline comments
        if (comment_data->multiline_start_symbol
            && buffer[i] == comment_data->multiline_start_symbol[comment_data->multiline_start_pointer]){
            (comment_data->multiline_start_pointer)++;
            if (comment_data->multiline_start_pointer == comment_data->multiline_start_length){
                // Commented block begins
                comment_data->multiline_start_pointer = 0;
                /*
                  Loop until multiline end pointer
                  Control should only exit this loop
                  at EOF or the end of the commented block
                */ 
                for(; i < buffer_size; i++){
                    if (buffer[i] == '\n'){
                        (*total)++;
                        (*loc) += ((*valid_characters) > minimum_characters);
                        *valid_characters = 0;
                    }
                    else if (buffer[i] == comment_data->multiline_end_symbol[comment_data->multiline_end_pointer]){
                        (comment_data->multiline_end_pointer)++;
                        if (comment_data->multiline_end_pointer == comment_data->multiline_end_length){
                            // Multiline end pointer found
                            *valid_characters -= (comment_data->multiline_start_length - 1);
                            break;
                        }
                        continue;
                    }
                    comment_data->multiline_end_pointer = 0;
                }
            }
            else {
                comment_data->partial_matches |= 0b01000000;
            }
        }
        /*
            Control reaches here only for non-comment symbols
            and UTF-8 !continuation bytes (e.g. ASCII)
        */
        // Reset pointers only on failed matches
        if (!(comment_data->partial_matches & 0b10000000)){
            comment_data->singleline_pointer = 0;
        }
        if (!(comment_data->partial_matches & 0b01000000)){
            comment_data->multiline_start_pointer = 0;
        }

        if (buffer[i] == '\n'){
            (*total)++;
            (*loc) += ((*valid_characters) >= minimum_characters);
            *valid_characters = 0;
        }
        else if (!comment_data->partial_matches) {
            (*valid_characters)++;
        }
        comment_data->partial_matches = 0;
    }
}