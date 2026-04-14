"""
Fleet 정비 데이터 생성 스크립트
쿠팡 로켓배송 맥락: 1톤 탑차 기준, 전국 배송캠프 소속
"""
import random
import json
from datetime import datetime, timedelta

random.seed(42)

# 기준 정보
CAMPS = ["서울송파", "서울강서", "경기부천", "경기동탄", "인천서구", "대전대덕", "부산사상"]
VENDORS = ["A모빌리티정비", "B오토서비스", "C카센터", "D종합정비", "E오토케어"]
MAINTENANCE_TYPES = {
    "예방정비": {"cost_range": (80000, 250000), "lead_range": (1, 2)},
    "사후정비": {"cost_range": (150000, 800000), "lead_range": (2, 5)},
    "긴급정비": {"cost_range": (300000, 1500000), "lead_range": (3, 8)},
}
PARTS = {
    "예방정비": ["엔진오일 교체", "에어필터 교체", "브레이크패드 점검", "타이어 공기압", "정기점검"],
    "사후정비": ["브레이크 디스크 교체", "배터리 교체", "냉각수 누수 수리", "와이퍼 교체", "전조등 교체"],
    "긴급정비": ["엔진 오버홀", "변속기 수리", "클러치 교체", "라디에이터 교체", "미션오일 누유 수리"],
}

# 30대 차량 생성
NUM_VEHICLES = 30
vehicles = []
for i in range(NUM_VEHICLES):
    year = random.choices([2019, 2020, 2021, 2022, 2023, 2024], weights=[5, 15, 20, 25, 20, 15])[0]
    base_mileage = (2025 - year) * random.randint(35000, 55000)
    vehicles.append({
        "vehicle_id": f"CLS-{3000+i:04d}",
        "year": year,
        "camp": random.choice(CAMPS),
        "model": "현대 포터2 1톤" if i % 3 != 0 else "기아 봉고3 1톤",
        "current_mileage": base_mileage,
    })

# 차량별 정비 프로파일 설정
# - 문제 차량(4대): 월 2~3회 정비 (긴급·사후 비율↑)
# - 일반 차량(나머지): 월 0~1회 정비 (예방 비율↑)
problem_indices = random.sample(range(NUM_VEHICLES), 4)
today = datetime(2026, 4, 14)

records = []
record_counter = 0

for v_idx, vehicle in enumerate(vehicles):
    is_problem = v_idx in problem_indices
    
    if is_problem:
        # 문제 차량: 12개월 동안 15~25건 정비
        num_records = random.randint(15, 25)
        type_weights = [20, 45, 35]  # 긴급/사후 많음
    else:
        # 일반 차량: 12개월 동안 3~7건 정비
        num_records = random.randint(3, 7)
        type_weights = [70, 25, 5]  # 예방 위주
    
    # 각 차량의 정비 날짜 생성 (랜덤 분포)
    days_list = random.sample(range(365), num_records)
    days_list.sort(reverse=True)
    
    # 문제 차량은 간혹 재정비 빈발 시뮬레이션 (기존 날짜 근처에 추가)
    if is_problem and random.random() < 0.7:
        # 랜덤하게 1~2쌍의 인접 정비 생성
        for _ in range(random.randint(1, 2)):
            if len(days_list) > 0:
                base_day = random.choice(days_list)
                # 3~6일 차이 정비 추가
                nearby_day = max(0, base_day - random.randint(3, 6))
                if nearby_day not in days_list:
                    days_list.append(nearby_day)
    
    for day_offset in days_list:
        mtype = random.choices(list(MAINTENANCE_TYPES.keys()), weights=type_weights)[0]
        config = MAINTENANCE_TYPES[mtype]
        cost = random.randint(*config["cost_range"])
        lead_days = random.randint(*config["lead_range"])
        maint_date = today - timedelta(days=day_offset)
        
        record_counter += 1
        records.append({
            "record_id": f"MR-{record_counter:04d}",
            "vehicle_id": vehicle["vehicle_id"],
            "camp": vehicle["camp"],
            "model": vehicle["model"],
            "year": vehicle["year"],
            "date": maint_date.strftime("%Y-%m-%d"),
            "type": mtype,
            "part": random.choice(PARTS[mtype]),
            "vendor": random.choice(VENDORS),
            "cost": cost,
            "lead_days": lead_days,
            "mileage_at_service": vehicle["current_mileage"] - random.randint(0, 20000),
        })

# 차량별 현재 상태 계산
vehicle_stats = {}
for v in vehicles:
    vid = v["vehicle_id"]
    v_records = [r for r in records if r["vehicle_id"] == vid]
    total_cost = sum(r["cost"] for r in v_records)
    total_lead = sum(r["lead_days"] for r in v_records)
    # 가동률 = (365 - 정비일) / 365
    uptime = round((365 - total_lead) / 365 * 100, 1)
    
    vehicle_stats[vid] = {
        **v,
        "total_maintenance_cost": total_cost,
        "total_downtime_days": total_lead,
        "maintenance_count": len(v_records),
        "uptime_rate": uptime,
        "cost_per_km": round(total_cost / max(v["current_mileage"], 1), 2),
        "age_years": 2026 - v["year"],
    }

# 날짜순 정렬
records.sort(key=lambda x: x["date"], reverse=True)

# JSON 저장
output = {
    "generated_at": today.strftime("%Y-%m-%d"),
    "vehicles": list(vehicle_stats.values()),
    "maintenance_records": records,
    "meta": {
        "total_vehicles": NUM_VEHICLES,
        "total_records": len(records),
        "camps": CAMPS,
        "vendors": VENDORS,
    }
}

with open("fleet_data.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"✅ 데이터 생성 완료")
print(f"   - 차량: {NUM_VEHICLES}대")
print(f"   - 정비 기록: {len(records)}건")
print(f"   - 총 정비비: ₩{sum(r['cost'] for r in records):,}")
print(f"   - 평균 가동률: {sum(v['uptime_rate'] for v in vehicle_stats.values())/NUM_VEHICLES:.1f}%")
