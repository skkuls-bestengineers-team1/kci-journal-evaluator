import io

import pandas as pd
import streamlit as st

import config  # 프로젝트 루트 .env를 먼저 로드한다.
from graph import build_graph


# ------------------------------------------------------------
# 1. 페이지 기본 설정
# ------------------------------------------------------------
st.set_page_config(
    page_title='KCI 논문 심사 어시스턴트',
    layout='wide',
    initial_sidebar_state='collapsed',
)

st.title('KCI 논문 심사 어시스턴트')
st.caption('체크리스트 5항목을 하나씩 확인한 뒤, 논문을 평가하고 등록합니다.')


CHECKLIST_ITEMS = [
    {
        'key': 'regularity',
        'stage1_key': '발행규칙성',
        'title': '(1) 발행의 규칙성 및 정시성',
        'desc': '학술지가 규정된 발행 주기를 지키며 정시에 발간되고 있는지 확인합니다.',
    },
    {
        'key': 'reviewers',
        'stage1_key': '심사위원수',
        'title': '(2) 논문당 심사위원수',
        'desc': '논문 1편당 심사위원 수가 KCI 기준(통상 2인 이상)을 충족하는지 확인합니다.',
    },
    {
        'key': 'ethics',
        'stage1_key': '연구윤리',
        'title': '(3) 연구 윤리',
        'desc': '연구윤리 규정, 표절 점검, 이해상충·연구부정 처리 절차가 갖춰져 있는지 확인합니다.',
    },
    {
        'key': 'diversity',
        'stage1_key': '투고다양성',
        'title': '(4) 논문 투고 다양성',
        'desc': '특정 기관·저자에게 투고가 편중되지 않고 투고 주체가 다양한지 확인합니다.',
    },
    {
        'key': 'system',
        'stage1_key': '기본체계',
        'title': '(5) 학술지 기본체계 구축',
        'desc': '편집위원회, 투고 규정, 심사 절차, ISSN 등 학술지 운영 체계가 구축되어 있는지 확인합니다.',
    },
]

SUBITEM_LABELS = {
    'recognition': '인지도 및 활용도',
    'suitability': '학술적 가치·적합성',
    'topic_fit': '학술지 주제 부합도',
    'completeness': '구성·체제 완전성',
    'readability': '가독성',
    'affiliation_clarity': '소속·직위 표기',
}

STAGE2_DETAIL_ITEMS = [
    {
        'title': '연간 학술지 발간 횟수',
        'score_key': 'journal_publication_frequency_score',
        'pass_key': 'journal_publication_frequency_passed',
        'desc': '학술지가 규정된 주기로 정기 발간되는지를 확인합니다. Tavily 검색과 학술지명·ISSN이 필요합니다.',
        'fail_hint': '학술지 메타데이터(이름, ISSN)나 TAVILY_API_KEY가 없으면 0점으로 처리됩니다.',
    },
    {
        'title': '온라인 접근성',
        'score_key': 'online_access_score',
        'pass_key': 'online_access_score_passed',
        'desc': '홈페이지·OA 여부·최근 발행연도를 OpenAlex에서 확인합니다.',
        'fail_hint': 'ISSN이 없거나 OPEN_ALEX_API_KEY가 비어 있으면 0점으로 처리됩니다.',
    },
    {
        'title': '주제어 및 초록 외국어화',
        'score_key': 'foreign_lang_score',
        'pass_key': 'foreign_lang_passed',
        'desc': '논문 본문에서 외국어 초록과 주제어가 모두 있는지를 Gemini가 판정합니다.',
        'fail_hint': '초록·주제어를 찾지 못하거나 Gemini 키가 없으면 미충족으로 처리됩니다.',
    },
]

STAGE3_AGENT_LABELS = {
    'academic_value': ('학술적 가치와 성과', config.ACADEMIC_VALUE_MAX_SCORE),
    'structure': ('구성·체제·가독성', config.STRUCTURE_MAX_SCORE),
}


def check_key(item_key: str) -> str:
    return f'check_{item_key}'


def persist_index(index: int) -> None:
    key = CHECKLIST_ITEMS[index]['key']
    widget_id = check_key(key)
    if widget_id in st.session_state:
        st.session_state.checks[key] = bool(st.session_state[widget_id])


def reset_checklist() -> None:
    st.session_state.checklist_index = 0
    st.session_state.checks = {item['key']: False for item in CHECKLIST_ITEMS}
    for item in CHECKLIST_ITEMS:
        widget_id = check_key(item['key'])
        if widget_id in st.session_state:
            st.session_state[widget_id] = False


def init_state() -> None:
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'eval_state' not in st.session_state:
        st.session_state.eval_state = None
    if 'analyzed_name' not in st.session_state:
        st.session_state.analyzed_name = None
    if 'registered_papers' not in st.session_state:
        st.session_state.registered_papers = []
    if 'checklist_index' not in st.session_state:
        st.session_state.checklist_index = 0
    if 'had_uploaded_file' not in st.session_state:
        st.session_state.had_uploaded_file = False
    if 'checks' not in st.session_state:
        st.session_state.checks = {item['key']: False for item in CHECKLIST_ITEMS}


def checked_count() -> int:
    return sum(1 for value in st.session_state.checks.values() if value)


def all_items_checked() -> bool:
    return checked_count() == len(CHECKLIST_ITEMS)


def go_prev() -> None:
    persist_index(st.session_state.checklist_index)
    st.session_state.checklist_index = max(0, st.session_state.checklist_index - 1)


def go_next() -> None:
    persist_index(st.session_state.checklist_index)
    last_index = len(CHECKLIST_ITEMS) - 1
    st.session_state.checklist_index = min(last_index, st.session_state.checklist_index + 1)


def stage1_checklist() -> dict:
    return {
        item['stage1_key']: bool(st.session_state.checks.get(item['key'], False))
        for item in CHECKLIST_ITEMS
    }


def extract_pdf_text(uploaded) -> str:
    import pdfplumber

    with pdfplumber.open(io.BytesIO(uploaded.getvalue())) as pdf:
        pages = [page.extract_text() or '' for page in pdf.pages]
    return '\n'.join(pages).strip()


def map_eval_to_ui(eval_state: dict) -> dict:
    strengths = []
    improvements = []
    for result in eval_state.get('stage3_results') or []:
        for key, item in (result.get('subitems') or {}).items():
            label = SUBITEM_LABELS.get(key, key)
            note = item.get('rationale') or ''
            grade = item.get('grade') or '-'
            line = f'{label} ({grade}): {note}'
            if grade in {'A', 'B'}:
                strengths.append(line)
            else:
                improvements.append(line)

    if eval_state.get('foreign_lang_passed') or eval_state.get('foreign_lang_satisfied'):
        strengths.append('주제어와 초록의 외국어 표기는 충족되었습니다. 다만 2단계 전체 통과는 세 항목을 모두 봐야 합니다.')
    elif eval_state.get('foreign_language_reason'):
        improvements.append(eval_state['foreign_language_reason'])
    elif eval_state.get('foreign_lang_extraction_failed'):
        improvements.append('초록·주제어 섹션을 찾지 못해 외국어화 여부를 확인하지 못했습니다.')

    stage2_ran = eval_state.get('stage1_pass') is not False
    if stage2_ran:
        if eval_state.get('journal_publication_frequency_passed'):
            strengths.append('연간 학술지 발간 횟수 항목을 충족했습니다.')
        else:
            improvements.append('연간 학술지 발간 횟수 항목이 0점이거나 미충족입니다. 학술지명·ISSN과 Tavily 키가 필요합니다.')

        if eval_state.get('online_access_score_passed'):
            strengths.append('온라인 접근성 항목을 충족했습니다.')
        else:
            improvements.append('온라인 접근성 항목이 0점이거나 미충족입니다. ISSN과 OpenAlex 조회가 필요합니다.')

        if not eval_state.get('total_stage2_pass', True):
            improvements.append(
                '2단계 체계평가는 세부 항목 중 하나라도 0점이면 과락입니다. '
                f"현재 합산 {eval_state.get('total_stage2_score') or 0}점입니다."
            )

    if not strengths:
        strengths.append('추가 강점 코멘트가 없습니다. 평가 결과를 항목별로 확인해 주세요.')
    if not improvements:
        improvements.append('즉시 보완이 필요한 항목은 확인되지 않았습니다.')

    score = eval_state.get('final_score')
    if score is None:
        probability = 0
    else:
        probability = int(round(float(score)))

    summary = eval_state.get('final_comment') or eval_state.get('rejection_reason') or ''
    return {
        'strengths': strengths,
        'improvements': improvements,
        'summary': summary,
        'kci_probability': probability,
        'verdict': eval_state.get('final_verdict'),
        'rejection_reason': eval_state.get('rejection_reason'),
    }


def run_evaluation(uploaded, journal_name: str) -> dict:
    raw_text = extract_pdf_text(uploaded)
    if not raw_text:
        raise ValueError('PDF에서 텍스트를 추출하지 못했습니다.')

    graph = build_graph()
    result = graph.invoke(
        {
            'journal_meta': {
                'journal_name': journal_name or '미상',
                'abbreviation': None,
                'issn': None,
                'eissn': None,
                'major_research_field': None,
                'middle_research_field': None,
            },
            'paper': {
                'paper_id': uploaded.name,
                'raw_text': raw_text,
            },
            'stage1_checklist': stage1_checklist(),
            'stage1_pass': None,
            'journal_publication_frequency_passed': False,
            'journal_publication_frequency_score': 0.0,
            'online_access_score_passed': False,
            'online_access_score': 0.0,
            'foreign_lang_score': 0.0,
            'foreign_lang_passed': False,
            'foreign_language_ratio': 0.0,
            'foreign_language_reason': '',
            'total_stage2_score': 0.0,
            'total_stage2_pass': False,
            'stage3_results': [],
            'stage3_total': None,
            'stage3_pass': None,
            'final_score': None,
            'final_verdict': None,
            'final_comment': None,
            'rejection_reason': None,
        }
    )
    if hasattr(result, 'model_dump'):
        return result.model_dump()
    return result


def probability_label(score: int) -> str:
    if score >= 80:
        return '등재후보 선정 기준에 근접하거나 충족합니다'
    if score >= 56:
        return '보완 후 재평가를 권합니다'
    return '현재 기준으로는 탈락 위험이 큽니다'


def _fmt_score(value) -> str:
    try:
        return f'{float(value or 0):.1f}'
    except (TypeError, ValueError):
        return '0.0'


def _status_pill(passed: bool | None, pending: bool = False) -> None:
    if pending or passed is None:
        st.caption('아직 평가되지 않았습니다.')
    elif passed:
        st.success('충족')
    else:
        st.error('미충족')


def _progress_score(value, maximum: float) -> None:
    numeric = float(value or 0)
    ratio = 0.0 if maximum <= 0 else min(1.0, max(0.0, numeric / maximum))
    st.progress(ratio)


def _next_steps(eval_state: dict) -> list[str]:
    steps = []
    if eval_state.get('stage1_pass') is False:
        steps.append('1단계 체크리스트에서 미충족 항목을 보완한 뒤 다시 평가하세요.')
        return steps
    if not eval_state.get('total_stage2_pass'):
        if not eval_state.get('journal_publication_frequency_passed'):
            steps.append('학술지명·ISSN을 넣고 Tavily 키를 설정하면 발간 횟수 항목을 재평가할 수 있습니다.')
        if not eval_state.get('online_access_score_passed'):
            steps.append('ISSN을 입력하고 OpenAlex 조회가 되면 온라인 접근성 점수가 반영됩니다.')
        if not eval_state.get('foreign_lang_passed'):
            steps.append('외국어 초록과 주제어를 논문에 명확히 표기한 뒤 다시 분석하세요.')
        steps.append('2단계는 세 항목 모두 0점보다 커야 다음 단계로 넘어갑니다.')
        return steps
    if eval_state.get('stage3_pass') is False:
        steps.append('3단계 내용평가 총점이 과락 기준에 미달했습니다. 학술적 가치·구성/가독성 근거를 보완하세요.')
        return steps
    if eval_state.get('final_verdict') == '탈락':
        steps.append('종합 점수가 합격 기준에 못 미쳤습니다. 낮은 등급 항목의 근거를 중심으로 개정하세요.')
    else:
        steps.append('현재 기준으로는 등재후보 선정 문턱을 넘었습니다. 세부 근거를 기록해 두세요.')
    return steps


def render_tab2(result: dict | None, eval_state: dict | None, probability: int) -> None:
    st.subheader('상세 평가 리포트')
    st.caption('단계별 점수, 항목 근거, 장점과 보완점을 위에서 아래로 확인할 수 있습니다.')

    if eval_state is None or result is None:
        st.info('분석을 실행하면 2단계·3단계 세부 항목과 총평이 이 탭에 표시됩니다.')
        st.markdown(
            '- **2단계 체계평가**: 발간 횟수, 온라인 접근성, 외국어화\n'
            '- **3단계 내용평가**: 학술적 가치, 구성·가독성\n'
            '- **종합심의**: 합산 점수와 선정/탈락 코멘트'
        )
        return

    verdict = result.get('verdict')
    rejection = result.get('rejection_reason') or ''
    if verdict == '등재후보 선정':
        st.success(f'최종 판정: {verdict}')
    elif verdict:
        st.error(f'최종 판정: {verdict}')
        if rejection:
            st.warning(rejection)

    stage2 = float(eval_state.get('total_stage2_score') or eval_state.get('stage2_score') or 0)
    stage3 = float(eval_state.get('stage3_total') or 0)
    final = float(eval_state.get('final_score') or 0)

    overview = st.container(border=True)
    with overview:
        st.markdown('#### 점수 한눈에 보기')
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric('2단계 체계평가', f'{_fmt_score(stage2)} / {config.STAGE2_MAX_SCORE}')
            _progress_score(stage2, config.STAGE2_MAX_SCORE)
            _status_pill(eval_state.get('total_stage2_pass'))
        with c2:
            st.metric('3단계 내용평가', f'{_fmt_score(stage3)} / {config.STAGE3_MAX_SCORE}')
            _progress_score(stage3, config.STAGE3_MAX_SCORE)
            if eval_state.get('stage3_total') is None:
                _status_pill(None, pending=True)
            else:
                _status_pill(eval_state.get('stage3_pass'))
        with c3:
            st.metric('종합 점수', f'{_fmt_score(final)} / {config.FINAL_MAX_SCORE}')
            _progress_score(final, config.FINAL_MAX_SCORE)
            st.caption(f'합격 기준 {config.FINAL_PASS_THRESHOLD}점 · {probability_label(probability)}')

    st.markdown('#### 1단계 신청자격')
    checklist = eval_state.get('stage1_checklist') or {}
    with st.container(border=True):
        cols = st.columns(len(CHECKLIST_ITEMS))
        for col, item in zip(cols, CHECKLIST_ITEMS):
            with col:
                ok = bool(checklist.get(item['stage1_key']))
                st.markdown(f"**{item['stage1_key']}**")
                _status_pill(ok)
        if eval_state.get('stage1_pass') is False:
            st.error('1단계 미충족으로 이후 평가가 중단되었습니다.')

    st.markdown('#### 2단계 체계평가 세부 항목')
    st.caption('세 항목 중 하나라도 0점이면 2단계 과락이며, 3단계로 넘어가지 않습니다.')
    for item in STAGE2_DETAIL_ITEMS:
        with st.container(border=True):
            title_col, score_col = st.columns([3, 1])
            passed = bool(eval_state.get(item['pass_key']))
            score = eval_state.get(item['score_key']) or 0
            with title_col:
                st.markdown(f"**{item['title']}**")
                st.write(item['desc'])
            with score_col:
                st.metric('점수', _fmt_score(score))
                _status_pill(passed)
            if item['score_key'] == 'foreign_lang_score':
                ratio = eval_state.get('foreign_language_ratio')
                reason = eval_state.get('foreign_language_reason') or ''
                if ratio is not None:
                    st.caption(f'외국어화 비율: {_fmt_score(ratio)}%')
                if reason:
                    st.markdown(f'> {reason}')
            elif not passed:
                st.caption(item['fail_hint'])

    st.markdown('#### 3단계 내용평가 세부 항목')
    results = eval_state.get('stage3_results') or []
    if not results:
        with st.container(border=True):
            st.info(
                '3단계 결과가 없습니다. 2단계 과락이거나 Agent2/Agent3가 아직 실행되지 않았습니다. '
                f'과락 기준은 {config.STAGE3_PASS_THRESHOLD}점입니다.'
            )
    else:
        st.caption(f'3단계 과락 기준은 {config.STAGE3_PASS_THRESHOLD} / {config.STAGE3_MAX_SCORE}점입니다.')
        for agent_result in results:
            agent = agent_result.get('agent', '')
            label, maximum = STAGE3_AGENT_LABELS.get(agent, (agent, None))
            with st.container(border=True):
                head, score_col = st.columns([3, 1])
                with head:
                    st.markdown(f"**{label}**")
                with score_col:
                    if maximum:
                        st.metric('점수', f'{_fmt_score(agent_result.get("score"))} / {maximum}')
                    else:
                        st.metric('점수', _fmt_score(agent_result.get('score')))
                for key, detail in (agent_result.get('subitems') or {}).items():
                    grade = detail.get('grade') or '-'
                    rationale = detail.get('rationale') or '근거가 제공되지 않았습니다.'
                    st.markdown(f"**{SUBITEM_LABELS.get(key, key)}** · 등급 {grade}")
                    st.markdown(f'> {rationale}')

    st.markdown('#### 장점')
    with st.container(border=True):
        for line in result['strengths']:
            st.markdown(f'- {line}')

    st.markdown('#### 보완할 점')
    with st.container(border=True):
        for line in result['improvements']:
            st.markdown(f'- {line}')

    st.markdown('#### 총평')
    with st.container(border=True):
        summary = result.get('summary') or '총평이 생성되지 않았습니다. 과락 시에는 탈락 사유가 총평을 대신합니다.'
        st.write(summary)
        st.caption(probability_label(probability))
        if eval_state.get('final_comment') and eval_state.get('rejection_reason'):
            st.divider()
            st.markdown('**게이트 중단 사유**')
            st.write(eval_state['rejection_reason'])

    st.markdown('#### 다음에 손볼 곳')
    with st.container(border=True):
        for step in _next_steps(eval_state):
            st.markdown(f'- {step}')


init_state()
persist_index(st.session_state.checklist_index)


# ------------------------------------------------------------
# 2. 파일 업로드
# ------------------------------------------------------------
uploaded = st.file_uploader(
    '논문 파일 업로드',
    type=['pdf'],
    help='평가 파이프라인은 PDF 텍스트 추출을 사용합니다.',
)

can_analyze = uploaded is not None and all_items_checked()
analyze = st.button(
    '분석 시작',
    width='stretch',
    disabled=not can_analyze,
)

if uploaded is None:
    if st.session_state.had_uploaded_file:
        reset_checklist()
    st.session_state.analysis_result = None
    st.session_state.eval_state = None
    st.session_state.analyzed_name = None
    st.session_state.had_uploaded_file = False
else:
    st.session_state.had_uploaded_file = True
    if analyze:
        try:
            eval_state = run_evaluation(uploaded, '')
            st.session_state.eval_state = eval_state
            st.session_state.analysis_result = map_eval_to_ui(eval_state)
            st.session_state.analyzed_name = uploaded.name
        except Exception as error:
            st.session_state.eval_state = None
            st.session_state.analysis_result = None
            st.error(f'평가를 실행하지 못했습니다: {error}')

result = st.session_state.analysis_result
eval_state = st.session_state.eval_state
can_register = uploaded is not None and all_items_checked()
passed_count = checked_count()
current_index = st.session_state.checklist_index
probability = 0 if result is None else result['kci_probability']
register_label = '가능' if can_register else '불가'
verdict = None if result is None else result.get('verdict')


# ------------------------------------------------------------
# 3. KPI
# ------------------------------------------------------------
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric('현재 항목', f'{current_index + 1} / 5')
kpi2.metric('체크 완료', f'{passed_count} / 5')
kpi3.metric('종합 점수', f'{probability} 점')
kpi4.metric('논문 등록', register_label)

if uploaded is not None:
    st.caption(f'선택된 파일: {uploaded.name}')
if verdict:
    if verdict == '등재후보 선정':
        st.success(f'최종 판정: {verdict}')
    else:
        st.error(f'최종 판정: {verdict}')
        if result.get('rejection_reason'):
            st.caption(result['rejection_reason'])


tab1, tab2, tab3 = st.tabs(
    [
        'Tab1. 체크리스트',
        'Tab2. 상세 평가 결과',
        'Tab3. 논문 등록',
    ]
)


# ------------------------------------------------------------
# Tab1. 체크리스트 — 화면 중앙에서 한 항목씩 확인
# ------------------------------------------------------------
with tab1:
    st.subheader('KCI 등재 평가 체크리스트')
    st.caption('한 항목씩 확인하고, 충족되면 체크한 뒤 다음 항목으로 이동하세요.')
    st.progress((current_index + 1) / len(CHECKLIST_ITEMS))

    item = CHECKLIST_ITEMS[current_index]
    st.markdown(f'**{item["title"]}**')
    st.write(item['desc'])

    if not all_items_checked():
        st.info('5개 항목을 모두 체크해야 분석을 시작할 수 있습니다.')
    elif uploaded is None:
        st.info('체크는 완료되었습니다. PDF를 올리면 분석을 시작할 수 있습니다.')
    elif result is None:
        st.info('분석 시작을 누르면 1단계 체크리스트 이후 평가 그래프가 실행됩니다.')

    widget_id = check_key(item['key'])
    if widget_id not in st.session_state:
        st.session_state[widget_id] = st.session_state.checks[item['key']]
    st.checkbox(
        '위 내용을 모두 만족합니다.',
        key=widget_id,
    )
    st.session_state.checks[item['key']] = bool(st.session_state[widget_id])

    prev_col, next_col = st.columns(2)
    with prev_col:
        st.button(
            '이전 항목',
            width='stretch',
            disabled=current_index == 0,
            on_click=go_prev,
        )
    with next_col:
        st.button(
            '다음 항목',
            width='stretch',
            disabled=current_index == len(CHECKLIST_ITEMS) - 1,
            on_click=go_next,
        )

    if can_register:
        st.success('5개 항목을 모두 체크했습니다. 분석 후 Tab3에서 논문을 등록할 수 있습니다.')
    else:
        st.caption(f'남은 항목 {5 - passed_count}개를 더 체크해야 논문을 등록할 수 있습니다.')


# ------------------------------------------------------------
# Tab2. 상세 평가 결과
# ------------------------------------------------------------
with tab2:
    render_tab2(result, eval_state, probability)


# ------------------------------------------------------------
# Tab3. 논문 등록
# ------------------------------------------------------------
with tab3:
    st.subheader('논문 등록')
    st.caption('체크리스트 5항목을 모두 체크해야 논문을 등록할 수 있습니다.')

    form_col, list_col = st.columns([1.1, 1])

    with form_col:
        if uploaded is None:
            st.warning('먼저 논문을 업로드하고 체크리스트 5항목을 확인해 주세요.')
        elif not can_register:
            st.warning('화면 중앙에서 체크리스트 5항목을 모두 체크해야 등록할 수 있습니다.')
            st.write('아직 체크하지 않은 항목:')
            for item in CHECKLIST_ITEMS:
                if not st.session_state.checks.get(item['key'], False):
                    st.write(f'- {item["title"]}')

        with st.form('paper_register_form', clear_on_submit=True):
            paper_title = st.text_input('논문명')
            authors = st.text_input('저자')
            journal = st.text_input('학술지명')
            submitted = st.form_submit_button(
                '논문 등록',
                width='stretch',
                disabled=not can_register,
            )

        if submitted and can_register:
            st.session_state.registered_papers.append(
                {
                    '논문명': paper_title or '(제목 없음)',
                    '저자': authors or '-',
                    '학술지명': journal or '-',
                    '파일명': st.session_state.analyzed_name or uploaded.name,
                    '종합점수': f'{probability} 점',
                    '판정': verdict or '-',
                    '체크리스트': '5/5 확인',
                }
            )
            st.success('논문이 등록되었습니다. 체크리스트 5항목을 모두 확인한 원고입니다.')

    with list_col:
        st.subheader('등록된 논문')
        registered_df = pd.DataFrame(st.session_state.registered_papers)
        if registered_df.empty:
            st.info('아직 등록된 논문이 없습니다.')
        else:
            st.dataframe(registered_df, width='stretch', hide_index=True)
