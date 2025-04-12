import pandas as pd
import streamlit as st
import plotly.express as px
import os
from dotenv import load_dotenv

load_dotenv()
# MAP4D_API_KEY = os.getenv("MAP4D_API_KEY")
# MAP4D_MAP_ID = os.getenv("MAP4D_MAP_ID", "")

MAP4D_API_KEY = st.secrets.get("MAP4D_API_KEY") or os.getenv("MAP4D_API_KEY")
MAP4D_MAP_ID = st.secrets.get("MAP4D_MAP_ID") or os.getenv("MAP4D_MAP_ID", "")

def extract_plant_type(name):
    name_lower = name.lower()
    if "mặt trời" in name_lower:
        return "Điện mặt trời"
    elif "gió" in name_lower:
        return "Điện gió"
    elif "thuỷ" in name_lower:
        return "Thuỷ điện"
    else:
        return name

def render_map4d(df, api_key, map_id=""):
    template_path = os.path.join(os.path.dirname(__file__), 'map4d_template.html')
    if not os.path.exists(template_path):
        st.error("❌ Không tìm thấy file map4d_template.html!")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()

    marker_js = ""
    for _, row in df.iterrows():
        marker_js += f"""
        new map4d.Marker({{
          position: {{ lat: {row['lat']}, lng: {row['lon']} }},
          title: "{row['name']}"
        }}).setMap(map);
        """
    html_content = (html_template
                    .replace("##MARKERS_PLACEHOLDER##", marker_js)
                    .replace("__API_KEY__", api_key)
                    .replace("__MAP_ID__", map_id or ""))
    st.components.v1.html(html_content, height=800)

def main():
    st.title("📊 Thống kê Nhà máy điện tái tạo")

    file_path = os.path.join(os.path.dirname(__file__), 'input.csv')
    try:
        df = pd.read_csv(file_path, sep='\t')
        st.success("")
    except Exception as e:
        st.error(f"❌ Lỗi khi đọc file CSV: {e}")
        return

    if 'latlng' not in df.columns:
        st.error("❌ Không tìm thấy cột 'latlng' trong dữ liệu!")
        return

    if 'sub_type' not in df.columns:
        st.error("❌ Không tìm thấy cột 'sub_type' trong dữ liệu!")
    df['sub_type'] = df.apply(lambda row: row['type'] if pd.isna(row['sub_type']) or row['sub_type'] == 'None' else row['sub_type'], axis=1)

    df = df.dropna(subset=['latlng'])
    df[['lat', 'lon']] = df['latlng'].str.replace('"', '').str.split(',', expand=True)
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    df = df.dropna(subset=['lat', 'lon'])

    if 'Column1' in df.columns:
        df.rename(columns={'Column1': 'name'}, inplace=True)
    else:
        st.error("❌ Không tìm thấy cột 'Column1' chứa tên nhà máy!")
        return

    df['type'] = df['type'].apply(extract_plant_type)

    # Các bộ lọc được đặt ở sidebar
    st.sidebar.header("Bộ lọc Nhà máy điện")
    name_filter = st.sidebar.text_input("Lọc theo tên nhà máy (name):", "")
    type_filter = st.sidebar.selectbox("Lọc theo loại nhà máy (type):", options=['Tất cả'] + sorted(df['type'].unique().tolist()))
    sub_type_filter = st.sidebar.selectbox("Lọc theo phân loại phụ (sub_type):", options=['Tất cả'] + sorted(df['sub_type'].unique().tolist()))
    province_filter = st.sidebar.selectbox("Lọc theo vị trí (province):", options=['Tất cả'] + sorted(df['province'].dropna().unique().tolist()))

    filtered_df = df.copy()
    if name_filter:
        filtered_df = filtered_df[filtered_df['name'].str.contains(name_filter, case=False, na=False)]
    if type_filter != 'Tất cả':
        filtered_df = filtered_df[filtered_df['type'] == type_filter]
    if sub_type_filter != 'Tất cả':
        filtered_df = filtered_df[filtered_df['sub_type'] == sub_type_filter]
    if province_filter != 'Tất cả':
        filtered_df = filtered_df[filtered_df['province'] == province_filter]

    st.markdown("### 📌 Dữ liệu đã xử lý:")
    st.dataframe(filtered_df[['name', 'type', 'sub_type', 'river', 'lat', 'lon', 'province']])

    st.markdown("### 📊 Số lượng nhà máy theo loại hình:")
    type_counts = df['type'].value_counts()
    st.dataframe(type_counts.rename("Số lượng"))

    # Bộ lọc bản đồ cũng đặt ở sidebar
    st.sidebar.markdown("### Bộ lọc Bản đồ")
    plant_type_filter_map = st.sidebar.selectbox("Chọn loại nhà máy (bản đồ):", options=['Tất cả'] + sorted(df['type'].unique().tolist()), key="plant_type_filter_map")
    province_filter_map = st.sidebar.selectbox("Chọn vị trí (bản đồ):", options=['Tất cả'] + sorted(df['province'].dropna().unique().tolist()), key="province_filter_map")

    filtered_df_map = df.copy()
    if plant_type_filter_map != 'Tất cả':
        filtered_df_map = filtered_df_map[filtered_df_map['type'] == plant_type_filter_map]
    if province_filter_map != 'Tất cả':
        filtered_df_map = filtered_df_map[filtered_df_map['province'] == province_filter_map]

    if "map_visible" not in st.session_state:
        st.session_state.map_visible = False
    if st.sidebar.button("Hiển thị/Ẩn bản đồ", key="toggle_map_button"):
        st.session_state.map_visible = not st.session_state.map_visible
    if st.session_state.map_visible:
        if not MAP4D_API_KEY:
            st.warning("⚠️ Vui lòng cấu hình MAP4D_API_KEY trong file .env")
        else:
            map_df = filtered_df_map[['lat', 'lon', 'name']]
            render_map4d(map_df, api_key=MAP4D_API_KEY, map_id=MAP4D_MAP_ID)

    # Các tùy chọn biểu đồ cũng đặt trong sidebar
    st.sidebar.markdown("### Tuỳ chọn biểu đồ")
    width = st.sidebar.slider("Chọn chiều rộng biểu đồ:", min_value=400, max_value=1200, value=800)
    height = st.sidebar.slider("Chọn chiều cao biểu đồ:", min_value=300, max_value=800, value=400)
    chart_option = st.sidebar.selectbox("Chọn biểu đồ:", options=["Cột chồng", "Tròn", "Cột ngang"], key="chart_option")
    if chart_option == "Cột chồng":
        st.markdown("### 📈 Biểu đồ cột chồng: Số lượng nhà máy theo loại hình và phân loại phụ")
        type_subtype_counts = filtered_df.groupby(['type', 'sub_type']).size().reset_index(name='count')
        fig1 = px.bar(
            type_subtype_counts, 
            x='type', 
            y='count', 
            color='sub_type',
            labels={'type': 'Loại hình', 'count': 'Số lượng', 'sub_type': 'Phân loại phụ'},
            title="Số lượng nhà máy theo loại hình và phân loại phụ",
            barmode='stack'
        )
        fig1.update_layout(width=width, height=height, xaxis_title="Loại hình", yaxis_title="Số lượng")
        st.plotly_chart(fig1)
    elif chart_option == "Tròn":
        st.markdown("### 🥧 Biểu đồ tròn: Tỉ lệ nhà máy theo loại hình")
        type_counts = df['type'].value_counts()
        fig2 = px.pie(
            names=type_counts.index, 
            values=type_counts.values, 
            title="Tỉ lệ phần trăm nhà máy"
        )
        fig2.update_layout(width=width, height=height)
        st.plotly_chart(fig2)
    elif chart_option == "Cột ngang":
        chart_filter = st.sidebar.selectbox("Chọn loại dữ liệu để vẽ biểu đồ cột ngang:", options=['Loại hình nhà máy', 'Phân loại phụ (sub_type)', 'Vị trí (province)'], key="chart_filter")
        if chart_filter == 'Loại hình nhà máy':
            st.markdown("### 📊 Biểu đồ cột ngang: Tổng công suất theo loại hình nhà máy")
            type_capacity = df.groupby('type')['capacity'].sum().reset_index()
            fig = px.bar(
                type_capacity, 
                x='capacity', 
                y='type', 
                orientation='h',
                labels={'capacity': 'Tổng công suất (MW)', 'type': 'Loại hình nhà máy'},
                title="Tổng công suất theo loại hình nhà máy"
            )
            fig.update_layout(width=width, height=height)
            st.plotly_chart(fig)
        elif chart_filter == 'Phân loại phụ (sub_type)':
            st.markdown("### 📊 Biểu đồ cột ngang: Tổng công suất theo phân loại phụ (sub_type)")
            sub_type_capacity = df.groupby('sub_type')['capacity'].sum().reset_index()
            fig = px.bar(
                sub_type_capacity, 
                x='capacity', 
                y='sub_type', 
                orientation='h',
                labels={'capacity': 'Tổng công suất (MW)', 'sub_type': 'Phân loại phụ'},
                title="Tổng công suất theo phân loại phụ (sub_type)"
            )
            fig.update_layout(width=width, height=height)
            st.plotly_chart(fig)
        elif chart_filter == 'Vị trí (province)':
            st.markdown("### 📊 Biểu đồ cột ngang: Tổng công suất theo tỉnh thành")
            province_capacity = df.groupby('province')['capacity'].sum().reset_index()
            fig = px.bar(
                province_capacity, 
                x='capacity', 
                y='province', 
                orientation='h',
                labels={'capacity': 'Tổng công suất (MW)', 'province': 'Tỉnh thành'},
                title="Tổng công suất theo tỉnh thành"
            )
            fig.update_layout(width=width, height=height)
            st.plotly_chart(fig)

def run_app():
    st.set_page_config(page_title="Ứng dụng Nhà máy điện & Bán lẻ", layout="wide")
    menu_option = st.sidebar.radio("Chọn loại hình:", options=["Nhà máy điện", "Cơ sở bán lẻ"], key="menu_option")
    if menu_option == "Nhà máy điện":
        main()
    else:
        st.title("Cơ sở bán lẻ")
        st.info("Chức năng 'Cơ sở bán lẻ' chưa được triển khai.")

if __name__ == "__main__":
    run_app()
