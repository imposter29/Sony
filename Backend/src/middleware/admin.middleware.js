// ─────────────────────────────────────────────────────────────────────────────
// @desc    Restrict access to admin-only routes
// @usage   router.get("/admin-only", authMiddleware, adminMiddleware, handler)
// @note    Must be used AFTER authMiddleware (req.user must already exist)
// ─────────────────────────────────────────────────────────────────────────────
const adminMiddleware = (req, res, next) => {
  if (!req.user || req.user.isAdmin !== true) {
    return res.status(403).json({
      success: false,
      message: "Forbidden. Admin access only.",
    });
  }

  next();
};

module.exports = adminMiddleware;
