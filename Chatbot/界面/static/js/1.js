// 修改原有的文件上传处理
chatActionButtons['attach-file'].addEventListener('click', function() {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/*,.pdf,.doc,.docx,.xml'; // 医疗常见格式
    fileInput.multiple = true;
    
    fileInput.onchange = async function(e) {
        const files = Array.from(e.target.files);
        if (files.length > 0) {
            addMessage(`已上传 ${files.length} 个医疗文件`, 'user');
            
            // 显示上传进度
            const progressMsg = document.createElement('div');
            progressMsg.className = 'message bot-message';
            progressMsg.innerHTML = `正在处理医疗文件...<div class="message-time">${getCurrentTime()}</div>`;
            chatHistory.appendChild(progressMsg);
            
            try {
                // 实际应用中这里上传文件到服务器
                // const results = await uploadMedicalFiles(files);
                
                // 模拟处理结果
                setTimeout(() => {
                    progressMsg.innerHTML = `已分析上传的医疗文件。<div class="message-time">${getCurrentTime()}</div>`;
                    
                    // 添加分析结果卡片
                    const analysisCard = document.createElement('div');
                    analysisCard.className = 'medical-card';
                    analysisCard.innerHTML = `
                        <div class="card-title">医疗记录摘要</div>
                        <ul class="suggestion-list">
                            <li class="suggestion-item">
                                <i class="fas fa-file-medical suggestion-icon"></i>
                                <span>发现3次就诊记录</span>
                            </li>
                            <li class="suggestion-item">
                                <i class="fas fa-prescription-bottle-alt suggestion-icon"></i>
                                <span>当前用药: 阿司匹林(100mg/天)</span>
                            </li>
                            <li class="suggestion-item">
                                <i class="fas fa-allergies suggestion-icon"></i>
                                <span>过敏史: 青霉素过敏</span>
                            </li>
                        </ul>
                    `;
                    
                    chatHistory.appendChild(analysisCard);
                    chatHistory.scrollTop = chatHistory.scrollHeight;
                }, 3000);
            } catch (error) {
                progressMsg.innerHTML = `文件处理失败: ${error.message}<div class="message-time">${getCurrentTime()}</div>`;
            }
        }
    };
    
    fileInput.click();
});