// 数据分析页面逻辑
// 基于统计服务API实现完整的数据可视化

class AnalyticsManager {
    constructor() {
        this.currentTimeRange = 30;
        this.currentTierFilter = 'all';
        this.chartInstances = new Map();
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadInitialData();
    }
    
    setupEventListeners() {
        // 时间范围控制
        document.getElementById('timeRange').addEventListener('change', (e) => {
            this.currentTimeRange = parseInt(e.target.value);
            this.refreshAllCharts();
        });
        
        // 段位筛选
        document.getElementById('tierFilter').addEventListener('change', (e) => {
            this.currentTierFilter = e.target.value;
            this.refreshAllCharts();
        });
        
        // 刷新按钮
        document.getElementById('refreshData').addEventListener('click', () => {
            this.refreshAllCharts();
        });
        
        // 图表切换标签
        this.setupChartTabs();
        
        // 导出功能
        document.getElementById('exportCharts').addEventListener('click', () => {
            this.exportAllCharts();
        });
        
        document.getElementById('exportData').addEventListener('click', () => {
            this.exportAllData();
        });
    }
    
    setupChartTabs() {
        // 为每个图表区域设置标签切换
        document.querySelectorAll('.chart-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const chartType = e.target.dataset.chart;
                const section = e.target.closest('section');
                
                // 更新标签状态
                section.querySelectorAll('.chart-tab').forEach(t => t.classList.remove('active'));
                e.target.classList.add('active');
                
                // 切换图表面板
                section.querySelectorAll('.chart-panel').forEach(panel => {
                    panel.classList.remove('active');
                });
                
                const targetPanel = section.querySelector(`#${chartType.replace('-', '')}Chart`) || 
                                  section.querySelector(`#${chartType}Chart`);
                if (targetPanel) {
                    targetPanel.classList.add('active');
                    
                    // 如果图表还没加载，则加载它
                    if (!this.chartInstances.has(targetPanel.id)) {
                        this.loadChartByType(chartType, targetPanel.id);
                    }
                }
            });
        });
    }
    
    async loadInitialData() {
        try {
            // 加载数据概览
            await this.loadDataSummary();
            
            // 加载默认图表（每个区域的第一个标签）
            await Promise.all([
                this.loadChartByType('hero-winrate', 'heroWinrateChart'),
                this.loadChartByType('match-duration', 'matchDurationChart'),
                this.loadChartByType('player-kda', 'playerKDAChart')
            ]);
            
        } catch (error) {
            console.error('加载初始数据失败:', error);
            this.showErrorMessage('数据加载失败，请刷新页面重试');
        }
    }
    
    async loadDataSummary() {
        try {
            const response = await api.getStatisticsSummary();
            
            if (response.success) {
                const summary = response.data.summary;
                
                // 更新概览卡片
                document.getElementById('totalMatches').textContent = 
                    summary.total_matches?.toLocaleString() || '-';
                document.getElementById('activeHeroes').textContent = 
                    summary.total_heroes || '-';
                document.getElementById('avgDuration').textContent = 
                    '35分钟'; // 可以从详细统计中获取
                document.getElementById('lastUpdate').textContent = 
                    summary.data_quality?.freshness || 'T-1';
            }
            
        } catch (error) {
            console.error('加载数据摘要失败:', error);
        }
    }
    
    async loadChartByType(chartType, containerId) {
        if (loadingManager.isLoading(containerId)) return;
        
        loadingManager.show(containerId, `正在加载${this.getChartDisplayName(chartType)}...`);
        
        try {
            let apiEndpoint;
            let chartMethod;
            
            // 根据图表类型调用相应的API方法
            let response;
            const filters = {
                time_range: this.currentTimeRange,
                tier_filter: this.currentTierFilter
            };
            
            switch (chartType) {
                case 'hero-winrate':
                    response = await api.getHeroWinrateRanking(filters);
                    chartMethod = 'renderHeroWinrateChart';
                    break;
                case 'hero-pickrate':
                    response = await api.getHeroPickrateHeatmap({ days: this.currentTimeRange });
                    chartMethod = 'renderHeroPickrateHeatmap';
                    break;
                case 'hero-roles':
                    response = await api.getHeroRoleDistribution(filters);
                    chartMethod = 'renderHeroRoleDistribution';
                    break;
                case 'match-duration':
                    response = await api.getMatchDurationDistribution(filters);
                    chartMethod = 'renderMatchDurationHistogram';
                    break;
                case 'economy-winrate':
                    response = await api.getEconomyWinrate(filters);
                    chartMethod = 'renderEconomyWinrateCurve';
                    break;
                case 'first-blood':
                    response = await api.getFirstBloodTiming(filters);
                    chartMethod = 'renderFirstBloodTrend';
                    break;
                case 'player-kda':
                    response = await api.getPlayerKDADistribution(filters);
                    chartMethod = 'renderKDABoxplot';
                    break;
                case 'farm-efficiency':
                    response = await api.getFarmEfficiencyComparison(filters);
                    chartMethod = 'renderFarmEfficiencyRadar';
                    break;
                default:
                    throw new Error(`未知的图表类型: ${chartType}`);
            }
            
            if (response.success) {
                // 使用数据适配器处理数据
                const adaptedData = DataAdapter.adaptChartData(response);
                
                // 渲染图表
                if (chartManager[chartMethod]) {
                    const chart = chartManager[chartMethod](containerId, adaptedData || response.data);
                    this.chartInstances.set(containerId, chart);
                } else {
                    console.warn(`图表渲染方法不存在: ${chartMethod}`);
                    this.showErrorInChart(containerId, '图表渲染方法不存在');
                }
            } else {
                this.showErrorInChart(containerId, response.error?.message || '数据加载失败');
            }
            
        } catch (error) {
            console.error(`加载图表失败 ${chartType}:`, error);
            this.showErrorInChart(containerId, error.message || '图表加载失败');
        } finally {
            loadingManager.hide(containerId);
        }
    }
    
    async refreshAllCharts() {
        // 显示全局刷新状态
        document.getElementById('refreshData').innerHTML = '🔄 刷新中...';
        document.getElementById('refreshData').disabled = true;
        
        try {
            // 刷新数据摘要
            await this.loadDataSummary();
            
            // 刷新所有已加载的图表
            const refreshPromises = [];
            this.chartInstances.forEach((chart, containerId) => {
                // 销毁旧图表
                chartManager.destroyChart(containerId);
                this.chartInstances.delete(containerId);
                
                // 重新加载
                const chartType = this.getChartTypeFromContainerId(containerId);
                if (chartType) {
                    refreshPromises.push(this.loadChartByType(chartType, containerId));
                }
            });
            
            await Promise.all(refreshPromises);
            
            this.showSuccessMessage('数据刷新完成');
            
        } catch (error) {
            console.error('刷新数据失败:', error);
            this.showErrorMessage('数据刷新失败');
        } finally {
            document.getElementById('refreshData').innerHTML = '🔄 刷新数据';
            document.getElementById('refreshData').disabled = false;
        }
    }
    
    // 供外部调用的刷新方法
    async refreshAllData() {
        return await this.refreshAllCharts();
    }
    
    getChartTypeFromContainerId(containerId) {
        const typeMap = {
            'heroWinrateChart': 'hero-winrate',
            'heroPickrateChart': 'hero-pickrate',
            'heroRolesChart': 'hero-roles',
            'matchDurationChart': 'match-duration',
            'economyWinrateChart': 'economy-winrate',
            'firstBloodChart': 'first-blood',
            'playerKDAChart': 'player-kda',
            'farmEfficiencyChart': 'farm-efficiency'
        };
        
        return typeMap[containerId];
    }
    
    getChartDisplayName(chartType) {
        const nameMap = {
            'hero-winrate': '英雄胜率数据',
            'hero-pickrate': '英雄选取热力图',
            'hero-roles': '英雄角色分布',
            'match-duration': '比赛时长分布',
            'economy-winrate': '经济胜率曲线',
            'first-blood': '首杀时间趋势',
            'player-kda': 'KDA分布数据',
            'farm-efficiency': 'Farm效率数据'
        };
        
        return nameMap[chartType] || '图表数据';
    }
    
    // 移除旧的loading方法，使用全局loadingManager
    
    showErrorInChart(containerId, message) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="flex flex-col items-center justify-center h-full text-center">
                    <div class="text-dire-500 text-4xl mb-4">⚠️</div>
                    <p class="text-gray-400 mb-2">图表加载失败</p>
                    <p class="text-sm text-gray-500">${message}</p>
                    <button onclick="analyticsManager.retryChart('${containerId}')" 
                            class="mt-4 bg-dota-accent hover:bg-blue-600 text-white px-4 py-2 rounded-lg transition-colors">
                        重试
                    </button>
                </div>
            `;
        }
    }
    
    retryChart(containerId) {
        const chartType = this.getChartTypeFromContainerId(containerId);
        if (chartType) {
            this.loadChartByType(chartType, containerId);
        }
    }
    
    showSuccessMessage(message) {
        errorHandler.showSuccess(message);
    }
    
    showErrorMessage(message) {
        errorHandler.showError(message);
    }
    
    async exportAllCharts() {
        try {
            const exports = [];
            
            this.chartInstances.forEach((chart, containerId) => {
                const dataUrl = chartManager.exportChart(containerId, 'png');
                if (dataUrl) {
                    exports.push({
                        name: containerId,
                        data: dataUrl
                    });
                }
            });
            
            if (exports.length === 0) {
                this.showErrorMessage('没有可导出的图表');
                return;
            }
            
            // 创建ZIP文件并下载
            // 这里可以使用JSZip库来创建ZIP文件
            // 暂时简化为下载第一个图表
            if (exports.length > 0) {
                const link = document.createElement('a');
                link.download = `dota-analytics-charts-${new Date().toISOString().split('T')[0]}.png`;
                link.href = exports[0].data;
                link.click();
                
                this.showSuccessMessage('图表导出成功');
            }
            
        } catch (error) {
            console.error('导出图表失败:', error);
            this.showErrorMessage('图表导出失败');
        }
    }
    
    async exportAllData() {
        try {
            // 获取当前所有图表的原始数据
            const exportData = {
                timestamp: new Date().toISOString(),
                timeRange: this.currentTimeRange,
                tierFilter: this.currentTierFilter,
                charts: {}
            };
            
            // 这里需要重新请求数据，因为图表可能只包含处理后的数据
            const chartTypes = Array.from(this.chartInstances.keys())
                .map(containerId => this.getChartTypeFromContainerId(containerId))
                .filter(Boolean);
            
            for (const chartType of chartTypes) {
                try {
                    const response = await api.request(`/stats/export/${chartType}`);
                    if (response.success) {
                        exportData.charts[chartType] = response.data;
                    }
                } catch (error) {
                    console.warn(`导出 ${chartType} 数据失败:`, error);
                }
            }
            
            // 创建并下载JSON文件
            const dataStr = JSON.stringify(exportData, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(dataBlob);
            
            const link = document.createElement('a');
            link.download = `dota-analytics-data-${new Date().toISOString().split('T')[0]}.json`;
            link.href = url;
            link.click();
            
            URL.revokeObjectURL(url);
            this.showSuccessMessage('数据导出成功');
            
        } catch (error) {
            console.error('导出数据失败:', error);
            this.showErrorMessage('数据导出失败');
        }
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 等待图表管理器加载完成
    setTimeout(() => {
        window.analyticsManager = new AnalyticsManager();
    }, 1000);
});

// 响应式处理
window.addEventListener('resize', () => {
    if (window.analyticsManager) {
        window.analyticsManager.chartInstances.forEach(chart => {
            if (chart && chart.resize) {
                chart.resize();
            }
        });
    }
});
