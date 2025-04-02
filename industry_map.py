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
        try:
            lat = float(row['latitude'])
            lng = float(row['longitude'])
        except Exception:
            continue

        # Nếu một id có nhiều địa chỉ, vẫn vẽ marker với tên lấy từ cột 'name'
        marker_js += f"""
        new map4d.Marker({{
            position: {{ lat: {lat}, lng: {lng} }},
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
        st.set_page_config(page_title="Bản đồ Khu công nghiệp", layout="wide")
    st.title("🏭 Bản đồ Khu công nghiệp")

    # Đọc file CSV chứa dữ liệu KCN
    file_path = os.path.join(os.path.dirname(__file__), "kcn.csv")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        st.error(f"❌ Lỗi khi đọc file CSV: {e}")
        return

    st.write("### Dữ liệu gốc:")
    st.dataframe(df.head(10))

    # Bộ lọc theo city và investor (nếu muốn)
    city_options = ['Tất cả'] + sorted(df['city'].dropna().unique().tolist())
    investor_options = ['Tất cả'] + sorted(df['investor'].dropna().unique().tolist())

    selected_city = st.selectbox("Chọn thành phố:", options=city_options, key="city_filter")
    selected_investor = st.selectbox("Chọn investor:", options=investor_options, key="investor_filter")

    filtered_df = df.copy()
    if selected_city != "Tất cả":
        filtered_df = filtered_df[filtered_df['city'] == selected_city]
    if selected_investor != "Tất cả":
        filtered_df = filtered_df[filtered_df['investor'] == selected_investor]

    st.write(f"### Dữ liệu đã lọc (số dòng: {filtered_df.shape[0]}):")
    st.dataframe(filtered_df[['id', 'name', 'address', 'city', 'latitude', 'longitude']])

    # Khi hiển thị bản đồ, chỉ sử dụng các dòng có tọa độ hợp lệ
    map_df = filtered_df.dropna(subset=["latitude", "longitude"])

    if "map_visible_industry" not in st.session_state:
        st.session_state.map_visible_industry = False
    if st.button("Hiển thị/Ẩn bản đồ KCN", key="toggle_map_industry"):
        st.session_state.map_visible_industry = not st.session_state.map_visible_industry

    if st.session_state.map_visible_industry:
        if not MAP4D_API_KEY:
            st.warning("⚠️ Vui lòng cấu hình MAP4D_API_KEY trong phần Secrets của Streamlit")
        else:
            render_map4d(map_df, api_key=MAP4D_API_KEY, map_id=MAP4D_MAP_ID)

if __name__ == "__main__":
    main()
