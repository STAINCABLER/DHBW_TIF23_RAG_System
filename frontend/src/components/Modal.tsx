import { useEffect } from 'react'
import type { MouseEvent, ReactNode } from 'react'
import { X } from 'lucide-react'
import { createPortal } from 'react-dom'

const MODAL_ROOT_ID = 'modal-root'

type ModalProps = {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
}

function ensureModalRoot() {
  if (typeof document === 'undefined') return null
  const existing = document.getElementById(MODAL_ROOT_ID)
  if (existing) return existing
  const element = document.createElement('div')
  element.id = MODAL_ROOT_ID
  document.body.appendChild(element)
  return element
}

export function Modal({ open, onClose, title, children }: ModalProps) {
  const modalRoot = ensureModalRoot()

  useEffect(() => {
    if (!open) return
    const handler = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  if (!open || !modalRoot) return null

  const handleOverlayClick = () => onClose()

  const stopPropagation = (event: MouseEvent) => event.stopPropagation()

  return createPortal(
    <div className="modal-overlay" role="presentation" onClick={handleOverlayClick}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={stopPropagation}
      >
        <header className="modal__header">
          <h2 className="modal__title u-no-select">{title}</h2>
          <button type="button" className="btn btn--ghost btn--icon" onClick={onClose} aria-label="Close dialog">
            <X size={18} aria-hidden />
          </button>
        </header>
        <div className="modal__body">{children}</div>
      </div>
    </div>,
    modalRoot,
  )
}
