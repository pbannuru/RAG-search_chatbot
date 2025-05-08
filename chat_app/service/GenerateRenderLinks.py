def getKaasLink(url, token):
    import requests
    import ssl
    import json

    payload = ""
    headers = {'Content-Type': 'application/json',
               "Authorization": f"Bearer {token}"}
    response=""

    if "extras_kaas" in url:
        response_temp = requests.get(url, headers=headers,verify=ssl.CERT_NONE)
        if response_temp.status_code==200:
            response=json.loads(response_temp.text)["render_link"]
        else:
            print(f"Error calling KaaS API")
            response = url
    else:
        response=url
    return response