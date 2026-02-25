const mongoose = require("mongoose");

/**
 * Connects to MongoDB using the MONGO_URI environment variable.
 * Exits the process on failure to prevent the server running in a broken state.
 */
const connectDB = async () => {
  try {
    const conn = await mongoose.connect(process.env.MONGO_URI);
    console.log(`✅  MongoDB connected: ${conn.connection.host}`);
  } catch (error) {
    console.error(`❌  MongoDB connection failed: ${error.message}`);
    process.exit(1);
  }
};

module.exports = connectDB;
