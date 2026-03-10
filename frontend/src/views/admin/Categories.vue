<template>
  <div class="admin-categories">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>版块管理</span>
          <el-button type="primary" @click="showCreateDialog">新建版块</el-button>
        </div>
      </template>

      <el-table :data="categories" v-loading="loading" stripe row-key="id">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="版块名称" width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="post_count" label="帖子数" width="100" />
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column prop="can_post" label="发帖等级" width="100" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="150">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑版块' : '新建版块'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="版块名称" required>
          <el-input v-model="form.name" placeholder="请输入版块名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入版块描述" />
        </el-form-item>
        <el-form-item label="父版块">
          <el-select v-model="form.parent_id" placeholder="无（顶级版块）" clearable style="width: 100%">
            <el-option
              v-for="cat in topLevelCategories"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
              :disabled="isEdit && cat.id === form.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="发帖等级">
          <el-input-number v-model="form.can_post" :min="0" />
        </el-form-item>
        <el-form-item label="图标">
          <el-input v-model="form.icon" placeholder="图标URL或图标类名" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const categories = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const form = ref({
  id: null,
  name: '',
  description: '',
  parent_id: null,
  sort_order: 0,
  can_post: 0,
  icon: '',
  is_active: true
})

const topLevelCategories = computed(() => {
  return categories.value.filter(c => !c.parent_id)
})

onMounted(() => {
  loadCategories()
})

async function loadCategories() {
  loading.value = true
  try {
    const data = await api.categories.getList()
    // 展开层级结构为平铺列表
    const flatList = []
    function flatten(items, depth = 0) {
      for (const item of items) {
        flatList.push({ ...item, depth })
        if (item.children && item.children.length > 0) {
          flatten(item.children, depth + 1)
        }
      }
    }
    flatten(data)
    categories.value = flatList
  } catch (error) {
    console.error('加载版块列表失败:', error)
  } finally {
    loading.value = false
  }
}

function showCreateDialog() {
  isEdit.value = false
  form.value = {
    id: null,
    name: '',
    description: '',
    parent_id: null,
    sort_order: 0,
    can_post: 0,
    icon: '',
    is_active: true
  }
  dialogVisible.value = true
}

function showEditDialog(row) {
  isEdit.value = true
  form.value = { ...row }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.value.name) {
    ElMessage.warning('请输入版块名称')
    return
  }
  try {
    if (isEdit.value) {
      await api.categories.update(form.value.id, form.value)
      ElMessage.success('版块已更新')
    } else {
      await api.categories.create(form.value)
      ElMessage.success('版块已创建')
    }
    dialogVisible.value = false
    loadCategories()
  } catch (error) {
    console.error('操作失败:', error)
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除版块"${row.name}"？删除后不可恢复！`, '警告', {
      type: 'warning'
    })
    await api.categories.delete(row.id)
    ElMessage.success('版块已删除')
    loadCategories()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
