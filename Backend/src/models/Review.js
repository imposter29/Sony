const mongoose = require("mongoose");

const reviewSchema = new mongoose.Schema(
  {
    user: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: [true, "Review must belong to a user"],
    },
    product: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Product",
      required: [true, "Review must be linked to a product"],
    },
    rating: {
      type: Number,
      required: [true, "Rating is required"],
      min: [1, "Rating must be at least 1"],
      max: [5, "Rating cannot exceed 5"],
    },
    comment: {
      type: String,
      trim: true,
      default: "",
    },
  },
  {
    timestamps: true,
  }
);

// ── Compound Index: one review per user per product ─────────────────────────
reviewSchema.index({ user: 1, product: 1 }, { unique: true });

// ── Index for fast lookups by product ───────────────────────────────────────
reviewSchema.index({ product: 1 });

const Review = mongoose.model("Review", reviewSchema);

module.exports = Review;
