// Product media: released prototype illustrations with the required AI label.
// Falls back to the vector art in art.js for products without an exported image.
import {instrument} from "./art.js";
import {text} from "./i18n.js";

const LABEL = "AI-generated illustration. It may differ from the actual product.";
let media = {};

// Also update images in an already-open preview when the site language changes.
document.addEventListener("language-changed", () => {
  const label = text(LABEL);
  document.querySelectorAll(".media-photo").forEach(figure => {
    const caption = figure.querySelector(".ai-label");
    const image = figure.querySelector(".product-photo");
    if (caption) caption.textContent = label;
    if (image) {
      image.title = label;
      if (image.dataset.productName) image.alt = image.dataset.productName + ". " + label;
    }
  });
});

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
  // Detailed visual review notes remain in the image index, not customer tooltips.
  const label = text(LABEL);
  return '<figure class="media-frame media-photo">' +
    '<img class="product-photo" src="/static/products/' + esc(entry.file) + '"' +
    ' data-product-name="' + esc(product.name) + '"' +
    ' alt="' + esc(product.name + ". " + label) + '" title="' + esc(label) + '"' +
    ' loading="lazy" decoding="async">' +
    '<figcaption class="ai-label">' + esc(label) + '</figcaption>' +
    '</figure>';
}
