// ─────────────────────────────────────────────────────────────────────────────
// Seed Script: Create a Super Admin
// Run with:  node src/scripts/createAdmin.js
// ─────────────────────────────────────────────────────────────────────────────

const dotenv = require("dotenv");
dotenv.config(); // Load .env from project root

const mongoose = require("mongoose");
const User = require("../models/User");

const ADMIN_NAME = "Super Admin";
const ADMIN_EMAIL = "admin@sonystore.com";
const ADMIN_PASSWORD = "Admin@123"; // Change this before running in production!

const createAdmin = async () => {
  try {
    // 1. Connect to MongoDB
    await mongoose.connect(process.env.MONGO_URI);
    console.log("✅  Connected to MongoDB");

    // 2. Check if admin already exists
    const existingAdmin = await User.findOne({ email: ADMIN_EMAIL });
    if (existingAdmin) {
      console.log("⚠️  Admin account already exists. Aborting.");
      process.exit(0);
    }

    // 3. Create admin user (password is hashed via pre-save hook)
    const admin = await User.create({
      name: ADMIN_NAME,
      email: ADMIN_EMAIL,
      password: ADMIN_PASSWORD,
      isAdmin: true, // Only way to set isAdmin = true (manual / seed)
    });

    console.log("🎉  Super Admin created successfully!");
    console.log(`    Name:  ${admin.name}`);
    console.log(`    Email: ${admin.email}`);
    console.log(`    Admin: ${admin.isAdmin}`);

    process.exit(0);
  } catch (error) {
    console.error("❌  Error creating admin:", error.message);
    process.exit(1);
  }
};

createAdmin();
