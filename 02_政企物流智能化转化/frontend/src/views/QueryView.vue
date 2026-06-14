<template>
    <div>
        <div class="page-header">
            <div>
                <h1>智能查询</h1>
                <p class="subtitle">用自然语言查询工单数据，AI 自动生成 SQL</p>
            </div>
        </div>

        <div class="page-body">
            <!-- Query Input -->
            <div class="query-input-card">
                <div class="card-title">
                    <el-icon><ChatDotRound /></el-icon>
                    自然语言查询
                </div>
                <el-input
                    v-model="question"
                    type="textarea"
                    :rows="3"
                    placeholder="用大白话提问，例如：帮我查一下上个月所有紧急工单、最近三天新建了多少工单、哪些工单还没处理..."
                    @keydown.ctrl.enter="handleQuery"
                />
                <div class="query-actions">
                    <div class="quick-tags">
                        <el-tag
                            v-for="tag in quickTags"
                            :key="tag"
                            class="quick-tag"
                            effect="plain"
                            @click="question = tag; handleQuery()"
                        >{{ tag }}</el-tag>
                    </div>
                    <div class="query-submit">
                        <span class="shortcut-hint">Ctrl + Enter</span>
                        <el-button type="primary" :loading="queryLoading" @click="handleQuery" class="query-btn">
                            <el-icon v-if="!queryLoading"><Search /></el-icon>
                            {{ queryLoading ? 'AI 思考中...' : '查询' }}
                        </el-button>
                    </div>
                </div>
            </div>

            <!-- Query Result -->
            <div v-if="queryResult" class="content-card">
                <div class="result-header">
                    <div class="card-title" style="margin-bottom:0;">
                        <el-icon><Grid /></el-icon>
                        查询结果
                        <span class="result-count">{{ queryResult.rowCount }} 行</span>
                    </div>
                    <el-tag size="small" type="info" effect="plain" class="sql-tag">
                        {{ queryResult.sql }}
                    </el-tag>
                </div>
                <el-table
                    v-if="queryResult.rowCount > 0"
                    :data="queryResult.rows"
                    stripe
                    style="width:100%"
                    highlight-current-row
                    @row-click="showDetail"
                >
                    <el-table-column
                        v-for="col in queryResult.columns"
                        :key="col"
                        :prop="col"
                        :label="columnLabel(col)"
                        min-width="130"
                        show-overflow-tooltip
                    />
                </el-table>
                <el-empty v-else description="查询结果为空" />
            </div>

            <!-- History -->
            <div class="content-card">
                <div class="card-title">
                    <el-icon><Timer /></el-icon>
                    查询历史
                    <el-button link type="primary" size="small" @click="loadHistory" style="margin-left:auto;">
                        <el-icon><Refresh /></el-icon> 刷新
                    </el-button>
                </div>
                <el-table :data="history" stripe style="width:100%">
                    <el-table-column prop="id" label="ID" width="60" />
                    <el-table-column prop="naturalQuestion" label="问题" min-width="180" show-overflow-tooltip />
                    <el-table-column prop="generatedSql" label="生成的SQL" min-width="200" show-overflow-tooltip>
                        <template #default="{ row }">
                            <span class="sql-text">{{ row.generatedSql || '-' }}</span>
                        </template>
                    </el-table-column>
                    <el-table-column label="状态" width="80" align="center">
                        <template #default="{ row }">
                            <el-tag :type="row.status === 'SUCCESS' ? 'success' : 'danger'" size="small" effect="light">
                                {{ row.status === 'SUCCESS' ? '成功' : '失败' }}
                            </el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column prop="errorMessage" label="错误信息" min-width="140" show-overflow-tooltip />
                    <el-table-column prop="createTime" label="时间" width="160" />
                    <el-table-column label="操作" width="200" fixed="right">
                        <template #default="{ row }">
                            <el-button link type="primary" size="small" @click="viewHistoryResult(row)" :disabled="row.status !== 'SUCCESS'">
                                <el-icon><View /></el-icon> 查看
                            </el-button>
                            <el-button link type="warning" size="small" @click="openEditDialog(row)">
                                <el-icon><Edit /></el-icon> 编辑
                            </el-button>
                            <el-popconfirm
                                title="确定删除这条记录吗？"
                                confirm-button-text="删除"
                                cancel-button-text="取消"
                                @confirm="deleteHistory(row.id)"
                            >
                                <template #reference>
                                    <el-button link type="danger" size="small">
                                        <el-icon><Delete /></el-icon> 删除
                                    </el-button>
                                </template>
                            </el-popconfirm>
                        </template>
                    </el-table-column>
                </el-table>
            </div>
        </div>

        <!-- Row Detail Dialog -->
        <el-dialog v-model="detailVisible" title="行详情" width="560px" destroy-on-close>
            <el-descriptions :column="1" border v-if="detailRow">
                <el-descriptions-item
                    v-for="col in detailColumns"
                    :key="col"
                    :label="columnLabel(col)"
                >
                    <template v-if="col === 'actions_taken'">
                        <el-tag
                            v-for="(a, i) in parseActions(detailRow[col])"
                            :key="i"
                            style="margin:2px 4px 2px 0;"
                            type="info"
                            size="small"
                        >{{ a }}</el-tag>
                    </template>
                    <template v-else-if="col === 'priority'">
                        <el-tag :type="detailRow[col] === 'URGENT' ? 'danger' : 'info'" size="small">
                            {{ detailRow[col] === 'URGENT' ? '紧急' : '普通' }}
                        </el-tag>
                    </template>
                    <template v-else-if="col === 'status'">
                        <el-tag :type="statusType(detailRow[col])" size="small">
                            {{ statusLabel(detailRow[col]) }}
                        </el-tag>
                    </template>
                    <template v-else>{{ detailRow[col] }}</template>
                </el-descriptions-item>
            </el-descriptions>
        </el-dialog>

        <!-- Edit Dialog -->
        <el-dialog v-model="editVisible" title="编辑查询" width="520px" destroy-on-close>
            <div style="margin-bottom:12px;">
                <p style="font-size:13px; color:var(--c-text-3); margin-bottom:8px;">修改问题后可以重新提交查询。</p>
                <el-input
                    v-model="editQuestion"
                    type="textarea"
                    :rows="3"
                    placeholder="修改查询问题..."
                />
            </div>
            <template #footer>
                <el-button @click="editVisible = false">取消</el-button>
                <el-button @click="saveEdit" type="info">
                    <el-icon><Check /></el-icon> 仅保存
                </el-button>
                <el-button type="primary" :loading="editRerunLoading" @click="saveAndRerun">
                    <el-icon v-if="!editRerunLoading"><Search /></el-icon>
                    {{ editRerunLoading ? '重新查询中...' : '保存并重新查询' }}
                </el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { nlpQuery, getQueryHistory, deleteQueryHistory, updateQueryHistory } from '../api'

const question = ref('')
const queryLoading = ref(false)
const queryResult = ref(null)
const history = ref([])
const detailVisible = ref(false)
const detailRow = ref(null)
const detailColumns = ref([])

const editVisible = ref(false)
const editRow = ref(null)
const editQuestion = ref('')
const editRerunLoading = ref(false)

const quickTags = [
    '帮我查一下所有紧急工单',
    '最近新建了多少工单',
    '哪些工单还没处理',
    '查看所有PENDING状态的工单'
]

const labelMap = {
    id: '工单ID', location: '地点', client_name: '客户姓名',
    issue: '问题描述', actions_taken: '已采取措施', assigned_to: '指派人员',
    priority: '优先级', status: '状态', create_time: '创建时间', update_time: '更新时间'
}

function columnLabel(col) {
    return labelMap[col] || col
}

function parseActions(val) {
    if (!val) return []
    if (Array.isArray(val)) return val
    try { return JSON.parse(val) } catch { return [val] }
}

function statusType(s) {
    return { PENDING: 'warning', PROCESSING: '', DONE: 'success' }[s] || 'info'
}

function statusLabel(s) {
    return { PENDING: '待处理', PROCESSING: '处理中', DONE: '已完成' }[s] || s
}

function showDetail(row) {
    detailRow.value = row
    detailColumns.value = queryResult.value?.columns || []
    detailVisible.value = true
}

async function viewHistoryResult(row) {
    if (row.queryResult) {
        try {
            const stored = typeof row.queryResult === 'string' ? JSON.parse(row.queryResult) : row.queryResult
            queryResult.value = stored
            question.value = row.naturalQuestion || ''
            ElMessage.success('已加载存储结果，共 ' + (stored.rowCount || 0) + ' 条记录')
            document.querySelector('.page-body')?.scrollTo({ top: 0, behavior: 'smooth' })
            return
        } catch (e) {
            console.warn('存储结果解析失败，将重新查询', e)
        }
    }
    if (!row.naturalQuestion) {
        ElMessage.warning('该记录无原始问题且无存储结果')
        return
    }
    question.value = row.naturalQuestion
    ElMessage.info('存储结果不可用，正在重新执行查询...')
    await handleQuery()
    document.querySelector('.page-body')?.scrollTo({ top: 0, behavior: 'smooth' })
}

function openEditDialog(row) {
    editRow.value = row
    editQuestion.value = row.naturalQuestion || ''
    editVisible.value = true
}

async function saveEdit() {
    if (!editQuestion.value.trim()) {
        ElMessage.warning('问题不能为空')
        return
    }
    try {
        await updateQueryHistory(editRow.value.id, editQuestion.value)
        ElMessage.success('保存成功')
        editVisible.value = false
        loadHistory()
    } catch (e) {
        ElMessage.error(e.message)
    }
}

async function saveAndRerun() {
    if (!editQuestion.value.trim()) {
        ElMessage.warning('问题不能为空')
        return
    }
    editRerunLoading.value = true
    try {
        await updateQueryHistory(editRow.value.id, editQuestion.value)
        question.value = editQuestion.value
        editVisible.value = false
        await handleQuery()
    } catch (e) {
        ElMessage.error(e.message)
    } finally {
        editRerunLoading.value = false
    }
}

async function deleteHistory(id) {
    try {
        await deleteQueryHistory(id)
        ElMessage.success('删除成功')
        loadHistory()
    } catch (e) {
        ElMessage.error(e.message)
    }
}

async function handleQuery() {
    if (!question.value.trim()) {
        ElMessage.warning('请输入查询问题')
        return
    }
    queryLoading.value = true
    try {
        const res = await nlpQuery(question.value)
        queryResult.value = res.data
        if (res.data.rowCount > 0) {
            ElMessage.success(`查询完成，共 ${res.data.rowCount} 条结果，点击行查看详情`)
        } else {
            ElMessage.info('查询完成，没有匹配的结果')
        }
        loadHistory()
    } catch (e) {
        ElMessage.error(e.message)
    } finally {
        queryLoading.value = false
    }
}

async function loadHistory() {
    try {
        const res = await getQueryHistory(20)
        history.value = res.data || []
    } catch {
        // silent
    }
}

onMounted(loadHistory)
</script>

<style scoped>
.query-input-card {
    background: var(--c-surface);
    border-radius: var(--radius-lg);
    padding: 20px 24px;
    box-shadow: var(--shadow-xs);
    border: 1px solid var(--c-border);
    margin-bottom: 16px;
}

.query-actions {
    margin-top: 12px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.quick-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    flex: 1;
}

.quick-tag {
    cursor: pointer;
    transition: all 0.2s;
    border-radius: var(--radius-xs);
    font-size: 12px;
}

.quick-tag:hover {
    color: var(--c-primary) !important;
    border-color: var(--c-primary) !important;
    background: var(--c-primary-light) !important;
}

.query-submit {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
}

.shortcut-hint {
    font-size: 11px;
    color: var(--c-text-3);
    background: var(--c-bg);
    padding: 2px 8px;
    border-radius: var(--radius-xs);
    font-family: monospace;
    white-space: nowrap;
}

.query-btn {
    min-width: 90px;
}

.result-header {
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}

.result-count {
    font-size: 11px;
    font-weight: 600;
    color: var(--c-success);
    background: var(--c-success-light);
    padding: 1px 8px;
    border-radius: 10px;
    margin-left: 4px;
}

.sql-tag {
    font-family: 'SF Mono', 'Fira Code', monospace;
    font-size: 11px;
    max-width: 400px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.sql-text {
    font-family: 'SF Mono', 'Fira Code', monospace;
    font-size: 12px;
    color: var(--c-text-2);
}
</style>
