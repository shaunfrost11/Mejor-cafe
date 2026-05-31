console.log("HELLO FROM APP.JS! THE FILE IS CONNECTED!");

const API_URL = "https://mejor-cafe.onrender.com"; // Change to http://127.0.0.1:8000 if testing locally
let cart = [];
let token = null;
let allProducts = []; 

// --- 1. INITIALIZATION ---
document.addEventListener("DOMContentLoaded", () => {
    checkLoginState();
    loadProducts();
});

// --- 2. AUTHENTICATION & UI STATE LOGIC ---
function checkLoginState() {
    console.log("--- 1. checkLoginState started ---");
    
    const savedToken = localStorage.getItem("token");
    const savedEmail = localStorage.getItem("email");
    const savedCart = localStorage.getItem("cart");
    
    console.log("--- 2. Storage Check | Token exists:", !!savedToken, "| Email:", savedEmail, "---");

    if (savedToken) {
        token = savedToken;
        console.log("--- 3. User is logged in. Updating UI... ---");

        try {
            // Helper functions that PREVENT crashes if an HTML element is missing
            const hideElement = (id) => {
                const el = document.getElementById(id);
                if (el) el.classList.add("hidden");
                else console.warn(`⚠️ Warning: Could not find HTML element to hide: '${id}'`);
            };
            
            const showElement = (id) => {
                const el = document.getElementById(id);
                if (el) el.classList.remove("hidden");
                else console.warn(`⚠️ Warning: Could not find HTML element to show: '${id}'`);
            };

            // 1. Hide Auth Sections
            hideElement("auth-container");
            hideElement("login-section");
            hideElement("signup-section");
            hideElement("profile-section");

            // 2. Show App Sections
            showElement("product-list");
            showElement("cart-section");
            showElement("btn-profile");
            showElement("btn-logout"); // The stubborn logout button!

            // 3. Set Email text
            const emailText = document.getElementById("profile-email");
            if (emailText) emailText.innerText = savedEmail || "";
            else console.warn("⚠️ Warning: Could not find 'profile-email' to set text.");

            console.log("--- 4. UI successfully updated! Restoring cart... ---");

            // 4. Restore Cart safely
            if (savedCart) {
                try {
                    cart = JSON.parse(savedCart);
                    updateCartUI();
                    console.log("--- 5. Cart restored successfully. ---");
                } catch (e) {
                    console.error("❌ Cart parsing failed:", e);
                    cart = [];
                }
            }
        } catch (error) {
            console.error("❌ CRASH inside checkLoginState:", error);
        }
    } else {
        console.log("--- 3. No token found. User is logged out. ---");
        // Ensure logged-out UI is visible
        const loginSection = document.getElementById("login-section");
        const authContainer = document.getElementById("auth-container");
        if (loginSection) loginSection.classList.remove("hidden");
        if (authContainer) authContainer.classList.remove("hidden");
    }
}

async function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const errorText = document.getElementById("login-error");
    
    const formData = new URLSearchParams();
    formData.append("username", email); 
    formData.append("password", password);

    try {
        const response = await fetch(`${API_URL}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            
            // Save to memory
            localStorage.setItem("token", data.access_token);
            localStorage.setItem("email", email);
            
            // Trigger the UI update!
            checkLoginState(); 
        } else {
            errorText.innerText = "Invalid credentials!";
        }
    } catch (error) {
        errorText.innerText = "Cannot connect to server.";
    }
}

function logout() {
    // 1. Wipe Memory
    token = null;
    cart = [];
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    localStorage.removeItem("cart");

    // 2. Reset UI by checking login state again
    checkLoginState();
    
    // 3. Ensure we are looking at the menu, not a blank profile screen
    viewMenu();
}

function toggleAuthMode(mode) {
    const loginSection = document.getElementById("login-section");
    const signupSection = document.getElementById("signup-section");
    document.getElementById("login-error").innerText = ""; 

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
        role: "customer" 
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
            alert(data.detail || "Registration failed.");
        }
    } catch (error) {
        alert("Cannot connect to server.");
    }
}

// --- 3. PRODUCT & VIEW LOGIC ---
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
        productContainer.innerHTML = "<p class='empty-cart-msg' style='grid-column: 1 / -1;'>No items found.</p>";
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

function viewMenu() {
    document.getElementById("profile-section").classList.add("hidden");
    document.getElementById("btn-menu").classList.add("hidden");
    
    document.getElementById("product-list").classList.remove("hidden");
    if(token) document.getElementById("btn-profile").classList.remove("hidden");
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
            document.getElementById("order-history-list").innerHTML = "<p style='color:red;'>Session expired. Please log out and log in again.</p>";
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
                <strong>Order #${order.order_id.substring(0,8)}...</strong>
                <span class="order-date">${new Date(order.created_at).toLocaleDateString()}</span>
            </div>
            <div class="order-details">
                <p>Status: <span style="text-transform: capitalize; font-weight: bold;">${order.status}</span></p>
                <p>Total: <strong>$${Number(order.total_amount).toFixed(2)}</strong></p>
            </div>
        </div>
    `).join('');
}

// --- 4. CART & CHECKOUT LOGIC ---
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

    // Save cart to local storage immediately
    if (token) {
        localStorage.setItem("cart", JSON.stringify(cart));
    }
}

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
            document.getElementById("checkout-message").innerHTML = `<span style="color: #6B8E23; font-weight:bold;">Success! Order ID: ${data.order_id.substring(0,8)}</span>`;
            cart = []; 
            localStorage.removeItem("cart"); 
            updateCartUI();
        } else {
            document.getElementById("checkout-message").innerHTML = `<span style="color: red;">Error: ${data.detail}</span>`;
        }
    } catch (error) {
        console.error("Checkout failed", error);
    }
}