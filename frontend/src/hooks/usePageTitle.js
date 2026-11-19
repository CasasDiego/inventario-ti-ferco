import { useEffect } from 'react'

export const APP_TITLE = 'Ferco Assets'

// Pone el título de la pestaña del navegador, p. ej. "[ACTI-100] HP ALL IN ONE - Ferco Assets".
// Si title es vacío/null no cambia nada (deja que otro componente lo controle).
export default function usePageTitle(title) {
  useEffect(() => {
    if (title) document.title = `${title} - ${APP_TITLE}`
  }, [title])
}
