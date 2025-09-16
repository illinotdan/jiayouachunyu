// 学习中心页面 - 纯API版本，无模拟数据

let currentTab = 'all';
let currentCategory = 'all';

document.addEventListener('DOMContentLoaded', function() {
    initLearningPage();
});

function initLearningPage() {
    // 初始化标签页
    initTabs();
    
    // 加载学习内容
    loadLearningContent();
}

function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tab = this.dataset.tab;
            switchTab(tab);
        });
    });
}

function switchTab(tab) {
    currentTab = tab;
    
    // 更新标签按钮状态
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active', 'border-dota-accent', 'text-dota-accent');
        btn.classList.add('text-gray-400');
    });
    
    const activeButton = document.querySelector(`[data-tab="${tab}"]`);
    if (activeButton) {
        activeButton.classList.remove('text-gray-400');
        activeButton.classList.add('active', 'border-dota-accent', 'text-dota-accent');
    }
    
    // 重新加载内容
    loadLearningContent();
}

function filterContent(category) {
    currentCategory = category;
    loadLearningContent();
}

async function loadLearningContent() {
    try {
        const container = document.getElementById('learning-content');
        const loading = document.getElementById('learning-loading');
        
        // 显示加载状态
        if (loading) loading.style.display = 'block';
        
        // 构建API请求参数
        const filters = {
            page: 1,
            page_size: 20
        };
        
        if (currentTab !== 'all') {
            filters.type = currentTab;
        }
        
        if (currentCategory !== 'all') {
            filters.category = currentCategory;
        }
        
        // 调用真实API
        const response = await apiCall(api.getLearningContent, filters);
        
        DataAdapter.validateApiResponse(response, ['content']);
        
        const learningContent = response.data.content || [];
        
        renderLearningContent(learningContent);
        
    } catch (error) {
        console.error('加载学习内容失败:', error);
        showLearningError(error.message);
    } finally {
        // 隐藏加载状态
        const loading = document.getElementById('learning-loading');
        if (loading) loading.style.display = 'none';
    }
}

function renderLearningContent(content) {
    const container = document.getElementById('learning-content');
    
    if (!content || content.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-12">
                <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                </svg>
                <p class="text-gray-400 text-lg mb-2">暂无学习内容</p>
                <p class="text-gray-500 text-sm">内容正在建设中，敬请期待</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = content.map(item => {
        const timeAgo = getTimeAgo(item.createdAt);
        const difficultyColor = getDifficultyColor(item.difficulty);
        
        return `
            <div class="match-card rounded-lg p-6 cursor-pointer" onclick="viewLearningContent(${item.id})">
                <!-- 内容类型和难度标签 -->
                <div class="flex justify-between items-center mb-3">
                    <div class="flex items-center space-x-2">
                        <span class="tag ${getTypeColor(item.type)}">
                            ${getTypeName(item.type)}
                        </span>
                        ${item.isVerified ? '<span class="tag bg-green-600/20 text-green-400 border-green-600/30">✓ 认证</span>' : ''}
                    </div>
                    <span class="text-xs px-2 py-1 rounded ${difficultyColor}">
                        ${item.difficulty}
                    </span>
                </div>
                
                <!-- 标题和描述 -->
                <h3 class="text-lg font-semibold text-white mb-2 hover:text-dota-accent transition-colors line-clamp-2">
                    ${item.title}
                </h3>
                <p class="text-gray-400 text-sm mb-4 line-clamp-2">
                    ${item.description || ''}
                </p>
                
                <!-- 标签 -->
                <div class="flex flex-wrap gap-1 mb-4">
                    ${(item.tags || []).slice(0, 3).map(tag => `
                        <span class="text-xs bg-dota-panel/50 text-gray-400 px-2 py-1 rounded border border-dota-border">
                            #${tag}
                        </span>
                    `).join('')}
                </div>
                
                <!-- 作者和统计 -->
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2">
                        <div class="w-8 h-8 bg-gradient-to-r from-radiant-500 to-radiant-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
                            ${(item.author || 'A').charAt(0)}
                        </div>
                        <div>
                            <div class="text-sm font-medium text-white">${item.author || '匿名作者'}</div>
                            <div class="text-xs text-gray-400">${timeAgo}</div>
                        </div>
                    </div>
                    
                    <div class="flex items-center space-x-3 text-xs text-gray-400">
                        <span class="flex items-center space-x-1">
                            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                            </svg>
                            <span>${formatNumber(item.viewCount || 0)}</span>
                        </span>
                        <span class="flex items-center space-x-1">
                            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
                            </svg>
                            <span>${item.commentCount || 0}</span>
                        </span>
                        <span class="flex items-center space-x-1">
                            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                            </svg>
                            <span>${item.likeCount || 0}</span>
                        </span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function showLearningError(message) {
    const container = document.getElementById('learning-content');
    container.innerHTML = `
        <div class="col-span-full text-center py-12">
            <svg class="w-16 h-16 text-dire-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
            </svg>
            <p class="text-dire-500 text-lg">${message}</p>
            <p class="text-gray-400 text-sm mb-4">请确保后端服务已启动</p>
            <button onclick="loadLearningContent()" class="mt-4 bg-dota-accent hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors">
                重新加载
            </button>
        </div>
    `;
}

function getTypeName(type) {
    // TODO: 从API获取真实分类配置
    const typeNames = {
        guide: '攻略教学', // TODO: 从API获取真实分类名称
        analysis: '技术分析', // TODO: 从API获取真实分类名称
        tips: '实用技巧', // TODO: 从API获取真实分类名称
        qa: '问答互助' // TODO: 从API获取真实分类名称
    };
    return typeNames[type] || '其他';
}

function getTypeColor(type) {
    const typeColors = {
        guide: 'bg-radiant-600/20 text-radiant-400 border-radiant-600/30',
        analysis: 'bg-ancient-600/20 text-ancient-400 border-ancient-600/30',
        tips: 'bg-dota-accent/20 text-dota-accent border-dota-accent/30',
        qa: 'bg-dire-600/20 text-dire-400 border-dire-600/30'
    };
    return typeColors[type] || 'bg-gray-600/20 text-gray-400 border-gray-600/30';
}

function getDifficultyColor(difficulty) {
    const colors = {
        'beginner': 'bg-green-600/20 text-green-400',
        'intermediate': 'bg-yellow-600/20 text-yellow-400',
        'advanced': 'bg-orange-600/20 text-orange-400',
        'expert': 'bg-red-600/20 text-red-400'
    };
    return colors[difficulty] || 'bg-gray-600/20 text-gray-400';
}

function viewLearningContent(contentId) {
    window.location.href = `learning-detail.html?id=${contentId}`;
}
