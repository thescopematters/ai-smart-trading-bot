import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.jsx";
import { ToastProvider } from './context/ToastContext';
import { LoaderProvider } from './context/LoaderContext';

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <ToastProvider>
      <LoaderProvider>
          <App />
      </LoaderProvider>
    </ToastProvider>
  </StrictMode>,
);
