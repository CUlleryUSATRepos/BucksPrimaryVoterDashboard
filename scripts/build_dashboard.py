from pathlib import Path
import json
import math

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import plotly.graph_objects as go


# =========================
# PATHS
# =========================

ROOT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT_DIR / "dashboard_source"
DOCS_DIR = ROOT_DIR / "docs"
ASSETS_DIR = DOCS_DIR / "assets"

DOCS_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)


# =========================
# FILE HELPERS
# =========================

def latest_file(prefix: str, suffix: str = ".csv") -> Path:
    matches = sorted(SOURCE_DIR.glob(f"{prefix}*{suffix}"))
    if not matches:
        raise FileNotFoundError(f"No file found for: {SOURCE_DIR / (prefix + '*' + suffix)}")
    return matches[-1]


def load_sources():
    files = {
        "precinct_map": SOURCE_DIR / "precinct_main_map.geojson",
        "municipality_stats": latest_file("municipality_party_counts_"),
        "precinct_stats": latest_file("precinct_split_party_counts_"),
        "weekly_regs": latest_file("county_registrations_weekly_"),
        "county_switchers": latest_file("county_party_switchers_enriched_"),
        "state_house_stats": latest_file("state_house_party_counts_"),
        "state_senate_stats": latest_file("state_senate_party_counts_"),
    }

    missing = [str(path) for path in files.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required source files:\n" + "\n".join(missing))

    data = {
        "files": files,
        "precinct_map": gpd.read_file(files["precinct_map"]),
        "municipality_stats": pd.read_csv(files["municipality_stats"]),
        "precinct_stats": pd.read_csv(files["precinct_stats"]),
        "weekly_regs": pd.read_csv(files["weekly_regs"]),
        "county_switchers": pd.read_csv(files["county_switchers"]),
        "state_house_stats": pd.read_csv(files["state_house_stats"]),
        "state_senate_stats": pd.read_csv(files["state_senate_stats"]),
    }

    return data


# =========================
# FORMAT HELPERS
# =========================

def fmt_int(value):
    if pd.isna(value):
        return "0"
    return f"{int(round(value)):,}"


def fmt_signed_int(value):
    if pd.isna(value):
        return "0"
    value = int(round(value))
    return f"+{value:,}" if value > 0 else f"{value:,}"


def fmt_pct(value):
    if pd.isna(value):
        return "0%"
    return f"{value:.1f}%"


def clean_geo_name(value):
    if pd.isna(value):
        return "Unknown"
    return str(value).strip()


def precinct_display_name(row):
    precinct_id = clean_geo_name(row.get("precinct_split_id", "Unknown precinct"))
    municipality = clean_geo_name(row.get("municipality", ""))

    if municipality and municipality != "Unknown":
        return f"{municipality}, precinct {precinct_id}"

    return f"precinct {precinct_id}"
# =========================
# MAP HELPERS
# =========================

DVR_BINS = [-100, -10, -5, -2.5, 2.5, 5, 10, 100]
DVR_LABELS = [
    "R +10 or more",
    "R +5 to +10",
    "R +2.5 to +5",
    "Within 2.5 points",
    "D +2.5 to +5",
    "D +5 to +10",
    "D +10 or more",
]

DVR_COLORS = {
    "R +10 or more": "#8B0000",
    "R +5 to +10": "#C43C39",
    "R +2.5 to +5": "#F4A3A3",
    "Within 2.5 points": "#D8C4E8",
    "D +2.5 to +5": "#A8C7F0",
    "D +5 to +10": "#4F83CC",
    "D +10 or more": "#174A8B",
}


def add_dvr_category(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["DvR_category"] = pd.cut(
        df["DvR_pct"],
        bins=DVR_BINS,
        labels=DVR_LABELS,
        include_lowest=True,
    )
    df["map_color"] = df["DvR_category"].map(DVR_COLORS)
    return df


def save_geography_map(
    gdf: gpd.GeoDataFrame,
    title: str,
    output_name: str,
    label_col: str | None = None,
):
    """
    Export an interactive Plotly HTML choropleth map.
    Hover tooltips replace hard-to-read labels on the map.
    """
    gdf = add_dvr_category(gdf).copy()

    if gdf.crs is None:
        gdf = gdf.set_crs(4326)
    else:
        gdf = gdf.to_crs(4326)

    gdf["_map_id"] = gdf.index.astype(str)

    def safe_value(row, col, default=""):
        if col not in row.index or pd.isna(row[col]):
            return default
        return row[col]

    def fmt_int_local(value):
        if pd.isna(value):
            return "0"
        return f"{int(round(value)):,}"

    def fmt_pct_local(value):
        if pd.isna(value):
            return "0.0%"
        return f"{float(value):.1f}%"

    def margin_label(value):
        if pd.isna(value):
            return "N/A"
        value = float(value)
        if value > 0:
            return f"D +{abs(value):.1f} pts"
        if value < 0:
            return f"R +{abs(value):.1f} pts"
        return "Even"

    def display_name(row):
        if label_col and label_col in row.index and pd.notna(row[label_col]):
            return str(row[label_col]).strip()

        for fallback in ["municipality", "state_house", "state_senate", "precinctid", "precinct_split_id"]:
            if fallback in row.index and pd.notna(row[fallback]):
                return str(row[fallback]).strip()

        return "Unknown"

    def hover_text(row):
        name = display_name(row)

        parts = [
            f"<b>{name}</b>",
            f"Total voters: {fmt_int_local(safe_value(row, 'total_voters', 0))}",
            f"Democratic: {fmt_int_local(safe_value(row, 'D', 0))} - {fmt_pct_local(safe_value(row, 'D_pct', 0))}",
            f"Republican: {fmt_int_local(safe_value(row, 'R', 0))} - {fmt_pct_local(safe_value(row, 'R_pct', 0))}",
            f"Other/unaffiliated: {fmt_int_local(safe_value(row, 'Oth', 0))} - {fmt_pct_local(safe_value(row, 'Oth_pct', 0))}",
            f"D vs. R margin: {margin_label(safe_value(row, 'DvR_pct', np.nan))}",
        ]

        if "avg_age_years" in row.index and pd.notna(row["avg_age_years"]):
            parts.append(f"Avg. age: {float(row['avg_age_years']):.1f}")

        if "avg_tenure_years" in row.index and pd.notna(row["avg_tenure_years"]):
            parts.append(f"Avg. tenure: {float(row['avg_tenure_years']):.1f} years")

        return "<br>".join(parts)

    gdf["_hover"] = gdf.apply(hover_text, axis=1)

    geojson = json.loads(gdf.to_json())

    fig = go.Figure()

    for category in DVR_LABELS:
        subset = gdf[gdf["DvR_category"].astype(str) == category].copy()

        if subset.empty:
            continue

        color = DVR_COLORS[category]

        fig.add_trace(
            go.Choropleth(
                geojson=geojson,
                locations=subset["_map_id"],
                z=[1] * len(subset),
                featureidkey="properties._map_id",
                colorscale=[[0, color], [1, color]],
                showscale=False,
                marker_line_color="white",
                marker_line_width=0.6,
                name=category,
                hovertext=subset["_hover"],
                hovertemplate="%{hovertext}<extra></extra>",
            )
        )

    no_data = gdf[gdf["DvR_category"].isna()].copy()
    if not no_data.empty:
        fig.add_trace(
            go.Choropleth(
                geojson=geojson,
                locations=no_data["_map_id"],
                z=[1] * len(no_data),
                featureidkey="properties._map_id",
                colorscale=[[0, "#E6E6E6"], [1, "#E6E6E6"]],
                showscale=False,
                marker_line_color="white",
                marker_line_width=0.6,
                name="No data",
                hovertext=no_data["_hover"],
                hovertemplate="%{hovertext}<extra></extra>",
            )
        )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
    )

    fig.update_layout(
        title={
            "text": title,
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 24},
        },
        height=680,
        margin={"l": 10, "r": 10, "t": 70, "b": 10},
        legend={
            "title": {"text": "D vs. R margin"},
            "orientation": "v",
            "x": 0.01,
            "y": 0.02,
            "bgcolor": "rgba(255,255,255,0.85)",
            "bordercolor": "#ddd",
            "borderwidth": 1,
        },
    )

    out_path = ASSETS_DIR / Path(output_name).with_suffix(".html").name
    fig.write_html(out_path, include_plotlyjs="cdn", full_html=True)

    print(f"Saved interactive map: {out_path}")
    return out_path




def build_precinct_map(precinct_map, precinct_stats):
    precinct_map = precinct_map.copy()
    precinct_stats = precinct_stats.copy()

    if "precinctid" not in precinct_map.columns:
        raise KeyError("'precinctid' not found in precinct_main_map.geojson")

    if "precinct_split_id" not in precinct_stats.columns:
        raise KeyError("'precinct_split_id' not found in precinct stats CSV")

    precinct_map["precinctid"] = precinct_map["precinctid"].astype(str).str.strip()
    precinct_stats["precinct_split_id"] = precinct_stats["precinct_split_id"].astype(str).str.strip()

    merged = precinct_map.merge(
        precinct_stats,
        left_on="precinctid",
        right_on="precinct_split_id",
        how="left",
    )

    if "municipality" in merged.columns:
        merged["precinct_label"] = (
            merged["municipality"].fillna("Unknown").astype(str).str.strip()
            + " - Precinct "
            + merged["precinctid"].astype(str).str.strip()
        )
    else:
        merged["precinct_label"] = "Precinct " + merged["precinctid"].astype(str).str.strip()

    return save_geography_map(
        merged,
        "Bucks County voter registration by precinct",
        "countywide_precinct_map.html",
        label_col="precinct_label",
    )


def build_municipality_map(precinct_map, municipality_stats):
    precinct_map = precinct_map.copy()
    municipality_stats = municipality_stats.copy()

    if "municipality" not in precinct_map.columns:
        raise KeyError("'municipality' not found in precinct_main_map.geojson")

    if "municipality" not in municipality_stats.columns:
        raise KeyError("'municipality' not found in municipality stats CSV")

    precinct_map["municipality"] = precinct_map["municipality"].astype(str).str.strip()
    municipality_stats["municipality"] = municipality_stats["municipality"].astype(str).str.strip()

    dissolved = precinct_map.dissolve(by="municipality", as_index=False)

    merged = dissolved.merge(
        municipality_stats,
        on="municipality",
        how="left",
    )

    return save_geography_map(
        merged,
        "Bucks County voter registration by municipality",
        "municipality_map.png",
        label_col="municipality",
    )


def build_district_map(precinct_map, district_stats, district_col, title, output_name):
    precinct_map = precinct_map.copy()
    district_stats = district_stats.copy()

    if district_col not in precinct_map.columns:
        print(f"Skipping {title}: '{district_col}' not found in precinct_main_map.geojson")
        return None

    if district_col not in district_stats.columns:
        print(f"Skipping {title}: '{district_col}' not found in stats CSV")
        return None

    precinct_map[district_col] = precinct_map[district_col].astype(str).str.strip()
    district_stats[district_col] = district_stats[district_col].astype(str).str.strip()

    dissolved = precinct_map.dissolve(by=district_col, as_index=False)

    merged = dissolved.merge(
        district_stats,
        on=district_col,
        how="left",
    )

    return save_geography_map(
        merged,
        title,
        output_name,
        label_col=district_col,
    )


# =========================
# CHARTS
# =========================

def build_weekly_registration_chart(weekly_regs):
    df = weekly_regs.copy()
    df["week"] = pd.to_datetime(df["week"], errors="coerce")
    df = df[df["week"].notna()].sort_values("week")

    cutoff = pd.Timestamp("2026-01-01")
    df = df[df["week"] >= cutoff].copy()

    fig = go.Figure()

    for party, label in [
        ("D", "Democratic"),
        ("R", "Republican"),
        ("Oth", "Other / unaffiliated"),
    ]:
        if party in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["week"],
                    y=df[party],
                    mode="lines+markers",
                    name=label,
                )
            )

    fig.update_layout(
        title="Weekly new voter registrations since Jan. 1, 2026",
        xaxis_title="Week",
        yaxis_title="New registrations",
        template="plotly_white",
        height=450,
        margin=dict(l=40, r=30, t=70, b=40),
    )

    out_path = ASSETS_DIR / "weekly_registration_chart.html"
    fig.write_html(out_path, include_plotlyjs="cdn", full_html=True)

    return out_path


def build_cumulative_registration_chart(weekly_regs):
    df = weekly_regs.copy()
    df["week"] = pd.to_datetime(df["week"], errors="coerce")
    df = df[df["week"].notna()].sort_values("week")

    cutoff = pd.Timestamp("2026-01-01")
    df = df[df["week"] >= cutoff].copy()

    for party in ["D", "R", "Oth"]:
        if party in df.columns:
            df[f"{party}_cum_2026"] = df[party].cumsum()

    fig = go.Figure()

    for col, label in [
        ("D_cum_2026", "Democratic"),
        ("R_cum_2026", "Republican"),
        ("Oth_cum_2026", "Other / unaffiliated"),
    ]:
        if col in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["week"],
                    y=df[col],
                    mode="lines+markers",
                    name=label,
                )
            )

    fig.update_layout(
        title="Cumulative new voter registrations since Jan. 1, 2026",
        xaxis_title="Week",
        yaxis_title="Cumulative registrations",
        template="plotly_white",
        height=450,
        margin=dict(l=40, r=30, t=70, b=40),
    )

    out_path = ASSETS_DIR / "cumulative_registration_chart.html"
    fig.write_html(out_path, include_plotlyjs="cdn", full_html=True)

    return out_path


# =========================
# SUMMARY CARD LOGIC
# =========================

def summarize_party_balance(df, geography_col):
    df = df.copy()
    df = df[df["total_voters"].notna()].copy()

    total_geos = len(df)
    total_voters = df["total_voters"].sum()

    competitive = df[df["DvR_pct"].abs() <= 2.5]
    dem_leaning = df[df["DvR_pct"] > 2.5]
    rep_leaning = df[df["DvR_pct"] < -2.5]

    strongest_dem = df.sort_values("DvR_pct", ascending=False).iloc[0]
    strongest_rep = df.sort_values("DvR_pct", ascending=True).iloc[0]
    closest = df.assign(abs_margin=df["DvR_pct"].abs()).sort_values("abs_margin").iloc[0]

    return {
        "total_geos": total_geos,
        "total_voters": int(total_voters),
        "competitive_count": len(competitive),
        "dem_leaning_count": len(dem_leaning),
        "rep_leaning_count": len(rep_leaning),
        "strongest_dem_name": precinct_display_name(strongest_dem) if geography_col == "precinct_split_id" else clean_geo_name(strongest_dem[geography_col]),
        "strongest_dem_margin": strongest_dem["DvR_pct"],
        "strongest_rep_name": precinct_display_name(strongest_rep) if geography_col == "precinct_split_id" else clean_geo_name(strongest_rep[geography_col]),
        "strongest_rep_margin": strongest_rep["DvR_pct"],
        "closest_name": precinct_display_name(closest) if geography_col == "precinct_split_id" else clean_geo_name(closest[geography_col]),
        "closest_margin": closest["DvR_pct"],
    }


def summarize_switchers(county_switchers):
    row = county_switchers.iloc[0]

    return {
        "total_switch": row.get("total_switch", 0),
        "D_gain": row.get("D_gain", 0),
        "D_loss": row.get("D_loss", 0),
        "D_net": row.get("D_net", 0),
        "R_gain": row.get("R_gain", 0),
        "R_loss": row.get("R_loss", 0),
        "R_net": row.get("R_net", 0),
        "Oth_gain": row.get("Oth_gain", 0),
        "Oth_loss": row.get("Oth_loss", 0),
        "Oth_net": row.get("Oth_net", 0),
        "D_to_R": row.get("D_to_R", 0),
        "R_to_D": row.get("R_to_D", 0),
        "D_to_Oth": row.get("D_to_Oth", 0),
        "R_to_Oth": row.get("R_to_Oth", 0),
        "Oth_to_D": row.get("Oth_to_D", 0),
        "Oth_to_R": row.get("Oth_to_R", 0),
    }

def party_balance_summary_html(summary, geography_label):
    return f"""
    <p>
      This view includes <strong>{fmt_int(summary["total_voters"])}</strong>
      voters across <strong>{fmt_int(summary["total_geos"])}</strong> {geography_label}.
      There are <strong>{fmt_int(summary["dem_leaning_count"])}</strong> Democratic-leaning {geography_label},
      <strong>{fmt_int(summary["rep_leaning_count"])}</strong> Republican-leaning {geography_label},
      and <strong>{fmt_int(summary["competitive_count"])}</strong> within 2.5 points.
    </p>

    <p>
      The strongest Democratic margin is in <strong>{summary["strongest_dem_name"]}</strong>
      at <strong>{fmt_pct(summary["strongest_dem_margin"])}</strong>.
      The strongest Republican margin is in <strong>{summary["strongest_rep_name"]}</strong>
      at <strong>{fmt_pct(abs(summary["strongest_rep_margin"]))}</strong>.
      The closest area is <strong>{summary["closest_name"]}</strong>,
      with a D-vs-R margin of <strong>{fmt_pct(summary["closest_margin"])}</strong>.
    </p>
    """
# =========================
# HTML BUILD
# =========================

def iframe_html(asset_name, height=520):
    return f'''
    <iframe
        src="assets/{asset_name}"
        width="100%"
        height="{height}"
        loading="lazy"
        style="border: 1px solid #ddd; border-radius: 10px; background: white;"
    ></iframe>
    '''


def img_html(asset_name, alt_text):
    return f'''
    <img
        src="assets/{asset_name}"
        alt="{alt_text}"
        class="dashboard-img"
    />
    '''


def build_index_html(context):
    """
    Legacy function name, but this no longer rewrites docs/index.html.
    It only writes docs/assets/dashboard-data.js for the static dashboard shell.
    """
    if "municipality_summary" in context:
        primary_summary = context["municipality_summary"]
        primary_key = "municipality"
        primary_button = "Municipalities"
        primary_title = "Municipality registration map"
        primary_frame = "assets/municipality_map.html"
        primary_geo_label = "municipalities"
        total_geos_label = "Total municipalities"
    else:
        primary_summary = context["county_summary"]
        primary_key = "precinct"
        primary_button = "County precincts"
        primary_title = "Countywide precinct registration map"
        primary_frame = "assets/countywide_precinct_map.html"
        primary_geo_label = "precincts"
        total_geos_label = "Total precincts"

    switch_summary = context["switch_summary"]
    source_files = context["source_files"]

    map_views = {
        primary_key: {
            "buttonLabel": primary_button,
            "title": primary_title,
            "frame": primary_frame,
            "summary": party_balance_summary_html(primary_summary, primary_geo_label),
        },
        "precinct": {
            "buttonLabel": "Precincts",
            "title": "Precinct registration map",
            "frame": "assets/countywide_precinct_map.html",
            "summary": party_balance_summary_html(context["precinct_summary"], "precincts"),
        },
        "house": {
            "buttonLabel": "State House",
            "title": "State House registration map",
            "frame": "assets/state_house_map.html",
            "summary": party_balance_summary_html(context["state_house_summary"], "State House districts"),
        },
        "senate": {
            "buttonLabel": "State Senate",
            "title": "State Senate registration map",
            "frame": "assets/state_senate_map.html",
            "summary": party_balance_summary_html(context["state_senate_summary"], "State Senate districts"),
        },
    }

    switcher_summary_html = f"""
    <p>
      The county file identifies <strong>{fmt_int(switch_summary["total_switch"])}</strong>
      voters whose current registration differs from the party they voted in during the 2024 general election.
    </p>

    <p>
      Democrats had a net change of <strong>{fmt_signed_int(switch_summary["D_net"])}</strong>
      after gaining <strong>{fmt_int(switch_summary["D_gain"])}</strong> voters and losing
      <strong>{fmt_int(switch_summary["D_loss"])}</strong>.
      Republicans had a net change of <strong>{fmt_signed_int(switch_summary["R_net"])}</strong>
      after gaining <strong>{fmt_int(switch_summary["R_gain"])}</strong> voters and losing
      <strong>{fmt_int(switch_summary["R_loss"])}</strong>.
      Other or unaffiliated voters had a net change of
      <strong>{fmt_signed_int(switch_summary["Oth_net"])}</strong>.
    </p>

    <p>
      Direct party movement included
      <strong>{fmt_int(switch_summary["D_to_R"])}</strong> Democratic-to-Republican switches,
      <strong>{fmt_int(switch_summary["R_to_D"])}</strong> Republican-to-Democratic switches,
      <strong>{fmt_int(switch_summary["D_to_Oth"])}</strong> Democratic-to-other switches,
      <strong>{fmt_int(switch_summary["R_to_Oth"])}</strong> Republican-to-other switches,
      <strong>{fmt_int(switch_summary["Oth_to_D"])}</strong> other-to-Democratic switches,
      and <strong>{fmt_int(switch_summary["Oth_to_R"])}</strong> other-to-Republican switches.
    </p>
    """

    dashboard_data = {
        "statCards": {
            "totalGeosLabel": total_geos_label,
            "totalGeos": fmt_int(primary_summary["total_geos"]),
            "totalVoters": fmt_int(primary_summary["total_voters"]),
            "competitiveCount": fmt_int(primary_summary["competitive_count"]),
            "partySwitchers": fmt_int(switch_summary["total_switch"]),
        },
        "mapViews": map_views,
        "switcherSummaryHtml": switcher_summary_html,
        "sourceFiles": {
            name: path.name
            for name, path in source_files.items()
        },
    }

    out_path = ASSETS_DIR / "dashboard-data.js"
    out_path.write_text(
        "window.DASHBOARD_DATA = " + json.dumps(dashboard_data, indent=2) + ";\n",
        encoding="utf-8",
    )

    print(f"Wrote dashboard data: {out_path}")
    return DOCS_DIR / "index.html"


# =========================
# MAIN
# =========================

def main():
    data = load_sources()

    print("Loaded source files:")
    for name, path in data["files"].items():
        print(f"  {name}: {path.name}")

    municipality_map = build_municipality_map(
        data["precinct_map"],
        data["municipality_stats"],
    )

    precinct_map_view = build_precinct_map(
        data["precinct_map"],
        data["precinct_stats"],
    )

    state_house_map = build_district_map(
        data["precinct_map"],
        data["state_house_stats"],
        "state_house",
        "Bucks County voter registration by State House district",
        "state_house_map.png",
    )

    state_senate_map = build_district_map(
        data["precinct_map"],
        data["state_senate_stats"],
        "state_senate",
        "Bucks County voter registration by State Senate district",
        "state_senate_map.png",
    )

    build_weekly_registration_chart(data["weekly_regs"])
    build_cumulative_registration_chart(data["weekly_regs"])

    municipality_summary = summarize_party_balance(
        data["municipality_stats"],
        "municipality",
    )

    precinct_summary = summarize_party_balance(
        data["precinct_stats"],
        "precinct_split_id",
    )

    state_house_summary = summarize_party_balance(
        data["state_house_stats"],
        "state_house",
    )

    state_senate_summary = summarize_party_balance(
        data["state_senate_stats"],
        "state_senate",
    )

    switch_summary = summarize_switchers(data["county_switchers"])

    index_path = build_index_html(
        {
            "municipality_summary": municipality_summary,
            "precinct_summary": precinct_summary,
            "state_house_summary": state_house_summary,
            "state_senate_summary": state_senate_summary,
            "switch_summary": switch_summary,
            "source_files": data["files"],
            "municipality_map": municipality_map,
            "precinct_map": precinct_map_view,
            "state_house_map": state_house_map,
            "state_senate_map": state_senate_map,
        }
    )

    print()
    print(f"Built dashboard: {index_path}")
    print("Open this file in your browser:")
    print(index_path)


if __name__ == "__main__":
    main()
