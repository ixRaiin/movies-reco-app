import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'home', component: () => import('../pages/Home.vue') },
  { path: '/search', name: 'search', component: () => import('../pages/Search.vue') },
  { path: '/details/:id', name: 'details', component: () => import('../pages/Details.vue') },
  { path: '/recommend', name: 'recommend', component: () => import('../pages/Recommend.vue') },
  { path: '/mood', name: 'mood', component: () => import('../pages/Mood.vue') },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('../pages/NotFound.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
