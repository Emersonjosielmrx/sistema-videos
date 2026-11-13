import json, sys, urllib.parse, urllib.request
sys.path.insert(0, r"D:\postador-de-videos\bin")
import politica
cid = sys.argv[1]
c = [x for x in politica.carregar_creds() if x["id"] == cid][0]
d = urllib.parse.urlencode({"client_id": c["clientId"], "client_secret": c["clientSecret"],
                            "refresh_token": c["refresh_token"], "grant_type": "refresh_token"}).encode()
tok = json.loads(urllib.request.urlopen("https://oauth2.googleapis.com/token", d, timeout=30).read())["access_token"]
H = {"Authorization": "Bearer " + tok}


def get(u):
    return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30).read())


ch = get("https://www.googleapis.com/youtube/v3/channels?part=contentDetails,statistics&mine=true")["items"][0]
up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
ids = [i["contentDetails"]["videoId"] for i in
       get(f"https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults=50&playlistId={up}")["items"]]
vs = get("https://www.googleapis.com/youtube/v3/videos?part=statistics,snippet&id=" + ",".join(ids))["items"]
soma = sum(int(v["statistics"].get("viewCount", 0)) for v in vs)
print("canal (total do YouTube):", ch["statistics"]["viewCount"], "| soma dos últimos 50 vídeos agora:", soma)
for v in sorted(vs, key=lambda v: v["snippet"]["publishedAt"], reverse=True)[:5]:
    print(v["snippet"]["publishedAt"][:16], v["statistics"].get("viewCount"), v["snippet"]["title"][:50])
