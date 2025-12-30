import os
import json
from typing import Dict, Any, List
import dashscope
from dashscope import Generation
from .memory import Memory
from .tool_manager import AtlasTools
from .config import SYSTEM_PROMPT

dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')


class AtlasBrain:
    """Atlas的大脑 - 整合千问、记忆和工具"""

    def __init__(self, debug: bool = False):
        self.memory = Memory()
        self.tools = AtlasTools()
        self.system_prompt = SYSTEM_PROMPT
        self.debug = debug  # 调试开关

    def _parse_tool_call(self, response: str) -> List[Dict[str, Any]]:
        """解析AI返回的工具调用（支持多个）"""
        try:
            # 先尝试提取代码块中的JSON
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                # 🔥 新增：如果没有代码块，尝试直接解析整个回复
                json_str = response.strip()

            tool_calls = json.loads(json_str)

            # 确保返回的是列表
            if isinstance(tool_calls, dict):
                return [tool_calls]
            elif isinstance(tool_calls, list):
                return tool_calls
            else:
                return None
        except Exception as e:
            return None

    def _execute_tool(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具调用"""
        action = tool_call.get('action')
        params = tool_call.get('parameters', {})

        tool_map = {
            'create_directory': self.tools.create_directory,
            'delete_directory': self.tools.delete_directory,
            'create_file': self.tools.create_file,
            'delete_file': self.tools.delete_file,
            'move_directory': self.tools.move_directory,
            'move_file': self.tools.move_file,
            'write_file': self.tools.write_file,
            'read_file': self.tools.read_file,
            'list_directory': self.tools.list_directory,
            'execute_python': self.tools.execute_python,
            'read_web_content': self.tools.read_web_content,
            'list_web_resources': self.tools.list_web_resources,
            'get_current_location': self.tools.get_current_location,
            'get_weather': self.tools.get_weather,
        }

        if action in tool_map:
            return tool_map[action](**params)
        else:
            return {"success": False, "message": f"未知工具: {action}"}

    def think(self, user_input: str) -> str:
        """主思考函数 - 处理用户输入并返回响应"""
        # 添加用户消息到记忆
        self.memory.add_message('user', user_input)

        # 构建消息列表（包含相关的长期记忆）
        messages = [{'role': 'system', 'content': self.system_prompt}]
        messages.extend(self.memory.format_for_qwen(include_long_term=True, query=user_input))

        # 调用千问
        response = Generation.call(
            model='qwen3-max',
            messages=messages,
            result_format='message'
        )

        ai_response = response.output.choices[0].message.content

        if self.debug:
            print(f"\n{'=' * 50}")
            print(f"[DEBUG] AI原始回复:\n{ai_response}")
            print(f"{'=' * 50}\n")

        # 检查是否需要执行工具
        tool_calls = self._parse_tool_call(ai_response)

        if self.debug:
            print(f"[DEBUG] 解析到的工具调用: {tool_calls}\n")

        if tool_calls:
            # 执行所有工具
            results = []
            thoughts = []

            for tool_call in tool_calls:
                thought = tool_call.get('thought', '')
                thoughts.append(thought)
                tool_result = self._execute_tool(tool_call)
                results.append(tool_result)

                if self.debug:
                    print(f"[DEBUG] 执行 {tool_call.get('action')}: {tool_result}\n")

            # 将工具执行结果反馈给AI
            feedback = f"工具执行结果: {json.dumps(results, ensure_ascii=False)}"
            self.memory.add_message('assistant', ai_response)
            self.memory.add_message('system', feedback)

            # 让AI根据工具结果生成最终回复
            messages = [{'role': 'system', 'content': self.system_prompt}]
            messages.extend(self.memory.format_for_qwen(include_long_term=False))

            final_response = Generation.call(
                model='qwen3-max',
                messages=messages,
                result_format='message'
            )

            final_answer = final_response.output.choices[0].message.content
            self.memory.add_message('assistant', final_answer)

            # 格式化输出
            thoughts_str = "\n".join([f"  {i + 1}. {t}" for i, t in enumerate(thoughts)])
            results_str = "\n".join([f"  {i + 1}. {r['message']}" for i, r in enumerate(results)])

            return f"💭 思考:\n{thoughts_str}\n\n🔧 执行:\n{results_str}\n\n✅ {final_answer}"
        else:
            # 普通对话
            self.memory.add_message('assistant', ai_response)
            return ai_response


    def get_memory_summary(self) -> str:
        """获取记忆摘要"""
        convs = self.memory.get_all_conversations()
        return f"共有 {len(convs)} 条对话记录"


    def clear_memory(self):
        """清空记忆"""
        self.memory.clear_memory()