<template>
    <div>
        <!-- Page Header -->
        <div class="page-header">
            <div>
                <h1>工单管理</h1>
                <p class="subtitle">口语化智能派单，实时工单追踪</p>
            </div>
            <el-button type="primary" @click="showDispatchDialog = true" class="header-action">
                <el-icon style="margin-right:5px;"><Plus /></el-icon>
                口语化派单
            </el-button>
        </div>

        <div class="page-body">
            <!-- Stat Cards -->
            <div class="stat-row">
                <div class="stat-card">
                    <div class="stat-icon pending"><el-icon><Clock /></el-icon></div>
                    <div class="stat-info">
                        <div class="num">{{ stats.pending }}</div>
                        <div class="label">待处理</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon processing"><el-icon><Loading /></el-icon></div>
                    <div class="stat-info">
                        <div class="num">{{ stats.processing }}</div>
                        <div class="label">处理中</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon done"><el-icon><CircleCheckFilled /></el-icon></div>
                    <div class="stat-info">
                        <div class="num">{{ stats.done }}</div>
                        <div class="label">已完成</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon urgent"><el-icon><WarningFilled /></el-icon></div>
                    <div class="stat-info">
                        <div class="num">{{ stats.urgent }}</div>
                        <div class="label">紧急工单</div>
                    </div>
                </div>
            </div>

            <!-- Filter Bar -->
            <div class="filter-bar">
                <el-form :inline="true" :model="filters" @submit.prevent="loadOrders">
                    <el-form-item label="状态" style="margin-bottom:0;">
                        <el-select v-model="filters.status" clearable placeholder="全部状态" style="width:130px">
                            <el-option label="待处理" value="PENDING" />
                            <el-option label="处理中" value="PROCESSING" />
                            <el-option label="已完成" value="DONE" />
                        </el-select>
                    </el-form-item>
                    <el-form-item label="优先级" style="margin-bottom:0;">
                        <el-select v-model="filters.priority" clearable placeholder="全部" style="width:120px">
                            <el-option label="紧急" value="URGENT" />
                            <el-option label="普通" value="NORMAL" />
                        </el-select>
                    </el-form-item>
                    <el-form-item style="margin-bottom:0;">
                        <el-button type="primary" @click="loadOrders">
                            <el-icon><Search /></el-icon>
                            查询
                        </el-button>
                    </el-form-item>
                </el-form>
            </div>

            <!-- Work Order Table -->
            <div class="content-card">
                <div class="card-title">
                    <el-icon><List /></el-icon>
                    工单列表
                    <span class="card-count">{{ pagination.total }}</span>
                </div>
                <el-table :data="orders" stripe v-loading="loading" style="width:100%">
                    <el-table-column prop="id" label="ID" width="60" />
                    <el-table-column prop="location" label="地点" min-width="120" show-overflow-tooltip />
                    <el-table-column prop="clientName" label="客户" width="100" />
                    <el-table-column prop="issue" label="问题描述" min-width="160" show-overflow-tooltip />
                    <el-table-column prop="assignedTo" label="指派人员" width="110" />
                    <el-table-column label="优先级" width="80" align="center">
                        <template #default="{ row }">
                            <el-tag
                                :type="row.priority === 'URGENT' ? 'danger' : 'info'"
                                size="small"
                                :effect="row.priority === 'URGENT' ? 'dark' : 'light'"
                            >
                                {{ row.priority === 'URGENT' ? '紧急' : '普通' }}
                            </el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column label="状态" width="90" align="center">
                        <template #default="{ row }">
                            <el-tag :type="statusType(row.status)" size="small" effect="light">
                                {{ statusLabel(row.status) }}
                            </el-tag>
                        </template>
                    </el-table-column>
                    <el-table-column prop="createTime" label="创建时间" width="160" />
                    <el-table-column label="操作" width="280" fixed="right">
                        <template #default="{ row }">
                            <el-button link type="primary" size="small" @click="showDetail(row)">
                                <el-icon><View /></el-icon> 详情
                            </el-button>
                            <el-button
                                v-if="row.status === 'PENDING'"
                                link type="warning" size="small"
                                @click="changeStatus(row.id, 'PROCESSING')"
                            >
                                <el-icon><VideoPlay /></el-icon> 开始处理
                            </el-button>
                            <el-button
                                v-if="row.status === 'PROCESSING'"
                                link type="success" size="small"
                                @click="changeStatus(row.id, 'DONE')"
                            >
                                <el-icon><CircleCheck /></el-icon> 完成
                            </el-button>

                            <el-button
                                
                                link type="info" size="small"
                                @click="openEditActions(row)"
                            >
                                <el-icon><Edit /></el-icon> 编辑
                            </el-button>
                            <el-popconfirm
                                title="确定要删除这条工单吗？"
                                confirm-button-text="删除"
                                cancel-button-text="取消"
                                @confirm="handleDelete(row.id)"
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

                <div class="pagination-wrap">
                    <el-pagination
                        v-model:current-page="pagination.page"
                        v-model:page-size="pagination.size"
                        :total="pagination.total"
                        :page-sizes="[10, 20, 50]"
                        layout="total, sizes, prev, pager, next"
                        @current-change="loadOrders"
                        @size-change="loadOrders"
                    />
                </div>
            </div>
        </div>

        <!-- Detail Dialog -->
        <el-dialog v-model="showDetailDialog" title="工单详情" width="580px">
            <el-descriptions v-if="detailOrder" :column="2" border>
                <el-descriptions-item label="ID" :span="1">{{ detailOrder.id }}</el-descriptions-item>
                <el-descriptions-item label="创建时间" :span="1">{{ detailOrder.createTime }}</el-descriptions-item>
                <el-descriptions-item label="地点" :span="1">{{ detailOrder.location || '-' }}</el-descriptions-item>
                <el-descriptions-item label="客户" :span="1">{{ detailOrder.clientName || '-' }}</el-descriptions-item>
                <el-descriptions-item label="问题描述" :span="2">{{ detailOrder.issue || '-' }}</el-descriptions-item>
                <el-descriptions-item label="已采取措施" :span="2">
                    <template v-if="detailOrder.actionsTaken?.length">
                        <el-tag v-for="(a, i) in detailOrder.actionsTaken" :key="i" size="small" style="margin:2px" type="info">{{ a }}</el-tag>
                    </template>
                    <span v-else style="color:var(--c-text-3)">-</span>
                </el-descriptions-item>
                <el-descriptions-item label="指派人员" :span="1">{{ detailOrder.assignedTo || '-' }}</el-descriptions-item>
                <el-descriptions-item label="优先级" :span="1">
                    <el-tag :type="detailOrder.priority === 'URGENT' ? 'danger' : 'info'" size="small" :effect="detailOrder.priority === 'URGENT' ? 'dark' : 'light'">
                        {{ detailOrder.priority === 'URGENT' ? '紧急' : '普通' }}
                    </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="状态" :span="1">
                    <el-tag :type="statusType(detailOrder.status)" size="small">
                        {{ statusLabel(detailOrder.status) }}
                    </el-tag>
                </el-descriptions-item>
            </el-descriptions>
        </el-dialog>

        <!-- Dispatch Dialog -->
        <el-dialog v-model="showDispatchDialog" title="口语化智能派单" width="620px">
            <div class="dispatch-tip">
                <el-icon style="margin-right:6px; vertical-align:middle;"><InfoFilled /></el-icon>
                用日常口语描述事件，AI 会自动提取地点、故障、人员等信息并生成工单。
            </div>
            <el-input
                v-model="dispatchText"
                type="textarea"
                :rows="5"
                placeholder="例如：刚才5点左右，3号楼202房间的张大爷说电风扇坏了，天气太热了，我已经拿了冰块过去，通知了维修部小王赶紧去看看。"
            />
            <template #footer>
                <el-button @click="showDispatchDialog = false">取消</el-button>
                <el-button type="primary" :loading="dispatchLoading" @click="handleDispatch">
                    <el-icon v-if="!dispatchLoading"><MagicStick /></el-icon>
                    {{ dispatchLoading ? 'AI 分析中...' : 'AI 智能派单' }}
                </el-button>
            </template>
        </el-dialog>
        
                <!-- 编辑工单弹窗 -->
        <el-dialog v-model="editActionsVisible" title="编辑工单信息" width="620px">
            <div v-if="editingOrder" style="display:flex; flex-direction:column; gap:18px;">
                <div style="padding:12px 16px; background:var(--c-bg); border-radius:var(--radius-md); font-size:13px; color:var(--c-text-2);">
                    <strong style="color:var(--c-text-1);">工单 #{{ editingOrder.id }}</strong>
                </div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
                    <div>
                        <label class="edit-label">地点</label>
                        <el-input v-model="editingForm.location" placeholder="例如：3号楼202房间" />
                    </div>
                    <div>
                        <label class="edit-label">客户</label>
                        <el-input v-model="editingForm.clientName" placeholder="例如：张大爷" />
                    </div>
                    <div style="grid-column:1/-1;">
                        <label class="edit-label">问题描述</label>
                        <el-input v-model="editingForm.issue" type="textarea" :rows="2" placeholder="例如：电风扇损坏" />
                    </div>
                    <div>
                        <label class="edit-label">指派人员</label>
                        <el-input v-model="editingForm.assignedTo" placeholder="例如：维修部小王" />
                    </div>
                    <div>
                        <label class="edit-label">优先级</label>
                        <el-select v-model="editingForm.priority" style="width:100%;">
                            <el-option label="紧急" value="URGENT" />
                            <el-option label="普通" value="NORMAL" />
                        </el-select>
                    </div>
                    <div>
                        <label class="edit-label">状态</label>
                        <el-select v-model="editingForm.status" style="width:100%;">
                            <el-option label="待处理" value="PENDING" />
                            <el-option label="处理中" value="PROCESSING" />
                            <el-option label="已完成" value="DONE" />
                        </el-select>
                    </div>
                </div>
                <div>
                    <label class="edit-label">已采取措施</label>
                    <div v-for="(action, index) in editingForm.actionsTaken" :key="index" style="display:flex; gap:8px; margin-bottom:8px;">
                        <el-input v-model="editingForm.actionsTaken[index]" placeholder="例如：已送冰块降温" style="flex:1;" />
                        <el-button type="danger" circle @click="editingForm.actionsTaken.splice(index, 1)" style="flex-shrink:0;"><el-icon><Delete /></el-icon></el-button>
                    </div>
                    <el-button type="primary" link @click="editingForm.actionsTaken.push('')" style="margin-top:4px;">
                        <el-icon style="margin-right:4px;"><Plus /></el-icon> 添加一项措施
                    </el-button>
                </div>
            </div>
            <template #footer>
                <el-button @click="editActionsVisible = false">取消</el-button>
                <el-button type="primary" :loading="editActionsLoading" @click="saveEditActions">
                    <el-icon v-if="!editActionsLoading"><Check /></el-icon>
                    {{ editActionsLoading ? '保存中...' : '保存' }}
                </el-button>
            </template>
        </el-dialog>
    </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getWorkOrders, getWorkOrderDetail, updateWorkOrderStatus, updateWorkOrder, deleteWorkOrder, dispatchWorkOrder } from '../api'

const orders = ref([])
const allOrders = ref([])
const loading = ref(false)
const filters = reactive({ status: '', priority: '' })
const pagination = reactive({ page: 1, size: 10, total: 0 })

const stats = computed(() => {
    const list = allOrders.value
    return {
        pending: list.filter(o => o.status === 'PENDING').length,
        processing: list.filter(o => o.status === 'PROCESSING').length,
        done: list.filter(o => o.status === 'DONE').length,
        urgent: list.filter(o => o.priority === 'URGENT' && o.status !== 'DONE').length
    }
})

async function loadOrders() {
    loading.value = true
    try {
        const res = await getWorkOrders({
            page: pagination.page,
            size: pagination.size,
            status: filters.status || undefined,
            priority: filters.priority || undefined
        })
        orders.value = res.data?.records || []
        pagination.total = res.data?.total || 0
    } catch (e) {
        ElMessage.error(e.message)
    } finally {
        loading.value = false
    }
}

async function loadAllForStats() {
    try {
        const res = await getWorkOrders({ page: 1, size: 9999 })
        allOrders.value = res.data?.records || []
    } catch { /* silent */ }
}

const showDetailDialog = ref(false)
const detailOrder = ref(null)

function showDetail(row) {
    detailOrder.value = row
    showDetailDialog.value = true
}

async function changeStatus(id, status) {
    const label = status === 'PROCESSING' ? '开始处理' : '标记完成'
    try {
        await ElMessageBox.confirm(`确定要${label}吗？`, '确认操作')
        await updateWorkOrderStatus(id, status)
        ElMessage.success('状态更新成功')
        loadOrders()
        loadAllForStats()
    } catch (e) {
        if (e !== 'cancel') ElMessage.error(e.message)
    }
}

async function handleDelete(id) {
    try {
        await deleteWorkOrder(id)
        ElMessage.success('工单删除成功')
        loadOrders()
        loadAllForStats()
    } catch (e) {
        ElMessage.error(e.message)
    }
}

// ---- 编辑工单 ----
const editActionsVisible = ref(false)
const editingOrder = ref(null)
const editingForm = ref({ location: "", clientName: "", issue: "", actionsTaken: [], assignedTo: "", priority: "NORMAL", status: "PENDING" })
const editActionsLoading = ref(false)

function openEditActions(row) {
    editingOrder.value = row
    editingForm.value = {
        location: row.location || "",
        clientName: row.clientName || "",
        issue: row.issue || "",
        actionsTaken: Array.isArray(row.actionsTaken) ? [...row.actionsTaken] : [],
        assignedTo: row.assignedTo || "",
        priority: row.priority || "NORMAL",
        status: row.status || "PENDING"
    }
    editActionsVisible.value = true
}

async function saveEditActions() {
    editActionsLoading.value = true
    try {
        const actions = editingForm.value.actionsTaken.filter(a => a && a.trim())
        await updateWorkOrder({
            id: editingOrder.value.id,
            location: editingForm.value.location || undefined,
            clientName: editingForm.value.clientName || undefined,
            issue: editingForm.value.issue || undefined,
            actionsTaken: actions,
            assignedTo: editingForm.value.assignedTo || undefined,
            priority: editingForm.value.priority || undefined,
            status: editingForm.value.status || undefined
        })
        ElMessage.success("工单信息更新成功")
        editActionsVisible.value = false
        loadOrders()
        loadAllForStats()
    } catch (e) {
        ElMessage.error(e.message)
    } finally {
        editActionsLoading.value = false
    }
}

const showDispatchDialog = ref(false)
const dispatchText = ref('')
const dispatchLoading = ref(false)

async function handleDispatch() {
    if (!dispatchText.value.trim()) {
        ElMessage.warning('请输入描述内容')
        return
    }
    dispatchLoading.value = true
    try {
        await dispatchWorkOrder(dispatchText.value)
        ElMessage.success('工单创建成功！')
        showDispatchDialog.value = false
        dispatchText.value = ''
        loadOrders()
        loadAllForStats()
    } catch (e) {
        ElMessage.error(e.message)
    } finally {
        dispatchLoading.value = false
    }
}

function statusType(s) {
    return { PENDING: 'warning', PROCESSING: '', DONE: 'success' }[s] || 'info'
}
function statusLabel(s) {
    return { PENDING: '待处理', PROCESSING: '处理中', DONE: '已完成' }[s] || s
}

onMounted(() => {
    loadOrders()
    loadAllForStats()
})
</script>

<style scoped>
.header-action {
    height: 36px;
    font-size: 13px;
    font-weight: 500;
    padding: 0 18px;
}

.filter-bar {
    background: var(--c-surface);
    border-radius: var(--radius-lg);
    padding: 14px 20px;
    border: 1px solid var(--c-border);
    margin-bottom: 16px;
    display: flex;
    align-items: center;
}

.filter-bar .el-form-item {
    margin-bottom: 0;
}

.card-count {
    font-size: 11px;
    font-weight: 600;
    color: var(--c-text-3);
    background: var(--c-bg);
    padding: 1px 8px;
    border-radius: 10px;
    margin-left: 4px;
}

.pagination-wrap {
    margin-top: 16px;
    display: flex;
    justify-content: flex-end;
}

.dispatch-tip {
    margin-bottom: 16px;
    padding: 12px 16px;
    background: var(--c-primary-light);
    border-radius: var(--radius-md);
    font-size: 13px;
    color: var(--c-primary-dark);
    border: 1px solid rgba(67, 97, 238, 0.1);
}

.edit-label {
    display: block;
    font-size: 13px;
    font-weight: 600;
    color: var(--c-text-2);
    margin-bottom: 6px;
}
</style>