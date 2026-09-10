// api/schemas.py 의 Pydantic 모델과 1:1로 대응하는 TypeScript 타입.

export interface FileEntry {
  path: string
  relative_path: string
  name: string
  ext: string
  size: number
  modified: string
  file_hash: string
  summary: string
  summary_status: string
}

export interface AssignmentInfo {
  dst: string
  reason: string
  confidence: '높음' | '보통' | '낮음' | string
  source: 'rule' | 'ai' | 'user' | 'fallback' | 'rename' | string
}

export interface RejectedItem {
  src: string
  dst: string
  reason: string
}

export interface OverrideInfo {
  dst?: string | null
  excluded: boolean
}

export interface EnvItem {
  item: string
  status: '정상' | '주의' | '오류' | string
  detail: string
  action: string
}

export interface EnvCheckResponse {
  items: EnvItem[]
  has_blocking_error: boolean
}

export interface TemplateFolder {
  path: string
  description: string
}

export interface KeywordRule {
  keywords: string[]
  target: string
}

export interface OrgTemplate {
  name: string
  version: string
  author: string
  folders: TemplateFolder[]
  keyword_rules: KeywordRule[]
}

export interface DuplicateGroup {
  hash: string
  files: FileEntry[]
}

export interface ScanErrorItem {
  path: string
  reason: string
}

export interface ScanResponse {
  scan_root: string
  entries: FileEntry[]
  duplicate_groups: DuplicateGroup[]
  errors: ScanErrorItem[]
  total_files: number
}

export interface ScanOptions {
  exclude_dirs: string[]
  exclude_exts: string[]
  include_hidden: boolean
  max_file_size_mb: number | null
}

export interface CacheInfo {
  exists: boolean
  path: string
  entry_count: number
  created_at: string | null
  models_used: string[]
}

export interface ClassifyResponse {
  categories: string[]
  assignments: Record<string, AssignmentInfo>
  notes: string
  ai_failed: boolean
  error_detail: string
}

export interface SuggestStructureResponse {
  categories: string[]
  assignments: Record<string, AssignmentInfo>
  notes: string
}

export interface SimilarPair {
  a: string
  b: string
  score: number
}

export interface ValidateResponse {
  valid: Record<string, AssignmentInfo>
  merged: Record<string, AssignmentInfo>
  rejected: RejectedItem[]
  excluded: string[]
  final_state: Record<string, string>[]
  tree_before: string
  tree_after: string
}

export type RenameMode = 'find_replace' | 'prefix' | 'suffix' | 'numbering'

export interface RenameRule {
  mode: RenameMode
  find?: string
  replace?: string
  text?: string
  base_name?: string
  start?: number
  digits?: number
}

export interface RenamePreviewRow {
  src: string
  old_name: string
  new_name: string
  dst: string
  changed: boolean
}

export interface PlanItem {
  src: string
  dst: string
  rel_src: string
  rel_dst: string
}

export interface VersionInfo {
  version_id: string
  timestamp: string
  note: string
  files_moved: number
  log_path: string
  restored: boolean
  can_restore: boolean
  restore_blocked_reason: string
}

export interface ApplyResponse {
  log_path: string
  moved_count: number
  plan_size: number
  version: VersionInfo
}

export interface GraphNode {
  id: string
  ext: string
  size: number
  file_count: number
}

export interface GraphEdge {
  source: string
  target: string
  weight: number
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface TreeNode {
  id: string
  file_count: number
  children: TreeNode[]
}

export interface StructureCopyResponse {
  count: number
  created: string[]
  skipped: string[]
}

export interface InfoResponse {
  program_version: string
  default_model: string
}

export interface SampleDataResponse {
  output_dir: string
  created_count: number
  already_existed: boolean
  dataset: string
  label: string
}

export interface SampleDatasetInfo {
  key: string
  label: string
  description: string
  output_dir: string
}

export interface OllamaModelInfo {
  name: string
  size_mb: number
  parameter_size: string
  quantization: string
}

export interface ModelsResponse {
  connected: boolean
  models: OllamaModelInfo[]
}

export interface RecommendedModelInfo {
  name: string
  label: string
  tier: string
  size_gb: number
  description: string
  installed: boolean
}

export interface PullProgressEvent {
  status: string
  digest?: string
  total?: number
  completed?: number
  error?: string
}
