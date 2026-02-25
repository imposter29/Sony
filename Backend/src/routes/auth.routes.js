const express = require("express");
const { signup, login, logout } = require("../controllers/auth.controller");
const authMiddleware = require("../middleware/auth.middleware");

const router = express.Router();

// POST /api/auth/signup
router.post("/signup", signup);

// POST /api/auth/login
router.post("/login", login);

// POST /api/auth/logout  (requires valid token)
router.post("/logout", authMiddleware, logout);

module.exports = router;
