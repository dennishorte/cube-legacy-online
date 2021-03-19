def normalize_newlines(string):
    tmp = string.replace('\r\n', '\n').replace('\r', '\n')
    return '\n'.join([x.strip() for x in tmp.split('\n')])
