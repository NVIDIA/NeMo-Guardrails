from dataclasses import dataclass

from colang import ColangMiniParser
from colang import ColangMiniListener

class FlowListener(ColangMiniListener):
    """A listener that builds a flow from the parsed data.

    This listener is responsible for building a flow from the parsed data.

    # NOTE:

    This implementation is provided to mimic the behavior of the original parser.
    This is not the final implementation and is subject to change and improvements.
    """
    def __init__(self, filename: str = None):
        self._elements = []
        self._filename = filename or "main.co"  # Just for the sake of this example, ideally this should be dynamic.

    def get_source_mapping(self, ctx):
        return {
            'filename': self._filename,
            'line_number': ctx.start.line,
            'line_text': ctx.getText(),  # this might not be perfect and might need adjustments.
            'comment': None  # Assuming no comments for now.
        }

    def exitAssignment(self, ctx: ColangMiniParser.AssignmentContext):
        key = ctx.variable().getText()
        expression = ctx.expression().getText()

        element = {
            '_type': 'set',
            'key': key[1:],  # Removing the starting '$'
            'expression': expression,
            '_source_mapping': self.get_source_mapping(ctx)
        }

        self._elements.append(element)

    def exitIf_stmt(self, ctx: ColangMiniParser.If_stmtContext):
        expression = ctx.expression().getText()

        element = {
            '_type': 'if',
            'expression': expression,
            '_source_mapping': self.get_source_mapping(ctx),
            '_next_else': None  # Not handling else or elif for now
        }

        self._elements.append(element)

    def exitUser_stmt(self, ctx: ColangMiniParser.User_stmtContext):
        intent_name = " ".join([id.getText() for id in ctx.ID()])

        element = {
            '_type': 'UserIntent',
            'intent_name': intent_name,
            'intent_params': {},  # Not handling params for now
            '_source_mapping': self.get_source_mapping(ctx)
        }

        self._elements.append(element)

    def exitBot_stmt(self, ctx: ColangMiniParser.Bot_stmtContext):
        action_value = " ".join([id.getText() for id in ctx.ID()])

        element = {
            '_type': 'run_action',
            'action_name': 'utter',
            'action_params': {'value': action_value},
            '_source_mapping': self.get_source_mapping(ctx)
        }

        self._elements.append(element)

    def get_elements(self):
        return {
            'id': 'anonymous-12c21ada',  # This is hardcoded for now.
            'elements': self._elements
        }
