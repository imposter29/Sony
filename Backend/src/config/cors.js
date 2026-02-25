/**
 * CORS configuration options.
 * Extend allowedOrigins with your actual frontend URLs in production.
 */
const corsOptions = {
  origin: process.env.CLIENT_ORIGIN || "*",
  methods: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
  allowedHeaders: ["Content-Type", "Authorization"],
  credentials: true,
};

module.exports = corsOptions;
