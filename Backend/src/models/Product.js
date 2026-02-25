const mongoose = require("mongoose");

// ── Camera Specs Sub-Schema (embedded, no separate _id) ─────────────────────
const cameraSpecsSchema = new mongoose.Schema(
  {
    sensorType: { type: String, trim: true },
    sensorSize: { type: String, trim: true },
    resolutionMP: { type: Number },
    lensMount: { type: String, trim: true },
    videoResolution: { type: String, trim: true },
    isoRange: { type: String, trim: true },
    burstRate: { type: String, trim: true },
    weight: { type: String, trim: true },
  },
  { _id: false }
);

// ── Product Schema ──────────────────────────────────────────────────────────
const productSchema = new mongoose.Schema(
  {
    title: {
      type: String,
      required: [true, "Product title is required"],
      trim: true,
    },
    slug: {
      type: String,
      required: [true, "Product slug is required"],
      unique: true,
      lowercase: true,
      trim: true,
    },
    brand: {
      type: String,
      default: "Sony",
      trim: true,
    },
    description: {
      type: String,
      trim: true,
      default: "",
    },
    category: {
      type: String,
      trim: true,
      index: true,
    },
    price: {
      type: Number,
      required: [true, "Product price is required"],
      min: [0, "Price cannot be negative"],
    },
    salePrice: {
      type: Number,
      min: [0, "Sale price cannot be negative"],
      default: null,
    },
    stock: {
      type: Number,
      required: [true, "Stock quantity is required"],
      min: [0, "Stock cannot be negative"],
      default: 0,
    },
    images: {
      type: [String],
      default: [],
    },
    cameraSpecs: {
      type: cameraSpecsSchema,
      default: null,
    },
    tags: {
      type: [String],
      default: [],
    },
    rating: {
      type: Number,
      default: 0,
      min: 0,
      max: 5,
    },
    reviewCount: {
      type: Number,
      default: 0,
      min: 0,
    },
  },
  {
    timestamps: true,
  }
);

// ── Text Index: enables $text search on title and tags ──────────────────────
productSchema.index({ title: "text", tags: "text" });

const Product = mongoose.model("Product", productSchema);

module.exports = Product;
