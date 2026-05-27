#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov  6 20:50:24 2025
📋 Ứng dụng Quản lý Công việc (QLCV)
@author: trieukimlanh
streamlit run "/Users/trieukimlanh/Library/CloudStorage/GoogleDrive-lanhtk@hub.edu.vn/My Drive/Spyder/app_QLCV/app_QLCV.py"
"""

import streamlit as st
import pandas as pd
import re
import io   # 👈 thêm dòng này
import matplotlib.pyplot as plt

# ==========================================================
# ⚙️ CẤU HÌNH
# ==========================================================
st.set_page_config(page_title="📋 Ứng dụng QLCV", layout="wide")
st.title("📋 Ứng dụng Quản lý Công việc")
st.write("Tổng hợp dữ liệu công việc từ nhiều bảng (df1_year-term-code; df2_category-description; GD_giảng dạy; NCKH_nghiên cứu; Other_khác)")

# ==========================================================
# 🧩 HÀM ĐỌC GOOGLE SHEET
# ==========================================================
def read_gsheet(link):
    try:
        base_id = link.split("/d/")[1].split("/")[0]
        gid = link.split("gid=")[-1].split("#")[0] if "gid=" in link else "0"
        url = f"https://docs.google.com/spreadsheets/d/{base_id}/export?format=csv&gid={gid}"
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"❌ Lỗi đọc Google Sheet: {e}")
        return None

# ==========================================================
# 🔗 CÁC LINK DỮ LIỆU
# ==========================================================
links = {
    "df1": "https://docs.google.com/spreadsheets/d/1-2LRE_94U5occybvmD5xDjDiA8Yn5tp-PvvSExg4GnU/export?format=csv&gid=2080729380",
    "df2": "https://docs.google.com/spreadsheets/d/1-2LRE_94U5occybvmD5xDjDiA8Yn5tp-PvvSExg4GnU/export?format=csv&gid=0",
    "GD": "https://docs.google.com/spreadsheets/d/1-2LRE_94U5occybvmD5xDjDiA8Yn5tp-PvvSExg4GnU/export?format=csv&gid=1431418978",
    "NCKH": "https://docs.google.com/spreadsheets/d/1-2LRE_94U5occybvmD5xDjDiA8Yn5tp-PvvSExg4GnU/export?format=csv&gid=110203336",
    "Other": "https://docs.google.com/spreadsheets/d/1-2LRE_94U5occybvmD5xDjDiA8Yn5tp-PvvSExg4GnU/export?format=csv&gid=1443108898",
}

# ==========================================================
# 🧮 TẢI DỮ LIỆU CƠ BẢN
# ==========================================================
st.header("📂 Dữ liệu mô tả (df1 & df2)")

col1, col2 = st.columns(2)

with col1:
    df1 = read_gsheet(links["df1"])
    if df1 is not None:
        st.session_state["df1"] = df1
        st.success("✅ Đã tải df1 (Year - Term - Code)!")
        st.dataframe(df1, height=180, use_container_width=True)

with col2:
    df2 = read_gsheet(links["df2"])
    if df2 is not None:
        st.session_state["df2"] = df2
        st.success("✅ Đã tải df2 (Category - Description)!")
        st.dataframe(df2, height=180, use_container_width=True)

# ==========================================================
# 📚 TẢI DỮ LIỆU CHI TIẾT
# ==========================================================
st.header("📘 Các nhóm công việc chi tiết")
detail_dfs = {}

for key in ["GD", "NCKH", "Other"]:
    df = read_gsheet(links[key])
    if df is not None:
        detail_dfs[key] = df
        st.success(f"✅ Đã tải {key}")
        st.dataframe(df, height=180, use_container_width=True)

st.session_state["detail_dfs"] = detail_dfs

# ==========================================================
# 🔍 TRA CỨU CÔNG VIỆC (tối ưu lọc nhiều từ khóa)
# ==========================================================
st.header("🔍 Tra cứu công việc nâng cao")

keyword_input = st.text_input(
    "🔎 Nhập từ khóa cần tìm (hỗ trợ nhiều điều kiện, ngăn cách bằng & hoặc ,)\n"
    "Ví dụ: hk1 & 2526.D1 & 2526.D2"
).strip().lower()

df1 = st.session_state.get("df1")
df2 = st.session_state.get("df2")
detail_dfs = st.session_state.get("detail_dfs", {})

if keyword_input:
    if df1 is None or df1.empty or df2 is None or df2.empty or not detail_dfs:
        st.warning("⚠️ Vui lòng đảm bảo đã tải đủ df1, df2 và các bảng công việc.")
    else:
        # --- Tách và làm sạch từ khóa ---
        keywords = [k.strip() for k in re.split(r"[&,]", keyword_input) if k.strip()]
        st.info(f"🔍 Đang tìm theo {len(keywords)} điều kiện: **{', '.join(keywords)}**")

        found_records = []

        for name, df in detail_dfs.items():
            df.columns = [c.strip() for c in df.columns]
            df_temp = df.copy()
            df_str = df_temp.astype(str).apply(lambda c: c.str.lower())

            # --- Lọc theo nhiều từ khóa trên các cột văn bản liên quan ---
            text_cols = [
                c for c in df_temp.columns
                if any(x in c.lower() for x in [
                    "category", "term", "đợt kê khai", "code",
                    "work", "subject", "tên sản phẩm", "program",
                    "loại hoạt động", "phân loại", "vai trò", "cấp độ"
                ])
            ]
            
            if text_cols:
                mask = pd.Series(True, index=df_temp.index)
                for kw in keywords:
                    mask_kw = df_temp[text_cols].apply(
                        lambda col: col.astype(str).str.lower().str.contains(kw, na=False)
                    ).any(axis=1)
                    mask &= mask_kw
            else:
                mask = pd.Series(False, index=df_temp.index)

            match_df = df_temp[mask]

            # --- Gộp thêm thông tin mô tả từ df1 và df2 ---
            if not match_df.empty:
                if "code" in match_df.columns and "code" in df1.columns:
                    match_df = match_df.merge(df1.drop_duplicates(subset=["code"]), on="code", how="left")
                if "category" in match_df.columns and "category" in df2.columns:
                    match_df = match_df.merge(df2.drop_duplicates(subset=["category"]), on="category", how="left")

                match_df = match_df.drop_duplicates()
                found_records.append((name, match_df))

        # ==========================================================
        # 📋 HIỂN THỊ KẾT QUẢ + THỐNG KÊ
        # ==========================================================
        if found_records:
            st.success(f"✅ Tìm thấy kết quả phù hợp với {len(keywords)} điều kiện")
            import matplotlib.pyplot as plt

            for name, rec_df in found_records:
                st.markdown(f"### 📘 Nhóm công việc: **{name}** — {len(rec_df)} dòng")

                display_cols = [c for c in [
                    "category", "term", "code", "work", "subject",
                    "Tên sản phẩm", "Đợt kê khai", "deadline",
                    "period", "SỐ TIẾT KÊ KHAI"
                ] if c in rec_df.columns]

                st.dataframe(
                    rec_df[display_cols + [c for c in rec_df.columns if c not in display_cols]],
                    use_container_width=True
                )

                # ======================================================
                # 📊 Thống kê nhanh
                # ======================================================
                with st.expander("📊 Thống kê nhanh", expanded=True):
                    summary = []
                    if name.upper().startswith("GD"):
                        period_col = next((c for c in rec_df.columns if c.lower() == "period"), None)
                        subj_col = next((c for c in rec_df.columns if "subject" in c.lower()), None)
                        if period_col and subj_col:
                            total_period = rec_df[period_col].apply(pd.to_numeric, errors="coerce").sum()
                            total_classes = len(rec_df)
                            total_subjects = rec_df[subj_col].nunique()
                            summary.append(f"**Tổng tiết:** {total_period:,.0f}")
                            summary.append(f"**Tổng lớp:** {total_classes:,}")
                            summary.append(f"**Tổng môn:** {total_subjects:,}")
                    elif name.upper().startswith("NCKH"):
                        tiet_col = next((c for c in rec_df.columns if "tiết" in c.lower()), None)
                        if tiet_col:
                            total_tiet = rec_df[tiet_col].apply(pd.to_numeric, errors="coerce").sum()
                            summary.append(f"**Tổng số tiết kê khai:** {total_tiet:,.0f}")
                    else:
                        summary.append(f"**Tổng số công việc:** {len(rec_df)}")
                    if summary:
                        st.markdown("<br>".join(summary), unsafe_allow_html=True)

                # ======================================================
                # 📈 Nếu là NCKH: vẽ đồ thị + bảng tổng
                # ======================================================
                if name.upper().startswith("NCKH") and \
                   "Đợt kê khai" in rec_df.columns and "SỐ TIẾT KÊ KHAI" in rec_df.columns:

                    st.markdown("#### 📆 Thống kê tổng tiết kê khai theo đợt và năm")

                    df_nckh = rec_df.copy()
                    df_nckh["SỐ TIẾT KÊ KHAI"] = pd.to_numeric(
                        df_nckh["SỐ TIẾT KÊ KHAI"], errors="coerce"
                    ).fillna(0)

                    # --- Tổng theo đợt kê khai ---
                    df_dot = (
                        df_nckh.groupby("Đợt kê khai")["SỐ TIẾT KÊ KHAI"]
                        .sum()
                        .reset_index()
                        .sort_values("Đợt kê khai")
                    )
                    total_dot = df_dot["SỐ TIẾT KÊ KHAI"].sum()
                    df_dot.loc[len(df_dot)] = ["**Tổng cộng**", total_dot]
                    st.markdown("**📋 Tổng tiết theo đợt kê khai**")
                    st.dataframe(df_dot, use_container_width=True)

                    # --- Tổng theo năm ---
                    df_nckh["Năm"] = df_nckh["Đợt kê khai"].astype(str).str.extract(r"(^\d{4})")
                    df_year = (
                        df_nckh.groupby("Năm")["SỐ TIẾT KÊ KHAI"]
                        .sum()
                        .reset_index()
                        .sort_values("Năm")
                    )
                    total_year = df_year["SỐ TIẾT KÊ KHAI"].sum()
                    df_year.loc[len(df_year)] = ["**Tổng cộng**", total_year]
                    st.markdown("**📅 Tổng tiết theo năm**")
                    st.dataframe(df_year, use_container_width=True)

                    # --- Vẽ biểu đồ (loại bỏ dòng Tổng cộng) ---
                    df_plot = df_year[df_year["Năm"] != "**Tổng cộng**"]
                    if not df_plot.empty:
                        fig, ax = plt.subplots(figsize=(6, 3))
                        bars = ax.bar(df_plot["Năm"], df_plot["SỐ TIẾT KÊ KHAI"], color="#4C72B0")

                        for bar in bars:
                            height = bar.get_height()
                            ax.text(
                                bar.get_x() + bar.get_width() / 2,
                                height,
                                f"{int(height)}",
                                ha="center",
                                va="bottom",
                                fontsize=8,
                                fontweight="bold",
                            )

                        ax.set_xlabel("Năm", fontsize=9)
                        ax.set_ylabel("Tổng số tiết kê khai", fontsize=9)
                        ax.set_title("Tổng tiết NCKH theo năm", fontsize=11, fontweight="bold")
                        ax.tick_params(axis="x", rotation=45)

                        col1, col2, col3 = st.columns([2, 7, 2])
                        with col2:
                            st.pyplot(fig, bbox_inches="tight")
        else:
            st.warning("❌ Không tìm thấy dữ liệu phù hợp.")
else:
    st.info("👆 Nhập từ khóa (có thể nhiều điều kiện nối bằng & hoặc ,) để bắt đầu.")



# ==========================================================
# 📊 BIỂU ĐỒ THỐNG KÊ TỔNG HỢP KẾT QUẢ TÌM KIẾM
# ==========================================================
import matplotlib.pyplot as plt

# 👇 Thêm đoạn này để tránh lỗi rec_df chưa định nghĩa
if 'found_records' in locals() and found_records:
    rec_df = found_records[-1][1]
else:
    rec_df = pd.DataFrame()  # tạo DataFrame trống để code phía dưới không lỗi

# --- Nhận diện các cột ---
subject_col = next((c for c in rec_df.columns if c.lower() in ["subject", "môn học"]), None)
short_col = next((c for c in rec_df.columns if "short" in c.lower()), None)
class_col = next((c for c in rec_df.columns if "class" in c.lower()), None)
period_col = next((c for c in rec_df.columns if "period" in c.lower() or "tiết" in c.lower()), None)
year_col = next((c for c in rec_df.columns if "year" in c.lower()), None)

# ==========================================================
# 📈 BIỂU ĐỒ 1 — TỔNG SỐ LỚP THEO MÔN HỌC
# ==========================================================
if not rec_df.empty and (subject_col or short_col):
    st.markdown("#### 📈 Thống kê tổng số lớp theo môn học (tổng hợp kết quả tìm kiếm)")

    # Ưu tiên dùng short_name nếu có
    group_col = short_col if short_col else subject_col

    df_chart = (
        rec_df.groupby(group_col)
        .size()
        .reset_index(name="Tổng số lớp")
        .sort_values("Tổng số lớp", ascending=False)
    )

    fig, ax = plt.subplots(figsize=(7, 3))
    bars = ax.bar(df_chart[group_col], df_chart["Tổng số lớp"])

    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{int(height)}",
            ha="center",
            va="bottom",
            fontsize=7,
            fontweight="bold",
        )

    ax.set_xlabel("Tên môn học", fontsize=8)
    ax.set_ylabel("Tổng số lớp", fontsize=8)
    ax.set_title("Tổng số lớp theo môn học", fontsize=10, fontweight="bold")
    ax.tick_params(axis="x", rotation=45)
    col1, col2, col3 = st.columns([2, 7, 2])
    with col2:
        st.pyplot(fig, bbox_inches="tight")

# ==========================================================
# 📊 BIỂU ĐỒ 2 — TỔNG SỐ TIẾT THEO NĂM HỌC
# ==========================================================
if year_col and period_col and not rec_df[year_col].isna().all():
    st.markdown("#### 📊 Thống kê tổng số tiết theo năm học")

    df_year = (
        rec_df.groupby(year_col)[period_col]
        .sum()
        .reset_index()
        .sort_values(year_col)
    )

    st.dataframe(df_year, use_container_width=True)

    fig2, ax2 = plt.subplots(figsize=(6, 3))
    bars2 = ax2.bar(df_year[year_col], df_year[period_col])

    for bar in bars2:
        height = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{int(height)}",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    ax2.set_xlabel("Năm học", fontsize=8)
    ax2.set_ylabel("Tổng số tiết", fontsize=8)
    ax2.set_title("Tổng tiết theo năm học", fontsize=10, fontweight="bold")
    ax2.tick_params(axis="x", rotation=45)
    col1, col2, col3 = st.columns([2, 7, 2])
    with col2:
        st.pyplot(fig2, bbox_inches="tight")

