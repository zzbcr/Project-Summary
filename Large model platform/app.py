from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from model import MedicalQAModel
import copy
from langchain.schema import HumanMessage
import logging

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:*", "http://127.0.0.1:*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

qa_model = MedicalQAModel()

@app.route("/")
def index():
    return render_template('1.html')

@app.route("/api/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        logger.debug(f"Received request data: {data}")
        
        question = data.get("question", "").strip()
        if not question:
            return jsonify({"error": "问题不能为空"}), 400

        model_info = qa_model.model_mapping[qa_model.current_model]
        messages = copy.deepcopy(model_info["messages"])
        messages.append(HumanMessage(content=question))
        
        response = model_info["client"](messages)
        answer = response.content
        
        logger.debug(f"Model response: {answer}")
        
        return jsonify({
            "answer": answer,
            "model": model_info["name"],
            "status": "success"
        })
    except Exception as e:
        logger.error(f"Error in ask endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

# 在 app.py 中添加以下代码
@app.route("/api/switch_model", methods=["POST"])
def switch_model():
    try:
        qa_model.switch_model()
        model_info = qa_model.model_mapping[qa_model.current_model]
        return jsonify({
            "status": "success",
            "model": model_info["name"]
        })
    except Exception as e:
        logger.error(f"Error in switch_model endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500
    
@app.route("/api/upload_medical_files", methods=["POST"])
def upload_medical_files():
    try:
        if 'files' not in request.files:
            return jsonify({"error": "没有上传文件", "status": "error"}), 400
            
        files = request.files.getlist('files')
        allowed_extensions = ['.pdf', '.doc', '.docx', '.xml', '.jpg', '.png']
        
        processed_files = []
        for file in files:
            # 验证文件类型
            filename = file.filename.lower()
            if not any(filename.endswith(ext) for ext in allowed_extensions):
                continue
                
            # 在实际应用中，这里应该保存文件并处理
            file_info = {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(file.read())
            }
            file.seek(0)  # 重置文件指针
            processed_files.append(file_info)
            
        return jsonify({
            "status": "success",
            "processed_files": processed_files,
            "message": "文件上传成功，正在分析..."
        })
    except Exception as e:
        logger.error(f"文件上传出错: {str(e)}", exc_info=True)
        return jsonify({"error": str(e), "status": "error"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001, threaded=True)