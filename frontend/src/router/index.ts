import { createRouter, createWebHistory } from "vue-router"

const Home = () => import("../pages/Home.vue")
const Search = () => import("../pages/Search.vue")
const Mood = () => import("../pages/Mood.vue")
const Details = () => import("../pages/Details.vue")
const Chatbot = () => import("../pages/Chatbot.vue")

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: Home },
    { path: "/search", name: "search", component: Search },
    {
      path: "/mood",
      name: "mood",
      component: Mood,
      props: route => ({
        qMood: route.query.mood,
        qPage: route.query.page ? Number(route.query.page) : undefined,
        qRegion: route.query.region
      })
    },
    { path: "/details/:id", name: "details", component: Details, props: true },
    { path: "/chatbot", name: "chatbot", component: Chatbot }
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

export default router
