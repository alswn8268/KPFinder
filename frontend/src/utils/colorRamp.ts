// 포인트 컬러 하나(hex)로부터 --color-accent-* 셰이드 전체를 런타임에 계산해
// document.documentElement에 CSS 커스텀 프로퍼티로 적용한다. 외부 색상 라이브러리 없이
// 순수 HSL 변환만 사용한다(디자인 토큰 문서의 "런타임에도 전파" 요구사항).

export const DEFAULT_ACCENT = '#5B4FE9'

interface Hsl {
  h: number
  s: number
  l: number
}

function hexToHsl(hex: string): Hsl {
  const clean = hex.replace('#', '')
  const r = parseInt(clean.substring(0, 2), 16) / 255
  const g = parseInt(clean.substring(2, 4), 16) / 255
  const b = parseInt(clean.substring(4, 6), 16) / 255

  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  const l = (max + min) / 2
  let h = 0
  let s = 0

  if (max !== min) {
    const d = max - min
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min)
    switch (max) {
      case r:
        h = (g - b) / d + (g < b ? 6 : 0)
        break
      case g:
        h = (b - r) / d + 2
        break
      default:
        h = (r - g) / d + 4
    }
    h /= 6
  }
  return { h: h * 360, s: s * 100, l: l * 100 }
}

function hslToHex({ h, s, l }: Hsl): string {
  const sNorm = s / 100
  const lNorm = l / 100
  const c = (1 - Math.abs(2 * lNorm - 1)) * sNorm
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1))
  const m = lNorm - c / 2
  let [r, g, b] = [0, 0, 0]

  if (h < 60) [r, g, b] = [c, x, 0]
  else if (h < 120) [r, g, b] = [x, c, 0]
  else if (h < 180) [r, g, b] = [0, c, x]
  else if (h < 240) [r, g, b] = [0, x, c]
  else if (h < 300) [r, g, b] = [x, 0, c]
  else [r, g, b] = [c, 0, x]

  const toHex = (v: number) =>
    Math.round((v + m) * 255)
      .toString(16)
      .padStart(2, '0')
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`
}

// 500이 입력 hex 그대로. 나머지는 밝기를 조절해 생성한다.
const LIGHTNESS_BY_SHADE: Record<string, number> = {
  '50': 96,
  '100': 92,
  '200': 85,
  '300': 74,
  '400': 62,
  '500': -1, // 원본 그대로
  '600': -1,
  '700': -1,
}

export function computeAccentRamp(hex: string): Record<string, string> {
  const base = hexToHsl(hex)
  const ramp: Record<string, string> = { '500': hex }
  for (const shade of ['50', '100', '200', '300', '400']) {
    const l = LIGHTNESS_BY_SHADE[shade]
    ramp[shade] = hslToHex({ h: base.h, s: Math.max(base.s * 0.9, 40), l })
  }
  ramp['600'] = hslToHex({ h: base.h, s: Math.min(base.s * 1.05, 100), l: Math.max(base.l - 10, 20) })
  ramp['700'] = hslToHex({ h: base.h, s: Math.min(base.s * 1.05, 100), l: Math.max(base.l - 22, 14) })
  ramp['soft'] = hslToHex({ h: base.h, s: Math.max(base.s * 0.5, 30), l: 95 })
  return ramp
}

export function applyAccentColor(hex: string) {
  if (typeof document === 'undefined') return
  const ramp = computeAccentRamp(hex)
  const root = document.documentElement
  for (const [shade, value] of Object.entries(ramp)) {
    root.style.setProperty(`--color-accent-${shade}`, value)
  }
}
