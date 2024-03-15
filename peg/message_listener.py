from dataclasses import dataclass

from colang import ColangMiniParser
from colang import ColangMiniListener

@dataclass
class Message:
    intent: str
    role: str
    samples: list[str]

    @classmethod
    def from_ctx(cls, ctx: ColangMiniParser.Define_userContext | ColangMiniParser.Define_botContext):
        return cls(
            intent=' '.join(token.getText() for token in ctx.intent().ID()),  # concatenate IDs for intent,
            role=ctx.role().getText(),
            samples=[token.getText() for token in ctx.samples().sample().STRING()]
        )


    def to_dict(self):
        return {
            "intent": self.intent,
            "role": self.role,
            "samples": self.samples
        }


class MessageListener(ColangMiniListener):
    def __init__(self):
        self._user_messages: list[Message] = []
        self._bot_messages: list[Message] = []
        self._flows = {}
        self._subflows = {}  # Initializing subflows dictionary

    def exitDefine_user(self, ctx:ColangMiniParser.Define_userContext):
        self._user_messages.append(Message.from_ctx(ctx))

    def exitDefine_bot(self, ctx:ColangMiniParser.Define_botContext):
        self._bot_messages.append(Message.from_ctx(ctx))

    # def exitDefine_flow(self, ctx: ColangMiniParser.Define_flowContext):
    #     flow_name = ctx.flow_name().getText()
    #     self._flows[flow_name] = []
    #     for stmt in ctx.block().stmt():
    #         if isinstance(stmt, ColangMiniParser.Define_subflowContext):
    #             subflow_name = stmt.flow_name().getText()
    #             self._subflows[subflow_name] = []
    #             for subflow_stmt in stmt.block().stmt():
    #                 self._subflows[subflow_name].append(subflow_stmt.getText())
    #         else:
    #             self._flows[flow_name].append(stmt.getText())

    def exitDefine_flow(self, ctx: ColangMiniParser.Define_flowContext):
        flow_name = ' '.join(token.getText() for token in ctx.flow_name().ID())
        self._flows[flow_name] = [stmt.getText() for stmt in ctx.block().stmt()]

    def exitDefine_subflow(self, ctx: ColangMiniParser.Define_subflowContext):
        subflow_name = ' '.join(token.getText() for token in ctx.flow_name().ID())
        self._subflows[subflow_name] = [stmt.getText() for stmt in ctx.block().stmt()]

    def get_parsed_data(self):
        return {
            "user_messages": [msg.to_dict() for msg in self._user_messages],
            "bot_messages": [msg.to_dict() for msg in self._bot_messages],
            "flows": self._flows,
            "subflows": self._subflows
        }