// 专家页面专用JavaScript

let allExperts = [];
let filteredExperts = [];

document.addEventListener('DOMContentLoaded', function() {
    initExpertsPage();
});

function initExpertsPage() {
    // 初始化筛选器
    initFilters();
    
    // 加载专家数据
    loadAllExperts();
}

function initFilters() {
    const searchInput = document.getElementById('expert-search');
    const tierFilter = document.getElementById('tier-filter');
    const expertiseFilter = document.getElementById('expertise-filter');
    
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                filterExperts();
            }, 300);
        });
    }
    
    if (tierFilter) {
        tierFilter.addEventListener('change', filterExperts);
    }
    
    if (expertiseFilter) {
        expertiseFilter.addEventListener('change', filterExperts);
    }
}

async function loadAllExperts() {
    try {
        // 显示加载状态
        const loading = document.getElementById('experts-loading');
        if (loading) loading.style.display = 'block';
        
        // 调用真实API
        const response = await apiCall(api.getExperts, {
            page: 1,
            page_size: 24
        });
        
        DataAdapter.validateApiResponse(response, ['experts']);
        
        allExperts = response.data.experts || [];
        
        filterExperts();
        
    } catch (error) {
        console.error('加载专家数据失败:', error);
        document.getElementById('experts-grid').innerHTML = `
            <div class="col-span-full text-center py-12">
                <svg class="w-16 h-16 text-dire-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                </svg>
                <p class="text-dire-500 mb-4">无法加载技术分享者数据</p>
                <p class="text-gray-400 text-sm mb-4">请确保后端服务已启动</p>
                <button onclick="loadAllExperts()" class="bg-dota-accent hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors">
                    重新加载
                </button>
            </div>
        `;
    } finally {
        // 隐藏加载状态
        const loading = document.getElementById('experts-loading');
        if (loading) loading.style.display = 'none';
    }
}

// generateMockExperts函数已删除 - 所有数据现在从API获取

function filterExperts() {
    const searchTerm = document.getElementById('expert-search')?.value.toLowerCase() || '';
    const tierFilter = document.getElementById('tier-filter')?.value || '';
    const expertiseFilter = document.getElementById('expertise-filter')?.value || '';
    
    filteredExperts = allExperts.filter(expert => {
        // 搜索筛选
        if (searchTerm && !expert.name.toLowerCase().includes(searchTerm) &&
            !expert.title.toLowerCase().includes(searchTerm) &&
            !expert.bio.toLowerCase().includes(searchTerm)) {
            return false;
        }
        
        // 等级筛选
        if (tierFilter && expert.tier !== tierFilter) return false;
        
        // 专业筛选
        if (expertiseFilter && !expert.specialties.includes(expertiseFilter)) return false;
        
        return true;
    });
    
    renderExperts(filteredExperts);
}

function renderExperts(experts) {
    const container = document.getElementById('experts-grid');
    const loading = document.getElementById('experts-loading');
    
    if (loading) loading.style.display = 'none';
    
    if (experts.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-12">
                <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
                </svg>
                <p class="text-gray-400 text-lg mb-2">没有找到符合条件的专家</p>
                <p class="text-gray-500 text-sm">尝试调整筛选条件或搜索关键词</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = experts.map(expert => {
        const tierInfo = getTierInfo(expert.tier);
        const formattedFollowers = formatNumber(expert.followers);
        
        return `
            <div class="match-card rounded-lg p-6 cursor-pointer" onclick="viewExpert(${expert.id})">
                <!-- 头部区域 -->
                <div class="relative mb-4">
                    ${expert.verified ? `
                        <div class="absolute top-0 right-0">
                            <span class="expert-badge">
                                <svg class="w-3 h-3 inline mr-1" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                                </svg>
                                认证
                            </span>
                        </div>
                    ` : ''}
                    
                    <div class="flex items-center space-x-4">
                        <div class="relative">
                            <div class="w-16 h-16 ${tierInfo.bgColor} rounded-full p-1 shadow-lg">
                                <img src="${expert.avatar}" alt="${expert.name}" class="w-full h-full rounded-full bg-dota-panel object-cover">
                            </div>
                            <div class="absolute -bottom-1 -right-1">
                                <span class="inline-block w-6 h-6 ${tierInfo.bgColor} rounded-full flex items-center justify-center text-white text-xs font-bold">
                                    ${tierInfo.icon}
                                </span>
                            </div>
                        </div>
                        <div class="flex-1 min-w-0">
                            <h3 class="font-semibold text-white truncate">${expert.name}</h3>
                            <p class="text-sm text-gray-400 truncate">${expert.title}</p>
                            <div class="flex items-center space-x-2 mt-1">
                                <span class="text-xs ${tierInfo.textColor} font-medium">${tierInfo.name}</span>
                                <span class="text-xs text-gray-500">•</span>
                                <span class="text-xs text-green-400 font-medium">${expert.accuracy.toFixed(1)}%</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 专业领域 -->
                <div class="mb-4">
                    <div class="flex flex-wrap gap-1">
                        ${expert.expertise.slice(0, 3).map((area, index) => `
                            <span class="tag ${getExpertiseColor(index)}">
                                ${area}
                            </span>
                        `).join('')}
                    </div>
                </div>

                <!-- 统计数据 -->
                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div class="text-center">
                        <div class="text-lg font-semibold text-radiant-500">${formattedFollowers}</div>
                        <div class="text-xs text-gray-400">关注者</div>
                    </div>
                    <div class="text-center">
                        <div class="text-lg font-semibold text-dota-accent">${expert.articles}</div>
                        <div class="text-xs text-gray-400">文章数</div>
                    </div>
                </div>

                <!-- 简介 -->
                <div class="text-sm text-gray-400 mb-4 line-clamp-2">
                    ${expert.bio}
                </div>

                <!-- 操作按钮 -->
                <div class="flex space-x-2">
                    <button class="flex-1 bg-dota-accent/20 hover:bg-dota-accent text-dota-accent hover:text-white border border-dota-accent/30 hover:border-dota-accent py-2 px-3 rounded-lg text-sm font-medium transition-all duration-300">
                        查看主页
                    </button>
                    <button class="px-3 py-2 bg-radiant-600/20 hover:bg-radiant-600 text-radiant-500 hover:text-white border border-radiant-600/30 hover:border-radiant-600 rounded-lg text-sm transition-all duration-300">
                        关注
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function getTierInfo(tier) {
    // TODO: 从API获取真实专家等级配置
    const tierMap = {
        diamond: {
            name: '钻石专家', // TODO: 从API获取真实等级名称
            icon: '💎', // TODO: 从API获取真实图标
            bgColor: 'bg-gradient-to-r from-purple-500 to-purple-600',
            textColor: 'text-purple-400'
        },
        platinum: {
            name: '铂金专家', // TODO: 从API获取真实等级名称
            icon: '🏆', // TODO: 从API获取真实图标
            bgColor: 'bg-gradient-to-r from-cyan-500 to-cyan-600',
            textColor: 'text-cyan-400'
        },
        gold: {
            name: '黄金专家', // TODO: 从API获取真实等级名称
            icon: '🥇', // TODO: 从API获取真实图标
            bgColor: 'bg-gradient-to-r from-yellow-500 to-yellow-600',
            textColor: 'text-yellow-400'
        },
        silver: {
            name: '白银专家', // TODO: 从API获取真实等级名称
            icon: '🥈', // TODO: 从API获取真实图标
            bgColor: 'bg-gradient-to-r from-gray-400 to-gray-500',
            textColor: 'text-gray-400'
        }
    };
    
    return tierMap[tier] || tierMap.silver;
}

function getExpertiseColor(index) {
    const colors = [
        'bg-radiant-600/20 text-radiant-400 border-radiant-600/30',
        'bg-dota-accent/20 text-dota-accent border-dota-accent/30',
        'bg-ancient-600/20 text-ancient-400 border-ancient-600/30'
    ];
    return colors[index % colors.length];
}

function viewExpert(expertId) {
    // 跳转到专家详情页
    window.location.href = `expert.html?id=${expertId}`;
}

function followExpert(expertId) {
    // 关注专家逻辑
    const expert = allExperts.find(e => e.id === expertId);
    if (expert) {
        showNotification(`已关注 ${expert.name}`, 'success');
    }
}
