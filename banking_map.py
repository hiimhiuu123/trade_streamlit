import streamlit as st
import pandas as pd
import os

# Sử dụng st.secrets nếu deploy trên Streamlit Cloud; nếu không, sử dụng os.getenv()
MAP4D_API_KEY = st.secrets.get("MAP4D_API_KEY") or os.getenv("MAP4D_API_KEY")
MAP4D_MAP_ID = st.secrets.get("MAP4D_MAP_ID") or os.getenv("MAP4D_MAP_ID", "")

def render_map4d(df, api_key, map_id=""):
    """
    Hiển thị bản đồ Map4D sử dụng template map4d_template.html.
    Template cần có các placeholder: ##MARKERS_PLACEHOLDER##, __API_KEY__, __MAP_ID__.
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
    # Chỉ gọi st.set_page_config nếu file được chạy độc lập
    if __name__ == "__main__":
        st.set_page_config(page_title="Bản đồ Cơ sở Ngân hàng", layout="wide")
    
    st.title("🏦 Bản đồ Cơ sở Ngân hàng")
    
    file_path = os.path.join(os.path.dirname(__file__), "banking_data.csv")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        st.error(f"❌ Lỗi khi đọc file CSV: {e}")
        return

    # Nếu cột 'name' trống, thay thế bằng bank_name + address
    df['name'] = df.apply(
        lambda row: f"{row['bank_name']} {row['address']}"
                    if (pd.isna(row['name']) or str(row['name']).strip() == "")
                    else row['name'],
        axis=1
    )

    st.write("### Dữ liệu gốc:")
    st.dataframe(df.head(10))

    # Bộ lọc theo city và bank
    city_options = ['Tất cả'] + sorted(df['city'].dropna().unique().tolist())
    bank_options = ['Tất cả'] + sorted(df['bank'].dropna().unique().tolist())
    
    selected_city = st.selectbox("Chọn thành phố:", options=city_options, key="bank_city_filter")
    selected_bank = st.selectbox("Chọn ngân hàng:", options=bank_options, key="bank_filter")
    
    filtered_df = df.copy()
    if selected_city != "Tất cả":
        filtered_df = filtered_df[filtered_df['city'] == selected_city]
    if selected_bank != "Tất cả":
        filtered_df = filtered_df[filtered_df['bank'] == selected_bank]
    
    st.write(f"### Dữ liệu đã lọc (số dòng: {filtered_df.shape[0]}):")
    st.dataframe(filtered_df[['id', 'bank', 'bank_name', 'name', 'city', 'latitude', 'longitude']])
    
    # Phân tích dữ liệu tọa độ
    with st.expander("Phân tích dữ liệu tọa độ"):
        total_rows = filtered_df.shape[0]
        # Xác định các dòng có tọa độ không hợp lệ (NaN)
        missing_coords = filtered_df[filtered_df['latitude'].isna() | filtered_df['longitude'].isna()]
        missing_count = missing_coords.shape[0]
        valid_count = total_rows - missing_count
        st.write(f"Tổng số dòng sau lọc: {total_rows}")
        st.write(f"Số dòng có tọa độ hợp lệ: {valid_count}")
        st.write(f"Số dòng thiếu tọa độ: {missing_count} ({(missing_count/total_rows*100):.2f}%)")
        
        # Phân tích theo thành phố
        missing_by_city = missing_coords.groupby('city').size().reset_index(name='missing_count')
        st.write("Số dòng thiếu tọa độ theo thành phố:")
        st.dataframe(missing_by_city)
        
        # Phân tích theo ngân hàng
        missing_by_bank = missing_coords.groupby('bank').size().reset_index(name='missing_count')
        st.write("Số dòng thiếu tọa độ theo ngân hàng:")
        st.dataframe(missing_by_bank)
    
    # Khi hiển thị bản đồ, chỉ sử dụng các dòng có tọa độ hợp lệ
    map_df = filtered_df.dropna(subset=["latitude", "longitude"])
    
    if "map_visible_bank" not in st.session_state:
        st.session_state.map_visible_bank = False
    if st.button("Hiển thị/Ẩn bản đồ Cơ sở Ngân hàng", key="toggle_map_bank"):
        st.session_state.map_visible_bank = not st.session_state.map_visible_bank
    
    if st.session_state.map_visible_bank:
        if not MAP4D_API_KEY:
            st.warning("⚠️ Vui lòng cấu hình MAP4D_API_KEY trong phần Secrets của Streamlit")
        else:
            render_map4d(map_df, api_key=MAP4D_API_KEY, map_id=MAP4D_MAP_ID)

if __name__ == "__main__":
    main()
