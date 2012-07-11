import string
MAX_LINE_LENGTH_IN_PIXELS = 64

def wrap_text(widget, text):
    return_text = text
    
    return_text_width = get_length(widget, return_text)
    if (wrapped_text_needed(return_text_width)):
        return_text = add_line_break(widget, text)
        return_text = ellipsize_last_line(widget, return_text)
    return return_text

def wrapped_text_needed(return_text_width):
    return return_text_width > MAX_LINE_LENGTH_IN_PIXELS

def ellipsize_last_line(widget, return_text):
    lines = return_text.split("\n")
    if len(lines) > 2:
        line_to_ellipsize = lines[1]
        line = ellipsize_line(widget, line_to_ellipsize)
        return_text = lines[0] + "\n" + line
    elif len(lines) > 1:
        line_to_ellipsize = lines[1]
        if line_needs_ellipsized(widget, line_to_ellipsize):
            line_to_ellipsize = ellipsize_line(widget, line_to_ellipsize)
        return_text = lines[0] + "\n" + line_to_ellipsize
    else: 
        return_text = ellipsize_line(widget, lines[0])
        
    return return_text

def ellipsize_line(widget, line):
    length = get_length_for_word(widget, line)
    while(length > MAX_LINE_LENGTH_IN_PIXELS):
        line = line[0:-1]
        length = get_length_for_word(widget, line + "...")
    return line + "..."

def line_needs_ellipsized(widget, line):
    return get_length(widget, line) > MAX_LINE_LENGTH_IN_PIXELS

def get_length(widget, text):
    return widget.create_pango_layout(text).get_pixel_size()[0]

def get_length_for_word(widget, word):
    if word.rfind("\n") > 0:
        temp = string.rsplit(word, "\n", 1)
        if len(temp) > 0:
            return get_length(widget, temp[1])
    else:
        return get_length(widget, word)

def add_line_break(widget, text):
    words = text.split()
    return_text = ""
    if len(words) == 1:
        return words[0]

    for word in words:
        curr_len = get_length_for_word(widget, return_text)
        next_word_len = get_length_for_word(widget, " " + word)
        if curr_len == 0:
            return_text += word
        elif curr_len + next_word_len <= MAX_LINE_LENGTH_IN_PIXELS:
            return_text += " " + word
        else:
            return_text += "\n" + word
    return return_text
