import os
import json
from typing import Dict, Any, List, Union
import dashscope
from dashscope import Generation
from .memory import Memory
from .tool_manager import AtlasTools
from .config import PLANNER_SYSTEM_PROMPT, EXECUTOR_SYSTEM_PROMPT


class AtlasBrain:
    """
    Atlas的大脑 - 具备规划和执行能力的AI核心.
    """

    def __init__(self, debug: bool = False):
        self.memory = Memory()
        self.tools = AtlasTools()
        self.debug = debug
        dashscope.api_key = os.getenv('DASHSCOPE_API_KEY') # Moved here

    def _call_qwen(self, system_prompt: str, user_prompt: str, history: List[Dict] = None) -> str:
        """通用的千问调用函数"""
        messages = [{'role': 'system', 'content': system_prompt}]
        if history:
            messages.extend(history)
        messages.append({'role': 'user', 'content': user_prompt})

        if self.debug:
            print(f"\n{'='*20} QWEN CALL {'='*20}")
            print(f"SYSTEM: {system_prompt[:100]}...")
            print(f"USER: {user_prompt}")
            print(f"{'='*50}\n")

        response = Generation.call(
            model='qwen3-max',
            messages=messages,
            result_format='message'
        )
        content = response.output.choices[0].message.content
        
        if self.debug:
            print(f"\n{'='*20} QWEN RESPONSE {'='*20}")
            print(content)
            print(f"{'='*52}\n")
            
        return content

    def _get_plan(self, user_input: str) -> Union[List[str], str]:
        """第一步: 让规划师(Planner)分析用户意图并制定计划"""
        plan_str = self._call_qwen(PLANNER_SYSTEM_PROMPT, user_input)
        
        try:
            # 移除代码块标记
            if "```json" in plan_str:
                plan_str = plan_str.split("```json")[1].split("```")[0].strip()
            
            plan_json = json.loads(plan_str)
            return plan_json.get("plan", "simple_task")
        except Exception as e:
            if self.debug:
                print(f"⚠️ 规划解析失败: {e}\n将作为简单任务处理.")
            return "simple_task"

    def _execute_step(self, instruction: str, context: str = "") -> Dict[str, Any]:
        """第二步: 让执行者(Executor)根据单步指令调用工具"""
        # 构建给执行者的prompt, 包含历史执行的上下文
        user_prompt = f"上下文: {context}\n\n当前任务: {instruction}" if context else f"当前任务: {instruction}"

        # 调用Qwen获取工具调用
        ai_response = self._call_qwen(EXECUTOR_SYSTEM_PROMPT, user_prompt)
        
        # 解析并执行工具
        tool_calls = self._parse_tool_call(ai_response)
        
        if not tool_calls:
             # 如果没有工具调用, 直接返回AI的文本回复
            return {"success": True, "message": "无需工具", "output": ai_response}

        results = []
        for tool_call in tool_calls:
            tool_result = self._execute_tool(tool_call)
            results.append(tool_result)
        
        # 目前只简单返回第一个工具的结果, 将来可以优化
        return results[0] 

    def _summarize_results(self, original_task: str, results: List[Dict]) -> str:
        """第三步: 总结所有执行结果并生成最终回复"""
        summary_prompt = f"""原始任务: "{original_task}"

我们按计划执行了以下步骤, 并取得了这些结果:
{json.dumps(results, ensure_ascii=False, indent=2)}

请根据以上信息, 生成一个完整、清晰、友好的最终回复给用户.
"""
        final_answer = self._call_qwen("你是一个善于总结的AI助手。", summary_prompt)
        return final_answer

    def think(self, user_input: str) -> Dict[str, Any]:
        """
        Atlas的核心思考循环: 规划 -> 执行 -> 总结
        返回一个包含 'answer' 和 'logs' 的字典.
        """
        logs = []
        
        # 1. 规划
        logs.append("🤔 正在分析和规划任务...")
        plan = self._get_plan(user_input)
        self.memory.add_message('user', user_input)

        # 2. 执行
        if plan == "simple_task":
            logs.append("📝 任务简单, 直接执行...")
            result = self._execute_step(user_input)
            
            # 尝试从result中提取最相关的输出作为最终答案
            if result and result.get('answer'): # 优先提取 Tavily 的 'answer'
                final_answer = result['answer']
            elif result and result.get('output'): # 其次提取 'output' (如代码执行结果)
                final_answer = result['output']
            elif result and result.get('message'): # 再次提取 'message'
                final_answer = result['message']
            elif result and result.get('results'): # 如果有搜索结果, 也可以显示
                final_answer = f"找到了一些结果:\n{json.dumps(result['results'], ensure_ascii=False, indent=2)}"
            else:
                final_answer = "任务已执行, 但无明确输出."
            logs.append(f"✅ 结果: {final_answer}")

        else:
            logs.append(f"🗺️ 好的, 我已经制定了计划, 共 {len(plan)} 步.")
            step_results = []
            context = f"原始任务: {user_input}\n"

            for i, step in enumerate(plan):
                log_step = f"\n第 {i+1}/{len(plan)} 步: {step}"
                logs.append(log_step)
                
                result = self._execute_step(step, context)
                
                step_results.append({"step": step, "result": result})
                context += f"第{i+1}步({step})已完成, 结果: {json.dumps(result, ensure_ascii=False)}\n"
                logs.append(f"✅ 第 {i+1} 步完成. 结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

            # 3. 总结
            logs.append("\n✅ 所有步骤已完成, 正在总结最终结果...")
            final_answer = self._summarize_results(user_input, step_results)

        self.memory.add_message('assistant', final_answer)
        return {"answer": final_answer, "logs": logs}

    def _parse_tool_call(self, response: str) -> List[Dict[str, Any]]:
        """解析AI返回的工具调用"""
        try:
            # 先尝试提取代码块中的JSON
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            else:
                # 尝试直接解析整个回复
                json_str = response.strip()
            tool_calls = json.loads(json_str)
            return [tool_calls] if isinstance(tool_calls, dict) else tool_calls
        except Exception:
            return None

    def _execute_tool(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """执行具体的工具调用"""
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
            'web_search': self.tools.web_search,
            'get_current_location': self.tools.get_current_location,
            'get_weather': self.tools.get_weather,
        }
        if action in tool_map:
            if self.debug:
                # 这个print可以保留,因为它在Flask的控制台输出,而不是给前端
                print(f"🔧 执行工具: {action} ({params})")
            return tool_map[action](**params)
        return {"success": False, "message": f"未知工具: {action}"}