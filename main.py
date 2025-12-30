from dotenv import load_dotenv
load_dotenv() # 在所有其他模块导入前加载 .env 文件

from core.brain import AtlasBrain
import atexit


def main():
    print("🤖 Atlas v0.0.2 启动!")
    print("=" * 50)

    # 开启调试模式
    brain = AtlasBrain(debug=True)

    # 注册退出时的保存函数
    def save_on_exit():
        print("\n💾 正在保存记忆...")
        brain.memory.save_all()

    atexit.register(save_on_exit)

    print(f"📊 {brain.memory.get_summary()}")
    print("\n输入 'exit' 退出, 'clear' 清空记忆\n")

    while True:
        try:
            user_input = input("你: ").strip()

            if not user_input:
                continue

            if user_input.lower() == 'exit':
                print("👋 再见!")
                break

            if user_input.lower() == 'clear':
                brain.memory.clear_memory()
                print(f"📊 {brain.memory.get_summary()}")
                continue

            response = brain.think(user_input)
            print(f"\nAtlas: {response}\n")

        except KeyboardInterrupt:
            print("\n\n👋 检测到中断，正在退出...")
            break
        except Exception as e:
            print(f"❌ 错误: {e}\n")


if __name__ == "__main__":
    main()
