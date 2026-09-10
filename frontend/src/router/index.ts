import { createRouter, createWebHistory } from 'vue-router'

import { useClassificationStore } from '@/stores/classification'
import { useScanStore } from '@/stores/scan'
import { useUiStore } from '@/stores/ui'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
    meta: { title: '시작' },
  },
  {
    path: '/scan',
    name: 'scan',
    component: () => import('@/views/ScanResultView.vue'),
    meta: { title: '스캔 결과', requires: 'entries' },
  },
  {
    path: '/directory-graph',
    name: 'directory-graph',
    component: () => import('@/views/DirectoryGraphView.vue'),
    meta: { title: '디렉토리 구조/연관도', requires: 'entries' },
  },
  {
    path: '/content-graph',
    name: 'content-graph',
    component: () => import('@/views/ContentGraphView.vue'),
    meta: { title: '파일 연관도', requires: 'entries' },
  },
  {
    path: '/rename',
    name: 'rename',
    component: () => import('@/views/RenameView.vue'),
    meta: { title: '이름 일괄 변경', requires: 'entries' },
  },
  {
    path: '/classify',
    name: 'classify',
    component: () => import('@/views/ClassifyView.vue'),
    meta: { title: '분류 실행', requires: 'entries' },
  },
  {
    path: '/proposal',
    name: 'proposal',
    component: () => import('@/views/ProposalEditView.vue'),
    meta: { title: '제안 편집', requires: 'proposal' },
  },
  {
    path: '/apply',
    name: 'apply',
    component: () => import('@/views/ApplyView.vue'),
    meta: { title: '적용', requires: 'proposal' },
  },
  {
    path: '/versions',
    name: 'versions',
    component: () => import('@/views/VersionsView.vue'),
    meta: { title: '버전 관리', requires: 'root' },
  },
  {
    path: '/templates',
    name: 'templates',
    component: () => import('@/views/TemplatesView.vue'),
    meta: { title: '조직 표준 템플릿' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFoundView.vue'),
    meta: { title: '페이지 없음' },
  },
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach((to) => {
  const requires = to.meta.requires as string | undefined
  if (!requires) return true

  const scan = useScanStore()
  const classification = useClassificationStore()

  const satisfied =
    (requires === 'entries' && scan.hasScanned) ||
    (requires === 'proposal' && classification.hasResult) ||
    (requires === 'root' && !!scan.root)

  if (satisfied) return true

  const ui = useUiStore()
  const messages: Record<string, string> = {
    entries: '먼저 폴더를 스캔하세요.',
    proposal: '먼저 분류를 실행하세요.',
    root: '먼저 폴더를 스캔하세요.',
  }
  ui.pushToast(messages[requires] ?? '먼저 이전 단계를 완료하세요.', 'warning')
  return { name: 'home' }
})
