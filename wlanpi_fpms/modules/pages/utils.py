
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
