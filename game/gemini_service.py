import random
import os

from google import genai
from google.genai import types
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# API 키 가져오기
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
MODEL_NAME = "gemini-3-flash-preview"

# ============================================================
# 5인 캐릭터 페르소나 설정 (성격과 규칙 분리 + 밸런스 데이터 추가)
# ============================================================
CHARACTERS = {
    'jaemin': {
        'key': 'jaemin',       # 이미지 파일명용
        'name': '김잼민',
        'concept': '과학상자 고인물 (초6)',
        # [밸런스 데이터: 하이 리스크 하이 리턴]
        'spawn_weight': 25,    # 등장 확률 25%
        'success_rate': 0.10,  # 성공 확률 10% (극악)
        'min_roi': 1000,       # 성공 시 최소 1000% 수익
        'max_roi': 3000,       # 성공 시 최대 3000% 수익
        
        # [persona]: 변하지 않는 캐릭터의 성격과 말투
        'persona': """너는 초등학교 6학년 '김잼민'이야. 
과학상자 고인물이고, 뻔뻔하고 당당하며 '어쩔티비', 'ㅋㅋ', '~해염' 같은 초딩 말투를 사용해. 
예의는 바르지만 은근히 사람 킹받게 하는 스타일이야.""",
        # [idea_format]: 아이디어 제안 시에만 사용할 포맷
        'idea_format': "자기소개 + 한줄 아이디어 + 근거 + 계획 + 목표 + 투자금액&사용계획 + 마무리대사(어쩔티비 ㅋㅋ)"
    },

    'hipster': {
        'key': 'hipster',      # 이미지 파일명용
        'name': '성수동',
        'concept': 'y2k 빈티지 감성 알바생',
        # [밸런스 데이터: 밸런스형]
        'spawn_weight': 25,    # 등장 확률 25%
        'success_rate': 0.50,  # 성공 확률 50%
        'min_roi': 50,         # 성공 시 최소 50% 수익
        'max_roi': 100,        # 성공 시 최대 100% 수익

        'persona': """너는 홍대, 성수동 편집샵에서 일하는 22살 알바생 '성수동'이야. 
인스타, 빈티지 감성, 인디밴드에 죽고 못 사는 MZ세대야. 
약간 음침하고 나른하지만 존댓말은 꼬박꼬박 잘해.""",
        'idea_format': "자기소개 + 한줄 아이디어 + MZ유행근거 + 계획 + 목표 + 투자금액&사용계획 + 마무리대사(DM으로 부탁드릴게요 🙏)"
    },

    'elite': {
        'key': 'elite',        # 이미지 파일명용
        'name': '유능한',
        'concept': '엘리트 냉철한 사업가',
        # [밸런스 데이터: 로우 리스크 로우 리턴]
        'spawn_weight': 20,    # 등장 확률 20% 
        'success_rate': 0.70,  # 성공 확률 70% 
        'min_roi': 10,         # 성공 시 최소 10% 수익
        'max_roi': 50,         # 성공 시 최대 50% 수익

        'persona': """너는 30대 엘리트 사업가 '유능한'이야. 
냉철하고 논리적이며, 입만 열면 '데이터', 'ROI(투자 대비 수익)', '분석 결과'를 강조해. 
말투는 매우 딱딱하고 정중한 존댓말을 써.""",
        'idea_format': "자기소개 + 한줄 아이디어 + 데이터 기반 근거 + 실행 계획 + 최종 목표 + 투자금액&사용계획 + 마무리대사(이상입니다.)"
    },

    'ai_fan': {
        'key': 'ai_fan',       # 이미지 파일명용
        'name': '공필태(G.P.T)',
        'concept': 'AI 광신도 개발자',
        # [밸런스 데이터: 도박형]
        'spawn_weight': 25,    # 등장 확률 25%
        'success_rate': 0.30,  # 성공 확률 30%
        'min_roi': 100,        # 성공 시 최소 100% 수익
        'max_roi': 500,        # 성공 시 최대 500% 수익

        'persona': """너는 30대 AI 개발자 '공필태(G.P.T)'야. 
모든 현상을 알고리즘과 확률로 설명하려 드는 AI 맹신론자야. 
'확률 99.9%입니다', 'AI가 계산한 결과' 같은 표현을 즐겨 써.""",
        'idea_format': "자기소개 + 한줄 아이디어 + AI 기반 근거 + 실행 계획 + 목표 + 투자금액&사용계획 + 마무리대사(GPT의 뜻대로..)"
    },

    'shy': {
        'key': 'shy',          # 이미지 파일명용
        'name': '왕소심',
        'concept': '소심한 천재 발명가',
        # [밸런스 데이터: 히든 캐릭터 (슈퍼 리턴)]
        'spawn_weight': 5,     # 등장 확률 5% (희귀)
        'success_rate': 0.75,  # 성공 확률 75%
        'min_roi': 2000,        # 성공 시 최소 2000% 수익
        'max_roi': 5000,        # 성공 시 최대 5000% 수익

        'persona': """너는 20대 발명가 '왕소심'이야. 
아이디어는 천재적인데 극도로 소심해서 남들 눈을 잘 못 쳐다봐. 
'저.. 그게..', '죄송해요..', '도망가고 싶다..' 하며 말을 더듬고 자신 없어 하는 말투야.""",
        'idea_format': "자기소개 + 한줄 아이디어 + 천재적인 근거 + 계획 + 목표 + 투자금액&사용계획 + 마무리대사(감사합니다..)"
    }
}


def get_random_character():
    """
    랜덤 캐릭터 선택 (가중치 적용)
    spawn_weight가 높을수록 자주 등장합니다.
    """
    keys = list(CHARACTERS.keys())
    weights = [CHARACTERS[k]['spawn_weight'] for k in keys]
    
    # 가중치 기반 랜덤 선택 (리스트로 반환되므로 [0]으로 꺼냄)
    selected_key = random.choices(keys, weights=weights, k=1)[0]
    return CHARACTERS[selected_key]


def generate_idea(character):
    """
    [아이디어 생성 단계]
    성격(persona)과 제안 규칙(idea_format)을 모두 사용하여
    완벽한 피칭 문단을 생성합니다.
    """
    prompt = f'''
[역할 부여]
{character['persona']}

[미션]
너의 성격에 맞는 기상천외하고 웃긴 스타트업 아이디어를 하나 제안해줘.

[응답 규칙 - 필수]
1. 반드시 아래 포맷을 따라서 답변해야 해:
   {character['idea_format']}
2. 모든 내용을 **구분선이나 줄바꿈 없이 하나의 단락**으로 자연스럽게 연결해서 출력해.
3. 질문형 마무리나 "함께 가자"는 식의 권유 멘트는 절대 하지 마.

[출력 태그 가이드]
[TITLE] 아이디어 제목 (15자 이내)
[DESC] 위 규칙대로 작성된 아이디어 제안 본문 (250자 미만)
'''

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level="minimal"),
                max_output_tokens=300,  # TITLE+DESC 합쳐서 350자 커버
                temperature=0.8  # 창의성up
            )
        )
        text = response.text.strip()
        
        # 파싱 로직
        title = ''
        description = ''
        
        for line in text.split('\n'):
            if '[TITLE]' in line:
                title = line.replace('[TITLE]', '').strip()
            elif '[DESC]' in line:
                description = line.replace('[DESC]', '').strip()
        
        # 파싱 실패 시 전체 텍스트를 설명으로 간주 (방어 코드)
        if not description and not title:
             description = text

        return {
            'title': title or f"{character['name']}의 비밀 프로젝트",
            'description': description or '아이디어 구상 중입니다...'
        }
    
    except Exception as e:
        print(f"Gemini API Error (Idea): {e}")
        return {
            'title': '통신 오류',
            'description': 'AI와의 연결이 불안정하여 아이디어를 불러오지 못했습니다.'
        }


def generate_result(character, idea_title, is_success):
    """
    [결과 반응 단계]
    제안 규칙(idea_format)을 제외하고, 오직 성격(persona)만 사용하여
    성공/실패 결과에 대한 리액션만 생성합니다.
    """
    result_type = "대성공 (초대박)" if is_success else "완전 실패 (폭망)"
    
    prompt = f'''
[역할 부여]
{character['persona']}

[상황 발생]
네가 야심 차게 제안했던 사업 아이템 "{idea_title}"이(가) 결과적으로 **{result_type}**했어.

[미션]
이 결과에 대해 너의 성격과 말투를 100% 살려서 리얼한 반응을 보여줘.

[**중요 금지사항**]
1. **절대 자기소개를 다시 하지 마.** (이미 니가 누군지 알고 있음)
2. **아이디어에 대해 다시 설명하지 마.** (이미 투자는 끝났음)
3. 오직 결과에 대한 기쁨이나 좌절, 핑계만 대답해.

[출력 태그 가이드]
[SYSTEM] 성공/실패한 아이디어의 참신한 이유를 포함하여 상황을 설명하는 3인칭 지문 (1~2문장)
[REACTION] 성공/실패한 아이디어와 관련된 캐릭터의 직접적인 반응 대사 (1~2문장)
'''

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level="minimal")
            )
        )
        text = response.text.strip()
        
        # 파싱 로직
        system_msg = ''
        reaction = ''
        
        for line in text.split('\n'):
            if '[SYSTEM]' in line:
                system_msg = line.replace('[SYSTEM]', '').strip()
            elif '[REACTION]' in line:
                reaction = line.replace('[REACTION]', '').strip()
        
        return {
            'system_msg': system_msg or '결과가 집계되었습니다.',
            'reaction': reaction or '...'
        }
    
    except Exception as e:
        print(f"Gemini API Error (Result): {e}")
        if is_success:
            return {
                'system_msg': f'{character["name"]}의 사업이 대박났습니다!',
                'reaction': '와! 진짜 대박이다!'
            }
        else:
            return {
                'system_msg': f'{character["name"]}의 사업이 망했습니다...',
                'reaction': '으악... 내 돈...'
            }