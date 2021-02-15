"""OxygenC v0.1.0

usage:
    oxygenc compile [-ldo FILE] <file>
    oxygenc run [-td] <file>
    oxygenc [-hv]

options:
    -h, --help                  Shows this help menu
    -v, --version               Shows the version
    -l, --llvm                  Emit llvm code
    -o FILE, --output FILE      Output file
    -t, --timer                 Time the execution
    -d, --debug                 Debug mode
"""

import os
from typing import Dict, Any

from docopt import docopt
from oxygen.compiler.code_generator import OxyCodeGenerator
from oxygen.lexer import Lexer
from oxygen.parser import Parser
from oxygen.type_checker import Preprocessor
from oxygen.utils import error


def process_file(oxy_file: str) -> OxyCodeGenerator:
    if not os.path.isfile(oxy_file):
        error(oxy_file + " is not a valid file")

    code = open(oxy_file, encoding="utf8").read()
    lexer = Lexer(code, oxy_file)
    parser = Parser(lexer)
    prog = parser.parse()
    symtab_builder = Preprocessor(oxy_file)
    symtab_builder.check(prog)

    generator = OxyCodeGenerator(oxy_file)
    generator.generate_code(prog)

    return generator


def _run(arg_list: Dict[str, Any]) -> None:
    oxy_file: str = arg_list['<file>']
    timer: bool = arg_list['--timer']
    debug: bool = arg_list['--debug']

    generator = process_file(oxy_file)
    generator.evaluate(not debug, debug, timer)


def _compile(arg_list: Dict[str, Any]) -> None:
    oxy_file: str = arg_list['<file>']
    output: str = arg_list['--output']
    emit_llvm: bool = arg_list['--llvm']
    debug: bool = arg_list['--debug']

    generator = process_file(oxy_file)
    generator.compile(oxy_file, not debug, output, emit_llvm)


if __name__ == "__main__":
    args: Dict[str, Any] = docopt(__doc__, version='v0.4.1')

    if args['compile']:
        _compile(args)
    elif args['run']:
        _run(args)
    else:
        exit(__doc__)
