"""
Atlas主控制器
整合所有模块，提供统一的接口
"""
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from config.settings import (
    PROJECT_ROOT,
    GENERATED_TOOLS_DIR,
    LLM_MODEL,
    LLM_API_KEY,
    LLM_BASE_URL,
    GIT_AUTO_COMMIT
)
from core.ai_engine import AIEngine
from core.tool_generator import ToolGenerator
from core.tool_manager import ToolManager
from core.git_manager import GitManager


class Atlas:
    """Atlas主控制器"""

    def __init__(self):
        """初始化Atlas系统"""
        print("=" * 60)
        print("🚀 Atlas 系统启动中...")
        print("=" * 60)

        # 初始化各个模块
        self.ai_engine = AIEngine(
            model=LLM_MODEL,
            api_key=LLM_API_KEY,
            base_url=LLM_BASE_URL
        )
        print("✓ AI引擎已初始化")

        self.tool_generator = ToolGenerator(output_dir=GENERATED_TOOLS_DIR)
        print("✓ 工具生成器已初始化")

        self.tool_manager = ToolManager(tools_dir=GENERATED_TOOLS_DIR)
        print("✓ 工具管理器已初始化")

        self.git_manager = GitManager(
            repo_path=PROJECT_ROOT,
            auto_commit=GIT_AUTO_COMMIT
        )
        print("✓ Git管理器已初始化")

        print("=" * 60)
        print("✅ Atlas 系统启动完成！")
        print("=" * 60)

    def create_tool(
            self,
            requirement: str,
            auto_review: bool = True,
            max_iterations: int = 3
    ) -> Dict[str, Any]:
        """
        创建工具（完整流程）

        Args:
            requirement: 需求描述
            auto_review: 是否自动审查和改进
            max_iterations: 最大改进迭代次数

        Returns:
            创建结果
        """
        print("\n" + "=" * 60)
        print(f"📝 开始创建工具")
        print(f"需求: {requirement}")
        print("=" * 60)

        try:
            # 1. 分析需求
            print("\n[1/5] 分析需求...")
            analysis = self.ai_engine.analyze_requirement(requirement)
            tool_name = analysis['tool_name']

            # 2. 生成代码
            print("\n[2/5] 生成代码...")
            code = self.ai_engine.generate_code(analysis)

            # 3. 审查和改进代码
            if auto_review:
                print("\n[3/5] 审查代码...")
                iteration = 0
                while iteration < max_iterations:
                    review_result = self.ai_engine.review_code(code, analysis)

                    if review_result['passed'] and review_result['score'] >= 80:
                        print(f"✓ 代码质量达标 (评分: {review_result['score']}/100)")
                        break

                    print(f"⚠ 代码需要改进 (评分: {review_result['score']}/100)")
                    print(f"  问题: {', '.join(review_result['issues'][:3])}")

                    code = self.ai_engine.improve_code(code, review_result)
                    iteration += 1

                    if iteration < max_iterations:
                        print(f"  第 {iteration} 次改进完成，重新审查...")
            else:
                print("\n[3/5] 跳过代码审查")

            # 4. 生成工具文件
            print("\n[4/5] 生成工具文件...")
            file_path = self.tool_generator.generate_tool(
                tool_name=tool_name,
                description=analysis['description'],
                parameters=analysis['parameters'],
                code_body=code,
                author="Atlas AI"
            )
            print(f"✓ 文件已生成: {file_path}")

            # 5. Git提交
            print("\n[5/5] 提交到Git...")
            self.git_manager.auto_commit_tool(
                file_path=file_path,
                tool_name=tool_name,
                action="新增"
            )

            # 6. 注册工具
            self.tool_manager.reload_tool(tool_name)

            print("\n" + "=" * 60)
            print(f"✅ 工具创建成功: {tool_name}")
            print("=" * 60)

            return {
                'success': True,
                'tool_name': tool_name,
                'file_path': str(file_path),
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            print("\n" + "=" * 60)
            print(f"❌ 工具创建失败: {e}")
            print("=" * 60)
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        调用工具

        Args:
            tool_name: 工具名称
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        print(f"\n🔧 调用工具: {tool_name}")
        print(f"参数: {kwargs}")

        try:
            result = self.tool_manager.call_tool(tool_name, **kwargs)
            print(f"✓ 执行成功")
            return result
        except Exception as e:
            print(f"✗ 执行失败: {e}")
            raise

    def list_tools(self) -> list:
        """列出所有工具"""
        tools = self.tool_manager.list_tools()
        print(f"\n📋 当前共有 {len(tools)} 个工具:")
        for i, tool_name in enumerate(tools, 1):
            info = self.tool_manager.get_tool_info(tool_name)
            print(f"  {i}. {tool_name} - {info['metadata']['description']}")
        return tools

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具信息"""
        return self.tool_manager.get_tool_info(tool_name)

    def chat(self, message: str) -> str:
        """
        与AI对话

        Args:
            message: 用户消息

        Returns:
            AI回复
        """
        return self.ai_engine.chat(message)

    def export_manifest(self, output_path: Optional[Path] = None):
        """
        导出工具清单

        Args:
            output_path: 输出路径
        """
        if output_path is None:
            output_path = PROJECT_ROOT / "tools_manifest.json"

        self.tool_manager.export_tools_manifest(output_path)

    def get_git_status(self) -> str:
        """获取Git状态"""
        return self.git_manager.get_status()

    def get_git_log(self, limit: int = 10) -> str:
        """获取Git日志"""
        return self.git_manager.get_log(limit)
