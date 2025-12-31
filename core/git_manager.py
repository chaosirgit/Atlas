"""
Git自动化管理模块
负责自动提交生成的工具代码到Git仓库
"""
import subprocess
from pathlib import Path
from typing import Optional, List
from datetime import datetime


class GitManager:
    """Git自动化管理器"""

    def __init__(self, repo_path: Path, auto_commit: bool = True):
        """
        初始化Git管理器

        Args:
            repo_path: Git仓库根目录
            auto_commit: 是否自动提交
        """
        self.repo_path = Path(repo_path)
        self.auto_commit = auto_commit
        self._ensure_git_initialized()

    def _ensure_git_initialized(self):
        """确保Git仓库已初始化"""
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            self._run_command(["git", "init"])
            print(f"✓ Git仓库已初始化: {self.repo_path}")

    def _run_command(self, command: List[str]) -> tuple[bool, str]:
        """
        执行Git命令

        Args:
            command: 命令列表

        Returns:
            (成功与否, 输出信息)
        """
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr

    def add_file(self, file_path: Path) -> bool:
        """
        添加文件到暂存区

        Args:
            file_path: 文件路径

        Returns:
            是否成功
        """
        # 转换为相对路径
        try:
            rel_path = file_path.relative_to(self.repo_path)
        except ValueError:
            rel_path = file_path

        success, output = self._run_command(["git", "add", str(rel_path)])
        if success:
            print(f"✓ 已添加到暂存区: {rel_path}")
        else:
            print(f"✗ 添加失败: {output}")
        return success

    def commit(self, message: str, author: Optional[str] = None) -> bool:
        """
        提交更改

        Args:
            message: 提交信息
            author: 作者信息（格式：Name <email>）

        Returns:
            是否成功
        """
        command = ["git", "commit", "-m", message]
        if author:
            command.extend(["--author", author])

        success, output = self._run_command(command)
        if success:
            print(f"✓ 提交成功: {message}")
        else:
            # 如果没有变更，不算失败
            if "nothing to commit" in output:
                print("ℹ 没有需要提交的变更")
                return True
            print(f"✗ 提交失败: {output}")
        return success

    def auto_commit_tool(self, file_path: Path, tool_name: str, action: str = "新增") -> bool:
        """
        自动提交工具代码

        Args:
            file_path: 工具文件路径
            tool_name: 工具名称
            action: 操作类型（新增/更新/删除）

        Returns:
            是否成功
        """
        if not self.auto_commit:
            return True

        # 添加文件
        if not self.add_file(file_path):
            return False

        # 生成中文提交信息
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"🔧 {action}工具: {tool_name}\n\n自动生成时间: {timestamp}"

        # 提交
        return self.commit(commit_message, author="Atlas AI <atlas@ai.system>")

    def get_status(self) -> str:
        """
        获取Git状态

        Returns:
            状态信息
        """
        success, output = self._run_command(["git", "status", "--short"])
        return output if success else "无法获取状态"

    def get_log(self, limit: int = 10) -> str:
        """
        获取提交日志

        Args:
            limit: 显示条数

        Returns:
            日志信息
        """
        success, output = self._run_command([
            "git", "log",
            f"-{limit}",
            "--pretty=format:%h - %s (%cr) <%an>"
        ])
        return output if success else "无法获取日志"
