import requests
import os

from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

BASE_DIR= Path(__file__).resolve().parent

ROOT_DIR = BASE_DIR.parent 

ENV_PATH = ROOT_DIR.parent / ".env"


load_dotenv()


OPEN_ALEX_API_KEY= os.getenv("OPEN_ALEX_API_KEY", "rqxsibReeMmwD1Y9p4yiYq")

OPEN_ALEX_URL = "https://api.openalex.org/sources/"


def get_online_access_score(
    issn : str
) -> int:
    """학술지 및 수록 논문의 온라인 접근성을 평가한다.

    Args:
        issn (str): ISSN(International Standard Serial Number)

    Raises:
        Exception: _description_

    Returns:
        int: 평가 점수
    """
    
    response = requests.get(
        f"{OPEN_ALEX_URL}issn:{issn}?api_key={OPEN_ALEX_API_KEY}"
    )
    

    
    if not response:
        raise Exception("API 요청에 실패하였습니다.")
    
    data = response.json()
    
    
    hompage_url = data.get("homepage_url")

    if hompage_url:
        print(f"온라인 접근성 여부 : {bool(hompage_url)}")
        
        
    is_oa = data.get("is_oa")

    if is_oa:
        print(f"OA (Open Access) 여부 : {bool(is_oa)}")
        
        
    last_publication_year = data.get("last_publication_year")
    
    
    if last_publication_year is None:
        print(f"{last_publication_year} 데이터가 존재하지 않습니다.")

    current_year = datetime.now().year
    
    
    
    score_15 = (
        (current_year-int(last_publication_year)) >= 6 and
        is_oa
        
    )
    score_12 = (
        (current_year-int(last_publication_year)) >= 4 and
        is_oa
    )
    score_9 = (
        (current_year-int(last_publication_year)) >= 9 and
        is_oa
    )
    score_3 = (
        (current_year-int(last_publication_year)) >= 1 and
        is_oa
    )
    
    
    if not is_oa:
        score = 0
        
        
    if score_15:
        score = 15
    elif score_12:
        score = 12
    elif score_9:
        score = 9
    elif score_3:
        score = 3
    else:
        score = 0
        
        
        
    return score
    
    
    
# if __name__ == "__main__":
#     online_access_score = online_access("2234-4772")
#     print("online_access_score: ", online_access_score)
    