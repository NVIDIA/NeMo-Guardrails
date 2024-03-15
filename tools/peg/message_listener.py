from typing import Literal
from dataclasses import dataclass

from colang import ColangMiniParser
from colang import ColangMiniListener

MessageRole = Literal["user", "bot"]

@dataclass
class Message:
    intent: str
    role: MessageRole
    samples: list[str]

    @classmethod
    def from_ctx(cls, ctx: ColangMiniParser.Define_messageContext):
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
        self._messages: list[Message] = []

    def exitDefine_message(self, ctx:ColangMiniParser.Define_messageContext):
        self._messages.append(Message.from_ctx(ctx))

    def get_parsed_data(self):
        return {
            "user_messages": [msg.to_dict() for msg in self._messages if msg.role == "user"],
            "bot_messages": [msg.to_dict() for msg in self._messages if msg.role == "bot"],
        }












    # it is possible to define flows and subflows in the same file
    # for illustration purposes, we will not use flows and subflows in this example
    # they are commented out below, but the actual implementation exist in the
    # flow_listener.py

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

    # def exitDefine_flow(self, ctx: ColangMiniParser.Define_flowContext):
    #     flow_name = ' '.join(token.getText() for token in ctx.flow_name().ID())
    #     self._flows[flow_name] = [stmt.getText() for stmt in ctx.block().stmt()]

    # def exitDefine_subflow(self, ctx: ColangMiniParser.Define_subflowContext):
    #     subflow_name = ' '.join(token.getText() for token in ctx.flow_name().ID())
    #     self._subflows[subflow_name] = [stmt.getText() for stmt in ctx.block().stmt()]
