"""
进化控制器 - 协调自我进化流程
"""
import os
from pathlib import Path
from .self_evolution import (
    CapabilityManager,
    CodeGenerator,
    SandboxTester,
    GitOperator
)


class EvolutionController:
    def __init__(self, api_key: str = None):
        self.capability_manager = CapabilityManager()

        # 从环境变量获取API密钥
        if api_key is None:
            api_key = os.getenv('DASHSCOPE_API_KEY')

        self.code_generator = CodeGenerator(api_key=api_key)
        self.sandbox_tester = SandboxTester()
        self.git_operator = GitOperator()

    def learn_new_capability(self, name: str, description: str,
                             requirements: str = "") -> dict:
        """学习新能力的完整流程"""

        result = {
            "success": False,
            "capability_name": name,
            "steps": []
        }

        # 步骤1: 检查能力是否已存在
        if self.capability_manager.get_capability(name):
            result["steps"].append({
                "step": "检查重复",
                "status": "failed",
                "message": f"能力'{name}'已存在"
            })
            return result

        result["steps"].append({
            "step": "检查重复",
            "status": "success",
            "message": "能力不存在，可以创建"
        })

        # 步骤2: 生成代码
        print(f"正在生成'{name}'的代码...")
        code_path = self.code_generator.generate_and_save(
            capability_name=name,
            capability_description=description,
            requirements=requirements
        )

        if not code_path:
            result["steps"].append({
                "step": "代码生成",
                "status": "failed",
                "message": "代码生成失败"
            })
            return result

        result["steps"].append({
            "step": "代码生成",
            "status": "success",
            "message": f"代码已生成: {code_path}"
        })
        result["code_path"] = code_path

        # 步骤3: 添加到能力管理器
        class_name = f"{name.title()}Tool"
        self.capability_manager.add_capability(
            name=name,
            description=description,
            code_path=code_path,
            status="pending"
        )

        result["steps"].append({
            "step": "注册能力",
            "status": "success",
            "message": "能力已注册到管理器"
        })

        # 步骤4: 沙盒测试
        print(f"正在测试'{name}'...")
        test_success, test_message = self.sandbox_tester.run_full_test(
            file_path=code_path,
            class_name=class_name
        )

        if test_success:
            self.capability_manager.update_capability_status(name, "tested")
            result["steps"].append({
                "step": "沙盒测试",
                "status": "success",
                "message": test_message
            })
        else:
            self.capability_manager.update_capability_status(name, "failed")
            result["steps"].append({
                "step": "沙盒测试",
                "status": "failed",
                "message": test_message
            })
            return result

        # 步骤5: Git提交
        print(f"正在提交到版本控制...")
        commit_success, commit_message = self.git_operator.commit_new_capability(
            capability_name=name,
            file_paths=[
                code_path,
                "core/self_evolution/capabilities.json"
            ]
        )

        if commit_success:
            self.capability_manager.update_capability_status(name, "active")
            result["steps"].append({
                "step": "版本控制",
                "status": "success",
                "message": "已提交到Git"
            })
            result["success"] = True
        else:
            result["steps"].append({
                "step": "版本控制",
                "status": "warning",
                "message": f"Git提交失败，但能力已可用: {commit_message}"
            })
            # 即使Git提交失败，能力也是可用的
            self.capability_manager.update_capability_status(name, "active")
            result["success"] = True

        return result

    def list_capabilities(self, status=None):
        """列出所有能力"""
        return self.capability_manager.list_capabilities(status)

    def get_capability_info(self, name: str):
        """获取能力信息"""
        return self.capability_manager.get_capability(name)
