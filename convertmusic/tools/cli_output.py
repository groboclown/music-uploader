import json

class Output:
    def __init__(self, writer):
        self._writer = writer

    def start(self):
        raise NotImplementedError()

    def end(self):
        raise NotImplementedError()

    def dict_section(self, name, key_values):
        self.dict_start(name)
        for k,v in key_values.items():
            self.dict_item(k, v)
        self.dict_end()

    def dict_start(self, name):
        raise NotImplementedError()

    def dict_item(self, k, v):
        raise NotImplementedError()

    def dict_end(self):
        raise NotImplementedError()

    def list_section(self, name, items):
        self.list_start(name)
        for i in items:
            self.list_item(i)
        self.list_end()

    def list_start(self, name):
        raise NotImplementedError()

    def list_item(self, item):
        raise NotImplementedError()

    def list_end(self):
        raise NotImplementedError()

    def error(self, err_msg):
        print("ERROR: {0}".format(err_msg))

    def _outln(self, text):
        self._writer(text)


class OutlineOutput(Output):
    def __init__(self, writer, indent_amount=2):
        Output.__init__(self, writer)
        self.__indent = 0
        self.__indent_amount = indent_amount
        self.__section_count = []

    def start(self):
        self.__section_count.append(0)

    def end(self):
        self.__section_count.pop()

    def _section_start(self, name):
        self.__section_count[-1] += 1
        if '/' not in name and '\\' not in name:
            # Probably not a filename.
            name = name.replace('_', ' ')
            name = name[0].upper() + name[1:] + ':'
        self._outln('{0}{1}'.format(' ' * self.__indent, name))
        self.__indent += self.__indent_amount
        self.__section_count.append(0)

    def _section_end(self):
        if self.__section_count[-1] <= 0:
            self._outln('{0}(no items)'.format(' ' * self.__indent))
        self.__indent -= self.__indent_amount
        self.__section_count.pop()

    def dict_start(self, name):
        self._section_start(name)

    def dict_item(self, k, v):
        self.__section_count[-1] += 1
        self._outln('{0}{1}: {2}'.format(' ' * self.__indent, k, v))

    def dict_end(self):
        self._section_end()

    def list_start(self, name):
        self._section_start(name)

    def list_item(self, item):
        self.__section_count[-1] += 1
        self._outln('{0}- {1}'.format(' ' * self.__indent, item))

    def list_end(self):
        self._section_end()

class YamlOutput(Output):
    def __init__(self, writer, indent_amount=2):
        Output.__init__(self, writer)
        self.__indent = 0
        self.__indent_amount = indent_amount

    def start(self):
        pass

    def end(self):
        pass

    def _section_start(self, name):
        self._outln('{0}{1}:'.format(' ' * self.__indent, name))
        self.__indent += self.__indent_amount

    def _section_end(self):
        self.__indent -= self.__indent_amount

    def dict_start(self, name):
        self._section_start(name)

    def dict_item(self, k, v):
        self._outln('{0}{1}: {2}'.format(' ' * self.__indent, k, v))

    def dict_end(self):
        self._section_end()

    def list_start(self, name):
        self._section_start(name)

    def list_item(self, item):
        self._outln('{0}- {1}'.format(' ' * self.__indent, item))

    def list_end(self):
        self._section_end()


class JsonOutput(Output):
    def __init__(self, writer):
        Output.__init__(self, writer)
        self.__indent = 0
        self.__prev_item = []

    def start(self):
        self._outln('{')
        self.__prev_item.append(False)
        self.__indent += 2

    def end(self):
        self.__indent -= 2
        self._outln('}')
        self.__prev_item.pop()

    def dict_start(self, name):
        prev_item = self.__prev_item[-1] and ',' or ''
        self._outln('{0}{1}{2}: {{'.format(' ' * self.__indent, prev_item, json.dumps(name)))
        self.__prev_item.append(False)
        self.__indent += 2

    def dict_item(self, k, v):
        prev_item = self.__prev_item[-1] and ',' or ''
        self._outln('{0}{1}{2}: {3}'.format(' ' * self.__indent, prev_item, json.dumps(k), json.dumps(v)))
        self.__prev_item[-1] = True

    def dict_end(self):
        self._outln('{0}}}'.format(' ' * self.__indent))
        self.__prev_item.pop()
        self.__prev_item[-1] = True
        self.__indent -= 2

    def list_start(self, name):
        prev_item = self.__prev_item[-1] and ',' or ''
        self._outln('{0}{1}{2}: ['.format(' ' * self.__indent, prev_item, json.dumps(name)))
        self.__prev_item.append(False)
        self.__indent += 2

    def list_item(self, item):
        prev_item = self.__prev_item[-1] and ',' or ''
        self._outln('{0}{1}{2}'.format(' ' * self.__indent, prev_item, json.dumps(item)))
        self.__prev_item[-1] = True

    def list_end(self):
        self._outln('{0}]'.format(' ' * self.__indent))
        self.__prev_item.pop()
        self.__prev_item[-1] = True
        self.__indent -= 2
