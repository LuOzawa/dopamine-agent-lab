"""固定响应只替代模型；编排、工具执行和消息流仍使用真实框架。"""
import os

# 教学离线模式不启用云端 tracing。
os.environ['LANGSMITH_TRACING'] = 'false'
os.environ['LANGCHAIN_TRACING_V2'] = 'false'

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class ScriptedModel(BaseChatModel):
    steps: list[AIMessage]

    @property
    def _llm_type(self):
        return 'teaching-script-no-network'

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        index = sum(isinstance(m, AIMessage) for m in messages)
        if index >= len(self.steps):
            raise RuntimeError('固定响应耗尽：检查工具错误或步骤配置')
        return ChatResult(generations=[ChatGeneration(message=self.steps[index])])


def call(name, args, number):
    return AIMessage(content='', tool_calls=[{
        'name': name, 'args': args, 'id': f'call_{number}', 'type': 'tool_call'}])
