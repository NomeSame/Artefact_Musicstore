// Product media: released prototype illustrations with the required AI label.
// Falls back to the vector art in art.js for products without an exported image.
import {instrument} from "./art.js";

const LABEL = "Ilustração gerada por IA. Pode diferir do produto real.";
let media = {};

export async function loadProductMedia() {
  try {
    const response = await fetch("/static/products/index.json", {cache: "no-cache"});
    media = response.ok ? await response.json() : {};
  } catch {
    media = {};
  }
  return media;
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
}

export function hasProductImage(productId) {
  return Boolean(media[String(productId)]);
}

export function productMedia(product) {
  const entry = media[String(product.product_id)];
  // Unresolved catalogue identities must never imply a specific generated model,
  // even when an older image manifest is still cached in this session.
  if (!entry || product.catalogue_conflict) {
    return '<div class="media-frame media-vector">' + instrument(product.category_id, product.product_id) + '</div>';
  }
  const details = (entry.tolerated_differences || []).join("; ");
  const title = details ? LABEL + " Differences: " + details : LABEL;
  return '<figure class="media-frame media-photo">' +
    '<img class="product-photo" src="/static/products/' + esc(entry.file) + '"' +
    ' alt="' + esc(product.name + " — " + LABEL) + '" title="' + esc(title) + '"' +
    ' loading="lazy" decoding="async">' +
    '<figcaption class="ai-label">' + esc(LABEL) + '</figcaption>' +
    '</figure>';
}
