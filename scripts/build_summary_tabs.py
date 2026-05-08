# -*- coding: utf-8 -*-
from pathlib import Path
import json
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT_DIR / "dashboard_source"
DOCS_DIR = ROOT_DIR / "docs"
ASSETS_DIR = DOCS_DIR / "assets"

ASSETS_DIR.mkdir(parents=True, exist_ok=True)

LEAN_THRESHOLD = 10.0


def latest_file(prefix: str, suffix: str = ".csv") -> Path | None:
    matches = sorted(SOURCE_DIR.glob(f"{prefix}*{suffix}"))
    return matches[-1] if matches else None


def clean_geo_name(value):
    if pd.isna(value):
        return "Unknown"
    return str(value).strip()


def format_signed_pct(value):
    if pd.isna(value):
        return "N/A"
    if value > 0:
        return f"D+{abs(value):.1f}"
    if value < 0:
        return f"R+{abs(value):.1f}"
    return "Even"


def format_number(value):
    if pd.isna(value):
        return "N/A"
    return f"{int(round(value)):,}"


def classify_balance(dvr_pct, threshold=LEAN_THRESHOLD):
    if pd.isna(dvr_pct):
        return "unknown"
    if dvr_pct >= threshold:
        return "Democratic-leaning"
    if dvr_pct <= -threshold:
        return "Republican-leaning"
    return "competitive"


def find_required_columns(df, required_cols, file_label):
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"{file_label} is missing required columns: {missing}")


def summarize_party_balance_map(csv_path, geography_col, map_label, threshold=LEAN_THRESHOLD, top_n=3):
    df = pd.read_csv(csv_path)

    find_required_columns(
        df,
        [geography_col, "D", "R", "Oth", "total_voters", "D_pct", "R_pct", "Oth_pct", "DvR", "DvR_pct"],
        csv_path.name,
    )

    df = df.copy()
    df[geography_col] = df[geography_col].apply(clean_geo_name)
    df["balance_group"] = df["DvR_pct"].apply(lambda x: classify_balance(x, threshold))

    total_geos = len(df)
    total_voters = df["total_voters"].sum()

    dem_lean_count = (df["balance_group"] == "Democratic-leaning").sum()
    rep_lean_count = (df["balance_group"] == "Republican-leaning").sum()
    competitive_count = (df["balance_group"] == "competitive").sum()

    strongest_dem = df.sort_values("DvR_pct", ascending=False).iloc[0]
    strongest_rep = df.sort_values("DvR_pct", ascending=True).iloc[0]
    closest = df.assign(abs_margin=df["DvR_pct"].abs()).sort_values("abs_margin").iloc[0]

    top_dem = df.sort_values("DvR_pct", ascending=False).head(top_n)
    top_rep = df.sort_values("DvR_pct", ascending=True).head(top_n)

    top_dem_text = "; ".join(
        f"{row[geography_col]} ({format_signed_pct(row['DvR_pct'])})"
        for _, row in top_dem.iterrows()
    )

    top_rep_text = "; ".join(
        f"{row[geography_col]} ({format_signed_pct(row['DvR_pct'])})"
        for _, row in top_rep.iterrows()
    )

    return [
        f"The {map_label} map includes {total_geos:,} geographies representing {format_number(total_voters)} registered voters.",
        f"Using a +/-{threshold:.0f}-point D-vs-R margin as the competitive range, {competitive_count:,} geographies are competitive, {dem_lean_count:,} are Democratic-leaning and {rep_lean_count:,} are Republican-leaning.",
        f"The strongest Democratic margin is in {strongest_dem[geography_col]}, where Democrats lead Republicans {format_signed_pct(strongest_dem['DvR_pct'])} among registered voters.",
        f"The strongest Republican margin is in {strongest_rep[geography_col]}, where Republicans lead Democrats {format_signed_pct(strongest_rep['DvR_pct'])} among registered voters.",
        f"The closest geography is {closest[geography_col]}, with a D-vs-R margin of {format_signed_pct(closest['DvR_pct'])}.",
        f"The top Democratic-leaning areas are: {top_dem_text}.",
        f"The top Republican-leaning areas are: {top_rep_text}.",
    ]


def summarize_switcher_map(csv_path, geography_col, map_label, top_n=5):
    df = pd.read_csv(csv_path)

    find_required_columns(
        df,
        [geography_col, "total_switch", "D_net", "R_net", "Oth_net"],
        csv_path.name,
    )

    df = df.copy()
    df[geography_col] = df[geography_col].apply(clean_geo_name)

    total_switchers = df["total_switch"].sum()
    d_net = df["D_net"].sum()
    r_net = df["R_net"].sum()
    oth_net = df["Oth_net"].sum()

    top_r_gain = df.sort_values("R_net", ascending=False).head(top_n)
    top_d_gain = df.sort_values("D_net", ascending=False).head(top_n)

    top_r_text = "; ".join(
        f"{row[geography_col]} ({format_number(row['R_net'])})"
        for _, row in top_r_gain.iterrows()
    )

    top_d_text = "; ".join(
        f"{row[geography_col]} ({format_number(row['D_net'])})"
        for _, row in top_d_gain.iterrows()
    )

    sentences = [
        f"The {map_label} switcher data includes {format_number(total_switchers)} voters who changed parties.",
        f"Across the mapped areas, party switching produced a net change of {format_number(d_net)} for Democrats, {format_number(r_net)} for Republicans and {format_number(oth_net)} for other or unaffiliated voters.",
    ]

    if r_net > d_net:
        sentences.append(
            f"Republicans had the larger net gain from party switching, outpacing Democrats by {format_number(r_net - d_net)} voters."
        )
    elif d_net > r_net:
        sentences.append(
            f"Democrats had the larger net gain from party switching, outpacing Republicans by {format_number(d_net - r_net)} voters."
        )
    else:
        sentences.append("Democrats and Republicans had the same net gain from party switching.")

    sentences.append(f"The largest Republican net gains were in: {top_r_text}.")
    sentences.append(f"The largest Democratic net gains were in: {top_d_text}.")

    return sentences



def summarize_countywide_registration(csv_path):
    df = pd.read_csv(csv_path)

    find_required_columns(
        df,
        ["county", "D", "R", "Oth", "total_voters", "D_pct", "R_pct", "Oth_pct", "DvR", "DvR_pct"],
        csv_path.name,
    )

    row = df.iloc[0]
    county_name = clean_geo_name(row["county"])

    if row["DvR_pct"] > 0:
        margin_sentence = (
            f"Democrats lead Republicans countywide by {format_signed_pct(row['DvR_pct'])}, "
            f"or {format_number(row['DvR'])} voters."
        )
    elif row["DvR_pct"] < 0:
        margin_sentence = (
            f"Republicans lead Democrats countywide by {format_signed_pct(row['DvR_pct'])}, "
            f"or {format_number(abs(row['DvR']))} voters."
        )
    else:
        margin_sentence = "Democrats and Republicans are tied countywide among registered voters."

    sentences = [
        f"The countywide registration file covers {county_name} County and includes {format_number(row['total_voters'])} registered voters.",
        f"Democrats account for {format_number(row['D'])} voters, or {row['D_pct']:.1f}% of registered voters.",
        f"Republicans account for {format_number(row['R'])} voters, or {row['R_pct']:.1f}% of registered voters.",
        f"Other or unaffiliated voters account for {format_number(row['Oth'])} voters, or {row['Oth_pct']:.1f}% of registered voters.",
        margin_sentence,
    ]

    if "avg_age_years" in df.columns and pd.notna(row.get("avg_age_years")):
        sentences.append(
            f"The average registered voter age is {row['avg_age_years']:.1f} years."
        )

    if "avg_tenure_years" in df.columns and pd.notna(row.get("avg_tenure_years")):
        sentences.append(
            f"The average voter registration tenure is {row['avg_tenure_years']:.1f} years."
        )

    return sentences



def build_summary_tabs():
    tabs = []

    county_registration_path = latest_file("county_party_counts_")
    if county_registration_path and county_registration_path.exists():
        tabs.append(
            {
                "key": "county-registration",
                "title": "Countywide registration",
                "group": "Registration balance",
                "file": county_registration_path.name,
                "sentences": summarize_countywide_registration(county_registration_path),
            }
        )

    party_balance_files = [
        {
            "key": "muni-registration",
            "title": "Municipality registration",
            "prefix": "municipality_party_counts_",
            "geo_col": "municipality",
            "label": "municipality registration",
        },
        {
            "key": "school-registration",
            "title": "School district registration",
            "prefix": "school_district_party_counts_",
            "geo_col": "school_district",
            "label": "school district registration",
        },
        {
            "key": "precinct-registration",
            "title": "Precinct registration",
            "prefix": "precinct_split_party_counts_",
            "geo_col": "precinct_split_id",
            "label": "precinct registration",
        },
        {
            "key": "house-registration",
            "title": "State House registration",
            "prefix": "state_house_party_counts_",
            "geo_col": "state_house",
            "label": "state House registration",
        },
        {
            "key": "senate-registration",
            "title": "State Senate registration",
            "prefix": "state_senate_party_counts_",
            "geo_col": "state_senate",
            "label": "state Senate registration",
        },
    ]

    switcher_files = [
        {
            "key": "county-switching",
            "title": "Countywide party switching",
            "prefix": "county_party_switchers_enriched_",
            "geo_col": "county_1",
            "label": "countywide party switching",
        },
        {
            "key": "muni-switching",
            "title": "Municipality party switching",
            "prefix": "municipality_party_switchers_enriched_",
            "geo_col": "municipality",
            "label": "municipality party switching",
        },
        {
            "key": "school-switching",
            "title": "School district party switching",
            "prefix": "school_district_party_switchers_enriched_",
            "geo_col": "school_district",
            "label": "school district party switching",
        },
        {
            "key": "house-switching",
            "title": "State House party switching",
            "prefix": "state_house_party_switchers_enriched_",
            "geo_col": "state_house",
            "label": "state House party switching",
        },
        {
            "key": "senate-switching",
            "title": "State Senate party switching",
            "prefix": "state_senate_party_switchers_enriched_",
            "geo_col": "state_senate",
            "label": "state Senate party switching",
        },
    ]

    for item in party_balance_files:
        path = latest_file(item["prefix"])
        if path and path.exists():
            tabs.append(
                {
                    "key": item["key"],
                    "title": item["title"],
                    "group": "Registration balance",
                    "file": path.name,
                    "sentences": summarize_party_balance_map(
                        csv_path=path,
                        geography_col=item["geo_col"],
                        map_label=item["label"],
                    ),
                }
            )

    for item in switcher_files:
        path = latest_file(item["prefix"])
        if path and path.exists():
            tabs.append(
                {
                    "key": item["key"],
                    "title": item["title"],
                    "group": "Party switching",
                    "file": path.name,
                    "sentences": summarize_switcher_map(
                        csv_path=path,
                        geography_col=item["geo_col"],
                        map_label=item["label"],
                    ),
                }
            )

    out_path = ASSETS_DIR / "summary-tabs.js"
    out_path.write_text(
        "window.SUMMARY_TABS = " + json.dumps(tabs, indent=2) + ";\n",
        encoding="utf-8",
    )

    print(f"Wrote summary tabs: {out_path}")
    print(f"Summary tabs generated: {len(tabs)}")


if __name__ == "__main__":
    build_summary_tabs()
