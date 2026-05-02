const API_URL = "https://mejor-cafe-backend.onrender.com";
let cart = [];
let token = null;

// NEW: A global variable to hold our menu in memory for instant searching
let allProducts = []; 

// 1. Fetch Products from Database
async function loadProducts() {
    try {
        const response = await fetch(`${API_URL}/products`);
        const data = await response.json();
        
        allProducts = data.products; // Save the database response to our global variable
        renderProducts(allProducts); // Draw all of them on the screen
        
    } catch (error) {
        console.error("Failed to load products", error);
    }
}

// 2. Draw Products on the Screen (Separated for reuse!)
function renderProducts(productsToDraw) {
    const productContainer = document.getElementById("product-list");
    productContainer.innerHTML = ""; 
    
    // If the search finds nothing, show a friendly message
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

// 3. The Live Search Engine
function filterMenu() {
    // Grab what the user typed and make it lowercase
    const query = document.getElementById("search-bar").value.toLowerCase();
    
    // Filter the global array. Keep items where the name OR description matches the query!
    const filtered = allProducts.filter(product => 
        product.name.toLowerCase().includes(query) || 
        product.description.toLowerCase().includes(query)
    );
    
    // Instantly redraw the screen with the filtered items
    renderProducts(filtered);
}

// ... The rest of your app.js (login, addToCart, checkout, etc.) stays exactly the same!

// 2. Handle Login
async function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    
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
            token = data.access_token;
            
            // --- FIXED: PROFILE REVEAL LOGIC ADDED HERE ---
            document.getElementById("profile-email").innerText = email; 
            document.getElementById("btn-profile").classList.remove("hidden"); 
            // ----------------------------------------------
            
            document.getElementById("login-section").classList.add("hidden");
            document.getElementById("cart-section").classList.remove("hidden");
        } else {
            document.getElementById("login-error").innerText = "Invalid credentials!";
        }
    } catch (error) {
        document.getElementById("login-error").innerText = "Cannot connect to server.";
    }
}

// 3. Handle Cart Logic
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
}

// 4. Handle Secure Checkout
async function checkout() {
    if (cart.length === 0) return alert("Your tray is empty!");

    const payload = { items: cart.map(item => ({ product_id: item.product_id, quantity: item.quantity })) };

    try {
        const response = await fetch(`${API_URL}/checkout`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok) {
            document.getElementById("checkout-message").innerHTML = `<span style="color: #6B8E23; font-weight:bold;">Success! Order ID: ${data.order_id}</span>`;
            cart = []; 
            updateCartUI();
        } else {
            document.getElementById("checkout-message").innerHTML = `<span style="color: red;">Error: ${data.detail}</span>`;
        }
    } catch (error) {
        console.error("Checkout failed", error);
    }
}

// Switches the view back to the coffee menu
function viewMenu() {
    document.getElementById("profile-section").classList.add("hidden");
    document.getElementById("btn-menu").classList.add("hidden");
    
    document.getElementById("product-list").classList.remove("hidden");
    document.getElementById("btn-profile").classList.remove("hidden");
}

// Switches to the profile view and fetches their specific orders
async function viewProfile() {
    // 1. Swap the UI
    document.getElementById("product-list").classList.add("hidden");
    document.getElementById("btn-profile").classList.add("hidden");
    
    document.getElementById("profile-section").classList.remove("hidden");
    document.getElementById("btn-menu").classList.remove("hidden");

    // 2. Fetch the orders from FastAPI
    try {
        const response = await fetch(`${API_URL}/my-orders`, {
            method: "GET",
            // We pass the token exactly like we did in the checkout function!
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

// 3. Draw the orders on the screen
function renderOrders(orders) {
    const container = document.getElementById("order-history-list");
    
    if (orders.length === 0) {
        container.innerHTML = "<p class='empty-cart-msg'>You haven't placed any orders yet.</p>";
        return;
    }

    // Loop through the database records and draw a receipt card for each one
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

// 5. Initialize the engine!
loadProducts();