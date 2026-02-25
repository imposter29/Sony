/**
 * Centralised environment variable validation.
 * Call this once at startup to catch missing config early.
 */
const validateEnv = () => {
  const required = ["MONGO_URI", "JWT_SECRET", "PORT"];

  required.forEach((key) => {
    if (!process.env[key]) {
      throw new Error(`Missing required environment variable: ${key}`);
    }
  });
};

module.exports = validateEnv;
