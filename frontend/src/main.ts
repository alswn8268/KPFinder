import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import { router } from './router'
import { onApiError } from '@/api/client'
import { useUiStore } from '@/stores/ui'
import '@/styles/main.scss'

const app = createApp(App)
app.use(createPinia())
app.use(router)

const ui = useUiStore()
onApiError((message) => ui.pushToast(message, 'error', 6000))

app.mount('#app')
