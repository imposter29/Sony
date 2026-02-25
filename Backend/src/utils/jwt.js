const jwt = require("jsonwebtoken");

/**
 * Generates a signed JWT for the given userId.
 * @param {string} userId - The MongoDB ObjectId of the user
 * @returns {string} Signed JWT token, expires in 7 days
 */
const generateToken = (userId) => {
  return jwt.sign({ id: userId }, process.env.JWT_SECRET, {
    expiresIn: "7d",
  });
};

module.exports = { generateToken };
