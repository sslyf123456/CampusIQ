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
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/login',
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  const requiresAuth = to.matched.some(r => r.meta.requiresAuth)
  const isGuest = to.matched.some(r => r.meta.guest)

  if (requiresAuth && !auth.isLoggedIn) {
    next('/login')
  } else if (isGuest && auth.isLoggedIn) {
    next('/')
  } else {
    next()
  }
})

export default router
