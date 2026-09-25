// Product detail page: loads reviews for PRODUCT_NAME (set inline by product.html)

const revState = { page: 1, sentiment: "", minRating: "" };

function starString(rating){
  const full = Math.round(rating);
  return "★".repeat(full) + "☆".repeat(5 - full);
}
document.getElementById("avgStars").textContent = starString(AVG_RATING);

async function loadReviews(){
  const params = new URLSearchParams({
    product: PRODUCT_NAME,
    page: revState.page,
    page_size: 10,
  });
  if (revState.sentiment) params.set("sentiment", revState.sentiment);
  if (revState.minRating) params.set("min_rating", revState.minRating);

  const res = await fetch(`/reviews?${params.toString()}`);
  const data = await res.json();

  const list = document.getElementById("reviewList");
  list.innerHTML = "";
  if (data.reviews.length === 0){
    list.innerHTML = '<p class="muted" style="font-family:var(--sans);padding:20px 0;">No reviews match those filters.</p>';
  }
  data.reviews.forEach(r => {
    const div = document.createElement("div");
    div.className = "review";
    div.innerHTML = `
      <div class="row1">
        <span class="title">${r.title} <span class="sentiment-tag sentiment-${r.sentiment}">${r.sentiment}</span></span>
        <span class="user">${r.username} · ${r.date}</span>
      </div>
      <div class="stars">${starString(r.rating)}</div>
      <div class="body">${r.text}</div>
      <div class="footer">${r.numHelpful} found this helpful · ${r.doRecommend ? "Recommends this product" : "Does not recommend"}</div>
    `;
    list.appendChild(div);
  });

  const pag = document.getElementById("revPagination");
  pag.innerHTML = "";
  const prev = document.createElement("button");
  prev.textContent = "← Prev";
  prev.disabled = data.page <= 1;
  prev.onclick = () => { revState.page--; loadReviews(); };
  const next = document.createElement("button");
  next.textContent = "Next →";
  next.disabled = data.page >= data.total_pages;
  next.onclick = () => { revState.page++; loadReviews(); };
  const label = document.createElement("span");
  label.style.alignSelf = "center";
  label.textContent = data.total_pages
    ? `Page ${data.page} of ${data.total_pages} (${data.total} reviews)`
    : "No reviews";
  pag.appendChild(prev);
  pag.appendChild(label);
  pag.appendChild(next);
}

document.getElementById("sentimentFilter").onchange = (e) => {
  revState.sentiment = e.target.value;
  revState.page = 1;
  loadReviews();
};
document.getElementById("minRatingFilter").onchange = (e) => {
  revState.minRating = e.target.value;
  revState.page = 1;
  loadReviews();
};

const addBtn = document.getElementById("addToCartBtn");
addBtn.onclick = () => {
  addToCart(addBtn.dataset.name, parseFloat(addBtn.dataset.price));
  const msg = document.getElementById("addedMsg");
  msg.hidden = false;
  setTimeout(() => { msg.hidden = true; }, 1500);
};

loadReviews();
