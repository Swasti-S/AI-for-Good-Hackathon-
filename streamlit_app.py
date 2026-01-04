from typing import Any, Dict, List, Optional

import json
import os
import pandas as pd
import streamlit as st

import _snowflake
from snowflake.snowpark.context import get_active_session

DATABASE = "AI_FOR_GOOD"
SCHEMA = "AI_HOME_INSPECTION"
SEMANTIC_VIEW = "AI_FOR_GOOD.AI_HOME_INSPECTION.AI_HOME_INSPECTION"

API_ENDPOINT = "/api/v2/cortex/analyst/message"
API_TIMEOUT = 50000  # ms

IMAGE_FOLDER = "Images"
IMAGE_COLUMN_NAME = "IMAGE_NAME"
CORTEX_MODEL = "claude-3-5-sonnet"

# Color Theme
PRIMARY_COLOR = "#1B3B6F"
ACCENT_COLOR = "#E6241A"

session = get_active_session()

def apply_custom_css():
    """Apply custom CSS for hackathon-ready UI."""
    st.markdown("""
    <style>
        /* Main container styling */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Header styling */
        .main-header {
            background: linear-gradient(135deg, #1B3B6F 0%, #2d5aa0 100%);
            padding: 1rem 2rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 15px rgba(27, 59, 111, 0.3);
        }
        
        .main-header h1 {
            color: #e8f4fd !important;
            margin: 0 !important;
            font-size: 2.5rem !important;
        }
        
        .main-header p {
            color: #D3D3D3 !important;
            margin: 0.5rem 0 0 0 !important;
            font-size: 0.8rem !important;
        }
        
        /* Metric card styling */
        .metric-card {
            /*background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);*/
            border-radius: 12px;
            padding: 1.2rem;
            border-left: 4px solid #1B3B6F;
            border-top: 4px solid #1B3B6F;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 1rem;
            transition: transform 0.2s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }
        
        .metric-card .metric-label {
            color: #666;
            font-size: 0.85rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .metric-card .metric-value {
            /*color: #1B3B6F;*/
            font-size: 1.8rem;
            font-weight: 700;
            margin: 0.3rem 0;
        }
        
        
        /* Insight card styling */
        .insight-card {
            background: linear-gradient(135deg, #f0f7ff 0%, #e8f4fd 100%);
            border-radius: 12px;
            padding: 1rem;
            border: 1px solid #cce5ff;
            margin: 1rem 0;
        }
        
        .insight-card h3 {
            color: #1B3B6F;
            margin-top: 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        /* Image gallery styling */
        .image-gallery-header {
            background: linear-gradient(135deg, #f0f7ff 0%, #e8f4fd 100%);
            border-radius: 12px;
            padding: 1rem;
            margin: 1rem 0;
            border: 1px solid #cce5ff;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1B3B6F 0%, #0d1f3c 100%);
        }
        
        [data-testid="stSidebar"] .stMarkdown {
            color: white;
        }
        
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3 {
            color: white !important;
        }
        
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] li {
            color: rgba(255,255,255,0.85) !important;
        }
        
        /* Chat message styling */
        [data-testid="stChatMessage"] {
            border-radius: 12px;
            margin-bottom: 1rem;
        }
        
        /* Button styling */
        .stButton > button {
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            font-weight: 600;
            color: #1B3B6F;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
            padding: 0.5rem 1rem;
        }
        
        /* DataFrame styling */
        .stDataFrame {
            border-radius: 8px;
            overflow: hidden;
        }
        
        /* Footer styling */
        .app-footer {
            text-align: center;
            padding: 1rem;
            color: #666;
            font-size: 0.85rem;
            border-top: 1px solid #eee;
            margin-top: 2rem;
        }
        
        /* Result summary card */
        .result-summary {
            background: #f8fafc;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            border: 1px solid #e2e8f0;
        }
    </style>
    """, unsafe_allow_html=True)

def get_risk_colors(value: str) -> dict:
    """
    Return color scheme based on risk level value.
    High -> Red, Medium -> Amber, Low -> Green
    """
    value_lower = str(value).lower().strip()
    
    # HIGH RISK - Red colors
    if value_lower in ['high']:
        return {
            "bg": "linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)",
            "border": "#dc2626",
            "text": "#dc2626"
        }
    # MEDIUM RISK - Amber/Orange colors
    elif value_lower in ['medium']:
        return {
            "bg": "linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)",
            "border": "#d97706",
            "text": "#d97706"
        }
    # LOW RISK - Green colors
    elif value_lower in ['low']:
        return {
            "bg": "linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)",
            "border": "#059669",
            "text": "#059669"
        }
    # DEFAULT - Blue colors
    else:
        return {
            "bg": "linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)",
            "border": "#1B3B6F",
            "text": "#1B3B6F"
        }


def is_risk_column(col_name: str) -> bool:
    """Check if column name suggests it contains risk/severity category values."""
    col_lower = col_name.lower()
    risk_keywords = ['risk', 'category']
    return any(keyword in col_lower for keyword in risk_keywords)


def create_metric_card(label: str, value: str , colors: dict=None) -> str:
    """Create a styled metric card HTML with dynamic colors."""
    if colors is None:
            colors = {
                "bg": "linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)",
                "border": "#1B3B6F",
                "text": "#1B3B6F"
            }
        
    return f"""
        <div class="metric-card" style="background: {colors['bg']}; border-left-color: {colors['border']}; border-top-color: {colors['border']};">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color: {colors['text']};">{value}</div>
        </div>
        """

def display_single_value_metrics(df: pd.DataFrame):
    """Display single row results as attractive metric cards."""
    num_cols = min(len(df.columns), 4)
    cols = st.columns(num_cols)
    
    for idx, col_name in enumerate(df.columns):
        value = df[col_name].iloc[0]
        with cols[idx % num_cols]:
            # Format value based on type
            if pd.api.types.is_numeric_dtype(df[col_name]):
                if isinstance(value, float):
                    display_value = f"{value:,.2f}"
                else:
                    display_value = f"{value:,}"
            else:
                display_value = str(value)[:50]  # Truncate long strings
            
            colors = None
            if is_risk_column(col_name):
                # Get colors based on the VALUE (High/Medium/Low)
                colors = get_risk_colors(str(value))
            
            st.markdown(create_metric_card(
                col_name.replace('_', ' ').title(),
                display_value,colors
            ), unsafe_allow_html=True)


def should_show_charts(df: pd.DataFrame) -> dict:
    """
    Intelligently determine if charts should be shown based on data characteristics.
    Returns a dict with chart recommendations.
    """
    recommendations = {
        "show_bar": False,
        "show_line": False,
        "reason": ""
    }
    
    num_rows = len(df)
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    non_numeric_cols = df.select_dtypes(exclude=['number']).columns.tolist()
    
    # Don't show charts for single value results
    if num_rows == 1 and len(numeric_cols) <= 2:
        recommendations["reason"] = "Single value result - displayed as metric card"
        return recommendations
    
    # Don't show charts if no numeric data
    if len(numeric_cols) == 0:
        recommendations["reason"] = "No numeric data for visualization"
        return recommendations
    
    # Don't show charts for image-only results
    if IMAGE_COLUMN_NAME.upper() in [c.upper() for c in df.columns] and len(df.columns) <= 3:
        recommendations["reason"] = "Image gallery result"
        return recommendations
    
    # Show bar chart for categorical comparisons (reasonable number of rows with categories)
    if 1 < num_rows <= 20 and len(non_numeric_cols) >= 1:
        recommendations["show_bar"] = True
    
    # Show line chart for time series or many data points
    if num_rows > 5:
        first_col = df.columns[0].lower()
        time_indicators = ['date', 'time', 'month', 'year', 'day', 'week', 'quarter']
        if any(indicator in first_col for indicator in time_indicators):
            recommendations["show_line"] = True
        elif num_rows > 15:
            recommendations["show_line"] = True
    
    return recommendations


def generate_data_insights(df: pd.DataFrame, user_question: str) -> str:
    """Generate natural language insights using Cortex LLM."""
    try:
        max_rows = 50
        if len(df) > max_rows:
            data_string = df.head(max_rows).to_string(index=False)
            data_note = f"(Showing first {max_rows} of {len(df)} rows)"
        else:
            data_string = df.to_string(index=False)
            data_note = f"(Total: {len(df)} rows)"
        
        prompt = f"""You are a data analyst assistant for a home inspection system. 
Analyze the following query results and provide a clear, concise summary with key insights.

User Question: {user_question}

Data Results {data_note}:
{data_string}

Please provide:
1. A direct answer to the user's question
2. Key findings or patterns (if applicable)
3. Any notable observations or concerns for property inspections

Keep the response concise, professional, and actionable. Format with markdown for readability."""

        escaped_prompt = prompt.replace("'", "''")
        
        sql_query = f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE(
                '{CORTEX_MODEL}',
                '{escaped_prompt}'
            ) AS insight
        """
        
        result = session.sql(sql_query).collect()
        
        if result and len(result) > 0:
            return result[0]["INSIGHT"]
        else:
            return "Unable to generate insights at this time."
            
    except Exception as e:
        return f"Error generating insights: {str(e)}"


def get_image_column(df: pd.DataFrame) -> Optional[str]:
    """Get the IMAGE_NAME column if it exists."""
    for col in df.columns:
        if col.upper() == IMAGE_COLUMN_NAME.upper():
            return col
    return None


def display_images_from_dataframe(df: pd.DataFrame) -> bool:
    """Display images in an attractive gallery layout."""
    image_column = get_image_column(df)
    
    if not image_column:
        return False
    
    images_to_display = []
    
    for _, row in df.iterrows():
        image_name = row.get(image_column)
        if pd.notna(image_name) and image_name:
            image_path = os.path.join(IMAGE_FOLDER, str(image_name))
            
            caption_parts = []
            for col in df.columns:
                if col != image_column and pd.notna(row.get(col)):
                    caption_parts.append(f"**{col.replace('_', ' ').title()}:** {row[col]}")
            
            images_to_display.append({
                "path": image_path,
                "name": str(image_name),
                "caption": " | ".join(caption_parts) if caption_parts else str(image_name)
            })
    
    if not images_to_display:
        return False
    
    # Gallery header
    st.markdown(f"""
    <div class="image-gallery-header">
        <h3 style="margin:0; color:#1B3B6F;"> 📷 Visual Evidence</h3>
    </div>
    """, unsafe_allow_html=True)
    
 
    # Display in grid
    cols = st.columns(3)
    
    for idx, img_data in enumerate(images_to_display):
        with cols[idx % 3]:
            if os.path.exists(img_data["path"]):
                st.image(
                    img_data["path"],
                    caption=img_data["caption"],
                    use_container_width=True
                )
            else:
                st.warning(f"Image not found: {img_data['name']}")
    
    return True

def send_message(prompt: str) -> Dict[str, Any]:
    """Send message to Cortex Analyst API."""
    payload = {
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": prompt}]}
        ],
        "semantic_view": SEMANTIC_VIEW,
    }

    response = _snowflake.send_snow_api_request(
        "POST",
        API_ENDPOINT,
        {},
        {},
        payload,
        None,
        API_TIMEOUT,
    )

    parsed = json.loads(response["content"])
    parsed["request_id"] = parsed.get("request_id", None)

    return parsed


def process_message(prompt: str) -> None:
    """Process user message and display response."""
    st.session_state.current_question = prompt
    
    st.session_state.messages.append(
        {"role": "user", "content": [{"type": "text", "text": prompt}]}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing your question..."):
            response = send_message(prompt)
            request_id = response.get("request_id")
            raw_message = response.get("message")

            if isinstance(raw_message, dict):
                content = raw_message.get("content", [])
            elif isinstance(raw_message, str):
                content = [{"type": "text", "text": raw_message}]
            else:
                content = []

            display_content(content, request_id=request_id)

    st.session_state.messages.append(
        {"role": "assistant", "content": content, "request_id": request_id}
    )


def display_content(
    content: List[Dict[str, str]],
    request_id: Optional[str] = None,
    message_index: Optional[int] = None,
) -> None:
    """Display response content with enhanced UI."""
    
    message_index = message_index or len(st.session_state.messages)

    for item in content:
        item_type = item.get("type", "")

        # Text output
        if item_type == "text":
            st.markdown(item.get("text", ""))

        # Suggestions
        elif item_type == "suggestions":
            st.markdown("**💡 Suggested questions:**")
            for i, suggestion in enumerate(item.get("suggestions", [])):
                if st.button(
                    f"  {suggestion}",
                    key=f"sugg_{message_index}_{i}",
                    use_container_width=True
                ):
                    st.session_state.active_suggestion = suggestion

        # SQL Results
        elif item_type == "sql":
            sql_query = item.get("statement", "")

            with st.spinner("Executing query..."):
                try:
                    df = session.sql(sql_query).to_pandas()
                except Exception as e:
                    st.error(f"Query Error: {str(e)}")
                    return

                if df.empty:
                    st.info("No data found for your query.")
                    return

                num_rows = len(df)
                chart_recs = should_show_charts(df)
                
                # Single value result - show as metrics
                if num_rows == 1:
                    st.markdown("""
                        <div class="insight-card">
                            <h3>📋 Query Results</h4>
                        </div>
                        """, unsafe_allow_html=True)
                    #st.markdown("### 📋 Query Results")
                    display_single_value_metrics(df)
                    
                    # Also show raw data in expander
                    with st.expander("View Raw Data", expanded=False):
                        st.dataframe(df, use_container_width=True)
                
                # Multiple rows - show table and optional charts
                else:
                    # Build tab list dynamically
                    tab_names = ["📋 Data"]
                    if chart_recs["show_bar"]:
                        tab_names.append("📊 Bar Chart")
                    if chart_recs["show_line"]:
                        tab_names.append("📈 Line Chart")
                    
                    if len(tab_names) == 1:
                        # Only data tab needed
                        st.markdown("""
                            <div class="insight-card">
                                <h3>📋 Query Results</h4>
                            </div>
                            """, unsafe_allow_html=True)
                        #st.markdown("### 📋 Query Results")
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.markdown("""
                                <div class="insight-card">
                                    <h3>📋 Query Results</h4>
                                </div>
                                """, unsafe_allow_html=True)
                        tabs = st.tabs(tab_names)
                        
                        with tabs[0]:  # Data tab
                            st.dataframe(df, use_container_width=True)
                        
                        # Chart data
                        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                        non_numeric_cols = df.select_dtypes(exclude=['number']).columns.tolist()
                        
                        if numeric_cols:
                            try:
                                if non_numeric_cols:
                                    index_col = non_numeric_cols[0]
                                    chart_df = df.set_index(index_col)[numeric_cols]
                                else:
                                    chart_df = df[numeric_cols].copy()
                                    chart_df.index = [f"Item {i+1}" for i in range(len(chart_df))]
                                
                                tab_idx = 1
                                if chart_recs["show_bar"] and tab_idx < len(tabs):
                                    with tabs[tab_idx]:
                                        st.bar_chart(chart_df)
                                    tab_idx += 1
                                
                                if chart_recs["show_line"] and tab_idx < len(tabs):
                                    with tabs[tab_idx]:
                                        st.line_chart(chart_df)
                            except Exception as chart_error:
                                st.caption(f"Chart unavailable: {chart_error}")

                # AI Summary

                user_question = st.session_state.get("current_question", "Analyze this data")
                
                with st.spinner("Generating insights..."):
                    insights = generate_data_insights(df, user_question)
                    st.markdown(insights)

                # Display images if present
                display_images_from_dataframe(df)

    # Request ID in footer (collapsed by default)
    if request_id:
        with st.expander("🔗 Request Details", expanded=False):
            st.code(request_id, language=None)



st.set_page_config(layout="wide")

apply_custom_css()

# Sidebar
with st.sidebar:

    st.image("logo2.png", width="content")
    st.caption("Powered by ❄️ Snowflake Cortex")
    
    if st.button("➕  New Conversation", use_container_width=True, type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    
    st.markdown("### 📝 Try These Queries")
    
    example_queries = [
        ("Severity Score for PROP-JPR-APT-008", "What is the total severity score for PROP-JPR-APT-008?"),
        ("Room Analysis for PROP-JPR-HOUS-002", "Show room-wise risk scores for PROP-JPR-HOUS-002"),
        ("View Images for PROP-JPR-APT-008", "Show inspection images for PROP-JPR-APT-008"),
        ("High & Med Risk Properties", "Which properties have High and Medium severity scores?")
    ]
    
    for label, query in example_queries:
        if st.button(label, key=f"ex_{hash(query)}", use_container_width=True,type="primary"):
            st.session_state.active_suggestion = query
    
    st.markdown("---")
    
    with st.expander("ℹ️  About This App"):
        st.markdown("""
        This AI-powered app analyzes home inspection data using **Snowflake Cortex**.
        
        **Features:**
        - Natural language queries
        - AI-generated insights
        - Visual defect evidence
        - Smart data visualization
        """)

st.markdown("""
<div class="main-header">
    <h1> Home Inspection Intelligence</h1>
    <p>AI-powered property risk analysis.</p>
</div>
""", unsafe_allow_html=True)


if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.active_suggestion = None
    st.session_state.current_question = None


for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        display_content(
            message["content"],
            request_id=message.get("request_id"),
            message_index=idx,
        )


if user_input := st.chat_input("Type your question or click an example query in the sidebar."):
    process_message(user_input)


if st.session_state.active_suggestion:
    process_message(st.session_state.active_suggestion)
    st.session_state.active_suggestion = None
