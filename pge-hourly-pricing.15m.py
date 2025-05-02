#!/usr/bin/env python3
# <xbar.title>PGE Hourly Flex Pricing</xbar.title>
# <xbar.version>v1.2</xbar.version>
# <xbar.author>Cameron Tuckerman-Lee</xbar.author>
# <xbar.desc>Show current flex pricing forcast.</xbar.desc>
# <xbar.dependencies>python3</xbar.dependencies>
# <xbar.refresh>15m</xbar.refresh>
# <xbar.var>string(VAR_RATE="EV2A"): Rate plan to query.</xbar.var>
# <xbar.var>string(VAR_CIRCUIT="083611114"): Representative circuit ID.</xbar.var>
# <xbar.var>string(VAR_PROGRAM="CalFUSE"): Program name.</xbar.var>

import os
import urllib.request
import json
from datetime import datetime, date

API = "https://pge-pe-api.gridx.com/v1/getPricing"
RATE = os.getenv("VAR_RATE", "EV2A")
CIRCUIT = os.getenv("VAR_CIRCUIT", "083611114")
PROGRAM = os.getenv("VAR_PROGRAM", "CalFUSE")

BUCKETS = [
    (0.15, "🟢", "0¢-15¢"),
    (0.25, "🟡", "15¢-25¢"),
    (0.50, "🟠", "25¢-50¢"),
    (1.00, "🔴", "50¢-100¢"),
    (float("inf"), "⚠️", ">100¢"),
]


def _parse_ts(ts_str) -> datetime:
    return datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S%z")


def bucket_of(price) -> tuple[str, str]:
    for bound, emoji, label in BUCKETS:
        if price <= bound:
            return emoji, label
    return BUCKETS[-1][1], BUCKETS[-1][2]


def fetch_prices():
    today = date.today().strftime("%Y%m%d")
    url = (
        f"{API}?utility=PGE&market=DAM"
        f"&startdate={today}&enddate={today}"
        f"&ratename={RATE}&representativeCircuitId={CIRCUIT}"
        f"&program={PROGRAM}"
    )
    with urllib.request.urlopen(url) as r:
        data = json.load(r)
    return data["data"][0]["priceDetails"]


def group_intervals(details):
    grouped = []
    for entry in details:
        ts = _parse_ts(entry["startIntervalTimeStamp"])
        hr = ts.hour
        price = float(entry["intervalPrice"])
        emo, label = bucket_of(price)
        if not grouped or grouped[-1]["label"] != label:
            grouped.append({"start": hr, "end": hr + 1, "emoji": emo, "label": label})
        else:
            grouped[-1]["end"] = hr + 1
    return grouped


def format_range(r):
    return f"{r['start']:02d}00-{r['end']%24:02d}00\t{r['emoji']} {r['label']}"


def main():
    details = fetch_prices()
    now = datetime.now()
    current = next(
        (
            float(e["intervalPrice"])
            for e in details
            if _parse_ts(e["startIntervalTimeStamp"]).hour == now.hour
        ),
        None,
    )
    emoji, _ = bucket_of(current) if current is not None else ("❓", "")
    print(f"⚡ {emoji}" if current is not None else "⚡ ❓")
    print("---")
    print("Time\tPrice")
    for grp in group_intervals(details):
        print(format_range(grp))


if __name__ == "__main__":
    main()
