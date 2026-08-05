import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import 'cesium/Build/Cesium/Widgets/widgets.css'
import './styles/layout.scss'
import './styles/dashboard.scss'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
