<template>
  <div class="login-page">
    <div class="login-bg">
      <div class="bg-shape shape-1" />
      <div class="bg-shape shape-2" />
      <div class="bg-shape shape-3" />
    </div>
    <div class="login-wrapper">
      <div class="login-brand">
        <div class="brand-icon">
          <el-icon :size="36"><Grid /></el-icon>
        </div>
        <h1>ERP 管理系统</h1>
        <p>Enterprise Resource Planning</p>
      </div>
      <div class="login-card">
        <div class="login-header">
          <h2>欢迎回来</h2>
          <p>请输入您的账号和密码</p>
        </div>
        <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="handleLogin">
          <el-form-item prop="username">
            <el-input
              v-model="form.username"
              placeholder="请输入账号"
              :prefix-icon="User"
              autocomplete="username"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              :prefix-icon="Lock"
              show-password
              autocomplete="current-password"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="loading" class="login-btn" @click="handleLogin">
              登 录
            </el-button>
          </el-form-item>
        </el-form>
      </div>
      <p class="login-footer">ERP System v1.0</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Grid } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const formRef = ref()
const loading = ref(false)
const form = ref({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  await formRef.value.validate()
  loading.value = true
  try {
    await auth.login(form.value.username, form.value.password)
    router.push('/')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #1e3a5f 100%);
}

/* 背景装饰 */
.login-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.bg-shape {
  position: absolute;
  border-radius: 50%;
  opacity: 0.08;
}
.shape-1 {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, #2563eb, transparent);
  top: -200px;
  right: -150px;
}
.shape-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #7c3aed, transparent);
  bottom: -100px;
  left: -80px;
}
.shape-3 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, #06b6d4, transparent);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.login-wrapper {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
}

/* 品牌区 */
.login-brand {
  text-align: center;
  color: #fff;
}
.brand-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.4);
}
.login-brand h1 {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 2px;
  margin: 0 0 6px;
}
.login-brand p {
  font-size: 13px;
  opacity: 0.5;
  letter-spacing: 3px;
  text-transform: uppercase;
  margin: 0;
}

/* 登录卡片 */
.login-card {
  width: 400px;
  padding: 36px 32px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}
.login-header {
  text-align: center;
  margin-bottom: 28px;
}
.login-header h2 {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 6px;
}
.login-header p {
  font-size: 13px;
  color: #94a3b8;
  margin: 0;
}

/* 登录按钮 */
.login-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 4px;
  border-radius: 8px;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  border: none;
}
.login-btn:hover {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
}

/* 底部文字 */
.login-footer {
  color: rgba(255, 255, 255, 0.3);
  font-size: 12px;
}
</style>
