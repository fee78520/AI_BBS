<template>
  <div class="create-post">
    <el-card>
      <h2>发帖</h2>
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="请输入标题" maxlength="200" show-word-limit />
        </el-form-item>
        <el-form-item label="版块">
          <el-select v-model="form.category_id" placeholder="选择版块" style="width: 100%;">
            <el-option
              v-for="cat in categories"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="内容">
          <div class="editor-container">
            <QuillEditor
              ref="editorRef"
              v-model:content="form.content"
              contentType="html"
              theme="snow"
              :toolbar="toolbarOptions"
              placeholder="请输入内容..."
              @ready="onEditorReady"
            />
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">发布</el-button>
          <el-button @click="router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'
import api from '@/api'
import Quill from 'quill'

const router = useRouter()
const editorRef = ref(null)
const submitting = ref(false)
const form = ref({
  title: '',
  category_id: null,
  content: '',
  post_type: 'normal',
  tags: []
})
const categories = ref([])

// 工具栏配置
const toolbarOptions = [
  ['bold', 'italic', 'underline', 'strike'],        // 加粗、斜体、下划线、删除线
  ['blockquote', 'code-block'],                      // 引用、代码块
  [{ 'header': [1, 2, 3, 4, 5, 6, false] }],        // 标题
  [{ 'list': 'ordered'}, { 'list': 'bullet' }],     // 有序列表、无序列表
  [{ 'indent': '-1'}, { 'indent': '+1' }],          // 缩进
  [{ 'color': [] }, { 'background': [] }],          // 字体颜色、背景色
  [{ 'align': [] }],                                 // 对齐方式
  ['link', 'image'],                                 // 链接、图片
  ['clean']                                          // 清除格式
]

onMounted(async () => {
  try {
    categories.value = await api.categories.getList()
    // 如果没有选择版块且有版块列表，默认选择第一个
    if (categories.value.length > 0 && !form.value.category_id) {
      form.value.category_id = categories.value[0].id
    }
  } catch (error) {
    console.error('加载版块失败:', error)
  }
})

function onEditorReady() {
  console.log('编辑器已就绪')
  // 自定义图片上传处理器
  const quill = editorRef.value.getQuill()
  const toolbar = quill.getModule('toolbar')
  
  toolbar.addHandler('image', function() {
    const input = document.createElement('input')
    input.setAttribute('type', 'file')
    input.setAttribute('accept', 'image/*')
    input.click()
    
    input.onchange = async () => {
      const file = input.files[0]
      if (!file) return
      
      // 检查文件大小 (最大10MB)
      if (file.size > 10 * 1024 * 1024) {
        ElMessage.warning('图片大小不能超过10MB')
        return
      }
      
      try {
        // 上传图片到服务器
        const result = await api.uploads.uploadImage(file)
        
        // 获取图片URL并插入编辑器
        const imageUrl = result.file_path
        const range = quill.getSelection(true)
        
        // 使用 Delta API 插入图片
        const Delta = Quill.import('delta')
        quill.updateContents(
          new Delta().retain(range.index).insert({ image: imageUrl }),
          'user'
        )
        quill.setSelection(range.index + 1)
        
        ElMessage.success('图片上传成功')
      } catch (error) {
        console.error('图片上传失败:', error)
        ElMessage.error('图片上传失败')
      }
    }
  })
}

async function handleSubmit() {
  // 验证
  if (!form.value.title.trim()) {
    ElMessage.warning('请输入标题')
    return
  }
  if (!form.value.category_id) {
    ElMessage.warning('请选择版块')
    return
  }
  if (!form.value.content || form.value.content.trim() === '' || form.value.content === '<p><br></p>') {
    ElMessage.warning('请输入内容')
    return
  }

  submitting.value = true
  try {
    await api.posts.create(form.value)
    ElMessage.success('发帖成功')
    router.push('/')
  } catch (error) {
    console.error('发帖失败:', error)
    ElMessage.error(error.response?.data?.detail || '发帖失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style lang="scss" scoped>
.create-post {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;

  h2 {
    margin-bottom: 20px;
    color: #333;
  }

  .editor-container {
    width: 100%;
    min-height: 300px;

    :deep(.ql-editor) {
      min-height: 300px;
      font-size: 15px;
      line-height: 1.8;
      
      img {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 10px 0;
      }
    }

    :deep(.ql-toolbar.ql-snow) {
      border: 1px solid #dcdfe6;
      border-radius: 4px 4px 0 0;
      background: #fafafa;
    }

    :deep(.ql-container.ql-snow) {
      border: 1px solid #dcdfe6;
      border-top: none;
      border-radius: 0 0 4px 4px;
    }

    :deep(.ql-editor.ql-blank::before) {
      color: #a8abb2;
      font-style: normal;
    }
  }
}
</style>
