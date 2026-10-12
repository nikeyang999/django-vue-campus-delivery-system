<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import api from './api'

const user = ref(JSON.parse(localStorage.getItem('campus_user') || 'null'))
const authMode = ref('login')
const authForm = reactive({ username: '', password: '', phone: '', role: 'student' })
const authError = ref('')
const loading = ref(false)
const view = ref('orders')
const orders = ref([])
const stats = ref({ total: 0, pending: 0, delivering: 0, completed: 0, total_fee: '0' })
const message = ref('')
const orderForm = reactive({ order_type: 'package', pickup_address: '', delivery_address: '', item_description: '', fee: 3, note: '' })

const roleLabel = computed(() => ({ student: '学生', courier: '配送员', admin: '管理员' }[user.value?.role] || '用户'))
const isLoggedIn = computed(() => !!user.value)
const canCreate = computed(() => user.value?.role === 'student')

const showMessage = (text) => { message.value = text; setTimeout(() => message.value = '', 2600) }
const setAuth = (data) => {
  localStorage.setItem('campus_token', data.token)
  localStorage.setItem('campus_user', JSON.stringify(data.user))
  user.value = data.user
  view.value = 'orders'
}

async function submitAuth() {
  authError.value = ''; loading.value = true
  try {
    const url = authMode.value === 'login' ? '/auth/login/' : '/auth/register/'
    const { data } = await api.post(url, authForm)
    setAuth(data)
    await loadOrders()
  } catch (e) { authError.value = e.response?.data?.detail || e.response?.data?.non_field_errors?.[0] || '操作失败，请检查输入' }
  finally { loading.value = false }
}

function logout() {
  localStorage.removeItem('campus_token'); localStorage.removeItem('campus_user'); user.value = null; orders.value = []
}

async function loadOrders() {
  if (!user.value) return
  try { orders.value = (await api.get('/orders/')).data; stats.value = (await api.get('/orders/stats/')).data }
  catch (e) { if (e.response?.status === 401) logout() }
}

async function createOrder() {
  try { await api.post('/orders/', orderForm); Object.assign(orderForm, { order_type: 'package', pickup_address: '', delivery_address: '', item_description: '', fee: 3, note: '' }); showMessage('订单发布成功'); await loadOrders() }
  catch (e) { showMessage(e.response?.data?.detail || '发布失败，请检查表单') }
}

async function acceptOrder(order) { try { await api.post(`/orders/${order.id}/accept/`); showMessage('接单成功'); await loadOrders() } catch (e) { showMessage(e.response?.data?.detail || '接单失败') } }
async function changeStatus(order, status) { try { await api.post(`/orders/${order.id}/change_status/`, { status }); showMessage('订单状态已更新'); await loadOrders() } catch (e) { showMessage(e.response?.data?.detail || '状态更新失败') } }
function statusClass(status) { return `status-${status}` }
function nextStatus(order) { return { accepted: 'picking', picking: 'delivering', delivering: 'completed' }[order.status] }
function nextLabel(order) { return { accepted: '开始取件', picking: '开始配送', delivering: '确认送达' }[order.status] }

onMounted(loadOrders)
</script>

<template>
  <div v-if="!isLoggedIn" class="auth-page">
    <div class="auth-card">
      <div class="brand-mark">校</div>
      <h1>校园配送服务管理系统</h1>
      <p class="muted">让校园生活的每一次取件都更简单</p>
      <div class="tabs"><button :class="{active: authMode === 'login'}" @click="authMode = 'login'">登录</button><button :class="{active: authMode === 'register'}" @click="authMode = 'register'">注册</button></div>
      <form @submit.prevent="submitAuth">
        <label>用户名<input v-model="authForm.username" required placeholder="请输入用户名" /></label>
        <label>密码<input v-model="authForm.password" required type="password" placeholder="至少6位" /></label>
        <label v-if="authMode === 'register'">手机号<input v-model="authForm.phone" placeholder="方便配送联系" /></label>
        <label v-if="authMode === 'register'">注册身份<select v-model="authForm.role"><option value="student">学生</option><option value="courier">配送员</option></select></label>
        <p v-if="authError" class="error">{{ authError }}</p><button class="primary full" :disabled="loading">{{ loading ? '处理中...' : authMode === 'login' ? '登录系统' : '创建账号' }}</button>
      </form>
      <p class="demo-tip">演示账号：student / courier / admin，密码均为 123456</p>
    </div>
  </div>
  <div v-else class="layout">
    <aside class="sidebar">
      <div class="side-brand"><span>校</span><div><strong>校园配送</strong><small>服务管理系统</small></div></div>
      <nav><button :class="{selected: view === 'orders'}" @click="view = 'orders'; loadOrders()">📦 订单中心</button><button v-if="canCreate" :class="{selected: view === 'create'}" @click="view = 'create'">✚ 发布配送</button><button v-if="user.role === 'admin'" :class="{selected: view === 'stats'}" @click="view = 'stats'; loadOrders()">▥ 数据看板</button></nav>
      <div class="side-bottom"><div class="avatar">{{ user.username[0].toUpperCase() }}</div><div class="user-mini"><strong>{{ user.username }}</strong><small>{{ roleLabel }}</small></div><button class="logout" @click="logout">退出</button></div>
    </aside>
    <main class="main"><header><div><p class="eyebrow">{{ user.role === 'admin' ? 'ADMIN CONSOLE' : 'CAMPUS SERVICE' }}</p><h2>{{ view === 'create' ? '发布配送需求' : view === 'stats' ? '运营数据看板' : '订单中心' }}</h2></div><div class="campus-tag">📍 主校区</div></header>
      <div v-if="message" class="toast">{{ message }}</div>
      <section v-if="view === 'orders'" class="content"><div class="stat-grid"><div class="stat-card"><span>全部订单</span><strong>{{ stats.total }}</strong><em>累计服务</em></div><div class="stat-card orange"><span>待接单</span><strong>{{ stats.pending }}</strong><em>等待配送员</em></div><div class="stat-card blue"><span>进行中</span><strong>{{ stats.delivering }}</strong><em>配送任务</em></div><div class="stat-card green"><span>已完成</span><strong>{{ stats.completed }}</strong><em>服务完成</em></div></div>
        <div class="section-head"><div><h3>{{ user.role === 'courier' ? '可接订单与我的任务' : user.role === 'admin' ? '全部配送订单' : '我的配送订单' }}</h3><p>实时查看订单状态和配送进度</p></div><button v-if="canCreate" class="primary" @click="view = 'create'">发布新订单</button></div>
        <div v-if="!orders.length" class="empty">暂时没有订单，发布一个配送需求吧。</div><div v-else class="order-list"><article v-for="order in orders" :key="order.id" class="order-card"><div class="order-top"><div><span class="order-no">{{ order.order_no }}</span><span class="type-pill">{{ order.order_type_label }}</span></div><span :class="['status', statusClass(order.status)]">{{ order.status_label }}</span></div><div class="route"><div><small>取件位置</small><strong>{{ order.pickup_address }}</strong></div><div class="arrow">→</div><div><small>送达位置</small><strong>{{ order.delivery_address }}</strong></div></div><div class="order-meta"><span>物品：{{ order.item_description }}</span><span>费用：¥{{ order.fee }}</span><span v-if="order.courier_name">配送员：{{ order.courier_name }}</span></div><div class="order-actions"><button v-if="user.role === 'courier' && order.status === 'pending'" class="primary small" @click="acceptOrder(order)">立即接单</button><button v-if="user.role === 'courier' && nextStatus(order)" class="secondary small" @click="changeStatus(order, nextStatus(order))">{{ nextLabel(order) }}</button><button v-if="user.role === 'student' && ['pending','accepted'].includes(order.status)" class="danger small" @click="changeStatus(order, 'cancelled')">取消订单</button><span v-if="order.note" class="note">备注：{{ order.note }}</span></div></article></div>
      </section>
      <section v-if="view === 'create'" class="content narrow"><div class="form-card"><div class="form-intro"><div class="icon-box">🚴</div><div><h3>发布校园配送</h3><p>填写取件和送达信息，配送员会尽快接单。</p></div></div><form class="grid-form" @submit.prevent="createOrder"><label>订单类型<select v-model="orderForm.order_type"><option value="package">快递代取</option><option value="food">外卖配送</option><option value="item">物品帮送</option><option value="other">其他服务</option></select></label><label>配送费用<input v-model="orderForm.fee" type="number" min="1" step="0.5" required /></label><label class="wide">取件地址<input v-model="orderForm.pickup_address" required placeholder="例如：东门菜鸟驿站" /></label><label class="wide">送达地址<input v-model="orderForm.delivery_address" required placeholder="例如：南区3栋205室" /></label><label class="wide">物品描述<input v-model="orderForm.item_description" required placeholder="例如：教材、日用品" /></label><label class="wide">备注信息<textarea v-model="orderForm.note" rows="4" placeholder="可填写取件码、送达要求等"></textarea></label><div class="form-footer"><button type="button" class="secondary" @click="view = 'orders'">取消</button><button class="primary">确认发布</button></div></form></div></section>
      <section v-if="view === 'stats'" class="content"><div class="stat-grid big"><div class="stat-card"><span>注册学生</span><strong>{{ stats.students || 0 }}</strong><em>服务用户</em></div><div class="stat-card blue"><span>配送员</span><strong>{{ stats.couriers || 0 }}</strong><em>认证人员</em></div><div class="stat-card green"><span>已完成订单</span><strong>{{ stats.completed }}</strong><em>累计完成</em></div><div class="stat-card purple"><span>完成金额</span><strong>¥{{ stats.total_fee }}</strong><em>已完成订单费用</em></div></div><div class="section-head"><div><h3>系统运营概览</h3><p>当前账号可见范围内的订单统计</p></div></div><div class="insight-card"><div><strong>订单完成率</strong><p>已完成订单 / 全部订单</p></div><div class="progress"><span :style="{width: `${stats.total ? Math.round(stats.completed / stats.total * 100) : 0}%`}"></span></div><strong>{{ stats.total ? Math.round(stats.completed / stats.total * 100) : 0 }}%</strong></div></section>
    </main>
  </div>
</template>

