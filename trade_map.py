#C:/Users/Dell/input.csv
    
import pandas as pd
import matplotlib.pyplot as plt

def extract_plant_type(name):
    """
    Hàm tách loại hình nhà máy điện từ tên nhà máy.
    Dựa vào các từ khóa: "mặt trời", "gió", "thủy".
    Nếu không khớp, trả về "Khác".
    """
    name_lower = name.lower()
    if "mặt trời" in name_lower:
        return "Điện mặt trời"
    elif "gió" in name_lower:
        return "Điện gió"
    elif "Thủy" in name_lower:
        return "Thủy điện"
    else:
        return "Khác"

def main():
    # Đường dẫn tới file CSV (đảm bảo file này có dấu tab làm phân cách)
    file_path = 'C:/Users/Dell/input.csv'
    
    try:
        df = pd.read_csv(file_path, sep='\t')
    except Exception as e:
        print("Lỗi khi đọc file CSV:", e)
        return

    print("Số dòng ban đầu:", df.shape[0])
    
    # Kiểm tra cột 'latlng'
    if 'latlng' not in df.columns:
        print("Không tìm thấy cột 'latlng' trong dữ liệu!")
        return
    
    # Loại bỏ các dòng thiếu giá trị ở cột latlng
    df = df.dropna(subset=['latlng'])
    
    # Tách cột latlng thành 2 cột: lat và lon (loại bỏ dấu ngoặc kép nếu có)
    try:
        df[['lat', 'lon']] = df['latlng'].str.replace('\"', '').str.split(',', expand=True)
    except Exception as e:
        print("Lỗi khi tách cột 'latlng':", e)
        return

    # Chuyển đổi lat và lon sang kiểu số thực
    df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
    df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
    df = df.dropna(subset=['lat', 'lon'])
    
    # Đổi tên cột chứa tên nhà máy từ 'Column1' thành 'plant_name'
    if 'Column1' in df.columns:
        df.rename(columns={'Column1': 'plant_name'}, inplace=True)
    else:
        print("Không tìm thấy cột 'Column1' chứa tên nhà máy!")
        return

    print("Số dòng sau xử lý:", df.shape[0])
    print("\nMột vài dòng dữ liệu sau xử lý:")
    print(df.head(), "\n")
    
    # Phân loại loại hình nhà máy dựa trên tên (theo từ khóa)
    df['plant_type'] = df['type'].apply(extract_plant_type)
    
    print("Phân loại loại hình nhà máy:")
    print(df[['plant_name', 'plant_type']].head(10), "\n")
    
    # Đếm số lượng nhà máy theo loại hình
    type_counts = df['plant_type'].value_counts()
    print("Số lượng nhà máy theo loại hình:")
    print(type_counts)
    
    # ----------------- Vẽ biểu đồ -----------------
    
    # Biểu đồ cột (bar chart)
    plt.figure(figsize=(8,6))
    plt.bar(type_counts.index, type_counts.values, color='skyblue')
    plt.xlabel("Loại hình nhà máy")
    plt.ylabel("Số lượng")
    plt.title("Số lượng nhà máy theo loại hình")
    plt.tight_layout()
    plt.savefig("bar_chart_plant_type.png")
    plt.show()
    
    # Biểu đồ tròn (pie chart)
    plt.figure(figsize=(8,8))
    plt.pie(type_counts.values, labels=type_counts.index, autopct='%1.1f%%', startangle=140)
    plt.title("Tỉ lệ phần trăm nhà máy theo loại hình")
    plt.tight_layout()
    plt.savefig("pie_chart_plant_type.png")
    plt.show()

if __name__ == "__main__":
    main()
