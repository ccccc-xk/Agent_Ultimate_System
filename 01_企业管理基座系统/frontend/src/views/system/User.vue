<template>
  <div class="user-page">
    <div class="page-header">
      <h2 class="page-title">用户管理</h2>
      <p class="page-desc">管理系统用户账号、状态与角色分配</p>
    </div>

    <div class="section-card">
      <div class="card-toolbar">
        <div class="toolbar-left">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索用户名 / 姓名 / 手机号"
            prefix-icon="Search"
            clearable
            style="width: 280px"
            @clear="loadData"
            @keyup.enter="loadData"
          />
        </div>
        <div class="toolbar-right">
          <el-button type="primary" @click="loadData">
            <el-icon><Search /></el-icon>查询
          </el-button>
          <el-button type="success" @click="openDialog()">
            <el-icon><Plus /></el-icon>新增用户
          </el-button>
        </div>
      </div>

      <el-table :data="tableData" stripe class="data-table" v-loading="tableLoading">
        <el-table-column prop="id" label="ID" width="70" align="center">
          <template #default="{ row }">
            <span class="cell-id">#{{ row.id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" width="160">
          <template #default="{ row }">
            <div class="user-cell">
              <div class="user-cell-avatar" :style="{ background: avatarGradient(row.username) }">
                {{ row.realName?.charAt(0) || row.username?.charAt(0) || 'U' }}
              </div>
              <div class="user-cell-info">
                <span class="user-cell-name">{{ row.username }}</span>
                <span v-if="row.roles && row.roles.length" class="user-cell-role">
                  <el-tag v-for="role in row.roles.slice(0, 2)" :key="role" size="small" type="info" effect="plain" round class="role-mini-tag">{{ role }}</el-tag>
                </span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="realName" label="姓名" width="110" />
        <el-table-column prop="phone" label="手机号" width="140">
          <template #default="{ row }">
            <span class="cell-mono">{{ row.phone || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <div class="status-badge" :class="row.status === 1 ? 'status-active' : 'status-disabled'">
              <span class="status-dot"></span>
              {{ row.status === 1 ? '正常' : '禁用' }}
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" min-width="170">
          <template #default="{ row }">
            <span class="cell-time">{{ row.createTime }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">
              <el-icon><Edit /></el-icon>编辑
            </el-button>
            <el-button link type="warning" @click="handleReset(row)">
              <el-icon><RefreshRight /></el-icon>重置
            </el-button>
            <el-button link type="danger" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>删除
            </el-button>
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

    <!-- Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑用户' : '新增用户'"
      width="500px"
    >
      <el-form ref="dialogFormRef" :model="dialogForm" :rules="dialogRules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="dialogForm.username" :disabled="isEdit" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="密码" prop="password">
          <el-input v-model="dialogForm.password" type="password" placeholder="默认 123456" show-password />
        </el-form-item>
        <el-form-item label="姓名" prop="realName">
          <el-input v-model="dialogForm.realName" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="dialogForm.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="dialogForm.status" :active-value="1" :inactive-value="0" active-text="正常" inactive-text="禁用" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="dialogForm.roleIds" multiple placeholder="选择角色" style="width: 100%">
            <el-option v-for="r in roleList" :key="r.id" :label="r.roleName" :value="r.id" />
          </el-select>
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
import { ref, reactive, onMounted } from 'vue'
import request from '@/utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'

const tableData = ref([])
const tableLoading = ref(false)
const roleList = ref([])
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)
const searchKeyword = ref('')

const dialogVisible = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const dialogFormRef = ref()
const dialogForm = reactive({
  id: null, username: '', password: '', realName: '', phone: '', status: 1, roleIds: [],
})
const dialogRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  realName: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
}

const gradients = [
  'linear-gradient(135deg, #3b82f6, #2563eb)',
  'linear-gradient(135deg, #6366f1, #4f46e5)',
  'linear-gradient(135deg, #8b5cf6, #7c3aed)',
  'linear-gradient(135deg, #10b981, #059669)',
  'linear-gradient(135deg, #f59e0b, #d97706)',
  'linear-gradient(135deg, #ef4444, #dc2626)',
  'linear-gradient(135deg, #ec4899, #db2777)',
  'linear-gradient(135deg, #06b6d4, #0891b2)',
]
function avatarGradient(name) {
  if (!name) return gradients[0]
  let hash = 0
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash)
  return gradients[Math.abs(hash) % gradients.length]
}

async function loadData() {
  tableLoading.value = true
  try {
    const res = await request.get('/api/user/page', {
      params: { pageNum: pageNum.value, pageSize: pageSize.value, keyword: searchKeyword.value || undefined },
    })
    tableData.value = res.data.records
    total.value = res.data.total
  } finally {
    tableLoading.value = false
  }
}

async function loadRoles() {
  const res = await request.get('/api/role/list')
  roleList.value = res.data
}

function openDialog(row) {
  isEdit.value = !!row
  if (row) {
    Object.assign(dialogForm, { ...row, roleIds: row.roleIds || [], password: '' })
  } else {
    Object.assign(dialogForm, { id: null, username: '', password: '', realName: '', phone: '', status: 1, roleIds: [] })
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await dialogFormRef.value.validate().catch(() => false)
  if (!valid) return
  submitLoading.value = true
  try {
    if (isEdit.value) {
      await request.put('/api/user', dialogForm)
    } else {
      await request.post('/api/user', dialogForm)
    }
    ElMessage.success(isEdit.value ? '编辑成功' : '新增成功')
    dialogVisible.value = false
    loadData()
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除用户 ${row.username}？`, '提示', { type: 'warning' })
  await request.delete(`/api/user/${row.id}`)
  ElMessage.success('删除成功')
  loadData()
}

async function handleReset(row) {
  await ElMessageBox.confirm(`确认重置 ${row.username} 的密码为 123456？`, '提示', { type: 'warning' })
  await request.put(`/api/user/reset-password/${row.id}`)
  ElMessage.success('密码已重置为 123456')
}

onMounted(() => {
  loadData()
  loadRoles()
})
</script>

<style scoped>
.user-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.page-header {
  margin-bottom: 0;
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
  flex-wrap: wrap;
  gap: 12px;
}
.toolbar-right {
  display: flex;
  gap: 8px;
}

.cell-id {
  font-size: 12px;
  color: var(--text-light);
  font-weight: 500;
}
.cell-mono {
  font-family: 'SF Mono', 'Consolas', monospace;
  font-size: 13px;
  color: var(--text-secondary);
}
.cell-time {
  font-size: 13px;
  color: var(--text-muted);
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}
.user-cell-avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
  transition: all var(--transition-normal);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
.user-cell:hover .user-cell-avatar {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
.user-cell-info {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.user-cell-name {
  font-weight: 500;
  color: var(--text-primary);
  font-size: 13px;
}
.user-cell-role {
  display: flex;
  gap: 4px;
}
.role-mini-tag {
  font-size: 10px !important;
  padding: 0 6px !important;
  height: 18px !important;
  line-height: 18px !important;
}

/* Status Badge */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  padding: 4px 10px;
  border-radius: 6px;
}
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.status-active {
  color: #059669;
  background: rgba(16, 185, 129, 0.08);
}
.status-active .status-dot {
  background: #10b981;
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.5);
}
.status-disabled {
  color: #dc2626;
  background: rgba(239, 68, 68, 0.08);
}
.status-disabled .status-dot {
  background: #ef4444;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
