import streamlit as st

from src.alignment import SectionAligner
from src.config import (
    DEFAULT_SEMANTIC_MODEL,
    AlignmentConfig,
    BackendSelection,
    SimilarityBackendType,
    build_backend,
    recommended_threshold,
)
from src.diffing import classify_change, word_diff_html
from src.extractors import extract_text
from src.sectioning import extract_sections
from src.summarization import RuleBasedChangeSummarizer
from src.text_utils import clean_text


@st.cache_resource(show_spinner="Loading similarity backend...")
def load_similarity_backend(
    backend_type: SimilarityBackendType,
    model_identifier: str,
    lexical_weight: float,
    semantic_weight: float,
) -> BackendSelection:
    """Construct and cache one reusable backend resource for the application."""
    return build_backend(
        AlignmentConfig(
            backend=backend_type,
            model_identifier=model_identifier,
            lexical_weight=lexical_weight,
            semantic_weight=semantic_weight,
        )
    )


st.set_page_config(page_title="Doc Drift Analyzer", layout="wide")

st.title("Doc Drift Analyzer")
st.caption("Compare two versions of a document and surface meaningful changes.")

left, right = st.columns(2)

with left:
    old_file = st.file_uploader("Old version", type=["txt", "pdf", "docx"], key="old_file")

with right:
    new_file = st.file_uploader("New version", type=["txt", "pdf", "docx"], key="new_file")

backend_type = SimilarityBackendType(
    st.selectbox(
        "Similarity backend",
        options=[backend.value for backend in SimilarityBackendType],
        index=0,
        format_func=str.title,
    )
)
threshold = st.slider(
    "Section alignment threshold",
    0.1,
    0.9,
    recommended_threshold(backend_type),
    0.05,
    key=f"threshold_{backend_type.value}",
)
show_unchanged = st.checkbox("Show unchanged sections", value=False)

if st.button("Compare documents", type="primary"):
    if old_file is None or new_file is None:
        st.warning("Please upload both document versions.")
    else:
        old_text = clean_text(extract_text(old_file))
        new_text = clean_text(extract_text(new_file))

        old_sections = extract_sections(old_text)
        new_sections = extract_sections(new_text)
        selection = load_similarity_backend(
            backend_type,
            DEFAULT_SEMANTIC_MODEL,
            lexical_weight=0.5,
            semantic_weight=0.5,
        )
        if selection.fallback is not None:
            st.warning(
                f"{selection.requested_backend.value.title()} similarity is unavailable. "
                f"Using lexical similarity instead: {selection.fallback.message}"
            )
        st.caption(f"Active similarity backend: {selection.active_backend.value.title()}")
        active_threshold = selection.threshold if selection.fallback is not None else threshold
        aligner = SectionAligner(similarity_backend=selection.backend)
        aligned = aligner.align(old_sections, new_sections, active_threshold)
        summary = RuleBasedChangeSummarizer().summarize(aligned)

        st.subheader("Summary")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Added", summary.added)
        m2.metric("Removed", summary.removed)
        m3.metric("Minor edits", summary.minor_edits)
        m4.metric("Major edits", summary.major_edits)
        m5.metric("Unchanged", summary.unchanged)

        st.markdown("### Key changes")
        if summary.bullets:
            for bullet in summary.bullets:
                st.write(f"- {bullet}")
        else:
            st.info("No meaningful changes found.")

        st.markdown("### Detailed review")
        for row in aligned:
            label = classify_change(row.old_content, row.new_content, row.similarity)
            if not show_unchanged and label == "Unchanged":
                continue

            title = f"{label} | {row.old_title or 'None'} -> {row.new_title or 'None'}"

            with st.expander(title, expanded=(label in {"Added", "Removed", "Edited (major)"})):
                st.caption(f"Similarity: {row.similarity:.2f}")

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Old**")
                    st.write(row.old_content or "<empty>")
                with c2:
                    st.markdown("**New**")
                    st.write(row.new_content or "<empty>")

                st.markdown("**Inline diff**")
                st.markdown(
                    word_diff_html(row.old_content, row.new_content),
                    unsafe_allow_html=True,
                )
