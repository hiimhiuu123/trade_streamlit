import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import os
from dotenv import load_dotenv

# Tải các biến môi trường từ .env
load_dotenv()
MAP4D_API_KEY = os.getenv("MAP4D_API_KEY")
MAP4D_MAP_ID = os.getenv("MAP4D_MAP_ID", "")

# ------------------ TÁCH HÀM ------------------

def extract_plant_type(name):
    name_lower = name.lower()
    if "mặt trời" in name_lower:
        return "Điện mặt trời"
    elif "gió" in name_lower:
        return "Điện gió"
    elif "thuỷ điện" in name_lower:
        return "Thủy điện"
    elif "thủy điện" in name_lower:
        return "Thủy điện"
    else:
        return name

def render_map4d(df, api_key, map_id=""):
    template_path = os.path.join(os.path.dirname(__file__), 'map4d_template.html')

    if not os.path.exists(template_path):
        st.error("❌ Không tìm thấy file map4d_template.html!")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()

    # Tạo đoạn JS marker động từ DataFrame
    marker_js = ""
    for _, row in df.iterrows():
        marker_js += f"""
        new map4d.Marker({{
          position: {{ lat: {row['lat']}, lng: {row['lon']} }},
          title: "{row['name']}"
        }}).setMap(map);
        """

    # Thay thế placeholder bằng nội dung thật
    html_content = (
        html_template
        .replace("##MARKERS_PLACEHOLDER##", marker_js)
        .replace("__API_KEY__", api_key)
        .replace("__MAP_ID__", map_id or "")
    )

    # Render trực tiếp vào giao diện Streamlit
    st.components.v1.html(html_content, height=800)

# ------------------ MAIN ------------------

def main():
    st.set_page_config(page_title="Thống kê nhà máy điện", layout="wide")
    st.title("📊 Thống kê Nhà máy điện từ File CSV")

    file_path = os.path.join(os.path.dirname(__file__), 'input.csv')

    try:
        df = pd.read_csv(file_path, sep='\t')
        st.success(f"✅ Đọc thành công dữ liệu từ: `{file_path}`")
    except Exception as e:
        st.error(f"❌ Lỗi khi đọc file CSV: {e}")
        return

    if 'latlng' not in df.columns:
        st.error("❌ Không tìm thấy cột `latlng` trong dữ liệu!")
        return
    if 'sub_type' not in df.columns:
        st.error("❌ Không tìm thấy cột `sub_type` trong dữ liệu!")
    # Nếu giá trị trong cột 'sub_type' là 'None' hoặc NaN, thay bằng giá trị ở cột 'type'
    df['sub_type'] = df.apply(lambda row: row['type'] if pd.isna(row['sub_type']) or row['sub_type'] == 'None' else row['sub_type'], axis=1)


    df = df.dropna(subset=['latlng'])
    df[['lat', 'lon']] = df['latlng'].str.replace('"', '').str.split(',', expand=True)
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    df = df.dropna(subset=['lat', 'lon'])

    if 'Column1' in df.columns:
        df.rename(columns={'Column1': 'name'}, inplace=True)
    else:
        st.error("❌ Không tìm thấy cột `Column1` chứa tên nhà máy!")
        return

    df['type'] = df['type'].apply(extract_plant_type)
    
    
    
    st.markdown("### 📌 Dữ liệu đã xử lý:")

    # Thêm bộ lọc cho các cột name, type, sub_type, province
    name_filter = st.text_input("Lọc theo tên nhà máy (name):", "")
    type_filter = st.selectbox("Lọc theo loại nhà máy (type):", options=['Tất cả'] + df['type'].unique().tolist())
    sub_type_filter = st.selectbox("Lọc theo phân loại phụ (sub_type):", options=['Tất cả'] + df['sub_type'].unique().tolist())
    province_filter = st.selectbox("Lọc theo vị trí (province):", options=['Tất cả'] + df['province'].dropna().unique().tolist())

    # Lọc dữ liệu theo các điều kiện đã chọn
    filtered_df = df.copy()

    # Lọc theo tên nhà máy
    if name_filter:
        filtered_df = filtered_df[filtered_df['name'].str.contains(name_filter, case=False, na=False)]

    # Lọc theo loại nhà máy
    if type_filter != 'Tất cả':
        filtered_df = filtered_df[filtered_df['type'] == type_filter]

    # Lọc theo phân loại phụ (sub_type)
    if sub_type_filter != 'Tất cả':
        filtered_df = filtered_df[filtered_df['sub_type'] == sub_type_filter]

    # Lọc theo tỉnh thành
    if province_filter != 'Tất cả':
        filtered_df = filtered_df[filtered_df['province'] == province_filter]

    # Hiển thị bảng dữ liệu đã lọc
    st.dataframe(filtered_df[['name', 'type', 'sub_type', 'river', 'lat', 'lon', 'province']])


    # Thống kê
    type_counts = df['type'].value_counts()
    st.markdown("### 📊 Số lượng nhà máy theo loại hình:")
    st.dataframe(type_counts.rename("Số lượng"))
            
            
    
    
    st.markdown("### 🗺️ Bản đồ Map4D")

    # Thêm bộ lọc cho loại nhà máy và tỉnh thành cho bản đồ
    plant_type_filter_map = st.selectbox(
        "Chọn loại nhà máy để lọc (bản đồ):", 
        options=['Tất cả'] + df['type'].unique().tolist(),
        key="plant_type_filter_map"  # Key duy nhất cho bộ lọc loại nhà máy
    )

    province_filter_map = st.selectbox(
        "Chọn vị trí nhà máy (bản đồ):", 
        options=['Tất cả'] + df['province'].dropna().unique().tolist(),
        key="province_filter_map"  # Key duy nhất cho bộ lọc tỉnh thành
    )

    # Lọc dữ liệu cho bản đồ
    filtered_df_map = df.copy()

    # Lọc theo loại nhà máy
    if plant_type_filter_map != 'Tất cả':
        filtered_df_map = filtered_df_map[filtered_df_map['type'] == plant_type_filter_map]

    # Lọc theo tỉnh thành
    if province_filter_map != 'Tất cả':
        filtered_df_map = filtered_df_map[filtered_df_map['province'] == province_filter_map]

    if "map_visible" not in st.session_state:
        st.session_state.map_visible = False

    # Tạo nút "Hiển thị/Ẩn bản đồ" với key duy nhất
    if st.button("Hiển thị/Ẩn bản đồ", key="toggle_map_button"):
        st.session_state.map_visible = not st.session_state.map_visible  # Thay đổi trạng thái hiển thị

    # Nếu bản đồ đang hiển thị, gọi hàm render_map4d
    if st.session_state.map_visible:
        if not MAP4D_API_KEY:
            st.warning("⚠️ Vui lòng cấu hình MAP4D_API_KEY trong file .env")
        else:
            map_df = filtered_df_map.rename(columns={'name': 'name'})[['lat', 'lon', 'name']]
            render_map4d(map_df, api_key=MAP4D_API_KEY, map_id=MAP4D_MAP_ID)
            
            
    # Điều chỉnh kích cỡ biểu đồ
    st.markdown("### Tuỳ chọn kích cỡ biểu đồ:")
    width = st.slider("Chọn chiều rộng biểu đồ:", min_value=400, max_value=1200, value=800)
    height = st.slider("Chọn chiều cao biểu đồ:", min_value=300, max_value=800, value=400)
    
    # Biểu đồ cột chồng
    
    st.markdown("### 📈 Biểu đồ cột chồng: Số lượng nhà máy theo loại hình, sub_type và Province")

    # Bộ lọc riêng cho biểu đồ cột chồng
    plant_type_filter_bar = st.selectbox(
        "Chọn loại nhà máy để lọc (biểu đồ cột chồng):",
        options=['Tất cả'] + df['type'].unique().tolist(),
        key="plant_type_filter_bar"  # Thêm key duy nhất
    )
    province_filter_bar = st.selectbox(
        "Chọn vị trí nhà máy (biểu đồ cột chồng):",
        options=['Tất cả'] + df['province'].dropna().unique().tolist(),
        key="province_filter_bar"  # Thêm key duy nhất
    )

    # Lọc dữ liệu theo bộ lọc: type và province
    filtered_df_bar = df.copy()
    if plant_type_filter_bar != 'Tất cả':
        filtered_df_bar = filtered_df_bar[filtered_df_bar['type'] == plant_type_filter_bar]
    if province_filter_bar != 'Tất cả':
        filtered_df_bar = filtered_df_bar[filtered_df_bar['province'] == province_filter_bar]

    # Tạo bảng đếm số lượng cho từng loại (type) và sub_type
    type_subtype_counts = filtered_df_bar.groupby(['type', 'sub_type']).size().reset_index(name='count')

    # Vẽ biểu đồ cột chồng với Plotly
    fig1 = px.bar(
        type_subtype_counts, 
        x='type', 
        y='count', 
        color='sub_type',  # Mỗi sub_type sẽ có màu riêng
        labels={'type': 'Loại hình', 'count': 'Số lượng', 'sub_type': 'Phân loại phụ'},
        title="Số lượng nhà máy theo loại hình và phân loại phụ (sub_type)",
        barmode='stack'  # Chế độ chồng cột
    )
    fig1.update_layout(
        width=width,   # Điều chỉnh chiều rộng
        height=height,  # Điều chỉnh chiều cao
        xaxis_title="Loại hình",
        yaxis_title="Số lượng"
    )
    st.plotly_chart(fig1)



    # Biểu đồ tròn
    
    st.markdown("### 🥧 Biểu đồ tròn: Tỷ lệ nhà máy theo loại hình")
    # Biểu đồ tròn bằng Plotly
    type_counts = df['type'].value_counts()
    fig2 = px.pie(
        names=type_counts.index, 
        values=type_counts.values, 
        title="Tỉ lệ phần trăm nhà máy"
    )
    fig2.update_layout(
        width=width,   # Điều chỉnh chiều rộng
        height=height,  # Điều chỉnh chiều cao
        xaxis_title="Loại hình",
        yaxis_title="Số lượng"
    )
    st.plotly_chart(fig2)
    


    # Thêm bộ lọc để chọn loại dữ liệu muốn vẽ biểu đồ
    chart_filter = st.selectbox(
        "Chọn loại dữ liệu để vẽ biểu đồ cột ngang:",
        options=['Loại hình nhà máy', 'Phân loại phụ (sub_type)', 'Vị trí (province)']
    )



    # Dựa trên lựa chọn của người dùng, lọc dữ liệu và vẽ biểu đồ
    if chart_filter == 'Loại hình nhà máy':
        st.markdown("### 📊 Biểu đồ cột ngang: Tổng công suất theo loại hình nhà máy")
        
        # Lọc dữ liệu theo loại hình nhà máy
        type_capacity = df.groupby('type')['capacity'].sum().reset_index()
        
        # Vẽ biểu đồ cột ngang
        fig = px.bar(
            type_capacity, 
            x='capacity', 
            y='type', 
            orientation='h',  # Cột ngang
            labels={'capacity': 'Tổng công suất (MW)', 'type': 'Loại hình nhà máy'},
            title="Tổng công suất theo loại hình nhà máy"
        )
        fig.update_layout(
            width=width,   # Sử dụng chiều rộng từ slider
            height=height,  # Sử dụng chiều cao từ slider
            xaxis_title="Tổng công suất (MW)",
            yaxis_title="Loại hình nhà máy"
        )
        st.plotly_chart(fig)

    elif chart_filter == 'Phân loại phụ (sub_type)':
        st.markdown("### 📊 Biểu đồ cột ngang: Tổng công suất theo phân loại phụ (sub_type)")
        
        # Lọc dữ liệu theo phân loại phụ
        sub_type_capacity = df.groupby('sub_type')['capacity'].sum().reset_index()
        
        # Vẽ biểu đồ cột ngang
        fig = px.bar(
            sub_type_capacity, 
            x='capacity', 
            y='sub_type', 
            orientation='h',  # Cột ngang
            labels={'capacity': 'Tổng công suất (MW)', 'sub_type': 'Phân loại phụ'},
            title="Tổng công suất theo phân loại phụ (sub_type)"
        )
        fig.update_layout(
            width=width,   # Sử dụng chiều rộng từ slider
            height=height,  # Sử dụng chiều cao từ slider
            xaxis_title="Tổng công suất (MW)",
            yaxis_title="Phân loại phụ (sub_type)"
        )
        st.plotly_chart(fig)

    elif chart_filter == 'Vị trí (province)':
        st.markdown("### 📊 Biểu đồ cột ngang: Tổng công suất theo tỉnh thành")
        
        # Lọc dữ liệu theo tỉnh thành
        province_capacity = df.groupby('province')['capacity'].sum().reset_index()
        
        # Vẽ biểu đồ cột ngang
        fig = px.bar(
            province_capacity, 
            x='capacity', 
            y='province', 
            orientation='h',  # Cột ngang
            labels={'capacity': 'Tổng công suất (MW)', 'province': 'Tỉnh thành'},
            title="Tổng công suất theo tỉnh thành"
        )
        fig.update_layout(
            width=width,   # Sử dụng chiều rộng từ slider
            height=height,  # Sử dụng chiều cao từ slider
            xaxis_title="Tổng công suất (MW)",
            yaxis_title="Tỉnh thành"
        )
        st.plotly_chart(fig)



if __name__ == "__main__":
    main()
