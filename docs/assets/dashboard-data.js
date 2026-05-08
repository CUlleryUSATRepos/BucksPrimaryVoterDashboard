window.DASHBOARD_DATA = {
  "statCards": {
    "totalGeosLabel": "Total municipalities",
    "totalGeos": "54",
    "totalVoters": "483,557",
    "competitiveCount": "5",
    "partySwitchers": "12,559"
  },
  "mapViews": {
    "municipality": {
      "buttonLabel": "Municipalities",
      "title": "Municipality registration map",
      "frame": "assets/municipality_map.html",
      "summary": "\n    <p>\n      This view includes <strong>483,557</strong>\n      voters across <strong>54</strong> municipalities.\n      There are <strong>15</strong> Democratic-leaning municipalities,\n      <strong>34</strong> Republican-leaning municipalities,\n      and <strong>5</strong> within 2.5 points.\n    </p>\n\n    <p>\n      The strongest Democratic margin is in <strong>Bristol borough</strong>\n      at <strong>32.0%</strong>.\n      The strongest Republican margin is in <strong>Nockamixon township</strong>\n      at <strong>30.0%</strong>.\n      The closest area is <strong>Doylestown township</strong>,\n      with a D-vs-R margin of <strong>-0.3%</strong>.\n    </p>\n    "
    },
    "precinct": {
      "buttonLabel": "Precincts",
      "title": "Precinct registration map",
      "frame": "assets/countywide_precinct_map.html",
      "summary": "\n    <p>\n      This view includes <strong>483,557</strong>\n      voters across <strong>304</strong> precincts.\n      There are <strong>124</strong> Democratic-leaning precincts,\n      <strong>148</strong> Republican-leaning precincts,\n      and <strong>32</strong> within 2.5 points.\n    </p>\n\n    <p>\n      The strongest Democratic margin is in <strong>Bristol township, precinct 05052-1</strong>\n      at <strong>46.1%</strong>.\n      The strongest Republican margin is in <strong>Nockamixon township, precinct 30020-1</strong>\n      at <strong>34.0%</strong>.\n      The closest area is <strong>Bristol township, precinct 05012-1</strong>,\n      with a D-vs-R margin of <strong>0.1%</strong>.\n    </p>\n    "
    },
    "house": {
      "buttonLabel": "State House",
      "title": "State House registration map",
      "frame": "assets/state_house_map.html",
      "summary": "\n    <p>\n      This view includes <strong>483,557</strong>\n      voters across <strong>10</strong> State House districts.\n      There are <strong>5</strong> Democratic-leaning State House districts,\n      <strong>5</strong> Republican-leaning State House districts,\n      and <strong>0</strong> within 2.5 points.\n    </p>\n\n    <p>\n      The strongest Democratic margin is in <strong>STH141</strong>\n      at <strong>17.2%</strong>.\n      The strongest Republican margin is in <strong>STH145</strong>\n      at <strong>18.6%</strong>.\n      The closest area is <strong>STH142</strong>,\n      with a D-vs-R margin of <strong>-2.9%</strong>.\n    </p>\n    "
    },
    "senate": {
      "buttonLabel": "State Senate",
      "title": "State Senate registration map",
      "frame": "assets/state_senate_map.html",
      "summary": "\n    <p>\n      This view includes <strong>483,557</strong>\n      voters across <strong>3</strong> State Senate districts.\n      There are <strong>1</strong> Democratic-leaning State Senate districts,\n      <strong>2</strong> Republican-leaning State Senate districts,\n      and <strong>0</strong> within 2.5 points.\n    </p>\n\n    <p>\n      The strongest Democratic margin is in <strong>STS10</strong>\n      at <strong>7.3%</strong>.\n      The strongest Republican margin is in <strong>STS16</strong>\n      at <strong>17.2%</strong>.\n      The closest area is <strong>STS06</strong>,\n      with a D-vs-R margin of <strong>-5.1%</strong>.\n    </p>\n    "
    }
  },
  "switcherSummaryHtml": "\n    <p>\n      The county file identifies <strong>12,559</strong>\n      voters whose current registration differs from the party they voted in during the 2024 general election.\n    </p>\n\n    <p>\n      Democrats had a net change of <strong>-890</strong>\n      after gaining <strong>3,934</strong> voters and losing\n      <strong>4,824</strong>.\n      Republicans had a net change of <strong>+858</strong>\n      after gaining <strong>4,413</strong> voters and losing\n      <strong>3,555</strong>.\n      Other or unaffiliated voters had a net change of\n      <strong>+32</strong>.\n    </p>\n\n    <p>\n      Direct party movement included\n      <strong>2,454</strong> Democratic-to-Republican switches,\n      <strong>1,713</strong> Republican-to-Democratic switches,\n      <strong>2,370</strong> Democratic-to-other switches,\n      <strong>1,842</strong> Republican-to-other switches,\n      <strong>2,221</strong> other-to-Democratic switches,\n      and <strong>1,959</strong> other-to-Republican switches.\n    </p>\n    ",
  "sourceFiles": {
    "precinct_map": "precinct_main_map.geojson",
    "municipality_stats": "municipality_party_counts_572026.csv",
    "precinct_stats": "precinct_split_party_counts_572026.csv",
    "weekly_regs": "county_registrations_weekly_572026.csv",
    "county_switchers": "county_party_switchers_enriched_572026.csv",
    "state_house_stats": "state_house_party_counts_572026.csv",
    "state_senate_stats": "state_senate_party_counts_572026.csv"
  }
};
