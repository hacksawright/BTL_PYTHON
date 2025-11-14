df = pd.read_sql_query("SELECT * FROM premier_league_2024_2025",conn)
# conn.close()
# # giữ lại các cột định dang là số
# numberic_df = df.select_dtypes(include=np.number)
# # phần này sẽ lấy ra các cột có trùng team và tính trung bình mean ,trung vị median, độ lệch chuẩn std 
# team_stats = df.groupby("Squad")[numberic_df.columns].agg(['mean','median','std']).reset_index()
# # in ra file csv
# team_stats.to_csv("team_statis.csv",index=False)
# print("Đã ghi kết quả xog")