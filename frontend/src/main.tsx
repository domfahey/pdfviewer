import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.tsx';

// Prevent custom element redefinition errors from external sources
const originalDefine = customElements.define;
customElements.define = function(name: string, constructor: CustomElementConstructor, options?: ElementDefinitionOptions) {
  try {
    return originalDefine.call(this, name, constructor, options);
  } catch (error) {
    if (error instanceof DOMException && error.message.includes('already been defined')) {
      console.warn(`Custom element '${name}' already defined, skipping redefinition`);
      return;
    }
    throw error;
  }
};

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
