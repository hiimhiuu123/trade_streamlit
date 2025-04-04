import os
import pandas as pd
import streamlit as st
import plotly.express as px
from dotenv import load_dotenv

# Load biến môi trường cho MAP4D
load_dotenv()
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

def load_data(file_path):
    try:
        df = pd.read_csv(file_path, sep='\t')
    except Exception as e:
        st.error(f"❌ Lỗi khi đọc file CSV: {e}")
        return None

    # Kiểm tra các cột cần thiết
    if 'latlng' not in df.columns or 'sub_type' not in df.columns or 'Column1' not in df.columns:
        st.error("❌ Dữ liệu không đầy đủ các cột cần thiết!")
        return None

    # Xử lý dữ liệu vị trí
    df = df.dropna(subset=['latlng'])
    df[['lat', 'lon']] = df['latlng'].str.replace('"', '').str.split(',', expand=True)
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    df = df.dropna(subset=['lat', 'lon'])

    # Đổi tên cột và xử lý phân loại phụ
    df.rename(columns={'Column1': 'name'}, inplace=True)
    df['sub_type'] = df.apply(
        lambda row: row['type'] if pd.isna(row['sub_type']) or row['sub_type'] == 'None' else row['sub_type'],
        axis=1
    )
    df['type'] = df['type'].apply(extract_plant_type)
    return df

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

def filter_data(df, filters):
    filtered_df = df.copy()
    if filters.get("name"):
        filtered_df = filtered_df[filtered_df['name'].str.contains(filters["name"], case=False, na=False)]
    if filters.get("type") and filters["type"] != 'Tất cả':
        filtered_df = filtered_df[filtered_df['type'] == filters["type"]]
    if filters.get("sub_type") and filters["sub_type"] != 'Tất cả':
        filtered_df = filtered_df[filtered_df['sub_type'] == filters["sub_type"]]
    if filters.get("province") and filters["province"] != 'Tất cả':
        filtered_df = filtered_df[filtered_df['province'] == filters["province"]]
    return filtered_df

def render_data_tab(df, filtered_df):
    st.subheader("Dữ liệu đã xử lý")
    st.dataframe(filtered_df[['name', 'type', 'sub_type', 'river', 'lat', 'lon', 'province']])
    
    st.subheader("Số lượng nhà máy theo loại hình")
    type_counts = df['type'].value_counts().reset_index()
    type_counts.columns = ['Loại hình', 'Số lượng']
    st.dataframe(type_counts)

def render_map_tab(df):
    st.subheader("Bản đồ nhà máy điện")
    st.info("Sử dụng bộ lọc riêng cho bản đồ.")
    type_options = ['Tất cả'] + sorted(df['type'].unique().tolist())
    province_options = ['Tất cả'] + (sorted(df['province'].dropna().unique().tolist()) if 'province' in df.columns else [])
    
    plant_type_filter_map = st.selectbox("Chọn loại nhà máy (bản đồ):", options=type_options, key="plant_type_filter_map")
    province_filter_map = st.selectbox("Chọn vị trí (bản đồ):", options=province_options, key="province_filter_map")
    
    filtered_map_df = df.copy()
    if plant_type_filter_map != 'Tất cả':
        filtered_map_df = filtered_map_df[filtered_map_df['type'] == plant_type_filter_map]
    if province_filter_map != 'Tất cả':
        filtered_map_df = filtered_map_df[filtered_map_df['province'] == province_filter_map]
    
    if not MAP4D_API_KEY:
        st.warning("⚠️ Vui lòng cấu hình MAP4D_API_KEY trong file .env")
    else:
        if st.button("Hiển thị bản đồ"):
            render_map4d(filtered_map_df[['lat', 'lon', 'name']], api_key=MAP4D_API_KEY, map_id=MAP4D_MAP_ID)

def render_chart_tab(df, filtered_df):
    st.subheader("Biểu đồ tương tác")
    chart_option = st.selectbox("Chọn biểu đồ:", options=["Biểu đồ cột chồng", "Biểu đồ tròn", "Biểu đồ cột ngang"])
    
    if chart_option == "Biểu đồ cột chồng":
        st.markdown("### Biểu đồ cột chồng: Số lượng nhà máy theo loại hình và phân loại phụ")
        type_subtype_counts = filtered_df.groupby(['type', 'sub_type']).size().reset_index(name='count')
        fig_bar = px.bar(
            type_subtype_counts, 
            x='type', 
            y='count', 
            color='sub_type', 
            title="Số lượng nhà máy theo loại hình và phân loại phụ",
            labels={'type': 'Loại hình', 'count': 'Số lượng', 'sub_type': 'Phân loại phụ'},
            barmode='stack'
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
    elif chart_option == "Biểu đồ tròn":
        st.markdown("### Biểu đồ tròn: Tỉ lệ phần trăm nhà máy theo loại hình")
        type_counts = df['type'].value_counts()
        fig_pie = px.pie(
            names=type_counts.index, 
            values=type_counts.values, 
            title="Tỉ lệ phần trăm nhà máy"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
    elif chart_option == "Biểu đồ cột ngang":
        st.markdown("### Biểu đồ cột ngang: Tổng công suất")
        horizontal_option = st.selectbox("Chọn dữ liệu:", options=["Loại hình", "Phân loại phụ", "Vị trí"])
        if horizontal_option == "Loại hình":
            cap_df = df.groupby('type')['capacity'].sum().reset_index()
            fig_hbar = px.bar(
                cap_df, 
                x='capacity', 
                y='type', 
                orientation='h', 
                title="Tổng công suất theo loại hình",
                labels={'capacity': 'Tổng công suất (MW)', 'type': 'Loại hình'}
            )
            st.plotly_chart(fig_hbar, use_container_width=True)
        elif horizontal_option == "Phân loại phụ":
            cap_df = df.groupby('sub_type')['capacity'].sum().reset_index()
            fig_hbar = px.bar(
                cap_df, 
                x='capacity', 
                y='sub_type', 
                orientation='h', 
                title="Tổng công suất theo phân loại phụ",
                labels={'capacity': 'Tổng công suất (MW)', 'sub_type': 'Phân loại phụ'}
            )
            st.plotly_chart(fig_hbar, use_container_width=True)
        elif horizontal_option == "Vị trí":
            cap_df = df.groupby('province')['capacity'].sum().reset_index()
            fig_hbar = px.bar(
                cap_df, 
                x='capacity', 
                y='province', 
                orientation='h', 
                title="Tổng công suất theo tỉnh thành",
                labels={'capacity': 'Tổng công suất (MW)', 'province': 'Tỉnh thành'}
            )
            st.plotly_chart(fig_hbar, use_container_width=True)

def main():
    st.set_page_config(page_title="Ứng dụng Nhà máy điện & Bán lẻ", layout="wide")
    menu_option = st.sidebar.radio("Chọn loại hình:", options=["Nhà máy điện", "Cơ sở bán lẻ"])
    
    if menu_option == "Nhà máy điện":
        st.title("📊 Thống kê Nhà máy điện tái tạo")
        file_path = os.path.join(os.path.dirname(__file__), 'input.csv')
        df = load_data(file_path)
        if df is None:
            return

        # Sidebar: Bộ lọc dữ liệu
        st.sidebar.header("Bộ lọc dữ liệu")
        name_filter = st.sidebar.text_input("Lọc theo tên nhà máy:", "")
        type_options = ['Tất cả'] + sorted(df['type'].unique().tolist())
        type_filter = st.sidebar.selectbox("Lọc theo loại nhà máy:", options=type_options)
        sub_type_options = ['Tất cả'] + sorted(df['sub_type'].unique().tolist())
        sub_type_filter = st.sidebar.selectbox("Lọc theo phân loại phụ:", options=sub_type_options)
        province_options = ['Tất cả'] + (sorted(df['province'].dropna().unique().tolist()) if 'province' in df.columns else [])
        province_filter = st.sidebar.selectbox("Lọc theo vị trí:", options=province_options)

        filters = {
            "name": name_filter,
            "type": type_filter,
            "sub_type": sub_type_filter,
            "province": province_filter
        }
        filtered_df = filter_data(df, filters)
        
        # Sử dụng Tabs cho các phần hiển thị
        tabs = st.tabs(["Dữ liệu", "Bản đồ", "Biểu đồ"])
        
        with tabs[0]:
            render_data_tab(df, filtered_df)
        with tabs[1]:
            render_map_tab(df)
        with tabs[2]:
            render_chart_tab(df, filtered_df)
            
    else:
        st.title("Cơ sở bán lẻ")
        st.info("Chức năng 'Cơ sở bán lẻ' chưa được triển khai.")

if __name__ == "__main__":
    main()
