import sys
from colang import ColangMiniLexer
from colang import ColangMiniParser
from antlr4 import FileStream
from antlr4 import CommonTokenStream
from antlr4 import ParseTreeWalker
from flow_listener import FlowListener


def run(argv,  input_path: str = "./inputs/input_1.co"):
    # an alternative to FileStream is InputStream which takes a string
    input_stream = FileStream(argv[1] if len(argv) > 1 else input_path)

    lexer = ColangMiniLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = ColangMiniParser(stream)

    tree = parser.program()

    if parser.getNumberOfSyntaxErrors():
        raise Exception("Syntax Error")

    listener = FlowListener(input_path)

    walker = ParseTreeWalker()
    walker.walk(listener, tree)

    flows = listener.get_elements()

    print(flows)

    if __name__ == '__main__':
        run(sys.argv)
