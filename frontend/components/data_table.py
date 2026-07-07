"""
Data Table Component
====================
Tabel data dengan search, pagination, dan action buttons.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional, Callable


def render_data_table(
    data: List[Dict[str, Any]],
    columns: Optional[Dict[str, str]] = None,
    key: str = "table",
    show_index: bool = False,
    on_edit: Optional[Callable[[Dict], None]] = None,
    on_delete: Optional[Callable[[str], None]] = None,
    on_view: Optional[Callable[[str], None]] = None,
    id_field: str = "id",
    page_size: int = 10,
    searchable: bool = True,
    search_placeholder: str = "🔍 Cari...",
) -> None:
    """Render tabel data dengan search, pagination, dan action buttons."""
    if not data:
        st.markdown(
            '<div style="text-align:center;padding:2.5rem;background:rgba(255,255,255,0.03);'
            'border:1px solid rgba(255,255,255,0.07);border-radius:12px;color:#6B7280;">'
            '<div style="font-size:2rem;margin-bottom:0.5rem;">📭</div>'
            '<div style="font-size:0.95rem;">Tidak ada data</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    df = pd.DataFrame(data)

    if columns:
        existing = [c for c in columns.keys() if c in df.columns]
        # Pertahankan id_field di df meski tidak ada di columns, untuk lookup aksi
        display_df = df[existing].rename(columns=columns)
    else:
        display_df = df.copy()

    # Search
    filtered_df = display_df.copy()
    # Tambahkan kolom id dari df asli agar bisa di-lookup saat aksi edit/delete
    filtered_df["__id__"] = df[id_field].astype(str) if id_field in df.columns else ""
    if searchable:
        q = st.text_input("search", label_visibility="collapsed",
                          placeholder=search_placeholder, key=key + "_search")
        if q:
            mask = filtered_df.apply(
                lambda row: row.astype(str).str.contains(q, case=False, na=False).any(), axis=1
            )
            filtered_df = filtered_df[mask]

    total_rows  = len(filtered_df)
    total_pages = max(1, (total_rows + page_size - 1) // page_size)

    if key + "_page" not in st.session_state:
        st.session_state[key + "_page"] = 1
    current_page = max(1, min(st.session_state[key + "_page"], total_pages))

    start_idx = (current_page - 1) * page_size
    end_idx   = min(start_idx + page_size, total_rows)
    page_df   = filtered_df.iloc[start_idx:end_idx]

    info_col, page_col = st.columns([3, 1])
    with info_col:
        st.markdown(
            '<p style="color:#6B7280;font-size:0.8rem;margin:0;">Menampilkan '
            + str(start_idx + 1) + '–' + str(end_idx) + ' dari ' + str(total_rows) + ' data</p>',
            unsafe_allow_html=True,
        )
    with page_col:
        st.markdown(
            '<p style="color:#6B7280;font-size:0.8rem;margin:0;text-align:right;">Hal '
            + str(current_page) + ' / ' + str(total_pages) + '</p>',
            unsafe_allow_html=True,
        )

    if on_edit or on_delete or on_view:
        _render_table_with_actions(page_df, data, key, id_field,
                                    show_index, on_edit, on_delete, on_view, start_idx, columns)
    else:
        st.dataframe(page_df.reset_index(drop=True), use_container_width=True, hide_index=not show_index)

    # Pagination controls
    if total_pages > 1:
        p1, p2, p3, p4, p5 = st.columns([1, 1, 3, 1, 1])
        with p1:
            if st.button("⏮", key=key + "_first", disabled=(current_page <= 1)):
                st.session_state[key + "_page"] = 1; st.rerun()
        with p2:
            if st.button("◀", key=key + "_prev", disabled=(current_page <= 1)):
                st.session_state[key + "_page"] = current_page - 1; st.rerun()
        with p4:
            if st.button("▶", key=key + "_next", disabled=(current_page >= total_pages)):
                st.session_state[key + "_page"] = current_page + 1; st.rerun()
        with p5:
            if st.button("⏭", key=key + "_last", disabled=(current_page >= total_pages)):
                st.session_state[key + "_page"] = total_pages; st.rerun()


def _render_table_with_actions(page_df, original_data, key, id_field,
                                 show_index, on_edit, on_delete, on_view, start_idx, col_mapping):
    """Render tabel dengan tombol aksi per baris."""
    # Kolom display: semua kecuali __id__ (hidden)
    display_cols = [c for c in page_df.columns if c != "__id__"]

    # Buat lookup map id -> original_row
    id_lookup = {str(r.get(id_field, i)): r for i, r in enumerate(original_data)}

    for idx, (_, row) in enumerate(page_df.iterrows()):
        # Ambil id dari kolom __id__ yang selalu ada
        row_id = str(row.get("__id__", "")) or str(row.get(id_field, idx))

        # Lookup original_row berdasarkan id
        original_row = id_lookup.get(row_id, {})

        actual_idx = idx

        n_data    = len(display_cols)
        n_actions = sum([bool(on_view), bool(on_edit), bool(on_delete)])
        col_sizes = ([1] if show_index else []) + [3] * n_data + [1] * n_actions
        cols      = st.columns(col_sizes)
        ptr       = 0

        if show_index:
            with cols[ptr]:
                st.markdown('<span style="color:#6B7280;font-size:0.8rem;">' + str(actual_idx + 1) + '</span>',
                            unsafe_allow_html=True)
            ptr += 1

        for col_name in display_cols:
            with cols[ptr]:
                val = str(row.get(col_name, ""))
                st.markdown('<span style="font-size:0.875rem;color:#F8F9FA;">' + val + '</span>',
                            unsafe_allow_html=True)
            ptr += 1

        if on_view:
            with cols[ptr]:
                if st.button("👁️", key=key + "_view_" + row_id, help="Lihat detail"):
                    on_view(row_id)
            ptr += 1
        if on_edit:
            with cols[ptr]:
                if st.button("✏️", key=key + "_edit_" + row_id, help="Edit"):
                    on_edit(original_row)
            ptr += 1
        if on_delete:
            with cols[ptr]:
                if st.button("🗑️", key=key + "_del_" + row_id, help="Hapus"):
                    on_delete(row_id)

        st.divider()


def render_table_header(
    title: str,
    count: int = 0,
    on_add: Optional[Callable] = None,
    add_label: str = "➕ Tambah",
) -> None:
    """Render header tabel dengan judul, count badge, dan tombol tambah."""
    header_col, btn_col = st.columns([4, 1])
    with header_col:
        st.markdown(
            '<div style="display:flex;align-items:center;gap:0.75rem;">'
            '<h3 style="margin:0;color:#F8F9FA;font-size:1.25rem;">' + title + '</h3>'
            '<span style="background:rgba(124,58,237,0.12);border:1px solid rgba(124,58,237,0.25);'
            'color:#8B5CF6;padding:0.2rem 0.6rem;border-radius:9999px;font-size:0.75rem;font-weight:700;">'
            + str(count) + '</span>'
            '</div>',
            unsafe_allow_html=True,
        )
    with btn_col:
        if on_add:
            if st.button(add_label, key="add_" + title, type="primary", use_container_width=True):
                on_add()


def render_confirm_delete(
    item_name: str,
    on_confirm: Callable,
    on_cancel: Callable,
    key: str = "confirm_delete",
) -> None:
    """Render konfirmasi dialog hapus data."""
    st.markdown(
        '<div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.25);'
        'border-radius:12px;padding:1.25rem;margin:0.5rem 0;">'
        '<div style="font-weight:600;color:#EF4444;margin-bottom:0.5rem;">⚠️ Konfirmasi Hapus</div>'
        '<div style="color:#ADB5BD;font-size:0.9rem;">Apakah Anda yakin ingin menghapus <strong style="color:#F8F9FA;">'
        + item_name + '</strong>? Tindakan ini tidak dapat dibatalkan.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Ya, Hapus", key=key + "_confirm", type="primary", use_container_width=True):
            on_confirm()
            st.rerun()
    with col2:
        if st.button("❌ Batal", key=key + "_cancel", use_container_width=True):
            on_cancel()
