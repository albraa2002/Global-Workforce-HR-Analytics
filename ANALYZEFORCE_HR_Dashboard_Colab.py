# ============================================================
#  ANALYZEFORCE — Global Workforce Analytics Dashboard
#  Single-Cell Google Colab Script | Senior HR Data Analyst
# ============================================================

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from google.colab import files
import warnings
warnings.filterwarnings('ignore')

np.random.seed(42)

# ─────────────────────────────────────────────
# STEP 1: GENERATE REALISTIC HR DATA (5,000)
# ─────────────────────────────────────────────

N = 5000

first_names = [
    "James","Mary","John","Patricia","Robert","Jennifer","Michael","Linda",
    "William","Barbara","David","Elizabeth","Richard","Susan","Joseph","Jessica",
    "Thomas","Sarah","Charles","Karen","Christopher","Lisa","Daniel","Nancy",
    "Matthew","Betty","Anthony","Margaret","Mark","Sandra","Donald","Ashley",
    "Steven","Dorothy","Paul","Kimberly","Andrew","Emily","Kenneth","Donna",
    "Joshua","Michelle","Kevin","Carol","Brian","Amanda","George","Melissa",
    "Timothy","Deborah","Ravi","Priya","Arjun","Anjali","Vikram","Deepa",
    "Amir","Fatima","Omar","Nour","Hassan","Layla","Youssef","Mariam",
    "Mohammed","Sara","Ahmed","Hana","Tariq","Rania","Khalid","Dina",
    "Ethan","Olivia","Noah","Emma","Liam","Ava","Mason","Sophia",
    "Logan","Isabella","Lucas","Mia","Aiden","Charlotte","Jackson","Amelia"
]

last_names = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
    "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson",
    "Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson",
    "White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson",
    "Walker","Young","Allen","King","Wright","Scott","Torres","Nguyen",
    "Hill","Flores","Green","Adams","Nelson","Baker","Hall","Rivera",
    "Campbell","Mitchell","Carter","Roberts","Patel","Shah","Kumar","Singh",
    "Sharma","Gupta","Verma","Agarwal","Mehta","Joshi","Nair","Reddy",
    "Ahmed","Hassan","Ibrahim","Ali","Omar","Khalil","Farouk","Mansour",
    "Al-Rashid","Qureshi","Malik","Chaudhry","Ansari","Sheikh","Mirza","Khan"
]

emp_ids = [f"EMP{str(i+1).zfill(4)}" for i in range(N)]

names = [
    f"{np.random.choice(first_names)} {np.random.choice(last_names)}"
    for _ in range(N)
]

# ── Country distribution: India ~40%, rest split ──
country_probs = [0.20, 0.12, 0.40, 0.15, 0.13]   # USA, UK, India, Egypt, UAE
countries = ['USA', 'UK', 'India', 'Egypt', 'UAE']
country_arr = np.random.choice(countries, size=N, p=country_probs)

# ── Hire Date: massive spike in 2024 ──
# Year weights: 2018-2023 modest, 2024 huge spike, 2025 moderate
year_weights = {2018: 0.06, 2019: 0.07, 2020: 0.06, 2021: 0.08,
                2022: 0.09, 2023: 0.10, 2024: 0.38, 2025: 0.16}
years = list(year_weights.keys())
year_probs = list(year_weights.values())
hire_years = np.random.choice(years, size=N, p=year_probs)

hire_dates = []
for y in hire_years:
    month = np.random.randint(1, 13)
    max_day = 28 if month == 2 else (30 if month in [4,6,9,11] else 31)
    day = np.random.randint(1, max_day + 1)
    hire_dates.append(pd.Timestamp(year=int(y), month=month, day=day))
hire_dates = pd.Series(hire_dates)

# ── Status: 85% Active ──
status_arr = np.random.choice(['Active', 'Terminated'], size=N, p=[0.85, 0.15])

# ── Gender ──
gender_arr = np.random.choice(['Male', 'Female'], size=N, p=[0.52, 0.48])

# ── Salary with business logic ──
# Base salary by country (USA highest, Egypt lowest)
country_base = {
    'USA':   {'mean': 105000, 'std': 25000},
    'UK':    {'mean':  80000, 'std': 18000},
    'India': {'mean':  42000, 'std': 12000},
    'Egypt': {'mean':  28000, 'std':  8000},   # lowest avg
    'UAE':   {'mean':  72000, 'std': 20000},
}

# Gender pay gap: males ~8% higher
gender_multiplier = np.where(gender_arr == 'Male', 1.04, 0.96)

salaries = np.array([
    max(15000, np.random.normal(
        country_base[c]['mean'],
        country_base[c]['std']
    ) * gm)
    for c, gm in zip(country_arr, gender_multiplier)
], dtype=float)

# ── Attendance Rate ──
attendance = np.random.normal(loc=88, scale=7, size=N).clip(70, 100)

# ── Assemble DataFrame ──
df = pd.DataFrame({
    'Emp_ID':          emp_ids,
    'Name':            names,
    'Gender':          gender_arr,
    'Country':         country_arr,
    'Hire_Date':       hire_dates,
    'Salary_USD':      np.round(salaries, 2),
    'Status':          status_arr,
    'Attendance_Rate': np.round(attendance, 2),
})

# ── Inject "Alex Mercer" as Active employee with lowest attendance ──
alex_idx = 0
df.at[alex_idx, 'Emp_ID']          = 'EMP0001'
df.at[alex_idx, 'Name']            = 'Alex Mercer'
df.at[alex_idx, 'Gender']          = 'Male'
df.at[alex_idx, 'Country']         = 'USA'
df.at[alex_idx, 'Status']          = 'Active'
df.at[alex_idx, 'Attendance_Rate'] = 62.0   # abnormally low

# Ensure no other employee has attendance ≤ 62
mask_others = df.index != alex_idx
df.loc[mask_others & (df['Attendance_Rate'] <= 63), 'Attendance_Rate'] = \
    np.random.uniform(64, 72, size=(mask_others & (df['Attendance_Rate'] <= 63)).sum())

print(f"✅ Dataset generated: {len(df):,} employees")
print(df.head(3))

# ─────────────────────────────────────────────
# STEP 2: CALCULATE KPIs — 7 BUSINESS QUESTIONS
# ─────────────────────────────────────────────

active_df = df[df['Status'] == 'Active'].copy()

# Q1 — Active count & gender split
q1_active_count = len(active_df)
q1_male_pct     = round(len(active_df[active_df['Gender'] == 'Male']) / q1_active_count * 100, 1)
q1_female_pct   = round(100 - q1_male_pct, 1)

# Q2 — Country with highest headcount
country_counts    = df['Country'].value_counts()
q2_top_country    = country_counts.idxmax()
q2_top_pct        = round(country_counts.max() / N * 100, 1)

# Q3 — Year with highest YoY hiring growth
df['Hire_Year'] = df['Hire_Date'].dt.year
yearly_hires    = df.groupby('Hire_Year').size().sort_index()
yoy_growth      = yearly_hires.pct_change() * 100
q3_best_year    = int(yoy_growth.idxmax())
q3_best_growth  = round(yoy_growth.max(), 1)

# Q4 — Country with lowest avg salary vs company avg
country_avg_salary  = df.groupby('Country')['Salary_USD'].mean()
q4_lowest_country   = country_avg_salary.idxmin()
q4_lowest_avg       = round(country_avg_salary.min(), 0)
q4_company_avg      = round(df['Salary_USD'].mean(), 0)

# Q5 — Gender Pay Gap (Active employees)
male_avg    = active_df[active_df['Gender'] == 'Male']['Salary_USD'].mean()
female_avg  = active_df[active_df['Gender'] == 'Female']['Salary_USD'].mean()
q5_gap      = round(male_avg - female_avg, 0)
q5_male_avg = round(male_avg, 0)
q5_fem_avg  = round(female_avg, 0)

# Q6 — Employee with lowest attendance
q6_low_att_idx  = df['Attendance_Rate'].idxmin()
q6_low_att_name = df.at[q6_low_att_idx, 'Name']
q6_low_att_val  = df.at[q6_low_att_idx, 'Attendance_Rate']

# Q7 — Country with highest total payroll
country_payroll = df.groupby('Country')['Salary_USD'].sum()
q7_top_payroll_country = country_payroll.idxmax()
q7_top_payroll_val     = round(country_payroll.max() / 1e6, 2)

print("\n📊 KPI Summary:")
print(f"  Q1: {q1_active_count:,} active | {q1_male_pct}% M / {q1_female_pct}% F")
print(f"  Q2: {q2_top_country} — {q2_top_pct}% of workforce")
print(f"  Q3: {q3_best_year} — {q3_best_growth}% YoY growth")
print(f"  Q4: {q4_lowest_country} avg ${q4_lowest_avg:,} vs company avg ${q4_company_avg:,}")
print(f"  Q5: Pay gap = ${q5_gap:,}  (M: ${q5_male_avg:,} | F: ${q5_fem_avg:,})")
print(f"  Q6: {q6_low_att_name} — {q6_low_att_val}%")
print(f"  Q7: {q7_top_payroll_country} — ${q7_top_payroll_val}M total payroll")

# ─────────────────────────────────────────────
# STEP 3: PLOTLY FIGURES
# ─────────────────────────────────────────────

# Corporate Executive palette
NAVY    = '#1B2A4A'
SLATE   = '#4A5568'
GOLD    = '#C9A84C'
TEAL    = '#2ABFBF'
LIGHT   = '#F4F6F9'
WHITE   = '#FFFFFF'
RED_ACC = '#E05252'

bar_colors = [GOLD if yr == 2024 else NAVY for yr in yearly_hires.index]

# ── fig_hiring: Bar chart hires per year ──
fig_hiring = go.Figure(go.Bar(
    x=yearly_hires.index.astype(str),
    y=yearly_hires.values,
    marker_color=bar_colors,
    marker_line_color=WHITE,
    marker_line_width=1.5,
    text=yearly_hires.values,
    textposition='outside',
    textfont=dict(color=NAVY, size=12, family='Georgia, serif'),
))
fig_hiring.update_layout(
    title=dict(text='Annual Hiring Volume — 2018–2025', font=dict(size=16, color=NAVY, family='Georgia, serif'), x=0.5),
    xaxis=dict(title='Year', tickfont=dict(color=SLATE), gridcolor='rgba(0,0,0,0)'),
    yaxis=dict(title='Employees Hired', tickfont=dict(color=SLATE), gridcolor='rgba(74,85,104,0.15)'),
    plot_bgcolor=WHITE,
    paper_bgcolor=WHITE,
    margin=dict(t=60, b=50, l=60, r=30),
    annotations=[dict(
        x='2024', y=yearly_hires[2024] * 1.08,
        text='🚀 Peak Hiring Year',
        showarrow=False,
        font=dict(color=GOLD, size=12, family='Georgia, serif'),
    )],
    height=380,
)

# ── fig_payroll: Horizontal bar — Total Payroll by Country ──
payroll_sorted = country_payroll.sort_values()
payroll_colors = [GOLD if c == q7_top_payroll_country else TEAL for c in payroll_sorted.index]

fig_payroll = go.Figure(go.Bar(
    x=payroll_sorted.values / 1e6,
    y=payroll_sorted.index,
    orientation='h',
    marker_color=payroll_colors,
    marker_line_color=WHITE,
    marker_line_width=1.2,
    text=[f'${v/1e6:.1f}M' for v in payroll_sorted.values],
    textposition='outside',
    textfont=dict(color=NAVY, size=12, family='Georgia, serif'),
))
fig_payroll.update_layout(
    title=dict(text='Total Payroll Cost by Country (USD)', font=dict(size=16, color=NAVY, family='Georgia, serif'), x=0.5),
    xaxis=dict(title='Payroll (USD Millions)', tickfont=dict(color=SLATE), gridcolor='rgba(74,85,104,0.15)'),
    yaxis=dict(tickfont=dict(color=SLATE, size=13)),
    plot_bgcolor=WHITE,
    paper_bgcolor=WHITE,
    margin=dict(t=60, b=50, l=80, r=80),
    height=380,
)

# ── fig_salary: Box plot — Salary by Gender (Active only) ──
active_male   = active_df[active_df['Gender'] == 'Male']['Salary_USD']
active_female = active_df[active_df['Gender'] == 'Female']['Salary_USD']

fig_salary = go.Figure()
fig_salary.add_trace(go.Box(
    y=active_male,
    name='Male',
    marker_color=NAVY,
    line_color=NAVY,
    boxmean='sd',
    fillcolor='rgba(27,42,74,0.25)',
))
fig_salary.add_trace(go.Box(
    y=active_female,
    name='Female',
    marker_color=TEAL,
    line_color=TEAL,
    boxmean='sd',
    fillcolor='rgba(42,191,191,0.25)',
))
fig_salary.update_layout(
    title=dict(text='Salary Distribution by Gender — Active Employees', font=dict(size=16, color=NAVY, family='Georgia, serif'), x=0.5),
    yaxis=dict(title='Salary (USD)', tickfont=dict(color=SLATE), gridcolor='rgba(74,85,104,0.15)'),
    xaxis=dict(tickfont=dict(color=SLATE, size=13)),
    plot_bgcolor=WHITE,
    paper_bgcolor=WHITE,
    margin=dict(t=60, b=50, l=80, r=30),
    showlegend=False,
    height=380,
)

# ── fig_gender: Pie chart — Active Gender split ──
gender_counts = active_df['Gender'].value_counts()
fig_gender = go.Figure(go.Pie(
    labels=gender_counts.index,
    values=gender_counts.values,
    hole=0.45,
    marker=dict(colors=[NAVY, TEAL], line=dict(color=WHITE, width=2)),
    textinfo='label+percent',
    textfont=dict(size=13, family='Georgia, serif', color=WHITE),
    insidetextorientation='radial',
))
fig_gender.update_layout(
    title=dict(text='Active Workforce — Gender Split', font=dict(size=16, color=NAVY, family='Georgia, serif'), x=0.5),
    paper_bgcolor=WHITE,
    margin=dict(t=60, b=30, l=30, r=30),
    height=380,
    legend=dict(font=dict(color=SLATE)),
)

print("\n✅ All 4 Plotly figures created.")

# ─────────────────────────────────────────────
# STEP 4: BUILD PURE HTML/CSS DASHBOARD
# ─────────────────────────────────────────────

# Convert figures to HTML fragments
h_hiring  = fig_hiring.to_html(full_html=False, include_plotlyjs=False)
h_payroll = fig_payroll.to_html(full_html=False, include_plotlyjs=False)
h_salary  = fig_salary.to_html(full_html=False, include_plotlyjs=False)
h_gender  = fig_gender.to_html(full_html=False, include_plotlyjs=False)

html_dashboard = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>ANALYZEFORCE — Global Workforce Analytics Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Source+Sans+Pro:wght@300;400;600&display=swap" rel="stylesheet"/>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --navy:   #1B2A4A;
      --slate:  #4A5568;
      --gold:   #C9A84C;
      --teal:   #2ABFBF;
      --bg:     #F4F6F9;
      --white:  #FFFFFF;
      --danger: #E05252;
      --card-shadow: 0 4px 24px rgba(27,42,74,0.10);
    }}

    body {{
      font-family: 'Source Sans Pro', sans-serif;
      background: var(--bg);
      color: var(--navy);
      min-height: 100vh;
    }}

    /* ── HEADER ── */
    header {{
      background: linear-gradient(135deg, var(--navy) 0%, #2C3F6B 100%);
      padding: 28px 48px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 3px solid var(--gold);
    }}
    .header-brand {{
      display: flex;
      align-items: center;
      gap: 18px;
    }}
    .brand-logo {{
      width: 52px; height: 52px;
      background: var(--gold);
      border-radius: 10px;
      display: flex; align-items: center; justify-content: center;
      font-family: 'Playfair Display', serif;
      font-size: 22px; font-weight: 700;
      color: var(--navy);
    }}
    .brand-text h1 {{
      font-family: 'Playfair Display', serif;
      font-size: 26px; font-weight: 700;
      color: var(--white);
      letter-spacing: 0.5px;
    }}
    .brand-text span {{
      font-size: 13px; color: rgba(255,255,255,0.65);
      letter-spacing: 2px; text-transform: uppercase;
    }}
    .header-meta {{
      text-align: right;
    }}
    .header-meta p {{
      color: rgba(255,255,255,0.65);
      font-size: 12px; letter-spacing: 1.5px;
      text-transform: uppercase;
    }}
    .header-meta strong {{
      color: var(--gold);
      font-size: 14px;
    }}

    /* ── MAIN WRAPPER ── */
    .dashboard-wrap {{
      max-width: 1440px;
      margin: 0 auto;
      padding: 36px 40px 56px;
    }}

    /* ── SECTION TITLES ── */
    .section-title {{
      font-family: 'Playfair Display', serif;
      font-size: 20px; font-weight: 600;
      color: var(--navy);
      margin-bottom: 20px;
      padding-bottom: 10px;
      border-bottom: 2px solid var(--gold);
      display: flex; align-items: center; gap: 10px;
    }}
    .section-title .icon {{
      font-size: 22px;
    }}

    /* ── EXECUTIVE SUMMARY CARD ── */
    .exec-summary {{
      background: var(--white);
      border-radius: 14px;
      box-shadow: var(--card-shadow);
      padding: 32px 36px;
      margin-bottom: 32px;
      border-top: 4px solid var(--gold);
    }}

    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
      gap: 18px;
      margin-top: 8px;
    }}

    .kpi-card {{
      background: linear-gradient(145deg, #F7F9FC 0%, #EEF1F7 100%);
      border-radius: 10px;
      padding: 20px 22px;
      border-left: 4px solid var(--teal);
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .kpi-card:hover {{
      transform: translateY(-3px);
      box-shadow: 0 8px 24px rgba(27,42,74,0.13);
    }}
    .kpi-card.highlight {{
      border-left-color: var(--gold);
    }}
    .kpi-card.alert {{
      border-left-color: var(--danger);
    }}

    .kpi-label {{
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 1.8px;
      color: var(--slate);
      margin-bottom: 8px;
      font-weight: 600;
    }}
    .kpi-question {{
      font-size: 13px;
      color: var(--slate);
      margin-bottom: 10px;
      font-style: italic;
    }}
    .kpi-answer {{
      font-family: 'Playfair Display', serif;
      font-size: 20px;
      font-weight: 700;
      color: var(--navy);
      line-height: 1.3;
    }}
    .kpi-answer .accent {{
      color: var(--gold);
    }}
    .kpi-answer .teal-acc {{
      color: var(--teal);
    }}
    .kpi-answer .red-acc {{
      color: var(--danger);
    }}
    .kpi-sub {{
      font-size: 12px;
      color: var(--slate);
      margin-top: 6px;
    }}

    /* ── CHART GRID ── */
    .chart-row {{
      display: grid;
      gap: 24px;
      margin-bottom: 28px;
    }}
    .chart-row.two-col {{
      grid-template-columns: 1fr 1fr;
    }}
    .chart-card {{
      background: var(--white);
      border-radius: 14px;
      box-shadow: var(--card-shadow);
      padding: 24px 20px 16px;
      overflow: hidden;
    }}

    /* ── FOOTER ── */
    footer {{
      background: var(--navy);
      color: rgba(255,255,255,0.5);
      text-align: center;
      padding: 18px;
      font-size: 12px;
      letter-spacing: 1px;
      margin-top: 12px;
    }}
    footer span {{ color: var(--gold); }}

    /* ── RESPONSIVE ── */
    @media (max-width: 900px) {{
      .chart-row.two-col {{ grid-template-columns: 1fr; }}
      header {{ flex-direction: column; gap: 16px; text-align: center; }}
      .dashboard-wrap {{ padding: 20px 16px 40px; }}
    }}
  </style>
</head>
<body>

  <!-- ── HEADER ── -->
  <header>
    <div class="header-brand">
      <div class="brand-logo">AF</div>
      <div class="brand-text">
        <h1>ANALYZEFORCE</h1>
        <span>Global Workforce Analytics Dashboard</span>
      </div>
    </div>
    <div class="header-meta">
      <p>Reporting Period</p>
      <strong>Jan 2018 — Dec 2025</strong>
      <p style="margin-top:6px;">Total Workforce</p>
      <strong>{N:,} Employees</strong>
    </div>
  </header>

  <!-- ── MAIN ── -->
  <div class="dashboard-wrap">

    <!-- EXECUTIVE SUMMARY -->
    <section class="exec-summary">
      <div class="section-title">
        <span class="icon">📋</span>
        Executive Summary: Business Questions Answered
      </div>

      <div class="kpi-grid">

        <!-- Q1 -->
        <div class="kpi-card highlight">
          <div class="kpi-label">Q1 — Active Workforce</div>
          <div class="kpi-question">How many employees are active, and what is the gender breakdown?</div>
          <div class="kpi-answer"><span class="accent">{q1_active_count:,}</span> Active Employees</div>
          <div class="kpi-sub">♂ Male: <strong>{q1_male_pct}%</strong> &nbsp;|&nbsp; ♀ Female: <strong>{q1_female_pct}%</strong></div>
        </div>

        <!-- Q2 -->
        <div class="kpi-card">
          <div class="kpi-label">Q2 — Highest Headcount Country</div>
          <div class="kpi-question">Which country has the largest share of the workforce?</div>
          <div class="kpi-answer"><span class="teal-acc">{q2_top_country}</span></div>
          <div class="kpi-sub">Represents <strong>{q2_top_pct}%</strong> of total workforce ({country_counts[q2_top_country]:,} employees)</div>
        </div>

        <!-- Q3 -->
        <div class="kpi-card highlight">
          <div class="kpi-label">Q3 — Peak Hiring Year</div>
          <div class="kpi-question">Which year recorded the highest YoY hiring growth?</div>
          <div class="kpi-answer"><span class="accent">{q3_best_year}</span></div>
          <div class="kpi-sub">YoY Growth: <strong>+{q3_best_growth}%</strong> ({yearly_hires[q3_best_year]:,} new hires)</div>
        </div>

        <!-- Q4 -->
        <div class="kpi-card">
          <div class="kpi-label">Q4 — Lowest Avg Salary Country</div>
          <div class="kpi-question">Which country has the lowest average salary vs. company average?</div>
          <div class="kpi-answer"><span class="teal-acc">{q4_lowest_country}</span> — <span style="font-size:17px;">${q4_lowest_avg:,.0f}</span></div>
          <div class="kpi-sub">Company Average: <strong>${q4_company_avg:,.0f}</strong> &nbsp;(Gap: ${q4_company_avg - q4_lowest_avg:,.0f})</div>
        </div>

        <!-- Q5 -->
        <div class="kpi-card highlight">
          <div class="kpi-label">Q5 — Gender Pay Gap</div>
          <div class="kpi-question">What is the salary gap between active Male and Female employees?</div>
          <div class="kpi-answer">Gap: <span class="accent">${q5_gap:,.0f}</span></div>
          <div class="kpi-sub">♂ Male Avg: <strong>${q5_male_avg:,.0f}</strong> &nbsp;|&nbsp; ♀ Female Avg: <strong>${q5_fem_avg:,.0f}</strong></div>
        </div>

        <!-- Q6 -->
        <div class="kpi-card alert">
          <div class="kpi-label">Q6 — Lowest Attendance ⚠</div>
          <div class="kpi-question">Which active employee has the lowest attendance rate?</div>
          <div class="kpi-answer"><span class="red-acc">{q6_low_att_name}</span></div>
          <div class="kpi-sub">Attendance Rate: <strong style="color:var(--danger);">{q6_low_att_val}%</strong> — Requires HR Review</div>
        </div>

        <!-- Q7 -->
        <div class="kpi-card">
          <div class="kpi-label">Q7 — Highest Total Payroll</div>
          <div class="kpi-question">Which country drives the highest total payroll cost?</div>
          <div class="kpi-answer"><span class="teal-acc">{q7_top_payroll_country}</span> — <span style="font-size:17px;">${q7_top_payroll_val}M</span></div>
          <div class="kpi-sub">Despite fewer employees than India, USA leads in total compensation spend</div>
        </div>

      </div>
    </section>

    <!-- ROW 2: Hiring Trend + Gender Pie -->
    <div class="chart-row two-col">
      <div class="chart-card">
        {h_hiring}
      </div>
      <div class="chart-card">
        {h_gender}
      </div>
    </div>

    <!-- ROW 3: Payroll + Salary Box -->
    <div class="chart-row two-col">
      <div class="chart-card">
        {h_payroll}
      </div>
      <div class="chart-card">
        {h_salary}
      </div>
    </div>

  </div>

  <!-- ── FOOTER ── -->
  <footer>
    &copy; 2025 <span>ANALYZEFORCE</span> &nbsp;|&nbsp; Global Workforce Analytics Division
    &nbsp;|&nbsp; Confidential — For Executive Use Only
  </footer>

</body>
</html>"""

# ─────────────────────────────────────────────
# STEP 5: EXPORT & AUTO-DOWNLOAD
# ─────────────────────────────────────────────

output_filename = 'ANALYZEFORCE_HR_Dashboard.html'

with open(output_filename, 'w', encoding='utf-8') as f:
    f.write(html_dashboard)

print(f"\n✅ Dashboard saved as '{output_filename}'")
print("⬇️  Triggering auto-download...")

files.download(output_filename)

print("\n🎉 ANALYZEFORCE Dashboard — Complete! Check your Downloads folder.")
