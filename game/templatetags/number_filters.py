from django import template

register = template.Library()


@register.filter
def korean_currency(value):
    """
    만원 단위 숫자를 한국식 억/조 단위로 변환
    예: 60452 → "6억 452만원"
        41760 → "4억 1,760만원"
        1250 → "1,250만원"
        0 → "0원"
    """
    try:
        value = int(value)
    except (ValueError, TypeError):
        return value
    
    if value == 0:
        return "0원"
    
    # 만원 단위 기준
    # 1억 = 10000만원
    # 1조 = 100000000만원
    
    jo = value // 100000000  # 조
    remainder = value % 100000000
    eok = remainder // 10000  # 억
    man = remainder % 10000  # 만
    
    parts = []
    
    if jo > 0:
        parts.append(f"{jo:,}조")
    
    if eok > 0:
        parts.append(f"{eok:,}억")
    
    if man > 0:
        parts.append(f"{man:,}만원")
    elif parts:  # 억/조가 있는데 만원 단위가 0이면
        parts[-1] += "원"
    
    return " ".join(parts) if parts else "0원"


@register.filter
def add_comma(value):
    """
    숫자에 쉼표 추가
    예: 60452 → "60,452"
    """
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return value
