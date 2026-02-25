const dotenv = require("dotenv");
dotenv.config(); // Load .env variables before anything else

const app = require("./app");
const connectDB = require("./config/db");
const validateEnv = require("./config/env");

// Validate all required env vars are present before starting
validateEnv();

const PORT = process.env.PORT || 5000;

// Connect to MongoDB then start the HTTP server
const startServer = async () => {
  await connectDB();

  app.listen(PORT, () => {
    console.log(`🚀  Server running on http://localhost:${PORT}`);
    console.log(`📌  Auth endpoints:`);
    console.log(`    POST http://localhost:${PORT}/api/auth/signup`);
    console.log(`    POST http://localhost:${PORT}/api/auth/login`);
  });
};

startServer();
