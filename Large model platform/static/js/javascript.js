// 全局变量
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const chatMessages = document.getElementById('chatMessages');
const historyContainer = document.getElementById('historyContainer');
const currentTime = document.getElementById('currentTime');
const voiceBtn = document.getElementById('voiceBtn');
const imageBtn = document.getElementById('imageBtn');
const imageInput = document.getElementById('imageInput');
const imageViewer = document.getElementById('imageViewer');
const viewerImage = document.getElementById('viewerImage');
const closeImageViewer = document.getElementById('closeImageViewer');
const voiceError = document.getElementById('voiceError');
const voiceErrorText = document.getElementById('voiceErrorText');
const imageError = document.getElementById('imageError');
const imageErrorText = document.getElementById('imageErrorText');
const imageLoading = document.getElementById('imageLoading');
const globalVoiceWave = document.getElementById('globalVoiceWave');
const successToast = document.getElementById('successToast');
const toastMessage = document.getElementById('toastMessage');
const deleteConfirmModal = document.getElementById('deleteConfirmModal');
const deleteModalTitle = document.getElementById('deleteModalTitle');
const deleteModalMessage = document.getElementById('deleteModalMessage');
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
const healthChartCtx = document.getElementById('healthChart').getContext('2d');
const avgTemp = document.getElementById('avgTemp');
const latestTemp = document.getElementById('latestTemp');
const mobileSidebarToggle = document.getElementById('mobileSidebarToggle');
const sidebar = document.getElementById('sidebar');
const newChatBtn = document.getElementById('newChatBtn');
const deleteAllHistoryBtn = document.getElementById('deleteAllHistoryBtn');
const switchModelBtn = document.getElementById('switchModelBtn');
const voiceControlBtn = document.getElementById('voice-control-btn') || createVoiceControlBtn();

// 新增语音合成相关变量
const voiceOutput = new Audio(); // 语音播放对象
let isSpeaking = false; // 语音播放状态
let currentVoiceText = ''; // 当前正在播放的文本
let isRecording = false; // 语音输入状态
let recognition; // 语音识别对象
let finalTranscript = ''; // 最终识别文本
let interimTranscript = ''; // 临时识别文本
let recognitionTimeout; // 识别超时计时器

// 语言选项相关变量
const languageSelect = document.getElementById('language-select');
let currentLanguage = 'zh-CN'; // 默认中文

// 创建语音控制按钮
function createVoiceControlBtn() {
    const btn = document.createElement('button');
    btn.id = 'voice-control-btn';
    btn.className = 'voice-control-btn absolute right-3 bottom-3 p-2 rounded-full bg-primary text-white shadow-lg z-50 hidden';
    btn.innerHTML = '<i class="fa fa-volume-up"></i>';
    chatMessages.parentNode.appendChild(btn);
    return btn;
}

let conversations = JSON.parse(localStorage.getItem('medicalChatHistory')) || [];
let currentConversationId = null;
let healthChart;

// 辅助函数：更新当前时间
function updateCurrentTime() {
    const now = new Date();
    currentTime.textContent = now.toLocaleTimeString();
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

// 辅助函数：显示图片错误
function showImageError(message) {
    imageErrorText.textContent = message;
    imageError.classList.remove('opacity-0', 'pointer-events-none');
    
    setTimeout(() => {
      imageError.classList.add('opacity-0', 'pointer-events-none');
    }, 3000);
  }

// 辅助函数：处理图片上传
function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // 验证文件类型
    if (!file.type.match('image.*')) {
      showImageError('请选择图片文件');
      return;
    }
    
    // 显示加载状态
    imageLoading.classList.remove('opacity-0', 'pointer-events-none');
    
    // 创建图片预览
    const reader = new FileReader();
    reader.onload = (e) => {
      const imageUrl = e.target.result;
      
      // 添加用户上传的图片消息
      appendMessage(imageUrl, "user");
      
      // 保存对话
      saveCurrentConversation();
      
      // 模拟AI处理图片
      setTimeout(() => {
        appendMessage("我分析了您上传的图片，这看起来像是...", "bot");
        saveCurrentConversation();
        imageLoading.classList.add('opacity-0', 'pointer-events-none');
      }, 2000);
    };
    reader.readAsDataURL(file);
    
    // 清空文件输入
    imageInput.value = '';
  }

// 辅助函数：初始化语音识别
function initSpeechRecognition() {
    // 检查浏览器是否支持语音识别API
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
      
      // 设置语音识别参数
      recognition.continuous = true; // 连续识别
      recognition.interimResults = true; // 返回临时结果
      recognition.lang = currentLanguage; // 设置识别语言
      
      // 语音识别开始事件
      recognition.onstart = function() {
        isRecording = true;
        showVoiceIndicators();
        voiceBtn.classList.remove('bg-gray-100', 'text-gray-600');
        voiceBtn.classList.add('bg-voice', 'text-white');
        voiceBtn.innerHTML = '<i class="fa fa-stop"></i>';
      };
      
      // 语音识别结束事件
      recognition.onend = function() {
        isRecording = false;
        hideVoiceIndicators();
        voiceBtn.classList.remove('bg-voice', 'text-white');
        voiceBtn.classList.add('bg-gray-100', 'text-gray-600');
        voiceBtn.innerHTML = '<i class="fa fa-microphone"></i>';
        
        // 如果有最终识别结果，将其添加到输入框
        if (finalTranscript) {
          userInput.value = finalTranscript;
          finalTranscript = '';
        }
      };
      
      // 识别到语音输入事件（包括临时结果）
      recognition.onresult = function(event) {
        interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          
          // 区分临时结果和最终结果
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }
        
        // 更新输入框中的临时内容
        userInput.value = interimTranscript;
      };
      
      // 语音识别错误事件
      recognition.onerror = function(event) {
        isRecording = false;
        hideVoiceIndicators();
        voiceBtn.classList.remove('bg-voice', 'text-white');
        voiceBtn.classList.add('bg-gray-100', 'text-gray-600');
        voiceBtn.innerHTML = '<i class="fa fa-microphone"></i>';
        
        showVoiceError('语音识别出错: ' + getErrorText(event.error));
      };
    } else {
      voiceBtn.disabled = true;
      voiceBtn.title = "您的浏览器不支持语音识别";
      showVoiceError('您的浏览器不支持语音识别功能');
    }
  }

// 辅助函数：开始录音
function startRecording() {
    if (isSpeaking) {
        cancelVoiceOutput();
    }
    
    isRecording = true;
    voiceBtn.classList.remove('bg-gray-100', 'text-gray-600');
    voiceBtn.classList.add('bg-voice', 'text-white');
    voiceBtn.innerHTML = '<i class="fa fa-stop"></i>';
    showVoiceIndicators();
    
    try {
      // 设置当前语言
      recognition.lang = currentLanguage;
      recognition.start();
      
      // 设置超时，无语音输入时自动停止
      recognitionTimeout = setTimeout(() => {
        if (isRecording) {
          toggleVoiceInput();
          showVoiceError('未检测到语音输入，已自动停止');
        }
      }, 15000); // 15秒无输入自动停止
    } catch (error) {
      console.error('启动语音识别失败:', error);
      stopRecording();
      showVoiceError('启动语音识别失败，请检查麦克风权限');
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

// 辅助函数：显示语音错误
function showVoiceError(message) {
    voiceErrorText.textContent = message;
    voiceError.classList.remove('opacity-0', 'pointer-events-none');
    
    setTimeout(() => {
      voiceError.classList.add('opacity-0', 'pointer-events-none');
    }, 3000);
  }

// 辅助函数：显示语音指示器
function showVoiceIndicators() {
    const voiceInputWave = document.getElementById('voice-input-wave');
    voiceInputWave.classList.remove('hidden');
    globalVoiceWave.classList.remove('opacity-0', 'pointer-events-none');
  }

// 辅助函数：隐藏语音指示器
function hideVoiceIndicators() {
    const voiceInputWave = document.getElementById('voice-input-wave');
    voiceInputWave.classList.add('hidden');
    globalVoiceWave.classList.add('opacity-0', 'pointer-events-none');
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

// 健康数据相关函数
function loadTemperatureData() {
    const tempRecords = JSON.parse(localStorage.getItem('healthTempRecords')) || [];
    renderTemperatureList(tempRecords);
    updateHealthChart();
    updateHealthStats();
  }

function renderTemperatureList(records) {
    tempList.innerHTML = '';
    
    if (records.length === 0) {
      const emptyState = document.createElement("div");
      emptyState.className = "p-4 text-center text-gray-500";
      emptyState.innerHTML = '<i class="fa fa-thermometer-empty text-3xl mb-2"></i><p>暂无体温记录</p>';
      tempList.appendChild(emptyState);
      return;
    }
    
    records.forEach((record, index) => {
      const recordItem = document.createElement("div");
      recordItem.className = "temp-record p-3 border-b last:border-b-0 hover:bg-gray-50 transition-colors";
      
      // 日期时间
      const dateTimeDiv = document.createElement("div");
      dateTimeDiv.className = "text-sm text-gray-500";
      dateTimeDiv.textContent = `${record.date} ${record.time}`;
      
      // 温度值
      const tempDiv = document.createElement("div");
      tempDiv.className = "text-xl font-semibold mt-1";
      tempDiv.textContent = `${record.temp}°C`;
      
      // 设置温度颜色
      if (record.temp >= 37.3) {
        tempDiv.classList.add("text-danger");
      } else if (record.temp < 36) {
        tempDiv.classList.add("text-blue-500");
      } else {
        tempDiv.classList.add("text-success");
      }
      
      // 删除按钮
      const deleteBtn = document.createElement("button");
      deleteBtn.className = "delete-temp-btn absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-danger transition-colors";
      deleteBtn.setAttribute("data-id", index);
      deleteBtn.innerHTML = '<i class="fa fa-trash-o"></i>';
      
      // 添加到记录项
      recordItem.appendChild(dateTimeDiv);
      recordItem.appendChild(tempDiv);
      recordItem.appendChild(deleteBtn);
      
      // 添加到列表
      tempList.appendChild(recordItem);
    });
  }

function updateHealthChart() {
    const tempRecords = JSON.parse(localStorage.getItem('healthTempRecords')) || [];
    
    // 按时间排序
    tempRecords.sort((a, b) => a.timestamp - b.timestamp);
    
    // 准备图表数据
    const labels = tempRecords.map(record => {
      const date = new Date(record.timestamp);
      return `${date.getMonth()+1}/${date.getDate()} ${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
    });
    
    const data = tempRecords.map(record => record.temp);
    
    // 更新图表
    healthChart.data.labels = labels;
    healthChart.data.datasets[0].data = data;
    healthChart.update();
  }

function updateHealthStats() {
    const tempRecords = JSON.parse(localStorage.getItem('healthTempRecords')) || [];
    
    if (tempRecords.length === 0) {
      avgTemp.textContent = "暂无数据";
      latestTemp.textContent = "暂无数据";
      return;
    }
    
    // 计算平均体温
    const sum = tempRecords.reduce((acc, record) => acc + record.temp, 0);
    const avgTempValue = (sum / tempRecords.length).toFixed(1);
    
    // 获取最近的体温
    const latestTempValue = tempRecords[0].temp;
    
    // 更新显示
    avgTemp.textContent = `${avgTempValue}°C`;
    latestTemp.textContent = `${latestTempValue}°C`;
  }

function initHealthChart() {
    healthChart = new Chart(healthChartCtx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label: '体温 (°C)',
          data: [],
          borderColor: '#165DFF',
          backgroundColor: 'rgba(22, 93, 255, 0.1)',
          tension: 0.4,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            min: 35,
            max: 38,
            ticks: {
              stepSize: 0.5
            },
            grid: {
              color: 'rgba(0, 0, 0, 0.05)'
            }
          },
          x: {
            grid: {
              display: false
            }
          }
        },
        plugins: {
          legend: {
            display: false
          }
        }
      }
    });
  }

// 语音合成并播放
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
        utterance.onstart = function() {
            console.log('语音播放开始');
        };
        
        // 语音播放结束事件
        utterance.onend = function() {
            isSpeaking = false;
            hideVoiceSpeakingIndicator();
            voiceControlBtn.innerHTML = '<i class="fa fa-volume-up"></i>';
            console.log('语音播放结束');
        };
        
        // 语音播放错误事件
        utterance.onerror = function(event) {
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

// 显示语音播放状态指示
function showVoiceSpeakingIndicator() {
    const voiceSpeakingIndicator = document.getElementById('voice-speaking-indicator');
    if (voiceSpeakingIndicator) {
        voiceSpeakingIndicator.classList.remove('hidden');
    }
}

// 隐藏语音播放状态指示
function hideVoiceSpeakingIndicator() {
    const voiceSpeakingIndicator = document.getElementById('voice-speaking-indicator');
    if (voiceSpeakingIndicator) {
        voiceSpeakingIndicator.classList.add('hidden');
    }
}

// 浏览器不支持语音合成时的备选方案
function simulateVoiceOutput(text) {
    // 这里可以使用预录音频或其他方式模拟语音输出
    // 以下为简单示例：创建临时音频元素并播放
    const textToUrl = `https://api.example.com/tts?text=${encodeURIComponent(text)}&lang=${currentLanguage}`;
    voiceOutput.src = textToUrl;
    voiceOutput.onloadedmetadata = function() {
        voiceOutput.play().catch(error => {
            console.error('音频播放错误:', error);
            isSpeaking = false;
            hideVoiceSpeakingIndicator();
            voiceControlBtn.innerHTML = '<i class="fa fa-volume-up"></i>';
        });
    };
    voiceOutput.onended = function() {
        isSpeaking = false;
        hideVoiceSpeakingIndicator();
        voiceControlBtn.innerHTML = '<i class="fa fa-volume-up"></i>';
    };
}

// 取消当前语音播放
function cancelVoiceOutput() {
    if (isSpeaking) {
        if ('SpeechSynthesis' in window) {
            window.speechSynthesis.cancel();
        } else {
            voiceOutput.pause();
            voiceOutput.src = '';
        }
        isSpeaking = false;
        hideVoiceSpeakingIndicator();
        voiceControlBtn.innerHTML = '<i class="fa fa-volume-up"></i>';
    }
}

// 切换语音输出
function toggleVoiceOutput() {
    if (isSpeaking) {
        cancelVoiceOutput();
    } else if (currentVoiceText) {
        speakText(currentVoiceText);
    }
}

// 切换语言
function changeLanguage(language) {
    currentLanguage = language;
    
    // 更新语音识别语言
    if (recognition) {
        recognition.lang = language;
    }
    
    // 显示语言变更提示
    showToast(`已切换到 ${getLanguageName(language)}`);
}

// 获取语言名称
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

// 辅助函数：切换模型
switchModelBtn.onclick = function() {
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

// 初始化
updateCurrentTime();
setInterval(updateCurrentTime, 1000);
loadHistoryList();
initSpeechRecognition();
initHealthChart();
loadTemperatureData();

// 创建语言选择器（如果不存在）
if (!document.getElementById('language-select')) {
    const languageSelect = document.createElement('select');
    languageSelect.id = 'language-select';
    languageSelect.className = 'language-select absolute right-12 bottom-3 bg-white text-gray-700 border border-gray-300 rounded-md px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 z-50';
    
    // 添加语言选项
    const languages = [
        { code: 'zh-CN', name: '中文（简体）' },
        { code: 'en-US', name: '英语（美国）' },
        { code: 'ja-JP', name: '日语' },
        { code: 'ko-KR', name: '韩语' },
        { code: 'fr-FR', name: '法语' },
        { code: 'de-DE', name: '德语' },
        { code: 'es-ES', name: '西班牙语' }
    ];
    
    languages.forEach(lang => {
        const option = document.createElement('option');
        option.value = lang.code;
        option.textContent = lang.name;
        option.selected = lang.code === currentLanguage;
        languageSelect.appendChild(option);
    });
    
    // 添加到页面
    chatMessages.parentNode.appendChild(languageSelect);
    
    // 添加事件监听
    languageSelect.addEventListener('change', (e) => {
        changeLanguage(e.target.value);
    });
}

// 事件监听
sendBtn.onclick = sendMessage;
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

historyContainer.addEventListener('click', (e) => {
    if (e.target.classList.contains('history-item')) {
        const conversationId = parseInt(e.target.getAttribute('data-id'));
        loadConversation(conversationId);
    } else if (e.target.classList.contains('delete-btn')) {
        const conversationId = parseInt(e.target.getAttribute('data-id'));
        deleteModalTitle.textContent = "确认删除";
        deleteModalMessage.textContent = "您确定要删除这条对话记录吗？此操作不可恢复。";
        deleteConfirmModal.classList.remove('opacity-0', 'pointer-events-none');

        confirmDeleteBtn.onclick = function() {
            conversations.splice(conversationId, 1);
            localStorage.setItem('medicalChatHistory', JSON.stringify(conversations));
            loadHistoryList();
            if (currentConversationId === conversationId) {
                chatMessages.innerHTML = '';
                appendMessage("您好！我是智慧医疗助手，可以为您解答一般的健康问题。请注意，我不能替代专业医生的诊断。请问您有什么健康方面的疑问？", "bot");
                currentConversationId = null;
                saveCurrentConversation();
            }
            deleteConfirmModal.classList.add('opacity-0', 'pointer-events-none');
            showToast('对话记录已删除');
        };
    }
});

deleteAllHistoryBtn.onclick = function() {
    deleteModalTitle.textContent = "确认删除所有对话";
    deleteModalMessage.textContent = "您确定要删除所有对话记录吗？此操作不可恢复。";
    deleteConfirmModal.classList.remove('opacity-0', 'pointer-events-none');

    confirmDeleteBtn.onclick = function() {
        deleteAllConversations();
        deleteConfirmModal.classList.add('opacity-0', 'pointer-events-none');
    };
};

cancelDeleteBtn.onclick = function() {
    deleteConfirmModal.classList.add('opacity-0', 'pointer-events-none');
};

voiceBtn.onclick = toggleVoiceInput;
imageBtn.onclick = () => imageInput.click();
imageInput.onchange = handleImageUpload;

closeImageViewer.onclick = () => {
    imageViewer.classList.add('opacity-0', 'pointer-events-none');
};

healthRecordBtn.onclick = () => {
    healthRecordModal.classList.remove('opacity-0', 'pointer-events-none');
};

closeHealthModal.onclick = () => {
    healthRecordModal.classList.add('opacity-0', 'pointer-events-none');
};

healthRecordTab.onclick = () => {
    healthRecordTab.classList.add('text-primary', 'border-primary');
    healthChartTab.classList.remove('text-primary', 'border-primary');
    healthRecordContent.classList.remove('hidden');
    healthChartContent.classList.add('hidden');
};

healthChartTab.onclick = () => {
    healthRecordTab.classList.remove('text-primary', 'border-primary');
    healthChartTab.classList.add('text-primary', 'border-primary');
    healthRecordContent.classList.add('hidden');
    healthChartContent.classList.remove('hidden');
};

addTempBtn.onclick = () => {
    const temp = parseFloat(tempInput.value);
    const date = tempDate.value;
    const time = tempTime.value;

    if (isNaN(temp) || !date || !time) {
        showToast('请填写完整的体温记录信息');
        return;
    }

    const timestamp = new Date(`${date} ${time}`).getTime();
    const tempRecords = JSON.parse(localStorage.getItem('healthTempRecords')) || [];
    tempRecords.unshift({ temp, date, time, timestamp });
    localStorage.setItem('healthTempRecords', JSON.stringify(tempRecords));

    loadTemperatureData();
    tempInput.value = '';
    tempDate.value = '';
    tempTime.value = '';
    showToast('体温记录已添加');
};

tempList.addEventListener('click', (e) => {
    if (e.target.classList.contains('delete-temp-btn')) {
        const index = parseInt(e.target.getAttribute('data-id'));
        const tempRecords = JSON.parse(localStorage.getItem('healthTempRecords')) || [];
        tempRecords.splice(index, 1);
        localStorage.setItem('healthTempRecords', JSON.stringify(tempRecords));
        loadTemperatureData();
        showToast('体温记录已删除');
    }
});

clearTempDataBtn.onclick = () => {
    localStorage.removeItem('healthTempRecords');
    loadTemperatureData();
    showToast('所有体温记录已清除');
};

saveTempDataBtn.onclick = () => {
    const tempRecords = JSON.parse(localStorage.getItem('healthTempRecords')) || [];
    const csvContent = "体温 (°C),日期,时间\n" + tempRecords.map(record => `${record.temp},${record.date},${record.time}`).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'health_temp_records.csv';
    a.click();
    URL.revokeObjectURL(url);
    showToast('体温记录已保存为CSV文件');
};

    mobileSidebarToggle.onclick = () => {
        sidebar.classList.toggle('-translate-x-full');
    };
    
    newChatBtn.onclick = () => {
        chatMessages.innerHTML = '';
        appendMessage("您好！我是智慧医疗助手，可以为您解答一般的健康问题。请注意，我不能替代专业医生的诊断。请问您有什么健康方面的疑问？", "bot");
        currentConversationId = null;
        saveCurrentConversation();
        sidebar.classList.add('-translate-x-full');
    };
    
    // 语音控制按钮事件
    voiceControlBtn.addEventListener('click', toggleVoiceOutput);
    
    // 移动端适配 - 输入框高度调整
    userInput.addEventListener('input', function() {
        this.style.height = '48px';
        this.style.height = (this.scrollHeight > 48 ? Math.min(this.scrollHeight, 150) : 48) + 'px';
    });
    
    // 症状快速选择按钮
    const symptomBtns = document.querySelectorAll('.symptom-btn');
    symptomBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // 清除其他按钮的选中状态
            symptomBtns.forEach(b => b.classList.remove('bg-primary/10', 'text-primary'));
            
            // 设置当前按钮为选中状态
            this.classList.add('bg-primary/10', 'text-primary');
            
            // 将症状文本添加到输入框
            userInput.value = this.textContent;
        });
    });
    
    // 窗口大小变化时处理移动端布局
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 768) {
            sidebar.classList.remove('-translate-x-full');
        }
    });
    
    // 初始化页面加载时的移动端布局
    if (window.innerWidth < 768) {
        sidebar.classList.add('-translate-x-full');
    }
    
    // 欢迎消息
    if (conversations.length === 0) {
        appendMessage("您好！我是智慧医疗助手，可以为您解答一般的健康问题。请注意，我不能替代专业医生的诊断。请问您有什么健康方面的疑问？", "bot");
        saveCurrentConversation();
    }
    
    // 键盘快捷键
    document.addEventListener('keydown', function(e) {
        // Ctrl+Enter 发送消息
        if (e.ctrlKey && e.key === 'Enter') {
            sendMessage();
        }
        
        // Alt+V 切换语音输入
        if (e.altKey && e.key.toLowerCase() === 'v') {
            toggleVoiceInput();
        }
        
        // Alt+L 打开语言选择
        if (e.altKey && e.key.toLowerCase() === 'l') {
            document.getElementById('language-select').focus();
        }
    });
    
    // 初始设置当前日期和时间
    const now = new Date();
    tempDate.value = now.toISOString().split('T')[0];
    tempTime.value = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', initApp);