import re
import streamlit as st


def render_scenario_viewer(report):
    st.markdown("### Scenario analysis")
    st.caption("The scenarios below are generated from the decision analysis. They are not guaranteed forecasts.")
    st.write(report[:6000])
