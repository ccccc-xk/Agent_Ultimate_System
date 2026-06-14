<template>
  <div class="role-page">
    <div class="page-header">
      <h2 class="page-title">角色管理</h2>
      <p class="page-desc">管理系统角色及其菜单权限</p>
    </div>

    <div class="section-card">
      <div class="card-toolbar">
        <div class="toolbar-left">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索角色名称 / 标识"
            prefix-icon="Search"
            clearable
            style="width: 240px"
            @clear="loadData"
            @keyup.enter="loadData"
          />
        </div>
        <div class="toolbar-right">
          <el-button type="primary" @click="loadData">
            <el-icon><Search /></el-icon>查询
          </el-button>
          <el-button type="success" @click="openDialog()">
            <el-icon><Plus /></el-icon>新增角色
          </el-button>
        </div>
      </div>

      <el-table :data="tableData" stripe class="data-table" v-loading="tableLoading">
        <el-table-column prop="id" label="ID" width="70" align="center">
          <template #default="{ row }">
            <span class="cell-id">#{{ row.id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="roleName" label="角色名称" width="200">
          <template #default="{ row }">
            <div class="role-cell">
              <div class="role-badge" :class="row.roleKey === 'admin' ? 'badge-admin' : 'badge-staff'">
                {{ row.roleName?.charAt(0) }}
              </div>
              <div class="role-cell-info">
                <span class="role-name">{{ row.roleName }}</span>
                <el-tag size="small" type="info" effect="plain" round class="role-key-tag">{{ row.roleKey }}</el-tag>
              </div>
            </div>
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
        <el-table-column label="菜单权限" min-width="200">
          <template #default="{ row }">
            <div class="perms-preview">
              <el-tag
                v-for="pid in (row.menuIds || []).slice(0, 4)"
                :key="pid"
                size="small"
                type="info"
                effect="plain"
                class="perms-tag"
              >
                {{ getPermLabel(pid) }}
              </el-tag>
              <span v-if="(row.menuIds || []).length > 4" class="perms-more">
                +{{ row.menuIds.length - 4 }}
              </span>
              <span v-if="!(row.menuIds || []).length" class="perms-none">未分配</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" width="170">
          <template #default="{ row }">
            <span class="cell-time">{{ row.createTime }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">
              <el-icon><Edit /></el-icon>编辑
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
      :title="isEdit ? '编辑角色' : '新增角色'"
      width="520px"
    >
      <el-form ref="dialogFormRef" :model="dialogForm" :rules="dialogRules" label-width="80px">
        <el-form-item label="角色名称" prop="roleName">
          <el-input v-model="dialogForm.roleName" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="角色标识" prop="roleKey">
          <el-input v-model="dialogForm.roleKey" :disabled="isEdit" placeholder="如 admin、staff" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="dialogForm.status" :active-value="1" :inactive-value="0" active-text="正常" inactive-text="禁用" />
        </el-form-item>
        <el-form-item label="菜单权限">
          <div class="tree-container">
            <div class="tree-toolbar">
              <el-button text size="small" @click="checkAll">全选</el-button>
              <el-button text size="small" @click="uncheckAll">取消全选</el-button>
            </div>
            <el-tree
              ref="menuTreeRef"
              :data="menuTree"
              :props="{ label: 'menuName', children: 'children' }"
              show-checkbox
              node-key="id"
              :default-checked-keys="dialogForm.menuIds"
              default-expand-all
            />
          </div>
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
import { ref, reactive, onMounted, nextTick } from 'vue'
import request from '@/utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'

const tableData = ref([])
const tableLoading = ref(false)
const menuTree = ref([])
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)
const searchKeyword = ref('')

const dialogVisible = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const dialogFormRef = ref()
const menuTreeRef = ref()
const dialogForm = reactive({ id: null, roleName: '', roleKey: '', status: 1, menuIds: [] })
const dialogRules = {
  roleName: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
  roleKey: [{ required: true, message: '请输入角色标识', trigger: 'blur' }],
}

let menuNameMap = {}
function buildMenuMap(list) {
  for (const m of list) {
    menuNameMap[m.id] = m.menuName
    if (m.children) buildMenuMap(m.children)
  }
}
function getPermLabel(id) {
  return menuNameMap[id] || `#${id}`
}

function checkAll() {
  if (!menuTreeRef.value) return
  const allKeys = []
  function walk(nodes) {
    for (const n of nodes) {
      allKeys.push(n.id)
      if (n.children) walk(n.children)
    }
  }
  walk(menuTree.value)
  menuTreeRef.value.setCheckedKeys(allKeys)
}
function uncheckAll() {
  menuTreeRef.value?.setCheckedKeys([])
}

async function loadData() {
  tableLoading.value = true
  try {
    const res = await request.get('/api/role/page', {
      params: { pageNum: pageNum.value, pageSize: pageSize.value, keyword: searchKeyword.value || undefined },
    })
    tableData.value = res.data.records
    total.value = res.data.total
  } finally {
    tableLoading.value = false
  }
}

async function loadMenuTree() {
  const res = await request.get('/api/menu/all')
  menuTree.value = res.data
  buildMenuMap(res.data)
}

function openDialog(row) {
  isEdit.value = !!row
  if (row) {
    Object.assign(dialogForm, { ...row, menuIds: row.menuIds || [] })
  } else {
    Object.assign(dialogForm, { id: null, roleName: '', roleKey: '', status: 1, menuIds: [] })
  }
  dialogVisible.value = true
  nextTick(() => {
    if (menuTreeRef.value) {
      menuTreeRef.value.setCheckedKeys(row?.menuIds || [])
    }
  })
}

async function handleSubmit() {
  const valid = await dialogFormRef.value.validate().catch(() => false)
  if (!valid) return
  submitLoading.value = true
  try {
    const checkedKeys = menuTreeRef.value.getCheckedKeys()
    const halfCheckedKeys = menuTreeRef.value.getHalfCheckedKeys()
    dialogForm.menuIds = [...checkedKeys, ...halfCheckedKeys]

    if (isEdit.value) {
      await request.put('/api/role', dialogForm)
    } else {
      await request.post('/api/role', dialogForm)
    }
    ElMessage.success(isEdit.value ? '编辑成功' : '新增成功')
    dialogVisible.value = false
    loadData()
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除角色 ${row.roleName}？`, '提示', { type: 'warning' })
  await request.delete(`/api/role/${row.id}`)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(() => {
  loadData()
  loadMenuTree()
})
</script>

<style scoped>
.role-page {
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
.cell-time {
  font-size: 13px;
  color: var(--text-muted);
}

.role-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}
.role-badge {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
  transition: all var(--transition-normal);
}
.role-cell:hover .role-badge {
  transform: scale(1.1);
}
.badge-admin {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}
.badge-staff {
  background: linear-gradient(135deg, #10b981, #059669);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}
.role-cell-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.role-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
}
.role-key-tag {
  font-size: 10px !important;
  width: fit-content;
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

.perms-preview {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}
.perms-tag {
  font-size: 11px;
}
.perms-more {
  font-size: 11px;
  color: var(--text-light);
  background: var(--bg-main);
  padding: 2px 8px;
  border-radius: 4px;
}
.perms-none {
  font-size: 12px;
  color: var(--text-light);
  font-style: italic;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.tree-container {
  width: 100%;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background: #f8fafc;
  overflow: hidden;
}
.tree-toolbar {
  display: flex;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border-light);
  background: #f1f5f9;
}
.tree-container :deep(.el-tree) {
  padding: 8px 0;
  max-height: 220px;
  overflow-y: auto;
}
.tree-container :deep(.el-tree-node__content) {
  height: 32px;
  padding-right: 12px;
}
.tree-container :deep(.el-tree-node__label) {
  font-size: 13px;
}
</style>
