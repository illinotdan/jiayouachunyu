// 比赛页面 - 纯API版本，无模拟数据

let currentPage = 1;
let totalPages = 1;
let allMatches = [];
let filteredMatches = [];
let currentTab = 'all';
let currentFilters = {};

document.addEventListener('DOMContentLoaded', function() {
    initMatchesPage();
});

function initMatchesPage() {
    // 初始化标签页
    initTabs();
    
    // 初始化筛选器
    initFilters();
    
    // 加载比赛数据
    loadAllMatches();
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
    currentPage = 1;
    
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
    
    // 重新加载数据
    loadAllMatches();
}

function initFilters() {
    const searchInput = document.getElementById('match-search');
    const leagueFilter = document.getElementById('league-filter');
    const statusFilter = document.getElementById('status-filter');
    
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                currentPage = 1;
                loadAllMatches();
            }, 300);
        });
    }
    
    if (leagueFilter) {
        leagueFilter.addEventListener('change', function() {
            currentPage = 1;
            loadAllMatches();
        });
    }
    
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            currentPage = 1;
            loadAllMatches();
        });
    }
}

async function loadAllMatches() {
    try {
        // 显示加载状态
        const loading = document.getElementById('matches-loading');
        if (loading) loading.style.display = 'block';
        
        // 构建筛选参数
        const filters = {
            page: currentPage,
            page_size: 12
        };
        
        // 添加标签页筛选
        if (currentTab !== 'all') {
            filters.status = currentTab;
        }
        
        // 添加搜索筛选
        const searchInput = document.getElementById('match-search');
        if (searchInput && searchInput.value.trim()) {
            filters.search = searchInput.value.trim();
        }
        
        // 添加联赛筛选
        const leagueFilter = document.getElementById('league-filter');
        if (leagueFilter && leagueFilter.value) {
            filters.league = leagueFilter.value;
        }
        
        // 添加状态筛选
        const statusFilter = document.getElementById('status-filter');
        if (statusFilter && statusFilter.value) {
            filters.status = statusFilter.value;
        }
        
        // 调用API
        const response = await apiCall(api.getMatches, filters);
        
        DataAdapter.validateApiResponse(response, ['matches']);
        
        allMatches = response.data.matches || [];
        
        // 更新分页信息
        if (response.data.pagination) {
            totalPages = response.data.pagination.totalPages;
            updatePaginationInfo(response.data.pagination);
        }
        
        renderMatches(allMatches);
        renderPagination();
        
    } catch (error) {
        console.error('加载比赛数据失败:', error);
        showMatchesError(error.message);
    } finally {
        // 隐藏加载状态
        const loading = document.getElementById('matches-loading');
        if (loading) loading.style.display = 'none';
    }
}

function renderMatches(matches) {
    const container = document.getElementById('matches-grid');
    
    if (!matches || matches.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center py-12">
                <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6-4h6m2 5.291A7.962 7.962 0 0112 15c-2.034 0-3.9.785-5.291 2.073M6.343 6.343A8 8 0 1017.657 17.657 8 8 0 006.343 6.343z"></path>
                </svg>
                <p class="text-gray-400 text-lg mb-2">没有找到符合条件的比赛</p>
                <p class="text-gray-500 text-sm">尝试调整筛选条件或等待数据同步</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = matches.map(match => {
        const timeAgo = getTimeAgo(match.startTime);
        const statusInfo = getMatchStatus(match);
        const duration = match.duration ? formatDuration(match.duration) : '';
        
        return `
            <div class="match-card rounded-lg p-6 cursor-pointer" onclick="viewMatch('${match.id}')">
                <div class="flex justify-between items-start mb-4">
                    <div class="text-sm text-gray-400 truncate flex-1 mr-2">${match.league?.name || '未知联赛'}</div>
                    <div class="text-sm ${statusInfo.color} ${statusInfo.class} flex-shrink-0">${statusInfo.text}</div>
                </div>
                <div class="space-y-3">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3 flex-1 min-w-0">
                            <div class="team-tag ${getTeamColor(match.radiantWin, true)} flex-shrink-0">
                                ${match.radiant?.tag || 'RAD'}
                            </div>
                            <span class="font-medium text-sm truncate">${match.radiant?.name || '天辉队伍'}</span>
                        </div>
                        <span class="font-bold ${getScoreColor(match.radiantWin, true)} ml-2">${match.radiant?.score || 0}</span>
                    </div>
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3 flex-1 min-w-0">
                            <div class="team-tag ${getTeamColor(match.radiantWin, false)} flex-shrink-0">
                                ${match.dire?.tag || 'DIR'}
                            </div>
                            <span class="font-medium text-sm truncate">${match.dire?.name || '夜魇队伍'}</span>
                        </div>
                        <span class="font-bold ${getScoreColor(match.radiantWin, false)} ml-2">${match.dire?.score || 0}</span>
                    </div>
                </div>
                <div class="mt-4 pt-4 border-t border-dota-border">
                    <div class="flex justify-between items-center text-sm">
                        <div class="text-gray-400">
                            <div>${timeAgo}</div>
                            ${duration ? `<div class="text-xs text-gray-500">${duration}</div>` : ''}
                        </div>
                        <div class="flex space-x-2 flex-wrap justify-end">
                            <span class="bg-ancient-600 text-white px-2 py-1 rounded text-xs whitespace-nowrap">${match.commentCount || 0}条讨论</span>
                            <span class="bg-dota-accent text-white px-2 py-1 rounded text-xs whitespace-nowrap cursor-pointer hover:bg-blue-600 transition-colors" onclick="event.stopPropagation(); window.location.href='match-discussion.html?id=${match.id}'">
                                💬 讨论版
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function renderPagination() {
    const pagination = document.getElementById('matches-pagination');
    const prevButton = document.getElementById('prev-page');
    const nextButton = document.getElementById('next-page');
    const pageNumbers = document.getElementById('page-numbers');
    
    if (totalPages <= 1) {
        if (pagination) pagination.style.display = 'none';
        return;
    }
    
    if (pagination) pagination.style.display = 'flex';
    
    // 更新上一页按钮
    if (prevButton) {
        prevButton.disabled = currentPage === 1;
        prevButton.onclick = () => {
            if (currentPage > 1) {
                currentPage--;
                loadAllMatches();
            }
        };
    }
    
    // 更新下一页按钮
    if (nextButton) {
        nextButton.disabled = currentPage === totalPages;
        nextButton.onclick = () => {
            if (currentPage < totalPages) {
                currentPage++;
                loadAllMatches();
            }
        };
    }
    
    // 生成页码
    if (pageNumbers) {
        let pageNumbersHTML = '';
        const maxVisiblePages = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
        let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
        
        if (endPage - startPage < maxVisiblePages - 1) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }
        
        for (let i = startPage; i <= endPage; i++) {
            pageNumbersHTML += `
                <button onclick="goToPage(${i})" class="pagination-page ${i === currentPage ? 'active' : ''}">
                    ${i}
                </button>
            `;
        }
        
        pageNumbers.innerHTML = pageNumbersHTML;
    }
}

function goToPage(page) {
    currentPage = page;
    loadAllMatches();
    
    // 滚动到顶部
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

function updatePaginationInfo(pagination) {
    // 更新分页信息显示
    const pageInfo = document.getElementById('page-info');
    if (pageInfo) {
        pageInfo.textContent = `第 ${pagination.page} 页，共 ${pagination.totalPages} 页 (总计 ${pagination.total} 场比赛)`;
    }
}

function showMatchesError(message) {
    const container = document.getElementById('matches-grid');
    container.innerHTML = `
        <div class="col-span-full text-center py-12">
            <svg class="w-16 h-16 text-dire-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
            </svg>
            <p class="text-dire-500 mb-4">无法加载比赛数据</p>
            <p class="text-gray-400 text-sm mb-4">${message}</p>
            <p class="text-gray-500 text-xs mb-4">请确保后端服务已启动: python backend/python/run.py</p>
            <button onclick="loadAllMatches()" class="bg-dota-accent hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors">
                重新加载
            </button>
        </div>
    `;
}

// 重写viewMatch函数
function viewMatch(matchId) {
    window.location.href = `match-discussion.html?id=${matchId}`;
}

// 工具函数
function getMatchStatus(match) {
    switch (match.status) {
        case 'live':
            return {
                text: '直播中',
                color: 'text-dire-500',
                class: 'status-live'
            };
        case 'upcoming':
            return {
                text: '即将开始', // TODO: 从API获取真实状态文本
                color: 'text-ancient-500',
                class: ''
            };
        case 'finished':
        default:
            return {
                text: '已结束',
                color: 'text-radiant-500',
                class: ''
            };
    }
}

function getTeamColor(radiantWin, isRadiant) {
    if (radiantWin === null) return 'bg-gray-600';
    
    if (isRadiant) {
        return radiantWin ? 'bg-radiant-600' : 'bg-gray-600';
    } else {
        return !radiantWin ? 'bg-dire-600' : 'bg-gray-600';
    }
}

function getScoreColor(radiantWin, isRadiant) {
    if (radiantWin === null) return 'text-gray-400';
    
    if (isRadiant) {
        return radiantWin ? 'text-radiant-500' : 'text-gray-400';
    } else {
        return !radiantWin ? 'text-dire-500' : 'text-gray-400';
    }
}
