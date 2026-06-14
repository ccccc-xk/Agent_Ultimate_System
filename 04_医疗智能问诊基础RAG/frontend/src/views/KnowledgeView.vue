<template>
  <div class="knowledge-view">
    <div class="page-header">
      <div class="header-left">
        <div class="header-icon">
          <el-icon :size="22" color="#2B7DE9"><Collection /></el-icon>
        </div>
        <div>
          <h2>知识库管理</h2>
          <p class="header-desc">管理医疗知识文档，上传后系统将自动切片、向量化并存入数据库</p>
        </div>
      </div>
      <el-tag v-if="documents.length > 0" effect="plain" round>
        共 {{ documents.length }} 份文档
      </el-tag>
    </div>

    <!-- Upload -->
    <div class="upload-section">
      <el-upload
        class="upload-dragger"
        drag
        :auto-upload="false"
        :on-change="handleFile"
        :show-file-list="false"
        accept=".pdf,.md,.markdown"
      >
        <div class="upload-inner">
          <div class="upload-icon-wrap">
            <el-icon :size="40"><UploadFilled /></el-icon>
          </div>
          <div class="upload-text">拖拽文件到此处，或<em>点击上传</em></div>
          <div class="upload-badges">
            <span class="badge pdf">PDF</span>
            <span class="badge md">Markdown</span>
          </div>
        </div>
      </el-upload>

      <!-- Progress -->
      <transition name="slide-up">
        <div v-if="uploading" class="progress-wrap">
          <div class="progress-info">
            <el-icon :size="14"><Loading /></el-icon>
            <span>{{ uploadingFile }}</span>
          </div>
          <el-progress
            :percentage="uploadPct"
            :status="uploadStatus"
            :stroke-width="8"
          />
        </div>
      </transition>

      <!-- Success animation -->
      <transition name="slide-up">
        <div v-if="showSuccess" class="success-wrap">
          <div class="success-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none">
              <circle cx="12" cy="12" r="10" fill="#ECFDF5" stroke="#10B981" stroke-width="1.5"/>
              <path class="check-path" d="M8 12.5L11 15.5L16.5 9" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <span class="success-text">已成功导入 {{ successChunks }} 个切片</span>
        </div>
      </transition>
    </div>

    <!-- Document table -->
    <div class="table-section">
      <el-table
        :data="documents"
        stripe
        :header-cell-style="{ background: '#F7F8FA', color: '#1D2129', fontWeight: 600 }"
        empty-text=""
        class="doc-table"
      >
        <el-table-column label="文档名称" min-width="240">
          <template #default="{ row }">
            <div class="doc-name-cell">
              <span class="file-badge" :class="row.doc_name.endsWith('.pdf') ? 'pdf' : 'md'">
                {{ row.doc_name.endsWith('.pdf') ? 'PDF' : 'MD' }}
              </span>
              <span>{{ row.doc_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="切片数量" width="120" align="center">
          <template #default="{ row }">
            <el-tag type="primary" effect="plain" round size="small">{{ row.chunk_count }} 片</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="入库时间" prop="created_at" width="190" />
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button type="danger" link @click="handleDelete(row)">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-table-column>

        <!-- Empty -->
        <template #empty>
          <div class="table-empty">
            <el-icon :size="48" color="#C9CDD4"><FolderOpened /></el-icon>
            <p>暂无文档，请上传医疗知识文档开始使用</p>
          </div>
        </template>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { uploadKnowledge, listKnowledge, deleteKnowledge } from '../api'

const documents = ref([])
const uploading = ref(false)
const uploadPct = ref(0)
const uploadStatus = ref('')
const uploadingFile = ref('')
const showSuccess = ref(false)
const successChunks = ref(0)

onMounted(() => loadDocs())

async function loadDocs() {
  try { const r = await listKnowledge(); documents.value = r.data.documents || [] } catch (_) {}
}

async function handleFile(file) {
  const ext = file.name.split('.').pop().toLowerCase()
  if (!['pdf', 'md', 'markdown'].includes(ext)) { ElMessage.error('仅支持 PDF 和 Markdown 格式'); return }

  uploading.value = true; uploadPct.value = 30; uploadStatus.value = ''; uploadingFile.value = file.name
  try {
    uploadPct.value = 60
    const r = await uploadKnowledge(file.raw)
    uploadPct.value = 100; uploadStatus.value = 'success'
    // Show success animation
    successChunks.value = r.data.chunk_count
    showSuccess.value = true
    setTimeout(() => { showSuccess.value = false }, 3000)
    ElMessage.success(`已导入 ${r.data.chunk_count} 个切片，耗时 ${r.data.elapsed_seconds}s`)
    loadDocs()
  } catch (e) {
    uploadPct.value = 100; uploadStatus.value = 'exception'
    ElMessage.error('上传失败: ' + (e.response?.data?.detail || e.message))
  } finally { setTimeout(() => { uploading.value = false; uploadPct.value = 0 }, 2000) }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除「${row.doc_name}」及 ${row.chunk_count} 个切片？`, '删除确认', {
      confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning'
    })
    await deleteKnowledge(row.doc_name)
    ElMessage.success(`已删除「${row.doc_name}」`)
    loadDocs()
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}
</script>

<style lang="scss" scoped>
@import '../assets/styles/variables.scss';

.knowledge-view {
  padding: 28px 32px;
  height: 100vh;
  overflow-y: auto;
  background: $bg-gray;

  @include mobile {
    padding: 16px;
    padding-bottom: 16px + $mobile-tab-height;
  }
}

/* ===== Header ===== */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;

  @include mobile {
    flex-direction: column;
    gap: 12px;
  }
}
.header-left { display: flex; align-items: center; gap: 14px; }
.header-icon {
  width: 44px; height: 44px;
  background: $primary-light;
  border-radius: $radius-md;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.page-header h2 { font-size: 20px; color: $text-title; font-weight: 700; }
.header-desc { font-size: 13px; color: $text-assist; margin-top: 2px; }

/* ===== Upload ===== */
.upload-section { margin-bottom: 24px; }

.upload-dragger :deep(.el-upload-dragger) {
  padding: 36px 20px;
  border-radius: $radius-lg;
  border-color: $border-light;
  background: $bg-white;
  transition: all 200ms ease;

  &:hover {
    border-color: $primary-blue;
    background: $primary-light;
  }
}

.upload-inner { text-align: center; }
.upload-icon-wrap { color: $text-assist; margin-bottom: 8px; }
.upload-text { color: $text-body; font-size: 14px; margin-bottom: 10px; }
.upload-text em { color: $primary-blue; font-style: normal; cursor: pointer; }
.upload-badges { display: flex; gap: 8px; justify-content: center; }

.badge {
  padding: 2px 10px;
  border-radius: $radius-full;
  font-size: 11px;
  font-weight: 600;
  &.pdf { background: $danger-light; color: $danger-red; }
  &.md { background: $primary-light; color: $primary-blue; }
}

/* ===== Progress ===== */
.progress-wrap {
  margin-top: 16px;
  padding: 14px 18px;
  background: $bg-white;
  border-radius: $radius-md;
  box-shadow: $shadow-card;
}
.progress-info { display: flex; align-items: center; gap: 6px; font-size: 13px; color: $text-body; margin-bottom: 8px; }

/* ===== Success Animation ===== */
.success-wrap {
  margin-top: 12px;
  padding: 14px 18px;
  background: $bg-white;
  border-radius: $radius-md;
  box-shadow: $shadow-card;
  display: flex;
  align-items: center;
  gap: 10px;
}

.success-icon {
  flex-shrink: 0;
}

.check-path {
  stroke-dasharray: 20;
  stroke-dashoffset: 20;
  animation: checkDraw 400ms ease-out 100ms forwards;
}

@keyframes checkDraw {
  to { stroke-dashoffset: 0; }
}

.success-text {
  font-size: 14px;
  font-weight: 500;
  color: $health-green;
}

.slide-up-enter-active { transition: all 300ms ease-out; }
.slide-up-leave-active { transition: all 200ms ease-in; }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translateY(-10px); }

/* ===== Table ===== */
.table-section {
  background: $bg-white;
  border-radius: $radius-lg;
  overflow: hidden;
  box-shadow: $shadow-card;
}

.doc-table { width: 100%; }

.doc-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-badge {
  padding: 1px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
  &.pdf { background: $danger-light; color: $danger-red; }
  &.md { background: $primary-light; color: $primary-blue; }
}

.table-empty {
  padding: 48px 0;
  text-align: center;
  p { margin-top: 12px; color: $text-assist; font-size: 14px; }
}
</style>
