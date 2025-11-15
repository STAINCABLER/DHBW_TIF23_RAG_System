export const UI_EVENTS = {
  NEW_CHAT: 'ui:new-chat',
} as const

type UiEventName = (typeof UI_EVENTS)[keyof typeof UI_EVENTS]

export function emitUiEvent(name: UiEventName) {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent(name))
}

type UiEventHandler = () => void

export function subscribeToUiEvent(name: UiEventName, handler: UiEventHandler) {
  if (typeof window === 'undefined') return () => {}
  window.addEventListener(name, handler)
  return () => window.removeEventListener(name, handler)
}
