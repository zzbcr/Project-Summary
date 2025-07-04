# -*- coding: UTF-8 -*-
import tensorflow as tf
import os
import datetime
from Seq2Seq import Encoder, Decoder
import typing
import jieba

# 设置参数
data_path = '../data'  # 数据目录（如果需要使用data目录下的文件）
tmp_path = '../tmp'  # tmp目录路径
epoch = 501  # 迭代训练次数
batch_size = 25  # 每批次样本数
embedding_dim = 256  # 词嵌入维度
hidden_dim = 512  # 隐层神经元个数
shuffle_buffer_size = 4  # 清洗数据数据集时将缓冲的实例数
device = 1  # 使用的设备ID，-1即不使用GPU
checkpoint_path = os.path.join(tmp_path, 'model')  # 模型参数保存的路径


# 确保目录存在
def ensure_model_dir():
    """确保模型保存目录存在且正确"""
    try:
        # 如果tmp目录不存在，创建它
        if not os.path.exists(tmp_path):
            os.makedirs(tmp_path)
            print(f"创建目录: {tmp_path}")

        # 如果model目录存在但不是目录，删除它
        if os.path.exists(checkpoint_path) and not os.path.isdir(checkpoint_path):
            os.remove(checkpoint_path)
            print(f"删除文件: {checkpoint_path}")

        # 确保model目录存在
        if not os.path.exists(checkpoint_path):
            os.makedirs(checkpoint_path)
            print(f"创建目录: {checkpoint_path}")

        return True
    except Exception as e:
        print(f"创建目录时出错: {str(e)}")
        return False


# 初始化目录
if not ensure_model_dir():
    raise RuntimeError("无法创建模型保存目录")

MAX_LENGTH = 50  # 句子的最大词长
CONST = {'_BOS': 0, '_EOS': 1, '_PAD': 2, '_UNK': 3}  # 特殊标记


# 确保目录结构存在
def ensure_directory_exists(path: str, is_file_path: bool = False) -> None:
    """
    确保指定路径的目录存在

    Args:
        path: 需要确保存在的路径
        is_file_path: 如果True，表示path是文件路径，否则是目录路径
    """
    directory = os.path.dirname(path) if is_file_path else path
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"创建目录: {directory}")
        except Exception as e:
            raise RuntimeError(f"无法创建目录 {directory}: {str(e)}")

    if not os.path.isdir(directory):
        raise ValueError(f"路径 {directory} 不是一个有效的目录")


# 验证并创建必要的目录
print(f"当前工作目录: {os.getcwd()}")
ensure_directory_exists(tmp_path)
ensure_directory_exists(checkpoint_path)

# 加载词典
print(f'[{datetime.datetime.now()}] 加载词典...')
dict_path = os.path.join(tmp_path, 'all_dict.txt')
ensure_directory_exists(dict_path, is_file_path=True)
if not os.path.exists(dict_path):
    raise FileNotFoundError(f"词典文件不存在: {dict_path}")

table = tf.lookup.StaticHashTable(
    initializer=tf.lookup.TextFileInitializer(
        dict_path,
        tf.string,
        tf.lookup.TextFileIndex.WHOLE_LINE,
        tf.int64,
        tf.lookup.TextFileIndex.LINE_NUMBER
    ),
    default_value=CONST['_UNK'] - len(CONST)
)

# 加载数据
print(f'[{datetime.datetime.now()}] 加载预处理后的数据...')


# 构造序列化的键值对字典
def to_tmp(text):
    """
    text：文本
    """
    tokenized = tf.strings.split(tf.reshape(text, [1]), sep=' ')
    tmp = table.lookup(tokenized.values) + len(CONST)
    return tmp


# 增加开始和结束标记
def add_start_end_tokens(tokens):
    """
    tokens：序列化的键值对字典
    """
    tmp = tf.concat([[CONST['_BOS']], tf.cast(tokens, tf.int32), [CONST['_EOS']]], axis=0)
    return tmp


# 获取数据
def get_dataset(src_path: str, table: tf.lookup.StaticHashTable) -> tf.data.Dataset:
    """
    src_path：文件路径
    table：初始化后不可变的通用哈希表。
    """
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"数据文件不存在: {src_path}")

    dataset = tf.data.TextLineDataset(src_path)
    dataset = dataset.map(to_tmp)
    dataset = dataset.map(add_start_end_tokens)
    return dataset


# 修改为tmp目录
source_path = os.path.join(tmp_path, 'source.txt')
target_path = os.path.join(tmp_path, 'target.txt')
ensure_directory_exists(source_path, is_file_path=True)
ensure_directory_exists(target_path, is_file_path=True)

src_train = get_dataset(source_path, table)
tgt_train = get_dataset(target_path, table)

# 把数据和特征构造为tf数据集
train_dataset = tf.data.Dataset.zip((src_train, tgt_train))


# 过滤数据实例
def filter_instance_by_max_length(src: tf.Tensor, tgt: tf.Tensor) -> tf.Tensor:
    """
    src：特征
    tgt：标签
    """
    return tf.logical_and(tf.size(src) <= MAX_LENGTH, tf.size(tgt) <= MAX_LENGTH)


train_dataset = train_dataset.filter(filter_instance_by_max_length)  # 过滤数据
train_dataset = train_dataset.shuffle(shuffle_buffer_size)  # 打乱数据
train_dataset = train_dataset.padded_batch(  # 将数据长度变为一致，长度不足用_PAD填充补齐
    batch_size,
    padded_shapes=([MAX_LENGTH + 2], [MAX_LENGTH + 2]),
    padding_values=(CONST['_PAD'], CONST['_PAD']),
    drop_remainder=True,
)
# 提升产生下一个批次数据的效率
train_dataset = train_dataset.prefetch(tf.data.experimental.AUTOTUNE)

# 建模
print(f'[{datetime.datetime.now()}] 创建一个seq2seq模型...')
encoder = Encoder(table.size().numpy() + len(CONST), embedding_dim, hidden_dim)
decoder = Decoder(table.size().numpy() + len(CONST), embedding_dim, hidden_dim)

# 设置优化器
print(f'[{datetime.datetime.now()}] 准备优化器...')
optimizer = tf.keras.optimizers.Adam()

# 设置损失函数
print(f'[{datetime.datetime.now()}] 设置损失函数...')
loss_object = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True, reduction='none')


# 损失函数
def loss_function(loss_object, real: tf.Tensor, pred: tf.Tensor) -> tf.Tensor:
    """
    loss_object：损失值计算方式
    real：真实值
    pred：预测值
    """
    # 计算真实值和预测值的误差
    loss_ = loss_object(real, pred)
    # 返回输出不相等的并用_PAD填充
    mask = tf.math.logical_not(tf.math.equal(real, CONST['_PAD']))
    # 数据格式转换为跟损失值一致
    mask = tf.cast(mask, dtype=loss_.dtype)
    return tf.reduce_mean(loss_ * mask)  # 返回平均误差


# 设置模型保存
checkpoint = tf.train.Checkpoint(optimizer=optimizer, encoder=encoder, decoder=decoder)


# 训练
def train_step(src: tf.Tensor, tgt: tf.Tensor):
    """
    src：输入的文本
    tgt：标签
    """
    # 获取标签维度
    tgt_width, tgt_length = tgt.shape
    loss = 0
    # 创建梯度带，用于反向计算导数
    with tf.GradientTape() as tape:
        # 对输入的文本编码
        enc_output, enc_hidden = encoder(src)
        # 设置解码的神经元数目与编码的神经元数目相等
        dec_hidden = enc_hidden
        # 根据标签对数据解码
        for t in range(tgt_length - 1):
            # 更新新的维度，新增1维
            dec_input = tf.expand_dims(tgt[:, t], 1)
            # 解码
            predictions, dec_hidden, dec_out = decoder(dec_input, dec_hidden, enc_output)
            # 计算损失值
            loss += loss_function(loss_object, tgt[:, t + 1], predictions)
    # 计算一次训练的平均损失值
    batch_loss = loss / tgt_length
    # 更新预测值
    variables = encoder.trainable_variables + decoder.trainable_variables
    # 反向求导
    gradients = tape.gradient(loss, variables)
    # 利用优化器更新权重
    optimizer.apply_gradients(zip(gradients, variables))
    return batch_loss  # 返回每次迭代训练的损失值


print(f'[{datetime.datetime.now()}] 开始训练模型...')

# 尝试加载最新的检查点
latest_checkpoint = tf.train.latest_checkpoint(checkpoint_path)
start_epoch = 0
if latest_checkpoint:
    checkpoint.restore(latest_checkpoint)
    # 从检查点文件名中提取epoch数
    checkpoint_name = os.path.basename(latest_checkpoint)
    if checkpoint_name.startswith('ckpt-'):
        try:
            start_epoch = int(checkpoint_name.split('-')[1]) + 1
            print(f"从epoch {start_epoch} 继续训练")
        except:
            print("无法从检查点文件名解析epoch数，从头开始训练")


# 清理旧的检查点文件
def cleanup_old_checkpoints():
    try:
        checkpoints = [f for f in os.listdir(checkpoint_path) if f.startswith('ckpt-')]
        if len(checkpoints) > 2:  # 只保留最新的两个检查点
            checkpoints.sort(key=lambda x: os.path.getmtime(os.path.join(checkpoint_path, x)), reverse=True)
            for old_checkpoint in checkpoints[2:]:
                old_path = os.path.join(checkpoint_path, old_checkpoint)
                try:
                    os.remove(old_path)
                    print(f"已删除旧检查点: {old_checkpoint}")
                except Exception as e:
                    print(f"删除旧检查点失败 {old_checkpoint}: {str(e)}")
    except Exception as e:
        print(f"清理旧检查点失败: {str(e)}")


# 根据设定的训练次数去训练模型
for ep in range(start_epoch, epoch):
    # 设置损失值
    total_loss = 0
    # 将每批次的数据取出，放入模型里
    try:
        for batch, (src, tgt) in enumerate(train_dataset):
            # 训练并计算损失值
            batch_loss = train_step(src, tgt)
            total_loss += batch_loss

            # 每500个batch保存一次检查点
            if batch % 100 == 0:
                try:
                    if ensure_model_dir():
                        checkpoint_prefix = os.path.join(checkpoint_path, f'ckpt-{ep}')
                        save_path = checkpoint.save(file_prefix=checkpoint_prefix)
                        print(f"中间检查点已保存至: {save_path}")
                        cleanup_old_checkpoints()  # 保存后清理旧检查点
                except Exception as e:
                    print(f"警告: 中间检查点保存失败 at epoch {ep}, batch {batch}: {str(e)}")

        # 每个epoch结束后保存检查点
        try:
            if ensure_model_dir():
                checkpoint_prefix = os.path.join(checkpoint_path, f'ckpt-{ep}')
                save_path = checkpoint.save(file_prefix=checkpoint_prefix)
                print(f"模型已保存至: {save_path}")
                cleanup_old_checkpoints()  # 保存后清理旧检查点
            else:
                print(f"警告: 无法确保模型保存目录存在，跳过保存")
        except Exception as e:
            print(f"警告: 模型保存失败 at epoch {ep}: {str(e)}")

        print(f'[{datetime.datetime.now()}] 迭代次数: {ep + 1} 损失值: {total_loss / (batch + 1):.4f}')

    except Exception as e:
        print(f"训练过程中出错 at epoch {ep}: {str(e)}")
        # 保存当前状态
        try:
            if ensure_model_dir():
                checkpoint_prefix = os.path.join(checkpoint_path, f'ckpt-{ep}')
                save_path = checkpoint.save(file_prefix=checkpoint_prefix)
                print(f"错误发生时的检查点已保存至: {save_path}")
                cleanup_old_checkpoints()  # 保存后清理旧检查点
        except Exception as save_error:
            print(f"警告: 错误发生时的检查点保存失败: {str(save_error)}")
        # 可以选择继续训练或终止
        # break


# 模型预测
def predict(sentence='你好'):
    """使用训练好的模型进行预测"""
    # 导入训练参数
    latest_checkpoint = tf.train.latest_checkpoint(checkpoint_path)
    if not latest_checkpoint:
        print(f"警告: 未找到检查点，使用未训练的模型")
    else:
        checkpoint.restore(latest_checkpoint)
        print(f"已加载检查点: {latest_checkpoint}")

    # 给句子添加开始和结束标记
    sentence = '_BOS' + sentence + '_EOS'

    # 读取字典
    dict_path = os.path.join(tmp_path, 'all_dict.txt')
    if not os.path.exists(dict_path):
        raise FileNotFoundError(f"词典文件不存在: {dict_path}")

    with open(dict_path, 'r', encoding='utf-8') as f:
        all_dict = f.read().split()

    # 构建id -->词的映射字典
    word2id = {j: i + len(CONST) for i, j in enumerate(all_dict)}
    word2id.update(CONST)
    id2word = dict(zip(word2id.values(), word2id.keys()))

    # 分词时保留_EOS和_BOS
    for i in ['_EOS', '_BOS']:
        jieba.add_word(i)

    # 添加识别不到的词，用_UNK表示
    inputs = [word2id.get(i, CONST['_UNK']) for i in jieba.lcut(sentence)]

    # 长度填充
    inputs = tf.keras.preprocessing.sequence.pad_sequences(
        [inputs], maxlen=MAX_LENGTH, padding='post', value=CONST['_PAD']
    )

    # 将数据转为tensorflow的数据类型
    inputs = tf.convert_to_tensor(inputs)

    # 空字符串，用于保留预测结果
    result = ''

    # 编码
    enc_out, enc_hidden = encoder(inputs)
    dec_hidden = enc_hidden
    dec_input = tf.expand_dims([word2id['_BOS']], 0)

    for t in range(MAX_LENGTH):
        # 解码
        predictions, dec_hidden, attention_weights = decoder(dec_input, dec_hidden, enc_out)

        # 预测出词语对应的id
        predicted_id = tf.argmax(predictions[0]).numpy()

        # 通过字典的映射，用id寻找词，遇到EOS停止输出
        if id2word.get(predicted_id, '_UNK') == '_EOS':
            break

        # 未预测出来的词用_UNK替代
        result += id2word.get(predicted_id, '_UNK')
        dec_input = tf.expand_dims([predicted_id], 0)

    return result.replace('_UNK', '^').strip() or '我们来聊聊天吧'


# 测试预测功能
try:
    print('预测示例: \n', predict(sentence='你好，在吗'))
except Exception as e:
    print(f"预测出错: {str(e)}")




