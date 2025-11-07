# LoRA 파인튜닝 데이터셋

## 개요

이 데이터셋은 6개 전문 에이전트를 위한 LoRA (Low-Rank Adaptation) 파인튜닝용 훈련 데이터입니다.

**기반 모델**: Qwen3-4B-Instruct
**목적**: 정부/지자체 업무 특화 에이전트 성능 향상
**언어**: 한국어
**Phase**: Phase 14 (Post-MVP)

## 에이전트별 역할

### 1. RAG Agent (문서 검색 및 분석)
- **역할**: 고급 문서 검색 및 다중 문서 추론
- **도구**: document_search
- **특징**: 정확한 출처 인용, 다중 문서 비교 분석

### 2. Citizen Support Agent (민원 지원)
- **역할**: 공감적이고 정중한 민원 응대
- **말투**: 존댓말, 친절한 안내
- **특징**: 절차 안내, 문의처 제공, 추가 질문 유도

### 3. Document Writing Agent (문서 작성)
- **역할**: 정부 공문서 및 보고서 생성
- **형식**: 표준 문서 구조 (개요, 배경, 내용, 예산, 일정, 효과)
- **특징**: 형식적이고 체계적인 문서

### 4. Legal Research Agent (법규 검색)
- **역할**: 법령 검색 및 쉬운 해석
- **도구**: legal_reference
- **특징**: 원문 제시 + 쉬운 설명 + 실무 적용

### 5. Data Analysis Agent (데이터 분석)
- **역할**: 통계 분석 및 시각화
- **도구**: calculator, data_analysis
- **특징**: 천 단위 쉼표, 퍼센트 계산, 트렌드 분석

### 6. Review Agent (검토)
- **역할**: 내용 검토 (사실, 문법, 정책 부합성)
- **특징**: 오류 발견, 개선 제안, 수정안 제시

## 데이터셋 구조

### 파일 형식: JSONL (JSON Lines)

각 줄은 하나의 훈련 샘플:

```json
{
  "instruction": "사용자 질문 또는 요청",
  "input": "추가 컨텍스트 (선택사항, 없으면 빈 문자열)",
  "output": "에이전트의 기대 응답",
  "agent_type": "rag|citizen_support|document_writing|legal_research|data_analysis|review"
}
```

### 현재 데이터셋 통계

| 에이전트 | 샘플 수 | 비율 |
|---------|--------|------|
| RAG | 4 | 17.4% |
| Citizen Support | 6 | 26.1% |
| Document Writing | 3 | 13.0% |
| Legal Research | 3 | 13.0% |
| Data Analysis | 4 | 17.4% |
| Review | 3 | 13.0% |
| **총계** | **23** | **100%** |

⚠️ **주의**: 현재는 예시 데이터셋입니다. Phase 14 실제 파인튜닝 시 **에이전트당 500-1000개 샘플** (총 3,000-6,000개) 필요.

## 데이터 수집 전략 (Phase 14)

### 1단계: 초기 샘플 확보 (각 에이전트 100개)
- 실제 업무 시나리오 기반 작성
- 각 부서별 업무 담당자 인터뷰
- 기존 민원/문서 아카이브 활용

### 2단계: 다양성 확보 (각 에이전트 200개)
- 난이도별 분포: 쉬움(30%), 보통(50%), 어려움(20%)
- 주제별 균형: 복지, 교육, 도로, 환경, 민원 등
- 예외 케이스 포함: 오류 처리, 불충분한 정보 등

### 3단계: 품질 검증 및 확장 (각 에이전트 500-1000개)
- 전문가 리뷰 (법무팀, 실무 담당자)
- A/B 테스트로 효과 검증
- 부족한 시나리오 추가 수집

## 파인튜닝 절차

### 1. 환경 설정

```bash
# PEFT 라이브러리 설치
pip install peft transformers bitsandbytes accelerate

# 기반 모델 다운로드 (폐쇄망 사전 준비)
huggingface-cli download Qwen/Qwen3-4B-Instruct
```

### 2. 데이터 전처리

```python
import json

# 에이전트별 데이터 분리
def split_by_agent(input_file):
    agents = {}
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            agent = data['agent_type']
            if agent not in agents:
                agents[agent] = []
            agents[agent].append(data)
    return agents

# 실행
agents_data = split_by_agent('lora_training_dataset.jsonl')
print(f"RAG samples: {len(agents_data['rag'])}")
```

### 3. LoRA 파인튜닝 (에이전트별)

```python
from peft import LoraConfig, get_peft_model, TaskType
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer

# 기반 모델 로드
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-4B-Instruct")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-4B-Instruct")

# LoRA 설정
lora_config = LoraConfig(
    r=16,  # Rank
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],  # Qwen 모델 기준
    lora_dropout=0.05,
    bias="none",
    task_type=TaskType.CAUSAL_LM
)

# LoRA 모델 생성
model = get_peft_model(model, lora_config)
print(f"Trainable params: {model.print_trainable_parameters()}")

# 훈련 설정
training_args = TrainingArguments(
    output_dir=f"./lora_models/rag_agent",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    logging_steps=10,
    save_steps=100,
    save_total_limit=3,
)

# 훈련 실행
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,  # 전처리된 데이터
)

trainer.train()

# LoRA 어댑터 저장
model.save_pretrained(f"./lora_models/rag_agent")
```

### 4. 어댑터 로딩 및 사용

```python
from peft import PeftModel

# 기반 모델 + LoRA 어댑터 로드
base_model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen3-4B-Instruct")
model = PeftModel.from_pretrained(base_model, "./lora_models/rag_agent")

# 추론
inputs = tokenizer("2023년 예산 집행 현황 문서를 찾아서 요약해줘", return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=500)
response = tokenizer.decode(outputs[0])
```

## 품질 기준

### 훈련 데이터 품질 체크리스트

- [ ] **정확성**: 사실 관계가 정확한가?
- [ ] **관련성**: 에이전트 역할에 부합하는가?
- [ ] **다양성**: 다양한 시나리오를 커버하는가?
- [ ] **난이도**: 쉬움/보통/어려움 균형이 맞는가?
- [ ] **형식**: JSON 구조가 올바른가?
- [ ] **한국어**: 자연스러운 한국어 표현인가?
- [ ] **길이**: 응답이 너무 짧거나 길지 않은가? (100-1000자 권장)
- [ ] **도구 사용**: 해당 에이전트의 도구 사용이 적절한가?

### 파인튜닝 성능 평가

1. **정량 평가**:
   - Perplexity 감소
   - 분류 정확도 (에이전트 선택)
   - 응답 생성 속도

2. **정성 평가**:
   - 전문가 블라인드 테스트 (A/B)
   - 실무 사용자 만족도
   - 오류율 감소

3. **목표 성능** (FR-071A):
   - 에이전트 선택 정확도: 85% 이상
   - 응답 품질: 4.0/5.0 이상 (사용자 평가)
   - 추론 시간: 3초 이하 (LoRA 교체 포함)

## 참고 사항

### LoRA 하이퍼파라미터 권장값

| 파라미터 | 권장값 | 설명 |
|---------|--------|------|
| r (Rank) | 16-32 | 작을수록 빠르지만 성능 하락 |
| lora_alpha | 32 | 보통 r의 2배 |
| lora_dropout | 0.05 | 과적합 방지 |
| learning_rate | 1e-4 ~ 3e-4 | Adam optimizer 기준 |
| batch_size | 4-8 | GPU 메모리에 따라 조정 |
| epochs | 3-5 | 데이터셋 크기에 따라 조정 |

### 메모리 요구사항

- **훈련**: GPU 16GB+ (RTX 4090, A10 등)
- **추론**:
  - Base 모델: ~2.5GB (Q4_K_M)
  - LoRA 어댑터: ~500MB per agent
  - LRU 캐시 (2-3개): ~1-1.5GB
  - **총**: ~4-5GB

### 폐쇄망 배포 체크리스트

- [ ] Qwen3-4B-Instruct 기반 모델 (GGUF)
- [ ] 6개 LoRA 어댑터 (.safetensors)
- [ ] PEFT 라이브러리 (오프라인 wheel)
- [ ] transformers 라이브러리
- [ ] 훈련 데이터셋 (백업)
- [ ] 파인튜닝 스크립트
- [ ] 성능 평가 스크립트

## 라이선스

- **기반 모델**: Qwen3-4B-Instruct (Apache 2.0)
- **데이터셋**: 내부 사용 (정부/지자체 업무 데이터)
- **LoRA 어댑터**: 파생물, 조직 내부 사용

## 문의

Phase 14 파인튜닝 관련 문의:
- 기술 문의: AI 개발팀
- 데이터 수집: 각 부서 실무 담당자
- 품질 검증: 법무팀, 전문가 그룹

---

**마지막 업데이트**: 2025-11-07
**버전**: 0.1 (예시 데이터셋)
**상태**: Phase 10 인프라 구축용, Phase 14 실제 파인튜닝 대기
