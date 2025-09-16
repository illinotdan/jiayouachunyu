// 数据统计页面JavaScript

let currentTab = 'heroes';

document.addEventListener('DOMContentLoaded', function() {
    initStatsPage();
});

function initStatsPage() {
    // 初始化标签页
    initTabs();
    
    // 加载统计数据
    loadStatsData();
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
    activeButton.classList.remove('text-gray-400');
    activeButton.classList.add('active', 'border-dota-accent', 'text-dota-accent');
    
    // 渲染对应的标签页内容
    renderTabContent(tab);
}

async function loadStatsData() {
    try {
        // 模拟加载延迟
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // 渲染默认标签页内容
        renderTabContent(currentTab);
        
    } catch (error) {
        console.error('加载统计数据失败:', error);
        showError('加载统计数据失败，请稍后重试');
    }
}

function renderTabContent(tab) {
    const container = document.getElementById('stats-content');
    const loading = document.getElementById('stats-loading');
    
    if (loading) loading.style.display = 'none';
    
    switch (tab) {
        case 'heroes':
            renderHeroStats(container);
            break;
        case 'teams':
            renderTeamStats(container);
            break;
        case 'trends':
            renderTrends(container);
            break;
        case 'predictions':
            renderPredictions(container);
            break;
    }
}

function renderHeroStats(container) {
    const heroStats = generateHeroStats();
    
    container.innerHTML = `
        <div class="space-y-8">
            <div class="flex justify-between items-center">
                <h3 class="text-2xl font-semibold">英雄胜率统计</h3>
                <div class="flex space-x-2">
                    <select class="bg-dota-panel border border-dota-border text-dota-text rounded-lg px-3 py-2 text-sm" id="timeRange">
                        <option value="week">本周数据</option>
                        <option value="month">本月数据</option>
                        <option value="all">全部数据</option>
                    </select>
                    <select class="bg-dota-panel border border-dota-border text-dota-text rounded-lg px-3 py-2 text-sm" id="matchType">
                        <option value="pro">职业比赛</option>
                        <option value="high">高分段</option>
                        <option value="all">全段位</option>
                    </select>
                </div>
            </div>
            
            <!-- 图表容器 -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                <div class="bg-dota-panel border border-dota-border rounded-lg p-6">
                    <h4 class="text-lg font-semibold mb-4">胜率排行榜</h4>
                    <div class="chart-container" style="height: 300px;">
                        <canvas id="winRateChart"></canvas>
                    </div>
                </div>
                <div class="bg-dota-panel border border-dota-border rounded-lg p-6">
                    <h4 class="text-lg font-semibold mb-4">选取率分布</h4>
                    <div class="chart-container" style="height: 300px;">
                        <canvas id="pickRateChart"></canvas>
                    </div>
                </div>
            </div>
            
            <!-- 英雄详细数据 -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                ${heroStats.map(hero => `
                    <div class="bg-dota-panel border border-dota-border rounded-lg p-4 card-hover">
                        <div class="flex items-center space-x-3 mb-3">
                            <div class="w-12 h-12 bg-gradient-to-r ${hero.gradient} rounded-lg flex items-center justify-center text-white font-bold text-sm">
                                ${hero.name.charAt(0)}
                            </div>
                            <div class="flex-1 min-w-0">
                                <h4 class="font-medium text-white truncate">${hero.name}</h4>
                                <p class="text-xs text-gray-400">${hero.role}</p>
                            </div>
                        </div>
                        
                        <div class="space-y-2">
                            <div class="flex justify-between items-center">
                                <span class="text-sm text-gray-400">胜率</span>
                                <span class="text-sm font-medium ${hero.winRate >= 50 ? 'text-radiant-500' : 'text-dire-500'}">
                                    ${hero.winRate.toFixed(1)}%
                                </span>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${hero.winRate}%"></div>
                            </div>
                            
                            <div class="grid grid-cols-2 gap-2 text-xs">
                                <div class="text-center">
                                    <div class="text-dota-accent font-medium">${hero.pickRate.toFixed(1)}%</div>
                                    <div class="text-gray-400">选取率</div>
                                </div>
                                <div class="text-center">
                                    <div class="text-ancient-500 font-medium">${hero.banRate.toFixed(1)}%</div>
                                    <div class="text-gray-400">禁用率</div>
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
    
    // 初始化图表
    setTimeout(() => {
        initHeroCharts(heroStats);
    }, 100);
}
}

function renderTeamStats(container) {
    const teamStats = generateTeamStats();
    
    container.innerHTML = `
        <div class="space-y-8">
            <div class="flex justify-between items-center">
                <h3 class="text-2xl font-semibold">战队排行榜</h3>
                <div class="flex space-x-2">
                    <select class="bg-dota-panel border border-dota-border text-dota-text rounded-lg px-3 py-2 text-sm" id="seasonRange">
                        <option value="current">当前赛季</option>
                        <option value="last">上一赛季</option>
                        <option value="all">历史数据</option>
                    </select>
                    <select class="bg-dota-panel border border-dota-border text-dota-text rounded-lg px-3 py-2 text-sm" id="tournamentType">
                        <option value="international">国际赛事</option>
                        <option value="regional">地区赛事</option>
                        <option value="all">所有赛事</option>
                    </select>
                </div>
            </div>
            
            <!-- 战队统计图表 -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                <div class="bg-dota-panel border border-dota-border rounded-lg p-6">
                    <h4 class="text-lg font-semibold mb-4">胜率分布</h4>
                    <div class="chart-container" style="height: 300px;">
                        <canvas id="teamWinRateChart"></canvas>
                    </div>
                </div>
                <div class="bg-dota-panel border border-dota-border rounded-lg p-6">
                    <h4 class="text-lg font-semibold mb-4">积分排名趋势</h4>
                    <div class="chart-container" style="height: 300px;">
                        <canvas id="teamPointsChart"></canvas>
                    </div>
                </div>
            </div>
            
            <!-- 战队详细数据表格 -->
            <div class="bg-dota-panel border border-dota-border rounded-lg overflow-hidden">
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-dota-border">
                        <thead class="bg-dota-bg">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">排名</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">战队</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">比赛场次</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">胜率</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">积分</th>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">趋势</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-dota-border">
                            ${teamStats.map((team, index) => `
                                <tr class="hover:bg-dota-bg transition-colors">
                                    <td class="px-6 py-4 whitespace-nowrap">
                                        <div class="flex items-center">
                                            <span class="text-lg font-bold text-dota-accent">${index + 1}</span>
                                            ${index < 3 ? `<span class="ml-2 text-${index === 0 ? 'yellow' : index === 1 ? 'gray' : 'orange'}-500">★</span>` : ''}
                                        </div>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap">
                                        <div class="flex items-center">
                                            <img src="${team.logo}" alt="${team.name}" class="w-10 h-10 rounded-lg mr-3">
                                            <div>
                                                <div class="text-white font-medium">${team.name}</div>
                                                <div class="text-gray-400 text-sm">${team.region}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-gray-300">
                                        <div>${team.matches.wins + team.matches.losses}</div>
                                        <div class="text-sm text-gray-400">${team.matches.wins}胜 ${team.matches.losses}负</div>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap">
                                        <div class="flex items-center">
                                            <span class="text-white font-medium mr-2">${team.winRate.toFixed(1)}%</span>
                                            <div class="progress-bar-small">
                                                <div class="progress-fill" style="width: ${team.winRate}%"></div>
                                            </div>
                                        </div>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap">
                                        <span class="text-dota-accent font-bold">${team.points}</span>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap">
                                        <span class="text-${team.trend > 0 ? 'radiant' : 'dire'}-500 text-sm font-medium">
                                            ${team.trend > 0 ? '↗' : '↘'} ${Math.abs(team.trend)}
                                        </span>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    // 初始化战队图表
    setTimeout(() => {
        initTeamCharts(teamStats);
    }, 100);
}

function renderTrends(container) {
    container.innerHTML = `
        <div class="space-y-8">
            <h3 class="text-2xl font-semibold">趋势分析</h3>
            
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- 版本趋势 -->
                <div class="bg-dota-panel border border-dota-border rounded-lg p-6">
                    <h4 class="text-lg font-semibold mb-4">版本英雄变化</h4>
                    <div class="space-y-3">
                        <!-- TODO: 从API获取真实版本趋势数据 -->
                        <div class="text-center py-8 text-gray-400">
                            <p>版本趋势数据加载中...</p>
                            <p class="text-xs mt-2">等待API集成</p>
                        </div>
                    </div>
                </div>
                
                <!-- Meta趋势 -->
                <div class="bg-dota-panel border border-dota-border rounded-lg p-6">
                    <h4 class="text-lg font-semibold mb-4">当前Meta趋势</h4>
                    <!-- TODO: 从API获取真实Meta趋势数据 -->
                    <div class="space-y-4">
                        <div class="text-center py-8 text-gray-400">
                            <p>Meta趋势数据加载中...</p>
                            <p class="text-xs mt-2">等待API集成</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderPredictions(container) {
    const predictionStats = generatePredictionStats();
    
    container.innerHTML = `
        <div class="space-y-8">
            <h3 class="text-2xl font-semibold">预测统计</h3>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                ${predictionStats.map(stat => `
                    <div class="stat-card">
                        <div class="text-center">
                            <div class="w-16 h-16 ${stat.bgColor} rounded-lg mx-auto mb-4 flex items-center justify-center">
                                <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${stat.icon}"></path>
                                </svg>
                            </div>
                            <div class="stat-number ${stat.textColor}">${stat.value}</div>
                            <div class="text-gray-400 mb-2">${stat.label}</div>
                            <div class="text-xs ${stat.trendColor}">${stat.trend}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
            
            <!-- 专家预测排行 -->
            <div class="bg-dota-panel border border-dota-border rounded-lg p-6">
                <h4 class="text-lg font-semibold mb-4">专家预测排行榜</h4>
                <div class="space-y-3">
                    ${generateExpertRanking().map((expert, index) => `
                        <div class="flex items-center justify-between p-3 bg-dota-bg/50 rounded-lg">
                            <div class="flex items-center space-x-3">
                                <span class="w-8 h-8 ${index < 3 ? 'bg-ancient-600' : 'bg-gray-600'} rounded-full flex items-center justify-center text-white font-bold text-sm">
                                    ${index + 1}
                                </span>
                                <img src="${expert.avatar}" alt="${expert.name}" class="w-8 h-8 rounded-full bg-dota-panel">
                                <div>
                                    <div class="font-medium">${expert.name}</div>
                                    <div class="text-xs text-gray-400">${expert.predictions}次预测</div>
                                </div>
                            </div>
                            <div class="text-right">
                                <div class="font-bold text-radiant-500">${expert.accuracy.toFixed(1)}%</div>
                                <div class="text-xs text-gray-400">准确率</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
}

function generateHeroStats() {
    return [
        { name: '祈求者', role: '核心', winRate: 52.3, pickRate: 23.1, banRate: 45.2, gradient: 'from-blue-500 to-purple-600' },
        { name: '影魔', role: '核心', winRate: 48.7, pickRate: 31.2, banRate: 38.9, gradient: 'from-red-500 to-orange-600' },
        { name: '帕克', role: '核心', winRate: 51.8, pickRate: 28.3, banRate: 42.1, gradient: 'from-green-500 to-teal-600' },
        { name: '风暴之灵', role: '核心', winRate: 49.2, pickRate: 26.7, banRate: 40.3, gradient: 'from-indigo-500 to-blue-600' },
        { name: '灰烬之灵', role: '核心', winRate: 53.1, pickRate: 29.4, banRate: 47.8, gradient: 'from-orange-500 to-red-600' },
        { name: '狙击手', role: '核心', winRate: 46.8, pickRate: 18.9, banRate: 25.6, gradient: 'from-yellow-500 to-orange-600' },
        { name: '主宰', role: '核心', winRate: 50.4, pickRate: 22.7, banRate: 35.2, gradient: 'from-red-600 to-pink-600' },
        { name: '冥魂大帝', role: '核心', winRate: 47.9, pickRate: 15.3, banRate: 28.7, gradient: 'from-green-600 to-emerald-600' }
    ];
}

// 初始化英雄相关图表
function initHeroCharts(heroStats) {
    // 胜率排行榜图表
    const winRateCtx = document.getElementById('winRateChart');
    if (winRateCtx) {
        const sortedHeroes = [...heroStats].sort((a, b) => b.winRate - a.winRate).slice(0, 8);
        new Chart(winRateCtx, {
            type: 'bar',
            data: {
                labels: sortedHeroes.map(hero => hero.name),
                datasets: [{
                    label: '胜率 (%)',
                    data: sortedHeroes.map(hero => hero.winRate),
                    backgroundColor: sortedHeroes.map(hero => 
                        hero.winRate >= 52 ? 'rgba(34, 197, 94, 0.8)' : 
                        hero.winRate >= 48 ? 'rgba(251, 191, 36, 0.8)' : 
                        'rgba(239, 68, 68, 0.8)'
                    ),
                    borderColor: sortedHeroes.map(hero => 
                        hero.winRate >= 52 ? 'rgb(34, 197, 94)' : 
                        hero.winRate >= 48 ? 'rgb(251, 191, 36)' : 
                        'rgb(239, 68, 68)'
                    ),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: '#9CA3AF',
                            maxRotation: 45
                        },
                        grid: {
                            color: 'rgba(156, 163, 175, 0.1)'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        max: 60,
                        ticks: {
                            color: '#9CA3AF',
                            callback: function(value) {
                                return value + '%';
                            }
                        },
                        grid: {
                            color: 'rgba(156, 163, 175, 0.1)'
                        }
                    }
                }
            }
        });
    }

    // 选取率分布图表
    const pickRateCtx = document.getElementById('pickRateChart');
    if (pickRateCtx) {
        new Chart(pickRateCtx, {
            type: 'doughnut',
            data: {
                labels: heroStats.map(hero => hero.name),
                datasets: [{
                    data: heroStats.map(hero => hero.pickRate),
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(34, 197, 94, 0.8)',
                        'rgba(251, 191, 36, 0.8)',
                        'rgba(168, 85, 247, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(236, 72, 153, 0.8)',
                        'rgba(20, 184, 166, 0.8)'
                    ],
                    borderColor: [
                        'rgb(59, 130, 246)',
                        'rgb(239, 68, 68)',
                        'rgb(34, 197, 94)',
                        'rgb(251, 191, 36)',
                        'rgb(168, 85, 247)',
                        'rgb(245, 158, 11)',
                        'rgb(236, 72, 153)',
                        'rgb(20, 184, 166)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: '#9CA3AF',
                            padding: 15,
                            font: {
                                size: 11
                            }
                        }
                    }
                }
            }
        });
    }
}

function generateTeamStats() {
    return [
        {
            name: 'Team Spirit',
            logo: 'https://via.placeholder.com/40x40/4F46E5/FFFFFF?text=TS',
            region: '欧洲',
            matches: { wins: 45, losses: 12 },
            winRate: 78.9,
            points: 2450,
            trend: 5
        },
        {
            name: 'PSG.LGD',
            logo: 'https://via.placeholder.com/40x40/EF4444/FFFFFF?text=LGD',
            region: '中国',
            matches: { wins: 42, losses: 15 },
            winRate: 73.7,
            points: 2380,
            trend: 3
        },
        {
            name: 'OG',
            logo: 'https://via.placeholder.com/40x40/10B981/FFFFFF?text=OG',
            region: '欧洲',
            matches: { wins: 38, losses: 18 },
            winRate: 67.9,
            points: 2210,
            trend: -2
        },
        {
            name: 'Team Secret',
            logo: 'https://via.placeholder.com/40x40/F59E0B/FFFFFF?text=TS',
            region: '欧洲',
            matches: { wins: 35, losses: 20 },
            winRate: 63.6,
            points: 2150,
            trend: 1
        },
        {
            name: 'Virtus.pro',
            logo: 'https://via.placeholder.com/40x40/8B5CF6/FFFFFF?text=VP',
            region: '东欧',
            matches: { wins: 32, losses: 23 },
            winRate: 58.2,
            points: 1980,
            trend: -3
        },
        {
            name: 'Evil Geniuses',
            logo: 'https://via.placeholder.com/40x40/F59E0B/FFFFFF?text=EG',
            region: '北美',
            matches: { wins: 30, losses: 25 },
            winRate: 54.5,
            points: 1890,
            trend: 2
        }
    ];
}

// 初始化战队相关图表
function initTeamCharts(teamStats) {
    // 胜率分布图表
    const winRateCtx = document.getElementById('teamWinRateChart');
    if (winRateCtx) {
        new Chart(winRateCtx, {
            type: 'bar',
            data: {
                labels: teamStats.map(team => team.name),
                datasets: [{
                    label: '胜率 (%)',
                    data: teamStats.map(team => team.winRate),
                    backgroundColor: teamStats.map(team => 
                        team.winRate >= 70 ? 'rgba(34, 197, 94, 0.8)' : 
                        team.winRate >= 60 ? 'rgba(251, 191, 36, 0.8)' : 
                        team.winRate >= 50 ? 'rgba(59, 130, 246, 0.8)' : 
                        'rgba(239, 68, 68, 0.8)'
                    ),
                    borderColor: teamStats.map(team => 
                        team.winRate >= 70 ? 'rgb(34, 197, 94)' : 
                        team.winRate >= 60 ? 'rgb(251, 191, 36)' : 
                        team.winRate >= 50 ? 'rgb(59, 130, 246)' : 
                        'rgb(239, 68, 68)'
                    ),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: '#9CA3AF',
                            maxRotation: 45
                        },
                        grid: {
                            color: 'rgba(156, 163, 175, 0.1)'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            color: '#9CA3AF',
                            callback: function(value) {
                                return value + '%';
                            }
                        },
                        grid: {
                            color: 'rgba(156, 163, 175, 0.1)'
                        }
                    }
                }
            }
        });
    }

    // 积分排名图表
    const pointsCtx = document.getElementById('teamPointsChart');
    if (pointsCtx) {
        const sortedTeams = [...teamStats].sort((a, b) => b.points - a.points);
        new Chart(pointsCtx, {
            type: 'line',
            data: {
                labels: sortedTeams.map(team => team.name),
                datasets: [{
                    label: '积分',
                    data: sortedTeams.map(team => team.points),
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: 'rgb(59, 130, 246)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: '#9CA3AF',
                            maxRotation: 45
                        },
                        grid: {
                            color: 'rgba(156, 163, 175, 0.1)'
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#9CA3AF'
                        },
                        grid: {
                            color: 'rgba(156, 163, 175, 0.1)'
                        }
                    }
                }
            }
        });
    }
}
    
    const trends = ['up', 'down', 'stable'];
    
    return teams.map(team => {
        const wins = Math.floor(Math.random() * 30) + 10;
        const losses = Math.floor(Math.random() * 20) + 5;
        const winRate = (wins / (wins + losses)) * 100;
        
        return {
            ...team,
            wins,
            losses,
            winRate,
            points: Math.floor(winRate * 10) + Math.floor(Math.random() * 100),
            trend: trends[Math.floor(Math.random() * trends.length)]
        };
    }).sort((a, b) => b.points - a.points);
}

function generatePredictionStats() {
    // TODO: 从API获取真实预测统计数据
    console.warn('generatePredictionStats: 使用模拟数据，需要从API获取真实预测统计数据');
    return [
        {
            label: '总预测数',
            value: '-',
            bgColor: 'bg-dota-accent',
            textColor: 'text-dota-accent',
            trend: '等待API',
            trendColor: 'text-gray-400',
            icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'
        },
        {
            label: '预测准确',
            value: '-',
            bgColor: 'bg-radiant-600',
            textColor: 'text-radiant-500',
            trend: '等待API',
            trendColor: 'text-gray-400',
            icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'
        },
        {
            label: '专家参与',
            value: '-',
            bgColor: 'bg-ancient-600',
            textColor: 'text-ancient-500',
            trend: '等待API',
            trendColor: 'text-gray-400',
            icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z'
        }
    ];
}

function generateExpertRanking() {
    // TODO: 从API获取真实专家数据
    // 临时返回空数组，等待API集成
    console.warn('generateExpertRanking: 使用模拟数据，需要从API获取真实专家数据');
    return [];
}

function showError(message) {
    const container = document.getElementById('stats-content');
    container.innerHTML = `
        <div class="text-center py-12">
            <svg class="w-16 h-16 text-dire-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
            </svg>
            <p class="text-dire-500 text-lg">${message}</p>
            <button onclick="loadStatsData()" class="mt-4 bg-dota-accent hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors">
                重新加载
            </button>
        </div>
    `;
}
