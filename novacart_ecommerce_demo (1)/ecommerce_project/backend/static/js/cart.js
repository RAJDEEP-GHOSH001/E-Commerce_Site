// Shared across every page: cart drawer (localStorage-backed) + nav search.

const CART_KEY = "novacart_cart_v1";

function readCart(){
  try{ return JSON.parse(localStorage.getItem(CART_KEY)) || []; }
  catch(e){ return []; }
}
function writeCart(items){
  localStorage.setItem(CART_KEY, JSON.stringify(items));
  renderCartCount();
}
function addToCart(name, price){
  const items = readCart();
  const existing = items.find(i => i.name === name);
  if (existing) existing.qty += 1;
  else items.push({ name, price, qty: 1 });
  writeCart(items);
}
function removeFromCart(name){
  writeCart(readCart().filter(i => i.name !== name));
}
function cartTotal(items){
  return items.reduce((sum, i) => sum + i.price * i.qty, 0);
}
function renderCartCount(){
  const items = readCart();
  const count = items.reduce((n, i) => n + i.qty, 0);
  const el = document.getElementById("cartCount");
  if (el) el.textContent = count;
}
function renderCartDrawer(){
  const items = readCart();
  const list = document.getElementById("cartItems");
  if (!list) return;
  list.innerHTML = "";
  if (items.length === 0){
    list.innerHTML = '<div class="cart-empty">Your cart is empty.</div>';
  } else {
    items.forEach(i => {
      const row = document.createElement("div");
      row.className = "cart-item";
      row.innerHTML = `
        <span>${i.name} × ${i.qty}</span>
        <span>$${(i.price * i.qty).toFixed(2)} <button data-name="${i.name}">remove</button></span>
      `;
      row.querySelector("button").onclick = () => {
        removeFromCart(i.name);
        renderCartDrawer();
      };
      list.appendChild(row);
    });
  }
  document.getElementById("cartTotal").textContent = `$${cartTotal(items).toFixed(2)}`;
}

function setupCartDrawer(){
  const drawer = document.getElementById("cartDrawer");
  const overlay = document.getElementById("cartOverlay");
  const openBtn = document.getElementById("cartBtn");
  const closeBtn = document.getElementById("cartClose");
  const checkoutBtn = document.getElementById("checkoutBtn");

  const open = () => { renderCartDrawer(); drawer.classList.add("open"); overlay.classList.add("open"); };
  const close = () => { drawer.classList.remove("open"); overlay.classList.remove("open"); };

  openBtn && (openBtn.onclick = open);
  closeBtn && (closeBtn.onclick = close);
  overlay && (overlay.onclick = close);
  checkoutBtn && (checkoutBtn.onclick = () => {
    writeCart([]);
    renderCartDrawer();
    checkoutBtn.textContent = "Cleared ✓";
    setTimeout(() => { checkoutBtn.textContent = "Checkout"; }, 1500);
  });
}

// --- Nav search: quick client-side lookup against /products ---
let ALL_PRODUCTS_CACHE = null;

async function setupNavSearch(){
  const input = document.getElementById("navSearch");
  const results = document.getElementById("navSearchResults");
  if (!input) return;

  input.addEventListener("input", async () => {
    const q = input.value.trim().toLowerCase();
    if (!q){ results.classList.remove("open"); results.innerHTML = ""; return; }

    if (!ALL_PRODUCTS_CACHE){
      const res = await fetch("/products");
      const data = await res.json();
      ALL_PRODUCTS_CACHE = data.products;
    }
    const matches = ALL_PRODUCTS_CACHE.filter(p =>
      p.name.toLowerCase().includes(q) || p.brand.toLowerCase().includes(q)
    ).slice(0, 8);

    results.innerHTML = "";
    if (matches.length === 0){
      results.innerHTML = '<a href="#" style="color:#6b6a63">No matches</a>';
    } else {
      matches.forEach(p => {
        const a = document.createElement("a");
        a.href = `/product/${p.slug}`;
        a.innerHTML = `<span>${p.name}</span><span>$${p.avgPrice.toFixed(2)}</span>`;
        results.appendChild(a);
      });
    }
    results.classList.add("open");
  });

  document.addEventListener("click", (e) => {
    if (!e.target.closest(".nav-search")) results.classList.remove("open");
  });
}

document.addEventListener("DOMContentLoaded", () => {
  renderCartCount();
  setupCartDrawer();
  setupNavSearch();
});
