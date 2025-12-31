from flask import Flask, render_template, request, jsonify, Response
from dotenv import load_dotenv
from core.brain import AtlasBrain

# 在程序启动时加载环境变量
load_dotenv()

app = Flask(__name__)

# 在应用启动时, 全局初始化一次AtlasBrain
# 开启debug模式, 以便在控制台看到详细的Qwen调用日志
print("正在初始化 Atlas 大脑, 请稍候...")
atlas_brain = AtlasBrain(debug=True)
print("✅ Atlas 大脑已准备就绪!")


@app.route('/')
def index():
    """渲染主页面"""
    return render_template('index.html')

@app.route('/think', methods=['POST'])
def think():
    """处理用户输入并返回Atlas的思考结果"""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    user_message = data.get('message')

    if not user_message:
        return jsonify({"error": "Missing message"}), 400

    try:
        # 调用大脑的思考函数
        result = atlas_brain.think(user_message)
        return jsonify(result)
    except Exception as e:
        # 在后端控制台打印详细错误
        print(f"Error during brain.think: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "大脑在思考时遇到了一个内部错误"}), 500

@app.route('/chat-stream') # Changed to GET by default, removed methods=['POST']
def chat_stream():
    """处理用户输入并使用SSE流式返回Atlas的思考过程"""
    user_message = request.args.get('message') # Read from query parameter

    if not user_message:
        # This will be caught by the frontend EventSource.onerror
        return Response("Missing message", status=400)

    def generate():
        try:
            for event_json in atlas_brain.think_stream(user_message):
                yield f"data: {event_json}\n\n"
        except Exception as e:
            print(f"Error during stream generation: {e}")
            import traceback
            traceback.print_exc()
            error_event = {"type": "error", "data": "流式处理时发生服务器错误"}
            yield f"data: {json.dumps(error_event)}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    # 使用 threaded=True 确保在处理请求时UI不会被阻塞
    # 使用 debug=False, 因为我们已经在 brain 中开启了我们自己的debug标志
    app.run(host='0.0.0.0', port=5001, threaded=True, debug=False)
