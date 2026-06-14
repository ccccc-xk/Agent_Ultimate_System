<template>
  <div class="dashboard-page">
    <!-- Welcome Banner -->
    <div class="welcome-banner">
      <div class="welcome-bg-orbs">
        <div class="orb orb-1"></div>
        <div class="orb orb-2"></div>
        <div class="orb orb-3"></div>
      </div>
      <div class="welcome-content">
        <h2 class="welcome-title">{{ greeting }}，{{ userStore.userInfo?.realName || userStore.userInfo?.username || '用户' }} <span class="wave">&#128075;</span></h2>
        <p class="welcome-desc">欢迎回到企业管理基座系统，以下是今日的企业运营概览</p>
      </div>
      <div class="welcome-right">
        <div class="welcome-date">
          <el-icon :size="16"><Calendar /></el-icon>
          <span>{{ todayStr }}</span>
        </div>
      </div>
    </div>

    <!-- Skeleton Loading -->
    <template v-if="loading">
      <div class="stat-cards">
        <div v-for="i in 4" :key="i" class="stat-card skeleton-card">
          <el-skeleton :rows="2" animated />
        </div>
      </div>
      <div class="charts-row">
        <div class="chart-card skeleton-chart"><el-skeleton :rows="6" animated /></div>
        <div class="chart-card skeleton-chart"><el-skeleton :rows="6" animated /></div>
      </div>
    </template>

    <!-- Real Content -->
    <template v-else>
      <!-- Stat Cards -->
      <div class="stat-cards">
        <div class="stat-card stat-revenue anim-fade-up anim-delay-1">
          <div class="stat-card-top-bar"></div>
          <div class="stat-card-inner">
            <div class="stat-icon-wrap">
              <div class="stat-icon">
                <el-icon :size="22"><Money /></el-icon>
              </div>
            </div>
            <div class="stat-body">
              <div class="stat-label">本月营收</div>
              <div class="stat-value">
                <span class="stat-num">{{ animatedRevenue }}</span>
                <span class="stat-unit">万元</span>
              </div>
              <div class="stat-trend" :class="summary.revenueGrowth >= 0 ? 'up' : 'down'">
                <el-icon :size="12"><component :is="summary.revenueGrowth >= 0 ? 'Top' : 'Bottom'" /></el-icon>
                {{ Math.abs(summary.revenueGrowth || 0).toFixed(1) }}%
                <span class="trend-label">同比</span>
              </div>
            </div>
          </div>
        </div>

        <div class="stat-card stat-profit anim-fade-up anim-delay-2">
          <div class="stat-card-top-bar"></div>
          <div class="stat-card-inner">
            <div class="stat-icon-wrap">
              <div class="stat-icon">
                <el-icon :size="22"><TrendCharts /></el-icon>
              </div>
            </div>
            <div class="stat-body">
              <div class="stat-label">本月利润</div>
              <div class="stat-value">
                <span class="stat-num">{{ animatedProfit }}</span>
                <span class="stat-unit">万元</span>
              </div>
              <div class="stat-trend" :class="summary.profitGrowth >= 0 ? 'up' : 'down'">
                <el-icon :size="12"><component :is="summary.profitGrowth >= 0 ? 'Top' : 'Bottom'" /></el-icon>
                {{ Math.abs(summary.profitGrowth || 0).toFixed(1) }}%
                <span class="trend-label">同比</span>
              </div>
            </div>
          </div>
        </div>

        <div class="stat-card stat-employees anim-fade-up anim-delay-3">
          <div class="stat-card-top-bar"></div>
          <div class="stat-card-inner">
            <div class="stat-icon-wrap">
              <div class="stat-icon">
                <el-icon :size="22"><User /></el-icon>
              </div>
            </div>
            <div class="stat-body">
              <div class="stat-label">员工总数</div>
              <div class="stat-value">
                <span class="stat-num">{{ summary.employeeCount || 0 }}</span>
                <span class="stat-unit">人</span>
              </div>
              <div class="stat-trend neutral">系统在册</div>
            </div>
          </div>
        </div>

        <div class="stat-card stat-cost anim-fade-up anim-delay-4">
          <div class="stat-card-top-bar"></div>
          <div class="stat-card-inner">
            <div class="stat-icon-wrap">
              <div class="stat-icon">
                <el-icon :size="22"><Coin /></el-icon>
              </div>
            </div>
            <div class="stat-body">
              <div class="stat-label">人力成本</div>
              <div class="stat-value">
                <span class="stat-num">{{ animatedCost }}</span>
                <span class="stat-unit">万元</span>
              </div>
              <div class="stat-trend neutral">本月支出</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Charts Row -->
      <div class="charts-row">
        <div class="chart-card chart-wide anim-fade-up anim-delay-3">
          <div class="chart-header">
            <div class="chart-title-area">
              <h3>月度营收趋势</h3>
              <span class="chart-subtitle">近12个月数据</span>
            </div>
            <div class="chart-legend">
              <span class="legend-item">
                <span class="legend-dot" style="background: linear-gradient(135deg, #3b82f6, #6366f1)"></span>营业额
              </span>
              <span class="legend-item">
                <span class="legend-dot" style="background: linear-gradient(135deg, #10b981, #059669)"></span>利润
              </span>
            </div>
          </div>
          <div ref="lineChartRef" class="chart-body"></div>
        </div>
        <div class="chart-card chart-narrow anim-fade-up anim-delay-4">
          <div class="chart-header">
            <div class="chart-title-area">
              <h3>利润与成本对比</h3>
              <span class="chart-subtitle">近6个月</span>
            </div>
          </div>
          <div ref="barChartRef" class="chart-body"></div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import request from '@/utils/request'
import { useUserStore } from '@/store/user'
import * as echarts from 'echarts'

const userStore = useUserStore()
const loading = ref(true)

const summary = reactive({
  currentRevenue: 0,
  currentProfit: 0,
  currentLaborCost: 0,
  revenueGrowth: 0,
  profitGrowth: 0,
  employeeCount: 0,
  monthlyData: [],
})

const animatedRevenue = ref('0.00')
const animatedProfit = ref('0.00')
const animatedCost = ref('0.00')

const lineChartRef = ref(null)
const barChartRef = ref(null)
let lineChart = null
let barChart = null

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return '早上好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const todayStr = computed(() => {
  const d = new Date()
  const days = ['日', '一', '二', '三', '四', '五', '六']
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 星期${days[d.getDay()]}`
})

function animateNumber(targetRef, endVal, duration = 900) {
  const startTime = performance.now()
  function step(now) {
    const elapsed = now - startTime
    const progress = Math.min(elapsed / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    targetRef.value = (endVal * eased).toFixed(2)
    if (progress < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

async function loadSummary() {
  loading.value = true
  try {
    const res = await request.get('/api/dashboard/summary')
    const d = res.data
    summary.currentRevenue = d.currentMonthRevenue || 0
    summary.currentProfit = d.currentMonthProfit || 0
    summary.currentLaborCost = d.currentMonthLaborCost || 0
    summary.revenueGrowth = d.revenueGrowthRate || 0
    summary.profitGrowth = d.profitGrowthRate || 0
    summary.employeeCount = d.totalEmployees || 0
    summary.monthlyData = d.trends || []
    loading.value = false
    await nextTick()
    animateNumber(animatedRevenue, summary.currentRevenue || 0)
    animateNumber(animatedProfit, summary.currentProfit || 0)
    animateNumber(animatedCost, summary.currentLaborCost || 0)
    renderCharts()
  } catch (e) {
    loading.value = false
    console.error('Failed to load dashboard', e)
  }
}

function renderCharts() {
  const data = summary.monthlyData || []
  if (!data.length) return

  if (lineChartRef.value) {
    lineChart = echarts.init(lineChartRef.value)
    lineChart.setOption({
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255,255,255,0.98)',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        textStyle: { color: '#1e293b', fontSize: 13 },
        axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(59, 130, 246, 0.04)' } },
        padding: [12, 16],
        extraCssText: 'border-radius: 10px; box-shadow: 0 8px 24px rgba(0,0,0,0.08);',
      },
      grid: { top: 20, right: 20, bottom: 32, left: 52 },
      xAxis: {
        type: 'category',
        data: data.map(d => d.month),
        axisLine: { lineStyle: { color: '#e5e7eb' } },
        axisLabel: { color: '#94a3b8', fontSize: 11 },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        name: '万元',
        nameLocation: 'end',
        nameTextStyle: { color: '#94a3b8', fontSize: 11, padding: [0, 0, 0, 0] },
        axisLine: { show: false },
        splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
        axisLabel: { color: '#94a3b8', fontSize: 11, formatter: '{value}' },
      },
      series: [
        {
          name: '营业额',
          type: 'line',
          data: data.map(d => d.revenue),
          smooth: true,
          symbol: 'circle',
          symbolSize: 7,
          lineStyle: { width: 2.5, color: '#3b82f6' },
          itemStyle: { color: '#3b82f6', borderWidth: 2, borderColor: '#fff' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(59, 130, 246, 0.15)' },
              { offset: 1, color: 'rgba(59, 130, 246, 0.01)' },
            ]),
          },
        },
        {
          name: '利润',
          type: 'line',
          data: data.map(d => d.profit),
          smooth: true,
          symbol: 'circle',
          symbolSize: 7,
          lineStyle: { width: 2.5, color: '#10b981' },
          itemStyle: { color: '#10b981', borderWidth: 2, borderColor: '#fff' },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(16, 185, 129, 0.12)' },
              { offset: 1, color: 'rgba(16, 185, 129, 0.01)' },
            ]),
          },
        },
      ],
      legend: { show: false },
      animationDuration: 1200,
      animationEasing: 'cubicOut',
    })
  }

  if (barChartRef.value) {
    const recent = data.slice(-6)
    barChart = echarts.init(barChartRef.value)
    barChart.setOption({
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255,255,255,0.98)',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        textStyle: { color: '#1e293b', fontSize: 13 },
        padding: [12, 16],
        extraCssText: 'border-radius: 10px; box-shadow: 0 8px 24px rgba(0,0,0,0.08);',
      },
      grid: { top: 20, right: 20, bottom: 40, left: 52 },
      xAxis: {
        type: 'category',
        data: recent.map(d => d.month),
        axisLine: { lineStyle: { color: '#e5e7eb' } },
        axisLabel: { color: '#94a3b8', fontSize: 11 },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        name: '万元',
        nameLocation: 'end',
        nameTextStyle: { color: '#94a3b8', fontSize: 11, padding: [0, 0, 0, 0] },
        axisLine: { show: false },
        splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
        axisLabel: { color: '#94a3b8', fontSize: 11, formatter: '{value}' },
      },
      series: [
        {
          name: '利润',
          type: 'bar',
          data: recent.map(d => d.profit),
          barWidth: 16,
          itemStyle: {
            borderRadius: [5, 5, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#3b82f6' },
              { offset: 1, color: '#6366f1' },
            ]),
          },
        },
        {
          name: '人力成本',
          type: 'bar',
          data: recent.map(d => d.laborCost),
          barWidth: 16,
          itemStyle: {
            borderRadius: [5, 5, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#f59e0b' },
              { offset: 1, color: '#f97316' },
            ]),
          },
        },
      ],
      legend: {
        data: ['利润', '人力成本'],
        bottom: 0,
        textStyle: { color: '#94a3b8', fontSize: 11 },
        itemWidth: 10,
        itemHeight: 10,
        itemGap: 20,
        icon: 'roundRect',
      },
      animationDuration: 1000,
      animationEasing: 'cubicOut',
    })
  }
}

function handleResize() {
  lineChart?.resize()
  barChart?.resize()
}

onMounted(() => {
  loadSummary()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  lineChart?.dispose()
  barChart?.dispose()
})
</script>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ======== Welcome Banner ======== */
.welcome-banner {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 40%, #1e1b4b 100%);
  border-radius: var(--radius-lg);
  padding: 28px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  overflow: hidden;
  min-height: 100px;
}
.welcome-bg-orbs {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}
.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(40px);
}
.orb-1 {
  width: 200px;
  height: 200px;
  background: rgba(59, 130, 246, 0.12);
  top: -60px;
  right: -20px;
  animation: orbFloat 8s ease-in-out infinite;
}
.orb-2 {
  width: 160px;
  height: 160px;
  background: rgba(99, 102, 241, 0.1);
  bottom: -40px;
  left: 30%;
  animation: orbFloat 10s ease-in-out infinite reverse;
}
.orb-3 {
  width: 120px;
  height: 120px;
  background: rgba(139, 92, 246, 0.08);
  top: 20%;
  left: -30px;
  animation: orbFloat 12s ease-in-out infinite;
}
@keyframes orbFloat {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(15px, -10px) scale(1.05); }
  66% { transform: translate(-10px, 8px) scale(0.95); }
}
.welcome-content {
  position: relative;
  z-index: 1;
}
.welcome-title {
  font-size: 20px;
  font-weight: 700;
  color: #f1f5f9;
  margin: 0 0 8px;
  letter-spacing: -0.3px;
}
.wave {
  display: inline-block;
  animation: waveHand 2.5s ease-in-out 1;
  transform-origin: 70% 70%;
}
@keyframes waveHand {
  0%, 100% { transform: rotate(0deg); }
  10% { transform: rotate(14deg); }
  20% { transform: rotate(-8deg); }
  30% { transform: rotate(14deg); }
  40% { transform: rotate(-4deg); }
  50% { transform: rotate(0deg); }
}
.welcome-desc {
  font-size: 13px;
  color: #94a3b8;
  margin: 0;
}
.welcome-right {
  position: relative;
  z-index: 1;
}
.welcome-date {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #94a3b8;
  font-size: 13px;
  background: rgba(255, 255, 255, 0.06);
  padding: 10px 18px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(8px);
}

/* ======== Stat Cards ======== */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: var(--bg-card);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  border: 1px solid rgba(0, 0, 0, 0.03);
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}
.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: rgba(0, 0, 0, 0.06);
}
.stat-card-top-bar {
  height: 3px;
  width: 100%;
}
.stat-revenue .stat-card-top-bar {
  background: linear-gradient(90deg, #3b82f6, #6366f1);
}
.stat-profit .stat-card-top-bar {
  background: linear-gradient(90deg, #10b981, #059669);
}
.stat-employees .stat-card-top-bar {
  background: linear-gradient(90deg, #8b5cf6, #7c3aed);
}
.stat-cost .stat-card-top-bar {
  background: linear-gradient(90deg, #f59e0b, #f97316);
}
.stat-card-inner {
  padding: 22px 24px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.stat-icon-wrap {
  flex-shrink: 0;
}
.stat-icon {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  transition: all var(--transition-normal);
}
.stat-card:hover .stat-icon {
  transform: scale(1.1);
}
.stat-revenue .stat-icon { background: linear-gradient(135deg, #3b82f6, #2563eb); box-shadow: 0 4px 14px rgba(59, 130, 246, 0.25); }
.stat-profit .stat-icon { background: linear-gradient(135deg, #10b981, #059669); box-shadow: 0 4px 14px rgba(16, 185, 129, 0.25); }
.stat-employees .stat-icon { background: linear-gradient(135deg, #8b5cf6, #7c3aed); box-shadow: 0 4px 14px rgba(139, 92, 246, 0.25); }
.stat-cost .stat-icon { background: linear-gradient(135deg, #f59e0b, #d97706); box-shadow: 0 4px 14px rgba(245, 158, 11, 0.25); }

.stat-body {
  flex: 1;
  min-width: 0;
}
.stat-label {
  font-size: 12px;
  color: var(--text-light);
  margin-bottom: 8px;
  font-weight: 500;
  letter-spacing: 0.3px;
}
.stat-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
}
.stat-num {
  font-size: 26px;
  font-weight: 800;
  color: var(--text-primary);
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.5px;
}
.stat-unit {
  font-size: 13px;
  font-weight: 400;
  color: var(--text-light);
}
.stat-trend {
  margin-top: 10px;
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 6px;
}
.stat-trend.up {
  color: #059669;
  background: rgba(16, 185, 129, 0.08);
}
.stat-trend.down {
  color: #dc2626;
  background: rgba(239, 68, 68, 0.08);
}
.stat-trend.neutral {
  color: var(--text-light);
  background: #f1f5f9;
}
.trend-label {
  font-weight: 400;
  opacity: 0.7;
}

/* Skeleton */
.skeleton-card {
  min-height: 120px;
  padding: 24px;
}
.skeleton-chart {
  min-height: 340px;
}

/* ======== Charts ======== */
.charts-row {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 16px;
}

.chart-card {
  background: var(--bg-card);
  border-radius: var(--radius-md);
  padding: 24px;
  box-shadow: var(--shadow-sm);
  border: 1px solid rgba(0, 0, 0, 0.03);
  transition: all var(--transition-normal);
}
.chart-card:hover {
  box-shadow: var(--shadow-md);
}
.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}
.chart-title-area h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 3px;
}
.chart-subtitle {
  font-size: 11px;
  color: var(--text-light);
}
.chart-legend {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 12px;
  color: var(--text-muted);
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.legend-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 3px;
}
.chart-body {
  width: 100%;
  height: 280px;
}

/* ======== Responsive ======== */
@media (max-width: 1200px) {
  .stat-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  .charts-row {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 640px) {
  .stat-cards {
    grid-template-columns: 1fr;
  }
  .welcome-banner {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
}
</style>
