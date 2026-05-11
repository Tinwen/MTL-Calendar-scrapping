import requests as r
import json as js
from urllib.parse import urlencode
from env import URL, OUTPUT_FILE, HEADERS

def get_json_data(nb_page=0):
    common_filters = "content_type:playlist OR content_type:local_story OR content_type:product"

    search_params = urlencode({
        # "clickAnalytics": "true",
        # "facetFilters": '[["_filter_seasons:Été"]]',
        "facets": '["*"]',
        "filters": common_filters,
        # "highlightPostTag": "__/ais-highlight__",
        # "highlightPreTag": "__ais-highlight__",
        "hitsPerPage": 2000,
        "maxValuesPerFacet": 2000,
        "page": nb_page,
        "userToken": "anonymous-bb993afd-4418-404c-85a2-93ab7e23f3c8",
    })

    facet_params = urlencode({
        # "analytics": "false",
        # "clickAnalytics": "false",
        # "facets": "_filter_seasons",
        "filters": common_filters,
        # "highlightPreTag": "__ais-highlight__",
        "hitsPerPage": 2000,
        "maxValuesPerFacet": 2000,
        "page": nb_page,
        "userToken": "anonymous-bb993afd-4418-404c-85a2-93ab7e23f3c8",
    })

    form_data = {"requests": [
        {"indexName": "prod_fr_dates", "params": search_params},
        {"indexName": "prod_fr_dates", "params": facet_params},
    ]}

    response = r.post(URL, headers=HEADERS, json=form_data)
    return response


def extract_hits(results):
    """Extract relevant fields from a list of Algolia result objects."""
    items = []
    for result in results:
        for hit in result.get("hits", []):
            dates = hit.get("_event_all_dates") or []
            items.append({
                "uuid": hit.get("uuid"),
                "title": hit.get("title"),
                "_url": "https://www.mtl.org" + hit.get("_url"),
                "_event_all_dates_first": dates[0] if dates else None,
                "_event_all_dates_last": dates[-1] if dates else None,
                "_permanent_identifier": hit.get("_permanent_identifier"),
            })
    return items


def fill_json_file():
    # Load existing data
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing = js.load(f)
    except (FileNotFoundError, js.JSONDecodeError):
        existing = []

    existing_uuids = {item["uuid"] for item in existing if item.get("uuid")}

    response = get_json_data()
    data = response.json()

    if response.status_code != 200:
        print(f"Erreur API ({response.status_code}): {data.get('message', 'Unknown error')}")
        exit(1)

    json_list = data["results"]
    all_hits = extract_hits(json_list)

    for result in json_list:
        max_pages = result.get("nbPages", 0)
        for page in range(1, max_pages + 1):
            resp = get_json_data(page)
            all_hits.extend(extract_hits(resp.json().get("results", [])))
            print("Page ", page, " out of ", max_pages)

    # Filter out duplicates
    new_items = [item for item in all_hits if item.get("uuid") not in existing_uuids]
    existing.extend(new_items)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        js.dump(existing, f, ensure_ascii=False, indent=2)

    print(f"{len(new_items)} nouveaux événements ajoutés ({len(existing)} total dans {OUTPUT_FILE})")


if __name__ == "__main__":
    fill_json_file()
