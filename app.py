import streamlit as st
from trade_map import main as powerplant_main
from retail_map import main as retail_map_main

st.set_page_config(page_title="Ứng dụng Nhà máy điện & Bán lẻ", layout="wide")

menu_option = st.sidebar.radio(
    "Chọn loại hình:",
    options=["Nhà máy điện", "Bán lẻ"],
    key="menu_option"
)

if menu_option == "Nhà máy điện":
    powerplant_main()
else:
    retail_map_main()
