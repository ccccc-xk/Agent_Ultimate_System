<template>
  <div class="source-card">
    <div class="source-toggle" @click="expanded = !expanded">
      <div class="toggle-left">
        <el-icon :size="14"><InfoFilled /></el-icon>
        <span>参考来源 ({{ sources.length }} 条)</span>
      </div>
      <div class="toggle-right">
        <span v-if="confidence > 0" class="confidence-badge">
          {{ (confidence * 100).toFixed(0) }}%
        </span>
        <el-icon class="chevron" :class="{ open: expanded }"><ArrowDown /></el-icon>
      </div>
    </div>

    <div class="source-wrap" :class="{ open: expanded }">
      <div class="source-body">
        <div
          v-for="(s, i) in sources"
          :key="i"
          class="source-item"
        >
          <div class="item-head">
            <el-icon :size="13"><Document /></el-icon>
            <span class="item-doc">{{ s.doc_name }}</span>
            <el-tag size="small" type="info" effect="plain">P{{ s.page_num }}</el-tag>
            <el-tag size="small" effect="plain" type="success">{{ (s.score * 100).toFixed(0) }}%</el-tag>
          </div>
          <div class="item-text">{{ s.chunk_text }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
defineProps({ sources: { type: Array, default: () => [] }, confidence: { type: Number, default: 0 } })
const expanded = ref(false)
</script>

<style lang="scss" scoped>
@import '../assets/styles/variables.scss';

.source-card {
  margin-top: 8px;
  border: 1px solid $border-light;
  border-radius: $radius-md;
  background: $bg-white;
  overflow: hidden;
  transition: box-shadow 200ms ease;
  &:hover { box-shadow: $shadow-card; }
}

.source-toggle {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px;
  cursor: pointer;
  font-size: 12px;
  color: $text-assist;
  transition: background 150ms ease;
  &:hover { background: $bg-hover; }
}

.toggle-left { display: flex; align-items: center; gap: 5px; }
.toggle-right { display: flex; align-items: center; gap: 8px; }

.confidence-badge {
  padding: 1px 8px;
  border-radius: $radius-full;
  background: $health-light;
  color: $health-green;
  font-size: 11px;
  font-weight: 600;
}

.chevron {
  font-size: 12px;
  transition: transform 200ms ease;
  &.open { transform: rotate(180deg); }
}

/* Smooth expand using grid-template-rows trick */
.source-wrap {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 250ms ease-out;

  &.open {
    grid-template-rows: 1fr;
  }
}

.source-body {
  overflow: hidden;
  padding: 0;
  border-top: 0 solid $border-light;
  transition: padding 250ms ease-out, border-top-width 250ms ease-out;

  .source-wrap.open & {
    padding: 10px;
    border-top-width: 1px;
  }
}

.source-item {
  padding: 10px 12px;
  background: $bg-gray;
  border-radius: $radius-sm;
  border-left: 3px solid $primary-blue;
  transition: box-shadow 200ms ease, transform 200ms ease;

  &:hover {
    box-shadow: 0 4px 16px rgba(43, 125, 233, 0.15);
    transform: translateY(-1px);
  }

  & + & {
    margin-top: 8px;
  }
}

.item-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  font-size: 12px;
  color: $text-body;
}

.item-doc { font-weight: 600; color: $text-title; }

.item-text {
  font-size: 12px;
  color: $text-assist;
  line-height: 1.6;
  max-height: 72px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}
</style>
