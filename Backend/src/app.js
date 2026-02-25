const express = require("express");
const authRoutes = require("./routes/auth.routes");

const app = express();

// ── Global Middleware ─────────────────────────────────────────────────────────
app.use(express.json());           // Parse JSON request bodies
app.use(express.urlencoded({ extended: true })); // Parse URL-encoded bodies

// ── Health Check ──────────────────────────────────────────────────────────────
app.get("/api/health", (req, res) => {
  res.status(200).json({ success: true, message: "Server is running 🚀" });
});

// ── API Routes ────────────────────────────────────────────────────────────────
app.use("/api/auth", authRoutes);

// ── 404 Handler ───────────────────────────────────────────────────────────────
app.use((req, res) => {
  res.status(404).json({ success: false, message: "Route not found" });
});

// ── Global Error Handler ──────────────────────────────────────────────────────
// eslint-disable-next-line no-unused-vars
app.use((err, req, res, next) => {
  console.error("Unhandled error:", err);
  res.status(err.status || 500).json({
    success: false,
    message: err.message || "Internal server error",
  });
});

module.exports = app;
