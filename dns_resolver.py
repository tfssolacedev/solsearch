import requests

def resolve_dns(domain):
    url = "https://cloudflare-dns.com/dns-query "
    headers = {"accept": "application/dns-json"}
    params = {"name": domain, "type": "A"}
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        return data["Answer"][0]["data"] if data.get("Answer") else None
    except:
        return None
