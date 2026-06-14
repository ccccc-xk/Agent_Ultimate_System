<template>
  <div class="report-page">
    <div class="page-header">
      <h2 class="page-title">财务报表</h2>
      <p class="page-desc">查看和管理企业月度财务数据，支持AI智能分析</p>
    </div>

    <!-- Summary Stats -->
    <div class="summary-stats">
      <div class="mini-stat anim-fade-up anim-delay-1">
        <div class="mini-icon" style="background: linear-gradient(135deg, #3b82f6, #2563eb)">
          <el-icon :size="16" color="#fff"><Document /></el-icon>
        </div>
        <div class="mini-body">
          <span class="mini-label">记录总数</span>
          <span class="mini-value">{{ total }}</span>
        </div>
      </div>
      <div class="mini-stat anim-fade-up anim-delay-2">
        <div class="mini-icon" style="background: linear-gradient(135deg, #10b981, #059669)">
          <el-icon :size="16" color="#fff"><Money /></el-icon>
        </div>
        <div class="mini-body">
          <span class="mini-label">总营业额</span>
          <span class="mini-value">{{ totalRevenue }} 万</span>
        </div>
      </div>
      <div class="mini-stat anim-fade-up anim-delay-3">
        <div class="mini-icon" style="background: linear-gradient(135deg, #8b5cf6, #7c3aed)">
          <el-icon :size="16" color="#fff"><TrendCharts /></el-icon>
        </div>
        <div class="mini-body">
          <span class="mini-label">总利润</span>
          <span class="mini-value" :class="totalProfitVal >= 0 ? 'text-success' : 'text-danger'">{{ totalProfit }} 万</span>
        </div>
      </div>
      <div class="mini-stat anim-fade-up anim-delay-4">
        <div class="mini-icon" style="background: linear-gradient(135deg, #f59e0b, #d97706)">
          <el-icon :size="16" color="#fff"><Coin /></el-icon>
        </div>
        <div class="mini-body">
          <span class="mini-label">平均利润率</span>
          <span class="mini-value">{{ avgProfitRate }}%</span>
        </div>
      </div>
    </div>

    <div class="content-layout">
      <!-- Left: Table -->
      <div class="table-section">
        <div class="section-card">
          <div class="card-toolbar">
            <div class="toolbar-left">
              <el-input
                v-model="searchMonth"
                placeholder="搜索月份，如 2024-01"
                prefix-icon="Search"
                clearable
                style="width: 220px"
                @clear="loadData"
                @keyup.enter="loadData"
              />
            </div>
            <div class="toolbar-right">
              <el-button type="primary" @click="loadData">
                <el-icon><Search /></el-icon>查询
              </el-button>
              <el-button type="warning" @click="showImportDialog = true">
                <el-icon><Upload /></el-icon>导入
              </el-button>
              <el-button @click="downloadTemplate">
                <el-icon><Download /></el-icon>模板
              </el-button>
              <el-button type="success" @click="openDialog()">
                <el-icon><Plus /></el-icon>新增
              </el-button>
            </div>
          </div>

          <el-table :data="tableData" stripe class="data-table" v-loading="tableLoading">
            <el-table-column prop="month" label="月份" min-width="110">
              <template #default="{ row }">
                <span class="cell-mono">{{ row.month }}</span>
              </template>
            </el-table-column>
            <el-table-column label="营业额(万)" min-width="120" align="right">
              <template #default="{ row }">
                <span class="cell-number">{{ Number(row.revenue).toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="利润(万)" min-width="110" align="right">
              <template #default="{ row }">
                <span class="cell-number" :class="row.profit >= 0 ? 'text-success' : 'text-danger'">
                  {{ Number(row.profit).toFixed(2) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="人力成本(万)" min-width="120" align="right">
              <template #default="{ row }">
                <span class="cell-number">{{ Number(row.laborCost).toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="利润率" min-width="100" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="row.revenue > 0 && (row.profit / row.revenue) > 0.1 ? 'success' : 'warning'"
                  size="small"
                  round
                  effect="light"
                >
                  {{ row.revenue > 0 ? ((row.profit / row.revenue) * 100).toFixed(1) : '0.0' }}%
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="130" align="center">
              <template #default="{ row }">
                <div class="action-btns">
                  <el-button link type="primary" @click="openDialog(row)">
                    <el-icon><Edit /></el-icon>编辑
                  </el-button>
                  <el-button link type="danger" @click="handleDelete(row)">
                    <el-icon><Delete /></el-icon>删除
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-wrap">
            <el-pagination
              v-model:current-page="pageNum"
              v-model:page-size="pageSize"
              :total="total"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              background
              @current-change="loadData"
              @size-change="loadData"
            />
          </div>
        </div>
      </div>

      <!-- Right: AI Summary -->
      <div class="ai-section">
        <div class="section-card ai-card">
          <div class="ai-header">
            <div class="ai-icon">
              <el-icon :size="20"><MagicStick /></el-icon>
            </div>
            <div>
              <h3 class="ai-title">AI 智能财务摘要</h3>
              <p class="ai-desc">基于财务数据生成运营风险提示</p>
            </div>
          </div>

          <div class="ai-form">
            <el-select v-model="aiMonth" placeholder="选择月份" style="width: 100%" size="large">
              <el-option v-for="item in tableData" :key="item.month" :label="item.month" :value="item.month" />
            </el-select>
            <el-button
              type="primary"
              :loading="aiLoading"
              size="large"
              class="ai-btn"
              @click="generateAiSummary"
            >
              <el-icon v-if="!aiLoading"><MagicStick /></el-icon>
              {{ aiLoading ? 'AI 分析中...' : '生成 AI 摘要' }}
            </el-button>
          </div>

          <transition name="fade-slide">
            <div v-if="aiResult" class="ai-result">
              <div class="ai-result-header">
                <el-icon :size="14"><MagicStick /></el-icon>
                <span>分析结果</span>
              </div>
              <div class="ai-result-text">{{ aiResult }}</div>
            </div>
            <div v-else class="ai-empty">
              <div class="ai-empty-icon">
                <el-icon :size="28"><MagicStick /></el-icon>
              </div>
              <p>选择月份后点击生成</p>
              <p class="ai-empty-hint">AI 将自动分析该月财务数据</p>
            </div>
          </transition>
        </div>
      </div>
    </div>

    <!-- Import Dialog -->
    <el-dialog v-model="showImportDialog" title="导入财务数据" width="500px" :close-on-click-modal="false">
      <div class="import-dialog-body">
        <div class="import-explain">
          <el-icon :size="20" color="#3b82f6"><InfoFilled /></el-icon>
          <div>
            <p class="import-tip">支持 .xlsx / .xls 格式，表头需包含：月份、营业额(万元)、利润(万元)、人力成本(万元)</p>
            <p class="import-hint">可先下载模板填写后导入，已存在的月份数据将被覆盖更新</p>
          </div>
        </div>
        <el-upload
          ref="uploadRef"
          class="import-upload"
          drag
          :auto-upload="false"
          :limit="1"
          accept=".xlsx,.xls"
          :on-change="handleFileChange"
          :on-exceed="handleExceed"
        >
          <div class="upload-inner">
            <el-icon :size="40" color="#c0c4cc"><Upload /></el-icon>
            <p class="upload-text">将文件拖到此处，或<em>点击上传</em></p>
            <p class="upload-hint">仅支持 .xlsx / .xls 文件</p>
          </div>
        </el-upload>
        <div v-if="importResult" class="import-result" :class="importResult.success ? 'success' : 'error'">
          <el-icon :size="16"><component :is="importResult.success ? 'CircleCheckFilled' : 'CircleCloseFilled'" /></el-icon>
          <span>{{ importResult.message }}</span>
        </div>
      </div>
      <template #footer>
        <el-button @click="closeImportDialog">取消</el-button>
        <el-button type="primary" :loading="importLoading" :disabled="!importFile" @click="submitImport">
          确认导入
        </el-button>
      </template>
    </el-dialog>

    <!-- Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑财务数据' : '新增财务数据'"
      width="480px"
    >
      <el-form ref="dialogFormRef" :model="dialogForm" :rules="dialogRules" label-width="100px">
        <el-form-item label="月份" prop="month">
          <el-date-picker
            v-model="dialogForm.month"
            type="month"
            value-format="YYYY-MM"
            placeholder="选择月份"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="营业额(万)" prop="revenue">
          <el-input-number v-model="dialogForm.revenue" :precision="2" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="利润(万)" prop="profit">
          <el-input-number v-model="dialogForm.profit" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="人力成本(万)" prop="laborCost">
          <el-input-number v-model="dialogForm.laborCost" :precision="2" :min="0" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import request from '@/utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'

const tableData = ref([])
const tableLoading = ref(false)
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)
const searchMonth = ref('')

const aiMonth = ref('')
const aiResult = ref('')
const aiLoading = ref(false)

const dialogVisible = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const dialogFormRef = ref()
const dialogForm = reactive({ id: null, month: '', revenue: 0, profit: 0, laborCost: 0 })
const dialogRules = {
  month: [{ required: true, message: '请选择月份', trigger: 'change' }],
  revenue: [{ required: true, message: '请输入营业额', trigger: 'blur' }],
}

const totalRevenueVal = computed(() => tableData.value.reduce((s, r) => s + Number(r.revenue || 0), 0))
const totalRevenue = computed(() => totalRevenueVal.value.toFixed(2))
const totalProfitVal = computed(() => tableData.value.reduce((s, r) => s + Number(r.profit || 0), 0))
const totalProfit = computed(() => totalProfitVal.value.toFixed(2))
const avgProfitRate = computed(() => {
  if (!tableData.value.length) return '0.0'
  const rates = tableData.value.map(r => r.revenue > 0 ? (r.profit / r.revenue) * 100 : 0)
  return (rates.reduce((s, r) => s + r, 0) / rates.length).toFixed(1)
})

async function loadData() {
  tableLoading.value = true
  try {
    const res = await request.get('/api/finance/page', {
      params: { pageNum: pageNum.value, pageSize: pageSize.value, month: searchMonth.value || undefined },
    })
    tableData.value = res.data.records
    total.value = res.data.total
  } finally {
    tableLoading.value = false
  }
}

function openDialog(row) {
  isEdit.value = !!row
  if (row) {
    Object.assign(dialogForm, row)
  } else {
    Object.assign(dialogForm, { id: null, month: '', revenue: 0, profit: 0, laborCost: 0 })
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await dialogFormRef.value.validate().catch(() => false)
  if (!valid) return
  submitLoading.value = true
  try {
    if (isEdit.value) {
      await request.put('/api/finance', dialogForm)
    } else {
      await request.post('/api/finance', dialogForm)
    }
    ElMessage.success(isEdit.value ? '编辑成功' : '新增成功')
    dialogVisible.value = false
    loadData()
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm('确认删除该条财务数据？', '提示', { type: 'warning' })
  await request.delete(`/api/finance/${row.id}`)
  ElMessage.success('删除成功')
  loadData()
}

async function generateAiSummary() {
  if (!aiMonth.value) {
    ElMessage.warning('请先选择月份')
    return
  }
  aiLoading.value = true
  aiResult.value = ''
  try {
    const res = await request.post(`/api/finance/ai-summary?month=${aiMonth.value}`)
    aiResult.value = res.data
  } finally {
    aiLoading.value = false
  }
}


// ======== Import ========
const showImportDialog = ref(false)
const importFile = ref(null)
const importLoading = ref(false)
const importResult = ref(null)
const uploadRef = ref(null)

function handleFileChange(file) {
  importFile.value = file.raw
  importResult.value = null
}

function handleExceed() {
  ElMessage.warning('只能选择一个文件')
}

async function downloadTemplate() {
  try {
    const token = localStorage.getItem('token')
    const response = await fetch('/api/finance/template', {
      headers: { 'Authorization': 'Bearer ' + token }
    })
    if (!response.ok) throw new Error('下载失败')
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = '财务数据导入模板.xlsx'
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('模板下载成功')
  } catch (e) {
    ElMessage.error('模板下载失败: ' + e.message)
  }
}

async function submitImport() {
  if (!importFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  importLoading.value = true
  importResult.value = null
  try {
    const formData = new FormData()
    formData.append('file', importFile.value)
    const res = await request.post('/api/finance/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    importResult.value = { success: true, message: res.data }
    ElMessage.success(res.data)
    loadData()
  } catch (e) {
    importResult.value = { success: false, message: e.message || '导入失败' }
  } finally {
    importLoading.value = false
  }
}

function closeImportDialog() {
  showImportDialog.value = false
  importFile.value = null
  importResult.value = null
  if (uploadRef.value) uploadRef.value.clearFiles()
}
onMounted(loadData)
</script>

<style scoped>
.report-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.page-header {
  margin-bottom: 0;
}

/* Summary Stats */
.summary-stats {
  display: flex;
  gap: 14px;
}
.mini-stat {
  flex: 1;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  padding: 16px 18px;
  box-shadow: var(--shadow-sm);
  display: flex;
  align-items: center;
  gap: 14px;
  border: 1px solid rgba(0, 0, 0, 0.03);
  transition: all var(--transition-normal);
}
.mini-stat:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
.mini-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.mini-body {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.mini-label {
  font-size: 11px;
  color: var(--text-light);
  font-weight: 500;
  letter-spacing: 0.3px;
}
.mini-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}
.text-success { color: var(--success) !important; }
.text-danger { color: var(--danger) !important; }

/* Layout */
.content-layout {
  display: flex;
  gap: 16px;
}
.table-section {
  flex: 1;
  min-width: 0;
}
.ai-section {
  width: 340px;
  flex-shrink: 0;
}

.section-card {
  background: var(--bg-card);
  border-radius: var(--radius-md);
  padding: 20px;
  box-shadow: var(--shadow-sm);
  border: 1px solid rgba(0, 0, 0, 0.03);
  transition: all var(--transition-normal);
}
.section-card:hover {
  box-shadow: var(--shadow-md);
}
.card-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.toolbar-right {
  display: flex;
  gap: 8px;
}

.cell-mono {
  font-family: 'SF Mono', 'Consolas', monospace;
  font-size: 13px;
  color: var(--text-secondary);
}
.cell-number {
  font-family: 'SF Mono', 'Consolas', monospace;
  font-size: 13px;
  color: var(--text-primary);
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* AI Section */
.ai-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}
.ai-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #8b5cf6, #6366f1, #3b82f6);
  background-size: 200% 100%;
  animation: gradientShift 3s ease infinite;
}
@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
.ai-header {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 24px;
  padding-top: 4px;
}
.ai-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.3);
}
.ai-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
.ai-desc {
  font-size: 12px;
  color: var(--text-light);
  margin: 3px 0 0;
}

.ai-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}
.ai-btn {
  width: 100%;
  border-radius: 10px;
  background: linear-gradient(135deg, #8b5cf6, #6366f1) !important;
  border: none !important;
  font-weight: 600;
  transition: all var(--transition-normal);
  height: 42px;
}
.ai-btn:hover {
  background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.35) !important;
}

.ai-result {
  flex: 1;
  background: linear-gradient(135deg, #faf5ff, #f5f3ff);
  border-radius: 10px;
  padding: 18px;
  border: 1px solid #ede9fe;
  animation: fadeInUp 0.3s ease-out;
}
.ai-result-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #7c3aed;
  font-weight: 600;
  margin-bottom: 10px;
}
.ai-result-text {
  font-size: 13.5px;
  color: var(--text-secondary);
  line-height: 1.9;
}

.ai-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: var(--text-light);
  font-size: 13px;
  padding: 20px 0;
}
.ai-empty-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f5f3ff, #ede9fe);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a78bfa;
  margin-bottom: 4px;
}
.ai-empty-hint {
  font-size: 11px;
  color: #c4b5fd;
  margin: 0;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 1000px) {
  .content-layout {
    flex-direction: column;
  }
  .ai-section {
    width: 100%;
  }
  .summary-stats {
    flex-wrap: wrap;
  }
  .mini-stat {
    flex: 1 1 calc(50% - 7px);
    min-width: 120px;
  }
}

/* Import Dialog */
.import-dialog-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.import-explain {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 14px 16px;
  background: #f0f9ff;
  border-radius: 8px;
  border: 1px solid #bae6fd;
}
.import-tip {
  margin: 0;
  font-size: 13px;
  color: #1e293b;
  line-height: 1.6;
}
.import-hint {
  margin: 4px 0 0;
  font-size: 12px;
  color: #64748b;
}
.import-upload {
  width: 100%;
}
.import-upload :deep(.el-upload-dragger) {
  border-radius: 10px;
  padding: 30px 20px;
}
.import-upload :deep(.el-upload) {
  width: 100%;
}
.upload-inner {
  text-align: center;
}
.upload-text {
  font-size: 14px;
  color: #606266;
  margin: 10px 0 4px;
}
.upload-text em {
  color: #409eff;
  font-style: normal;
}
.upload-hint {
  font-size: 12px;
  color: #909399;
  margin: 0;
}
.import-result {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 13px;
}
.import-result.success {
  background: #f0fdf4;
  color: #16a34a;
  border: 1px solid #bbf7d0;
}
.import-result.error {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.action-btns {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  white-space: nowrap;
}</style>
