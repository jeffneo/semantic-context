import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router";
import App from "./App";
import "./index.css";
import { startCustomer } from "./live/customer";
import { applyStoredTheme } from "./theme/useTheme";

applyStoredTheme(); // before first paint: no flash of the wrong palette
startCustomer(); // the customer for memory's examples; asking also wakes the way to the warehouse, so the first live example is not the first to use it

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
