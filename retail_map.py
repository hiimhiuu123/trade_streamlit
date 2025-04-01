import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

# Tải các biến môi trường từ file .env (cho phát triển cục bộ; khi deploy, cấu hình trực tiếp trên nền tảng)
load_dotenv()
MAP4D_API_KEY = st.secrets.get("MAP4D_API_KEY") or os.getenv("MAP4D_API_KEY")
MAP4D_MAP_ID = st.secrets.get("MAP4D_MAP_ID") or os.getenv("MAP4D_MAP_ID", "")

def render_map4d(df, api_key, map_id=""):
    """
    Hiển thị bản đồ Map4D sử dụng template map4d_template.html.
    Template cần chứa các placeholder: ##MARKERS_PLACEHOLDER##, __API_KEY__, __MAP_ID__.
    """
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
    # Nếu file được chạy độc lập, cấu hình trang; khi được import thì không gọi.
    if __name__ == "__main__":
        st.set_page_config(page_title="Bản đồ Cơ sở bán lẻ", layout="wide")
    
    st.title("🛒 Bản đồ Cơ sở bán lẻ")
    
    file_path = os.path.join(os.path.dirname(__file__), "retail_chain_data.csv")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        st.error(f"❌ Lỗi khi đọc file CSV: {e}")
        return

    # Xử lý: Nếu cột 'name' bị trống, thay thế bằng retail_chain + address
    df['name'] = df.apply(
        lambda row: f"{row['retail_chain']} {row['address']}" 
                    if (pd.isna(row['name']) or str(row['name']).strip() == "") 
                    else row['name'],
        axis=1
    )

    st.write("### Dữ liệu gốc:")
    st.dataframe(df.head(10))

    # Bộ lọc theo city và retail_chain
    city_options = ['Tất cả'] + sorted(df['city'].dropna().unique().tolist())
    retail_options = ['Tất cả'] + sorted(df['retail_chain'].dropna().unique().tolist())
    
    selected_city = st.selectbox("Chọn thành phố:", options=city_options, key="retail_city_filter")
    selected_retail = st.selectbox("Chọn retail_chain:", options=retail_options, key="retail_filter_retail")
    
    filtered_df = df.copy()
    if selected_city != "Tất cả":
        filtered_df = filtered_df[filtered_df['city'] == selected_city]
    if selected_retail != "Tất cả":
        filtered_df = filtered_df[filtered_df['retail_chain'] == selected_retail]
    
    st.write(f"### Dữ liệu đã lọc (số dòng: {filtered_df.shape[0]}):")
    st.dataframe(filtered_df[['id', 'retail_chain', 'name', 'address', 'city', 'latitude', 'longitude']])
    
    # Phân tích dữ liệu tọa độ (không loại bỏ dòng có NaN để hiển thị bảng)
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

    # Khi hiển thị bản đồ, chỉ sử dụng các dòng có tọa độ hợp lệ
    map_df = filtered_df.dropna(subset=["latitude", "longitude"])
    
    if "map_visible_retail" not in st.session_state:
        st.session_state.map_visible_retail = False
    if st.button("Hiển thị/Ẩn bản đồ Cơ sở bán lẻ", key="toggle_map_retail"):
        st.session_state.map_visible_retail = not st.session_state.map_visible_retail

    if st.session_state.map_visible_retail:
        if not MAP4D_API_KEY:
            st.warning("⚠️ Vui lòng cấu hình MAP4D_API_KEY trong phần Secrets của Streamlit")
        else:
            render_map4d(map_df, api_key=MAP4D_API_KEY, map_id=MAP4D_MAP_ID)

if __name__ == "__main__":
    main()
