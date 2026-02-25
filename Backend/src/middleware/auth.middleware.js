const jwt = require("jsonwebtoken");
const User = require("../models/User");

// ─────────────────────────────────────────────────────────────────────────────
// @desc    Protect routes — verify Bearer JWT and attach user to req.user
// @usage   router.get("/protected", authMiddleware, handler)
// ─────────────────────────────────────────────────────────────────────────────
const authMiddleware = async (req, res, next) => {
  try {
    // 1. Read the Authorization header
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return res.status(401).json({
        success: false,
        message: "Access denied. No token provided.",
      });
    }

    // 2. Extract token from "Bearer <token>"
    const token = authHeader.split(" ")[1];

    // 3. Verify the token
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    // 4. Fetch the user from DB and attach to request (excluding password)
    const user = await User.findById(decoded.id);
    if (!user) {
      return res.status(401).json({
        success: false,
        message: "User belonging to this token no longer exists.",
      });
    }

    req.user = user;
    next();
  } catch (error) {
    // Handles TokenExpiredError, JsonWebTokenError, etc.
    return res.status(401).json({
      success: false,
      message: "Invalid or expired token.",
    });
  }
};

module.exports = authMiddleware;
