# #
# # from flask import Flask, render_template, request, jsonify
# # import tensorflow as tf
# # import numpy as np
# # import os
# # import datetime
# # from Seq2Seq import Encoder, Decoder
# # from tensorflow.keras.preprocessing.sequence import pad_sequences
# # import jieba
# #
# # app = Flask(__name__)
# #
# # # 配置参数da
# # data_path = '../tmp'
# # embedding_dim = 256
# # hidden_dim = 512
# # MAX_LENGTH = 50
# # CONST = {'_BOS': 0, '_EOS': 1, '_PAD': 2, '_UNK': 3}
# #
# #
# # def load_vocab():
# #     CONST = {'_BOS': 0, '_EOS': 1, '_PAD': 2, '_UNK': 3}
# #
# #     with open(os.path.join(data_path, 'all_dict.txt'), 'r', encoding='utf-8') as f:
# #         all_dict = [line.strip() for line in f if line.strip()]
# #
# #     word2id = {word: i + len(CONST) for i, word in enumerate(all_dict)}
# #     word2id.update(CONST)
# #
# #     id2word = {v: k for k, v in word2id.items()}
# #
# #     table = tf.lookup.StaticHashTable(
# #         initializer=tf.lookup.TextFileInitializer(
# #             os.path.join(data_path, 'all_dict.txt'),
# #             key_dtype=tf.string,
# #             key_index=tf.lookup.TextFileIndex.WHOLE_LINE,
# #             value_dtype=tf.int64,
# #             value_index=tf.lookup.TextFileIndex.LINE_NUMBER
# #         ),
# #         default_value=CONST['_UNK'] - len(CONST)
# #     )
# #
# #     return table, word2id, id2word
# #
# #
# #
# # def load_model():
# #     table, word2id, id2word = load_vocab()
# #     vocab_size = table.size().numpy() + len(CONST)
# #
# #     encoder = Encoder(vocab_size, embedding_dim, hidden_dim)
# #     decoder = Decoder(vocab_size, embedding_dim, hidden_dim)
# #
# #     checkpoint = tf.train.Checkpoint(encoder=encoder, decoder=decoder)
# #     checkpoint_dir = '../tmp/model'
# #     latest_checkpoint = tf.train.latest_checkpoint(checkpoint_dir)
# #
# #     if latest_checkpoint:
# #         checkpoint.restore(latest_checkpoint).expect_partial()
# #         print(f"已加载模型检查点: {latest_checkpoint}")
# #     else:
# #         print("未找到模型检查点，使用未训练的模型")
# #
# #     return encoder, decoder, table, word2id, id2word
# #
# #
# #
# # def preprocess_input(sentence, table, word2id):
# #     tokens = jieba.lcut(sentence)
# #     ids = []
# #     for token in tokens:
# #         lookup = table.lookup(tf.constant(token)).numpy()
# #         id_val = int(lookup) + len(CONST) if lookup >= 0 else CONST['_UNK']
# #         ids.append(id_val)
# #     input_ids = [CONST['_BOS']] + ids + [CONST['_EOS']]
# #     padded_ids = pad_sequences([input_ids], maxlen=MAX_LENGTH, padding='post', value=CONST['_PAD'])
# #     return tf.convert_to_tensor(padded_ids)
# #
# #
# # def generate_response(sentence, encoder, decoder, table, word2id, id2word):
# #     inputs = preprocess_input(sentence, table, word2id)
# #     enc_output, enc_hidden = encoder(inputs)
# #     dec_hidden = enc_hidden
# #     dec_input = tf.expand_dims([CONST['_BOS']], 0)
# #
# #     result = []
# #     for i in range(MAX_LENGTH):
# #         predictions, dec_hidden, _ = decoder(dec_input, dec_hidden, enc_output)
# #         predicted_id = tf.argmax(predictions[0]).numpy()
# #
# #         if predicted_id == CONST['_EOS']:
# #             break
# #
# #         predicted_word = id2word.get(predicted_id, '^_^')  # 不认识的词用表情符代替
# #         result.append(predicted_word)
# #         dec_input = tf.expand_dims([predicted_id], 0)
# #
# #     return ''.join(result)
# #
# #
# #
# # # 简单情绪分析
# # def analyze_emotion(text):
# #     positive_keywords = ['开心', '快乐', '满意', '轻松', '平静', '愉悦']
# #     negative_keywords = ['焦虑', '难过', '失眠', '压力', '抑郁', '孤独', '烦躁']
# #
# #     for word in positive_keywords:
# #         if word in text:
# #             return 'positive'
# #     for word in negative_keywords:
# #         if word in text:
# #             return 'negative'
# #     return 'neutral'
# #
# #
# # # 快捷回复
# # def load_quick_replies():
# #     return {
# #         '常见问题': ['我感到焦虑', '失眠怎么办', '如何缓解压力', '情绪低落'],
# #         '心理状态': ['我最近压力很大', '我感到很孤独', '我无法集中注意力', '我容易发脾气'],
# #         '寻求帮助': ['心理咨询有帮助吗', '如何找到合适的心理咨询师', '心理问题需要治疗吗']
# #     }
# #
# #
# # @app.route('/')
# # def index():
# #     return render_template('index.html')
# #
# #
# # @app.route('/api/chat', methods=['POST'])
# # def chat():
# #     data = request.json
# #     message = data.get('message', '')
# #     if not message:
# #         return jsonify({'error': '消息不能为空'}), 400
# #
# #     response = generate_response(
# #         message,
# #         app.config['encoder'],
# #         app.config['decoder'],
# #         app.config['table'],
# #         app.config['word2id'],
# #         app.config['id2word']
# #     )
# #
# #     emotion = analyze_emotion(message)
# #
# #     return jsonify({
# #         'reply': response,
# #         'emotion': emotion,
# #         'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
# #     })
# #
# #
# # @app.route('/api/quick_replies', methods=['GET'])
# # def quick_replies():
# #     return jsonify(load_quick_replies())
# #
# #
# # if __name__ == '__main__':
# #     print("正在加载模型...")
# #     encoder, decoder, table, word2id, id2word = load_model()
# #
# #     app.config['encoder'] = encoder
# #     app.config['decoder'] = decoder
# #     app.config['table'] = table
# #     app.config['word2id'] = word2id
# #     app.config['id2word'] = id2word
# #
# #
# #     print("模型加载完成，服务器启动中...")
# #     app.run(debug=True, host='0.0.0.0', port=5000)
# #
# #
# #
# #
#
# from flask import Flask, render_template, request, jsonify
# import tensorflow as tf
# import numpy as np
# import os
# import datetime
# from Seq2Seq import Encoder, Decoder
# from tensorflow.keras.preprocessing.sequence import pad_sequences
# import jieba
# import json
# from gtts import gTTS
# import base64
# import tempfile
# import time
#
# app = Flask(__name__)
#
# # 配置参数
# data_path = '../tmp'
# embedding_dim = 256
# hidden_dim = 512
# MAX_LENGTH = 50
# CONST = {'_BOS': 0, '_EOS': 1, '_PAD': 2, '_UNK': 3}
# AUDIO_CACHE_DIR = 'audio_cache'
# os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)
#
#
# def load_vocab():
#     CONST = {'_BOS': 0, '_EOS': 1, '_PAD': 2, '_UNK': 3}
#
#     with open(os.path.join(data_path, 'all_dict.txt'), 'r', encoding='utf-8') as f:
#         all_dict = [line.strip() for line in f if line.strip()]
#
#     word2id = {word: i + len(CONST) for i, word in enumerate(all_dict)}
#     word2id.update(CONST)
#
#     id2word = {v: k for k, v in word2id.items()}
#
#     table = tf.lookup.StaticHashTable(
#         initializer=tf.lookup.TextFileInitializer(
#             os.path.join(data_path, 'all_dict.txt'),
#             key_dtype=tf.string,
#             key_index=tf.lookup.TextFileIndex.WHOLE_LINE,
#             value_dtype=tf.int64,
#             value_index=tf.lookup.TextFileIndex.LINE_NUMBER
#         ),
#         default_value=CONST['_UNK'] - len(CONST)
#     )
#
#     return table, word2id, id2word
#
#
# def load_model():
#     table, word2id, id2word = load_vocab()
#     vocab_size = table.size().numpy() + len(CONST)
#
#     encoder = Encoder(vocab_size, embedding_dim, hidden_dim)
#     decoder = Decoder(vocab_size, embedding_dim, hidden_dim)
#
#     checkpoint = tf.train.Checkpoint(encoder=encoder, decoder=decoder)
#     checkpoint_dir = '../tmp/model'
#     latest_checkpoint = tf.train.latest_checkpoint(checkpoint_dir)
#
#     if latest_checkpoint:
#         checkpoint.restore(latest_checkpoint).expect_partial()
#         print(f"已加载模型检查点: {latest_checkpoint}")
#     else:
#         print("未找到模型检查点，使用未训练的模型")
#
#     return encoder, decoder, table, word2id, id2word
#
#
# def preprocess_input(sentence, table, word2id):
#     tokens = jieba.lcut(sentence)
#     ids = []
#     for token in tokens:
#         lookup = table.lookup(tf.constant(token)).numpy()
#         id_val = int(lookup) + len(CONST) if lookup >= 0 else CONST['_UNK']
#         ids.append(id_val)
#     input_ids = [CONST['_BOS']] + ids + [CONST['_EOS']]
#     padded_ids = pad_sequences([input_ids], maxlen=MAX_LENGTH, padding='post', value=CONST['_PAD'])
#     return tf.convert_to_tensor(padded_ids)
#
#
# def generate_response(sentence, encoder, decoder, table, word2id, id2word):
#     inputs = preprocess_input(sentence, table, word2id)
#     enc_output, enc_hidden = encoder(inputs)
#     dec_hidden = enc_hidden
#     dec_input = tf.expand_dims([CONST['_BOS']], 0)
#
#     result = []
#     for i in range(MAX_LENGTH):
#         predictions, dec_hidden, _ = decoder(dec_input, dec_hidden, enc_output)
#         predicted_id = tf.argmax(predictions[0]).numpy()
#
#         if predicted_id == CONST['_EOS']:
#             break
#
#         predicted_word = id2word.get(predicted_id, '^_^')  # 不认识的词用表情符代替
#         result.append(predicted_word)
#         dec_input = tf.expand_dims([predicted_id], 0)
#
#     return ''.join(result)
#
#
# # 简单情绪分析
# def analyze_emotion(text):
#     positive_keywords = ['开心', '快乐', '满意', '轻松', '平静', '愉悦']
#     negative_keywords = ['焦虑', '难过', '失眠', '压力', '抑郁', '孤独', '烦躁']
#
#     for word in positive_keywords:
#         if word in text:
#             return 'happy'  # 对应前端的happy情绪
#     for word in negative_keywords:
#         if word in text:
#             return 'anxious'  # 对应前端的anxious情绪
#     return 'neutral'
#
#
# # 快捷回复
# def load_quick_replies():
#     return {
#         '常见问题': ['我感到焦虑', '失眠怎么办', '如何缓解压力', '情绪低落'],
#         '心理状态': ['我最近压力很大', '我感到很孤独', '我无法集中注意力', '我容易发脾气'],
#         '寻求帮助': ['心理咨询有帮助吗', '如何找到合适的心理咨询师', '心理问题需要治疗吗']
#     }
#
#
# def text_to_speech(text, lang='zh-cn'):
#     """将文本转换为语音并返回音频文件路径"""
#     # 生成唯一的文件名
#     timestamp = int(time.time())
#     filename = f"response_{timestamp}.mp3"
#     file_path = os.path.join(AUDIO_CACHE_DIR, filename)
#
#     # 使用gTTS生成语音
#     tts = gTTS(text=text, lang=lang, slow=False)
#     tts.save(file_path)
#
#     return file_path
#
#
# def get_audio_base64(file_path):
#     """将音频文件转换为Base64编码"""
#     with open(file_path, 'rb') as f:
#         audio_data = f.read()
#     return base64.b64encode(audio_data).decode('utf-8')
#
#
# @app.route('/')
# def index():
#     return render_template('index.html')
#
#
# @app.route('/api/chat', methods=['POST'])
# def chat():
#     data = request.json
#     message = data.get('message', '')
#     history = data.get('history', [])
#
#     if not message:
#         return jsonify({'error': '消息不能为空'}), 400
#
#     response = generate_response(
#         message,
#         app.config['encoder'],
#         app.config['decoder'],
#         app.config['table'],
#         app.config['word2id'],
#         app.config['id2word']
#     )
#
#     emotion = analyze_emotion(message)
#
#     # 生成语音回复
#     audio_path = text_to_speech(response)
#     audio_base64 = get_audio_base64(audio_path)
#
#     return jsonify({
#         'reply': response,
#         'emotion': emotion,
#         'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#         'audio': audio_base64  # 返回音频Base64数据
#     })
#
#
# @app.route('/api/quick_replies', methods=['GET'])
# def quick_replies():
#     return jsonify(load_quick_replies())
#
#
# @app.route('/api/speech-to-text', methods=['POST'])
# def speech_to_text():
#     """处理语音转文字请求"""
#     try:
#         # 这里简化处理，实际应用中需要处理音频数据
#         # 前端会将语音识别的文本通过message参数传递过来
#         data = request.json
#         message = data.get('message', '')
#
#         if not message:
#             return jsonify({'error': '音频数据或文本为空'}), 400
#
#         return jsonify({'text': message}), 200
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
#
#
# if __name__ == '__main__':
#     print("正在加载模型...")
#     encoder, decoder, table, word2id, id2word = load_model()
#
#     app.config['encoder'] = encoder
#     app.config['decoder'] = decoder
#     app.config['table'] = table
#     app.config['word2id'] = word2id
#     app.config['id2word'] = id2word
#
#     print("模型加载完成，服务器启动中...")
#     app.run(debug=True, host='0.0.0.0', port=5000)


from flask import Flask, render_template, request, jsonify
import tensorflow as tf
import numpy as np
import os
import datetime
from Seq2Seq import Encoder, Decoder
from tensorflow.keras.preprocessing.sequence import pad_sequences
import jieba
import json
from gtts import gTTS
import base64
import tempfile
import time

app = Flask(__name__)

# 配置参数
data_path = '../tmp'
embedding_dim = 256
hidden_dim = 512
MAX_LENGTH = 50
CONST = {'_BOS': 0, '_EOS': 1, '_PAD': 2, '_UNK': 3}
AUDIO_CACHE_DIR = 'audio_cache'
os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)


def load_vocab():
    CONST = {'_BOS': 0, '_EOS': 1, '_PAD': 2, '_UNK': 3}

    with open(os.path.join(data_path, 'all_dict.txt'), 'r', encoding='utf-8') as f:
        all_dict = [line.strip() for line in f if line.strip()]

    word2id = {word: i + len(CONST) for i, word in enumerate(all_dict)}
    word2id.update(CONST)

    id2word = {v: k for k, v in word2id.items()}

    table = tf.lookup.StaticHashTable(
        initializer=tf.lookup.TextFileInitializer(
            os.path.join(data_path, 'all_dict.txt'),
            key_dtype=tf.string,
            key_index=tf.lookup.TextFileIndex.WHOLE_LINE,
            value_dtype=tf.int64,
            value_index=tf.lookup.TextFileIndex.LINE_NUMBER
        ),
        default_value=CONST['_UNK'] - len(CONST)
    )

    return table, word2id, id2word


def load_model():
    table, word2id, id2word = load_vocab()
    vocab_size = table.size().numpy() + len(CONST)

    encoder = Encoder(vocab_size, embedding_dim, hidden_dim)
    decoder = Decoder(vocab_size, embedding_dim, hidden_dim)

    checkpoint = tf.train.Checkpoint(encoder=encoder, decoder=decoder)
    checkpoint_dir = '../tmp/model'
    latest_checkpoint = tf.train.latest_checkpoint(checkpoint_dir)

    if latest_checkpoint:
        checkpoint.restore(latest_checkpoint).expect_partial()
        print(f"已加载模型检查点: {latest_checkpoint}")
    else:
        print("未找到模型检查点，使用未训练的模型")

    return encoder, decoder, table, word2id, id2word


def preprocess_input(sentence, table, word2id):
    tokens = jieba.lcut(sentence)
    ids = []
    for token in tokens:
        lookup = table.lookup(tf.constant(token)).numpy()
        id_val = int(lookup) + len(CONST) if lookup >= 0 else CONST['_UNK']
        ids.append(id_val)
    input_ids = [CONST['_BOS']] + ids + [CONST['_EOS']]
    padded_ids = pad_sequences([input_ids], maxlen=MAX_LENGTH, padding='post', value=CONST['_PAD'])
    return tf.convert_to_tensor(padded_ids)


def generate_response(sentence, encoder, decoder, table, word2id, id2word):
    inputs = preprocess_input(sentence, table, word2id)
    enc_output, enc_hidden = encoder(inputs)
    dec_hidden = enc_hidden
    dec_input = tf.expand_dims([CONST['_BOS']], 0)

    result = []
    for i in range(MAX_LENGTH):
        predictions, dec_hidden, _ = decoder(dec_input, dec_hidden, enc_output)
        predicted_id = tf.argmax(predictions[0]).numpy()

        if predicted_id == CONST['_EOS']:
            break

        predicted_word = id2word.get(predicted_id, '^_^')  # 不认识的词用表情符代替
        result.append(predicted_word)
        dec_input = tf.expand_dims([predicted_id], 0)

    return ''.join(result)


# 简单情绪分析
def analyze_emotion(text):
    positive_keywords = ['开心', '快乐', '满意', '轻松', '平静', '愉悦']
    negative_keywords = ['焦虑', '难过', '失眠', '压力', '抑郁', '孤独', '烦躁']

    for word in positive_keywords:
        if word in text:
            return 'happy'  # 对应前端的happy情绪
    for word in negative_keywords:
        if word in text:
            return 'anxious'  # 对应前端的anxious情绪
    return 'neutral'


# 快捷回复
def load_quick_replies():
    return {
        '常见问题': ['我感到焦虑', '失眠怎么办', '如何缓解压力', '情绪低落'],
        '心理状态': ['我最近压力很大', '我感到很孤独', '我无法集中注意力', '我容易发脾气'],
        '寻求帮助': ['心理咨询有帮助吗', '如何找到合适的心理咨询师', '心理问题需要治疗吗']
    }


def text_to_speech(text, lang='zh-cn'):
    """将文本转换为语音并返回音频文件路径"""
    # 生成唯一的文件名
    timestamp = int(time.time())
    filename = f"response_{timestamp}.mp3"
    file_path = os.path.join(AUDIO_CACHE_DIR, filename)

    # 使用gTTS生成语音
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(file_path)

    return file_path


def get_audio_base64(file_path):
    """将音频文件转换为Base64编码"""
    with open(file_path, 'rb') as f:
        audio_data = f.read()
    return base64.b64encode(audio_data).decode('utf-8')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    history = data.get('history', [])

    if not message:
        return jsonify({'error': '消息不能为空'}), 400

    response = generate_response(
        message,
        app.config['encoder'],
        app.config['decoder'],
        app.config['table'],
        app.config['word2id'],
        app.config['id2word']
    )

    emotion = analyze_emotion(message)

    # 生成语音回复
    audio_path = text_to_speech(response)
    audio_base64 = get_audio_base64(audio_path)

    return jsonify({
        'reply': response,
        'emotion': emotion,
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'audio': audio_base64  # 返回音频Base64数据
    })


@app.route('/api/quick_replies', methods=['GET'])
def quick_replies():
    return jsonify(load_quick_replies())


@app.route('/api/speech-to-text', methods=['POST'])
def speech_to_text():
    """处理语音转文字请求"""
    try:
        # 这里简化处理，实际应用中需要处理音频数据
        # 前端会将语音识别的文本通过message参数传递过来
        data = request.json
        message = data.get('message', '')

        if not message:
            return jsonify({'error': '音频数据或文本为空'}), 400

        return jsonify({'text': message}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("正在加载模型...")
    encoder, decoder, table, word2id, id2word = load_model()

    app.config['encoder'] = encoder
    app.config['decoder'] = decoder
    app.config['table'] = table
    app.config['word2id'] = word2id
    app.config['id2word'] = id2word

    print("模型加载完成，服务器启动中...")
    app.run(debug=True, host='0.0.0.0', port=5000)