import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Set page config
st.set_page_config(
    page_title="NBFC Lending Business Calculator",
    page_icon="💰",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #2E8B57, #4169E1);
    padding: 20px;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 20px;
}
.metric-container {
    background-color: #f0f2f6;
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid #2E8B57;
    margin: 5px 0;
}
.calculation-header {
    background-color: #e1f5fe;
    padding: 10px;
    border-radius: 5px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# Title
st.markdown("""
<div class="main-header">
    <h1>💰 NBFC Lending Business Calculator</h1>
</div>
""", unsafe_allow_html=True)

# Sidebar for all inputs
st.sidebar.markdown("# 🎛️ Input Business Parameters")

# Number of months selection at the top
st.sidebar.markdown("## 📅 Projection Period")
num_months = st.sidebar.number_input("Number of Months", min_value=1, max_value=48, value=12, step=1)

# Capital Deployment Parameters
st.sidebar.markdown("## 💰 Capital Deployment (₹ Crores)")

# Create dynamic capital inputs based on number of months
capital_values = []
if num_months <= 12:
    # Two columns for 12 or fewer months
    cap_col1, cap_col2 = st.sidebar.columns(2)
    for i in range(num_months):
        month_num = i + 1
        if month_num <= 5:
            default_val = [5.0, 4.0, 4.0, 4.0, 3.0][i] if month_num <= 5 else 0.0
        else:
            default_val = 0.0
            
        if i % 2 == 0:
            with cap_col1:
                val = st.number_input(f"Month {month_num}", min_value=0.0, max_value=20.0, value=default_val, step=0.5, key=f"cap_{month_num}")
        else:
            with cap_col2:
                val = st.number_input(f"Month {month_num}", min_value=0.0, max_value=20.0, value=default_val, step=0.5, key=f"cap_{month_num}")
        capital_values.append(val)
else:
    # Single column for more than 12 months
    for i in range(num_months):
        month_num = i + 1
        if month_num <= 5:
            default_val = [5.0, 4.0, 4.0, 4.0, 3.0][i]
        else:
            default_val = 0.0
        val = st.sidebar.number_input(f"Month {month_num}", min_value=0.0, max_value=20.0, value=default_val, step=0.5, key=f"cap_{month_num}")
        capital_values.append(val)

# Create individual variables for backward compatibility
for i in range(48):  # Create all possible month variables
    if i < len(capital_values):
        globals()[f"month{i+1}_capital"] = capital_values[i]
    else:
        globals()[f"month{i+1}_capital"] = 0.0

total_capital = sum(capital_values)

# Business Parameters
st.sidebar.markdown("## 📈 Revenue Parameters")
processing_fees = st.sidebar.number_input("Processing Fees (%)", min_value=5.0, max_value=25.0, value=11.8, step=0.1) / 100
monthly_interest_rate = st.sidebar.number_input("Monthly Interest Rate (%)", min_value=15.0, max_value=50.0, value=30.0, step=0.5) / 100
marketing_rate = st.sidebar.number_input("Marketing Expenses (%)", min_value=1.0, max_value=5.0, value=2.0, step=0.1) / 100
cost_of_funds_rate = st.sidebar.number_input("Cost of Funds (% monthly)", min_value=0.5, max_value=5.0, value=1.5, step=0.1) / 100

# Operational expense rates
st.sidebar.markdown("## 🏢 Operational Expenses (%)")
opex_month1_value = st.sidebar.number_input("Month 1 OpEx (₹)", 1000000, 5000000, 1500000, 50000)
opex_month1 = opex_month1_value / 1e7  # Convert to crores for consistency

# Create dynamic OPEX inputs based on number of months (starting from month 2)
opex_values = [opex_month1]  # Month 1 is already handled above
for i in range(1, num_months):  # Start from month 2
    month_num = i + 1
    if month_num <= 3:
        default_val = 10.0
    elif month_num <= 5:
        default_val = 5.0
    else:
        default_val = 4.0
    val = st.sidebar.number_input(f"Month {month_num} OpEx Rate (%)", min_value=0.0, max_value=30.0, value=default_val, step=0.5, key=f"opex_{month_num}") / 100
    opex_values.append(val)

# Create individual variables for backward compatibility
for i in range(48):  # Create all possible month variables
    if i < len(opex_values):
        globals()[f"opex_month{i+1}"] = opex_values[i]
    else:
        globals()[f"opex_month{i+1}"] = 0.04  # Default 4%

# Loan parameters
st.sidebar.markdown("## 🎯 Loan Parameters")
avg_ticket_size = st.sidebar.number_input("Average Loan Ticket (₹)", 10000, 50000, 22000, 1000)

# Collection parameters
st.sidebar.markdown("## 📊 Collection Parameters")
t0_collection = st.sidebar.number_input("T+0 Collection Rate (%)", min_value=0, max_value=100, value=80, step=1) / 100
t30_collection = st.sidebar.number_input("T+30 Collection Rate (%)", min_value=0, max_value=100, value=5, step=1) / 100
t60_collection = st.sidebar.number_input("T+60 Collection Rate (%)", min_value=0, max_value=100, value=5, step=1) / 100
t90_collection = st.sidebar.number_input("T+90 Collection Rate (%)", min_value=0, max_value=100, value=3, step=1) / 100

# Validation for collection rates
total_collection_rate_percent = (t0_collection + t30_collection + t60_collection + t90_collection) * 100
if total_collection_rate_percent > 100:
    st.sidebar.error(f"⚠️ Total collection rate is {total_collection_rate_percent:.1f}% - should not exceed 100%")
else:
    st.sidebar.success(f"✅ Total collection rate: {total_collection_rate_percent:.1f}%")

# API costs
api_cost_80_percent = st.sidebar.number_input("API Cost (Per Lead Not Converted) ₹", 20, 100, 35, 5)
api_cost_20_percent = st.sidebar.number_input("API Cost (Per Converted Customers) ₹", 50, 150, 95, 5)

# Fixed costs
st.sidebar.markdown("## 💳 Monthly Principal Return (₹ Crores)")

# Create dynamic principal return inputs based on number of months
principal_values = []
if num_months <= 12:
    # Two columns for 12 or fewer months
    prin_col1, prin_col2 = st.sidebar.columns(2)
    for i in range(num_months):
        month_num = i + 1
        if i % 2 == 0:
            with prin_col1:
                val = st.number_input(f"Month {month_num} PR", min_value=0.0, value=0.0, step=0.1, key=f"prin_{month_num}")
        else:
            with prin_col2:
                val = st.number_input(f"Month {month_num} PR", min_value=0.0, value=0.0, step=0.1, key=f"prin_{month_num}")
        principal_values.append(val)
else:
    # Single column for more than 12 months
    for i in range(num_months):
        month_num = i + 1
        val = st.sidebar.number_input(f"Month {month_num} PR", min_value=0.0, value=0.0, step=0.1, key=f"prin_{month_num}")
        principal_values.append(val)

# Create individual variables for backward compatibility
for i in range(48):  # Create all possible month variables
    if i < len(principal_values):
        globals()[f"month{i+1}_principal"] = principal_values[i]
    else:
        globals()[f"month{i+1}_principal"] = 0.0

# EXACT calculation function using your formulas
def calculate_with_exact_formulas():
    months = num_months  # Use dynamic number of months
    
    # Capital deployment schedule - use actual number of months
    capital_invested = [capital_values[i] * 1e7 if i < len(capital_values) else 0 for i in range(months)]
    
    # OPEX rates array - use actual number of months
    opex_rates = [opex_values[i] if i < len(opex_values) else 0.04 for i in range(months)]
    
    # Principal return array - use actual number of months (convert from crores to rupees)
    principal_returns = [principal_values[i] * 1e7 if i < len(principal_values) else 0 for i in range(months)]
    
    # Initialize arrays to store all calculations
    amount_invested = []
    amount_available = []
    amount_disbursed = []
    customers = []
    opex = []
    api_expense = []
    marketing_expense = []
    cost_of_funds = []
    bad_debt_default = []
    gst = []
    salary = []
    principal_return = []
    interest_revenue = []
    bad_debt_recovery = []
    processing_fees_revenue = []
    profit_loss = []
    aum = []
    
    for month in range(months):
        # Amount Invested
        amount_invested.append(capital_invested[month])
        
        # Amount Available for Disbursal
        if month == 0:
            available = capital_invested[month]
        else:
            prev_profit = profit_loss[month-1]
            available = amount_available[month-1] + prev_profit + capital_invested[month]
        
        amount_available.append(available)
        
        # Amount Actually Disbursed = Amount Available / (1 - Processing Fees)
        disbursed = available / (1 - processing_fees)
        amount_disbursed.append(disbursed)
        
        # Number of Customers
        num_customers = int(disbursed / avg_ticket_size)
        customers.append(num_customers)
        
        # Operational Expenses
        if month == 0:
            op_expense = opex_month1_value  # Use editable value for month 1
        else:
            prev_aum = aum[month-1]
            op_expense = prev_aum * opex_rates[month]
        
        opex.append(op_expense)
        
        # API Cost
        api_cost = (num_customers * 2 * api_cost_20_percent) + (num_customers * 8 * api_cost_80_percent)
        api_expense.append(api_cost)
        
        # Marketing Expense
        marketing_exp = disbursed * marketing_rate
        marketing_expense.append(marketing_exp)
        
        # Cost of Funds (quarterly calculation - adapted for variable months)
        cost_of_funds_expense = 0
        # Calculate cost of funds for quarters that are complete within the selected months
        if month == 2 and months >= 3:  # Month 3 (Q1) - if we have at least 3 months
            cost_q1_m1 = capital_invested[0] * cost_of_funds_rate
            cost_q1_m2 = sum(capital_invested[:2]) * cost_of_funds_rate  
            cost_q1_m3 = sum(capital_invested[:3]) * cost_of_funds_rate
            cost_of_funds_expense = cost_q1_m1 + cost_q1_m2 + cost_q1_m3
        elif month == 5 and months >= 6:  # Month 6 (Q2) - if we have at least 6 months
            cost_q2_m4 = sum(capital_invested[:4]) * cost_of_funds_rate
            cost_q2_m5 = sum(capital_invested[:5]) * cost_of_funds_rate
            cost_q2_m6 = sum(capital_invested[:6]) * cost_of_funds_rate
            cost_of_funds_expense = cost_q2_m4 + cost_q2_m5 + cost_q2_m6
        elif month == 8 and months >= 9:  # Month 9 (Q3) - if we have at least 9 months
            cost_q3_m7 = sum(capital_invested[:7]) * cost_of_funds_rate
            cost_q3_m8 = sum(capital_invested[:8]) * cost_of_funds_rate
            cost_q3_m9 = sum(capital_invested[:9]) * cost_of_funds_rate
            cost_of_funds_expense = cost_q3_m7 + cost_q3_m8 + cost_q3_m9
        elif month == 11 and months >= 12:  # Month 12 (Q4) - if we have at least 12 months
            cost_q4_m10 = sum(capital_invested[:10]) * cost_of_funds_rate
            cost_q4_m11 = sum(capital_invested[:11]) * cost_of_funds_rate
            cost_q4_m12 = sum(capital_invested[:12]) * cost_of_funds_rate
            cost_of_funds_expense = cost_q4_m10 + cost_q4_m11 + cost_q4_m12
        # Add additional quarters for periods longer than 12 months
        elif month == 14 and months >= 15:  # Month 15 (Q5)
            cost_q5_m13 = sum(capital_invested[:13]) * cost_of_funds_rate
            cost_q5_m14 = sum(capital_invested[:14]) * cost_of_funds_rate
            cost_q5_m15 = sum(capital_invested[:15]) * cost_of_funds_rate
            cost_of_funds_expense = cost_q5_m13 + cost_q5_m14 + cost_q5_m15
        elif month == 17 and months >= 18:  # Month 18 (Q6)
            cost_q6_m16 = sum(capital_invested[:16]) * cost_of_funds_rate
            cost_q6_m17 = sum(capital_invested[:17]) * cost_of_funds_rate
            cost_q6_m18 = sum(capital_invested[:18]) * cost_of_funds_rate
            cost_of_funds_expense = cost_q6_m16 + cost_q6_m17 + cost_q6_m18
        # Continue pattern for longer periods - every 3rd month starting from month 3
        elif (month + 1) % 3 == 0 and month >= 2 and months > month:  # General quarterly calculation
            quarter_start = month - 2
            cost_q_m1 = sum(capital_invested[:quarter_start+1]) * cost_of_funds_rate
            cost_q_m2 = sum(capital_invested[:quarter_start+2]) * cost_of_funds_rate
            cost_q_m3 = sum(capital_invested[:quarter_start+3]) * cost_of_funds_rate
            cost_of_funds_expense = cost_q_m1 + cost_q_m2 + cost_q_m3
        
        cost_of_funds.append(cost_of_funds_expense)
        
        # Interest calculation (split across two months)
        if month == 0:
            interest = (disbursed * monthly_interest_rate) / 2
        else:
            current_month_interest = (disbursed * monthly_interest_rate) / 2
            prev_month_interest = (amount_disbursed[month-1] * monthly_interest_rate) / 2
            interest = current_month_interest + prev_month_interest
        
        interest_revenue.append(interest)
        
        # Bad Debt Default = (Amount Disbursed + Interest) × (1 - T+0 Collection Rate)
        bad_debt = (disbursed + interest) * (1 - t0_collection)
        bad_debt_default.append(bad_debt)
        
        # Recovery of Bad Debt
        recovery = 0
        if month >= 1:
            prev_disbursed_plus_interest = amount_disbursed[month-1] + interest_revenue[month-1]
            recovery += prev_disbursed_plus_interest * t30_collection
        if month >= 2:
            prev2_disbursed_plus_interest = amount_disbursed[month-2] + interest_revenue[month-2]
            recovery += prev2_disbursed_plus_interest * t60_collection
        if month >= 3:
            prev3_disbursed_plus_interest = amount_disbursed[month-3] + interest_revenue[month-3]
            recovery += prev3_disbursed_plus_interest * t90_collection
        
        bad_debt_recovery.append(recovery)
        
        # Processing Fees
        pf = disbursed * processing_fees
        processing_fees_revenue.append(pf)
        
        # GST
        gst_amount = pf * (18/118)
        gst.append(gst_amount)
        
        # Fixed costs
        monthly_salary = 0  # Fixed at 0 since removed from inputs
        salary.append(monthly_salary)
        principal_return.append(principal_returns[month])
        
        # Profit/Loss
        profit = (interest + recovery + pf) - (op_expense + api_cost + marketing_exp + cost_of_funds_expense + bad_debt + gst_amount + monthly_salary + principal_returns[month])
        profit_loss.append(profit)
        
        # AUM = Amount Actually Disbursed + Interest
        aum_value = disbursed + interest
        aum.append(aum_value)
    
    # Create DataFrame with dynamic number of months
    df = pd.DataFrame({
        'month': range(1, months + 1),
        'amount_invested': [x/1e7 for x in amount_invested],
        'amount_available': [x/1e7 for x in amount_available],
        'amount_disbursed': [x/1e7 for x in amount_disbursed],
        'customers': customers,
        'opex': [x/1e7 for x in opex],
        'api_expense': [x/1e7 for x in api_expense],
        'marketing_expense': [x/1e7 for x in marketing_expense],
        'cost_of_funds': [x/1e7 for x in cost_of_funds],
        'bad_debt_default': [x/1e7 for x in bad_debt_default],
        'gst': [x/1e7 for x in gst],
        'salary': [x/1e7 for x in salary],
        'principal_return': [x/1e7 for x in principal_return],
        'interest_revenue': [x/1e7 for x in interest_revenue],
        'bad_debt_recovery': [x/1e7 for x in bad_debt_recovery],
        'processing_fees_revenue': [x/1e7 for x in processing_fees_revenue],
        'profit_loss': [x/1e7 for x in profit_loss],
        'aum': [x/1e7 for x in aum]
    })
    
    return df

# Calculate derived metrics
# Time-weighted investment calculation for variable months
sum_annual_investment = 0
for i, capital in enumerate(capital_values):
    months_remaining = num_months - i
    weight = months_remaining / num_months
    sum_annual_investment += capital * weight

# Calculate projections first to get final month values
df = calculate_with_exact_formulas()

# Calculate Actual Period ROI (not annualized)
final_month_aum = df['aum'].iloc[-1]
if sum_annual_investment > 0:
    period_roi = ((final_month_aum - sum_annual_investment) / sum_annual_investment) * 100
else:
    period_roi = 0

# Display key metrics
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("💰 Capital Invested", f"₹{total_capital:.1f} Cr")
    
with col2:
    st.metric("📈 Period ROI", f"{period_roi:.1f}%")
    
with col3:
    final_month_disbursed = df['amount_disbursed'].iloc[-1]
    st.metric(f"📊 Month {num_months} Disbursed", f"₹{final_month_disbursed:.2f} Cr")
    
with col4:
    final_month_profit = df['profit_loss'].iloc[-1]
    st.metric(f"🎯 Month {num_months} Profit", f"₹{final_month_profit:.2f} Cr")
    
with col5:
    final_month_aum = df['aum'].iloc[-1]
    st.metric(f"🏆 Month {num_months} AUM", f"₹{final_month_aum:.2f} Cr")

# Charts
st.markdown("---")
st.markdown("## 📈 Business Analysis Charts")

# Row 1: AUM Chart and Monthly Revenue vs Cost Analysis (side by side)
col1, col2 = st.columns(2)

with col1:
    # 1. AUM Growth Analysis
    fig_aum_growth = px.area(
        df,
        x='month',
        y='aum',
        title="Assets Under Management (AUM) Growth",
        color_discrete_sequence=['#4169E1']
    )
    fig_aum_growth.update_layout(
        xaxis_title="Month",
        yaxis_title="AUM (₹ Crores)",
        height=400
    )
    fig_aum_growth.update_xaxes(dtick=1)  # Show every month
    fig_aum_growth.update_traces(hovertemplate='Month %{x}<br>AUM: ₹%{y:.2f} Cr<extra></extra>')
    st.plotly_chart(fig_aum_growth, use_container_width=True)

with col2:
    # 2. Revenue vs Costs
    fig_revenue_costs = go.Figure()

    # Calculate revenue and costs
    total_revenue = df['interest_revenue'] + df['processing_fees_revenue'] + df['bad_debt_recovery']
    total_costs = (df['opex'] + df['api_expense'] + df['marketing_expense'] + 
                   df['cost_of_funds'] + df['bad_debt_default'] + df['gst'] + 
                   df['salary'] + df['principal_return'])

    fig_revenue_costs.add_trace(go.Bar(
        x=df['month'],
        y=total_revenue,
        name='Total Revenue',
        marker_color='#2E8B57',
        hovertemplate='Month %{x}<br>Revenue: ₹%{y:.2f} Cr<extra></extra>'
    ))

    fig_revenue_costs.add_trace(go.Bar(
        x=df['month'],
        y=total_costs,
        name='Total Costs',
        marker_color='#FF6B6B',
        hovertemplate='Month %{x}<br>Costs: ₹%{y:.2f} Cr<extra></extra>'
    ))

    fig_revenue_costs.add_trace(go.Scatter(
        x=df['month'],
        y=df['profit_loss'],
        mode='lines+markers',
        name='Net Profit',
        line=dict(color='#FFD700', width=4),
        marker=dict(size=10),
        hovertemplate='Month %{x}<br>Profit: ₹%{y:.2f} Cr<extra></extra>'
    ))

    fig_revenue_costs.update_layout(
        title="Monthly Revenue vs Costs Analysis",
        xaxis_title="Month",
        yaxis_title="Amount (₹ Crores)",
        hovermode='x unified',
        height=400
    )
    fig_revenue_costs.update_xaxes(dtick=1)  # Show every month

    st.plotly_chart(fig_revenue_costs, use_container_width=True)

# Row 2: Monthly Profit/Loss Analysis (full width)
# 3. Profit/Loss Analysis
fig_profit = px.bar(
    df,
    x='month',
    y='profit_loss',
    title="Monthly Profit/Loss Analysis",
    color='profit_loss',
    color_continuous_scale=['red', 'yellow', 'green']
)
fig_profit.update_layout(
    xaxis_title="Month",
    yaxis_title="Profit/Loss (₹ Crores)",
    height=400,
    showlegend=False
)
fig_profit.update_xaxes(dtick=1)  # Show every month
fig_profit.update_traces(hovertemplate='Month %{x}<br>Profit/Loss: ₹%{y:.2f} Cr<extra></extra>')
st.plotly_chart(fig_profit, use_container_width=True)

# Row 3: Amount Invested vs Available and Amount Disbursed (side by side)
col1, col2 = st.columns(2)

with col1:
    # 4. Amount Invested vs Available for Disbursal - Both as bars
    fig_invested_vs_available = go.Figure()

    fig_invested_vs_available.add_trace(go.Bar(
        x=df['month'],
        y=df['amount_invested'],
        name='Amount Invested',
        marker_color='#4169E1',
        hovertemplate='Month %{x}<br>Invested: ₹%{y:.2f} Cr<extra></extra>'
    ))

    fig_invested_vs_available.add_trace(go.Bar(
        x=df['month'],
        y=df['amount_available'],
        name='Available for Disbursal',
        marker_color='#2E8B57',
        hovertemplate='Month %{x}<br>Available: ₹%{y:.2f} Cr<extra></extra>'
    ))

    fig_invested_vs_available.update_layout(
        title="Amount Invested vs Available for Disbursal",
        xaxis_title="Month",
        yaxis_title="Amount (₹ Crores)",
        hovermode='x unified',
        height=400,
        barmode='group'
    )
    fig_invested_vs_available.update_xaxes(dtick=1)  # Show every month

    st.plotly_chart(fig_invested_vs_available, use_container_width=True)

with col2:
    # 5. Amount Actually Disbursed vs Month
    fig_disbursed = px.line(
        df,
        x='month',
        y='amount_disbursed',
        title="Amount Actually Disbursed",
        markers=True,
        color_discrete_sequence=['#2E8B57']
    )
    fig_disbursed.update_layout(
        xaxis_title="Month",
        yaxis_title="Amount Disbursed (₹ Crores)",
        height=400
    )
    fig_disbursed.update_xaxes(dtick=1)  # Show every month
    fig_disbursed.update_traces(hovertemplate='Month %{x}<br>Disbursed: ₹%{y:.2f} Cr<extra></extra>')
    st.plotly_chart(fig_disbursed, use_container_width=True)

# Row 4: Revenue Breakdown and Customer Acquisition (side by side)
col1, col2 = st.columns(2)

with col1:
    # 6. Revenue Breakdown
    fig_revenue_breakdown = go.Figure()

    fig_revenue_breakdown.add_trace(go.Bar(
        x=df['month'],
        y=df['interest_revenue'],
        name='Interest Revenue',
        marker_color='#2E8B57',
        hovertemplate='Month %{x}<br>Interest: ₹%{y:.2f} Cr<extra></extra>'
    ))

    fig_revenue_breakdown.add_trace(go.Bar(
        x=df['month'],
        y=df['processing_fees_revenue'],
        name='Processing Fees',
        marker_color='#4169E1',
        hovertemplate='Month %{x}<br>Processing Fees: ₹%{y:.2f} Cr<extra></extra>'
    ))

    fig_revenue_breakdown.add_trace(go.Bar(
        x=df['month'],
        y=df['bad_debt_recovery'],
        name='Bad Debt Recovery',
        marker_color='#FF8C00',
        hovertemplate='Month %{x}<br>Recovery: ₹%{y:.2f} Cr<extra></extra>'
    ))

    fig_revenue_breakdown.update_layout(
        title="Monthly Revenue Breakdown",
        xaxis_title="Month",
        yaxis_title="Amount (₹ Crores)",
        barmode='stack',
        height=400
    )
    fig_revenue_breakdown.update_xaxes(dtick=1)  # Show every month

    st.plotly_chart(fig_revenue_breakdown, use_container_width=True)

with col2:
    # 7. Customer Acquisition
    fig_customers = px.bar(
        df,
        x='month',
        y='customers',
        title="Monthly Customer Acquisition",
        color='customers',
        color_continuous_scale='viridis'
    )
    fig_customers.update_layout(
        xaxis_title="Month",
        yaxis_title="Number of Customers",
        height=400,
        showlegend=False
    )
    fig_customers.update_xaxes(dtick=1)  # Show every month
    fig_customers.update_traces(hovertemplate='Month %{x}<br>Customers: %{y:,.0f}<extra></extra>')
    st.plotly_chart(fig_customers, use_container_width=True)

# Complete calculations table
st.markdown("---")
st.markdown("## 📋 Complete Monthly Calculations")

# Round for display
display_df = df.round(3)

# Rename columns for better readability and remove salary
column_names = {
    'month': 'Month',
    'amount_invested': 'Invested (₹Cr)',
    'amount_available': 'Available (₹Cr)',
    'amount_disbursed': 'Disbursed (₹Cr)',
    'customers': 'Customers',
    'opex': 'OpEx (₹Cr)',
    'api_expense': 'API (₹Cr)',
    'marketing_expense': 'Marketing (₹Cr)',
    'cost_of_funds': 'Cost of Funds (₹Cr)',
    'bad_debt_default': 'Bad Debt (₹Cr)',
    'gst': 'GST (₹Cr)',
    'interest_revenue': 'Interest (₹Cr)',
    'bad_debt_recovery': 'Recovery (₹Cr)',
    'processing_fees_revenue': 'PF (₹Cr)',
    'principal_return': 'Principal Return (₹Cr)',
    'profit_loss': 'Profit (₹Cr)',
    'aum': 'AUM (₹Cr)'
}

# Remove salary column and rename
display_df = display_df.drop('salary', axis=1)
display_df = display_df.rename(columns=column_names)
st.dataframe(display_df, use_container_width=True, hide_index=True, height=400)

# Summary and export
st.markdown("---")
st.markdown("## 📊 Financial Summary")

st.markdown(f"### 💰 {num_months}-Month Summary")
total_revenue_sum = total_revenue.sum()
total_costs_sum = total_costs.sum()
net_profit_sum = df['profit_loss'].sum()
final_aum = df['aum'].iloc[-1]
final_month_available = df['amount_available'].iloc[-1]
total_customers_sum = df['customers'].sum()
final_month_aum_summary = df['aum'].iloc[-1]

st.write(f"**Capital Invested:** ₹{total_capital:.2f} Cr")
st.write(f"**Month {num_months} Available for Disbursal:** ₹{final_month_available:.2f} Cr")
st.write(f"**Month {num_months} AUM:** ₹{final_month_aum_summary:.2f} Cr")
st.write(f"**Total Profit/Loss ({num_months} months):** ₹{net_profit_sum:.2f} Cr")
st.write(f"**Total Customers:** {total_customers_sum:,}")
st.write(f"**Total Revenue:** ₹{total_revenue_sum:.2f} Cr")
st.write(f"**Total Costs:** ₹{total_costs_sum:.2f} Cr")
#st.write(f"**Profit Margin:** {(net_profit_sum/total_revenue_sum*100):.1f}%")