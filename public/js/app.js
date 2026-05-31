const API_URL = "https://mejor-cafe.onrender.com";
let cart = [];
let token = null;
let allProducts = []; 

// --- 1. PRODUCT LOGIC ---
async function loadProducts() {
    try {
        const response = await fetch(`${API_URL}/products`);
        const data = await response.json();
        allProducts = data.products; 
        renderProducts(allProducts); 
    } catch (error) {
        console.error("Failed to load products", error);
    }
}

function renderProducts(productsToDraw) {
    const productContainer = document.getElementById("product-list");
    productContainer.innerHTML = ""; 
    
    if (productsToDraw.length === 0) {
        productContainer.innerHTML = "<p class='empty-cart-msg' style='grid-column: 1 / -1;'>No items found matching your search.</p>";
        return;
    }

    productsToDraw.forEach(product => {
        const card = document.createElement("div");
        card.className = "product-card";
        card.innerHTML = `
            <img src="${product.image_url}" alt="${product.name}" class="product-img">
            <div class="product-info">
                <h3>${product.name}</h3>
                <p>${product.description}</p>
                <div class="product-price">$${product.price.toFixed(2)}</div>
                <button class="btn-add" onclick="addToCart('${product.product_id}', '${product.name}', ${product.price})">
                    + Add to Tray
                </button>
            </div>
        `;
        productContainer.appendChild(card);
    });
}

function filterMenu() {
    const query = document.getElementById("search-bar").value.toLowerCase();
    const filtered = allProducts.filter(product => 
        product.name.toLowerCase().includes(query) || 
        product.description.toLowerCase().includes(query)
    );
    renderProducts(filtered);
}

// --- 2. AUTHENTICATION LOGIC (LOGIN & SIGNUP) ---

function toggleAuthMode(mode) {
    const loginSection = document.getElementById("login-section");
    const signupSection = document.getElementById("signup-section");
    const errorMsg = document.getElementById("login-error");
    
    if (errorMsg) errorMsg.innerText = ""; 

    if (mode === 'signup') {
        loginSection.classList.add("hidden");
        signupSection.classList.remove("hidden");
    } else {
        signupSection.classList.add("hidden");
        loginSection.classList.remove("hidden");
    }
}
async function register() {
    const email = document.getElementById("signup-email").value;
    const password = document.getElementById("signup-password").value;
    const fullName = document.getElementById("signup-fullname").value;

    const payload = {
        email: email,
        password: password,
        full_name: fullName,
        role: "customer" // Matches your backend requirement
    };

    try {
        const response = await fetch(`${API_URL}/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok) {
            alert("Account created successfully! Please log in.");
            toggleAuthMode('login');
        } else {
            document.getElementById("login-error").innerText = data.detail || "Registration failed.";
        }
    } catch (error) {
        document.getElementById("login-error").innerText = "Cannot connect to server.";
    }
}

async function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    
    const formData = new URLSearchParams();
    formData.append("username", email); // OAuth2 format uses 'username'
    formData.append("password", password);

    try {
        const response = await fetch(`${API_URL}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            token = data.access_token;
            localStorage.setItem("token", token);
            localStorage.setItem("email", email);
            
            console.log("Login successful, token saved to localStorage.");
            
            document.getElementById("profile-email").innerText = email; 
            document.getElementById("btn-profile").classList.remove("hidden"); 
            document.getElementById("login-section").classList.add("hidden");
            document.getElementById("cart-section").classList.remove("hidden");
            const logoutBtn = document.getElementById("btn-logout");
            if (logoutBtn) logoutBtn.classList.remove("hidden");
        } else {
            document.getElementById("login-error").innerText = "Invalid credentials!";
        }
    } catch (error) {
        document.getElementById("login-error").innerText = "Cannot connect to server.";
    }
}

function logout() {
    token = null;
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    cart = [];
    updateCartUI();

    document.getElementById("profile-email").innerText = "";
    document.getElementById("btn-profile").classList.add("hidden");
    document.getElementById("cart-section").classList.add("hidden");
    document.getElementById("login-section").classList.remove("hidden");
    
    const logoutBtn = document.getElementById("btn-logout");
    if (logoutBtn) logoutBtn.classList.add("hidden");

    viewMenu(); // Make sure they are brought back to the menu view
}

// --- 3. CART & CHECKOUT LOGIC ---
function addToCart(id, name, price) {
    if (!token) {
        alert("Please log in to start adding items to your tray!");
        return;
    }
    
    const existingItem = cart.find(item => item.product_id === id);
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({ product_id: id, name: name, price: price, quantity: 1 });
    }
    updateCartUI();
}

// --- UPDATED: Save cart to localStorage every time it updates ---
function updateCartUI() {
    const cartContainer = document.getElementById("cart-items");
    const cartCount = document.getElementById("cart-count");
    cartContainer.innerHTML = "";
    
    let total = 0;
    let totalItems = 0;

    if (cart.length === 0) {
        cartContainer.innerHTML = '<p class="empty-cart-msg">Your tray is empty.</p>';
    } else {
        cart.forEach(item => {
            total += item.price * item.quantity;
            totalItems += item.quantity;
            cartContainer.innerHTML += `
                <div class="cart-item">
                    <span><strong>${item.quantity}x</strong> ${item.name}</span>
                    <span>$${(item.price * item.quantity).toFixed(2)}</span>
                </div>
            `;
        });
    }
    
    document.getElementById("cart-total").innerText = total.toFixed(2);
    cartCount.innerText = totalItems;

    // NEW: Save the cart to local storage so it survives a refresh
    localStorage.setItem("cart", JSON.stringify(cart));
}

// --- UPDATED: Clear cart from storage after successful checkout ---
async function checkout() {
    if (cart.length === 0) return alert("Your tray is empty!");

    const payload = { items: cart.map(item => ({ product_id: item.product_id, quantity: item.quantity })) };

    try {
        const response = await fetch(`${API_URL}/checkout`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json", 
                "Authorization": `Bearer ${token}` 
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok) {
            document.getElementById("checkout-message").innerHTML = `<span style="color: #6B8E23; font-weight:bold;">Success! Order ID: ${data.order_id}</span>`;
            cart = []; 
            localStorage.removeItem("cart"); // NEW: Clear saved cart
            updateCartUI();
        } else {
            document.getElementById("checkout-message").innerHTML = `<span style="color: red;">Error: ${data.detail}</span>`;
        }
    } catch (error) {
        console.error("Checkout failed", error);
    }
}

// --- UPDATED: Bulletproof refresh handling ---
// --- BULLETPROOF LOGIN STATE CHECK ---
function checkLoginState() {
    const savedToken = localStorage.getItem("token");
    const savedEmail = localStorage.getItem("email");
    const savedCart = localStorage.getItem("cart");

    if (savedToken) {
        token = savedToken;
        
        // 1. Force hide all authentication sections
        const loginSection = document.getElementById("login-section");
        const signupSection = document.getElementById("signup-section");
        if (loginSection) loginSection.classList.add("hidden");
        if (signupSection) signupSection.classList.add("hidden");

        // 2. Force show the main store view and user controls
        const productList = document.getElementById("product-list");
        const cartSection = document.getElementById("cart-section");
        const btnProfile = document.getElementById("btn-profile");
        const btnLogout = document.getElementById("btn-logout");
        
        if (productList) productList.classList.remove("hidden");
        if (cartSection) cartSection.classList.remove("hidden");
        if (btnProfile) btnProfile.classList.remove("hidden");
        if (btnLogout) btnLogout.classList.remove("hidden");

        // 3. Restore user data
        const profileEmail = document.getElementById("profile-email");
        if (profileEmail) profileEmail.innerText = savedEmail || "";

        // 4. Restore Cart
        if (savedCart) {
            cart = JSON.parse(savedCart);
            updateCartUI();
        }
    }
}

// --- BULLETPROOF LOGOUT FUNCTION ---
function logout() {
    // 1. Clear memory and storage
    token = null;
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    localStorage.removeItem("cart"); 
    cart = [];
    updateCartUI();

    // 2. Hide logged-in UI elements
    const btnProfile = document.getElementById("btn-profile");
    const cartSection = document.getElementById("cart-section");
    const btnLogout = document.getElementById("btn-logout");
    const profileEmail = document.getElementById("profile-email");
    const profileSection = document.getElementById("profile-section");
    
    if (btnProfile) btnProfile.classList.add("hidden");
    if (cartSection) cartSection.classList.add("hidden");
    if (btnLogout) btnLogout.classList.add("hidden");
    if (profileSection) profileSection.classList.add("hidden");
    if (profileEmail) profileEmail.innerText = "";

    // 3. Show login view
    const loginSection = document.getElementById("login-section");
    const productList = document.getElementById("product-list");
    
    if (loginSection) loginSection.classList.remove("hidden");
    if (productList) productList.classList.remove("hidden"); // Optional: keep menu visible behind login
}

// --- 4. VIEW LOGIC ---
function viewMenu() {
    document.getElementById("profile-section").classList.add("hidden");
    document.getElementById("btn-menu").classList.add("hidden");
    document.getElementById("product-list").classList.remove("hidden");
    document.getElementById("btn-profile").classList.remove("hidden");
}

async function viewProfile() {
    document.getElementById("product-list").classList.add("hidden");
    document.getElementById("btn-profile").classList.add("hidden");
    document.getElementById("profile-section").classList.remove("hidden");
    document.getElementById("btn-menu").classList.remove("hidden");

    try {
        const response = await fetch(`${API_URL}/my-orders`, {
            method: "GET",
            headers: { "Authorization": `Bearer ${token}` } 
        });

        if (response.ok) {
            const data = await response.json();
            renderOrders(data.my_orders);
        } else {
            document.getElementById("order-history-list").innerHTML = "<p style='color:red;'>Session expired. Please log in again.</p>";
        }
    } catch (error) {
        console.error("Failed to fetch orders", error);
    }
}

function renderOrders(orders) {
    const container = document.getElementById("order-history-list");
    if (orders.length === 0) {
        container.innerHTML = "<p class='empty-cart-msg'>You haven't placed any orders yet.</p>";
        return;
    }

    container.innerHTML = orders.map(order => `
        <div class="order-card">
            <div class="order-header">
                <strong>Order #${order.order_id}</strong>
                <span class="order-date">${new Date(order.created_at).toLocaleDateString()}</span>
            </div>
            <div class="order-details">
                <p>Status: <span style="text-transform: capitalize; font-weight: bold;">${order.status}</span></p>
                <p>Total: <strong>$${Number(order.total_amount).toFixed(2)}</strong></p>
            </div>
        </div>
    `).join('');
}

