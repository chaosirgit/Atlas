import os
import json
from typing import Dict, Any, List, Union
import dashscope
from dashscope import Generation
from .memory import Memory
from .tool_manager import AtlasTools
from .config import PLANNER_SYSTEM_PROMPT, EXECUTOR_SYSTEM_PROMPT, REFLECT_AND_REMEMBER_PROMPT
from .tools.knowledge import _load_kb # 导入知识库加载函数


class AtlasBrain:
    """
    Atlas的大脑 - 具备规划和执行能力的AI核心.
    """

    def __init__(self, debug: bool = False):
        self.memory = Memory()
        self.tools = AtlasTools()
        self.debug = debug
        dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')
        self.knowledge_base = _load_kb() # 初始化时加载知识库

    def _get_kb_context_string(self) -> str:
        """将知识库格式化为字符串, 以便注入到Prompt"""
        if not self.knowledge_base:
            return ""
        
        context = "--- 知识库 ---\n"
        for key, value in self.knowledge_base.items():
            context += f"- {key}: {value}\n"
        context += "---------------\n"
        return context

    def _call_qwen(self, system_prompt: str, user_prompt: str, history: List[Dict] = None) -> str:
        """通用的千问调用函数"""
        # 注入知识库上下文
        kb_context = self._get_kb_context_string()
        
        messages = [{'role': 'system', 'content': system_prompt}]
        if kb_context:
            messages.append({'role': 'system', 'content': kb_context})
        
        if history:
            messages.extend(history)
        messages.append({'role': 'user', 'content': user_prompt})

        if self.debug:
            print(f"\n{'='*20} QWEN CALL {'='*20}")
            # 打印完整的System Prompt以便调试
            for msg in messages:
                if msg['role'] == 'system':
                    print(f"SYSTEM: {msg['content'][:300]}...")
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
            
            # 如果知识库被修改,立即重新加载以保证上下文同步
            if tool_call.get('action') in ['remember', 'forget'] and tool_result.get('success'):
                self.knowledge_base = _load_kb()
                if self.debug:
                    print("🧠 知识库已更新!")
        
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
            logs.append("📝 任务被判定为简单任务, 启动持续对话模式...")
            
            # 对于简单任务, 我们启动一个ReAct循环, 直到获得最终答案
            context = f"原始任务: {user_input}\n"
            final_answer = ""
            max_turns = 5 # 防止无限循环
            
            for i in range(max_turns):
                logs.append(f"--- 思考回合 {i+1} ---")
                
                # 在这个模式下,我们直接使用Executor,并把之前的步骤作为上下文
                user_prompt = f"上下文:\n{context}\n\n当前任务: {user_input}\n\n请根据上下文, 判断是应该继续调用工具, 还是已经可以回答原始任务了. 如果能回答, 请直接给出最终答案, 不要再输出JSON."
                
                ai_response_str = self._call_qwen(EXECUTOR_SYSTEM_PROMPT, user_prompt)
                
                # 尝试解析工具调用
                tool_calls = self._parse_tool_call(ai_response_str)
                
                if not tool_calls:
                    # 如果没有工具调用, 我们认为这是最终答案
                    final_answer = ai_response_str
                    logs.append(f"✅ AI认为任务已完成, 生成最终回答.")
                    break
                
                # 执行工具
                for tool_call in tool_calls:
                    logs.append(f"🔧 准备执行工具: {tool_call.get('action')}")
                    result = self._execute_tool(tool_call)
                    context += f"在第{i+1}回合, 调用了工具 '{tool_call.get('action')}', 结果是: {json.dumps(result, ensure_ascii=False)}\n"
                    logs.append(f"工具执行结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if not final_answer:
                final_answer = "我已经执行了多次操作, 但似乎仍未得出最终结论. 您可以尝试更明确地提出您的问题."
                logs.append("⚠️ 已达到最大思考回合, 终止任务.")

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
        
        # 4. 反思
        # 在返回结果后, 悄悄进行一次反思, 看是否需要记忆新的事实
        self._reflection_step(user_input, final_answer)

        return {"answer": final_answer, "logs": logs}

    def _reflection_step(self, user_input: str, assistant_answer: str):
        """第四步: 反思对话, 决定是否需要记忆新知识"""
        if self.debug:
            print("\n🤔 正在反思对话, 检查是否有新知识需要记忆...")

        prompt = f"""对话:
User: {user_input}
Assistant: {assistant_answer}
"""
        
        # 调用Qwen判断是否需要记忆
        response = self._call_qwen(REFLECT_AND_REMEMBER_PROMPT, prompt)
        
        # 解析响应, 看是否有remember工具调用
        tool_calls = self._parse_tool_call(response)
        
        if not tool_calls:
            if self.debug:
                print("💡 无新知识需要记忆.")
            return

        if self.debug:
            print(f"💡 发现新知识, 准备记忆 {len(tool_calls)} 条...")
            
        for tool_call in tool_calls:
            if tool_call.get("action") == "remember":
                tool_result = self._execute_tool(tool_call)
                # 如果记忆成功, 立即更新当前大脑中的知识库
                if tool_result.get("success"):
                    self.knowledge_base = _load_kb()
                    if self.debug:
                        print(f"🧠 知识库已更新: {tool_call['parameters']}")
                else:
                    if self.debug:
                        print(f"⚠️ 记忆失败: {tool_result.get('message')}")


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
            'remember': self.tools.remember,
            'recall': self.tools.recall,
            'forget': self.tools.forget,
            'list_facts': self.tools.list_facts,
            'get_current_location': self.tools.get_current_location,
            'get_weather': self.tools.get_weather,
        }
        if action in tool_map:
            if self.debug:
                # 这个print可以保留,因为它在Flask的控制台输出,而不是给前端
                print(f"🔧 执行工具: {action} ({params})")
            return tool_map[action](**params)
        return {"success": False, "message": f"未知工具: {action}"}