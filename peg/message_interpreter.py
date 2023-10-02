import sys
from colang import ColangMiniLexer
from colang import ColangMiniParser
from antlr4 import FileStream
from antlr4 import CommonTokenStream
from antlr4 import ParseTreeWalker
from message_listener import MessageListener


def main(argv):
  input_path = "input.co"
  input_stream = FileStream(argv[1] if len(argv) > 1 else input_path)
  lexer = ColangMiniLexer(input_stream)
  stream = CommonTokenStream(lexer)
  parser = ColangMiniParser(stream)
  tree = parser.program()
  if parser.getNumberOfSyntaxErrors():
    raise Exception("Syntax Error")
  listener = MessageListener()

  walker = ParseTreeWalker()
  walker.walk(listener, tree)

  walker.walk(listener, tree)

  print(listener.get_parsed_data())

if __name__ == '__main__':
  main(sys.argv)