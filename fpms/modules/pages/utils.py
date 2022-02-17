
class StringFormatter(object):

    def __init__(self):
        pass

    def justify(self, text, width=21):
        '''
        Inserts spaces between ':' and the remaining of the text to make
        sure 'text' is 'width' characters in length.
        '''

        if len(text) < width:
            index = text.find(':') + 1
            if index > 0:
                return text[:index] + (' ' * (width - len(text))) + text[index:]

        return text

    def split(self, lines, length=21):
        '''
        Split lines that are longer than the given length
        '''
        new_lines = []
        for line in lines:
            new_lines.extend([line[i:i+length] for i in range(0, len(line), length)])
        return new_lines
