"""
Atlas 命令行入口
"""
import sys
import os
from pathlib import Path

import dotenv
from dotenv import load_dotenv

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv()
from core.atlas import Atlas


def print_banner():
    """打印启动横幅"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     █████╗ ████████╗██╗      █████╗ ███████╗            ║
    ║    ██╔══██╗╚══██╔══╝██║     ██╔══██╗██╔════╝            ║
    ║    ███████║   ██║   ██║     ███████║███████╗            ║
    ║    ██╔══██║   ██║   ██║     ██╔══██║╚════██║            ║
    ║    ██║  ██║   ██║   ███████╗██║  ██║███████║            ║
    ║    ╚═╝  ╚═╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝            ║
    ║                                                           ║
    ║          AI驱动的自主工具生成与管理系统                  ║
    ║                  Version 1.0.0                           ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_menu():
    """打印菜单"""
    menu = """
    ┌─────────────────────────────────────────────────────────┐
    │  请选择操作:                                            │
    │                                                         │
    │  1. 创建新工具 (根据需求自动生成)                      │
    │  2. 列出所有工具                                        │
    │  3. 调用工具                                            │
    │  4. 查看工具信息                                        │
    │  5. 与AI对话                                            │
    │  6. 查看Git状态                                         │
    │  7. 查看Git日志                                         │
    │  8. 导出工具清单                                        │
    │  9. 退出                                                │
    │                                                         │
    └─────────────────────────────────────────────────────────┘
    """
    print(menu)


def create_tool_interactive(atlas: Atlas):
    """交互式创建工具"""
    print("\n" + "─" * 60)
    print("📝 创建新工具")
    print("─" * 60)

    requirement = input("\n请描述你需要的工具功能:\n> ").strip()

    if not requirement:
        print("❌ 需求描述不能为空")
        return

    auto_review = input("\n是否启用自动代码审查? (y/n, 默认y): ").strip().lower()
    auto_review = auto_review != 'n'

    result = atlas.create_tool(requirement, auto_review=auto_review)

    if result['success']:
        print(f"\n✅ 工具已创建: {result['tool_name']}")
        print(f"📁 文件路径: {result['file_path']}")
    else:
        print(f"\n❌ 创建失败: {result['error']}")


def call_tool_interactive(atlas: Atlas):
    """交互式调用工具"""
    print("\n" + "─" * 60)
    print("🔧 调用工具")
    print("─" * 60)

    tools = atlas.list_tools()

    if not tools:
        print("\n⚠ 还没有任何工具，请先创建工具")
        return

    tool_name = input("\n请输入要调用的工具名称:\n> ").strip()

    if tool_name not in tools:
        print(f"❌ 工具不存在: {tool_name}")
        return

    # 获取工具信息
    info = atlas.get_tool_info(tool_name)
    parameters = info['metadata']['parameters']

    print(f"\n工具: {tool_name}")
    print(f"描述: {info['metadata']['description']}")
    print(f"\n参数列表:")

    kwargs = {}
    for param_name, param_info in parameters.items():
        required = param_info.get('required', True)
        param_type = param_info.get('type', 'str')
        description = param_info.get('description', '')

        prompt = f"  {param_name} ({param_type})"
        if not required:
            prompt += " [可选]"
        prompt += f" - {description}\n  > "

        value = input(prompt).strip()

        if not value and required:
            print(f"❌ 参数 {param_name} 是必需的")
            return

        if value:
            # 简单的类型转换
            try:
                if param_type == 'int':
                    value = int(value)
                elif param_type == 'float':
                    value = float(value)
                elif param_type == 'bool':
                    value = value.lower() in ('true', 'yes', '1', 'y')
                elif param_type in ('list', 'dict'):
                    import json
                    value = json.loads(value)
            except Exception as e:
                print(f"⚠ 参数类型转换失败: {e}，将使用字符串类型")

            kwargs[param_name] = value

    # 调用工具
    try:
        result = atlas.call_tool(tool_name, **kwargs)
        print(f"\n✅ 执行结果:")
        print(result)
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")


def chat_interactive(atlas: Atlas):
    """交互式对话"""
    print("\n" + "─" * 60)
    print("💬 与AI对话 (输入 'exit' 退出对话)")
    print("─" * 60)

    while True:
        message = input("\n你: ").strip()

        if message.lower() in ('exit', 'quit', '退出'):
            break

        if not message:
            continue

        try:
            response = atlas.chat(message)
            print(f"\nAI: {response}")
        except Exception as e:
            print(f"\n❌ 对话失败: {e}")


def main():
    """主函数"""
    print_banner()

    # 检查API密钥
    if not os.getenv("DASHSCOPE_API_KEY"):
        print("\n⚠ 警告: 未设置 DASHSCOPE_API_KEY 环境变量")
        print("请运行: export DASHSCOPE_API_KEY='your-api-key'")
        print("或在 .env 文件中设置\n")

    # 初始化Atlas
    try:
        atlas = Atlas()
    except Exception as e:
        print(f"\n❌ 系统初始化失败: {e}")
        return

    # 主循环
    while True:
        print_menu()
        choice = input("请输入选项 (1-9): ").strip()

        if choice == '1':
            create_tool_interactive(atlas)

        elif choice == '2':
            print("\n" + "─" * 60)
            atlas.list_tools()
            print("─" * 60)

        elif choice == '3':
            call_tool_interactive(atlas)

        elif choice == '4':
            tool_name = input("\n请输入工具名称: ").strip()
            info = atlas.get_tool_info(tool_name)
            if info:
                import json
                print(f"\n{json.dumps(info, ensure_ascii=False, indent=2)}")
            else:
                print(f"\n❌ 工具不存在: {tool_name}")

        elif choice == '5':
            chat_interactive(atlas)

        elif choice == '6':
            print("\n" + "─" * 60)
            print("📊 Git状态:")
            print("─" * 60)
            print(atlas.get_git_status())

        elif choice == '7':
            print("\n" + "─" * 60)
            print("📜 Git日志:")
            print("─" * 60)
            print(atlas.get_git_log())

        elif choice == '8':
            atlas.export_manifest()

        elif choice == '9':
            print("\n👋 再见！")
            break

        else:
            print("\n❌ 无效的选项，请重新输入")

        input("\n按回车键继续...")


if __name__ == "__main__":
    main()
