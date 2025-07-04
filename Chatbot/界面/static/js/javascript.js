// 全局变量
let conversations = JSON.parse(localStorage.getItem('medicalChatHistory')) || [];
let currentConversationId = null;
let isRecording = false;
let recognition;
let finalTranscript = '';
let recognitionTimeout;
let isSpeaking = false;
let currentVoiceText = '';
let currentLanguage = 'zh-CN';

// 获取 DOM 元素
const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const voiceBtn = document.getElementById('voiceBtn');
const voiceInputWave = document.getElementById('voice-input-wave');
const historyContainer = document.getElementById('historyContainer');
const deleteAllHistoryBtn = document.getElementById('deleteAllHistoryBtn');
const deleteConfirmModal = document.getElementById('deleteConfirmModal');
const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
const healthRecordBtn = document.getElementById('healthRecordBtn');
const healthRecordModal = document.getElementById('healthRecordModal');
const closeHealthModal = document.getElementById('closeHealthModal');
const healthRecordTab = document.getElementById('healthRecordTab');
const healthChartTab = document.getElementById('healthChartTab');
const healthRecordContent = document.getElementById('healthRecordContent');
const healthChartContent = document.getElementById('healthChartContent');
const tempInput = document.getElementById('tempInput');
const tempDate = document.getElementById('tempDate');
const tempTime = document.getElementById('tempTime');
const addTempBtn = document.getElementById('addTempBtn');
const tempList = document.getElementById('tempList');
const clearTempDataBtn = document.getElementById('clearTempDataBtn');
const saveTempDataBtn = document.getElementById('saveTempDataBtn');
const healthChart = document.getElementById('healthChart');
const avgTemp = document.getElementById('avgTemp');
const mobileSidebarToggle = document.getElementById('mobileSidebarToggle');
const sidebar = document.getElementById('sidebar');
const voiceError = document.getElementById('voiceError');
const voiceErrorText = document.getElementById('voiceErrorText');
const imageError = document.getElementById('imageError');
const imageErrorText = document.getElementById('imageErrorText');
const imageLoading = document.getElementById('imageLoading');
const successToast = document.getElementById('successToast');
const toastMessage = document.getElementById('toastMessage');
const voiceControlBtn = createVoiceControlBtn();
const imageBtn = document.getElementById('imageBtn');
const imageInput = document.getElementById('imageInput');
const currentTime = document.getElementById('currentTime');
const switchModelBtn = document.getElementById('switchModelBtn');

// 辅助函数：更新当前时间
function updateCurrentTime() {
    const now = new Date();
    currentTime.textContent = now.toLocaleTimeString();
}

// 辅助函数：创建语音控制按钮
function createVoiceControlBtn() {
    const btn = document.createElement('button');
    btn.id = 'voice-control-btn';
    btn.className = 'voice-control-btn absolute right-3 bottom-3 p-2 rounded-full bg-primary text-white shadow-lg z-50 hidden';
    btn.innerHTML = '<i class="fa fa-volume-up"></i>';
    chatMessages.parentNode.appendChild(btn);
    return btn;
}

// 辅助函数：添加消息到聊天窗口
function appendMessage(content, sender) {
    // 创建消息元素
    const messageDiv = document.createElement("div");
    messageDiv.className = `flex ${sender === "user" ? "justify-end" : "justify-start"} mb-4`;

    // 创建头像容器
    const avatarDiv = document.createElement("div");
    avatarDiv.className = "avatar-circle mr-2";
    avatarDiv.style.backgroundColor = sender === "user" ? "#165DFF" : "#FF7D00";

    // 创建头像图标
    const avatarIcon = document.createElement("i");
    avatarIcon.className = `avatar-icon fa ${sender === "user" ? "fa-user" : "fa-robot"}`;

    // 将头像图标添加到头像容器
    avatarDiv.appendChild(avatarIcon);

    // 创建消息内容容器
    const contentDiv = document.createElement("div");
    contentDiv.className = `message-content max-w-[80%] p-3 rounded-lg shadow-sm ${sender === "user" ? "bg-primary text-white" : "bg-white text-gray-800"}`;

    // 检查内容是否是图片URL
    if (content.startsWith("data:image/") || /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(content)) {
        const img = document.createElement("img");
        img.src = content;
        img.alt = "上传的图片";
        img.className = "message-image max-w-full h-auto rounded-lg";
        contentDiv.appendChild(img);
    } else {
        // 普通文本消息
        contentDiv.textContent = content;
    }

    // 将头像和内容添加到消息容器
    if (sender === "user") {
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(avatarDiv);
    } else {
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
    }

    // 添加到聊天窗口
    chatMessages.appendChild(messageDiv);

    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // 如果是机器人消息且未在播放中，显示语音控制按钮
    if (sender === "bot" && !isSpeaking) {
        voiceControlBtn.classList.remove('hidden');
    }
}

// 辅助函数：发送消息
function sendMessage() {
    const message = userInput.value.trim();
    if (message === '') return;

    // 重置输入框
    userInput.value = '';
    userInput.style.height = '48px';

    // 清除症状按钮的选中状态
    const symptomBtns = document.querySelectorAll('.symptom-btn');
    symptomBtns.forEach(b => b.classList.remove('bg-primary/10', 'text-primary'));

    // 添加用户消息
    appendMessage(message, "user");

    // 保存对话
    saveCurrentConversation();

    // 发送请求到后端获取AI回复
    fetch('/api/ask', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ question: message, language: currentLanguage })
    })
      .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
      .then(data => {
            console.log('Received data:', data);
            if (data.answer) {
                appendMessage(data.answer, "bot");
                saveCurrentConversation();

                // 添加语音合成
                speakText(data.answer);
            } else {
                showToast('获取回答失败');
            }
        })
      .catch(error => {
            console.error('Fetch error:', error);
            showToast('请求出错，请稍后再试');
        });
}

// 辅助函数：保存当前对话
function saveCurrentConversation() {
    const messages = Array.from(chatMessages.children).map((messageDiv) => {
        const sender = messageDiv.classList.contains('justify-end') ? 'user' : 'bot';
        const content = messageDiv.querySelector('.message-content').textContent;
        return { sender, content };
    });

    if (currentConversationId === null) {
        const newConversation = {
            title: `对话 ${conversations.length + 1}`,
            time: new Date().toLocaleString(),
            messages
        };
        conversations.push(newConversation);
        currentConversationId = conversations.length - 1;
    } else {
        conversations[currentConversationId].messages = messages;
        conversations[currentConversationId].time = new Date().toLocaleString();
    }

    localStorage.setItem('medicalChatHistory', JSON.stringify(conversations));
    loadHistoryList();
}

// 辅助函数：加载历史对话列表
function loadHistoryList() {
    // 清空历史容器
    historyContainer.innerHTML = '';

    // 如果没有对话，显示提示
    if (conversations.length === 0) {
        const emptyState = document.createElement("div");
        emptyState.className = "p-4 text-center text-gray-500";
        emptyState.innerHTML = '<i class="fa fa-comments-o text-3xl mb-2"></i><p>暂无对话记录</p>';
        historyContainer.appendChild(emptyState);
        return;
    }

    // 显示对话列表
    conversations.forEach((conversation, index) => {
        const historyItem = document.createElement("div");
        historyItem.className = `history-item p-3 rounded-lg cursor-pointer hover:bg-gray-50 transition-colors ${index === currentConversationId ? 'active' : ''}`;
        historyItem.setAttribute('data-id', index);

        // 对话标题
        const titleDiv = document.createElement("div");
        titleDiv.className = "font-medium text-sm";
        titleDiv.textContent = conversation.title;

        // 对话时间
        const timeDiv = document.createElement("div");
        timeDiv.className = "text-xs text-gray-500 mt-1";
        timeDiv.textContent = conversation.time;

        // 删除按钮
        const deleteBtn = document.createElement("button");
        deleteBtn.className = "delete-btn";
        deleteBtn.setAttribute('data-id', index);
        deleteBtn.innerHTML = '<i class="fa fa-trash-o"></i>';

        // 添加到历史项
        historyItem.appendChild(titleDiv);
        historyItem.appendChild(timeDiv);
        historyItem.appendChild(deleteBtn);

        // 添加到历史容器
        historyContainer.appendChild(historyItem);
    });
}

// 辅助函数：加载指定对话
function loadConversation(conversationId) {
    if (conversationId < 0 || conversationId >= conversations.length) return;

    // 获取对话
    const conversation = conversations[conversationId];

    // 清空当前聊天
    chatMessages.innerHTML = '';

    // 添加对话消息
    conversation.messages.forEach((message) => {
        appendMessage(message.content, message.sender);
    });

    // 更新当前对话ID
    currentConversationId = conversationId;

    // 更新历史列表（高亮当前对话）
    loadHistoryList();

    // 关闭侧边栏（移动端）
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.add('-translate-x-full');
}

// 辅助函数：删除所有对话
function deleteAllConversations() {
    // 清空对话数组
    conversations = [];

    // 更新本地存储
    localStorage.removeItem('medicalChatHistory');

    // 重新加载历史列表
    loadHistoryList();

    // 清空当前聊天
    chatMessages.innerHTML = '';

    // 添加欢迎消息
    appendMessage("您好！我是智慧医疗助手，可以为您解答一般的健康问题。请注意，我不能替代专业医生的诊断。请问您有什么健康方面的疑问？", "bot");

    // 设置当前对话为新对话
    currentConversationId = null;

    // 保存对话
    saveCurrentConversation();

    // 关闭模态框
    deleteConfirmModal.classList.add('opacity-0', 'pointer-events-none');

    // 显示成功提示
    showToast('所有对话记录已删除');
}

// 辅助函数：开始录音
function startRecording() {
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = currentLanguage;

        recognition.onstart = function () {
            isRecording = true;
            voiceBtn.classList.remove('bg-gray-100', 'text-gray-600');
            voiceBtn.classList.add('bg-voice', 'text-white');
            voiceBtn.innerHTML = '<i class="fa fa-stop"></i>';
            showVoiceIndicators();
            recognitionTimeout = setTimeout(() => {
                stopRecording();
            }, 60000); // 录音最长60秒
        };

        recognition.onresult = function (event) {
            finalTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                }
            }
            userInput.value = finalTranscript;
        };

        recognition.onerror = function (event) {
            stopRecording();
            showVoiceError(getErrorText(event.error));
        };

        recognition.onend = function () {
            if (isRecording) {
                stopRecording();
            }
        };

        recognition.start();
    } else {
        showVoiceError('您的浏览器不支持语音输入');
    }
}

// 辅助函数：停止录音
function stopRecording() {
    isRecording = false;
    voiceBtn.classList.remove('bg-voice', 'text-white');
    voiceBtn.classList.add('bg-gray-100', 'text-gray-600');
    voiceBtn.innerHTML = '<i class="fa fa-microphone"></i>';
    hideVoiceIndicators();
    clearTimeout(recognitionTimeout);

    if (recognition) {
        recognition.stop();
    }

    // 处理最终识别结果
    if (finalTranscript) {
        userInput.value = finalTranscript;
        finalTranscript = '';
    }
}

// 辅助函数：显示语音指示器
function showVoiceIndicators() {
    voiceInputWave.classList.remove('hidden');
}

// 辅助函数：隐藏语音指示器
function hideVoiceIndicators() {
    voiceInputWave.classList.add('hidden');
}

// 辅助函数：显示语音错误
function showVoiceError(message) {
    voiceErrorText.textContent = message;
    voiceError.classList.remove('opacity-0', 'pointer-events-none');

    setTimeout(() => {
        voiceError.classList.add('opacity-0', 'pointer-events-none');
    }, 3000);
}

// 辅助函数：获取错误文本
function getErrorText(error) {
    switch (error) {
        case 'no-speech':
            return '没有检测到语音';
        case 'audio-capture':
            return '音频捕获错误';
        case 'not-allowed':
            return '未允许使用麦克风';
        case 'service-error':
            return '服务错误';
        case 'network-error':
            return '网络错误';
        default:
            return '未知错误';
    }
}

// 辅助函数：语音合成并播放
function speakText(text) {
    if (!text || isSpeaking) return;

    currentVoiceText = text;
    isSpeaking = true;
    voiceControlBtn.innerHTML = '<i class="fa fa-pause"></i>';

    // 显示正在说话的状态
    showVoiceSpeakingIndicator();

    // 检查浏览器是否支持语音合成API
    if ('SpeechSynthesis' in window) {
        const synth = window.speechSynthesis;
        const utterance = new SpeechSynthesisUtterance(text);

        // 设置语音参数
        utterance.lang = currentLanguage; // 使用当前选择的语言
        utterance.rate = 1.0; // 语速
        utterance.pitch = 1.0; // 音高

        // 语音开始播放事件
        utterance.onstart = function () {
            console.log('语音播放开始');
        };

        // 语音播放结束事件
        utterance.onend = function () {
            isSpeaking = false;
            hideVoiceSpeakingIndicator();
            voiceControlBtn.innerHTML = '<i class="fa fa-volume-up"></i>';
            console.log('语音播放结束');
        };

        // 语音播放错误事件
        utterance.onerror = function (event) {
            isSpeaking = false;
            hideVoiceSpeakingIndicator();
            voiceControlBtn.innerHTML = '<i class="fa fa-volume-up"></i>';
            console.error('语音播放错误:', event.error);
        };

        // 取消之前的语音播放并开始新的播放
        synth.cancel();
        synth.speak(utterance);
    } else {
        // 浏览器不支持时使用HTML5音频模拟（备选方案）
        simulateVoiceOutput(text);
    }
}

// 辅助函数：显示语音正在说话的指示器
function showVoiceSpeakingIndicator() {
    // 这里可以添加显示指示器的逻辑
}

// 辅助函数：隐藏语音正在说话的指示器
function hideVoiceSpeakingIndicator() {
    // 这里可以添加隐藏指示器的逻辑
}

// 浏览器不支持语音合成时的备选方案
function simulateVoiceOutput(text) {
    // 这里可以使用预录音频或其他方式模拟语音输出
    // 以下为简单示例：创建临时音频元素并播放
    const textToUrl = `https://api.example.com/tts?text=${encodeURIComponent(text)}&lang=${currentLanguage}`;
    const voiceOutput = document.createElement('audio');
    voiceOutput.src = textToUrl;
    voiceOutput.onloadedmetadata = function () {
        voiceOutput.play().catch(error => {
            console.error('音频播放错误:', error);
            isSpeaking = false;
            hideVoiceSpeakingIndicator();
            voiceControlBtn.innerHTML = '<i class="fa fa-volume-up"></i>';
        });
    };
    voiceOutput.onended = function () {
        isSpeaking = false;
        hideVoiceSpeakingIndicator();
        voiceControlBtn.innerHTML = '<i class="fa fa-volume-up"></i>';
    };
}

// 辅助函数：切换语音输出
function toggleVoiceOutput() {
    if (isSpeaking) {
        cancelVoiceOutput();
    } else if (currentVoiceText) {
        speakText(currentVoiceText);
    }
}

// 辅助函数：取消语音输出
function cancelVoiceOutput() {
    if ('SpeechSynthesis' in window) {
        const synth = window.speechSynthesis;
        synth.cancel();
    }
    isSpeaking = false;
    hideVoiceSpeakingIndicator();
    voiceControlBtn.innerHTML = '<i class="fa fa-volume-up"></i>';
}

// 辅助函数：切换语音输入
function toggleVoiceInput() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

// 辅助函数：显示成功提示
function showToast(message) {
    toastMessage.textContent = message;
    successToast.classList.remove('opacity-0');

    setTimeout(() => {
        successToast.classList.add('opacity-0');
    }, 3000);
}

// 辅助函数：显示图片错误
function showImageError(message) {
    imageErrorText.textContent = message;
    imageError.classList.remove('opacity-0', 'pointer-events-none');

    setTimeout(() => {
        imageError.classList.add('opacity-0', 'pointer-events-none');
    }, 3000);
}

// 辅助函数：切换模型
switchModelBtn.onclick = function () {
    // 发送请求到后端切换模型
    fetch('/api/switch_model', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
      .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
      .then(data => {
            if (data.status === 'success') {
                showToast(`已切换到 ${data.model}`);
            } else {
                showToast('切换模型失败');
            }
        })
      .catch(error => {
            console.error('Fetch error:', error);
            showToast('请求出错，请稍后再试');
        });
};

// 辅助函数：切换语言
function changeLanguage(language) {
    currentLanguage = language;

    // 更新语音识别语言
    if (recognition) {
        recognition.lang = language;
    }

    // 显示语言变更提示
    showToast(`已切换到 ${getLanguageName(language)}`);
}

// 辅助函数：获取语言名称
function getLanguageName(languageCode) {
    const languageNames = {
        'zh-CN': '中文（简体）',
        'en-US': '英语（美国）',
        'ja-JP': '日语',
        'ko-KR': '韩语',
        'fr-FR': '法语',
        'de-DE': '德语',
        'es-ES': '西班牙语'
    };

    return languageNames[languageCode] || languageCode;
}

// 图片上传处理
imageBtn.onclick = () => imageInput.click();
imageInput.onchange = async function (e) {
    const file = e.target.files[0];
    if (!file) return;

    // 显示加载状态
    imageLoading.classList.remove('opacity-0', 'pointer-events-none');

    // 创建FormData对象
    const formData = new FormData();
    formData.append('file', file);

    try {
        // 发送请求到后端进行图片分析
        const response = await fetch('/api/analyze_medical_image', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.status === 'success') {
            const analysis = data.analysis;
            appendMessage(`已上传图片，以下是分析结果：
                图片类型: ${analysis.image_type}
                检查结果: ${analysis.findings}
                建议: ${analysis.recommendation}`, "bot");
            appendMessage(analysis.image_data, "bot");
            saveCurrentConversation();
        } else {
            showImageError(`图片分析失败: ${data.error}`);
        }
    } catch (error) {
        console.error('Fetch error:', error);
        showImageError('请求出错，请稍后再试');
    } finally {
        // 隐藏加载状态
        imageLoading.classList.add('opacity-0', 'pointer-events-none');
    }
};

// 初始化
loadHistoryList();
appendMessage("您好！我是智慧医疗助手，可以为您解答一般的健康问题。请注意，我不能替代专业医生的诊断。请问您有什么健康方面的疑问？", "bot");
saveCurrentConversation();
setInterval(updateCurrentTime, 1000);

// 事件监听
sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
voiceBtn.addEventListener('click', toggleVoiceInput);
deleteAllHistoryBtn.addEventListener('click', function () {
    deleteConfirmModal.classList.remove('opacity-0', 'pointer-events-none');
});
cancelDeleteBtn.addEventListener('click', function () {
    deleteConfirmModal.classList.add('opacity-0', 'pointer-events-none');
});
confirmDeleteBtn.addEventListener('click', deleteAllConversations);
healthRecordBtn.addEventListener('click', function () {
    healthRecordModal.classList.remove('opacity-0', 'pointer-events-none');
});
closeHealthModal.addEventListener('click', function () {
    healthRecordModal.classList.add('opacity-0', 'pointer-events-none');
});
healthRecordTab.addEventListener('click', function () {
    healthRecordTab.classList.add('text-primary', 'border-primary');
    healthChartTab.classList.remove('text-primary', 'border-primary');
    healthRecordContent.classList.remove('hidden');
    healthChartContent.classList.add('hidden');
});
healthChartTab.addEventListener('click', function () {
    healthChartTab.classList.add('text-primary', 'border-primary');
    healthRecordTab.classList.remove('text-primary', 'border-primary');
    healthChartContent.classList.remove('hidden');
    healthRecordContent.classList.add('hidden');
});
addTempBtn.addEventListener('click', function () {
    const temp = tempInput.value;
    const date = tempDate.value;
    const time = tempTime.value;

    if (temp && date && time) {
        const record = document.createElement('div');
        record.className = 'temp-record p-3 border-b';
        record.innerHTML = `
            <p class="text-sm text-gray-600">${date} ${time}</p>
            <p class="text-lg font-medium">${temp}°C</p>
        `;
        tempList.appendChild(record);

        tempInput.value = '';
        tempDate.value = '';
        tempTime.value = '';

        showToast('体温记录已添加');
    } else {
        showToast('请填写完整的体温记录信息');
    }
});
clearTempDataBtn.addEventListener('click', function () {
    tempList.innerHTML = '';
    showToast('体温记录已清除');
});
saveTempDataBtn.addEventListener('click', function () {
    showToast('体温数据已保存');
});
mobileSidebarToggle.addEventListener('click', function () {
    sidebar.classList.toggle('-translate-x-full');
});
voiceControlBtn.addEventListener('click', toggleVoiceOutput);