import transformers
import torch
import gc
import os

# 환경 변수 설정 (메모리 단편화 방지)
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'

# 전역 파이프라인 캐시
_pipeline_cache = None

def prepare_pipeline_obj():
    """
    파이프라인을 한 번만 생성하고 재사용합니다.
    """
    global _pipeline_cache
    
    if _pipeline_cache is not None:
        print("✅ 기존 파이프라인 재사용")
        return _pipeline_cache
    
    print("🔄 새 파이프라인 생성 중...")
    
    # 메모리 완전 정리
    gc.collect()
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    
    print(f"🧹 정리 전 GPU 메모리: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
    
    # 양자화 없이 float16만 사용
    _pipeline_cache = transformers.pipeline(
        "text-generation",
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        model_kwargs={
            "torch_dtype": torch.float16,
            "low_cpu_mem_usage": True,
        },
        device_map="auto",
    )
    
    print(f"✅ 모델 로드 완료. GPU 메모리 사용량: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
    
    return _pipeline_cache


def cleanup_pipeline():
    global _pipeline_cache
    
    if _pipeline_cache is not None:
        print("🧹 파이프라인 메모리 해제 중...")
        del _pipeline_cache
        _pipeline_cache = None
        gc.collect()
        torch.cuda.empty_cache()
        print("✅ 파이프라인 메모리 해제 완료")


def chat_with_llama3(pipeline_obj, system_prompt, user_prompt):
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    prompt = pipeline_obj.tokenizer.apply_chat_template(
        messages,
        tokenize=False, 
        add_generation_prompt=True 
    )

    eos_tokens = [
        pipeline_obj.tokenizer.eos_token_id, 
        pipeline_obj.tokenizer.convert_tokens_to_ids("```"),
        pipeline_obj.tokenizer.convert_tokens_to_ids("]"),
        pipeline_obj.tokenizer.convert_tokens_to_ids("}")
    ]
    
    with torch.no_grad():
        outputs = pipeline_obj(
            prompt,
            max_new_tokens=128,  # 256 → 128로 더욱 줄임
            do_sample=True,
            temperature=0.3,
            top_p=0.8,
            return_full_text=False,
            eos_token_id=eos_tokens,
            pad_token_id=pipeline_obj.tokenizer.eos_token_id
        )

    torch.cuda.empty_cache()
    
    return outputs[0]["generated_text"].strip()