// 统计图表管理器 - 基于图表推荐文档实现
// 支持多种图表类型和交互功能

class ChartManager {
    constructor() {
        this.charts = new Map();
        this.chartLibraries = {
            echarts: null,
            d3: null,
            plotly: null
        };
        this.defaultOptions = CONFIG.charts || {};
        
        // 加载图表库
        this.loadChartLibraries();
    }
    
    // 加载图表库
    async loadChartLibraries() {
        try {
            // 加载ECharts（主要图表库）
            if (!window.echarts) {
                await this.loadScript('https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js');
            }
            this.chartLibraries.echarts = window.echarts;
            
            // 加载D3.js（复杂可视化）
            if (!window.d3) {
                await this.loadScript('https://cdn.jsdelivr.net/npm/d3@7.8.5/dist/d3.min.js');
            }
            this.chartLibraries.d3 = window.d3;
            
            console.log('📊 图表库加载完成');
        } catch (error) {
            console.error('图表库加载失败:', error);
        }
    }
    
    // 动态加载脚本
    loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
    
    // ========== 1. 英雄Meta分析图表 ==========
    
    // 英雄胜率排行榜 - 柱状图
    renderHeroWinrateChart(containerId, data, options = {}) {
        try {
            const container = document.getElementById(containerId);
            if (!container) return;
            
            const chart = this.chartLibraries.echarts.init(container);
            
            // 处理数据
            const heroNames = data.data.overall.slice(0, 20).map(h => h.hero_name);
            const winrates = data.data.overall.slice(0, 20).map(h => h.winrate);
            const matches = data.data.overall.slice(0, 20).map(h => h.matches);
            
            const chartOptions = {
                title: {
                    text: data.title || '英雄胜率排行榜',
                    left: 'center',
                    textStyle: {
                        color: '#e2e8f0'
                    }
                },
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow'
                    },
                    formatter: function(params) {
                        const index = params[0].dataIndex;
                        return `
                            <div style="color: #1a1f2e;">
                                <strong>${heroNames[index]}</strong><br/>
                                胜率: ${winrates[index]}%<br/>
                                场次: ${matches[index]}
                            </div>
                        `;
                    }
                },
                grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '3%',
                    containLabel: true
                },
                xAxis: {
                    type: 'category',
                    data: heroNames,
                    axisLabel: {
                        rotate: 45,
                        color: '#94a3b8'
                    },
                    axisLine: {
                        lineStyle: {
                            color: '#2d3748'
                        }
                    }
                },
                yAxis: {
                    type: 'value',
                    name: '胜率 (%)',
                    axisLabel: {
                        color: '#94a3b8'
                    },
                    axisLine: {
                        lineStyle: {
                            color: '#2d3748'
                        }
                    },
                    splitLine: {
                        lineStyle: {
                            color: '#2d3748'
                        }
                    }
                },
                series: [{
                    name: '胜率',
                    type: 'bar',
                    data: winrates,
                    itemStyle: {
                        color: new this.chartLibraries.echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: '#22c55e' },
                            { offset: 1, color: '#16a34a' }
                        ])
                    },
                    emphasis: {
                        itemStyle: {
                            color: '#4ade80'
                        }
                    }
                }]
            };
            
            chart.setOption(chartOptions);
            this.charts.set(containerId, chart);
            
            // 响应式处理
            window.addEventListener('resize', () => {
                chart.resize();
            });
            
            return chart;
            
        } catch (error) {
            console.error('渲染英雄胜率图表失败:', error);
        }
    }
    
    // 英雄选取率热力图
    renderHeroPickrateHeatmap(containerId, data, options = {}) {
        try {
            const container = document.getElementById(containerId);
            if (!container) return;
            
            const chart = this.chartLibraries.echarts.init(container);
            
            // 处理热力图数据
            const matrixData = data.data.matrix.map(item => [
                item.x, item.y, item.value
            ]);
            
            const chartOptions = {
                title: {
                    text: data.title || '英雄选取率热力图',
                    left: 'center',
                    textStyle: {
                        color: '#e2e8f0'
                    }
                },
                tooltip: {
                    position: 'top',
                    formatter: function(params) {
                        const item = data.data.matrix[params.dataIndex];
                        return `
                            <div style="color: #1a1f2e;">
                                <strong>${item.hero}</strong><br/>
                                日期: ${item.date}<br/>
                                选取次数: ${item.value}
                            </div>
                        `;
                    }
                },
                grid: {
                    height: '50%',
                    top: '10%'
                },
                xAxis: {
                    type: 'category',
                    data: data.data.x_labels,
                    splitArea: {
                        show: true
                    },
                    axisLabel: {
                        color: '#94a3b8'
                    }
                },
                yAxis: {
                    type: 'category',
                    data: data.data.y_labels.slice(0, 20), // 只显示前20个英雄
                    splitArea: {
                        show: true
                    },
                    axisLabel: {
                        color: '#94a3b8'
                    }
                },
                visualMap: {
                    min: 0,
                    max: data.data.meta.max_picks,
                    calculable: true,
                    orient: 'horizontal',
                    left: 'center',
                    bottom: '15%',
                    inRange: {
                        color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
                    },
                    textStyle: {
                        color: '#e2e8f0'
                    }
                },
                series: [{
                    name: '选取次数',
                    type: 'heatmap',
                    data: matrixData.filter(item => item[1] < 20), // 只显示前20个英雄
                    label: {
                        show: false
                    },
                    emphasis: {
                        itemStyle: {
                            shadowBlur: 10,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }]
            };
            
            chart.setOption(chartOptions);
            this.charts.set(containerId, chart);
            
            window.addEventListener('resize', () => {
                chart.resize();
            });
            
            return chart;
            
        } catch (error) {
            console.error('渲染英雄选取率热力图失败:', error);
        }
    }
    
    // 英雄角色分布饼图
    renderHeroRoleDistribution(containerId, data, options = {}) {
        try {
            const container = document.getElementById(containerId);
            if (!container) return;
            
            const chart = this.chartLibraries.echarts.init(container);
            
            const chartOptions = {
                title: {
                    text: data.title || '英雄角色分布',
                    left: 'center',
                    textStyle: {
                        color: '#e2e8f0'
                    }
                },
                tooltip: {
                    trigger: 'item',
                    formatter: '{a} <br/>{b}: {c} ({d}%)'
                },
                legend: {
                    orient: 'vertical',
                    left: 'left',
                    textStyle: {
                        color: '#94a3b8'
                    }
                },
                series: [{
                    name: '角色分布',
                    type: 'pie',
                    radius: '50%',
                    data: data.data.segments.map(segment => ({
                        value: segment.value,
                        name: segment.name
                    })),
                    itemStyle: {
                        borderRadius: 10,
                        borderColor: '#1a1f2e',
                        borderWidth: 2
                    },
                    emphasis: {
                        itemStyle: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }]
            };
            
            chart.setOption(chartOptions);
            this.charts.set(containerId, chart);
            
            window.addEventListener('resize', () => {
                chart.resize();
            });
            
            return chart;
            
        } catch (error) {
            console.error('渲染英雄角色分布图失败:', error);
        }
    }
    
    // ========== 2. 比赛数据分析图表 ==========
    
    // 比赛时长分布直方图
    renderMatchDurationHistogram(containerId, data, options = {}) {
        try {
            const container = document.getElementById(containerId);
            if (!container) return;
            
            const chart = this.chartLibraries.echarts.init(container);
            
            const chartOptions = {
                title: {
                    text: data.title || '比赛时长分布',
                    left: 'center',
                    textStyle: {
                        color: '#e2e8f0'
                    }
                },
                tooltip: {
                    trigger: 'axis',
                    axisPointer: {
                        type: 'shadow'
                    },
                    formatter: function(params) {
                        const item = params[0];
                        return `
                            <div style="color: #1a1f2e;">
                                <strong>${item.name}</strong><br/>
                                比赛数: ${item.value}<br/>
                                占比: ${data.data.bins[item.dataIndex].percentage}%
                            </div>
                        `;
                    }
                },
                grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '3%',
                    containLabel: true
                },
                xAxis: {
                    type: 'category',
                    data: data.data.bins.map(bin => bin.range),
                    axisLabel: {
                        rotate: 45,
                        color: '#94a3b8'
                    },
                    axisLine: {
                        lineStyle: {
                            color: '#2d3748'
                        }
                    }
                },
                yAxis: {
                    type: 'value',
                    name: '比赛数量',
                    axisLabel: {
                        color: '#94a3b8'
                    },
                    axisLine: {
                        lineStyle: {
                            color: '#2d3748'
                        }
                    },
                    splitLine: {
                        lineStyle: {
                            color: '#2d3748'
                        }
                    }
                },
                series: [{
                    name: '比赛数量',
                    type: 'bar',
                    data: data.data.bins.map(bin => bin.count),
                    itemStyle: {
                        color: new this.chartLibraries.echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: '#4299e1' },
                            { offset: 1, color: '#2563eb' }
                        ])
                    }
                }]
            };
            
            chart.setOption(chartOptions);
            this.charts.set(containerId, chart);
            
            window.addEventListener('resize', () => {
                chart.resize();
            });
            
            return chart;
            
        } catch (error) {
            console.error('渲染比赛时长分布图失败:', error);
        }
    }
    
    // 经济优势胜率曲线
    renderEconomyWinrateCurve(containerId, data, options = {}) {
        try {
            const container = document.getElementById(containerId);
            if (!container) return;
            
            const chart = this.chartLibraries.echarts.init(container);
            
            const chartOptions = {
                title: {
                    text: data.title || '经济优势胜率曲线',
                    left: 'center',
                    textStyle: {
                        color: '#e2e8f0'
                    }
                },
                tooltip: {
                    trigger: 'axis',
                    formatter: function(params) {
                        const item = params[0];
                        const curvePoint = data.data.curve_points[item.dataIndex];
                        return `
                            <div style="color: #1a1f2e;">
                                <strong>${curvePoint.range}</strong><br/>
                                胜率: ${curvePoint.winrate}%<br/>
                                样本数: ${curvePoint.matches}
                            </div>
                        `;
                    }
                },
                grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '3%',
                    containLabel: true
                },
                xAxis: {
                    type: 'category',
                    data: data.data.curve_points.map(point => point.range),
                    axisLabel: {
                        color: '#94a3b8'
                    },
                    axisLine: {
                        lineStyle: {
                            color: '#2d3748'
                        }
                    }
                },
                yAxis: {
                    type: 'value',
                    name: '胜率 (%)',
                    min: 0,
                    max: 100,
                    axisLabel: {
                        color: '#94a3b8'
                    },
                    axisLine: {
                        lineStyle: {
                            color: '#2d3748'
                        }
                    },
                    splitLine: {
                        lineStyle: {
                            color: '#2d3748'
                        }
                    }
                },
                series: [{
                    name: '胜率',
                    type: 'line',
                    data: data.data.curve_points.map(point => point.winrate),
                    smooth: true,
                    lineStyle: {
                        color: '#eab308',
                        width: 3
                    },
                    itemStyle: {
                        color: '#eab308'
                    },
                    areaStyle: {
                        color: new this.chartLibraries.echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: 'rgba(234, 179, 8, 0.3)' },
                            { offset: 1, color: 'rgba(234, 179, 8, 0.1)' }
                        ])
                    }
                }]
            };
            
            chart.setOption(chartOptions);
            this.charts.set(containerId, chart);
            
            window.addEventListener('resize', () => {
                chart.resize();
            });
            
            return chart;
            
        } catch (error) {
            console.error('渲染经济优势胜率曲线失败:', error);
        }
    }
    
    // ========== 3. 选手表现分析图表 ==========
    
    // KDA分布箱线图
    renderKDABoxplot(containerId, data, options = {}) {
        try {
            const container = document.getElementById(containerId);
            if (!container) return;
            
            const chart = this.chartLibraries.echarts.init(container);
            
            const stats = data.data.statistics;
            const boxplotData = [[stats.min, stats.q1, stats.median, stats.q3, stats.max]];
            
            const chartOptions = {
                title: {
                    text: data.title || 'KDA分布箱线图',
                    left: 'center',
                    textStyle: {
                        color: '#e2e8f0'
                    }
                },
                tooltip: {
                    trigger: 'item',
                    formatter: function(params) {
                        return `
                            <div style="color: #1a1f2e;">
                                <strong>KDA统计</strong><br/>
                                最小值: ${stats.min}<br/>
                                Q1: ${stats.q1}<br/>
                                中位数: ${stats.median}<br/>
                                Q3: ${stats.q3}<br/>
                                最大值: ${stats.max}<br/>
                                平均值: ${stats.mean.toFixed(2)}
                            </div>
                        `;
                    }
                },
                grid: {
                    left: '10%',
                    right: '10%',
                    bottom: '15%'
                },
                xAxis: {
                    type: 'category',
                    data: ['KDA分布'],
                    axisLabel: {
                        color: '#94a3b8'
                    },
                    axisLine: {
                        lineStyle: {
                            color: '#2d3748'
                        }
                    }
                },
                yAxis: {
                    type: 'value',
                    name: 'KDA值',
                    axisLabel: {
                        color: '#94a3b8'
                    },
                    axisLine: {
                        lineStyle: {
                            color: '#2d3748'
                        }
                    },
                    splitLine: {
                        lineStyle: {
                            color: '#2d3748'
                        }
                    }
                },
                series: [{
                    name: 'KDA',
                    type: 'boxplot',
                    data: boxplotData,
                    itemStyle: {
                        color: '#22c55e',
                        borderColor: '#16a34a'
                    }
                }]
            };
            
            chart.setOption(chartOptions);
            this.charts.set(containerId, chart);
            
            window.addEventListener('resize', () => {
                chart.resize();
            });
            
            return chart;
            
        } catch (error) {
            console.error('渲染KDA箱线图失败:', error);
        }
    }
    
    // Farm效率雷达图
    renderFarmEfficiencyRadar(containerId, data, options = {}) {
        try {
            const container = document.getElementById(containerId);
            if (!container) return;
            
            const chart = this.chartLibraries.echarts.init(container);
            
            const indicators = data.data.dimensions.map(dim => ({ name: dim, max: 1000 }));
            const seriesData = data.data.players.map(player => ({
                value: Object.values(player.metrics),
                name: player.player
            }));
            
            const chartOptions = {
                title: {
                    text: data.title || 'Farm效率雷达图',
                    left: 'center',
                    textStyle: {
                        color: '#e2e8f0'
                    }
                },
                tooltip: {
                    trigger: 'item'
                },
                legend: {
                    data: data.data.players.map(p => p.player),
                    bottom: 0,
                    textStyle: {
                        color: '#94a3b8'
                    }
                },
                radar: {
                    indicator: indicators,
                    axisName: {
                        color: '#94a3b8'
                    },
                    splitLine: {
                        lineStyle: {
                            color: '#2d3748'
                        }
                    },
                    splitArea: {
                        show: false
                    }
                },
                series: [{
                    name: 'Farm效率',
                    type: 'radar',
                    data: seriesData
                }]
            };
            
            chart.setOption(chartOptions);
            this.charts.set(containerId, chart);
            
            window.addEventListener('resize', () => {
                chart.resize();
            });
            
            return chart;
            
        } catch (error) {
            console.error('渲染Farm效率雷达图失败:', error);
        }
    }
    
    // 首杀时间趋势图
    renderFirstBloodTrend(containerId, data, options = {}) {
        try {
            const container = document.getElementById(containerId);
            if (!container) return;
            
            // 如果没有数据，显示占位符
            if (!data.data || !data.data.timeline || data.data.timeline.length === 0) {
                container.innerHTML = `
                    <div class="flex flex-col items-center justify-center h-full text-center">
                        <div class="text-ancient-500 text-4xl mb-4">📊</div>
                        <p class="text-gray-400 mb-2">首杀时间趋势</p>
                        <p class="text-sm text-gray-500">需要比赛详细事件数据支持</p>
                        <p class="text-xs text-gray-600 mt-2">即将在后续版本中提供</p>
                    </div>
                `;
                return;
            }
            
            const chart = this.chartLibraries.echarts.init(container);
            
            // 这里可以添加真实的首杀时间趋势图实现
            const chartOptions = {
                title: {
                    text: data.title || '首杀时间趋势',
                    left: 'center',
                    textStyle: {
                        color: '#e2e8f0'
                    }
                },
                // ... 图表配置
            };
            
            chart.setOption(chartOptions);
            this.charts.set(containerId, chart);
            
            return chart;
            
        } catch (error) {
            console.error('渲染首杀时间趋势图失败:', error);
        }
    }
    
    // ========== 4. 通用方法 ==========
    
    // 销毁图表
    destroyChart(containerId) {
        const chart = this.charts.get(containerId);
        if (chart) {
            chart.dispose();
            this.charts.delete(containerId);
        }
    }
    
    // 销毁所有图表
    destroyAllCharts() {
        this.charts.forEach((chart, id) => {
            chart.dispose();
        });
        this.charts.clear();
    }
    
    // 导出图表
    exportChart(containerId, type = 'png') {
        const chart = this.charts.get(containerId);
        if (!chart) return null;
        
        return chart.getDataURL({
            type: type,
            pixelRatio: 2,
            backgroundColor: '#1a1f2e'
        });
    }
    
    // 更新图表主题
    updateTheme(theme = 'dark') {
        this.charts.forEach(chart => {
            // 更新主题配置
            chart.resize();
        });
    }
}

// 全局图表管理器实例
const chartManager = new ChartManager();

// 导出供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ChartManager, chartManager };
}
