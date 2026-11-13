import anime_discover
import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

queries = anime_discover.SHORT_QUERIES
# Just let it return everything from _rank_pool without limits so we can see how big the pool is.
pool = anime_discover._rank_pool(queries, 30, 8, 180, 200, "test")
print(f"Total pool size before probe: {len(pool)}")

verticais = 0
for r in pool:
    ar = anime_discover._aspect_ratio_remote(r["url"])
    if ar is not None and ar < 0.9:
        verticais += 1
        print(f"VERTICAL: {r['title']} ({ar})")

print(f"Total verticais in pool: {verticais}")
