import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, time

DATA_FILE = "tugas_kuliah.json"

# Kamus Nama Bulan Indonesia
BULAN_INDO = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember"
}

# Fungsi format datetime ke string Indonesia lengkap jam (Contoh: "13 Oktober 2026, 23:59")
def format_datetime_indo(dt_obj):
    if isinstance(dt_obj, str):
        try:
            dt_obj = datetime.strptime(dt_obj, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                dt_obj = datetime.strptime(dt_obj, "%Y-%m-%d")
            except ValueError:
                return dt_obj
    return f"{dt_obj.day} {BULAN_INDO[dt_obj.month]} {dt_obj.year}, pukul {dt_obj.strftime('%H:%M')}"

# Load Data JSON
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

# Save Data JSON
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Inisialisasi State
if "tugas_list" not in st.session_state:
    st.session_state.tugas_list = load_data()

st.set_page_config(page_title="Manajemen Tugas Kuliah", page_icon="🎓", layout="wide")

# Header Utama
st.title("🎓 Portal Tugas & Jadwal Kuliah")
st.caption("Kelola tugas perkuliahan, pantau deadline, dan langsung kumpulkan via link terkait.")
st.markdown("---")

# --- SIDEBAR: FORM TAMBAH / EDIT ---
st.sidebar.header("📝 Kelola Tugas")

options_list = ["+ Tambah Tugas Baru"] + [
    f"{t['id']} - {t['mata_kuliah']}: {t['nama_tugas']}" 
    for t in st.session_state.tugas_list if not t.get('selesai', False)
]

edit_choice = st.sidebar.selectbox(
    "Pilih Mode / Tugas",
    options=options_list
)

default_matkul = ""
default_tugas = ""
default_link = ""
default_tenggat_date = datetime.now().date()
default_tenggat_time = time(23, 59)
is_editing = False
target_id = None

if edit_choice != "+ Tambah Tugas Baru":
    is_editing = True
    target_id = int(edit_choice.split(" - ")[0])
    target_item = next((item for item in st.session_state.tugas_list if item["id"] == target_id), None)
    if target_item:
        default_matkul = target_item.get("mata_kuliah", "")
        default_tugas = target_item.get("nama_tugas", "")
        default_link = target_item.get("link_pengumpulan", "")
        try:
            dt_parsed = datetime.strptime(target_item["tenggat"], "%Y-%m-%d %H:%M")
            default_tenggat_date = dt_parsed.date()
            default_tenggat_time = dt_parsed.time()
        except Exception:
            try:
                dt_parsed = datetime.strptime(target_item["tenggat"], "%Y-%m-%d")
                default_tenggat_date = dt_parsed.date()
            except Exception:
                pass

with st.sidebar.form("form_tugas", clear_on_submit=True):
    st.subheader("Edit Detail" if is_editing else "Tambah Tugas Baru")
    matkul = st.text_input("Mata Kuliah", value=default_matkul, placeholder="Contoh: Kalkulus / Pemrograman")
    nama_tugas = st.text_area("Deskripsi / Nama Tugas", value=default_tugas, placeholder="Contoh: Kerjakan Latihan Bab 3")
    link_pengumpulan = st.text_input("Link Pengumpulan (Opsional)", value=default_link, placeholder="https://classroom.google.com/...")
    
    col_date, col_time = st.columns(2)
    with col_date:
        tenggat_date = st.date_input("Tanggal Tenggat", value=default_tenggat_date)
    with col_time:
        tenggat_time = st.time_input("Jam Tenggat", value=default_tenggat_time)
        
    submit_button = st.form_submit_button(
        label="💾 Simpan Perubahan" if is_editing else "➕ Tambah ke Daftar", 
        use_container_width=True
    )

    if submit_button:
        if matkul.strip() and nama_tugas.strip():
            tenggat_full_str = f"{tenggat_date} {tenggat_time.strftime('%H:%M')}"
            
            # Format link agar berawalan http:// atau https:// jika diisi
            link_clean = link_pengumpulan.strip()
            if link_clean and not (link_clean.startswith("http://") or link_clean.startswith("https://")):
                link_clean = "https://" + link_clean

            if is_editing:
                for t in st.session_state.tugas_list:
                    if t["id"] == target_id:
                        t["mata_kuliah"] = matkul
                        t["nama_tugas"] = nama_tugas
                        t["link_pengumpulan"] = link_clean
                        t["tenggat"] = tenggat_full_str
                st.sidebar.success("Tugas berhasil diperbarui!")
            else:
                new_id = max([t["id"] for t in st.session_state.tugas_list], default=0) + 1
                st.session_state.tugas_list.append({
                    "id": new_id,
                    "mata_kuliah": matkul,
                    "nama_tugas": nama_tugas,
                    "link_pengumpulan": link_clean,
                    "tenggat": tenggat_full_str,
                    "selesai": False,
                    "tanggal_selesai": "-"
                })
                st.sidebar.success("Tugas baru berhasil disimpan!")
            
            save_data(st.session_state.tugas_list)
            st.rerun()
        else:
            st.sidebar.error("Mata Kuliah dan Deskripsi Tugas wajib diisi!")

# --- TAB UTAMA ---
tab1, tab2 = st.tabs(["📌 Daftar Tugas Aktif", "📜 Riwayat Tugas Selesai"])

# --- TAB 1: TUGAS AKTIF ---
with tab1:
    tugas_aktif = [t for t in st.session_state.tugas_list if not t.get("selesai", False)]
    
    if not tugas_aktif:
        st.success("🎉 Tidak ada tugas aktif. Semua tugas sudah selesai!")
    else:
        now = datetime.now()
        
        for t in tugas_aktif:
            try:
                tenggat_dt = datetime.strptime(t["tenggat"], "%Y-%m-%d %H:%M")
            except ValueError:
                tenggat_dt = datetime.strptime(t["tenggat"], "%Y-%m-%d").replace(hour=23, minute=59)
            
            selisih = tenggat_dt - now
            sisa_detik = selisih.total_seconds()
            tenggat_indo = format_datetime_indo(tenggat_dt)
            link_url = t.get("link_pengumpulan", "")
            
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 3, 2])
                
                with col1:
                    st.markdown(f"### 📖 {t['mata_kuliah']}")
                    st.write(t["nama_tugas"])
                    if link_url:
                        st.link_button("🔗 Buka Link Pengumpulan", link_url, use_container_width=False)
                
                with col2:
                    st.write("⏳ **Deadline:**")
                    st.markdown(f"**{tenggat_indo}**")
                    
                    if sisa_detik < 0:
                        st.caption("🔴 *Terlewat deadline!*")
                    else:
                        sisa_hari = selisih.days
                        sisa_jam = selisih.seconds // 3600
                        sisa_menit = (selisih.seconds % 3600) // 60
                        
                        if sisa_hari == 0:
                            if sisa_jam == 0:
                                st.caption(f"🚨 *Mendesak! Sisa {sisa_menit} menit lagi!*")
                            else:
                                st.caption(f"🚨 *Hari ini! Sisa {sisa_jam} jam {sisa_menit} menit lagi!*")
                        elif sisa_hari <= 3:
                            st.caption(f"🟡 *Sisa {sisa_hari} hari {sisa_jam} jam lagi*")
                        else:
                            st.caption(f"🟢 *Sisa {sisa_hari} hari lagi*")
                
                with col3:
                    st.write("")
                    if st.button("✅ Selesai Dikerjakan", key=f"done_{t['id']}", use_container_width=True):
                        t["selesai"] = True
                        now_dt = datetime.now()
                        waktu_selesai_indo = format_datetime_indo(now_dt)
                        t["tanggal_selesai"] = waktu_selesai_indo
                        save_data(st.session_state.tugas_list)
                        st.toast(f"Mantap! Tugas '{t['nama_tugas']}' selesai!")
                        st.rerun()

# --- TAB 2: RIWAYAT SELESAI ---
with tab2:
    tugas_selesai = [t for t in st.session_state.tugas_list if t.get("selesai", False)]
    
    if not tugas_selesai:
        st.info("Belum ada riwayat tugas yang diselesaikan.")
    else:
        for t in tugas_selesai:
            t["tenggat_formatted"] = format_datetime_indo(t["tenggat"])
            t["link_display"] = t.get("link_pengumpulan", "-") if t.get("link_pengumpulan") else "-"
            
        df_history = pd.DataFrame(tugas_selesai)
        df_history = df_history[["mata_kuliah", "nama_tugas", "link_display", "tenggat_formatted", "tanggal_selesai"]]
        df_history.columns = ["Mata Kuliah", "Nama Tugas", "Link Pengumpulan", "Tenggat Waktu", "Waktu Diselesaikan"]
        
        st.dataframe(
            df_history, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Link Pengumpulan": st.column_config.LinkColumn(
                    "Link Pengumpulan",
                    display_text="Buka Link"
                )
            }
        )

        st.markdown("---")
        if st.button("🗑️ Hapus Semua Riwayat", type="secondary"):
            st.session_state.tugas_list = [t for t in st.session_state.tugas_list if not t.get("selesai", False)]
            save_data(st.session_state.tugas_list)
            st.rerun()