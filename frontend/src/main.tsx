import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { I18nProvider } from './i18n/context'
import { CodiProvider } from './lib/codi'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <I18nProvider>
      <CodiProvider>
        <App />
      </CodiProvider>
    </I18nProvider>
  </StrictMode>,
)
