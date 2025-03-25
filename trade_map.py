import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def extract_plant_type(name):
    name_lower = name.lower()
    if "mặt trời" in name_lower:
        return "Điện mặt trời"
    elif "gió" in name_lower:
        return "Điện gió"
    elif "thủy" in name_lower:
        return "Thủy điện"
    else:
        return "Khác"

def main():
    st.set_page_config(page_title="Thống kê nhà máy điện", layout="wide")
    st.title("📊 Thống kê Nhà máy điện từ File CSV")

    file_path = 'C:/Users/Dell/input.csv'

    try:
        df = pd.read_csv(file_path, sep='\t')
        st.success(f"✅ Đọc thành công dữ liệu từ: `{file_path}`")
    except Exception as e:
        st.error(f"❌ Lỗi khi đọc file CSV: {e}")
        return

    if 'latlng' not in df.columns:
        st.error("❌ Không tìm thấy cột `latlng` trong dữ liệu!")
        return

    df = df.dropna(subset=['latlng'])

    try:
        df[['lat', 'lon']] = df['latlng'].str.replace('"', '').str.split(',', expand=True)
    except Exception as e:
        st.error(f"❌ Lỗi khi tách cột 'latlng': {e}")
        return

    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    df = df.dropna(subset=['lat', 'lon'])

    if 'Column1' in df.columns:
        df.rename(columns={'Column1': 'plant_name'}, inplace=True)
    else:
        st.error("❌ Không tìm thấy cột `Column1` chứa tên nhà máy!")
        return

    # Phân loại
    df['plant_type'] = df['type'].apply(extract_plant_type)

    st.markdown("### 📌 Một vài dòng dữ liệu đã xử lý:")
    st.dataframe(df[['plant_name', 'type', 'plant_type', 'lat', 'lon']].head(10))

    # Thống kê
    type_counts = df['plant_type'].value_counts()

    st.markdown("### 📊 Số lượng nhà máy theo loại hình:")
    st.dataframe(type_counts.rename("Số lượng"))

    # Biểu đồ cột
    st.markdown("### 📈 Biểu đồ cột: Số lượng nhà máy")
    fig1, ax1 = plt.subplots()
    ax1.bar(type_counts.index, type_counts.values, color='skyblue')
    ax1.set_xlabel("Loại hình nhà máy")
    ax1.set_ylabel("Số lượng")
    ax1.set_title("Số lượng nhà máy theo loại hình")
    st.pyplot(fig1)

    # Biểu đồ tròn
    st.markdown("### 🥧 Biểu đồ tròn: Tỷ lệ nhà máy")
    fig2, ax2 = plt.subplots()
    ax2.pie(type_counts.values, labels=type_counts.index, autopct='%1.1f%%', startangle=140)
    ax2.set_title("Tỉ lệ phần trăm nhà máy theo loại hình")
    st.pyplot(fig2)

if __name__ == "__main__":
    main()
