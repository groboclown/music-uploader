
import os
import sys
from .db import get_history
from .tools.cli_output import OutlineOutput, JsonOutput, YamlOutput, Output
from . import transform_db_path

def stdout_writer(text):
    print(text)

OUTPUT = OutlineOutput(stdout_writer)

class Cmd:
    def __init__(self):
        self.name = 'wha??'
        self.desc = 'No description'
        self.help = 'No help'

    def run(self, history, args):
        if len(args) > 0:
            if args[0] == '-h' or args[0] == 'help':
                print('{0}: {1}'.format(self.name, self.desc))
                print(self.help)
                return
        correct, args = self._parse_args(args)
        if not correct:
            return 1
        OUTPUT.start()
        ret = self._cmd(history, args)
        OUTPUT.end()
        return ret

    def _parse_args(self, args):
        """
        Parses the arguments.  Returns (True/False, parsed args).
        If the arguments were not valid, then the first argument should be
        False.  It is up to the parser to report the argument errors.
        """
        return True, args

    def _cmd(self, history, args):
        """
        Processes the command with the parsed arguments.
        Returns an error code or 0 if there was no error.
        """
        raise NotImplementedError()


class Option:
    def __init__(self):
        self.name = 'nope'
        self.has_arg = False
        self.help = 'Nope!'

    def process(self, arg):
        raise NotImplementedError()

    @property
    def key(self):
        if len(self.name) == 1:
            ret = '-{0}'.format(self.name)
        else:
            ret = '--{0}'.format(self.name)
        if self.has_arg:
            ret += '='
        return ret

    @property
    def key_help(self):
        if self.has_arg:
            return self.key + '?'
        return self.key


class TransformTranscodeOption(Option):
    def __init__(self):
        Option.__init__(self)
        self.name = 'txtc'
        self.has_arg = True
        self.help = 'Transform the transcode base directory in the form `src/path=dest/path`'

    def process(self, arg):
        p = arg.find('=')
        transform_transcode.set_transcode_transform(arg[0:p].strip(), arg[p+1:].strip())


class JsonOption(Option):
    def __init__(self):
        Option.__init__(self)
        self.name = 'json'
        self.has_arg = False
        self.help = 'Output in json format'

    def process(self, arg):
        set_output('json')

JSON_OPTION = JsonOption()


class YamlOption(Option):
    def __init__(self):
        Option.__init__(self)
        self.name = 'yaml'
        self.has_arg = False
        self.help = 'Output in yaml format'

    def process(self, arg):
        set_output('yaml')

YAML_OPTION = YamlOption()

STD_OPTIONS = (JSON_OPTION, YAML_OPTION)

OUTPUT_TYPES = {
    'json': JsonOutput,
    'yaml': YamlOutput,
    'default': OutlineOutput,
    'outline': OutlineOutput
}

def set_output(output_type, writer=None):
    if isinstance(output_type, str):
        if output_type not in OUTPUT_TYPES:
            raise Exception('No such output type {0}'.format(repr(output_type)))
        output_type = OUTPUT_TYPES[output_type]
    if not callable(output_type):
        raise Exception('Not an Output type: {0}'.format(repr(output_type)))
    if writer is None:
        writer = stdout_writer
    o = output_type(writer)
    if not isinstance(o, Output):
        raise Exception('Not an Output type: {0}'.format(repr(output_type)))
    global OUTPUT
    OUTPUT = o


def _help(exec_name, commands, options=None):
    option_list = []
    for option in options:
        option_list.append(option.key_help)
    print("Usage: {0} (output-dir) {1} (operation) (args)".format(
        exec_name, ' '.join(option_list)
    ))
    print("Where:")
    max_len = len('output-dir')
    for option in options:
        max_len = max(max_len, len(option.key))
    for cmd in commands:
        max_len = max(max_len, len(cmd.name))
    print(("  {0:" + str(max_len) + "s}  {1}").format('output-dir',
        'The directory where the output was generated.  This will contain the media.db file.'))
    for option in options:
        print(("  {0:" + str(max_len) + "s}  {1}").format(option.key_help, option.help))
    print("Operations:")
    for cmd in commands:
        print(("  {0:" + str(max_len) + "s}  {1}").format(cmd.name, cmd.desc))
    print("Use `(operation) help` for details on that command.")
    return 1



def std_main(args, commands, options=None):
    """
    Standard main processing. It should be invoked by running:

    >>> if __name__ == '__main__':
    ...   sys.exit(std_main(sys.argv, MY_COMMAND_LIST))
    """
    if options is None:
        options = STD_OPTIONS
    exec_name = args[0]
    cmd_args = args[1:]
    command_names = {}
    for cmd in commands:
        command_names[cmd.name] = cmd
    option_names = {}
    for option in options:
        option_names[option.key] = option

    if len(args) <= 1:
        return _help(exec_name, commands, options)
    media_db_file = os.path.join(cmd_args[0], 'media.db')
    if not os.path.isfile(media_db_file):
        print("Could not find `media.db` in path {0}".format(cmd_args[0]))
        return 1
    argp = 1
    while argp < len(cmd_args):
        if cmd_args[argp] == '-h' or cmd_args[argp] == '/h' or cmd_args[argp] == 'help':
            return _help(exec_name, commands, options)
        if cmd_args[argp] in command_names:
            cmd = command_names[cmd_args[argp]]
            argp += 1
            try:
                history = get_history(media_db_file)
            except Exception as e:
                print("Problem loading database file: {0}".format(e))
                return 1
            try:
                return cmd.run(history, cmd_args[argp:])
            finally:
                history.close()
        found_option = False
        for option_name, option in option_names.items():
            if option.has_arg and cmd_args[argp].startswith(option_name):
                arg = cmd_args[argp][len(option_name):]
                r = option.process(arg)
                if not(r == 0 or r is True or r is None):
                    return r
                found_option = True
                argp += 1
                break
            elif option_name == cmd_args[argp]:
                option.process(None)
                found_option = True
                argp += 1
                break
        if not found_option:
            print("Unknown operation {0}.  Use '-h' for help.".format(cmd_args[argp]))
            return 1
    print("You must specify an operation.  Use '-h' for help.")
    return 1


def prompt_key(msg, keys):
    print('{0} ({1}) > '.format(msg, '/'.join(keys)), end='')
    while True:
        sys.stdout.flush()
        k = sys.stdin.readline().strip()
        if k == '?':
            print('{0} ({1}) > '.format(msg, '/'.join(keys)), end='')
        if len(k) != 1 or k not in keys:
            print('{0} > '.format('/'.join(keys)), end='')
        else:
            return k


def prompt_value(msg):
    sys.stdout.write('{0} > '.format(msg))
    sys.stdout.flush()
    ret = sys.stdin.readline().strip()
    if len(ret) <= 0:
        return None
    return ret
