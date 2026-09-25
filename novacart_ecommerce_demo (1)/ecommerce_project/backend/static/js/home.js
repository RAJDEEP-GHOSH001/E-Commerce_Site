// Homepage: category/rating filters, sort, product grid (links to /product/<slug>)

const state = { category: null, minRating: null, sort: "name" };

async function fetchJSON(url){
  const res = await fetch(url);
  return res.json();
}

async function loadCategories(){
  const data = await fetchJSON("/categories");
  const el = document.getElementById("categoryFilters");
  el.innerHTML = "";
  el.appendChild(makeFilterBtn("All categories", null, true));
  data.categories.forEach(c => el.appendChild(makeFilterBtn(c, c, false)));

  // honor ?category= from a footer/breadcrumb link
  const params = new URLSearchParams(window.location.search);
  const initialCategory = params.get("category");
  if (initialCategory){
    state.category = initialCategory;
    [...el.children].forEach(b => b.classList.toggle("active", b.textContent === initialCategory));
  }
}

function makeFilterBtn(label, value, active){
  const btn = document.createElement("button");
  btn.className = "filter-btn" + (active ? " active" : "");
  btn.textContent = label;
  btn.onclick = () => {
    state.category = value;
    document.querySelectorAll("#categoryFilters .filter-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    loadProducts();
  };
  return btn;
}

function setupRatingFilters(){
  const el = document.getElementById("ratingFilters");
  const options = [["Any", null], ["4+ stars", 4], ["3+ stars", 3]];
  options.forEach(([label, val], i) => {
    const btn = document.createElement("button");
    btn.className = "filter-btn" + (i === 0 ? " active" : "");
    btn.textContent = label;
    btn.onclick = () => {
      state.minRating = val;
      document.querySelectorAll("#ratingFilters .filter-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      loadProducts();
    };
    el.appendChild(btn);
  });
}

function starString(rating){
  const full = Math.round(rating);
  return "★".repeat(full) + "☆".repeat(5 - full);
}

async function loadProducts(){
  let url = "/products";
  if (state.category) url += "?category=" + encodeURIComponent(state.category);
  const data = await fetchJSON(url);
  let items = data.products;
  if (state.minRating) items = items.filter(p => p.avgRating >= state.minRating);

  items.sort((a, b) => {
    if (state.sort === "rating") return b.avgRating - a.avgRating;
    if (state.sort === "price") return a.avgPrice - b.avgPrice;
    if (state.sort === "reviews") return b.reviewCount - a.reviewCount;
    return a.name.localeCompare(b.name);
  });

  renderGrid(items);
  document.getElementById("resultCount").textContent = `${items.length} products`;
  document.getElementById("emptyState").hidden = items.length !== 0;
}

function renderGrid(items){
  const grid = document.getElementById("productGrid");
  grid.innerHTML = "";
  items.forEach(p => {
    const card = document.createElement("a");
    card.className = "card";
    card.href = `/product/${p.slug}`;
    card.innerHTML = `
      <div class="card-glyph">${p.name[0]}</div>
      <div class="brand-tag">${p.brand}</div>
      <h4>${p.name}</h4>
      <div class="price">$${p.avgPrice.toFixed(2)}</div>
      <div class="stars">${starString(p.avgRating)} <span style="color:var(--muted)">${p.avgRating.toFixed(1)}</span></div>
      <div class="meta">${p.reviewCount} reviews · ${p.primaryCategories}</div>
    `;
    grid.appendChild(card);
  });
}

document.getElementById("sortSelect").onchange = (e) => {
  state.sort = e.target.value;
  loadProducts();
};

(async function init(){
  await loadCategories();
  setupRatingFilters();
  await loadProducts();
})();
