import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// IMPORTANT: base must match your repo name on GitHub Pages
// Your Pages URL: https://my-project4101.github.io/changeanyfile/
// So base path is "/changeanyfile/"
export default defineConfig({
  plugins: [react()],
  base: "/changeanyfile/",
});
