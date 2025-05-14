// cart.js
document.addEventListener('DOMContentLoaded', () => {
  // Add to cart buttons
  const addToCartButtons = document.querySelectorAll('[data-add-to-cart]');

  addToCartButtons.forEach(button => {
    button.addEventListener('click', async (e) => {
      const productId = button.getAttribute('data-product-id');
      const variantId = button.getAttribute('data-variant-id');
      const quantity = parseInt(document.getElementById('quantity')?.value || '1');

      try {
        const response = await fetch('/api/v1/cart/items/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
          },
          body: JSON.stringify({
            product: productId,
            variant: variantId || null,
            quantity: quantity
          })
        });

        if (response.ok) {
          const result = await response.json();
          updateCartCount();
          showNotification('Product added to cart!');
        } else {
          const error = await response.json();
          showNotification(error.error || 'Error adding product to cart', 'error');
        }
      } catch (error) {
        console.error('Error:', error);
        showNotification('Error adding product to cart', 'error');
      }
    });
  });

  // Function to get CSRF token from cookies
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // Function to update cart count in header
  async function updateCartCount() {
    try {
      const response = await fetch('/api/v1/cart/');
      if (response.ok) {
        const cart = await response.json();
        const cartCountElement = document.getElementById('cart-count');
        if (cartCountElement) {
          cartCountElement.textContent = cart.total_items;
          if (cart.total_items > 0) {
            cartCountElement.classList.remove('hidden');
          }
        }
      }
    } catch (error) {
      console.error('Error updating cart count:', error);
    }
  }

  // Call updateCartCount on page load
  updateCartCount();

  // Function to show notification
  function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg ${type === 'success' ? 'bg-green-500' : 'bg-red-500'
      } text-white`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
      notification.remove();
    }, 3000);
  }
});
