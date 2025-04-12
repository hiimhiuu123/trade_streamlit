import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv

load_dotenv()
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
        .replace("__API_KEY__", MAP4D_API_KEY)
        .replace("__MAP_ID__", MAP4D_MAP_ID or "")
    )
    st.components.v1.html(html_content, height=800)

def main():
    if __name__ == "__main__":
        st.set_page_config(page_title="Bản đồ Cơ sở bán lẻ", layout="wide")
    
    st.title("🛒 Bản đồ Cơ sở bán lẻ")
    
    file_path = os.path.join(os.path.dirname(__file__), "retail_chain_data.csv")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        st.error(f"❌ Lỗi khi đọc file CSV: {e}")
        return

    st.write("### Dữ liệu gốc:")
    st.dataframe(df.head(10))

    city_options = ['Tất cả'] + sorted(df['city'].dropna().unique().tolist())
    retail_options = ['Tất cả'] + sorted(df['retail_chain'].dropna().unique().tolist())
    
    st.sidebar.header("Bộ lọc Bán lẻ")
    selected_city = st.sidebar.selectbox("Chọn thành phố:", options=city_options, key="retail_city_filter")
    selected_retail = st.sidebar.selectbox("Chọn retail_chain:", options=retail_options, key="retail_filter_retail")
    
    filtered_df = df.copy()
    if selected_city != "Tất cả":
        filtered_df = filtered_df[filtered_df['city'] == selected_city]
    if selected_retail != "Tất cả":
        filtered_df = filtered_df[filtered_df['retail_chain'] == selected_retail]
    
    st.write(f"### Dữ liệu đã lọc (số dòng: {filtered_df.shape[0]}):")
    st.dataframe(filtered_df[['id', 'retail_chain', 'name','type', 'address', 'city', 'latitude', 'longitude']])
    
    with st.expander("Xem phân tích dữ liệu tọa độ"):
        total_rows = filtered_df.shape[0]
        missing_coords = filtered_df[filtered_df['latitude'].isna() | filtered_df['longitude'].isna()]
        missing_count = missing_coords.shape[0]
        valid_count = total_rows - missing_count
        st.write(f"Tổng số dòng sau lọc: {total_rows}")
        st.write(f"Số dòng có tọa độ hợp lệ: {valid_count}")
        st.write(f"Số dòng thiếu tọa độ: {missing_count} ({(missing_count/total_rows*100):.2f}%)")
        if 'city' in filtered_df.columns:
            missing_by_city = missing_coords.groupby('city').size().reset_index(name='missing_count')
            st.write("Số dòng thiếu tọa độ theo thành phố:")
            st.dataframe(missing_by_city)
        missing_by_bank = missing_coords.groupby('retail_chain').size().reset_index(name='missing_count')
        st.write("Số dòng thiếu tọa độ theo chuỗi bán lẻ:")
        st.dataframe(missing_by_bank)

    map_df = filtered_df.dropna(subset=["latitude", "longitude"])
    st.sidebar.markdown("### Tuỳ chọn biểu đồ")
    width = st.sidebar.slider("Chọn chiều rộng biểu đồ:", min_value=400, max_value=1200, value=800)
    height = st.sidebar.slider("Chọn chiều cao biểu đồ:", min_value=300, max_value=800, value=400)
    chart_option = st.sidebar.selectbox("Chọn biểu đồ:", options=["Cột chồng", "Tròn"], key="chart_option")
    if chart_option == "Cột chồng":
        st.markdown("### 📈 Biểu đồ cột chồng: Số lượng cửa hàng bán lẻ theo tên chuỗi và loại hình")
        type_subtype_counts = filtered_df.groupby(['retail_chain', 'type']).size().reset_index(name='count')
        fig1 = px.bar(
            type_subtype_counts, 
            x='retail_chain', 
            y='count', 
            color='type',
            labels={'retail_chain': 'Chuỗi bán lẻ', 'count': 'Số lượng', 'type': 'Loại hình'},
            title="Số lượng cửa hàng bán lẻ theo tên chuỗi và loại hình",
            barmode='stack'
        )
        fig1.update_layout(width=width, height=height, xaxis_title="Chuỗi bán lẻ", yaxis_title="Số lượng")
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
    
    if "map_visible_retail" not in st.session_state:
        st.session_state.map_visible_retail = False
    if st.sidebar.button("Hiển thị/Ẩn bản đồ Bán lẻ", key="toggle_map_retail"):
        st.session_state.map_visible_retail = not st.session_state.map_visible_retail

    if st.session_state.map_visible_retail:
        if not MAP4D_API_KEY:
            st.warning("⚠️ Vui lòng cấu hình MAP4D_API_KEY trong phần Secrets của Streamlit")
        else:
            render_map4d(map_df, api_key=MAP4D_API_KEY, map_id=MAP4D_MAP_ID)

if __name__ == "__main__":
    main()
