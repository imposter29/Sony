const mongoose = require("mongoose");

const blacklistedTokenSchema = new mongoose.Schema({
  token: {
    type: String,
    required: true,
    unique: true,
  },
  expiresAt: {
    type: Date,
    required: true,
    index: { expires: 0 }, // TTL index — MongoDB auto-deletes expired docs
  },
});

const BlacklistedToken = mongoose.model(
  "BlacklistedToken",
  blacklistedTokenSchema
);

module.exports = BlacklistedToken;
