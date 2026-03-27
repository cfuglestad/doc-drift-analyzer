import streamlit as st

from src.extractors import extract_text
from src.text_utils import clean_text
from src.sectioning import extract_sections
from src.alignment import align_sections
from src.diffing import classify_change, summarize_changes, word_diff_html
from src.summarization import build_change_bullets

st.set_page_config(page_title="Doc Drift Analyzer", layout="wide")

st.title("Doc Drift Analyzer")
st.caption("Compare two versions of a document and surface meaningful changes.")

left, right = st.columns(2)

with left:
    old_file = st.file_uploader("Old version", type=["txt", "pdf", "docx"], key="old_file")

with right:
    new_file = st.file_uploader("New version", type=["txt", "pdf", "docx"], key="new_file")

threshold = st.slider("Section alignment threshold", 0.1, 0.9, 0.35, 0.05)
show_unchanged = st.checkbox("Show unchanged sections", value=False)

if st.button("Compare documents", type="primary"):
    if old_file is None or new_file is None:
        st.warning("Please upload both document versions.")
    else:
        old_text = clean_text(extract_text(old_file))
        new_text = clean_text(extract_text(new_file))

        old_sections = extract_sections(old_text)
        new_sections = extract_sections(new_text)
        aligned = align_sections(old_sections, new_sections, threshold)
        summary = summarize_changes(aligned)
        bullets = build_change_bullets(aligned)

        st.subheader("Summary")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Added", summary["Added"])
        m2.metric("Removed", summary["Removed"])
        m3.metric("Minor edits", summary["Edited (minor)"])
        m4.metric("Major edits", summary["Edited (major)"])
        m5.metric("Unchanged", summary["Unchanged"])

        st.markdown("### Key changes")
        if bullets:
            for bullet in bullets:
                st.write(f"- {bullet}")
        else:
            st.info("No meaningful changes found.")

        st.markdown("### Detailed review")
        for row in aligned:
            label = classify_change(row["old_content"], row["new_content"], row["similarity"])
            if not show_unchanged and label == "Unchanged":
                continue

            title = f"{label} | {row['old_title'] or 'None'} -> {row['new_title'] or 'None'}"

            with st.expander(title, expanded=(label in {"Added", "Removed", "Edited (major)"})):
                st.caption(f"Similarity: {row['similarity']:.2f}")

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Old**")
                    st.write(row["old_content"] or "<empty>")
                with c2:
                    st.markdown("**New**")
                    st.write(row["new_content"] or "<empty>")

                st.markdown("**Inline diff**")
                st.markdown(word_diff_html(row["old_content"], row["new_content"]), unsafe_allow_html=True)
