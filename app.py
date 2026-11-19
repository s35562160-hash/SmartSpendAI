import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from google import genai

# ---------------- PAGE SETTINGS ----------------

st.set_page_config(
    page_title="SmartSpend AI",
    page_icon="💜",
    layout="wide"
)

# ---------------- COLOUR THEME ----------------

st.markdown("""
<style>

/* Main background and default text */
.stApp {
    background-color: #F5EFFF;
    color: #241536;
}

/* Headings and normal text */
h1, h2, h3, h4, h5, h6,
p, label, span, li,
.stMarkdown, [data-testid="stMarkdownContainer"] {
    color: #241536 !important;
}

/* Widget labels */
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label {
    color: #241536 !important;
    font-weight: 600 !important;
}

/* Text boxes and number inputs */
input, textarea {
    background-color: #FFFFFF !important;
    color: #241536 !important;
    -webkit-text-fill-color: #241536 !important;
    border: 1px solid #9870C5 !important;
    border-radius: 8px !important;
}

/* Placeholder text */
input::placeholder,
textarea::placeholder {
    color: #756583 !important;
    -webkit-text-fill-color: #756583 !important;
    opacity: 1 !important;
}

/* Date input */
div[data-testid="stDateInput"] input {
    background-color: #FFFFFF !important;
    color: #241536 !important;
    -webkit-text-fill-color: #241536 !important;
}

/* Dropdown boxes */
div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    border: 1px solid #9870C5 !important;
}

div[data-baseweb="select"] span,
div[data-baseweb="select"] input {
    color: #241536 !important;
    -webkit-text-fill-color: #241536 !important;
}

/* Dropdown options */
ul[role="listbox"] {
    background-color: #FFFFFF !important;
}

li[role="option"] {
    color: #241536 !important;
}

/* Calendar */
div[data-baseweb="calendar"] {
    background-color: #FFFFFF !important;
    color: #241536 !important;
}

div[data-baseweb="calendar"] button {
    color: #241536 !important;
}

/* Buttons */
.stButton button,
.stDownloadButton button,
.stFormSubmitButton button {
    background-color: #7040A0 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: bold !important;
    padding: 10px 16px !important;
}

.stButton button p,
.stDownloadButton button p,
.stFormSubmitButton button p {
    color: #FFFFFF !important;
}

.stButton button:hover,
.stDownloadButton button:hover,
.stFormSubmitButton button:hover {
    background-color: #512875 !important;
}

/* Alerts */
div[data-testid="stAlert"] {
    background-color: #E9DDF8 !important;
    border: 1px solid #9870C5 !important;
}

div[data-testid="stAlert"] p,
div[data-testid="stAlert"] div {
    color: #241536 !important;
}

/* Dashboard metric cards */
div[data-testid="stMetric"] {
    background-color: #FFFFFF !important;
    padding: 16px !important;
    border-radius: 12px !important;
    border: 1px solid #D7C2EF !important;
}

div[data-testid="stMetric"] label,
div[data-testid="stMetric"] [data-testid="stMetricValue"],
div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    color: #241536 !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #E9DDF8 !important;
}

section[data-testid="stSidebar"] * {
    color: #241536 !important;
}

/* Data table */
div[data-testid="stDataFrame"] {
    color: #241536 !important;
}

/* Expander */
details {
    background-color: #FFFFFF !important;
    border-radius: 10px !important;
}

/* Footer */
.footer {
    text-align: center;
    color: #512875 !important;
    font-weight: bold;
    padding: 15px;
}

</style>
""", unsafe_allow_html=True)


# ---------------- GEMINI AI FUNCTION ----------------

def analyze_expenses_with_gemini(expense_data):

    api_key = st.secrets.get("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "Gemini API key not found. Check your .streamlit/secrets.toml file."
        )

    client = genai.Client(api_key=api_key)

    total = expense_data["Amount"].sum()

    category_totals = (
        expense_data.groupby("Category")["Amount"]
        .sum()
        .sort_values(ascending=False)
    )

    expense_details = expense_data.to_string(index=False)

    prompt = f"""
You are SmartSpend AI, a helpful personal finance assistant.

Analyse the following expense records:

{expense_details}

TOTAL EXPENSES: Rs. {total:.2f}

CATEGORY-WISE TOTALS:
{category_totals.to_string()}

Prepare a clear financial analysis containing:

1. Total spending summary.
2. Highest spending category.
3. Spending patterns.
4. Categories where spending can be reduced.
5. Five practical money-saving suggestions.
6. A simple monthly saving plan.

Use Indian Rupees.
Use clear headings and bullet points.
Do not invent expenses or income information.
Keep the recommendations practical and beginner-friendly.
"""

    interaction = client.interactions.create(
        model="gemini-3.8-flash",
        input=prompt
    )

    result = interaction.output_text

    if not result:
        raise ValueError("Gemini returned an empty response.")

    return result


# ---------------- APPLICATION HEADER ----------------

st.title("💜 SmartSpend AI")
st.subheader("Your Personal AI Expense Analyzer")

st.write(
    "Track your expenses, understand your spending habits "
    "and manage your monthly budget intelligently."
)

st.divider()


# ---------------- SESSION STATE ----------------

if "expenses" not in st.session_state:
    st.session_state.expenses = []

if "ai_analysis" not in st.session_state:
    st.session_state.ai_analysis = None


# ---------------- ADD EXPENSE ----------------

st.header("➕ Add New Expense")

with st.form("expense_form"):

    expense_date = st.date_input(
        "Expense Date",
        value=date.today()
    )

    category = st.selectbox(
        "Category",
        [
            "Food",
            "Shopping",
            "Transportation",
            "Entertainment",
            "Education",
            "Health",
            "Other"
        ]
    )

    description = st.text_input(
        "Description",
        placeholder="Enter expense details"
    )

    amount = st.number_input(
        "Amount (₹)",
        min_value=0.0,
        step=10.0,
        format="%.2f"
    )

    submitted = st.form_submit_button("Add Expense 💜")

    if submitted:

        if amount <= 0:
            st.error("Please enter an amount greater than zero.")

        else:
            new_expense = {
                "Date": expense_date,
                "Category": category,
                "Description": description,
                "Amount": amount
            }

            st.session_state.expenses.append(new_expense)
            st.session_state.ai_analysis = None

            st.success("Expense added successfully! 💜")


st.divider()


# ---------------- EXPENSE DASHBOARD ----------------

st.header("📊 Expense Dashboard")

if len(st.session_state.expenses) == 0:

    st.markdown("""
    <div style="
        background-color:#512875;
        color:#FFFFFF;
        padding:22px;
        border-radius:12px;
        text-align:center;
        font-size:18px;
        font-weight:bold;
        border:2px solid #35164F;">
        No expenses added yet.<br>
        Add your first expense above! 💜
    </div>
    """, unsafe_allow_html=True)

else:

    df = pd.DataFrame(st.session_state.expenses)

    total_expenses = df["Amount"].sum()

    category_totals = df.groupby("Category")["Amount"].sum()

    highest_category = category_totals.idxmax()

    highest_amount = category_totals.max()

    # Dashboard metrics
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Expenses",
        f"₹{total_expenses:,.2f}"
    )

    col2.metric(
        "Number of Expenses",
        len(df)
    )

    col3.metric(
        "Highest Spending",
        highest_category
    )

    st.divider()

    # Expense table
    st.subheader("🧾 Your Expense Details")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    # Pie chart
    st.subheader("📈 Spending by Category")

    category_data = (
        df.groupby("Category", as_index=False)["Amount"].sum()
    )

    fig = px.pie(
        category_data,
        names="Category",
        values="Amount",
        title="Expense Distribution",
        hole=0.4
    )

    fig.update_layout(
        paper_bgcolor="#F5EFFF",
        plot_bgcolor="#F5EFFF",
        font_color="#241536",
        title_font_color="#241536",
        legend_font_color="#241536"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # Spending insights
    st.subheader("💡 Spending Insights")

    st.write(
        f"Your total spending is ₹{total_expenses:,.2f}."
    )

    st.write(
        f"Your highest expense category is {highest_category}, "
        f"with ₹{highest_amount:,.2f}."
    )

    st.write("**Saving suggestion:**")

    if highest_category == "Food":
        st.write(
            "Try planning meals and reducing unnecessary food orders."
        )

    elif highest_category == "Shopping":
        st.write(
            "Make a shopping list and avoid unnecessary purchases."
        )

    elif highest_category == "Transportation":
        st.write(
            "Consider public transport or sharing rides."
        )

    elif highest_category == "Entertainment":
        st.write(
            "Set a monthly entertainment budget."
        )

    else:
        st.write(
            "Review your spending regularly and set a monthly budget."
        )

    st.divider()

    # Gemini AI analysis
    st.subheader("✨ AI-Powered Expense Analysis")

    if st.button("Analyse My Expenses with Gemini AI 🤖"):

        try:

            with st.spinner(
                "Gemini AI is analysing your expenses..."
            ):

                st.session_state.ai_analysis = (
                    analyze_expenses_with_gemini(df)
                )

            st.success(
                "AI Analysis completed successfully! 💜"
            )

        except Exception as e:

            st.error(f"AI Analysis failed: {e}")

    if st.session_state.ai_analysis:

        st.markdown("### 🤖 Gemini AI Recommendations")

        st.markdown(
            st.session_state.ai_analysis
        )

    st.divider()

    # Download expenses
    st.subheader("📥 Download Your Expenses")

    csv_data = df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Expense Report",
        data=csv_data,
        file_name="SmartSpend_Expenses.csv",
        mime="text/csv"
    )

    # Delete last expense
    if st.button("Delete Last Expense"):

        st.session_state.expenses.pop()

        st.session_state.ai_analysis = None

        st.rerun()


# ---------------- FOOTER ----------------

st.divider()

st.markdown("""
<div class="footer">
Made with 💜 | SmartSpend AI
</div>
""", unsafe_allow_html=True)
