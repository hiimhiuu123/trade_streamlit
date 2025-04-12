import streamlit as st
import pandas as pd
import plotly.express as px
import os

# MAP4D_API_KEY = os.getenv("MAP4D_API_KEY")
# MAP4D_MAP_ID = os.getenv("MAP4D_MAP_ID", "")

MAP4D_API_KEY = st.secrets.get("MAP4D_API_KEY") or os.getenv("MAP4D_API_KEY")
MAP4D_MAP_ID = st.secrets.get("MAP4D_MAP_ID") or os.getenv("MAP4D_MAP_ID", "")

def render_map4d(df, api_key, map_id=""):
    template_path = os.path.join(os.path.dirname(__file__), "map4d_template.html")
    if not os.path.exists(template_path):
        st.error("❌ Không tìm thấy file map4d_template.html!")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()

    marker_js = ""
    for _, row in df.iterrows():
        marker_js += f"""
        new map4d.Marker({{
            position: {{ lat: {row['latitude']}, lng: {row['longitude']} }},
            title: "{row['name']}"
        }}).setMap(map);
        """
    html_content = (
        html_template
        .replace("##MARKERS_PLACEHOLDER##", marker_js)
        .replace("__API_KEY__", api_key)
        .replace("__MAP_ID__", map_id or "")
    )
    st.components.v1.html(html_content, height=800)

def main():
    if __name__ == "__main__":
        st.set_page_config(page_title="Bản đồ Cơ sở Ngân hàng", layout="wide")
    
    st.title("🏦 Bản đồ Cơ sở Ngân hàng")
    
    file_path = os.path.join(os.path.dirname(__file__), "banking_data.csv")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        st.error(f"❌ Lỗi khi đọc file CSV: {e}")
        return

    st.write("### Dữ liệu gốc:")
    st.dataframe(df)

    # Các bộ lọc được chuyển sang sidebar
    city_options = ['Tất cả'] + sorted(df['city'].dropna().unique().tolist())
    bank_options = ['Tất cả'] + sorted(df['bank'].dropna().unique().tolist())
    
    st.sidebar.header("Bộ lọc Ngân hàng")
    selected_city = st.sidebar.selectbox("Chọn thành phố:", options=city_options, key="bank_city_filter")
    selected_bank = st.sidebar.selectbox("Chọn ngân hàng:", options=bank_options, key="bank_filter")
    
    filtered_df = df.copy()
    if selected_city != "Tất cả":
        filtered_df = filtered_df[filtered_df['city'] == selected_city]
    if selected_bank != "Tất cả":
        filtered_df = filtered_df[filtered_df['bank'] == selected_bank]
    
    st.write(f"### Dữ liệu đã lọc (số dòng: {filtered_df.shape[0]}):")
    st.dataframe(filtered_df[['id', 'bank', 'bank_name', 'name', 'city', 'latitude', 'longitude']])
    
    with st.expander("Phân tích dữ liệu tọa độ"):
        total_rows = filtered_df.shape[0]
        missing_coords = filtered_df[filtered_df['latitude'].isna() | filtered_df['longitude'].isna()]
        missing_count = missing_coords.shape[0]
        valid_count = total_rows - missing_count
        st.write(f"Tổng số dòng sau lọc: {total_rows}")
        st.write(f"Số dòng có tọa độ hợp lệ: {valid_count}")
        st.write(f"Số dòng thiếu tọa độ: {missing_count} ({(missing_count/total_rows*100):.2f}%)")
        
        missing_by_city = missing_coords.groupby('city').size().reset_index(name='missing_count')
        st.write("Số dòng thiếu tọa độ theo thành phố:")
        st.dataframe(missing_by_city)
        
        missing_by_bank = missing_coords.groupby('bank').size().reset_index(name='missing_count')
        st.write("Số dòng thiếu tọa độ theo ngân hàng:")
        st.dataframe(missing_by_bank)
    
    map_df = filtered_df.dropna(subset=["latitude", "longitude"])
    
    if "map_visible_bank" not in st.session_state:
        st.session_state.map_visible_bank = False
    if st.sidebar.button("Hiển thị/Ẩn bản đồ Ngân hàng", key="toggle_map_bank"):
        st.session_state.map_visible_bank = not st.session_state.map_visible_bank
    st.sidebar.markdown("### Tuỳ chọn biểu đồ")
    width = st.sidebar.slider("Chọn chiều rộng biểu đồ:", min_value=400, max_value=1200, value=800)
    height = st.sidebar.slider("Chọn chiều cao biểu đồ:", min_value=300, max_value=800, value=400)
    chart_option = st.sidebar.selectbox("Chọn biểu đồ:", options=["Cột chồng", "Tròn"], key="chart_option")
    if chart_option == "Cột chồng":
        st.markdown("### 📈 Biểu đồ cột chồng: Số lượng ATM và phòng giao dịch theo loại hình")
        type_subtype_counts = filtered_df.groupby(['bank', 'type']).size().reset_index(name='count')
        fig1 = px.bar(
            type_subtype_counts, 
            x='bank', 
            y='count', 
            color='type',
            labels={'bank': 'Ngân hàng', 'count': 'Số lượng', 'type': 'Loại hình'},
            title="Số lượng ATM và địa điểm giao dịch theo ngân hàng và loại hình",
            barmode='stack'
        )
        fig1.update_layout(width=width, height=height, xaxis_title="Ngân hàng", yaxis_title="Số lượng")
        st.plotly_chart(fig1)
    elif chart_option == "Tròn":
        st.markdown("### 🥧 Biểu đồ tròn: Tỉ lệ địa điểm giao dịch theo ngân hàng")
        type_counts = df['bank'].value_counts()
        fig2 = px.pie(
            names=type_counts.index, 
            values=type_counts.values, 
            title="Tỉ lệ phần trăm ngân hàng"
        )
        fig2.update_layout(width=width, height=height)
        st.plotly_chart(fig2)
    if st.session_state.map_visible_bank:
        if not MAP4D_API_KEY:
            st.warning("⚠️ Vui lòng cấu hình MAP4D_API_KEY trong phần Secrets của Streamlit")
        else:
            render_map4d(map_df, api_key=MAP4D_API_KEY, map_id=MAP4D_MAP_ID)

if __name__ == "__main__":
    main()
