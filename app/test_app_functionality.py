import requests
from bs4 import BeautifulSoup

BASE_URL = "http://127.0.0.1:8000"

results = []

def test_home():
    try:
        r = requests.get(BASE_URL + "/")
        assert r.status_code == 200 and "Perfumania" in r.text
        results.append(("Home page", True))
    except Exception as e:
        results.append(("Home page", False))

def test_shop():
    try:
        r = requests.get(BASE_URL + "/shop", allow_redirects=True)
        assert r.status_code == 200 and "Perfumania" in r.text
        results.append(("Shop page", True))
    except Exception as e:
        results.append(("Shop page", False))

def test_login():
    try:
        r = requests.get(BASE_URL + "/auths/login")
        assert r.status_code == 200 and ("login" in r.text.lower() or "sign in" in r.text.lower())
        results.append(("Login page", True))
    except Exception as e:
        results.append(("Login page", False))

def test_add_to_cart(product_id=1):
    try:
        s = requests.Session()
        # Simulate login by setting a fake session cookie if needed
        # s.cookies.set('session', '...')
        r = s.post(BASE_URL + f"/add-to-cart/{product_id}", allow_redirects=True)
        assert r.status_code in (200, 303)
        results.append(("Add to cart", True))
    except Exception as e:
        results.append(("Add to cart", False))

def test_cart():
    try:
        r = requests.get(BASE_URL + "/cart")
        assert r.status_code == 200 and ("cart" in r.text.lower())
        results.append(("View cart", True))
    except Exception as e:
        results.append(("View cart", False))

def test_remove_from_cart(cart_item_id=1):
    try:
        s = requests.Session()
        r = s.post(BASE_URL + f"/remove-from-cart/{cart_item_id}", allow_redirects=True)
        assert r.status_code in (200, 303)
        results.append(("Remove from cart", True))
    except Exception as e:
        results.append(("Remove from cart", False))

def test_checkout():
    try:
        r = requests.get(BASE_URL + "/checkout")
        assert r.status_code == 200 and ("checkout" in r.text.lower())
        results.append(("Checkout page", True))
    except Exception as e:
        results.append(("Checkout page", False))

def test_confirm_order():
    try:
        s = requests.Session()
        data = {
            "name": "Test User",
            "email": "testuser@example.com",
            "phone": "1234567890",
            "address": "123 Test Street"
        }
        r = s.post(BASE_URL + "/confirm-order", data=data, allow_redirects=True)
        assert r.status_code == 200 and ("order" in r.text.lower() or "confirmation" in r.text.lower())
        results.append(("Confirm order", True))
    except Exception as e:
        results.append(("Confirm order", False))

def print_results():
    print("\n--- FUNCTIONALITY TEST RESULTS ---")
    for name, ok in results:
        print(f"{name:25}: {'✅' if ok else '❌'}")

if __name__ == "__main__":
    test_home()
    test_shop()
    test_login()
    test_add_to_cart()
    test_cart()
    test_remove_from_cart()
    test_checkout()
    test_confirm_order()
    print_results()
