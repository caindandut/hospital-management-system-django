from adminpanel.models import DoctorRankFee

def get_rank_fees():
    """Get rank fees from database"""
    fees = {}
    try:
        for rank_fee in DoctorRankFee.objects.all():
            fees[rank_fee.rank] = int(rank_fee.default_fee)
    except Exception:
        # Fallback to hardcoded values if database is not available
        fees = {
            "BS": 200_000,
            "THS": 300_000,
            "TS": 500_000,
            "PGS": 700_000,
            "GS": 1_000_000,
        }
    return fees

def get_default_fee():
    """Get default fee from database"""
    try:
        bs_fee = DoctorRankFee.objects.filter(rank="BS").first()
        return int(bs_fee.default_fee) if bs_fee else 200_000
    except Exception:
        return 200_000

# Cache the fees to avoid repeated database queries
_rank_fees_cache = None
def get_cached_rank_fees():
    global _rank_fees_cache
    if _rank_fees_cache is None:
        _rank_fees_cache = get_rank_fees()
    return _rank_fees_cache

RANK_FEES = get_cached_rank_fees()
DEFAULT_FEE = get_default_fee()

NORMALIZE_MAP = {
    "bs": "BS", "bácsĩ": "BS", "bacsi": "BS", "bác sĩ": "BS",
    "ths": "THS", "thacsĩ": "THS", "thacsi": "THS", "th.s": "THS", "thạc sĩ": "THS",
    "ts": "TS", "tiensĩ": "TS", "tiensi": "TS", "t.s": "TS", "tiến sĩ": "TS",
    "pgs": "PGS", "phó giáo sư": "PGS",
    "gs": "GS", "giaosư": "GS", "giaosu": "GS", "giáo sư": "GS",
}


def normalize_rank(raw: str | None) -> str:
    v = (raw or "").strip()
    if not v:
        return ""
    # Try exact match first
    key = v.lower()
    if key in NORMALIZE_MAP:
        return NORMALIZE_MAP[key]
    # Try with spaces and dots removed
    key = key.replace(".", "").replace(" ", "")
    if key in NORMALIZE_MAP:
        return NORMALIZE_MAP[key]
    # Return uppercase if no match
    return v.upper()


def get_consultation_fee(doctor) -> int:
    code = ""
    # Ưu tiên field rank; nếu dự án dùng tên khác, thử thêm:
    for field in ("rank", "degree", "degree_code", "title_code"):
        if hasattr(doctor, field) and getattr(doctor, field):
            code = normalize_rank(getattr(doctor, field))
            break
    
    # Get fresh fees from database
    fees = get_rank_fees()
    return fees.get(code or "", get_default_fee())


# Backward-compatibility helper (if some places still call this)
def get_effective_fee(rank: str | None) -> int:
    fees = get_rank_fees()
    return fees.get(normalize_rank(rank), get_default_fee())


