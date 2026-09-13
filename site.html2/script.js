const defaultProducts = [
  {
    id: 1,
    name: "Sculpt Knit Set",
    category: "women",
    price: 129,
    subtitle: "Soft wool blend",
    badge: "New",
    rating: 4.9,
    image:
      "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=900&q=80",
  },
  {
    id: 2,
    name: "Tailored Wool Coat",
    category: "women",
    price: 240,
    subtitle: "Structured warmth",
    badge: "Trending",
    rating: 4.8,
    image:
      "https://images.unsplash.com/photo-1496747611176-843222e1e57c?auto=format&fit=crop&w=900&q=80",
  },
  {
    id: 3,
    name: "Monochrome Hoodie",
    category: "men",
    price: 98,
    subtitle: "Premium cotton",
    badge: "Bestseller",
    rating: 4.7,
    image:
      "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=900&q=80",
  },
  {
    id: 4,
    name: "Layered Utility Shirt",
    category: "men",
    price: 118,
    subtitle: "Relaxed fit",
    badge: "Limited",
    rating: 4.8,
    image:
      "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=900&q=80",
  },
  {
    id: 5,
    name: "Aster Leather Tote",
    category: "accessories",
    price: 142,
    subtitle: "Italian leather",
    badge: "Top pick",
    rating: 4.9,
    image:
      "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=900&q=80",
  },
  {
    id: 6,
    name: "Hayden Sunglasses",
    category: "accessories",
    price: 74,
    subtitle: "UV protection",
    badge: "Hot",
    rating: 4.6,
    image:
      "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=900&q=80",
  },
  {
    id: 7,
    name: "Luna Overshirt",
    category: "women",
    price: 136,
    subtitle: "Lightweight layer",
    badge: "New",
    rating: 4.8,
    image:
      "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=900&q=80",
  },
  {
    id: 8,
    name: "Noir Striped Tee",
    category: "men",
    price: 68,
    subtitle: "Essential staple",
    badge: "Sale",
    rating: 4.7,
    image:
      "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=900&q=80",
  },
];

const STORAGE_KEYS = {
  products: "cza-products",
  cart: "cza-cart",
  orders: "cza-orders",
  admin: "cza-admin-auth",
  currency: "cza-currency",
  credentials: "cza-admin-credentials",
};

const defaultAdminPasswordHash = "ce258a4967db3acc31388ab7df7be18e1c8ff40164b104946550c9f69b413891";

async function hashCredential(value) {
  const bytes = new TextEncoder().encode(value);
  const hash = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(hash)).map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function getAdminCredentials() {
  const stored = localStorage.getItem(STORAGE_KEYS.credentials);
  if (!stored) {
    const defaults = { username: "admin", passwordHash: defaultAdminPasswordHash };
    localStorage.setItem(STORAGE_KEYS.credentials, JSON.stringify(defaults));
    return defaults;
  }
  try {
    return JSON.parse(stored);
  } catch (error) {
    return { username: "admin", passwordHash: defaultAdminPasswordHash };
  }
}

const currencyRates = {
  UGX: 1,
  USD: 1 / 3750,
  EUR: 1 / 4300,
  GBP: 1 / 5000,
};

function getCurrency() {
  return localStorage.getItem(STORAGE_KEYS.currency) || "UGX";
}

function formatMoney(value, currency = null) {
  const curr = currency || getCurrency();
  const amount = Number(value) || 0;
  return new Intl.NumberFormat("en-US", { style: "currency", currency: curr, maximumFractionDigits: curr === "UGX" ? 0 : 2 }).format(amount);
}

function productPriceMarkup(product) {
  const hasDiscount = Number(product.discountPrice) > 0 && Number(product.discountPrice) < Number(product.price);
  if (!hasDiscount) return `<span class="product-price">${formatMoney(product.price)}</span>`;
  const percent = product.discountPercent || Math.round((1 - product.discountPrice / product.price) * 100);
  return `<span class="product-price product-price-sale"><del>${formatMoney(product.price)}</del><strong>${formatMoney(product.discountPrice)}</strong><em>${percent}% off</em></span>`;
}

function productDetailsMarkup(product) {
  const sizes = Array.isArray(product.sizes) && product.sizes.length ? product.sizes.join(" · ") : "One size";
  const colors = Array.isArray(product.colors) && product.colors.length
    ? `<div class="product-colors">${product.colors.map((color) => `<span class="color-chip"><i class="color-swatch" style="--swatch:${color.toLowerCase()}"></i>${color}</span>`).join("")}</div>`
    : "";
  return `<p class="product-subtitle">${product.subtitle}</p><p class="product-sizes">Sizes: ${sizes}</p>${colors}`;
}

let cart = JSON.parse(localStorage.getItem(STORAGE_KEYS.cart) || "[]");

function getProducts() {
  const stored = localStorage.getItem(STORAGE_KEYS.products);
  if (!stored) {
    localStorage.setItem(STORAGE_KEYS.products, JSON.stringify(defaultProducts));
    return [...defaultProducts];
  }

  try {
    return JSON.parse(stored);
  } catch (error) {
    localStorage.setItem(STORAGE_KEYS.products, JSON.stringify(defaultProducts));
    return [...defaultProducts];
  }
}

function saveProducts(products) {
  localStorage.setItem(STORAGE_KEYS.products, JSON.stringify(products));

  fetch("/api/products", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(products),
  }).catch(() => {});
}

function getOrders() {
  const stored = localStorage.getItem(STORAGE_KEYS.orders);
  if (!stored) {
    localStorage.setItem(STORAGE_KEYS.orders, JSON.stringify([]));
    return [];
  }

  try {
    return JSON.parse(stored);
  } catch (error) {
    localStorage.setItem(STORAGE_KEYS.orders, JSON.stringify([]));
    return [];
  }
}

function saveOrders(orders) {
  localStorage.setItem(STORAGE_KEYS.orders, JSON.stringify(orders));

  fetch("/api/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(orders),
  }).catch(() => {});
}

async function syncSharedData() {
  try {
    const productsResponse = await fetch("/api/products");
    if (productsResponse.ok) {
      const products = await productsResponse.json();
      if (Array.isArray(products)) {
        localStorage.setItem(STORAGE_KEYS.products, JSON.stringify(products));
      }
    }
  } catch (error) {
    console.info("Shared products sync unavailable:", error.message);
  }

  try {
    const ordersResponse = await fetch("/api/orders");
    if (ordersResponse.ok) {
      const orders = await ordersResponse.json();
      if (Array.isArray(orders)) {
        localStorage.setItem(STORAGE_KEYS.orders, JSON.stringify(orders));
      }
    }
  } catch (error) {
    console.info("Shared orders sync unavailable:", error.message);
  }
}

function getBagCount() {
  return cart.reduce((sum, item) => sum + item.qty, 0);
}

function updateBagCount() {
  const bagCount = document.querySelector(".bag-count");
  if (bagCount) bagCount.textContent = String(getBagCount());
}

function getActiveCategory() {
  return new URLSearchParams(window.location.search).get("category") || "all";
}

function openCheckout() {
  window.location.href = "checkout.html";
}

function saveCart() {
  localStorage.setItem(STORAGE_KEYS.cart, JSON.stringify(cart));
  updateBagCount();
  renderCart();
  
  // Notify checkout pages to update
  window.dispatchEvent(new CustomEvent("cartUpdated", { detail: { cart } }));
}

function showToast(message) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(showToast.timeoutId);
  showToast.timeoutId = setTimeout(() => toast.classList.remove("show"), 2000);
}

function renderProducts(target, category = "all") {
  if (!target) return;

  const items = category === "all" ? getProducts() : getProducts().filter((product) => product.category === category);

  target.innerHTML = items
    .map(
      (product) => `
        <article class="product-card">
          <div class="product-image">
            <img src="${product.image}" alt="${product.name}" />
            <span class="product-badge">${product.badge}</span>
          </div>
          <div class="product-info">
            <div class="product-meta">
              <h3 class="product-name">${product.name}</h3>
              ${productPriceMarkup(product)}
            </div>
            ${productDetailsMarkup(product)}
            <div class="product-footer">
              <span class="rating">★★★★★ ${product.rating}</span>
              <button class="add-to-cart" type="button" data-name="${product.name}">Add</button>
            </div>
          </div>
        </article>
      `
    )
    .join("");

  const itemCount = document.getElementById("item-count");
  if (itemCount) itemCount.textContent = String(items.length);

  attachCartActions();
}

function attachCartActions() {
  document.querySelectorAll(".add-to-cart").forEach((button) => {
    button.addEventListener("click", () => {
      const name = button.dataset.name;
      const product = getProducts().find((item) => item.name === name);
      if (!product) return;

      const existing = cart.find((item) => item.id === product.id);
      if (existing) {
        existing.qty += 1;
      } else {
        cart.push({ ...product, qty: 1 });
      }

      saveCart();
      button.textContent = "Added";
      button.disabled = true;
      setTimeout(() => {
        button.textContent = "Add";
        button.disabled = false;
      }, 800);
      showToast(`${product.name} added to bag`);
    });
  });
}

function renderCart() {
  const cartItems = document.getElementById("cart-items");
  if (!cartItems) return;

  if (!cart.length) {
    cartItems.innerHTML = '<p class="cart-empty">Your bag is empty.</p>';
    return;
  }

  const total = cart.reduce((sum, item) => sum + (item.discountPrice || item.price) * item.qty, 0);

  cartItems.innerHTML = `
    ${cart
      .map(
        (item, index) => `
          <div class="cart-item" style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid var(--line); gap: 12px;">
            <div style="flex: 1;">
              <strong>${item.name}</strong>
              <div style="font-size: 0.85rem; color: var(--muted);">Qty: ${item.qty}</div>
            </div>
            <strong>${formatMoney((item.discountPrice || item.price) * item.qty)}</strong>
            <button type="button" class="remove-from-cart" data-index="${index}" style="background: none; border: none; color: #c00; cursor: pointer; font-size: 1.2rem; padding: 0 4px;" title="Remove item">×</button>
          </div>
        `
      )
      .join("")}
    <div class="cart-item" style="display: flex; justify-content: space-between; padding-top: 12px; border-top: 2px solid var(--line); margin-top: 12px; font-weight: 600;">
      <span>Total</span>
      <strong>${formatMoney(total)}</strong>
    </div>
  `;

  // Attach remove handlers
  document.querySelectorAll(".remove-from-cart").forEach((btn) => {
    btn.addEventListener("click", () => {
      const index = Number(btn.dataset.index);
      cart.splice(index, 1);
      saveCart();
      showToast("Item removed from bag");
    });
  });
}

function renderPaymentNotifications() {
  const notificationsList = document.getElementById("payment-notifications-list");
  if (!notificationsList) return;

  let notifications = [];
  try {
    notifications = JSON.parse(localStorage.getItem("cza-payment-notifications") || "[]");
  } catch (e) {
    notifications = [];
  }

  const paymentsBadge = document.getElementById("payments-badge");
  if (paymentsBadge) paymentsBadge.textContent = `${notifications.length} payment${notifications.length === 1 ? "" : "s"}`;

  if (!notifications.length) {
    notificationsList.innerHTML = '<li><span style="color: var(--muted);">No payments yet</span></li>';
    return;
  }

  notificationsList.innerHTML = notifications
    .slice(0, 10)
    .map(
      (payment) => `
        <li style="background: rgba(255, 255, 255, 0.6); padding: 12px; margin-bottom: 8px; border-radius: var(--radius-sm); border-left: 4px solid var(--success);">
          <div class="order-main">
            <div class="order-avatar" style="background: linear-gradient(135deg, var(--gold), var(--accent)); color: white; font-weight: 600;">${payment.customerName.slice(0, 1).toUpperCase()}</div>
            <div>
              <strong>${payment.customerName}</strong>
              <span class="order-meta" style="display: block; font-size: 0.85rem;">📧 ${payment.customerEmail}</span>
              <span class="order-meta" style="display: block; font-size: 0.85rem;">📍 ${payment.deliveryCity}, ${payment.deliveryCountry}</span>
              <span class="order-meta" style="display: block; font-size: 0.85rem; color: var(--success);">✓ Payment received</span>
            </div>
          </div>
          <div class="order-side">
            <strong style="color: var(--success); font-size: 1.1rem;">${formatMoney(payment.total, payment.currency)}</strong>
            <span style="display: block; font-size: 0.8rem; color: var(--muted); margin-top: 4px;">${new Date(payment.createdAt).toLocaleDateString()}</span>
          </div>
        </li>
      `
    )
    .join("");
}

function renderDashboard() {
  const dashboard = document.getElementById("admin-dashboard") || document.getElementById("admin-shell");
  if (!dashboard || dashboard.classList.contains("hidden")) return;

  const orders = getOrders();
  renderPaymentNotifications();
  const productList = getProducts();

  const salesTotal = orders.reduce((sum, order) => sum + Number(order.total), 0);
  const salesElement = document.getElementById("sales-total");
  const ordersElement = document.getElementById("orders-count");
  const bestSellerElement = document.getElementById("best-seller");

  if (salesElement) salesElement.textContent = formatMoney(salesTotal);
  if (ordersElement) ordersElement.textContent = String(orders.length);
  const ordersBadge = document.getElementById("orders-badge");
  if (ordersBadge) ordersBadge.textContent = `${orders.length} ${orders.length === 1 ? "order" : "orders"}`;
  const profileProducts = document.getElementById("profile-products");
  const profileOrders = document.getElementById("profile-orders");
  if (profileProducts) profileProducts.textContent = String(productList.length);
  if (profileOrders) profileOrders.textContent = String(orders.length);
  document.querySelectorAll(".chart-y span").forEach((label, index) => {
    const values = [500000, 250000, 0];
    label.textContent = formatMoney(values[index] / 3750);
  });

  const frequency = {};
  orders.forEach((order) => {
    order.items.forEach((item) => {
      frequency[item.name] = (frequency[item.name] || 0) + item.qty;
    });
  });

  const bestSeller = Object.entries(frequency).sort((a, b) => b[1] - a[1])[0];
  if (bestSellerElement) bestSellerElement.textContent = bestSeller ? bestSeller[0] : "—";

  const orderList = document.getElementById("order-list");
  if (orderList) {
    orderList.innerHTML = orders.length
      ? orders
          .slice(0, 6)
          .map(
            (order) => `
              <li>
                <div class="order-main">
                  <div class="order-avatar">${order.customerName.slice(0, 1).toUpperCase()}</div>
                  <div>
                    <strong>${order.customerName}</strong>
                    <span class="order-meta">${order.items.map((item) => `${item.name} x${item.qty}`).join(", ") || "No items"}</span>
                    <span class="order-meta">${order.deliveryAddress || "Address pending"}</span>
                  </div>
                </div>
                <div class="order-side">
                  <strong>${formatMoney(order.total)}</strong>
                  <select class="order-status" data-order-id="${order.id}" aria-label="Order status">
                    ${["New", "Processing", "Shipped", "Completed"]
                      .map((status) => `<option ${status === (order.status || "New") ? "selected" : ""}>${status}</option>`)
                      .join("")}
                  </select>
                  ${order.customerPhone ? `<a class="order-contact" href="https://wa.me/${String(order.customerPhone).replace(/[^0-9]/g, "")}" target="_blank" rel="noreferrer">Message</a>` : ""}
                </div>
              </li>
            `
          )
          .join("")
      : '<li><span>No orders yet.</span></li>';

    orderList.querySelectorAll(".order-status").forEach((select) => {
      select.addEventListener("change", () => {
        const orderId = Number(select.dataset.orderId);
        const updatedOrders = getOrders().map((order) =>
          order.id === orderId ? { ...order, status: select.value } : order
        );
        saveOrders(updatedOrders);
        showToast("Order status updated");
      });
    });
  }

  const inventoryList = document.getElementById("inventory-list");
  if (inventoryList) {
    inventoryList.innerHTML = productList
      .map(
        (product) => `
          <li>
            <div>
              <strong>${product.name}</strong><br>
              <span>${productPriceMarkup(product)}</span><br>
              <small>Sizes: ${Array.isArray(product.sizes) && product.sizes.length ? product.sizes.join(", ") : "One size"}</small><br>
              <small>Colors: ${Array.isArray(product.colors) && product.colors.length ? product.colors.join(", ") : "Not set"}</small>
            </div>
            <div class="inventory-actions"><button class="edit-item" type="button" data-id="${product.id}">Edit</button><button class="delete-item" type="button" data-id="${product.id}">Remove</button></div>
          </li>
        `
      )
      .join("");

    inventoryList.querySelectorAll(".delete-item").forEach((button) => {
      button.addEventListener("click", () => {
        const productId = Number(button.dataset.id);
        const updated = getProducts().filter((product) => product.id !== productId);
        saveProducts(updated);
        renderProducts(document.getElementById("featured-products"), document.querySelector(".filter-btn.active")?.dataset.filter || "all");
        renderProducts(document.getElementById("shop-products"), "all");
        renderDashboard();
        showToast("Item removed from shop");
      });
    });

    inventoryList.querySelectorAll(".edit-item").forEach((button) => {
      button.addEventListener("click", () => {
        const product = getProducts().find((item) => String(item.id) === String(button.dataset.id));
        if (!product) return;
        const form = document.getElementById("product-form");
        form.elements.productId.value = product.id;
        form.elements.name.value = product.name;
        form.elements.price.value = Math.round(product.price || 0);
        form.elements.category.value = product.category;
        form.elements.sizes.value = (product.sizes || []).join(", ");
        form.elements.colors.value = (product.colors || []).join(", ");
        form.elements.discountPrice.value = product.discountPrice ? Math.round(product.discountPrice || 0) : "";
        form.elements.discountPercent.value = product.discountPercent || "";
        form.elements.image.value = product.image;
        document.getElementById("product-submit").textContent = "Save changes";
        document.getElementById("cancel-edit").classList.remove("hidden");
        form.scrollIntoView({ behavior: "smooth", block: "center" });
      });
    });
  }
}

function openAdminModal() {
  const modal = document.getElementById("admin-modal");
  if (modal) modal.classList.add("open");
}

function closeAdminModal() {
  const modal = document.getElementById("admin-modal");
  if (modal) modal.classList.remove("open");
}

async function loginAdmin(event) {
  event.preventDefault();
  const form = event.target;
  const formData = new FormData(form);
  const username = String(formData.get("username") || "").trim();
  const password = String(formData.get("password") || "").trim();

  const credentials = getAdminCredentials();
  if (username === credentials.username && await hashCredential(password) === credentials.passwordHash) {
    sessionStorage.setItem(STORAGE_KEYS.admin, "true");
    if (document.body.classList.contains("admin-page")) {
      document.getElementById("admin-login-screen")?.classList.add("hidden");
      document.getElementById("admin-shell")?.classList.remove("hidden");
      renderDashboard();
      return;
    }
    localStorage.setItem(STORAGE_KEYS.admin, "true");
    closeAdminModal();
    document.getElementById("admin-dashboard")?.classList.remove("hidden");
    renderDashboard();
    showToast("Welcome back, CZA admin");
  } else {
    showToast("Incorrect login details");
  }
}

function logoutAdmin() {
  sessionStorage.removeItem(STORAGE_KEYS.admin);
  document.getElementById("admin-dashboard")?.classList.add("hidden");
  document.getElementById("admin-shell")?.classList.add("hidden");
  document.getElementById("admin-login-screen")?.classList.remove("hidden");
  showToast("Logged out");
}

function setupChatWidget() {
  const toggle = document.querySelector(".chat-toggle");
  const windowEl = document.getElementById("chat-window");
  const closeButton = document.querySelector(".chat-close");

  if (!toggle || !windowEl) return;

  toggle.addEventListener("click", () => {
    windowEl.classList.toggle("hidden");
  });

  if (closeButton) {
    closeButton.addEventListener("click", () => windowEl.classList.add("hidden"));
  }
}

function setupSearch() {
  const searchPanel = document.getElementById("search-panel");
  const searchForm = document.getElementById("search-form");
  const searchStatus = document.getElementById("search-status");
  if (!searchPanel || !searchForm) return;

  document.querySelectorAll('[aria-label="Search"]').forEach((button) => {
    button.addEventListener("click", () => {
      searchPanel.classList.add("open");
      searchPanel.setAttribute("aria-hidden", "false");
      document.getElementById("site-search")?.focus();
    });
  });

  document.querySelector(".search-close")?.addEventListener("click", () => {
    searchPanel.classList.remove("open");
    searchPanel.setAttribute("aria-hidden", "true");
  });

  searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const query = String(new FormData(searchForm).get("site-search") || "").trim().toLowerCase();
    if (!query) return;

    const matches = getProducts().filter((product) => `${product.name} ${product.category} ${product.subtitle}`.toLowerCase().includes(query));
    if (document.getElementById("shop-products")) {
      const target = document.getElementById("shop-products");
      target.innerHTML = "";
      renderProductItems(target, matches);
      if (searchStatus) searchStatus.textContent = `${matches.length} result${matches.length === 1 ? "" : "s"} for “${query}”`;
    } else {
      window.location.href = `shop.html?search=${encodeURIComponent(query)}`;
    }
  });
}

function renderProductItems(target, items) {
  if (!target) return;
  const itemCount = document.getElementById("item-count");
  if (itemCount) itemCount.textContent = String(items.length);
  target.innerHTML = items.length
    ? items.map((product) => `
      <article class="product-card">
        <div class="product-image"><img src="${product.image}" alt="${product.name}" /><span class="product-badge">${product.badge}</span></div>
        <div class="product-info"><div class="product-meta"><h3 class="product-name">${product.name}</h3>${productPriceMarkup(product)}</div>
        ${productDetailsMarkup(product)}<div class="product-footer"><span class="rating">★★★★★ ${product.rating}</span><button class="add-to-cart" type="button" data-name="${product.name}">Add</button></div></div>
      </article>`).join("")
    : '<p class="cart-empty">No CZA pieces matched that search.</p>';
  attachCartActions();
}

function bindNavbar() {
  const navToggle = document.querySelector(".nav-toggle");
  const siteNav = document.querySelector(".site-nav");
  if (navToggle && siteNav) {
    navToggle.addEventListener("click", () => {
      siteNav.classList.toggle("open");
    });
  }

  document.querySelectorAll(".bag-button").forEach((button) => button.addEventListener("click", openCheckout));

  document.querySelector(".close-admin")?.addEventListener("click", closeAdminModal);
  document.getElementById("admin-login-form")?.addEventListener("submit", loginAdmin);
  document.querySelector(".dashboard-close")?.addEventListener("click", logoutAdmin);
  
  // Mobile sidebar toggle
  setupAdminMobileSidebar();
}

function setupAdminMobileSidebar() {
  const toggleBtn = document.getElementById("admin-mobile-toggle");
  const sidebar = document.querySelector(".admin-sidebar");
  const shell = document.querySelector(".admin-shell");

  if (!toggleBtn || !sidebar) return;

  // Show toggle on mobile
  const showToggle = () => {
    toggleBtn.style.display = window.innerWidth <= 768 ? "block" : "none";
  };

  showToggle();
  window.addEventListener("resize", showToggle);

  // Toggle sidebar
  toggleBtn.addEventListener("click", () => {
    sidebar.classList.toggle("mobile-open");
  });

  // Close sidebar when clicking on a nav link
  sidebar.querySelectorAll(".admin-nav a").forEach((link) => {
    link.addEventListener("click", () => {
      if (window.innerWidth <= 768) {
        sidebar.classList.remove("mobile-open");
      }
    });
  });

  // Close sidebar when clicking outside
  document.addEventListener("click", (e) => {
    if (window.innerWidth <= 768 && !sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
      sidebar.classList.remove("mobile-open");
    }
  });
}

function bindCheckout() {
  const checkoutForm = document.getElementById("checkout-form");
  if (!checkoutForm) return;

  checkoutForm.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!cart.length) {
      showToast("Add items before checkout");
      return;
    }

    const formData = new FormData(checkoutForm);
    const total = cart.reduce((sum, item) => sum + (item.discountPrice || item.price) * item.qty, 0);

    const countryCode = String(formData.get("countryCode") || "+256");
    const phoneNumber = String(formData.get("customerPhone") || "").replace(/[^0-9]/g, "");
    const orderId = Date.now();
    const order = {
      id: orderId,
      customerName: String(formData.get("customerName") || "Customer").trim(),
      customerEmail: String(formData.get("customerEmail") || "").trim(),
      customerPhone: `${countryCode.replace("+", "")}${phoneNumber}`,
      countryCode,
      deliveryAddress: String(formData.get("deliveryAddress") || "").trim(),
      deliveryCity: String(formData.get("customerCity") || "").trim(),
      deliveryRegion: String(formData.get("customerRegion") || "").trim(),
      deliveryCountry: String(formData.get("customerCountry") || "").trim(),
      deliveryNotes: String(formData.get("deliveryNotes") || "").trim(),
      items: cart.map((item) => ({ name: item.name, qty: item.qty, price: item.discountPrice || item.price })),
      total,
      currency: getCurrency(),
      status: "New",
      createdAt: new Date().toISOString(),
      confirmationLink: buildConfirmationLink(orderId),
    };

    const orders = getOrders();
    orders.unshift(order);
    saveOrders(orders);

    notifyAdminOfOrder(order);

    cart = [];
    localStorage.setItem(STORAGE_KEYS.cart, JSON.stringify(cart));
    renderCart();
    updateBagCount();
    renderDashboard();
    checkoutForm.reset();
    showToast("Order sent to the dashboard");
  });

  document.getElementById("clear-cart")?.addEventListener("click", () => {
    cart = [];
    saveCart();
    showToast("Cart cleared");
  });
}

function buildConfirmationLink(orderId) {
  const baseUrl = window.location.origin || "http://localhost";
  return `${baseUrl}${window.location.pathname.replace(/\/[^/]*$/, "/") || "/"}?order=${orderId}`;
}

function notifyAdminOfOrder(order) {
  // Store notification in localStorage for dashboard
  const notification = {
    id: order.id,
    type: "payment",
    customerName: order.customerName,
    customerEmail: order.customerEmail,
    customerPhone: order.customerPhone,
    deliveryCity: order.deliveryCity,
    deliveryCountry: order.deliveryCountry,
    deliveryAddress: order.deliveryAddress,
    items: order.items,
    total: order.total,
    currency: order.currency,
    confirmationLink: order.confirmationLink,
    createdAt: order.createdAt,
    timestamp: Date.now(),
  };

  localStorage.setItem("cza-latest-order-notification", JSON.stringify(notification));
  
  // Also add to orders notifications array
  let notifications = [];
  try {
    notifications = JSON.parse(localStorage.getItem("cza-payment-notifications") || "[]");
  } catch (e) {
    notifications = [];
  }
  notifications.unshift(notification);
  localStorage.setItem("cza-payment-notifications", JSON.stringify(notifications.slice(0, 50))); // Keep last 50

  // Show browser notification to admin if logged in
  if ("Notification" in window && Notification.permission === "granted") {
    const itemsList = order.items.map((item) => `${item.name} (×${item.qty})`).join(", ");
    new Notification("💳 Payment Received - CZA", {
      body: `${order.customerName} paid ${formatMoney(order.total, order.currency)} | Delivering to ${order.deliveryCity}`,
      icon: "cza-logo.svg",
      tag: `order-${order.id}`,
      requireInteraction: true,
    });
  }
}

function setupAdminNotifications() {
  if (!document.body.classList.contains("admin-page")) return;
  window.addEventListener("storage", (event) => {
    if (event.key === STORAGE_KEYS.orders || event.key === "cza-latest-order-notification" || event.key === "cza-payment-notifications") {
      renderDashboard();
      const latest = event.key === "cza-latest-order-notification" && event.newValue ? JSON.parse(event.newValue) : null;
      if (latest && "Notification" in window && Notification.permission === "granted") {
        new Notification("💳 CZA Payment Received", {
          body: `${latest.customerName} paid ${formatMoney(latest.total, latest.currency)} → ${latest.deliveryCity}`,
          icon: "cza-logo.svg",
          tag: `payment-${latest.id}`,
          requireInteraction: true,
        });
      }
      if (event.key === STORAGE_KEYS.orders) showToast("New order received");
    }
  });
  document.querySelector(".admin-icon-button")?.addEventListener("click", async () => {
    if (!("Notification" in window)) {
      showToast("This browser does not support notifications");
      return;
    }
    const permission = await Notification.requestPermission();
    if (permission === "granted") {
      showToast("✓ Payment notifications enabled");
      new Notification("CZA Notifications Active", { body: "You will receive notifications when customers make payments." });
    } else {
      showToast("Notifications remain disabled");
    }
  });
}

function bindAccountSettings() {
  const form = document.getElementById("account-settings-form");
  if (!form) return;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const credentials = getAdminCredentials();
    if (await hashCredential(String(data.get("currentPassword"))) !== credentials.passwordHash) {
      showToast("Current password is incorrect");
      return;
    }
    const username = String(data.get("username") || "").trim();
    const newPassword = String(data.get("newPassword") || "");
    if (username.length < 3 || newPassword.length < 8) {
      showToast("Use a username with 3+ characters and password with 8+ characters");
      return;
    }
    const passwordHash = await hashCredential(newPassword);
    localStorage.setItem(STORAGE_KEYS.credentials, JSON.stringify({ username, passwordHash }));
    form.reset();
    showToast("Login details updated");
  });
}

function bindAdminProductForm() {
  const productForm = document.getElementById("product-form");
  if (!productForm) return;

  productForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(productForm);
    const products = getProducts();
    const productId = String(formData.get("productId") || "").trim();
    const newProduct = {
      id: productId ? Number(productId) : Date.now(),
      name: String(formData.get("name") || "").trim(),
      price: Number(formData.get("price") || 0),
      discountPrice: Number(formData.get("discountPrice") || 0),
      discountPercent: Math.min(100, Math.max(0, Number(formData.get("discountPercent") || 0))),
      sizes: String(formData.get("sizes") || "").split(",").map((size) => size.trim().toUpperCase()).filter(Boolean),
      colors: String(formData.get("colors") || "").split(",").map((color) => color.trim()).filter(Boolean),
      category: String(formData.get("category") || "women").trim(),
      subtitle: "New addition",
      badge: "New",
      rating: 5,
      image: String(formData.get("image") || "").trim(),
    };

    if (!newProduct.name || !newProduct.image || !newProduct.price) {
      showToast("Add a valid product first");
      return;
    }

    if (newProduct.discountPercent && !newProduct.discountPrice) {
      newProduct.discountPrice = newProduct.price * (1 - newProduct.discountPercent / 100);
    }
    if (newProduct.discountPrice && !newProduct.discountPercent) {
      newProduct.discountPercent = Math.round((1 - newProduct.discountPrice / newProduct.price) * 100);
    }

    const existingIndex = products.findIndex((product) => String(product.id) === productId);
    if (existingIndex >= 0) products[existingIndex] = { ...products[existingIndex], ...newProduct };
    else products.unshift(newProduct);
    saveProducts(products);
    productForm.reset();
    document.getElementById("product-submit").textContent = "Add product";
    document.getElementById("cancel-edit")?.classList.add("hidden");
    renderProducts(document.getElementById("featured-products"), document.querySelector(".filter-btn.active")?.dataset.filter || "all");
    renderProducts(document.getElementById("shop-products"), "all");
    renderDashboard();
    showToast("Product added to inventory");
  });

  document.getElementById("cancel-edit")?.addEventListener("click", () => {
    productForm.reset();
    document.getElementById("product-submit").textContent = "Add product";
    document.getElementById("cancel-edit").classList.add("hidden");
  });
}

async function initApp() {
  await syncSharedData();

  if (!window.__czaSharedSyncInterval) {
    window.__czaSharedSyncInterval = setInterval(async () => {
      await syncSharedData();
    }, 5000);
  }

  updateBagCount();
  renderCart();

  const featuredProducts = document.getElementById("featured-products");
  const shopProducts = document.getElementById("shop-products");

  if (featuredProducts) {
    renderProducts(featuredProducts, "all");
    document.querySelectorAll(".filter-btn").forEach((button) => {
      button.addEventListener("click", () => {
        document.querySelectorAll(".filter-btn").forEach((btn) => btn.classList.remove("active"));
        button.classList.add("active");
        renderProducts(featuredProducts, button.dataset.filter || "all");
      });
    });
  }

  if (shopProducts) {
    const params = new URLSearchParams(window.location.search);
    const searchQuery = params.get("search")?.trim().toLowerCase();
    const category = getActiveCategory();
    if (searchQuery) {
      renderProductItems(shopProducts, getProducts().filter((product) => `${product.name} ${product.category} ${product.subtitle}`.toLowerCase().includes(searchQuery)));
    } else {
      renderProducts(shopProducts, category);
    }
  }

  // Initialize checkout form in shop page if present
  if (document.getElementById("checkout-form") && document.getElementById("summary-items")) {
    initShopCheckout();
  }

  bindNavbar();
  bindCheckout();
  bindAdminProductForm();
  setupChatWidget();
  setupSearch();

  const year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();

  const subscribeForm = document.querySelector(".subscribe-form");
  if (subscribeForm) {
    subscribeForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const button = event.target.querySelector("button");
      const input = event.target.querySelector("input");
      button.textContent = "Subscribed";
      input.value = "";
      button.disabled = true;
      showToast("Thanks for subscribing");
    });
  }

  const privateAdminEntry = new URLSearchParams(window.location.search).get("cza-admin") === "1";
  if (document.body.classList.contains("admin-page")) {
    const isLoggedIn = sessionStorage.getItem(STORAGE_KEYS.admin) === "true";
    if (isLoggedIn) {
      document.getElementById("admin-login-screen")?.classList.add("hidden");
      document.getElementById("admin-shell")?.classList.remove("hidden");
      renderDashboard();
    }
    document.getElementById("currency-setting")?.addEventListener("change", (event) => {
      localStorage.setItem(STORAGE_KEYS.currency, event.target.value);
      renderDashboard();
      renderProducts(document.getElementById("featured-products"), "all");
      renderProducts(document.getElementById("shop-products"), "all");
      renderCart();
      showToast(`Currency changed to ${event.target.value}`);
    });
    const currencySetting = document.getElementById("currency-setting");
    if (currencySetting) currencySetting.value = getCurrency();
    initializeJjumaPayments();
    bindAccountSettings();
    setupAdminNotifications();
  } else if (privateAdminEntry && sessionStorage.getItem(STORAGE_KEYS.admin) === "true") {
    document.getElementById("admin-dashboard")?.classList.remove("hidden");
    renderDashboard();
  } else if (privateAdminEntry) {
    openAdminModal();
  }
}

function initShopCheckout() {
  // Reload cart from localStorage
  cart = JSON.parse(localStorage.getItem(STORAGE_KEYS.cart) || "[]");

  // Check if cart is empty
  if (!cart || cart.length === 0) {
    const checkoutEmpty = document.getElementById("checkout-empty-shop");
    const checkoutForm = document.getElementById("checkout-form");
    const goToBagSection = document.getElementById("go-to-bag-section");
    if (checkoutEmpty) checkoutEmpty.style.display = "block";
    if (checkoutForm) checkoutForm.style.display = "none";
    if (goToBagSection) goToBagSection.style.display = "none";
    return;
  }

  const checkoutEmpty = document.getElementById("checkout-empty-shop");
  const checkoutForm = document.getElementById("checkout-form");
  const goToBagSection = document.getElementById("go-to-bag-section");
  if (checkoutEmpty) checkoutEmpty.style.display = "none";
  if (checkoutForm) checkoutForm.style.display = "grid";
  if (goToBagSection) goToBagSection.style.display = "block";

  // Setup "Go to Bag" button
  const goToBagBtn = document.getElementById("go-to-bag-btn");
  if (goToBagBtn) {
    goToBagBtn.addEventListener("click", () => {
      const checkoutSection = document.getElementById("shop-checkout-section");
      if (checkoutSection) {
        checkoutSection.style.display = "block";
        checkoutSection.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  }

  // Initialize JJuma Payments
  initializeJjumaPayments();

  // Setup currency selector with highlighting
  const currencyBtns = document.querySelectorAll(".currency-btn");
  currencyBtns.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      currencyBtns.forEach((b) => {
        b.style.border = "2px solid var(--line)";
        b.style.background = "rgba(255, 255, 255, 0.6)";
        b.style.color = "var(--ink)";
      });
      btn.style.border = "3px solid var(--gold)";
      btn.style.background = "var(--gold-bright)";
      btn.style.color = "#fff";
      selectedCurrencyForPayment = btn.dataset.currency;
      updateOrderSummary();
    });
  });

  // Setup payment method highlighting
  const paymentRadios = document.querySelectorAll("input[name='paymentMethod']");
  paymentRadios.forEach((radio) => {
    radio.addEventListener("change", () => {
      const cardLabel = document.querySelector("label:has(input[value='card'])");
      const mobileLabel = document.querySelector("label:has(input[value='mobile_money'])");
      if (cardLabel && mobileLabel) {
        if (radio.value === "card") {
          cardLabel.style.border = "2px solid var(--gold)";
          mobileLabel.style.border = "2px solid var(--line)";
        } else {
          cardLabel.style.border = "2px solid var(--line)";
          mobileLabel.style.border = "2px solid var(--gold)";
        }
      }
    });
  });

  // Setup country code to country mapping
  setupCountryCodeMapping();

  // Setup form submission
  const form = document.getElementById("checkout-form");
  if (form) {
    form.addEventListener("submit", processCardPayment);
  }

  // Update order summary
  updateOrderSummary();

  // Listen for cart updates from other windows/tabs or same page
  window.addEventListener("cartUpdated", (event) => {
    cart = event.detail.cart;
    
    // Check if cart became empty
    if (!cart || cart.length === 0) {
      const checkoutEmpty = document.getElementById("checkout-empty-shop");
      const checkoutForm = document.getElementById("checkout-form");
      const goToBagSection = document.getElementById("go-to-bag-section");
      if (checkoutEmpty) checkoutEmpty.style.display = "block";
      if (checkoutForm) checkoutForm.style.display = "none";
      if (goToBagSection) goToBagSection.style.display = "none";
      return;
    }
    
    updateOrderSummary();
  });

  // Also listen to storage changes for cross-tab updates
  window.addEventListener("storage", (event) => {
    if (event.key === STORAGE_KEYS.cart) {
      cart = JSON.parse(event.newValue || "[]");
      
      // Check if cart became empty
      if (!cart || cart.length === 0) {
        const checkoutEmpty = document.getElementById("checkout-empty-shop");
        const checkoutForm = document.getElementById("checkout-form");
        const goToBagSection = document.getElementById("go-to-bag-section");
        if (checkoutEmpty) checkoutEmpty.style.display = "block";
        if (checkoutForm) checkoutForm.style.display = "none";
        if (goToBagSection) goToBagSection.style.display = "none";
        return;
      }
      
      updateOrderSummary();
    }
  });
}

// ============================================
// JJUMA PAYMENTS INTEGRATION
// ============================================

const JJUMA_CONFIG = {
  apiUrl: "/api/jjuma",
};

let jjumaConfigured = false;

function isJjumaConfigured() {
  return jjumaConfigured;
}

function updateGatewayStatus() {
  const status = document.querySelector(".gateway-status");
  if (!status) return;

  const statusIndicator = status.querySelector("i");
  const statusStrong = status.querySelector("strong");
  const statusText = status.querySelector("span");

  if (!statusIndicator || !statusStrong || !statusText) return;

  if (isJjumaConfigured()) {
    statusIndicator.style.background = "#3dbd7a";
    statusStrong.textContent = "Connected";
    statusText.textContent = "JJuma live credentials detected.";
  } else {
    statusIndicator.style.background = "#d4a15d";
    statusStrong.textContent = "Not configured";
    statusText.textContent = "JJuma credentials are not configured yet, so live checkout is unavailable.";
  }
}

let selectedCurrencyForPayment = "UGX";

async function initializeJjumaPayments() {
  try {
    const response = await fetch("/api/jjuma/config");
    if (response.ok) {
      const config = await response.json();
      jjumaConfigured = Boolean(config.configured);
      JJUMA_CONFIG.apiUrl = config.baseUrl || "/api/jjuma";
    } else {
      jjumaConfigured = false;
    }
  } catch (error) {
    console.warn("Could not load JJuma configuration:", error);
    jjumaConfigured = false;
  }

  updateGatewayStatus();
}

function getCurrencyRate(currency) {
  const rates = { UGX: 3750, USD: 1, EUR: 0.92, GBP: 0.78 };
  return rates[currency] || 1;
}

function convertPrice(basePrice, currency = "UGX") {
  const amount = Number(basePrice) || 0;
  if (currency === "UGX") {
    return amount;
  }

  return amount * (currencyRates[currency] || 1);
}

function getCartTotal(currency = "USD") {
  return cart.reduce((sum, item) => sum + (item.discountPrice || item.price) * item.qty, 0);
}

async function createJjumaPayment(orderData) {
  try {
    if (!isJjumaConfigured()) {
      throw new Error("JJuma Payments is not configured. Add live gateway credentials to enable real payments.");
    }

    const total = Number(orderData.total || getCartTotal("UGX") || 0);
    const amount = Math.round(total);

    const requestBody = {
      amount: amount,
      currency: "UGX",
      description: `Order from CZA - ${orderData.customerName}`,
      customerName: orderData.customerName,
      customerEmail: orderData.customerEmail,
      customerPhone: orderData.customerPhone,
      customerAddress: orderData.deliveryAddress,
      orderId: orderData.id,
      paymentMethod: orderData.paymentMethod,
      metadata: {
        orderId: orderData.id,
        customerName: orderData.customerName,
        deliveryAddress: orderData.deliveryAddress,
        items: orderData.items,
        paymentMethod: orderData.paymentMethod,
      },
    };

    const response = await fetch(`${JJUMA_CONFIG.apiUrl}/create-payment`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(errorData?.error || `Failed to create JJuma payment: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error creating JJuma payment:", error);
    throw error;
  }
}

function addPaymentMethodHint(checkoutUrl, paymentMethod) {
  if (!checkoutUrl) return checkoutUrl;

  try {
    const url = new URL(checkoutUrl);
    url.searchParams.set("payment_method", paymentMethod || "card");
    url.searchParams.set("method", paymentMethod || "card");
    return url.toString();
  } catch (error) {
    console.warn("Unable to attach payment method hint to checkout URL:", error);
    return checkoutUrl;
  }
}

async function processCardPayment(event) {
  event.preventDefault();

  if (!cart.length) {
    showErrorMessage("Add items before checkout");
    return;
  }

  const form = document.getElementById("checkout-form");
  if (!form) return;

  const formData = new FormData(form);
  const checkoutButton = document.getElementById("checkout-submit");
  const paymentLoading = document.getElementById("payment-loading");
  const paymentMethod = String(formData.get("paymentMethod") || "card");

  try {
    checkoutButton.disabled = true;
    paymentLoading.classList.add("show");

    // Validate form
    if (!form.checkValidity()) {
      showErrorMessage("Please fill in all required fields");
      paymentLoading.classList.remove("show");
      checkoutButton.disabled = false;
      return;
    }

    // Create order object
    const total = getCartTotal("UGX");
    const order = {
      id: Date.now(),
      customerName: String(formData.get("customerName") || "Customer").trim(),
      customerEmail: String(formData.get("customerEmail") || "").trim(),
      customerPhone: String(formData.get("customerPhone") || "").trim(),
      countryCode: String(formData.get("countryCode") || "+256"),
      deliveryAddress: String(formData.get("deliveryAddress") || "").trim(),
      deliveryCity: String(formData.get("customerCity") || "").trim(),
      deliveryRegion: String(formData.get("customerRegion") || "").trim(),
      deliveryCountry: String(formData.get("customerCountry") || "").trim(),
      deliveryNotes: String(formData.get("deliveryNotes") || "").trim(),
      items: cart.map((item) => ({ name: item.name, qty: item.qty, price: item.discountPrice || item.price })),
      total: total,
      currency: "UGX",
      status: "Pending",
      createdAt: new Date().toISOString(),
      paymentMethod,
    };

    if (paymentMethod === "card" || paymentMethod === "mobile_money") {
      if (!isJjumaConfigured()) {
        await initializeJjumaPayments();
      }

      if (!isJjumaConfigured()) {
        showErrorMessage("JJuma payments are not configured yet. Please add the live JJuma credentials first.");
        paymentLoading.classList.remove("show");
        checkoutButton.disabled = false;
        return;
      }

      try {
        const jjumaPayment = await createJjumaPayment(order);
        const checkoutUrl = jjumaPayment?.data?.payment_url || jjumaPayment?.payment_url || jjumaPayment?.checkout_url || jjumaPayment?.checkoutUrl || jjumaPayment?.url || jjumaPayment?.link;

        if (!checkoutUrl) {
          throw new Error("JJuma did not return a valid payment URL.");
        }

        const checkoutUrlWithMethodHint = addPaymentMethodHint(checkoutUrl, paymentMethod);

        order.reference = jjumaPayment?.data?.reference || jjumaPayment?.reference || order.id;
        order.transactionId = jjumaPayment?.data?.transaction_id || jjumaPayment?.transaction_id || order.reference;
        order.paymentProvider = "jjuma";
        order.paymentStatus = jjumaPayment?.data?.status || "pending";

        sessionStorage.setItem("pending_order", JSON.stringify(order));
        sessionStorage.setItem("payment_redirect_url", checkoutUrlWithMethodHint);
        window.location.href = checkoutUrlWithMethodHint;
        return;
      } catch (error) {
        console.error("JJuma payment flow failed:", error);
        showErrorMessage(error.message || "JJuma payment failed. Please try again later.");
      }

      paymentLoading.classList.remove("show");
      checkoutButton.disabled = false;
      return;
    }
  } catch (error) {
    console.error("Payment error:", error);
    showErrorMessage(`Payment failed: ${error.message}`);
    paymentLoading.classList.remove("show");
    checkoutButton.disabled = false;
  }
}

async function simulatePaymentProcessing(order, paymentIntent) {
  // Simulate payment processing delay
  await new Promise((resolve) => setTimeout(resolve, 2000));

  // JJuma handles the hosted checkout flow and redirects the customer back to the site.
  completeOrder(order);
}

function completeOrder(order) {
  try {
    // Save order to localStorage
    const orders = getOrders();
    orders.unshift({ ...order, status: "Confirmed" });
    saveOrders(orders);

    // Clear cart
    cart = [];
    localStorage.setItem(STORAGE_KEYS.cart, JSON.stringify(cart));

    // Clear pending order
    sessionStorage.removeItem("pending_order");
    sessionStorage.removeItem("payment_intent_id");

    // Show success page
    showPaymentSuccessPage(order);

    // Notify admin
    notifyAdminOfOrder(order);

    // Update dashboard
    renderDashboard();
  } catch (error) {
    console.error("Error completing order:", error);
    showErrorMessage("There was an issue saving your order. Please contact support.");
  }
}

function showPaymentSuccessPage(order) {
  const checkoutContent = document.getElementById("checkout-content");
  const paymentSuccess = document.getElementById("payment-success");

  if (checkoutContent) checkoutContent.style.display = "none";
  if (paymentSuccess) {
    const emailEl = document.getElementById("confirm-email");
    const orderIdEl = document.getElementById("confirm-order-id");
    const totalEl = document.getElementById("confirm-total");
    const phoneEl = document.getElementById("confirm-phone");
    const deliveryEl = document.getElementById("confirm-delivery");
    const linkEl = document.getElementById("confirm-link");

    if (emailEl) emailEl.textContent = order.customerEmail;
    if (orderIdEl) orderIdEl.textContent = `#${order.id}`;
    if (totalEl) totalEl.textContent = formatMoney(order.total, order.currency || getCurrency());
    if (phoneEl) phoneEl.textContent = order.customerPhone;
    if (deliveryEl) deliveryEl.textContent = `${order.deliveryCity || "Your city"}, ${order.deliveryCountry || "Your country"}`;
    if (linkEl) {
      const link = order.confirmationLink || buildConfirmationLink(order.id);
      linkEl.href = link;
      linkEl.textContent = link;
      linkEl.style.display = "inline-block";
    }

    paymentSuccess.classList.add("show");
  }
}

function showErrorMessage(message) {
  const errorEl = document.getElementById("error-message");
  if (errorEl) {
    errorEl.textContent = message;
    errorEl.classList.add("show");
    setTimeout(() => errorEl.classList.remove("show"), 5000);
  }
}

function initCheckoutPage() {
  const paymentStatus = new URLSearchParams(window.location.search).get("payment");
  const pendingOrderRaw = sessionStorage.getItem("pending_order");

  if (paymentStatus === "success" && pendingOrderRaw) {
    try {
      const pendingOrder = JSON.parse(pendingOrderRaw);
      completeOrder(pendingOrder);
      return;
    } catch (error) {
      console.warn("Unable to restore pending payment order:", error);
      sessionStorage.removeItem("pending_order");
    }
  }

  if (paymentStatus === "failed") {
    sessionStorage.removeItem("pending_order");
    sessionStorage.removeItem("payment_redirect_url");
    showErrorMessage("Your payment was not completed. You can try again or return to your bag.");
  }

  // Reload cart from localStorage to ensure fresh data
  cart = JSON.parse(localStorage.getItem(STORAGE_KEYS.cart) || "[]");
  
  // Check if cart is empty
  if (!cart || cart.length === 0) {
    const checkoutEmpty = document.getElementById("checkout-empty");
    const checkoutContent = document.getElementById("checkout-content");
    if (checkoutEmpty) checkoutEmpty.style.display = "block";
    if (checkoutContent) checkoutContent.style.display = "none";
    return;
  }

  const checkoutEmpty = document.getElementById("checkout-empty");
  const checkoutContent = document.getElementById("checkout-content");
  if (checkoutEmpty) checkoutEmpty.style.display = "none";
  if (checkoutContent) checkoutContent.style.display = "block";

  // Initialize JJuma Payments
  initializeJjumaPayments();

  // Setup currency selector with highlighting
  const currencyBtns = document.querySelectorAll(".currency-btn");
  currencyBtns.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      currencyBtns.forEach((b) => {
        b.style.border = "2px solid var(--line)";
        b.style.background = "rgba(255, 255, 255, 0.6)";
        b.style.color = "var(--ink)";
      });
      btn.style.border = "3px solid var(--gold)";
      btn.style.background = "var(--gold-bright)";
      btn.style.color = "#fff";
      selectedCurrencyForPayment = btn.dataset.currency;
      updateOrderSummary();
    });
  });

  // Setup payment method highlighting
  const paymentRadios = document.querySelectorAll("input[name='paymentMethod']");
  paymentRadios.forEach((radio) => {
    radio.addEventListener("change", () => {
      const cardLabel = document.querySelector("label:has(input[value='card'])");
      const mobileLabel = document.querySelector("label:has(input[value='mobile_money'])");
      if (cardLabel && mobileLabel) {
        if (radio.value === "card") {
          cardLabel.style.border = "2px solid var(--gold)";
          mobileLabel.style.border = "2px solid var(--line)";
        } else {
          cardLabel.style.border = "2px solid var(--line)";
          mobileLabel.style.border = "2px solid var(--gold)";
        }
      }
    });
  });

  // Setup country code to country mapping
  setupCountryCodeMapping();

  // Setup form submission
  const checkoutForm = document.getElementById("checkout-form");
  if (checkoutForm) {
    checkoutForm.addEventListener("submit", processCardPayment);
  }

  // Update order summary
  updateOrderSummary();

  // Set up year
  const year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();

  // Setup navbar for checkout page
  bindNavbar();

  // Listen for cart updates from other windows/tabs
  window.addEventListener("cartUpdated", (event) => {
    cart = event.detail.cart;
    updateOrderSummary();
  });

  // Also listen to storage changes for cross-tab updates
  window.addEventListener("storage", (event) => {
    if (event.key === STORAGE_KEYS.cart) {
      cart = JSON.parse(event.newValue || "[]");
      updateOrderSummary();
    }
  });
}

function setupCountryCodeMapping() {
  const countryCodeSelect = document.querySelector("select[name='countryCode']");
  const countryInput = document.getElementById("customerCountry");
  
  if (!countryCodeSelect || !countryInput) return;

  const countryMap = {
    "+256": "Uganda",
    "+1": "United States",
    "+44": "United Kingdom",
    "+33": "France",
    "+49": "Germany",
    "+39": "Italy",
    "+353": "Ireland",
    "+27": "South Africa",
    "+254": "Kenya",
    "+255": "Tanzania",
    "+250": "Rwanda",
    "+234": "Nigeria",
    "+233": "Ghana",
    "+20": "Egypt",
    "+971": "United Arab Emirates",
    "+91": "India",
    "+61": "Australia",
    "+86": "China",
    "+81": "Japan",
    "+82": "South Korea",
    "+55": "Brazil",
    "+34": "Spain",
    "+31": "Netherlands",
    "+32": "Belgium",
    "+47": "Norway",
    "+46": "Sweden",
    "+45": "Denmark",
    "+358": "Finland",
    "+41": "Switzerland",
    "+43": "Austria",
    "+36": "Hungary",
    "+48": "Poland",
    "+30": "Greece",
    "+90": "Turkey",
    "+212": "Morocco",
    "+216": "Tunisia",
    "+213": "Algeria",
    "+1-242": "Bahamas",
    "+1-246": "Barbados",
    "+1-441": "Bermuda",
    "+1-649": "Turks and Caicos",
    "+1-876": "Jamaica",
    "+1-868": "Trinidad and Tobago",
  };

  // Set initial country based on country code
  const updateCountry = () => {
    const selectedCode = countryCodeSelect.value;
    if (countryMap[selectedCode]) {
      countryInput.value = countryMap[selectedCode];
    }
  };

  updateCountry();

  // Update country when country code changes
  countryCodeSelect.addEventListener("change", updateCountry);
}

function updateOrderSummary() {
  const summaryItems = document.getElementById("summary-items");
  const summarySubtotal = document.getElementById("summary-subtotal");
  const summaryTotal = document.getElementById("summary-total");

  if (!summaryItems) return;

  // Render items with better formatting
  summaryItems.innerHTML = cart.length
    ? cart
        .map(
          (item) => `
      <div class="summary-item">
        <div style="flex: 1;">
          <div style="font-weight: 600; color: var(--ink); margin-bottom: 4px;">${item.name}</div>
          <span class="item-qty">×${item.qty}</span>
          <span style="font-size: 0.85rem; color: var(--muted);">${item.subtitle || ''}</span>
        </div>
        <span style="font-weight: 600; white-space: nowrap;">${formatMoney(convertPrice((item.discountPrice || item.price) * item.qty, selectedCurrencyForPayment), selectedCurrencyForPayment)}</span>
      </div>
    `
        )
        .join("")
    : '<p style="color: var(--muted); text-align: center; padding: 20px 0;">No items in bag</p>';

  const baseTotal = getCartTotal("UGX");
  const convertedSubtotal = convertPrice(baseTotal, selectedCurrencyForPayment);
  const convertedTotal = convertedSubtotal; // No tax/shipping in this demo

  if (summarySubtotal) {
    summarySubtotal.textContent = formatMoney(convertedSubtotal, selectedCurrencyForPayment);
  }
  if (summaryTotal) {
    summaryTotal.textContent = formatMoney(convertedTotal, selectedCurrencyForPayment);
  }
}

document.addEventListener("DOMContentLoaded", initApp);
