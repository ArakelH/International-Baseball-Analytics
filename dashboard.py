"""Interactive MLB birth-country data-quality and batting analysis dashboard.

Launch from repository root: python -m streamlit run dashboard.py
"""
from __future__ import annotations

from pathlib import Path

import plotly.express as px
import streamlit as st

from src.dashboard_data import RATE_METRICS, country_summary, filter_seasons, read_outputs, yearly_summary

ROOT = Path(__file__).resolve().parent
OUTPUTS = ROOT / 'outputs'

st.set_page_config(page_title='International Baseball | Analytics', page_icon='⚾', layout='wide')
st.markdown('''
<style>
.block-container {padding-top: 2rem; max-width: 1250px;}
[data-testid="stMetric"] {background:#12213a; border:1px solid #293d5e; border-radius:12px; padding:15px;}
[data-testid="stMetricLabel"] {color:#bccbe0;}
</style>
''', unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_data():
    return read_outputs(OUTPUTS)

st.title('⚾ International-Born MLB Hitters')
st.caption('Historical player-season exploration  |  2015–2025  |  SABR Lahman data')
st.info('**Purpose:** A transparent data-analysis portfolio demo, not an international prospect ranking or a scouting model.')

try:
    data, quality = load_data()
except (FileNotFoundError, ValueError) as exc:
    st.error(str(exc))
    st.code('python -m src.pipeline --download\npython -m streamlit run dashboard.py', language='bash')
    st.stop()

available_countries = sorted(data['birth_country'].dropna().unique().tolist())
year_min, year_max = int(data['year'].min()), int(data['year'].max())

with st.sidebar:
    st.header('Explore the data')
    st.caption('All filters apply to the headline metrics, plots and table.')
    countries = st.multiselect('Birth-country codes', available_countries, default=available_countries)
    years = st.slider('MLB seasons', min_value=year_min, max_value=year_max,
                      value=(year_min, year_max), step=1)
    search = st.text_input('Player name or player ID', placeholder='e.g. Ohtani')
    metric = st.selectbox('Rate statistic', options=list(RATE_METRICS),
                          format_func=lambda m: RATE_METRICS[m])
    top_n = st.slider('Countries in bar chart', 5, 20, 10)
    st.divider()
    st.caption('Sample rule: at least 200 estimated plate appearances (PA proxy) per hitter-season. '
               'Birth country is not nationality or international signing status.')

filtered = filter_seasons(data, countries, years, search)
if filtered.empty:
    st.warning('No player-seasons match these filters. Try selecting more countries or clearing the search.')
    st.stop()

m1,m2,m3,m4=st.columns(4)
m1.metric('Hitter-seasons', f'{len(filtered):,}')
m2.metric('Unique players', f'{filtered.player_id.nunique():,}')
m3.metric('Birth countries', f'{filtered.birth_country.nunique():,}')
m4.metric(f'Mean player-season {RATE_METRICS[metric]}',
          f'{filtered[metric].mean():.3f}' if filtered[metric].notna().any() else 'N/A')
st.caption('Each player contributes one record per qualifying season. Mean rates are unweighted averages of those records, not pooled batting rates.')

country = country_summary(filtered, metric)
yearly = yearly_summary(filtered, metric)
left, right = st.columns([1.12, 1])
with left:
    st.subheader('Where do qualifying hitter-seasons come from?')
    subset = country.head(top_n).sort_values('hitter_seasons')
    fig = px.bar(subset, x='hitter_seasons', y='birth_country', orientation='h',
                 hover_data={'unique_players': True, 'mean_rate': ':.3f'},
                 labels={'hitter_seasons':'Hitter-seasons', 'birth_country':'Birth-country code',
                         'mean_rate':f'Mean {RATE_METRICS[metric]}'},
                 color_discrete_sequence=['#3c83e6'])
    fig.update_layout(height=410, margin=dict(l=0,r=10,t=15,b=0))
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader(f'Performance over time: mean {RATE_METRICS[metric]}')
    trend = px.line(yearly, x='year', y='mean_rate', markers=True,
                    labels={'year':'Season', 'mean_rate':f'Mean player-season {RATE_METRICS[metric]}'},
                    color_discrete_sequence=['#36a894'])
    trend.update_xaxes(dtick=1)
    trend.update_layout(height=410, margin=dict(l=0,r=10,t=15,b=0))
    st.plotly_chart(trend, use_container_width=True)

st.subheader('Compare individual hitter-seasons')
scatter_rows=filtered.dropna(subset=['ops', 'pa_proxy']).copy()
if scatter_rows.empty:
    st.info('No OPS values are available for the current selection.')
else:
    scatter=px.scatter(scatter_rows, x='pa_proxy', y='ops', color='birth_country',
                       hover_name='player_name', hover_data=['year','ab','h','hr','bb'],
                       labels={'pa_proxy':'Estimated plate appearances', 'ops':'OPS',
                               'birth_country':'Birth country'}, opacity=0.76)
    scatter.update_layout(height=440, margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(scatter, use_container_width=True)

st.subheader('Explore and export records')
columns=['year','player_name','birth_country','pa_proxy','ab','h','hr','bb','obp','slg','ops','player_id']
records=filtered[columns].sort_values(['year','player_name'], ascending=[False,True])
st.dataframe(records, use_container_width=True, hide_index=True,
             column_config={
                 'player_name':'Player', 'birth_country':'Birth country',
                 'pa_proxy':'PA proxy', 'player_id':'Player ID',
                 'obp':st.column_config.NumberColumn('OBP', format='%.3f'),
                 'slg':st.column_config.NumberColumn('SLG', format='%.3f'),
                 'ops':st.column_config.NumberColumn('OPS', format='%.3f')
             })
st.download_button('Download filtered player-seasons (CSV)',
                   records.to_csv(index=False).encode('utf-8'),
                   file_name='filtered_player_seasons.csv', mime='text/csv')

with st.expander('Data-quality report and important limitations'):
    c1,c2=st.columns(2)
    with c1:
        st.write('**Source:**', quality.get('source','SABR Lahman'))
        st.write('**Seasons:**', quality.get('period','2015–2025'))
        st.write('**Source player records:**', f"{quality.get('people_rows',0):,}")
        st.write('**Batting lines in period:**', f"{quality.get('batting_lines_in_period',0):,}")
    with c2:
        st.write('**Batting lines without player match:**', quality.get('batting_lines_without_people','N/A'))
        st.write('**Missing birth country in full People table:**', quality.get('players_with_missing_birth_country','N/A'))
        st.write('**Original qualifying hitter-seasons:**', quality.get('qualifying_player_seasons','N/A'))
        st.write('**Birth countries in qualifying sample:**', quality.get('countries_in_qualified_sample','N/A'))
    st.markdown('''
- A hitter-season is one player in one season. It is **not** a distinct player across the full period.
- **PA proxy = AB + BB + HBP + SF + SH** and is not an official play-by-play PA measure.
- **OPS = OBP + SLG**. Rate statistics were rounded to three decimals by the source pipeline.
- **Mean OPS/OBP/SLG** is the simple average across filtered player-seasons, not a PA-weighted metric.
- Birth country is **not** citizenship, scouting territory, nationality, or eligibility under MLB international signing rules. Puerto Rico is not an international amateur market under the same rules as the Dominican Republic.
- The sample consists of MLB survivors. It cannot measure international prospect success rates or identify the best scouting regions.
- Metrics are not park-adjusted or league-adjusted; filters may create very small samples.
''')

st.caption('Source: SABR Lahman Baseball Database (2025 release). Independent educational portfolio project; not affiliated with MLB or the Dodgers.')
