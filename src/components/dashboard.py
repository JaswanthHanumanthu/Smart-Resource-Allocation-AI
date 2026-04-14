import streamlit as st
import pandas as pd

def render():
    st.subheader("Resource Overview Dashboard")
    
    # Styled metrics container
    st.markdown("""
        <style>
            div[data-testid="metric-container"] {
                background-color: rgba(28, 131, 225, 0.1);
                border: 1px solid rgba(28, 131, 225, 0.1);
                padding: 1.5rem 1rem;
                height: 100%;
                border-radius: 0.5rem;
            }
        </style>
        """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Available Budget", "$1,000,000")
    col2.metric("Funds Allocated", "$750,000", delta="-25,000 (Last Week)")
    col3.metric("Pending Requests", "12", delta="3 (New)")
    
    st.markdown("---")
    st.markdown("### Recent Allocation Requests")
    
    # Sample Mock Data for visual wow-factor
    df = pd.DataFrame({
        "Recipient Initiative": ["Education Access", "Community Health", "Clean Water Taskforce", "Tech for Good"],
        "Requested Amount ($)": [200000, 300000, 150000, 50000],
        "Allocated ($)": [200000, 250000, 150000, 0],
        "Urgency Level": ["High", "Critical", "Medium", "Low"],
        "Status": ["Fully Funded", "Partially Funded", "Fully Funded", "Pending Review"]
    })
    
    # Simple styling on dataframe
    st.dataframe(
        df, 
        width='stretch',
        hide_index=True,
        column_config={
            "Requested Amount ($)": st.column_config.NumberColumn(format="$%d"),
            "Allocated ($)": st.column_config.NumberColumn(format="$%d")
        }
    )
