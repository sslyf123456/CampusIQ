import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/',
      component: () => import('@/components/layout/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: '/profile',
        },
        {
          path: 'profile',
          name: 'Profile',
          component: () => import('@/views/ProfileView.vue'),
        },
        {
          path: 'students',
          name: 'Students',
          component: () => import('@/views/StudentManageView.vue'),
          meta: { role: 'admin' },
        },
        {
          path: 'schedule',
          name: 'Schedule',
          component: () => import('@/views/ScheduleView.vue'),
        },
        {
          path: 'repair',
          name: 'Repair',
          component: () => import('@/views/RepairView.vue'),
        },
        {
          path: 'scholarship',
          name: 'Scholarship',
          component: () => import('@/views/ScholarshipView.vue'),
        },
        {
          path: 'notice',
          name: 'Notice',
          component: () => import('@/views/NoticeView.vue'),
        },
        {
          path: 'chat',
          name: 'Chat',
          component: () => import('@/views/ChatView.vue'),
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/login',
    },
  ],
})

router.beforeEach(async (to, _from, next) => {
  const auth = useAuthStore()
  const requiresAuth = to.matched.some(r => r.meta.requiresAuth)
  const isGuest = to.matched.some(r => r.meta.guest)

  if (requiresAuth && !auth.isLoggedIn) {
    next('/login')
  } else if (isGuest && auth.isLoggedIn) {
    next('/')
  } else if (auth.isLoggedIn && !auth.user) {
    try {
      await auth.fetchProfile()
      // 登录后补拉用户信息，再做角色守卫
      const requiredRole = to.meta.role as string | undefined
      if (requiredRole && auth.user?.role !== requiredRole) {
        next('/')
        return
      }
      next()
    } catch {
      await auth.logout()
      next('/login')
    }
  } else {
    const requiredRole = to.meta.role as string | undefined
    if (requiredRole && auth.user?.role !== requiredRole) {
      next('/')
      return
    }
    next()
  }
})

export default router
