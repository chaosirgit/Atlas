import os
import json
from typing import Dict, Any, List
import dashscope
from dashscope import Generation
from dotenv import load_dotenv
from .memory import Memory
from .tools import AtlasTools

load_dotenv()
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')


class AtlasBrain:
    """Atlas的大脑 - 整合千问、记忆和工具"""

    def __init__(self, debug: bool = False):
        self.memory = Memory()
        self.tools = AtlasTools()
        self.system_prompt = self._build_system_prompt()
        self.debug = debug  # 调试开关

    def _build_system_prompt(self) -> str:
        return """你是Atlas，一个具有文件系统操作和代码执行能力的AI助手。

    ## 可用工具

    ### 文件操作工具
    1. create_directory(path) - 创建目录
    2. delete_directory(path) - 删除目录  
    3. create_file(path, content) - 创建文件
    4. delete_file(path) - 删除文件
    5. move_directory(src, dst) - 移动目录
    6. move_file(src, dst) - 移动文件
    7. write_file(path, content, mode) - 写入文件 (mode: 'w'覆盖, 'a'追加)
    8. read_file(path) - 读取文件
    9. list_directory(path) - 列出目录内容

    ### 代码执行工具
    10. execute_python(code) - 执行Python代码
    
    ### 网页工具
    11. read_web_content(url) - 读取网页的主要文本内容
    12. list_web_resources(url) - 列出网页引用的所有资源 (CSS, JS, 图片等)

    ## 重要规则

    ### 文件路径规则
    - ✅ 正确: {"path": "test/hello.py"}
    - ❌ 错误: {"path": "atlas_workspace/test/hello.py"}
    - 所有路径都是相对路径，系统会自动加上atlas_workspace前缀

    ### Python代码规则
    - 以下模块已预导入，直接使用即可：math, random, datetime, json, collections, itertools, functools, re, statistics
    - ✅ 正确: print(math.pi)
    - ❌ 错误: import math; print(math.pi)
    - 代码超时限制：10秒

    ### 返回格式
    直接返回JSON数组，不要用```包裹：

    [
        {
            "thought": "你的思考过程",
            "action": "工具名称",
            "parameters": {参数}
        }
    ]

    ## 示例

    ### 文件操作示例
    用户: 创建一个test目录，里面放个hello.py文件
    返回:
    [
        {
            "thought": "先创建test目录",
            "action": "create_directory",
            "parameters": {"path": "test"}
        },
        {
            "thought": "在test目录下创建hello.py文件",
            "action": "create_file",
            "parameters": {"path": "test/hello.py", "content": "print('Hello')"}
        }
    ]

    ### 代码执行示例
    用户: 计算圆周率
    返回:
    [
        {
            "thought": "使用math.pi获取圆周率",
            "action": "execute_python",
            "parameters": {"code": "print(f'圆周率: {math.pi}')"}
        }
    ]

    如果不需要使用工具，就正常对话。"""

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