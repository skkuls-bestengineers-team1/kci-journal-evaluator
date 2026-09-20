"""Streamlit UI: PDF 업로드, 1단계 체크리스트, 그래프 실행, 결과 렌더링

TODO:
- PDF -> raw_text 추출 (pdfplumber)
- 1단계 체크리스트 UI (stage1_checklist)
- graph.invoke() 호출 및 결과 렌더링 (rejection_reason 또는 final_verdict)
"""

import streamlit as st

from graph import build_graph

st.set_page_config(page_title="KCI 등재후보학술지 예측", layout="wide")
st.title("KCI 등재후보학술지 예측 (MVP — 논문 1편 기준)")

# TODO: 1단계 체크리스트 UI
# TODO: PDF 업로드 위젯 + 텍스트 추출
# TODO: "평가 실행" 버튼 -> build_graph().invoke(initial_state)
# TODO: 결과 렌더링 (탈락 사유 또는 최종 판정/점수/코멘트)


