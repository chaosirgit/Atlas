from dotenv import load_dotenv
load_dotenv() # 在所有其他模块导入前加载 .env 文件

from core.brain import AtlasBrain
import atexit
from core.evolution_controller import EvolutionController



def main():
    print("🤖 Atlas v0.0.2 启动!")
    print("=" * 50)

    # 开启调试模式
    brain = AtlasBrain(debug=True)

    # 初始化进化控制器
    evolution_controller = EvolutionController()

    # 注册退出时的保存函数
    def save_on_exit():
        print("\n💾 正在保存记忆...")
        brain.memory.save_all()

    atexit.register(save_on_exit)

    print(f"📊 {brain.memory.get_summary()}")
    print("\n命令列表:")
    print("  exit - 退出程序")
    print("  clear - 清空记忆")
    print("  /learn <名称>|<描述>|<要求> - 学习新能力")
    print("  /caps - 查看所有能力")
    print()

    while True:
        try:
            user_input = input("你: ").strip()

            if not user_input:
                continue

            # 退出命令
            if user_input.lower() == 'exit':
                print("👋 再见!")
                break

            # 清空记忆命令
            if user_input.lower() == 'clear':
                brain.memory.clear_memory()
                print(f"📊 {brain.memory.get_summary()}")
                continue

            # 学习新能力命令
            if user_input.startswith("/learn"):
                try:
                    # 解析: /learn 能力名称|能力描述|额外要求
                    content = user_input[6:].strip()
                    parts = content.split("|")

                    if len(parts) < 2:
                        print("❌ 用法: /learn 能力名称|能力描述|额外要求(可选)")
                        print("   示例: /learn Weather|获取天气信息|需要支持多个城市")
                        continue

                    name = parts[0].strip()
                    description = parts[1].strip()
                    requirements = parts[2].strip() if len(parts) > 2 else ""

                    print(f"\n🧠 开始学习新能力: {name}")
                    print("=" * 60)

                    result = evolution_controller.learn_new_capability(
                        name=name,
                        description=description,
                        requirements=requirements
                    )

                    # 显示每个步骤的结果
                    for step in result['steps']:
                        if step['status'] == 'success':
                            print(f"✓ [{step['step']}] {step['message']}")
                        elif step['status'] == 'failed':
                            print(f"✗ [{step['step']}] {step['message']}")
                        else:
                            print(f"⚠ [{step['step']}] {step['message']}")

                    print("=" * 60)

                    if result['success']:
                        print(f"🎉 能力 '{name}' 学习成功!")
                        if 'code_path' in result:
                            print(f"📄 代码位置: {result['code_path']}")
                    else:
                        print(f"😢 能力 '{name}' 学习失败")

                    print()

                except Exception as e:
                    print(f"❌ 学习能力时出错: {e}\n")

                continue

            # 查看所有能力命令
            if user_input == "/caps":
                print("\n📚 当前已学习的能力:")
                print("=" * 60)

                caps = evolution_controller.list_capabilities()

                if caps:
                    for cap in caps:
                        status_icon = {
                            'active': '✓',
                            'tested': '⚡',
                            'pending': '⏳',
                            'failed': '✗'
                        }.get(cap['status'], '?')

                        print(f"{status_icon} {cap['name']} [{cap['status']}]")
                        print(f"   描述: {cap['description']}")
                        print(f"   创建: {cap['created_at']}")
                        print(f"   路径: {cap['code_path']}")
                        print()
                else:
                    print("还没有学习任何能力")

                print("=" * 60)
                print()
                continue

            # 正常对话
            response = brain.think(user_input)
            print(f"\nAtlas: {response}\n")

        except KeyboardInterrupt:
            print("\n\n👋 检测到中断，正在退出...")
            break
        except Exception as e:
            print(f"❌ 错误: {e}\n")

    if __name__ == "__main__":
        main()
