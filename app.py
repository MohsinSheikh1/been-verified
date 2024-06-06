from seleniumbase import SB
from flask import Flask, request, jsonify
import threading
import requests

app = Flask(__name__)

PATH = "C:\\Webdriver\\chromedriver.exe"
EMAIL = "eli@thrivecapital.us"
PASSWORD = "Thrive2024!"
ADDRESS = "1315 Count Mallard Dr SE, Decatur, AL 35601"
ADDRESS2 = "1315 N Council Ave."
LOGIN_URL = "https://www.beenverified.com/rf/login"
DASHBOARD_URL = "https://www.beenverified.com/rf/dashboard"
ZAPIER_HOOK = "https://hooks.zapier.com/hooks/catch/10788817/2y9sgyt/"


def login(sb):
    try:
        # type in email
        sb.driver.reconnect(5)
        sb.focus("#email", by="css selector", timeout=None)
        sb.press_keys("#email", EMAIL, by="css selector", timeout=None)
        sb.sleep(5)

        # type in password
        sb.driver.reconnect(5)
        sb.focus("#password", by="css selector", timeout=None)
        sb.press_keys("#password", PASSWORD, by="css selector", timeout=None)
        sb.sleep(5)

        # click on sign in button
        sb.driver.uc_click('button:contains("Sign In")', 20)

    except Exception as e:
        print("Failed to log in: ", e)  # logging
        raise Exception("Failed to log in.")


def save_cookies(sb):
    try:
        sb.delete_saved_cookies(name="cookies.txt")
        sb.save_cookies(name="cookies.txt")
    except Exception as e:
        print("Failed to save cookies: ", e)
        raise Exception("Failed to save cookies.")


def load_cookies(sb):
    try:
        sb.load_cookies(name="cookies.txt")
    except Exception as e:
        print("Failed to load cookies: ", e)
        raise Exception("Failed to load cookies.")


def scrape_data(sb, address):
    try:
        # search for property
        print("scraping started")
        print(sb.get_current_url())
        sb.driver.uc_click('button:contains("Property")')
        sb.sleep(2)
        sb.press_keys("input", address, by="css selector", timeout=None)
        sb.sleep(2)
        sb.driver.uc_click('button:contains("Search")', 5)
        sb.sleep(15)
        print("buttons clicked")

        sb.maximize_window()

        print(sb.get_current_url())
        print(sb.get_page_source())

        print(
            sb.is_text_visible("View Person Report", selector="html", by="css selector")
        )

        # find all the owners report button
        owners = sb.find_elements(
            "#possible-owners-section button:contains('View Person Report')",
        )

        print(len(owners))

        # if there are no owners simply return a response to user with no user found
        if owners == 0:
            sb.driver.quit()
            return
            # return jsonify({"message": "No owners found"}), 200

        # now we have to loop through all of the owners to collect their data
        original_window_handle = sb.driver.current_window_handle

        print(original_window_handle)

        owners_data = []

        for i in range(len(owners)):

            # click on owner
            owners[i].click()
            sb.sleep(10)

            # switch to owner window
            for handle in sb.driver.window_handles:
                if handle != original_window_handle:
                    sb.switch_to_window(handle)
                    sb.driver.switch_to.window(handle)
                    break

            sb.sleep(2)

            # get the no. of each data except name
            name = sb.get_text('h1[data-cy="overview-title"]', by="css selector")
            num_phone = sb.get_text('div[data-testid="1"] + div > p', by="css selector")
            num_emails = sb.get_text(
                'div[data-testid="2"] + div > p', by="css selector"
            )
            num_socials = sb.get_text(
                'div[data-testid="12"] + div > p', by="css selector"
            )

            # variables to store the data
            phone_nos = []
            emails = []
            socials = []

            # get the data
            if num_phone != 0:
                phone_els = sb.find_elements(
                    "#phone-numbers-section h2.css-1vugsqn", by="css selector", limit=0
                )

                for i in range(len(phone_els)):
                    phone_nos.append(phone_els[i].text)

            if num_emails != 0:
                email_els = sb.find_elements(
                    "#email-section h2.css-1vugsqn", by="css selector", limit=0
                )

                for i in range(len(email_els)):
                    emails.append(email_els[i].text)

            if num_socials != 0:
                social_els = sb.find_elements(
                    "#social-media-section  div.css-1mlztek a",
                    by="css selector",
                    limit=0,
                )

                for i in range(len(social_els)):
                    socials.append(social_els[i].get_attribute("href"))

            print("scraping finished")

            print("data")

            # print the data
            print("Phone No.: " + "".join(str(phone_no) for phone_no in phone_nos))
            print("Emails: " + "".join(str(email) for email in emails))
            print("Social Links: " + "".join(str(social) for social in socials))
            print("Person Name: " + str(name))

            # create an object for owner with i as index
            owner = {
                "index": i,
                "name": name,
                "phone_nos": phone_nos,
                "emails": emails,
                "socials": socials,
            }

            # push the data to owners_data array
            owners_data.append(owner)

            # close new window and switch to original window for more owners or completion
            sb.driver.close()
            sb.switch_to_window(original_window_handle)
            sb.driver.switch_to.window(original_window_handle)

            sb.sleep(10)

        print("before quitting")
        sb.driver.quit()

        # post the data to the webhook
        response = requests.post(ZAPIER_HOOK, json={"owners": owners_data})
        print(response.status_code)

        return

    except Exception as e:
        print("Failed to scrape data: ", e)
        raise Exception("Failed to scrape data.")

        # return the data to user
        # return jsonify({"owners": owners_data}), 200


def initial(address):
    print("inside thread")
    try:
        with SB(uc=True, undetectable=True) as sb:
            # open dashboard url
            sb.sleep(5)
            sb.driver.uc_open_with_reconnect(DASHBOARD_URL, 20)
            sb.sleep(25)

            # load cookies
            load_cookies(sb=sb)
            sb.sleep(10)

            # open dashboard again
            sb.driver.uc_open_with_reconnect(DASHBOARD_URL, reconnect_time=20)
            sb.sleep(25)

            print("cookies loaded")

            # Check Now if we are on login page or dashboard page
            if sb.get_current_url() == LOGIN_URL:

                # since we were redirected to url page, we will open login page again with reconnect
                sb.driver.uc_open_with_reconnect(LOGIN_URL, reconnect_time=20)
                sb.sleep(25)

                # now login
                login(sb=sb)
                sb.sleep(25)

            print("logged in")

            # save cookies
            save_cookies(sb=sb)
            sb.sleep(10)

            # Now we are in dashboard and ready to scrape data
            scrape_data(sb=sb, address=address)
    except Exception as e:
        print("Failed to scrape data: ", e)
        raise Exception("Failed to scrape data.")


@app.route("/")
def hello_world():
    return jsonify({"message": "here"})


@app.route("/scrape", methods=["POST"])
def scrape_endpoint():
    data = request.json
    address = data.get("address", "")

    print("got address")

    if not address:
        return jsonify({"error", "Address is required"}), 400

    print("starting thread")

    thread = threading.Thread(target=initial, args=(address,))
    thread.start()
    return jsonify({"message": "Scraping Started"})


if __name__ == "main":
    app.run(debug=True)
